"""
Cylinder Pressure Analyzer - Professional Combustion Analysis

Provides advanced analysis of cylinder pressure data for professional tuning:
- Peak Firing Pressure (PFP)
- Rate of Pressure Rise (ROPR) - detonation detection
- Indicated Mean Effective Pressure (IMEP) - accurate HP/TQ calculation
- Combustion stability analysis
- Optimal ignition timing recommendations
"""

from __future__ import annotations

import logging
import math
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Deque, Dict, List, Optional, Tuple

import numpy as np

try:
    from scipy import integrate
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

LOGGER = logging.getLogger(__name__)

# Constants
SPECIFIC_HEAT_RATIO = 1.35  # γ for air
DEGREES_TO_RADIANS = math.pi / 180.0
RADIANS_TO_DEGREES = 180.0 / math.pi
PSI_TO_PA = 6894.76  # PSI to Pascals
PA_TO_PSI = 1.0 / 6894.76
BAR_TO_PA = 100000.0
PA_TO_BAR = 1.0 / 100000.0


class PressureUnit(Enum):
    """Pressure unit options."""
    PSI = "psi"
    BAR = "bar"
    KPA = "kpa"
    PA = "pa"


@dataclass
class PressureReading:
    """Single cylinder pressure reading with crank angle."""
    crank_angle_deg: float  # Crank angle in degrees (0-720 for 4-stroke)
    pressure: float  # Pressure in specified unit
    timestamp: float  # Timestamp in seconds
    cylinder: int = 1  # Cylinder number (1-based)
    rpm: Optional[float] = None  # Engine RPM at this reading
    afr: Optional[float] = None  # Air-fuel ratio (if available)
    ignition_timing: Optional[float] = None  # Ignition timing in degrees BTDC
    boost_psi: Optional[float] = None  # Boost pressure (if available)


@dataclass
class PressureCycle:
    """Complete pressure cycle (720° for 4-stroke engine)."""
    cylinder: int
    readings: List[PressureReading]
    cycle_number: int  # Cycle number (for cycle-to-cycle analysis)
    timestamp_start: float
    timestamp_end: float
    
    def get_pressure_array(self) -> np.ndarray:
        """Get pressure values as numpy array."""
        return np.array([r.pressure for r in self.readings])
    
    def get_crank_angle_array(self) -> np.ndarray:
        """Get crank angle values as numpy array."""
        return np.array([r.crank_angle_deg for r in self.readings])
    
    def get_rpm(self) -> Optional[float]:
        """Get average RPM for this cycle."""
        rpms = [r.rpm for r in self.readings if r.rpm is not None]
        return np.mean(rpms) if rpms else None


@dataclass
class CombustionMetrics:
    """Combustion analysis metrics for a single cycle."""
    pfp: float  # Peak Firing Pressure
    pfp_angle: float  # Crank angle at PFP (degrees ATDC)
    ropr_max: float  # Maximum Rate of Pressure Rise (PSI/degree)
    ropr_max_angle: float  # Crank angle at max ROPR
    imep: float  # Indicated Mean Effective Pressure
    combustion_start_angle: Optional[float] = None  # Start of combustion (degrees ATDC)
    combustion_end_angle: Optional[float] = None  # End of combustion
    combustion_duration: Optional[float] = None  # Combustion duration (degrees)
    heat_release_peak: Optional[float] = None  # Peak heat release rate
    detonation_detected: bool = False  # Detonation detected flag
    detonation_severity: float = 0.0  # Detonation severity (0-1)


@dataclass
class StabilityMetrics:
    """Combustion stability metrics across multiple cycles."""
    cov_pfp: float  # Coefficient of Variation for PFP
    pfp_mean: float  # Mean PFP
    pfp_std: float  # Standard deviation of PFP
    pfp_min: float  # Minimum PFP
    pfp_max: float  # Maximum PFP
    cycle_count: int  # Number of cycles analyzed
    cylinder_variation: Optional[Dict[int, float]] = None  # PFP variation per cylinder
    cycle_to_cycle_variation: float = 0.0  # Cycle-to-cycle variation (COV)


