"""
Configuration Change Notifier
Widget that shows proactive warnings when configuration changes are made
"""

from __future__ import annotations

from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size
from ui.racing_ui_theme import get_racing_stylesheet, RacingColor

try:
    from services.intelligent_config_monitor import IntelligentConfigMonitor, ConfigWarning
    from services.config_version_control import ConfigChange, ChangeType, ChangeSeverity
    MONITOR_AVAILABLE = True
except ImportError:
    MONITOR_AVAILABLE = False
    IntelligentConfigMonitor = None  # type: ignore
    ConfigWarning = None  # type: ignore
    ConfigChange = None  # type: ignore
    ChangeType = None  # type: ignore
    ChangeSeverity = None  # type: ignore


class ConfigChangeNotifier(QWidget):
    """
    Configuration change notifier widget.
    Shows proactive warnings and suggestions when settings are changed.
    """
    
    # Signal emitted when warnings are generated
    warnings_generated = Signal(list)
    
    def __init__(self, config_monitor: Optional[IntelligentConfigMonitor] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        
        self.config_monitor = config_monitor
        if not self.config_monitor and MONITOR_AVAILABLE and IntelligentConfigMonitor:
            try:
                from services.config_version_control import ConfigVersionControl
                config_vc = ConfigVersionControl()
                self.config_monitor = IntelligentConfigMonitor(config_vc=config_vc)
            except Exception as e:
                print(f"Failed to initialize config monitor: {e}")
        
        self.current_warnings: List[ConfigWarning] = []
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Setup notifier widget."""
        main_layout = QVBoxLayout(self)
        margin = self.scaler.get_scaled_size(5)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(self.scaler.get_scaled_size(5))
        
        # Header
        header = QLabel("Q - Configuration Monitor")
        header_font = self.scaler.get_scaled_font_size(12)
        header.setStyleSheet(f"""
            font-size: {header_font}px;
            font-weight: bold;
            color: {RacingColor.ACCENT_NEON_BLUE.value};
        """)
        main_layout.addWidget(header)
        
        # Warnings display
        self.warnings_display = QTextEdit()
        self.warnings_display.setReadOnly(True)
        warnings_font = self.scaler.get_scaled_font_size(10)
        self.warnings_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: #0a0a0a;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: {warnings_font}px;
                border: 1px solid #404040;
                border-radius: {self.scaler.get_scaled_size(3)}px;
            }}
        """)
        self.warnings_display.setMinimumHeight(self.scaler.get_scaled_size(200))
        self.warnings_display.setMaximumHeight(self.scaler.get_scaled_size(300))
        main_layout.addWidget(self.warnings_display)
        
        # Actions
        actions_layout = QHBoxLayout()
        
        dismiss_btn = QPushButton("Dismiss")
        dismiss_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #404040;
                color: #ffffff;
                padding: {self.scaler.get_scaled_size(3)}px {self.scaler.get_scaled_size(8)}px;
                font-size: {self.scaler.get_scaled_font_size(9)}px;
            }}
        """)
        dismiss_btn.clicked.connect(self._dismiss_warnings)
        actions_layout.addWidget(dismiss_btn)
        
        actions_layout.addStretch()
        main_layout.addLayout(actions_layout)
        
        # Initially hidden
        self.hide()
    
    def notify_change(
        self,
        change_type: ChangeType,
        category: str,
        parameter: str,
        old_value: any,
        new_value: any,
        telemetry: Optional[Dict[str, float]] = None,
    ) -> None:
        """
        Notify about a configuration change.
        
        Args:
            change_type: Type of change
            category: Category
            parameter: Parameter name
            old_value: Previous value
            new_value: New value
            telemetry: Current telemetry
        """
        if not self.config_monitor:
            return
        
        # Monitor change and get warnings
        warnings = self.config_monitor.monitor_change(
            change_type=change_type,
            category=category,
            parameter=parameter,
            old_value=old_value,
            new_value=new_value,
            telemetry=telemetry,
        )
        
        if warnings:
            self.current_warnings = warnings
            self._display_warnings(warnings)
            self.warnings_generated.emit(warnings)
            self.show()
        else:
            self.hide()
    
    def _display_warnings(self, warnings: List[ConfigWarning]) -> None:
        """Display warnings in the widget."""
        html = ""
        
        # Group by severity
        critical = [w for w in warnings if w.severity == "critical"]
        high = [w for w in warnings if w.severity == "high"]
        info = [w for w in warnings if w.severity == "info"]
        
        if critical:
            html += f'<div style="color: {RacingColor.ACCENT_NEON_RED.value}; font-weight: bold;">🚨 CRITICAL:</div>'
            for warning in critical:
                html += f'<div style="color: {RacingColor.ACCENT_NEON_RED.value}; margin-left: 10px;">• {self._escape_html(warning.message)}</div>'
                if warning.suggestion:
                    html += f'<div style="color: #ff8000; margin-left: 20px;">💡 {self._escape_html(warning.suggestion)}</div>'
                if warning.alternative_value is not None:
                    html += f'<div style="color: {RacingColor.ACCENT_NEON_GREEN.value}; margin-left: 20px;">✅ Better: {warning.alternative_value}</div>'
            html += "<br>"
        
        if high:
            html += f'<div style="color: {RacingColor.ACCENT_NEON_ORANGE.value}; font-weight: bold;">⚠️ WARNING:</div>'
            for warning in high:
                html += f'<div style="color: {RacingColor.ACCENT_NEON_ORANGE.value}; margin-left: 10px;">• {self._escape_html(warning.message)}</div>'
                if warning.suggestion:
                    html += f'<div style="color: #ffaa00; margin-left: 20px;">💡 {self._escape_html(warning.suggestion)}</div>'
            html += "<br>"
        
        if info:
            html += f'<div style="color: {RacingColor.ACCENT_NEON_BLUE.value}; font-weight: bold;">💡 SUGGESTION:</div>'
            for warning in info:
                html += f'<div style="color: {RacingColor.ACCENT_NEON_BLUE.value}; margin-left: 10px;">• {self._escape_html(warning.message)}</div>'
        
        self.warnings_display.setHtml(html)
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\n", "<br>"))
    
    def _dismiss_warnings(self) -> None:
        """Dismiss current warnings."""
        self.current_warnings = []
        self.warnings_display.clear()
        self.hide()
        
        if self.config_monitor:
            self.config_monitor.clear_warnings()

