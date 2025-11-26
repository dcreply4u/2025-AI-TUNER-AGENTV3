"""
MoTeC Advanced Features UI Components
UI components for advanced MoTeC ECU features like Hi/Lo Injection, Multi-Pulse Injection,
Site Tables, Gear Change Ignition Cut, CAM Control, etc.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
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
)

from ui.ecu_tuning_widgets import VETableWidget


class HiLoInjectionTab(QWidget):
    """Hi/Lo Injection (dual injector staging) control tab."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup Hi/Lo Injection tab."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Title
        title = QLabel("Hi/Lo Injection - Dual Injector Staging")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        main_layout.addWidget(title)
        
        # Enable checkbox
        enable_layout = QHBoxLayout()
        self.enable_checkbox = QCheckBox("Enable Hi/Lo Injection")
        self.enable_checkbox.setStyleSheet("font-size: 12px; color: #ffffff;")
        enable_layout.addWidget(self.enable_checkbox)
        enable_layout.addStretch()
        main_layout.addLayout(enable_layout)
        
        # Settings group
        settings_group = QGroupBox("Hi/Lo Injection Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        settings_layout = QGridLayout()
        
        settings_layout.addWidget(QLabel("Primary Injector Activation:"), 0, 0)
        self.primary_activation = QComboBox()
        self.primary_activation.addItems(["Always On", "RPM Based", "Load Based", "RPM + Load"])
        settings_layout.addWidget(self.primary_activation, 0, 1)
        
        settings_layout.addWidget(QLabel("Secondary Injector Activation RPM:"), 1, 0)
        self.secondary_activation_rpm = QSpinBox()
        self.secondary_activation_rpm.setRange(2000, 8000)
        self.secondary_activation_rpm.setValue(4000)
        self.secondary_activation_rpm.setSuffix(" RPM")
        settings_layout.addWidget(self.secondary_activation_rpm, 1, 1)
        
        settings_layout.addWidget(QLabel("Secondary Injector Activation Load:"), 2, 0)
        self.secondary_activation_load = QDoubleSpinBox()
        self.secondary_activation_load.setRange(0.0, 100.0)
        self.secondary_activation_load.setValue(50.0)
        self.secondary_activation_load.setSuffix(" %")
        settings_layout.addWidget(self.secondary_activation_load, 2, 1)
        
        settings_layout.addWidget(QLabel("Transition Smoothing:"), 3, 0)
        self.transition_smoothing = QSlider(Qt.Orientation.Horizontal)
        self.transition_smoothing.setRange(0, 100)
        self.transition_smoothing.setValue(50)
        settings_layout.addWidget(self.transition_smoothing, 3, 1)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # Activation map table
        map_group = QGroupBox("Hi/Lo Activation Map (RPM vs Load)")
        map_group.setStyleSheet(settings_group.styleSheet())
        map_layout = QVBoxLayout()
        
        self.activation_table = VETableWidget()
        map_layout.addWidget(self.activation_table)
        
        map_group.setLayout(map_layout)
        main_layout.addWidget(map_group, stretch=1)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_btn = QPushButton("Apply Settings")
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #0080ff;
                color: #ffffff;
                border: none;
                padding: 8px 20px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0066cc;
            }
        """)
        button_layout.addWidget(self.apply_btn)
        
        main_layout.addLayout(button_layout)


class MultiPulseInjectionTab(QWidget):
    """Multi-Pulse Injection control tab."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup Multi-Pulse Injection tab."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Title
        title = QLabel("Multi-Pulse Injection - Multiple Injection Events Per Cycle")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        main_layout.addWidget(title)
        
        # Enable checkbox
        enable_layout = QHBoxLayout()
        self.enable_checkbox = QCheckBox("Enable Multi-Pulse Injection")
        self.enable_checkbox.setStyleSheet("font-size: 12px; color: #ffffff;")
        enable_layout.addWidget(self.enable_checkbox)
        enable_layout.addStretch()
        main_layout.addLayout(enable_layout)
        
        # Settings group
        settings_group = QGroupBox("Multi-Pulse Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        settings_layout = QGridLayout()
        
        settings_layout.addWidget(QLabel("Number of Pulses:"), 0, 0)
        self.pulse_count = QSpinBox()
        self.pulse_count.setRange(2, 5)
        self.pulse_count.setValue(2)
        settings_layout.addWidget(self.pulse_count, 0, 1)
        
        settings_layout.addWidget(QLabel("Pulse Distribution:"), 1, 0)
        self.pulse_distribution = QComboBox()
        self.pulse_distribution.addItems(["Equal", "Early Heavy", "Late Heavy", "Custom"])
        settings_layout.addWidget(self.pulse_distribution, 1, 1)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # Pulse timing table
        timing_group = QGroupBox("Pulse Timing Map (RPM vs Load)")
        timing_group.setStyleSheet(settings_group.styleSheet())
        timing_layout = QVBoxLayout()
        
        self.timing_table = VETableWidget()
        timing_layout.addWidget(self.timing_table)
        
        timing_group.setLayout(timing_layout)
        main_layout.addWidget(timing_group, stretch=1)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_btn = QPushButton("Apply Settings")
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #0080ff;
                color: #ffffff;
                border: none;
                padding: 8px 20px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0066cc;
            }
        """)
        button_layout.addWidget(self.apply_btn)
        
        main_layout.addLayout(button_layout)


class InjectionTimingTab(QWidget):
    """Fuel Injection Timing control tab."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup Injection Timing tab."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Title
        title = QLabel("Fuel Injection Timing - Injection Angle Control")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        main_layout.addWidget(title)
        
        # Description
        desc = QLabel("Control when fuel is injected during the engine cycle (separate from fuel quantity)")
        desc.setStyleSheet("font-size: 11px; color: #aaaaaa;")
        main_layout.addWidget(desc)
        
        # Injection timing table
        timing_group = QGroupBox("Injection Timing Map (RPM vs Load)")
        timing_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        timing_layout = QVBoxLayout()
        
        self.timing_table = VETableWidget()
        timing_layout.addWidget(self.timing_table)
        
        timing_group.setLayout(timing_layout)
        main_layout.addWidget(timing_group, stretch=1)
        
        # Settings
        settings_group = QGroupBox("Injection Timing Settings")
        settings_group.setStyleSheet(timing_group.styleSheet())
        settings_layout = QGridLayout()
        
        settings_layout.addWidget(QLabel("Base Injection Angle:"), 0, 0)
        self.base_angle = QDoubleSpinBox()
        self.base_angle.setRange(270.0, 360.0)
        self.base_angle.setValue(330.0)
        self.base_angle.setSuffix("° BTDC")
        settings_layout.addWidget(self.base_angle, 0, 1)
        
        settings_layout.addWidget(QLabel("Injection Mode:"), 1, 0)
        self.injection_mode = QComboBox()
        self.injection_mode.addItems(["Sequential", "Batch", "Semi-Sequential"])
        settings_layout.addWidget(self.injection_mode, 1, 1)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_btn = QPushButton("Apply Settings")
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #0080ff;
                color: #ffffff;
                border: none;
                padding: 8px 20px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0066cc;
            }
        """)
        button_layout.addWidget(self.apply_btn)
        
        main_layout.addLayout(button_layout)


class ColdStartFuelTab(QWidget):
    """Cold Start Fuel control tab."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup Cold Start Fuel tab."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Title
        title = QLabel("Cold Start Fuel - Separate Cold Start Enrichment")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        main_layout.addWidget(title)
        
        # Description
        desc = QLabel("Separate fuel calibration for cold engine starting and warm-up")
        desc.setStyleSheet("font-size: 11px; color: #aaaaaa;")
        main_layout.addWidget(desc)
        
        # Settings group
        settings_group = QGroupBox("Cold Start Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        settings_layout = QGridLayout()
        
        settings_layout.addWidget(QLabel("Temperature Threshold:"), 0, 0)
        self.temp_threshold = QDoubleSpinBox()
        self.temp_threshold.setRange(0.0, 100.0)
        self.temp_threshold.setValue(60.0)
        self.temp_threshold.setSuffix(" °C")
        settings_layout.addWidget(self.temp_threshold, 0, 1)
        
        settings_layout.addWidget(QLabel("Base Enrichment:"), 1, 0)
        self.base_enrichment = QDoubleSpinBox()
        self.base_enrichment.setRange(1.0, 2.0)
        self.base_enrichment.setValue(1.2)
        self.base_enrichment.setSuffix("x")
        settings_layout.addWidget(self.base_enrichment, 1, 1)
        
        settings_layout.addWidget(QLabel("Warm-up Rate:"), 2, 0)
        self.warmup_rate = QDoubleSpinBox()
        self.warmup_rate.setRange(0.1, 2.0)
        self.warmup_rate.setValue(0.5)
        self.warmup_rate.setSuffix(" /min")
        settings_layout.addWidget(self.warmup_rate, 2, 1)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # Cold start fuel table
        fuel_group = QGroupBox("Cold Start Fuel Map (Temperature vs RPM)")
        fuel_group.setStyleSheet(settings_group.styleSheet())
        fuel_layout = QVBoxLayout()
        
        self.cold_start_table = VETableWidget()
        fuel_layout.addWidget(self.cold_start_table)
        
        fuel_group.setLayout(fuel_layout)
        main_layout.addWidget(fuel_group, stretch=1)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_btn = QPushButton("Apply Settings")
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #0080ff;
                color: #ffffff;
                border: none;
                padding: 8px 20px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0066cc;
            }
        """)
        button_layout.addWidget(self.apply_btn)
        
        main_layout.addLayout(button_layout)


class SiteTablesTab(QWidget):
    """Site Tables (altitude/weather compensation) control tab."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup Site Tables tab."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Title
        title = QLabel("Site Tables - Altitude and Weather Compensation")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        main_layout.addWidget(title)
        
        # Description
        desc = QLabel("Compensate for changes in atmospheric pressure (altitude) and weather conditions")
        desc.setStyleSheet("font-size: 11px; color: #aaaaaa;")
        main_layout.addWidget(desc)
        
        # Tabs for different compensation types
        tabs = QTabWidget()
        tabs.setStyleSheet("""
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
        
        # Altitude compensation tab
        altitude_tab = QWidget()
        altitude_layout = QVBoxLayout(altitude_tab)
        altitude_layout.setContentsMargins(10, 10, 10, 10)
        
        altitude_title = QLabel("Altitude Compensation")
        altitude_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        altitude_layout.addWidget(altitude_title)
        
        self.altitude_table = VETableWidget()
        altitude_layout.addWidget(self.altitude_table, stretch=1)
        
        tabs.addTab(altitude_tab, "Altitude")
        
        # Weather compensation tab
        weather_tab = QWidget()
        weather_layout = QVBoxLayout(weather_tab)
        weather_layout.setContentsMargins(10, 10, 10, 10)
        
        weather_title = QLabel("Weather/Atmospheric Compensation")
        weather_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        weather_layout.addWidget(weather_title)
        
        self.weather_table = VETableWidget()
        weather_layout.addWidget(self.weather_table, stretch=1)
        
        tabs.addTab(weather_tab, "Weather")
        
        main_layout.addWidget(tabs, stretch=1)
        
        # Settings
        settings_group = QGroupBox("Site Table Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        settings_layout = QGridLayout()
        
        settings_layout.addWidget(QLabel("Barometric Pressure Sensor:"), 0, 0)
        self.baro_sensor = QCheckBox("Enabled")
        settings_layout.addWidget(self.baro_sensor, 0, 1)
        
        settings_layout.addWidget(QLabel("Air Temperature Sensor:"), 1, 0)
        self.air_temp_sensor = QCheckBox("Enabled")
        settings_layout.addWidget(self.air_temp_sensor, 1, 1)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_btn = QPushButton("Apply Settings")
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #0080ff;
                color: #ffffff;
                border: none;
                padding: 8px 20px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0066cc;
            }
        """)
        button_layout.addWidget(self.apply_btn)
        
        main_layout.addLayout(button_layout)


