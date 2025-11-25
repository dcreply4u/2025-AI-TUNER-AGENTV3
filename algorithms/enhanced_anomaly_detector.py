"""
Enhanced Anomaly Detection Algorithm

Monitors sensor data for unusual patterns or values that could indicate
potential mechanical issues or tuning problems. Proactive identification
before they lead to damage.
"""

from __future__ import annotations

import logging
import time
from collections import deque
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


class AnomalyType(Enum):
    """Types of anomalies."""

    SPIKE = "spike"  # Sudden large change
    DROP = "drop"  # Sudden large decrease
    STUCK = "stuck"  # Value not changing
    OSCILLATION = "oscillation"  # Rapid oscillation
    DRIFT = "drift"  # Gradual drift from normal
    CORRELATION_BREAK = "correlation_break"  # Expected correlation broken
    PATTERN_DEVIATION = "pattern_deviation"  # Deviation from expected pattern


class AnomalySeverity(Enum):
    """Anomaly severity levels."""

    CRITICAL = "critical"  # Immediate attention required
    HIGH = "high"  # Significant concern
    MEDIUM = "medium"  # Moderate concern
    LOW = "low"  # Minor anomaly


@dataclass
class Anomaly:
    """Detected anomaly."""

    sensor_name: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    timestamp: float
    value: float
    expected_value: Optional[float] = None
    deviation: Optional[float] = None
    confidence: float = 0.0  # 0.0 to 1.0
    description: str = ""
    recommendation: str = ""
    context: Dict[str, float] = field(default_factory=dict)


