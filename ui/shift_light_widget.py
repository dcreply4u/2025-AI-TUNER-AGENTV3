"""
Shift Light Widget

Visual display and configuration UI for advanced shift lights.
"""

from __future__ import annotations

import logging
from typing import Optional

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QSpinBox, QDoubleSpinBox, QComboBox, QTableWidget, QTableWidgetItem,
        QGroupBox, QCheckBox, QColorDialog, QSlider, QProgressBar,
    )
    from PySide6.QtCore import Qt, Signal, QTimer
    from PySide6.QtGui import QColor, QPainter, QPen, QBrush
except ImportError:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QSpinBox, QDoubleSpinBox, QComboBox, QTableWidget, QTableWidgetItem,
        QGroupBox, QCheckBox, QColorDialog, QSlider, QProgressBar,
    )
    from PyQt5.QtCore import Qt, Signal as Signal, QTimer
    from PyQt5.QtGui import QColor, QPainter, QPen, QBrush

from services.shift_light_manager import (
    ShiftLightManager,
    ShiftLightConfig,
    LEDConfig,
    GearShiftPoint,
    ShiftLightColor,
    FlashMode,
)

LOGGER = logging.getLogger(__name__)


class ShiftLightDisplay(QWidget):
    """Visual shift light display widget."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.led_count = 5
        self.active_leds: list[int] = []
        self.led_colors: list[ShiftLightColor] = []
        self.setMinimumSize(400, 100)
        self.setMaximumHeight(150)
    
    def update_leds(self, active_leds: list[int], colors: list[ShiftLightColor]) -> None:
        """Update LED display."""
        self.active_leds = active_leds
        self.led_colors = colors
        self.update()
    
    def paintEvent(self, event) -> None:
        """Paint the shift light display."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        led_width = width / self.led_count
        led_height = height - 20
        
        for i in range(self.led_count):
            x = i * led_width
            y = 10
            
            # Determine color
            if i in self.active_leds:
                idx = self.active_leds.index(i)
                color_name = self.led_colors[idx] if idx < len(self.led_colors) else ShiftLightColor.RED
            else:
                color_name = ShiftLightColor.OFF
            
            # Map color
            color_map = {
                ShiftLightColor.OFF: QColor(30, 30, 30),
                ShiftLightColor.GREEN: QColor(0, 255, 0),
                ShiftLightColor.YELLOW: QColor(255, 255, 0),
                ShiftLightColor.ORANGE: QColor(255, 165, 0),
                ShiftLightColor.RED: QColor(255, 0, 0),
                ShiftLightColor.BLUE: QColor(0, 0, 255),
            }
            
            color = color_map.get(color_name, QColor(30, 30, 30))
            
            # Draw LED
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(100, 100, 100), 2))
            painter.drawRoundedRect(
                int(x + 5), int(y),
                int(led_width - 10), int(led_height),
                5, 5
            )


