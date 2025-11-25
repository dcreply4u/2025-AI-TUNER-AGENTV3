"""
Contextual Modes System
Mode-specific displays (Qualifying, Race, Wet Race, etc.) that adapt UI
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from ui.racing_ui_theme import get_racing_theme, RacingColor


class RacingMode(Enum):
    """Racing mode types."""
    QUALIFYING = "qualifying"
    RACE = "race"
    WET_RACE = "wet_race"
    PRACTICE = "practice"
    TUNING = "tuning"
    DIAGNOSTIC = "diagnostic"
    STREET = "street"


@dataclass
class ModeConfiguration:
    """Configuration for a specific racing mode."""
    mode: RacingMode
    visible_data: List[str] = field(default_factory=list)
    hidden_data: List[str] = field(default_factory=list)
    priority_data: List[str] = field(default_factory=list)
    color_scheme: Dict[str, str] = field(default_factory=dict)
    layout_preset: str = "default"
    alerts_enabled: List[str] = field(default_factory=list)
    tuning_options: List[str] = field(default_factory=list)


class ContextualModeManager:
    """
    Manages contextual modes that adapt UI based on racing context.
    
    Features:
    - Mode-specific data visibility
    - Adaptive color schemes
    - Context-aware alerts
    - Mode-specific tuning options
    """
    
    MODE_CONFIGS = {
        RacingMode.QUALIFYING: ModeConfiguration(
            mode=RacingMode.QUALIFYING,
            visible_data=["RPM", "Speed", "Lap_Time", "Sector_Time", "Boost", "AFR"],
            priority_data=["Lap_Time", "Sector_Time", "Speed"],
            color_scheme={
                "primary": RacingColor.ACCENT_NEON_BLUE.value,
                "secondary": RacingColor.ACCENT_NEON_GREEN.value,
            },
            alerts_enabled=["Overboost", "Overheat", "Low_Fuel"],
            tuning_options=["Boost_Control", "Ignition_Timing", "Launch_Control"],
        ),
        RacingMode.RACE: ModeConfiguration(
            mode=RacingMode.RACE,
            visible_data=["RPM", "Speed", "Lap_Time", "Fuel_Level", "Tire_Temp", "Boost", "AFR", "EGT"],
            priority_data=["Fuel_Level", "Lap_Time", "Tire_Temp"],
            color_scheme={
                "primary": RacingColor.ACCENT_NEON_GREEN.value,
                "secondary": RacingColor.ACCENT_NEON_BLUE.value,
            },
            alerts_enabled=["Low_Fuel", "Overheat", "Tire_Pressure", "Overboost"],
            tuning_options=["Fuel_Strategy", "Boost_Control", "Tire_Management"],
        ),
        RacingMode.WET_RACE: ModeConfiguration(
            mode=RacingMode.WET_RACE,
            visible_data=["RPM", "Speed", "Lap_Time", "Tire_Temp", "Traction", "Boost", "AFR"],
            priority_data=["Traction", "Tire_Temp", "Speed"],
            color_scheme={
                "primary": RacingColor.ACCENT_NEON_BLUE.value,
                "secondary": RacingColor.ACCENT_NEON_YELLOW.value,
            },
            alerts_enabled=["Low_Traction", "Aquaplaning", "Overboost"],
            tuning_options=["Traction_Control", "Boost_Reduction", "Ignition_Retard"],
        ),
        RacingMode.TUNING: ModeConfiguration(
            mode=RacingMode.TUNING,
            visible_data=["RPM", "Boost", "AFR", "Lambda", "Ignition_Timing", "EGT", "Knock"],
            priority_data=["AFR", "Lambda", "Ignition_Timing", "Knock"],
            color_scheme={
                "primary": RacingColor.ACCENT_NEON_ORANGE.value,
                "secondary": RacingColor.ACCENT_NEON_BLUE.value,
            },
            alerts_enabled=["Knock", "Lean", "Rich", "Overboost", "Overheat"],
            tuning_options=["Fuel_Map", "Ignition_Map", "Boost_Map", "All"],
        ),
    }
    
    def __init__(self):
        """Initialize contextual mode manager."""
        self.current_mode = RacingMode.TUNING
        self.mode_history: List[RacingMode] = []
    
    def set_mode(self, mode: RacingMode) -> None:
        """Set current racing mode."""
        self.mode_history.append(self.current_mode)
        self.current_mode = mode
    
    def get_config(self, mode: Optional[RacingMode] = None) -> ModeConfiguration:
        """Get configuration for mode."""
        mode = mode or self.current_mode
        return self.MODE_CONFIGS.get(mode, ModeConfiguration(mode=mode))
    
    def get_visible_data(self) -> List[str]:
        """Get list of visible data fields for current mode."""
        config = self.get_config()
        return config.visible_data
    
    def get_priority_data(self) -> List[str]:
        """Get priority data fields for current mode."""
        config = self.get_config()
        return config.priority_data
    
    def should_show_alert(self, alert_type: str) -> bool:
        """Check if alert should be shown in current mode."""
        config = self.get_config()
        return alert_type in config.alerts_enabled
















