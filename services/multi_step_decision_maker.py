"""
Multi-step Decision Making
Plans complex workflows and holistic car setup plans.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any

LOGGER = logging.getLogger(__name__)


class DecisionType(Enum):
    """Types of decisions."""
    SETUP_CHANGE = "setup_change"
    TUNING_ADJUSTMENT = "tuning_adjustment"
    TESTING = "testing"
    VERIFICATION = "verification"


@dataclass
class DecisionStep:
    """A single step in a decision plan."""
    step_number: int
    decision_type: DecisionType
    action: str
    parameter: Optional[str] = None
    value: Optional[float] = None
    reason: str = ""
    dependencies: List[int] = field(default_factory=list)  # Step numbers this depends on
    expected_outcome: str = ""
    verification_criteria: List[str] = field(default_factory=list)


@dataclass
class DecisionPlan:
    """A complete multi-step decision plan."""
    plan_id: str
    goal: str
    steps: List[DecisionStep] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    estimated_duration: float = 0.0  # minutes
    success_criteria: List[str] = field(default_factory=list)


class MultiStepDecisionMaker:
    """
    Creates multi-step decision plans for complex workflows.
    
    Features:
    - Holistic car setup planning
    - Interdependent change management
    - Constraint satisfaction
    - Workflow optimization
    """
    
    def __init__(self):
        """Initialize decision maker."""
        self.plans: Dict[str, DecisionPlan] = {}
    
    def create_setup_plan(
        self,
        goal: str,
        current_setup: Dict[str, float],
        constraints: List[str] = None,
        track_conditions: Optional[Dict[str, Any]] = None
    ) -> DecisionPlan:
        """
        Create a holistic car setup plan.
        
        Args:
            goal: Setup goal (e.g., "high speed stability", "maximum power")
            current_setup: Current vehicle setup
            constraints: Constraints (e.g., "must maintain safety", "budget limit")
            track_conditions: Track and weather conditions
            
        Returns:
            Complete setup plan
        """
        plan = DecisionPlan(
            plan_id=f"setup_{int(time.time())}",
            goal=goal,
            constraints=constraints or []
        )
        
        # Analyze goal and create steps
        if "power" in goal.lower():
            plan.steps.extend(self._create_power_setup_steps(current_setup, track_conditions))
        elif "stability" in goal.lower() or "handling" in goal.lower():
            plan.steps.extend(self._create_handling_setup_steps(current_setup, track_conditions))
        elif "balanced" in goal.lower():
            plan.steps.extend(self._create_balanced_setup_steps(current_setup, track_conditions))
        
        # Add verification steps
        plan.steps.extend(self._create_verification_steps(plan.steps))
        
        # Calculate estimated duration
        plan.estimated_duration = len(plan.steps) * 5  # 5 minutes per step
        
        # Define success criteria
        plan.success_criteria = self._define_success_criteria(goal)
        
        return plan
    
    def _create_power_setup_steps(
        self,
        current_setup: Dict[str, float],
        track_conditions: Optional[Dict[str, Any]]
    ) -> List[DecisionStep]:
        """Create steps for power-focused setup."""
        steps = []
        step_num = 1
        
        # Step 1: Ensure fuel system is adequate
        steps.append(DecisionStep(
            step_number=step_num,
            decision_type=DecisionType.VERIFICATION,
            action="Verify fuel pressure is adequate (>45 PSI)",
            parameter="Fuel_Pressure",
            reason="Power increases require adequate fuel delivery",
            expected_outcome="Fuel pressure confirmed adequate"
        ))
        step_num += 1
        
        # Step 2: Optimize fuel mixture
        current_afr = current_setup.get("target_afr", 14.7)
        if current_afr > 13.0:
            steps.append(DecisionStep(
                step_number=step_num,
                decision_type=DecisionType.TUNING_ADJUSTMENT,
                action="Enrich fuel mixture for WOT",
                parameter="target_afr",
                value=12.8,
                reason="Optimal AFR for power is 12.8:1",
                dependencies=[1],
                expected_outcome="AFR optimized for power"
            ))
            step_num += 1
        
        # Step 3: Increase boost (if safe)
        current_boost = current_setup.get("boost_target", 10)
        if current_boost < 20:
            steps.append(DecisionStep(
                step_number=step_num,
                decision_type=DecisionType.TUNING_ADJUSTMENT,
                action="Increase boost target",
                parameter="boost_target",
                value=min(20, current_boost + 3),
                reason="Increase boost for more power",
                dependencies=[1, 2],
                expected_outcome="Boost increased safely"
            ))
            step_num += 1
        
        # Step 4: Optimize timing
        current_timing = current_setup.get("timing_advance", 20)
        if current_timing < 28:
            steps.append(DecisionStep(
                step_number=step_num,
                decision_type=DecisionType.TUNING_ADJUSTMENT,
                action="Advance timing for power",
                parameter="timing_advance",
                value=min(28, current_timing + 2),
                reason="More timing advance increases power",
                dependencies=[2, 3],
                expected_outcome="Timing optimized"
            ))
        
        return steps
    
    def _create_handling_setup_steps(
        self,
        current_setup: Dict[str, float],
        track_conditions: Optional[Dict[str, Any]]
    ) -> List[DecisionStep]:
        """Create steps for handling-focused setup."""
        steps = []
        step_num = 1
        
        # Step 1: Analyze current handling issues
        steps.append(DecisionStep(
            step_number=step_num,
            decision_type=DecisionType.VERIFICATION,
            action="Identify handling characteristics",
            reason="Need to understand current behavior",
            expected_outcome="Handling issues identified"
        ))
        step_num += 1
        
        # Step 2: Adjust suspension (example)
        steps.append(DecisionStep(
            step_number=step_num,
            decision_type=DecisionType.SETUP_CHANGE,
            action="Adjust suspension for stability",
            parameter="rear_wing_angle",
            value=2,
            reason="Increase rear downforce for stability",
            dependencies=[1],
            expected_outcome="Improved rear stability"
        ))
        
        return steps
    
    def _create_balanced_setup_steps(
        self,
        current_setup: Dict[str, float],
        track_conditions: Optional[Dict[str, Any]]
    ) -> List[DecisionStep]:
        """Create steps for balanced setup."""
        steps = []
        step_num = 1
        
        # Combine power and handling steps
        steps.extend(self._create_power_setup_steps(current_setup, track_conditions))
        step_num = len(steps) + 1
        steps.extend(self._create_handling_setup_steps(current_setup, track_conditions))
        
        return steps
    
    def _create_verification_steps(self, previous_steps: List[DecisionStep]) -> List[DecisionStep]:
        """Create verification steps for the plan."""
        steps = []
        step_num = len(previous_steps) + 1
        
        # Final verification
        steps.append(DecisionStep(
            step_number=step_num,
            decision_type=DecisionType.VERIFICATION,
            action="Test complete setup",
            reason="Verify all changes work together",
            dependencies=[s.step_number for s in previous_steps],
            expected_outcome="Complete setup verified",
            verification_criteria=[
                "No knock detected",
                "AFR within target range",
                "EGT within safe limits",
                "Handling improved"
            ]
        ))
        
        return steps
    
    def _define_success_criteria(self, goal: str) -> List[str]:
        """Define success criteria based on goal."""
        criteria = []
        
        if "power" in goal.lower():
            criteria.extend([
                "Power increase achieved",
                "No knock detected",
                "AFR optimized",
                "EGT within limits"
            ])
        elif "stability" in goal.lower():
            criteria.extend([
                "Handling improved",
                "Reduced incidents",
                "Consistent lap times"
            ])
        else:
            criteria.extend([
                "Overall performance improved",
                "No safety issues",
                "User satisfied with results"
            ])
        
        return criteria
    
    def execute_plan(self, plan: DecisionPlan, current_step: int = 1) -> Dict[str, Any]:
        """
        Execute a decision plan step by step.
        
        Args:
            plan: Decision plan to execute
            current_step: Current step number
            
        Returns:
            Execution status
        """
        if current_step > len(plan.steps):
            return {"status": "complete", "message": "Plan executed successfully"}
        
        step = plan.steps[current_step - 1]
        
        # Check dependencies
        for dep_step_num in step.dependencies:
            dep_step = next((s for s in plan.steps if s.step_number == dep_step_num), None)
            if dep_step and not hasattr(dep_step, 'completed'):
                return {
                    "status": "waiting",
                    "message": f"Waiting for step {dep_step_num} to complete",
                    "current_step": current_step
                }
        
        return {
            "status": "ready",
            "step": step,
            "current_step": current_step,
            "total_steps": len(plan.steps)
        }


__all__ = ["MultiStepDecisionMaker", "DecisionPlan", "DecisionStep", "DecisionType"]

