"""
Closed-Loop Tuning Control System

Provides continuous feedback and adjustment for real-time tuning optimization.
Features:
- PID-like control for fuel and timing
- Adaptive gain adjustment
- Safety interlocks
- Performance tracking
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class ControlMode(Enum):
    """Control modes."""
    MANUAL = "manual"  # Manual control, no auto-adjustments
    SEMI_AUTO = "semi_auto"  # Suggest changes, user approves
    FULL_AUTO = "full_auto"  # Automatically apply safe changes
    LEARNING = "learning"  # Learn optimal settings, don't apply


@dataclass
class PIDController:
    """PID controller for closed-loop tuning."""
    kp: float = 1.0  # Proportional gain
    ki: float = 0.1  # Integral gain
    kd: float = 0.05  # Derivative gain
    setpoint: float = 1.0  # Target value
    integral: float = 0.0
    last_error: float = 0.0
    last_time: float = 0.0
    output_min: float = -10.0
    output_max: float = 10.0
    
    def compute(self, current_value: float, dt: float) -> float:
        """
        Compute PID output.
        
        Args:
            current_value: Current measured value
            dt: Time delta since last computation
            
        Returns:
            Control output
        """
        error = self.setpoint - current_value
        
        # Proportional term
        p_term = self.kp * error
        
        # Integral term
        self.integral += error * dt
        self.integral = max(-10.0, min(10.0, self.integral))  # Anti-windup
        i_term = self.ki * self.integral
        
        # Derivative term
        if dt > 0:
            d_term = self.kd * (error - self.last_error) / dt
        else:
            d_term = 0.0
        
        # Total output
        output = p_term + i_term + d_term
        output = max(self.output_min, min(self.output_max, output))
        
        # Update state
        self.last_error = error
        self.last_time = time.time()
        
        return output
    
    def reset(self) -> None:
        """Reset controller state."""
        self.integral = 0.0
        self.last_error = 0.0
        self.last_time = time.time()


@dataclass
class ControlAction:
    """A control action to apply."""
    parameter: str
    adjustment: float
    reason: str
    confidence: float
    safety_ok: bool = True


class ClosedLoopTuningController:
    """
    Closed-loop tuning controller with PID control and adaptive learning.
    
    Provides continuous feedback and adjustment for:
    - Lambda/AFR control (fuel)
    - Ignition timing control
    - Boost control
    - Performance optimization
    """
    
    def __init__(
        self,
        mode: ControlMode = ControlMode.SEMI_AUTO,
        target_lambda: float = 1.0,
        max_adjustment_rate: float = 0.05,  # Max 5% change per cycle
    ):
        """
        Initialize closed-loop controller.
        
        Args:
            mode: Control mode
            target_lambda: Target lambda value
            max_adjustment_rate: Maximum adjustment rate per cycle
        """
        self.mode = mode
        self.max_adjustment_rate = max_adjustment_rate
        
        # PID controllers
        self.lambda_controller = PIDController(
            kp=2.0,
            ki=0.2,
            kd=0.1,
            setpoint=target_lambda,
        )
        
        self.timing_controller = PIDController(
            kp=0.5,
            ki=0.05,
            kd=0.02,
            setpoint=0.0,  # Target knock count = 0
            output_min=-5.0,
            output_max=3.0,
        )
        
        # State tracking
        self.last_telemetry: Optional[Dict[str, float]] = None
        self.last_update_time = time.time()
        self.adjustment_history: deque[ControlAction] = deque(maxlen=100)
        
        # Performance tracking
        self.performance_history: deque[float] = deque(maxlen=100)
        self.best_performance: float = 0.0
        
        # Safety interlocks
        self.safety_interlocks: List[str] = []
    
    def update(
        self,
        telemetry: Dict[str, float],
    ) -> List[ControlAction]:
        """
        Update controller with new telemetry and generate control actions.
        
        Args:
            telemetry: Current telemetry data
            
        Returns:
            List of control actions
        """
        current_time = time.time()
        dt = current_time - self.last_update_time
        
        if dt < 0.1:  # Minimum 100ms between updates
            return []
        
        self.last_update_time = current_time
        
        # Check safety interlocks
        self._check_safety_interlocks(telemetry)
        
        if self.safety_interlocks:
            LOGGER.warning(f"Safety interlocks active: {self.safety_interlocks}")
            return []  # Don't make adjustments if safety issues
        
        # Generate control actions
        actions = []
        
        if self.mode in [ControlMode.SEMI_AUTO, ControlMode.FULL_AUTO]:
            # Lambda control (fuel adjustment)
            lambda_action = self._control_lambda(telemetry, dt)
            if lambda_action:
                actions.append(lambda_action)
            
            # Timing control (knock-based)
            timing_action = self._control_timing(telemetry, dt)
            if timing_action:
                actions.append(timing_action)
        
        # Track performance
        self._track_performance(telemetry)
        
        self.last_telemetry = telemetry.copy()
        
        return actions
    
    def _check_safety_interlocks(self, telemetry: Dict[str, float]) -> None:
        """Check safety conditions and set interlocks."""
        self.safety_interlocks = []
        
        # Check coolant temperature
        coolant_temp = telemetry.get("Coolant_Temp", telemetry.get("CoolantTemperature", 90))
        if coolant_temp > 105:
            self.safety_interlocks.append("High coolant temperature")
        
        # Check EGT
        egt = telemetry.get("EGT", telemetry.get("EGT_Avg", 800))
        if egt > 1100:
            self.safety_interlocks.append("High EGT")
        
        # Check knock
        knock_count = telemetry.get("Knock_Count", telemetry.get("knock", 0))
        if knock_count > 5:
            self.safety_interlocks.append("Excessive knock")
        
        # Check lambda (too lean)
        lambda_val = telemetry.get("Lambda", telemetry.get("AFR", 14.7) / 14.7)
        if lambda_val > 1.15:
            self.safety_interlocks.append("Too lean - risk of detonation")
        
        # Check lambda (too rich)
        if lambda_val < 0.85:
            self.safety_interlocks.append("Too rich - risk of fouling")
    
    def _control_lambda(
        self,
        telemetry: Dict[str, float],
        dt: float,
    ) -> Optional[ControlAction]:
        """Control lambda using PID controller."""
        lambda_val = telemetry.get("Lambda", telemetry.get("AFR", 14.7) / 14.7)
        
        # Update setpoint based on conditions
        boost = telemetry.get("Boost_Pressure", telemetry.get("Boost", 0))
        if boost > 15:
            self.lambda_controller.setpoint = 0.95  # Slightly rich under boost
        else:
            self.lambda_controller.setpoint = 1.0  # Stoichiometric
        
        # Compute PID output
        error = self.lambda_controller.setpoint - lambda_val
        output = self.lambda_controller.compute(lambda_val, dt)
        
        # Convert to fuel adjustment percentage
        if abs(output) < 0.01:  # Deadband
            return None
        
        # Limit adjustment rate
        fuel_adjustment = output * 0.01  # Scale to percentage
        fuel_adjustment = max(
            -self.max_adjustment_rate,
            min(self.max_adjustment_rate, fuel_adjustment)
        )
        
        # Calculate confidence
        confidence = min(0.95, 0.7 + abs(error) * 2.0)
        
        return ControlAction(
            parameter="fuel",
            adjustment=fuel_adjustment,
            reason=f"Lambda control: {lambda_val:.3f} -> {self.lambda_controller.setpoint:.3f} (error: {error:.3f})",
            confidence=confidence,
            safety_ok=True,
        )
    
    def _control_timing(
        self,
        telemetry: Dict[str, float],
        dt: float,
    ) -> Optional[ControlAction]:
        """Control ignition timing based on knock."""
        knock_count = telemetry.get("Knock_Count", telemetry.get("knock", 0))
        current_timing = telemetry.get("Ignition_Timing", telemetry.get("timing_advance", 15.0))
        
        # Setpoint is 0 knock
        self.timing_controller.setpoint = 0.0
        
        # Compute PID output (negative = retard, positive = advance)
        output = self.timing_controller.compute(float(knock_count), dt)
        
        if abs(output) < 0.1:  # Deadband
            return None
        
        # Limit adjustment
        timing_adjustment = output
        timing_adjustment = max(-2.0, min(1.0, timing_adjustment))  # Max 2° retard, 1° advance
        
        # Calculate confidence
        confidence = 0.9 if knock_count > 0 else 0.6
        
        return ControlAction(
            parameter="timing",
            adjustment=timing_adjustment,
            reason=f"Timing control: knock={knock_count}, current={current_timing:.1f}°",
            confidence=confidence,
            safety_ok=knock_count <= 3,
        )
    
    def _track_performance(self, telemetry: Dict[str, float]) -> None:
        """Track performance metrics."""
        # Estimate performance (simplified)
        rpm = telemetry.get("RPM", telemetry.get("Engine_RPM", 0))
        load = telemetry.get("Load", telemetry.get("Manifold_Pressure", 0)) / 100.0
        boost = telemetry.get("Boost_Pressure", telemetry.get("Boost", 0))
        
        performance = rpm * load * (1 + boost / 14.7)
        self.performance_history.append(performance)
        
        if performance > self.best_performance:
            self.best_performance = performance
    
    def set_target_lambda(self, target: float) -> None:
        """Set target lambda value."""
        self.lambda_controller.setpoint = target
        LOGGER.info(f"Target lambda set to {target:.3f}")
    
    def set_mode(self, mode: ControlMode) -> None:
        """Set control mode."""
        self.mode = mode
        LOGGER.info(f"Control mode set to {mode.value}")
    
    def reset_controllers(self) -> None:
        """Reset all controllers."""
        self.lambda_controller.reset()
        self.timing_controller.reset()
        self.safety_interlocks = []
        LOGGER.info("Controllers reset")
    
    def get_statistics(self) -> Dict:
        """Get controller statistics."""
        return {
            "mode": self.mode.value,
            "target_lambda": self.lambda_controller.setpoint,
            "adjustment_count": len(self.adjustment_history),
            "performance_samples": len(self.performance_history),
            "best_performance": self.best_performance,
            "safety_interlocks": len(self.safety_interlocks),
            "active_interlocks": self.safety_interlocks,
        }


__all__ = [
    "ClosedLoopTuningController",
    "ControlMode",
    "ControlAction",
    "PIDController",
]










