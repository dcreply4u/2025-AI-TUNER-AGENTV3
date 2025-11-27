"""
Sensor Settings Dialog - Configure individual sensor display properties
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QDoubleSpinBox,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QGroupBox,
    QSpinBox,
    QMessageBox,
)


@dataclass
class SensorConfig:
    """Configuration for a sensor channel."""
    name: str
    enabled: bool = True
    color: str = "#3498db"
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    alert_min: Optional[float] = None
    alert_max: Optional[float] = None
    smoothing: int = 0  # 0 = no smoothing, 1-10 = smoothing level
    unit: str = ""
    scale: float = 1.0  # Scale factor for display
    offset: float = 0.0  # Offset for display
    axis: int = 0  # Y-axis index (0 = left, 1 = right, etc.)
    line_width: int = 2
    line_style: str = "solid"  # solid, dashed, dotted


class SensorSettingsDialog(QDialog):
    """Dialog for configuring sensor display settings."""
    
    config_changed = Signal(str, SensorConfig)  # Emitted when config changes
    
    def __init__(self, sensor_name: str, current_config: Optional[SensorConfig] = None, parent=None):
        super().__init__(parent)
        self.sensor_name = sensor_name
        self.config = current_config or SensorConfig(name=sensor_name)
        self.setWindowTitle(f"Sensor Settings: {sensor_name}")
        self.setMinimumWidth(500)
        self.setup_ui()
        self.load_config()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel(f"<h2>{self.sensor_name}</h2>")
        layout.addWidget(header)
        
        # Basic settings
        basic_group = QGroupBox("Basic Settings")
        basic_layout = QFormLayout()
        
        self.enabled_cb = QCheckBox("Enable sensor")
        self.enabled_cb.setChecked(self.config.enabled)
        basic_layout.addRow("Enabled:", self.enabled_cb)
        
        # Color picker
        color_layout = QHBoxLayout()
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(60, 30)
        self.color_btn.setStyleSheet(f"background-color: {self.config.color}; border: 1px solid #ccc;")
        self.color_btn.clicked.connect(self._pick_color)
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch()
        basic_layout.addRow("Color:", color_layout)
        
        # Line width
        self.line_width_spin = QSpinBox()
        self.line_width_spin.setRange(1, 10)
        self.line_width_spin.setValue(self.config.line_width)
        basic_layout.addRow("Line Width:", self.line_width_spin)
        
        # Line style
        self.line_style_combo = QComboBox()
        self.line_style_combo.addItems(["solid", "dashed", "dotted"])
        self.line_style_combo.setCurrentText(self.config.line_style)
        basic_layout.addRow("Line Style:", self.line_style_combo)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # Scale settings
        scale_group = QGroupBox("Scale & Display")
        scale_layout = QFormLayout()
        
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.001, 1000.0)
        self.scale_spin.setValue(self.config.scale)
        self.scale_spin.setDecimals(3)
        scale_layout.addRow("Scale Factor:", self.scale_spin)
        
        self.offset_spin = QDoubleSpinBox()
        self.offset_spin.setRange(-10000.0, 10000.0)
        self.offset_spin.setValue(self.config.offset)
        self.offset_spin.setDecimals(2)
        scale_layout.addRow("Offset:", self.offset_spin)
        
        self.unit_edit = QLineEdit(self.config.unit)
        scale_layout.addRow("Unit:", self.unit_edit)
        
        self.axis_spin = QSpinBox()
        self.axis_spin.setRange(0, 3)
        self.axis_spin.setValue(self.config.axis)
        scale_layout.addRow("Y-Axis Index:", self.axis_spin)
        
        scale_group.setLayout(scale_layout)
        layout.addWidget(scale_group)
        
        # Range settings
        range_group = QGroupBox("Value Range")
        range_layout = QFormLayout()
        
        self.min_spin = QDoubleSpinBox()
        self.min_spin.setRange(-100000.0, 100000.0)
        self.min_spin.setValue(self.config.min_value if self.config.min_value is not None else 0.0)
        self.min_spin.setSpecialValueText("Auto")
        range_layout.addRow("Min Value:", self.min_spin)
        
        self.max_spin = QDoubleSpinBox()
        self.max_spin.setRange(-100000.0, 100000.0)
        self.max_spin.setValue(self.config.max_value if self.config.max_value is not None else 100.0)
        self.max_spin.setSpecialValueText("Auto")
        range_layout.addRow("Max Value:", self.max_spin)
        
        range_group.setLayout(range_layout)
        layout.addWidget(range_group)
        
        # Alert settings
        alert_group = QGroupBox("Alerts & Thresholds")
        alert_layout = QFormLayout()
        
        self.alert_min_spin = QDoubleSpinBox()
        self.alert_min_spin.setRange(-100000.0, 100000.0)
        self.alert_min_spin.setValue(self.config.alert_min if self.config.alert_min is not None else 0.0)
        self.alert_min_spin.setSpecialValueText("Disabled")
        alert_layout.addRow("Alert Below:", self.alert_min_spin)
        
        self.alert_max_spin = QDoubleSpinBox()
        self.alert_max_spin.setRange(-100000.0, 100000.0)
        self.alert_max_spin.setValue(self.config.alert_max if self.config.alert_max is not None else 100.0)
        self.alert_max_spin.setSpecialValueText("Disabled")
        alert_layout.addRow("Alert Above:", self.alert_max_spin)
        
        alert_group.setLayout(alert_layout)
        layout.addWidget(alert_group)
        
        # Smoothing
        smoothing_group = QGroupBox("Data Processing")
        smoothing_layout = QFormLayout()
        
        self.smoothing_spin = QSpinBox()
        self.smoothing_spin.setRange(0, 10)
        self.smoothing_spin.setValue(self.config.smoothing)
        self.smoothing_spin.setToolTip("0 = no smoothing, higher = more smoothing")
        smoothing_layout.addRow("Smoothing Level:", self.smoothing_spin)
        
        smoothing_group.setLayout(smoothing_layout)
        layout.addWidget(smoothing_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self._apply_config)
        button_layout.addWidget(self.apply_btn)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self._ok_clicked)
        button_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def load_config(self):
        """Load current config into UI."""
        self.enabled_cb.setChecked(self.config.enabled)
        self.color_btn.setStyleSheet(f"background-color: {self.config.color}; border: 1px solid #ccc;")
        self.line_width_spin.setValue(self.config.line_width)
        self.line_style_combo.setCurrentText(self.config.line_style)
        self.scale_spin.setValue(self.config.scale)
        self.offset_spin.setValue(self.config.offset)
        self.unit_edit.setText(self.config.unit)
        self.axis_spin.setValue(self.config.axis)
        if self.config.min_value is not None:
            self.min_spin.setValue(self.config.min_value)
        if self.config.max_value is not None:
            self.max_spin.setValue(self.config.max_value)
        if self.config.alert_min is not None:
            self.alert_min_spin.setValue(self.config.alert_min)
        if self.config.alert_max is not None:
            self.alert_max_spin.setValue(self.config.alert_max)
        self.smoothing_spin.setValue(self.config.smoothing)
    
    def _pick_color(self):
        """Open color picker dialog."""
        color = QColorDialog.getColor(QColor(self.config.color), self, "Choose Color")
        if color.isValid():
            self.config.color = color.name()
            self.color_btn.setStyleSheet(f"background-color: {self.config.color}; border: 1px solid #ccc;")
    
    def _apply_config(self):
        """Apply configuration without closing dialog."""
        self._save_config()
        self.config_changed.emit(self.sensor_name, self.config)
        QMessageBox.information(self, "Applied", "Settings applied successfully!")
    
    def _ok_clicked(self):
        """Save and close."""
        self._save_config()
        self.config_changed.emit(self.sensor_name, self.config)
        self.accept()
    
    def _save_config(self):
        """Save UI values to config."""
        self.config.enabled = self.enabled_cb.isChecked()
        self.config.line_width = self.line_width_spin.value()
        self.config.line_style = self.line_style_combo.currentText()
        self.config.scale = self.scale_spin.value()
        self.config.offset = self.offset_spin.value()
        self.config.unit = self.unit_edit.text()
        self.config.axis = self.axis_spin.value()
        
        # Handle special values
        min_val = self.min_spin.value()
        self.config.min_value = None if min_val == self.min_spin.minimum() else min_val
        
        max_val = self.max_spin.value()
        self.config.max_value = None if max_val == self.max_spin.maximum() else max_val
        
        alert_min = self.alert_min_spin.value()
        self.config.alert_min = None if alert_min == self.alert_min_spin.minimum() else alert_min
        
        alert_max = self.alert_max_spin.value()
        self.config.alert_max = None if alert_max == self.alert_max_spin.maximum() else alert_max
        
        self.config.smoothing = self.smoothing_spin.value()
    
    def get_config(self) -> SensorConfig:
        """Get the current configuration."""
        return self.config

