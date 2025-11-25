"""
Automated Data Log Analysis Algorithm

Parses large data logs quickly, identifying deviations from target values,
pinpointing specific operating conditions that warrant further review.
Converts raw data into actionable insights.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class DeviationSeverity(Enum):
    """Deviation severity levels."""

    CRITICAL = "critical"  # Immediate attention required
    HIGH = "high"  # Significant deviation
    MEDIUM = "medium"  # Moderate deviation
    LOW = "low"  # Minor deviation
    NORMAL = "normal"  # Within acceptable range


@dataclass
class TargetValue:
    """Target value definition for a sensor."""

    sensor_name: str
    target: float
    tolerance: float  # Acceptable deviation from target
    min_safe: Optional[float] = None
    max_safe: Optional[float] = None
    unit: str = ""


@dataclass
class Deviation:
    """Detected deviation from target."""

    sensor_name: str
    timestamp: float
    actual_value: float
    target_value: float
    deviation: float  # Absolute deviation
    deviation_percent: float  # Percentage deviation
    severity: DeviationSeverity
    operating_condition: Dict[str, float] = field(default_factory=dict)  # Context (RPM, throttle, etc.)
    recommendation: str = ""


@dataclass
class OperatingCondition:
    """Specific operating condition that warrants review."""

    condition_id: str
    description: str
    timestamp_start: float
    timestamp_end: float
    duration: float
    sensors_involved: List[str]
    deviations: List[Deviation]
    severity: DeviationSeverity
    summary: str = ""


@dataclass
class LogAnalysisResult:
    """Complete log analysis result."""

    log_file: str
    total_samples: int
    analysis_duration: float
    deviations: List[Deviation]
    operating_conditions: List[OperatingCondition]
    summary: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class AutomatedLogAnalyzer:
    """Automated data log analysis algorithm."""

    def __init__(
        self,
        target_values: Optional[Dict[str, TargetValue]] = None,
        deviation_thresholds: Optional[Dict[DeviationSeverity, float]] = None,
    ):
        """
        Initialize automated log analyzer.

        Args:
            target_values: Dictionary of sensor targets
            deviation_thresholds: Thresholds for severity classification
        """
        self.target_values = target_values or self._get_default_targets()
        self.deviation_thresholds = deviation_thresholds or {
            DeviationSeverity.CRITICAL: 20.0,  # >20% deviation
            DeviationSeverity.HIGH: 10.0,  # 10-20% deviation
            DeviationSeverity.MEDIUM: 5.0,  # 5-10% deviation
            DeviationSeverity.LOW: 2.0,  # 2-5% deviation
        }

    def analyze_log(
        self,
        log_data: List[Dict[str, Any]],
        context_sensors: Optional[List[str]] = None,
    ) -> LogAnalysisResult:
        """
        Analyze data log for deviations and issues.

        Args:
            log_data: List of telemetry samples (each is a dict with sensor values)
            context_sensors: Sensors to include in operating condition context

        Returns:
            LogAnalysisResult with deviations and operating conditions
        """
        start_time = time.time()

        if not log_data:
            return LogAnalysisResult(
                log_file="",
                total_samples=0,
                analysis_duration=0.0,
                deviations=[],
                operating_conditions=[],
            )

        context_sensors = context_sensors or ["Engine_RPM", "Throttle_Position", "Vehicle_Speed"]

        # Analyze deviations
        deviations = self._analyze_deviations(log_data, context_sensors)

        # Group deviations into operating conditions
        operating_conditions = self._identify_operating_conditions(deviations, log_data)

        # Generate summary
        summary = self._generate_summary(deviations, operating_conditions, len(log_data))

        # Generate recommendations
        recommendations = self._generate_recommendations(deviations, operating_conditions)

        analysis_duration = time.time() - start_time

        return LogAnalysisResult(
            log_file="",
            total_samples=len(log_data),
            analysis_duration=analysis_duration,
            deviations=deviations,
            operating_conditions=operating_conditions,
            summary=summary,
            recommendations=recommendations,
        )

    def _analyze_deviations(
        self, log_data: List[Dict[str, Any]], context_sensors: List[str]
    ) -> List[Deviation]:
        """Analyze log data for deviations from targets."""
        deviations = []

        for sample in log_data:
            timestamp = sample.get("timestamp", time.time())

            # Get context (operating condition)
            context = {sensor: sample.get(sensor, 0.0) for sensor in context_sensors}

            # Check each target sensor
            for sensor_name, target_def in self.target_values.items():
                if sensor_name not in sample:
                    continue

                actual_value = float(sample[sensor_name])
                target_value = target_def.target

                # Calculate deviation
                if target_value == 0:
                    deviation_percent = abs(actual_value) * 100.0
                else:
                    deviation = abs(actual_value - target_value)
                    deviation_percent = (deviation / abs(target_value)) * 100.0

                # Check safe limits first
                if target_def.min_safe is not None and actual_value < target_def.min_safe:
                    severity = DeviationSeverity.CRITICAL
                    recommendation = f"{sensor_name} below safe minimum ({target_def.min_safe} {target_def.unit})"
                elif target_def.max_safe is not None and actual_value > target_def.max_safe:
                    severity = DeviationSeverity.CRITICAL
                    recommendation = f"{sensor_name} above safe maximum ({target_def.max_safe} {target_def.unit})"
                else:
                    # Determine severity based on deviation percentage
                    if deviation_percent <= self.deviation_thresholds[DeviationSeverity.LOW]:
                        severity = DeviationSeverity.NORMAL
                        recommendation = ""
                    elif deviation_percent <= self.deviation_thresholds[DeviationSeverity.MEDIUM]:
                        severity = DeviationSeverity.LOW
                        recommendation = f"{sensor_name} slightly off target ({deviation_percent:.1f}% deviation)"
                    elif deviation_percent <= self.deviation_thresholds[DeviationSeverity.HIGH]:
                        severity = DeviationSeverity.MEDIUM
                        recommendation = f"{sensor_name} moderately off target ({deviation_percent:.1f}% deviation)"
                    elif deviation_percent <= self.deviation_thresholds[DeviationSeverity.CRITICAL]:
                        severity = DeviationSeverity.HIGH
                        recommendation = f"{sensor_name} significantly off target ({deviation_percent:.1f}% deviation)"
                    else:
                        severity = DeviationSeverity.CRITICAL
                        recommendation = f"{sensor_name} critically off target ({deviation_percent:.1f}% deviation)"

                # Only record if not normal
                if severity != DeviationSeverity.NORMAL:
                    deviation = Deviation(
                        sensor_name=sensor_name,
                        timestamp=timestamp,
                        actual_value=actual_value,
                        target_value=target_value,
                        deviation=abs(actual_value - target_value),
                        deviation_percent=deviation_percent,
                        severity=severity,
                        operating_condition=context,
                        recommendation=recommendation,
                    )
                    deviations.append(deviation)

        return deviations

    def _identify_operating_conditions(
        self, deviations: List[Deviation], log_data: List[Dict[str, Any]]
    ) -> List[OperatingCondition]:
        """Group deviations into operating conditions that warrant review."""
        if not deviations:
            return []

        # Group deviations by time proximity and sensor combinations
        conditions = []
        condition_id = 0

        # Sort deviations by timestamp
        sorted_deviations = sorted(deviations, key=lambda d: d.timestamp)

        current_condition: Optional[OperatingCondition] = None
        condition_window = 5.0  # 5 seconds window for grouping

        for deviation in sorted_deviations:
            if current_condition is None:
                # Start new condition
                condition_id += 1
                current_condition = OperatingCondition(
                    condition_id=f"COND_{condition_id:04d}",
                    description="",
                    timestamp_start=deviation.timestamp,
                    timestamp_end=deviation.timestamp,
                    duration=0.0,
                    sensors_involved=[deviation.sensor_name],
                    deviations=[deviation],
                    severity=deviation.severity,
                )
            elif deviation.timestamp - current_condition.timestamp_end <= condition_window:
                # Extend current condition
                current_condition.timestamp_end = deviation.timestamp
                current_condition.duration = (
                    current_condition.timestamp_end - current_condition.timestamp_start
                )
                if deviation.sensor_name not in current_condition.sensors_involved:
                    current_condition.sensors_involved.append(deviation.sensor_name)
                current_condition.deviations.append(deviation)
                # Update severity to highest
                if deviation.severity.value > current_condition.severity.value:
                    current_condition.severity = deviation.severity
            else:
                # Finalize current condition and start new one
                current_condition.description = self._generate_condition_description(current_condition)
                current_condition.summary = self._generate_condition_summary(current_condition)
                conditions.append(current_condition)

                condition_id += 1
                current_condition = OperatingCondition(
                    condition_id=f"COND_{condition_id:04d}",
                    description="",
                    timestamp_start=deviation.timestamp,
                    timestamp_end=deviation.timestamp,
                    duration=0.0,
                    sensors_involved=[deviation.sensor_name],
                    deviations=[deviation],
                    severity=deviation.severity,
                )

        # Finalize last condition
        if current_condition:
            current_condition.description = self._generate_condition_description(current_condition)
            current_condition.summary = self._generate_condition_summary(current_condition)
            conditions.append(current_condition)

        return conditions

    def _generate_condition_description(self, condition: OperatingCondition) -> str:
        """Generate human-readable description of operating condition."""
        sensors_str = ", ".join(condition.sensors_involved)
        severity_str = condition.severity.value.upper()
        duration_str = f"{condition.duration:.1f}s"

        return f"{severity_str} condition: {sensors_str} deviations over {duration_str}"

    def _generate_condition_summary(self, condition: OperatingCondition) -> str:
        """Generate summary of operating condition."""
        if not condition.deviations:
            return "No deviations"

        # Get average RPM and throttle from context
        avg_rpm = 0.0
        avg_throttle = 0.0
        count = 0

        for dev in condition.deviations:
            if "Engine_RPM" in dev.operating_condition:
                avg_rpm += dev.operating_condition["Engine_RPM"]
            if "Throttle_Position" in dev.operating_condition:
                avg_throttle += dev.operating_condition["Throttle_Position"]
            count += 1

        if count > 0:
            avg_rpm /= count
            avg_throttle /= count

        summary = f"{len(condition.deviations)} deviations detected"
        if avg_rpm > 0:
            summary += f" at ~{avg_rpm:.0f} RPM"
        if avg_throttle > 0:
            summary += f", {avg_throttle:.0f}% throttle"

        return summary

    def _generate_summary(
        self,
        deviations: List[Deviation],
        operating_conditions: List[OperatingCondition],
        total_samples: int,
    ) -> Dict[str, Any]:
        """Generate analysis summary."""
        if not deviations:
            return {
                "status": "clean",
                "message": "No deviations detected in log",
                "total_deviations": 0,
                "total_conditions": 0,
            }

        # Count by severity
        severity_counts = defaultdict(int)
        for dev in deviations:
            severity_counts[dev.severity] += 1

        # Count critical conditions
        critical_conditions = sum(1 for cond in operating_conditions if cond.severity == DeviationSeverity.CRITICAL)

        return {
            "status": "issues_detected",
            "total_deviations": len(deviations),
            "total_conditions": len(operating_conditions),
            "critical_conditions": critical_conditions,
            "severity_breakdown": {sev.value: count for sev, count in severity_counts.items()},
            "samples_analyzed": total_samples,
            "deviation_rate": (len(deviations) / total_samples * 100) if total_samples > 0 else 0.0,
        }

    def _generate_recommendations(
        self, deviations: List[Deviation], operating_conditions: List[OperatingCondition]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if not deviations:
            recommendations.append("Log analysis complete: No issues detected. System operating normally.")
            return recommendations

        # Group by sensor
        sensor_deviations = defaultdict(list)
        for dev in deviations:
            sensor_deviations[dev.sensor_name].append(dev)

        # Generate recommendations for each sensor with issues
        for sensor_name, sensor_devs in sensor_deviations.items():
            critical_count = sum(1 for d in sensor_devs if d.severity == DeviationSeverity.CRITICAL)
            high_count = sum(1 for d in sensor_devs if d.severity == DeviationSeverity.HIGH)

            if critical_count > 0:
                recommendations.append(
                    f"URGENT: {sensor_name} has {critical_count} critical deviations. Review immediately."
                )
            elif high_count > 0:
                recommendations.append(
                    f"Review {sensor_name}: {high_count} significant deviations detected."
                )

        # Operating condition recommendations
        critical_conditions = [c for c in operating_conditions if c.severity == DeviationSeverity.CRITICAL]
        if critical_conditions:
            recommendations.append(
                f"URGENT: {len(critical_conditions)} critical operating conditions detected. "
                "Review specific time ranges in log."
            )

        return recommendations

    def _get_default_targets(self) -> Dict[str, TargetValue]:
        """Get default target values for common sensors."""
        return {
            "Coolant_Temp": TargetValue(
                sensor_name="Coolant_Temp",
                target=190.0,  # °F
                tolerance=10.0,
                min_safe=160.0,
                max_safe=220.0,
                unit="°F",
            ),
            "Oil_Pressure": TargetValue(
                sensor_name="Oil_Pressure",
                target=45.0,  # psi
                tolerance=5.0,
                min_safe=20.0,
                max_safe=80.0,
                unit="psi",
            ),
            "Boost_Pressure": TargetValue(
                sensor_name="Boost_Pressure",
                target=15.0,  # psi
                tolerance=2.0,
                min_safe=-5.0,
                max_safe=30.0,
                unit="psi",
            ),
            "AFR": TargetValue(
                sensor_name="AFR",
                target=14.7,  # Stoichiometric
                tolerance=0.5,
                min_safe=12.0,
                max_safe=16.0,
                unit=":1",
            ),
        }


__all__ = [
    "AutomatedLogAnalyzer",
    "LogAnalysisResult",
    "Deviation",
    "OperatingCondition",
    "DeviationSeverity",
    "TargetValue",
]



