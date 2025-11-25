"""
Dyno Analyzer - Advanced Analysis and Comparison Tools

Advanced features for dyno data analysis:
- Before/after mod comparisons
- Power band analysis
- Weather correction (SAE standard)
- Mod impact analysis
- Predictive power modeling
- Historical tracking
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from services.virtual_dyno import DynoCurve, DynoReading

LOGGER = logging.getLogger(__name__)


class WeatherStandard(Enum):
    """Weather correction standards."""

    SAE_J1349 = "sae_j1349"  # SAE standard (most common)
    SAE_J607 = "sae_j607"  # Older SAE standard
    DIN = "din"  # German standard
    ECE = "ece"  # European standard
    NONE = "none"  # No correction


@dataclass
class ModImpact:
    """Impact of a modification on power."""

    mod_name: str
    before_hp: float
    after_hp: float
    hp_gain: float
    before_torque: float
    after_torque: float
    torque_gain: float
    peak_hp_rpm_before: float
    peak_hp_rpm_after: float
    cost_per_hp: Optional[float] = None  # Cost of mod / HP gained
    efficiency_score: float = 0.0  # 0-1, how efficient the mod is


@dataclass
class PowerBandAnalysis:
    """Analysis of power band characteristics."""

    peak_hp: float
    peak_hp_rpm: float
    peak_torque: float
    peak_torque_rpm: float
    power_band_width_rpm: float  # RPM range where power is >90% of peak
    torque_band_width_rpm: float  # RPM range where torque is >90% of peak
    area_under_curve: float  # Total area under HP curve (power delivery)
    flatness_score: float  # 0-1, how flat the power curve is
    responsiveness_score: float  # 0-1, how responsive (low-end torque)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class DynoComparison:
    """Comparison between two dyno runs."""

    run1_name: str
    run2_name: str
    run1_curve: DynoCurve
    run2_curve: DynoCurve
    hp_difference: float
    torque_difference: float
    rpm_differences: Dict[float, float]  # RPM -> HP difference
    improvement_percent: float
    mod_impact: Optional[ModImpact] = None


class DynoAnalyzer:
    """
    Advanced dyno analysis and comparison tools.
    
    Features:
    - Before/after mod comparisons
    - Power band analysis
    - Weather correction (SAE standard)
    - Mod impact analysis
    - Predictive power modeling
    - Historical tracking
    """

    def __init__(self) -> None:
        """Initialize dyno analyzer."""
        self.historical_runs: List[Tuple[str, DynoCurve]] = []  # (name, curve)
        self.mod_history: List[ModImpact] = []

    def compare_runs(
        self,
        run1_name: str,
        run1_curve: DynoCurve,
        run2_name: str,
        run2_curve: DynoCurve,
    ) -> DynoComparison:
        """
        Compare two dyno runs (e.g., before/after mods).
        
        Args:
            run1_name: Name of first run (e.g., "Stock")
            run1_curve: First dyno curve
            run2_name: Name of second run (e.g., "After Tune")
            run2_curve: Second dyno curve
            
        Returns:
            Detailed comparison
        """
        hp_diff = run2_curve.peak_hp_crank - run1_curve.peak_hp_crank
        torque_diff = run2_curve.peak_torque_ftlb - run1_curve.peak_torque_ftlb
        
        improvement = (hp_diff / run1_curve.peak_hp_crank * 100) if run1_curve.peak_hp_crank > 0 else 0.0
        
        # Compare at different RPM points
        rpm_diffs = {}
        for rpm in [2000, 3000, 4000, 5000, 6000, 7000]:
            hp1 = self._get_hp_at_rpm(run1_curve, rpm)
            hp2 = self._get_hp_at_rpm(run2_curve, rpm)
            if hp1 > 0 and hp2 > 0:
                rpm_diffs[rpm] = hp2 - hp1
        
        # Calculate mod impact if applicable
        mod_impact = None
        if "stock" in run1_name.lower() or "before" in run1_name.lower():
            mod_impact = ModImpact(
                mod_name=run2_name,
                before_hp=run1_curve.peak_hp_crank,
                after_hp=run2_curve.peak_hp_crank,
                hp_gain=hp_diff,
                before_torque=run1_curve.peak_torque_ftlb,
                after_torque=run2_curve.peak_torque_ftlb,
                torque_gain=torque_diff,
                peak_hp_rpm_before=run1_curve.peak_hp_rpm,
                peak_hp_rpm_after=run2_curve.peak_hp_rpm,
            )
            self.mod_history.append(mod_impact)
        
        return DynoComparison(
            run1_name=run1_name,
            run2_name=run2_name,
            run1_curve=run1_curve,
            run2_curve=run2_curve,
            hp_difference=hp_diff,
            torque_difference=torque_diff,
            rpm_differences=rpm_diffs,
            improvement_percent=improvement,
            mod_impact=mod_impact,
        )

    def analyze_power_band(self, curve: DynoCurve) -> PowerBandAnalysis:
        """
        Analyze power band characteristics.
        
        Returns insights like:
        - Power band width
        - Torque band width
        - Flatness (how flat the curve is)
        - Responsiveness (low-end torque)
        """
        if not curve.readings:
            return PowerBandAnalysis(
                peak_hp=0.0,
                peak_hp_rpm=0.0,
                peak_torque=0.0,
                peak_torque_rpm=0.0,
                power_band_width_rpm=0.0,
                torque_band_width_rpm=0.0,
                area_under_curve=0.0,
                flatness_score=0.0,
                responsiveness_score=0.0,
            )
        
        # Find RPM range
        rpms = [r.rpm for r in curve.readings if r.rpm is not None and r.rpm > 0]
        if not rpms:
            return PowerBandAnalysis(
                peak_hp=curve.peak_hp_crank,
                peak_hp_rpm=curve.peak_hp_rpm,
                peak_torque=curve.peak_torque_ftlb,
                peak_torque_rpm=curve.peak_torque_rpm,
                power_band_width_rpm=0.0,
                torque_band_width_rpm=0.0,
                area_under_curve=0.0,
                flatness_score=0.0,
                responsiveness_score=0.0,
            )
        
        min_rpm = min(rpms)
        max_rpm = max(rpms)
        
        # Calculate power band width (RPM range where HP > 90% of peak)
        peak_hp = curve.peak_hp_crank
        power_band_rpms = [
            r.rpm for r in curve.readings
            if r.rpm is not None and r.horsepower_crank >= (peak_hp * 0.90)
        ]
        power_band_width = max(power_band_rpms) - min(power_band_rpms) if power_band_rpms else 0.0
        
        # Calculate torque band width
        peak_torque = curve.peak_torque_ftlb
        torque_band_rpms = [
            r.rpm for r in curve.readings
            if r.rpm is not None and r.torque_ftlb is not None
            and r.torque_ftlb >= (peak_torque * 0.90)
        ]
        torque_band_width = max(torque_band_rpms) - min(torque_band_rpms) if torque_band_rpms else 0.0
        
        # Calculate area under curve (total power delivery)
        sorted_readings = sorted([r for r in curve.readings if r.rpm is not None], key=lambda x: x.rpm or 0)
        area = 0.0
        for i in range(len(sorted_readings) - 1):
            r1 = sorted_readings[i]
            r2 = sorted_readings[i + 1]
            if r1.rpm and r2.rpm:
                width = r2.rpm - r1.rpm
                avg_hp = (r1.horsepower_crank + r2.horsepower_crank) / 2.0
                area += width * avg_hp
        
        # Flatness score (how flat the curve is, 0-1)
        # Lower variance = flatter = better
        hp_values = [r.horsepower_crank for r in sorted_readings]
        if len(hp_values) > 1:
            mean_hp = sum(hp_values) / len(hp_values)
            variance = sum((h - mean_hp) ** 2 for h in hp_values) / len(hp_values)
            std_dev = math.sqrt(variance)
            # Normalize: lower std dev = higher score
            flatness_score = max(0.0, 1.0 - (std_dev / mean_hp)) if mean_hp > 0 else 0.0
        else:
            flatness_score = 0.0
        
        # Responsiveness score (low-end torque, 0-1)
        # Higher torque at low RPM = more responsive
        low_rpm_readings = [r for r in sorted_readings if r.rpm and r.rpm < 3000 and r.torque_ftlb]
        if low_rpm_readings:
            avg_low_torque = sum(r.torque_ftlb for r in low_rpm_readings if r.torque_ftlb) / len(low_rpm_readings)
            # Normalize: higher torque = higher score (normalize to 0-1)
            responsiveness_score = min(1.0, avg_low_torque / 300.0)  # 300 ft-lb = max score
        else:
            responsiveness_score = 0.0
        
        # Generate recommendations
        recommendations = []
        if power_band_width < 2000:
            recommendations.append("Narrow power band - consider cam/tune adjustments")
        if flatness_score < 0.7:
            recommendations.append("Power curve is peaky - may benefit from smoothing")
        if responsiveness_score < 0.5:
            recommendations.append("Low-end torque could be improved")
        if torque_band_width > power_band_width * 1.5:
            recommendations.append("Torque band is wider than power band - good for street")
        
        return PowerBandAnalysis(
            peak_hp=curve.peak_hp_crank,
            peak_hp_rpm=curve.peak_hp_rpm,
            peak_torque=curve.peak_torque_ftlb,
            peak_torque_rpm=curve.peak_torque_rpm,
            power_band_width_rpm=power_band_width,
            torque_band_width_rpm=torque_band_width,
            area_under_curve=area,
            flatness_score=flatness_score,
            responsiveness_score=responsiveness_score,
            recommendations=recommendations,
        )

    def apply_weather_correction(
        self,
        curve: DynoCurve,
        actual_temp_c: float,
        actual_pressure_kpa: float,
        actual_humidity_percent: float,
        standard: WeatherStandard = WeatherStandard.SAE_J1349,
    ) -> DynoCurve:
        """
        Apply weather correction to dyno curve (SAE standard).
        
        This corrects power to standard conditions so runs can be compared
        regardless of weather (temperature, pressure, humidity).
        
        Args:
            curve: Dyno curve to correct
            actual_temp_c: Actual air temperature during run
            actual_pressure_kpa: Actual barometric pressure
            actual_humidity_percent: Actual relative humidity
            standard: Weather correction standard to use
            
        Returns:
            Corrected dyno curve
        """
        if standard == WeatherStandard.NONE:
            return curve
        
        # SAE J1349 standard conditions
        std_temp_c = 25.0  # 77°F
        std_pressure_kpa = 99.208  # 29.23 inHg
        std_humidity_percent = 0.0  # Dry air
        
        # Calculate correction factor
        if standard == WeatherStandard.SAE_J1349:
            correction_factor = self._sae_j1349_correction(
                actual_temp_c,
                actual_pressure_kpa,
                actual_humidity_percent,
                std_temp_c,
                std_pressure_kpa,
                std_humidity_percent,
            )
        else:
            # Default to SAE J1349
            correction_factor = self._sae_j1349_correction(
                actual_temp_c,
                actual_pressure_kpa,
                actual_humidity_percent,
                std_temp_c,
                std_pressure_kpa,
                std_humidity_percent,
            )
        
        # Apply correction to all readings
        corrected_readings = []
        for reading in curve.readings:
            corrected_reading = DynoReading(
                timestamp=reading.timestamp,
                rpm=reading.rpm,
                speed_mph=reading.speed_mph,
                speed_mps=reading.speed_mps,
                acceleration_mps2=reading.acceleration_mps2,
                horsepower_wheel=reading.horsepower_wheel * correction_factor,
                horsepower_crank=reading.horsepower_crank * correction_factor,
                torque_ftlb=reading.torque_ftlb * correction_factor if reading.torque_ftlb else None,
                method=reading.method,
                confidence=reading.confidence,
                conditions=reading.conditions,
            )
            corrected_readings.append(corrected_reading)
        
        # Create corrected curve
        corrected_curve = DynoCurve(
            readings=corrected_readings,
            peak_hp_wheel=curve.peak_hp_wheel * correction_factor,
            peak_hp_crank=curve.peak_hp_crank * correction_factor,
            peak_hp_rpm=curve.peak_hp_rpm,
            peak_torque_ftlb=curve.peak_torque_ftlb * correction_factor,
            peak_torque_rpm=curve.peak_torque_rpm,
            accuracy_estimate=curve.accuracy_estimate,
            calibration_factor=curve.calibration_factor,
        )
        
        return corrected_curve

    def _sae_j1349_correction(
        self,
        temp_c: float,
        pressure_kpa: float,
        humidity_percent: float,
        std_temp_c: float,
        std_pressure_kpa: float,
        std_humidity_percent: float,
    ) -> float:
        """
        Calculate SAE J1349 correction factor.
        
        Formula: CF = (99/Pd) * ((Tc + 273)/(298))^0.5 * (1 - 0.18 * (Pv/Pd))
        Where:
        - Pd = dry air pressure
        - Tc = temperature in Celsius
        - Pv = water vapor pressure
        """
        # Convert to Kelvin
        temp_k = temp_c + 273.15
        std_temp_k = std_temp_c + 273.15
        
        # Calculate water vapor pressure (simplified)
        # More accurate would use Antoine equation
        pv = (humidity_percent / 100.0) * 0.611 * math.exp(17.27 * temp_c / (temp_c + 237.3))
        pd = pressure_kpa - pv  # Dry air pressure
        
        std_pv = (std_humidity_percent / 100.0) * 0.611 * math.exp(17.27 * std_temp_c / (std_temp_c + 237.3))
        std_pd = std_pressure_kpa - std_pv
        
        # SAE J1349 correction factor
        cf = (99.0 / pd) * math.sqrt(temp_k / 298.0) * (1.0 - 0.18 * (pv / pd))
        
        # Normalize to standard conditions
        std_cf = (99.0 / std_pd) * math.sqrt(std_temp_k / 298.0) * (1.0 - 0.18 * (std_pv / std_pd))
        
        return cf / std_cf

    def _get_hp_at_rpm(self, curve: DynoCurve, target_rpm: float) -> float:
        """Get horsepower at specific RPM (interpolated)."""
        if not curve.readings:
            return 0.0
        
        # Find readings near target RPM
        readings_with_rpm = [(r.rpm or 0, r.horsepower_crank) for r in curve.readings if r.rpm is not None]
        if not readings_with_rpm:
            return 0.0
        
        # Find closest readings
        sorted_readings = sorted(readings_with_rpm, key=lambda x: abs(x[0] - target_rpm))
        
        if len(sorted_readings) >= 2:
            # Linear interpolation
            r1 = sorted_readings[0]
            r2 = sorted_readings[1]
            if r1[0] != r2[0]:
                t = (target_rpm - r1[0]) / (r2[0] - r1[0])
                return r1[1] + t * (r2[1] - r1[1])
            else:
                return r1[1]
        else:
            return sorted_readings[0][1] if sorted_readings else 0.0

    def save_run(self, name: str, curve: DynoCurve) -> None:
        """Save a dyno run to history."""
        self.historical_runs.append((name, curve))
        LOGGER.info("Saved dyno run: %s (Peak HP: %.1f)", name, curve.peak_hp_crank)

    def get_mod_efficiency(self, mod_name: str) -> Optional[ModImpact]:
        """Get efficiency analysis for a specific mod."""
        for mod in self.mod_history:
            if mod.mod_name.lower() == mod_name.lower():
                if mod.cost_per_hp:
                    mod.efficiency_score = 1.0 / (mod.cost_per_hp / 100.0) if mod.cost_per_hp > 0 else 0.0
                return mod
        return None

    def predict_power_gain(
        self,
        base_curve: DynoCurve,
        mod_type: str,
        mod_params: Dict[str, float],
    ) -> DynoCurve:
        """
        Predict power gain from a modification (what-if analysis).
        
        Uses historical mod data to predict impact.
        
        Args:
            base_curve: Base dyno curve
            mod_type: Type of mod (e.g., "tune", "turbo", "exhaust")
            mod_params: Mod parameters (e.g., {"boost_psi": 25.0})
            
        Returns:
            Predicted dyno curve
        """
        # This would use ML or historical data to predict
        # For now, return base curve (placeholder)
        # TODO: Implement ML-based prediction
        return base_curve


__all__ = [
    "DynoAnalyzer",
    "DynoComparison",
    "ModImpact",
    "PowerBandAnalysis",
    "WeatherStandard",
]

