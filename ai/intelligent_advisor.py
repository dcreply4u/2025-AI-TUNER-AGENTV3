"""
Intelligent Tuning Advisor

Advanced AI advisor that analyzes runs, compares to historical data,
and provides actionable tuning recommendations based on performance patterns.
"""

from __future__ import annotations

import logging
import statistics
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from services.advanced_analytics import AdvancedAnalytics, LapData, TrendAnalysis

LOGGER = logging.getLogger(__name__)


class AdvicePriority(Enum):
    """Priority levels for advice."""

    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"  # Important improvement
    MEDIUM = "medium"  # Recommended optimization
    LOW = "low"  # Nice to have


class AdviceCategory(Enum):
    """Categories of tuning advice."""

    TIMING = "timing"
    FUEL = "fuel"
    BOOST = "boost"
    COOLING = "cooling"
    TRACTION = "traction"
    SHIFTING = "shifting"
    SAFETY = "safety"
    GENERAL = "general"


@dataclass
class TuningAdvice:
    """A piece of tuning advice."""

    title: str
    description: str
    category: AdviceCategory
    priority: AdvicePriority
    confidence: float  # 0.0 to 1.0
    reasoning: str
    suggested_action: str
    expected_improvement: Optional[str] = None
    historical_basis: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class RunAnalysis:
    """Analysis of a single run/pass."""

    run_number: int
    run_time: float
    metrics: Dict[str, float]
    best_metrics: Dict[str, Optional[float]]
    health_score: float
    issues_detected: List[str]
    advice: List[TuningAdvice]
    timestamp: float = field(default_factory=time.time)


