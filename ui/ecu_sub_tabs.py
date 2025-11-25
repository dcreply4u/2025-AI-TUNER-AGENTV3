"""
ECU Sub-Tabs
Sub-tabs within the ECU Tuning tab for different ECU functions
"""

from __future__ import annotations

from typing import Dict, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTabWidget,
    QGroupBox,
    QDoubleSpinBox,
    QSpinBox,
    QCheckBox,
    QComboBox,
    QGridLayout,
)

from ui.ecu_tuning_widgets import (
    AnalogGauge,
    VETableWidget,
    RealTimeGraph,
    CellWeightingWidget,
    StatisticsPanel,
)


class IgnitionTimingTab(QWidget):
    """Ignition timing map sub-tab."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup ignition timing tab."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Control bar
        control_bar = self._create_control_bar("Ignition Timing Map Control Panel")
        main_layout.addWidget(control_bar)
        
        # Content layout
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        
        # Left: Gauges
        left_panel = self._create_gauges_panel()
        content_layout.addWidget(left_panel, stretch=0)
        
        # Center: Timing table
        center_panel = self._create_timing_table()
        content_layout.addWidget(center_panel, stretch=3)
        
        # Right: Settings
        right_panel = self._create_right_panel()
        content_layout.addWidget(right_panel, stretch=1)
        
        main_layout.addLayout(content_layout, stretch=1)
        
        # Bottom graph
        self.realtime_graph = RealTimeGraph()
        main_layout.addWidget(self.realtime_graph, stretch=1)
        
    def _create_control_bar(self, title: str) -> QWidget:
        """Create control bar."""
        bar = QWidget()
        bar.setStyleSheet("background-color: #2a2a2a; padding: 5px; border: 1px solid #404040;")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 5, 10, 5)
        
        fps_label = QLabel("21.6 fps")
        fps_label.setStyleSheet("font-size: 10px; color: #ffffff;")
        layout.addWidget(fps_label)
        
        layout.addStretch()
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        buttons = ["Update Controller", "Send", "Burn", "Active", "Stop"]
        for btn_text in buttons:
            btn = QPushButton(btn_text)
            if btn_text == "Active":
                btn.setStyleSheet("background-color: #ff0000; color: #ffffff; padding: 5px 10px; font-weight: bold;")
            else:
                btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 5px 10px;")
            layout.addWidget(btn)
            
        return bar
        
    def _create_gauges_panel(self) -> QWidget:
        """Create gauges panel."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        panel.setMaximumWidth(250)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Timing Advance gauge
        self.timing_gauge = AnalogGauge(
            "Timing Advance",
            min_value=-20,
            max_value=50,
            unit="deg",
        )
        layout.addWidget(self.timing_gauge)
        
        # Knock Retard gauge
        self.knock_gauge = AnalogGauge(
            "Knock Retard",
            min_value=0,
            max_value=10,
            unit="deg",
            warning_start=5,
            warning_end=10,
            warning_color="#ff0000",
        )
        layout.addWidget(self.knock_gauge)
        
        # Base Timing gauge
        self.base_gauge = AnalogGauge(
            "Base Timing",
            min_value=0,
            max_value=40,
            unit="deg",
        )
        layout.addWidget(self.base_gauge)
        
        layout.addStretch()
        return panel
        
    def _create_timing_table(self) -> QWidget:
        """Create ignition timing table."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Ignition Timing Map")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Create timing table
        self.table = QTableWidget()
        self.table.setRowCount(16)
        self.table.setColumnCount(12)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setMinimumHeight(400)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #404040;
            }
        """)
        
        # Initialize table
        rpm_values = [800, 1100, 1400, 1700, 2000, 2500, 3000, 3500, 4000, 5000, 6000, 7000]
        for col, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setHorizontalHeaderItem(col, item)
        
        map_values = [100, 95, 90, 85, 80, 75, 70, 65, 60, 55, 50, 45, 40, 35, 30, 25]
        for row, map_val in enumerate(map_values):
            item = QTableWidgetItem(f"{map_val}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setVerticalHeaderItem(row, item)
        
        # Fill with timing values
        import random
        for row in range(16):
            for col in range(12):
                timing = 10 + (rpm_values[col] / 1000) * 5 + (map_values[row] / 100) * 10
                timing = max(5, min(45, timing))
                item = QTableWidgetItem(f"{timing:.1f}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                # Color code
                if timing > 35:
                    item.setBackground(QBrush(QColor("#ff0000")))  # Red
                elif timing > 25:
                    item.setBackground(QBrush(QColor("#ff8000")))  # Orange
                elif timing > 15:
                    item.setBackground(QBrush(QColor("#0080ff")))  # Blue
                else:
                    item.setBackground(QBrush(QColor("#00ff00")))  # Green
                
                self.table.setItem(row, col, item)
        
        layout.addWidget(self.table)
        return panel
        
    def _create_right_panel(self) -> QWidget:
        """Create right panel."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        panel.setMaximumWidth(200)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Settings group
        settings_group = QGroupBox("Timing Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        settings_layout = QVBoxLayout()
        
        settings_layout.addWidget(QLabel("Base Timing:"))
        self.base_timing = QDoubleSpinBox()
        self.base_timing.setRange(0, 40)
        self.base_timing.setValue(10)
        self.base_timing.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.base_timing)
        
        settings_layout.addWidget(QLabel("Max Advance:"))
        self.max_advance = QDoubleSpinBox()
        self.max_advance.setRange(0, 50)
        self.max_advance.setValue(35)
        self.max_advance.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.max_advance)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Visualization
        self.weighting_widget = CellWeightingWidget("Timing Weighting")
        layout.addWidget(self.weighting_widget)
        
        layout.addStretch()
        return panel
        
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update with telemetry data."""
        timing = data.get("ignition_timing", data.get("timing_advance", 15))
        knock = data.get("knock_retard", 0)
        base = data.get("base_timing", 10)
        
        self.timing_gauge.set_value(timing)
        self.knock_gauge.set_value(knock)
        self.base_gauge.set_value(base)
        
        rpm = data.get("RPM", data.get("Engine_RPM", 0))
        map_val = data.get("Boost_Pressure", 0) * 6.895
        afr = data.get("AFR", 14.7)
        ego = timing / 2
        self.realtime_graph.update_data(rpm, map_val, afr, ego)


class IdleControlTab(QWidget):
    """Idle control sub-tab."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup idle control tab."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Control bar
        control_bar = self._create_control_bar("Idle Control Panel")
        main_layout.addWidget(control_bar)
        
        # Content layout
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        
        # Left: Gauges
        left_panel = self._create_gauges_panel()
        content_layout.addWidget(left_panel, stretch=0)
        
        # Center: Idle table
        center_panel = self._create_idle_table()
        content_layout.addWidget(center_panel, stretch=3)
        
        # Right: Settings
        right_panel = self._create_right_panel()
        content_layout.addWidget(right_panel, stretch=1)
        
        main_layout.addLayout(content_layout, stretch=1)
        
    def _create_control_bar(self, title: str) -> QWidget:
        """Create control bar."""
        bar = QWidget()
        bar.setStyleSheet("background-color: #2a2a2a; padding: 5px; border: 1px solid #404040;")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 5, 10, 5)
        
        layout.addStretch()
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title_label)
        layout.addStretch()
        
        return bar
        
    def _create_gauges_panel(self) -> QWidget:
        """Create gauges panel."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        panel.setMaximumWidth(250)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Idle RPM gauge
        self.idle_rpm_gauge = AnalogGauge(
            "Idle RPM",
            min_value=0,
            max_value=2000,
            unit="RPM",
        )
        layout.addWidget(self.idle_rpm_gauge)
        
        # IAC Position gauge
        self.iac_gauge = AnalogGauge(
            "IAC Position",
            min_value=0,
            max_value=100,
            unit="%",
        )
        layout.addWidget(self.iac_gauge)
        
        layout.addStretch()
        return panel
        
    def _create_idle_table(self) -> QWidget:
        """Create idle control table."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Idle Control Map (RPM vs Coolant Temp)")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        self.table = QTableWidget()
        self.table.setRowCount(10)
        self.table.setColumnCount(8)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setMinimumHeight(300)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #404040;
            }
        """)
        
        # Initialize table
        temp_values = [0, 20, 40, 60, 80, 100, 120, 140]
        for col, temp in enumerate(temp_values):
            item = QTableWidgetItem(f"{temp}°F")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setHorizontalHeaderItem(col, item)
        
        load_values = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]
        for row, load in enumerate(load_values):
            item = QTableWidgetItem(f"{load}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setVerticalHeaderItem(row, item)
        
        # Fill with idle RPM values
        for row in range(10):
            for col in range(8):
                idle_rpm = 800 + (temp_values[col] / 140) * 400 - (load_values[row] / 10)
                idle_rpm = max(600, min(1500, idle_rpm))
                item = QTableWidgetItem(f"{int(idle_rpm)}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                item.setBackground(QBrush(QColor("#0080ff")))
                self.table.setItem(row, col, item)
        
        layout.addWidget(self.table)
        return panel
        
    def _create_right_panel(self) -> QWidget:
        """Create right panel with idle control settings including E-Throttle and VANOS/VVTi."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        panel.setMaximumWidth(300)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Idle Control Method
        method_group = QGroupBox("Idle Control Method")
        method_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        method_layout = QVBoxLayout()
        
        self.idle_method = QComboBox()
        self.idle_method.addItems([
            "E-Throttle",
            "Idle Solenoid",
            "Stepper Motor",
            "Ignition Timing"
        ])
        self.idle_method.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        method_layout.addWidget(self.idle_method)
        
        method_group.setLayout(method_layout)
        layout.addWidget(method_group)
        
        # Closed Loop Anti-Stall
        antistall_group = QGroupBox("Closed Loop Anti-Stall")
        antistall_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        antistall_layout = QVBoxLayout()
        
        self.antistall_enabled = QCheckBox("Anti-Stall Enabled")
        self.antistall_enabled.setChecked(True)
        self.antistall_enabled.setStyleSheet("color: #ffffff;")
        antistall_layout.addWidget(self.antistall_enabled)
        
        antistall_layout.addWidget(QLabel("Min RPM Threshold:"))
        self.antistall_rpm = QSpinBox()
        self.antistall_rpm.setRange(300, 1000)
        self.antistall_rpm.setValue(500)
        self.antistall_rpm.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        antistall_layout.addWidget(self.antistall_rpm)
        
        antistall_layout.addWidget(QLabel("Correction Rate (%/s):"))
        self.antistall_rate = QDoubleSpinBox()
        self.antistall_rate.setRange(0, 100)
        self.antistall_rate.setValue(10)
        self.antistall_rate.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        antistall_layout.addWidget(self.antistall_rate)
        
        antistall_group.setLayout(antistall_layout)
        layout.addWidget(antistall_group)
        
        # E-Throttle Settings
        ethrottle_group = QGroupBox("E-Throttle Settings")
        ethrottle_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        ethrottle_layout = QVBoxLayout()
        
        ethrottle_layout.addWidget(QLabel("Min Position (%):"))
        self.ethrottle_min = QDoubleSpinBox()
        self.ethrottle_min.setRange(0, 20)
        self.ethrottle_min.setValue(2)
        self.ethrottle_min.setSuffix("%")
        self.ethrottle_min.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        ethrottle_layout.addWidget(self.ethrottle_min)
        
        ethrottle_layout.addWidget(QLabel("Max Position (%):"))
        self.ethrottle_max = QDoubleSpinBox()
        self.ethrottle_max.setRange(0, 30)
        self.ethrottle_max.setValue(8)
        self.ethrottle_max.setSuffix("%")
        self.ethrottle_max.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        ethrottle_layout.addWidget(self.ethrottle_max)
        
        ethrottle_group.setLayout(ethrottle_layout)
        layout.addWidget(ethrottle_group)
        
        # VANOS/VVTi Support
        vanos_group = QGroupBox("VANOS/VVTi Support")
        vanos_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        vanos_layout = QVBoxLayout()
        
        self.vanos_enabled = QCheckBox("VANOS/VVTi Enabled")
        self.vanos_enabled.setStyleSheet("color: #ffffff;")
        vanos_layout.addWidget(self.vanos_enabled)
        
        vanos_layout.addWidget(QLabel("Control Type:"))
        self.vanos_type = QComboBox()
        self.vanos_type.addItems(["VANOS (BMW)", "VVTi (Toyota)", "Generic"])
        self.vanos_type.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        vanos_layout.addWidget(self.vanos_type)
        
        vanos_layout.addWidget(QLabel("Advance Range (deg):"))
        self.vanos_range = QDoubleSpinBox()
        self.vanos_range.setRange(0, 60)
        self.vanos_range.setValue(30)
        self.vanos_range.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        vanos_layout.addWidget(self.vanos_range)
        
        vanos_group.setLayout(vanos_layout)
        layout.addWidget(vanos_group)
        
        # Basic Idle Settings
        settings_group = QGroupBox("Idle Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        settings_layout = QVBoxLayout()
        
        settings_layout.addWidget(QLabel("Target Idle RPM:"))
        self.target_idle = QSpinBox()
        self.target_idle.setRange(600, 1500)
        self.target_idle.setValue(800)
        self.target_idle.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.target_idle)
        
        settings_layout.addWidget(QLabel("IAC Steps:"))
        self.iac_steps = QSpinBox()
        self.iac_steps.setRange(0, 255)
        self.iac_steps.setValue(50)
        self.iac_steps.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.iac_steps)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        return panel
        
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update with telemetry data."""
        idle_rpm = data.get("idle_rpm", data.get("RPM", 800))
        iac = data.get("iac_position", 50)
        
        self.idle_rpm_gauge.set_value(idle_rpm)
        self.iac_gauge.set_value(iac)


class BoostControlTab(QWidget):
    """Boost control sub-tab."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup boost control tab."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Control bar
        control_bar = self._create_control_bar("Boost Control Panel")
        main_layout.addWidget(control_bar)
        
        # Content layout
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        
        # Left: Gauges
        left_panel = self._create_gauges_panel()
        content_layout.addWidget(left_panel, stretch=0)
        
        # Center: Tabbed maps and tables
        center_panel = self._create_center_tabs()
        content_layout.addWidget(center_panel, stretch=3)
        
        # Right: Settings
        right_panel = self._create_right_panel()
        content_layout.addWidget(right_panel, stretch=1)
        
        main_layout.addLayout(content_layout, stretch=1)
        
        # Bottom: Real-time monitoring graphs
        graphs_panel = self._create_graphs_panel()
        main_layout.addWidget(graphs_panel, stretch=1)
        
    def _create_control_bar(self, title: str) -> QWidget:
        """Create control bar."""
        bar = QWidget()
        bar.setStyleSheet("background-color: #2a2a2a; padding: 5px; border: 1px solid #404040;")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 5, 10, 5)
        
        layout.addStretch()
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title_label)
        layout.addStretch()
        
        return bar
        
    def _create_gauges_panel(self) -> QWidget:
        """Create gauges panel."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        panel.setMaximumWidth(250)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Boost Target gauge
        self.boost_target_gauge = AnalogGauge(
            "Boost Target",
            min_value=0,
            max_value=50,
            unit="psi",
            warning_start=40,
            warning_end=50,
            warning_color="#ff0000",
        )
        layout.addWidget(self.boost_target_gauge)
        
        # Wastegate Duty gauge
        self.wastegate_gauge = AnalogGauge(
            "Wastegate Duty",
            min_value=0,
            max_value=100,
            unit="%",
        )
        layout.addWidget(self.wastegate_gauge)
        
        # Turbo Speed gauge
        self.turbo_speed_gauge = AnalogGauge(
            "Turbo Speed",
            min_value=0,
            max_value=200000,
            unit="RPM",
        )
        layout.addWidget(self.turbo_speed_gauge)
        
        # AFR gauge
        self.afr_gauge = AnalogGauge(
            "AFR",
            min_value=10,
            max_value=18,
            unit="",
        )
        layout.addWidget(self.afr_gauge)
        
        layout.addStretch()
        return panel
        
    def _create_center_tabs(self) -> QWidget:
        """Create center panel with tabbed maps."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.center_tabs = QTabWidget()
        self.center_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 6px 15px;
                margin-right: 2px;
                border: 1px solid #404040;
                font-size: 10px;
            }
            QTabBar::tab:selected {
                background-color: #1a1a1a;
                border-bottom: 2px solid #0080ff;
            }
        """)
        
        # Target Boost Map (existing)
        self.center_tabs.addTab(self._create_boost_table(), "Target Boost")
        
        # Wastegate Duty Cycle Map (new)
        self.center_tabs.addTab(self._create_wastegate_duty_table(), "Wastegate Duty")
        
        # Boost by Gear Map (new)
        self.center_tabs.addTab(self._create_boost_by_gear_table(), "Boost by Gear")
        
        # AFR Targets Map (new)
        self.center_tabs.addTab(self._create_afr_targets_table(), "AFR Targets")
        
        # Ignition Timing Map (new)
        self.center_tabs.addTab(self._create_ignition_timing_table(), "Ignition Timing")
        
        # Compressor Map Overlay (new)
        self.center_tabs.addTab(self._create_compressor_map_overlay(), "Compressor Map")
        
        layout.addWidget(self.center_tabs)
        return panel
    
    def _create_boost_table(self) -> QWidget:
        """Create boost control table."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Target Boost Map (vs RPM & TPS/MAP)")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        self.table = QTableWidget()
        self.table.setRowCount(8)
        self.table.setColumnCount(10)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setMinimumHeight(300)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #404040;
            }
        """)
        
        # Initialize table
        rpm_values = [2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 7000]
        for col, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setHorizontalHeaderItem(col, item)
        
        throttle_values = [30, 40, 50, 60, 70, 80, 90, 100]
        for row, throttle in enumerate(throttle_values):
            item = QTableWidgetItem(f"{throttle}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setVerticalHeaderItem(row, item)
        
        # Fill with boost values
        for row in range(8):
            for col in range(10):
                boost = (throttle_values[row] / 100) * 30 + (rpm_values[col] / 7000) * 10
                boost = max(0, min(50, boost))
                item = QTableWidgetItem(f"{boost:.1f}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if boost > 40:
                    item.setBackground(QBrush(QColor("#ff0000")))
                elif boost > 30:
                    item.setBackground(QBrush(QColor("#ff8000")))
                elif boost > 20:
                    item.setBackground(QBrush(QColor("#0080ff")))
                else:
                    item.setBackground(QBrush(QColor("#00ff00")))
                
                self.table.setItem(row, col, item)
        
        layout.addWidget(self.table)
        return panel
    
    def _create_wastegate_duty_table(self) -> QWidget:
        """Create wastegate duty cycle map."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Wastegate Duty Cycle Map (vs RPM & TPS/MAP)")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        table = QTableWidget()
        table.setRowCount(8)
        table.setColumnCount(10)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(300)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #404040;
            }
        """)
        
        rpm_values = [2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 7000]
        for col, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        throttle_values = [30, 40, 50, 60, 70, 80, 90, 100]
        for row, throttle in enumerate(throttle_values):
            item = QTableWidgetItem(f"{throttle}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with duty cycle values (0-100%)
        for row in range(8):
            for col in range(10):
                duty = (throttle_values[row] / 100) * 80 + (rpm_values[col] / 7000) * 20
                duty = max(0, min(100, duty))
                item = QTableWidgetItem(f"{duty:.0f}%")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if duty > 80:
                    item.setBackground(QBrush(QColor("#ff0000")))
                elif duty > 60:
                    item.setBackground(QBrush(QColor("#ff8000")))
                elif duty > 40:
                    item.setBackground(QBrush(QColor("#0080ff")))
                else:
                    item.setBackground(QBrush(QColor("#00ff00")))
                
                table.setItem(row, col, item)
        
        layout.addWidget(table)
        return panel
    
    def _create_boost_by_gear_table(self) -> QWidget:
        """Create boost by gear table."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Boost by Gear (vs RPM)")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        table = QTableWidget()
        table.setRowCount(6)  # Gears 1-6
        table.setColumnCount(10)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(300)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #404040;
            }
        """)
        
        rpm_values = [2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 7000]
        for col, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        gear_values = [1, 2, 3, 4, 5, 6]
        for row, gear in enumerate(gear_values):
            item = QTableWidgetItem(f"Gear {gear}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with boost values (lower in 1st/2nd, higher in 3rd+)
        for row in range(6):
            for col in range(10):
                base_boost = 15 + (rpm_values[col] / 7000) * 15
                # Reduce boost in lower gears for traction
                if gear_values[row] <= 2:
                    boost = base_boost * 0.6  # 60% in 1st/2nd
                elif gear_values[row] == 3:
                    boost = base_boost * 0.8  # 80% in 3rd
                else:
                    boost = base_boost  # Full boost in 4th+
                boost = max(0, min(50, boost))
                
                item = QTableWidgetItem(f"{boost:.1f}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if boost > 40:
                    item.setBackground(QBrush(QColor("#ff0000")))
                elif boost > 30:
                    item.setBackground(QBrush(QColor("#ff8000")))
                elif boost > 20:
                    item.setBackground(QBrush(QColor("#0080ff")))
                else:
                    item.setBackground(QBrush(QColor("#00ff00")))
                
                table.setItem(row, col, item)
        
        layout.addWidget(table)
        return panel
    
    def _create_afr_targets_table(self) -> QWidget:
        """Create AFR targets table (progressive enrichment with boost)."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("AFR Targets (vs Boost & RPM) - Progressive Enrichment")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        table = QTableWidget()
        table.setRowCount(8)  # Boost levels
        table.setColumnCount(10)  # RPM
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(300)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #404040;
            }
        """)
        
        rpm_values = [2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 7000]
        for col, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        boost_values = [5, 10, 15, 20, 25, 30, 35, 40]
        for row, boost in enumerate(boost_values):
            item = QTableWidgetItem(f"{boost}psi")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with AFR values (richer as boost increases)
        for row in range(8):
            for col in range(10):
                base_afr = 14.7
                # Richer at higher boost and RPM
                afr = base_afr - (boost_values[row] / 40) * 3.0 - (rpm_values[col] / 7000) * 0.5
                afr = max(10.0, min(14.7, afr))  # Range: 10.0 (rich) to 14.7 (stoich)
                
                item = QTableWidgetItem(f"{afr:.2f}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if afr < 11.5:
                    item.setBackground(QBrush(QColor("#ff0000")))  # Very rich
                elif afr < 12.5:
                    item.setBackground(QBrush(QColor("#ff8000")))  # Rich
                elif afr < 13.5:
                    item.setBackground(QBrush(QColor("#0080ff")))  # Moderate
                else:
                    item.setBackground(QBrush(QColor("#00ff00")))  # Lean
                
                table.setItem(row, col, item)
        
        layout.addWidget(table)
        return panel
    
    def _create_ignition_timing_table(self) -> QWidget:
        """Create ignition timing table (retarded with boost)."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Ignition Timing Advance (vs MAP & RPM) - Boost Retard")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        table = QTableWidget()
        table.setRowCount(8)  # MAP/Boost levels
        table.setColumnCount(10)  # RPM
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(300)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #404040;
            }
        """)
        
        rpm_values = [2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 7000]
        for col, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        map_values = [50, 75, 100, 125, 150, 175, 200, 225]  # kPa (includes boost)
        for row, map_val in enumerate(map_values):
            item = QTableWidgetItem(f"{map_val}kPa")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with timing values (retarded as MAP/boost increases)
        for row in range(8):
            for col in range(10):
                base_timing = 30.0  # Base advance
                # Retard with boost, advance with RPM
                timing = base_timing + (rpm_values[col] / 7000) * 10 - ((map_values[row] - 100) / 100) * 8
                timing = max(5.0, min(40.0, timing))  # Range: 5-40 degrees
                
                item = QTableWidgetItem(f"{timing:.1f}°")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if timing < 10:
                    item.setBackground(QBrush(QColor("#ff0000")))  # Very retarded
                elif timing < 20:
                    item.setBackground(QBrush(QColor("#ff8000")))  # Retarded
                elif timing < 30:
                    item.setBackground(QBrush(QColor("#0080ff")))  # Moderate
                else:
                    item.setBackground(QBrush(QColor("#00ff00")))  # Advanced
                
                table.setItem(row, col, item)
        
        layout.addWidget(table)
        return panel
    
    def _create_compressor_map_overlay(self) -> QWidget:
        """Create compressor map overlay visualization."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Turbo Compressor Map Overlay (Pressure Ratio vs Mass Flow)")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Info label
        info_label = QLabel("Operating points displayed on compressor efficiency map. Green = Optimal, Blue = Acceptable, Red = Surge/Choke")
        info_label.setStyleSheet("font-size: 10px; color: #888888;")
        layout.addWidget(info_label)
        
        # Use RealTimeGraph for compressor map visualization
        compressor_graph = RealTimeGraph()
        compressor_graph.setMinimumHeight(400)
        compressor_graph.setStyleSheet("""
            QWidget {
                background-color: #0a0a0a;
                border: 1px solid #404040;
            }
        """)
        
        # Note: In a full implementation, this would show:
        # - Compressor efficiency islands (contour lines)
        # - Surge line (left boundary)
        # - Choke line (right boundary)
        # - Current operating point (from mass flow and pressure ratio)
        # - Safe operating envelope
        
        layout.addWidget(compressor_graph)
        self.compressor_map_graph = compressor_graph
        
        # Settings for compressor map
        settings_layout = QHBoxLayout()
        
        settings_layout.addWidget(QLabel("Turbo Model:"))
        self.turbo_model = QComboBox()
        self.turbo_model.addItems(["Generic", "Garrett GT2860RS", "Garrett GT3076R", "BorgWarner EFR", "Custom"])
        self.turbo_model.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.turbo_model)
        
        settings_layout.addWidget(QLabel("Max RPM:"))
        self.turbo_max_rpm = QSpinBox()
        self.turbo_max_rpm.setRange(50000, 300000)
        self.turbo_max_rpm.setValue(150000)
        self.turbo_max_rpm.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.turbo_max_rpm)
        
        self.show_efficiency_islands = QCheckBox("Show Efficiency Islands")
        self.show_efficiency_islands.setChecked(True)
        self.show_efficiency_islands.setStyleSheet("color: #ffffff;")
        settings_layout.addWidget(self.show_efficiency_islands)
        
        self.show_surge_choke = QCheckBox("Show Surge/Choke Lines")
        self.show_surge_choke.setChecked(True)
        self.show_surge_choke.setStyleSheet("color: #ffffff;")
        settings_layout.addWidget(self.show_surge_choke)
        
        settings_layout.addStretch()
        layout.addLayout(settings_layout)
        
        return panel
        
    def _create_right_panel(self) -> QWidget:
        """Create right panel."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        panel.setMaximumWidth(200)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        settings_group = QGroupBox("Boost Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        settings_layout = QVBoxLayout()
        
        # Boost Control Mode
        mode_group = QGroupBox("Boost Control Mode")
        mode_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        mode_layout = QVBoxLayout()
        
        self.boost_mode = QComboBox()
        self.boost_mode.addItems(["Closed Loop", "Open Loop"])
        self.boost_mode.setCurrentIndex(0)
        self.boost_mode.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        mode_layout.addWidget(self.boost_mode)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # Boost Level Switching
        level_group = QGroupBox("Boost Level Switching")
        level_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        level_layout = QVBoxLayout()
        
        self.boost_level_enabled = QCheckBox("Boost Level Switching Enabled")
        self.boost_level_enabled.setStyleSheet("color: #ffffff;")
        level_layout.addWidget(self.boost_level_enabled)
        
        level_layout.addWidget(QLabel("Digital Input:"))
        self.boost_level_input = QComboBox()
        self.boost_level_input.addItems(["Input 1", "Input 2", "Input 3", "Input 4"])
        self.boost_level_input.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        level_layout.addWidget(self.boost_level_input)
        
        level_layout.addWidget(QLabel("Low Boost Level (psi):"))
        self.boost_low = QDoubleSpinBox()
        self.boost_low.setRange(0, 50)
        self.boost_low.setValue(15)
        self.boost_low.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        level_layout.addWidget(self.boost_low)
        
        level_layout.addWidget(QLabel("High Boost Level (psi):"))
        self.boost_high = QDoubleSpinBox()
        self.boost_high.setRange(0, 50)
        self.boost_high.setValue(25)
        self.boost_high.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        level_layout.addWidget(self.boost_high)
        
        level_group.setLayout(level_layout)
        layout.addWidget(level_group)
        
        # Compensation Tables Sub-Tab
        comp_tabs = QTabWidget()
        comp_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px 15px;
                margin-right: 2px;
                border: 1px solid #404040;
            }
            QTabBar::tab:selected {
                background-color: #1a1a1a;
                border-bottom: 2px solid #0080ff;
            }
        """)
        
        # IAT Compensation
        iat_tab = self._create_compensation_tab("IAT Compensation", "IAT (°C)", "Boost Add (psi)")
        comp_tabs.addTab(iat_tab, "IAT")
        
        # Gear Compensation
        gear_tab = self._create_compensation_tab("Gear Compensation", "Gear", "Boost Add (psi)")
        comp_tabs.addTab(gear_tab, "Gear")
        
        # EGT Compensation
        egt_tab = self._create_compensation_tab("EGT Compensation", "EGT (°C)", "Boost Add (psi)")
        comp_tabs.addTab(egt_tab, "EGT")
        
        layout.addWidget(comp_tabs, stretch=1)
        
        # Boost Ramp Rate / Turbo Lag Reduction
        ramp_group = QGroupBox("Boost Ramp Rate / Turbo Lag Reduction")
        ramp_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        ramp_layout = QVBoxLayout()
        
        ramp_layout.addWidget(QLabel("Ramp Rate (psi/sec):"))
        self.ramp_rate = QDoubleSpinBox()
        self.ramp_rate.setRange(0.1, 50.0)
        self.ramp_rate.setValue(5.0)
        self.ramp_rate.setSingleStep(0.5)
        self.ramp_rate.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        ramp_layout.addWidget(self.ramp_rate)
        
        ramp_layout.addWidget(QLabel("Initial Boost Target (psi):"))
        self.initial_boost = QDoubleSpinBox()
        self.initial_boost.setRange(0, 30)
        self.initial_boost.setValue(10)
        self.initial_boost.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        ramp_layout.addWidget(self.initial_boost)
        
        self.anti_lag_enabled = QCheckBox("Anti-Lag Enabled")
        self.anti_lag_enabled.setStyleSheet("color: #ffffff;")
        ramp_layout.addWidget(self.anti_lag_enabled)
        
        ramp_group.setLayout(ramp_layout)
        layout.addWidget(ramp_group)
        
        # Throttle Response Curves
        throttle_group = QGroupBox("Throttle Response / Curves")
        throttle_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        throttle_layout = QVBoxLayout()
        
        throttle_layout.addWidget(QLabel("Response Mode:"))
        self.throttle_mode = QComboBox()
        self.throttle_mode.addItems(["Linear", "Aggressive", "Smooth", "Custom"])
        self.throttle_mode.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        throttle_layout.addWidget(self.throttle_mode)
        
        throttle_layout.addWidget(QLabel("Response Factor:"))
        self.throttle_factor = QDoubleSpinBox()
        self.throttle_factor.setRange(0.1, 3.0)
        self.throttle_factor.setValue(1.0)
        self.throttle_factor.setSingleStep(0.1)
        self.throttle_factor.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        throttle_layout.addWidget(self.throttle_factor)
        
        throttle_group.setLayout(throttle_layout)
        layout.addWidget(throttle_group)
        
        # Altitude Compensation
        altitude_group = QGroupBox("Altitude Compensation")
        altitude_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        altitude_layout = QVBoxLayout()
        
        self.altitude_comp_enabled = QCheckBox("Altitude Compensation Enabled")
        self.altitude_comp_enabled.setChecked(True)
        self.altitude_comp_enabled.setStyleSheet("color: #ffffff;")
        altitude_layout.addWidget(self.altitude_comp_enabled)
        
        altitude_layout.addWidget(QLabel("Current Altitude (ft):"))
        self.current_altitude = QSpinBox()
        self.current_altitude.setRange(-500, 15000)
        self.current_altitude.setValue(0)
        self.current_altitude.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        altitude_layout.addWidget(self.current_altitude)
        
        altitude_layout.addWidget(QLabel("Barometric Pressure (kPa):"))
        self.baro_pressure = QDoubleSpinBox()
        self.baro_pressure.setRange(50, 110)
        self.baro_pressure.setValue(101.3)
        self.baro_pressure.setDecimals(1)
        self.baro_pressure.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        altitude_layout.addWidget(self.baro_pressure)
        
        altitude_group.setLayout(altitude_layout)
        layout.addWidget(altitude_group)
        
        # Safety Limits / Fail-safes
        safety_group = QGroupBox("Safety Limits / Fail-safes")
        safety_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        safety_layout = QVBoxLayout()
        
        safety_layout.addWidget(QLabel("Max Boost (psi):"))
        self.max_boost_limit = QDoubleSpinBox()
        self.max_boost_limit.setRange(0, 60)
        self.max_boost_limit.setValue(45)
        self.max_boost_limit.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        safety_layout.addWidget(self.max_boost_limit)
        
        safety_layout.addWidget(QLabel("Max Coolant Temp (°C):"))
        self.max_coolant_temp = QSpinBox()
        self.max_coolant_temp.setRange(80, 130)
        self.max_coolant_temp.setValue(110)
        self.max_coolant_temp.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        safety_layout.addWidget(self.max_coolant_temp)
        
        safety_layout.addWidget(QLabel("Max IAT (°C):"))
        self.max_iat = QSpinBox()
        self.max_iat.setRange(30, 100)
        self.max_iat.setValue(70)
        self.max_iat.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        safety_layout.addWidget(self.max_iat)
        
        safety_layout.addWidget(QLabel("Min Oil Pressure (psi):"))
        self.min_oil_pressure = QDoubleSpinBox()
        self.min_oil_pressure.setRange(0, 100)
        self.min_oil_pressure.setValue(20)
        self.min_oil_pressure.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        safety_layout.addWidget(self.min_oil_pressure)
        
        safety_layout.addWidget(QLabel("Protection Action:"))
        self.protection_action = QComboBox()
        self.protection_action.addItems(["Reduce Boost", "Cut Fuel", "Cut Ignition", "Reduce Boost + Retard Timing"])
        self.protection_action.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        safety_layout.addWidget(self.protection_action)
        
        safety_group.setLayout(safety_layout)
        layout.addWidget(safety_group)
        
        layout.addStretch()
        return panel
        
    def _create_compensation_tab(self, title: str, x_label: str, y_label: str) -> QWidget:
        """Create a compensation table tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title_label)
        
        comp_table = QTableWidget()
        comp_table.setRowCount(6)
        comp_table.setColumnCount(5)
        comp_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        comp_table.setMaximumHeight(200)
        comp_table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
            }
        """)
        
        # Initialize table headers based on type
        if "IAT" in title:
            x_values = [0, 20, 40, 60, 80]
            for col, val in enumerate(x_values):
                item = QTableWidgetItem(f"{val}°C")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                comp_table.setHorizontalHeaderItem(col, item)
        elif "Gear" in title:
            x_values = [1, 2, 3, 4, 5]
            for col, val in enumerate(x_values):
                item = QTableWidgetItem(f"G{val}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                comp_table.setHorizontalHeaderItem(col, item)
        else:  # EGT
            x_values = [600, 700, 800, 900, 1000]
            for col, val in enumerate(x_values):
                item = QTableWidgetItem(f"{val}°C")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                comp_table.setHorizontalHeaderItem(col, item)
        
        rpm_values = [2000, 3000, 4000, 5000, 6000, 7000]
        for row, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            comp_table.setVerticalHeaderItem(row, item)
        
        # Fill with compensation values
        for row in range(6):
            for col in range(5):
                comp_val = (row * 0.5) + (col * 0.3)
                item = QTableWidgetItem(f"{comp_val:.1f}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                if comp_val > 2.0:
                    item.setBackground(QBrush(QColor("#ff0000")))
                elif comp_val > 1.0:
                    item.setBackground(QBrush(QColor("#ff8000")))
                else:
                    item.setBackground(QBrush(QColor("#0080ff")))
                comp_table.setItem(row, col, item)
        
        layout.addWidget(comp_table)
        return tab
        
    def _create_graphs_panel(self) -> QWidget:
        """Create real-time monitoring graphs panel."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Real-Time Monitoring Graphs")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Create tabbed graphs
        graph_tabs = QTabWidget()
        graph_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px 12px;
                margin-right: 2px;
                border: 1px solid #404040;
                font-size: 10px;
            }
            QTabBar::tab:selected {
                background-color: #1a1a1a;
                border-bottom: 2px solid #0080ff;
            }
        """)
        
        # Boost vs Time/RPM graph
        boost_graph = RealTimeGraph()
        boost_graph.setMinimumHeight(200)
        graph_tabs.addTab(boost_graph, "Boost vs Time/RPM")
        self.boost_graph = boost_graph
        
        # AFR vs Time/RPM graph
        afr_graph = RealTimeGraph()
        afr_graph.setMinimumHeight(200)
        graph_tabs.addTab(afr_graph, "AFR vs Time/RPM")
        self.afr_graph = afr_graph
        
        # Turbo Speed graph
        turbo_speed_graph = RealTimeGraph()
        turbo_speed_graph.setMinimumHeight(200)
        graph_tabs.addTab(turbo_speed_graph, "Turbo Speed")
        self.turbo_speed_graph = turbo_speed_graph
        
        # Multi-parameter graph
        multi_graph = RealTimeGraph()
        multi_graph.setMinimumHeight(200)
        graph_tabs.addTab(multi_graph, "Multi-Parameter")
        self.multi_graph = multi_graph
        
        layout.addWidget(graph_tabs)
        return panel
    
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update with telemetry data."""
        boost = data.get("Boost_Pressure", data.get("boost_psi", 0))
        wastegate = data.get("wastegate_duty", 50)
        turbo_speed = data.get("turbo_speed", 100000)
        afr = data.get("AFR", data.get("lambda_value", 1.0) * 14.7)
        rpm = data.get("RPM", data.get("Engine_RPM", 0))
        
        self.boost_target_gauge.set_value(boost)
        self.wastegate_gauge.set_value(wastegate)
        if hasattr(self, 'turbo_speed_gauge'):
            self.turbo_speed_gauge.set_value(turbo_speed)
        if hasattr(self, 'afr_gauge'):
            self.afr_gauge.set_value(afr)
        
        # Update graphs
        if hasattr(self, 'boost_graph'):
            map_val = boost * 6.895  # Convert to kPa
            self.boost_graph.update_data(rpm, map_val, boost, wastegate)
        
        if hasattr(self, 'afr_graph'):
            lambda_val = afr / 14.7
            self.afr_graph.update_data(rpm, lambda_val, afr, 0)
        
        if hasattr(self, 'turbo_speed_graph'):
            turbo_rpm = turbo_speed / 1000  # Normalize for display
            self.turbo_speed_graph.update_data(rpm, turbo_rpm, turbo_speed / 100, 0)
        
        if hasattr(self, 'multi_graph'):
            # Multi-parameter: RPM, Boost, AFR, Turbo Speed
            self.multi_graph.update_data(rpm, boost, afr, turbo_speed / 1000)


