"""
ELD/HOS Compliance Service

Electronic Logging Device (ELD) and Hours of Service (HOS) compliance tracking
for commercial vehicle fleet management and DOT compliance.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class DutyStatus(Enum):
    """DOT duty status types."""

    OFF_DUTY = "off_duty"
    SLEEPER_BERTH = "sleeper_berth"
    DRIVING = "driving"
    ON_DUTY_NOT_DRIVING = "on_duty_not_driving"


class ViolationType(Enum):
    """HOS violation types."""

    DRIVING_TIME_EXCEEDED = "driving_time_exceeded"  # 11 hours
    ON_DUTY_TIME_EXCEEDED = "on_duty_time_exceeded"  # 14 hours
    WEEKLY_DRIVING_EXCEEDED = "weekly_driving_exceeded"  # 60 hours
    WEEKLY_ON_DUTY_EXCEEDED = "weekly_on_duty_exceeded"  # 70 hours
    REST_BREAK_REQUIRED = "rest_break_required"  # 30 min break after 8 hours
    WEEKLY_REST_REQUIRED = "weekly_rest_required"  # 34 hour restart


@dataclass
class DutyStatusRecord:
    """Duty status change record."""

    record_id: str
    timestamp: float
    status: DutyStatus
    location: Optional[tuple[float, float]] = None  # (lat, lon)
    odometer: Optional[float] = None
    remarks: str = ""
    driver_id: Optional[str] = None
    vehicle_id: Optional[str] = None


@dataclass
class HOSMetrics:
    """Hours of Service metrics for current period."""

    driver_id: str
    period_start: float
    driving_time: float = 0.0  # hours
    on_duty_time: float = 0.0  # hours
    off_duty_time: float = 0.0  # hours
    sleeper_berth_time: float = 0.0  # hours
    current_status: DutyStatus = DutyStatus.OFF_DUTY
    last_status_change: float = field(default_factory=time.time)
    violations: List[ViolationType] = field(default_factory=list)
    can_drive: bool = True
    time_until_driving_allowed: Optional[float] = None  # hours


class ELDComplianceTracker:
    """
    Electronic Logging Device (ELD) and Hours of Service (HOS) compliance tracking.

    Features:
    - Real-time HOS tracking
    - DOT compliance monitoring
    - Violation detection and alerts
    - Automatic duty status changes
    - Rest break reminders
    - Weekly hour calculations
    - Compliance reports
    - Audit trail
    """

    # HOS Limits (hours)
    MAX_DRIVING_TIME = 11.0  # 11 hours driving
    MAX_ON_DUTY_TIME = 14.0  # 14 hours on duty
    MAX_WEEKLY_DRIVING = 60.0  # 60 hours in 7 days
    MAX_WEEKLY_ON_DUTY = 70.0  # 70 hours in 7 days
    REST_BREAK_REQUIRED_AFTER = 8.0  # 8 hours driving requires 30 min break
    WEEKLY_REST_REQUIRED = 34.0  # 34 hour restart

    def __init__(self, driver_id: str, vehicle_id: str) -> None:
        """
        Initialize ELD compliance tracker.

        Args:
            driver_id: Driver identifier
            vehicle_id: Vehicle identifier
        """
        self.driver_id = driver_id
        self.vehicle_id = vehicle_id

        # Current metrics
        self.current_metrics = HOSMetrics(
            driver_id=driver_id,
            period_start=time.time(),
        )

        # Duty status history
        self.duty_history: List[DutyStatusRecord] = []

        # Weekly tracking (rolling 7 days)
        self.weekly_driving: List[float] = []  # Hours per day
        self.weekly_on_duty: List[float] = []  # Hours per day

        # Violation callbacks
        self.violation_callbacks: List[callable] = []

    def change_duty_status(
        self,
        status: DutyStatus,
        location: Optional[tuple[float, float]] = None,
        odometer: Optional[float] = None,
        remarks: str = "",
        timestamp: Optional[float] = None,
    ) -> DutyStatusRecord:
        """
        Change driver duty status.

        Args:
            status: New duty status
            location: GPS location
            odometer: Current odometer reading
            remarks: Remarks/notes
            timestamp: Timestamp (defaults to current time)

        Returns:
            Duty status record
        """
        if timestamp is None:
            timestamp = time.time()

        # Calculate time in previous status
        time_in_previous = (timestamp - self.current_metrics.last_status_change) / 3600.0

        # Update metrics based on previous status
        if self.current_metrics.current_status == DutyStatus.DRIVING:
            self.current_metrics.driving_time += time_in_previous
        elif self.current_metrics.current_status == DutyStatus.ON_DUTY_NOT_DRIVING:
            self.current_metrics.on_duty_time += time_in_previous
        elif self.current_metrics.current_status == DutyStatus.OFF_DUTY:
            self.current_metrics.off_duty_time += time_in_previous
        elif self.current_metrics.current_status == DutyStatus.SLEEPER_BERTH:
            self.current_metrics.sleeper_berth_time += time_in_previous

        # Create record
        record = DutyStatusRecord(
            record_id=f"eld_{int(timestamp)}",
            timestamp=timestamp,
            status=status,
            location=location,
            odometer=odometer,
            remarks=remarks,
            driver_id=self.driver_id,
            vehicle_id=self.vehicle_id,
        )

        self.duty_history.append(record)

        # Update current status
        self.current_metrics.current_status = status
        self.current_metrics.last_status_change = timestamp

        # Check for violations
        self._check_violations()

        LOGGER.info("Duty status changed to %s for driver %s", status.value, self.driver_id)
        return record

    def update_driving_time(self, is_driving: bool, timestamp: Optional[float] = None) -> None:
        """
        Update driving time (called automatically when vehicle is moving).

        Args:
            is_driving: Whether vehicle is currently driving
            timestamp: Timestamp (defaults to current time)
        """
        if timestamp is None:
            timestamp = time.time()

        # Auto-change status if needed
        if is_driving and self.current_metrics.current_status != DutyStatus.DRIVING:
            self.change_duty_status(DutyStatus.DRIVING, timestamp=timestamp)
        elif not is_driving and self.current_metrics.current_status == DutyStatus.DRIVING:
            # Don't auto-change from driving (driver must manually change)
            pass

        # Update metrics
        self._update_metrics(timestamp)

    def _update_metrics(self, timestamp: float) -> None:
        """Update HOS metrics."""
        time_since_change = (timestamp - self.current_metrics.last_status_change) / 3600.0

        if self.current_metrics.current_status == DutyStatus.DRIVING:
            self.current_metrics.driving_time += time_since_change
            self.current_metrics.on_duty_time += time_since_change
        elif self.current_metrics.current_status == DutyStatus.ON_DUTY_NOT_DRIVING:
            self.current_metrics.on_duty_time += time_since_change

        self.current_metrics.last_status_change = timestamp

        # Update weekly tracking
        self._update_weekly_tracking()

        # Check violations
        self._check_violations()

    def _update_weekly_tracking(self) -> None:
        """Update rolling 7-day tracking."""
        current_time = time.time()
        cutoff_time = current_time - (7 * 24 * 3600)

        # Filter history to last 7 days
        recent_history = [r for r in self.duty_history if r.timestamp >= cutoff_time]

        # Calculate daily totals
        daily_driving: Dict[int, float] = {}
        daily_on_duty: Dict[int, float] = {}

        for i in range(len(recent_history) - 1):
            record = recent_history[i]
            next_record = recent_history[i + 1]

            duration = (next_record.timestamp - record.timestamp) / 3600.0
            day = int((record.timestamp - cutoff_time) / (24 * 3600))

            if record.status == DutyStatus.DRIVING:
                daily_driving[day] = daily_driving.get(day, 0.0) + duration
            if record.status in [DutyStatus.DRIVING, DutyStatus.ON_DUTY_NOT_DRIVING]:
                daily_on_duty[day] = daily_on_duty.get(day, 0.0) + duration

        self.weekly_driving = [daily_driving.get(i, 0.0) for i in range(7)]
        self.weekly_on_duty = [daily_on_duty.get(i, 0.0) for i in range(7)]

    def _check_violations(self) -> None:
        """Check for HOS violations."""
        violations = []

        # Check driving time limit (11 hours)
        if self.current_metrics.driving_time > self.MAX_DRIVING_TIME:
            violations.append(ViolationType.DRIVING_TIME_EXCEEDED)
            self.current_metrics.can_drive = False
            self.current_metrics.time_until_driving_allowed = (
                self.current_metrics.driving_time - self.MAX_DRIVING_TIME
            )

        # Check on-duty time limit (14 hours)
        if self.current_metrics.on_duty_time > self.MAX_ON_DUTY_TIME:
            violations.append(ViolationType.ON_DUTY_TIME_EXCEEDED)
            if self.current_metrics.current_status == DutyStatus.DRIVING:
                self.current_metrics.can_drive = False

        # Check weekly driving (60 hours in 7 days)
        weekly_driving_total = sum(self.weekly_driving)
        if weekly_driving_total > self.MAX_WEEKLY_DRIVING:
            violations.append(ViolationType.WEEKLY_DRIVING_EXCEEDED)

        # Check weekly on-duty (70 hours in 7 days)
        weekly_on_duty_total = sum(self.weekly_on_duty)
        if weekly_on_duty_total > self.MAX_WEEKLY_ON_DUTY:
            violations.append(ViolationType.WEEKLY_ON_DUTY_EXCEEDED)

        # Check rest break requirement (30 min after 8 hours driving)
        if (
            self.current_metrics.driving_time > self.REST_BREAK_REQUIRED_AFTER
            and self.current_metrics.off_duty_time < 0.5
        ):
            violations.append(ViolationType.REST_BREAK_REQUIRED)

        # Update violations
        new_violations = [v for v in violations if v not in self.current_metrics.violations]
        self.current_metrics.violations = violations

        # Trigger callbacks for new violations
        for violation in new_violations:
            for callback in self.violation_callbacks:
                try:
                    callback(violation, self.current_metrics)
                except Exception as e:
                    LOGGER.error("Error in violation callback: %s", e)

    def get_compliance_status(self) -> Dict[str, Any]:
        """Get current compliance status."""
        return {
            "driver_id": self.driver_id,
            "current_status": self.current_metrics.current_status.value,
            "driving_time_hours": self.current_metrics.driving_time,
            "on_duty_time_hours": self.current_metrics.on_duty_time,
            "off_duty_time_hours": self.current_metrics.off_duty_time,
            "can_drive": self.current_metrics.can_drive,
            "violations": [v.value for v in self.current_metrics.violations],
            "weekly_driving_hours": sum(self.weekly_driving),
            "weekly_on_duty_hours": sum(self.weekly_on_duty),
            "time_until_driving_allowed": self.current_metrics.time_until_driving_allowed,
        }

    def generate_eld_report(
        self, start_date: float, end_date: float
    ) -> Dict[str, Any]:
        """
        Generate ELD compliance report for date range.

        Args:
            start_date: Start timestamp
            end_date: End timestamp

        Returns:
            ELD report dictionary
        """
        period_records = [
            r for r in self.duty_history if start_date <= r.timestamp <= end_date
        ]

        total_driving = 0.0
        total_on_duty = 0.0
        total_off_duty = 0.0

        for i in range(len(period_records) - 1):
            record = period_records[i]
            next_record = period_records[i + 1]
            duration = (next_record.timestamp - record.timestamp) / 3600.0

            if record.status == DutyStatus.DRIVING:
                total_driving += duration
            if record.status in [DutyStatus.DRIVING, DutyStatus.ON_DUTY_NOT_DRIVING]:
                total_on_duty += duration
            if record.status == DutyStatus.OFF_DUTY:
                total_off_duty += duration

        return {
            "driver_id": self.driver_id,
            "vehicle_id": self.vehicle_id,
            "start_date": start_date,
            "end_date": end_date,
            "total_driving_hours": total_driving,
            "total_on_duty_hours": total_on_duty,
            "total_off_duty_hours": total_off_duty,
            "duty_records": [
                {
                    "timestamp": r.timestamp,
                    "status": r.status.value,
                    "location": r.location,
                    "odometer": r.odometer,
                    "remarks": r.remarks,
                }
                for r in period_records
            ],
            "compliance_status": "compliant" if not self.current_metrics.violations else "violations",
        }

    def register_violation_callback(self, callback: callable) -> None:
        """
        Register callback for HOS violations.

        Args:
            callback: Function to call when violation detected
                (receives ViolationType, HOSMetrics)
        """
        self.violation_callbacks.append(callback)


__all__ = [
    "DutyStatus",
    "ViolationType",
    "DutyStatusRecord",
    "HOSMetrics",
    "ELDComplianceTracker",
]









