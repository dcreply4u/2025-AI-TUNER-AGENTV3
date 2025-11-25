"""
Industry Integration Service

Integrates all industry-specific services (driver behavior, fuel efficiency,
maintenance, ELD compliance, route optimization, crash detection) with
the main data stream controller.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

LOGGER = logging.getLogger(__name__)

try:
    from core.industry_mode import IndustryMode, IndustryModeManager, get_mode_manager
    from services.driver_behavior import DriverBehaviorAnalyzer, BehaviorEvent
    from services.fuel_efficiency import FuelEfficiencyTracker
    from services.maintenance_scheduler import MaintenanceScheduler
    from services.eld_compliance import ELDComplianceTracker, DutyStatus
    from services.route_optimizer import RouteOptimizer
    from services.crash_detection import CrashDetector, CrashEvent
    from services.fleet_management import FleetManagement
    SERVICES_AVAILABLE = True
except ImportError as e:
    SERVICES_AVAILABLE = False
    LOGGER.warning("Industry services not available: %s", e)


class IndustryIntegration:
    """
    Integrates industry-specific services with telemetry data stream.

    Automatically initializes and updates:
    - Driver behavior analyzer
    - Fuel efficiency tracker
    - Maintenance scheduler
    - ELD compliance tracker
    - Route optimizer
    - Crash detector
    - Fleet management
    """

    def __init__(
        self,
        vehicle_id: str,
        driver_id: Optional[str] = None,
        industry_mode: Optional[IndustryMode] = None,
    ) -> None:
        """
        Initialize industry integration.

        Args:
            vehicle_id: Vehicle identifier
            driver_id: Driver identifier (optional)
            industry_mode: Industry mode (auto-detected if None)
        """
        if not SERVICES_AVAILABLE:
            raise RuntimeError("Industry services not available")

        self.vehicle_id = vehicle_id
        self.driver_id = driver_id
        self.mode_manager = get_mode_manager()

        if industry_mode:
            self.mode_manager.set_mode(industry_mode)
        self.current_mode = self.mode_manager.get_mode()

        # Initialize services based on mode
        self.driver_behavior: Optional[DriverBehaviorAnalyzer] = None
        self.fuel_efficiency: Optional[FuelEfficiencyTracker] = None
        self.maintenance: Optional[MaintenanceScheduler] = None
        self.eld_compliance: Optional[ELDComplianceTracker] = None
        self.route_optimizer: Optional[RouteOptimizer] = None
        self.crash_detector: Optional[CrashDetector] = None
        self.fleet_manager: Optional[FleetManagement] = None

        self._initialize_services()

    def _initialize_services(self) -> None:
        """Initialize services based on current industry mode."""
        config = self.mode_manager.get_config()

        # Driver behavior (fleet, insurance, commercial, personal)
        if self.mode_manager.is_feature_enabled("driver_behavior"):
            self.driver_behavior = DriverBehaviorAnalyzer()
            LOGGER.info("Driver behavior analyzer initialized")

        # Fuel efficiency (fleet, commercial, personal)
        if self.mode_manager.is_feature_enabled("fuel_efficiency"):
            self.fuel_efficiency = FuelEfficiencyTracker(
                vehicle_type="truck" if self.current_mode in [IndustryMode.FLEET, IndustryMode.COMMERCIAL] else "car"
            )
            LOGGER.info("Fuel efficiency tracker initialized")

        # Maintenance scheduling (fleet, commercial, personal)
        if self.mode_manager.is_feature_enabled("maintenance_scheduling"):
            self.maintenance = MaintenanceScheduler(vehicle_id=self.vehicle_id)
            LOGGER.info("Maintenance scheduler initialized")

        # ELD compliance (fleet, commercial)
        if self.mode_manager.is_feature_enabled("eld_compliance") and self.driver_id:
            self.eld_compliance = ELDComplianceTracker(
                driver_id=self.driver_id,
                vehicle_id=self.vehicle_id,
            )
            LOGGER.info("ELD compliance tracker initialized")

        # Route optimizer (fleet, commercial)
        if self.mode_manager.is_feature_enabled("route_optimization"):
            self.route_optimizer = RouteOptimizer()
            LOGGER.info("Route optimizer initialized")

        # Crash detection (fleet, insurance, commercial)
        if self.mode_manager.is_feature_enabled("crash_detection"):
            self.crash_detector = CrashDetector()
            LOGGER.info("Crash detector initialized")

        # Fleet management (fleet, commercial)
        if self.mode_manager.is_feature_enabled("fleet_dashboard"):
            self.fleet_manager = FleetManagement(industry_mode=self.current_mode.value)
            LOGGER.info("Fleet manager initialized")

    def update_telemetry(
        self,
        telemetry: Dict[str, float],
        location: Optional[Tuple[float, float]] = None,
        speed_limit: Optional[float] = None,
    ) -> Dict[str, any]:
        """
        Update all industry services with new telemetry data.

        Args:
            telemetry: Telemetry data dictionary
            location: GPS location (lat, lon)
            speed_limit: Current speed limit (mph)

        Returns:
            Dictionary with updates from all services
        """
        updates = {}

        speed = telemetry.get("speed_mph") or telemetry.get("Vehicle_Speed", 0.0)
        acceleration = telemetry.get("acceleration_g") or telemetry.get("Acceleration", 0.0)
        lateral_g = telemetry.get("lateral_g") or 0.0
        fuel_level = telemetry.get("fuel_level") or telemetry.get("Fuel_Level", None)
        is_idle = speed < 0.5

        # Update driver behavior
        if self.driver_behavior:
            events = self.driver_behavior.update(
                speed=speed,
                acceleration=acceleration,
                lateral_g=lateral_g,
                location=location,
                speed_limit=speed_limit,
            )
            if events:
                updates["driver_events"] = events
            updates["driver_score"] = self.driver_behavior.get_score()

        # Update fuel efficiency
        if self.fuel_efficiency:
            self.fuel_efficiency.update(
                fuel_level=fuel_level,
                location=location,
                speed=speed,
                is_idle=is_idle,
            )
            updates["current_mpg"] = self.fuel_efficiency.get_current_mpg()

        # Update maintenance scheduler
        if self.maintenance:
            mileage = telemetry.get("mileage") or telemetry.get("Odometer", 0.0)
            due_items = self.maintenance.update_mileage(mileage)
            if due_items:
                updates["maintenance_due"] = due_items

        # Update ELD compliance
        if self.eld_compliance:
            is_driving = speed > 0.5
            self.eld_compliance.update_driving_time(is_driving)
            updates["eld_status"] = self.eld_compliance.get_compliance_status()

        # Update crash detector
        if self.crash_detector:
            # Calculate total G-force from acceleration and lateral
            total_g = (acceleration ** 2 + lateral_g ** 2) ** 0.5
            crash_event = self.crash_detector.update(
                g_force=total_g,
                location=location,
                speed=speed,
            )
            if crash_event:
                updates["crash_detected"] = crash_event

        # Update fleet manager
        if self.fleet_manager and self.vehicle_id:
            driver_score = updates.get("driver_score")
            if driver_score:
                self.fleet_manager.update_vehicle_metrics(
                    vehicle_id=self.vehicle_id,
                    driver_score=driver_score.overall_score,
                    fuel_efficiency=updates.get("current_mpg"),
                    location=location,
                )

        return updates

    def set_industry_mode(self, mode: IndustryMode) -> None:
        """
        Change industry mode and reinitialize services.

        Args:
            mode: New industry mode
        """
        self.mode_manager.set_mode(mode)
        self.current_mode = mode
        self._initialize_services()
        LOGGER.info("Industry mode changed to: %s", mode.value)

    def get_fleet_manager(self) -> Optional[FleetManagement]:
        """Get fleet manager instance."""
        return self.fleet_manager

    def get_driver_behavior(self) -> Optional[DriverBehaviorAnalyzer]:
        """Get driver behavior analyzer."""
        return self.driver_behavior

    def get_fuel_efficiency(self) -> Optional[FuelEfficiencyTracker]:
        """Get fuel efficiency tracker."""
        return self.fuel_efficiency

    def get_maintenance(self) -> Optional[MaintenanceScheduler]:
        """Get maintenance scheduler."""
        return self.maintenance

    def get_eld_compliance(self) -> Optional[ELDComplianceTracker]:
        """Get ELD compliance tracker."""
        return self.eld_compliance

    def get_route_optimizer(self) -> Optional[RouteOptimizer]:
        """Get route optimizer."""
        return self.route_optimizer

    def get_crash_detector(self) -> Optional[CrashDetector]:
        """Get crash detector."""
        return self.crash_detector


__all__ = ["IndustryIntegration"]