class FuelMapsTab(QWidget):
    """Fuel maps sub-tab (additional fuel tables)."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup fuel maps tab."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Control bar
        control_bar = self._create_control_bar("Fuel Maps Control Panel")
        main_layout.addWidget(control_bar)
        
        # Content layout
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        
        # Left: Gauges
        left_panel = self._create_gauges_panel()
        content_layout.addWidget(left_panel, stretch=0)
        
        # Center: Fuel map selector and table
        center_panel = self._create_fuel_maps()
        content_layout.addWidget(center_panel, stretch=3)
        
        # Right: Settings
        right_panel = self._create_right_panel()
        content_layout.addWidget(right_panel, stretch=1)
        
        main_layout.addLayout(content_layout, stretch=1)
        
    def _create_control_bar(self, title: str) -> QWidget:
        """Create control bar."""
        bar = QWidget()
        bar.setStyleSheet("background-color: #2a2a2a; padding: 5px; border: 1px solid #404040;")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 5, 10, 5)
        
        layout.addStretch()
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title_label)
        layout.addStretch()
        
        return bar
        
    def _create_gauges_panel(self) -> QWidget:
        """Create gauges panel."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        panel.setMaximumWidth(250)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # AFR Target gauge
        self.afr_gauge = AnalogGauge(
            "AFR Target",
            min_value=10,
            max_value=18,
            unit="",
        )
        layout.addWidget(self.afr_gauge)
        
        # Fuel Correction gauge
        self.correction_gauge = AnalogGauge(
            "Fuel Correction",
            min_value=-50,
            max_value=50,
            unit="%",
        )
        layout.addWidget(self.correction_gauge)
        
        layout.addStretch()
        return panel
        
    def _create_fuel_maps(self) -> QWidget:
        """Create fuel maps panel."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Map selector
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Fuel Map:"))
        self.map_selector = QComboBox()
        self.map_selector.addItems(["VE Table 1", "VE Table 2", "AFR Target", "Accel Enrichment", "Cold Start"])
        self.map_selector.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        selector_layout.addWidget(self.map_selector)
        selector_layout.addStretch()
        layout.addLayout(selector_layout)
        
        # Table (reuse VE table widget style)
        self.table = VETableWidget()
        layout.addWidget(self.table, stretch=1)
        
        return panel
        
    def _create_right_panel(self) -> QWidget:
        """Create right panel."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        panel.setMaximumWidth(200)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        settings_group = QGroupBox("Fuel Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        settings_layout = QVBoxLayout()
        
        settings_layout.addWidget(QLabel("AFR Target:"))
        self.afr_target = QDoubleSpinBox()
        self.afr_target.setRange(10, 18)
        self.afr_target.setValue(14.7)
        self.afr_target.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.afr_target)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        layout.addStretch()
        
        return panel
        
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update with telemetry data."""
        afr = data.get("AFR", data.get("lambda_value", 1.0) * 14.7)
        correction = data.get("fuel_correction", 0)
        
        self.afr_gauge.set_value(afr)
        self.correction_gauge.set_value(correction)


__all__ = [
    "IgnitionTimingTab",
    "IdleControlTab",
    "BoostControlTab",
    "FuelMapsTab",
]

