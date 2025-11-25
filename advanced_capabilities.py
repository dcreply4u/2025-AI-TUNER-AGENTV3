"""
Advanced Capabilities Module for AI Tuner CAN Agent

Provides advanced sensor suite, health scoring, predictive maintenance,
and feature suggestions for the AI Tuner system.
"""

import time
import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class SensorReading:
    """Represents a sensor reading with metadata."""
    metric: str
    value: float
    timestamp: float
    unit: str = ""


class AdvancedSensorSuite:
    """
    Advanced sensor suite with comprehensive metric tracking and analysis.
    
    Features:
    - Multi-sensor data collection
    - Real-time metric tracking
    - Historical data retention
    - Sensor health monitoring
    """
    
    def __init__(self, history_size: int = 1000):
        """
        Initialize the advanced sensor suite.
        
        Args:
            history_size: Maximum number of readings to retain per sensor
        """
        self.sensors: Dict[str, deque] = defaultdict(lambda: deque(maxlen=history_size))
        self.metadata: Dict[str, Dict] = defaultdict(dict)
        self.last_update: Dict[str, float] = {}
        
    def update(self, metric: str, value: float, unit: str = "", metadata: Optional[Dict] = None):
        """
        Update sensor reading.
        
        Args:
            metric: Sensor metric name
            value: Sensor value
            unit: Unit of measurement
            metadata: Optional metadata dictionary
        """
        timestamp = time.time()
        reading = SensorReading(metric=metric, value=value, timestamp=timestamp, unit=unit)
        self.sensors[metric].append(reading)
        self.last_update[metric] = timestamp
        
        if metadata:
            self.metadata[metric].update(metadata)
    
    def get(self, metric: str, count: int = 1) -> List[SensorReading]:
        """
        Get recent sensor readings.
        
        Args:
            metric: Sensor metric name
            count: Number of recent readings to return
            
        Returns:
            List of SensorReading objects
        """
        if metric not in self.sensors:
            return []
        readings = list(self.sensors[metric])
        return readings[-count:] if count > 0 else readings
    
    def get_statistics(self, metric: str) -> Optional[Dict]:
        """
        Get statistical summary for a sensor.
        
        Args:
            metric: Sensor metric name
            
        Returns:
            Dictionary with statistics or None if no data
        """
        if metric not in self.sensors or len(self.sensors[metric]) == 0:
            return None
        
        values = [r.value for r in self.sensors[metric]]
        return {
            "count": len(values),
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "last_value": values[-1],
            "last_update": self.last_update.get(metric, 0)
        }
    
    def all(self) -> List[str]:
        """Get list of all tracked sensor metrics."""
        return list(self.sensors.keys())
    
    def is_healthy(self, metric: str, timeout: float = 60.0) -> bool:
        """
        Check if sensor is healthy (receiving updates).
        
        Args:
            metric: Sensor metric name
            timeout: Maximum seconds since last update
            
        Returns:
            True if sensor is healthy, False otherwise
        """
        if metric not in self.last_update:
            return False
        return (time.time() - self.last_update[metric]) < timeout


