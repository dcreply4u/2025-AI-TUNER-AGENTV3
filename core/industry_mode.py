"""
Industry Mode System

Manages different industry modes (Racing, Fleet, Insurance, Personal) with
mode-specific features, terminology, and UI customization.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

LOGGER = logging.getLogger(__name__)


class IndustryMode(Enum):
    """Industry modes for different use cases."""

    RACING = "racing"
    FLEET = "fleet"
    INSURANCE = "insurance"
    PERSONAL = "personal"
    COMMERCIAL = "commercial"


class UserRole(Enum):
    """User roles for access control."""

    DRIVER = "driver"
    FLEET_MANAGER = "fleet_manager"
    ADMIN = "admin"
    INSURANCE_AGENT = "insurance_agent"
    VEHICLE_OWNER = "vehicle_owner"
    RACE_TEAM_MEMBER = "race_team_member"


class VehicleType(Enum):
    """Vehicle types across industries."""

    RACE_CAR = "race_car"
    COMMERCIAL_TRUCK = "commercial_truck"
    DELIVERY_VAN = "delivery_van"
    BUS = "bus"
    PERSONAL_VEHICLE = "personal_vehicle"
    MOTORCYCLE = "motorcycle"
    SEMI_TRUCK = "semi_truck"
    FLEET_CAR = "fleet_car"


@dataclass
class ModeConfiguration:
    """Configuration for a specific industry mode."""

    mode: IndustryMode
    display_name: str
    description: str
    enabled_features: Set[str] = field(default_factory=set)
    terminology_map: Dict[str, str] = field(default_factory=dict)
    default_metrics: List[str] = field(default_factory=list)
    ui_theme: str = "default"
    role_permissions: Dict[UserRole, Set[str]] = field(default_factory=dict)


class IndustryModeManager:
    """Manages industry modes and mode-specific configurations."""

    # Feature flags
    FEATURES = {
        "lap_timing",
        "driver_behavior",
        "fuel_efficiency",
        "maintenance_scheduling",
        "eld_compliance",
        "crash_detection",
        "route_optimization",
        "insurance_ubi",
        "fleet_dashboard",
        "racing_controls",
        "video_overlay",
        "performance_tracking",
        "predictive_maintenance",
        "cargo_management",
    }

    def __init__(self, default_mode: IndustryMode = IndustryMode.RACING) -> None:
        """
        Initialize industry mode manager.

        Args:
            default_mode: Default industry mode
        """
        self.current_mode = default_mode
        self.configurations: Dict[IndustryMode, ModeConfiguration] = {}
        self._initialize_configurations()

    def _initialize_configurations(self) -> None:
        """Initialize mode configurations."""
        # Racing Mode
        self.configurations[IndustryMode.RACING] = ModeConfiguration(
            mode=IndustryMode.RACING,
            display_name="Racing",
            description="High-performance racing and track use",
            enabled_features={
                "lap_timing",
                "racing_controls",
                "video_overlay",
                "performance_tracking",
                "predictive_maintenance",
            },
            terminology_map={
                "lap": "lap",
                "track": "track",
                "session": "session",
                "run": "run",
                "best_lap": "best_lap",
                "sector": "sector",
            },
            default_metrics=["lap_time", "speed", "rpm", "boost", "power"],
            ui_theme="racing",
            role_permissions={
                UserRole.RACE_TEAM_MEMBER: {"view", "control", "export"},
                UserRole.ADMIN: {"view", "control", "export", "configure"},
            },
        )

        # Fleet Mode
        self.configurations[IndustryMode.FLEET] = ModeConfiguration(
            mode=IndustryMode.FLEET,
            display_name="Fleet Management",
            description="Commercial fleet management and optimization",
            enabled_features={
                "driver_behavior",
                "fuel_efficiency",
                "maintenance_scheduling",
                "eld_compliance",
                "route_optimization",
                "fleet_dashboard",
                "predictive_maintenance",
                "crash_detection",
            },
            terminology_map={
                "lap": "trip",
                "track": "route",
                "session": "shift",
                "run": "delivery",
                "best_lap": "best_trip",
                "sector": "segment",
            },
            default_metrics=["mpg", "idle_time", "driver_score", "fuel_cost", "maintenance_due"],
            ui_theme="professional",
            role_permissions={
                UserRole.DRIVER: {"view", "log"},
                UserRole.FLEET_MANAGER: {"view", "export", "configure", "reports"},
                UserRole.ADMIN: {"view", "export", "configure", "reports", "manage_users"},
            },
        )

        # Insurance Mode
        self.configurations[IndustryMode.INSURANCE] = ModeConfiguration(
            mode=IndustryMode.INSURANCE,
            display_name="Insurance Telematics",
            description="Usage-based insurance and risk assessment",
            enabled_features={
                "insurance_ubi",
                "crash_detection",
                "driver_behavior",
                "fuel_efficiency",
                "predictive_maintenance",
            },
            terminology_map={
                "lap": "trip",
                "track": "route",
                "session": "drive",
                "run": "journey",
                "best_lap": "best_trip",
                "sector": "segment",
            },
            default_metrics=["risk_score", "mileage", "driving_time", "safe_driving_score"],
            ui_theme="insurance",
            role_permissions={
                UserRole.VEHICLE_OWNER: {"view", "privacy_controls"},
                UserRole.INSURANCE_AGENT: {"view", "export", "risk_assessment"},
                UserRole.ADMIN: {"view", "export", "configure", "manage_users"},
            },
        )

        # Personal Mode
        self.configurations[IndustryMode.PERSONAL] = ModeConfiguration(
            mode=IndustryMode.PERSONAL,
            display_name="Personal Vehicle",
            description="Personal vehicle management and monitoring",
            enabled_features={
                "fuel_efficiency",
                "maintenance_scheduling",
                "predictive_maintenance",
                "driver_behavior",
            },
            terminology_map={
                "lap": "trip",
                "track": "route",
                "session": "drive",
                "run": "journey",
                "best_lap": "best_trip",
                "sector": "segment",
            },
            default_metrics=["mpg", "maintenance_due", "health_score", "fuel_cost"],
            ui_theme="consumer",
            role_permissions={
                UserRole.VEHICLE_OWNER: {"view", "configure", "export"},
            },
        )

        # Commercial Mode
        self.configurations[IndustryMode.COMMERCIAL] = ModeConfiguration(
            mode=IndustryMode.COMMERCIAL,
            display_name="Commercial Vehicles",
            description="Commercial vehicle management (trucks, buses, vans)",
            enabled_features={
                "driver_behavior",
                "fuel_efficiency",
                "maintenance_scheduling",
                "eld_compliance",
                "cargo_management",
                "crash_detection",
                "predictive_maintenance",
            },
            terminology_map={
                "lap": "route",
                "track": "route",
                "session": "shift",
                "run": "delivery",
                "best_lap": "best_route",
                "sector": "segment",
            },
            default_metrics=["mpg", "driver_score", "cargo_status", "eld_hours", "maintenance_due"],
            ui_theme="professional",
            role_permissions={
                UserRole.DRIVER: {"view", "log", "dvir"},
                UserRole.FLEET_MANAGER: {"view", "export", "configure", "reports"},
                UserRole.ADMIN: {"view", "export", "configure", "reports", "manage_users"},
            },
        )

    def set_mode(self, mode: IndustryMode) -> None:
        """
        Set current industry mode.

        Args:
            mode: Industry mode to set
        """
        if mode not in self.configurations:
            raise ValueError(f"Invalid industry mode: {mode}")

        self.current_mode = mode
        LOGGER.info("Industry mode set to: %s", mode.value)

    def get_mode(self) -> IndustryMode:
        """Get current industry mode."""
        return self.current_mode

    def get_config(self) -> ModeConfiguration:
        """Get current mode configuration."""
        return self.configurations[self.current_mode]

    def is_feature_enabled(self, feature: str) -> bool:
        """
        Check if a feature is enabled in current mode.

        Args:
            feature: Feature name

        Returns:
            True if feature is enabled
        """
        config = self.get_config()
        return feature in config.enabled_features

    def translate_term(self, term: str) -> str:
        """
        Translate terminology based on current mode.

        Args:
            term: Term to translate

        Returns:
            Translated term
        """
        config = self.get_config()
        return config.terminology_map.get(term, term)

    def get_default_metrics(self) -> List[str]:
        """Get default metrics for current mode."""
        config = self.get_config()
        return config.default_metrics.copy()

    def has_permission(self, role: UserRole, permission: str) -> bool:
        """
        Check if role has permission in current mode.

        Args:
            role: User role
            permission: Permission to check

        Returns:
            True if role has permission
        """
        config = self.get_config()
        permissions = config.role_permissions.get(role, set())
        return permission in permissions

    def get_available_modes(self) -> List[IndustryMode]:
        """Get list of available industry modes."""
        return list(self.configurations.keys())

    def get_mode_info(self, mode: IndustryMode) -> Dict[str, Any]:
        """
        Get information about a mode.

        Args:
            mode: Industry mode

        Returns:
            Mode information dictionary
        """
        if mode not in self.configurations:
            return {}

        config = self.configurations[mode]
        return {
            "mode": mode.value,
            "display_name": config.display_name,
            "description": config.description,
            "enabled_features": list(config.enabled_features),
            "default_metrics": config.default_metrics,
            "ui_theme": config.ui_theme,
        }


# Global instance
_mode_manager: Optional[IndustryModeManager] = None


def get_mode_manager() -> IndustryModeManager:
    """Get global industry mode manager instance."""
    global _mode_manager
    if _mode_manager is None:
        _mode_manager = IndustryModeManager()
    return _mode_manager


def set_industry_mode(mode: IndustryMode) -> None:
    """
    Set global industry mode.

    Args:
        mode: Industry mode to set
    """
    manager = get_mode_manager()
    manager.set_mode(mode)


def get_industry_mode() -> IndustryMode:
    """Get current global industry mode."""
    manager = get_mode_manager()
    return manager.get_mode()


__all__ = [
    "IndustryMode",
    "UserRole",
    "VehicleType",
    "ModeConfiguration",
    "IndustryModeManager",
    "get_mode_manager",
    "set_industry_mode",
    "get_industry_mode",
]









