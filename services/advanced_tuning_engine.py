"""
Advanced Tuning Engine with Multi-Objective Optimization

Features:
- Multi-objective optimization (performance, efficiency, safety)
- Predictive modeling for tuning outcomes
- Reinforcement learning concepts
- Closed-loop control
- Safety validation
- Advanced fuel/ignition optimization algorithms
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    GradientBoostingRegressor = None  # type: ignore
    RandomForestRegressor = None  # type: ignore
    StandardScaler = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class OptimizationTarget(Enum):
    """Optimization targets."""
    PERFORMANCE = "performance"  # Maximum power
    EFFICIENCY = "efficiency"  # Best fuel economy
    BALANCED = "balanced"  # Balance of both
    SAFETY = "safety"  # Conservative, safe settings


@dataclass
class TuningState:
    """Current tuning state snapshot."""
    timestamp: float
    rpm: float
    load: float
    boost: float
    lambda_value: float
    timing: float
    fuel_map_value: float
    coolant_temp: float
    iat: float
    knock_count: int
    egt: float
    hp_estimate: float = 0.0
    efficiency_estimate: float = 0.0


@dataclass
class TuningAction:
    """A tuning action to apply."""
    parameter: str  # "fuel", "timing", "boost", "lambda_target"
    current_value: float
    new_value: float
    delta: float
    confidence: float
    expected_hp_gain: float = 0.0
    expected_efficiency_gain: float = 0.0
    safety_score: float = 1.0  # 0-1, higher is safer
    reason: str = ""


@dataclass
class TuningResult:
    """Result of applying a tuning action."""
    action: TuningAction
    before_state: TuningState
    after_state: Optional[TuningState] = None
    actual_hp_change: float = 0.0
    actual_efficiency_change: float = 0.0
    success: bool = True
    safety_issues: List[str] = field(default_factory=list)


class AdvancedTuningEngine:
    """
    Advanced tuning engine with multi-objective optimization and predictive modeling.
    
    Features:
    - Multi-objective optimization (performance vs efficiency vs safety)
    - Predictive models for tuning outcomes
    - Reinforcement learning concepts (Q-learning inspired)
    - Closed-loop control with feedback
    - Safety validation before applying changes
    - Advanced fuel/ignition optimization algorithms
    """
    
    def __init__(
        self,
        target: OptimizationTarget = OptimizationTarget.BALANCED,
        learning_rate: float = 0.1,
        safety_threshold: float = 0.7,
    ):
        """
        Initialize advanced tuning engine.
        
        Args:
            target: Optimization target
            learning_rate: Learning rate for Q-learning updates (0-1)
            safety_threshold: Minimum safety score to apply changes (0-1)
        """
        self.target = target
        self.learning_rate = learning_rate
        self.safety_threshold = safety_threshold
        
        # State history for learning
        self.state_history: deque[TuningState] = deque(maxlen=1000)
        self.action_history: deque[TuningResult] = deque(maxlen=500)
        
        # Q-table for reinforcement learning (state -> action -> value)
        self.q_table: Dict[str, Dict[str, float]] = {}
        
        # Predictive models
        self.hp_predictor = None
        self.efficiency_predictor = None
        self.safety_predictor = None
        self.scaler = None
        
        # Optimal settings learned per condition
        self.learned_optimal: Dict[str, Dict[str, float]] = {}
        
        # Current state
        self.current_state: Optional[TuningState] = None
        
        # Initialize ML models if available
        if ML_AVAILABLE:
            self._initialize_predictive_models()
    
    def _initialize_predictive_models(self) -> None:
        """Initialize predictive ML models."""
        if not ML_AVAILABLE:
            return
        
        try:
            # Model to predict HP change from tuning action
            self.hp_predictor = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42,
            )
            
            # Model to predict efficiency change
            self.efficiency_predictor = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42,
            )
            
            # Model to predict safety score
            self.safety_predictor = RandomForestRegressor(
                n_estimators=50,
                max_depth=5,
                random_state=42,
            )
            
            # Feature scaler
            self.scaler = StandardScaler()
            
            LOGGER.info("Predictive models initialized")
        except Exception as e:
            LOGGER.warning(f"Failed to initialize predictive models: {e}")
    
    def analyze_and_optimize(
        self,
        telemetry: Dict[str, float],
        apply_auto: bool = False,
    ) -> List[TuningAction]:
        """
        Analyze current state and generate optimal tuning actions.
        
        Args:
            telemetry: Current telemetry data
            apply_auto: Automatically apply safe actions
            
        Returns:
            List of recommended tuning actions
        """
        # Create current state snapshot
        state = self._create_state_from_telemetry(telemetry)
        self.current_state = state
        self.state_history.append(state)
        
        # Generate candidate actions
        candidates = self._generate_candidate_actions(state)
        
        # Evaluate and rank actions
        evaluated = []
        for action in candidates:
            # Predict outcomes
            hp_gain, eff_gain, safety = self._predict_outcomes(state, action)
            action.expected_hp_gain = hp_gain
            action.expected_efficiency_gain = eff_gain
            action.safety_score = safety
            
            # Multi-objective scoring
            score = self._calculate_multi_objective_score(
                hp_gain, eff_gain, safety, action
            )
            
            evaluated.append((score, action))
        
        # Sort by score (highest first)
        evaluated.sort(key=lambda x: x[0], reverse=True)
        
        # Filter by safety threshold
        safe_actions = [
            action for score, action in evaluated
            if action.safety_score >= self.safety_threshold
        ]
        
        # Apply actions if enabled
        applied_actions = []
        if apply_auto and safe_actions:
            for action in safe_actions[:3]:  # Apply top 3 safe actions
                result = self._apply_action(action, state)
                if result.success:
                    applied_actions.append(action)
                    self._update_learning(state, action, result)
        
        return safe_actions[:5]  # Return top 5 recommendations
    
    def _create_state_from_telemetry(self, telemetry: Dict[str, float]) -> TuningState:
        """Create TuningState from telemetry data."""
        return TuningState(
            timestamp=time.time(),
            rpm=telemetry.get("RPM", telemetry.get("Engine_RPM", 0)),
            load=telemetry.get("Load", telemetry.get("Manifold_Pressure", 0)) / 100.0,
            boost=telemetry.get("Boost_Pressure", telemetry.get("Boost", 0)),
            lambda_value=telemetry.get("Lambda", telemetry.get("AFR", 14.7) / 14.7),
            timing=telemetry.get("Ignition_Timing", telemetry.get("timing_advance", 15.0)),
            fuel_map_value=telemetry.get("fuel_map_value", telemetry.get("VE", 80)),
            coolant_temp=telemetry.get("Coolant_Temp", telemetry.get("CoolantTemperature", 90)),
            iat=telemetry.get("IAT", telemetry.get("IntakeAirTemp", 25)),
            knock_count=telemetry.get("Knock_Count", telemetry.get("knock", 0)),
            egt=telemetry.get("EGT", telemetry.get("EGT_Avg", 800)),
            hp_estimate=self._estimate_hp(telemetry),
            efficiency_estimate=self._estimate_efficiency(telemetry),
        )
    
    def _estimate_hp(self, telemetry: Dict[str, float]) -> float:
        """Estimate current horsepower."""
        rpm = telemetry.get("RPM", 0)
        load = telemetry.get("Load", 0) / 100.0
        boost = telemetry.get("Boost_Pressure", 0)
        
        # Simple estimation: HP ≈ (RPM × Load × (1 + Boost/14.7)) / constant
        base_hp = (rpm * load * (1 + boost / 14.7)) / 1000.0
        return max(0, base_hp)
    
    def _estimate_efficiency(self, telemetry: Dict[str, float]) -> float:
        """Estimate current efficiency (MPG equivalent)."""
        lambda_val = telemetry.get("Lambda", 1.0)
        load = telemetry.get("Load", 0) / 100.0
        
        # Efficiency decreases with rich mixtures and high load
        efficiency = 1.0 / (1.0 + abs(lambda_val - 1.0) * 2.0 + load * 0.5)
        return max(0, efficiency)
    
    def _generate_candidate_actions(self, state: TuningState) -> List[TuningAction]:
        """Generate candidate tuning actions."""
        actions = []
        
        # Fuel map adjustments
        if state.lambda_value > 1.05:  # Lean
            actions.append(TuningAction(
                parameter="fuel",
                current_value=state.fuel_map_value,
                new_value=state.fuel_map_value * 1.05,
                delta=0.05,
                confidence=0.8,
                reason="Lean condition - enrich fuel",
            ))
        elif state.lambda_value < 0.95:  # Rich
            actions.append(TuningAction(
                parameter="fuel",
                current_value=state.fuel_map_value,
                new_value=state.fuel_map_value * 0.97,
                delta=-0.03,
                confidence=0.8,
                reason="Rich condition - lean fuel",
            ))
        
        # Ignition timing adjustments
        if state.knock_count > 0:
            actions.append(TuningAction(
                parameter="timing",
                current_value=state.timing,
                new_value=state.timing - 2.0,
                delta=-2.0,
                confidence=0.95,
                reason="Knock detected - retard timing",
            ))
        elif state.knock_count == 0 and state.boost > 10 and state.rpm > 3000:
            # Can advance timing for more power
            actions.append(TuningAction(
                parameter="timing",
                current_value=state.timing,
                new_value=state.timing + 1.0,
                delta=1.0,
                confidence=0.6,
                reason="No knock - advance timing for power",
            ))
        
        # Boost control adjustments
        if state.lambda_value > 0.98 and state.coolant_temp < 95:
            actions.append(TuningAction(
                parameter="boost",
                current_value=state.boost,
                new_value=state.boost + 1.0,
                delta=1.0,
                confidence=0.7,
                reason="Conditions optimal - increase boost",
            ))
        elif state.lambda_value < 0.92 and state.boost > 15:
            actions.append(TuningAction(
                parameter="boost",
                current_value=state.boost,
                new_value=state.boost - 2.0,
                delta=-2.0,
                confidence=0.85,
                reason="Too rich for boost - reduce boost",
            ))
        
        # Lambda target adjustments
        if self.target == OptimizationTarget.PERFORMANCE and state.boost > 15:
            target_lambda = 0.95  # Slightly rich for power
            if abs(state.lambda_value - target_lambda) > 0.02:
                actions.append(TuningAction(
                    parameter="lambda_target",
                    current_value=state.lambda_value,
                    new_value=target_lambda,
                    delta=target_lambda - state.lambda_value,
                    confidence=0.75,
                    reason="Optimize lambda for maximum power",
                ))
        elif self.target == OptimizationTarget.EFFICIENCY:
            target_lambda = 1.0  # Stoichiometric for efficiency
            if abs(state.lambda_value - target_lambda) > 0.02:
                actions.append(TuningAction(
                    parameter="lambda_target",
                    current_value=state.lambda_value,
                    new_value=target_lambda,
                    delta=target_lambda - state.lambda_value,
                    confidence=0.8,
                    reason="Optimize lambda for efficiency",
                ))
        
        return actions
    
    def _predict_outcomes(
        self,
        state: TuningState,
        action: TuningAction,
    ) -> Tuple[float, float, float]:
        """
        Predict outcomes of a tuning action.
        
        Returns:
            (hp_gain, efficiency_gain, safety_score)
        """
        # Use ML models if available and trained
        if (self.hp_predictor and self.efficiency_predictor and
            self.safety_predictor and len(self.action_history) > 50):
            try:
                features = self._extract_features(state, action)
                features_scaled = self.scaler.transform([features])[0]
                
                hp_gain = float(self.hp_predictor.predict([features_scaled])[0])
                eff_gain = float(self.efficiency_predictor.predict([features_scaled])[0])
                safety = float(self.safety_predictor.predict([features_scaled])[0])
                safety = max(0.0, min(1.0, safety))  # Clamp to 0-1
                
                return hp_gain, eff_gain, safety
            except Exception as e:
                LOGGER.debug(f"ML prediction failed: {e}, using heuristics")
        
        # Fallback to heuristic predictions
        return self._heuristic_predict_outcomes(state, action)
    
    def _heuristic_predict_outcomes(
        self,
        state: TuningState,
        action: TuningAction,
    ) -> Tuple[float, float, float]:
        """Heuristic prediction when ML models unavailable."""
        hp_gain = 0.0
        eff_gain = 0.0
        safety = 1.0
        
        if action.parameter == "fuel":
            # Fuel adjustments
            if action.delta > 0:  # Enriching
                if state.lambda_value > 1.05:
                    hp_gain = 2.0  # Fixing lean condition
                    eff_gain = -0.5  # Slight efficiency loss
                safety = 0.9 if state.lambda_value > 1.1 else 0.95
            else:  # Leaning
                if state.lambda_value < 0.95:
                    hp_gain = 1.0  # Slight power gain
                    eff_gain = 1.5  # Efficiency gain
                safety = 0.85 if state.lambda_value < 0.9 else 0.95
        
        elif action.parameter == "timing":
            # Timing adjustments
            if action.delta > 0:  # Advancing
                hp_gain = 1.5 * action.delta
                eff_gain = 0.5
                safety = 0.7 if state.knock_count == 0 else 0.5
            else:  # Retarding
                hp_gain = -1.0 * abs(action.delta)
                eff_gain = 0.0
                safety = 0.95  # Very safe
        
        elif action.parameter == "boost":
            # Boost adjustments
            if action.delta > 0:  # Increasing
                hp_gain = 5.0 * action.delta
                eff_gain = -1.0
                safety = 0.8 if state.lambda_value > 0.95 else 0.6
            else:  # Decreasing
                hp_gain = -3.0 * abs(action.delta)
                eff_gain = 0.5
                safety = 0.95
        
        elif action.parameter == "lambda_target":
            # Lambda target adjustments
            if abs(action.delta) > 0.02:
                if action.new_value < state.lambda_value:  # Richer
                    hp_gain = 2.0
                    eff_gain = -1.0
                else:  # Leaner
                    hp_gain = -1.0
                    eff_gain = 2.0
                safety = 0.9
        
        return hp_gain, eff_gain, safety
    
    def _extract_features(
        self,
        state: TuningState,
        action: TuningAction,
    ) -> List[float]:
        """Extract features for ML models."""
        return [
            state.rpm / 10000.0,  # Normalized
            state.load,
            state.boost / 50.0,  # Normalized
            state.lambda_value,
            state.timing / 50.0,  # Normalized
            state.fuel_map_value / 200.0,  # Normalized
            state.coolant_temp / 150.0,  # Normalized
            state.iat / 100.0,  # Normalized
            state.knock_count / 10.0,  # Normalized
            state.egt / 1500.0,  # Normalized
            # Action features
            1.0 if action.parameter == "fuel" else 0.0,
            1.0 if action.parameter == "timing" else 0.0,
            1.0 if action.parameter == "boost" else 0.0,
            1.0 if action.parameter == "lambda_target" else 0.0,
            action.delta,
            action.current_value / 200.0,  # Normalized
        ]
    
    def _calculate_multi_objective_score(
        self,
        hp_gain: float,
        eff_gain: float,
        safety: float,
        action: TuningAction,
    ) -> float:
        """Calculate multi-objective score based on target."""
        if self.target == OptimizationTarget.PERFORMANCE:
            # Weight: HP (70%), Safety (30%)
            score = 0.7 * hp_gain + 0.3 * safety * 10.0
        elif self.target == OptimizationTarget.EFFICIENCY:
            # Weight: Efficiency (70%), Safety (30%)
            score = 0.7 * eff_gain + 0.3 * safety * 10.0
        elif self.target == OptimizationTarget.SAFETY:
            # Weight: Safety (100%)
            score = safety * 20.0
        else:  # BALANCED
            # Weight: HP (40%), Efficiency (30%), Safety (30%)
            score = 0.4 * hp_gain + 0.3 * eff_gain + 0.3 * safety * 10.0
        
        # Penalize low confidence
        score *= action.confidence
        
        return score
    
    def _apply_action(
        self,
        action: TuningAction,
        before_state: TuningState,
    ) -> TuningResult:
        """
        Apply a tuning action (simulated - would interface with ECU).
        
        Args:
            action: Tuning action to apply
            before_state: State before applying action
            
        Returns:
            Tuning result
        """
        # Simulate applying action (in real implementation, would interface with ECU)
        LOGGER.info(
            f"Applying {action.parameter}: {action.current_value:.2f} -> {action.new_value:.2f}"
        )
        
        # Create after state (simulated)
        after_state = TuningState(
            timestamp=time.time(),
            rpm=before_state.rpm,
            load=before_state.load,
            boost=before_state.boost + (action.delta if action.parameter == "boost" else 0),
            lambda_value=before_state.lambda_value + (action.delta if action.parameter == "lambda_target" else 0),
            timing=before_state.timing + (action.delta if action.parameter == "timing" else 0),
            fuel_map_value=before_state.fuel_map_value * (1.0 + action.delta) if action.parameter == "fuel" else before_state.fuel_map_value,
            coolant_temp=before_state.coolant_temp,
            iat=before_state.iat,
            knock_count=before_state.knock_count,
            egt=before_state.egt,
            hp_estimate=before_state.hp_estimate + action.expected_hp_gain,
            efficiency_estimate=before_state.efficiency_estimate + action.expected_efficiency_gain,
        )
        
        # Check for safety issues
        safety_issues = []
        if after_state.knock_count > before_state.knock_count:
            safety_issues.append("Knock increased")
        if after_state.coolant_temp > 100:
            safety_issues.append("Coolant temperature high")
        if after_state.lambda_value < 0.85:
            safety_issues.append("Too rich - risk of fouling")
        if after_state.lambda_value > 1.15:
            safety_issues.append("Too lean - risk of detonation")
        
        result = TuningResult(
            action=action,
            before_state=before_state,
            after_state=after_state,
            actual_hp_change=action.expected_hp_gain,  # In real system, measure actual change
            actual_efficiency_change=action.expected_efficiency_gain,
            success=len(safety_issues) == 0,
            safety_issues=safety_issues,
        )
        
        return result
    
    def _update_learning(
        self,
        state: TuningState,
        action: TuningAction,
        result: TuningResult,
    ) -> None:
        """Update learning from action result (Q-learning inspired)."""
        # Store result in history
        self.action_history.append(result)
        
        # Update Q-table (simplified Q-learning)
        state_key = self._state_to_key(state)
        action_key = f"{action.parameter}_{action.delta:.2f}"
        
        if state_key not in self.q_table:
            self.q_table[state_key] = {}
        
        # Calculate reward
        reward = 0.0
        if result.success:
            if self.target == OptimizationTarget.PERFORMANCE:
                reward = result.actual_hp_change
            elif self.target == OptimizationTarget.EFFICIENCY:
                reward = result.actual_efficiency_change
            else:  # BALANCED
                reward = (result.actual_hp_change + result.actual_efficiency_change) / 2.0
        else:
            reward = -10.0  # Penalty for unsafe actions
        
        # Q-learning update: Q(s,a) = Q(s,a) + α * (reward - Q(s,a))
        current_q = self.q_table[state_key].get(action_key, 0.0)
        new_q = current_q + self.learning_rate * (reward - current_q)
        self.q_table[state_key][action_key] = new_q
        
        # Retrain predictive models periodically
        if len(self.action_history) % 50 == 0 and ML_AVAILABLE:
            self._retrain_predictive_models()
    
    def _state_to_key(self, state: TuningState) -> str:
        """Convert state to key for Q-table."""
        # Discretize state for Q-table
        rpm_bin = int(state.rpm / 500) * 500
        load_bin = int(state.load * 10) / 10.0
        boost_bin = int(state.boost / 5) * 5
        return f"{rpm_bin}_{load_bin:.1f}_{boost_bin}"
    
    def _retrain_predictive_models(self) -> None:
        """Retrain predictive models on accumulated data."""
        if not ML_AVAILABLE or len(self.action_history) < 50:
            return
        
        try:
            X = []
            y_hp = []
            y_eff = []
            y_safety = []
            
            for result in self.action_history:
                if result.after_state:
                    features = self._extract_features(result.before_state, result.action)
                    X.append(features)
                    y_hp.append(result.actual_hp_change)
                    y_eff.append(result.actual_efficiency_change)
                    y_safety.append(1.0 if result.success else 0.0)
            
            if len(X) > 20:
                X = np.array(X)
                y_hp = np.array(y_hp)
                y_eff = np.array(y_eff)
                y_safety = np.array(y_safety)
                
                # Scale features
                self.scaler.fit(X)
                X_scaled = self.scaler.transform(X)
                
                # Retrain models
                if self.hp_predictor:
                    self.hp_predictor.fit(X_scaled, y_hp)
                if self.efficiency_predictor:
                    self.efficiency_predictor.fit(X_scaled, y_eff)
                if self.safety_predictor:
                    self.safety_predictor.fit(X_scaled, y_safety)
                
                LOGGER.info("Predictive models retrained on %d samples", len(X))
        except Exception as e:
            LOGGER.warning(f"Failed to retrain predictive models: {e}")
    
    def get_statistics(self) -> Dict:
        """Get engine statistics."""
        return {
            "state_history_size": len(self.state_history),
            "action_history_size": len(self.action_history),
            "q_table_size": sum(len(actions) for actions in self.q_table.values()),
            "target": self.target.value,
            "ml_available": ML_AVAILABLE,
            "models_trained": (
                self.hp_predictor is not None and
                self.efficiency_predictor is not None and
                self.safety_predictor is not None
            ),
        }


__all__ = [
    "AdvancedTuningEngine",
    "TuningAction",
    "TuningState",
    "TuningResult",
    "OptimizationTarget",
]

