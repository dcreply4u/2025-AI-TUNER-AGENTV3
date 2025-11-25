"""
Advanced Shift Light Manager

Features:
- Customizable RPM thresholds per LED
- Gear-dependent shift points
- Data logging and analysis
- Predictive lap timing integration
- External hardware connectivity (CAN/Bluetooth)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Tuple

LOGGER = logging.getLogger(__name__)


class ShiftLightColor(str, Enum):
    """Shift light colors."""
    OFF = "off"
    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"
    BLUE = "blue"


class FlashMode(str, Enum):
    """Flash modes."""
    SOLID = "solid"
    SLOW = "slow"  # ~2 Hz
    MEDIUM = "medium"  # ~4 Hz
    FAST = "fast"  # ~8 Hz
    VERY_FAST = "very_fast"  # ~16 Hz


@dataclass
class LEDConfig:
    """Configuration for a single LED in the shift light."""
    led_index: int  # 0-based index
    rpm_threshold: float
    color: ShiftLightColor
    flash_mode: FlashMode = FlashMode.SOLID
    brightness: int = 100  # 0-100
    enabled: bool = True


@dataclass
class GearShiftPoint:
    """Shift point configuration for a specific gear."""
    gear: int
    optimal_rpm: float
    max_rpm: float
    shift_light_start_rpm: float  # When to start showing shift light
    shift_light_peak_rpm: float  # When all LEDs should be on


@dataclass
class ShiftEvent:
    """Recorded shift event."""
    timestamp: float
    gear_before: int
    gear_after: int
    rpm_at_shift: float
    reaction_time_ms: float  # Time from peak shift light to actual shift
    lap_time_delta: Optional[float] = None  # Change in lap time vs best
    optimal: bool = False  # Was shift at optimal RPM?


@dataclass
class ShiftLightConfig:
    """Complete shift light configuration."""
    name: str
    led_configs: List[LEDConfig] = field(default_factory=list)
    gear_shift_points: Dict[int, GearShiftPoint] = field(default_factory=dict)
    enable_gear_dependent: bool = True
    enable_predictive_timing: bool = False
    predictive_timing_threshold: float = 0.1  # 0.1s improvement = green
    external_hardware_enabled: bool = False
    external_hardware_type: str = "can"  # "can" or "bluetooth"
    external_hardware_address: Optional[str] = None


class ShiftLightManager:
    """Advanced shift light manager."""
    
    def __init__(self, config: Optional[ShiftLightConfig] = None) -> None:
        """
        Initialize shift light manager.
        
        Args:
            config: Shift light configuration (default config if None)
        """
        self.config = config or self._default_config()
        
        # Current state
        self.current_rpm: float = 0.0
        self.current_gear: int = 1
        self.current_lap_time: Optional[float] = None
        self.best_lap_time: Optional[float] = None
        self.lap_time_delta: float = 0.0
        
        # Active LEDs
        self.active_leds: List[int] = []
        self.last_update_time: float = 0.0
        
        # Shift event logging
        self.shift_events: List[ShiftEvent] = []
        self.max_shift_events = 1000
        
        # Shift detection
        self.last_gear: int = 1
        self.last_rpm: float = 0.0
        self.shift_light_peak_time: Optional[float] = None
        self.shift_light_peak_rpm: Optional[float] = None
        
        # Callbacks
        self.led_update_callbacks: List[Callable[[List[int], List[ShiftLightColor]], None]] = []
        self.shift_event_callbacks: List[Callable[[ShiftEvent], None]] = []
        
        # External hardware
        self.external_hardware: Optional[object] = None
        if self.config.external_hardware_enabled:
            self._init_external_hardware()
    
    def _default_config(self) -> ShiftLightConfig:
        """Create default shift light configuration."""
        # Default 5-LED sequential shift light
        leds = [
            LEDConfig(0, 5000, ShiftLightColor.GREEN, FlashMode.SOLID),
            LEDConfig(1, 5500, ShiftLightColor.YELLOW, FlashMode.SOLID),
            LEDConfig(2, 6000, ShiftLightColor.ORANGE, FlashMode.SLOW),
            LEDConfig(3, 6500, ShiftLightColor.RED, FlashMode.MEDIUM),
            LEDConfig(4, 7000, ShiftLightColor.RED, FlashMode.FAST),
        ]
        
        # Default gear shift points (example for a typical race car)
        gear_points = {
            1: GearShiftPoint(1, 6500, 7500, 6000, 7000),
            2: GearShiftPoint(2, 6800, 7500, 6300, 7200),
            3: GearShiftPoint(3, 7000, 7500, 6500, 7300),
            4: GearShiftPoint(4, 7200, 7500, 6700, 7400),
            5: GearShiftPoint(5, 7400, 7500, 6900, 7500),
            6: GearShiftPoint(6, 7500, 7500, 7100, 7500),
        }
        
        return ShiftLightConfig(
            name="Default",
            led_configs=leds,
            gear_shift_points=gear_points,
        )
    
    def _init_external_hardware(self) -> None:
        """Initialize external shift light hardware."""
        try:
            if self.config.external_hardware_type == "can":
                # Initialize CAN bus connection
                from interfaces.can_interface import CANInterface
                if self.config.external_hardware_address:
                    self.external_hardware = CANInterface(
                        channel=self.config.external_hardware_address
                    )
            elif self.config.external_hardware_type == "bluetooth":
                # Initialize Bluetooth connection
                import bluetooth
                if self.config.external_hardware_address:
                    # Connect to Bluetooth device
                    # Implementation depends on specific hardware
                    pass
        except Exception as e:
            LOGGER.warning("Failed to initialize external shift light hardware: %s", e)
    
    def update(self, rpm: float, gear: int, lap_time: Optional[float] = None) -> None:
        """
        Update shift light state.
        
        Args:
            rpm: Current RPM
            gear: Current gear
            lap_time: Current lap time (for predictive timing)
        """
        self.current_rpm = rpm
        self.current_gear = gear
        self.current_lap_time = lap_time
        
        # Calculate lap time delta
        if lap_time and self.best_lap_time:
            self.lap_time_delta = lap_time - self.best_lap_time
        else:
            self.lap_time_delta = 0.0
        
        # Get shift point for current gear
        if self.config.enable_gear_dependent and gear in self.config.gear_shift_points:
            shift_point = self.config.gear_shift_points[gear]
            effective_rpm = rpm
        else:
            # Use first gear shift point as default
            if 1 in self.config.gear_shift_points:
                shift_point = self.config.gear_shift_points[1]
                effective_rpm = rpm
            else:
                # No shift points configured
                self.active_leds = []
                return
        
        # Check if we've hit peak shift light
        if rpm >= shift_point.shift_light_peak_rpm:
            if self.shift_light_peak_time is None:
                self.shift_light_peak_time = time.time()
                self.shift_light_peak_rpm = rpm
        
        # Determine active LEDs
        active_leds = []
        led_colors = []
        
        for led in self.config.led_configs:
            if not led.enabled:
                continue
            
            # Check if RPM threshold reached
            if rpm >= led.rpm_threshold:
                active_leds.append(led.led_index)
                
                # Determine color (may be overridden by predictive timing)
                color = led.color
                
                # Predictive timing integration
                if self.config.enable_predictive_timing and self.lap_time_delta < 0:
                    # Improving lap time
                    if abs(self.lap_time_delta) >= self.config.predictive_timing_threshold:
                        color = ShiftLightColor.GREEN
                elif self.config.enable_predictive_timing and self.lap_time_delta > 0:
                    # Falling behind
                    if self.lap_time_delta >= self.config.predictive_timing_threshold:
                        color = ShiftLightColor.RED
                
                led_colors.append(color)
        
        self.active_leds = active_leds
        self.last_update_time = time.time()
        
        # Update external hardware
        if self.external_hardware:
            self._update_external_hardware(active_leds, led_colors)
        
        # Notify callbacks
        for callback in self.led_update_callbacks:
            try:
                callback(active_leds, led_colors)
            except Exception as e:
                LOGGER.error("Error in LED update callback: %s", e)
        
        # Detect gear shift
        if gear != self.last_gear:
            self._record_shift_event()
        
        self.last_gear = gear
        self.last_rpm = rpm
    
    def _update_external_hardware(self, active_leds: List[int], colors: List[ShiftLightColor]) -> None:
        """Update external shift light hardware."""
        if not self.external_hardware:
            return
        
        try:
            if self.config.external_hardware_type == "can":
                # Send CAN message with LED states
                # Format depends on specific hardware
                # Example: ID 0x200, data = [gear, active_led_count, led_states...]
                can_data = bytes([
                    self.current_gear,
                    len(active_leds),
                    *active_leds,
                ])
                # self.external_hardware.send_message(0x200, can_data)
        except Exception as e:
            LOGGER.warning("Failed to update external shift light: %s", e)
    
    def _record_shift_event(self) -> None:
        """Record a shift event."""
        if self.shift_light_peak_time is None:
            return
        
        # Calculate reaction time
        reaction_time = (time.time() - self.shift_light_peak_time) * 1000  # ms
        
        # Get shift point for previous gear
        if self.last_gear in self.config.gear_shift_points:
            shift_point = self.config.gear_shift_points[self.last_gear]
            optimal = abs(self.last_rpm - shift_point.optimal_rpm) < 200  # Within 200 RPM
        else:
            optimal = False
        
        event = ShiftEvent(
            timestamp=time.time(),
            gear_before=self.last_gear,
            gear_after=self.current_gear,
            rpm_at_shift=self.last_rpm,
            reaction_time_ms=reaction_time,
            lap_time_delta=self.lap_time_delta if self.lap_time_delta != 0 else None,
            optimal=optimal,
        )
        
        self.shift_events.append(event)
        if len(self.shift_events) > self.max_shift_events:
            self.shift_events.pop(0)
        
        # Reset peak tracking
        self.shift_light_peak_time = None
        self.shift_light_peak_rpm = None
        
        # Notify callbacks
        for callback in self.shift_event_callbacks:
            try:
                callback(event)
            except Exception as e:
                LOGGER.error("Error in shift event callback: %s", e)
    
    def set_best_lap_time(self, lap_time: float) -> None:
        """Set best lap time for predictive timing."""
        if self.best_lap_time is None or lap_time < self.best_lap_time:
            self.best_lap_time = lap_time
    
    def get_shift_analysis(self) -> Dict:
        """Get shift analysis statistics."""
        if not self.shift_events:
            return {
                "total_shifts": 0,
                "average_reaction_time_ms": 0.0,
                "optimal_shift_percentage": 0.0,
            }
        
        total = len(self.shift_events)
        avg_reaction = sum(e.reaction_time_ms for e in self.shift_events) / total
        optimal_count = sum(1 for e in self.shift_events if e.optimal)
        optimal_pct = (optimal_count / total) * 100
        
        return {
            "total_shifts": total,
            "average_reaction_time_ms": avg_reaction,
            "optimal_shift_percentage": optimal_pct,
            "recent_shifts": [
                {
                    "gear": f"{e.gear_before}->{e.gear_after}",
                    "rpm": e.rpm_at_shift,
                    "reaction_ms": e.reaction_time_ms,
                    "optimal": e.optimal,
                }
                for e in self.shift_events[-10:]
            ],
        }
    
    def register_led_update_callback(self, callback: Callable[[List[int], List[ShiftLightColor]], None]) -> None:
        """Register callback for LED state updates."""
        self.led_update_callbacks.append(callback)
    
    def register_shift_event_callback(self, callback: Callable[[ShiftEvent], None]) -> None:
        """Register callback for shift events."""
        self.shift_event_callbacks.append(callback)
    
    def update_config(self, config: ShiftLightConfig) -> None:
        """Update shift light configuration."""
        self.config = config
        if self.config.external_hardware_enabled and not self.external_hardware:
            self._init_external_hardware()


__all__ = [
    "ShiftLightManager",
    "ShiftLightConfig",
    "LEDConfig",
    "GearShiftPoint",
    "ShiftEvent",
    "ShiftLightColor",
    "FlashMode",
]