class GearChangeIgnitionCutTab(QWidget):
    """Gear Change Ignition Cut control tab."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup Gear Change Ignition Cut tab."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Title
        title = QLabel("Gear Change Ignition Cut - Faster Shifts")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        main_layout.addWidget(title)
        
        # Description
        desc = QLabel("Temporarily cuts ignition during gear changes to reduce engine load and enable faster shifts")
        desc.setStyleSheet("font-size: 11px; color: #aaaaaa;")
        main_layout.addWidget(desc)
        
        # Enable checkbox
        enable_layout = QHBoxLayout()
        self.enable_checkbox = QCheckBox("Enable Gear Change Ignition Cut")
        self.enable_checkbox.setStyleSheet("font-size: 12px; color: #ffffff;")
        enable_layout.addWidget(self.enable_checkbox)
        enable_layout.addStretch()
        main_layout.addLayout(enable_layout)
        
        # Settings group
        settings_group = QGroupBox("Gear Change Cut Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        settings_layout = QGridLayout()
        
        settings_layout.addWidget(QLabel("Cut Duration:"), 0, 0)
        self.cut_duration = QDoubleSpinBox()
        self.cut_duration.setRange(10.0, 200.0)
        self.cut_duration.setValue(50.0)
        self.cut_duration.setSuffix(" ms")
        settings_layout.addWidget(self.cut_duration, 0, 1)
        
        settings_layout.addWidget(QLabel("Detection Method:"), 1, 0)
        self.detection_method = QComboBox()
        self.detection_method.addItems(["Gear Position Sensor", "Clutch Switch", "Both"])
        settings_layout.addWidget(self.detection_method, 1, 1)
        
        settings_layout.addWidget(QLabel("RPM Threshold:"), 2, 0)
        self.rpm_threshold = QSpinBox()
        self.rpm_threshold.setRange(2000, 10000)
        self.rpm_threshold.setValue(4000)
        self.rpm_threshold.setSuffix(" RPM")
        settings_layout.addWidget(self.rpm_threshold, 2, 1)
        
        settings_layout.addWidget(QLabel("Cut Percentage:"), 3, 0)
        self.cut_percentage = QDoubleSpinBox()
        self.cut_percentage.setRange(0.0, 100.0)
        self.cut_percentage.setValue(100.0)
        self.cut_percentage.setSuffix(" %")
        settings_layout.addWidget(self.cut_percentage, 3, 1)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # Gear-specific settings table
        gear_group = QGroupBox("Gear-Specific Cut Settings")
        gear_group.setStyleSheet(settings_group.styleSheet())
        gear_layout = QVBoxLayout()
        
        self.gear_table = QTableWidget()
        self.gear_table.setRowCount(6)  # 6 gears
        self.gear_table.setColumnCount(3)  # Gear, Duration, Enabled
        self.gear_table.setHorizontalHeaderLabels(["Gear", "Cut Duration (ms)", "Enabled"])
        self.gear_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        gear_layout.addWidget(self.gear_table)
        
        gear_group.setLayout(gear_layout)
        main_layout.addWidget(gear_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_btn = QPushButton("Apply Settings")
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #0080ff;
                color: #ffffff;
                border: none;
                padding: 8px 20px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0066cc;
            }
        """)
        button_layout.addWidget(self.apply_btn)
        
        main_layout.addLayout(button_layout)


