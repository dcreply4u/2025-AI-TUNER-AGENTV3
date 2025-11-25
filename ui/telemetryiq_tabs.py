"""
telemetryIQ Interface Tabs
Protections, Motorsport, and Transmission tabs
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
    QSlider,
    QLineEdit,
    QSizePolicy,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size

from ui.ecu_tuning_widgets import (
    AnalogGauge,
    RealTimeGraph,
    CellWeightingWidget,
)


class ProtectionsTab(QWidget):
    """Engine Protections tab with Lambda/EGT correction and protection settings."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup protections tab."""
        main_layout = QVBoxLayout(self)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # Control bar
        control_bar = self._create_control_bar()
        main_layout.addWidget(control_bar)
        
        # Content layout
        content_layout = QHBoxLayout()
        content_layout.setSpacing(get_scaled_size(15))
        
        # Left: Gauges with enhanced diagnostics
        left_panel = self._create_gauges_panel()
        content_layout.addWidget(left_panel, stretch=0)
        
        # Center: Lambda & EGT Correction tables
        center_panel = self._create_center_panel()
        content_layout.addWidget(center_panel, stretch=3)
        
        # Right: Engine Protections settings
        right_panel = self._create_right_panel()
        content_layout.addWidget(right_panel, stretch=1)
        
        main_layout.addLayout(content_layout, stretch=1)
        
        # Bottom: Advanced Features sub-panel
        advanced_panel = self._create_advanced_panel()
        main_layout.addWidget(advanced_panel, stretch=1)
        
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
        
        fps_label = QLabel("21.6 fps")
        fps_font = get_scaled_font_size(10)
        fps_label.setStyleSheet(f"font-size: {fps_font}px; color: #ffffff;")
        layout.addWidget(fps_label)
        
        layout.addStretch()
        
        title = QLabel("Engine Protections Control Panel")
        title_font = get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        buttons = ["Update Controller", "Send", "Burn", "Active", "Stop"]
        btn_padding_v = get_scaled_size(5)
        btn_padding_h = get_scaled_size(10)
        btn_font = get_scaled_font_size(11)
        for btn_text in buttons:
            btn = QPushButton(btn_text)
            btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            if btn_text == "Active":
                btn.setStyleSheet(f"background-color: #ff0000; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px; font-weight: bold; font-size: {btn_font}px;")
            else:
                btn.setStyleSheet(f"background-color: #404040; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px; font-size: {btn_font}px;")
            layout.addWidget(btn)
            
        return bar
        
    def _create_gauges_panel(self) -> QWidget:
        """Create left gauges panel with enhanced diagnostics."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        panel.setMaximumWidth(get_scaled_size(250))
        panel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(15)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # Engine RPM gauge
        self.rpm_gauge = AnalogGauge(
            "Engine RPM",
            min_value=0,
            max_value=8000,
            unit="RPM",
            warning_start=7500,
            warning_end=8000,
            warning_color="#ffaa00",
        )
        layout.addWidget(self.rpm_gauge)
        
        # Engine MAP gauge
        self.map_gauge = AnalogGauge(
            "Engine MAP",
            min_value=-80,
            max_value=240,
            unit="kPa",
            warning_start=200,
            warning_end=240,
            warning_color="#ff0000",
        )
        layout.addWidget(self.map_gauge)
        
        # Air:Fuel Ratio gauge
        self.afr_gauge = AnalogGauge(
            "Air:Fuel Ratio",
            min_value=10,
            max_value=18,
            unit="",
            warning_start=17,
            warning_end=18,
            warning_color="#ff0000",
        )
        layout.addWidget(self.afr_gauge)
        
        # Flex Fuel digital readout
        flex_group = QGroupBox("Flex Fuel")
        flex_group_font = get_scaled_font_size(11)
        flex_group_border = get_scaled_size(1)
        flex_group_radius = get_scaled_size(3)
        flex_group_margin = get_scaled_size(5)
        flex_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {flex_group_font}px; font-weight: bold; color: #ffffff;
                border: {flex_group_border}px solid #404040; border-radius: {flex_group_radius}px;
                margin-top: {flex_group_margin}px; padding-top: {flex_group_margin}px;
            }}
        """)
        flex_layout = QVBoxLayout()
        self.ethanol_label = QLabel("E85%: 72.4%")
        ethanol_font = get_scaled_font_size(14)
        ethanol_padding = get_scaled_size(5)
        self.ethanol_label.setStyleSheet(f"font-size: {ethanol_font}px; font-weight: bold; color: #00ff00; padding: {ethanol_padding}px;")
        flex_layout.addWidget(self.ethanol_label)
        flex_group.setLayout(flex_layout)
        layout.addWidget(flex_group)
        
        # EGT digital readout
        egt_group = QGroupBox("Exhaust Gas Temperature")
        egt_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {flex_group_font}px; font-weight: bold; color: #ffffff;
                border: {flex_group_border}px solid #404040; border-radius: {flex_group_radius}px;
                margin-top: {flex_group_margin}px; padding-top: {flex_group_margin}px;
            }}
        """)
        egt_layout = QVBoxLayout()
        self.egt_label = QLabel("EGT Cyl 1: 850 °C")
        self.egt_label.setStyleSheet(f"font-size: {ethanol_font}px; font-weight: bold; color: #ff8000; padding: {ethanol_padding}px;")
        egt_layout.addWidget(self.egt_label)
        egt_group.setLayout(egt_layout)
        layout.addWidget(egt_group)
        
        # Status Light Panel
        status_group = QGroupBox("Engine Protections Status")
        status_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {flex_group_font}px; font-weight: bold; color: #ffffff;
                border: {flex_group_border}px solid #404040; border-radius: {flex_group_radius}px;
                margin-top: {flex_group_margin}px; padding-top: {flex_group_margin}px;
            }}
        """)
        status_layout = QVBoxLayout()
        status_layout.setSpacing(get_scaled_size(5))
        
        # Status lights (store both widget and LED for updates)
        self.lean_cut_light, self.lean_cut_led = self._create_status_light("LEAN CUT", "#ff0000", False)
        status_layout.addWidget(self.lean_cut_light)
        
        self.egt_cut_light, self.egt_cut_led = self._create_status_light("EGT CUT", "#ff0000", False)
        status_layout.addWidget(self.egt_cut_light)
        
        self.rev_limit_light, self.rev_limit_led = self._create_status_light("REV LIMIT", "#ffaa00", False)
        status_layout.addWidget(self.rev_limit_light)
        
        self.lim_speed_light, self.lim_speed_led = self._create_status_light("LIM-SPEED", "#00ff00", True)
        status_layout.addWidget(self.lim_speed_light)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        layout.addStretch()
        return panel
        
    def _create_status_light(self, label: str, color: str, active: bool) -> tuple[QWidget, QLabel]:
        """Create a status light indicator. Returns (widget, led_label) for easy updates."""
        widget = QWidget()
        border = get_scaled_size(1)
        padding = get_scaled_size(3)
        widget.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040; padding: {padding}px;")
        layout = QHBoxLayout(widget)
        margin_h = get_scaled_size(5)
        margin_v = get_scaled_size(3)
        layout.setContentsMargins(margin_h, margin_v, margin_h, margin_v)
        
        # LED indicator (scaled)
        led = QLabel()
        led_size = get_scaled_size(12)
        led.setFixedSize(led_size, led_size)
        led_radius = get_scaled_size(6)
        led.setStyleSheet(f"background-color: {'#00ff00' if active else '#404040'}; border-radius: {led_radius}px; border: {border}px solid {color};")
        layout.addWidget(led)
        
        # Label (scaled)
        label_widget = QLabel(label)
        label_font = get_scaled_font_size(10)
        label_widget.setStyleSheet(f"font-size: {label_font}px; color: #ffffff;")
        layout.addWidget(label_widget)
        
        layout.addStretch()
        return widget, led
        
    def _create_center_panel(self) -> QWidget:
        """Create center panel with Lambda & EGT correction tables."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(15)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # Lambda Control section
        lambda_group = QGroupBox("Lambda Fuel Correction (Closed Loop)")
        group_font = get_scaled_font_size(12)
        group_border = get_scaled_size(1)
        group_radius = get_scaled_size(3)
        group_margin = get_scaled_size(10)
        lambda_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        lambda_layout = QVBoxLayout()
        
        # Toggle switch
        toggle_layout = QHBoxLayout()
        toggle_layout.addWidget(QLabel("Enabled:"))
        self.lambda_enabled = QCheckBox()
        self.lambda_enabled.setChecked(True)
        self.lambda_enabled.setStyleSheet("color: #ffffff;")
        toggle_layout.addWidget(self.lambda_enabled)
        toggle_layout.addStretch()
        lambda_layout.addLayout(toggle_layout)
        
        # Lambda table
        lambda_table_label = QLabel("Target Lambda Table (RPM vs MAP)")
        label_font = get_scaled_font_size(11)
        lambda_table_label.setStyleSheet(f"font-size: {label_font}px; color: #ffffff;")
        lambda_layout.addWidget(lambda_table_label)
        
        self.lambda_table = QTableWidget()
        self.lambda_table.setRowCount(8)
        self.lambda_table.setColumnCount(6)
        self.lambda_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.lambda_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.lambda_table.setMaximumHeight(get_scaled_size(200))
        self.lambda_table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
            }
        """)
        
        # Initialize lambda table
        rpm_values = [1000, 2000, 3000, 4000, 5000, 6000]
        for col, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lambda_table.setHorizontalHeaderItem(col, item)
            
        map_values = [50, 60, 70, 80, 90, 95, 100, 105]
        for row, map_val in enumerate(map_values):
            item = QTableWidgetItem(f"{map_val}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lambda_table.setVerticalHeaderItem(row, item)
            
        # Fill with lambda values (0.8-1.2)
        import random
        for row in range(8):
            for col in range(6):
                lambda_val = 0.85 + random.random() * 0.25
                item = QTableWidgetItem(f"{lambda_val:.2f}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                if lambda_val > 1.1:
                    item.setBackground(QBrush(QColor("#ff0000")))
                elif lambda_val > 0.95:
                    item.setBackground(QBrush(QColor("#00ff00")))
                else:
                    item.setBackground(QBrush(QColor("#0080ff")))
                self.lambda_table.setItem(row, col, item)
        
        lambda_layout.addWidget(self.lambda_table)
        lambda_group.setLayout(lambda_layout)
        layout.addWidget(lambda_group)
        
        # EGT Correction section
        egt_group = QGroupBox("EGT Fuel Correction Table")
        egt_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        egt_layout = QVBoxLayout()
        
        egt_table_label = QLabel("Fuel Enrichment % (EGT vs RPM)")
        egt_table_label.setStyleSheet(f"font-size: {label_font}px; color: #ffffff;")
        egt_layout.addWidget(egt_table_label)
        
        self.egt_table = QTableWidget()
        self.egt_table.setRowCount(6)
        self.egt_table.setColumnCount(5)
        self.egt_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.egt_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.egt_table.setMaximumHeight(get_scaled_size(150))
        self.egt_table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
            }
        """)
        
        # Initialize EGT table
        egt_values = [600, 700, 800, 900, 1000]
        for col, egt in enumerate(egt_values):
            item = QTableWidgetItem(f"{egt}°C")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.egt_table.setHorizontalHeaderItem(col, item)
            
        egt_rpm_values = [2000, 3000, 4000, 5000, 6000, 7000]
        for row, rpm in enumerate(egt_rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.egt_table.setVerticalHeaderItem(row, item)
            
        # Fill with enrichment values
        for row in range(6):
            for col in range(5):
                enrichment = max(0, (egt_values[col] - 600) / 10)
                item = QTableWidgetItem(f"+{enrichment:.1f}%")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                if enrichment > 30:
                    item.setBackground(QBrush(QColor("#ff0000")))
                elif enrichment > 20:
                    item.setBackground(QBrush(QColor("#ff8000")))
                else:
                    item.setBackground(QBrush(QColor("#0080ff")))
                self.egt_table.setItem(row, col, item)
        
        egt_layout.addWidget(self.egt_table)
        egt_group.setLayout(egt_layout)
        layout.addWidget(egt_group)
        
        layout.addStretch()
        return panel
        
    def _create_right_panel(self) -> QWidget:
        """Create right panel with engine protection settings."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        panel.setMaximumWidth(get_scaled_size(250))
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(15)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # Advanced Warning and Protection System (3-Level)
        warning_group = QGroupBox("Advanced Warning & Protection System")
        group_font = get_scaled_font_size(12)
        group_border = get_scaled_size(1)
        group_radius = get_scaled_size(3)
        group_margin = get_scaled_size(10)
        warning_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        warning_layout = QVBoxLayout()
        warning_layout.setSpacing(get_scaled_size(8))
        
        # Level 1: Retard
        level1_group = QGroupBox("Level 1: Retard")
        level1_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {get_scaled_font_size(11)}px; font-weight: bold; color: #ffaa00;
                border: {group_border}px solid #ffaa00; border-radius: {group_radius}px;
                margin-top: {get_scaled_size(5)}px; padding-top: {get_scaled_size(5)}px;
            }}
        """)
        level1_layout = QVBoxLayout()
        level1_layout.addWidget(QLabel("Ignition Retard (deg):"))
        self.level1_retard = QDoubleSpinBox()
        self.level1_retard.setRange(-20, 0)
        self.level1_retard.setValue(-5)
        self.level1_retard.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        level1_layout.addWidget(self.level1_retard)
        level1_layout.addWidget(QLabel("Activation Threshold:"))
        self.level1_threshold = QDoubleSpinBox()
        self.level1_threshold.setRange(0, 100)
        self.level1_threshold.setValue(80)
        self.level1_threshold.setSuffix("%")
        self.level1_threshold.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        level1_layout.addWidget(self.level1_threshold)
        level1_group.setLayout(level1_layout)
        warning_layout.addWidget(level1_group)
        
        # Level 2: Soft Cut
        level2_group = QGroupBox("Level 2: Soft Cut")
        level2_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {get_scaled_font_size(11)}px; font-weight: bold; color: #ff8000;
                border: {group_border}px solid #ff8000; border-radius: {group_radius}px;
                margin-top: {get_scaled_size(5)}px; padding-top: {get_scaled_size(5)}px;
            }}
        """)
        level2_layout = QVBoxLayout()
        level2_layout.addWidget(QLabel("Cut Percentage (%):"))
        self.level2_cut_pct = QDoubleSpinBox()
        self.level2_cut_pct.setRange(0, 100)
        self.level2_cut_pct.setValue(50)
        self.level2_cut_pct.setSuffix("%")
        self.level2_cut_pct.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        level2_layout.addWidget(self.level2_cut_pct)
        level2_layout.addWidget(QLabel("Pattern:"))
        self.level2_pattern = QComboBox()
        self.level2_pattern.addItems(["Spark Cut", "Fuel Cut", "Blended"])
        self.level2_pattern.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        level2_layout.addWidget(self.level2_pattern)
        level2_layout.addWidget(QLabel("Activation Threshold:"))
        self.level2_threshold = QDoubleSpinBox()
        self.level2_threshold.setRange(0, 100)
        self.level2_threshold.setValue(90)
        self.level2_threshold.setSuffix("%")
        self.level2_threshold.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        level2_layout.addWidget(self.level2_threshold)
        level2_group.setLayout(level2_layout)
        warning_layout.addWidget(level2_group)
        
        # Level 3: Hard Cut
        level3_group = QGroupBox("Level 3: Hard Cut")
        level3_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {get_scaled_font_size(11)}px; font-weight: bold; color: #ff0000;
                border: {group_border}px solid #ff0000; border-radius: {group_radius}px;
                margin-top: {get_scaled_size(5)}px; padding-top: {get_scaled_size(5)}px;
            }}
        """)
        level3_layout = QVBoxLayout()
        level3_layout.addWidget(QLabel("Cut Type:"))
        self.level3_cut_type = QComboBox()
        self.level3_cut_type.addItems(["Full Fuel Cut", "Full Spark Cut", "Engine Shutdown"])
        self.level3_cut_type.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        level3_layout.addWidget(self.level3_cut_type)
        level3_layout.addWidget(QLabel("Activation Threshold:"))
        self.level3_threshold = QDoubleSpinBox()
        self.level3_threshold.setRange(0, 100)
        self.level3_threshold.setValue(95)
        self.level3_threshold.setSuffix("%")
        self.level3_threshold.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        level3_layout.addWidget(self.level3_threshold)
        level3_group.setLayout(level3_layout)
        warning_layout.addWidget(level3_group)
        
        warning_group.setLayout(warning_layout)
        layout.addWidget(warning_group)
        
        # Engine Protections group (Basic settings)
        protections_group = QGroupBox("Engine Protections")
        protections_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        protections_layout = QVBoxLayout()
        protections_layout.setSpacing(get_scaled_size(10))
        
        # Rev Limit
        protections_layout.addWidget(QLabel("Rev Limit (RPM):"))
        self.rev_limit = QSpinBox()
        self.rev_limit.setRange(0, 10000)
        self.rev_limit.setValue(7500)
        self.rev_limit.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        protections_layout.addWidget(self.rev_limit)
        
        # Rev Limit Type
        protections_layout.addWidget(QLabel("Rev Limit Type:"))
        self.rev_limit_type = QComboBox()
        self.rev_limit_type.addItems(["Fuel Cut", "Spark Cut", "Blended"])
        self.rev_limit_type.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        protections_layout.addWidget(self.rev_limit_type)
        
        # Soft Cut percentage for rev limit
        protections_layout.addWidget(QLabel("Soft Cut %:"))
        self.rev_soft_cut = QDoubleSpinBox()
        self.rev_soft_cut.setRange(0, 100)
        self.rev_soft_cut.setValue(25)
        self.rev_soft_cut.setSuffix("%")
        self.rev_soft_cut.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        protections_layout.addWidget(self.rev_soft_cut)
        
        # Hard Cut RPM
        protections_layout.addWidget(QLabel("Hard Cut RPM:"))
        self.rev_hard_cut = QSpinBox()
        self.rev_hard_cut.setRange(0, 10000)
        self.rev_hard_cut.setValue(8000)
        self.rev_hard_cut.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        protections_layout.addWidget(self.rev_hard_cut)
        
        # Lean Power Cut
        protections_layout.addWidget(QLabel("Lean Power Cut (Lambda):"))
        self.lean_cut = QDoubleSpinBox()
        self.lean_cut.setRange(0.5, 2.0)
        self.lean_cut.setValue(1.2)
        self.lean_cut.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        protections_layout.addWidget(self.lean_cut)
        
        # Lean Power Cut conditions
        protections_layout.addWidget(QLabel("Min MAP (kPa):"))
        self.lean_min_map = QDoubleSpinBox()
        self.lean_min_map.setRange(0, 200)
        self.lean_min_map.setValue(50)
        self.lean_min_map.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        protections_layout.addWidget(self.lean_min_map)
        
        protections_layout.addWidget(QLabel("Min RPM:"))
        self.lean_min_rpm = QSpinBox()
        self.lean_min_rpm.setRange(0, 10000)
        self.lean_min_rpm.setValue(2000)
        self.lean_min_rpm.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        protections_layout.addWidget(self.lean_min_rpm)
        
        protections_layout.addWidget(QLabel("Min TPS (%):"))
        self.lean_min_tps = QDoubleSpinBox()
        self.lean_min_tps.setRange(0, 100)
        self.lean_min_tps.setValue(50)
        self.lean_min_tps.setSuffix("%")
        self.lean_min_tps.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        protections_layout.addWidget(self.lean_min_tps)
        
        # EGT Power Cut
        protections_layout.addWidget(QLabel("EGT Power Cut (°C):"))
        self.egt_cut = QSpinBox()
        self.egt_cut.setRange(0, 1200)
        self.egt_cut.setValue(950)
        self.egt_cut.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        protections_layout.addWidget(self.egt_cut)
        
        protections_group.setLayout(protections_layout)
        layout.addWidget(protections_group)
        
        layout.addStretch()
        return panel
        
    def _create_advanced_panel(self) -> QWidget:
        """Create advanced features sub-panel."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # Advanced Settings sub-tab
        advanced_tabs = QTabWidget()
        tab_border = get_scaled_size(1)
        tab_padding_v = get_scaled_size(5)
        tab_padding_h = get_scaled_size(15)
        tab_margin = get_scaled_size(2)
        advanced_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: {tab_border}px solid #404040;
                background-color: #1a1a1a;
            }}
            QTabBar::tab {{
                background-color: #2a2a2a;
                color: #ffffff;
                padding: {tab_padding_v}px {tab_padding_h}px;
                margin-right: {tab_margin}px;
                border: {tab_border}px solid #404040;
            }}
            QTabBar::tab:selected {{
                background-color: #1a1a1a;
                border-bottom: {get_scaled_size(2)}px solid #0080ff;
            }}
        """)
        
        # Cylinder Correction tab
        cylinder_tab = self._create_cylinder_correction_tab()
        advanced_tabs.addTab(cylinder_tab, "Cylinder Correction")
        
        # Filtering tab
        filtering_tab = self._create_filtering_tab()
        advanced_tabs.addTab(filtering_tab, "Filtering")
        
        # Staging/Virtuals tab
        staging_tab = self._create_staging_tab()
        advanced_tabs.addTab(staging_tab, "Staging/Virtuals")
        
        layout.addWidget(advanced_tabs)
        return panel
        
    def _create_cylinder_correction_tab(self) -> QWidget:
        """Create cylinder correction tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        title = QLabel("Individual Fuel Correction per Cylinder")
        title_font = get_scaled_font_size(12)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Cylinder correction bars
        cylinders_layout = QGridLayout()
        self.cylinder_corrections = {}
        for i in range(8):
            row = i // 4
            col = i % 4
            
            cyl_label = QLabel(f"Cyl {i+1}:")
            cyl_label.setStyleSheet("color: #ffffff;")
            cylinders_layout.addWidget(cyl_label, row, col * 2)
            
            correction_label = QLabel("+3.5%")
            correction_font = get_scaled_font_size(12)
            if i == 2:  # Highlight cylinder 3
                correction_label.setStyleSheet(f"font-size: {correction_font}px; font-weight: bold; color: #ff8000;")
            else:
                correction_label.setStyleSheet(f"font-size: {correction_font}px; color: #ffffff;")
            self.cylinder_corrections[i] = correction_label
            cylinders_layout.addWidget(correction_label, row, col * 2 + 1)
        
        layout.addLayout(cylinders_layout)
        layout.addStretch()
        return tab
        
    def _create_filtering_tab(self) -> QWidget:
        """Create filtering tab with TPS, RPM, and MAP signal filters."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        title = QLabel("Signal Filters on TPS, RPM and MAP")
        title_font = get_scaled_font_size(12)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # TPS Filter
        tps_group = QGroupBox("TPS Filter")
        group_font = get_scaled_font_size(11)
        group_border = get_scaled_size(1)
        group_radius = get_scaled_size(3)
        group_margin = get_scaled_size(10)
        tps_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        tps_layout = QVBoxLayout()
        tps_layout.addWidget(QLabel("Filter Aggressiveness (0-100%):"))
        self.tps_filter = QSlider(Qt.Orientation.Horizontal)
        self.tps_filter.setRange(0, 100)
        self.tps_filter.setValue(50)
        tps_layout.addWidget(self.tps_filter)
        self.tps_filter_label = QLabel("50%")
        self.tps_filter_label.setStyleSheet("color: #ffffff;")
        tps_layout.addWidget(self.tps_filter_label)
        self.tps_filter.valueChanged.connect(lambda v: self.tps_filter_label.setText(f"{v}%"))
        tps_group.setLayout(tps_layout)
        layout.addWidget(tps_group)
        
        # RPM Filter
        rpm_group = QGroupBox("RPM Filter")
        rpm_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        rpm_layout = QVBoxLayout()
        rpm_layout.addWidget(QLabel("Filter Aggressiveness (0-100%):"))
        self.rpm_filter = QSlider(Qt.Orientation.Horizontal)
        self.rpm_filter.setRange(0, 100)
        self.rpm_filter.setValue(50)
        rpm_layout.addWidget(self.rpm_filter)
        self.rpm_filter_label = QLabel("50%")
        self.rpm_filter_label.setStyleSheet("color: #ffffff;")
        rpm_layout.addWidget(self.rpm_filter_label)
        self.rpm_filter.valueChanged.connect(lambda v: self.rpm_filter_label.setText(f"{v}%"))
        rpm_group.setLayout(rpm_layout)
        layout.addWidget(rpm_group)
        
        # MAP Filter
        map_group = QGroupBox("MAP Filter")
        map_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        map_layout = QVBoxLayout()
        map_layout.addWidget(QLabel("Filter Aggressiveness (0-100%):"))
        self.map_filter = QSlider(Qt.Orientation.Horizontal)
        self.map_filter.setRange(0, 100)
        self.map_filter.setValue(50)
        map_layout.addWidget(self.map_filter)
        self.map_filter_label = QLabel("50%")
        self.map_filter_label.setStyleSheet("color: #ffffff;")
        map_layout.addWidget(self.map_filter_label)
        self.map_filter.valueChanged.connect(lambda v: self.map_filter_label.setText(f"{v}%"))
        map_group.setLayout(map_layout)
        layout.addWidget(map_group)
        
        layout.addStretch()
        
        # TPS Filter
        tps_layout = QHBoxLayout()
        tps_layout.addWidget(QLabel("TPS Filter Lag:"))
        self.tps_filter = QSpinBox()
        self.tps_filter.setRange(0, 100)
        self.tps_filter.setValue(5)
        self.tps_filter.setSuffix(" ms")
        self.tps_filter.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        tps_layout.addWidget(self.tps_filter)
        layout.addLayout(tps_layout)
        
        # RPM Filter
        rpm_layout = QHBoxLayout()
        rpm_layout.addWidget(QLabel("RPM Filter Lag:"))
        self.rpm_filter = QSpinBox()
        self.rpm_filter.setRange(0, 100)
        self.rpm_filter.setValue(10)
        self.rpm_filter.setSuffix(" ms")
        self.rpm_filter.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        rpm_layout.addWidget(self.rpm_filter)
        layout.addLayout(rpm_layout)
        
        # MAP Filter
        map_layout = QHBoxLayout()
        map_layout.addWidget(QLabel("MAP Filter Lag:"))
        self.map_filter = QSpinBox()
        self.map_filter.setRange(0, 100)
        self.map_filter.setValue(12)
        self.map_filter.setSuffix(" ms")
        self.map_filter.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        map_layout.addWidget(self.map_filter)
        layout.addLayout(map_layout)
        
        layout.addStretch()
        return tab
        
    def _create_staging_tab(self) -> QWidget:
        """Create staging/virtuals tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        title = QLabel("Injector Staging and Virtual Inputs/Outputs")
        title_font = get_scaled_font_size(12)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Virtual outputs list
        from PySide6.QtWidgets import QListWidget
        virtual_list = QListWidget()
        border = get_scaled_size(1)
        virtual_list.setStyleSheet(f"""
            QListWidget {{
                background-color: #0a0a0a;
                color: #ffffff;
                border: {border}px solid #404040;
            }}
        """)
        virtual_list.addItem("Virtual Out 1: AC Request -> IF IAT > 50C")
        virtual_list.addItem("Virtual Out 2: Fan Control -> IF Coolant > 90C")
        virtual_list.addItem("Virtual Out 3: Boost Solenoid -> IF MAP > 100 kPa")
        layout.addWidget(virtual_list)
        
        layout.addStretch()
        return tab
        
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update with telemetry data."""
        rpm = data.get("RPM", data.get("Engine_RPM", 0))
        map_val = data.get("Boost_Pressure", 0) * 6.895
        if map_val < 0:
            map_val = 100 - abs(map_val)
        afr = data.get("AFR", data.get("lambda_value", 1.0) * 14.7)
        
        self.rpm_gauge.set_value(rpm)
        self.map_gauge.set_value(map_val)
        self.afr_gauge.set_value(afr)
        
        # Update Flex Fuel
        ethanol = data.get("e85_percent", data.get("FlexFuelPercent", 72.4))
        self.ethanol_label.setText(f"E85%: {ethanol:.1f}%")
        
        # Update EGT
        egt = data.get("EGT", data.get("ExhaustTemp", 850))
        self.egt_label.setText(f"EGT Cyl 1: {egt:.0f} °C")
        
        # Update status lights
        lambda_val = data.get("lambda_value", 1.0)
        led_radius = get_scaled_size(6)
        if lambda_val > 1.2:
            self.lean_cut_led.setStyleSheet(f"background-color: #ff0000; border-radius: {led_radius}px; border: {get_scaled_size(1)}px solid #ff0000;")
        else:
            self.lean_cut_led.setStyleSheet(f"background-color: #404040; border-radius: {led_radius}px; border: {get_scaled_size(1)}px solid #ff0000;")
            
        if egt > 950:
            self.egt_cut_led.setStyleSheet(f"background-color: #ff0000; border-radius: {led_radius}px; border: {get_scaled_size(1)}px solid #ff0000;")
        else:
            self.egt_cut_led.setStyleSheet(f"background-color: #404040; border-radius: {led_radius}px; border: {get_scaled_size(1)}px solid #ff0000;")
            
        if rpm > 7500:
            self.rev_limit_led.setStyleSheet(f"background-color: #ffaa00; border-radius: {led_radius}px; border: {get_scaled_size(1)}px solid #ffaa00;")
        else:
            self.rev_limit_led.setStyleSheet(f"background-color: #404040; border-radius: {led_radius}px; border: {get_scaled_size(1)}px solid #ffaa00;")


class MotorsportTab(QWidget):
    """Motorsport features tab: Launch Control, Anti-Lag, Traction Control, Shift-Cut."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup motorsport tab."""
        main_layout = QVBoxLayout(self)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # Control bar
        control_bar = self._create_control_bar()
        main_layout.addWidget(control_bar)
        
        # Sub-tabs for different motorsport features
        self.sub_tabs = QTabWidget()
        tab_border = get_scaled_size(1)
        tab_padding_v = get_scaled_size(6)
        tab_padding_h = get_scaled_size(15)
        tab_margin = get_scaled_size(2)
        tab_font = get_scaled_font_size(10)
        self.sub_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: {tab_border}px solid #404040;
                background-color: #1a1a1a;
            }}
            QTabBar::tab {{
                background-color: #2a2a2a;
                color: #ffffff;
                padding: {tab_padding_v}px {tab_padding_h}px;
                margin-right: {tab_margin}px;
                border: {tab_border}px solid #404040;
                font-size: {tab_font}px;
                min-height: {get_scaled_size(25)}px;
            }}
            QTabBar::tab:selected {{
                background-color: #1a1a1a;
                border-bottom: {get_scaled_size(2)}px solid #0080ff;
            }}
        """)
        
        # Launch Control tab
        launch_tab = self._create_launch_control_tab()
        self.sub_tabs.addTab(launch_tab, "Launch Control")
        
        # Anti-Lag tab
        antilag_tab = self._create_antilag_tab()
        self.sub_tabs.addTab(antilag_tab, "Anti-Lag")
        
        # Traction Control tab
        tc_tab = self._create_traction_control_tab()
        self.sub_tabs.addTab(tc_tab, "Traction Control")
        
        # Shift-Cut tab
        shiftcut_tab = self._create_shiftcut_tab()
        self.sub_tabs.addTab(shiftcut_tab, "Shift-Cut")
        
        main_layout.addWidget(self.sub_tabs, stretch=1)
        
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
        
        fps_label = QLabel("21.6 fps")
        fps_font = get_scaled_font_size(10)
        fps_label.setStyleSheet(f"font-size: {fps_font}px; color: #ffffff;")
        layout.addWidget(fps_label)
        
        layout.addStretch()
        
        title = QLabel("Motorsport Features Control Panel")
        title_font = get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        buttons = ["Update Controller", "Send", "Burn", "Active", "Stop"]
        btn_padding_v = get_scaled_size(5)
        btn_padding_h = get_scaled_size(10)
        btn_font = get_scaled_font_size(11)
        for btn_text in buttons:
            btn = QPushButton(btn_text)
            btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            if btn_text == "Active":
                btn.setStyleSheet(f"background-color: #ff0000; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px; font-weight: bold; font-size: {btn_font}px;")
            else:
                btn.setStyleSheet(f"background-color: #404040; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px; font-size: {btn_font}px;")
            layout.addWidget(btn)
            
        return bar
        
    def _create_launch_control_tab(self) -> QWidget:
        """Create launch control tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(15)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # Content layout
        content_layout = QHBoxLayout()
        content_layout.setSpacing(get_scaled_size(15))
        
        # Left: Gauges
        left_panel = QWidget()
        border = get_scaled_size(1)
        left_panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        left_panel.setMaximumWidth(get_scaled_size(250))
        left_layout = QVBoxLayout(left_panel)
        left_margin = get_scaled_size(10)
        left_layout.setContentsMargins(left_margin, left_margin, left_margin, left_margin)
        
        self.launch_rpm_gauge = AnalogGauge(
            "Launch RPM",
            min_value=0,
            max_value=8000,
            unit="RPM",
        )
        left_layout.addWidget(self.launch_rpm_gauge)
        
        self.launch_wheel_slip = AnalogGauge(
            "Wheel Slip",
            min_value=0,
            max_value=100,
            unit="%",
        )
        left_layout.addWidget(self.launch_wheel_slip)
        left_layout.addStretch()
        content_layout.addWidget(left_panel, stretch=0)
        
        # Center: Launch control map
        center_panel = QWidget()
        center_panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(left_margin, left_margin, left_margin, left_margin)
        
        title = QLabel("Launch Control Map")
        title_font = get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        center_layout.addWidget(title)
        
        # Launch settings table
        self.launch_table = QTableWidget()
        self.launch_table.setRowCount(5)
        self.launch_table.setColumnCount(4)
        self.launch_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.launch_table.setMaximumHeight(get_scaled_size(200))
        self.launch_table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
            }
        """)
        
        headers = ["RPM Limit", "Wheel Slip %", "Torque Reduction %", "Duration (s)"]
        for col, header in enumerate(headers):
            item = QTableWidgetItem(header)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.launch_table.setHorizontalHeaderItem(col, item)
            
        for row in range(5):
            for col in range(4):
                if col == 0:
                    val = f"{3000 + row * 500}"
                elif col == 1:
                    val = f"{10 + row * 5}"
                elif col == 2:
                    val = f"{20 + row * 10}"
                else:
                    val = f"{0.5 + row * 0.2:.1f}"
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                item.setBackground(QBrush(QColor("#2a2a2a")))
                self.launch_table.setItem(row, col, item)
        
        center_layout.addWidget(self.launch_table)
        content_layout.addWidget(center_panel, stretch=3)
        
        # Right: Settings
        right_panel = QWidget()
        right_panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        right_panel.setMaximumWidth(get_scaled_size(200))
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(left_margin, left_margin, left_margin, left_margin)
        
        settings_group = QGroupBox("Launch Settings")
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
        
        self.launch_enabled = QCheckBox("Launch Control Enabled")
        self.launch_enabled.setStyleSheet("color: #ffffff; font-weight: bold;")
        settings_layout.addWidget(self.launch_enabled)
        
        # 3-Stage Launch Control
        stage_group = QGroupBox("3-Stage Launch Control")
        stage_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {get_scaled_font_size(11)}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {get_scaled_size(5)}px; padding-top: {get_scaled_size(5)}px;
            }}
        """)
        stage_layout = QVBoxLayout()
        stage_layout.setSpacing(get_scaled_size(5))
        
        stage_layout.addWidget(QLabel("Stage 1 RPM:"))
        self.stage1_rpm = QSpinBox()
        self.stage1_rpm.setRange(0, 10000)
        self.stage1_rpm.setValue(4000)
        self.stage1_rpm.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        stage_layout.addWidget(self.stage1_rpm)
        
        stage_layout.addWidget(QLabel("Stage 2 RPM:"))
        self.stage2_rpm = QSpinBox()
        self.stage2_rpm.setRange(0, 10000)
        self.stage2_rpm.setValue(5000)
        self.stage2_rpm.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        stage_layout.addWidget(self.stage2_rpm)
        
        stage_layout.addWidget(QLabel("Stage 3 RPM:"))
        self.stage3_rpm = QSpinBox()
        self.stage3_rpm.setRange(0, 10000)
        self.stage3_rpm.setValue(6000)
        self.stage3_rpm.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        stage_layout.addWidget(self.stage3_rpm)
        
        stage_group.setLayout(stage_layout)
        settings_layout.addWidget(stage_group)
        
        # Rolling Launch
        rolling_group = QGroupBox("Rolling Launch")
        rolling_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {get_scaled_font_size(11)}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {get_scaled_size(5)}px; padding-top: {get_scaled_size(5)}px;
            }}
        """)
        rolling_layout = QVBoxLayout()
        rolling_layout.setSpacing(get_scaled_size(5))
        
        self.rolling_enabled = QCheckBox("Rolling Launch Enabled")
        self.rolling_enabled.setStyleSheet("color: #ffffff;")
        rolling_layout.addWidget(self.rolling_enabled)
        
        rolling_layout.addWidget(QLabel("Activation Speed (mph):"))
        self.rolling_speed = QDoubleSpinBox()
        self.rolling_speed.setRange(0, 100)
        self.rolling_speed.setValue(5)
        self.rolling_speed.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        rolling_layout.addWidget(self.rolling_speed)
        
        rolling_layout.addWidget(QLabel("Release Speed (mph):"))
        self.rolling_release = QDoubleSpinBox()
        self.rolling_release.setRange(0, 100)
        self.rolling_release.setValue(20)
        self.rolling_release.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        rolling_layout.addWidget(self.rolling_release)
        
        rolling_group.setLayout(rolling_layout)
        settings_layout.addWidget(rolling_group)
        
        settings_layout.addWidget(QLabel("Max Wheel Slip:"))
        self.max_slip = QSpinBox()
        self.max_slip.setRange(0, 100)
        self.max_slip.setValue(20)
        self.max_slip.setSuffix("%")
        self.max_slip.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.max_slip)
        
        settings_group.setLayout(settings_layout)
        right_layout.addWidget(settings_group)
        right_layout.addStretch()
        content_layout.addWidget(right_panel, stretch=1)
        
        layout.addLayout(content_layout, stretch=1)
        
        # Bottom graph
        self.launch_graph = RealTimeGraph()
        layout.addWidget(self.launch_graph, stretch=1)
        
        return tab
        
    def _create_antilag_tab(self) -> QWidget:
        """Create anti-lag tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        title = QLabel("Anti-Lag System")
        title_font = get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Anti-lag settings
        settings_group = QGroupBox("Anti-Lag Settings")
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
        
        self.antilag_enabled = QCheckBox("Anti-Lag Enabled")
        self.antilag_enabled.setStyleSheet("color: #ffffff;")
        settings_layout.addWidget(self.antilag_enabled)
        
        settings_layout.addWidget(QLabel("Ignition Retard (deg):"))
        self.antilag_retard = QDoubleSpinBox()
        self.antilag_retard.setRange(-20, 0)
        self.antilag_retard.setValue(-5)
        self.antilag_retard.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.antilag_retard)
        
        settings_layout.addWidget(QLabel("Fuel Enrichment (%):"))
        self.antilag_fuel = QDoubleSpinBox()
        self.antilag_fuel.setRange(0, 100)
        self.antilag_fuel.setValue(20)
        self.antilag_fuel.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.antilag_fuel)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        layout.addStretch()
        
        return tab
        
    def _create_traction_control_tab(self) -> QWidget:
        """Create traction control tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        title = QLabel("Traction Control System")
        title_font = get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Traction control map
        self.tc_table = QTableWidget()
        self.tc_table.setRowCount(8)
        self.tc_table.setColumnCount(6)
        self.tc_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tc_table.setMinimumHeight(get_scaled_size(300))
        self.tc_table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
            }
        """)
        
        # Initialize TC table (Wheel Slip % vs RPM)
        rpm_values = [2000, 3000, 4000, 5000, 6000, 7000]
        for col, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tc_table.setHorizontalHeaderItem(col, item)
            
        slip_values = [5, 10, 15, 20, 25, 30, 35, 40]
        for row, slip in enumerate(slip_values):
            item = QTableWidgetItem(f"{slip}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tc_table.setVerticalHeaderItem(row, item)
            
        # Fill with torque reduction values
        for row in range(8):
            for col in range(6):
                reduction = min(100, (slip_values[row] - 5) * 3 + (rpm_values[col] / 1000) * 5)
                item = QTableWidgetItem(f"{reduction:.0f}%")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                if reduction > 70:
                    item.setBackground(QBrush(QColor("#ff0000")))
                elif reduction > 40:
                    item.setBackground(QBrush(QColor("#ff8000")))
                else:
                    item.setBackground(QBrush(QColor("#0080ff")))
                self.tc_table.setItem(row, col, item)
        
        layout.addWidget(self.tc_table)
        layout.addStretch()
        
        return tab
        
    def _create_shiftcut_tab(self) -> QWidget:
        """Create shift-cut tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        title = QLabel("Shift-Cut System")
        title_font = get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Shift-cut settings
        settings_group = QGroupBox("Shift-Cut Settings")
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
        
        self.shiftcut_enabled = QCheckBox("Shift-Cut Enabled")
        self.shiftcut_enabled.setStyleSheet("color: #ffffff;")
        settings_layout.addWidget(self.shiftcut_enabled)
        
        settings_layout.addWidget(QLabel("Cut Duration (ms):"))
        self.shiftcut_duration = QSpinBox()
        self.shiftcut_duration.setRange(0, 500)
        self.shiftcut_duration.setValue(50)
        self.shiftcut_duration.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.shiftcut_duration)
        
        settings_layout.addWidget(QLabel("Fuel Cut (%):"))
        self.shiftcut_fuel = QDoubleSpinBox()
        self.shiftcut_fuel.setRange(0, 100)
        self.shiftcut_fuel.setValue(100)
        self.shiftcut_fuel.setSuffix("%")
        self.shiftcut_fuel.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.shiftcut_fuel)
        
        settings_layout.addWidget(QLabel("Delay (ms):"))
        self.shiftcut_delay = QSpinBox()
        self.shiftcut_delay.setRange(0, 200)
        self.shiftcut_delay.setValue(10)
        self.shiftcut_delay.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.shiftcut_delay)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Overrun Fuel Cut
        overrun_group = QGroupBox("Overrun Fuel Cut")
        overrun_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        overrun_layout = QVBoxLayout()
        overrun_layout.setSpacing(get_scaled_size(8))
        
        self.overrun_enabled = QCheckBox("Overrun Fuel Cut Enabled")
        self.overrun_enabled.setStyleSheet("color: #ffffff;")
        overrun_layout.addWidget(self.overrun_enabled)
        
        overrun_layout.addWidget(QLabel("Activation RPM:"))
        self.overrun_rpm = QSpinBox()
        self.overrun_rpm.setRange(0, 10000)
        self.overrun_rpm.setValue(2000)
        self.overrun_rpm.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        overrun_layout.addWidget(self.overrun_rpm)
        
        overrun_layout.addWidget(QLabel("Activation TPS (%):"))
        self.overrun_tps = QDoubleSpinBox()
        self.overrun_tps.setRange(0, 100)
        self.overrun_tps.setValue(5)
        self.overrun_tps.setSuffix("%")
        self.overrun_tps.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        overrun_layout.addWidget(self.overrun_tps)
        
        overrun_layout.addWidget(QLabel("Fuel Re-enable Speed (mph):"))
        self.overrun_speed = QDoubleSpinBox()
        self.overrun_speed.setRange(0, 200)
        self.overrun_speed.setValue(10)
        self.overrun_speed.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        overrun_layout.addWidget(self.overrun_speed)
        
        overrun_group.setLayout(overrun_layout)
        layout.addWidget(overrun_group)
        
        layout.addStretch()
        return tab
        
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update with telemetry data."""
        rpm = data.get("RPM", data.get("Engine_RPM", 0))
        if hasattr(self, 'launch_rpm_gauge'):
            self.launch_rpm_gauge.set_value(rpm)
            
        wheel_slip = data.get("wheel_slip", 0)
        if hasattr(self, 'launch_wheel_slip'):
            self.launch_wheel_slip.set_value(wheel_slip)


class TransmissionTab(QWidget):
    """Transmission Control (TCU) tab for automatic/DCT/DSG transmission configuration."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup transmission tab."""
        main_layout = QVBoxLayout(self)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # Control bar
        control_bar = self._create_control_bar()
        main_layout.addWidget(control_bar)
        
        # Content layout
        content_layout = QHBoxLayout()
        content_layout.setSpacing(get_scaled_size(15))
        
        # Left: Gauges
        left_panel = self._create_gauges_panel()
        content_layout.addWidget(left_panel, stretch=0)
        
        # Center: Shift Map Editor
        center_panel = self._create_shift_map_panel()
        content_layout.addWidget(center_panel, stretch=3)
        
        # Right: Clutch Slip and Launch Control
        right_panel = self._create_right_panel()
        content_layout.addWidget(right_panel, stretch=1)
        
        main_layout.addLayout(content_layout, stretch=1)
        
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
        
        fps_label = QLabel("21.6 fps")
        fps_font = get_scaled_font_size(10)
        fps_label.setStyleSheet(f"font-size: {fps_font}px; color: #ffffff;")
        layout.addWidget(fps_label)
        
        layout.addStretch()
        
        title = QLabel("Transmission Control (TCU) Panel")
        title_font = get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Transmission type selector (ECU auto transmission support)
        layout.addWidget(QLabel("Gearbox:"))
        self.trans_type = QComboBox()
        self.trans_type.addItems([
            "GM 4L80E/4L85E",
            "GM 4L60E/4L65E",
            "Toyota A340E",
            "Toyota A341E",
            "Toyota A650E",
            "BMW DCT",
            "VAG DSG",
            "8HP",
            "Sequential",
            "Generic"
        ])
        self.trans_type.setStyleSheet("color: #ffffff; background-color: #2a2a2a; padding: 4px;")
        self.trans_type.setToolTip("ECU auto transmission support")
        self.trans_type.currentIndexChanged.connect(self._on_gearbox_changed)
        layout.addWidget(self.trans_type)
        
        buttons = ["Update Controller", "Send", "Burn"]
        btn_padding_v = get_scaled_size(5)
        btn_padding_h = get_scaled_size(10)
        btn_font = get_scaled_font_size(11)
        for btn_text in buttons:
            btn = QPushButton(btn_text)
            btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            btn.setStyleSheet(f"background-color: #404040; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px; font-size: {btn_font}px;")
            layout.addWidget(btn)
            
        return bar
        
    def _create_gauges_panel(self) -> QWidget:
        """Create gauges panel."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        panel.setMaximumWidth(get_scaled_size(250))
        panel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(15)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # Current Gear gauge
        self.gear_gauge = AnalogGauge(
            "Current Gear",
            min_value=0,
            max_value=8,
            unit="",
        )
        layout.addWidget(self.gear_gauge)
        
        # Transmission Temp gauge
        self.temp_gauge = AnalogGauge(
            "Trans Temp",
            min_value=0,
            max_value=150,
            unit="°C",
            warning_start=120,
            warning_end=150,
            warning_color="#ff0000",
        )
        layout.addWidget(self.temp_gauge)
        
        # Clutch Pressure gauge
        self.clutch_pressure = AnalogGauge(
            "Clutch Pressure",
            min_value=0,
            max_value=100,
            unit="%",
        )
        layout.addWidget(self.clutch_pressure)
        
        layout.addStretch()
        return panel
        
    def _create_shift_map_panel(self) -> QWidget:
        """Create shift map editor panel."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        # Mode selector
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Shift Mode:"))
        self.shift_mode = QComboBox()
        self.shift_mode.addItems(["D (Drive)", "S (Sport)", "M (Manual)"])
        self.shift_mode.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        mode_layout.addWidget(self.shift_mode)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        
        title = QLabel("Shift Map Editor (Throttle Position % vs Vehicle Speed/RPM)")
        title_font = get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Shift map table
        self.shift_map = QTableWidget()
        self.shift_map.setRowCount(10)
        self.shift_map.setColumnCount(8)
        self.shift_map.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.shift_map.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.shift_map.setMinimumHeight(get_scaled_size(400))
        self.shift_map.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
            }
        """)
        
        # Initialize shift map (Throttle % vs Speed)
        speed_values = [20, 30, 40, 50, 60, 70, 80, 90]
        for col, speed in enumerate(speed_values):
            item = QTableWidgetItem(f"{speed} km/h")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.shift_map.setHorizontalHeaderItem(col, item)
            
        throttle_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for row, throttle in enumerate(throttle_values):
            item = QTableWidgetItem(f"{throttle}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.shift_map.setVerticalHeaderItem(row, item)
            
        # Fill with shift points (gear numbers)
        for row in range(10):
            for col in range(8):
                # Calculate gear based on throttle and speed
                gear = min(6, max(1, int((throttle_values[row] / 100) * 3 + (speed_values[col] / 90) * 3)))
                item = QTableWidgetItem(f"{gear}-{gear+1}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                # Color code: green for light throttle, red for WOT
                if throttle_values[row] > 80:
                    item.setBackground(QBrush(QColor("#ff0000")))
                elif throttle_values[row] > 50:
                    item.setBackground(QBrush(QColor("#ff8000")))
                else:
                    item.setBackground(QBrush(QColor("#00ff00")))
                    
                self.shift_map.setItem(row, col, item)
        
        layout.addWidget(self.shift_map)
        return panel
        
    def _create_right_panel(self) -> QWidget:
        """Create right panel with clutch slip and launch control."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        panel.setMaximumWidth(get_scaled_size(300))
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(15)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # Clutch Slip Control
        clutch_group = QGroupBox("Clutch Slip Control Table")
        group_font = get_scaled_font_size(12)
        group_border = get_scaled_size(1)
        group_radius = get_scaled_size(3)
        group_margin = get_scaled_size(10)
        clutch_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        clutch_layout = QVBoxLayout()
        
        clutch_table_label = QLabel("Commanded Slip (RPM vs Gear)")
        label_font = get_scaled_font_size(11)
        clutch_table_label.setStyleSheet(f"font-size: {label_font}px; color: #ffffff;")
        clutch_layout.addWidget(clutch_table_label)
        
        self.clutch_table = QTableWidget()
        self.clutch_table.setRowCount(6)
        self.clutch_table.setColumnCount(7)
        self.clutch_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.clutch_table.setMaximumHeight(get_scaled_size(200))
        self.clutch_table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
            }
        """)
        
        # Initialize clutch table
        gear_values = [1, 2, 3, 4, 5, 6, 7]
        for col, gear in enumerate(gear_values):
            item = QTableWidgetItem(f"G{gear}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.clutch_table.setHorizontalHeaderItem(col, item)
            
        rpm_values = [2000, 3000, 4000, 5000, 6000, 7000]
        for row, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.clutch_table.setVerticalHeaderItem(row, item)
            
        # Fill with slip values (%)
        for row in range(6):
            for col in range(7):
                slip = max(0, min(100, (gear_values[col] - 1) * 5 + (rpm_values[row] / 1000) * 10))
                item = QTableWidgetItem(f"{slip:.0f}%")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                if slip > 70:
                    item.setBackground(QBrush(QColor("#ff0000")))
                elif slip > 40:
                    item.setBackground(QBrush(QColor("#ff8000")))
                else:
                    item.setBackground(QBrush(QColor("#0080ff")))
                self.clutch_table.setItem(row, col, item)
        
        clutch_layout.addWidget(self.clutch_table)
        clutch_group.setLayout(clutch_layout)
        layout.addWidget(clutch_group)
        
        # Sequential Gearbox Control
        sequential_group = QGroupBox("Sequential Gearbox Control")
        sequential_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        sequential_layout = QVBoxLayout()
        sequential_layout.setSpacing(get_scaled_size(8))
        
        sequential_layout.addWidget(QLabel("Strain Gauge Input:"))
        self.strain_gauge = QComboBox()
        self.strain_gauge.addItems(["Input 1", "Input 2", "Input 3", "Input 4"])
        self.strain_gauge.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        sequential_layout.addWidget(self.strain_gauge)
        
        sequential_layout.addWidget(QLabel("Solenoid Actuation Time (ms):"))
        self.solenoid_time = QSpinBox()
        self.solenoid_time.setRange(0, 500)
        self.solenoid_time.setValue(50)
        self.solenoid_time.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        sequential_layout.addWidget(self.solenoid_time)
        
        sequential_group.setLayout(sequential_layout)
        layout.addWidget(sequential_group)
        
        # CAN TCU Control
        can_tcu_group = QGroupBox("CAN for OEM Protocols")
        can_tcu_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        can_tcu_layout = QVBoxLayout()
        can_tcu_layout.setSpacing(get_scaled_size(8))
        
        self.can_tcu_enabled = QCheckBox("CAN TCU Connection Enabled")
        self.can_tcu_enabled.setStyleSheet("color: #ffffff;")
        can_tcu_layout.addWidget(self.can_tcu_enabled)
        
        can_tcu_layout.addWidget(QLabel("Connection Status:"))
        self.can_tcu_status = QLabel("Disconnected")
        self.can_tcu_status.setStyleSheet("color: #ff0000; font-weight: bold;")
        can_tcu_layout.addWidget(self.can_tcu_status)
        
        can_tcu_layout.addWidget(QLabel("Protocol:"))
        self.can_protocol = QComboBox()
        self.can_protocol.addItems(["OEM Native", "OBDII", "CAN Module"])
        self.can_protocol.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        can_tcu_layout.addWidget(self.can_protocol)
        
        can_tcu_group.setLayout(can_tcu_layout)
        layout.addWidget(can_tcu_group)
        
        # Launch Control Parameters
        launch_group = QGroupBox("Launch Control Parameters")
        launch_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        launch_layout = QVBoxLayout()
        
        launch_layout.addWidget(QLabel("Launch RPM:"))
        self.launch_rpm = QSpinBox()
        self.launch_rpm.setRange(0, 8000)
        self.launch_rpm.setValue(4000)
        self.launch_rpm.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        launch_layout.addWidget(self.launch_rpm)
        
        launch_layout.addWidget(QLabel("Desired Clutch Pressure (%):"))
        self.clutch_pressure_target = QDoubleSpinBox()
        self.clutch_pressure_target.setRange(0, 100)
        self.clutch_pressure_target.setValue(80)
        self.clutch_pressure_target.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        launch_layout.addWidget(self.clutch_pressure_target)
        
        launch_layout.addWidget(QLabel("Torque Reduction (%):"))
        self.torque_reduction = QDoubleSpinBox()
        self.torque_reduction.setRange(0, 100)
        self.torque_reduction.setValue(30)
        self.torque_reduction.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        launch_layout.addWidget(self.torque_reduction)
        
        launch_group.setLayout(launch_layout)
        layout.addWidget(launch_group)
        
        layout.addStretch()
        return panel
        
    def _on_gearbox_changed(self, index: int) -> None:
        """Handle gearbox type change."""
        gearbox = self.trans_type.currentText()
        # Enable/disable sequential controls based on selection
        if "Sequential" in gearbox:
            # Show sequential controls
            if hasattr(self, 'strain_gauge'):
                self.strain_gauge.setEnabled(True)
        else:
            # Hide sequential controls
            if hasattr(self, 'strain_gauge'):
                self.strain_gauge.setEnabled(False)
        
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update with telemetry data."""
        gear = data.get("current_gear", data.get("Gear", 1))
        temp = data.get("trans_temp", data.get("TransmissionTemp", 80))
        clutch = data.get("clutch_pressure", 50)
        
        self.gear_gauge.set_value(gear)
        self.temp_gauge.set_value(temp)
        self.clutch_pressure.set_value(clutch)


__all__ = ["ProtectionsTab", "MotorsportTab", "TransmissionTab"]

