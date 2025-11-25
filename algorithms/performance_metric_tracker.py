"""
Performance Metric Tracking and Analysis Algorithm

Tracks and analyzes performance metrics over time or across different runs:
- 0-60 mph times
- Lap times
- Quarter-mile speeds
- Statistical analysis and comparisons
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class MetricType(Enum):
    """Performance metric types."""

    ACCELERATION_0_60 = "0_60"  # 0-60 mph time
    QUARTER_MILE = "quarter_mile"  # Quarter-mile time and speed
    LAP_TIME = "lap_time"  # Lap time
    TOP_SPEED = "top_speed"  # Maximum speed
    BRAKING_DISTANCE = "braking_distance"  # Distance to stop from speed
    CUSTOM = "custom"  # User-defined metric


@dataclass
class PerformanceRun:
    """Single performance run/measurement."""

    run_id: str
    metric_type: MetricType
    value: float  # Primary value (time, speed, etc.)
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional data (speed, distance, etc.)
    conditions: Dict[str, float] = field(default_factory=dict)  # Environmental conditions


@dataclass
class PerformanceStatistics:
    """Statistical analysis of performance metrics."""

    metric_type: MetricType
    runs: List[PerformanceRun]
    count: int
    mean: float
    median: float
    std_dev: float
    min_value: float
    max_value: float
    best_run: Optional[PerformanceRun] = None
    worst_run: Optional[PerformanceRun] = None
    improvement_trend: Optional[str] = None  # "improving", "degrading", "stable"


@dataclass
class PerformanceComparison:
    """Comparison between two sets of runs."""

    metric_type: MetricType
    baseline_stats: PerformanceStatistics
    comparison_stats: PerformanceStatistics
    improvement_percent: float
    is_improvement: bool  # True if better (lower time or higher speed)
    significance: str  # "significant", "moderate", "minimal"


class PerformanceMetricTracker:
    """Performance metric tracking and analysis algorithm."""

    def __init__(self):
        """Initialize performance metric tracker."""
        self.runs: Dict[MetricType, List[PerformanceRun]] = defaultdict(list)
        self.run_counter = 0

    def add_run(
        self,
        metric_type: MetricType,
        value: float,
        metadata: Optional[Dict[str, Any]] = None,
        conditions: Optional[Dict[str, float]] = None,
        timestamp: Optional[float] = None,
    ) -> PerformanceRun:
        """
        Add a performance run.

        Args:
            metric_type: Type of metric
            value: Primary value (time in seconds, speed in mph, etc.)
            metadata: Additional data (e.g., trap speed for quarter-mile)
            conditions: Environmental conditions (temperature, humidity, etc.)
            timestamp: Optional timestamp (defaults to now)

        Returns:
            Created PerformanceRun
        """
        if timestamp is None:
            timestamp = time.time()

        self.run_counter += 1
        run_id = f"RUN_{self.run_counter:06d}"

        run = PerformanceRun(
            run_id=run_id,
            metric_type=metric_type,
            value=value,
            timestamp=timestamp,
            metadata=metadata or {},
            conditions=conditions or {},
        )

        self.runs[metric_type].append(run)
        return run

    def calculate_statistics(self, metric_type: MetricType) -> Optional[PerformanceStatistics]:
        """
        Calculate statistics for a metric type.

        Args:
            metric_type: Metric type to analyze

        Returns:
            PerformanceStatistics or None if insufficient data
        """
        runs = self.runs.get(metric_type, [])

        if not runs:
            return None

        if len(runs) < 2:
            # Single run - minimal statistics
            run = runs[0]
            return PerformanceStatistics(
                metric_type=metric_type,
                runs=runs,
                count=1,
                mean=run.value,
                median=run.value,
                std_dev=0.0,
                min_value=run.value,
                max_value=run.value,
                best_run=run,
                worst_run=run,
            )

        values = [run.value for run in runs]

        if not NUMPY_AVAILABLE:
            # Fallback to simple statistics
            return self._simple_statistics(metric_type, runs, values)

        try:
            arr = np.array(values)

            mean = float(np.mean(arr))
            median = float(np.median(arr))
            std_dev = float(np.std(arr))
            min_value = float(np.min(arr))
            max_value = float(np.max(arr))

            # Determine best and worst (depends on metric type)
            if metric_type in [MetricType.ACCELERATION_0_60, MetricType.QUARTER_MILE, MetricType.LAP_TIME]:
                # Lower is better
                best_idx = np.argmin(arr)
                worst_idx = np.argmax(arr)
            else:
                # Higher is better (top speed, etc.)
                best_idx = np.argmax(arr)
                worst_idx = np.argmin(arr)

            best_run = runs[best_idx]
            worst_run = runs[worst_idx]

            # Calculate improvement trend
            improvement_trend = self._calculate_trend(runs)

            return PerformanceStatistics(
                metric_type=metric_type,
                runs=runs,
                count=len(runs),
                mean=mean,
                median=median,
                std_dev=std_dev,
                min_value=min_value,
                max_value=max_value,
                best_run=best_run,
                worst_run=worst_run,
                improvement_trend=improvement_trend,
            )

        except (ValueError, TypeError, ZeroDivisionError, AttributeError) as e:
            LOGGER.warning("Statistics calculation failed: %s", e, exc_info=True)
            return self._simple_statistics(metric_type, runs, values)
        except Exception as e:
            LOGGER.error("Unexpected error in statistics calculation: %s", e, exc_info=True)
            return self._simple_statistics(metric_type, runs, values)

    def _simple_statistics(
        self, metric_type: MetricType, runs: List[PerformanceRun], values: List[float]
    ) -> PerformanceStatistics:
        """Simple statistics without numpy."""
        mean = sum(values) / len(values)
        sorted_values = sorted(values)
        median = sorted_values[len(sorted_values) // 2]

        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5

        min_value = min(values)
        max_value = max(values)

        # Best and worst
        if metric_type in [MetricType.ACCELERATION_0_60, MetricType.QUARTER_MILE, MetricType.LAP_TIME]:
            best_run = runs[values.index(min_value)]
            worst_run = runs[values.index(max_value)]
        else:
            best_run = runs[values.index(max_value)]
            worst_run = runs[values.index(min_value)]

        improvement_trend = self._calculate_trend(runs)

        return PerformanceStatistics(
            metric_type=metric_type,
            runs=runs,
            count=len(runs),
            mean=mean,
            median=median,
            std_dev=std_dev,
            min_value=min_value,
            max_value=max_value,
            best_run=best_run,
            worst_run=worst_run,
            improvement_trend=improvement_trend,
        )

    def _calculate_trend(self, runs: List[PerformanceRun]) -> Optional[str]:
        """Calculate improvement trend."""
        if len(runs) < 3:
            return None

        # Sort by timestamp
        sorted_runs = sorted(runs, key=lambda r: r.timestamp)

        # Compare first half vs second half
        mid_point = len(sorted_runs) // 2
        first_half = sorted_runs[:mid_point]
        second_half = sorted_runs[mid_point:]

        first_avg = sum(r.value for r in first_half) / len(first_half)
        second_avg = sum(r.value for r in second_half) / len(second_half)

        # Determine if improving (depends on metric type)
        metric_type = sorted_runs[0].metric_type
        if metric_type in [MetricType.ACCELERATION_0_60, MetricType.QUARTER_MILE, MetricType.LAP_TIME]:
            # Lower is better
            if second_avg < first_avg * 0.98:  # 2% improvement
                return "improving"
            elif second_avg > first_avg * 1.02:  # 2% degradation
                return "degrading"
        else:
            # Higher is better
            if second_avg > first_avg * 1.02:
                return "improving"
            elif second_avg < first_avg * 0.98:
                return "degrading"

        return "stable"

    def compare_runs(
        self,
        metric_type: MetricType,
        baseline_runs: List[PerformanceRun],
        comparison_runs: List[PerformanceRun],
    ) -> Optional[PerformanceComparison]:
        """
        Compare two sets of runs.

        Args:
            metric_type: Metric type
            baseline_runs: Baseline runs to compare against
            comparison_runs: Runs to compare

        Returns:
            PerformanceComparison or None if insufficient data
        """
        if not baseline_runs or not comparison_runs:
            return None

        baseline_stats = self._calculate_stats_for_runs(metric_type, baseline_runs)
        comparison_stats = self._calculate_stats_for_runs(metric_type, comparison_runs)

        if not baseline_stats or not comparison_stats:
            return None

        # Calculate improvement
        if metric_type in [MetricType.ACCELERATION_0_60, MetricType.QUARTER_MILE, MetricType.LAP_TIME]:
            # Lower is better
            improvement_percent = ((baseline_stats.mean - comparison_stats.mean) / baseline_stats.mean) * 100
            is_improvement = comparison_stats.mean < baseline_stats.mean
        else:
            # Higher is better
            improvement_percent = ((comparison_stats.mean - baseline_stats.mean) / baseline_stats.mean) * 100
            is_improvement = comparison_stats.mean > baseline_stats.mean

        # Determine significance
        abs_improvement = abs(improvement_percent)
        if abs_improvement > 5.0:
            significance = "significant"
        elif abs_improvement > 2.0:
            significance = "moderate"
        else:
            significance = "minimal"

        return PerformanceComparison(
            metric_type=metric_type,
            baseline_stats=baseline_stats,
            comparison_stats=comparison_stats,
            improvement_percent=improvement_percent,
            is_improvement=is_improvement,
            significance=significance,
        )

    def _calculate_stats_for_runs(
        self, metric_type: MetricType, runs: List[PerformanceRun]
    ) -> Optional[PerformanceStatistics]:
        """Calculate statistics for a specific list of runs."""
        if not runs:
            return None

        values = [r.value for r in runs]

        if not NUMPY_AVAILABLE:
            mean = sum(values) / len(values)
            sorted_values = sorted(values)
            median = sorted_values[len(sorted_values) // 2]
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            std_dev = variance ** 0.5
        else:
            arr = np.array(values)
            mean = float(np.mean(arr))
            median = float(np.median(arr))
            std_dev = float(np.std(arr))

        min_value = min(values)
        max_value = max(values)

        if metric_type in [MetricType.ACCELERATION_0_60, MetricType.QUARTER_MILE, MetricType.LAP_TIME]:
            best_run = runs[values.index(min_value)]
            worst_run = runs[values.index(max_value)]
        else:
            best_run = runs[values.index(max_value)]
            worst_run = runs[values.index(min_value)]

        return PerformanceStatistics(
            metric_type=metric_type,
            runs=runs,
            count=len(runs),
            mean=mean,
            median=median,
            std_dev=std_dev,
            min_value=min_value,
            max_value=max_value,
            best_run=best_run,
            worst_run=worst_run,
        )

    def detect_0_60_from_telemetry(
        self, telemetry_data: List[Dict[str, float]], speed_key: str = "Vehicle_Speed"
    ) -> Optional[PerformanceRun]:
        """
        Detect 0-60 mph time from telemetry data.

        Args:
            telemetry_data: List of telemetry samples
            speed_key: Key for speed sensor

        Returns:
            PerformanceRun if 0-60 detected, None otherwise
        """
        if not telemetry_data:
            return None

        # Find when speed crosses 0 and 60
        start_idx = None
        end_idx = None

        for i, sample in enumerate(telemetry_data):
            speed = sample.get(speed_key, 0.0)
            if start_idx is None and speed < 2.0:  # Below 2 mph (essentially 0)
                start_idx = i
            elif start_idx is not None and speed >= 60.0:
                end_idx = i
                break

        if start_idx is None or end_idx is None:
            return None

        # Calculate time
        start_time = telemetry_data[start_idx].get("timestamp", start_idx * 0.1)
        end_time = telemetry_data[end_idx].get("timestamp", end_idx * 0.1)
        elapsed_time = end_time - start_time

        if elapsed_time <= 0:
            return None

        return self.add_run(
            metric_type=MetricType.ACCELERATION_0_60,
            value=elapsed_time,
            metadata={
                "start_speed": telemetry_data[start_idx].get(speed_key, 0.0),
                "end_speed": telemetry_data[end_idx].get(speed_key, 60.0),
                "samples": end_idx - start_idx,
            },
        )


__all__ = [
    "PerformanceMetricTracker",
    "PerformanceRun",
    "PerformanceStatistics",
    "PerformanceComparison",
    "MetricType",
]

