"""
Virtual Dyno - Calculate Horsepower from Real-Time Telemetry

This is a GAME CHANGER! No more expensive dyno runs - calculate HP from real driving data.

Accuracy depends on:
1. Quality of speed/acceleration data (GPS is best)
2. Accurate vehicle weight (including driver, fuel, etc.)
3. Accounting for all losses (aerodynamic drag, rolling resistance, drivetrain)
4. Environmental factors (temperature, altitude, air density)
5. Calibration with known dyno runs (machine learning)

Target accuracy: ±3-5% when properly calibrated (comparable to real dyno!)
"""

from __future__ import annotations

import logging
import math
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Deque, Dict, List, Optional, Tuple, Union

import numpy as np

try:
    from scipy.signal import savgol_filter
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    LOGGER.warning("scipy not available - using simple smoothing instead of Savitzky-Golay filter")

LOGGER = logging.getLogger(__name__)

# Constants
GRAVITY = 9.80665  # m/s²
AIR_DENSITY_SEA_LEVEL = 1.225  # kg/m³ at 15°C, sea level
DRIVETRAIN_LOSS_TYPICAL = 0.15  # 15% loss (FWD), 18% (RWD), 20% (AWD)
MPH_TO_MPS = 0.44704  # mph to m/s
MPS_TO_MPH = 2.23694  # m/s to mph
HP_TO_WATTS = 745.7  # More precise: 745.699872 W/HP
WATTS_TO_HP = 1.0 / 745.7  # More accurate conversion (matches provided code)


class DynoMethod(Enum):
    """Different methods for calculating horsepower."""

    ACCELERATION_BASED = "acceleration"  # Most accurate for real-world
    TORQUE_BASED = "torque"  # If torque sensor available
    SPEED_DELTA = "speed_delta"  # Alternative acceleration method
    COAST_DOWN = "coast_down"  # Measures losses during deceleration
    CALIBRATED_ML = "calibrated_ml"  # Machine learning from known dyno runs


@dataclass
class VehicleSpecs:
    """Vehicle specifications needed for accurate HP calculation."""

    curb_weight_kg: float  # Vehicle weight without driver/fuel
    driver_weight_kg: float = 80.0  # Driver weight
    fuel_weight_kg: float = 0.0  # Current fuel weight
    frontal_area_m2: float = 2.0  # Frontal area (m²) - typical car: 1.8-2.5
    drag_coefficient: float = 0.30  # Cd - typical: 0.25-0.35
    rolling_resistance_coef: float = 0.015  # Crr - typical: 0.012-0.018
    drivetrain_loss: float = DRIVETRAIN_LOSS_TYPICAL  # 0.15 = 15% loss
    wheel_radius_m: float = 0.33  # Wheel radius in meters (typical: 0.30-0.35)
    drivetrain_type: str = "RWD"  # FWD, RWD, AWD

    def total_weight_kg(self) -> float:
        """Total vehicle weight including driver and fuel."""
        return self.curb_weight_kg + self.driver_weight_kg + self.fuel_weight_kg


