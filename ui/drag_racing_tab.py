"""
Drag Racing Analyzer Tab
Dedicated tab for drag racing analysis and coaching
"""

from __future__ import annotations

from typing import Dict, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QDoubleSpinBox,
    QSpinBox,
    QCheckBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSizePolicy,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size

try:
    from services.drag_racing_analyzer import DragRacingAnalyzer, DragRun
except ImportError:
    DragRacingAnalyzer = None
    DragRun = None


class DragRacingTab(QWidget):
    """Drag Racing Analyzer tab with run analysis and coaching."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.analyzer: Optional[DragRacingAnalyzer] = None
        self.setup_ui()
        self._start_update_timer()
        
    def setup_ui(self) -> None:
        """Setup drag racing tab UI."""
        main_layout = QVBoxLayout(self)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        self.setStyleSheet("background-color: #1a1a1a;")
        
        # Control bar
        control_bar = self._create_control_bar()
        main_layout.addWidget(control_bar)
        
        # Content layout
        content_layout = QHBoxLayout()
        content_layout.setSpacing(get_scaled_size(15))
        
        # Left: Settings and coaching
        left_panel = self._create_settings_panel()
        content_layout.addWidget(left_panel, stretch=1)
        
        # Center: Run times and analysis
        center_panel = self._create_analysis_panel()
        content_layout.addWidget(center_panel, stretch=2)
        
        # Right: History and comparison
        right_panel = self._create_history_panel()
        content_layout.addWidget(right_panel, stretch=1)
        
        main_layout.addLayout(content_layout, stretch=1)
        
        # Import/Export bar
        from ui.module_feature_helper import add_import_export_bar
        add_import_export_bar(self, main_layout)
        
    def _create_control_bar(self) -> QWidget:
        """Create control bar."""
        bar = QWidget()
        padding = get_scaled_size(5)
        border = get_scaled_size(1)
        bar.setStyleSheet(f"background-color: #2a2a2a; padding: {padding}px; border: {border}px solid #404040;")
        layout = QHBoxLayout(bar)
        margin_h = get_scaled_size(10)
        margin_v = get_scaled_size(5)
        layout.setContentsMargins(margin_h, margin_v, margin_h, margin_v)
        
        title = QLabel("Drag Racing Analyzer")
        title_font = get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Start run button
        self.start_run_btn = QPushButton("Start Run")
        btn_padding_v = get_scaled_size(5)
        btn_padding_h = get_scaled_size(10)
        btn_font = get_scaled_font_size(11)
        self.start_run_btn.setStyleSheet(f"background-color: #00ff00; color: #000000; padding: {btn_padding_v}px {btn_padding_h}px; font-weight: bold; font-size: {btn_font}px;")
        layout.addWidget(self.start_run_btn)
        
        # Stop run button
        self.stop_run_btn = QPushButton("Stop Run")
        self.stop_run_btn.setStyleSheet(f"background-color: #ff0000; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px; font-size: {btn_font}px;")
        layout.addWidget(self.stop_run_btn)
        
        # Clear button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setStyleSheet(f"background-color: #404040; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px; font-size: {btn_font}px;")
        layout.addWidget(self.clear_btn)
        
        return bar
        
    def _create_settings_panel(self) -> QWidget:
        """Create settings panel."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        panel.setMaximumWidth(get_scaled_size(250))
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(15)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # Run settings
        settings_group = QGroupBox("Run Settings")
        group_font = get_scaled_font_size(12)
        group_border = get_scaled_size(1)
        group_radius = get_scaled_size(3)
        group_margin = get_scaled_size(10)
        settings_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(get_scaled_size(10))
        
        # Distance selection
        settings_layout.addWidget(QLabel("Target Distance:"))
        self.distance_combo = QComboBox()
        self.distance_combo.addItems(["60ft", "1/8 mile", "1/4 mile", "1/2 mile"])
        self.distance_combo.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.distance_combo)
        
        # Coaching enabled
        self.coaching_enabled = QCheckBox("Enable Coaching")
        self.coaching_enabled.setChecked(True)
        self.coaching_enabled.setStyleSheet("color: #ffffff;")
        settings_layout.addWidget(self.coaching_enabled)
        
        # Auto-start
        self.auto_start = QCheckBox("Auto-Start on Launch")
        self.auto_start.setChecked(True)
        self.auto_start.setStyleSheet("color: #ffffff;")
        settings_layout.addWidget(self.auto_start)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Coaching advice
        coaching_group = QGroupBox("Coaching Advice")
        coaching_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        coaching_layout = QVBoxLayout()
        
        self.coaching_label = QLabel("No run data yet")
        coaching_font = get_scaled_font_size(11)
        self.coaching_label.setStyleSheet(f"font-size: {coaching_font}px; color: #9aa0a6; padding: {get_scaled_size(5)}px;")
        self.coaching_label.setWordWrap(True)
        coaching_layout.addWidget(self.coaching_label)
        
        coaching_group.setLayout(coaching_layout)
        layout.addWidget(coaching_group)
        
        layout.addStretch()
        return panel
        
    def _create_analysis_panel(self) -> QWidget:
        """Create analysis panel."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        # Current run times
        times_group = QGroupBox("Current Run Times")
        group_font = get_scaled_font_size(12)
        group_border = get_scaled_size(1)
        group_radius = get_scaled_size(3)
        group_margin = get_scaled_size(10)
        times_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        times_layout = QHBoxLayout()
        
        # Time displays
        self.time_60ft = QLabel("60ft: --")
        time_font = get_scaled_font_size(16)
        self.time_60ft.setStyleSheet(f"font-size: {time_font}px; font-weight: bold; color: #00e0ff; padding: {get_scaled_size(10)}px;")
        times_layout.addWidget(self.time_60ft)
        
        self.time_18 = QLabel("1/8: --")
        self.time_18.setStyleSheet(f"font-size: {time_font}px; font-weight: bold; color: #00e0ff; padding: {get_scaled_size(10)}px;")
        times_layout.addWidget(self.time_18)
        
        self.time_14 = QLabel("1/4: --")
        self.time_14.setStyleSheet(f"font-size: {time_font}px; font-weight: bold; color: #00e0ff; padding: {get_scaled_size(10)}px;")
        times_layout.addWidget(self.time_14)
        
        times_group.setLayout(times_layout)
        layout.addWidget(times_group)
        
        # Trap speeds
        speeds_group = QGroupBox("Trap Speeds")
        speeds_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        speeds_layout = QHBoxLayout()
        
        self.speed_60ft = QLabel("60ft: -- mph")
        speed_font = get_scaled_font_size(14)
        self.speed_60ft.setStyleSheet(f"font-size: {speed_font}px; color: #ffffff; padding: {get_scaled_size(5)}px;")
        speeds_layout.addWidget(self.speed_60ft)
        
        self.speed_18 = QLabel("1/8: -- mph")
        self.speed_18.setStyleSheet(f"font-size: {speed_font}px; color: #ffffff; padding: {get_scaled_size(5)}px;")
        speeds_layout.addWidget(self.speed_18)
        
        self.speed_14 = QLabel("1/4: -- mph")
        self.speed_14.setStyleSheet(f"font-size: {speed_font}px; color: #ffffff; padding: {get_scaled_size(5)}px;")
        speeds_layout.addWidget(self.speed_14)
        
        speeds_group.setLayout(speeds_layout)
        layout.addWidget(speeds_group)
        
        layout.addStretch()
        return panel
        
    def _create_history_panel(self) -> QWidget:
        """Create history panel."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        panel.setMaximumWidth(get_scaled_size(300))
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        # Run history table
        title = QLabel("Run History")
        title_font = get_scaled_font_size(12)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["Run", "60ft", "1/8", "1/4"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.setMaximumHeight(get_scaled_size(300))
        self.history_table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
            }
        """)
        layout.addWidget(self.history_table)
        
        layout.addStretch()
        return panel
        
    def _start_update_timer(self) -> None:
        """Start timer for updates."""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(100)  # 10 Hz
        
    def _update_display(self) -> None:
        """Update display with current data."""
        pass
        
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update drag racing tab with telemetry data."""
        if not self.analyzer:
            if DragRacingAnalyzer:
                try:
                    self.analyzer = DragRacingAnalyzer()
                except Exception:
                    pass
        
        # Update times if analyzer is active
        if self.analyzer and hasattr(self.analyzer, 'current_run'):
            # Update display with current run data
            pass


__all__ = ["DragRacingTab"]



