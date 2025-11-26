"""
Contextual Tuning Suggestions
Provides specific, actionable tuning recommendations with exact values and trade-offs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

LOGGER = logging.getLogger(__name__)


@dataclass
class TuningSuggestion:
    """A specific tuning suggestion with exact values."""
    parameter: str
    current_value: Optional[float]
    suggested_value: float
    change_amount: float
    unit: str
    reason: str
    expected_benefit: str
    trade_offs: List[str] = field(default_factory=list)
    confidence: float = 0.8
    priority: str = "medium"  # "low", "medium", "high", "critical"
    prerequisites: List[str] = field(default_factory=list)


class ContextualTuningSuggestions:
    """
    Generates contextual, specific tuning suggestions based on current state.
    
    Features:
    - Specific values (e.g., "Increase rear wing angle by 2 degrees")
    - Trade-off explanations
    - Context-aware recommendations
    - Priority-based suggestions
    """
    
    def __init__(self):
        """Initialize tuning suggestion engine."""
        self.suggestion_history: List[TuningSuggestion] = []
    
    def generate_suggestions(
        self,
        telemetry: Dict[str, float],
        current_setup: Optional[Dict[str, float]] = None,
        goal: str = "balanced",  # "power", "efficiency", "stability", "balanced"
        context: Optional[str] = None
    ) -> List[TuningSuggestion]:
        """
        Generate contextual tuning suggestions.
        
        Args:
            telemetry: Current telemetry data
            current_setup: Current vehicle setup (boost, timing, etc.)
            goal: Tuning goal
            context: Additional context (e.g., "high speed corner instability")
            
        Returns:
            List of specific tuning suggestions
        """
        suggestions = []
        
        try:
            # Validate inputs
            if not telemetry or not isinstance(telemetry, dict):
                LOGGER.warning("Invalid telemetry data provided to suggestion engine")
                return suggestions
            
            if current_setup is not None and not isinstance(current_setup, dict):
                LOGGER.warning("Invalid current_setup provided, using None")
                current_setup = None
            
            # Analyze telemetry and generate suggestions with error handling
            try:
                suggestions.extend(self._analyze_boost_suggestions(telemetry, current_setup, goal))
            except Exception as e:
                LOGGER.error("Error generating boost suggestions: %s", e, exc_info=True)
            
            try:
                suggestions.extend(self._analyze_timing_suggestions(telemetry, current_setup, goal))
            except Exception as e:
                LOGGER.error("Error generating timing suggestions: %s", e, exc_info=True)
            
            try:
                suggestions.extend(self._analyze_fuel_suggestions(telemetry, current_setup, goal))
            except Exception as e:
                LOGGER.error("Error generating fuel suggestions: %s", e, exc_info=True)
            
            try:
                suggestions.extend(self._analyze_handling_suggestions(telemetry, current_setup, goal, context))
            except Exception as e:
                LOGGER.error("Error generating handling suggestions: %s", e, exc_info=True)
            
            # Sort by priority
            priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            suggestions.sort(key=lambda x: (priority_order.get(x.priority, 3), -x.confidence))
            
            LOGGER.debug("Generated %d tuning suggestions for goal: %s", len(suggestions), goal)
            
        except Exception as e:
            LOGGER.error("Critical error generating suggestions: %s", e, exc_info=True)
        
        return suggestions
    
    def _analyze_boost_suggestions(
        self,
        telemetry: Dict[str, float],
        current_setup: Optional[Dict[str, float]],
        goal: str
    ) -> List[TuningSuggestion]:
        """Generate boost-related suggestions."""
        suggestions = []
        
        try:
            # Safely extract values with defaults
            boost = float(telemetry.get("Boost_Pressure", 0) or 0)
            afr = float(telemetry.get("AFR", 14.7) or 14.7)
            timing = float(telemetry.get("Timing_Advance", 20) or 20)
            egt = float(telemetry.get("EGT", 700) or 700)
            fuel_pressure = float(telemetry.get("Fuel_Pressure", 50) or 50)
            knock_count = int(telemetry.get("Knock_Count", 0) or 0)
            
            current_boost_target = float(current_setup.get("boost_target", boost) or boost) if current_setup else boost
            
            # Safety checks first
            if fuel_pressure < 40 and boost > 15:
                suggestions.append(TuningSuggestion(
                    parameter="Boost Target",
                    current_value=current_boost_target,
                    suggested_value=max(5, current_boost_target - 3),
                    change_amount=-3,
                    unit="PSI",
                    reason=f"Fuel pressure ({fuel_pressure:.1f} PSI) is insufficient for current boost",
                    expected_benefit="Prevents lean condition and engine damage",
                    trade_offs=["Reduces peak power"],
                    confidence=0.95,
                    priority="critical",
                    prerequisites=["Fix fuel system first"]
                ))
            
            if knock_count > 0 and boost > 15:
                suggestions.append(TuningSuggestion(
                    parameter="Boost Target",
                    current_value=current_boost_target,
                    suggested_value=max(10, current_boost_target - 2),
                    change_amount=-2,
                    unit="PSI",
                    reason=f"Knock detected ({knock_count} counts) at current boost level",
                    expected_benefit="Eliminates knock and prevents engine damage",
                    trade_offs=["Reduces power by ~10-15 HP"],
                    confidence=0.9,
                    priority="critical"
                ))
            
            # Performance optimization
            if goal == "power" and boost < 20 and afr < 13.5 and timing < 25 and fuel_pressure > 45:
                safe_increase = min(3, 20 - boost)
                if safe_increase > 0:
                    suggestions.append(TuningSuggestion(
                        parameter="Boost Target",
                        current_value=current_boost_target,
                        suggested_value=current_boost_target + safe_increase,
                        change_amount=safe_increase,
                        unit="PSI",
                        reason="Safe conditions for power increase: good AFR, timing, and fuel pressure",
                        expected_benefit=f"Increase power by ~{int(safe_increase * 8)}-{int(safe_increase * 12)} HP",
                        trade_offs=["Increases heat and stress", "May need richer AFR", "Monitor EGT closely"],
                        confidence=0.75,
                        priority="medium",
                        prerequisites=["Monitor AFR and EGT", "Ensure fuel pressure stays >45 PSI"]
                    ))
        
        except (ValueError, TypeError, KeyError) as e:
            LOGGER.error("Error extracting boost analysis values: %s", e)
        except Exception as e:
            LOGGER.error("Unexpected error in boost suggestions: %s", e, exc_info=True)
        
        return suggestions
    
    def _analyze_timing_suggestions(
        self,
        telemetry: Dict[str, float],
        current_setup: Optional[Dict[str, float]],
        goal: str
    ) -> List[TuningSuggestion]:
        """Generate timing-related suggestions."""
        suggestions = []
        
        timing = telemetry.get("Timing_Advance", 20)
        boost = telemetry.get("Boost_Pressure", 0)
        afr = telemetry.get("AFR", 14.7)
        egt = telemetry.get("EGT", 700)
        knock_count = telemetry.get("Knock_Count", 0)
        iat = telemetry.get("Intake_Air_Temp", 25)
        
        current_timing = current_setup.get("timing_advance", timing) if current_setup else timing
        
        # Safety: Reduce timing if knock
        if knock_count > 0:
            reduction = min(3, knock_count)
            suggestions.append(TuningSuggestion(
                parameter="Ignition Timing",
                current_value=current_timing,
                suggested_value=current_timing - reduction,
                change_amount=-reduction,
                unit="degrees",
                reason=f"Knock detected ({knock_count} counts). Timing too advanced.",
                expected_benefit="Eliminates knock and prevents engine damage",
                trade_offs=["May reduce power by 2-5 HP"],
                confidence=0.95,
                priority="critical"
            ))
        
        # Safety: Reduce timing if high boost + high IAT
        if boost > 18 and iat > 50 and timing > 22:
            suggestions.append(TuningSuggestion(
                parameter="Ignition Timing",
                current_value=current_timing,
                suggested_value=current_timing - 2,
                change_amount=-2,
                unit="degrees",
                reason=f"High boost ({boost:.1f} PSI) + hot intake air ({iat:.1f}°C) increases knock risk",
                expected_benefit="Reduces knock risk and prevents engine damage",
                trade_offs=["Slight power reduction (~3-5 HP)"],
                confidence=0.85,
                priority="high"
            ))
        
        # Optimization: Advance timing if safe
        if goal == "power" and knock_count == 0 and boost < 15 and timing < 28 and egt < 850:
            safe_advance = min(2, 28 - timing)
            if safe_advance > 0:
                suggestions.append(TuningSuggestion(
                    parameter="Ignition Timing",
                    current_value=current_timing,
                    suggested_value=current_timing + safe_advance,
                    change_amount=safe_advance,
                    unit="degrees",
                    reason="Safe conditions for timing advance: no knock, moderate boost, good EGT",
                    expected_benefit=f"Increase power by ~{int(safe_advance * 2)}-{int(safe_advance * 4)} HP and improve throttle response",
                    trade_offs=["Increases knock risk", "Monitor knock sensor closely"],
                    confidence=0.7,
                    priority="medium",
                    prerequisites=["Monitor knock sensor", "Test incrementally"]
                ))
        
        return suggestions
    
    def _analyze_fuel_suggestions(
        self,
        telemetry: Dict[str, float],
        current_setup: Optional[Dict[str, float]],
        goal: str
    ) -> List[TuningSuggestion]:
        """Generate fuel-related suggestions."""
        suggestions = []
        
        afr = telemetry.get("AFR", 14.7)
        lambda_val = telemetry.get("Lambda", 1.0)
        boost = telemetry.get("Boost_Pressure", 0)
        egt = telemetry.get("EGT", 700)
        
        # Use lambda if available, otherwise convert AFR
        if lambda_val > 0 and lambda_val < 2:
            current_afr = lambda_val * 14.7
        else:
            current_afr = afr
        
        # Safety: Enrich if lean under boost
        if boost > 15 and current_afr > 13.5:
            target_afr = 12.8
            ve_increase = ((current_afr - target_afr) / target_afr) * 100
            suggestions.append(TuningSuggestion(
                parameter="VE Table (Fuel)",
                current_value=None,
                suggested_value=ve_increase,
                change_amount=ve_increase,
                unit="% increase",
                reason=f"AFR is {current_afr:.2f}:1 (lean) under {boost:.1f} PSI boost. Dangerous condition.",
                expected_benefit="Prevents lean condition, reduces EGT, prevents engine damage",
                trade_offs=["Slightly reduces fuel economy", "May need to adjust timing"],
                confidence=0.95,
                priority="critical",
                prerequisites=["Use wideband O2 sensor for feedback"]
            ))
        
        # Optimization: Fine-tune AFR for power
        if goal == "power" and boost > 10 and 12.5 < current_afr < 13.5:
            if current_afr > 13.0:
                target_afr = 12.8
                ve_increase = ((current_afr - target_afr) / target_afr) * 100
                suggestions.append(TuningSuggestion(
                    parameter="VE Table (Fuel)",
                    current_value=None,
                    suggested_value=ve_increase,
                    change_amount=ve_increase,
                    unit="% increase",
                    reason=f"AFR {current_afr:.2f}:1 is slightly lean for maximum power",
                    expected_benefit="Optimizes power output (target 12.8:1 for WOT)",
                    trade_offs=["Slight fuel economy reduction"],
                    confidence=0.75,
                    priority="low"
                ))
        
        # Safety: Check EGT
        if egt > 850 and current_afr > 13.0:
            target_afr = 12.5
            ve_increase = ((current_afr - target_afr) / target_afr) * 100
            suggestions.append(TuningSuggestion(
                parameter="VE Table (Fuel)",
                current_value=None,
                suggested_value=ve_increase,
                change_amount=ve_increase,
                unit="% increase",
                reason=f"High EGT ({egt:.0f}°C) with lean AFR ({current_afr:.2f}:1)",
                expected_benefit="Reduces EGT and prevents exhaust valve damage",
                trade_offs=["Reduces fuel economy"],
                confidence=0.9,
                priority="high"
            ))
        
        return suggestions
    
    def _analyze_handling_suggestions(
        self,
        telemetry: Dict[str, float],
        current_setup: Optional[Dict[str, float]],
        goal: str,
        context: Optional[str]
    ) -> List[TuningSuggestion]:
        """Generate handling-related suggestions."""
        suggestions = []
        
        if not context:
            return suggestions
        
        context_lower = context.lower()
        
        # High-speed corner instability
        if "unstable" in context_lower or "oversteer" in context_lower or "loose" in context_lower:
            if "high speed" in context_lower or "fast corner" in context_lower:
                suggestions.append(TuningSuggestion(
                    parameter="Rear Wing Angle",
                    current_value=current_setup.get("rear_wing_angle", 0) if current_setup else None,
                    suggested_value=2,
                    change_amount=2,
                    unit="degrees",
                    reason="High-speed corner instability indicates need for more rear downforce",
                    expected_benefit="Increases rear downforce, improves stability in fast corners",
                    trade_offs=["Increases drag (slight top speed reduction)", "May reduce front grip slightly"],
                    confidence=0.8,
                    priority="high"
                ))
            
            if "low speed" in context_lower or "tight corner" in context_lower:
                suggestions.append(TuningSuggestion(
                    parameter="Rear Sway Bar",
                    current_value=current_setup.get("rear_sway_bar", 0) if current_setup else None,
                    suggested_value=-1,
                    change_amount=-1,
                    unit="setting (softer)",
                    reason="Low-speed oversteer indicates rear is too stiff",
                    expected_benefit="Improves rear grip in tight corners, reduces snap oversteer",
                    trade_offs=["May reduce high-speed stability"],
                    confidence=0.75,
                    priority="medium"
                ))
        
        # Understeer
        if "understeer" in context_lower or "push" in context_lower:
            suggestions.append(TuningSuggestion(
                parameter="Front Sway Bar",
                current_value=current_setup.get("front_sway_bar", 0) if current_setup else None,
                suggested_value=-1,
                change_amount=-1,
                unit="setting (softer)",
                reason="Understeer indicates front end is too stiff or lacks grip",
                expected_benefit="Improves front grip and turn-in response",
                trade_offs=["May increase oversteer tendency"],
                confidence=0.8,
                priority="medium"
            ))
        
        return suggestions
    
    def format_suggestion(self, suggestion: TuningSuggestion) -> str:
        """Format a suggestion as a readable string."""
        parts = []
        
        # Header
        priority_icon = "🔴" if suggestion.priority == "critical" else "⚠️" if suggestion.priority == "high" else "💡"
        parts.append(f"{priority_icon} {suggestion.parameter}")
        
        # Current and suggested values
        if suggestion.current_value is not None:
            parts.append(f"   Current: {suggestion.current_value:.2f} {suggestion.unit}")
        if suggestion.change_amount > 0:
            parts.append(f"   Suggested: {suggestion.current_value + suggestion.change_amount:.2f} {suggestion.unit} (+{suggestion.change_amount:.2f} {suggestion.unit})")
        else:
            parts.append(f"   Suggested: {suggestion.suggested_value:.2f} {suggestion.unit} ({suggestion.change_amount:.2f} {suggestion.unit})")
        
        # Reason
        parts.append(f"   Reason: {suggestion.reason}")
        
        # Expected benefit
        parts.append(f"   Expected: {suggestion.expected_benefit}")
        
        # Trade-offs
        if suggestion.trade_offs:
            parts.append(f"   Trade-offs: {', '.join(suggestion.trade_offs)}")
        
        # Prerequisites
        if suggestion.prerequisites:
            parts.append(f"   Prerequisites: {', '.join(suggestion.prerequisites)}")
        
        return "\n".join(parts)


__all__ = ["ContextualTuningSuggestions", "TuningSuggestion"]

