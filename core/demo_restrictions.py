"""
Demo Restrictions Manager

Manages usage limits and restrictions for demo mode.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

LOGGER = logging.getLogger(__name__)


@dataclass
class UsageLimits:
    """Usage limits for demo mode."""
    max_session_time: int = 300  # 5 minutes per session
    max_exports: int = 10  # Maximum exports
    max_data_points: int = 10000  # Maximum data points per session
    max_logging_time: int = 300  # 5 minutes logging per session
    max_sessions_per_day: int = 5  # Maximum sessions per day
    max_ecu_writes: int = 0  # No ECU writes in demo
    max_video_recordings: int = 0  # No video in demo
    max_cloud_syncs: int = 0  # No cloud sync in demo


class DemoRestrictions:
    """
    Demo restrictions manager.
    
    Tracks usage and enforces limits for demo mode.
    """
    
    def __init__(self) -> None:
        """Initialize demo restrictions."""
        self.limits = UsageLimits()
        self.session_start = time.time()
        self.export_count = 0
        self.data_point_count = 0
        self.logging_start: Optional[float] = None
        self.ecu_write_count = 0
        self.video_recording_count = 0
        self.cloud_sync_count = 0
        self.session_count = 0
        self.last_session_date: Optional[str] = None
        
        # Reset daily counters if new day
        self._check_daily_reset()
    
    def _check_daily_reset(self) -> None:
        """Reset daily counters if new day."""
        today = time.strftime("%Y-%m-%d")
        if self.last_session_date != today:
            self.session_count = 0
            self.last_session_date = today
    
    def can_use_feature(self, feature: str) -> Tuple[bool, str]:
        """
        Check if feature can be used in demo mode.
        
        Args:
            feature: Feature name to check
            
        Returns:
            (allowed, reason_message)
        """
        # Reset daily counters if needed
        self._check_daily_reset()
        
        if feature == 'export':
            if self.export_count >= self.limits.max_exports:
                return False, (
                    f"Demo mode: Maximum {self.limits.max_exports} exports reached. "
                    "Enter a license key to unlock unlimited exports."
                )
            return True, ""
        
        if feature == 'logging':
            if self.logging_start:
                elapsed = time.time() - self.logging_start
                if elapsed >= self.limits.max_logging_time:
                    return False, (
                        f"Demo mode: Maximum {self.limits.max_logging_time}s logging time reached. "
                        "Enter a license key to unlock unlimited logging."
                    )
            return True, ""
        
        if feature == 'data_collection':
            if self.data_point_count >= self.limits.max_data_points:
                return False, (
                    f"Demo mode: Maximum {self.limits.max_data_points} data points reached. "
                    "Enter a license key to unlock unlimited data collection."
                )
            return True, ""
        
        if feature == 'ecu_write':
            if self.ecu_write_count >= self.limits.max_ecu_writes:
                return False, (
                    "Demo mode: ECU writes are disabled. "
                    "Enter a license key to unlock ECU tuning features."
                )
            return True, ""
        
        if feature == 'video_recording':
            if self.video_recording_count >= self.limits.max_video_recordings:
                return False, (
                    "Demo mode: Video recording is disabled. "
                    "Enter a license key to unlock video recording."
                )
            return True, ""
        
        if feature == 'cloud_sync':
            if self.cloud_sync_count >= self.limits.max_cloud_syncs:
                return False, (
                    "Demo mode: Cloud sync is disabled. "
                    "Enter a license key to unlock cloud synchronization."
                )
            return True, ""
        
        if feature == 'new_session':
            if self.session_count >= self.limits.max_sessions_per_day:
                return False, (
                    f"Demo mode: Maximum {self.limits.max_sessions_per_day} sessions per day reached. "
                    "Enter a license key to unlock unlimited sessions."
                )
            return True, ""
        
        return True, ""
    
    def record_export(self) -> None:
        """Record an export operation."""
        self.export_count += 1
        LOGGER.debug(f"Export recorded: {self.export_count}/{self.limits.max_exports}")
    
    def record_data_point(self) -> None:
        """Record a data point collection."""
        self.data_point_count += 1
    
    def record_ecu_write(self) -> None:
        """Record an ECU write operation."""
        self.ecu_write_count += 1
    
    def record_video_recording(self) -> None:
        """Record a video recording."""
        self.video_recording_count += 1
    
    def record_cloud_sync(self) -> None:
        """Record a cloud sync operation."""
        self.cloud_sync_count += 1
    
    def start_logging(self) -> None:
        """Start logging session."""
        self.logging_start = time.time()
        LOGGER.debug("Logging session started")
    
    def stop_logging(self) -> None:
        """Stop logging session."""
        if self.logging_start:
            elapsed = time.time() - self.logging_start
            LOGGER.debug(f"Logging session stopped: {elapsed:.1f}s")
        self.logging_start = None
    
    def start_session(self) -> None:
        """Start a new session."""
        self._check_daily_reset()
        self.session_count += 1
        self.session_start = time.time()
        LOGGER.debug(f"Session started: {self.session_count}/{self.limits.max_sessions_per_day}")
    
    def get_session_time_remaining(self) -> int:
        """Get remaining session time in seconds."""
        elapsed = time.time() - self.session_start
        remaining = self.limits.max_session_time - int(elapsed)
        return max(0, remaining)
    
    def get_logging_time_remaining(self) -> int:
        """Get remaining logging time in seconds."""
        if not self.logging_start:
            return self.limits.max_logging_time
        
        elapsed = time.time() - self.logging_start
        remaining = self.limits.max_logging_time - int(elapsed)
        return max(0, remaining)
    
    def get_usage_stats(self) -> Dict:
        """Get current usage statistics."""
        return {
            'exports_used': self.export_count,
            'exports_remaining': max(0, self.limits.max_exports - self.export_count),
            'data_points_used': self.data_point_count,
            'data_points_remaining': max(0, self.limits.max_data_points - self.data_point_count),
            'session_time_remaining': self.get_session_time_remaining(),
            'logging_time_remaining': self.get_logging_time_remaining(),
            'sessions_today': self.session_count,
            'sessions_remaining': max(0, self.limits.max_sessions_per_day - self.session_count),
        }
    
    def reset_session(self) -> None:
        """Reset session counters (but keep daily counters)."""
        self.export_count = 0
        self.data_point_count = 0
        self.logging_start = None
        self.ecu_write_count = 0
        self.video_recording_count = 0
        self.cloud_sync_count = 0
        self.session_start = time.time()


# Global demo restrictions instance
_demo_restrictions: Optional[DemoRestrictions] = None


def get_demo_restrictions() -> DemoRestrictions:
    """Get global demo restrictions instance."""
    global _demo_restrictions
    if _demo_restrictions is None:
        _demo_restrictions = DemoRestrictions()
    return _demo_restrictions


__all__ = [
    "DemoRestrictions",
    "UsageLimits",
    "get_demo_restrictions",
]










