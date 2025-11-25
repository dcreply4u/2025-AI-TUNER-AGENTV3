"""
Racing Controls Tab

UI for Anti-Lag and Launch Control systems.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
    QComboBox,
    QProgressBar,
    QTextEdit,
)

from ui.ui_scaling import get_scaled_size, get_scaled_font_size

try:
    from controllers.racing_controls import (
        RacingControls,
        AntiLagMode,
        LaunchControlMode,
        AntiLagConfig,
        LaunchControlConfig,
    )
    RACING_CONTROLS_AVAILABLE = True
except ImportError:
    RACING_CONTROLS_AVAILABLE = False
    RacingControls = None  # type: ignore
    AntiLagMode = None  # type: ignore
    LaunchControlMode = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class RacingControlsTab(QWidget):
    """Racing Controls tab for Anti-Lag and Launch Control."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.racing_controls: Optional[RacingControls] = None
        self.telemetry_callback: Optional[callable] = None
        self.can_sender: Optional[callable] = None
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(100)  # 10 Hz update
        
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Setup the racing controls UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Title
        title = QLabel("Racing Controls - Anti-Lag & Launch Control")
        title.setStyleSheet(f"font-size: {get_scaled_font_size(16)}px; font-weight: bold; color: #ffffff;")
        main_layout.addWidget(title)
        
        # Main content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        
        # Left: Anti-Lag Controls
        anti_lag_panel = self._create_anti_lag_panel()
        content_layout.addWidget(anti_lag_panel, stretch=1)
        
        # Center: Launch Control
        launch_panel = self._create_launch_control_panel()
        content_layout.addWidget(launch_panel, stretch=1)
        
        # Right: Status & Warnings
        status_panel = self._create_status_panel()
        content_layout.addWidget(status_panel, stretch=1)
        
        main_layout.addLayout(content_layout, stretch=1)
        
        # Bottom: Log/History
        log_panel = self._create_log_panel()
        main_layout.addWidget(log_panel, stretch=0)
    
    def _create_anti_lag_panel(self) -> QWidget:
        """Create anti-lag control panel."""
        panel = QGroupBox("Anti-Lag Control")
        panel.setStyleSheet(f"""
            QGroupBox {{
                font-size: {get_scaled_font_size(12)}px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 15, 10, 10)
        
        # Enable checkbox
        self.anti_lag_enabled = QCheckBox("Enable Anti-Lag")
        self.anti_lag_enabled.setStyleSheet("color: #ffffff; font-size: 11px;")
        self.anti_lag_enabled.toggled.connect(self._on_anti_lag_enabled_changed)
        layout.addWidget(self.anti_lag_enabled)
        
        # Mode selection
        layout.addWidget(QLabel("Mode:"))
        self.anti_lag_mode = QComboBox()
        if RACING_CONTROLS_AVAILABLE and AntiLagMode:
            self.anti_lag_mode.addItems([mode.value.upper() for mode in AntiLagMode])
        else:
            self.anti_lag_mode.addItems(["OFF", "SOFT", "AGGRESSIVE", "AUTO"])
        self.anti_lag_mode.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        self.anti_lag_mode.currentTextChanged.connect(self._on_anti_lag_mode_changed)
        layout.addWidget(self.anti_lag_mode)
        
        # RPM settings
        layout.addWidget(QLabel("Min RPM:"))
        self.anti_lag_min_rpm = QSpinBox()
        self.anti_lag_min_rpm.setRange(1000, 6000)
        self.anti_lag_min_rpm.setValue(2000)
        self.anti_lag_min_rpm.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        self.anti_lag_min_rpm.valueChanged.connect(self._on_anti_lag_config_changed)
        layout.addWidget(self.anti_lag_min_rpm)
        
        layout.addWidget(QLabel("Max RPM:"))
        self.anti_lag_max_rpm = QSpinBox()
        self.anti_lag_max_rpm.setRange(2000, 8000)
        self.anti_lag_max_rpm.setValue(4000)
        self.anti_lag_max_rpm.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        self.anti_lag_max_rpm.valueChanged.connect(self._on_anti_lag_config_changed)
        layout.addWidget(self.anti_lag_max_rpm)
        
        # Boost target
        layout.addWidget(QLabel("Boost Target (PSI):"))
        self.anti_lag_boost_target = QDoubleSpinBox()
        self.anti_lag_boost_target.setRange(0, 50)
        self.anti_lag_boost_target.setValue(10.0)
        self.anti_lag_boost_target.setSingleStep(0.5)
        self.anti_lag_boost_target.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        self.anti_lag_boost_target.valueChanged.connect(self._on_anti_lag_config_changed)
        layout.addWidget(self.anti_lag_boost_target)
        
        # Safety limits
        safety_group = QGroupBox("Safety Limits")
        safety_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {get_scaled_font_size(10)}px; font-weight: bold; color: #ff8000;
                border: 1px solid #ff8000; border-radius: 3px;
                margin-top: 5px; padding-top: 5px;
            }}
        """)
        safety_layout = QVBoxLayout()
        
        safety_layout.addWidget(QLabel("Max RPM:"))
        self.anti_lag_safety_max_rpm = QSpinBox()
        self.anti_lag_safety_max_rpm.setRange(3000, 10000)
        self.anti_lag_safety_max_rpm.setValue(5000)
        self.anti_lag_safety_max_rpm.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        self.anti_lag_safety_max_rpm.valueChanged.connect(self._on_anti_lag_config_changed)
        safety_layout.addWidget(self.anti_lag_safety_max_rpm)
        
        safety_layout.addWidget(QLabel("Max EGT (°F):"))
        self.anti_lag_safety_max_egt = QDoubleSpinBox()
        self.anti_lag_safety_max_egt.setRange(1000, 2000)
        self.anti_lag_safety_max_egt.setValue(1650.0)
        self.anti_lag_safety_max_egt.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        self.anti_lag_safety_max_egt.valueChanged.connect(self._on_anti_lag_config_changed)
        safety_layout.addWidget(self.anti_lag_safety_max_egt)
        
        safety_group.setLayout(safety_layout)
        layout.addWidget(safety_group)
        
        # Status indicator
        self.anti_lag_status = QLabel("Status: INACTIVE")
        self.anti_lag_status.setStyleSheet("color: #808080; font-weight: bold; font-size: 11px;")
        layout.addWidget(self.anti_lag_status)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    def _create_launch_control_panel(self) -> QWidget:
        """Create launch control panel."""
        panel = QGroupBox("Launch Control")
        panel.setStyleSheet(f"""
            QGroupBox {{
                font-size: {get_scaled_font_size(12)}px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 15, 10, 10)
        
        # Enable checkbox
        self.launch_enabled = QCheckBox("Enable Launch Control")
        self.launch_enabled.setStyleSheet("color: #ffffff; font-size: 11px;")
        self.launch_enabled.toggled.connect(self._on_launch_enabled_changed)
        layout.addWidget(self.launch_enabled)
        
        # Mode selection
        layout.addWidget(QLabel("Mode:"))
        self.launch_mode = QComboBox()
        if RACING_CONTROLS_AVAILABLE and LaunchControlMode:
            self.launch_mode.addItems([mode.value.upper().replace("_", " ") for mode in LaunchControlMode])
        else:
            self.launch_mode.addItems(["OFF", "RPM LIMIT", "TRACTION", "AUTO"])
        self.launch_mode.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        self.launch_mode.currentTextChanged.connect(self._on_launch_mode_changed)
        layout.addWidget(self.launch_mode)
        
        # Launch RPM
        layout.addWidget(QLabel("Launch RPM:"))
        self.launch_rpm = QSpinBox()
        self.launch_rpm.setRange(2000, 8000)
        self.launch_rpm.setValue(3500)
        self.launch_rpm.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        self.launch_rpm.valueChanged.connect(self._on_launch_config_changed)
        layout.addWidget(self.launch_rpm)
        
        # RPM tolerance
        layout.addWidget(QLabel("RPM Tolerance:"))
        self.launch_rpm_tolerance = QSpinBox()
        self.launch_rpm_tolerance.setRange(50, 500)
        self.launch_rpm_tolerance.setValue(200)
        self.launch_rpm_tolerance.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        self.launch_rpm_tolerance.valueChanged.connect(self._on_launch_config_changed)
        layout.addWidget(self.launch_rpm_tolerance)
        
        # Max launch time
        layout.addWidget(QLabel("Max Launch Time (s):"))
        self.launch_max_time = QDoubleSpinBox()
        self.launch_max_time.setRange(1.0, 30.0)
        self.launch_max_time.setValue(5.0)
        self.launch_max_time.setSingleStep(0.5)
        self.launch_max_time.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        self.launch_max_time.valueChanged.connect(self._on_launch_config_changed)
        layout.addWidget(self.launch_max_time)
        
        # Min speed to disable
        layout.addWidget(QLabel("Min Speed to Disable (mph):"))
        self.launch_min_speed = QDoubleSpinBox()
        self.launch_min_speed.setRange(0, 20)
        self.launch_min_speed.setValue(5.0)
        self.launch_min_speed.setSingleStep(0.5)
        self.launch_min_speed.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        self.launch_min_speed.valueChanged.connect(self._on_launch_config_changed)
        layout.addWidget(self.launch_min_speed)
        
        # Transbrake required
        self.launch_transbrake_required = QCheckBox("Require Transbrake")
        self.launch_transbrake_required.setChecked(True)
        self.launch_transbrake_required.setStyleSheet("color: #ffffff; font-size: 11px;")
        self.launch_transbrake_required.toggled.connect(self._on_launch_config_changed)
        layout.addWidget(self.launch_transbrake_required)
        
        # Status indicator
        self.launch_status = QLabel("Status: INACTIVE")
        self.launch_status.setStyleSheet("color: #808080; font-weight: bold; font-size: 11px;")
        layout.addWidget(self.launch_status)
        
        # Launch timer
        self.launch_timer_label = QLabel("Timer: 0.0s")
        self.launch_timer_label.setStyleSheet("color: #ff8000; font-weight: bold; font-size: 11px;")
        layout.addWidget(self.launch_timer_label)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    def _create_status_panel(self) -> QWidget:
        """Create status and warnings panel."""
        panel = QGroupBox("Status & Warnings")
        panel.setStyleSheet(f"""
            QGroupBox {{
                font-size: {get_scaled_font_size(12)}px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 15, 10, 10)
        
        # System status
        self.system_status = QLabel("System: STOPPED")
        self.system_status.setStyleSheet("color: #ff0000; font-weight: bold; font-size: 12px;")
        layout.addWidget(self.system_status)
        
        # Warnings display
        layout.addWidget(QLabel("Warnings:"))
        self.warnings_display = QTextEdit()
        self.warnings_display.setReadOnly(True)
        self.warnings_display.setMaximumHeight(150)
        self.warnings_display.setStyleSheet("background-color: #0a0a0a; color: #ff8000; border: 1px solid #404040;")
        layout.addWidget(self.warnings_display)
        
        # Start/Stop button
        self.start_stop_btn = QPushButton("Start System")
        self.start_stop_btn.setStyleSheet("background-color: #0080ff; color: #ffffff; padding: 8px; font-weight: bold;")
        self.start_stop_btn.clicked.connect(self._toggle_system)
        layout.addWidget(self.start_stop_btn)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    def _create_log_panel(self) -> QWidget:
        """Create log/history panel."""
        panel = QGroupBox("Event Log")
        panel.setStyleSheet(f"""
            QGroupBox {{
                font-size: {get_scaled_font_size(11)}px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 5px; padding-top: 5px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 15, 10, 10)
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(150)
        self.log_display.setStyleSheet("background-color: #0a0a0a; color: #00ff00; border: 1px solid #404040; font-family: monospace; font-size: 10px;")
        layout.addWidget(self.log_display)
        
        panel.setLayout(layout)
        return panel
    
    def _on_anti_lag_enabled_changed(self, enabled: bool) -> None:
        """Handle anti-lag enable/disable."""
        if self.racing_controls:
            mode_str = self.anti_lag_mode.currentText().lower()
            if RACING_CONTROLS_AVAILABLE and AntiLagMode:
                mode = AntiLagMode(mode_str)
            else:
                mode = None
            self.racing_controls.set_anti_lag(enabled, mode or AntiLagMode.AUTO if AntiLagMode else None)
            self._log(f"Anti-lag {'enabled' if enabled else 'disabled'}")
    
    def _on_anti_lag_mode_changed(self, mode_str: str) -> None:
        """Handle anti-lag mode change."""
        if self.racing_controls and self.anti_lag_enabled.isChecked():
            mode = AntiLagMode(mode_str.lower()) if RACING_CONTROLS_AVAILABLE and AntiLagMode else None
            self.racing_controls.set_anti_lag(True, mode or AntiLagMode.AUTO if AntiLagMode else None)
            self._log(f"Anti-lag mode: {mode_str}")
    
    def _on_anti_lag_config_changed(self) -> None:
        """Update anti-lag configuration."""
        if self.racing_controls:
            config = self.racing_controls.anti_lag_config
            config.min_rpm = self.anti_lag_min_rpm.value()
            config.max_rpm = self.anti_lag_max_rpm.value()
            config.boost_target = self.anti_lag_boost_target.value()
            config.safety_max_rpm = self.anti_lag_safety_max_rpm.value()
            config.safety_max_egt = self.anti_lag_safety_max_egt.value()
    
    def _on_launch_enabled_changed(self, enabled: bool) -> None:
        """Handle launch control enable/disable."""
        if self.racing_controls:
            mode_str = self.launch_mode.currentText().lower().replace(" ", "_")
            if RACING_CONTROLS_AVAILABLE and LaunchControlMode:
                mode = LaunchControlMode(mode_str)
            else:
                mode = None
            self.racing_controls.set_launch_control(
                enabled,
                self.launch_rpm.value(),
                mode or LaunchControlMode.RPM_LIMIT if LaunchControlMode else None
            )
            self._log(f"Launch control {'enabled' if enabled else 'disabled'}")
    
    def _on_launch_mode_changed(self, mode_str: str) -> None:
        """Handle launch control mode change."""
        if self.racing_controls and self.launch_enabled.isChecked():
            mode = LaunchControlMode(mode_str.lower().replace(" ", "_")) if RACING_CONTROLS_AVAILABLE and LaunchControlMode else None
            self.racing_controls.set_launch_control(
                True,
                self.launch_rpm.value(),
                mode or LaunchControlMode.RPM_LIMIT if LaunchControlMode else None
            )
            self._log(f"Launch control mode: {mode_str}")
    
    def _on_launch_config_changed(self) -> None:
        """Update launch control configuration."""
        if self.racing_controls:
            config = self.racing_controls.launch_config
            config.launch_rpm = self.launch_rpm.value()
            config.rpm_tolerance = self.launch_rpm_tolerance.value()
            config.max_launch_time = self.launch_max_time.value()
            config.min_speed = self.launch_min_speed.value()
            config.transbrake_required = self.launch_transbrake_required.isChecked()
    
    def _toggle_system(self) -> None:
        """Start/stop the racing controls system."""
        if not self.racing_controls:
            self._initialize_racing_controls()
        
        if self.racing_controls:
            if self.start_stop_btn.text() == "Start System":
                self.racing_controls.start()
                self.start_stop_btn.setText("Stop System")
                self.start_stop_btn.setStyleSheet("background-color: #ff0000; color: #ffffff; padding: 8px; font-weight: bold;")
                self.system_status.setText("System: RUNNING")
                self.system_status.setStyleSheet("color: #00ff00; font-weight: bold; font-size: 12px;")
                self._log("Racing controls system started")
            else:
                self.racing_controls.stop()
                self.start_stop_btn.setText("Start System")
                self.start_stop_btn.setStyleSheet("background-color: #0080ff; color: #ffffff; padding: 8px; font-weight: bold;")
                self.system_status.setText("System: STOPPED")
                self.system_status.setStyleSheet("color: #ff0000; font-weight: bold; font-size: 12px;")
                self._log("Racing controls system stopped")
    
    def _initialize_racing_controls(self) -> None:
        """Initialize racing controls system."""
        if not RACING_CONTROLS_AVAILABLE:
            self._log("ERROR: Racing controls module not available")
            return
        
        try:
            self.racing_controls = RacingControls(
                can_sender=self.can_sender,
                telemetry_callback=self.telemetry_callback,
            )
            self._log("Racing controls initialized")
        except Exception as e:
            LOGGER.error(f"Failed to initialize racing controls: {e}")
            self._log(f"ERROR: Failed to initialize: {e}")
    
    def _update_display(self) -> None:
        """Update display with current state."""
        if not self.racing_controls:
            return
        
        try:
            state = self.racing_controls.get_state()
            
            # Update anti-lag status
            if state.anti_lag_active:
                self.anti_lag_status.setText("Status: ACTIVE")
                self.anti_lag_status.setStyleSheet("color: #00ff00; font-weight: bold; font-size: 11px;")
            else:
                self.anti_lag_status.setText("Status: INACTIVE")
                self.anti_lag_status.setStyleSheet("color: #808080; font-weight: bold; font-size: 11px;")
            
            # Update launch control status
            if state.launch_control_active:
                self.launch_status.setText("Status: ACTIVE")
                self.launch_status.setStyleSheet("color: #00ff00; font-weight: bold; font-size: 11px;")
                elapsed = time.time() - state.launch_timer if state.launch_timer > 0 else 0.0
                self.launch_timer_label.setText(f"Timer: {elapsed:.1f}s")
            else:
                self.launch_status.setText("Status: INACTIVE")
                self.launch_status.setStyleSheet("color: #808080; font-weight: bold; font-size: 11px;")
                self.launch_timer_label.setText("Timer: 0.0s")
            
            # Update warnings
            if state.warnings:
                warnings_text = "\n".join(state.warnings)
                self.warnings_display.setPlainText(warnings_text)
                self.warnings_display.setStyleSheet("background-color: #0a0a0a; color: #ff0000; border: 1px solid #ff0000;")
            else:
                self.warnings_display.setPlainText("No warnings")
                self.warnings_display.setStyleSheet("background-color: #0a0a0a; color: #00ff00; border: 1px solid #404040;")
        except Exception as e:
            LOGGER.debug(f"Error updating display: {e}")
    
    def _log(self, message: str) -> None:
        """Add message to log."""
        timestamp = time.strftime("%H:%M:%S")
        self.log_display.append(f"[{timestamp}] {message}")
        # Keep last 50 lines
        text = self.log_display.toPlainText()
        lines = text.split("\n")
        if len(lines) > 50:
            self.log_display.setPlainText("\n".join(lines[-50:]))
    
    def set_telemetry_callback(self, callback: callable) -> None:
        """Set telemetry callback function."""
        self.telemetry_callback = callback
        if self.racing_controls:
            self.racing_controls.telemetry_callback = callback
    
    def set_can_sender(self, sender: callable) -> None:
        """Set CAN message sender function."""
        self.can_sender = sender
        if self.racing_controls:
            self.racing_controls.can_sender = sender


__all__ = ["RacingControlsTab"]










