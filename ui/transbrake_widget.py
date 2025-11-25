"""
Transbrake Widget

Visual display and configuration UI for advanced transbrake control.
"""

from __future__ import annotations

import logging
from typing import Optional

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QSpinBox, QDoubleSpinBox, QComboBox, QTableWidget, QTableWidgetItem,
        QGroupBox, QCheckBox, QSlider, QProgressBar, QLineEdit,
    )
    from PySide6.QtCore import Qt, Signal, QTimer
    from PySide6.QtGui import QColor, QPainter, QPen, QBrush
except ImportError:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QSpinBox, QDoubleSpinBox, QComboBox, QTableWidget, QTableWidgetItem,
        QGroupBox, QCheckBox, QSlider, QProgressBar, QLineEdit,
    )
    from PyQt5.QtCore import Qt, Signal as Signal, QTimer
    from PyQt5.QtGui import QColor, QPainter, QPen, QBrush

from services.transbrake_manager import (
    TransbrakeManager,
    TransbrakeConfig,
    LaunchParameters,
    StagingConfig,
    ClutchSlipConfig,
    SafetyLimits,
    TransbrakeState,
    StagingMode,
)

LOGGER = logging.getLogger(__name__)


class TransbrakeStatusWidget(QWidget):
    """Status display widget for transbrake."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.state = TransbrakeState.DISABLED
        self.setMinimumSize(300, 100)
        self.setMaximumHeight(120)
    
    def set_state(self, state: TransbrakeState) -> None:
        """Set transbrake state."""
        self.state = state
        self.update()
    
    def paintEvent(self, event) -> None:
        """Paint the status display."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # State color mapping
        color_map = {
            TransbrakeState.DISABLED: QColor(100, 100, 100),
            TransbrakeState.ARMED: QColor(255, 255, 0),
            TransbrakeState.ENGAGED: QColor(255, 165, 0),
            TransbrakeState.LAUNCHING: QColor(0, 255, 0),
            TransbrakeState.RELEASED: QColor(0, 255, 255),
            TransbrakeState.ERROR: QColor(255, 0, 0),
        }
        
        color = color_map.get(self.state, QColor(100, 100, 100))
        
        # Draw status circle
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(QColor(200, 200, 200), 3))
        painter.drawEllipse(10, 10, width - 20, height - 20)
        
        # Draw state text
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.drawText(
            0, 0, width, height,
            Qt.AlignCenter,
            self.state.value.upper()
        )