class EnhancedAnomalyDetector:
    """Enhanced anomaly detection algorithm."""

    def __init__(
        self,
        window_size: int = 100,
        spike_threshold: float = 3.0,  # Standard deviations
        stuck_threshold: float = 0.01,  # Max variation for "stuck"
        oscillation_threshold: float = 5.0,  # Oscillations per window
    ):
        """
        Initialize enhanced anomaly detector.

        Args:
            window_size: Size of rolling window for analysis
            spike_threshold: Threshold for spike detection (std devs)
            stuck_threshold: Max variation to consider "stuck"
            oscillation_threshold: Oscillations per window to trigger
        """
        self.window_size = window_size
        self.spike_threshold = spike_threshold
        self.stuck_threshold = stuck_threshold
        self.oscillation_threshold = oscillation_threshold

        # Data buffers for each sensor
        self.data_buffers: Dict[str, deque] = {}
        self.timestamps: Dict[str, deque] = {}

        # Statistics for each sensor
        self.statistics: Dict[str, Dict[str, float]] = {}

    def update(self, data: Dict[str, float], timestamp: Optional[float] = None) -> List[Anomaly]:
        """
        Update with new data and detect anomalies.

        Args:
            data: Sensor data dictionary
            timestamp: Optional timestamp

        Returns:
            List of detected anomalies
        """
        if timestamp is None:
            timestamp = time.time()

        anomalies = []

        for sensor_name, value in data.items():
            if not isinstance(value, (int, float)):
                continue

            # Initialize buffer if needed
            if sensor_name not in self.data_buffers:
                self.data_buffers[sensor_name] = deque(maxlen=self.window_size)
                self.timestamps[sensor_name] = deque(maxlen=self.window_size)

            # Add to buffer
            self.data_buffers[sensor_name].append(float(value))
            self.timestamps[sensor_name].append(timestamp)

            # Update statistics
            self._update_statistics(sensor_name)

            # Detect anomalies
            sensor_anomalies = self._detect_sensor_anomalies(sensor_name, value, timestamp, data)
            anomalies.extend(sensor_anomalies)

        return anomalies

    def _update_statistics(self, sensor_name: str) -> None:
        """Update statistics for a sensor."""
        if sensor_name not in self.data_buffers:
            return

        buffer = list(self.data_buffers[sensor_name])

        if len(buffer) < 10:
            return

        if not NUMPY_AVAILABLE:
            # Simple statistics
            mean = sum(buffer) / len(buffer)
            variance = sum((x - mean) ** 2 for x in buffer) / len(buffer)
            std_dev = variance ** 0.5
            min_val = min(buffer)
            max_val = max(buffer)
        else:
            arr = np.array(buffer)
            mean = float(np.mean(arr))
            std_dev = float(np.std(arr))
            min_val = float(np.min(arr))
            max_val = float(np.max(arr))

        self.statistics[sensor_name] = {
            "mean": mean,
            "std_dev": std_dev,
            "min": min_val,
            "max": max_val,
            "range": max_val - min_val,
        }

    def _detect_sensor_anomalies(
        self, sensor_name: str, value: float, timestamp: float, context: Dict[str, float]
    ) -> List[Anomaly]:
        """Detect anomalies for a specific sensor."""
        anomalies = []

        if sensor_name not in self.statistics:
            return anomalies

        stats = self.statistics[sensor_name]
        buffer = list(self.data_buffers[sensor_name])

        # 1. Spike detection
        spike_anomaly = self._detect_spike(sensor_name, value, stats, timestamp, context)
        if spike_anomaly:
            anomalies.append(spike_anomaly)

        # 2. Drop detection
        drop_anomaly = self._detect_drop(sensor_name, value, stats, timestamp, context)
        if drop_anomaly:
            anomalies.append(drop_anomaly)

        # 3. Stuck value detection
        stuck_anomaly = self._detect_stuck(sensor_name, buffer, timestamp, context)
        if stuck_anomaly:
            anomalies.append(stuck_anomaly)

        # 4. Oscillation detection
        oscillation_anomaly = self._detect_oscillation(sensor_name, buffer, timestamp, context)
        if oscillation_anomaly:
            anomalies.append(oscillation_anomaly)

        # 5. Drift detection
        drift_anomaly = self._detect_drift(sensor_name, buffer, stats, timestamp, context)
        if drift_anomaly:
            anomalies.append(drift_anomaly)

        return anomalies

    def _detect_spike(
        self, sensor_name: str, value: float, stats: Dict[str, float], timestamp: float, context: Dict[str, float]
    ) -> Optional[Anomaly]:
        """Detect sudden spike in value."""
        if stats["std_dev"] == 0:
            return None

        z_score = abs(value - stats["mean"]) / stats["std_dev"]

        if z_score > self.spike_threshold:
            deviation = value - stats["mean"]
            severity = (
                AnomalySeverity.CRITICAL
                if z_score > 5.0
                else AnomalySeverity.HIGH
                if z_score > 4.0
                else AnomalySeverity.MEDIUM
            )

            return Anomaly(
                sensor_name=sensor_name,
                anomaly_type=AnomalyType.SPIKE,
                severity=severity,
                timestamp=timestamp,
                value=value,
                expected_value=stats["mean"],
                deviation=deviation,
                confidence=min(1.0, z_score / 5.0),
                description=f"{sensor_name} spiked to {value:.2f} (expected ~{stats['mean']:.2f}, {z_score:.1f}σ deviation)",
                recommendation=f"Investigate sudden spike in {sensor_name}. Possible sensor issue or system problem.",
                context=context,
            )

        return None

    def _detect_drop(
        self, sensor_name: str, value: float, stats: Dict[str, float], timestamp: float, context: Dict[str, float]
    ) -> Optional[Anomaly]:
        """Detect sudden drop in value."""
        if stats["std_dev"] == 0:
            return None

        # Only detect if value dropped significantly below mean
        if value < stats["mean"]:
            z_score = abs(value - stats["mean"]) / stats["std_dev"]

            if z_score > self.spike_threshold:
                deviation = value - stats["mean"]
                severity = (
                    AnomalySeverity.CRITICAL
                    if z_score > 5.0
                    else AnomalySeverity.HIGH
                    if z_score > 4.0
                    else AnomalySeverity.MEDIUM
                )

                return Anomaly(
                    sensor_name=sensor_name,
                    anomaly_type=AnomalyType.DROP,
                    severity=severity,
                    timestamp=timestamp,
                    value=value,
                    expected_value=stats["mean"],
                    deviation=deviation,
                    confidence=min(1.0, z_score / 5.0),
                    description=f"{sensor_name} dropped to {value:.2f} (expected ~{stats['mean']:.2f}, {z_score:.1f}σ deviation)",
                    recommendation=f"Investigate sudden drop in {sensor_name}. Possible sensor failure or system issue.",
                    context=context,
                )

        return None

    def _detect_stuck(
        self, sensor_name: str, buffer: List[float], timestamp: float, context: Dict[str, float]
    ) -> Optional[Anomaly]:
        """Detect stuck value (not changing)."""
        if len(buffer) < 20:
            return None

        # Check if values are essentially constant
        recent_values = buffer[-20:]
        value_range = max(recent_values) - min(recent_values)

        if value_range <= self.stuck_threshold:
            # Value is stuck
            avg_value = sum(recent_values) / len(recent_values)

            return Anomaly(
                sensor_name=sensor_name,
                anomaly_type=AnomalyType.STUCK,
                severity=AnomalySeverity.MEDIUM,
                timestamp=timestamp,
                value=avg_value,
                confidence=0.8,
                description=f"{sensor_name} appears stuck at {avg_value:.2f} (variation < {self.stuck_threshold})",
                recommendation=f"{sensor_name} is not changing. Check sensor connection and functionality.",
                context=context,
            )

        return None

    def _detect_oscillation(
        self, sensor_name: str, buffer: List[float], timestamp: float, context: Dict[str, float]
    ) -> Optional[Anomaly]:
        """Detect rapid oscillation."""
        if len(buffer) < 30:
            return None

        # Count zero crossings (sign changes)
        zero_crossings = 0
        for i in range(1, len(buffer)):
            if (buffer[i] - buffer[i - 1]) * (buffer[i - 1] - buffer[i - 2] if i > 1 else 0) < 0:
                zero_crossings += 1

        oscillations_per_window = zero_crossings / len(buffer)

        if oscillations_per_window > self.oscillation_threshold / self.window_size:
            return Anomaly(
                sensor_name=sensor_name,
                anomaly_type=AnomalyType.OSCILLATION,
                severity=AnomalySeverity.MEDIUM,
                timestamp=timestamp,
                value=buffer[-1],
                confidence=min(1.0, oscillations_per_window * self.window_size / self.oscillation_threshold),
                description=f"{sensor_name} showing rapid oscillation ({zero_crossings} sign changes in {len(buffer)} samples)",
                recommendation=f"{sensor_name} is oscillating rapidly. Check for electrical noise or sensor instability.",
                context=context,
            )

        return None

    def _detect_drift(
        self, sensor_name: str, buffer: List[float], stats: Dict[str, float], timestamp: float, context: Dict[str, float]
    ) -> Optional[Anomaly]:
        """Detect gradual drift from normal."""
        if len(buffer) < 50:
            return None

        # Compare first half vs second half
        mid_point = len(buffer) // 2
        first_half = buffer[:mid_point]
        second_half = buffer[mid_point:]

        first_mean = sum(first_half) / len(first_half)
        second_mean = sum(second_half) / len(second_half)

        drift = abs(second_mean - first_mean)
        drift_percent = (drift / abs(first_mean)) * 100.0 if first_mean != 0 else 0.0

        # Significant drift (>10% change)
        if drift_percent > 10.0:
            return Anomaly(
                sensor_name=sensor_name,
                anomaly_type=AnomalyType.DRIFT,
                severity=AnomalySeverity.LOW if drift_percent < 20.0 else AnomalySeverity.MEDIUM,
                timestamp=timestamp,
                value=second_mean,
                expected_value=first_mean,
                deviation=drift,
                confidence=min(1.0, drift_percent / 30.0),
                description=f"{sensor_name} drifting from {first_mean:.2f} to {second_mean:.2f} ({drift_percent:.1f}% change)",
                recommendation=f"{sensor_name} is gradually drifting. Monitor for continued trend.",
                context=context,
            )

        return None


__all__ = [
    "EnhancedAnomalyDetector",
    "Anomaly",
    "AnomalyType",
    "AnomalySeverity",
]



