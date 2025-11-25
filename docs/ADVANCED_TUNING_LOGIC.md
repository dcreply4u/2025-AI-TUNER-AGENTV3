# Advanced Tuning Logic

## Overview

The AI Tuner includes advanced tuning logic systems that go beyond simple rule-based adjustments. These systems use multi-objective optimization, predictive modeling, reinforcement learning concepts, and closed-loop control to provide intelligent, adaptive tuning recommendations.

## Components

### 1. Advanced Tuning Engine (`services/advanced_tuning_engine.py`)

The Advanced Tuning Engine provides sophisticated tuning optimization with the following features:

#### Multi-Objective Optimization

The engine can optimize for different targets:
- **Performance**: Maximum horsepower
- **Efficiency**: Best fuel economy
- **Balanced**: Balance of performance and efficiency
- **Safety**: Conservative, safe settings

The scoring function weights different objectives based on the selected target:

```python
# Performance mode: 70% HP, 30% Safety
# Efficiency mode: 70% Efficiency, 30% Safety
# Balanced mode: 40% HP, 30% Efficiency, 30% Safety
# Safety mode: 100% Safety
```

#### Predictive Modeling

The engine uses machine learning models (Gradient Boosting, Random Forest) to predict the outcomes of tuning actions before applying them:

- **HP Predictor**: Predicts horsepower gain/loss from tuning changes
- **Efficiency Predictor**: Predicts fuel economy changes
- **Safety Predictor**: Predicts safety score (0-1) for each action

These models are trained on historical tuning data and continuously retrained as more data becomes available.

#### Reinforcement Learning Concepts

The engine uses Q-learning inspired algorithms to learn optimal actions for different engine states:

- **Q-Table**: Stores learned values for state-action pairs
- **Reward Function**: Calculates rewards based on actual outcomes
- **Learning Rate**: Controls how quickly the system adapts to new information

The system learns which tuning actions work best in different conditions (RPM, load, boost, temperature, etc.).

#### Safety Validation

All tuning actions are validated for safety before application:

- Minimum safety score threshold (default: 0.7)
- Checks for knock, high temperatures, lean/rich conditions
- Prevents unsafe adjustments even if they would improve performance

#### Usage Example

```python
from services.advanced_tuning_engine import AdvancedTuningEngine, OptimizationTarget

# Create engine with balanced optimization
engine = AdvancedTuningEngine(
    target=OptimizationTarget.BALANCED,
    learning_rate=0.1,
    safety_threshold=0.7,
)

# Analyze and get recommendations
telemetry = {
    "RPM": 5000,
    "Load": 85,
    "Boost_Pressure": 20,
    "Lambda": 0.98,
    "Ignition_Timing": 18.0,
    "Coolant_Temp": 92,
}

actions = engine.analyze_and_optimize(telemetry, apply_auto=False)

for action in actions:
    print(f"{action.parameter}: {action.current_value:.2f} -> {action.new_value:.2f}")
    print(f"  Expected HP gain: {action.expected_hp_gain:.1f}")
    print(f"  Safety score: {action.safety_score:.2f}")
    print(f"  Reason: {action.reason}")
```

### 2. Closed-Loop Tuning Controller (`services/closed_loop_tuning.py`)

The Closed-Loop Tuning Controller provides continuous, real-time adjustment using PID control algorithms.

#### Features

- **PID Control**: Proportional-Integral-Derivative control for precise adjustments
- **Lambda Control**: Maintains target air-fuel ratio automatically
- **Timing Control**: Adjusts ignition timing based on knock detection
- **Safety Interlocks**: Prevents adjustments when safety conditions are violated
- **Adaptive Learning**: Adjusts control gains based on performance

#### Control Modes

- **Manual**: No automatic adjustments
- **Semi-Auto**: Suggests changes, requires user approval
- **Full-Auto**: Automatically applies safe changes
- **Learning**: Learns optimal settings without applying changes

#### PID Controllers

The system uses separate PID controllers for different parameters:

1. **Lambda Controller**: Maintains target lambda (AFR)
   - Proportional gain: 2.0
   - Integral gain: 0.2
   - Derivative gain: 0.1