class TransbrakeConfigWidget(QWidget):
    """Configuration widget for transbrake."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.config: Optional[TransbrakeConfig] = None
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        # Launch Parameters
        launch_group = QGroupBox("Launch Parameters")
        launch_layout = QVBoxLayout()
        
        # Target RPM
        rpm_layout = QHBoxLayout()
        rpm_layout.addWidget(QLabel("Target RPM:"))
        self.target_rpm_spin = QDoubleSpinBox()
        self.target_rpm_spin.setRange(0, 10000)
        self.target_rpm_spin.setValue(4000)
        self.target_rpm_spin.setSingleStep(100)
        rpm_layout.addWidget(self.target_rpm_spin)
        launch_layout.addLayout(rpm_layout)
        
        # Target Boost
        boost_layout = QHBoxLayout()
        boost_layout.addWidget(QLabel("Target Boost (PSI):"))
        self.target_boost_spin = QDoubleSpinBox()
        self.target_boost_spin.setRange(0, 50)
        self.target_boost_spin.setValue(0)
        self.target_boost_spin.setSingleStep(1)
        boost_layout.addWidget(self.target_boost_spin)
        launch_layout.addLayout(boost_layout)
        
        # Timing Advance
        timing_layout = QHBoxLayout()
        timing_layout.addWidget(QLabel("Timing Advance:"))
        self.timing_spin = QDoubleSpinBox()
        self.timing_spin.setRange(-20, 20)
        self.timing_spin.setValue(0)
        self.timing_spin.setSingleStep(1)
        timing_layout.addWidget(self.timing_spin)
        launch_layout.addLayout(timing_layout)
        
        # Enable checkboxes
        self.boost_control_cb = QCheckBox("Enable Boost Control")
        launch_layout.addWidget(self.boost_control_cb)
        
        self.timing_control_cb = QCheckBox("Enable Timing Control")
        launch_layout.addWidget(self.timing_control_cb)
        
        launch_group.setLayout(launch_layout)
        layout.addWidget(launch_group)
        
        # Staging Control
        staging_group = QGroupBox("Staging Control")
        staging_layout = QVBoxLayout()
        
        # Mode
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.staging_mode_combo = QComboBox()
        self.staging_mode_combo.addItems([m.value for m in StagingMode])
        mode_layout.addWidget(self.staging_mode_combo)
        staging_layout.addLayout(mode_layout)
        
        # Bump settings
        bump_layout = QHBoxLayout()
        bump_layout.addWidget(QLabel("Bump Duty Cycle:"))
        self.bump_duty_spin = QDoubleSpinBox()
        self.bump_duty_spin.setRange(0, 1)
        self.bump_duty_spin.setValue(0.5)
        self.bump_duty_spin.setSingleStep(0.1)
        self.bump_duty_spin.setDecimals(2)
        bump_layout.addWidget(self.bump_duty_spin)
        
        bump_layout.addWidget(QLabel("Frequency (Hz):"))
        self.bump_freq_spin = QDoubleSpinBox()
        self.bump_freq_spin.setRange(0.1, 10)
        self.bump_freq_spin.setValue(2.0)
        self.bump_freq_spin.setSingleStep(0.1)
        bump_layout.addWidget(self.bump_freq_spin)
        staging_layout.addLayout(bump_layout)
        
        # Creep settings
        creep_layout = QHBoxLayout()
        creep_layout.addWidget(QLabel("Creep Duty Cycle:"))
        self.creep_duty_spin = QDoubleSpinBox()
        self.creep_duty_spin.setRange(0, 1)
        self.creep_duty_spin.setValue(0.3)
        self.creep_duty_spin.setSingleStep(0.1)
        self.creep_duty_spin.setDecimals(2)
        creep_layout.addWidget(self.creep_duty_spin)
        
        creep_layout.addWidget(QLabel("Frequency (Hz):"))
        self.creep_freq_spin = QDoubleSpinBox()
        self.creep_freq_spin.setRange(0.1, 10)
        self.creep_freq_spin.setValue(1.0)
        self.creep_freq_spin.setSingleStep(0.1)
        creep_layout.addWidget(self.creep_freq_spin)
        staging_layout.addLayout(creep_layout)
        
        staging_group.setLayout(staging_layout)
        layout.addWidget(staging_group)
        
        # Safety Limits
        safety_group = QGroupBox("Safety Limits")
        safety_layout = QVBoxLayout()
        
        # Coolant temp
        coolant_layout = QHBoxLayout()
        coolant_layout.addWidget(QLabel("Max Coolant Temp (F):"))
        self.max_coolant_spin = QDoubleSpinBox()
        self.max_coolant_spin.setRange(150, 300)
        self.max_coolant_spin.setValue(220)
        self.max_coolant_spin.setSingleStep(5)
        coolant_layout.addWidget(self.max_coolant_spin)
        safety_layout.addLayout(coolant_layout)
        
        # Trans temp
        trans_layout = QHBoxLayout()
        trans_layout.addWidget(QLabel("Max Trans Temp (F):"))
        self.max_trans_spin = QDoubleSpinBox()
        self.max_trans_spin.setRange(150, 300)
        self.max_trans_spin.setValue(250)
        self.max_trans_spin.setSingleStep(5)
        trans_layout.addWidget(self.max_trans_spin)
        safety_layout.addLayout(trans_layout)
        
        # Max launch time
        launch_time_layout = QHBoxLayout()
        launch_time_layout.addWidget(QLabel("Max Launch Time (s):"))
        self.max_launch_time_spin = QDoubleSpinBox()
        self.max_launch_time_spin.setRange(1, 30)
        self.max_launch_time_spin.setValue(5)
        self.max_launch_time_spin.setSingleStep(0.5)
        launch_time_layout.addWidget(self.max_launch_time_spin)
        safety_layout.addLayout(launch_time_layout)
        
        # Min battery voltage
        battery_layout = QHBoxLayout()
        battery_layout.addWidget(QLabel("Min Battery Voltage:"))
        self.min_battery_spin = QDoubleSpinBox()
        self.min_battery_spin.setRange(10, 15)
        self.min_battery_spin.setValue(12.0)
        self.min_battery_spin.setSingleStep(0.1)
        self.min_battery_spin.setDecimals(1)
        battery_layout.addWidget(self.min_battery_spin)
        safety_layout.addLayout(battery_layout)
        
        self.safety_checks_cb = QCheckBox("Enable Safety Checks")
        self.safety_checks_cb.setChecked(True)
        safety_layout.addWidget(self.safety_checks_cb)
        
        safety_group.setLayout(safety_layout)
        layout.addWidget(safety_group)
        
        layout.addStretch()
    
    def load_config(self, config: TransbrakeConfig) -> None:
        """Load configuration into UI."""
        self.config = config
        
        # Launch parameters
        self.target_rpm_spin.setValue(config.launch_params.target_rpm)
        self.target_boost_spin.setValue(config.launch_params.target_boost_psi)
        self.timing_spin.setValue(config.launch_params.timing_advance)
        self.boost_control_cb.setChecked(config.launch_params.enable_boost_control)
        self.timing_control_cb.setChecked(config.launch_params.enable_timing_control)
        
        # Staging config
        self.staging_mode_combo.setCurrentText(config.staging_config.mode.value)
        self.bump_duty_spin.setValue(config.staging_config.bump_duty_cycle)
        self.bump_freq_spin.setValue(config.staging_config.bump_frequency_hz)
        self.creep_duty_spin.setValue(config.staging_config.creep_duty_cycle)
        self.creep_freq_spin.setValue(config.staging_config.creep_frequency_hz)
        
        # Safety limits
        self.max_coolant_spin.setValue(config.safety_limits.max_coolant_temp_f)
        self.max_trans_spin.setValue(config.safety_limits.max_trans_temp_f)
        self.max_launch_time_spin.setValue(config.safety_limits.max_launch_time_seconds)
        self.min_battery_spin.setValue(config.safety_limits.min_battery_voltage)
        self.safety_checks_cb.setChecked(config.safety_limits.enable_safety_checks)
    
    def get_config(self) -> TransbrakeConfig:
        """Get configuration from UI."""
        return TransbrakeConfig(
            name="Custom",
            launch_params=LaunchParameters(
                target_rpm=self.target_rpm_spin.value(),
                target_boost_psi=self.target_boost_spin.value(),
                timing_advance=self.timing_spin.value(),
                enable_boost_control=self.boost_control_cb.isChecked(),
                enable_timing_control=self.timing_control_cb.isChecked(),
            ),
            staging_config=StagingConfig(
                mode=StagingMode(self.staging_mode_combo.currentText()),
                bump_duty_cycle=self.bump_duty_spin.value(),
                bump_frequency_hz=self.bump_freq_spin.value(),
                creep_duty_cycle=self.creep_duty_spin.value(),
                creep_frequency_hz=self.creep_freq_spin.value(),
            ),
            safety_limits=SafetyLimits(
                max_coolant_temp_f=self.max_coolant_spin.value(),
                max_trans_temp_f=self.max_trans_spin.value(),
                max_launch_time_seconds=self.max_launch_time_spin.value(),
                min_battery_voltage=self.min_battery_spin.value(),
                enable_safety_checks=self.safety_checks_cb.isChecked(),
            ),
        )


class TransbrakeTab(QWidget):
    """Main transbrake tab."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.transbrake_manager: Optional[TransbrakeManager] = None
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        # Status display
        self.status_widget = TransbrakeStatusWidget()
        layout.addWidget(self.status_widget)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.arm_btn = QPushButton("ARM")
        self.arm_btn.setStyleSheet("background-color: yellow; font-weight: bold;")
        self.arm_btn.clicked.connect(self._arm)
        button_layout.addWidget(self.arm_btn)
        
        self.disarm_btn = QPushButton("DISARM")
        self.disarm_btn.setStyleSheet("background-color: gray;")
        self.disarm_btn.clicked.connect(self._disarm)
        button_layout.addWidget(self.disarm_btn)
        
        self.engage_btn = QPushButton("ENGAGE")
        self.engage_btn.setStyleSheet("background-color: orange; font-weight: bold;")
        self.engage_btn.clicked.connect(self._engage)
        self.engage_btn.setEnabled(False)
        button_layout.addWidget(self.engage_btn)
        
        self.release_btn = QPushButton("RELEASE")
        self.release_btn.setStyleSheet("background-color: green; font-weight: bold;")
        self.release_btn.clicked.connect(self._release)
        self.release_btn.setEnabled(False)
        button_layout.addWidget(self.release_btn)
        
        layout.addLayout(button_layout)
        
        # Current readings
        readings_group = QGroupBox("Current Readings")
        readings_layout = QVBoxLayout()
        
        readings_grid = QHBoxLayout()
        self.rpm_label = QLabel("RPM: 0")
        self.boost_label = QLabel("Boost: 0.0 PSI")
        self.coolant_label = QLabel("Coolant: 0°F")
        self.trans_label = QLabel("Trans: 0°F")
        self.battery_label = QLabel("Battery: 12.6V")
        self.g_force_label = QLabel("G-Force: 0.0")
        
        readings_grid.addWidget(self.rpm_label)
        readings_grid.addWidget(self.boost_label)
        readings_grid.addWidget(self.coolant_label)
        readings_grid.addWidget(self.trans_label)
        readings_grid.addWidget(self.battery_label)
        readings_grid.addWidget(self.g_force_label)
        
        readings_layout.addLayout(readings_grid)
        readings_group.setLayout(readings_layout)
        layout.addWidget(readings_group)
        
        # Configuration
        self.config_widget = TransbrakeConfigWidget()
        layout.addWidget(self.config_widget)
        
        # Buttons
        config_button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self._save_config)
        config_button_layout.addWidget(save_btn)
        
        load_btn = QPushButton("Load Configuration")
        load_btn.clicked.connect(self._load_config)
        config_button_layout.addWidget(load_btn)
        
        layout.addLayout(config_button_layout)
        
        # Launch Analysis
        analysis_group = QGroupBox("Launch Analysis")
        analysis_layout = QVBoxLayout()
        
        self.analysis_table = QTableWidget()
        self.analysis_table.setColumnCount(5)
        self.analysis_table.setHorizontalHeaderLabels([
            "RPM", "Boost", "60ft Time", "Peak G", "Wheel Speed"
        ])
        analysis_layout.addWidget(self.analysis_table)
        
        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)
        
        # Start update timer
        self.update_timer.start(100)  # 10 Hz
    
    def set_transbrake_manager(self, manager: TransbrakeManager) -> None:
        """Set transbrake manager."""
        self.transbrake_manager = manager
        
        # Register callbacks
        manager.register_state_change_callback(self._on_state_change)
        manager.register_launch_event_callback(self._on_launch_event)
        
        # Load config
        self.config_widget.load_config(manager.config)
    
    def _update_display(self) -> None:
        """Update display with current data."""
        if not self.transbrake_manager:
            return
        
        # Update labels
        self.rpm_label.setText(f"RPM: {self.transbrake_manager.current_rpm:.0f}")
        self.boost_label.setText(f"Boost: {self.transbrake_manager.current_boost:.1f} PSI")
        self.coolant_label.setText(f"Coolant: {self.transbrake_manager.coolant_temp_f:.0f}°F")
        self.trans_label.setText(f"Trans: {self.transbrake_manager.trans_temp_f:.0f}°F")
        self.battery_label.setText(f"Battery: {self.transbrake_manager.battery_voltage:.1f}V")
        self.g_force_label.setText(f"G-Force: {self.transbrake_manager.g_force:.2f}")
        
        # Update button states
        self.engage_btn.setEnabled(self.transbrake_manager.armed)
        self.release_btn.setEnabled(self.transbrake_manager.engaged)
    
    def _on_state_change(self, state: TransbrakeState) -> None:
        """Handle state change."""
        self.status_widget.set_state(state)
    
    def _on_launch_event(self, event) -> None:
        """Handle launch event."""
        # Update analysis table
        row = self.analysis_table.rowCount()
        self.analysis_table.insertRow(row)
        
        self.analysis_table.setItem(row, 0, QTableWidgetItem(f"{event.launch_rpm:.0f}"))
        self.analysis_table.setItem(row, 1, QTableWidgetItem(f"{event.launch_boost:.1f}"))
        self.analysis_table.setItem(row, 2, QTableWidgetItem(f"{event.time_60ft:.3f}"))
        self.analysis_table.setItem(row, 3, QTableWidgetItem(f"{event.g_force_peak:.2f}"))
        self.analysis_table.setItem(row, 4, QTableWidgetItem(f"{event.wheel_speed_60ft:.1f}"))
    
    def _arm(self) -> None:
        """Arm transbrake."""
        if self.transbrake_manager:
            self.transbrake_manager.arm()
    
    def _disarm(self) -> None:
        """Disarm transbrake."""
        if self.transbrake_manager:
            self.transbrake_manager.disarm()
    
    def _engage(self) -> None:
        """Engage transbrake."""
        if self.transbrake_manager:
            self.transbrake_manager.engage()
    
    def _release(self) -> None:
        """Release transbrake."""
        if self.transbrake_manager:
            self.transbrake_manager.release()
    
    def _save_config(self) -> None:
        """Save configuration."""
        if not self.transbrake_manager:
            return
        
        config = self.config_widget.get_config()
        self.transbrake_manager.update_config(config)
        LOGGER.info("Transbrake configuration saved")
    
    def _load_config(self) -> None:
        """Load configuration."""
        if not self.transbrake_manager:
            return
        
        self.config_widget.load_config(self.transbrake_manager.config)


__all__ = ["TransbrakeTab", "TransbrakeStatusWidget", "TransbrakeConfigWidget"]

