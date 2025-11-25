"""
Diesel Auto-Tuning Engine
AI-powered automatic tuning for diesel engines.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from services.diesel_engine_detector import DieselEngineProfile, DieselSystem

LOGGER = logging.getLogger(__name__)


class DieselTuningMode(Enum):
    """Diesel tuning modes."""
    ECONOMY = "economy"  # Fuel economy focus
    PERFORMANCE = "performance"  # Power and torque
    TOWING = "towing"  # Towing optimization
    RACING = "racing"  # Maximum performance
    EMISSIONS = "emissions"  # Emissions compliance
    BALANCED = "balanced"  # Balanced approach


@dataclass
class DieselTuningParameter:
    """Diesel tuning parameter."""
    name: str
    current_value: float
    min_value: float
    max_value: float
    unit: str
    category: str  # injection, boost, timing, emissions, etc.
    safety_critical: bool = False


@dataclass
class DieselOptimizationResult:
    """Diesel optimization result."""
    parameter_name: str
    current_value: float
    optimized_value: float
    improvement_estimate: float  # %
    confidence: float
    reasoning: str
    safety_check: bool = True
    requires_approval: bool = True


@dataclass
class DieselTuningRecommendation:
    """Complete diesel tuning recommendation."""
    recommendations: List[DieselOptimizationResult]
    expected_power_gain: Optional[float] = None  # HP
    expected_torque_gain: Optional[float] = None  # lb-ft
    expected_efficiency_gain: Optional[float] = None  # %
    expected_emissions_change: Optional[float] = None  # %
    confidence: float = 0.0
    reasoning: str = ""
    conditions: Dict[str, Any] = field(default_factory=dict)


class DieselAutoTuning:
    """
    Diesel auto-tuning engine.
    
    Features:
    - Automatic parameter optimization
    - Diesel-specific tuning modes
    - Safety limits for diesel engines
    - Emissions system consideration
    - Turbo optimization
    - Injection timing optimization
    """
    
    def __init__(
        self,
        engine_profile: DieselEngineProfile,
        tuning_mode: DieselTuningMode = DieselTuningMode.BALANCED,
    ):
        """
        Initialize diesel auto-tuning.
        
        Args:
            engine_profile: Diesel engine profile
            tuning_mode: Tuning mode
        """
        self.engine_profile = engine_profile
        self.tuning_mode = tuning_mode
        
        # Safety limits
        self.safety_limits: Dict[str, tuple[float, float]] = {}
        self._initialize_safety_limits()
    
    def _initialize_safety_limits(self) -> None:
        """Initialize safety limits for diesel engine."""
        profile = self.engine_profile
        
        # Injection pressure limits
        self.safety_limits["injection_pressure"] = (
            profile.max_injection_pressure * 0.5,  # Min
            profile.max_injection_pressure * 1.1,  # Max (10% over stock)
        )
        
        # Boost pressure limits
        self.safety_limits["boost_pressure"] = (
            0.0,  # Min
            profile.max_boost_pressure * 1.2,  # Max (20% over stock)
        )
        
        # EGT (Exhaust Gas Temperature) limits
        self.safety_limits["egt"] = (
            200,  # Min (Fahrenheit)
            1650,  # Max (critical for diesel)
        )
        
        # Cylinder pressure limits
        self.safety_limits["cylinder_pressure"] = (
            0.0,
            3000,  # PSI - typical max for diesel
        )
        
        # Injection timing limits
        self.safety_limits["injection_timing"] = (
            -10,  # Degrees BTDC
            30,  # Degrees BTDC
        )
    
    def analyze_and_optimize(
        self,
        current_telemetry: Dict[str, Any],
        current_parameters: Dict[str, float],
        conditions: Optional[Dict[str, Any]] = None,
    ) -> DieselTuningRecommendation:
        """
        Analyze and optimize diesel engine parameters.
        
        Args:
            current_telemetry: Current telemetry data
            current_parameters: Current tuning parameters
            conditions: Environmental conditions
        
        Returns:
            DieselTuningRecommendation
        """
        recommendations = []
        
        # Optimize injection timing
        if "injection_timing" in current_parameters:
            timing_rec = self._optimize_injection_timing(current_telemetry, current_parameters, conditions)
            if timing_rec:
                recommendations.append(timing_rec)
        
        # Optimize injection pressure
        if "injection_pressure" in current_parameters or "rail_pressure" in current_parameters:
            pressure_rec = self._optimize_injection_pressure(current_telemetry, current_parameters, conditions)
            if pressure_rec:
                recommendations.append(pressure_rec)
        
        # Optimize boost
        if "boost_pressure" in current_parameters:
            boost_rec = self._optimize_boost(current_telemetry, current_parameters, conditions)
            if boost_rec:
                recommendations.append(boost_rec)
        
        # Optimize fuel quantity
        if "fuel_quantity" in current_parameters or "fuel_duration" in current_parameters:
            fuel_rec = self._optimize_fuel_quantity(current_telemetry, current_parameters, conditions)
            if fuel_rec:
                recommendations.append(fuel_rec)
        
        # Calculate expected improvements
        power_gain, torque_gain, efficiency_gain, emissions_change = self._estimate_improvements(recommendations)
        
        # Overall confidence
        confidence = sum(r.confidence for r in recommendations) / len(recommendations) if recommendations else 0.0
        
        return DieselTuningRecommendation(
            recommendations=recommendations,
            expected_power_gain=power_gain,
            expected_torque_gain=torque_gain,
            expected_efficiency_gain=efficiency_gain,
            expected_emissions_change=emissions_change,
            confidence=confidence,
            reasoning=self._generate_reasoning(recommendations, conditions),
            conditions=conditions or {},
        )
    
    def _optimize_injection_timing(
        self,
        telemetry: Dict[str, Any],
        parameters: Dict[str, float],
        conditions: Optional[Dict[str, Any]],
    ) -> Optional[DieselOptimizationResult]:
        """Optimize injection timing."""
        current_timing = parameters.get("injection_timing", telemetry.get("injection_timing", 0.0))
        
        # Calculate optimal timing based on mode
        if self.tuning_mode == DieselTuningMode.PERFORMANCE:
            target_timing = current_timing + 2.0  # Advance for power
        elif self.tuning_mode == DieselTuningMode.ECONOMY:
            target_timing = current_timing - 1.0  # Retard for efficiency
        elif self.tuning_mode == DieselTuningMode.TOWING:
            target_timing = current_timing + 1.0  # Slight advance
        else:
            target_timing = current_timing  # No change
        
        # Check safety limits
        min_timing, max_timing = self.safety_limits.get("injection_timing", (-10, 30))
        target_timing = max(min_timing, min(max_timing, target_timing))
        
        if abs(target_timing - current_timing) < 0.5:
            return None
        
        improvement = abs(target_timing - current_timing) / abs(current_timing) * 100 if current_timing != 0 else 0
        confidence = 0.75
        
        return DieselOptimizationResult(
            parameter_name="injection_timing",
            current_value=current_timing,
            optimized_value=target_timing,
            improvement_estimate=improvement,
            confidence=confidence,
            reasoning=f"Optimize injection timing for {self.tuning_mode.value}",
            safety_check=True,
            requires_approval=True,
        )
    
    def _optimize_injection_pressure(
        self,
        telemetry: Dict[str, Any],
        parameters: Dict[str, float],
        conditions: Optional[Dict[str, Any]],
    ) -> Optional[DieselOptimizationResult]:
        """Optimize injection pressure."""
        current_pressure = parameters.get(
            "injection_pressure",
            parameters.get("rail_pressure", telemetry.get("rail_pressure", 0.0))
        )
        
        # Calculate optimal pressure
        if self.tuning_mode == DieselTuningMode.PERFORMANCE:
            target_pressure = current_pressure * 1.05  # Increase for power
        elif self.tuning_mode == DieselTuningMode.ECONOMY:
            target_pressure = current_pressure * 0.98  # Slight decrease
        else:
            target_pressure = current_pressure
        
        # Check safety limits
        min_pressure, max_pressure = self.safety_limits.get("injection_pressure", (0, 30000))
        target_pressure = max(min_pressure, min(max_pressure, target_pressure))
        
        if abs(target_pressure - current_pressure) < 100:  # 100 PSI tolerance
            return None
        
        improvement = (target_pressure - current_pressure) / current_pressure * 100 if current_pressure > 0 else 0
        confidence = 0.70
        
        return DieselOptimizationResult(
            parameter_name="injection_pressure",
            current_value=current_pressure,
            optimized_value=target_pressure,
            improvement_estimate=improvement,
            confidence=confidence,
            reasoning=f"Optimize injection pressure for {self.tuning_mode.value}",
            safety_check=True,
            requires_approval=True,
        )
    
    def _optimize_boost(
        self,
        telemetry: Dict[str, Any],
        parameters: Dict[str, float],
        conditions: Optional[Dict[str, Any]],
    ) -> Optional[DieselOptimizationResult]:
        """Optimize boost pressure."""
        current_boost = parameters.get("boost_pressure", telemetry.get("boost_pressure", 0.0))
        
        # Check EGT to ensure safe boost
        egt = telemetry.get("egt", telemetry.get("exhaust_temp", 0))
        egt_limit = self.safety_limits.get("egt", (200, 1650))[1]
        
        if egt > egt_limit * 0.9:  # Approaching limit
            # Reduce boost to protect engine
            target_boost = current_boost * 0.95
        elif self.tuning_mode == DieselTuningMode.PERFORMANCE:
            target_boost = min(current_boost * 1.1, self.engine_profile.max_boost_pressure * 1.2)
        else:
            target_boost = current_boost
        
        # Check safety limits
        min_boost, max_boost = self.safety_limits.get("boost_pressure", (0, 50))
        target_boost = max(min_boost, min(max_boost, target_boost))
        
        if abs(target_boost - current_boost) < 0.5:
            return None
        
        improvement = (target_boost - current_boost) / current_boost * 100 if current_boost > 0 else 0
        confidence = 0.80
        
        return DieselOptimizationResult(
            parameter_name="boost_pressure",
            current_value=current_boost,
            optimized_value=target_boost,
            improvement_estimate=improvement,
            confidence=confidence,
            reasoning=f"Optimize boost for {self.tuning_mode.value} (EGT: {egt:.0f}°F)",
            safety_check=True,
            requires_approval=True,
        )
    
    def _optimize_fuel_quantity(
        self,
        telemetry: Dict[str, Any],
        parameters: Dict[str, float],
        conditions: Optional[Dict[str, Any]],
    ) -> Optional[DieselOptimizationResult]:
        """Optimize fuel quantity/duration."""
        current_fuel = parameters.get(
            "fuel_quantity",
            parameters.get("fuel_duration", telemetry.get("fuel_duration", 0.0))
        )
        
        # Check smoke/air-fuel ratio
        afr = telemetry.get("afr", telemetry.get("lambda", 0))
        
        if self.tuning_mode == DieselTuningMode.PERFORMANCE:
            # Increase fuel for power (but watch smoke)
            if afr > 18:  # Lean - can add fuel
                target_fuel = current_fuel * 1.05
            else:
                target_fuel = current_fuel  # Too rich already
        elif self.tuning_mode == DieselTuningMode.ECONOMY:
            target_fuel = current_fuel * 0.98  # Reduce for efficiency
        else:
            target_fuel = current_fuel
        
        if abs(target_fuel - current_fuel) < 0.01:
            return None
        
        improvement = (target_fuel - current_fuel) / current_fuel * 100 if current_fuel > 0 else 0
        confidence = 0.65
        
        return DieselOptimizationResult(
            parameter_name="fuel_quantity",
            current_value=current_fuel,
            optimized_value=target_fuel,
            improvement_estimate=improvement,
            confidence=confidence,
            reasoning=f"Optimize fuel quantity for {self.tuning_mode.value} (AFR: {afr:.1f})",
            safety_check=True,
            requires_approval=True,
        )
    
    def _estimate_improvements(
        self,
        recommendations: List[DieselOptimizationResult],
    ) -> tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
        """Estimate power, torque, efficiency, and emissions improvements."""
        if not recommendations:
            return None, None, None, None
        
        total_improvement = sum(r.improvement_estimate for r in recommendations) / len(recommendations)
        
        if self.tuning_mode == DieselTuningMode.PERFORMANCE:
            power_gain = total_improvement * 3.0  # Rough estimate
            torque_gain = total_improvement * 3.5
            efficiency_gain = None
            emissions_change = 5.0  # Typically increases
        elif self.tuning_mode == DieselTuningMode.ECONOMY:
            power_gain = None
            torque_gain = None
            efficiency_gain = total_improvement * 2.0
            emissions_change = -2.0  # Typically decreases
        else:
            power_gain = total_improvement * 1.5
            torque_gain = total_improvement * 2.0
            efficiency_gain = total_improvement * 0.5
            emissions_change = 0.0
        
        return power_gain, torque_gain, efficiency_gain, emissions_change
    
    def _generate_reasoning(
        self,
        recommendations: List[DieselOptimizationResult],
        conditions: Optional[Dict[str, Any]],
    ) -> str:
        """Generate human-readable reasoning."""
        reasoning_parts = []
        
        reasoning_parts.append(f"Diesel engine: {self.engine_profile.make} {self.engine_profile.model}")
        reasoning_parts.append(f"Tuning mode: {self.tuning_mode.value}")
        reasoning_parts.append(f"Engine type: {self.engine_profile.engine_type.value}")
        
        if conditions:
            if "altitude" in conditions:
                reasoning_parts.append(f"Altitude: {conditions['altitude']}ft")
            if "temperature_f" in conditions:
                reasoning_parts.append(f"Temperature: {conditions['temperature_f']}°F")
        
        reasoning_parts.append(f"Generated {len(recommendations)} optimization recommendations")
        
        return ". ".join(reasoning_parts)


