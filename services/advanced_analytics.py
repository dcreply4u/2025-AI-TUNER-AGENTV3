"""
Advanced Analytics Service

Provides lap-by-lap comparison, trend analysis, and performance insights.
"""

from __future__ import annotations

import logging
import statistics
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

LOGGER = logging.getLogger(__name__)


@dataclass
class LapData:
    """Data for a single lap."""

    lap_number: int
    lap_time: float
    timestamp: float = field(default_factory=time.time)
    metrics: Dict[str, float] = field(default_factory=dict)
    best_sector: Optional[int] = None
    worst_sector: Optional[int] = None


@dataclass
class TrendAnalysis:
    """Trend analysis results."""

    metric_name: str
    trend: str  # "improving", "declining", "stable"
    change_percent: float
    average_value: float
    best_value: float
    worst_value: float
    data_points: int


class AdvancedAnalytics:
    """Advanced analytics for performance tracking."""

    def __init__(self) -> None:
        """Initialize analytics engine."""
        self.lap_history: List[LapData] = []
        self.metric_history: Dict[str, List[tuple[float, float]]] = {}  # metric -> [(timestamp, value), ...]

    def record_lap(self, lap_data: LapData) -> None:
        """
        Record a lap.

        Args:
            lap_data: Lap data to record
        """
        self.lap_history.append(lap_data)
        LOGGER.info("Recorded lap %d: %.2f seconds", lap_data.lap_number, lap_data.lap_time)

    def compare_laps(self, lap1_index: int, lap2_index: int) -> Dict[str, float]:
        """
        Compare two laps.

        Args:
            lap1_index: Index of first lap
            lap2_index: Index of second lap

        Returns:
            Dictionary of differences
        """
        if lap1_index >= len(self.lap_history) or lap2_index >= len(self.lap_history):
            return {}

        lap1 = self.lap_history[lap1_index]
        lap2 = self.lap_history[lap2_index]

        comparison = {
            "lap_time_diff": lap2.lap_time - lap1.lap_time,
            "lap_time_percent": ((lap2.lap_time - lap1.lap_time) / lap1.lap_time) * 100,
        }

        # Compare metrics
        for metric in set(lap1.metrics.keys()) | set(lap2.metrics.keys()):
            val1 = lap1.metrics.get(metric, 0)
            val2 = lap2.metrics.get(metric, 0)
            comparison[f"{metric}_diff"] = val2 - val1
            if val1 != 0:
                comparison[f"{metric}_percent"] = ((val2 - val1) / val1) * 100

        return comparison

    def analyze_trend(self, metric_name: str, window_size: Optional[int] = None) -> Optional[TrendAnalysis]:
        """
        Analyze trend for a metric.

        Args:
            metric_name: Name of metric to analyze
            window_size: Number of recent data points to analyze (None = all)

        Returns:
            Trend analysis or None if insufficient data
        """
        if metric_name not in self.metric_history:
            return None

        history = self.metric_history[metric_name]
        if window_size:
            history = history[-window_size:]

        if len(history) < 3:
            return None

        values = [v for _, v in history]
        timestamps = [t for t, _ in history]

        # Calculate trend
        if len(values) >= 2:
            first_half = values[: len(values) // 2]
            second_half = values[len(values) // 2 :]

            first_avg = statistics.mean(first_half)
            second_avg = statistics.mean(second_half)

            if first_avg == 0:
                change_percent = 0.0
            else:
                change_percent = ((second_avg - first_avg) / abs(first_avg)) * 100

            if abs(change_percent) < 2:
                trend = "stable"
            elif change_percent > 0:
                trend = "improving" if metric_name in ["lap_time"] else "declining"
            else:
                trend = "declining" if metric_name in ["lap_time"] else "improving"
        else:
            trend = "stable"
            change_percent = 0.0

        return TrendAnalysis(
            metric_name=metric_name,
            trend=trend,
            change_percent=change_percent,
            average_value=statistics.mean(values),
            best_value=min(values) if "time" in metric_name.lower() else max(values),
            worst_value=max(values) if "time" in metric_name.lower() else min(values),
            data_points=len(values),
        )

    def get_lap_statistics(self) -> Dict[str, float]:
        """Get statistics for all recorded laps."""
        if not self.lap_history:
            return {}

        lap_times = [lap.lap_time for lap in self.lap_history]

        return {
            "total_laps": len(self.lap_history),
            "best_lap_time": min(lap_times),
            "worst_lap_time": max(lap_times),
            "average_lap_time": statistics.mean(lap_times),
            "median_lap_time": statistics.median(lap_times),
            "std_dev": statistics.stdev(lap_times) if len(lap_times) > 1 else 0.0,
        }

    def get_performance_insights(self) -> List[str]:
        """
        Generate performance insights.

        Returns:
            List of insight messages
        """
        insights = []

        if len(self.lap_history) < 2:
            return ["Record more laps to get performance insights"]

        # Lap time consistency
        lap_times = [lap.lap_time for lap in self.lap_history]
        if len(lap_times) > 1:
            std_dev = statistics.stdev(lap_times)
            avg_time = statistics.mean(lap_times)
            consistency = (1 - (std_dev / avg_time)) * 100 if avg_time > 0 else 0

            if consistency > 95:
                insights.append("Excellent lap time consistency")
            elif consistency > 90:
                insights.append("Good lap time consistency")
            else:
                insights.append(f"Lap times vary by {100-consistency:.1f}% - focus on consistency")

        # Improvement trend
        if len(self.lap_history) >= 3:
            recent_laps = self.lap_history[-3:]
            times = [lap.lap_time for lap in recent_laps]
            if times[0] > times[-1]:
                improvement = ((times[0] - times[-1]) / times[0]) * 100
                insights.append(f"Improving: {improvement:.1f}% faster in last 3 laps")
            elif times[0] < times[-1]:
                decline = ((times[-1] - times[0]) / times[0]) * 100
                insights.append(f"Declining: {decline:.1f}% slower in last 3 laps")

        # Best lap analysis
        best_lap = min(self.lap_history, key=lambda l: l.lap_time)
        insights.append(f"Best lap: #{best_lap.lap_number} ({best_lap.lap_time:.2f}s)")

        return insights

    def record_metric(self, metric_name: str, value: float, timestamp: Optional[float] = None) -> None:
        """
        Record a metric value.

        Args:
            metric_name: Name of metric
            value: Metric value
            timestamp: Timestamp (defaults to now)
        """
        if metric_name not in self.metric_history:
            self.metric_history[metric_name] = []

        timestamp = timestamp or time.time()
        self.metric_history[metric_name].append((timestamp, value))

        # Keep history limited
        if len(self.metric_history[metric_name]) > 1000:
            self.metric_history[metric_name].pop(0)

    def get_metric_statistics(self, metric_name: str) -> Optional[Dict[str, float]]:
        """
        Get statistics for a metric.

        Args:
            metric_name: Name of metric

        Returns:
            Statistics dictionary or None if no data
        """
        if metric_name not in self.metric_history or not self.metric_history[metric_name]:
            return None

        values = [v for _, v in self.metric_history[metric_name]]

        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
            "min": min(values),
            "max": max(values),
        }

    def reset(self) -> None:
        """Reset all analytics data."""
        self.lap_history.clear()
        self.metric_history.clear()
        LOGGER.info("Analytics data reset")


__all__ = ["AdvancedAnalytics", "LapData", "TrendAnalysis"]

