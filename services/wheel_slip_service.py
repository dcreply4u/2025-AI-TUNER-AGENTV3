"""
Wheel Slip Calculation and Traction Control Service

In drag racing, wheel slippage (wheel spin) is calculated by comparing 
the theoretical driven wheel speed to the actual vehicle speed using 
specialized sensors and data acquisition systems.

Formula:
    Slip% = ((Driven Wheel Speed - Actual Vehicle Speed) / Actual Vehicle Speed) × 100%

- 0% = Pure rolling (no slip)
- Positive % = Wheel spin (driven wheels turning faster than vehicle moving)
- Negative % = Wheel lockup (during braking)

Optimal slip for maximum acceleration is typically 5-15% depending on:
- Tire compound and condition
- Track surface
- Temperature
- Vehicle setup
"""

from __future__ import annotations

import logging
import math
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Deque, Dict, List, Optional, Tuple

from PySide6.QtCore import QObject, Signal

LOGGER = logging.getLogger(__name__)


class SlipStatus(Enum):
    """Wheel slip status categories."""
    OPTIMAL = "optimal"          # 5-12% - Maximum traction
    LOW = "low"                  # 0-5% - Could use more throttle
    MODERATE = "moderate"        # 12-18% - Slight wheel spin
    EXCESSIVE = "excessive"      # 18-30% - Significant wheel spin
    CRITICAL = "critical"        # >30% - Smoking tires, losing time
    LOCKUP = "lockup"            # Negative slip during braking
    STATIONARY = "stationary"    # Vehicle not moving


@dataclass
class SlipReading:
    """Single wheel slip reading with metadata."""
    timestamp: float
    driven_wheel_speed: float  # Speed of driven wheels (mph, km/h, or m/s)
    actual_vehicle_speed: float  # Ground speed from GPS/front wheels
    slip_percentage: float
    status: SlipStatus
    driveshaft_rpm: Optional[float] = None
    tire_diameter_inches: Optional[float] = None


@dataclass
class SlipStatistics:
    """Statistical analysis of slip data over a run."""
    average_slip: float
    max_slip: float
    min_slip: float
    time_in_optimal: float  # Percentage of time in optimal slip
    time_excessive: float   # Percentage of time with excessive slip
    total_readings: int
    slip_events: List[Tuple[float, float]]  # (timestamp, peak_slip) for significant events


@dataclass
class TractionControlRecommendation:
    """Recommendation for traction control adjustment."""
    action: str  # "reduce_power", "increase_power", "maintain", "adjust_timing"
    severity: str  # "immediate", "suggested", "informational"
    message: str
    target_slip: float  # Recommended slip percentage
    current_slip: float
    confidence: float  # 0-1


