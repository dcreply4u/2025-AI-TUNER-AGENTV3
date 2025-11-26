"""VBOX IMU Features Tab - IMU integration and Kalman filter features."""

from __future__ import annotations
from typing import Dict, Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QFormLayout, QCheckBox, QDoubleSpinBox, QPushButton, QLabel, QScrollArea
from ui.ui_scaling import get_scaled_size


class VBOXIMUFeaturesTab(QWidget):
    """IMU Features sub-tab."""
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # IMU Integration
        imu_group = QGroupBox("IMU Integration")
        imu_form = QFormLayout()
        self.imu_enable = QCheckBox("Enable IMU")
        imu_form.addRow("IMU:", self.imu_enable)
        self.roof_mount = QCheckBox("Roof Mount Mode")
        imu_form.addRow("Roof Mount:", self.roof_mount)
        self.kalman_filter = QCheckBox("Enable Kalman Filter")
        imu_form.addRow("Kalman Filter:", self.kalman_filter)
        imu_group.setLayout(imu_form)
        content_layout.addWidget(imu_group)
        
        # Offsets
        offset_group = QGroupBox("IMU Offsets")
        offset_form = QFormLayout()
        self.antenna_x = QDoubleSpinBox()
        self.antenna_y = QDoubleSpinBox()
        self.antenna_z = QDoubleSpinBox()
        offset_form.addRow("Antenna to IMU X:", self.antenna_x)
        offset_form.addRow("Antenna to IMU Y:", self.antenna_y)
        offset_form.addRow("Antenna to IMU Z:", self.antenna_z)
        offset_group.setLayout(offset_form)
        content_layout.addWidget(offset_group)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
    
    def update_telemetry(self, data: Dict[str, float]) -> None:
        pass