class IntelligentAdvisor:
    """Intelligent tuning advisor with historical learning."""

    def __init__(self, analytics: Optional[AdvancedAnalytics] = None) -> None:
        """
        Initialize intelligent advisor.

        Args:
            analytics: Advanced analytics instance for historical data
        """
        self.analytics = analytics or AdvancedAnalytics()
        self.run_history: List[RunAnalysis] = []
        self.advice_history: List[TuningAdvice] = []
        self.learning_patterns: Dict[str, Dict] = {}

    def analyze_run(
        self,
        run_number: int,
        run_time: float,
        metrics: Dict[str, float],
        best_metrics: Dict[str, Optional[float]],
        health_score: float,
        previous_runs: Optional[List[RunAnalysis]] = None,
    ) -> RunAnalysis:
        """
        Analyze a run and generate advice.

        Args:
            run_number: Run number
            run_time: Run time in seconds
            metrics: Current run metrics
            best_metrics: Best historical metrics
            health_score: Engine health score
            previous_runs: Previous run analyses for comparison

        Returns:
            Complete run analysis with advice
        """
        # Detect issues
        issues = self._detect_issues(metrics, health_score)

        # Generate advice based on multiple factors
        advice = []
        advice.extend(self._analyze_performance(run_time, metrics, best_metrics, previous_runs))
        advice.extend(self._analyze_health(metrics, health_score))
        advice.extend(self._analyze_trends(metrics, previous_runs))
        advice.extend(self._analyze_efficiency(metrics, run_time))
        advice.extend(self._analyze_safety(metrics, health_score))

        # Sort advice by priority and confidence
        advice.sort(key=lambda a: (a.priority.value, -a.confidence), reverse=True)

        analysis = RunAnalysis(
            run_number=run_number,
            run_time=run_time,
            metrics=metrics,
            best_metrics=best_metrics,
            health_score=health_score,
            issues_detected=issues,
            advice=advice,
        )

        self.run_history.append(analysis)
        self.advice_history.extend(advice)

        # Learn from this run
        self._learn_from_run(analysis)

        return analysis

    def _detect_issues(self, metrics: Dict[str, float], health_score: float) -> List[str]:
        """Detect issues in current run."""
        issues = []

        # High temperature
        if metrics.get("Coolant_Temp", 0) > 110:
            issues.append("High coolant temperature")

        # Low oil pressure
        if metrics.get("Oil_Pressure", 100) < 25:
            issues.append("Low oil pressure")

        # Knock detection
        if metrics.get("Knock_Count", 0) > 0:
            issues.append("Engine knock detected")

        # Lean condition
        if metrics.get("Lambda", 1.0) > 1.15:
            issues.append("Lean air/fuel ratio")

        # Rich condition
        if metrics.get("Lambda", 1.0) < 0.85:
            issues.append("Rich air/fuel ratio")

        # Poor health
        if health_score < 70:
            issues.append("Engine health degraded")

        return issues

    def _analyze_performance(
        self,
        run_time: float,
        metrics: Dict[str, float],
        best_metrics: Dict[str, Optional[float]],
        previous_runs: Optional[List[RunAnalysis]],
    ) -> List[TuningAdvice]:
        """Analyze performance and suggest improvements."""
        advice = []

        # Compare to best time
        best_time = best_metrics.get("lap_time") or best_metrics.get("0-60 mph")
        if best_time and run_time > best_time:
            time_diff = run_time - best_time
            if time_diff > 0.5:
                advice.append(
                    TuningAdvice(
                        title="Run Time Slower Than Best",
                        description=f"Current run ({run_time:.2f}s) is {time_diff:.2f}s slower than best ({best_time:.2f}s)",
                        category=AdviceCategory.GENERAL,
                        priority=AdvicePriority.MEDIUM,
                        confidence=0.9,
                        reasoning="Performance degradation detected",
                        suggested_action="Review recent changes and compare to best run conditions",
                        expected_improvement=f"Potential {time_diff:.2f}s improvement",
                        historical_basis=f"Best time: {best_time:.2f}s",
                    )
                )

        # Analyze launch performance
        if previous_runs and len(previous_runs) >= 2:
            recent_60_times = [r.metrics.get("0-60 mph") for r in previous_runs[-5:] if r.metrics.get("0-60 mph")]
            if recent_60_times:
                avg_60 = statistics.mean(recent_60_times)
                current_60 = metrics.get("0-60 mph")
                if current_60 and current_60 > avg_60 * 1.05:  # 5% slower
                    advice.append(
                        TuningAdvice(
                            title="Launch Performance Degraded",
                            description=f"0-60 time ({current_60:.2f}s) is slower than recent average ({avg_60:.2f}s)",
                            category=AdviceCategory.TRACTION,
                            priority=AdvicePriority.HIGH,
                            confidence=0.85,
                            reasoning="Launch performance has declined",
                            suggested_action="Check tire pressure, traction control settings, and launch RPM",
                            expected_improvement=f"Potential {current_60 - avg_60:.2f}s improvement",
                            historical_basis=f"Recent average: {avg_60:.2f}s",
                        )
                    )

        # Analyze top speed / trap speed
        trap_speed = metrics.get("trap_speed") or metrics.get("Vehicle_Speed")
        if trap_speed and previous_runs:
            recent_traps = [r.metrics.get("trap_speed") or r.metrics.get("Vehicle_Speed", 0) for r in previous_runs[-5:]]
            if recent_traps:
                avg_trap = statistics.mean(recent_traps)
                if trap_speed < avg_trap * 0.98:  # 2% slower
                    advice.append(
                        TuningAdvice(
                            title="Trap Speed Lower Than Average",
                            description=f"Trap speed ({trap_speed:.1f} mph) below recent average ({avg_trap:.1f} mph)",
                            category=AdviceCategory.BOOST,
                            priority=AdvicePriority.MEDIUM,
                            confidence=0.8,
                            reasoning="Top end power may be reduced",
                            suggested_action="Check boost curve, fuel delivery, and air intake at high RPM",
                            expected_improvement=f"Potential {avg_trap - trap_speed:.1f} mph gain",
                            historical_basis=f"Recent average: {avg_trap:.1f} mph",
                        )
                    )

        return advice

    def _analyze_health(self, metrics: Dict[str, float], health_score: float) -> List[TuningAdvice]:
        """Analyze engine health and suggest maintenance."""
        advice = []

        # Coolant temperature analysis
        coolant_temp = metrics.get("Coolant_Temp", 0)
        if coolant_temp > 105:
            advice.append(
                TuningAdvice(
                    title="High Coolant Temperature",
                    description=f"Coolant temp ({coolant_temp:.1f}°C) is elevated",
                    category=AdviceCategory.COOLING,
                    priority=AdvicePriority.HIGH if coolant_temp > 110 else AdvicePriority.MEDIUM,
                    confidence=0.95,
                    reasoning="Elevated temperatures reduce power and increase wear",
                    suggested_action="Check cooling system, consider richer fuel map, or reduce boost",
                    expected_improvement="Improved reliability and potential power recovery",
                )
            )

        # Oil pressure analysis
        oil_pressure = metrics.get("Oil_Pressure", 0)
        if oil_pressure < 30:
            advice.append(
                TuningAdvice(
                    title="Low Oil Pressure",
                    description=f"Oil pressure ({oil_pressure:.1f} psi) is below optimal",
                    category=AdviceCategory.SAFETY,
                    priority=AdvicePriority.CRITICAL if oil_pressure < 25 else AdvicePriority.HIGH,
                    confidence=0.98,
                    reasoning="Low oil pressure can cause engine damage",
                    suggested_action="Immediately check oil level, oil pump, and consider reducing RPM",
                    expected_improvement="Prevent engine damage",
                )
            )

        # Lambda/AFR analysis
        lambda_val = metrics.get("Lambda", 1.0)
        if lambda_val > 1.15:
            advice.append(
                TuningAdvice(
                    title="Lean Air/Fuel Ratio",
                    description=f"Lambda ({lambda_val:.2f}) indicates lean condition",
                    category=AdviceCategory.FUEL,
                    priority=AdvicePriority.HIGH,
                    confidence=0.9,
                    reasoning="Lean condition can cause detonation and engine damage",
                    suggested_action="Enrich fuel map in affected RPM/load cells",
                    expected_improvement="Safer operation and potential power increase",
                )
            )
        elif lambda_val < 0.85:
            advice.append(
                TuningAdvice(
                    title="Rich Air/Fuel Ratio",
                    description=f"Lambda ({lambda_val:.2f}) indicates rich condition",
                    category=AdviceCategory.FUEL,
                    priority=AdvicePriority.MEDIUM,
                    confidence=0.85,
                    reasoning="Rich condition wastes fuel and reduces power",
                    suggested_action="Lean fuel map slightly in affected areas",
                    expected_improvement="Better fuel economy and potential power increase",
                )
            )

        # Knock analysis
        knock_count = metrics.get("Knock_Count", 0)
        if knock_count > 0:
            advice.append(
                TuningAdvice(
                    title="Engine Knock Detected",
                    description=f"Knock count: {knock_count}",
                    category=AdviceCategory.TIMING,
                    priority=AdvicePriority.CRITICAL,
                    confidence=0.95,
                    reasoning="Knock can cause severe engine damage",
                    suggested_action="Reduce timing advance, enrich fuel, or reduce boost immediately",
                    expected_improvement="Prevent engine damage",
                )
            )

        return advice

    def _analyze_trends(
        self, metrics: Dict[str, float], previous_runs: Optional[List[RunAnalysis]]
    ) -> List[TuningAdvice]:
        """Analyze trends across multiple runs."""
        advice = []

        if not previous_runs or len(previous_runs) < 3:
            return advice

        # Analyze temperature trend
        recent_temps = [r.metrics.get("Coolant_Temp", 0) for r in previous_runs[-5:]]
        if len(recent_temps) >= 3:
            temp_trend = statistics.mean(recent_temps[-3:]) - statistics.mean(recent_temps[:3])
            if temp_trend > 5:  # Increasing trend
                advice.append(
                    TuningAdvice(
                        title="Cooling System Degradation",
                        description="Coolant temperature trending upward over recent runs",
                        category=AdviceCategory.COOLING,
                        priority=AdvicePriority.MEDIUM,
                        confidence=0.75,
                        reasoning="Progressive temperature increase suggests cooling system issue",
                        suggested_action="Inspect radiator, water pump, and cooling system for issues",
                        expected_improvement="Restore optimal operating temperature",
                        historical_basis=f"Temperature increased {temp_trend:.1f}°C over recent runs",
                    )
                )

        # Analyze performance trend
        recent_times = [r.run_time for r in previous_runs[-5:]]
        if len(recent_times) >= 3:
            time_trend = statistics.mean(recent_times[-3:]) - statistics.mean(recent_times[:3])
            if time_trend > 0.3:  # Getting slower
                advice.append(
                    TuningAdvice(
                        title="Performance Declining",
                        description="Run times trending slower over recent runs",
                        category=AdviceCategory.GENERAL,
                        priority=AdvicePriority.MEDIUM,
                        confidence=0.7,
                        reasoning="Consistent performance degradation",
                        suggested_action="Review recent tuning changes, check for mechanical issues",
                        expected_improvement="Restore previous performance levels",
                        historical_basis=f"Times increased {time_trend:.2f}s over recent runs",
                    )
                )

        return advice

    def _analyze_efficiency(self, metrics: Dict[str, float], run_time: float) -> List[TuningAdvice]:
        """Analyze efficiency and optimization opportunities."""
        advice = []

        # Boost efficiency
        boost = metrics.get("Boost_Pressure", 0)
        throttle = metrics.get("Throttle_Position", 0)
        if boost > 0 and throttle > 80:
            # Check if boost is being used efficiently
            rpm = metrics.get("Engine_RPM", 0)
            if rpm > 6000 and boost < 20:
                advice.append(
                    TuningAdvice(
                        title="Boost Not Maximized at High RPM",
                        description=f"Boost ({boost:.1f} psi) could be higher at {rpm:.0f} RPM",
                        category=AdviceCategory.BOOST,
                        priority=AdvicePriority.LOW,
                        confidence=0.65,
                        reasoning="Potential for more power at high RPM",
                        suggested_action="Review boost curve and wastegate settings",
                        expected_improvement="Potential power increase at top end",
                    )
                )

        # Fuel efficiency for racing applications
        lambda_val = metrics.get("Lambda", 1.0)
        if 0.95 < lambda_val < 1.05:  # Good range
            # Check if we can optimize further
            if metrics.get("Coolant_Temp", 0) < 95:
                advice.append(
                    TuningAdvice(
                        title="Optimal Operating Conditions",
                        description="Engine running in optimal range",
                        category=AdviceCategory.GENERAL,
                        priority=AdvicePriority.LOW,
                        confidence=0.9,
                        reasoning="All parameters within optimal ranges",
                        suggested_action="Maintain current settings, consider fine-tuning for specific conditions",
                        expected_improvement="Consistent performance",
                    )
                )

        return advice

    def _analyze_safety(self, metrics: Dict[str, float], health_score: float) -> List[TuningAdvice]:
        """Analyze safety-critical parameters."""
        advice = []

        # Critical safety checks
        if health_score < 60:
            advice.append(
                TuningAdvice(
                    title="Critical Engine Health Warning",
                    description=f"Engine health score ({health_score:.0f}) is critically low",
                    category=AdviceCategory.SAFETY,
                    priority=AdvicePriority.CRITICAL,
                    confidence=0.95,
                    reasoning="Multiple parameters indicate engine stress",
                    suggested_action="Immediately reduce power, check all systems, consider stopping session",
                    expected_improvement="Prevent catastrophic failure",
                )
            )

        # E85/Methanol safety
        e85_percent = metrics.get("FlexFuelPercent", 0)
        if e85_percent < 50 and metrics.get("Boost_Pressure", 0) > 25:
            advice.append(
                TuningAdvice(
                    title="High Boost with Low Ethanol Content",
                    description=f"Boost ({metrics.get('Boost_Pressure', 0):.1f} psi) is high but ethanol ({e85_percent:.0f}%) is low",
                    category=AdviceCategory.SAFETY,
                    priority=AdvicePriority.HIGH,
                    confidence=0.85,
                    reasoning="High boost requires higher octane fuel for safety",
                    suggested_action="Increase ethanol content or reduce boost to prevent detonation",
                    expected_improvement="Safer operation",
                )
            )

        # Methanol injection safety
        meth_duty = metrics.get("MethInjectionDuty", 0)
        meth_level = metrics.get("MethTankLevel", 100)
        if meth_duty > 70 and meth_level < 20:
            advice.append(
                TuningAdvice(
                    title="Methanol Tank Low",
                    description=f"Methanol injection active ({meth_duty:.0f}%) but tank level low ({meth_level:.0f}%)",
                    category=AdviceCategory.SAFETY,
                    priority=AdvicePriority.HIGH,
                    confidence=0.9,
                    reasoning="Low methanol level can cause lean condition if injection fails",
                    suggested_action="Refill methanol tank before next run",
                    expected_improvement="Prevent dangerous lean condition",
                )
            )

        return advice

    def _learn_from_run(self, analysis: RunAnalysis) -> None:
        """Learn patterns from run analysis."""
        # Track which advice categories are most common
        category_counts: Dict[str, int] = {}
        for advice in analysis.advice:
            cat = advice.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Learn performance patterns
        if len(self.run_history) >= 5:
            recent_runs = self.run_history[-5:]
            avg_time = statistics.mean([r.run_time for r in recent_runs])
            std_time = statistics.stdev([r.run_time for r in recent_runs]) if len(recent_runs) > 1 else 0

            self.learning_patterns["consistency"] = {
                "average_time": avg_time,
                "std_deviation": std_time,
                "consistency_score": 1 - (std_time / avg_time) if avg_time > 0 else 0,
            }

    def get_summary_advice(self, num_runs: int = 5) -> List[TuningAdvice]:
        """
        Get summary advice based on recent runs.

        Args:
            num_runs: Number of recent runs to analyze

        Returns:
            List of prioritized advice
        """
        if len(self.run_history) < num_runs:
            return []

        recent_runs = self.run_history[-num_runs:]
        all_advice: List[TuningAdvice] = []

        # Collect all advice from recent runs
        for run in recent_runs:
            all_advice.extend(run.advice)

        # Group by category and prioritize
        category_advice: Dict[str, List[TuningAdvice]] = {}
        for advice in all_advice:
            cat = advice.category.value
            if cat not in category_advice:
                category_advice[cat] = []
            category_advice[cat].append(advice)

        # Select top advice from each category
        summary = []
        for cat, advice_list in category_advice.items():
            # Sort by priority and confidence
            advice_list.sort(key=lambda a: (a.priority.value, -a.confidence), reverse=True)
            # Take top 2 from each category
            summary.extend(advice_list[:2])

        # Sort overall by priority
        summary.sort(key=lambda a: (a.priority.value, -a.confidence), reverse=True)

        return summary[:10]  # Top 10 pieces of advice

    def get_historical_comparison(self, run_number: int) -> Optional[Dict]:
        """Get comparison to historical runs."""
        if run_number >= len(self.run_history):
            return None

        current_run = self.run_history[run_number]
        if len(self.run_history) < 2:
            return None

        previous_runs = [r for r in self.run_history[:run_number]]

        comparison = {
            "current_time": current_run.run_time,
            "best_time": min([r.run_time for r in self.run_history]),
            "average_time": statistics.mean([r.run_time for r in previous_runs]) if previous_runs else None,
            "improvement": None,
            "degradation": None,
        }

        if previous_runs:
            avg_prev = statistics.mean([r.run_time for r in previous_runs])
            if current_run.run_time < avg_prev:
                comparison["improvement"] = avg_prev - current_run.run_time
            else:
                comparison["degradation"] = current_run.run_time - avg_prev

        return comparison


__all__ = [
    "IntelligentAdvisor",
    "TuningAdvice",
    "RunAnalysis",
    "AdvicePriority",
    "AdviceCategory",
]

