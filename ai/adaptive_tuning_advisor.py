"""
Adaptive Tuning Advisor with Machine Learning

Enhanced version with:
- Historical pattern learning
- Multi-factor decision trees
- Confidence scoring
- Reinforcement learning concepts
- Per-vehicle adaptation
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
    from sklearn.tree import DecisionTreeClassifier
    ML_AVAILABLE = True
except Exception:
    ML_AVAILABLE = False
    RandomForestClassifier = None  # type: ignore
    GradientBoostingRegressor = None  # type: ignore
    DecisionTreeClassifier = None  # type: ignore

LOGGER = logging.getLogger(__name__)


@dataclass
class TuningRecommendation:
    """Enhanced tuning recommendation with confidence and learning."""

    rule_name: str
    message: str
    confidence: float  # 0-1
    priority: str  # "low", "medium", "high", "critical"
    expected_improvement: Optional[float] = None  # Estimated gain (hp, efficiency, etc.)
    historical_success_rate: float = 0.0  # Based on past applications
    conditions: Dict[str, float] = field(default_factory=dict)  # Conditions when this applies


class AdaptiveTuningAdvisor:
    """
    Adaptive tuning advisor with machine learning and historical learning.

    Features:
    - Rule-based system (baseline)
    - Historical pattern learning
    - Confidence scoring
    - Multi-factor analysis
    - Per-vehicle adaptation
    """

    def __init__(
        self,
        use_ml: bool = True,
        learning_enabled: bool = True,
    ) -> None:
        """
        Initialize adaptive tuning advisor.

        Args:
            use_ml: Enable machine learning models
            learning_enabled: Enable historical learning
        """
        self.use_ml = use_ml and ML_AVAILABLE
        self.learning_enabled = learning_enabled

        # Base rules (same as original)
        self.rules: List[Tuple[str, Callable, str]] = self._initialize_rules()

        # Historical data for learning
        self.recommendation_history: List[Dict] = []
        self.success_history: Dict[str, List[bool]] = defaultdict(list)
        self.condition_history: List[Dict] = []

        # ML models (if available)
        self.success_predictor = None
        self.confidence_estimator = None

        if self.use_ml:
            self._initialize_ml_models()

    def _initialize_rules(self) -> List[Tuple[str, Callable, str]]:
        """Initialize base rule set."""
        def _first(data: Mapping[str, float], *keys: str) -> float | None:
            for key in keys:
                value = data.get(key)
                if value is not None:
                    return value
            return None

        return [
            (
                "High RPM with low throttle",
                lambda d: d.get("RPM", 0) > 4000 and d.get("Throttle", 0) < 20,
                "Possible clutch slip or drivetrain loss detected.",
            ),
            (
                "High coolant temperature",
                lambda d: d.get("CoolantTemp", 0) > 105,
                "Engine running hot — inspect cooling system or enrich mixture.",
            ),
            (
                "Low speed, high throttle",
                lambda d: d.get("Speed", 0) < 10 and d.get("Throttle", 0) > 70,
                "Likely traction loss — consider traction control adjustments.",
            ),
            (
                "Low ethanol content for boost",
                lambda d: (_first(d, "Boost_Pressure", "Manifold_Pressure", "Boost") or 0) > 120
                and (_first(d, "Ethanol_Content", "FlexFuel_Percent", "Fuel_EthanolPercent") or 100) < 70,
                "Ethanol content is low for high boost—reduce load or switch to pump fuel.",
            ),
            (
                "Methanol flow insufficient",
                lambda d: (_first(d, "Boost_Pressure", "Manifold_Pressure", "Boost") or 0) > 120
                and (_first(d, "Methanol_Flow", "MethInjection_Duty") or 0) < 20,
                "Methanol injection duty is low while in boost—check pump, filters, or tank level.",
            ),
            (
                "Nitrous bottle pressure low",
                lambda d: (_first(d, "Nitrous_Solenoid_State", "Nitrous_Solenoid") or 0) > 0.5
                and (_first(d, "Nitrous_Bottle_Pressure", "Nitrous_Pressure") or 2000) < 850,
                "Nitrous system armed but bottle pressure is low—heat or refill bottle before next pass.",
            ),
            (
                "Transbrake dragging",
                lambda d: (_first(d, "TransBrake_State", "TransBrake") or 0) > 0.5
                and (d.get("Speed", 0) or 0) > 5,
                "Transbrake appears engaged while the car is moving—inspect release and wiring.",
            ),
        ]

    def _initialize_ml_models(self) -> None:
        """Initialize machine learning models."""
        if not ML_AVAILABLE:
            return

        try:
            # Model to predict if a recommendation will be successful
            # Features: conditions (RPM, temp, boost, etc.), recommendation type
            # Target: success (binary)
            self.success_predictor = RandomForestClassifier(
                n_estimators=50,
                max_depth=10,
                random_state=42,
            )

            # Model to estimate confidence in recommendations
            # Features: conditions, recommendation type, historical success rate
            # Target: confidence (0-1)
            self.confidence_estimator = GradientBoostingRegressor(
                n_estimators=50,
                max_depth=5,
                random_state=42,
            )

            LOGGER.info("ML models initialized")
        except Exception as e:
            LOGGER.warning(f"Failed to initialize ML models: {e}")
            self.use_ml = False

    def evaluate(
        self,
        data: Mapping[str, float],
        track_feedback: Optional[bool] = None,
    ) -> List[TuningRecommendation]:
        """
        Evaluate telemetry and return recommendations with confidence.

        Args:
            data: Current telemetry data
            track_feedback: Optional feedback on previous recommendation (True = worked, False = didn't)

        Returns:
            List of tuning recommendations with confidence scores
        """
        recommendations: List[TuningRecommendation] = []

        # Learn from feedback if provided
        if track_feedback is not None and self.learning_enabled and self.recommendation_history:
            self._update_learning(track_feedback)

        # Evaluate base rules
        for name, predicate, advice in self.rules:
            try:
                if predicate(data):
                    # Calculate confidence
                    confidence = self._calculate_confidence(name, data)

                    # Get historical success rate
                    success_rate = self._get_success_rate(name)

                    # Determine priority
                    priority = self._determine_priority(name, data, confidence)

                    # Estimate improvement (if ML available)
                    expected_improvement = None
                    if self.use_ml:
                        expected_improvement = self._estimate_improvement(name, data)

                    rec = TuningRecommendation(
                        rule_name=name,
                        message=advice,
                        confidence=confidence,
                        priority=priority,
                        expected_improvement=expected_improvement,
                        historical_success_rate=success_rate,
                        conditions=dict(data),
                    )
                    recommendations.append(rec)

                    # Record for learning
                    if self.learning_enabled:
                        self.recommendation_history.append({
                            "rule": name,
                            "conditions": dict(data),
                            "timestamp": time.time(),
                        })
            except Exception as e:
                LOGGER.debug(f"Rule evaluation failed for {name}: {e}")
                continue

        # Sort by priority and confidence
        recommendations.sort(key=lambda r: (
            {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(r.priority, 0),
            r.confidence
        ), reverse=True)

        return recommendations

    def _calculate_confidence(self, rule_name: str, data: Mapping[str, float]) -> float:
        """Calculate confidence in a recommendation."""
        base_confidence = 0.7  # Default confidence

        # Boost confidence based on historical success
        success_rate = self._get_success_rate(rule_name)
        if success_rate > 0.7:
            base_confidence = min(0.95, base_confidence + 0.2)
        elif success_rate < 0.3:
            base_confidence = max(0.3, base_confidence - 0.2)

        # Use ML model if available
        if self.use_ml and self.confidence_estimator and len(self.recommendation_history) > 50:
            try:
                # Extract features
                features = self._extract_features(data, rule_name)
                if features:
                    predicted_confidence = self.confidence_estimator.predict([features])[0]
                    base_confidence = float(np.clip(predicted_confidence, 0.0, 1.0))
            except Exception:
                pass

        return base_confidence

    def _get_success_rate(self, rule_name: str) -> float:
        """Get historical success rate for a rule."""
        if rule_name not in self.success_history or len(self.success_history[rule_name]) == 0:
            return 0.5  # Default: unknown

        successes = sum(self.success_history[rule_name])
        total = len(self.success_history[rule_name])
        return successes / total if total > 0 else 0.5

    def _determine_priority(self, rule_name: str, data: Mapping[str, float], confidence: float) -> str:
        """Determine priority level for recommendation."""
        # Critical: Safety issues
        critical_rules = ["High coolant temperature", "Nitrous bottle pressure low", "Transbrake dragging"]
        if rule_name in critical_rules:
            return "critical"

        # High: Performance issues with high confidence
        if confidence > 0.8:
            return "high"

        # Medium: Moderate confidence
        if confidence > 0.6:
            return "medium"

        # Low: Low confidence
        return "low"

    def _estimate_improvement(self, rule_name: str, data: Mapping[str, float]) -> Optional[float]:
        """Estimate expected improvement from recommendation."""
        # Simple heuristics (could be replaced with ML model)
        if "coolant" in rule_name.lower():
            return 5.0  # Estimated HP gain from fixing cooling
        elif "ethanol" in rule_name.lower() or "methanol" in rule_name.lower():
            return 10.0  # Estimated HP gain from proper fuel
        elif "nitrous" in rule_name.lower():
            return 15.0  # Estimated HP gain from proper nitrous
        return None

    def _extract_features(self, data: Mapping[str, float], rule_name: str) -> List[float]:
        """Extract features for ML models."""
        features = [
            data.get("RPM", 0.0),
            data.get("Throttle", 0.0),
            data.get("CoolantTemp", 90.0),
            data.get("Speed", 0.0),
            data.get("Boost_Pressure", 0.0),
            data.get("Lambda", 1.0),
        ]
        # Add rule name encoding (simple hash)
        rule_hash = hash(rule_name) % 100 / 100.0
        features.append(rule_hash)
        return features

    def _update_learning(self, feedback: bool) -> None:
        """Update learning from user feedback."""
        if not self.recommendation_history:
            return

        # Get last recommendation
        last_rec = self.recommendation_history[-1]
        rule_name = last_rec["rule"]

        # Record success/failure
        self.success_history[rule_name].append(feedback)

        # Keep only recent history (last 100)
        if len(self.success_history[rule_name]) > 100:
            self.success_history[rule_name].pop(0)

        # Retrain ML models periodically
        if len(self.recommendation_history) % 50 == 0 and self.use_ml:
            self._retrain_ml_models()

    def _retrain_ml_models(self) -> None:
        """Retrain ML models on accumulated data."""
        if not self.use_ml or len(self.recommendation_history) < 50:
            return

        try:
            # Prepare training data
            X = []
            y_success = []
            y_confidence = []

            for i, rec in enumerate(self.recommendation_history):
                if i < len(self.success_history.get(rec["rule"], [])):
                    features = self._extract_features(rec["conditions"], rec["rule"])
                    X.append(features)

                    # Success label
                    rule_name = rec["rule"]
                    if rule_name in self.success_history and len(self.success_history[rule_name]) > 0:
                        success = self.success_history[rule_name][-1]
                        y_success.append(1 if success else 0)
                    else:
                        y_success.append(0)

                    # Confidence label (based on success rate)
                    success_rate = self._get_success_rate(rule_name)
                    y_confidence.append(success_rate)

            if len(X) > 20:
                X = np.array(X)
                y_success = np.array(y_success)
                y_confidence = np.array(y_confidence)

                # Retrain models
                if self.success_predictor:
                    self.success_predictor.fit(X, y_success)

                if self.confidence_estimator:
                    self.confidence_estimator.fit(X, y_confidence)

                LOGGER.info("ML models retrained")
        except Exception as e:
            LOGGER.warning(f"ML model retraining failed: {e}")

    def get_statistics(self) -> Dict:
        """Get advisor statistics."""
        total_recommendations = len(self.recommendation_history)
        rule_stats = {}
        for rule_name, successes in self.success_history.items():
            if len(successes) > 0:
                rule_stats[rule_name] = {
                    "count": len(successes),
                    "success_rate": sum(successes) / len(successes),
                }

        return {
            "total_recommendations": total_recommendations,
            "rule_statistics": rule_stats,
            "learning_enabled": self.learning_enabled,
            "ml_enabled": self.use_ml,
        }


__all__ = ["AdaptiveTuningAdvisor", "TuningRecommendation"]