class HealthScoringEngine:
    """
    Engine health scoring system based on multiple sensor metrics.
    
    Features:
    - Multi-metric health scoring
    - Weighted scoring algorithm
    - Threshold-based alerts
    - Trend analysis
    """
    
    # Health scoring rules with thresholds
    SCORING_RULES = {
        "Lambda": {
            "optimal_range": (0.95, 1.05),
            "warning_range": (0.90, 1.10),
            "weight": 0.25,
            "description": "Air-fuel ratio"
        },
        "Knock_Count": {
            "optimal_range": (0, 5),
            "warning_range": (5, 10),
            "weight": 0.20,
            "description": "Engine knock events"
        },
        "Oil_Pressure": {
            "optimal_range": (200, 600),
            "warning_range": (150, 700),
            "weight": 0.15,
            "description": "Oil pressure (kPa)"
        },
        "Coolant_Temp": {
            "optimal_range": (85, 105),
            "warning_range": (80, 110),
            "weight": 0.15,
            "description": "Coolant temperature (°C)"
        },
        "Boost_Pressure": {
            "optimal_range": (0, 150),
            "warning_range": (-10, 200),
            "weight": 0.10,
            "description": "Boost pressure (kPa)"
        },
        "Fuel_Pressure": {
            "optimal_range": (300, 500),
            "warning_range": (250, 550),
            "weight": 0.15,
            "description": "Fuel pressure (kPa)"
        },
        "Ethanol_Content": {
            "optimal_range": (70, 85),
            "warning_range": (65, 90),
            "weight": 0.10,
            "description": "Flex-fuel ethanol percentage (%)"
        },
        "Methanol_Flow": {
            "optimal_range": (30, 90),
            "warning_range": (20, 95),
            "weight": 0.08,
            "description": "Methanol injection duty (%)"
        },
        "Methanol_Level": {
            "optimal_range": (40, 100),
            "warning_range": (25, 100),
            "weight": 0.05,
            "description": "Methanol tank level (%)"
        },
        "Nitrous_Bottle_Pressure": {
            "optimal_range": (900, 1100),
            "warning_range": (800, 1200),
            "weight": 0.07,
            "description": "Nitrous bottle pressure (psi)"
        }
    }
    
    def __init__(self):
        """Initialize the health scoring engine."""
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.weights_sum = sum(rule["weight"] for rule in self.SCORING_RULES.values())
    
    def update(self, metric: str, value: float):
        """
        Update metric value for health scoring.
        
        Args:
            metric: Metric name
            value: Metric value
        """
        self.metrics[metric].append({
            "value": value,
            "timestamp": time.time()
        })
    
    def _calculate_metric_score(self, metric: str, value: float) -> float:
        """
        Calculate health score for a single metric.
        
        Args:
            metric: Metric name
            value: Metric value
            
        Returns:
            Score between 0.0 (poor) and 1.0 (optimal)
        """
        if metric not in self.SCORING_RULES:
            return 0.5  # Unknown metrics get neutral score
        
        rule = self.SCORING_RULES[metric]
        optimal_min, optimal_max = rule["optimal_range"]
        warning_min, warning_max = rule["warning_range"]
        
        # Optimal range: score = 1.0
        if optimal_min <= value <= optimal_max:
            return 1.0
        
        # Warning range: score = 0.5 to 0.9 (linear interpolation)
        if warning_min <= value <= warning_max:
            if value < optimal_min:
                # Below optimal
                ratio = (value - warning_min) / (optimal_min - warning_min)
                return 0.5 + (ratio * 0.4)
            else:
                # Above optimal
                ratio = (warning_max - value) / (warning_max - optimal_max)
                return 0.5 + (ratio * 0.4)
        
        # Critical range: score = 0.0 to 0.5
        if value < warning_min:
            distance = abs(value - warning_min)
            max_distance = abs(warning_min - optimal_min) * 2
            if max_distance > 0:
                ratio = min(distance / max_distance, 1.0)
                return 0.5 * (1.0 - ratio)
        else:  # value > warning_max
            distance = abs(value - warning_max)
            max_distance = abs(warning_max - optimal_max) * 2
            if max_distance > 0:
                ratio = min(distance / max_distance, 1.0)
                return 0.5 * (1.0 - ratio)
        
        return 0.0
    
    def score(self) -> Optional[Dict]:
        """
        Calculate overall engine health score.
        
        Returns:
            Dictionary with overall score and per-metric breakdown, or None if insufficient data
        """
        if not self.metrics:
            return None
        
        total_score = 0.0
        metric_scores = {}
        total_weight = 0.0
        
        for metric, rule in self.SCORING_RULES.items():
            if metric not in self.metrics or len(self.metrics[metric]) == 0:
                continue
            
            # Use most recent value
            recent_reading = self.metrics[metric][-1]
            value = recent_reading["value"]
            
            metric_score = self._calculate_metric_score(metric, value)
            weight = rule["weight"]
            
            metric_scores[metric] = {
                "score": metric_score,
                "value": value,
                "weight": weight,
                "status": self._get_status(metric_score)
            }
            
            total_score += metric_score * weight
            total_weight += weight
        
        if total_weight == 0:
            return None
        
        # Normalize score
        overall_score = total_score / total_weight if total_weight > 0 else 0.0
        
        return {
            "score": round(overall_score, 3),
            "status": self._get_status(overall_score),
            "metrics": metric_scores,
            "timestamp": time.time()
        }
    
    def _get_status(self, score: float) -> str:
        """Get status string from score."""
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "fair"
        elif score >= 0.2:
            return "poor"
        else:
            return "critical"


