"""
Expert Telemetry Analyzer
Provides deep, real-time analysis of telemetry data with actionable insights.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any

LOGGER = logging.getLogger(__name__)


class AnalysisType(Enum):
    """Types of telemetry analysis."""
    ANOMALY_DETECTION = "anomaly"
    PERFORMANCE_TREND = "trend"
    CORRELATION_ANALYSIS = "correlation"
    PREDICTIVE_WARNING = "predictive"
    ROOT_CAUSE = "root_cause"


@dataclass
class TelemetryInsight:
    """A single insight from telemetry analysis."""
    insight_type: AnalysisType
    title: str
    description: str
    severity: str  # "info", "warning", "critical"
    confidence: float  # 0.0 to 1.0
    affected_parameters: List[str] = field(default_factory=list)
    recommended_action: Optional[str] = None
    expected_impact: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class TelemetryPattern:
    """A detected pattern in telemetry data."""
    pattern_type: str  # "oscillation", "trend", "spike", "correlation"
    parameters: List[str]
    description: str
    significance: float  # 0.0 to 1.0
    detected_at: float = field(default_factory=time.time)


class ExpertTelemetryAnalyzer:
    """
    Expert-level telemetry analysis with deep insights.
    
    Features:
    - Real-time anomaly detection
    - Performance trend analysis
    - Cross-parameter correlation
    - Predictive warnings
    - Root cause identification
    """
    
    def __init__(self, history_window: int = 100):
        """
        Initialize analyzer.
        
        Args:
            history_window: Number of samples to keep in history
        """
        self.history_window = history_window
        self.telemetry_history: List[Dict[str, float]] = []
        self.patterns: List[TelemetryPattern] = []
        
        # Normal operating ranges (can be customized per vehicle)
        self.normal_ranges = {
            "RPM": (500, 8000),
            "Boost_Pressure": (0, 30),  # PSI
            "AFR": (12.0, 15.0),
            "Lambda": (0.8, 1.1),
            "Coolant_Temp": (80, 110),  # Celsius
            "Oil_Pressure": (30, 80),  # PSI
            "Fuel_Pressure": (35, 60),  # PSI
            "EGT": (600, 900),  # Celsius
            "Timing_Advance": (10, 35),  # Degrees
            "Throttle_Position": (0, 100),  # Percent
        }
    
    def analyze(self, current_telemetry: Dict[str, float]) -> List[TelemetryInsight]:
        """
        Perform comprehensive analysis of current telemetry.
        
        Args:
            current_telemetry: Current telemetry data
            
        Returns:
            List of insights
        """
        insights = []
        
        # Add to history
        self.telemetry_history.append(current_telemetry.copy())
        if len(self.telemetry_history) > self.history_window:
            self.telemetry_history.pop(0)
        
        # Run various analyses
        insights.extend(self._detect_anomalies(current_telemetry))
        insights.extend(self._analyze_trends())
        insights.extend(self._analyze_correlations(current_telemetry))
        insights.extend(self._predictive_warnings(current_telemetry))
        
        return insights
    
    def _detect_anomalies(self, telemetry: Dict[str, float]) -> List[TelemetryInsight]:
        """Detect anomalies in current telemetry."""
        insights = []
        
        for param, (min_val, max_val) in self.normal_ranges.items():
            value = telemetry.get(param)
            if value is None:
                continue
            
            # Check if out of normal range
            if value < min_val or value > max_val:
                severity = "critical" if abs(value - (min_val + max_val) / 2) > (max_val - min_val) * 0.5 else "warning"
                
                if value < min_val:
                    description = f"{param} is {value:.1f}, which is below normal range ({min_val}-{max_val})"
                    recommended = self._get_recommendation_for_low_value(param, value, min_val)
                else:
                    description = f"{param} is {value:.1f}, which is above normal range ({min_val}-{max_val})"
                    recommended = self._get_recommendation_for_high_value(param, value, max_val)
                
                insights.append(TelemetryInsight(
                    insight_type=AnalysisType.ANOMALY_DETECTION,
                    title=f"Anomalous {param}",
                    description=description,
                    severity=severity,
                    confidence=0.9,
                    affected_parameters=[param],
                    recommended_action=recommended,
                ))
        
        # Check for rapid changes (spikes)
        if len(self.telemetry_history) >= 3:
            for param in ["Boost_Pressure", "AFR", "RPM"]:
                if param not in telemetry:
                    continue
                
                recent_values = [t.get(param, 0) for t in self.telemetry_history[-3:]]
                if len(recent_values) == 3:
                    change_rate = abs(recent_values[2] - recent_values[0]) / max(abs(recent_values[0]), 0.1)
                    if change_rate > 0.3:  # 30% change in 2 samples
                        insights.append(TelemetryInsight(
                            insight_type=AnalysisType.ANOMALY_DETECTION,
                            title=f"Rapid {param} Change",
                            description=f"{param} changed by {change_rate*100:.1f}% rapidly",
                            severity="warning",
                            confidence=0.8,
                            affected_parameters=[param],
                            recommended_action=f"Investigate cause of rapid {param} change",
                        ))
        
        return insights
    
    def _analyze_trends(self) -> List[TelemetryInsight]:
        """Analyze trends in telemetry history."""
        insights = []
        
        if len(self.telemetry_history) < 10:
            return insights  # Need enough data
        
        # Analyze trends for key parameters
        for param in ["Coolant_Temp", "EGT", "Boost_Pressure", "AFR"]:
            values = [t.get(param) for t in self.telemetry_history if param in t]
            if len(values) < 10:
                continue
            
            # Simple trend detection (increasing/decreasing)
            recent_avg = sum(values[-5:]) / 5
            earlier_avg = sum(values[:5]) / 5
            
            if recent_avg > earlier_avg * 1.1:  # 10% increase
                insights.append(TelemetryInsight(
                    insight_type=AnalysisType.PERFORMANCE_TREND,
                    title=f"Increasing {param} Trend",
                    description=f"{param} is trending upward (avg: {recent_avg:.1f} vs {earlier_avg:.1f})",
                    severity="warning" if param in ["Coolant_Temp", "EGT"] else "info",
                    confidence=0.7,
                    affected_parameters=[param],
                    recommended_action=self._get_trend_recommendation(param, "increasing"),
                ))
            elif recent_avg < earlier_avg * 0.9:  # 10% decrease
                insights.append(TelemetryInsight(
                    insight_type=AnalysisType.PERFORMANCE_TREND,
                    title=f"Decreasing {param} Trend",
                    description=f"{param} is trending downward (avg: {recent_avg:.1f} vs {earlier_avg:.1f})",
                    severity="info",
                    confidence=0.7,
                    affected_parameters=[param],
                    recommended_action=self._get_trend_recommendation(param, "decreasing"),
                ))
        
        return insights
    
    def _analyze_correlations(self, telemetry: Dict[str, float]) -> List[TelemetryInsight]:
        """Analyze correlations between parameters."""
        insights = []
        
        if len(self.telemetry_history) < 20:
            return insights
        
        # Check for problematic correlations
        # Example: High boost + lean AFR = dangerous
        boost = telemetry.get("Boost_Pressure", 0)
        afr = telemetry.get("AFR", 14.7)
        lambda_val = telemetry.get("Lambda", 1.0)
        
        if boost > 20 and (afr > 14.5 or lambda_val > 1.0):
            insights.append(TelemetryInsight(
                insight_type=AnalysisType.CORRELATION_ANALYSIS,
                title="High Boost with Lean AFR",
                description=f"Boost is {boost:.1f} PSI but AFR is {afr:.2f}:1 (lean). This is dangerous.",
                severity="critical",
                confidence=0.95,
                affected_parameters=["Boost_Pressure", "AFR"],
                recommended_action="Enrich fuel mixture immediately. Target AFR 12.5-13.2:1 at high boost.",
                expected_impact="Prevents engine damage from lean condition under boost",
            ))
        
        # High EGT + lean AFR
        egt = telemetry.get("EGT", 0)
        if egt > 850 and (afr > 14.0 or lambda_val > 0.95):
            insights.append(TelemetryInsight(
                insight_type=AnalysisType.CORRELATION_ANALYSIS,
                title="High EGT with Lean Condition",
                description=f"EGT is {egt:.0f}°C with AFR {afr:.2f}:1. High EGT indicates lean condition.",
                severity="warning",
                confidence=0.85,
                affected_parameters=["EGT", "AFR"],
                recommended_action="Enrich fuel mixture. High EGT can damage exhaust valves.",
                expected_impact="Reduces EGT and prevents valve damage",
            ))
        
        # Low fuel pressure + high boost
        fuel_pressure = telemetry.get("Fuel_Pressure", 50)
        if fuel_pressure < 40 and boost > 15:
            insights.append(TelemetryInsight(
                insight_type=AnalysisType.CORRELATION_ANALYSIS,
                title="Low Fuel Pressure Under Boost",
                description=f"Fuel pressure is {fuel_pressure:.1f} PSI while boost is {boost:.1f} PSI. Insufficient fuel delivery.",
                severity="critical",
                confidence=0.9,
                affected_parameters=["Fuel_Pressure", "Boost_Pressure"],
                recommended_action="Check fuel pump, filter, and regulator. Increase fuel pressure or reduce boost.",
                expected_impact="Prevents lean condition and engine damage",
            ))
        
        return insights
    
    def _predictive_warnings(self, telemetry: Dict[str, float]) -> List[TelemetryInsight]:
        """Generate predictive warnings based on current state."""
        insights = []
        
        # Predict knock risk
        boost = telemetry.get("Boost_Pressure", 0)
        timing = telemetry.get("Timing_Advance", 20)
        iat = telemetry.get("Intake_Air_Temp", 25)
        
        knock_risk = 0.0
        if boost > 15 and timing > 25:
            knock_risk += 0.4
        if iat > 50:
            knock_risk += 0.3
        if boost > 20:
            knock_risk += 0.3
        
        if knock_risk > 0.5:
            insights.append(TelemetryInsight(
                insight_type=AnalysisType.PREDICTIVE_WARNING,
                title="High Knock Risk",
                description=f"Current conditions (Boost: {boost:.1f} PSI, Timing: {timing:.1f}°, IAT: {iat:.1f}°C) indicate high knock risk.",
                severity="warning",
                confidence=knock_risk,
                affected_parameters=["Boost_Pressure", "Timing_Advance", "Intake_Air_Temp"],
                recommended_action=f"Reduce timing by {int(2 + knock_risk * 3)}° or reduce boost by {int(2 + knock_risk * 3)} PSI",
                expected_impact="Reduces knock risk and prevents engine damage",
            ))
        
        # Predict overheating
        coolant_temp = telemetry.get("Coolant_Temp", 90)
        if coolant_temp > 100:
            insights.append(TelemetryInsight(
                insight_type=AnalysisType.PREDICTIVE_WARNING,
                title="Overheating Risk",
                description=f"Coolant temperature is {coolant_temp:.1f}°C. Approaching dangerous levels.",
                severity="warning",
                confidence=0.8,
                affected_parameters=["Coolant_Temp"],
                recommended_action="Reduce load, check cooling system, consider reducing boost/timing",
                expected_impact="Prevents engine overheating and damage",
            ))
        
        return insights
    
    def _get_recommendation_for_low_value(self, param: str, value: float, min_val: float) -> str:
        """Get recommendation for parameter below normal."""
        recommendations = {
            "Fuel_Pressure": "Check fuel pump, filter, and regulator. May need fuel system service.",
            "Oil_Pressure": "Check oil level and pump. Engine damage risk if not addressed.",
            "AFR": "Check fuel delivery system. Lean condition can cause engine damage.",
            "Boost_Pressure": "Check for boost leaks or wastegate issues.",
        }
        return recommendations.get(param, f"Investigate cause of low {param}. Value is {value:.1f}, normal is {min_val}+")
    
    def _get_recommendation_for_high_value(self, param: str, value: float, max_val: float) -> str:
        """Get recommendation for parameter above normal."""
        recommendations = {
            "Coolant_Temp": "Check cooling system, reduce load, or reduce boost/timing.",
            "EGT": "Enrich fuel mixture or reduce timing. High EGT can damage exhaust valves.",
            "Boost_Pressure": "Check wastegate operation. Overboost can damage engine.",
            "RPM": "Check rev limiter settings. Over-revving can cause engine damage.",
        }
        return recommendations.get(param, f"Investigate cause of high {param}. Value is {value:.1f}, normal is {max_val}-")
    
    def _get_trend_recommendation(self, param: str, direction: str) -> str:
        """Get recommendation for trending parameter."""
        if param == "Coolant_Temp" and direction == "increasing":
            return "Monitor closely. May need to reduce load or check cooling system."
        elif param == "EGT" and direction == "increasing":
            return "Enrich fuel mixture or reduce timing to lower EGT."
        elif param == "Boost_Pressure" and direction == "increasing":
            return "Monitor for overboost. Check wastegate operation."
        return f"Monitor {param} trend. {direction.capitalize()} trend detected."
    
    def get_root_cause_analysis(self, problem_description: str, telemetry: Dict[str, float]) -> List[TelemetryInsight]:
        """
        Perform root cause analysis based on problem description and telemetry.
        
        Args:
            problem_description: User's description of the problem
            telemetry: Current telemetry data
            
        Returns:
            List of insights identifying potential root causes
        """
        insights = []
        desc_lower = problem_description.lower()
        
        # Analyze based on problem keywords
        if "unstable" in desc_lower or "oversteer" in desc_lower or "loose" in desc_lower:
            # Check for throttle lift-off
            throttle = telemetry.get("Throttle_Position", 0)
            if throttle < 20:  # Low throttle
                insights.append(TelemetryInsight(
                    insight_type=AnalysisType.ROOT_CAUSE,
                    title="Throttle Lift-Off Causing Instability",
                    description="Telemetry shows low throttle position. Sharp throttle lift-off can cause snap oversteer.",
                    severity="info",
                    confidence=0.7,
                    affected_parameters=["Throttle_Position"],
                    recommended_action="Smooth throttle transitions. Consider adjusting throttle mapping or traction control.",
                    expected_impact="Reduces snap oversteer and improves stability",
                ))
        
        if "knock" in desc_lower or "ping" in desc_lower or "detonation" in desc_lower:
            boost = telemetry.get("Boost_Pressure", 0)
            timing = telemetry.get("Timing_Advance", 20)
            afr = telemetry.get("AFR", 14.7)
            
            causes = []
            if boost > 15:
                causes.append(f"high boost ({boost:.1f} PSI)")
            if timing > 25:
                causes.append(f"advanced timing ({timing:.1f}°)")
            if afr > 14.0:
                causes.append(f"lean AFR ({afr:.2f}:1)")
            
            if causes:
                insights.append(TelemetryInsight(
                    insight_type=AnalysisType.ROOT_CAUSE,
                    title="Knock Root Cause Analysis",
                    description=f"Knock is likely caused by: {', '.join(causes)}",
                    severity="warning",
                    confidence=0.8,
                    affected_parameters=["Boost_Pressure", "Timing_Advance", "AFR"],
                    recommended_action="Reduce timing by 2-3°, enrich fuel mixture, or reduce boost",
                    expected_impact="Eliminates knock and prevents engine damage",
                ))
        
        if "overheat" in desc_lower or "hot" in desc_lower:
            coolant = telemetry.get("Coolant_Temp", 90)
            egt = telemetry.get("EGT", 700)
            
            if coolant > 95 or egt > 800:
                insights.append(TelemetryInsight(
                    insight_type=AnalysisType.ROOT_CAUSE,
                    title="Overheating Root Cause",
                    description=f"High temperatures detected: Coolant {coolant:.1f}°C, EGT {egt:.0f}°C",
                    severity="warning",
                    confidence=0.85,
                    affected_parameters=["Coolant_Temp", "EGT"],
                    recommended_action="Check cooling system, reduce load, enrich fuel (lowers EGT), or reduce timing",
                    expected_impact="Prevents overheating and engine damage",
                ))
        
        return insights


__all__ = ["ExpertTelemetryAnalyzer", "TelemetryInsight", "AnalysisType", "TelemetryPattern"]

