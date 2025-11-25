"""
Racing Control Module

Implements anti-lag and launch control systems for racing applications.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

LOGGER = logging.getLogger(__name__)


class AntiLagMode(Enum):
    """Anti-lag operating modes."""

    OFF = "off"
    SOFT = "soft"  # Mild anti-lag for street use
    AGGRESSIVE = "aggressive"  # Full anti-lag for track
    AUTO = "auto"  # Automatic based on conditions


class LaunchControlMode(Enum):
    """Launch control operating modes."""

    OFF = "off"
    RPM_LIMIT = "rpm_limit"  # Simple RPM limiter
    TRACTION = "traction"  # RPM + traction control
    AUTO = "auto"  # Automatic based on conditions


@dataclass
class AntiLagConfig:
    """Anti-lag configuration."""

    enabled: bool = False
    mode: AntiLagMode = AntiLagMode.OFF
    min_rpm: int = 2000  # Minimum RPM to activate
    max_rpm: int = 4000  # Maximum RPM for anti-lag
    boost_target: float = 10.0  # Target boost pressure (PSI)
    safety_max_rpm: int = 5000  # Safety cutoff RPM
    safety_max_egt: float = 1650.0  # Safety max EGT (F)
    activation_delay: float = 0.5  # Delay before activation (seconds)


@dataclass
class LaunchControlConfig:
    """Launch control configuration."""

    enabled: bool = False
    mode: LaunchControlMode = LaunchControlMode.OFF
    launch_rpm: int = 3500  # Target launch RPM
    rpm_tolerance: int = 200  # RPM tolerance band
    max_launch_time: float = 5.0  # Maximum launch duration (seconds)
    min_speed: float = 5.0  # Minimum speed to disable (mph)
    transbrake_required: bool = True  # Require transbrake for launch


@dataclass
class RacingControlState:
    """Current state of racing controls."""

    anti_lag_active: bool = False
    launch_control_active: bool = False
    launch_timer: float = 0.0
    last_update: float = field(default_factory=time.time)
    warnings: list[str] = field(default_factory=list)


class RacingControls:
    """Manages anti-lag and launch control systems."""

    def __init__(
        self,
        can_sender: Optional[Callable[[int, bytes], bool]] = None,
        telemetry_callback: Optional[Callable[[], dict]] = None,
    ) -> None:
        """
        Initialize racing controls.

        Args:
            can_sender: Optional function to send CAN messages (arb_id, data)
            telemetry_callback: Optional function to get current telemetry
        """
        self.anti_lag_config = AntiLagConfig()
        self.launch_config = LaunchControlConfig()
        self.state = RacingControlState()
        self.can_sender = can_sender
        self.telemetry_callback = telemetry_callback
        self._lock = threading.RLock()
        self._control_thread: Optional[threading.Thread] = None
        self._running = False

    def start(self) -> None:
        """Start the racing control system."""
        with self._lock:
            if self._running:
                return
            self._running = True
            self._control_thread = threading.Thread(target=self._control_loop, daemon=True)
            self._control_thread.start()
            LOGGER.info("Racing controls started")

    def stop(self) -> None:
        """Stop the racing control system."""
        with self._lock:
            self._running = False
            self.anti_lag_config.enabled = False
            self.launch_config.enabled = False
            self.state.anti_lag_active = False
            self.state.launch_control_active = False
        if self._control_thread:
            self._control_thread.join(timeout=2.0)
        LOGGER.info("Racing controls stopped")

    def set_anti_lag(self, enabled: bool, mode: AntiLagMode = AntiLagMode.AUTO) -> None:
        """Enable/disable anti-lag."""
        with self._lock:
            self.anti_lag_config.enabled = enabled
            self.anti_lag_config.mode = mode
            if not enabled:
                self.state.anti_lag_active = False
            LOGGER.info("Anti-lag %s (mode: %s)", "enabled" if enabled else "disabled", mode.value)

    def set_launch_control(self, enabled: bool, launch_rpm: int = 3500, mode: LaunchControlMode = LaunchControlMode.RPM_LIMIT) -> None:
        """Enable/disable launch control."""
        with self._lock:
            self.launch_config.enabled = enabled
            self.launch_config.launch_rpm = launch_rpm
            self.launch_config.mode = mode
            if not enabled:
                self.state.launch_control_active = False
                self.state.launch_timer = 0.0
            LOGGER.info("Launch control %s (RPM: %d, mode: %s)", "enabled" if enabled else "disabled", launch_rpm, mode.value)

    def get_state(self) -> RacingControlState:
        """Get current racing control state."""
        with self._lock:
            return RacingControlState(
                anti_lag_active=self.state.anti_lag_active,
                launch_control_active=self.state.launch_control_active,
                launch_timer=self.state.launch_timer,
                last_update=self.state.last_update,
                warnings=list(self.state.warnings),
            )

    def _control_loop(self) -> None:
        """Main control loop running in background thread."""
        while self._running:
            try:
                telemetry = self._get_telemetry()
                if telemetry:
                    self._update_anti_lag(telemetry)
                    self._update_launch_control(telemetry)
                time.sleep(0.1)  # 10 Hz update rate
            except Exception as e:
                LOGGER.error("Error in racing control loop: %s", e)
                time.sleep(0.5)

    def _get_telemetry(self) -> Optional[dict]:
        """Get current telemetry data."""
        if self.telemetry_callback:
            try:
                return self.telemetry_callback()
            except Exception:
                return None
        return None

    def _update_anti_lag(self, telemetry: dict) -> None:
        """Update anti-lag state based on telemetry."""
        if not self.anti_lag_config.enabled:
            self.state.anti_lag_active = False
            return

        rpm = telemetry.get("Engine_RPM", 0) or telemetry.get("RPM", 0) or 0
        boost = telemetry.get("Boost_Pressure", 0) or telemetry.get("Manifold_Pressure", 0) or 0
        egt = telemetry.get("EGT", 0) or telemetry.get("Exhaust_Temp", 0) or 0
        throttle = telemetry.get("Throttle_Position", 0) or telemetry.get("Throttle", 0) or 0

        # Safety checks
        warnings = []
        if rpm > self.anti_lag_config.safety_max_rpm:
            warnings.append("RPM exceeds safety limit")
            self.state.anti_lag_active = False
        elif egt > self.anti_lag_config.safety_max_egt:
            warnings.append("EGT exceeds safety limit")
            self.state.anti_lag_active = False
        else:
            # Activation logic
            should_activate = (
                rpm >= self.anti_lag_config.min_rpm
                and rpm <= self.anti_lag_config.max_rpm
                and throttle < 10  # Low throttle (deceleration/coasting)
                and boost < self.anti_lag_config.boost_target
            )

            if should_activate and not self.state.anti_lag_active:
                # Activate anti-lag
                self.state.anti_lag_active = True
                self._send_anti_lag_command(True)
                LOGGER.info("Anti-lag activated (RPM: %d, Boost: %.1f)", rpm, boost)
            elif not should_activate and self.state.anti_lag_active:
                # Deactivate anti-lag
                self.state.anti_lag_active = False
                self._send_anti_lag_command(False)
                LOGGER.info("Anti-lag deactivated")

        self.state.warnings = warnings
        self.state.last_update = time.time()

    def _update_launch_control(self, telemetry: dict) -> None:
        """Update launch control state based on telemetry."""
        if not self.launch_config.enabled:
            self.state.launch_control_active = False
            self.state.launch_timer = 0.0
            return

        rpm = telemetry.get("Engine_RPM", 0) or telemetry.get("RPM", 0) or 0
        speed = telemetry.get("Vehicle_Speed", 0) or telemetry.get("Speed", 0) or 0
        transbrake = telemetry.get("TransBrakeActive", 0) or telemetry.get("TransBrake", 0) or 0

        # Check if transbrake is required
        if self.launch_config.transbrake_required and not transbrake:
            self.state.launch_control_active = False
            self.state.launch_timer = 0.0
            return

        # Check if vehicle is moving (disable launch control)
        if speed > self.launch_config.min_speed:
            if self.state.launch_control_active:
                self.state.launch_control_active = False
                self.state.launch_timer = 0.0
                self._send_launch_control_command(False)
                LOGGER.info("Launch control disabled (speed: %.1f mph)", speed)
            return

        # Launch control active
        if not self.state.launch_control_active:
            self.state.launch_control_active = True
            self.state.launch_timer = time.time()
            self._send_launch_control_command(True)
            LOGGER.info("Launch control activated (RPM: %d)", rpm)

        # Check launch timer
        elapsed = time.time() - self.state.launch_timer
        if elapsed > self.launch_config.max_launch_time:
            self.state.launch_control_active = False
            self.state.launch_timer = 0.0
            self._send_launch_control_command(False)
            LOGGER.warning("Launch control timeout (%.1f seconds)", elapsed)
            return

        # RPM limiting
        target_rpm = self.launch_config.launch_rpm
        if rpm > target_rpm + self.launch_config.rpm_tolerance:
            self._send_rpm_limit_command(target_rpm)
        elif rpm < target_rpm - self.launch_config.rpm_tolerance:
            # Allow RPM to build up
            pass

        self.state.last_update = time.time()

    def _send_anti_lag_command(self, activate: bool) -> None:
        """Send CAN command to activate/deactivate anti-lag."""
        if not self.can_sender:
            return
        try:
            # Example CAN message (adjust for your ECU)
            # Anti-lag command typically on EMS CAN bus
            arb_id = 0x7E0  # Example: EMS request ID
            data = bytes([0x30, 0x01, 0x01 if activate else 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            self.can_sender(arb_id, data)
        except Exception as e:
            LOGGER.error("Failed to send anti-lag command: %s", e)

    def _send_launch_control_command(self, activate: bool) -> None:
        """Send CAN command to activate/deactivate launch control."""
        if not self.can_sender:
            return
        try:
            # Example CAN message (adjust for your ECU)
            arb_id = 0x7E0  # Example: EMS request ID
            data = bytes([0x30, 0x02, 0x01 if activate else 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            self.can_sender(arb_id, data)
        except Exception as e:
            LOGGER.error("Failed to send launch control command: %s", e)

    def _send_rpm_limit_command(self, rpm_limit: int) -> None:
        """Send CAN command to set RPM limit."""
        if not self.can_sender:
            return
        try:
            # Example CAN message (adjust for your ECU)
            arb_id = 0x7E0  # Example: EMS request ID
            rpm_bytes = rpm_limit.to_bytes(2, byteorder="big")
            data = bytes([0x30, 0x03]) + rpm_bytes + bytes(4)
            self.can_sender(arb_id, data)
        except Exception as e:
            LOGGER.error("Failed to send RPM limit command: %s", e)


__all__ = [
    "AntiLagMode",
    "LaunchControlMode",
    "AntiLagConfig",
    "LaunchControlConfig",
    "RacingControlState",
    "RacingControls",
]

