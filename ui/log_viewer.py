"""
Log Viewer UI

Provides a GUI for viewing and analyzing logs with:
- Real-time log streaming
- Filtering and search
- Log level filtering
- Performance metrics visualization
- Error pattern detection
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.logging_config import LoggingManager, get_logger

LOGGER = get_logger(__name__)


class LogViewer(QWidget):
    """Log viewer widget with filtering and search."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize log viewer."""
        super().__init__(parent)
        self.logging_manager = LoggingManager()
        self.log_file_path: Optional[Path] = None
        self._setup_ui()
        self._setup_timer()
    
    def _setup_ui(self) -> None:
        """Set up UI components."""
        layout = QVBoxLayout(self)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Log level filter
        controls_layout.addWidget(QLabel("Level:"))
        self.level_filter = QComboBox()
        self.level_filter.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_filter.setCurrentText("INFO")
        self.level_filter.currentTextChanged.connect(self._apply_filters)
        controls_layout.addWidget(self.level_filter)
        
        # Search
        controls_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search logs...")
        self.search_input.textChanged.connect(self._apply_filters)
        controls_layout.addWidget(self.search_input)
        
        # Module filter
        controls_layout.addWidget(QLabel("Module:"))
        self.module_filter = QComboBox()
        self.module_filter.addItem("ALL")
        self.module_filter.setEditable(True)
        self.module_filter.currentTextChanged.connect(self._apply_filters)
        controls_layout.addWidget(self.module_filter)
        
        # Buttons
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._refresh_logs)
        controls_layout.addWidget(self.refresh_btn)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self._clear_logs)
        controls_layout.addWidget(self.clear_btn)
        
        self.auto_scroll_btn = QPushButton("Auto-scroll: ON")
        self.auto_scroll_btn.setCheckable(True)
        self.auto_scroll_btn.setChecked(True)
        self.auto_scroll_btn.clicked.connect(self._toggle_auto_scroll)
        controls_layout.addWidget(self.auto_scroll_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFontFamily("Courier")
        self.log_display.setFontPointSize(9)
        layout.addWidget(self.log_display)
        
        # Status
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
    
    def _setup_timer(self) -> None:
        """Set up auto-refresh timer."""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_logs)
        self.refresh_timer.start(2000)  # Refresh every 2 seconds
    
    def set_log_file(self, log_file: Path) -> None:
        """Set log file to display."""
        self.log_file_path = log_file
        self._refresh_logs()
    
    def _refresh_logs(self) -> None:
        """Refresh log display."""
        if not self.log_file_path or not self.log_file_path.exists():
            # Try default log file
            default_log = Path("logs/ai_tuner.log")
            if default_log.exists():
                self.log_file_path = default_log
            else:
                self.status_label.setText("No log file found")
                return
        
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Apply filters
            filtered_lines = self._filter_lines(lines)
            
            # Update display
            current_scroll = self.log_display.verticalScrollBar().value()
            max_scroll = self.log_display.verticalScrollBar().maximum()
            auto_scroll = self.auto_scroll_btn.isChecked() and (current_scroll >= max_scroll - 10)
            
            self.log_display.clear()
            self.log_display.setPlainText(''.join(filtered_lines))
            
            if auto_scroll:
                self.log_display.verticalScrollBar().setValue(
                    self.log_display.verticalScrollBar().maximum()
                )
            
            # Update status
            self.status_label.setText(
                f"Showing {len(filtered_lines)}/{len(lines)} lines "
                f"({self.log_file_path.name})"
            )
        except Exception as e:
            self.status_label.setText(f"Error reading log file: {e}")
            LOGGER.error(f"Error reading log file: {e}")
    
    def _filter_lines(self, lines: List[str]) -> List[str]:
        """Filter log lines based on current filters."""
        filtered = []
        level = self.level_filter.currentText()
        search_text = self.search_input.text().lower()
        module_text = self.module_filter.currentText().lower()
        
        for line in lines:
            # Level filter
            if level != "ALL":
                if f"[{level}]" not in line.upper():
                    continue
            
            # Module filter
            if module_text and module_text != "all":
                if module_text not in line.lower():
                    continue
            
            # Search filter
            if search_text:
                if search_text not in line.lower():
                    continue
            
            filtered.append(line)
        
        return filtered
    
    def _apply_filters(self) -> None:
        """Apply current filters."""
        self._refresh_logs()
    
    def _clear_logs(self) -> None:
        """Clear log display."""
        self.log_display.clear()
        self.status_label.setText("Logs cleared")
    
    def _toggle_auto_scroll(self, checked: bool) -> None:
        """Toggle auto-scroll."""
        self.auto_scroll_btn.setText(f"Auto-scroll: {'ON' if checked else 'OFF'}")
    
    def closeEvent(self, event) -> None:
        """Clean up on close."""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        super().closeEvent(event)


__all__ = ["LogViewer"]

