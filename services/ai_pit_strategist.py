"""
AI Pit Strategist

AI calculates optimal pit stop timing, tire strategy, and fuel management.
This is what separates winners from losers in endurance racing!
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class TireCondition(Enum):
    """Tire condition levels."""

    NEW = "new"
    GOOD = "good"
    WORN = "worn"
    CRITICAL = "critical"


@dataclass
class PitStrategy:
    """Pit stop strategy recommendation."""

    pit_lap: int
    reason: str
    tire_change: bool
    fuel_amount: float  # Liters
    estimated_time_loss: float  # Seconds
    estimated_gain: float  # Seconds gained from strategy
    confidence: float  # 0-1


@dataclass
class RaceConditions:
    """Current race conditions."""

    current_lap: int
    total_laps: int
    fuel_remaining: float  # Liters
    tire_age_laps: int
    tire_condition: TireCondition
    track_temperature: float  # Celsius
    weather: str  # "dry", "wet", "drying"
    position: int
    gap_to_leader: float  # Seconds
    gap_to_next: float  # Seconds


class AIPitStrategist:
    """
    AI Pit Strategist.

    UNIQUE FEATURE: No one has done AI pit strategy optimization!
    This calculates optimal pit timing, tire changes, and fuel strategy.
    This is what WINS races!
    """

    def __init__(self) -> None:
        """Initialize AI pit strategist."""
        self.strategy_history: List[PitStrategy] = []
        self.race_conditions: Optional[RaceConditions] = None

    def calculate_strategy(self, conditions: RaceConditions) -> List[PitStrategy]:
        """
        Calculate optimal pit stop strategy.

        Args:
            conditions: Current race conditions

        Returns:
            List of pit strategy recommendations
        """
        self.race_conditions = conditions
        strategies = []

        # Check if pit stop needed now
        immediate_strategy = self._check_immediate_pit(conditions)
        if immediate_strategy:
            strategies.append(immediate_strategy)

        # Calculate optimal pit window
        optimal_strategy = self._calculate_optimal_pit(conditions)
        if optimal_strategy:
            strategies.append(optimal_strategy)

        # Calculate fuel strategy
        fuel_strategy = self._calculate_fuel_strategy(conditions)
        if fuel_strategy:
            strategies.append(fuel_strategy)

        return strategies

    def _check_immediate_pit(self, conditions: RaceConditions) -> Optional[PitStrategy]:
        """Check if immediate pit stop is needed."""
        # Critical tire condition
        if conditions.tire_condition == TireCondition.CRITICAL:
            return PitStrategy(
                pit_lap=conditions.current_lap,
                reason="Tires are critical - immediate pit required",
                tire_change=True,
                fuel_amount=self._calculate_fuel_needed(conditions),
                estimated_time_loss=25.0,  # Typical pit time
                estimated_gain=float("inf"),  # Prevents crash
                confidence=1.0,
            )

        # Low fuel
        if conditions.fuel_remaining < 5.0:  # Less than 5 liters
            return PitStrategy(
                pit_lap=conditions.current_lap,
                reason="Low fuel - pit now or risk running out",
                tire_change=conditions.tire_age_laps > 20,
                fuel_amount=conditions.fuel_remaining + 50.0,  # Fill tank
                estimated_time_loss=25.0,
                estimated_gain=0.0,  # Safety, not performance
                confidence=0.95,
            )

        return None

    def _calculate_optimal_pit(self, conditions: RaceConditions) -> Optional[PitStrategy]:
        """Calculate optimal pit stop timing."""
        laps_remaining = conditions.total_laps - conditions.current_lap

        # Optimal pit window (middle third of race)
        optimal_window_start = conditions.total_laps // 3
        optimal_window_end = (conditions.total_laps * 2) // 3

        if optimal_window_start <= conditions.current_lap <= optimal_window_end:
            # Check tire condition
            if conditions.tire_age_laps > 15 or conditions.tire_condition == TireCondition.WORN:
                return PitStrategy(
                    pit_lap=conditions.current_lap,
                    reason="Optimal pit window - tires are worn",
                    tire_change=True,
                    fuel_amount=self._calculate_fuel_needed(conditions),
                    estimated_time_loss=25.0,
                    estimated_gain=5.0,  # Fresh tires = faster laps
                    confidence=0.8,
                )

        # Early pit if undercut opportunity
        if conditions.gap_to_next < 2.0 and conditions.position > 1:
            # Undercut - pit early to get ahead
            return PitStrategy(
                pit_lap=conditions.current_lap + 1,
                reason="Undercut opportunity - pit early to gain position",
                tire_change=conditions.tire_age_laps > 10,
                fuel_amount=self._calculate_fuel_needed(conditions),
                estimated_time_loss=25.0,
                estimated_gain=3.0,  # Position gain
                confidence=0.7,
            )

        return None

    def _calculate_fuel_strategy(self, conditions: RaceConditions) -> Optional[PitStrategy]:
        """Calculate fuel strategy."""
        laps_remaining = conditions.total_laps - conditions.current_lap
        fuel_per_lap = 2.5  # Liters per lap (would be calculated from telemetry)

        fuel_needed = laps_remaining * fuel_per_lap

        if fuel_needed > conditions.fuel_remaining:
            # Need to pit for fuel
            return PitStrategy(
                pit_lap=conditions.current_lap + max(1, int((fuel_needed - conditions.fuel_remaining) / fuel_per_lap)),
                reason=f"Fuel strategy - need {fuel_needed:.1f}L, have {conditions.fuel_remaining:.1f}L",
                tire_change=False,  # Just fuel
                fuel_amount=fuel_needed + 5.0,  # Safety margin
                estimated_time_loss=20.0,  # Fuel-only pit is faster
                estimated_gain=0.0,
                confidence=0.9,
            )

        return None

    def _calculate_fuel_needed(self, conditions: RaceConditions) -> float:
        """Calculate fuel needed to finish race."""
        laps_remaining = conditions.total_laps - conditions.current_lap
        fuel_per_lap = 2.5  # Would be calculated from actual consumption
        return max(0, (laps_remaining * fuel_per_lap) - conditions.fuel_remaining + 5.0)  # Safety margin

    def get_strategy_summary(self) -> Dict:
        """Get summary of pit strategies."""
        if not self.strategy_history:
            return {}

        return {
            "total_strategies": len(self.strategy_history),
            "average_time_loss": sum(s.estimated_time_loss for s in self.strategy_history) / len(self.strategy_history),
            "total_estimated_gain": sum(s.estimated_gain for s in self.strategy_history),
        }


__all__ = ["AIPitStrategist", "PitStrategy", "RaceConditions", "TireCondition"]