2. **Timing Controller**: Controls ignition timing based on knock
   - Proportional gain: 0.5
   - Integral gain: 0.05
   - Derivative gain: 0.02

#### Safety Interlocks

The controller automatically prevents adjustments when:
- Coolant temperature > 105°C
- EGT > 1100°C
- Knock count > 5
- Lambda too lean (> 1.15) or too rich (< 0.85)

#### Usage Example

```python
from services.closed_loop_tuning import ClosedLoopTuningController, ControlMode

# Create controller
controller = ClosedLoopTuningController(
    mode=ControlMode.SEMI_AUTO,
    target_lambda=1.0,
    max_adjustment_rate=0.05,
)

# Update with telemetry (call continuously)
telemetry = {
    "RPM": 5000,
    "Lambda": 0.98,
    "Knock_Count": 0,
    "Coolant_Temp": 92,
}

actions = controller.update(telemetry)

for action in actions:
    print(f"{action.parameter}: {action.adjustment:+.2f}%")
    print(f"  Reason: {action.reason}")
    print(f"  Confidence: {action.confidence:.2f}")
```

### 3. Integration with Existing Systems

The advanced tuning logic integrates with existing systems:

- **Auto Tuning Engine**: Can optionally use advanced engine for better recommendations
- **Adaptive Tuning Advisor**: Enhanced with ML-based confidence scoring
- **Weather Adaptive Tuning**: Uses advanced optimization for weather-based adjustments

## Algorithm Details

### Multi-Objective Scoring

The scoring function combines multiple objectives:

```python
if target == PERFORMANCE:
    score = 0.7 * hp_gain + 0.3 * safety * 10.0
elif target == EFFICIENCY:
    score = 0.7 * eff_gain + 0.3 * safety * 10.0
elif target == BALANCED:
    score = 0.4 * hp_gain + 0.3 * eff_gain + 0.3 * safety * 10.0
else:  # SAFETY
    score = safety * 20.0
```

### Predictive Model Features

The ML models use the following features:
- RPM (normalized)
- Load
- Boost pressure (normalized)
- Lambda value
- Ignition timing (normalized)
- Fuel map value (normalized)
- Coolant temperature (normalized)
- Intake air temperature (normalized)
- Knock count (normalized)
- EGT (normalized)
- Action type (one-hot encoded)
- Action delta
- Current parameter value (normalized)

### Q-Learning Update

The Q-table is updated using:

```
Q(s,a) = Q(s,a) + α * (reward - Q(s,a))
```

Where:
- `α` = learning rate (default: 0.1)
- `reward` = actual outcome (HP gain, efficiency gain, or penalty for unsafe actions)

## Performance Characteristics

### Accuracy

- **Predictive Models**: Improve accuracy as more training data accumulates
- **Q-Learning**: Converges to optimal actions after ~100-200 tuning sessions
- **PID Control**: Provides stable control with < 1% steady-state error

### Safety

- **Safety Threshold**: Default 0.7 (70% confidence required)
- **Interlocks**: Prevent adjustments in unsafe conditions
- **Validation**: All actions validated before application

### Learning Speed

- **Initial Learning**: Uses heuristic predictions until 50+ samples collected
- **Model Retraining**: Every 50 actions
- **Q-Table Updates**: Continuous, every action

## Best Practices

1. **Start Conservative**: Begin with `safety_threshold=0.8` and `OptimizationTarget.SAFETY`
2. **Gradual Transition**: Move to `BALANCED` or `PERFORMANCE` as system learns
3. **Monitor Safety**: Always watch for safety interlock activations
4. **Review Actions**: In `SEMI_AUTO` mode, review all actions before applying
5. **Collect Data**: More data = better predictions and learning

## Future Enhancements

Planned improvements:
- Deep reinforcement learning (DQN, PPO)
- Multi-vehicle learning (transfer learning)
- Real-time model updates (online learning)
- Advanced safety models (predictive failure detection)
- Integration with dyno data for validation

## See Also

- [Auto Tuning Engine Documentation](AUTO_TUNING.md)
- [Adaptive Tuning Advisor](ADAPTIVE_TUNING.md)
- [AI Algorithm Optimization Plan](AI_ALGORITHM_OPTIMIZATION.md)










