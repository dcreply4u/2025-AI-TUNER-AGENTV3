"""
Sensors Tab
Comprehensive sensor configuration and monitoring with sub-tabs for each sensor type
"""

from __future__ import annotations

from typing import Dict, Optional, List

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QComboBox,
    QDoubleSpinBox,
    QSpinBox,
    QCheckBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSizePolicy,
    QSlider,
    QLineEdit,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size

from ui.ecu_tuning_widgets import AnalogGauge


class SensorSubTab(QWidget):
    """Base class for sensor sub-tabs."""
    
    def __init__(self, sensor_name: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.sensor_name = sensor_name
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup sensor tab UI."""
        layout = QVBoxLayout(self)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        # Content layout
        content_layout = QHBoxLayout()
        content_layout.setSpacing(get_scaled_size(15))
        
        # Left: Gauge/Display
        left_panel = self._create_display_panel()
        content_layout.addWidget(left_panel, stretch=1)
        
        # Center: Settings
        center_panel = self._create_settings_panel()
        content_layout.addWidget(center_panel, stretch=2)
        
        # Right: Calibration/Advanced
        right_panel = self._create_calibration_panel()
        content_layout.addWidget(right_panel, stretch=1)
        
        layout.addLayout(content_layout, stretch=1)
        
    def _create_display_panel(self) -> QWidget:
        """Create display panel with gauge."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        panel.setMaximumWidth(get_scaled_size(250))
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        # Gauge
        self.gauge = self._create_gauge()
        if self.gauge:
            layout.addWidget(self.gauge)
            
        layout.addStretch()
        return panel
        
    def _create_gauge(self) -> Optional[AnalogGauge]:
        """Create gauge for sensor. Override in subclasses."""
        return None
        
    def _create_settings_panel(self) -> QWidget:
        """Create settings panel. Override in subclasses."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        layout = QVBoxLayout(panel)
        layout.addWidget(QLabel("Settings panel"))
        return panel
        
    def _create_calibration_panel(self) -> QWidget:
        """Create calibration panel."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        panel.setMaximumWidth(get_scaled_size(300))
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        # Calibration settings
        cal_group = QGroupBox("Calibration")
        group_font = get_scaled_font_size(12)
        group_border = get_scaled_size(1)
        group_radius = get_scaled_size(3)
        group_margin = get_scaled_size(10)
        cal_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        cal_layout = QVBoxLayout()
        
        cal_layout.addWidget(QLabel("Offset:"))
        self.offset = QDoubleSpinBox()
        self.offset.setRange(-1000, 1000)
        self.offset.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        cal_layout.addWidget(self.offset)
        
        cal_layout.addWidget(QLabel("Multiplier:"))
        self.multiplier = QDoubleSpinBox()
        self.multiplier.setRange(0.01, 10.0)
        self.multiplier.setValue(1.0)
        self.multiplier.setDecimals(3)
        self.multiplier.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        cal_layout.addWidget(self.multiplier)
        
        cal_group.setLayout(cal_layout)
        layout.addWidget(cal_group)
        
        layout.addStretch()
        return panel
        
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update sensor with telemetry data."""
        if hasattr(self, 'gauge') and self.gauge:
            data_key = self._get_data_key()
            value = data.get(data_key, 0)
            # Apply calibration
            if hasattr(self, 'offset') and hasattr(self, 'multiplier'):
                value = (value + self.offset.value()) * self.multiplier.value()
            self.gauge.set_value(value)
            
    def _get_data_key(self) -> str:
        """Get data key for this sensor. Override in subclasses."""
        return self.sensor_name.replace(" ", "_")


# Individual sensor sub-tabs
class KnockSensorTab(SensorSubTab):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Knock Sensor", parent)
        
    def _create_gauge(self) -> AnalogGauge:
        return AnalogGauge("Knock Level", 0, 100, unit="%", warning_start=80, warning_end=100, warning_color="#ff0000")
        
    def _create_settings_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        settings_group = QGroupBox("Knock Sensor Settings")
        group_font = get_scaled_font_size(12)
        settings_group.setStyleSheet(f"font-size: {group_font}px; font-weight: bold; color: #ffffff; border: 1px solid #404040;")
        settings_layout = QVBoxLayout()
        
        settings_layout.addWidget(QLabel("Sensitivity:"))
        self.sensitivity = QDoubleSpinBox()
        self.sensitivity.setRange(0.1, 10.0)
        self.sensitivity.setValue(1.0)
        self.sensitivity.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.sensitivity)
        
        settings_layout.addWidget(QLabel("Frequency Range (Hz):"))
        self.freq_min = QSpinBox()
        self.freq_min.setRange(1000, 20000)
        self.freq_min.setValue(5000)
        self.freq_min.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(QLabel("Min:"))
        settings_layout.addWidget(self.freq_min)
        
        self.freq_max = QSpinBox()
        self.freq_max.setRange(1000, 20000)
        self.freq_max.setValue(15000)
        self.freq_max.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(QLabel("Max:"))
        settings_layout.addWidget(self.freq_max)
        
        self.knock_enabled = QCheckBox("Knock Detection Enabled")
        self.knock_enabled.setChecked(True)
        self.knock_enabled.setStyleSheet("color: #ffffff;")
        settings_layout.addWidget(self.knock_enabled)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        return panel
        
    def _get_data_key(self) -> str:
        return "knock_level"


class MAFSensorTab(SensorSubTab):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Mass Air Flow Sensor", parent)
        
    def _create_gauge(self) -> AnalogGauge:
        return AnalogGauge("MAF", 0, 500, unit="g/s")
        
    def _create_settings_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        settings_group = QGroupBox("MAF Sensor Settings")
        group_font = get_scaled_font_size(12)
        settings_group.setStyleSheet(f"font-size: {group_font}px; font-weight: bold; color: #ffffff; border: 1px solid #404040;")
        settings_layout = QVBoxLayout()
        
        settings_layout.addWidget(QLabel("Sensor Type:"))
        self.sensor_type = QComboBox()
        self.sensor_type.addItems(["Hot Wire", "Hot Film", "Vane", "MAP-based"])
        self.sensor_type.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.sensor_type)
        
        settings_layout.addWidget(QLabel("Max Flow Rate (g/s):"))
        self.max_flow = QDoubleSpinBox()
        self.max_flow.setRange(0, 1000)
        self.max_flow.setValue(500)
        self.max_flow.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.max_flow)
        
        self.maf_enabled = QCheckBox("MAF Enabled")
        self.maf_enabled.setChecked(True)
        self.maf_enabled.setStyleSheet("color: #ffffff;")
        settings_layout.addWidget(self.maf_enabled)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        return panel
        
    def _get_data_key(self) -> str:
        return "MAF"


class OxygenSensorTab(SensorSubTab):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Oxygen Sensor", parent)
        
    def _create_gauge(self) -> AnalogGauge:
        return AnalogGauge("O2 Sensor", 0, 1.0, unit="V", warning_start=0.8, warning_end=1.0, warning_color="#ff0000")
        
    def _create_settings_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        settings_group = QGroupBox("Oxygen Sensor Settings")
        group_font = get_scaled_font_size(12)
        settings_group.setStyleSheet(f"font-size: {group_font}px; font-weight: bold; color: #ffffff; border: 1px solid #404040;")
        settings_layout = QVBoxLayout()
        
        settings_layout.addWidget(QLabel("Sensor Type:"))
        self.sensor_type = QComboBox()
        self.sensor_type.addItems(["Narrowband", "Wideband", "UEGO"])
        self.sensor_type.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.sensor_type)
        
        settings_layout.addWidget(QLabel("Bank:"))
        self.bank = QComboBox()
        self.bank.addItems(["Bank 1", "Bank 2", "Both"])
        self.bank.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.bank)
        
        settings_layout.addWidget(QLabel("Heater Control:"))
        self.heater_enabled = QCheckBox("Heater Enabled")
        self.heater_enabled.setChecked(True)
        self.heater_enabled.setStyleSheet("color: #ffffff;")
        settings_layout.addWidget(self.heater_enabled)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        return panel
        
    def _get_data_key(self) -> str:
        return "O2_voltage"


class MAPSensorTab(SensorSubTab):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Manifold Absolute Pressure Sensor", parent)
        
    def _create_gauge(self) -> AnalogGauge:
        return AnalogGauge("MAP", -80, 240, unit="kPa", warning_start=200, warning_end=240, warning_color="#ff0000")
        
    def _create_settings_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        settings_group = QGroupBox("MAP Sensor Settings")
        group_font = get_scaled_font_size(12)
        settings_group.setStyleSheet(f"font-size: {group_font}px; font-weight: bold; color: #ffffff; border: 1px solid #404040;")
        settings_layout = QVBoxLayout()
        
        settings_layout.addWidget(QLabel("Sensor Type:"))
        self.sensor_type = QComboBox()
        self.sensor_type.addItems(["Absolute", "Relative", "Barometric"])
        self.sensor_type.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.sensor_type)
        
        settings_layout.addWidget(QLabel("Max Pressure (kPa):"))
        self.max_pressure = QDoubleSpinBox()
        self.max_pressure.setRange(0, 500)
        self.max_pressure.setValue(240)
        self.max_pressure.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.max_pressure)
        
        settings_layout.addWidget(QLabel("Barometric Reference (kPa):"))
        self.baro_ref = QDoubleSpinBox()
        self.baro_ref.setRange(80, 110)
        self.baro_ref.setValue(101.3)
        self.baro_ref.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.baro_ref)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        return panel
        
    def _get_data_key(self) -> str:
        return "MAP"


class CoolantSensorTab(SensorSubTab):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Coolant Sensor", parent)
        
    def _create_gauge(self) -> AnalogGauge:
        return AnalogGauge("Coolant Temp", -40, 150, unit="°C", warning_start=100, warning_end=150, warning_color="#ff0000")
        
    def _create_settings_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        settings_group = QGroupBox("Coolant Sensor Settings")
        group_font = get_scaled_font_size(12)
        settings_group.setStyleSheet(f"font-size: {group_font}px; font-weight: bold; color: #ffffff; border: 1px solid #404040;")
        settings_layout = QVBoxLayout()
        
        settings_layout.addWidget(QLabel("Sensor Type:"))
        self.sensor_type = QComboBox()
        self.sensor_type.addItems(["NTC Thermistor", "RTD", "Thermocouple"])
        self.sensor_type.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.sensor_type)
        
        settings_layout.addWidget(QLabel("Overheat Threshold (°C):"))
        self.overheat_threshold = QDoubleSpinBox()
        self.overheat_threshold.setRange(80, 150)
        self.overheat_threshold.setValue(105)
        self.overheat_threshold.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.overheat_threshold)
        
        self.fan_control = QCheckBox("Fan Control Enabled")
        self.fan_control.setChecked(True)
        self.fan_control.setStyleSheet("color: #ffffff;")
        settings_layout.addWidget(self.fan_control)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        return panel
        
    def _get_data_key(self) -> str:
        return "Coolant_Temp"


class CrankPositionSensorTab(SensorSubTab):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Crankshaft Position Sensor", parent)
        
    def _create_gauge(self) -> AnalogGauge:
        return AnalogGauge("Crank RPM", 0, 10000, unit="RPM", warning_start=7500, warning_end=10000, warning_color="#ffaa00")
        
    def _create_settings_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        settings_group = QGroupBox("Crank Position Sensor Settings")
        group_font = get_scaled_font_size(12)
        settings_group.setStyleSheet(f"font-size: {group_font}px; font-weight: bold; color: #ffffff; border: 1px solid #404040;")
        settings_layout = QVBoxLayout()
        
        settings_layout.addWidget(QLabel("Trigger Pattern:"))
        self.trigger_pattern = QComboBox()
        self.trigger_pattern.addItems(["36-1", "60-2", "24+1", "Custom"])
        self.trigger_pattern.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.trigger_pattern)
        
        settings_layout.addWidget(QLabel("Teeth Count:"))
        self.teeth_count = QSpinBox()
        self.teeth_count.setRange(1, 100)
        self.teeth_count.setValue(36)
        self.teeth_count.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.teeth_count)
        
        settings_layout.addWidget(QLabel("Missing Teeth:"))
        self.missing_teeth = QSpinBox()
        self.missing_teeth.setRange(0, 10)
        self.missing_teeth.setValue(1)
        self.missing_teeth.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.missing_teeth)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        return panel
        
    def _get_data_key(self) -> str:
        return "RPM"


class SpeedSensorTab(SensorSubTab):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Speed Sensor", parent)
        
    def _create_gauge(self) -> AnalogGauge:
        return AnalogGauge("Vehicle Speed", 0, 200, unit="mph")
        
    def _create_settings_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        settings_group = QGroupBox("Speed Sensor Settings")
        group_font = get_scaled_font_size(12)
        settings_group.setStyleSheet(f"font-size: {group_font}px; font-weight: bold; color: #ffffff; border: 1px solid #404040;")
        settings_layout = QVBoxLayout()
        
        settings_layout.addWidget(QLabel("Sensor Type:"))
        self.sensor_type = QComboBox()
        self.sensor_type.addItems(["Hall Effect", "Magnetic", "GPS", "Wheel Speed"])
        self.sensor_type.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.sensor_type)
        
        settings_layout.addWidget(QLabel("Pulses per Revolution:"))
        self.ppr = QSpinBox()
        self.ppr.setRange(1, 100)
        self.ppr.setValue(40)
        self.ppr.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.ppr)
        
        settings_layout.addWidget(QLabel("Tire Diameter (inches):"))
        self.tire_diameter = QDoubleSpinBox()
        self.tire_diameter.setRange(10, 50)
        self.tire_diameter.setValue(26)
        self.tire_diameter.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.tire_diameter)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        return panel
        
    def _get_data_key(self) -> str:
        return "Speed"


class TPSensorTab(SensorSubTab):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Throttle Position Sensor", parent)
        
    def _create_gauge(self) -> AnalogGauge:
        return AnalogGauge("Throttle Position", 0, 100, unit="%")
        
    def _create_settings_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        settings_group = QGroupBox("TPS Settings")
        group_font = get_scaled_font_size(12)
        settings_group.setStyleSheet(f"font-size: {group_font}px; font-weight: bold; color: #ffffff; border: 1px solid #404040;")
        settings_layout = QVBoxLayout()
        
        settings_layout.addWidget(QLabel("Sensor Type:"))
        self.sensor_type = QComboBox()
        self.sensor_type.addItems(["Potentiometer", "Hall Effect", "Contactless"])
        self.sensor_type.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.sensor_type)
        
        settings_layout.addWidget(QLabel("Closed Position (%):"))
        self.closed_pos = QDoubleSpinBox()
        self.closed_pos.setRange(0, 20)
        self.closed_pos.setValue(0)
        self.closed_pos.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.closed_pos)
        
        settings_layout.addWidget(QLabel("WOT Position (%):"))
        self.wot_pos = QDoubleSpinBox()
        self.wot_pos.setRange(80, 100)
        self.wot_pos.setValue(100)
        self.wot_pos.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.wot_pos)
        
        self.tps_calibrate_btn = QPushButton("Calibrate TPS")
        self.tps_calibrate_btn.setStyleSheet("background-color: #0080ff; color: #ffffff; padding: 5px;")
        settings_layout.addWidget(self.tps_calibrate_btn)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        return panel
        
    def _get_data_key(self) -> str:
        return "Throttle_Position"


class FuelTempSensorTab(SensorSubTab):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Fuel Temperature Sensor", parent)
        
    def _create_gauge(self) -> AnalogGauge:
        return AnalogGauge("Fuel Temp", -40, 150, unit="°C")
        
    def _get_data_key(self) -> str:
        return "Fuel_Temp"


class CamPositionSensorTab(SensorSubTab):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Camshaft Position Sensor", parent)
        
    def _create_gauge(self) -> AnalogGauge:
        return AnalogGauge("Cam Position", 0, 720, unit="deg")
        
    def _get_data_key(self) -> str:
        return "Cam_Position"


class IATSensorTab(SensorSubTab):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Air Intake Temperature Sensor", parent)
        
    def _create_gauge(self) -> AnalogGauge:
        return AnalogGauge("IAT", -40, 150, unit="°C", warning_start=50, warning_end=150, warning_color="#ff8000")
        
    def _get_data_key(self) -> str:
        return "IAT"


class OilPressureSensorTab(SensorSubTab):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Oil Pressure Sensor", parent)
        
    def _create_gauge(self) -> AnalogGauge:
        return AnalogGauge("Oil Pressure", 0, 100, unit="psi", warning_start=0, warning_end=20, warning_color="#ff0000")
        
    def _get_data_key(self) -> str:
        return "Oil_Pressure"


class VoltageSensorTab(SensorSubTab):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Voltage Sensor", parent)
        
    def _create_gauge(self) -> AnalogGauge:
        return AnalogGauge("Voltage", 10, 16, unit="V", warning_start=10, warning_end=11.5, warning_color="#ff0000")
        
    def _get_data_key(self) -> str:
        return "Voltage"


class BoostPressureSensorTab(SensorSubTab):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Boost Pressure Sensor", parent)
        
    def _create_gauge(self) -> AnalogGauge:
        return AnalogGauge("Boost Pressure", 0, 50, unit="psi", warning_start=40, warning_end=50, warning_color="#ff0000")
        
    def _get_data_key(self) -> str:
        return "Boost_Pressure"


class FuelPressureSensorTab(SensorSubTab):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Fuel Pressure Sensor", parent)
        
    def _create_gauge(self) -> AnalogGauge:
        return AnalogGauge("Fuel Pressure", 0, 100, unit="psi", warning_start=0, warning_end=30, warning_color="#ff0000")
        
    def _get_data_key(self) -> str:
        return "Fuel_Pressure"


class EGTPerCylinderTab(SensorSubTab):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("EGT Per Cylinder", parent)
        
    def _create_display_panel(self) -> QWidget:
        """Create display with multiple EGT gauges."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        # Create gauges for each cylinder
        self.egt_gauges = {}
        for cyl in range(1, 9):  # Up to 8 cylinders
            gauge = AnalogGauge(f"EGT Cyl {cyl}", 0, 1200, unit="°C", warning_start=950, warning_end=1200, warning_color="#ff0000")
            self.egt_gauges[cyl] = gauge
            layout.addWidget(gauge)
            
        layout.addStretch()
        return panel
        
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update EGT gauges for each cylinder."""
        for cyl, gauge in self.egt_gauges.items():
            key = f"EGT_Cyl_{cyl}"
            value = data.get(key, data.get(f"EGT_Cylinder_{cyl}", 0))
            gauge.set_value(value)


class SensorsTab(QWidget):
    """Main Sensors tab with sub-tabs for each sensor type."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup sensors tab."""
        main_layout = QVBoxLayout(self)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        self.setStyleSheet("background-color: #1a1a1a;")
        
        # Control bar
        control_bar = self._create_control_bar()
        main_layout.addWidget(control_bar)
        
        # Sub-tabs for sensors
        self.sensor_tabs = QTabWidget()
        tab_border = get_scaled_size(1)
        tab_padding_v = get_scaled_size(6)
        tab_padding_h = get_scaled_size(15)
        tab_font = get_scaled_font_size(10)
        self.sensor_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: {tab_border}px solid #404040;
                background-color: #1a1a1a;
            }}
            QTabBar::tab {{
                background-color: #2a2a2a;
                color: #ffffff;
                padding: {tab_padding_v}px {tab_padding_h}px;
                margin-right: {get_scaled_size(2)}px;
                border: {tab_border}px solid #404040;
                font-size: {tab_font}px;
            }}
            QTabBar::tab:selected {{
                background-color: #1a1a1a;
                border-bottom: {get_scaled_size(2)}px solid #0080ff;
            }}
        """)
        
        # Add sensor sub-tabs
        sensors = [
            ("GPIO Interface", None),  # Special case - will add GPIO tab separately
            ("Knock Sensor", KnockSensorTab),
            ("MAF Sensor", MAFSensorTab),
            ("Oxygen Sensor", OxygenSensorTab),
            ("MAP Sensor", MAPSensorTab),
            ("Coolant Sensor", CoolantSensorTab),
            ("Crank Position", CrankPositionSensorTab),
            ("Speed Sensor", SpeedSensorTab),
            ("TPS", TPSensorTab),
            ("Fuel Temp", FuelTempSensorTab),
            ("Cam Position", CamPositionSensorTab),
            ("IAT", IATSensorTab),
            ("Oil Pressure", OilPressureSensorTab),
            ("Voltage", VoltageSensorTab),
            ("Boost Pressure", BoostPressureSensorTab),
            ("Fuel Pressure", FuelPressureSensorTab),
            ("EGT Per Cylinder", EGTPerCylinderTab),
        ]
        
        # Add GPIO tab first (special handling)
        try:
            from ui.gpio_interface_tab import GPIOInterfaceTab
            gpio_tab = GPIOInterfaceTab(self)
            self.sensor_tabs.insertTab(0, gpio_tab, "🔌 GPIO Interface")
        except Exception as e:
            print(f"[WARN] Could not create GPIO Interface tab: {e}")
        
        # Add CAN Interface tab (special handling)
        try:
            from ui.can_interface_tab import CANInterfaceTab
            can_tab = CANInterfaceTab(self)
            self.sensor_tabs.insertTab(1, can_tab, "🚗 CAN Bus Interface")
        except Exception as e:
            print(f"[WARN] Could not create CAN Bus Interface tab: {e}")
        
        # Add other sensor tabs
        for name, tab_class in sensors:
            if name == "GPIO Interface":  # Skip, already added
                continue
            if tab_class is None:
                continue
            try:
                tab = tab_class(self)
                self.sensor_tabs.addTab(tab, name)
            except Exception as e:
                print(f"[WARN] Could not create {name} tab: {e}")
        
        main_layout.addWidget(self.sensor_tabs, stretch=1)
        
        # Add graphing and import/export tabs
        from ui.module_feature_helper import add_graphing_tab, add_import_export_tab
        graph_widget = add_graphing_tab(self.sensor_tabs, "Sensors")
        self.sensor_graph = graph_widget
        add_import_export_tab(self.sensor_tabs, "Sensors")
        
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
        
        title = QLabel("Sensors Configuration")
        title_font = get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("Refresh All")
        btn_padding_v = get_scaled_size(5)
        btn_padding_h = get_scaled_size(10)
        btn_font = get_scaled_font_size(11)
        refresh_btn.setStyleSheet(f"background-color: #404040; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px; font-size: {btn_font}px;")
        layout.addWidget(refresh_btn)
        
        return bar
        
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update all sensor tabs with telemetry data."""
        for i in range(self.sensor_tabs.count()):
            tab = self.sensor_tabs.widget(i)
            if tab and hasattr(tab, 'update_telemetry'):
                try:
                    tab.update_telemetry(data)
                except Exception:
                    pass
        
        # Update graph if available
        if hasattr(self, 'sensor_graph') and self.sensor_graph:
            try:
                if hasattr(self.sensor_graph, 'update_data'):
                    self.sensor_graph.update_data(data)
                elif hasattr(self.sensor_graph, 'add_data'):
                    for key, value in data.items():
                        self.sensor_graph.add_data(key, value)
            except Exception:
                pass


__all__ = ["SensorsTab"]