class CAMControlTab(QWidget):
    """Variable Cam Timing (CAM Control) tab."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup CAM Control tab."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Title
        title = QLabel("Variable Cam Timing (CAM Control)")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        main_layout.addWidget(title)
        
        # Description
        desc = QLabel("Control variable valve timing systems for optimal performance across RPM range")
        desc.setStyleSheet("font-size: 11px; color: #aaaaaa;")
        main_layout.addWidget(desc)
        
        # Tabs for intake and exhaust
        tabs = QTabWidget()
        tabs.setStyleSheet("""
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
        
        # Intake cam tab
        intake_tab = QWidget()
        intake_layout = QVBoxLayout(intake_tab)
        intake_layout.setContentsMargins(10, 10, 10, 10)
        
        intake_title = QLabel("Intake Cam Timing")
        intake_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        intake_layout.addWidget(intake_title)
        
        self.intake_cam_table = VETableWidget()
        intake_layout.addWidget(self.intake_cam_table, stretch=1)
        
        tabs.addTab(intake_tab, "Intake")
        
        # Exhaust cam tab
        exhaust_tab = QWidget()
        exhaust_layout = QVBoxLayout(exhaust_tab)
        exhaust_layout.setContentsMargins(10, 10, 10, 10)
        
        exhaust_title = QLabel("Exhaust Cam Timing")
        exhaust_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        exhaust_layout.addWidget(exhaust_title)
        
        self.exhaust_cam_table = VETableWidget()
        exhaust_layout.addWidget(self.exhaust_cam_table, stretch=1)
        
        tabs.addTab(exhaust_tab, "Exhaust")
        
        main_layout.addWidget(tabs, stretch=1)
        
        # Settings
        settings_group = QGroupBox("CAM Control Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        settings_layout = QGridLayout()
        
        settings_layout.addWidget(QLabel("Actuator Type:"), 0, 0)
        self.actuator_type = QComboBox()
        self.actuator_type.addItems(["Hydraulic", "Electric", "Both"])
        settings_layout.addWidget(self.actuator_type, 0, 1)
        
        settings_layout.addWidget(QLabel("Position Feedback:"), 1, 0)
        self.position_feedback = QCheckBox("Enabled")
        settings_layout.addWidget(self.position_feedback, 1, 1)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_btn = QPushButton("Apply Settings")
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #0080ff;
                color: #ffffff;
                border: none;
                padding: 8px 20px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0066cc;
            }
        """)
        button_layout.addWidget(self.apply_btn)
        
        main_layout.addLayout(button_layout)


class ServoMotorControlTab(QWidget):
    """Servo Motor Control tab."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup Servo Motor Control tab."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Title
        title = QLabel("Servo Motor Control - Precise Motor Control")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        main_layout.addWidget(title)
        
        # Description
        desc = QLabel("Control servo motors for electronic throttle bodies, variable intake systems, etc.")
        desc.setStyleSheet("font-size: 11px; color: #aaaaaa;")
        main_layout.addWidget(desc)
        
        # Enable checkbox
        enable_layout = QHBoxLayout()
        self.enable_checkbox = QCheckBox("Enable Servo Motor Control")
        self.enable_checkbox.setStyleSheet("font-size: 12px; color: #ffffff;")
        enable_layout.addWidget(self.enable_checkbox)
        enable_layout.addStretch()
        main_layout.addLayout(enable_layout)
        
        # Servo selection
        servo_group = QGroupBox("Servo Motor Configuration")
        servo_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        servo_layout = QGridLayout()
        
        servo_layout.addWidget(QLabel("Servo Application:"), 0, 0)
        self.servo_application = QComboBox()
        self.servo_application.addItems(["Electronic Throttle", "Variable Intake", "Boost Control", "Wastegate", "Custom"])
        servo_layout.addWidget(self.servo_application, 0, 1)
        
        servo_layout.addWidget(QLabel("Position Feedback:"), 1, 0)
        self.position_feedback = QCheckBox("Enabled")
        servo_layout.addWidget(self.position_feedback, 1, 1)
        
        servo_layout.addWidget(QLabel("Control Mode:"), 2, 0)
        self.control_mode = QComboBox()
        self.control_mode.addItems(["Open Loop", "Closed Loop", "Hybrid"])
        servo_layout.addWidget(self.control_mode, 2, 1)
        
        servo_group.setLayout(servo_layout)
        main_layout.addWidget(servo_group)
        
        # Position map table
        position_group = QGroupBox("Servo Position Map (RPM vs Load)")
        position_group.setStyleSheet(servo_group.styleSheet())
        position_layout = QVBoxLayout()
        
        self.position_table = VETableWidget()
        position_layout.addWidget(self.position_table)
        
        position_group.setLayout(position_layout)
        main_layout.addWidget(position_group, stretch=1)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_btn = QPushButton("Apply Settings")
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #0080ff;
                color: #ffffff;
                border: none;
                padding: 8px 20px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0066cc;
            }
        """)
        button_layout.addWidget(self.apply_btn)
        
        main_layout.addLayout(button_layout)


__all__ = [
    "HiLoInjectionTab",
    "MultiPulseInjectionTab",
    "InjectionTimingTab",
    "ColdStartFuelTab",
    "SiteTablesTab",
    "GearChangeIgnitionCutTab",
    "CAMControlTab",
    "ServoMotorControlTab",
]

