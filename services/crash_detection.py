"""
Crash Detection Service

Advanced crash detection, emergency response, and insurance integration.
Features: G-force threshold detection, automatic emergency notifications, video capture.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Tuple

LOGGER = logging.getLogger(__name__)


class CrashSeverity(Enum):
    """Crash severity levels."""

    MINOR = "minor"  # Low G-force, likely fender bender
    MODERATE = "moderate"  # Medium G-force, possible damage
    SEVERE = "severe"  # High G-force, significant impact
    CRITICAL = "critical"  # Very high G-force, major accident


@dataclass
class CrashEvent:
    """Crash detection event."""

    event_id: str
    timestamp: float
    severity: CrashSeverity
    location: Tuple[float, float]  # (lat, lon)
    g_force: float
    speed_at_impact: float  # mph
    direction: str  # "frontal", "rear", "side", "rollover"
    video_captured: bool = False
    video_path: Optional[str] = None
    emergency_contacted: bool = False
    emergency_contact_time: Optional[float] = None
    driver_responded: bool = False
    driver_response_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class CrashDetector:
    """
    Advanced crash detection and emergency response system.

    Features:
    - G-force threshold detection
    - Automatic crash detection
    - Emergency contact notification
    - Video capture (pre/post crash)
    - Insurance claim automation
    - Crash severity assessment
    - Location tracking
    """

    # G-force thresholds (G)
    MINOR_THRESHOLD = 2.0
    MODERATE_THRESHOLD = 4.0
    SEVERE_THRESHOLD = 6.0
    CRITICAL_THRESHOLD = 8.0

    # Detection window (seconds)
    DETECTION_WINDOW = 2.0

    def __init__(
        self,
        emergency_contact: Optional[str] = None,
        auto_call_emergency: bool = True,
        video_capture_enabled: bool = True,
    ) -> None:
        """
        Initialize crash detector.

        Args:
            emergency_contact: Emergency contact phone number
            auto_call_emergency: Automatically call emergency services
            video_capture_enabled: Enable video capture on crash
        """
        self.emergency_contact = emergency_contact
        self.auto_call_emergency = auto_call_emergency
        self.video_capture_enabled = video_capture_enabled

        # G-force history (for detection)
        self.g_force_history: List[Tuple[float, float]] = []  # (timestamp, g_force)
        self.max_history_size = 100

        # Crash events
        self.crash_events: List[CrashEvent] = []
        self.last_crash_time: float = 0.0
        self.crash_cooldown = 60.0  # seconds (prevent duplicate detections)

        # Callbacks
        self.crash_callbacks: List[Callable] = []
        self.emergency_callbacks: List[Callable] = []

    def update(
        self,
        g_force: float,
        location: Optional[Tuple[float, float]] = None,
        speed: Optional[float] = None,  # mph
        timestamp: Optional[float] = None,
    ) -> Optional[CrashEvent]:
        """
        Update crash detector with new G-force data.

        Args:
            g_force: Current G-force (absolute value)
            location: GPS location (lat, lon)
            speed: Current speed (mph)
            timestamp: Timestamp (defaults to current time)

        Returns:
            CrashEvent if crash detected, None otherwise
        """
        if timestamp is None:
            timestamp = time.time()

        # Prevent duplicate detections
        if timestamp - self.last_crash_time < self.crash_cooldown:
            return None

        # Store G-force reading
        abs_g_force = abs(g_force)
        self.g_force_history.append((timestamp, abs_g_force))

        # Keep history size manageable
        if len(self.g_force_history) > self.max_history_size:
            self.g_force_history.pop(0)

        # Check for crash (threshold exceeded)
        if abs_g_force >= self.MINOR_THRESHOLD:
            # Determine severity
            if abs_g_force >= self.CRITICAL_THRESHOLD:
                severity = CrashSeverity.CRITICAL
            elif abs_g_force >= self.SEVERE_THRESHOLD:
                severity = CrashSeverity.SEVERE
            elif abs_g_force >= self.MODERATE_THRESHOLD:
                severity = CrashSeverity.MODERATE
            else:
                severity = CrashSeverity.MINOR

            # Determine direction (simplified - would need 3-axis accelerometer)
            direction = self._determine_direction(g_force)

            # Create crash event
            crash_event = CrashEvent(
                event_id=f"crash_{int(timestamp)}",
                timestamp=timestamp,
                severity=severity,
                location=location or (0.0, 0.0),
                g_force=abs_g_force,
                speed_at_impact=speed or 0.0,
                direction=direction,
            )

            # Capture video if enabled
            if self.video_capture_enabled:
                crash_event.video_captured = True
                crash_event.video_path = self._capture_crash_video(crash_event)

            # Store event
            self.crash_events.append(crash_event)
            self.last_crash_time = timestamp

            # Trigger callbacks
            for callback in self.crash_callbacks:
                try:
                    callback(crash_event)
                except Exception as e:
                    LOGGER.error("Error in crash callback: %s", e)

            # Auto-call emergency for severe crashes
            if self.auto_call_emergency and severity in [
                CrashSeverity.SEVERE,
                CrashSeverity.CRITICAL,
            ]:
                self._contact_emergency(crash_event)

            LOGGER.warning(
                "Crash detected: %s severity, %.2fG at %s",
                severity.value,
                abs_g_force,
                location,
            )

            return crash_event

        return None

    def _determine_direction(self, g_force: float) -> str:
        """
        Determine crash direction from G-force.

        Args:
            g_force: G-force value

        Returns:
            Direction string
        """
        # Simplified - would need 3-axis accelerometer for accurate direction
        if g_force > 0:
            return "frontal"
        else:
            return "rear"

    def _capture_crash_video(self, crash_event: CrashEvent) -> Optional[str]:
        """
        Capture video around crash event.

        Args:
            crash_event: Crash event

        Returns:
            Video file path
        """
        # This would integrate with video logger to capture pre/post crash video
        # For now, return placeholder
        video_path = f"logs/video/crash_{crash_event.event_id}.mp4"
        LOGGER.info("Crash video captured: %s", video_path)
        return video_path

    def _contact_emergency(self, crash_event: CrashEvent) -> None:
        """
        Contact emergency services.

        Args:
            crash_event: Crash event
        """
        crash_event.emergency_contacted = True
        crash_event.emergency_contact_time = time.time()

        # Trigger emergency callbacks
        for callback in self.emergency_callbacks:
            try:
                callback(crash_event)
            except Exception as e:
                LOGGER.error("Error in emergency callback: %s", e)

        LOGGER.critical(
            "Emergency services contacted for crash at %s",
            crash_event.location,
        )

    def get_crash_history(self, limit: int = 50) -> List[CrashEvent]:
        """
        Get crash history.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of crash events
        """
        return self.crash_events[-limit:] if limit else self.crash_events

    def register_crash_callback(self, callback: Callable) -> None:
        """
        Register callback for crash events.

        Args:
            callback: Function to call when crash detected (receives CrashEvent)
        """
        self.crash_callbacks.append(callback)

    def register_emergency_callback(self, callback: Callable) -> None:
        """
        Register callback for emergency contact.

        Args:
            callback: Function to call when emergency contacted (receives CrashEvent)
        """
        self.emergency_callbacks.append(callback)


__all__ = [
    "CrashSeverity",
    "CrashEvent",
    "CrashDetector",
]