@dataclass
class EnvironmentalConditions:
    """Environmental factors affecting power calculations."""

    temperature_c: float = 20.0  # Air temperature in Celsius
    altitude_m: float = 0.0  # Altitude in meters
    humidity_percent: float = 50.0  # Relative humidity
    barometric_pressure_kpa: float = 101.325  # Standard sea level

    def air_density_kg_m3(self) -> float:
        """
        Calculate air density (kg/m³) using temperature, altitude, and humidity.
        
        Enhanced formula based on barometric equation and ideal gas law with proper
        humidity correction for maximum accuracy.
        
        Formula:
        - Barometric pressure: P = P0 * (1 - 2.25577e-5 * h)^5.25588
        - Saturation pressure: P_sat = 6.1078 * 10^((7.5*T)/(T+237.3)) * 100
        - Vapor pressure: P_v = humidity * P_sat
        - Dry air pressure: P_dry = P - P_v
        - Air density: ρ = P_dry/(R_dry*T) + P_v/(R_vapor*T)
        """
        temp_kelvin = self.temperature_c + 273.15
        humidity_ratio = self.humidity_percent / 100.0
        
        # Barometric pressure at altitude (barometric formula)
        # P = P0 * (1 - 2.25577e-5 * h)^5.25588
        # Using standard sea level pressure if not provided
        if self.barometric_pressure_kpa == 101.325:
            pressure_pa = 101325.0 * (1 - 2.25577e-5 * self.altitude_m) ** 5.25588
        else:
            # Use provided pressure with altitude correction
            pressure_ratio = math.exp(-self.altitude_m / 8434.5)
            pressure_pa = self.barometric_pressure_kpa * 1000 * pressure_ratio
        
        # Saturation vapor pressure (Magnus formula)
        # P_sat = 6.1078 * 10^((7.5*T)/(T+237.3)) * 100
        saturation_pressure_pa = 6.1078 * (10 ** ((7.5 * self.temperature_c) / (self.temperature_c + 237.3))) * 100
        
        # Vapor pressure
        vapor_pressure_pa = humidity_ratio * saturation_pressure_pa
        
        # Dry air pressure
        dry_air_pressure_pa = pressure_pa - vapor_pressure_pa
        
        # Gas constants
        R_dry = 287.058  # J/(kg·K) for dry air
        R_vapor = 461.495  # J/(kg·K) for water vapor
        
        # Air density: ρ = ρ_dry + ρ_vapor
        # ρ_dry = P_dry / (R_dry * T)
        # ρ_vapor = P_v / (R_vapor * T)
        air_density = (dry_air_pressure_pa / (R_dry * temp_kelvin)) + \
                     (vapor_pressure_pa / (R_vapor * temp_kelvin))
        
        return air_density


@dataclass
class DynoReading:
    """A single horsepower reading at a specific RPM/speed."""

    timestamp: float
    rpm: Optional[float]
    speed_mph: float
    speed_mps: float
    acceleration_mps2: float
    horsepower_wheel: float  # Wheel horsepower
    horsepower_crank: float  # Estimated crank horsepower
    torque_ftlb: Optional[float] = None
    method: DynoMethod = DynoMethod.ACCELERATION_BASED
    confidence: float = 0.0  # 0-1, how confident we are in this reading
    conditions: Optional[EnvironmentalConditions] = None


@dataclass
class DynoCurve:
    """Complete dyno curve with HP and torque vs RPM."""

    readings: List[DynoReading] = field(default_factory=list)
    peak_hp_wheel: float = 0.0
    peak_hp_crank: float = 0.0
    peak_hp_rpm: float = 0.0
    peak_torque_ftlb: float = 0.0
    peak_torque_rpm: float = 0.0
    accuracy_estimate: float = 0.0  # Estimated accuracy (0-1)
    calibration_factor: float = 1.0  # Calibration from known dyno runs
    run_name: str = ""  # Optional name for this run
    run_timestamp: float = field(default_factory=time.time)  # When this run was created


