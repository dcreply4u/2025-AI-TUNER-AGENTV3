"""
VBOX GPS Features Tab
GPS/GNSS features including dual antenna, RTK/DGPS, and GPS configuration.
"""

from __future__ import annotations

from typing import Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QPushButton,
    QCheckBox,
    QFormLayout,
    QScrollArea,
)

from ui.ui_scaling import get_scaled_size, get_scaled_font_size


class VBOXGPSFeaturesTab(QWidget):
    """GPS Features sub-tab with VBOX 3i GPS capabilities."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Setup GPS features UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #1a1a1a; }")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(12)
        
        # Basic GPS Settings
        basic_group = QGroupBox("Basic GPS Settings")
        basic_layout = QFormLayout()
        
        self.gps_rate_combo = QComboBox()
        self.gps_rate_combo.addItems(["1 Hz", "5 Hz", "10 Hz", "20 Hz", "50 Hz", "100 Hz"])
        self.gps_rate_combo.setCurrentText("10 Hz")
        basic_layout.addRow("GPS Sample Rate:", self.gps_rate_combo)
        
        self.optimization_combo = QComboBox()
        self.optimization_combo.addItems(["High Dynamics", "Medium Dynamics", "Low Dynamics"])
        self.optimization_combo.setCurrentText("Medium Dynamics")
        basic_layout.addRow("GPS Optimization:", self.optimization_combo)
        
        self.elevation_mask_spin = QDoubleSpinBox()
        self.elevation_mask_spin.setRange(10.0, 25.0)
        self.elevation_mask_spin.setValue(15.0)
        self.elevation_mask_spin.setSuffix("°")
        basic_layout.addRow("Elevation Mask:", self.elevation_mask_spin)
        
        self.leap_second_spin = QSpinBox()
        self.leap_second_spin.setRange(0, 30)
        self.leap_second_spin.setValue(18)
        self.leap_second_spin.setSuffix("s")
        basic_layout.addRow("Leap Second:", self.leap_second_spin)
        
        self.glonass_check = QCheckBox("Enable GLONASS")
        self.glonass_check.setChecked(False)
        basic_layout.addRow("GLONASS Support:", self.glonass_check)
        
        coldstart_btn = QPushButton("GPS Coldstart")
        coldstart_btn.clicked.connect(self._on_coldstart)
        basic_layout.addRow("GPS Coldstart:", coldstart_btn)
        
        basic_group.setLayout(basic_layout)
        content_layout.addWidget(basic_group)
        
        # Dual Antenna Settings
        dual_group = QGroupBox("Dual Antenna Configuration")
        dual_layout = QFormLayout()
        
        self.dual_antenna_check = QCheckBox("Enable Dual Antenna Mode")
        self.dual_antenna_check.setChecked(False)
        self.dual_antenna_check.toggled.connect(self._on_dual_antenna_toggled)
        dual_layout.addRow("Dual Antenna:", self.dual_antenna_check)
        
        self.antenna_separation_spin = QDoubleSpinBox()
        self.antenna_separation_spin.setRange(0.1, 10.0)
        self.antenna_separation_spin.setValue(1.0)
        self.antenna_separation_spin.setSuffix(" m")
        self.antenna_separation_spin.setEnabled(False)
        dual_layout.addRow("Antenna Separation:", self.antenna_separation_spin)
        
        self.orientation_test_check = QCheckBox("Enable Orientation Testing")
        self.orientation_test_check.setEnabled(False)
        dual_layout.addRow("Orientation Testing:", self.orientation_test_check)
        
        self.slip_angle_check = QCheckBox("Calculate Slip Angle")
        self.slip_angle_check.setEnabled(False)
        dual_layout.addRow("Slip Angle:", self.slip_angle_check)
        
        self.dual_lock_status_label = QLabel("Status: Disabled")
        self.dual_lock_status_label.setStyleSheet("color: #888;")
        dual_layout.addRow("Lock Status:", self.dual_lock_status_label)
        
        dual_group.setLayout(dual_layout)
        content_layout.addWidget(dual_group)
        
        # RTK/DGPS Settings
        rtk_group = QGroupBox("RTK/DGPS Configuration")
        rtk_layout = QFormLayout()
        
        self.dgps_mode_combo = QComboBox()
        self.dgps_mode_combo.addItems([
            "None",
            "CMR",
            "RTCMv3",
            "NTRIP",
            "MB-Base",
            "MB-Rover",
            "SBAS"
        ])
        self.dgps_mode_combo.setCurrentText("None")
        self.dgps_mode_combo.currentTextChanged.connect(self._on_dgps_mode_changed)
        rtk_layout.addRow("DGPS Mode:", self.dgps_mode_combo)
        
        self.dgps_baud_combo = QComboBox()
        self.dgps_baud_combo.addItems(["19200", "38400", "115200"])
        self.dgps_baud_combo.setCurrentText("115200")
        self.dgps_baud_combo.setEnabled(False)
        rtk_layout.addRow("DGPS Baud Rate:", self.dgps_baud_combo)
        
        self.ntrip_host_edit = QLabel("NTRIP Host: (configure when NTRIP selected)")
        self.ntrip_host_edit.setStyleSheet("color: #888;")
        self.ntrip_host_edit.setEnabled(False)
        rtk_layout.addRow("NTRIP Host:", self.ntrip_host_edit)
        
        self.rtk_status_label = QLabel("RTK Status: Not Active")
        self.rtk_status_label.setStyleSheet("color: #888;")
        rtk_layout.addRow("RTK Status:", self.rtk_status_label)
        
        self.differential_age_label = QLabel("Differential Age: N/A")
        self.differential_age_label.setStyleSheet("color: #888;")
        rtk_layout.addRow("Differential Age:", self.differential_age_label)
        
        rtk_group.setLayout(rtk_layout)
        content_layout.addWidget(rtk_group)
        
        # Solution Type Display
        solution_group = QGroupBox("GPS Solution Information")
        solution_layout = QVBoxLayout()
        
        self.solution_type_label = QLabel("Solution Type: GNSS")
        self.solution_type_label.setStyleSheet("color: #0f0; font-weight: bold;")
        solution_layout.addWidget(self.solution_type_label)
        
        self.position_quality_label = QLabel("Position Quality: Good")
        self.position_quality_label.setStyleSheet("color: #0f0;")
        solution_layout.addWidget(self.position_quality_label)
        
        self.satellites_label = QLabel("Satellites: 0 GPS, 0 GLONASS")
        self.satellites_label.setStyleSheet("color: #888;")
        solution_layout.addWidget(self.satellites_label)
        
        solution_group.setLayout(solution_layout)
        content_layout.addWidget(solution_group)
        
        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
    
    def _on_dual_antenna_toggled(self, checked: bool) -> None:
        """Handle dual antenna enable/disable."""
        self.antenna_separation_spin.setEnabled(checked)
        self.orientation_test_check.setEnabled(checked)
        self.slip_angle_check.setEnabled(checked)
        if checked:
            self.dual_lock_status_label.setText("Status: Initializing...")
            self.dual_lock_status_label.setStyleSheet("color: #ff0;")
        else:
            self.dual_lock_status_label.setText("Status: Disabled")
            self.dual_lock_status_label.setStyleSheet("color: #888;")
    
    def _on_dgps_mode_changed(self, mode: str) -> None:
        """Handle DGPS mode change."""
        enabled = mode != "None"
        self.dgps_baud_combo.setEnabled(enabled)
        self.ntrip_host_edit.setEnabled(enabled)
        if mode == "RTCMv3" or mode == "CMR":
            self.rtk_status_label.setText("RTK Status: Available")
            self.rtk_status_label.setStyleSheet("color: #0f0;")
        else:
            self.rtk_status_label.setText("RTK Status: Not Active")
            self.rtk_status_label.setStyleSheet("color: #888;")
    
    def _on_coldstart(self) -> None:
        """Handle GPS coldstart button."""
        # TODO: Implement GPS coldstart
        print("GPS Coldstart requested")
    
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update GPS status from telemetry data."""
        # Update solution type, position quality, satellites from telemetry
        if "GPS_Satellites" in data:
            gps_sats = int(data.get("GPS_Satellites", 0))
            glonass_sats = int(data.get("GLONASS_Satellites", 0)) if self.glonass_check.isChecked() else 0
            self.satellites_label.setText(f"Satellites: {gps_sats} GPS, {glonass_sats} GLONASS")
        
        if "GPS_Quality" in data:
            quality = data["GPS_Quality"]
            if quality > 0.8:
                self.position_quality_label.setText("Position Quality: Excellent")
                self.position_quality_label.setStyleSheet("color: #0f0;")
            elif quality > 0.5:
                self.position_quality_label.setText("Position Quality: Good")
                self.position_quality_label.setStyleSheet("color: #0f0;")
            else:
                self.position_quality_label.setText("Position Quality: Poor")
                self.position_quality_label.setStyleSheet("color: #f00;")

