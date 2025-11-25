"""
Maintenance Scheduling Service

Advanced maintenance tracking, scheduling, cost management, and predictive maintenance
for fleet management and personal vehicle use.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class MaintenanceType(Enum):
    """Types of maintenance."""

    OIL_CHANGE = "oil_change"
    TIRE_ROTATION = "tire_rotation"
    BRAKE_SERVICE = "brake_service"
    FLUID_FLUSH = "fluid_flush"
    FILTER_REPLACEMENT = "filter_replacement"
    BELT_REPLACEMENT = "belt_replacement"
    BATTERY_REPLACEMENT = "battery_replacement"
    INSPECTION = "inspection"
    TUNE_UP = "tune_up"
    TRANSMISSION_SERVICE = "transmission_service"
    CUSTOM = "custom"


class MaintenancePriority(Enum):
    """Maintenance priority levels."""

    CRITICAL = "critical"  # Do immediately
    HIGH = "high"  # Do soon
    MEDIUM = "medium"  # Schedule soon
    LOW = "low"  # Routine maintenance
    PREVENTIVE = "preventive"  # Preventive maintenance


@dataclass
class MaintenanceItem:
    """Maintenance item/task."""

    item_id: str
    maintenance_type: MaintenanceType
    description: str
    priority: MaintenancePriority
    mileage_interval: Optional[float] = None  # miles
    time_interval: Optional[float] = None  # days
    last_performed_mileage: Optional[float] = None
    last_performed_date: Optional[float] = None
    next_due_mileage: Optional[float] = None
    next_due_date: Optional[float] = None
    estimated_cost: float = 0.0
    actual_cost: Optional[float] = None
    parts_needed: List[str] = field(default_factory=list)
    notes: str = ""
    is_overdue: bool = False
    days_until_due: Optional[int] = None


@dataclass
class MaintenanceHistory:
    """Maintenance history record."""

    record_id: str
    item_id: str
    performed_date: float
    performed_mileage: float
    cost: float
    technician: Optional[str] = None
    notes: str = ""
    parts_used: List[str] = field(default_factory=list)
    next_due_mileage: Optional[float] = None
    next_due_date: Optional[float] = None


class MaintenanceScheduler:
    """
    Advanced maintenance scheduling and tracking system.

    Features:
    - Mileage-based maintenance reminders
    - Time-based maintenance reminders
    - Service history tracking
    - Cost tracking and budgeting
    - Parts inventory integration
    - Predictive maintenance (based on health score)
    - Downtime prediction
    - Service appointment scheduling
    - Maintenance reports
    """

    def __init__(
        self,
        vehicle_id: str,
        current_mileage: float = 0.0,
        purchase_date: Optional[float] = None,
    ) -> None:
        """
        Initialize maintenance scheduler.

        Args:
            vehicle_id: Vehicle identifier
            current_mileage: Current vehicle mileage
            purchase_date: Vehicle purchase date (timestamp)
        """
        self.vehicle_id = vehicle_id
        self.current_mileage = current_mileage
        self.purchase_date = purchase_date or time.time()

        # Maintenance items
        self.maintenance_items: Dict[str, MaintenanceItem] = {}
        self.maintenance_history: List[MaintenanceHistory] = []

        # Default maintenance schedules
        self._initialize_default_schedule()

    def _initialize_default_schedule(self) -> None:
        """Initialize default maintenance schedule."""
        default_items = [
            MaintenanceItem(
                item_id="oil_change",
                maintenance_type=MaintenanceType.OIL_CHANGE,
                description="Oil Change",
                priority=MaintenancePriority.MEDIUM,
                mileage_interval=5000.0,
                time_interval=180.0,  # 6 months
                estimated_cost=50.0,
            ),
            MaintenanceItem(
                item_id="tire_rotation",
                maintenance_type=MaintenanceType.TIRE_ROTATION,
                description="Tire Rotation",
                priority=MaintenancePriority.LOW,
                mileage_interval=7500.0,
                estimated_cost=30.0,
            ),
            MaintenanceItem(
                item_id="brake_inspection",
                maintenance_type=MaintenanceType.BRAKE_SERVICE,
                description="Brake Inspection",
                priority=MaintenancePriority.HIGH,
                mileage_interval=15000.0,
                estimated_cost=100.0,
            ),
            MaintenanceItem(
                item_id="air_filter",
                maintenance_type=MaintenanceType.FILTER_REPLACEMENT,
                description="Air Filter Replacement",
                priority=MaintenancePriority.LOW,
                mileage_interval=15000.0,
                estimated_cost=25.0,
            ),
            MaintenanceItem(
                item_id="transmission_service",
                maintenance_type=MaintenanceType.TRANSMISSION_SERVICE,
                description="Transmission Service",
                priority=MaintenancePriority.MEDIUM,
                mileage_interval=30000.0,
                estimated_cost=150.0,
            ),
        ]

        for item in default_items:
            self.maintenance_items[item.item_id] = item

    def add_maintenance_item(self, item: MaintenanceItem) -> None:
        """
        Add a maintenance item to the schedule.

        Args:
            item: Maintenance item
        """
        self.maintenance_items[item.item_id] = item
        self._update_item_due_dates(item.item_id)
        LOGGER.info("Added maintenance item: %s", item.description)

    def update_mileage(self, mileage: float) -> List[MaintenanceItem]:
        """
        Update current mileage and check for due maintenance.

        Args:
            mileage: Current vehicle mileage

        Returns:
            List of maintenance items that are due or overdue
        """
        self.current_mileage = mileage
        due_items = []

        for item_id, item in self.maintenance_items.items():
            self._update_item_due_dates(item_id)
            if item.is_overdue or (item.days_until_due is not None and item.days_until_due <= 7):
                due_items.append(item)

        return due_items

    def _update_item_due_dates(self, item_id: str) -> None:
        """Update due dates for a maintenance item."""
        item = self.maintenance_items.get(item_id)
        if not item:
            return

        # Calculate next due based on mileage
        if item.mileage_interval and item.last_performed_mileage is not None:
            item.next_due_mileage = item.last_performed_mileage + item.mileage_interval
            if self.current_mileage >= item.next_due_mileage:
                item.is_overdue = True
            else:
                item.is_overdue = False

        # Calculate next due based on time
        if item.time_interval and item.last_performed_date is not None:
            item.next_due_date = item.last_performed_date + (item.time_interval * 24 * 3600)
            days_until = (item.next_due_date - time.time()) / (24 * 3600)
            item.days_until_due = int(days_until)
            if days_until < 0:
                item.is_overdue = True

        # If no previous maintenance, set initial due dates
        if item.last_performed_mileage is None and item.mileage_interval:
            item.next_due_mileage = item.mileage_interval
            if self.current_mileage >= item.next_due_mileage:
                item.is_overdue = True

        if item.last_performed_date is None and item.time_interval:
            item.next_due_date = self.purchase_date + (item.time_interval * 24 * 3600)
            days_until = (item.next_due_date - time.time()) / (24 * 3600)
            item.days_until_due = int(days_until)
            if days_until < 0:
                item.is_overdue = True

    def record_maintenance(
        self,
        item_id: str,
        cost: float,
        technician: Optional[str] = None,
        notes: str = "",
        parts_used: Optional[List[str]] = None,
    ) -> MaintenanceHistory:
        """
        Record that maintenance was performed.

        Args:
            item_id: Maintenance item ID
            cost: Actual cost
            technician: Technician name
            notes: Maintenance notes
            parts_used: List of parts used

        Returns:
            Maintenance history record
        """
        item = self.maintenance_items.get(item_id)
        if not item:
            raise ValueError(f"Maintenance item not found: {item_id}")

        # Create history record
        record = MaintenanceHistory(
            record_id=f"maint_{int(time.time())}",
            item_id=item_id,
            performed_date=time.time(),
            performed_mileage=self.current_mileage,
            cost=cost,
            technician=technician,
            notes=notes,
            parts_used=parts_used or [],
        )

        # Update item
        item.last_performed_mileage = self.current_mileage
        item.last_performed_date = time.time()
        item.actual_cost = cost
        item.is_overdue = False

        # Calculate next due dates
        if item.mileage_interval:
            record.next_due_mileage = self.current_mileage + item.mileage_interval
        if item.time_interval:
            record.next_due_date = time.time() + (item.time_interval * 24 * 3600)

        item.next_due_mileage = record.next_due_mileage
        item.next_due_date = record.next_due_date

        # Store history
        self.maintenance_history.append(record)

        LOGGER.info("Recorded maintenance: %s, cost: $%.2f", item.description, cost)
        return record

    def get_due_maintenance(self, include_upcoming: bool = True) -> List[MaintenanceItem]:
        """
        Get maintenance items that are due or upcoming.

        Args:
            include_upcoming: Include items due within 7 days

        Returns:
            List of due/upcoming maintenance items
        """
        due_items = []
        for item in self.maintenance_items.values():
            if item.is_overdue:
                due_items.append(item)
            elif include_upcoming and item.days_until_due is not None and item.days_until_due <= 7:
                due_items.append(item)

        # Sort by priority and due date
        due_items.sort(
            key=lambda x: (
                x.priority.value,
                x.days_until_due if x.days_until_due else float("inf"),
            )
        )

        return due_items

    def get_maintenance_cost_summary(
        self, days: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Get maintenance cost summary.

        Args:
            days: Number of days to look back (None = all time)

        Returns:
            Dictionary with cost metrics
        """
        cutoff_time = time.time() - (days * 24 * 3600) if days else 0

        recent_history = [
            h for h in self.maintenance_history if h.performed_date >= cutoff_time
        ]

        total_cost = sum(h.cost for h in recent_history)
        avg_cost = total_cost / len(recent_history) if recent_history else 0.0

        # Calculate cost per mile
        if recent_history:
            mileage_range = (
                max(h.performed_mileage for h in recent_history)
                - min(h.performed_mileage for h in recent_history)
            )
            cost_per_mile = total_cost / mileage_range if mileage_range > 0 else 0.0
        else:
            cost_per_mile = 0.0

        return {
            "total_cost": total_cost,
            "average_cost": avg_cost,
            "service_count": len(recent_history),
            "cost_per_mile": cost_per_mile,
        }

    def predict_downtime(self, health_score: Optional[float] = None) -> Dict[str, Any]:
        """
        Predict potential downtime based on maintenance needs and health.

        Args:
            health_score: Current vehicle health score (0-100)

        Returns:
            Dictionary with downtime predictions
        """
        overdue_count = sum(1 for item in self.maintenance_items.values() if item.is_overdue)
        critical_count = sum(
            1
            for item in self.maintenance_items.values()
            if item.priority == MaintenancePriority.CRITICAL and item.is_overdue
        )

        # Estimate downtime based on overdue items
        estimated_downtime_hours = overdue_count * 2.0  # 2 hours per overdue item
        if critical_count > 0:
            estimated_downtime_hours += critical_count * 8.0  # 8 hours for critical

        # Factor in health score
        if health_score is not None and health_score < 70:
            estimated_downtime_hours += (70 - health_score) * 0.5

        return {
            "estimated_downtime_hours": estimated_downtime_hours,
            "overdue_items": overdue_count,
            "critical_items": critical_count,
            "risk_level": (
                "high" if critical_count > 0 or overdue_count > 3 else "medium" if overdue_count > 0 else "low"
            ),
        }

    def get_upcoming_maintenance_schedule(self, days: int = 90) -> List[MaintenanceItem]:
        """
        Get maintenance schedule for upcoming period.

        Args:
            days: Number of days to look ahead

        Returns:
            List of maintenance items due in period
        """
        cutoff_date = time.time() + (days * 24 * 3600)
        upcoming = []

        for item in self.maintenance_items.values():
            if item.next_due_date and item.next_due_date <= cutoff_date:
                upcoming.append(item)

        upcoming.sort(key=lambda x: x.next_due_date if x.next_due_date else float("inf"))
        return upcoming


__all__ = [
    "MaintenanceType",
    "MaintenancePriority",
    "MaintenanceItem",
    "MaintenanceHistory",
    "MaintenanceScheduler",
]