class WheelSlipService(QObject):
    """
    Calculates and monitors wheel slip for drag racing optimization.
    
    Provides:
    - Real-time slip percentage calculation
    - Optimal slip range monitoring
    - Traction control recommendations
    - Historical slip analysis
    - Integration with ECU for automated corrections
    """
    
    # Qt Signals for UI updates
    slip_updated = Signal(float, str)  # slip_percentage, status
    slip_warning = Signal(str, float)  # message, slip_percentage
    traction_recommendation = Signal(dict)  # recommendation dict
    
    # Optimal slip ranges by tire type (approximate)
    SLIP_RANGES = {
        "street": {"optimal_min": 3.0, "optimal_max": 8.0, "warning": 12.0, "critical": 20.0},
        "drag_radial": {"optimal_min": 5.0, "optimal_max": 12.0, "warning": 18.0, "critical": 25.0},
        "slick": {"optimal_min": 8.0, "optimal_max": 15.0, "warning": 22.0, "critical": 30.0},
        "pro_stock": {"optimal_min": 10.0, "optimal_max": 18.0, "warning": 25.0, "critical": 35.0},
    }
    
    def __init__(
        self,
        tire_type: str = "drag_radial",
        tire_diameter_inches: float = 28.0,
        final_drive_ratio: float = 3.73,
        history_size: int = 1000,
        parent: Optional[QObject] = None,
    ) -> None:
        """
        Initialize wheel slip service.
        
        Args:
            tire_type: Type of tire for optimal slip range selection
            tire_diameter_inches: Rear tire diameter in inches
            final_drive_ratio: Axle ratio for driveshaft-to-wheel conversion
            history_size: Number of readings to keep in history
            parent: Qt parent object
        """
        super().__init__(parent)
        
        self.tire_type = tire_type
        self.tire_diameter_inches = tire_diameter_inches
        self.final_drive_ratio = final_drive_ratio
        self.tire_circumference_miles = (tire_diameter_inches * math.pi) / 63360.0
        
        # Slip ranges for current tire type
        self.slip_config = self.SLIP_RANGES.get(tire_type, self.SLIP_RANGES["drag_radial"])
        
        # History storage
        self.history: Deque[SlipReading] = deque(maxlen=history_size)
        self.current_run_history: List[SlipReading] = []
        
        # Current state
        self.current_slip: float = 0.0
        self.current_status: SlipStatus = SlipStatus.STATIONARY
        self.is_running: bool = False
        
        # Callbacks for traction control
        self.traction_callbacks: List[Callable[[TractionControlRecommendation], None]] = []
        
        # Statistics
        self.run_count: int = 0
        self.total_readings: int = 0
        
        LOGGER.info(
            f"WheelSlipService initialized: tire={tire_type}, "
            f"diameter={tire_diameter_inches}in, ratio={final_drive_ratio}"
        )
    
    def calculate_slip_percentage(
        self,
        driven_wheel_speed: float,
        actual_vehicle_speed: float,
    ) -> float:
        """
        Calculate wheel slip percentage.
        
        Args:
            driven_wheel_speed: Speed of driven wheels (same units as actual)
            actual_vehicle_speed: Actual ground speed of vehicle
            
        Returns:
            Slip percentage (positive = wheel spin, negative = lockup)
        """
        # Handle edge cases
        if actual_vehicle_speed <= 0.1:
            # Vehicle essentially stationary
            if driven_wheel_speed > 1.0:
                return 100.0  # Spinning while stopped
            return 0.0
        
        # Standard slip calculation
        slip = ((driven_wheel_speed - actual_vehicle_speed) / actual_vehicle_speed) * 100.0
        return slip
    
    def driveshaft_rpm_to_wheel_speed(
        self,
        driveshaft_rpm: float,
        gear_ratio: float = 1.0,
    ) -> float:
        """
        Convert driveshaft RPM to wheel speed in mph.
        
        Args:
            driveshaft_rpm: Driveshaft rotational speed
            gear_ratio: Current transmission gear ratio (1.0 if measuring after trans)
            
        Returns:
            Theoretical wheel speed in mph
        """
        # Wheel RPM = Driveshaft RPM / (Final Drive × Gear Ratio)
        wheel_rpm = driveshaft_rpm / (self.final_drive_ratio * gear_ratio)
        
        # Speed = Wheel RPM × Tire Circumference (in miles) × 60 (min to hour)
        speed_mph = wheel_rpm * self.tire_circumference_miles * 60.0
        
        return speed_mph
    
    def get_slip_status(self, slip_percentage: float) -> SlipStatus:
        """
        Determine slip status category from percentage.
        
        Args:
            slip_percentage: Current slip percentage
            
        Returns:
            SlipStatus enum value
        """
        if slip_percentage < -5.0:
            return SlipStatus.LOCKUP
        elif slip_percentage < self.slip_config["optimal_min"]:
            return SlipStatus.LOW
        elif slip_percentage <= self.slip_config["optimal_max"]:
            return SlipStatus.OPTIMAL
        elif slip_percentage <= self.slip_config["warning"]:
            return SlipStatus.MODERATE
        elif slip_percentage <= self.slip_config["critical"]:
            return SlipStatus.EXCESSIVE
        else:
            return SlipStatus.CRITICAL
    
    def update(
        self,
        driven_wheel_speed: float,
        actual_vehicle_speed: float,
        driveshaft_rpm: Optional[float] = None,
    ) -> SlipReading:
        """
        Update with new speed readings and calculate slip.
        
        This is the main method to call with real-time data.
        
        Args:
            driven_wheel_speed: Speed calculated from driven wheels/driveshaft
            actual_vehicle_speed: Actual ground speed (GPS, front wheels)
            driveshaft_rpm: Optional driveshaft RPM for logging
            
        Returns:
            SlipReading with calculated values
        """
        timestamp = time.time()
        
        # Calculate slip
        slip = self.calculate_slip_percentage(driven_wheel_speed, actual_vehicle_speed)
        status = self.get_slip_status(slip)
        
        # Create reading
        reading = SlipReading(
            timestamp=timestamp,
            driven_wheel_speed=driven_wheel_speed,
            actual_vehicle_speed=actual_vehicle_speed,
            slip_percentage=slip,
            status=status,
            driveshaft_rpm=driveshaft_rpm,
            tire_diameter_inches=self.tire_diameter_inches,
        )
        
        # Update state
        self.current_slip = slip
        self.current_status = status
        self.total_readings += 1
        
        # Store in history
        self.history.append(reading)
        if self.is_running:
            self.current_run_history.append(reading)
        
        # Emit signals
        self.slip_updated.emit(slip, status.value)
        
        # Check for warnings
        if status == SlipStatus.EXCESSIVE:
            self.slip_warning.emit("Excessive wheel spin detected!", slip)
        elif status == SlipStatus.CRITICAL:
            self.slip_warning.emit("CRITICAL: Smoking tires! Reduce throttle!", slip)
        
        # Generate traction recommendation if needed
        if status in (SlipStatus.EXCESSIVE, SlipStatus.CRITICAL, SlipStatus.LOW):
            rec = self._generate_recommendation(slip, status)
            self.traction_recommendation.emit(rec.__dict__)
            for callback in self.traction_callbacks:
                try:
                    callback(rec)
                except Exception as e:
                    LOGGER.error(f"Traction callback error: {e}")
        
        return reading
    
    def update_from_driveshaft(
        self,
        driveshaft_rpm: float,
        actual_vehicle_speed: float,
        gear_ratio: float = 1.0,
    ) -> SlipReading:
        """
        Update using driveshaft RPM instead of wheel speed.
        
        Args:
            driveshaft_rpm: Current driveshaft RPM
            actual_vehicle_speed: Actual ground speed in mph
            gear_ratio: Current transmission gear ratio
            
        Returns:
            SlipReading with calculated values
        """
        driven_wheel_speed = self.driveshaft_rpm_to_wheel_speed(driveshaft_rpm, gear_ratio)
        return self.update(driven_wheel_speed, actual_vehicle_speed, driveshaft_rpm)
    
    def _generate_recommendation(
        self,
        slip: float,
        status: SlipStatus,
    ) -> TractionControlRecommendation:
        """Generate traction control recommendation."""
        optimal_target = (self.slip_config["optimal_min"] + self.slip_config["optimal_max"]) / 2
        
        if status == SlipStatus.CRITICAL:
            return TractionControlRecommendation(
                action="reduce_power",
                severity="immediate",
                message="Immediate power reduction required! Tires losing traction.",
                target_slip=optimal_target,
                current_slip=slip,
                confidence=0.95,
            )
        elif status == SlipStatus.EXCESSIVE:
            return TractionControlRecommendation(
                action="reduce_power",
                severity="suggested",
                message="Reduce throttle slightly to optimize traction.",
                target_slip=optimal_target,
                current_slip=slip,
                confidence=0.85,
            )
        elif status == SlipStatus.LOW:
            return TractionControlRecommendation(
                action="increase_power",
                severity="informational",
                message="Room for more throttle - not at optimal slip.",
                target_slip=optimal_target,
                current_slip=slip,
                confidence=0.7,
            )
        else:
            return TractionControlRecommendation(
                action="maintain",
                severity="informational",
                message="Maintaining optimal slip range.",
                target_slip=optimal_target,
                current_slip=slip,
                confidence=0.9,
            )
    
    def start_run(self) -> None:
        """Start a new run - clears run-specific history."""
        self.is_running = True
        self.current_run_history.clear()
        self.run_count += 1
        LOGGER.info(f"Started run #{self.run_count}")
    
    def end_run(self) -> SlipStatistics:
        """
        End current run and calculate statistics.
        
        Returns:
            SlipStatistics for the completed run
        """
        self.is_running = False
        stats = self.calculate_statistics(self.current_run_history)
        LOGGER.info(f"Run #{self.run_count} complete: avg_slip={stats.average_slip:.1f}%")
        return stats
    
    def calculate_statistics(
        self,
        readings: Optional[List[SlipReading]] = None,
    ) -> SlipStatistics:
        """
        Calculate slip statistics for a set of readings.
        
        Args:
            readings: List of readings to analyze (defaults to current run)
            
        Returns:
            SlipStatistics dataclass
        """
        if readings is None:
            readings = self.current_run_history
        
        if not readings:
            return SlipStatistics(
                average_slip=0.0,
                max_slip=0.0,
                min_slip=0.0,
                time_in_optimal=0.0,
                time_excessive=0.0,
                total_readings=0,
                slip_events=[],
            )
        
        slips = [r.slip_percentage for r in readings]
        optimal_count = sum(1 for r in readings if r.status == SlipStatus.OPTIMAL)
        excessive_count = sum(
            1 for r in readings 
            if r.status in (SlipStatus.EXCESSIVE, SlipStatus.CRITICAL)
        )
        
        # Find significant slip events (peaks above warning threshold)
        slip_events: List[Tuple[float, float]] = []
        in_event = False
        event_peak = 0.0
        event_time = 0.0
        
        for reading in readings:
            if reading.slip_percentage > self.slip_config["warning"]:
                if not in_event:
                    in_event = True
                    event_time = reading.timestamp
                    event_peak = reading.slip_percentage
                else:
                    event_peak = max(event_peak, reading.slip_percentage)
            else:
                if in_event:
                    slip_events.append((event_time, event_peak))
                    in_event = False
        
        # Capture final event if still in one
        if in_event:
            slip_events.append((event_time, event_peak))
        
        return SlipStatistics(
            average_slip=sum(slips) / len(slips),
            max_slip=max(slips),
            min_slip=min(slips),
            time_in_optimal=(optimal_count / len(readings)) * 100.0,
            time_excessive=(excessive_count / len(readings)) * 100.0,
            total_readings=len(readings),
            slip_events=slip_events,
        )
    
    def set_tire_type(self, tire_type: str) -> None:
        """Update tire type and slip ranges."""
        if tire_type in self.SLIP_RANGES:
            self.tire_type = tire_type
            self.slip_config = self.SLIP_RANGES[tire_type]
            LOGGER.info(f"Tire type updated to: {tire_type}")
        else:
            LOGGER.warning(f"Unknown tire type: {tire_type}")
    
    def set_tire_diameter(self, diameter_inches: float) -> None:
        """Update tire diameter for calculations."""
        self.tire_diameter_inches = diameter_inches
        self.tire_circumference_miles = (diameter_inches * math.pi) / 63360.0
        LOGGER.info(f"Tire diameter updated to: {diameter_inches} inches")
    
    def set_final_drive_ratio(self, ratio: float) -> None:
        """Update final drive ratio."""
        self.final_drive_ratio = ratio
        LOGGER.info(f"Final drive ratio updated to: {ratio}")
    
    def add_traction_callback(
        self,
        callback: Callable[[TractionControlRecommendation], None],
    ) -> None:
        """Add a callback for traction control recommendations."""
        self.traction_callbacks.append(callback)
    
    def get_current_slip(self) -> Tuple[float, SlipStatus]:
        """Get current slip percentage and status."""
        return self.current_slip, self.current_status
    
    def get_optimal_range(self) -> Tuple[float, float]:
        """Get optimal slip range for current tire type."""
        return self.slip_config["optimal_min"], self.slip_config["optimal_max"]
    
    def get_recent_average(self, samples: int = 10) -> float:
        """Get average slip over recent samples."""
        if not self.history:
            return 0.0
        
        recent = list(self.history)[-samples:]
        return sum(r.slip_percentage for r in recent) / len(recent)
    
    def get_slip_color(self, slip: Optional[float] = None) -> str:
        """Get color code for slip percentage (for UI)."""
        if slip is None:
            slip = self.current_slip
        
        status = self.get_slip_status(slip)
        
        color_map = {
            SlipStatus.OPTIMAL: "#27ae60",     # Green
            SlipStatus.LOW: "#3498db",         # Blue
            SlipStatus.MODERATE: "#f39c12",    # Orange
            SlipStatus.EXCESSIVE: "#e74c3c",   # Red
            SlipStatus.CRITICAL: "#8e44ad",    # Purple (danger)
            SlipStatus.LOCKUP: "#2c3e50",      # Dark gray
            SlipStatus.STATIONARY: "#95a5a6",  # Gray
        }
        
        return color_map.get(status, "#95a5a6")


# Convenience function for simple calculations
def calculate_wheel_slip_percentage(
    driven_wheel_speed: float,
    actual_vehicle_speed: float,
) -> float:
    """
    Calculate wheel slip percentage (standalone function).
    
    Args:
        driven_wheel_speed: Speed of driven wheels (rear wheels/driveshaft)
        actual_vehicle_speed: Actual ground speed from GPS/front wheels
        
    Returns:
        Slip percentage (0% = pure rolling, positive = wheel spin)
    """
    if actual_vehicle_speed <= 0:
        return 0.0 if driven_wheel_speed <= 0 else 100.0
    
    return ((driven_wheel_speed - actual_vehicle_speed) / actual_vehicle_speed) * 100.0


__all__ = [
    "WheelSlipService",
    "SlipReading",
    "SlipStatistics",
    "SlipStatus",
    "TractionControlRecommendation",
    "calculate_wheel_slip_percentage",
]






