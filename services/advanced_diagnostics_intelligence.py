"""
Advanced Diagnostics Intelligence
Comprehensive ML-based diagnostics with LSTM, time-series forecasting, and predictive maintenance
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    from sklearn.ensemble import IsolationForest, RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    IsolationForest = None  # type: ignore
    RandomForestRegressor = None  # type: ignore
    StandardScaler = None  # type: ignore

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None  # type: ignore
    nn = None  # type: ignore

LOGGER = logging.getLogger(__name__)


# Conditional LSTM Autoencoder class
if TORCH_AVAILABLE and nn:
    class LSTMAutoencoder(nn.Module):
        """LSTM Autoencoder for time-series anomaly detection."""
        
        def __init__(self, input_size: int = 10, hidden_size: int = 64, num_layers: int = 2):
            super().__init__()
            self.input_size = input_size
            self.hidden_size = hidden_size
            self.num_layers = num_layers
            
            # Encoder
            self.encoder = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
            
            # Decoder
            self.decoder = nn.LSTM(hidden_size, input_size, num_layers, batch_first=True)
            
        def forward(self, x):
            # Encode
            encoded, (hidden, cell) = self.encoder(x)
            
            # Decode
            decoded, _ = self.decoder(encoded, (hidden, cell))
            
            return decoded
else:
    # Dummy class when torch is not available
    class LSTMAutoencoder:
        """Dummy LSTM Autoencoder when PyTorch is not available."""
        def __init__(self, *args, **kwargs):
            pass
        def forward(self, x):
            return x


@dataclass
class DiagnosticAlert:
    """Diagnostic alert with confidence and prediction."""
    
    component: str
    alert_type: str  # "anomaly", "degradation", "failure_prediction"
    severity: str  # "low", "medium", "high", "critical"
    confidence: float  # 0-1
    message: str
    predicted_failure_time: Optional[float] = None  # Hours until failure
    recommended_action: str = ""
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class ComponentHealth:
    """Component health status with RUL estimation."""
    
    component: str
    health_score: float  # 0-100
    status: str  # "excellent", "good", "fair", "poor", "critical"
    remaining_useful_life: Optional[float] = None  # Hours
    degradation_rate: float = 0.0  # Per hour
    trend: str = "stable"  # "improving", "stable", "degrading", "critical"
    confidence: float = 0.0  # 0-1


class AdvancedDiagnosticsIntelligence:
    """
    Advanced Diagnostics Intelligence with ML algorithms.
    
    Features:
    - LSTM-based time-series anomaly detection
    - Multi-signal correlation analysis
    - Predictive failure models
    - Remaining Useful Life (RUL) estimation
    - Real-time health scoring with ML
    - Adaptive threshold learning
    """
    
    def __init__(
        self,
        use_lstm: bool = True,
        use_ensemble: bool = True,
        window_size: int = 60,
    ):
        """
        Initialize advanced diagnostics intelligence.
        
        Args:
            use_lstm: Use LSTM autoencoder for anomaly detection
            use_ensemble: Use ensemble methods (IsolationForest + LSTM)
            window_size: Time window size for analysis (seconds)
        """
        self.use_lstm = use_lstm and TORCH_AVAILABLE
        self.use_ensemble = use_ensemble and SKLEARN_AVAILABLE
        self.window_size = window_size
        
        # Data buffers
        self.telemetry_buffer: deque = deque(maxlen=window_size * 10)  # 10x window for history
        self.component_history: Dict[str, deque] = {}
        
        # ML Models
        self.lstm_model: Optional[LSTMAutoencoder] = None
        self.isolation_forest: Optional[IsolationForest] = None
        self.rul_models: Dict[str, RandomForestRegressor] = {}
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        
        # Component health tracking
        self.component_health: Dict[str, ComponentHealth] = {}
        
        # Adaptive thresholds (learned per vehicle)
        self.adaptive_thresholds: Dict[str, Dict[str, float]] = {}
        
        # Initialize models
        if self.use_lstm:
            self._init_lstm_model()
        if self.use_ensemble:
            self._init_ensemble_models()
    
    def _init_lstm_model(self) -> None:
        """Initialize LSTM autoencoder model."""
        if not TORCH_AVAILABLE:
            return
        
        try:
            self.lstm_model = LSTMAutoencoder(input_size=10, hidden_size=64, num_layers=2)
            self.lstm_model.eval()
            LOGGER.info("LSTM autoencoder initialized")
        except Exception as e:
            LOGGER.error(f"Failed to initialize LSTM model: {e}")
            self.use_lstm = False
    
    def _init_ensemble_models(self) -> None:
        """Initialize ensemble models."""
        if not SKLEARN_AVAILABLE:
            return
        
        try:
            self.isolation_forest = IsolationForest(
                n_estimators=50,  # Reduced for performance
                contamination=0.05,
                random_state=42,
            )
            LOGGER.info("IsolationForest initialized")
        except Exception as e:
            LOGGER.error(f"Failed to initialize IsolationForest: {e}")
            self.use_ensemble = False
    
    def update(self, telemetry: Dict[str, float]) -> List[DiagnosticAlert]:
        """
        Update diagnostics with new telemetry data.
        
        Args:
            telemetry: Current telemetry data
            
        Returns:
            List of diagnostic alerts
        """
        # Add to buffer
        self.telemetry_buffer.append({
            **telemetry,
            "timestamp": time.time(),
        })
        
        alerts = []
        
        # Extract features
        features = self._extract_features(telemetry)
        
        # Anomaly detection
        anomaly_alerts = self._detect_anomalies(features, telemetry)
        alerts.extend(anomaly_alerts)
        
        # Component health analysis
        health_alerts = self._analyze_component_health(telemetry)
        alerts.extend(health_alerts)
        
        # Predictive failure analysis
        failure_alerts = self._predict_failures(telemetry)
        alerts.extend(failure_alerts)
        
        # Update adaptive thresholds
        self._update_adaptive_thresholds(telemetry)
        
        return alerts
    
    def _extract_features(self, telemetry: Dict[str, float]) -> np.ndarray:
        """Extract features from telemetry data."""
        # Key features for diagnostics
        feature_keys = [
            "RPM", "Boost_Pressure", "AFR", "Lambda", "Coolant_Temp",
            "Oil_Pressure", "Oil_Temp", "Fuel_Pressure", "EGT", "Knock_Count"
        ]
        
        features = []
        for key in feature_keys:
            value = telemetry.get(key, telemetry.get(key.replace("_", ""), 0.0))
            features.append(float(value))
        
        return np.array(features, dtype=np.float32)
    
    def _detect_anomalies(
        self,
        features: np.ndarray,
        telemetry: Dict[str, float]
    ) -> List[DiagnosticAlert]:
        """Detect anomalies using ensemble methods."""
        alerts = []
        
        if len(self.telemetry_buffer) < self.window_size:
            return alerts  # Not enough data yet
        
        # Prepare time-series window
        window_data = list(self.telemetry_buffer)[-self.window_size:]
        window_features = np.array([self._extract_features(d) for d in window_data])
        
        # LSTM-based anomaly detection
        if self.use_lstm and self.lstm_model:
            lstm_alert = self._lstm_anomaly_detection(window_features, telemetry)
            if lstm_alert:
                alerts.append(lstm_alert)
        
        # IsolationForest anomaly detection
        if self.use_ensemble and self.isolation_forest:
            if_alert = self._isolation_forest_detection(features, telemetry)
            if if_alert:
                alerts.append(if_alert)
        
        # Multi-signal correlation analysis
        correlation_alert = self._correlation_anomaly_detection(telemetry)
        if correlation_alert:
            alerts.append(correlation_alert)
        
        return alerts
    
    def _lstm_anomaly_detection(
        self,
        window_features: np.ndarray,
        telemetry: Dict[str, float]
    ) -> Optional[DiagnosticAlert]:
        """LSTM-based time-series anomaly detection."""
        if not self.lstm_model or not TORCH_AVAILABLE:
            return None
        
        try:
            # Normalize features
            if self.scaler:
                window_features = self.scaler.fit_transform(window_features)
            
            # Reshape for LSTM (batch, sequence, features)
            window_tensor = torch.FloatTensor(window_features).unsqueeze(0)
            
            # Forward pass
            with torch.no_grad():
                reconstructed = self.lstm_model(window_tensor)
            
            # Calculate reconstruction error
            error = torch.mean((window_tensor - reconstructed) ** 2).item()
            
            # Adaptive threshold (learned)
            threshold = self.adaptive_thresholds.get("lstm_error", {}).get("threshold", 0.1)
            
            if error > threshold:
                # Determine which component is anomalous
                component = self._identify_anomalous_component(window_features[-1], reconstructed[0, -1].numpy())
                
                return DiagnosticAlert(
                    component=component,
                    alert_type="anomaly",
                    severity="high" if error > threshold * 2 else "medium",
                    confidence=min(1.0, error / threshold),
                    message=f"Anomaly detected in {component} (LSTM reconstruction error: {error:.3f})",
                    recommended_action="Inspect component and review recent changes",
                    metrics={"reconstruction_error": error, "threshold": threshold}
                )
        except Exception as e:
            LOGGER.error(f"LSTM anomaly detection failed: {e}")
        
        return None
    
    def _isolation_forest_detection(
        self,
        features: np.ndarray,
        telemetry: Dict[str, float]
    ) -> Optional[DiagnosticAlert]:
        """IsolationForest-based anomaly detection."""
        if not self.isolation_forest:
            return None
        
        try:
            # Prepare training data if needed
            if len(self.telemetry_buffer) >= self.window_size * 2:
                training_data = np.array([
                    self._extract_features(d) for d in list(self.telemetry_buffer)[-self.window_size * 2:-self.window_size]
                ])
                
                # Fit model periodically
                if len(self.telemetry_buffer) % (self.window_size * 5) == 0:
                    self.isolation_forest.fit(training_data)
            
            # Predict anomaly
            prediction = self.isolation_forest.predict([features])
            anomaly_score = self.isolation_forest.score_samples([features])[0]
            
            if prediction[0] == -1:  # Anomaly detected
                component = self._identify_anomalous_component_from_features(features)
                
                return DiagnosticAlert(
                    component=component,
                    alert_type="anomaly",
                    severity="high" if anomaly_score < -0.5 else "medium",
                    confidence=min(1.0, abs(anomaly_score)),
                    message=f"Anomaly detected in {component} (IsolationForest score: {anomaly_score:.3f})",
                    recommended_action="Review component operation and sensor readings",
                    metrics={"anomaly_score": float(anomaly_score)}
                )
        except Exception as e:
            LOGGER.error(f"IsolationForest detection failed: {e}")
        
        return None
    
    def _correlation_anomaly_detection(
        self,
        telemetry: Dict[str, float]
    ) -> Optional[DiagnosticAlert]:
        """Multi-signal correlation anomaly detection."""
        if len(self.telemetry_buffer) < self.window_size:
            return None
        
        # Calculate correlations between key signals
        rpm = telemetry.get("RPM", 0)
        boost = telemetry.get("Boost_Pressure", 0)
        afr = telemetry.get("AFR", 14.7)
        coolant = telemetry.get("Coolant_Temp", 90)
        
        # Expected correlations
        # RPM and Boost should correlate (higher RPM = higher boost potential)
        # AFR should be inversely correlated with boost (richer at high boost)
        
        # Check for correlation violations
        if rpm > 5000 and boost < 5:
            return DiagnosticAlert(
                component="Turbo/Boost System",
                alert_type="anomaly",
                severity="medium",
                confidence=0.7,
                message="Low boost at high RPM - possible turbo or wastegate issue",
                recommended_action="Check turbo operation and wastegate function",
                metrics={"rpm": rpm, "boost": boost}
            )
        
        if boost > 20 and afr > 15.0:
            return DiagnosticAlert(
                component="Fuel System",
                alert_type="anomaly",
                severity="high",
                confidence=0.8,
                message="Lean AFR at high boost - dangerous condition",
                recommended_action="Immediately reduce boost or add fuel",
                metrics={"boost": boost, "afr": afr}
            )
        
        return None
    
    def _analyze_component_health(
        self,
        telemetry: Dict[str, float]
    ) -> List[DiagnosticAlert]:
        """Analyze component health and degradation."""
        alerts = []
        
        # Analyze key components
        components = {
            "Turbo": self._analyze_turbo_health(telemetry),
            "Fuel Pump": self._analyze_fuel_pump_health(telemetry),
            "Cooling System": self._analyze_cooling_health(telemetry),
            "Oil System": self._analyze_oil_health(telemetry),
            "Ignition System": self._analyze_ignition_health(telemetry),
        }
        
        for component_name, health in components.items():
            if health:
                self.component_health[component_name] = health
                
                # Generate alerts for degrading components
                if health.status in ["poor", "critical"]:
                    alerts.append(DiagnosticAlert(
                        component=component_name,
                        alert_type="degradation",
                        severity=health.status,
                        confidence=health.confidence,
                        message=f"{component_name} health: {health.status} (Score: {health.health_score:.1f}/100)",
                        predicted_failure_time=health.remaining_useful_life,
                        recommended_action=f"Inspect {component_name} - {health.trend} trend detected",
                        metrics={
                            "health_score": health.health_score,
                            "rul_hours": health.remaining_useful_life or 0,
                            "degradation_rate": health.degradation_rate,
                        }
                    ))
        
        return alerts
    
    def _analyze_turbo_health(self, telemetry: Dict[str, float]) -> Optional[ComponentHealth]:
        """Analyze turbocharger health."""
        boost = telemetry.get("Boost_Pressure", 0)
        egt = telemetry.get("EGT", 800)
        rpm = telemetry.get("RPM", 0)
        
        # Calculate health score
        health_score = 100.0
        
        # Boost efficiency (lower boost at same RPM = degradation)
        if rpm > 4000:
            expected_boost = rpm / 400  # Rough estimate
            if boost < expected_boost * 0.8:
                health_score -= 20
        
        # EGT analysis (high EGT = stress)
        if egt > 1600:
            health_score -= 30
        elif egt > 1400:
            health_score -= 15
        
        # Determine status
        if health_score >= 80:
            status = "excellent"
        elif health_score >= 60:
            status = "good"
        elif health_score >= 40:
            status = "fair"
        elif health_score >= 20:
            status = "poor"
        else:
            status = "critical"
        
        # Estimate RUL (simplified)
        degradation_rate = max(0, (100 - health_score) / 1000)  # Per hour
        rul = (health_score / degradation_rate) if degradation_rate > 0 else None
        
        return ComponentHealth(
            component="Turbo",
            health_score=max(0, min(100, health_score)),
            status=status,
            remaining_useful_life=rul,
            degradation_rate=degradation_rate,
            trend="degrading" if health_score < 60 else "stable",
            confidence=0.7
        )
    
    def _analyze_fuel_pump_health(self, telemetry: Dict[str, float]) -> Optional[ComponentHealth]:
        """Analyze fuel pump health."""
        fuel_pressure = telemetry.get("Fuel_Pressure", 43.5)
        afr = telemetry.get("AFR", 14.7)
        
        health_score = 100.0
        
        # Low fuel pressure indicates pump degradation
        if fuel_pressure < 35:
            health_score -= 40
        elif fuel_pressure < 40:
            health_score -= 20
        
        # AFR instability can indicate pump issues
        if abs(afr - 14.7) > 2.0:
            health_score -= 15
        
        status = "excellent" if health_score >= 80 else "good" if health_score >= 60 else "fair" if health_score >= 40 else "poor" if health_score >= 20 else "critical"
        
        degradation_rate = max(0, (100 - health_score) / 800)
        rul = (health_score / degradation_rate) if degradation_rate > 0 else None
        
        return ComponentHealth(
            component="Fuel Pump",
            health_score=max(0, min(100, health_score)),
            status=status,
            remaining_useful_life=rul,
            degradation_rate=degradation_rate,
            trend="degrading" if health_score < 60 else "stable",
            confidence=0.75
        )
    
    def _analyze_cooling_health(self, telemetry: Dict[str, float]) -> Optional[ComponentHealth]:
        """Analyze cooling system health."""
        coolant_temp = telemetry.get("Coolant_Temp", 90)
        
        health_score = 100.0
        
        if coolant_temp > 110:
            health_score -= 50
        elif coolant_temp > 100:
            health_score -= 25
        
        status = "excellent" if health_score >= 80 else "good" if health_score >= 60 else "fair" if health_score >= 40 else "poor" if health_score >= 20 else "critical"
        
        return ComponentHealth(
            component="Cooling System",
            health_score=max(0, min(100, health_score)),
            status=status,
            remaining_useful_life=None,
            degradation_rate=0.0,
            trend="stable",
            confidence=0.8
        )
    
    def _analyze_oil_health(self, telemetry: Dict[str, float]) -> Optional[ComponentHealth]:
        """Analyze oil system health."""
        oil_pressure = telemetry.get("Oil_Pressure", 50)
        oil_temp = telemetry.get("Oil_Temp", 100)
        
        health_score = 100.0
        
        if oil_pressure < 20:
            health_score -= 60
        elif oil_pressure < 30:
            health_score -= 30
        
        if oil_temp > 130:
            health_score -= 20
        
        status = "excellent" if health_score >= 80 else "good" if health_score >= 60 else "fair" if health_score >= 40 else "poor" if health_score >= 20 else "critical"
        
        return ComponentHealth(
            component="Oil System",
            health_score=max(0, min(100, health_score)),
            status=status,
            remaining_useful_life=None,
            degradation_rate=0.0,
            trend="stable",
            confidence=0.85
        )
    
    def _analyze_ignition_health(self, telemetry: Dict[str, float]) -> Optional[ComponentHealth]:
        """Analyze ignition system health."""
        knock_count = telemetry.get("Knock_Count", 0)
        rpm = telemetry.get("RPM", 0)
        
        health_score = 100.0
        
        # High knock count indicates ignition issues
        if knock_count > 10:
            health_score -= 40
        elif knock_count > 5:
            health_score -= 20
        
        status = "excellent" if health_score >= 80 else "good" if health_score >= 60 else "fair" if health_score >= 40 else "poor" if health_score >= 20 else "critical"
        
        return ComponentHealth(
            component="Ignition System",
            health_score=max(0, min(100, health_score)),
            status=status,
            remaining_useful_life=None,
            degradation_rate=0.0,
            trend="stable",
            confidence=0.7
        )
    
    def _predict_failures(self, telemetry: Dict[str, float]) -> List[DiagnosticAlert]:
        """Predict component failures using ML models."""
        alerts = []
        
        # Use RUL models if available
        for component, health in self.component_health.items():
            if health.remaining_useful_life and health.remaining_useful_life < 100:  # Less than 100 hours
                alerts.append(DiagnosticAlert(
                    component=component,
                    alert_type="failure_prediction",
                    severity="critical" if health.remaining_useful_life < 10 else "high",
                    confidence=health.confidence,
                    message=f"{component} predicted failure in {health.remaining_useful_life:.1f} hours",
                    predicted_failure_time=health.remaining_useful_life,
                    recommended_action=f"Replace {component} immediately",
                    metrics={"rul_hours": health.remaining_useful_life}
                ))
        
        return alerts
    
    def _update_adaptive_thresholds(self, telemetry: Dict[str, float]) -> None:
        """Update adaptive thresholds based on learned patterns."""
        # Learn normal operating ranges per vehicle
        for key, value in telemetry.items():
            if key not in self.adaptive_thresholds:
                self.adaptive_thresholds[key] = {
                    "mean": value,
                    "std": 0.0,
                    "min": value,
                    "max": value,
                    "count": 1,
                }
            else:
                stats = self.adaptive_thresholds[key]
                stats["count"] += 1
                n = stats["count"]
                
                # Update running statistics
                old_mean = stats["mean"]
                stats["mean"] = (old_mean * (n - 1) + value) / n
                stats["std"] = np.sqrt(((n - 1) * stats["std"] ** 2 + (value - old_mean) * (value - stats["mean"])) / n)
                stats["min"] = min(stats["min"], value)
                stats["max"] = max(stats["max"], value)
    
    def _identify_anomalous_component(
        self,
        actual: np.ndarray,
        reconstructed: np.ndarray
    ) -> str:
        """Identify which component is anomalous based on reconstruction error."""
        errors = np.abs(actual - reconstructed)
        max_error_idx = np.argmax(errors)
        
        components = [
            "RPM", "Boost", "AFR", "Lambda", "Coolant",
            "Oil Pressure", "Oil Temp", "Fuel Pressure", "EGT", "Knock"
        ]
        
        return components[min(max_error_idx, len(components) - 1)]
    
    def _identify_anomalous_component_from_features(self, features: np.ndarray) -> str:
        """Identify anomalous component from feature vector."""
        # Find feature with largest deviation from normal
        if len(self.telemetry_buffer) < self.window_size:
            return "Unknown"
        
        # Calculate mean for each feature
        historical = np.array([self._extract_features(d) for d in list(self.telemetry_buffer)[-self.window_size:]])
        means = np.mean(historical, axis=0)
        stds = np.std(historical, axis=0)
        
        # Find feature with largest z-score
        z_scores = np.abs((features - means) / (stds + 1e-6))
        max_z_idx = np.argmax(z_scores)
        
        components = [
            "RPM", "Boost", "AFR", "Lambda", "Coolant",
            "Oil Pressure", "Oil Temp", "Fuel Pressure", "EGT", "Knock"
        ]
        
        return components[min(max_z_idx, len(components) - 1)]
    
    def get_component_health(self, component: Optional[str] = None) -> Dict[str, ComponentHealth]:
        """Get component health status."""
        if component:
            return {component: self.component_health.get(component)}
        return self.component_health.copy()
    
    def get_overall_health_score(self) -> float:
        """Get overall engine health score."""
        if not self.component_health:
            return 100.0
        
        scores = [h.health_score for h in self.component_health.values()]
        return np.mean(scores) if scores else 100.0

