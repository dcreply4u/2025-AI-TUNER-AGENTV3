"""
AI Auto-Tuning Engine
AI automatically optimizes ECU parameters based on conditions and performance.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

LOGGER = logging.getLogger(__name__)


class TuningMode(Enum):
    """Tuning optimization mode."""
    SAFE = "safe"  # Conservative, safety-first
    MODERATE = "moderate"  # Balanced performance and safety
    AGGRESSIVE = "aggressive"  # Maximum performance
    ADAPTIVE = "adaptive"  # Learns from user preferences


class OptimizationGoal(Enum):
    """Optimization goal."""
    MAX_POWER = "max_power"
    MAX_TORQUE = "max_torque"
    FUEL_EFFICIENCY = "fuel_efficiency"
    BALANCED = "balanced"
    TRACK_PERFORMANCE = "track_performance"
    STREET_PERFORMANCE = "street_performance"


@dataclass
class TuningParameter:
    """ECU tuning parameter."""
    name: str
    current_value: float
    min_value: float
    max_value: float
    unit: str
    category: str  # fuel, ignition, boost, etc.
    safety_critical: bool = False


@dataclass
class OptimizationResult:
    """Result of parameter optimization."""
    parameter_name: str
    current_value: float
    optimized_value: float
    improvement_estimate: float  # Estimated improvement (%)
    confidence: float  # 0.0 - 1.0
    reasoning: str
    safety_check: bool = True
    requires_approval: bool = True


@dataclass
class TuningRecommendation:
    """Complete tuning recommendation."""
    recommendations: List[OptimizationResult]
    expected_power_gain: Optional[float] = None  # HP
    expected_torque_gain: Optional[float] = None  # lb-ft
    expected_efficiency_gain: Optional[float] = None  # %
    confidence: float = 0.0
    reasoning: str = ""
    conditions: Dict[str, Any] = field(default_factory=dict)  # Weather, altitude, etc.


class AIAutoTuningEngine:
    """
    AI-powered automatic tuning engine.
    
    Features:
    - Analyzes telemetry data
    - Optimizes ECU parameters
    - Adapts to conditions (weather, altitude, fuel)
    - Learns from user preferences
    - Safety-first approach
    """
    
    def __init__(
        self,
        tuning_mode: TuningMode = TuningMode.MODERATE,
        optimization_goal: OptimizationGoal = OptimizationGoal.BALANCED,
        learning_enabled: bool = True,
    ):
        """
        Initialize AI auto-tuning engine.
        
        Args:
            tuning_mode: Tuning optimization mode
            optimization_goal: Primary optimization goal
            learning_enabled: Enable machine learning from user feedback
        """
        self.tuning_mode = tuning_mode
        self.optimization_goal = optimization_goal
        self.learning_enabled = learning_enabled
        
        # Learning data
        self.user_feedback: List[Dict[str, Any]] = []
        self.optimization_history: List[TuningRecommendation] = []
        
        # Safety limits
        self.safety_limits: Dict[str, Tuple[float, float]] = {}
        self._initialize_safety_limits()
    
    def _initialize_safety_limits(self) -> None:
        """Initialize safety limits for parameters."""
        # Default safety limits (can be customized per vehicle)
        self.safety_limits = {
            "afr_min": (12.0, 14.7),  # Min, Max AFR
            "afr_max": (14.7, 16.0),
            "ignition_advance_max": (30.0, 50.0),  # Degrees
            "boost_max": (15.0, 30.0),  # PSI
            "rpm_limit_max": (7000, 9000),  # RPM
            "coolant_temp_max": (200, 250),  # Fahrenheit
        }
    
    def analyze_and_optimize(
        self,
        current_telemetry: Dict[str, Any],
        current_parameters: Dict[str, float],
        vehicle_profile: Optional[Dict[str, Any]] = None,
        conditions: Optional[Dict[str, Any]] = None,
    ) -> TuningRecommendation:
        """
        Analyze current state and generate optimization recommendations.
        
        Args:
            current_telemetry: Current telemetry data
            current_parameters: Current ECU parameters
            vehicle_profile: Vehicle profile information
            conditions: Environmental conditions (weather, altitude, etc.)
        
        Returns:
            TuningRecommendation with optimization suggestions
        """
        recommendations = []
        
        # Analyze each parameter category
        if "fuel" in current_parameters or "afr" in current_telemetry:
            fuel_rec = self._optimize_fuel(current_telemetry, current_parameters, conditions)
            if fuel_rec:
                recommendations.append(fuel_rec)
        
        if "ignition" in current_parameters or "ignition_timing" in current_telemetry:
            ignition_rec = self._optimize_ignition(current_telemetry, current_parameters, conditions)
            if ignition_rec:
                recommendations.append(ignition_rec)
        
        if "boost" in current_parameters or "boost_psi" in current_telemetry:
            boost_rec = self._optimize_boost(current_telemetry, current_parameters, conditions)
            if boost_rec:
                recommendations.append(boost_rec)
        
        # Calculate expected improvements
        power_gain, torque_gain, efficiency_gain = self._estimate_improvements(recommendations)
        
        # Overall confidence
        confidence = sum(r.confidence for r in recommendations) / len(recommendations) if recommendations else 0.0
        
        recommendation = TuningRecommendation(
            recommendations=recommendations,
            expected_power_gain=power_gain,
            expected_torque_gain=torque_gain,
            expected_efficiency_gain=efficiency_gain,
            confidence=confidence,
            reasoning=self._generate_reasoning(recommendations, conditions),
            conditions=conditions or {},
        )
        
        # Store in history
        self.optimization_history.append(recommendation)
        
        return recommendation
    
    def _optimize_fuel(
        self,
        telemetry: Dict[str, Any],
        parameters: Dict[str, float],
        conditions: Optional[Dict[str, Any]],
    ) -> Optional[OptimizationResult]:
        """Optimize fuel/AFR parameters."""
        # Input validation
        if not isinstance(telemetry, dict) or not isinstance(parameters, dict):
            LOGGER.error("Invalid input types for fuel optimization")
            return None
        
        current_afr = telemetry.get("afr", parameters.get("afr", 14.7))
        
        # Validate current AFR is reasonable
        if not isinstance(current_afr, (int, float)) or current_afr < 10 or current_afr > 20:
            LOGGER.warning("Invalid AFR value: %s", current_afr)
            return None
        
        target_afr = self._calculate_optimal_afr(telemetry, conditions)
        
        if abs(current_afr - target_afr) < 0.1:  # Already close to optimal
            return None
        
        # Check safety limits
        min_afr, max_afr = self.safety_limits.get("afr_min", (12.0, 14.7))[0], \
                          self.safety_limits.get("afr_max", (14.7, 16.0))[1]
        
        if target_afr < min_afr or target_afr > max_afr:
            LOGGER.warning("Target AFR outside safety limits: %s", target_afr)
            target_afr = max(min_afr, min(max_afr, target_afr))
        
        improvement = abs(target_afr - current_afr) / current_afr * 100
        confidence = self._calculate_confidence("fuel", telemetry, conditions)
        
        return OptimizationResult(
            parameter_name="afr_target",
            current_value=current_afr,
            optimized_value=target_afr,
            improvement_estimate=improvement,
            confidence=confidence,
            reasoning=f"Optimize AFR for {self.optimization_goal.value} - current: {current_afr:.2f}, target: {target_afr:.2f}",
            safety_check=True,
            requires_approval=self.tuning_mode != TuningMode.SAFE,
        )
    
    def _optimize_ignition(
        self,
        telemetry: Dict[str, Any],
        parameters: Dict[str, float],
        conditions: Optional[Dict[str, Any]],
    ) -> Optional[OptimizationResult]:
        """Optimize ignition timing."""
        current_timing = telemetry.get("ignition_timing", parameters.get("ignition_timing", 15.0))
        target_timing = self._calculate_optimal_timing(telemetry, conditions)
        
        if abs(current_timing - target_timing) < 0.5:  # Already close
            return None
        
        # Check safety limits
        max_advance = self.safety_limits.get("ignition_advance_max", (30.0, 50.0))[1]
        if target_timing > max_advance:
            target_timing = max_advance
        
        improvement = abs(target_timing - current_timing) / current_timing * 100 if current_timing > 0 else 0
        confidence = self._calculate_confidence("ignition", telemetry, conditions)
        
        return OptimizationResult(
            parameter_name="ignition_timing",
            current_value=current_timing,
            optimized_value=target_timing,
            improvement_estimate=improvement,
            confidence=confidence,
            reasoning=f"Optimize ignition timing for {self.optimization_goal.value}",
            safety_check=True,
            requires_approval=True,
        )
    
    def _optimize_boost(
        self,
        telemetry: Dict[str, Any],
        parameters: Dict[str, float],
        conditions: Optional[Dict[str, Any]],
    ) -> Optional[OptimizationResult]:
        """Optimize boost pressure."""
        current_boost = telemetry.get("boost_psi", parameters.get("boost_psi", 0.0))
        
        if self.optimization_goal == OptimizationGoal.MAX_POWER:
            target_boost = self._calculate_max_safe_boost(telemetry, conditions)
        else:
            target_boost = current_boost  # No change for other goals
        
        if abs(current_boost - target_boost) < 0.5:  # Already close
            return None
        
        # Check safety limits
        max_boost = self.safety_limits.get("boost_max", (15.0, 30.0))[1]
        if target_boost > max_boost:
            target_boost = max_boost
        
        improvement = (target_boost - current_boost) / current_boost * 100 if current_boost > 0 else 0
        confidence = self._calculate_confidence("boost", telemetry, conditions)
        
        return OptimizationResult(
            parameter_name="boost_target",
            current_value=current_boost,
            optimized_value=target_boost,
            improvement_estimate=improvement,
            confidence=confidence,
            reasoning=f"Optimize boost for {self.optimization_goal.value}",
            safety_check=True,
            requires_approval=True,
        )
    
    def _calculate_optimal_afr(
        self,
        telemetry: Dict[str, Any],
        conditions: Optional[Dict[str, Any]],
    ) -> float:
        """Calculate optimal AFR based on conditions and goals."""
        base_afr = 14.7  # Stoichiometric
        
        # Adjust based on optimization goal
        if self.optimization_goal == OptimizationGoal.MAX_POWER:
            base_afr = 12.8  # Rich for power
        elif self.optimization_goal == OptimizationGoal.FUEL_EFFICIENCY:
            base_afr = 15.0  # Lean for efficiency
        elif self.optimization_goal == OptimizationGoal.BALANCED:
            base_afr = 14.2  # Slightly rich
        
        # Adjust for conditions
        if conditions:
            # Altitude adjustment
            altitude = conditions.get("altitude", 0)
            if altitude > 5000:  # High altitude
                base_afr += 0.2  # Leaner at altitude
            
            # Temperature adjustment
            temp = conditions.get("temperature_f", 70)
            if temp > 90:  # Hot weather
                base_afr += 0.1  # Slightly leaner
        
        # Adjust for tuning mode
        if self.tuning_mode == TuningMode.SAFE:
            base_afr = max(13.5, base_afr)  # Conservative
        elif self.tuning_mode == TuningMode.AGGRESSIVE:
            base_afr = min(12.5, base_afr)  # More aggressive
        
        return base_afr
    
    def _calculate_optimal_timing(
        self,
        telemetry: Dict[str, Any],
        conditions: Optional[Dict[str, Any]],
    ) -> float:
        """Calculate optimal ignition timing."""
        base_timing = 20.0  # Base timing
        
        # Adjust based on goal
        if self.optimization_goal == OptimizationGoal.MAX_POWER:
            base_timing += 5.0  # More advance
        elif self.optimization_goal == OptimizationGoal.FUEL_EFFICIENCY:
            base_timing -= 2.0  # Less advance
        
        # Adjust for conditions
        if conditions:
            # Fuel octane
            octane = conditions.get("fuel_octane", 91)
            if octane >= 93:
                base_timing += 2.0  # Can run more advance
            elif octane < 87:
                base_timing -= 3.0  # Less advance for lower octane
        
        # Adjust for tuning mode
        if self.tuning_mode == TuningMode.SAFE:
            base_timing -= 3.0  # Conservative
        elif self.tuning_mode == TuningMode.AGGRESSIVE:
            base_timing += 3.0  # More aggressive
        
        return base_timing
    
    def _calculate_max_safe_boost(
        self,
        telemetry: Dict[str, Any],
        conditions: Optional[Dict[str, Any]],
    ) -> float:
        """Calculate maximum safe boost pressure."""
        base_boost = 15.0  # Base boost
        
        # Adjust based on conditions
        if conditions:
            # Altitude
            altitude = conditions.get("altitude", 0)
            if altitude > 5000:
                base_boost += 2.0  # Can run more boost at altitude
            
            # Intercooler efficiency
            iat = telemetry.get("iat", 70)
            if iat < 60:  # Cool intake
                base_boost += 1.0
        
        # Adjust for tuning mode
        if self.tuning_mode == TuningMode.SAFE:
            base_boost -= 2.0  # Conservative
        elif self.tuning_mode == TuningMode.AGGRESSIVE:
            base_boost += 3.0  # More aggressive
        
        return base_boost
    
    def _calculate_confidence(
        self,
        parameter_type: str,
        telemetry: Dict[str, Any],
        conditions: Optional[Dict[str, Any]],
    ) -> float:
        """Calculate confidence in optimization."""
        confidence = 0.7  # Base confidence
        
        # Increase confidence with more data
        if len(telemetry) > 10:
            confidence += 0.1
        
        # Decrease if conditions unknown
        if not conditions:
            confidence -= 0.1
        
        # Increase if we have historical data
        if len(self.optimization_history) > 5:
            confidence += 0.1
        
        return min(1.0, max(0.0, confidence))
    
    def _estimate_improvements(
        self,
        recommendations: List[OptimizationResult],
    ) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Estimate power, torque, and efficiency improvements."""
        if not recommendations:
            return None, None, None
        
        # Simple estimation (would be more sophisticated with ML model)
        total_improvement = sum(r.improvement_estimate for r in recommendations) / len(recommendations)
        
        if self.optimization_goal == OptimizationGoal.MAX_POWER:
            power_gain = total_improvement * 2.0  # Rough estimate
            torque_gain = total_improvement * 1.5
            efficiency_gain = None
        elif self.optimization_goal == OptimizationGoal.FUEL_EFFICIENCY:
            power_gain = None
            torque_gain = None
            efficiency_gain = total_improvement * 1.5
        else:
            power_gain = total_improvement * 1.0
            torque_gain = total_improvement * 0.8
            efficiency_gain = total_improvement * 0.5
        
        return power_gain, torque_gain, efficiency_gain
    
    def _generate_reasoning(
        self,
        recommendations: List[OptimizationResult],
        conditions: Optional[Dict[str, Any]],
    ) -> str:
        """Generate human-readable reasoning for recommendations."""
        reasoning_parts = []
        
        reasoning_parts.append(f"Optimization goal: {self.optimization_goal.value}")
        reasoning_parts.append(f"Tuning mode: {self.tuning_mode.value}")
        
        if conditions:
            if "altitude" in conditions:
                reasoning_parts.append(f"Altitude: {conditions['altitude']}ft")
            if "temperature_f" in conditions:
                reasoning_parts.append(f"Temperature: {conditions['temperature_f']}°F")
        
        reasoning_parts.append(f"Generated {len(recommendations)} optimization recommendations")
        
        return ". ".join(reasoning_parts)
    
    def learn_from_feedback(
        self,
        recommendation: TuningRecommendation,
        user_feedback: Dict[str, Any],
    ) -> None:
        """
        Learn from user feedback to improve future recommendations.
        
        Args:
            recommendation: The recommendation that was applied
            user_feedback: User feedback (approved, rejected, results, etc.)
        """
        if not self.learning_enabled:
            return
        
        feedback_entry = {
            "recommendation": recommendation,
            "feedback": user_feedback,
            "timestamp": time.time(),
        }
        
        self.user_feedback.append(feedback_entry)
        
        # Keep only recent feedback (last 100)
        if len(self.user_feedback) > 100:
            self.user_feedback.pop(0)
        
        LOGGER.info("Learned from user feedback: %s", user_feedback)
    
    def set_tuning_mode(self, mode: TuningMode) -> None:
        """Set tuning optimization mode."""
        self.tuning_mode = mode
        LOGGER.info("Tuning mode set to: %s", mode.value)
    
    def set_optimization_goal(self, goal: OptimizationGoal) -> None:
        """Set optimization goal."""
        self.optimization_goal = goal
        LOGGER.info("Optimization goal set to: %s", goal.value)


