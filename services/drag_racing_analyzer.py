"""
Drag Racing Time Analysis and Coaching

Analyzes 60ft, 1/8th mile, 1/4 mile, and 1/2 mile times
and provides actionable coaching to improve performance.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from services.voice_feedback import FeedbackPriority, VoiceFeedback

LOGGER = logging.getLogger(__name__)

# Distance targets in meters
DRAG_DISTANCES = {
    "60ft": 18.288,  # 60 feet in meters
    "1/8 mile": 201.168,  # 1/8 mile in meters
    "1/4 mile": 402.336,  # 1/4 mile in meters
    "1/2 mile": 804.672,  # 1/2 mile in meters
}


class DragSegment(Enum):
    """Drag racing segments."""
    LAUNCH = "launch"  # 0-60ft
    SHORT = "short"  # 60ft-1/8th
    MID = "mid"  # 1/8th-1/4
    LONG = "long"  # 1/4-1/2


@dataclass
class DragRun:
    """Complete drag racing run data."""
    run_id: str
    timestamp: float
    times: Dict[str, Optional[float]] = field(default_factory=dict)  # 60ft, 1/8th, 1/4, 1/2 mile times
    speeds: Dict[str, Optional[float]] = field(default_factory=dict)  # Trap speeds
    telemetry_snapshot: Dict[str, float] = field(default_factory=dict)
    notes: str = ""


@dataclass
class DragCoachingAdvice:
    """Coaching advice for drag racing improvement."""
    segment: DragSegment
    metric: str  # e.g., "60ft", "1/8 mile"
    current_time: float
    best_time: Optional[float]
    improvement_potential: float  # Seconds that could be saved
    advice: str
    priority: FeedbackPriority
    actionable_steps: List[str]
    confidence: float  # 0-1


class DragRacingAnalyzer:
    """
    Analyzes drag racing times and provides coaching to improve performance.
    
    Tracks:
    - 60ft time (launch performance)
    - 1/8th mile time
    - 1/4 mile time
    - 1/2 mile time (for high-speed runs)
    """

    def __init__(self, voice_feedback: Optional[VoiceFeedback] = None) -> None:
        """Initialize drag racing analyzer."""
        self.voice_feedback = voice_feedback
        self.runs: List[DragRun] = []
        self.best_times: Dict[str, Optional[float]] = {
            "60ft": None,
            "1/8 mile": None,
            "1/4 mile": None,
            "1/2 mile": None,
        }
        self.best_speeds: Dict[str, Optional[float]] = {
            "60ft": None,
            "1/8 mile": None,
            "1/4 mile": None,
            "1/2 mile": None,
        }
        
        # Segment analysis
        self.segment_times: Dict[str, List[float]] = {
            "60ft": [],
            "1/8 mile": [],
            "1/4 mile": [],
            "1/2 mile": [],
        }

    def record_run(self, run: DragRun) -> None:
        """Record a drag racing run."""
        self.runs.append(run)
        
        # Update best times
        for metric, time_value in run.times.items():
            if time_value is not None:
                self.segment_times[metric].append(time_value)
                if self.best_times[metric] is None or time_value < self.best_times[metric]:
                    self.best_times[metric] = time_value
                    LOGGER.info(f"New best {metric}: {time_value:.3f}s")
        
        # Update best speeds
        for metric, speed_value in run.speeds.items():
            if speed_value is not None:
                if self.best_speeds[metric] is None or speed_value > self.best_speeds[metric]:
                    self.best_speeds[metric] = speed_value

    def analyze_run(self, run: DragRun) -> List[DragCoachingAdvice]:
        """
        Analyze a drag racing run and provide coaching advice.
        
        Returns actionable advice to improve times.
        """
        advice_list: List[DragCoachingAdvice] = []
        
        # Analyze each segment
        if "60ft" in run.times and run.times["60ft"] is not None:
            advice = self._analyze_60ft(run)
            if advice:
                advice_list.append(advice)
        
        if "1/8 mile" in run.times and run.times["1/8 mile"] is not None:
            advice = self._analyze_18th_mile(run)
            if advice:
                advice_list.append(advice)
        
        if "1/4 mile" in run.times and run.times["1/4 mile"] is not None:
            advice = self._analyze_14th_mile(run)
            if advice:
                advice_list.append(advice)
        
        if "1/2 mile" in run.times and run.times["1/2 mile"] is not None:
            advice = self._analyze_12th_mile(run)
            if advice:
                advice_list.append(advice)
        
        # Overall run analysis
        overall = self._analyze_overall(run)
        if overall:
            advice_list.extend(overall)
        
        # Provide voice coaching
        for advice in advice_list:
            if advice.priority in (FeedbackPriority.HIGH, FeedbackPriority.MEDIUM):
                self._provide_voice_coaching(advice)
        
        return advice_list

    def _analyze_60ft(self, run: DragRun) -> Optional[DragCoachingAdvice]:
        """Analyze 60ft time (launch performance)."""
        current_time = run.times.get("60ft")
        if current_time is None:
            return None
        
        best_time = self.best_times.get("60ft")
        improvement = 0.0
        
        # 60ft time analysis
        if current_time > 2.0:
            # Very slow launch
            improvement = current_time - 1.8  # Target: 1.8s
            return DragCoachingAdvice(
                segment=DragSegment.LAUNCH,
                metric="60ft",
                current_time=current_time,
                best_time=best_time,
                improvement_potential=improvement,
                advice="Your 60ft time is slow. Focus on launch technique.",
                priority=FeedbackPriority.HIGH,
                actionable_steps=[
                    "Check tire pressure (lower for better grip)",
                    "Improve launch RPM (find optimal RPM for your setup)",
                    "Work on throttle control (smooth application, avoid wheelspin)",
                    "Consider transbrake or launch control if available",
                    "Check suspension setup for weight transfer",
                ],
                confidence=0.9,
            )
        elif current_time > 1.8:
            # Moderate launch
            improvement = current_time - 1.6
            return DragCoachingAdvice(
                segment=DragSegment.LAUNCH,
                metric="60ft",
                current_time=current_time,
                best_time=best_time,
                improvement_potential=improvement,
                advice="60ft time can be improved. Focus on launch consistency.",
                priority=FeedbackPriority.MEDIUM,
                actionable_steps=[
                    "Practice consistent launch RPM",
                    "Work on throttle modulation to prevent wheelspin",
                    "Optimize shift points for better acceleration",
                    "Check if you're bogging or spinning",
                ],
                confidence=0.8,
            )
        elif best_time and current_time > best_time + 0.1:
            # Slower than best
            improvement = current_time - best_time
            return DragCoachingAdvice(
                segment=DragSegment.LAUNCH,
                metric="60ft",
                current_time=current_time,
                best_time=best_time,
                improvement_potential=improvement,
                advice=f"60ft is {improvement:.2f}s slower than your best. Review launch technique.",
                priority=FeedbackPriority.MEDIUM,
                actionable_steps=[
                    "Compare this run to your best run",
                    "Check what was different (RPM, throttle, conditions)",
                    "Focus on consistency",
                ],
                confidence=0.7,
            )
        
        return None

    def _analyze_18th_mile(self, run: DragRun) -> Optional[DragCoachingAdvice]:
        """Analyze 1/8th mile time."""
        current_time = run.times.get("1/8 mile")
        if current_time is None:
            return None
        
        best_time = self.best_times.get("1/8 mile")
        improvement = 0.0
        
        # Calculate segment time (1/8th - 60ft)
        sixty_ft_time = run.times.get("60ft", 0) or 0
        segment_time = current_time - sixty_ft_time if sixty_ft_time > 0 else None
        
        if segment_time and segment_time > 6.0:
            # Slow mid-section
            improvement = segment_time - 5.5
            return DragCoachingAdvice(
                segment=DragSegment.SHORT,
                metric="1/8 mile",
                current_time=current_time,
                best_time=best_time,
                improvement_potential=improvement,
                advice="1/8th mile time is slow. Focus on acceleration after launch.",
                priority=FeedbackPriority.MEDIUM,
                actionable_steps=[
                    "Check shift points (shift at optimal RPM)",
                    "Avoid wheelspin in 1st-2nd gear",
                    "Maintain full throttle through shifts",
                    "Check if you're shifting too early or too late",
                    "Review traction control settings",
                ],
                confidence=0.8,
            )
        
        if best_time and current_time > best_time + 0.2:
            improvement = current_time - best_time
            return DragCoachingAdvice(
                segment=DragSegment.SHORT,
                metric="1/8 mile",
                current_time=current_time,
                best_time=best_time,
                improvement_potential=improvement,
                advice=f"1/8th mile is {improvement:.2f}s slower than best. Review acceleration technique.",
                priority=FeedbackPriority.MEDIUM,
                actionable_steps=[
                    "Compare shift points to best run",
                    "Check throttle application",
                    "Review gear selection",
                ],
                confidence=0.7,
            )
        
        return None

    def _analyze_14th_mile(self, run: DragRun) -> Optional[DragCoachingAdvice]:
        """Analyze 1/4 mile time."""
        current_time = run.times.get("1/4 mile")
        if current_time is None:
            return None
        
        best_time = self.best_times.get("1/4 mile")
        improvement = 0.0
        
        # Calculate segment time (1/4 - 1/8th)
        eighth_time = run.times.get("1/8 mile", 0) or 0
        segment_time = current_time - eighth_time if eighth_time > 0 else None
        
        if segment_time and segment_time > 5.5:
            # Slow top-end
            improvement = segment_time - 5.0
            return DragCoachingAdvice(
                segment=DragSegment.MID,
                metric="1/4 mile",
                current_time=current_time,
                best_time=best_time,
                improvement_potential=improvement,
                advice="1/4 mile time can be improved. Focus on top-end performance.",
                priority=FeedbackPriority.MEDIUM,
                actionable_steps=[
                    "Check shift points in higher gears",
                    "Review aerodynamics (reduce drag)",
                    "Ensure you're staying in power band",
                    "Check if you're hitting rev limiter",
                    "Review boost/nitrous timing",
                ],
                confidence=0.75,
            )
        
        if best_time and current_time > best_time + 0.3:
            improvement = current_time - best_time
            return DragCoachingAdvice(
                segment=DragSegment.MID,
                metric="1/4 mile",
                current_time=current_time,
                best_time=best_time,
                improvement_potential=improvement,
                advice=f"1/4 mile is {improvement:.2f}s slower than best. Review overall technique.",
                priority=FeedbackPriority.HIGH,
                actionable_steps=[
                    "Compare all segments to best run",
                    "Identify which segment lost the most time",
                    "Review telemetry data for differences",
                ],
                confidence=0.8,
            )
        
        return None

    def _analyze_12th_mile(self, run: DragRun) -> Optional[DragCoachingAdvice]:
        """Analyze 1/2 mile time (for high-speed runs)."""
        current_time = run.times.get("1/2 mile")
        if current_time is None:
            return None
        
        best_time = self.best_times.get("1/2 mile")
        
        # Calculate segment time (1/2 - 1/4)
        quarter_time = run.times.get("1/4 mile", 0) or 0
        segment_time = current_time - quarter_time if quarter_time > 0 else None
        
        if segment_time and segment_time > 8.0:
            improvement = segment_time - 7.0
            return DragCoachingAdvice(
                segment=DragSegment.LONG,
                metric="1/2 mile",
                current_time=current_time,
                best_time=best_time,
                improvement_potential=improvement,
                advice="1/2 mile time can be improved. Focus on high-speed performance.",
                priority=FeedbackPriority.MEDIUM,
                actionable_steps=[
                    "Review aerodynamics (reduce drag at high speed)",
                    "Check gearing (ensure optimal gear ratios)",
                    "Review power delivery (boost/nitrous timing)",
                    "Check cooling (prevent heat soak)",
                ],
                confidence=0.7,
            )
        
        return None

    def _analyze_overall(self, run: DragRun) -> List[DragCoachingAdvice]:
        """Analyze overall run performance."""
        advice_list: List[DragCoachingAdvice] = []
        
        # Check for consistency
        if len(self.runs) >= 3:
            recent_times = [r.times.get("1/4 mile") for r in self.runs[-3:] if r.times.get("1/4 mile")]
            if len(recent_times) >= 3:
                avg_time = sum(recent_times) / len(recent_times)
                variance = max(recent_times) - min(recent_times)
                
                if variance > 0.5:
                    advice_list.append(DragCoachingAdvice(
                        segment=DragSegment.LAUNCH,
                        metric="Consistency",
                        current_time=avg_time,
                        best_time=None,
                        improvement_potential=variance,
                        advice=f"Your times vary by {variance:.2f}s. Focus on consistency.",
                        priority=FeedbackPriority.MEDIUM,
                        actionable_steps=[
                            "Practice consistent launch technique",
                            "Record what's different between runs",
                            "Focus on repeatability over speed initially",
                        ],
                        confidence=0.8,
                    ))
        
        # Check for improvement trends
        if len(self.runs) >= 5:
            recent = [r.times.get("1/4 mile") for r in self.runs[-5:] if r.times.get("1/4 mile")]
            if len(recent) >= 5:
                if recent[-1] > recent[0] + 0.2:
                    advice_list.append(DragCoachingAdvice(
                        segment=DragSegment.MID,
                        metric="Trend",
                        current_time=recent[-1],
                        best_time=min(recent),
                        improvement_potential=recent[-1] - min(recent),
                        advice="Your times are getting slower. Review recent changes.",
                        priority=FeedbackPriority.HIGH,
                        actionable_steps=[
                            "Check vehicle condition (tires, engine, etc.)",
                            "Review recent modifications",
                            "Check weather conditions",
                            "Consider taking a break if fatigued",
                        ],
                        confidence=0.7,
                    ))
        
        return advice_list

    def _provide_voice_coaching(self, advice: DragCoachingAdvice) -> None:
        """Provide voice coaching feedback."""
        if self.voice_feedback:
            message = f"{advice.metric}: {advice.advice}"
            self.voice_feedback.announce(
                message,
                priority=advice.priority,
                channel="drag_coaching",
                throttle=5.0,  # Don't spam
            )

    def get_statistics(self) -> Dict:
        """Get statistics about all runs."""
        if not self.runs:
            return {"total_runs": 0}
        
        stats = {
            "total_runs": len(self.runs),
            "best_times": dict(self.best_times),
            "best_speeds": dict(self.best_speeds),
            "average_times": {},
            "improvement_trends": {},
        }
        
        # Calculate averages
        for metric in ["60ft", "1/8 mile", "1/4 mile", "1/2 mile"]:
            times = [r.times.get(metric) for r in self.runs if r.times.get(metric) is not None]
            if times:
                stats["average_times"][metric] = sum(times) / len(times)
        
        # Calculate improvement trends
        if len(self.runs) >= 3:
            recent = self.runs[-3:]
            older = self.runs[:max(1, len(self.runs) - 3)]
            
            for metric in ["60ft", "1/8 mile", "1/4 mile"]:
                recent_times = [r.times.get(metric) for r in recent if r.times.get(metric)]
                older_times = [r.times.get(metric) for r in older if r.times.get(metric)]
                
                if recent_times and older_times:
                    recent_avg = sum(recent_times) / len(recent_times)
                    older_avg = sum(older_times) / len(older_times)
                    improvement = older_avg - recent_avg
                    stats["improvement_trends"][metric] = improvement
        
        return stats

    def compare_runs(self, run1: DragRun, run2: DragRun) -> Dict[str, float]:
        """Compare two runs and show differences."""
        comparison = {}
        
        for metric in ["60ft", "1/8 mile", "1/4 mile", "1/2 mile"]:
            time1 = run1.times.get(metric)
            time2 = run2.times.get(metric)
            
            if time1 is not None and time2 is not None:
                diff = time2 - time1
                comparison[metric] = diff
        
        return comparison


__all__ = [
    "DragRacingAnalyzer",
    "DragRun",
    "DragCoachingAdvice",
    "DragSegment",
    "DRAG_DISTANCES",
]

