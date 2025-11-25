"""
Advanced Algorithm Integration Service

Integrates all advanced algorithms for unified data analysis:
- Automated log analysis
- Sensor correlation
- Performance tracking
- Anomaly detection
- Parameter limit monitoring
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from algorithms.automated_log_analyzer import AutomatedLogAnalyzer, LogAnalysisResult
from algorithms.enhanced_anomaly_detector import Anomaly, EnhancedAnomalyDetector
from algorithms.parameter_limit_monitor import LimitStatus, ParameterLimitMonitor
from algorithms.performance_metric_tracker import (
    MetricType,
    PerformanceMetricTracker,
    PerformanceStatistics,
)
from algorithms.sensor_correlation_analyzer import (
    CorrelationMatrix,
    SensorCorrelationAnalyzer,
)

LOGGER = logging.getLogger(__name__)


@dataclass
class AlgorithmResults:
    """Combined results from all algorithms."""

    anomalies: List[Anomaly] = field(default_factory=list)
    limit_violations: LimitStatus = None  # type: ignore
    correlations: Optional[CorrelationMatrix] = None
    performance_stats: Dict[MetricType, PerformanceStatistics] = field(default_factory=dict)
    log_analysis: Optional[LogAnalysisResult] = None
    timestamp: float = field(default_factory=lambda: __import__("time").time())


class AdvancedAlgorithmIntegration:
    """Integration service for all advanced algorithms."""

    def __init__(self):
        """Initialize algorithm integration service."""
        # Initialize all algorithms
        self.log_analyzer = AutomatedLogAnalyzer()
        self.correlation_analyzer = SensorCorrelationAnalyzer()
        self.performance_tracker = PerformanceMetricTracker()
        self.anomaly_detector = EnhancedAnomalyDetector()
        self.limit_monitor = ParameterLimitMonitor()

        # Log buffer for analysis
        self.log_buffer: List[Dict[str, Any]] = []
        self.max_log_buffer = 10000  # Keep last 10k samples

    def process_telemetry(
        self, telemetry_data: Dict[str, float], timestamp: Optional[float] = None
    ) -> AlgorithmResults:
        """
        Process telemetry data through all algorithms.

        Args:
            telemetry_data: Current telemetry data
            timestamp: Optional timestamp

        Returns:
            AlgorithmResults with all analysis results
        """
        import time

        if timestamp is None:
            timestamp = time.time()

        # Add timestamp to data
        data_with_timestamp = {**telemetry_data, "timestamp": timestamp}

        # Add to log buffer
        self.log_buffer.append(data_with_timestamp)
        if len(self.log_buffer) > self.max_log_buffer:
            self.log_buffer.pop(0)

        # 1. Anomaly detection
        anomalies = self.anomaly_detector.update(telemetry_data, timestamp)

        # 2. Parameter limit monitoring
        limit_status = self.limit_monitor.check_parameters(telemetry_data)

        # 3. Sensor correlation (add data point)
        self.correlation_analyzer.add_data_point(telemetry_data, timestamp)

        # 4. Performance tracking (if applicable)
        # This would be called when specific events occur (0-60, lap, etc.)

        return AlgorithmResults(
            anomalies=anomalies,
            limit_violations=limit_status,
            timestamp=timestamp,
        )

    def analyze_log(self, log_data: Optional[List[Dict[str, Any]]] = None) -> LogAnalysisResult:
        """
        Analyze data log for deviations.

        Args:
            log_data: Optional log data (uses buffer if None)

        Returns:
            LogAnalysisResult
        """
        if log_data is None:
            log_data = self.log_buffer

        return self.log_analyzer.analyze_log(log_data)

    def get_correlations(self) -> CorrelationMatrix:
        """Get current correlation matrix."""
        return self.correlation_analyzer.calculate_correlations()

    def get_performance_statistics(
        self, metric_type: MetricType
    ) -> Optional[PerformanceStatistics]:
        """Get performance statistics for a metric type."""
        return self.performance_tracker.calculate_statistics(metric_type)

    def get_combined_results(self) -> AlgorithmResults:
        """Get combined results from all algorithms."""
        # Get correlations
        correlations = self.get_correlations()

        # Get performance stats for all tracked metrics
        performance_stats = {}
        for metric_type in MetricType:
            stats = self.get_performance_statistics(metric_type)
            if stats:
                performance_stats[metric_type] = stats

        return AlgorithmResults(
            anomalies=[],  # Would need to track these
            limit_violations=LimitStatus(parameters={}, violations=[]),  # Would need current status
            correlations=correlations,
            performance_stats=performance_stats,
        )


__all__ = ["AdvancedAlgorithmIntegration", "AlgorithmResults"]



