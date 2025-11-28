"""
Dyno Enhancements - Advanced Features for Virtual Dyno

This module adds the missing features:
- Adjustable smoothing (1-10 scale)
- DIN 70020 correction (in addition to SAE J1349)
- Delta comparisons (percentage gains at RPM ranges)
- Shift point calculations
- 5,252 RPM crossing verification
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    from scipy.signal import savgol_filter
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

from services.virtual_dyno import DynoCurve, DynoReading, EnvironmentalConditions

LOGGER = logging.getLogger(__name__)


class CorrectionStandard(Enum):
    """Correction standards for dyno results."""
    NONE = "none"
    SAE_J1349 = "sae_j1349"  # SAE J1349 (US standard)
    DIN_70020 = "din_70020"  # DIN 70020 (European standard)
    ECE_R24 = "ece_r24"  # ECE R24 (European alternative)


@dataclass
class SmoothingConfig:
    """Configuration for data smoothing."""
    level: int  # 1-10 scale
    window_size: int  # Calculated window size
    polynomial_order: int  # Polynomial order for Savitzky-Golay


def calculate_smoothing_config(level: int) -> SmoothingConfig:
    """
    Calculate smoothing configuration from 1-10 scale.
    
    Level 1: Raw data (no smoothing)
    Level 3-6: Recommended (balanced)
    Level 10: Maximum smoothing
    
    Args:
        level: Smoothing level (1-10)
        
    Returns:
        SmoothingConfig with calculated parameters
    """
    level = max(1, min(10, level))
    
    if level == 1:
        # Raw data - no smoothing
        return SmoothingConfig(level=1, window_size=1, polynomial_order=1)
    elif level <= 3:
        # Light smoothing
        window_size = 5 + (level - 1) * 2  # 5, 7, 9
        return SmoothingConfig(level=level, window_size=window_size, polynomial_order=2)
    elif level <= 6:
        # Medium smoothing (recommended)
        window_size = 11 + (level - 3) * 4  # 11, 15, 19, 23
        return SmoothingConfig(level=level, window_size=window_size, polynomial_order=3)
    else:
        # Heavy smoothing
        window_size = 27 + (level - 6) * 6  # 27, 33, 39, 45
        return SmoothingConfig(level=level, window_size=window_size, polynomial_order=3)


def apply_smoothing(
    data: np.ndarray,
    smoothing_level: int = 5,
    ensure_odd: bool = True
) -> np.ndarray:
    """
    Apply smoothing to data based on 1-10 scale.
    
    Args:
        data: Data array to smooth
        smoothing_level: Smoothing level (1-10)
        ensure_odd: Ensure window size is odd (required for Savitzky-Golay)
        
    Returns:
        Smoothed data array
    """
    if smoothing_level == 1 or len(data) < 3:
        return data
    
    config = calculate_smoothing_config(smoothing_level)
    
    # Ensure window size is odd and within bounds
    window_size = config.window_size
    if ensure_odd and window_size % 2 == 0:
        window_size += 1
    
    window_size = max(3, min(window_size, len(data)))
    if window_size >= len(data):
        window_size = len(data) - 1 if len(data) > 1 else 1
        if ensure_odd and window_size % 2 == 0:
            window_size -= 1
    
    if window_size < 3:
        return data
    
    # Apply Savitzky-Golay filter if available
    if SCIPY_AVAILABLE and window_size >= 3:
        try:
            poly_order = min(config.polynomial_order, window_size - 1)
            return savgol_filter(data, window_size, poly_order)
        except Exception as e:
            LOGGER.warning(f"Savitzky-Golay filter failed: {e}, using moving average")
    
    # Fallback to moving average
    smoothed = np.zeros_like(data)
    half_window = window_size // 2
    
    for i in range(len(data)):
        start = max(0, i - half_window)
        end = min(len(data), i + half_window + 1)
        smoothed[i] = np.mean(data[start:end])
    
    return smoothed


def calculate_din_70020_correction(
    conditions: EnvironmentalConditions
) -> float:
    """
    Calculate DIN 70020 correction factor.
    
    DIN 70020 standardizes to:
    - 20°C temperature
    - 1013.25 mbar (101.325 kPa) barometric pressure
    - 0% humidity (dry air)
    
    Formula: CF = (P_std / P_actual) × sqrt(T_actual / T_std)
    Where P is in mbar, T is in Kelvin
    
    Args:
        conditions: Environmental conditions
        
    Returns:
        Correction factor
    """
    # Standard conditions (DIN 70020)
    T_std = 20.0 + 273.15  # 293.15 K
    P_std = 1013.25  # mbar
    
    # Current conditions
    T_actual = conditions.temperature_c + 273.15
    P_actual = conditions.barometric_pressure_kpa * 10.0  # Convert kPa to mbar
    
    # Calculate dry air pressure
    humidity_ratio = conditions.humidity_percent / 100.0
    saturation_pressure_pa = 6.1078 * (10 ** ((7.5 * conditions.temperature_c) / (conditions.temperature_c + 237.3))) * 100
    vapor_pressure_pa = humidity_ratio * saturation_pressure_pa
    dry_air_pressure_pa = (P_actual * 100) - vapor_pressure_pa  # Convert mbar to Pa
    dry_air_pressure_mbar = dry_air_pressure_pa / 100.0
    
    # DIN 70020 correction factor
    if dry_air_pressure_mbar > 0:
        pressure_ratio = P_std / dry_air_pressure_mbar
        temp_ratio = math.sqrt(T_actual / T_std)
        return pressure_ratio * temp_ratio
    
    return 1.0


@dataclass
class DeltaComparison:
    """Delta comparison between two dyno runs."""
    rpm: float
    hp_delta: float  # HP difference (run2 - run1)
    hp_percent_change: float  # Percentage change
    torque_delta: float  # Torque difference
    torque_percent_change: float  # Percentage change


@dataclass
class DynoDeltaAnalysis:
    """Comprehensive delta analysis between two dyno runs."""
    run1_name: str
    run2_name: str
    peak_hp_delta: float
    peak_hp_percent_change: float
    peak_torque_delta: float
    peak_torque_percent_change: float
    rpm_deltas: List[DeltaComparison]
    average_hp_gain: float
    average_torque_gain: float
    best_rpm_range: Optional[Tuple[float, float]]  # RPM range with best gains


def calculate_delta_comparison(
    run1: DynoCurve,
    run2: DynoCurve,
    run1_name: str = "Run 1",
    run2_name: str = "Run 2",
    rpm_points: Optional[List[float]] = None
) -> DynoDeltaAnalysis:
    """
    Calculate delta comparison between two dyno runs.
    
    Shows percentage gains at specific RPM ranges, which is more valuable
    than just peak numbers for tuning analysis.
    
    Args:
        run1: First dyno curve (baseline)
        run2: Second dyno curve (modified)
        run1_name: Name for first run
        run2_name: Name for second run
        rpm_points: Specific RPM points to compare (default: 500 RPM intervals)
        
    Returns:
        DynoDeltaAnalysis with comprehensive comparison
    """
    # Default RPM points if not provided
    if rpm_points is None:
        rpm_points = list(range(2000, 8000, 500))
    
    # Helper function to get HP/Torque at specific RPM
    def get_values_at_rpm(curve: DynoCurve, rpm: float) -> Tuple[float, float]:
        """Get HP and Torque at specific RPM using interpolation."""
        readings_with_rpm = [
            r for r in curve.readings
            if r.rpm is not None and r.rpm > 0
        ]
        if not readings_with_rpm:
            return 0.0, 0.0
        
        sorted_readings = sorted(readings_with_rpm, key=lambda x: x.rpm or 0)
        rpms = [r.rpm for r in sorted_readings if r.rpm]
        
        if not rpms:
            return 0.0, 0.0
        
        # Find closest readings
        if rpm <= rpms[0]:
            reading = sorted_readings[0]
            return reading.horsepower_crank, reading.torque_ftlb or 0.0
        elif rpm >= rpms[-1]:
            reading = sorted_readings[-1]
            return reading.horsepower_crank, reading.torque_ftlb or 0.0
        
        # Interpolate
        for i in range(len(rpms) - 1):
            if rpms[i] <= rpm <= rpms[i + 1]:
                r1 = sorted_readings[i]
                r2 = sorted_readings[i + 1]
                if r1.rpm and r2.rpm:
                    t = (rpm - r1.rpm) / (r2.rpm - r1.rpm)
                    hp = r1.horsepower_crank + t * (r2.horsepower_crank - r1.horsepower_crank)
                    tq1 = r1.torque_ftlb or 0.0
                    tq2 = r2.torque_ftlb or 0.0
                    torque = tq1 + t * (tq2 - tq1)
                    return hp, torque
        
        return 0.0, 0.0
    
    # Calculate deltas at each RPM point
    rpm_deltas = []
    hp_gains = []
    torque_gains = []
    
    for rpm in rpm_points:
        hp1, tq1 = get_values_at_rpm(run1, rpm)
        hp2, tq2 = get_values_at_rpm(run2, rpm)
        
        hp_delta = hp2 - hp1
        tq_delta = tq2 - tq1
        
        hp_percent = (hp_delta / hp1 * 100) if hp1 > 0 else 0.0
        tq_percent = (tq_delta / tq1 * 100) if tq1 > 0 else 0.0
        
        rpm_deltas.append(DeltaComparison(
            rpm=rpm,
            hp_delta=hp_delta,
            hp_percent_change=hp_percent,
            torque_delta=tq_delta,
            torque_percent_change=tq_percent,
        ))
        
        if hp_delta > 0:
            hp_gains.append(hp_delta)
        if tq_delta > 0:
            torque_gains.append(tq_delta)
    
    # Peak deltas
    peak_hp_delta = run2.peak_hp_crank - run1.peak_hp_crank
    peak_hp_percent = (peak_hp_delta / run1.peak_hp_crank * 100) if run1.peak_hp_crank > 0 else 0.0
    
    peak_torque_delta = run2.peak_torque_ftlb - run1.peak_torque_ftlb
    peak_torque_percent = (peak_torque_delta / run1.peak_torque_ftlb * 100) if run1.peak_torque_ftlb > 0 else 0.0
    
    # Average gains
    avg_hp_gain = np.mean(hp_gains) if hp_gains else 0.0
    avg_torque_gain = np.mean(torque_gains) if torque_gains else 0.0
    
    # Find best RPM range (where gains are highest)
    best_range = None
    if rpm_deltas:
        max_gain = max(d.hp_percent_change for d in rpm_deltas)
        if max_gain > 0:
            best_delta = next(d for d in rpm_deltas if d.hp_percent_change == max_gain)
            # Find range around best point (±500 RPM)
            best_rpm = best_delta.rpm
            best_range = (max(2000, best_rpm - 500), min(8000, best_rpm + 500))
    
    return DynoDeltaAnalysis(
        run1_name=run1_name,
        run2_name=run2_name,
        peak_hp_delta=peak_hp_delta,
        peak_hp_percent_change=peak_hp_percent,
        peak_torque_delta=peak_torque_delta,
        peak_torque_percent_change=peak_torque_percent,
        rpm_deltas=rpm_deltas,
        average_hp_gain=avg_hp_gain,
        average_torque_gain=avg_torque_gain,
        best_rpm_range=best_range,
    )


@dataclass
class ShiftPoint:
    """Optimal shift point recommendation."""
    from_gear: int
    to_gear: int
    shift_rpm: float
    reason: str
    power_loss_if_shift_early: float  # HP lost if shifting too early
    power_loss_if_shift_late: float  # HP lost if shifting too late


def calculate_optimal_shift_points(
    curve: DynoCurve,
    gear_ratios: List[float],
    final_drive_ratio: float = 3.5,
    redline_rpm: float = 7000.0
) -> List[ShiftPoint]:
    """
    Calculate optimal shift points based on torque curve and gear ratios.
    
    Ensures the car stays in its peak power band during acceleration.
    
    Args:
        curve: Dyno curve with torque data
        gear_ratios: List of gear ratios [1st, 2nd, 3rd, ...]
        final_drive_ratio: Final drive ratio
        redline_rpm: Redline RPM (maximum safe RPM)
        
    Returns:
        List of optimal shift points for each gear transition
    """
    if not curve.readings or not gear_ratios:
        return []
    
    # Get torque curve data
    readings_with_rpm = [
        r for r in curve.readings
        if r.rpm is not None and r.rpm > 0 and r.torque_ftlb is not None
    ]
    if not readings_with_rpm:
        return []
    
    sorted_readings = sorted(readings_with_rpm, key=lambda x: x.rpm or 0)
    rpms = [r.rpm for r in sorted_readings if r.rpm]
    torques = [r.torque_ftlb for r in sorted_readings if r.torque_ftlb]
    
    if len(rpms) < 2:
        return []
    
    shift_points = []
    
    # For each gear transition
    for gear_idx in range(len(gear_ratios) - 1):
        current_gear = gear_idx + 1
        next_gear = gear_idx + 2
        
        current_ratio = gear_ratios[gear_idx] * final_drive_ratio
        next_ratio = gear_ratios[gear_idx + 1] * final_drive_ratio
        
        # Calculate RPM after shift (RPM drops when shifting up)
        # After shift RPM = Current RPM × (next_gear_ratio / current_gear_ratio)
        rpm_ratio = next_ratio / current_ratio
        
        # Find optimal shift point
        # We want to shift when the torque in the next gear (at lower RPM)
        # equals or exceeds the torque in current gear
        best_shift_rpm = redline_rpm
        best_reason = "Redline"
        
        # Check RPM range from peak torque to redline
        peak_torque_rpm = curve.peak_torque_rpm if curve.peak_torque_rpm > 0 else 3000.0
        check_rpms = np.linspace(peak_torque_rpm, redline_rpm, 50)
        
        for test_rpm in check_rpms:
            if test_rpm > redline_rpm:
                break
            
            # Get torque at current RPM in current gear
            current_torque = np.interp(test_rpm, rpms, torques)
            
            # Calculate RPM after shift
            after_shift_rpm = test_rpm * rpm_ratio
            
            if after_shift_rpm < rpms[0]:
                continue
            
            # Get torque at after-shift RPM in next gear
            after_shift_torque = np.interp(after_shift_rpm, rpms, torques)
            
            # Calculate effective torque (accounting for gear ratio)
            # Effective torque = torque × gear_ratio
            current_effective = current_torque * current_ratio
            next_effective = after_shift_torque * next_ratio
            
            # If next gear provides more effective torque, this is a good shift point
            if next_effective >= current_effective * 0.95:  # 95% threshold
                best_shift_rpm = test_rpm
                best_reason = f"Next gear torque matches (effective: {next_effective:.0f} vs {current_effective:.0f})"
                break
        
        # Calculate power loss if shifting early/late
        early_loss = 0.0
        late_loss = 0.0
        
        if best_shift_rpm < redline_rpm:
            # Loss if shifting early (at peak torque instead of optimal)
            peak_tq = np.interp(curve.peak_torque_rpm, rpms, torques)
            optimal_tq = np.interp(best_shift_rpm, rpms, torques)
            early_loss = (peak_tq - optimal_tq) * current_ratio if peak_tq > optimal_tq else 0.0
        
        if best_shift_rpm < redline_rpm:
            # Loss if shifting late (past optimal point)
            redline_tq = np.interp(redline_rpm, rpms, torques)
            optimal_tq = np.interp(best_shift_rpm, rpms, torques)
            late_loss = (optimal_tq - redline_tq) * current_ratio if optimal_tq > redline_tq else 0.0
        
        shift_points.append(ShiftPoint(
            from_gear=current_gear,
            to_gear=next_gear,
            shift_rpm=best_shift_rpm,
            reason=best_reason,
            power_loss_if_shift_early=early_loss,
            power_loss_if_shift_late=late_loss,
        ))
    
    return shift_points


def verify_5252_crossing(curve: DynoCurve) -> Tuple[bool, Optional[float], Optional[float]]:
    """
    Verify that HP and Torque curves cross at 5,252 RPM.
    
    This is a fundamental physics requirement: HP = (Torque × RPM) / 5252
    Therefore, HP and Torque must be equal at exactly 5,252 RPM.
    
    Args:
        curve: Dyno curve to verify
        
    Returns:
        Tuple of (crosses_at_5252, hp_at_5252, torque_at_5252)
    """
    readings_with_rpm = [
        r for r in curve.readings
        if r.rpm is not None and r.rpm > 0
        and r.torque_ftlb is not None
    ]
    
    if not readings_with_rpm:
        return False, None, None
    
    sorted_readings = sorted(readings_with_rpm, key=lambda x: x.rpm or 0)
    rpms = [r.rpm for r in sorted_readings if r.rpm]
    hp_values = [r.horsepower_crank for r in sorted_readings]
    torque_values = [r.torque_ftlb for r in sorted_readings if r.torque_ftlb]
    
    if not rpms or 5252 < rpms[0] or 5252 > rpms[-1]:
        return False, None, None
    
    # Interpolate HP and Torque at 5252 RPM
    hp_at_5252 = np.interp(5252.0, rpms, hp_values)
    torque_at_5252 = np.interp(5252.0, rpms, torque_values)
    
    # Check if they're close (within 1% tolerance)
    difference = abs(hp_at_5252 - torque_at_5252)
    tolerance = max(hp_at_5252, torque_at_5252) * 0.01
    
    crosses = difference <= tolerance
    
    if not crosses:
        LOGGER.warning(
            f"HP and Torque do not cross at 5,252 RPM: "
            f"HP={hp_at_5252:.1f}, Torque={torque_at_5252:.1f}, "
            f"Difference={difference:.1f}"
        )
    
    return crosses, hp_at_5252, torque_at_5252


__all__ = [
    "CorrectionStandard",
    "SmoothingConfig",
    "calculate_smoothing_config",
    "apply_smoothing",
    "calculate_din_70020_correction",
    "DeltaComparison",
    "DynoDeltaAnalysis",
    "calculate_delta_comparison",
    "ShiftPoint",
    "calculate_optimal_shift_points",
    "verify_5252_crossing",
]

