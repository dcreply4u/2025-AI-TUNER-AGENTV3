"""
Voice-Activated ECU Control

Control your ECU with voice commands. "More power", "Better fuel economy",
"Race mode". This is INSANE - hands-free tuning!
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class VoiceCommand(Enum):
    """Voice command types."""

    MORE_POWER = "more_power"
    FUEL_ECONOMY = "fuel_economy"
    RACE_MODE = "race_mode"
    SAFE_MODE = "safe_mode"
    INCREASE_BOOST = "increase_boost"
    DECREASE_BOOST = "decrease_boost"
    RICHER = "richer"
    LEANER = "leaner"
    RESET = "reset"


@dataclass
class ECUAdjustment:
    """ECU adjustment from voice command."""

    command: VoiceCommand
    parameter_changes: Dict[str, float]  # parameter -> adjustment
    safety_check_passed: bool
    applied: bool
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class VoiceECUControl:
    """
    Voice-Activated ECU Control.

    UNIQUE FEATURE: No one has done voice control for ECU tuning!
    Hands-free tuning while driving. "More power" and it happens!
    """

    def __init__(self, ecu_control=None) -> None:
        """
        Initialize voice ECU control.

        Args:
            ecu_control: ECU control interface (optional)
        """
        self.ecu_control = ecu_control
        self.command_history: List[ECUAdjustment] = []
        self.current_mode: str = "balanced"

        # Command mappings
        self.command_map = {
            "more power": VoiceCommand.MORE_POWER,
            "more boost": VoiceCommand.INCREASE_BOOST,
            "less boost": VoiceCommand.DECREASE_BOOST,
            "fuel economy": VoiceCommand.FUEL_ECONOMY,
            "save fuel": VoiceCommand.FUEL_ECONOMY,
            "race mode": VoiceCommand.RACE_MODE,
            "safe mode": VoiceCommand.SAFE_MODE,
            "richer": VoiceCommand.RICHER,
            "leaner": VoiceCommand.LEANER,
            "reset": VoiceCommand.RESET,
        }

    def process_voice_command(self, command_text: str, current_telemetry: Dict[str, float]) -> Optional[ECUAdjustment]:
        """
        Process voice command and apply ECU adjustments.

        Args:
            command_text: Voice command text
            current_telemetry: Current telemetry for safety checks

        Returns:
            ECU adjustment if applied
        """
        command_text = command_text.lower().strip()

        # Find matching command
        command = None
        for key, cmd in self.command_map.items():
            if key in command_text:
                command = cmd
                break

        if not command:
            return None

        # Generate adjustment
        adjustment = self._generate_adjustment(command, current_telemetry)

        if adjustment and adjustment.safety_check_passed:
            # Apply adjustment
            if self.ecu_control:
                self._apply_adjustment(adjustment)
            adjustment.applied = True

        self.command_history.append(adjustment)
        return adjustment

    def _generate_adjustment(self, command: VoiceCommand, telemetry: Dict) -> Optional[ECUAdjustment]:
        """Generate ECU adjustment from command."""
        parameter_changes = {}

        if command == VoiceCommand.MORE_POWER:
            # Increase boost, advance timing, enrich fuel
            parameter_changes = {
                "boost_target": 2.0,  # Increase 2 PSI
                "timing_advance": 1.0,  # Advance 1 degree
                "fuel_enrichment": 0.05,  # Enrich 5%
            }
            self.current_mode = "power"

        elif command == VoiceCommand.FUEL_ECONOMY:
            # Reduce boost, retard timing, lean fuel
            parameter_changes = {
                "boost_target": -3.0,  # Reduce 3 PSI
                "timing_advance": -2.0,  # Retard 2 degrees
                "fuel_enrichment": -0.1,  # Lean 10%
            }
            self.current_mode = "economy"

        elif command == VoiceCommand.RACE_MODE:
            # Maximum performance
            parameter_changes = {
                "boost_target": 5.0,
                "timing_advance": 2.0,
                "fuel_enrichment": 0.1,
                "throttle_response": 0.2,  # More aggressive
            }
            self.current_mode = "race"

        elif command == VoiceCommand.SAFE_MODE:
            # Conservative settings
            parameter_changes = {
                "boost_target": -5.0,
                "timing_advance": -3.0,
                "fuel_enrichment": 0.0,
            }
            self.current_mode = "safe"

        elif command == VoiceCommand.INCREASE_BOOST:
            parameter_changes = {"boost_target": 1.0}

        elif command == VoiceCommand.DECREASE_BOOST:
            parameter_changes = {"boost_target": -1.0}

        elif command == VoiceCommand.RICHER:
            parameter_changes = {"fuel_enrichment": 0.05}

        elif command == VoiceCommand.LEANER:
            parameter_changes = {"fuel_enrichment": -0.05}

        elif command == VoiceCommand.RESET:
            parameter_changes = {
                "boost_target": 0.0,
                "timing_advance": 0.0,
                "fuel_enrichment": 0.0,
            }
            self.current_mode = "balanced"

        # Safety check
        safety_passed = self._safety_check(parameter_changes, telemetry)

        return ECUAdjustment(
            command=command,
            parameter_changes=parameter_changes,
            safety_check_passed=safety_passed,
            applied=False,
        )

    def _safety_check(self, parameter_changes: Dict, telemetry: Dict) -> bool:
        """Perform safety checks before applying changes."""
        # Check for knock
        if telemetry.get("Knock_Count", 0) > 0:
            if parameter_changes.get("timing_advance", 0) > 0:
                LOGGER.warning("Knock detected - not advancing timing")
                return False

        # Check coolant temperature
        coolant_temp = telemetry.get("Coolant_Temp", 90)
        if coolant_temp > 100:
            if parameter_changes.get("boost_target", 0) > 0:
                LOGGER.warning("High coolant temp - not increasing boost")
                return False

        # Check lambda
        lambda_val = telemetry.get("Lambda", 1.0)
        if lambda_val < 0.85:
            if parameter_changes.get("fuel_enrichment", 0) > 0:
                LOGGER.warning("Already too rich - not enriching further")
                return False

        return True

    def _apply_adjustment(self, adjustment: ECUAdjustment) -> bool:
        """Apply adjustment to ECU."""
        if not self.ecu_control:
            return False

        LOGGER.info(f"Applying voice command: {adjustment.command.value}")

        # Would interface with ECU control
        for parameter, change in adjustment.parameter_changes.items():
            LOGGER.info(f"  {parameter}: {change:+.2f}")

        return True


__all__ = ["VoiceECUControl", "ECUAdjustment", "VoiceCommand"]

