"""
Logging Health Monitor

Monitors data logging status, detects issues, and provides alerts
(visual and voice) when logging stops or problems occur.
"""

from __future__ import annotations

import logging
import os
import shutil
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

LOGGER = logging.getLogger(__name__)


class LoggingStatus(Enum):
    """Logging status states."""

    ACTIVE = "active"  # Logging normally
    STOPPED = "stopped"  # Logging stopped
    ERROR = "error"  # Error occurred
    STORAGE_FULL = "storage_full"  # Storage full
    STORAGE_ERROR = "storage_error"  # Storage error
    NO_STORAGE = "no_storage"  # No storage available


@dataclass
class LoggingHealth:
    """Current logging health status."""

    status: LoggingStatus
    is_logging: bool
    last_log_time: float
    storage_path: Optional[Path]
    storage_available_gb: float
    storage_total_gb: float
    storage_usage_percent: float
    error_message: Optional[str] = None
    vendor: Optional[str] = None


class LoggingHealthMonitor:
    """Monitors logging health and provides alerts."""

    def __init__(
        self,
        check_interval: float = 2.0,
        alert_threshold_seconds: float = 5.0,
        storage_warning_percent: float = 90.0,
        on_status_change: Optional[Callable[[LoggingHealth], None]] = None,
        voice_alert: Optional[Callable[[str], None]] = None,
    ) -> None:
        """
        Initialize logging health monitor.

        Args:
            check_interval: How often to check logging status (seconds)
            alert_threshold_seconds: Seconds without logging before alert
            storage_warning_percent: Storage usage percentage to warn at
            on_status_change: Callback when status changes
            voice_alert: Callback for voice alerts
        """
        self.check_interval = check_interval
        self.alert_threshold_seconds = alert_threshold_seconds
        self.storage_warning_percent = storage_warning_percent
        self.on_status_change = on_status_change
        self.voice_alert = voice_alert

        self.current_health: Optional[LoggingHealth] = None
        self.last_log_timestamp: float = 0.0
        self.last_status: Optional[LoggingStatus] = None
        self.storage_path: Optional[Path] = None
        self.logging_active = False
        self._alert_cooldown: dict[str, float] = {}

    def set_storage_path(self, path: Path) -> None:
        """Set the storage path to monitor."""
        self.storage_path = Path(path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def update_log_timestamp(self) -> None:
        """Update the last log timestamp (call when data is logged)."""
        self.last_log_timestamp = time.time()
        self.logging_active = True

    def check_health(self) -> LoggingHealth:
        """
        Check current logging health.

        Returns:
            Current health status
        """
        now = time.time()
        time_since_last_log = now - self.last_log_timestamp if self.last_log_timestamp > 0 else float("inf")

        # Determine status
        if not self.storage_path:
            status = LoggingStatus.NO_STORAGE
            is_logging = False
            error_message = "No storage path configured"
        elif not self.storage_path.exists():
            status = LoggingStatus.STORAGE_ERROR
            is_logging = False
            error_message = f"Storage path does not exist: {self.storage_path}"
        elif time_since_last_log > self.alert_threshold_seconds:
            status = LoggingStatus.STOPPED
            is_logging = False
            error_message = f"Logging stopped - no data for {time_since_last_log:.1f} seconds"
        else:
            # Check storage space
            storage_info = self._get_storage_info()
            if storage_info["usage_percent"] >= 100:
                status = LoggingStatus.STORAGE_FULL
                is_logging = False
                error_message = "Storage is full"
            elif storage_info["usage_percent"] >= self.storage_warning_percent:
                status = LoggingStatus.ACTIVE
                is_logging = True
                error_message = f"Storage {storage_info['usage_percent']:.1f}% full"
            else:
                status = LoggingStatus.ACTIVE
                is_logging = True
                error_message = None

        # Get storage info
        storage_info = self._get_storage_info() if self.storage_path else {"available_gb": 0.0, "total_gb": 0.0, "usage_percent": 0.0}

        health = LoggingHealth(
            status=status,
            is_logging=is_logging,
            last_log_time=self.last_log_timestamp,
            storage_path=self.storage_path,
            storage_available_gb=storage_info["available_gb"],
            storage_total_gb=storage_info["total_gb"],
            storage_usage_percent=storage_info["usage_percent"],
            error_message=error_message,
        )

        # Check for status changes and trigger alerts
        if self.last_status != status:
            self._handle_status_change(health)
            self.last_status = status

        self.current_health = health
        return health

    def _get_storage_info(self) -> dict:
        """Get storage information."""
        if not self.storage_path or not self.storage_path.exists():
            return {"available_gb": 0.0, "total_gb": 0.0, "usage_percent": 0.0}

        try:
            stat = shutil.disk_usage(self.storage_path)
            total_gb = stat.total / (1024**3)
            available_gb = stat.free / (1024**3)
            used_gb = (stat.total - stat.free) / (1024**3)
            usage_percent = (used_gb / total_gb * 100) if total_gb > 0 else 0.0

            return {
                "available_gb": available_gb,
                "total_gb": total_gb,
                "usage_percent": usage_percent,
            }
        except Exception as e:
            LOGGER.error("Error getting storage info: %s", e)
            return {"available_gb": 0.0, "total_gb": 0.0, "usage_percent": 100.0}

    def _handle_status_change(self, health: LoggingHealth) -> None:
        """Handle status changes and trigger alerts."""
        # Call status change callback
        if self.on_status_change:
            try:
                self.on_status_change(health)
            except Exception as e:
                LOGGER.error("Error in status change callback: %s", e)

        # Voice alerts for critical issues
        alert_key = health.status.value
        now = time.time()
        last_alert = self._alert_cooldown.get(alert_key, 0.0)

        # Cooldown to prevent spam (different for different alert types)
        cooldown = 30.0 if health.status == LoggingStatus.STOPPED else 60.0

        if now - last_alert > cooldown:
            if health.status == LoggingStatus.STOPPED:
                message = "Warning: Data logging has stopped. No data received."
                self._trigger_voice_alert(message)
                self._alert_cooldown[alert_key] = now
            elif health.status == LoggingStatus.STORAGE_FULL:
                message = "Critical: Storage is full. Logging cannot continue."
                self._trigger_voice_alert(message)
                self._alert_cooldown[alert_key] = now
            elif health.status == LoggingStatus.STORAGE_ERROR:
                message = f"Error: Storage error - {health.error_message}"
                self._trigger_voice_alert(message)
                self._alert_cooldown[alert_key] = now
            elif health.status == LoggingStatus.NO_STORAGE:
                message = "Warning: No storage configured. Logging to local disk."
                self._trigger_voice_alert(message)
                self._alert_cooldown[alert_key] = now
            elif health.error_message and "Storage" in health.error_message and health.storage_usage_percent >= self.storage_warning_percent:
                message = f"Warning: Storage is {health.storage_usage_percent:.1f} percent full."
                self._trigger_voice_alert(message)
                self._alert_cooldown[alert_key] = now

    def _trigger_voice_alert(self, message: str) -> None:
        """Trigger voice alert."""
        if self.voice_alert:
            try:
                self.voice_alert(message)
            except Exception as e:
                LOGGER.error("Error triggering voice alert: %s", e)

    def get_status_message(self) -> str:
        """Get human-readable status message."""
        if not self.current_health:
            return "Status: Unknown"

        health = self.current_health

        if health.status == LoggingStatus.ACTIVE:
            if health.storage_usage_percent >= self.storage_warning_percent:
                return f"Logging: Active (Storage {health.storage_usage_percent:.1f}% full)"
            return f"Logging: Active ({health.storage_available_gb:.1f} GB available)"
        elif health.status == LoggingStatus.STOPPED:
            return f"Logging: STOPPED - {health.error_message}"
        elif health.status == LoggingStatus.STORAGE_FULL:
            return "Logging: STOPPED - Storage Full"
        elif health.status == LoggingStatus.STORAGE_ERROR:
            return f"Logging: ERROR - {health.error_message}"
        elif health.status == LoggingStatus.NO_STORAGE:
            return "Logging: Using Local Disk (No USB)"
        else:
            return f"Logging: {health.status.value.upper()}"

    def get_status_color(self) -> str:
        """Get status color for UI (green/yellow/red)."""
        if not self.current_health:
            return "gray"

        status = self.current_health.status
        if status == LoggingStatus.ACTIVE:
            if self.current_health.storage_usage_percent >= self.storage_warning_percent:
                return "yellow"
            return "green"
        elif status in (LoggingStatus.STOPPED, LoggingStatus.STORAGE_FULL, LoggingStatus.STORAGE_ERROR):
            return "red"
        else:
            return "yellow"


__all__ = ["LoggingHealthMonitor", "LoggingStatus", "LoggingHealth"]