class CylinderPressureAnalyzer:
    """
    Analyzes cylinder pressure data for professional tuning applications.
    
    Features:
    - Peak Firing Pressure (PFP) calculation
    - Rate of Pressure Rise (ROPR) analysis
    - Indicated Mean Effective Pressure (IMEP) calculation
    - Combustion stability analysis
    - Detonation detection
    - Optimal ignition timing recommendations
    """
    
    def __init__(
        self,
        pressure_unit: PressureUnit = PressureUnit.PSI,
        engine_displacement_cc: float = 5000.0,  # Engine displacement in cc
        number_of_cylinders: int = 8,
        detonation_threshold_ropr: float = 20.0,  # PSI/degree threshold for detonation
        smoothing_window: int = 5,  # Moving average window for smoothing
    ) -> None:
        """
        Initialize cylinder pressure analyzer.
        
        Args:
            pressure_unit: Unit for pressure values
            engine_displacement_cc: Total engine displacement in cubic centimeters
            number_of_cylinders: Number of cylinders
            detonation_threshold_ropr: ROPR threshold for detonation detection (PSI/degree)
            smoothing_window: Window size for moving average smoothing
        """
        self.pressure_unit = pressure_unit
        self.engine_displacement_cc = engine_displacement_cc
        self.displacement_per_cylinder_cc = engine_displacement_cc / number_of_cylinders
        self.number_of_cylinders = number_of_cylinders
        self.detonation_threshold_ropr = detonation_threshold_ropr
        self.smoothing_window = smoothing_window
        
        # History for cycle-to-cycle analysis
        self.cycle_history: Deque[PressureCycle] = deque(maxlen=100)
        self.metrics_history: Deque[CombustionMetrics] = deque(maxlen=100)
        
        LOGGER.info(
            f"Cylinder Pressure Analyzer initialized: "
            f"{engine_displacement_cc}cc, {number_of_cylinders} cylinders, "
            f"unit={pressure_unit.value}"
        )
    
    def calculate_pfp(self, cycle: PressureCycle) -> Tuple[float, float]:
        """
        Calculate Peak Firing Pressure (PFP) and its location.
        
        Args:
            cycle: Pressure cycle to analyze
            
        Returns:
            Tuple of (PFP value, crank angle at PFP in degrees ATDC)
        """
        if not cycle.readings:
            return 0.0, 0.0
        
        pressures = cycle.get_pressure_array()
        angles = cycle.get_crank_angle_array()
        
        # Find maximum pressure
        max_idx = np.argmax(pressures)
        pfp = float(pressures[max_idx])
        pfp_angle = float(angles[max_idx])
        
        # Convert to ATDC (assuming 0° is TDC)
        # For 4-stroke: 0-180° = compression/power, 180-360° = exhaust/intake
        if pfp_angle > 180:
            pfp_angle = pfp_angle - 360  # Convert to negative (BTDC) or keep as ATDC
        
        return pfp, pfp_angle
    
    def calculate_ropr(
        self,
        cycle: PressureCycle,
        window_size: int = 3
    ) -> Tuple[float, float, np.ndarray]:
        """
        Calculate Rate of Pressure Rise (ROPR).
        
        Args:
            cycle: Pressure cycle to analyze
            window_size: Window size for derivative calculation
            
        Returns:
            Tuple of (max ROPR, angle at max ROPR, ROPR array)
        """
        if len(cycle.readings) < window_size + 1:
            return 0.0, 0.0, np.array([])
        
        pressures = cycle.get_pressure_array()
        angles = cycle.get_crank_angle_array()
        
        # Calculate derivative (dP/dθ)
        ropr = np.gradient(pressures, angles)
        
        # Apply smoothing if needed
        if self.smoothing_window > 1:
            ropr = self._apply_smoothing(ropr, self.smoothing_window)
        
        # Find maximum ROPR
        max_idx = np.argmax(ropr)
        max_ropr = float(ropr[max_idx])
        max_angle = float(angles[max_idx])
        
        return max_ropr, max_angle, ropr
    
    def calculate_imep(
        self,
        cycle: PressureCycle,
        bore_mm: Optional[float] = None,
        stroke_mm: Optional[float] = None
    ) -> float:
        """
        Calculate Indicated Mean Effective Pressure (IMEP).
        
        IMEP = (1 / V_d) × ∫ P dV
        
        Args:
            cycle: Pressure cycle to analyze
            bore_mm: Cylinder bore in mm (optional, for volume calculation)
            stroke_mm: Stroke length in mm (optional, for volume calculation)
            
        Returns:
            IMEP in same unit as pressure
        """
        if len(cycle.readings) < 2:
            return 0.0
        
        pressures = cycle.get_pressure_array()
        angles = cycle.get_crank_angle_array()
        
        # Convert angles to radians
        angles_rad = np.deg2rad(angles)
        
        # Calculate volume as function of crank angle
        # Simplified: V(θ) = V_c + (V_d/2) × (1 - cos(θ))
        # Where V_c = clearance volume, V_d = displacement volume
        
        if bore_mm and stroke_mm:
            # Calculate actual volume
            bore_m = bore_mm / 1000.0
            stroke_m = stroke_mm / 1000.0
            v_d = math.pi * (bore_m / 2.0) ** 2 * stroke_m  # Displacement volume per cylinder
            v_c = v_d / 8.0  # Approximate clearance volume (compression ratio ~9:1)
            
            # Volume as function of angle (simplified)
            volumes = v_c + (v_d / 2.0) * (1.0 - np.cos(angles_rad))
        else:
            # Simplified: use angle as proxy for volume
            # Normalize to 0-1 range
            volumes = (1.0 - np.cos(angles_rad)) / 2.0
        
        # Integrate P dV
        if SCIPY_AVAILABLE:
            # Use scipy for accurate integration
            imep_value = integrate.trapz(pressures, volumes)
        else:
            # Simple trapezoidal integration
            imep_value = np.trapz(pressures, volumes)
        
        # Normalize by displacement volume
        if bore_mm and stroke_mm:
            imep = imep_value / v_d
        else:
            # Use normalized volume
            imep = imep_value * 2.0  # Scale factor for normalized volume
        
        return float(imep)
    
    def analyze_combustion(
        self,
        cycle: PressureCycle,
        calculate_heat_release: bool = False
    ) -> CombustionMetrics:
        """
        Perform complete combustion analysis for a cycle.
        
        Args:
            cycle: Pressure cycle to analyze
            calculate_heat_release: Whether to calculate heat release (requires volume data)
            
        Returns:
            CombustionMetrics with all calculated values
        """
        # Calculate PFP
        pfp, pfp_angle = self.calculate_pfp(cycle)
        
        # Calculate ROPR
        max_ropr, ropr_angle, ropr_array = self.calculate_ropr(cycle)
        
        # Calculate IMEP
        imep = self.calculate_imep(cycle)
        
        # Detect detonation
        detonation_detected = max_ropr > self.detonation_threshold_ropr
        detonation_severity = min(1.0, max_ropr / (self.detonation_threshold_ropr * 2.0))
        
        # Calculate combustion phasing (simplified)
        # Find where pressure starts rising significantly (combustion start)
        pressures = cycle.get_pressure_array()
        angles = cycle.get_crank_angle_array()
        
        # Find TDC (0° or 360°)
        tdc_idx = np.argmin(np.abs(angles % 360))
        
        # Find combustion start (pressure rise after TDC)
        if tdc_idx < len(pressures) - 10:
            post_tdc_pressures = pressures[tdc_idx:]
            post_tdc_angles = angles[tdc_idx:]
            
            # Find where pressure starts rising (threshold: 10% of max)
            threshold = pressures[tdc_idx] + (pfp - pressures[tdc_idx]) * 0.1
            start_indices = np.where(post_tdc_pressures > threshold)[0]
            combustion_start_angle = float(post_tdc_angles[start_indices[0]]) if len(start_indices) > 0 else None
            
            # Find combustion end (pressure peak or 90% of peak)
            end_threshold = pfp * 0.9
            end_indices = np.where(post_tdc_pressures > end_threshold)[0]
            combustion_end_angle = float(post_tdc_angles[end_indices[-1]]) if len(end_indices) > 0 else None
            
            combustion_duration = (
                combustion_end_angle - combustion_start_angle
                if combustion_start_angle and combustion_end_angle
                else None
            )
        else:
            combustion_start_angle = None
            combustion_end_angle = None
            combustion_duration = None
        
        # Heat release (simplified - requires full volume calculation)
        heat_release_peak = None
        if calculate_heat_release:
            # This would require full P-V diagram calculation
            # Simplified version here
            pass
        
        return CombustionMetrics(
            pfp=pfp,
            pfp_angle=pfp_angle,
            ropr_max=max_ropr,
            ropr_max_angle=ropr_angle,
            imep=imep,
            combustion_start_angle=combustion_start_angle,
            combustion_end_angle=combustion_end_angle,
            combustion_duration=combustion_duration,
            heat_release_peak=heat_release_peak,
            detonation_detected=detonation_detected,
            detonation_severity=detonation_severity,
        )
    
    def analyze_stability(
        self,
        cycles: List[PressureCycle],
        per_cylinder: bool = True
    ) -> StabilityMetrics:
        """
        Analyze combustion stability across multiple cycles.
        
        Args:
            cycles: List of pressure cycles to analyze
            per_cylinder: Whether to calculate per-cylinder variation
            
        Returns:
            StabilityMetrics with stability analysis
        """
        if not cycles:
            return StabilityMetrics(
                cov_pfp=0.0,
                pfp_mean=0.0,
                pfp_std=0.0,
                pfp_min=0.0,
                pfp_max=0.0,
                cycle_count=0,
            )
        
        # Calculate PFP for all cycles
        pfps = []
        for cycle in cycles:
            pfp, _ = self.calculate_pfp(cycle)
            pfps.append(pfp)
        
        pfps_array = np.array(pfps)
        pfp_mean = float(np.mean(pfps_array))
        pfp_std = float(np.std(pfps_array))
        pfp_min = float(np.min(pfps_array))
        pfp_max = float(np.max(pfps_array))
        
        # Coefficient of Variation
        cov_pfp = (pfp_std / pfp_mean * 100.0) if pfp_mean > 0 else 0.0
        
        # Per-cylinder variation
        cylinder_variation = None
        if per_cylinder:
            cylinder_variation = {}
            for cylinder_num in range(1, self.number_of_cylinders + 1):
                cylinder_cycles = [c for c in cycles if c.cylinder == cylinder_num]
                if cylinder_cycles:
                    cylinder_pfps = [self.calculate_pfp(c)[0] for c in cylinder_cycles]
                    cylinder_mean = np.mean(cylinder_pfps)
                    cylinder_std = np.std(cylinder_pfps)
                    cylinder_cov = (cylinder_std / cylinder_mean * 100.0) if cylinder_mean > 0 else 0.0
                    cylinder_variation[cylinder_num] = float(cylinder_cov)
        
        return StabilityMetrics(
            cov_pfp=cov_pfp,
            pfp_mean=pfp_mean,
            pfp_std=pfp_std,
            pfp_min=pfp_min,
            pfp_max=pfp_max,
            cycle_count=len(cycles),
            cylinder_variation=cylinder_variation,
            cycle_to_cycle_variation=cov_pfp,
        )
    
    def calculate_hp_from_imep(
        self,
        imep: float,
        rpm: float,
        pressure_unit: Optional[PressureUnit] = None
    ) -> float:
        """
        Calculate horsepower from IMEP.
        
        HP = (IMEP × V_d × RPM × N) / (792,000 × 2)
        
        Where:
        - V_d = Displacement per cylinder (cubic inches)
        - RPM = Engine speed
        - N = Number of cylinders
        - 792,000 = Conversion factor (12 × 33,000 × 2)
        - 2 = 4-stroke cycle factor
        
        Args:
            imep: Indicated Mean Effective Pressure
            rpm: Engine RPM
            pressure_unit: Unit of IMEP (defaults to instance unit)
            
        Returns:
            Horsepower
        """
        if pressure_unit is None:
            pressure_unit = self.pressure_unit
        
        # Convert IMEP to PSI if needed
        if pressure_unit == PressureUnit.BAR:
            imep_psi = imep * 14.5038
        elif pressure_unit == PressureUnit.KPA:
            imep_psi = imep * 0.145038
        elif pressure_unit == PressureUnit.PA:
            imep_psi = imep * PA_TO_PSI
        else:
            imep_psi = imep  # Already in PSI
        
        # Convert displacement to cubic inches
        displacement_ci = self.engine_displacement_cc * 0.0610237
        
        # Calculate HP
        hp = (imep_psi * displacement_ci * rpm * self.number_of_cylinders) / (792000.0 * 2.0)
        
        return float(hp)
    
    def optimize_ignition_timing(
        self,
        cycles_by_timing: Dict[float, List[PressureCycle]]
    ) -> Dict[str, Any]:
        """
        Recommend optimal ignition timing based on pressure analysis.
        
        Args:
            cycles_by_timing: Dictionary mapping ignition timing to cycles
            
        Returns:
            Dictionary with optimization results
        """
        if not cycles_by_timing:
            return {
                "optimal_timing": None,
                "recommendation": "Insufficient data",
                "pfp_by_timing": {},
                "ropr_by_timing": {},
            }
        
        pfp_by_timing = {}
        ropr_by_timing = {}
        
        for timing, cycles in cycles_by_timing.items():
            if not cycles:
                continue
            
            # Average PFP for this timing
            pfps = [self.calculate_pfp(c)[0] for c in cycles]
            avg_pfp = np.mean(pfps)
            pfp_by_timing[timing] = float(avg_pfp)
            
            # Average max ROPR
            roprs = [self.calculate_ropr(c)[0] for c in cycles]
            avg_ropr = np.mean(roprs)
            ropr_by_timing[timing] = float(avg_ropr)
        
        # Find optimal timing (highest PFP without excessive ROPR)
        optimal_timing = None
        best_score = -1.0
        
        for timing in pfp_by_timing.keys():
            pfp = pfp_by_timing[timing]
            ropr = ropr_by_timing.get(timing, 0.0)
            
            # Score: PFP weighted, penalize high ROPR
            score = pfp - (ropr * 2.0)  # Penalize ROPR
            
            if score > best_score:
                best_score = score
                optimal_timing = timing
        
        # Generate recommendation
        if optimal_timing:
            recommendation = (
                f"Optimal ignition timing: {optimal_timing:.1f}° BTDC. "
                f"PFP: {pfp_by_timing[optimal_timing]:.1f} {self.pressure_unit.value}, "
                f"ROPR: {ropr_by_timing.get(optimal_timing, 0.0):.1f} PSI/deg"
            )
        else:
            recommendation = "Unable to determine optimal timing"
        
        return {
            "optimal_timing": optimal_timing,
            "recommendation": recommendation,
            "pfp_by_timing": pfp_by_timing,
            "ropr_by_timing": ropr_by_timing,
            "score": best_score,
        }
    
    def _apply_smoothing(self, data: np.ndarray, window: int) -> np.ndarray:
        """Apply moving average smoothing."""
        if len(data) < window:
            return data
        
        # Use convolution for moving average
        kernel = np.ones(window) / window
        smoothed = np.convolve(data, kernel, mode='same')
        
        return smoothed
    
    def add_cycle(self, cycle: PressureCycle) -> CombustionMetrics:
        """
        Add a cycle for analysis and return metrics.
        
        Args:
            cycle: Pressure cycle to add
            
        Returns:
            CombustionMetrics for the cycle
        """
        metrics = self.analyze_combustion(cycle)
        
        # Store in history
        self.cycle_history.append(cycle)
        self.metrics_history.append(metrics)
        
        return metrics
    
    def get_recent_stability(self, num_cycles: int = 10) -> StabilityMetrics:
        """
        Get stability metrics for recent cycles.
        
        Args:
            num_cycles: Number of recent cycles to analyze
            
        Returns:
            StabilityMetrics
        """
        recent_cycles = list(self.cycle_history)[-num_cycles:]
        return self.analyze_stability(recent_cycles)

