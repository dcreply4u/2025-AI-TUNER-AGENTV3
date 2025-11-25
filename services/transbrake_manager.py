"""
Advanced Transbrake Manager

Features:
- Adjustable launch parameters (RPM, boost, timing)
- Staging control (Bump and Creep)
- Clutch slip/torque converter control
- Integrated safety features
- Data analysis (G-force, wheel speed, 60-foot times)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Tuple

LOGGER = logging.getLogger(__name__)


class TransbrakeState(str, Enum):
    """Transbrake states."""
    DISABLED = "disabled"
    ARMED = "armed"
    ENGAGED = "engaged"
    LAUNCHING = "launching"
    RELEASED = "released"
    ERROR = "error"


class StagingMode(str, Enum):
    """Staging control modes."""
    MANUAL = "manual"
    BUMP = "bump"  # Pulse on/off to move forward
    CREEP = "creep"  # Slow continuous movement


@dataclass
class LaunchParameters:
    """Launch parameters configuration."""
    target_rpm: float = 4000.0
    target_boost_psi: float = 0.0  # For turbo/supercharged
    timing_advance: float = 0.0  # Timing adjustment during launch
    enable_boost_control: bool = False
    enable_timing_control: bool = False


@dataclass
class StagingConfig:
    """Staging control configuration."""
    mode: StagingMode = StagingMode.MANUAL
    bump_duty_cycle: float = 0.5  # 0.0-1.0
    bump_frequency_hz: float = 2.0  # Hz
    creep_duty_cycle: float = 0.3  # 0.0-1.0
    creep_frequency_hz: float = 1.0  # Hz
    max_staging_time_seconds: float = 30.0  # Safety timeout


@dataclass
class ClutchSlipConfig:
    """Clutch slip/torque converter control configuration."""
    enable_slip_control: bool = False
    target_slip_rpm: float = 0.0  # Target slip RPM
    slip_table: Dict[float, float] = field(default_factory=dict)  # Time -> Slip RPM
    max_slip_time_seconds: float = 2.0
    release_threshold_rpm: float = 0.0  # Release when RPM drops below this


@dataclass
class SafetyLimits:
    """Safety limits for transbrake operation."""
    max_coolant_temp_f: float = 220.0
    max_trans_temp_f: float = 250.0
    max_launch_time_seconds: float = 5.0
    min_battery_voltage: float = 12.0
    enable_safety_checks: bool = True


@dataclass
class LaunchEvent:
    """Recorded launch event."""
    timestamp: float
    launch_rpm: float
    launch_boost: float
    launch_timing: float
    g_force_peak: float
    g_force_60ft: float
    wheel_speed_60ft: float
    time_60ft: float
    time_330ft: Optional[float] = None
    time_660ft: Optional[float] = None
    trap_speed: Optional[float] = None
    staging_time: float = 0.0
    safety_triggered: bool = False
    safety_reason: Optional[str] = None


@dataclass
class TransbrakeConfig:
    """Complete transbrake configuration."""
    name: str
    launch_params: LaunchParameters = field(default_factory=LaunchParameters)
    staging_config: StagingConfig = field(default_factory=StagingConfig)
    clutch_slip_config: ClutchSlipConfig = field(default_factory=ClutchSlipConfig)
    safety_limits: SafetyLimits = field(default_factory=SafetyLimits)
    enable_data_logging: bool = True


class TransbrakeManager:
    """Advanced transbrake manager."""
    
    def __init__(self, config: Optional[TransbrakeConfig] = None) -> None:
        """
        Initialize transbrake manager.
        
        Args:
            config: Transbrake configuration (default config if None)
        """
        self.config = config or self._default_config()
        
        # Current state
        self.state = TransbrakeState.DISABLED
        self.armed = False
        self.engaged = False
        
        # Current sensor readings
        self.current_rpm: float = 0.0
        self.current_boost: float = 0.0
        self.current_timing: float = 0.0
        self.coolant_temp_f: float = 0.0
        self.trans_temp_f: float = 0.0
        self.battery_voltage: float = 12.6
        self.g_force: float = 0.0
        self.wheel_speed_mph: float = 0.0
        
        # Launch tracking
        self.launch_start_time: Optional[float] = None
        self.staging_start_time: Optional[float] = None
        self.last_staging_pulse_time: float = 0.0
        self.staging_pulse_state: bool = False
        
        # Launch events
        self.launch_events: List[LaunchEvent] = []
        self.max_launch_events = 100
        
        # Callbacks
        self.state_change_callbacks: List[Callable[[TransbrakeState], None]] = []
        self.launch_event_callbacks: List[Callable[[LaunchEvent], None]] = []
        
        # Data logging
        self.launch_data_log: List[Dict] = []
        self.logging_enabled = self.config.enable_data_logging
    
    def _default_config(self) -> TransbrakeConfig:
        """Create default transbrake configuration."""
        return TransbrakeConfig(
            name="Default",
            launch_params=LaunchParameters(
                target_rpm=4000.0,
                target_boost_psi=0.0,
                timing_advance=0.0,
            ),
            staging_config=StagingConfig(),
            clutch_slip_config=ClutchSlipConfig(),
            safety_limits=SafetyLimits(),
        )
    
    def arm(self) -> bool:
        """
        Arm the transbrake.
        
        Returns:
            True if armed successfully
        """
        if not self._check_safety():
            self.state = TransbrakeState.ERROR
            return False
        
        self.armed = True
        self.state = TransbrakeState.ARMED
        self._notify_state_change()
        LOGGER.info("Transbrake armed")
        return True
    
    def disarm(self) -> None:
        """Disarm the transbrake."""
        self.armed = False
        if self.engaged:
            self.release()
        self.state = TransbrakeState.DISABLED
        self._notify_state_change()
        LOGGER.info("Transbrake disarmed")
    
    def engage(self) -> bool:
        """
        Engage the transbrake.
        
        Returns:
            True if engaged successfully
        """
        if not self.armed:
            LOGGER.warning("Cannot engage transbrake - not armed")
            return False
        
        if not self._check_safety():
            self.state = TransbrakeState.ERROR
            return False
        
        self.engaged = True
        self.state = TransbrakeState.ENGAGED
        self.staging_start_time = time.time()
        self._notify_state_change()
        LOGGER.info("Transbrake engaged")
        
        # Start launch parameter control
        self._start_launch_control()
        
        return True
    
    def release(self) -> None:
        """Release the transbrake."""
        if not self.engaged:
            return
        
        self.engaged = False
        self.state = TransbrakeState.RELEASED
        
        # Record launch event
        if self.launch_start_time:
            self._record_launch_event()
        
        self.launch_start_time = None
        self.staging_start_time = None
        self._notify_state_change()
        LOGGER.info("Transbrake released")
    
    def update(
        self,
        rpm: float,
        boost: float = 0.0,
        timing: float = 0.0,
        coolant_temp: float = 0.0,
        trans_temp: float = 0.0,
        battery_voltage: float = 12.6,
        g_force: float = 0.0,
        wheel_speed: float = 0.0,
    ) -> None:
        """
        Update transbrake with current sensor data.
        
        Args:
            rpm: Current RPM
            boost: Current boost pressure (PSI)
            timing: Current timing advance
            coolant_temp: Coolant temperature (F)
            trans_temp: Transmission temperature (F)
            battery_voltage: Battery voltage
            g_force: Current G-force
            wheel_speed: Wheel speed (MPH)
        """
        self.current_rpm = rpm
        self.current_boost = boost
        self.current_timing = timing
        self.coolant_temp_f = coolant_temp
        self.trans_temp_f = trans_temp
        self.battery_voltage = battery_voltage
        self.g_force = g_force
        self.wheel_speed_mph = wheel_speed
        
        # Check safety limits
        if self.engaged and not self._check_safety():
            LOGGER.warning("Safety limit exceeded - releasing transbrake")
            self.release()
            return
        
        # Handle staging control
        if self.engaged and self.config.staging_config.mode != StagingMode.MANUAL:
            self._update_staging_control()
        
        # Handle launch control
        if self.engaged:
            self._update_launch_control()
        
        # Detect launch (when transbrake is released and car starts moving)
        if self.state == TransbrakeState.RELEASED and g_force > 0.1:
            if self.launch_start_time is None:
                self.launch_start_time = time.time()
                self.state = TransbrakeState.LAUNCHING
                self._notify_state_change()
        
        # Log launch data
        if self.logging_enabled and self.state == TransbrakeState.LAUNCHING:
            self._log_launch_data()
    
    def _check_safety(self) -> bool:
        """Check safety limits."""
        if not self.config.safety_limits.enable_safety_checks:
            return True
        
        limits = self.config.safety_limits
        
        if self.coolant_temp_f > limits.max_coolant_temp_f:
            LOGGER.error("Coolant temperature too high: %.1f F", self.coolant_temp_f)
            return False
        
        if self.trans_temp_f > limits.max_trans_temp_f:
            LOGGER.error("Transmission temperature too high: %.1f F", self.trans_temp_f)
            return False
        
        if self.battery_voltage < limits.min_battery_voltage:
            LOGGER.error("Battery voltage too low: %.2f V", self.battery_voltage)
            return False
        
        if self.engaged and self.staging_start_time:
            elapsed = time.time() - self.staging_start_time
            if elapsed > limits.max_launch_time_seconds:
                LOGGER.error("Launch time exceeded: %.1f s", elapsed)
                return False
        
        return True
    
    def _start_launch_control(self) -> None:
        """Start launch parameter control."""
        # This would interface with ECU to set target RPM, boost, timing
        # Implementation depends on ECU type
        pass
    
    def _update_launch_control(self) -> None:
        """Update launch parameter control."""
        params = self.config.launch_params
        
        # Control RPM (if supported by ECU)
        if params.target_rpm > 0:
            # Send RPM target to ECU
            pass
        
        # Control boost (if enabled)
        if params.enable_boost_control and params.target_boost_psi > 0:
            # Send boost target to boost controller
            pass
        
        # Control timing (if enabled)
        if params.enable_timing_control:
            # Send timing adjustment to ECU
            pass
    
    def _update_staging_control(self) -> None:
        """Update staging control (bump/creep)."""
        if not self.staging_start_time:
            return
        
        now = time.time()
        elapsed = now - self.staging_start_time
        
        # Check timeout
        if elapsed > self.config.staging_config.max_staging_time_seconds:
            LOGGER.warning("Staging timeout exceeded")
            return
        
        config = self.config.staging_config
        
        if config.mode == StagingMode.BUMP:
            # Calculate pulse timing
            period = 1.0 / config.bump_frequency_hz
            phase = (elapsed % period) / period
            
            # Pulse on/off based on duty cycle
            should_pulse = phase < config.bump_duty_cycle
            
            if should_pulse != self.staging_pulse_state:
                self.staging_pulse_state = should_pulse
                # Send pulse command to transbrake solenoid
                # self._send_transbrake_pulse(should_pulse)
        
        elif config.mode == StagingMode.CREEP:
            # Continuous low-duty cycle pulsing
            period = 1.0 / config.creep_frequency_hz
            phase = (elapsed % period) / period
            
            should_pulse = phase < config.creep_duty_cycle
            
            if should_pulse != self.staging_pulse_state:
                self.staging_pulse_state = should_pulse
                # self._send_transbrake_pulse(should_pulse)
    
    def _log_launch_data(self) -> None:
        """Log launch data for analysis."""
        if not self.launch_start_time:
            return
        
        elapsed = time.time() - self.launch_start_time
        
        # Calculate 60-foot time
        # This would typically come from track timing system
        # For now, estimate based on wheel speed and G-force
        
        data_point = {
            "timestamp": time.time(),
            "elapsed": elapsed,
            "rpm": self.current_rpm,
            "boost": self.current_boost,
            "g_force": self.g_force,
            "wheel_speed": self.wheel_speed_mph,
            "distance_ft": self._estimate_distance_ft(elapsed),
        }
        
        self.launch_data_log.append(data_point)
    
    def _estimate_distance_ft(self, elapsed: float) -> float:
        """Estimate distance traveled in feet."""
        # Simple integration of velocity
        # More accurate would use actual distance sensors
        if elapsed == 0:
            return 0.0
        
        # Convert MPH to ft/s and integrate
        velocity_ft_s = self.wheel_speed_mph * 1.46667
        distance = velocity_ft_s * elapsed
        return distance
    
    def _record_launch_event(self) -> None:
        """Record a launch event."""
        if not self.launch_start_time:
            return
        
        # Find 60-foot data
        time_60ft = None
        g_force_60ft = 0.0
        wheel_speed_60ft = 0.0
        
        for data in self.launch_data_log:
            if data.get("distance_ft", 0) >= 60.0:
                time_60ft = data.get("elapsed", 0)
                g_force_60ft = data.get("g_force", 0.0)
                wheel_speed_60ft = data.get("wheel_speed", 0.0)
                break
        
        # Find peak G-force
        peak_g = max((d.get("g_force", 0.0) for d in self.launch_data_log), default=0.0)
        
        event = LaunchEvent(
            timestamp=time.time(),
            launch_rpm=self.current_rpm,
            launch_boost=self.current_boost,
            launch_timing=self.current_timing,
            g_force_peak=peak_g,
            g_force_60ft=g_force_60ft,
            wheel_speed_60ft=wheel_speed_60ft,
            time_60ft=time_60ft or 0.0,
            staging_time=(self.staging_start_time - time.time()) if self.staging_start_time else 0.0,
            safety_triggered=False,
        )
        
        self.launch_events.append(event)
        if len(self.launch_events) > self.max_launch_events:
            self.launch_events.pop(0)
        
        # Notify callbacks
        for callback in self.launch_event_callbacks:
            try:
                callback(event)
            except Exception as e:
                LOGGER.error("Error in launch event callback: %s", e)
        
        # Clear launch data log
        self.launch_data_log = []
    
    def get_launch_analysis(self) -> Dict:
        """Get launch analysis statistics."""
        if not self.launch_events:
            return {
                "total_launches": 0,
                "average_60ft_time": 0.0,
                "best_60ft_time": 0.0,
            }
        
        total = len(self.launch_events)
        avg_60ft = sum(e.time_60ft for e in self.launch_events if e.time_60ft > 0) / total
        best_60ft = min((e.time_60ft for e in self.launch_events if e.time_60ft > 0), default=0.0)
        
        return {
            "total_launches": total,
            "average_60ft_time": avg_60ft,
            "best_60ft_time": best_60ft,
            "average_peak_g": sum(e.g_force_peak for e in self.launch_events) / total,
            "recent_launches": [
                {
                    "rpm": e.launch_rpm,
                    "boost": e.launch_boost,
                    "60ft_time": e.time_60ft,
                    "peak_g": e.g_force_peak,
                }
                for e in self.launch_events[-10:]
            ],
        }
    
    def register_state_change_callback(self, callback: Callable[[TransbrakeState], None]) -> None:
        """Register callback for state changes."""
        self.state_change_callbacks.append(callback)
    
    def register_launch_event_callback(self, callback: Callable[[LaunchEvent], None]) -> None:
        """Register callback for launch events."""
        self.launch_event_callbacks.append(callback)
    
    def _notify_state_change(self) -> None:
        """Notify callbacks of state change."""
        for callback in self.state_change_callbacks:
            try:
                callback(self.state)
            except Exception as e:
                LOGGER.error("Error in state change callback: %s", e)
    
    def update_config(self, config: TransbrakeConfig) -> None:
        """Update transbrake configuration."""
        self.config = config
        self.logging_enabled = config.enable_data_logging


__all__ = [
    "TransbrakeManager",
    "TransbrakeConfig",
    "LaunchParameters",
    "StagingConfig",
    "ClutchSlipConfig",
    "SafetyLimits",
    "LaunchEvent",
    "TransbrakeState",
    "StagingMode",
]






