"""
Sensor Data Correlation and Visualization Algorithm

Analyzes relationships between different sensor readings and presents
data in clear, interactive graphs. Helps users understand parameter interactions.
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


class CorrelationStrength(Enum):
    """Correlation strength classification."""

    VERY_STRONG = "very_strong"  # |r| > 0.9
    STRONG = "strong"  # 0.7 < |r| <= 0.9
    MODERATE = "moderate"  # 0.5 < |r| <= 0.7
    WEAK = "weak"  # 0.3 < |r| <= 0.5
    VERY_WEAK = "very_weak"  # |r| <= 0.3


@dataclass
class SensorCorrelation:
    """Correlation between two sensors."""

    sensor1: str
    sensor2: str
    correlation_coefficient: float  # -1 to 1
    strength: CorrelationStrength
    relationship_type: str  # "positive", "negative", "none"
    sample_count: int
    interpretation: str = ""


@dataclass
class CorrelationMatrix:
    """Complete correlation matrix for all sensors."""

    sensors: List[str]
    correlations: Dict[Tuple[str, str], SensorCorrelation]
    timestamp: float = field(default_factory=time.time)
    sample_count: int = 0


@dataclass
class CorrelationInsight:
    """Insight derived from correlation analysis."""

    insight_type: str  # "expected", "unexpected", "anomaly", "optimization"
    description: str
    sensors_involved: List[str]
    confidence: float  # 0.0 to 1.0
    recommendation: str = ""


class SensorCorrelationAnalyzer:
    """Sensor data correlation and visualization algorithm."""

    def __init__(
        self,
        expected_correlations: Optional[Dict[Tuple[str, str], float]] = None,
        min_samples: int = 50,
    ):
        """
        Initialize sensor correlation analyzer.

        Args:
            expected_correlations: Expected correlation values (sensor_pair -> expected_r)
            min_samples: Minimum samples required for correlation calculation
        """
        self.expected_correlations = expected_correlations or {}
        self.min_samples = min_samples
        self.data_buffer: Dict[str, List[float]] = defaultdict(list)
        self.timestamps: List[float] = []

    def add_data_point(self, data: Dict[str, float], timestamp: Optional[float] = None) -> None:
        """
        Add a data point for correlation analysis.

        Args:
            data: Sensor data dictionary
            timestamp: Optional timestamp
        """
        if timestamp is None:
            timestamp = time.time()

        self.timestamps.append(timestamp)

        for sensor_name, value in data.items():
            if isinstance(value, (int, float)):
                self.data_buffer[sensor_name].append(float(value))

        # Limit buffer size (keep last 10000 samples)
        max_buffer = 10000
        if len(self.timestamps) > max_buffer:
            # Remove oldest
            remove_count = len(self.timestamps) - max_buffer
            self.timestamps = self.timestamps[remove_count:]
            for sensor_name in self.data_buffer:
                self.data_buffer[sensor_name] = self.data_buffer[sensor_name][remove_count:]

    def calculate_correlations(
        self, sensors: Optional[List[str]] = None
    ) -> CorrelationMatrix:
        """
        Calculate correlation matrix for sensors.

        Args:
            sensors: List of sensors to analyze (None = all available)

        Returns:
            CorrelationMatrix with all correlations
        """
        if sensors is None:
            sensors = list(self.data_buffer.keys())

        # Filter sensors that have enough data
        valid_sensors = [
            s for s in sensors if s in self.data_buffer and len(self.data_buffer[s]) >= self.min_samples
        ]

        if len(valid_sensors) < 2:
            return CorrelationMatrix(
                sensors=valid_sensors,
                correlations={},
                sample_count=len(self.timestamps),
            )

        correlations: Dict[Tuple[str, str], SensorCorrelation] = {}

        # Calculate pairwise correlations
        for i, sensor1 in enumerate(valid_sensors):
            for sensor2 in valid_sensors[i + 1 :]:
                correlation = self._calculate_pairwise_correlation(sensor1, sensor2)
                if correlation:
                    correlations[(sensor1, sensor2)] = correlation

        return CorrelationMatrix(
            sensors=valid_sensors,
            correlations=correlations,
            sample_count=len(self.timestamps),
        )

    def _calculate_pairwise_correlation(
        self, sensor1: str, sensor2: str
    ) -> Optional[SensorCorrelation]:
        """Calculate correlation between two sensors."""
        if sensor1 not in self.data_buffer or sensor2 not in self.data_buffer:
            return None

        data1 = self.data_buffer[sensor1]
        data2 = self.data_buffer[sensor2]

        # Ensure same length
        min_len = min(len(data1), len(data2))
        if min_len < self.min_samples:
            return None

        data1 = data1[:min_len]
        data2 = data2[:min_len]

        if not NUMPY_AVAILABLE:
            # Fallback to simple correlation
            return self._simple_correlation(sensor1, sensor2, data1, data2)

        try:
            # Calculate Pearson correlation coefficient
            arr1 = np.array(data1)
            arr2 = np.array(data2)

            # Remove NaN and infinite values
            mask = np.isfinite(arr1) & np.isfinite(arr2)
            if np.sum(mask) < self.min_samples:
                return None

            arr1 = arr1[mask]
            arr2 = arr2[mask]

            # Calculate correlation
            if len(arr1) < 2 or np.std(arr1) == 0 or np.std(arr2) == 0:
                return None

            correlation_coefficient = float(np.corrcoef(arr1, arr2)[0, 1])

            # Classify strength
            abs_r = abs(correlation_coefficient)
            if abs_r > 0.9:
                strength = CorrelationStrength.VERY_STRONG
            elif abs_r > 0.7:
                strength = CorrelationStrength.STRONG
            elif abs_r > 0.5:
                strength = CorrelationStrength.MODERATE
            elif abs_r > 0.3:
                strength = CorrelationStrength.WEAK
            else:
                strength = CorrelationStrength.VERY_WEAK

            # Determine relationship type
            if abs_r < 0.1:
                relationship_type = "none"
            elif correlation_coefficient > 0:
                relationship_type = "positive"
            else:
                relationship_type = "negative"

            # Generate interpretation
            interpretation = self._interpret_correlation(
                sensor1, sensor2, correlation_coefficient, strength, relationship_type
            )

            return SensorCorrelation(
                sensor1=sensor1,
                sensor2=sensor2,
                correlation_coefficient=correlation_coefficient,
                strength=strength,
                relationship_type=relationship_type,
                sample_count=len(arr1),
                interpretation=interpretation,
            )

        except (ValueError, TypeError, ZeroDivisionError, AttributeError) as e:
            LOGGER.warning("Correlation calculation failed: %s", e, exc_info=True)
            return None
        except Exception as e:
            LOGGER.error("Unexpected error in correlation calculation: %s", e, exc_info=True)
            return None

    def _simple_correlation(
        self, sensor1: str, sensor2: str, data1: List[float], data2: List[float]
    ) -> Optional[SensorCorrelation]:
        """Simple correlation calculation without numpy."""
        if len(data1) != len(data2) or len(data1) < self.min_samples:
            return None

        # Calculate means
        mean1 = sum(data1) / len(data1)
        mean2 = sum(data2) / len(data2)

        # Calculate covariance and variances
        covariance = sum((data1[i] - mean1) * (data2[i] - mean2) for i in range(len(data1)))
        variance1 = sum((x - mean1) ** 2 for x in data1)
        variance2 = sum((x - mean2) ** 2 for x in data2)

        if variance1 == 0 or variance2 == 0:
            return None

        correlation_coefficient = covariance / (variance1 * variance2) ** 0.5

        # Classify (same as numpy version)
        abs_r = abs(correlation_coefficient)
        if abs_r > 0.9:
            strength = CorrelationStrength.VERY_STRONG
        elif abs_r > 0.7:
            strength = CorrelationStrength.STRONG
        elif abs_r > 0.5:
            strength = CorrelationStrength.MODERATE
        elif abs_r > 0.3:
            strength = CorrelationStrength.WEAK
        else:
            strength = CorrelationStrength.VERY_WEAK

        relationship_type = "positive" if correlation_coefficient > 0 else "negative" if correlation_coefficient < 0 else "none"

        interpretation = self._interpret_correlation(
            sensor1, sensor2, correlation_coefficient, strength, relationship_type
        )

        return SensorCorrelation(
            sensor1=sensor1,
            sensor2=sensor2,
            correlation_coefficient=correlation_coefficient,
            strength=strength,
            relationship_type=relationship_type,
            sample_count=len(data1),
            interpretation=interpretation,
        )

    def _interpret_correlation(
        self,
        sensor1: str,
        sensor2: str,
        r: float,
        strength: CorrelationStrength,
        relationship_type: str,
    ) -> str:
        """Generate human-readable interpretation of correlation."""
        abs_r = abs(r)

        if abs_r < 0.1:
            return f"{sensor1} and {sensor2} show no significant correlation (r={r:.3f})"

        direction = "increases together" if relationship_type == "positive" else "inversely related"

        strength_str = strength.value.replace("_", " ").title()

        return (
            f"{sensor1} and {sensor2} are {strength_str.lower()}ly correlated (r={r:.3f}). "
            f"They {direction}."
        )

    def generate_insights(self, correlation_matrix: CorrelationMatrix) -> List[CorrelationInsight]:
        """
        Generate insights from correlation analysis.

        Args:
            correlation_matrix: Calculated correlation matrix

        Returns:
            List of insights
        """
        insights = []

        for (sensor1, sensor2), correlation in correlation_matrix.correlations.items():
            # Check against expected correlations
            expected_r = self.expected_correlations.get((sensor1, sensor2)) or self.expected_correlations.get(
                (sensor2, sensor1)
            )

            if expected_r is not None:
                # Compare with expected
                diff = abs(correlation.correlation_coefficient - expected_r)
                if diff > 0.2:  # Significant difference
                    insights.append(
                        CorrelationInsight(
                            insight_type="unexpected",
                            description=f"{sensor1} and {sensor2} correlation ({correlation.correlation_coefficient:.3f}) "
                            f"differs significantly from expected ({expected_r:.3f})",
                            sensors_involved=[sensor1, sensor2],
                            confidence=min(1.0, diff),
                            recommendation=f"Investigate why {sensor1} and {sensor2} relationship differs from expected.",
                        )
                    )

            # Strong correlations for optimization opportunities
            if correlation.strength in [CorrelationStrength.VERY_STRONG, CorrelationStrength.STRONG]:
                insights.append(
                    CorrelationInsight(
                        insight_type="optimization",
                        description=f"Strong {correlation.relationship_type} correlation between {sensor1} and {sensor2}",
                        sensors_involved=[sensor1, sensor2],
                        confidence=abs(correlation.correlation_coefficient),
                        recommendation=f"Consider using {sensor1} to predict or control {sensor2} for optimization.",
                    )
                )

            # Very weak correlations that should be strong (potential issues)
            if correlation.strength == CorrelationStrength.VERY_WEAK:
                # Check if this is a known relationship that should be strong
                known_relationships = [
                    ("Engine_RPM", "Throttle_Position"),
                    ("Boost_Pressure", "Throttle_Position"),
                    ("Coolant_Temp", "Engine_RPM"),
                ]

                if (sensor1, sensor2) in known_relationships or (sensor2, sensor1) in known_relationships:
                    insights.append(
                        CorrelationInsight(
                            insight_type="anomaly",
                            description=f"{sensor1} and {sensor2} should be correlated but show weak relationship",
                            sensors_involved=[sensor1, sensor2],
                            confidence=0.7,
                            recommendation=f"Investigate why {sensor1} and {sensor2} are not showing expected relationship. "
                            "Possible sensor issue or system problem.",
                        )
                    )

        return insights

    def get_correlation_data_for_visualization(
        self, sensor1: str, sensor2: str, max_points: int = 1000
    ) -> Optional[Dict[str, Any]]:
        """
        Get data formatted for visualization (scatter plot).

        Args:
            sensor1: First sensor name
            sensor2: Second sensor name
            max_points: Maximum points to return (for performance)

        Returns:
            Dictionary with x, y data and metadata
        """
        if sensor1 not in self.data_buffer or sensor2 not in self.data_buffer:
            return None

        data1 = self.data_buffer[sensor1]
        data2 = self.data_buffer[sensor2]

        min_len = min(len(data1), len(data2))
        if min_len == 0:
            return None

        # Sample if too many points
        if min_len > max_points:
            step = min_len // max_points
            data1 = data1[::step]
            data2 = data2[::step]
            min_len = len(data1)

        data1 = data1[:min_len]
        data2 = data2[:min_len]

        # Calculate correlation for this pair
        correlation = self._calculate_pairwise_correlation(sensor1, sensor2)

        return {
            "sensor1": sensor1,
            "sensor2": sensor2,
            "x_data": data1,
            "y_data": data2,
            "correlation": correlation.correlation_coefficient if correlation else 0.0,
            "sample_count": min_len,
            "timestamps": self.timestamps[:min_len] if len(self.timestamps) >= min_len else [],
        }


__all__ = [
    "SensorCorrelationAnalyzer",
    "CorrelationMatrix",
    "SensorCorrelation",
    "CorrelationInsight",
    "CorrelationStrength",
]