class ShiftLightConfigWidget(QWidget):
    """Configuration widget for shift lights."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.config: Optional[ShiftLightConfig] = None
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        # LED Configuration
        led_group = QGroupBox("LED Configuration")
        led_layout = QVBoxLayout()
        
        self.led_table = QTableWidget()
        self.led_table.setColumnCount(5)
        self.led_table.setHorizontalHeaderLabels([
            "LED", "RPM Threshold", "Color", "Flash Mode", "Enabled"
        ])
        led_layout.addWidget(self.led_table)
        
        # Add LED button
        add_led_btn = QPushButton("Add LED")
        add_led_btn.clicked.connect(self._add_led)
        led_layout.addWidget(add_led_btn)
        
        led_group.setLayout(led_layout)
        layout.addWidget(led_group)
        
        # Gear Shift Points
        gear_group = QGroupBox("Gear-Dependent Shift Points")
        gear_layout = QVBoxLayout()
        
        self.gear_table = QTableWidget()
        self.gear_table.setColumnCount(5)
        self.gear_table.setHorizontalHeaderLabels([
            "Gear", "Optimal RPM", "Max RPM", "Start RPM", "Peak RPM"
        ])
        gear_layout.addWidget(self.gear_table)
        
        # Add gear button
        add_gear_btn = QPushButton("Add Gear")
        add_gear_btn.clicked.connect(self._add_gear)
        gear_layout.addWidget(add_gear_btn)
        
        gear_group.setLayout(gear_layout)
        layout.addWidget(gear_group)
        
        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()
        
        self.gear_dependent_cb = QCheckBox("Enable Gear-Dependent Settings")
        self.gear_dependent_cb.setChecked(True)
        options_layout.addWidget(self.gear_dependent_cb)
        
        self.predictive_timing_cb = QCheckBox("Enable Predictive Lap Timing")
        options_layout.addWidget(self.predictive_timing_cb)
        
        self.external_hardware_cb = QCheckBox("Enable External Hardware")
        options_layout.addWidget(self.external_hardware_cb)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        layout.addStretch()
    
    def _add_led(self) -> None:
        """Add a new LED configuration."""
        row = self.led_table.rowCount()
        self.led_table.insertRow(row)
        
        # LED index
        self.led_table.setItem(row, 0, QTableWidgetItem(str(row)))
        
        # RPM threshold
        rpm_item = QTableWidgetItem("5000")
        self.led_table.setItem(row, 1, rpm_item)
        
        # Color
        color_combo = QComboBox()
        color_combo.addItems([c.value for c in ShiftLightColor])
        color_combo.setCurrentText(ShiftLightColor.RED.value)
        self.led_table.setCellWidget(row, 2, color_combo)
        
        # Flash mode
        flash_combo = QComboBox()
        flash_combo.addItems([f.value for f in FlashMode])
        flash_combo.setCurrentText(FlashMode.SOLID.value)
        self.led_table.setCellWidget(row, 3, flash_combo)
        
        # Enabled
        enabled_cb = QCheckBox()
        enabled_cb.setChecked(True)
        self.led_table.setCellWidget(row, 4, enabled_cb)
    
    def _add_gear(self) -> None:
        """Add a new gear shift point."""
        row = self.gear_table.rowCount()
        self.gear_table.insertRow(row)
        
        # Gear
        gear_item = QTableWidgetItem(str(row + 1))
        self.gear_table.setItem(row, 0, gear_item)
        
        # Optimal RPM
        self.gear_table.setItem(row, 1, QTableWidgetItem("6500"))
        
        # Max RPM
        self.gear_table.setItem(row, 2, QTableWidgetItem("7500"))
        
        # Start RPM
        self.gear_table.setItem(row, 3, QTableWidgetItem("6000"))
        
        # Peak RPM
        self.gear_table.setItem(row, 4, QTableWidgetItem("7000"))
    
    def load_config(self, config: ShiftLightConfig) -> None:
        """Load configuration into UI."""
        self.config = config
        
        # Load LEDs
        self.led_table.setRowCount(0)
        for led in config.led_configs:
            row = self.led_table.rowCount()
            self.led_table.insertRow(row)
            
            self.led_table.setItem(row, 0, QTableWidgetItem(str(led.led_index)))
            self.led_table.setItem(row, 1, QTableWidgetItem(str(led.rpm_threshold)))
            
            color_combo = QComboBox()
            color_combo.addItems([c.value for c in ShiftLightColor])
            color_combo.setCurrentText(led.color.value)
            self.led_table.setCellWidget(row, 2, color_combo)
            
            flash_combo = QComboBox()
            flash_combo.addItems([f.value for f in FlashMode])
            flash_combo.setCurrentText(led.flash_mode.value)
            self.led_table.setCellWidget(row, 3, flash_combo)
            
            enabled_cb = QCheckBox()
            enabled_cb.setChecked(led.enabled)
            self.led_table.setCellWidget(row, 4, enabled_cb)
        
        # Load gears
        self.gear_table.setRowCount(0)
        for gear, point in config.gear_shift_points.items():
            row = self.gear_table.rowCount()
            self.gear_table.insertRow(row)
            
            self.gear_table.setItem(row, 0, QTableWidgetItem(str(point.gear)))
            self.gear_table.setItem(row, 1, QTableWidgetItem(str(point.optimal_rpm)))
            self.gear_table.setItem(row, 2, QTableWidgetItem(str(point.max_rpm)))
            self.gear_table.setItem(row, 3, QTableWidgetItem(str(point.shift_light_start_rpm)))
            self.gear_table.setItem(row, 4, QTableWidgetItem(str(point.shift_light_peak_rpm)))
        
        # Load options
        self.gear_dependent_cb.setChecked(config.enable_gear_dependent)
        self.predictive_timing_cb.setChecked(config.enable_predictive_timing)
        self.external_hardware_cb.setChecked(config.external_hardware_enabled)
    
    def get_config(self) -> ShiftLightConfig:
        """Get configuration from UI."""
        # Build LED configs
        led_configs = []
        for row in range(self.led_table.rowCount()):
            led_index = int(self.led_table.item(row, 0).text())
            rpm_threshold = float(self.led_table.item(row, 1).text())
            
            color_combo = self.led_table.cellWidget(row, 2)
            color = ShiftLightColor(color_combo.currentText())
            
            flash_combo = self.led_table.cellWidget(row, 3)
            flash_mode = FlashMode(flash_combo.currentText())
            
            enabled_cb = self.led_table.cellWidget(row, 4)
            enabled = enabled_cb.isChecked()
            
            led_configs.append(LEDConfig(
                led_index=led_index,
                rpm_threshold=rpm_threshold,
                color=color,
                flash_mode=flash_mode,
                enabled=enabled,
            ))
        
        # Build gear shift points
        gear_points = {}
        for row in range(self.gear_table.rowCount()):
            gear = int(self.gear_table.item(row, 0).text())
            optimal_rpm = float(self.gear_table.item(row, 1).text())
            max_rpm = float(self.gear_table.item(row, 2).text())
            start_rpm = float(self.gear_table.item(row, 3).text())
            peak_rpm = float(self.gear_table.item(row, 4).text())
            
            gear_points[gear] = GearShiftPoint(
                gear=gear,
                optimal_rpm=optimal_rpm,
                max_rpm=max_rpm,
                shift_light_start_rpm=start_rpm,
                shift_light_peak_rpm=peak_rpm,
            )
        
        return ShiftLightConfig(
            name="Custom",
            led_configs=led_configs,
            gear_shift_points=gear_points,
            enable_gear_dependent=self.gear_dependent_cb.isChecked(),
            enable_predictive_timing=self.predictive_timing_cb.isChecked(),
            external_hardware_enabled=self.external_hardware_cb.isChecked(),
        )


class ShiftLightTab(QWidget):
    """Main shift light tab."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.shift_light_manager: Optional[ShiftLightManager] = None
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        # Display
        self.display = ShiftLightDisplay()
        layout.addWidget(self.display)
        
        # Current status
        status_layout = QHBoxLayout()
        self.rpm_label = QLabel("RPM: 0")
        self.gear_label = QLabel("Gear: 1")
        self.lap_delta_label = QLabel("Lap Δ: 0.000s")
        status_layout.addWidget(self.rpm_label)
        status_layout.addWidget(self.gear_label)
        status_layout.addWidget(self.lap_delta_label)
        layout.addLayout(status_layout)
        
        # Configuration
        self.config_widget = ShiftLightConfigWidget()
        layout.addWidget(self.config_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self._save_config)
        button_layout.addWidget(save_btn)
        
        load_btn = QPushButton("Load Configuration")
        load_btn.clicked.connect(self._load_config)
        button_layout.addWidget(load_btn)
        
        layout.addLayout(button_layout)
        
        # Analysis
        analysis_group = QGroupBox("Shift Analysis")
        analysis_layout = QVBoxLayout()
        
        self.analysis_table = QTableWidget()
        self.analysis_table.setColumnCount(5)
        self.analysis_table.setHorizontalHeaderLabels([
            "Gear", "RPM", "Reaction (ms)", "Optimal", "Lap Δ"
        ])
        analysis_layout.addWidget(self.analysis_table)
        
        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)
    
    def set_shift_light_manager(self, manager: ShiftLightManager) -> None:
        """Set shift light manager."""
        self.shift_light_manager = manager
        
        # Register callbacks
        manager.register_led_update_callback(self._on_led_update)
        manager.register_shift_event_callback(self._on_shift_event)
        
        # Load config
        self.config_widget.load_config(manager.config)
        
        # Start update timer
        self.update_timer.start(50)  # 20 Hz
    
    def _update_display(self) -> None:
        """Update display with current data."""
        if not self.shift_light_manager:
            return
        
        # Update labels
        self.rpm_label.setText(f"RPM: {self.shift_light_manager.current_rpm:.0f}")
        self.gear_label.setText(f"Gear: {self.shift_light_manager.current_gear}")
        
        if self.shift_light_manager.lap_time_delta != 0:
            delta_str = f"{self.shift_light_manager.lap_time_delta:+.3f}s"
            if self.shift_light_manager.lap_time_delta < 0:
                delta_str = f"<span style='color: green'>{delta_str}</span>"
            else:
                delta_str = f"<span style='color: red'>{delta_str}</span>"
            self.lap_delta_label.setText(f"Lap Δ: {delta_str}")
        else:
            self.lap_delta_label.setText("Lap Δ: --")
    
    def _on_led_update(self, active_leds: list[int], colors: list[ShiftLightColor]) -> None:
        """Handle LED update."""
        self.display.update_leds(active_leds, colors)
    
    def _on_shift_event(self, event) -> None:
        """Handle shift event."""
        # Update analysis table
        row = self.analysis_table.rowCount()
        self.analysis_table.insertRow(row)
        
        self.analysis_table.setItem(row, 0, QTableWidgetItem(f"{event.gear_before}→{event.gear_after}"))
        self.analysis_table.setItem(row, 1, QTableWidgetItem(f"{event.rpm_at_shift:.0f}"))
        self.analysis_table.setItem(row, 2, QTableWidgetItem(f"{event.reaction_time_ms:.1f}"))
        self.analysis_table.setItem(row, 3, QTableWidgetItem("✓" if event.optimal else "✗"))
        
        if event.lap_time_delta:
            delta_str = f"{event.lap_time_delta:+.3f}s"
            self.analysis_table.setItem(row, 4, QTableWidgetItem(delta_str))
        else:
            self.analysis_table.setItem(row, 4, QTableWidgetItem("--"))
    
    def _save_config(self) -> None:
        """Save configuration."""
        if not self.shift_light_manager:
            return
        
        config = self.config_widget.get_config()
        self.shift_light_manager.update_config(config)
        LOGGER.info("Shift light configuration saved")
    
    def _load_config(self) -> None:
        """Load configuration."""
        if not self.shift_light_manager:
            return
        
        self.config_widget.load_config(self.shift_light_manager.config)


__all__ = ["ShiftLightTab", "ShiftLightDisplay", "ShiftLightConfigWidget"]

