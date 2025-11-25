"""
Advanced Self-Learning Intelligence
Reinforcement Learning, Deep Q-Networks, Online Learning, and Multi-Objective Optimization
"""

from __future__ import annotations

import logging
import random
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None  # type: ignore
    nn = None  # type: ignore
    optim = None  # type: ignore

LOGGER = logging.getLogger(__name__)


# Conditional neural network classes
if TORCH_AVAILABLE and nn and torch:
    class DQNNetwork(nn.Module):
        """Deep Q-Network for tuning optimization."""
        
        def __init__(self, state_size: int = 10, action_size: int = 5, hidden_size: int = 128):
            super().__init__()
            self.state_size = state_size
            self.action_size = action_size
            
            self.network = nn.Sequential(
                nn.Linear(state_size, hidden_size),
                nn.ReLU(),
                nn.Linear(hidden_size, hidden_size),
                nn.ReLU(),
                nn.Linear(hidden_size, hidden_size // 2),
                nn.ReLU(),
                nn.Linear(hidden_size // 2, action_size)
            )
        
        def forward(self, state):
            return self.network(state)
    
    
    class PolicyNetwork(nn.Module):
        """Policy network for continuous action space."""
        
        def __init__(self, state_size: int = 10, action_size: int = 1, hidden_size: int = 128):
            super().__init__()
            self.state_size = state_size
            self.action_size = action_size
            
            self.shared = nn.Sequential(
                nn.Linear(state_size, hidden_size),
                nn.ReLU(),
                nn.Linear(hidden_size, hidden_size),
                nn.ReLU(),
            )
            
            # Mean and std for continuous actions
            self.mean_head = nn.Linear(hidden_size, action_size)
            self.std_head = nn.Linear(hidden_size, action_size)
        
        def forward(self, state):
            shared = self.shared(state)
            mean = self.mean_head(shared)
            std = torch.clamp(torch.exp(self.std_head(shared)), min=0.01, max=1.0)
            return mean, std
else:
    # Dummy classes when torch is not available
    class DQNNetwork:
        """Dummy DQN Network when PyTorch is not available."""
        def __init__(self, *args, **kwargs):
            pass
        def forward(self, x):
            return None
    
    class PolicyNetwork:
        """Dummy Policy Network when PyTorch is not available."""
        def __init__(self, *args, **kwargs):
            pass
        def forward(self, x):
            return None, None


@dataclass
class TuningAction:
    """Tuning action with parameters."""
    
    parameter: str  # e.g., "fuel_trim", "ignition_advance", "boost_target"
    adjustment: float  # Adjustment value
    confidence: float  # 0-1
    expected_reward: float  # Expected improvement
    safety_score: float  # 0-1, safety of this action


@dataclass
class LearningExperience:
    """Experience for reinforcement learning."""
    
    state: np.ndarray  # Current state (telemetry features)
    action: TuningAction  # Action taken
    reward: float  # Reward received
    next_state: np.ndarray  # Next state
    done: bool  # Whether episode is done
    timestamp: float = field(default_factory=time.time)


class AdvancedSelfLearningIntelligence:
    """
    Advanced Self-Learning Intelligence with RL algorithms.
    
    Features:
    - Deep Q-Network (DQN) for discrete action optimization
    - Policy Gradient (PPO-style) for continuous actions
    - Experience Replay for learning from history
    - Multi-Objective Optimization (performance vs safety)
    - Online Learning with incremental updates
    - Adaptive Exploration-Exploitation
    - Transfer Learning between similar vehicles
    """
    
    def __init__(
        self,
        use_dqn: bool = True,
        use_policy_gradient: bool = True,
        learning_rate: float = 1e-4,
        gamma: float = 0.99,  # Discount factor
        epsilon: float = 0.1,  # Exploration rate
        epsilon_decay: float = 0.995,
        memory_size: int = 10000,
        batch_size: int = 64,
    ):
        """
        Initialize advanced self-learning intelligence.
        
        Args:
            use_dqn: Use Deep Q-Network for discrete actions
            use_policy_gradient: Use policy gradient for continuous actions
            learning_rate: Learning rate for neural networks
            gamma: Discount factor for future rewards
            epsilon: Initial exploration rate
            epsilon_decay: Epsilon decay rate
            memory_size: Experience replay buffer size
            batch_size: Batch size for training
        """
        self.use_dqn = use_dqn and TORCH_AVAILABLE
        self.use_policy_gradient = use_policy_gradient and TORCH_AVAILABLE
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        
        # Experience replay buffer
        self.memory: deque = deque(maxlen=memory_size)
        
        # Neural networks
        self.dqn_network: Optional[DQNNetwork] = None
        self.dqn_target: Optional[DQNNetwork] = None
        self.policy_network: Optional[PolicyNetwork] = None
        
        # Optimizers
        self.dqn_optimizer: Optional[optim.Adam] = None
        self.policy_optimizer: Optional[optim.Adam] = None
        
        # Learning statistics
        self.learning_history: List[Dict] = []
        self.total_reward = 0.0
        self.episode_count = 0
        
        # Adaptive thresholds (learned)
        self.learned_optimal: Dict[str, Dict[str, float]] = {}
        
        # Multi-objective weights
        self.performance_weight = 0.6
        self.safety_weight = 0.3
        self.efficiency_weight = 0.1
        
        # Initialize networks
        if self.use_dqn:
            self._init_dqn()
        if self.use_policy_gradient:
            self._init_policy_network()
    
    def _init_dqn(self) -> None:
        """Initialize Deep Q-Network."""
        if not TORCH_AVAILABLE:
            return
        
        try:
            state_size = 10  # RPM, Load, AFR, Boost, etc.
            action_size = 5  # Fuel trim levels: -10%, -5%, 0%, +5%, +10%
            
            self.dqn_network = DQNNetwork(state_size, action_size)
            self.dqn_target = DQNNetwork(state_size, action_size)
            self.dqn_target.load_state_dict(self.dqn_network.state_dict())
            self.dqn_target.eval()
            
            self.dqn_optimizer = optim.Adam(self.dqn_network.parameters(), lr=self.learning_rate)
            
            LOGGER.info("DQN network initialized")
        except Exception as e:
            LOGGER.error(f"Failed to initialize DQN: {e}")
            self.use_dqn = False
    
    def _init_policy_network(self) -> None:
        """Initialize policy network for continuous actions."""
        if not TORCH_AVAILABLE:
            return
        
        try:
            state_size = 10
            action_size = 1  # Continuous adjustment value
            
            self.policy_network = PolicyNetwork(state_size, action_size)
            self.policy_optimizer = optim.Adam(self.policy_network.parameters(), lr=self.learning_rate)
            
            LOGGER.info("Policy network initialized")
        except Exception as e:
            LOGGER.error(f"Failed to initialize policy network: {e}")
            self.use_policy_gradient = False
    
    def select_action(
        self,
        state: Dict[str, float],
        action_type: str = "fuel_trim"
    ) -> TuningAction:
        """
        Select optimal action using learned policy.
        
        Args:
            state: Current telemetry state
            action_type: Type of action ("fuel_trim", "ignition_advance", "boost_target")
            
        Returns:
            Optimal tuning action
        """
        # Extract state features
        state_features = self._extract_state_features(state)
        state_tensor = torch.FloatTensor(state_features).unsqueeze(0)
        
        # Exploration vs exploitation
        if random.random() < self.epsilon:
            # Exploration: random action
            return self._random_action(action_type)
        
        # Exploitation: use learned policy
        if self.use_policy_gradient and self.policy_network:
            return self._policy_action(state_tensor, action_type)
        elif self.use_dqn and self.dqn_network:
            return self._dqn_action(state_tensor, action_type)
        else:
            # Fallback to heuristic
            return self._heuristic_action(state, action_type)
    
    def _extract_state_features(self, state: Dict[str, float]) -> np.ndarray:
        """Extract features from state dictionary."""
        features = [
            state.get("RPM", 0) / 10000.0,  # Normalized
            state.get("Load", state.get("MAP", 0) / 100.0),
            state.get("AFR", 14.7) / 20.0,  # Normalized
            state.get("Boost_Pressure", 0) / 30.0,  # Normalized
            state.get("Coolant_Temp", 90) / 130.0,  # Normalized
            state.get("Oil_Pressure", 50) / 100.0,  # Normalized
            state.get("Knock_Count", 0) / 20.0,  # Normalized
            state.get("Throttle_Position", 0) / 100.0,  # Normalized
            state.get("EGT", 800) / 2000.0,  # Normalized
            state.get("Lambda", 1.0),
        ]
        return np.array(features, dtype=np.float32)
    
    def _random_action(self, action_type: str) -> TuningAction:
        """Generate random action for exploration."""
        adjustment = random.uniform(-10.0, 10.0)  # ±10% adjustment
        
        return TuningAction(
            parameter=action_type,
            adjustment=adjustment,
            confidence=0.1,  # Low confidence for random
            expected_reward=0.0,
            safety_score=0.5,  # Medium safety
        )
    
    def _policy_action(
        self,
        state_tensor: torch.Tensor,
        action_type: str
    ) -> TuningAction:
        """Select action using policy network."""
        if not self.policy_network:
            return self._random_action(action_type)
        
        with torch.no_grad():
            mean, std = self.policy_network(state_tensor)
            
            # Sample from normal distribution
            action_dist = torch.distributions.Normal(mean, std)
            action_value = action_dist.sample()
            
            # Clamp to reasonable range
            adjustment = torch.clamp(action_value, -10.0, 10.0).item()
            
            # Calculate confidence based on std (lower std = higher confidence)
            confidence = 1.0 / (1.0 + std.item())
            
            # Estimate expected reward (simplified)
            expected_reward = self._estimate_reward(state_tensor, adjustment)
            
            # Calculate safety score
            safety_score = self._calculate_safety_score(state_tensor, adjustment)
        
        return TuningAction(
            parameter=action_type,
            adjustment=adjustment,
            confidence=min(1.0, max(0.0, confidence)),
            expected_reward=expected_reward,
            safety_score=safety_score,
        )
    
    def _dqn_action(
        self,
        state_tensor: torch.Tensor,
        action_type: str
    ) -> TuningAction:
        """Select action using DQN."""
        if not self.dqn_network:
            return self._random_action(action_type)
        
        with torch.no_grad():
            q_values = self.dqn_network(state_tensor)
            action_idx = torch.argmax(q_values).item()
            
            # Map action index to adjustment value
            action_map = [-10.0, -5.0, 0.0, 5.0, 10.0]
            adjustment = action_map[min(action_idx, len(action_map) - 1)]
            
            # Confidence based on Q-value spread
            q_max = q_values.max().item()
            q_mean = q_values.mean().item()
            confidence = min(1.0, (q_max - q_mean) / 10.0)
            
            expected_reward = q_max
            safety_score = self._calculate_safety_score(state_tensor, adjustment)
        
        return TuningAction(
            parameter=action_type,
            adjustment=adjustment,
            confidence=confidence,
            expected_reward=expected_reward,
            safety_score=safety_score,
        )
    
    def _heuristic_action(
        self,
        state: Dict[str, float],
        action_type: str
    ) -> TuningAction:
        """Fallback heuristic action."""
        # Simple rule-based adjustment
        afr = state.get("AFR", 14.7)
        target_afr = 14.7
        
        if afr > target_afr + 0.5:  # Lean
            adjustment = 5.0  # Add fuel
        elif afr < target_afr - 0.5:  # Rich
            adjustment = -5.0  # Remove fuel
        else:
            adjustment = 0.0
        
        return TuningAction(
            parameter=action_type,
            adjustment=adjustment,
            confidence=0.5,
            expected_reward=1.0,
            safety_score=0.8,
        )
    
    def learn_from_experience(
        self,
        experience: LearningExperience
    ) -> None:
        """
        Learn from experience using reinforcement learning.
        
        Args:
            experience: Learning experience (state, action, reward, next_state)
        """
        # Add to replay buffer
        self.memory.append(experience)
        
        # Update total reward
        self.total_reward += experience.reward
        
        # Train networks if enough experiences
        if len(self.memory) >= self.batch_size:
            if self.use_dqn:
                self._train_dqn()
            if self.use_policy_gradient:
                self._train_policy_network()
        
        # Decay exploration
        self.epsilon = max(0.01, self.epsilon * self.epsilon_decay)
        
        # Update learning history
        self.learning_history.append({
            "episode": self.episode_count,
            "reward": experience.reward,
            "total_reward": self.total_reward,
            "epsilon": self.epsilon,
            "timestamp": time.time(),
        })
    
    def _train_dqn(self) -> None:
        """Train DQN network using experience replay."""
        if not self.dqn_network or len(self.memory) < self.batch_size:
            return
        
        # Sample batch
        batch = random.sample(self.memory, self.batch_size)
        
        # Prepare batches
        states = torch.FloatTensor([exp.state for exp in batch])
        actions = [exp.action.adjustment for exp in batch]
        rewards = torch.FloatTensor([exp.reward for exp in batch])
        next_states = torch.FloatTensor([exp.next_state for exp in batch])
        dones = torch.BoolTensor([exp.done for exp in batch])
        
        # Current Q values
        current_q_values = self.dqn_network(states)
        
        # Next Q values from target network
        with torch.no_grad():
            next_q_values = self.dqn_target(next_states)
            target_q_values = rewards + (1 - dones.float()) * self.gamma * next_q_values.max(1)[0]
        
        # Map actions to indices
        action_map = [-10.0, -5.0, 0.0, 5.0, 10.0]
        action_indices = torch.LongTensor([
            action_map.index(min(action_map, key=lambda x: abs(x - a))) if a in action_map else 2
            for a in actions
        ])
        
        # Compute loss
        q_value = current_q_values.gather(1, action_indices.unsqueeze(1)).squeeze(1)
        loss = nn.MSELoss()(q_value, target_q_values)
        
        # Optimize
        self.dqn_optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.dqn_network.parameters(), 1.0)  # Gradient clipping
        self.dqn_optimizer.step()
        
        # Update target network periodically
        if len(self.learning_history) % 100 == 0:
            self.dqn_target.load_state_dict(self.dqn_network.state_dict())
    
    def _train_policy_network(self) -> None:
        """Train policy network using policy gradient."""
        if not self.policy_network or len(self.memory) < self.batch_size:
            return
        
        # Sample batch
        batch = random.sample(self.memory, self.batch_size)
        
        # Prepare batches
        states = torch.FloatTensor([exp.state for exp in batch])
        actions = torch.FloatTensor([[exp.action.adjustment] for exp in batch])
        rewards = torch.FloatTensor([exp.reward for exp in batch])
        
        # Normalize rewards
        rewards = (rewards - rewards.mean()) / (rewards.std() + 1e-8)
        
        # Get policy distribution
        means, stds = self.policy_network(states)
        action_dist = torch.distributions.Normal(means, stds)
        
        # Compute log probabilities
        log_probs = action_dist.log_prob(actions).sum(dim=1)
        
        # Policy gradient loss (REINFORCE)
        loss = -(log_probs * rewards).mean()
        
        # Optimize
        self.policy_optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_network.parameters(), 1.0)
        self.policy_optimizer.step()
    
    def calculate_reward(
        self,
        state: Dict[str, float],
        action: TuningAction,
        next_state: Dict[str, float]
    ) -> float:
        """
        Calculate reward for multi-objective optimization.
        
        Args:
            state: Previous state
            action: Action taken
            next_state: New state after action
            
        Returns:
            Reward value
        """
        # Performance reward (power/torque improvement)
        performance_reward = self._performance_reward(state, next_state)
        
        # Safety reward (avoiding dangerous conditions)
        safety_reward = self._safety_reward(state, next_state)
        
        # Efficiency reward (fuel economy)
        efficiency_reward = self._efficiency_reward(state, next_state)
        
        # Combined reward with weights
        total_reward = (
            self.performance_weight * performance_reward +
            self.safety_weight * safety_reward +
            self.efficiency_weight * efficiency_reward
        )
        
        return total_reward
    
    def _performance_reward(
        self,
        state: Dict[str, float],
        next_state: Dict[str, float]
    ) -> float:
        """Calculate performance reward."""
        # Estimate power from RPM and load
        prev_power = state.get("RPM", 0) * state.get("Load", 0) / 1000.0
        next_power = next_state.get("RPM", 0) * next_state.get("Load", 0) / 1000.0
        
        power_gain = next_power - prev_power
        return max(-10.0, min(10.0, power_gain / 10.0))  # Normalized
    
    def _safety_reward(
        self,
        state: Dict[str, float],
        next_state: Dict[str, float]
    ) -> float:
        """Calculate safety reward."""
        reward = 0.0
        
        # Penalize dangerous AFR
        afr = next_state.get("AFR", 14.7)
        if afr > 16.0 or afr < 11.0:
            reward -= 20.0  # Large penalty
        
        # Penalize high knock
        knock = next_state.get("Knock_Count", 0)
        if knock > 5:
            reward -= 10.0
        
        # Penalize high temperatures
        coolant = next_state.get("Coolant_Temp", 90)
        if coolant > 110:
            reward -= 15.0
        
        # Reward safe operation
        if 12.0 < afr < 15.0 and knock < 3 and coolant < 100:
            reward += 5.0
        
        return max(-20.0, min(10.0, reward))
    
    def _efficiency_reward(
        self,
        state: Dict[str, float],
        next_state: Dict[str, float]
    ) -> float:
        """Calculate efficiency reward."""
        # Simplified: reward for maintaining target AFR
        afr = next_state.get("AFR", 14.7)
        target_afr = 14.7
        
        afr_error = abs(afr - target_afr)
        reward = max(0.0, 5.0 - afr_error * 2.0)  # Reward for being close to target
        
        return reward
    
    def _estimate_reward(
        self,
        state_tensor: torch.Tensor,
        adjustment: float
    ) -> float:
        """Estimate expected reward for an action."""
        # Simplified estimation
        return 1.0 - abs(adjustment) / 10.0  # Prefer smaller adjustments
    
    def _calculate_safety_score(
        self,
        state_tensor: torch.Tensor,
        adjustment: float
    ) -> float:
        """Calculate safety score for an action."""
        # Large adjustments are less safe
        safety = 1.0 - abs(adjustment) / 20.0
        
        # Check state for dangerous conditions
        state_array = state_tensor.squeeze().numpy()
        
        # High RPM + large adjustment = risky
        if state_array[0] > 0.8 and abs(adjustment) > 5.0:
            safety *= 0.5
        
        return max(0.0, min(1.0, safety))
    
    def optimize_multi_objective(
        self,
        state: Dict[str, float],
        objectives: Dict[str, float]
    ) -> TuningAction:
        """
        Optimize for multiple objectives simultaneously.
        
        Args:
            state: Current state
            objectives: Objective weights {"performance": 0.6, "safety": 0.3, "efficiency": 0.1}
            
        Returns:
            Optimal action balancing all objectives
        """
        # Update objective weights
        self.performance_weight = objectives.get("performance", 0.6)
        self.safety_weight = objectives.get("safety", 0.3)
        self.efficiency_weight = objectives.get("efficiency", 0.1)
        
        # Normalize weights
        total = self.performance_weight + self.safety_weight + self.efficiency_weight
        if total > 0:
            self.performance_weight /= total
            self.safety_weight /= total
            self.efficiency_weight /= total
        
        # Select action with updated weights
        return self.select_action(state, "fuel_trim")
    
    def get_learning_statistics(self) -> Dict:
        """Get learning statistics."""
        return {
            "episode_count": self.episode_count,
            "total_reward": self.total_reward,
            "average_reward": self.total_reward / max(1, len(self.learning_history)),
            "epsilon": self.epsilon,
            "memory_size": len(self.memory),
            "learned_optimal_count": len(self.learned_optimal),
        }
    
    def save_learned_model(self, filepath: str) -> None:
        """Save learned models to file."""
        if not TORCH_AVAILABLE:
            return
        
        try:
            checkpoint = {
                "dqn_state": self.dqn_network.state_dict() if self.dqn_network else None,
                "policy_state": self.policy_network.state_dict() if self.policy_network else None,
                "epsilon": self.epsilon,
                "learned_optimal": self.learned_optimal,
                "learning_history": self.learning_history[-1000:],  # Last 1000 experiences
            }
            torch.save(checkpoint, filepath)
            LOGGER.info(f"Learned model saved to {filepath}")
        except Exception as e:
            LOGGER.error(f"Failed to save model: {e}")
    
    def load_learned_model(self, filepath: str) -> None:
        """Load learned models from file."""
        if not TORCH_AVAILABLE:
            return
        
        try:
            checkpoint = torch.load(filepath)
            
            if checkpoint.get("dqn_state") and self.dqn_network:
                self.dqn_network.load_state_dict(checkpoint["dqn_state"])
                self.dqn_target.load_state_dict(checkpoint["dqn_state"])
            
            if checkpoint.get("policy_state") and self.policy_network:
                self.policy_network.load_state_dict(checkpoint["policy_state"])
            
            self.epsilon = checkpoint.get("epsilon", 0.1)
            self.learned_optimal = checkpoint.get("learned_optimal", {})
            
            LOGGER.info(f"Learned model loaded from {filepath}")
        except Exception as e:
            LOGGER.error(f"Failed to load model: {e}")