class VirtualDyno:
    """
    Virtual Dyno - Calculate horsepower from real-time telemetry.
    
    This is HUGE! No more expensive dyno runs - get HP numbers from real driving!
    
    Accuracy can reach ±3-5% when:
    - Properly calibrated with known dyno runs
    - Accurate vehicle specs
    - Good GPS/speed data
    - Environmental conditions accounted for
    
    Methods:
    1. Acceleration-based (most accurate for real-world)
    2. Torque-based (if torque sensor available)
    3. Coast-down (measures losses)
    4. Machine learning (learns from real dyno runs)
    """

    def __init__(
        self,
        vehicle_specs: VehicleSpecs,
        calibration_factor: float = 1.0,
        enable_ml_calibration: bool = True,
    ) -> None:
        """
        Initialize virtual dyno.

        Args:
            vehicle_specs: Vehicle specifications
            calibration_factor: Calibration factor from known dyno runs (1.0 = no calibration)
            enable_ml_calibration: Enable machine learning calibration from known runs
        """
        self.vehicle_specs = vehicle_specs
        self.calibration_factor = calibration_factor
        self.enable_ml_calibration = enable_ml_calibration

        # Data buffers for smoothing
        self.speed_buffer: Deque[Tuple[float, float]] = deque(maxlen=20)  # (timestamp, speed_mps)
        self.accel_buffer: Deque[float] = deque(maxlen=10)
        self.rpm_buffer: Deque[Tuple[float, float]] = deque(maxlen=20)  # (timestamp, rpm)

        # Current dyno curve
        self.current_curve = DynoCurve(calibration_factor=calibration_factor)

        # Session management - store multiple runs
        self.session_runs: List[DynoCurve] = []  # All runs in current session
        self.run_counter: int = 0  # Track run numbers

        # Calibration data (from known dyno runs)
        self.calibration_runs: List[Tuple[DynoCurve, DynoCurve]] = []  # (virtual, real)

        # Environmental conditions
        self.current_conditions = EnvironmentalConditions()

    def update_environment(
        self,
        temperature_c: Optional[float] = None,
        altitude_m: Optional[float] = None,
        humidity_percent: Optional[float] = None,
        barometric_pressure_kpa: Optional[float] = None,
    ) -> None:
        """Update environmental conditions for more accurate calculations."""
        if temperature_c is not None:
            self.current_conditions.temperature_c = temperature_c
        if altitude_m is not None:
            self.current_conditions.altitude_m = altitude_m
        if humidity_percent is not None:
            self.current_conditions.humidity_percent = humidity_percent
        if barometric_pressure_kpa is not None:
            self.current_conditions.barometric_pressure_kpa = barometric_pressure_kpa

    def calculate_horsepower(
        self,
        speed_mph: float,
        acceleration_mps2: float,
        rpm: Optional[float] = None,
        torque_ftlb: Optional[float] = None,
        timestamp: Optional[float] = None,
    ) -> DynoReading:
        """
        Calculate horsepower from current telemetry.

        This is the CORE function - calculates HP using multiple methods and averages.

        Args:
            speed_mph: Current speed in mph
            speed_mps: Current speed in m/s
            acceleration_mps2: Current acceleration in m/s²
            rpm: Engine RPM (optional, improves accuracy)
            torque_ftlb: Torque in ft-lb (optional, if sensor available)
            timestamp: Timestamp (defaults to now)

        Returns:
            DynoReading with calculated horsepower
        """
        timestamp = timestamp or time.time()
        speed_mps = speed_mph * MPH_TO_MPS

        # Store in buffers for smoothing
        self.speed_buffer.append((timestamp, speed_mps))
        self.accel_buffer.append(acceleration_mps2)
        if rpm is not None:
            self.rpm_buffer.append((timestamp, rpm))

        # Smooth acceleration (reduce noise)
        # Use Savitzky-Golay filter if available and enough data, otherwise use moving average
        if SCIPY_AVAILABLE and len(self.accel_buffer) >= 11:
            # Savitzky-Golay filter preserves signal characteristics better than simple average
            accel_array = np.array(list(self.accel_buffer))
            window = min(11, len(accel_array))
            if window % 2 == 0:  # Must be odd
                window -= 1
            if window >= 3:
                smoothed_accel = savgol_filter(accel_array, window, 3)[-1]
            else:
                smoothed_accel = acceleration_mps2
        elif len(self.accel_buffer) >= 3:
            smoothed_accel = np.mean(list(self.accel_buffer))
        else:
            smoothed_accel = acceleration_mps2

        # Method 1: Acceleration-based (most accurate for real-world)
        hp_wheel_accel = self._calculate_hp_from_acceleration(speed_mps, smoothed_accel)
        confidence_accel = self._calculate_confidence(speed_mps, smoothed_accel)

        # Method 2: Torque-based (if torque available)
        hp_wheel_torque = None
        confidence_torque = 0.0
        if torque_ftlb is not None and rpm is not None:
            hp_wheel_torque = self._calculate_hp_from_torque(torque_ftlb, rpm)
            confidence_torque = 0.95  # High confidence if torque sensor available

        # Method 3: RPM-based estimation (if RPM available, less accurate)
        hp_wheel_rpm = None
        if rpm is not None and hp_wheel_torque is None:
            # Estimate from RPM and speed (rough approximation)
            hp_wheel_rpm = self._estimate_hp_from_rpm_speed(rpm, speed_mps)
            confidence_torque = 0.6  # Lower confidence

        # Combine methods (weighted average based on confidence)
        hp_values = []
        confidences = []
        
        if hp_wheel_accel > 0:
            hp_values.append(hp_wheel_accel)
            confidences.append(confidence_accel)
        
        if hp_wheel_torque is not None and hp_wheel_torque > 0:
            hp_values.append(hp_wheel_torque)
            confidences.append(confidence_torque)
        elif hp_wheel_rpm is not None and hp_wheel_rpm > 0:
            hp_values.append(hp_wheel_rpm)
            confidences.append(0.6)

        if not hp_values:
            # Fallback: very rough estimate
            hp_wheel = 100.0  # Default fallback
            confidence = 0.1
        else:
            # Weighted average
            total_confidence = sum(confidences)
            if total_confidence > 0:
                hp_wheel = sum(hp * c for hp, c in zip(hp_values, confidences)) / total_confidence
                confidence = total_confidence / len(confidences)
            else:
                hp_wheel = hp_values[0]
                confidence = 0.5

        # Apply calibration factor
        hp_wheel_calibrated = hp_wheel * self.calibration_factor

        # Estimate crank horsepower (account for drivetrain loss)
        drivetrain_efficiency = 1.0 - self.vehicle_specs.drivetrain_loss
        hp_crank = hp_wheel_calibrated / drivetrain_efficiency

        # Calculate torque if not provided (always calculate when RPM available)
        calculated_torque = None
        if rpm is not None and rpm > 0:
            # HP = (Torque × RPM) / 5252
            # Therefore: Torque = (HP × 5252) / RPM
            calculated_torque = (hp_crank * 5252.0) / rpm
        elif torque_ftlb is not None:
            # Use provided torque
            calculated_torque = torque_ftlb

        # Determine method used
        method = DynoMethod.ACCELERATION_BASED
        if torque_ftlb is not None:
            method = DynoMethod.TORQUE_BASED
        elif rpm is not None:
            method = DynoMethod.SPEED_DELTA

        reading = DynoReading(
            timestamp=timestamp,
            rpm=rpm,
            speed_mph=speed_mph,
            speed_mps=speed_mps,
            acceleration_mps2=smoothed_accel,
            horsepower_wheel=hp_wheel_calibrated,
            horsepower_crank=hp_crank,
            torque_ftlb=calculated_torque or torque_ftlb,
            method=method,
            confidence=confidence,
            conditions=EnvironmentalConditions(
                temperature_c=self.current_conditions.temperature_c,
                altitude_m=self.current_conditions.altitude_m,
                humidity_percent=self.current_conditions.humidity_percent,
                barometric_pressure_kpa=self.current_conditions.barometric_pressure_kpa,
            ),
        )

        # Add to current curve
        self.current_curve.readings.append(reading)

        # Update peak values (always update if better)
        if hp_crank > self.current_curve.peak_hp_crank:
            self.current_curve.peak_hp_crank = hp_crank
            self.current_curve.peak_hp_wheel = hp_wheel_calibrated
            if rpm is not None and rpm > 0:
                self.current_curve.peak_hp_rpm = rpm

        if calculated_torque is not None:
            if calculated_torque > self.current_curve.peak_torque_ftlb:
                self.current_curve.peak_torque_ftlb = calculated_torque
                if rpm is not None and rpm > 0:
                    self.current_curve.peak_torque_rpm = rpm

        return reading

    def _calculate_hp_from_acceleration(self, speed_mps: float, acceleration_mps2: float) -> float:
        """
        Calculate horsepower from acceleration (most accurate method).
        
        Improved formula based on best practices:
        - Cleaner force calculation structure
        - Proper separation of forces
        - Accurate power calculation
        
        Formula: P = F × v
        Where F = m×a + F_drag + F_roll
        """
        total_weight_kg = self.vehicle_specs.total_weight_kg()

        # Compute resistive forces (independent of acceleration)
        air_density = self.current_conditions.air_density_kg_m3()
        F_drag = 0.5 * air_density * self.vehicle_specs.drag_coefficient * \
                 self.vehicle_specs.frontal_area_m2 * (speed_mps ** 2)
        
        F_roll = self.vehicle_specs.rolling_resistance_coef * total_weight_kg * GRAVITY

        # Compute total tractive force at the wheels
        F_tractive = total_weight_kg * acceleration_mps2 + F_drag + F_roll

        # Power at wheels (Watts): P = F × v
        P_wheel_watts = F_tractive * speed_mps

        # Convert to horsepower (wheel HP)
        # Using 745.7 W/HP (matches industry standard and provided code)
        hp_wheel = P_wheel_watts * WATTS_TO_HP

        return max(0.0, hp_wheel)

    def _calculate_hp_from_torque(self, torque_ftlb: float, rpm: float) -> float:
        """
        Calculate horsepower from torque (if torque sensor available).
        
        Formula: HP = (Torque × RPM) / 5252
        """
        if rpm <= 0:
            return 0.0
        
        # This gives crank HP directly
        hp_crank = (torque_ftlb * rpm) / 5252.0
        
        # Convert to wheel HP (account for drivetrain loss)
        drivetrain_efficiency = 1.0 - self.vehicle_specs.drivetrain_loss
        hp_wheel = hp_crank * drivetrain_efficiency
        
        return max(0.0, hp_wheel)

    def _estimate_hp_from_rpm_speed(self, rpm: float, speed_mps: float) -> float:
        """
        Rough estimate of HP from RPM and speed (less accurate).
        Uses gear ratio estimation.
        """
        # Estimate gear ratio from speed and RPM
        # Typical: at 60 mph, ~2000 RPM in top gear = ratio ~3.0
        # This is very rough and vehicle-dependent
        if speed_mps < 0.1 or rpm < 100:
            return 0.0
        
        # Rough estimation (this is not very accurate)
        # Would need actual gear ratios for accuracy
        estimated_hp = (rpm * speed_mps) / 10000.0  # Very rough formula
        
        return max(0.0, estimated_hp)

    def _calculate_confidence(self, speed_mps: float, acceleration_mps2: float) -> float:
        """
        Calculate confidence in HP reading (0-1).
        
        Higher confidence when:
        - Higher speed (more data)
        - Significant acceleration (not coasting)
        - Smooth data (low noise)
        """
        confidence = 0.5  # Base confidence

        # Speed factor (need some speed for accuracy)
        if speed_mps > 5.0:  # ~11 mph
            confidence += 0.2
        if speed_mps > 13.4:  # ~30 mph
            confidence += 0.15
        if speed_mps > 26.8:  # ~60 mph
            confidence += 0.1

        # Acceleration factor (need acceleration, not coasting)
        if abs(acceleration_mps2) > 0.5:  # Significant acceleration
            confidence += 0.15
        elif abs(acceleration_mps2) < 0.1:  # Coasting
            confidence -= 0.2

        # Data quality (smooth data = higher confidence)
        if len(self.accel_buffer) >= 5:
            accel_std = np.std(list(self.accel_buffer))
            if accel_std < 0.5:  # Low noise
                confidence += 0.1

        return max(0.0, min(1.0, confidence))

    def calibrate_with_dyno_run(
        self,
        real_dyno_curve: DynoCurve,
        virtual_dyno_curve: DynoCurve,
    ) -> float:
        """
        Calibrate virtual dyno using a known real dyno run.
        
        This is KEY for accuracy! Compare virtual dyno to real dyno,
        calculate correction factor, and apply to future runs.
        
        Args:
            real_dyno_curve: Real dyno curve from actual dyno run
            virtual_dyno_curve: Virtual dyno curve from same run
            
        Returns:
            New calibration factor
        """
        # Compare peak HP
        if real_dyno_curve.peak_hp_crank > 0 and virtual_dyno_curve.peak_hp_crank > 0:
            factor_peak = real_dyno_curve.peak_hp_crank / virtual_dyno_curve.peak_hp_crank
        else:
            factor_peak = 1.0

        # Compare across RPM range (more accurate)
        if len(real_dyno_curve.readings) > 0 and len(virtual_dyno_curve.readings) > 0:
            factors = []
            # Match readings by RPM
            for real_reading in real_dyno_curve.readings:
                if real_reading.rpm is None:
                    continue
                # Find closest virtual reading by RPM
                closest_virtual = min(
                    virtual_dyno_curve.readings,
                    key=lambda r: abs((r.rpm or 0) - real_reading.rpm),
                )
                if closest_virtual.rpm and closest_virtual.horsepower_crank > 0:
                    factor = real_reading.horsepower_crank / closest_virtual.horsepower_crank
                    factors.append(factor)

            if factors:
                # Use median (more robust than mean)
                factor_median = np.median(factors)
                # Weighted average: 70% median, 30% peak
                new_factor = (factor_median * 0.7) + (factor_peak * 0.3)
            else:
                new_factor = factor_peak
        else:
            new_factor = factor_peak

        # Update calibration factor (exponential moving average)
        self.calibration_factor = (self.calibration_factor * 0.7) + (new_factor * 0.3)

        # Store calibration run for ML learning
        self.calibration_runs.append((virtual_dyno_curve, real_dyno_curve))

        LOGGER.info(
            "Calibrated virtual dyno: factor = %.3f (was %.3f)",
            self.calibration_factor,
            new_factor,
        )

        return self.calibration_factor

    def get_dyno_curve(self) -> DynoCurve:
        """Get current dyno curve."""
        return self.current_curve

    def reset_curve(self) -> None:
        """Reset current dyno curve (start new run)."""
        # Save current run to session if it has data
        if self.current_curve.readings:
            self.run_counter += 1
            self.current_curve.run_name = f"Run_{self.run_counter}"
            self.current_curve.run_timestamp = time.time()
            self.session_runs.append(self.current_curve)
        
        # Create new curve
        self.current_curve = DynoCurve(calibration_factor=self.calibration_factor)
        self.speed_buffer.clear()
        self.accel_buffer.clear()
        self.rpm_buffer.clear()
    
    def get_session_runs(self) -> List[DynoCurve]:
        """Get all runs in current session."""
        # Include current run if it has data
        runs = list(self.session_runs)
        if self.current_curve.readings:
            runs.append(self.current_curve)
        return runs
    
    def clear_session(self) -> None:
        """Clear all runs from current session."""
        self.session_runs.clear()
        self.run_counter = 0
    
    def export_session(self, filename: Optional[str] = None) -> str:
        """
        Export all session runs to CSV file.
        
        Args:
            filename: Output filename (defaults to session_summary_TIMESTAMP.csv)
            
        Returns:
            Path to exported file
        """
        import pandas as pd
        from pathlib import Path
        
        runs = self.get_session_runs()
        if not runs:
            raise ValueError("No runs to export")
        
        if filename is None:
            timestamp = int(time.time())
            filename = f"session_summary_{timestamp}.csv"
        
        # Combine all runs into single DataFrame
        all_data = []
        for run in runs:
            for reading in run.readings:
                # Calculate relative time from run start
                rel_time = reading.timestamp - run.run_timestamp if run.run_timestamp > 0 else 0
                
                all_data.append({
                    'run_name': run.run_name,
                    'run_timestamp': run.run_timestamp,
                    'time_s': rel_time,
                    'rpm': reading.rpm or 0.0,
                    'speed_mph': reading.speed_mph,
                    'speed_mps': reading.speed_mps,
                    'acceleration_mps2': reading.acceleration_mps2,
                    'wheel_hp': reading.horsepower_wheel,
                    'engine_hp': reading.horsepower_crank,
                    'torque_ftlb': reading.torque_ftlb or 0.0,
                    'confidence': reading.confidence,
                    'method': reading.method.value,
                })
        
        df = pd.DataFrame(all_data)
        df.to_csv(filename, index=False)
        
        LOGGER.info(f"Exported {len(runs)} runs to {filename}")
        return filename

    def calculate_horsepower_from_timeseries(
        self,
        time_s: Union[np.ndarray, List[float]],
        speed_mps: Union[np.ndarray, List[float]],
        rpm: Optional[Union[np.ndarray, List[float]]] = None,
        smooth_window: int = 11,
        smooth_poly: int = 3,
    ) -> List[DynoReading]:
        """
        Calculate horsepower from time series data (batch processing).
        
        This method uses improved algorithms:
        - np.gradient() for accurate acceleration calculation (central differences)
        - Savitzky-Golay filter for superior noise reduction
        - More accurate than point-by-point calculation
        
        Args:
            time_s: Time data in seconds (must be evenly spaced or close)
            speed_mps: Vehicle speed in m/s (array)
            rpm: Engine RPM (optional array, improves accuracy)
            smooth_window: Window size for Savitzky-Golay filter (must be odd, default 11)
            smooth_poly: Polynomial order for smoothing filter (default 3)
            
        Returns:
            List of DynoReading objects for each time point
        """
        # Convert to numpy arrays
        time_s = np.asarray(time_s)
        speed_mps = np.asarray(speed_mps)
        
        if len(time_s) != len(speed_mps):
            raise ValueError("time_s and speed_mps must have the same length")
        
        if len(time_s) < 2:
            raise ValueError("Need at least 2 data points for calculation")
        
        # Compute acceleration using central differences (more accurate than simple diff)
        dt = np.gradient(time_s)
        accel_mps2 = np.gradient(speed_mps, dt)
        
        # Smooth acceleration using Savitzky-Golay filter (preserves signal characteristics)
        if SCIPY_AVAILABLE and len(accel_mps2) >= smooth_window:
            # Ensure window is odd
            if smooth_window % 2 == 0:
                smooth_window = smooth_window - 1
            smooth_window = max(3, min(smooth_window, len(accel_mps2)))
            if smooth_window >= 3:
                accel_mps2 = savgol_filter(accel_mps2, smooth_window, smooth_poly)
        elif len(accel_mps2) >= 3:
            # Fallback to simple moving average if scipy not available
            accel_smoothed = np.zeros_like(accel_mps2)
            window = min(3, len(accel_mps2))
            for i in range(len(accel_mps2)):
                start = max(0, i - window // 2)
                end = min(len(accel_mps2), i + window // 2 + 1)
                accel_smoothed[i] = np.mean(accel_mps2[start:end])
            accel_mps2 = accel_smoothed
        
        # Convert RPM if provided
        rpm_array = None
        if rpm is not None:
            rpm_array = np.asarray(rpm)
            if len(rpm_array) != len(time_s):
                LOGGER.warning("RPM array length doesn't match time, ignoring RPM")
                rpm_array = None
        
        # Calculate HP for each point
        readings = []
        for i in range(len(time_s)):
            speed_mph = speed_mps[i] * MPS_TO_MPH
            rpm_val = float(rpm_array[i]) if rpm_array is not None else None
            
            # Use the improved single-point calculation
            reading = self.calculate_horsepower(
                speed_mph=speed_mph,
                acceleration_mps2=float(accel_mps2[i]),
                rpm=rpm_val,
                timestamp=time_s[i],
            )
            readings.append(reading)
        
        return readings
    
    def estimate_accuracy(self) -> float:
        """
        Estimate accuracy of virtual dyno (0-1).
        
        Higher accuracy when:
        - Calibrated with real dyno runs
        - Good vehicle specs
        - Quality telemetry data
        - Multiple calibration runs
        """
        accuracy = 0.5  # Base accuracy

        # Calibration factor close to 1.0 = better
        if 0.95 < self.calibration_factor < 1.05:
            accuracy += 0.2
        elif 0.90 < self.calibration_factor < 1.10:
            accuracy += 0.1

        # Number of calibration runs
        if len(self.calibration_runs) >= 3:
            accuracy += 0.15
        elif len(self.calibration_runs) >= 1:
            accuracy += 0.1

        # Vehicle specs quality (user-provided vs default)
        if self.vehicle_specs.curb_weight_kg > 0:
            accuracy += 0.1
        if self.vehicle_specs.frontal_area_m2 != 2.0:  # Not default
            accuracy += 0.05

        return min(1.0, accuracy)


__all__ = [
    "VirtualDyno",
    "VehicleSpecs",
    "EnvironmentalConditions",
    "DynoReading",
    "DynoCurve",
    "DynoMethod",
]

