"""
Data Validation and Quality System

Validates sensor readings, detects outliers, and ensures data integrity.
"""

from __future__ import annotations

import logging
import statistics
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation severity levels."""

    PASS = "pass"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of data validation."""

    valid: bool
    level: ValidationLevel
    message: str
    metric_name: str
    value: float
    expected_range: Optional[tuple[float, float]] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class MetricDefinition:
    """Definition of a metric with validation rules."""

    name: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    expected_range: Optional[tuple[float, float]] = None
    outlier_threshold: float = 3.0  # Standard deviations for outlier detection
    rate_of_change_limit: Optional[float] = None  # Max change per second
    required: bool = False


class DataValidator:
    """Validates telemetry data for quality and integrity."""

    # Standard metric definitions
    STANDARD_METRICS = {
        "Engine_RPM": MetricDefinition(
            name="Engine_RPM",
            min_value=0,
            max_value=20000,
            expected_range=(500, 8000),
            rate_of_change_limit=5000,  # RPM per second
        ),
        "Coolant_Temp": MetricDefinition(
            name="Coolant_Temp",
            min_value=-40,
            max_value=150,
            expected_range=(70, 110),
            rate_of_change_limit=5.0,  # Degrees per second
        ),
        "Oil_Pressure": MetricDefinition(
            name="Oil_Pressure",
            min_value=0,
            max_value=150,
            expected_range=(20, 80),
        ),
        "Boost_Pressure": MetricDefinition(
            name="Boost_Pressure",
            min_value=-30,
            max_value=50,
            expected_range=(-5, 30),
            rate_of_change_limit=10.0,  # PSI per second
        ),
        "Vehicle_Speed": MetricDefinition(
            name="Vehicle_Speed",
            min_value=0,
            max_value=300,
            rate_of_change_limit=30.0,  # MPH per second
        ),
        "Throttle_Position": MetricDefinition(
            name="Throttle_Position",
            min_value=0,
            max_value=100,
            expected_range=(0, 100),
        ),
        "Lambda": MetricDefinition(
            name="Lambda",
            min_value=0.5,
            max_value=2.0,
            expected_range=(0.8, 1.2),
        ),
    }

    def __init__(self) -> None:
        """Initialize data validator."""
        self.metric_definitions: Dict[str, MetricDefinition] = dict(self.STANDARD_METRICS)
        self.value_history: Dict[str, List[tuple[float, float]]] = {}  # metric -> [(timestamp, value), ...]
        self.max_history = 100
        self.statistics: Dict[str, Dict[str, float]] = {}  # metric -> {mean, std_dev, ...}

    def validate(self, data: Dict[str, float]) -> List[ValidationResult]:
        """
        Validate a data sample.

        Args:
            data: Dictionary of metric values

        Returns:
            List of validation results
        """
        results = []
        timestamp = time.time()

        for metric_name, value in data.items():
            if metric_name not in self.metric_definitions:
                continue  # Skip unknown metrics

            definition = self.metric_definitions[metric_name]
            result = self._validate_metric(metric_name, value, definition, timestamp)
            if result:
                results.append(result)

            # Update history and statistics
            self._update_history(metric_name, value, timestamp)

        return results

    def _validate_metric(
        self, metric_name: str, value: float, definition: MetricDefinition, timestamp: float
    ) -> Optional[ValidationResult]:
        """Validate a single metric."""
        # Check if value is numeric
        if not isinstance(value, (int, float)):
            return ValidationResult(
                valid=False,
                level=ValidationLevel.ERROR,
                message=f"Non-numeric value for {metric_name}",
                metric_name=metric_name,
                value=value,
            )

        # Check min/max bounds
        if definition.min_value is not None and value < definition.min_value:
            return ValidationResult(
                valid=False,
                level=ValidationLevel.ERROR,
                message=f"{metric_name} below minimum: {value} < {definition.min_value}",
                metric_name=metric_name,
                value=value,
                expected_range=(definition.min_value, definition.max_value),
            )

        if definition.max_value is not None and value > definition.max_value:
            return ValidationResult(
                valid=False,
                level=ValidationLevel.CRITICAL,
                message=f"{metric_name} above maximum: {value} > {definition.max_value}",
                metric_name=metric_name,
                value=value,
                expected_range=(definition.min_value, definition.max_value),
            )

        # Check expected range (warning level)
        if definition.expected_range:
            min_expected, max_expected = definition.expected_range
            if value < min_expected or value > max_expected:
                return ValidationResult(
                    valid=True,  # Still valid, just outside expected range
                    level=ValidationLevel.WARNING,
                    message=f"{metric_name} outside expected range: {value} not in [{min_expected}, {max_expected}]",
                    metric_name=metric_name,
                    value=value,
                    expected_range=definition.expected_range,
                )

        # Check rate of change
        if definition.rate_of_change_limit:
            rate = self._calculate_rate_of_change(metric_name, value, timestamp)
            if rate and rate > definition.rate_of_change_limit:
                return ValidationResult(
                    valid=True,
                    level=ValidationLevel.WARNING,
                    message=f"{metric_name} changing too rapidly: {rate:.2f} units/sec (limit: {definition.rate_of_change_limit})",
                    metric_name=metric_name,
                    value=value,
                )

        # Check for outliers using statistical analysis
        if metric_name in self.statistics:
            is_outlier = self._detect_outlier(metric_name, value, definition)
            if is_outlier:
                return ValidationResult(
                    valid=True,
                    level=ValidationLevel.WARNING,
                    message=f"{metric_name} appears to be an outlier based on historical data",
                    metric_name=metric_name,
                    value=value,
                )

        # All checks passed
        return ValidationResult(
            valid=True,
            level=ValidationLevel.PASS,
            message=f"{metric_name} is valid",
            metric_name=metric_name,
            value=value,
        )

    def _update_history(self, metric_name: str, value: float, timestamp: float) -> None:
        """Update value history and statistics."""
        if metric_name not in self.value_history:
            self.value_history[metric_name] = []

        history = self.value_history[metric_name]
        history.append((timestamp, value))

        # Trim history
        if len(history) > self.max_history:
            history.pop(0)

        # Update statistics
        if len(history) >= 10:  # Need enough samples
            values = [v for _, v in history]
            self.statistics[metric_name] = {
                "mean": statistics.mean(values),
                "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
                "min": min(values),
                "max": max(values),
            }

    def _calculate_rate_of_change(self, metric_name: str, value: float, timestamp: float) -> Optional[float]:
        """Calculate rate of change for a metric."""
        if metric_name not in self.value_history or len(self.value_history[metric_name]) < 2:
            return None

        history = self.value_history[metric_name]
        last_timestamp, last_value = history[-1]

        time_delta = timestamp - last_timestamp
        if time_delta <= 0:
            return None

        value_delta = value - last_value
        return abs(value_delta / time_delta)

    def _detect_outlier(self, metric_name: str, value: float, definition: MetricDefinition) -> bool:
        """Detect if a value is an outlier using statistical methods."""
        if metric_name not in self.statistics:
            return False

        stats = self.statistics[metric_name]
        mean = stats["mean"]
        std_dev = stats["std_dev"]

        if std_dev == 0:
            return False

        z_score = abs((value - mean) / std_dev)
        return z_score > definition.outlier_threshold

    def add_metric_definition(self, definition: MetricDefinition) -> None:
        """Add or update a metric definition."""
        self.metric_definitions[definition.name] = definition

    def get_validation_summary(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """Get summary of validation results."""
        total = len(results)
        passed = sum(1 for r in results if r.valid and r.level == ValidationLevel.PASS)
        warnings = sum(1 for r in results if r.level == ValidationLevel.WARNING)
        errors = sum(1 for r in results if r.level == ValidationLevel.ERROR)
        critical = sum(1 for r in results if r.level == ValidationLevel.CRITICAL)

        return {
            "total": total,
            "passed": passed,
            "warnings": warnings,
            "errors": errors,
            "critical": critical,
            "quality_score": (passed / total * 100) if total > 0 else 0,
        }

    def reset_history(self, metric_name: Optional[str] = None) -> None:
        """Reset validation history."""
        if metric_name:
            if metric_name in self.value_history:
                del self.value_history[metric_name]
            if metric_name in self.statistics:
                del self.statistics[metric_name]
        else:
            self.value_history.clear()
            self.statistics.clear()


__all__ = ["DataValidator", "ValidationResult", "ValidationLevel", "MetricDefinition"]

