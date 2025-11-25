"""
AI-Driven Tuning Recommendations

Algorithms that suggest specific tuning adjustments based on user goals,
current telemetry, and vehicle modifications.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any

LOGGER = logging.getLogger(__name__)


class TuningGoal(Enum):
    """Tuning goals."""
    MAX_POWER = "max_power"
    MAX_TORQUE = "max_torque"
    FUEL_EFFICIENCY = "fuel_efficiency"
    BALANCED = "balanced"
    SAFETY = "safety"
    RESPONSIVENESS = "responsiveness"


@dataclass
class TuningRecommendation:
    """Tuning recommendation."""
    recommendation_id: str
    parameter: str  # "fuel", "timing", "boost", etc.
    current_value: Any
    recommended_value: Any
    change_amount: Any
    goal: TuningGoal
    confidence: float  # 0-1
    reasoning: str
    expected_impact: Dict[str, Any]  # Expected HP gain, etc.
    safety_notes: str = ""
    prerequisites: List[str] = field(default_factory=list)


@dataclass
class TuningScenario:
    """What-if scenario for tuning changes."""
    scenario_id: str
    name: str
    description: str
    changes: Dict[str, Any]  # Proposed changes
    current_state: Dict[str, Any]  # Current vehicle state
    predicted_results: Dict[str, Any]  # Predicted outcomes
    confidence: float
    risks: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)


class AITuningRecommendations:
    """
    AI-driven tuning recommendation engine.
    
    Features:
    - Goal-based recommendations
    - Telemetry-aware suggestions
    - Safety-first approach
    - What-if scenario simulation
    - Multi-parameter optimization
    """
    
    def __init__(self):
        """Initialize AI tuning recommendations engine."""
        self.recommendation_history: List[TuningRecommendation] = []
        self.scenarios: Dict[str, TuningScenario] = {}
    
    def generate_recommendations(
        self,
        goal: TuningGoal,
        current_telemetry: Dict[str, float],
        vehicle_specs: Optional[Dict[str, Any]] = None,
        modifications: Optional[List[str]] = None
    ) -> List[TuningRecommendation]:
        """
        Generate tuning recommendations based on goal.
        
        Args:
            goal: Tuning goal
            current_telemetry: Current telemetry data
            vehicle_specs: Vehicle specifications
            modifications: List of modifications
        
        Returns:
            List of tuning recommendations
        """
        recommendations = []
        
        if goal == TuningGoal.MAX_POWER:
            recommendations.extend(self._recommend_for_power(current_telemetry, vehicle_specs, modifications))
        elif goal == TuningGoal.MAX_TORQUE:
            recommendations.extend(self._recommend_for_torque(current_telemetry, vehicle_specs, modifications))
        elif goal == TuningGoal.FUEL_EFFICIENCY:
            recommendations.extend(self._recommend_for_efficiency(current_telemetry, vehicle_specs))
        elif goal == TuningGoal.BALANCED:
            recommendations.extend(self._recommend_balanced(current_telemetry, vehicle_specs, modifications))
        elif goal == TuningGoal.SAFETY:
            recommendations.extend(self._recommend_for_safety(current_telemetry, vehicle_specs))
        elif goal == TuningGoal.RESPONSIVENESS:
            recommendations.extend(self._recommend_for_responsiveness(current_telemetry, vehicle_specs))
        
        # Sort by confidence and expected impact
        recommendations.sort(key=lambda r: (r.confidence, r.expected_impact.get("hp_gain", 0)), reverse=True)
        
        return recommendations
    
    def simulate_scenario(
        self,
        name: str,
        description: str,
        proposed_changes: Dict[str, Any],
        current_state: Dict[str, Any],
        vehicle_specs: Optional[Dict[str, Any]] = None
    ) -> TuningScenario:
        """
        Simulate what-if scenario.
        
        Args:
            name: Scenario name
            description: Scenario description
            proposed_changes: Proposed tuning changes
            current_state: Current vehicle state
            vehicle_specs: Vehicle specifications
        
        Returns:
            Tuning scenario with predictions
        """
        scenario_id = f"scenario_{len(self.scenarios)}"
        
        # Predict results
        predicted_results = self._predict_changes(proposed_changes, current_state, vehicle_specs)
        
        # Assess risks and benefits
        risks = self._assess_risks(proposed_changes, current_state)
        benefits = self._assess_benefits(proposed_changes, predicted_results)
        
        # Calculate confidence
        confidence = self._calculate_scenario_confidence(proposed_changes, current_state)
        
        scenario = TuningScenario(
            scenario_id=scenario_id,
            name=name,
            description=description,
            changes=proposed_changes,
            current_state=current_state,
            predicted_results=predicted_results,
            confidence=confidence,
            risks=risks,
            benefits=benefits,
        )
        
        self.scenarios[scenario_id] = scenario
        return scenario
    
    def _recommend_for_power(
        self,
        telemetry: Dict[str, float],
        specs: Optional[Dict[str, Any]],
        modifications: Optional[List[str]]
    ) -> List[TuningRecommendation]:
        """Generate recommendations for maximum power."""
        recommendations = []
        
        # Check current AFR
        afr = telemetry.get("lambda", 1.0) * 14.7
        if afr > 13.0:  # Too lean for power
            recommendations.append(TuningRecommendation(
                recommendation_id="power_fuel_1",
                parameter="fuel",
                current_value=afr,
                recommended_value=12.5,
                change_amount=-0.5,
                goal=TuningGoal.MAX_POWER,
                confidence=0.8,
                reasoning="Rich AFR (12.5:1) provides better power and safety margin",
                expected_impact={"hp_gain": 5, "safety_improvement": True},
                safety_notes="Richer mixture reduces knock risk",
            ))
        
        # Check timing
        timing = telemetry.get("timing", 0.0)
        if timing < 25 and telemetry.get("knock_count", 0) == 0:
            recommendations.append(TuningRecommendation(
                recommendation_id="power_timing_1",
                parameter="timing",
                current_value=timing,
                recommended_value=timing + 2.0,
                change_amount=2.0,
                goal=TuningGoal.MAX_POWER,
                confidence=0.7,
                reasoning="Slight timing advance can increase power if no knock",
                expected_impact={"hp_gain": 3, "torque_gain": 5},
                safety_notes="Monitor knock sensor closely",
                prerequisites=["knock_sensor_active"],
            ))
        
        # Check boost
        boost = telemetry.get("boost_psi", 0.0)
        if boost < 15 and telemetry.get("egt", 0.0) < 850:
            recommendations.append(TuningRecommendation(
                recommendation_id="power_boost_1",
                parameter="boost",
                current_value=boost,
                recommended_value=boost + 2.0,
                change_amount=2.0,
                goal=TuningGoal.MAX_POWER,
                confidence=0.6,
                reasoning="Increasing boost can increase power if fuel/timing adjusted",
                expected_impact={"hp_gain": 15, "requires_fuel_adjustment": True},
                safety_notes="Must increase fuel proportionally, monitor EGT",
                prerequisites=["fuel_enrichment", "egt_monitoring"],
            ))
        
        return recommendations
    
    def _recommend_for_torque(
        self,
        telemetry: Dict[str, float],
        specs: Optional[Dict[str, Any]],
        modifications: Optional[List[str]]
    ) -> List[TuningRecommendation]:
        """Generate recommendations for maximum torque."""
        recommendations = []
        
        # Torque optimization typically involves:
        # - Lower RPM tuning
        # - More aggressive timing at low RPM
        # - Better fuel delivery at low load
        
        timing = telemetry.get("timing", 0.0)
        rpm = telemetry.get("rpm", 0.0)
        
        if rpm < 4000 and timing < 30:
            recommendations.append(TuningRecommendation(
                recommendation_id="torque_timing_1",
                parameter="timing",
                current_value=timing,
                recommended_value=timing + 3.0,
                change_amount=3.0,
                goal=TuningGoal.MAX_TORQUE,
                confidence=0.7,
                reasoning="More timing advance at low RPM increases torque",
                expected_impact={"torque_gain": 10, "hp_gain": 2},
                safety_notes="Only at low RPM, reduce at high RPM",
            ))
        
        return recommendations
    
    def _recommend_for_efficiency(
        self,
        telemetry: Dict[str, float],
        specs: Optional[Dict[str, Any]]
    ) -> List[TuningRecommendation]:
        """Generate recommendations for fuel efficiency."""
        recommendations = []
        
        # Efficiency: Leaner AFR, more timing advance at cruise
        afr = telemetry.get("lambda", 1.0) * 14.7
        load = telemetry.get("load", 0.0)
        
        if load < 0.5 and afr < 14.5:  # Cruise conditions
            recommendations.append(TuningRecommendation(
                recommendation_id="efficiency_fuel_1",
                parameter="fuel",
                current_value=afr,
                recommended_value=14.7,
                change_amount=0.2,
                goal=TuningGoal.FUEL_EFFICIENCY,
                confidence=0.8,
                reasoning="Leaner AFR at cruise improves efficiency",
                expected_impact={"mpg_improvement": 5, "hp_loss": -2},
                safety_notes="Only at low load, not at WOT",
            ))
        
        return recommendations
    
    def _recommend_balanced(
        self,
        telemetry: Dict[str, float],
        specs: Optional[Dict[str, Any]],
        modifications: Optional[List[str]]
    ) -> List[TuningRecommendation]:
        """Generate balanced recommendations."""
        # Combine power and efficiency recommendations
        power_recs = self._recommend_for_power(telemetry, specs, modifications)
        efficiency_recs = self._recommend_for_efficiency(telemetry, specs)
        
        # Filter for balanced approach
        balanced = []
        for rec in power_recs + efficiency_recs:
            if rec.confidence > 0.6:
                rec.goal = TuningGoal.BALANCED
                balanced.append(rec)
        
        return balanced
    
    def _recommend_for_safety(
        self,
        telemetry: Dict[str, float],
        specs: Optional[Dict[str, Any]]
    ) -> List[TuningRecommendation]:
        """Generate safety-focused recommendations."""
        recommendations = []
        
        # Check for safety issues
        knock_count = telemetry.get("knock_count", 0)
        egt = telemetry.get("egt", 0.0)
        afr = telemetry.get("lambda", 1.0) * 14.7
        
        if knock_count > 0:
            timing = telemetry.get("timing", 0.0)
            recommendations.append(TuningRecommendation(
                recommendation_id="safety_timing_1",
                parameter="timing",
                current_value=timing,
                recommended_value=timing - 2.0,
                change_amount=-2.0,
                goal=TuningGoal.SAFETY,
                confidence=0.9,
                reasoning="Knock detected, reduce timing for safety",
                expected_impact={"hp_loss": -5, "safety_improvement": True},
                safety_notes="Critical: Knock can cause engine damage",
            ))
        
        if egt > 900:
            recommendations.append(TuningRecommendation(
                recommendation_id="safety_fuel_1",
                parameter="fuel",
                current_value=afr,
                recommended_value=12.0,
                change_amount=-2.0,
                goal=TuningGoal.SAFETY,
                confidence=0.9,
                reasoning="High EGT, richen mixture to cool",
                expected_impact={"egt_reduction": 50, "hp_loss": -3},
                safety_notes="High EGT can damage engine",
            ))
        
        return recommendations
    
    def _recommend_for_responsiveness(
        self,
        telemetry: Dict[str, float],
        specs: Optional[Dict[str, Any]]
    ) -> List[TuningRecommendation]:
        """Generate recommendations for responsiveness."""
        recommendations = []
        
        # Responsiveness: Better throttle response, less lag
        # Typically involves: better fuel delivery, timing advance, boost response
        
        timing = telemetry.get("timing", 0.0)
        tps = telemetry.get("throttle", 0.0)
        
        if tps > 0.5 and timing < 28:  # Part throttle
            recommendations.append(TuningRecommendation(
                recommendation_id="response_timing_1",
                parameter="timing",
                current_value=timing,
                recommended_value=timing + 1.5,
                change_amount=1.5,
                goal=TuningGoal.RESPONSIVENESS,
                confidence=0.7,
                reasoning="More timing at part throttle improves response",
                expected_impact={"throttle_response": "improved"},
            ))
        
        return recommendations
    
    def _predict_changes(
        self,
        changes: Dict[str, Any],
        current_state: Dict[str, Any],
        specs: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Predict results of tuning changes."""
        predictions = {}
        
        # Simple heuristic predictions
        if "fuel" in changes:
            fuel_change = changes["fuel"]
            # Richer = more power, less efficiency
            if fuel_change < 0:  # Richer
                predictions["hp_gain"] = abs(fuel_change) * 2
                predictions["mpg_loss"] = abs(fuel_change) * 1
            else:  # Leaner
                predictions["hp_loss"] = fuel_change * 1
                predictions["mpg_gain"] = fuel_change * 2
        
        if "timing" in changes:
            timing_change = changes["timing"]
            if timing_change > 0:  # More advance
                predictions["hp_gain"] = predictions.get("hp_gain", 0) + timing_change * 1.5
                predictions["knock_risk"] = "increased"
            else:  # Less advance
                predictions["hp_loss"] = predictions.get("hp_loss", 0) + abs(timing_change) * 1.5
                predictions["knock_risk"] = "decreased"
        
        if "boost" in changes:
            boost_change = changes["boost"]
            if boost_change > 0:
                predictions["hp_gain"] = predictions.get("hp_gain", 0) + boost_change * 8
                predictions["egt_increase"] = boost_change * 20
                predictions["requires_fuel"] = True
        
        return predictions
    
    def _assess_risks(
        self,
        changes: Dict[str, Any],
        current_state: Dict[str, Any]
    ) -> List[str]:
        """Assess risks of proposed changes."""
        risks = []
        
        if "timing" in changes and changes["timing"] > 0:
            risks.append("Increased knock risk - monitor knock sensor")
        
        if "boost" in changes and changes["boost"] > 0:
            risks.append("Higher boost increases EGT and stress")
            risks.append("Requires fuel enrichment to prevent lean condition")
        
        if "fuel" in changes and changes["fuel"] < 0:  # Richer
            risks.append("Richer mixture may foul spark plugs over time")
        
        return risks
    
    def _assess_benefits(
        self,
        changes: Dict[str, Any],
        predicted_results: Dict[str, Any]
    ) -> List[str]:
        """Assess benefits of proposed changes."""
        benefits = []
        
        if predicted_results.get("hp_gain", 0) > 0:
            benefits.append(f"Expected {predicted_results['hp_gain']} HP gain")
        
        if predicted_results.get("torque_gain", 0) > 0:
            benefits.append(f"Expected {predicted_results['torque_gain']} lb-ft torque gain")
        
        if predicted_results.get("mpg_gain", 0) > 0:
            benefits.append(f"Expected {predicted_results['mpg_gain']}% fuel economy improvement")
        
        if predicted_results.get("safety_improvement"):
            benefits.append("Improves safety margins")
        
        return benefits
    
    def _calculate_scenario_confidence(
        self,
        changes: Dict[str, Any],
        current_state: Dict[str, Any]
    ) -> float:
        """Calculate confidence in scenario predictions."""
        # Base confidence
        confidence = 0.7
        
        # Reduce confidence for large changes
        for param, change in changes.items():
            if isinstance(change, (int, float)):
                if abs(change) > 10:
                    confidence -= 0.1
                if abs(change) > 20:
                    confidence -= 0.1
        
        # Increase confidence if we have good current state data
        if len(current_state) > 5:
            confidence += 0.1
        
        return max(0.3, min(1.0, confidence))


__all__ = [
    "AITuningRecommendations",
    "TuningGoal",
    "TuningRecommendation",
    "TuningScenario",
]









