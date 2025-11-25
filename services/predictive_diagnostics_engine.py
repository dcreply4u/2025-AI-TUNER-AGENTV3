"""
Predictive Diagnostics Engine

Uses machine learning to analyze historical data and telemetry
to identify potential issues before they become critical failures.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

LOGGER = logging.getLogger(__name__)

# Try to import ML libraries
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None  # type: ignore

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    IsolationForest = None  # type: ignore
    StandardScaler = None  # type: ignore


@dataclass
class DiagnosticAlert:
    """Diagnostic alert from predictive system."""
    alert_id: str
    timestamp: float
    severity: str  # "low", "medium", "high", "critical"
    component: str  # Component/system affected
    issue_type: str  # Type of issue
    description: str
    confidence: float  # 0-1
    predicted_failure_time: Optional[float] = None  # Hours until failure
    recommended_action: str = ""
    telemetry_trends: Dict[str, List[float]] = field(default_factory=dict)


@dataclass
class TelemetryTrend:
    """Trend analysis for telemetry signal."""
    signal_name: str
    current_value: float
    average_value: float
    trend_direction: str  # "increasing", "decreasing", "stable"
    trend_strength: float  # 0-1
    rate_of_change: float
    anomaly_score: float  # 0-1, higher = more anomalous


class PredictiveDiagnosticsEngine:
    """
    Predictive diagnostics engine using ML for failure prediction.
    
    Features:
    - Trend analysis
    - Anomaly detection
    - Failure prediction
    - Pattern recognition
    - Early warning system
    """
    
    def __init__(self, vehicle_id: str):
        """
        Initialize predictive diagnostics engine.
        
        Args:
            vehicle_id: Vehicle identifier
        """
        self.vehicle_id = vehicle_id
        
        # Telemetry history (sliding window)
        self.telemetry_history: Dict[str, deque] = {}
        self.history_size = 1000  # Keep last 1000 samples
        
        # ML models
        self.anomaly_detector = None
        self.scaler = None
        
        # Alert history
        self.active_alerts: Dict[str, DiagnosticAlert] = {}
        self.alert_history: List[DiagnosticAlert] = []
        
        # Initialize ML models if available
        if SKLEARN_AVAILABLE and NUMPY_AVAILABLE:
            self._initialize_models()
    
    def _initialize_models(self) -> None:
        """Initialize ML models."""
        try:
            # Isolation Forest for anomaly detection
            self.anomaly_detector = IsolationForest(
                n_estimators=100,
                contamination=0.1,
                random_state=42,
            )
            self.scaler = StandardScaler()
            LOGGER.info("Predictive diagnostics models initialized")
        except Exception as e:
            LOGGER.warning("Failed to initialize ML models: %s", e)
    
    def update_telemetry(self, telemetry: Dict[str, float]) -> List[DiagnosticAlert]:
        """
        Update with new telemetry and generate alerts.
        
        Args:
            telemetry: Current telemetry data
        
        Returns:
            List of new diagnostic alerts
        """
        # Store telemetry in history
        for signal, value in telemetry.items():
            if signal not in self.telemetry_history:
                self.telemetry_history[signal] = deque(maxlen=self.history_size)
            self.telemetry_history[signal].append(value)
        
        # Analyze trends
        trends = self._analyze_trends(telemetry)
        
        # Detect anomalies
        anomalies = self._detect_anomalies(telemetry, trends)
        
        # Predict failures
        failure_predictions = self._predict_failures(trends)
        
        # Generate alerts
        new_alerts = self._generate_alerts(anomalies, failure_predictions, trends)
        
        # Update active alerts
        for alert in new_alerts:
            self.active_alerts[alert.alert_id] = alert
            self.alert_history.append(alert)
        
        # Clean old alerts
        self._clean_old_alerts()
        
        return new_alerts
    
    def _analyze_trends(self, current_telemetry: Dict[str, float]) -> Dict[str, TelemetryTrend]:
        """Analyze trends in telemetry signals."""
        trends = {}
        
        for signal, current_value in current_telemetry.items():
            if signal not in self.telemetry_history or len(self.telemetry_history[signal]) < 10:
                continue
            
            history = list(self.telemetry_history[signal])
            average = sum(history) / len(history)
            
            # Calculate trend direction
            recent_values = history[-20:] if len(history) >= 20 else history
            if len(recent_values) >= 2:
                # Simple linear trend
                first_half = sum(recent_values[:len(recent_values)//2]) / (len(recent_values)//2)
                second_half = sum(recent_values[len(recent_values)//2:]) / (len(recent_values) - len(recent_values)//2)
                
                if second_half > first_half * 1.05:
                    direction = "increasing"
                    strength = min(1.0, (second_half - first_half) / first_half)
                elif second_half < first_half * 0.95:
                    direction = "decreasing"
                    strength = min(1.0, (first_half - second_half) / first_half)
                else:
                    direction = "stable"
                    strength = 0.0
                
                rate_of_change = (current_value - history[-10]) / 10 if len(history) >= 10 else 0.0
            else:
                direction = "stable"
                strength = 0.0
                rate_of_change = 0.0
            
            # Calculate anomaly score (simple z-score)
            if len(history) >= 10:
                mean = average
                std = (sum((x - mean) ** 2 for x in history) / len(history)) ** 0.5
                if std > 0:
                    z_score = abs((current_value - mean) / std)
                    anomaly_score = min(1.0, z_score / 3.0)  # Normalize to 0-1
                else:
                    anomaly_score = 0.0
            else:
                anomaly_score = 0.0
            
            trends[signal] = TelemetryTrend(
                signal_name=signal,
                current_value=current_value,
                average_value=average,
                trend_direction=direction,
                trend_strength=strength,
                rate_of_change=rate_of_change,
                anomaly_score=anomaly_score,
            )
        
        return trends
    
    def _detect_anomalies(
        self,
        telemetry: Dict[str, float],
        trends: Dict[str, TelemetryTrend]
    ) -> List[Tuple[str, float]]:
        """Detect anomalies in telemetry."""
        anomalies = []
        
        # Threshold-based detection
        thresholds = {
            "coolant_temp": (80.0, 110.0),  # Normal range
            "oil_pressure": (20.0, 80.0),
            "egt": (400.0, 900.0),
            "knock_count": (0, 5),
            "lambda": (0.8, 1.2),
        }
        
        for signal, value in telemetry.items():
            if signal in thresholds:
                min_val, max_val = thresholds[signal]
                if value < min_val or value > max_val:
                    severity = (
                        "critical" if abs(value - (min_val + max_val) / 2) > (max_val - min_val) * 0.5
                        else "high"
                    )
                    anomalies.append((signal, 0.8 if severity == "critical" else 0.6))
        
        # Trend-based detection
        for signal, trend in trends.items():
            if trend.anomaly_score > 0.7:
                anomalies.append((signal, trend.anomaly_score))
        
        return anomalies
    
    def _predict_failures(
        self,
        trends: Dict[str, TelemetryTrend]
    ) -> List[Tuple[str, float, float]]:
        """
        Predict potential failures.
        
        Returns:
            List of (component, confidence, hours_until_failure) tuples
        """
        predictions = []
        
        # Example: Predict based on trends
        if "coolant_temp" in trends:
            trend = trends["coolant_temp"]
            if trend.trend_direction == "increasing" and trend.trend_strength > 0.5:
                # Temperature increasing - could indicate cooling system issue
                if trend.current_value > 100:
                    # Estimate hours until overheating
                    rate = trend.rate_of_change
                    if rate > 0:
                        hours_until = (110 - trend.current_value) / (rate * 3600) if rate > 0 else None
                        if hours_until and 0 < hours_until < 24:
                            predictions.append(("cooling_system", 0.7, hours_until))
        
        if "oil_pressure" in trends:
            trend = trends["oil_pressure"]
            if trend.trend_direction == "decreasing" and trend.trend_strength > 0.3:
                # Oil pressure decreasing
                if trend.current_value < 30:
                    rate = abs(trend.rate_of_change)
                    if rate > 0:
                        hours_until = (20 - trend.current_value) / (rate * 3600) if rate > 0 else None
                        if hours_until and 0 < hours_until < 48:
                            predictions.append(("oil_system", 0.6, hours_until))
        
        return predictions
    
    def _generate_alerts(
        self,
        anomalies: List[Tuple[str, float]],
        failure_predictions: List[Tuple[str, float, float]],
        trends: Dict[str, TelemetryTrend]
    ) -> List[DiagnosticAlert]:
        """Generate diagnostic alerts."""
        alerts = []
        
        # Anomaly alerts
        for signal, confidence in anomalies:
            alert_id = f"anomaly_{signal}_{int(time.time())}"
            
            # Determine severity
            if confidence > 0.8:
                severity = "critical"
            elif confidence > 0.6:
                severity = "high"
            else:
                severity = "medium"
            
            # Get trend data
            trend = trends.get(signal)
            trend_data = {}
            if trend:
                trend_data[signal] = [trend.current_value, trend.average_value]
            
            alert = DiagnosticAlert(
                alert_id=alert_id,
                timestamp=time.time(),
                severity=severity,
                component=signal,
                issue_type="anomaly",
                description=f"Anomaly detected in {signal}",
                confidence=confidence,
                recommended_action=self._get_recommended_action(signal, severity),
                telemetry_trends=trend_data,
            )
            alerts.append(alert)
        
        # Failure prediction alerts
        for component, confidence, hours_until in failure_predictions:
            alert_id = f"prediction_{component}_{int(time.time())}"
            
            severity = "high" if hours_until < 12 else "medium"
            
            alert = DiagnosticAlert(
                alert_id=alert_id,
                timestamp=time.time(),
                severity=severity,
                component=component,
                issue_type="predicted_failure",
                description=f"Potential {component} failure predicted in {hours_until:.1f} hours",
                confidence=confidence,
                predicted_failure_time=hours_until,
                recommended_action=self._get_recommended_action(component, severity),
            )
            alerts.append(alert)
        
        return alerts
    
    def _get_recommended_action(self, component: str, severity: str) -> str:
        """Get recommended action for issue."""
        actions = {
            "coolant_temp": {
                "critical": "Immediately stop engine and check cooling system",
                "high": "Monitor temperature closely, check coolant level",
                "medium": "Inspect cooling system at next opportunity",
            },
            "oil_pressure": {
                "critical": "Stop engine immediately, check oil level and pump",
                "high": "Check oil level and pressure sensor",
                "medium": "Monitor oil pressure, plan inspection",
            },
            "cooling_system": {
                "critical": "Stop immediately, check for leaks and pump",
                "high": "Inspect cooling system, check coolant",
                "medium": "Schedule cooling system inspection",
            },
            "oil_system": {
                "critical": "Stop engine, check oil level and pump",
                "high": "Check oil level and quality",
                "medium": "Monitor oil pressure, plan service",
            },
        }
        
        component_actions = actions.get(component, {})
        return component_actions.get(severity, "Monitor and investigate")
    
    def _clean_old_alerts(self) -> None:
        """Remove old resolved alerts."""
        current_time = time.time()
        # Remove alerts older than 24 hours
        self.active_alerts = {
            k: v for k, v in self.active_alerts.items()
            if current_time - v.timestamp < 24 * 3600
        }
    
    def get_active_alerts(self) -> List[DiagnosticAlert]:
        """Get all active alerts."""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 50) -> List[DiagnosticAlert]:
        """Get alert history."""
        return self.alert_history[-limit:]


__all__ = [
    "PredictiveDiagnosticsEngine",
    "DiagnosticAlert",
    "TelemetryTrend",
]