class PredictiveMaintenanceAdvisor:
    """
    Predictive maintenance advisor with trend analysis and alert generation.
    
    Features:
    - Trend detection
    - Predictive alerts
    - Maintenance recommendations
    - Anomaly detection
    """
    
    def __init__(self, trend_window: int = 50, alert_threshold: float = 0.15):
        """
        Initialize predictive maintenance advisor.
        
        Args:
            trend_window: Number of readings to analyze for trends
            alert_threshold: Percentage change threshold for alerts
        """
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=trend_window * 2))
        self.trend_window = trend_window
        self.alert_threshold = alert_threshold
        self.alerts: List[Dict] = []
        self.last_alert_time: Dict[str, float] = {}
    
    def update(self, metric: str, value: float, timestamp: Optional[float] = None):
        """
        Update metric value for trend analysis.
        
        Args:
            metric: Metric name
            value: Metric value
            timestamp: Optional timestamp (defaults to current time)
        """
        if timestamp is None:
            timestamp = time.time()
        
        self.metrics[metric].append({
            "value": value,
            "timestamp": timestamp
        })
    
    def _detect_trend(self, metric: str) -> Optional[str]:
        """
        Detect trend direction for a metric.
        
        Args:
            metric: Metric name
            
        Returns:
            "increasing", "decreasing", "stable", or None if insufficient data
        """
        if metric not in self.metrics or len(self.metrics[metric]) < self.trend_window:
            return None
        
        values = [r["value"] for r in list(self.metrics[metric])[-self.trend_window:]]
        
        # Simple linear regression slope
        n = len(values)
        x = np.arange(n)
        slope = np.polyfit(x, values, 1)[0]
        
        # Normalize slope by mean value
        mean_value = np.mean(values)
        if mean_value == 0:
            return None
        
        normalized_slope = slope / mean_value
        
        if abs(normalized_slope) < 0.01:
            return "stable"
        elif normalized_slope > 0:
            return "increasing"
        else:
            return "decreasing"
    
    def _check_thresholds(self, metric: str, value: float) -> Optional[Dict]:
        """
        Check if metric value exceeds thresholds.
        
        Args:
            metric: Metric name
            value: Metric value
            
        Returns:
            Alert dictionary or None
        """
        # Define critical thresholds for common metrics
        thresholds = {
            "Coolant_Temp": {"critical": 115, "warning": 110},
            "Oil_Pressure": {"critical": 100, "warning": 150},
            "Boost_Pressure": {"critical": 250, "warning": 200},
            "Fuel_Pressure": {"critical": 100, "warning": 200},
            "Knock_Count": {"critical": 20, "warning": 10},
            "Ethanol_Content": {"warning_low": 70, "critical_low": 60},
            "Methanol_Flow": {"warning_low": 20, "critical_low": 10},
            "Methanol_Level": {"warning_low": 30, "critical_low": 15},
            "Nitrous_Bottle_Pressure": {"warning_low": 850, "critical_low": 750}
        }
        
        if metric not in thresholds:
            return None
        
        threshold = thresholds[metric]
        severity = None
        message = None
        
        if value >= threshold["critical"]:
            severity = "critical"
            message = f"{metric} is critically high: {value:.2f}"
        elif value >= threshold["warning"]:
            severity = "warning"
            message = f"{metric} is elevated: {value:.2f}"
        elif value <= threshold.get("critical_low", -999999):
            severity = "critical"
            message = f"{metric} is critically low: {value:.2f}"
        elif value <= threshold.get("warning_low", -999999):
            severity = "warning"
            message = f"{metric} is low: {value:.2f}"
        
        if severity:
            return {
                "metric": metric,
                "severity": severity,
                "message": message,
                "value": value,
                "threshold": threshold
            }
        
        return None
    
    def generate_alerts(self) -> List[Dict]:
        """
        Generate predictive maintenance alerts.
        
        Returns:
            List of alert dictionaries
        """
        alerts = []
        current_time = time.time()
        
        for metric in self.metrics.keys():
            if len(self.metrics[metric]) < 10:
                continue
            
            recent_reading = self.metrics[metric][-1]
            value = recent_reading["value"]
            
            # Check threshold-based alerts
            threshold_alert = self._check_thresholds(metric, value)
            if threshold_alert:
                # Rate limit alerts (max one per minute per metric)
                alert_key = f"{metric}_threshold"
                if alert_key not in self.last_alert_time or \
                   (current_time - self.last_alert_time[alert_key]) > 60:
                    alerts.append(threshold_alert)
                    self.last_alert_time[alert_key] = current_time
            
            # Check trend-based alerts
            trend = self._detect_trend(metric)
            if trend and trend != "stable":
                # Calculate trend magnitude
                values = [r["value"] for r in list(self.metrics[metric])[-self.trend_window:]]
                change_pct = abs((values[-1] - values[0]) / values[0]) if values[0] != 0 else 0
                
                if change_pct >= self.alert_threshold:
                    alert_key = f"{metric}_trend_{trend}"
                    if alert_key not in self.last_alert_time or \
                       (current_time - self.last_alert_time[alert_key]) > 300:  # 5 minutes
                        alerts.append({
                            "metric": metric,
                            "severity": "info" if change_pct < 0.25 else "warning",
                            "message": f"{metric} showing {trend} trend ({change_pct*100:.1f}% change)",
                            "value": value,
                            "trend": trend,
                            "change_pct": change_pct
                        })
                        self.last_alert_time[alert_key] = current_time
        
        return alerts


def suggest_advanced_features() -> List[str]:
    """
    Suggest advanced features for the AI Tuner system.
    
    Returns:
        List of suggested feature descriptions
    """
    return [
        "🔬 Real-time ML-based anomaly detection using edge models",
        "📊 Advanced data visualization dashboard with Grafana integration",
        "🔐 Enhanced security with end-to-end encryption and certificate rotation",
        "🌐 Multi-protocol support (CAN-FD, LIN, FlexRay)",
        "🤖 AI-powered tuning recommendations based on performance patterns",
        "📱 Mobile app integration for remote monitoring",
        "🔄 OTA (Over-The-Air) firmware update capability",
        "💾 Time-series database integration (InfluxDB/TimescaleDB)",
        "🎯 Predictive failure analysis using historical patterns",
        "🔍 Advanced DTC correlation and root cause analysis",
        "⚡ High-frequency data sampling with configurable rates",
        "🌍 Multi-cloud support (AWS, Azure, GCP)",
        "📈 Performance benchmarking and comparison tools",
        "🔔 Smart alerting with machine learning-based threshold adaptation",
        "🎨 Customizable dashboards and report generation"
    ]
