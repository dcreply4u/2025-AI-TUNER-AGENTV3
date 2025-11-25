"""
Voice Feedback Service

Provides proactive voice announcements for:
- Performance milestones
- Health warnings
- System status
- GPS updates
- Camera status
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, Optional

from interfaces.voice_output import VoiceOutput


class FeedbackPriority(Enum):
    """Priority levels for voice feedback."""

    LOW = "low"  # Informational
    MEDIUM = "medium"  # Important updates
    HIGH = "high"  # Warnings
    CRITICAL = "critical"  # Urgent alerts


@dataclass
class FeedbackEvent:
    """Voice feedback event."""

    message: str
    priority: FeedbackPriority
    channel: str
    throttle_seconds: float = 5.0
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class VoiceFeedback:
    """Manages proactive voice feedback and announcements."""

    def __init__(self, voice_output: Optional[VoiceOutput] = None, enabled: bool = True) -> None:
        """
        Initialize voice feedback service.

        Args:
            voice_output: VoiceOutput instance for TTS
            enabled: Enable/disable voice feedback
        """
        self.voice_output = voice_output or VoiceOutput()
        self.enabled = enabled and (voice_output is not None or VoiceOutput is not None)

        # Throttling per channel
        self._last_spoken: Dict[str, float] = {}
        self._event_history: list[FeedbackEvent] = []
        self._max_history = 100

        # Performance milestone tracking
        self._announced_milestones: Dict[str, bool] = {}
        self._last_performance_update = 0.0

        # Health status tracking
        self._last_health_status: Optional[str] = None
        self._health_warning_cooldown = 30.0  # Don't repeat health warnings too often

    def announce(self, message: str, priority: FeedbackPriority = FeedbackPriority.MEDIUM, channel: str = "general", throttle: float = 5.0) -> bool:
        """
        Announce a message via voice.

        Args:
            message: Message to speak
            priority: Priority level
            channel: Channel for throttling
            throttle: Minimum seconds between messages on this channel

        Returns:
            True if message was spoken, False if throttled
        """
        if not self.enabled or not message:
            return False

        # Check throttling
        now = time.time()
        last_spoken = self._last_spoken.get(channel, 0.0)
        if now - last_spoken < throttle:
            return False

        # Speak the message
        if self.voice_output:
            self.voice_output.speak(message)
            self._last_spoken[channel] = now

            # Record event
            event = FeedbackEvent(message=message, priority=priority, channel=channel, throttle_seconds=throttle)
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)

            return True
        return False

    def announce_performance(self, metric_name: str, value: float, unit: str = "", is_best: bool = False) -> None:
        """
        Announce performance metrics.

        Args:
            metric_name: Name of metric (e.g., "0-60", "lap time")
            value: Metric value
            unit: Unit string (e.g., "seconds", "mph")
            is_best: Whether this is a new best
        """
        if not self.enabled:
            return

        # Format message
        if is_best:
            message = f"New best {metric_name}: {value:.2f} {unit}"
            priority = FeedbackPriority.HIGH
        else:
            message = f"{metric_name}: {value:.2f} {unit}"
            priority = FeedbackPriority.LOW

        self.announce(message, priority=priority, channel="performance", throttle=3.0)

    def announce_health_warning(self, warning: str, severity: str = "warning") -> None:
        """
        Announce health warnings.

        Args:
            warning: Warning message
            severity: Severity level (warning, critical)
        """
        if not self.enabled:
            return

        priority = FeedbackPriority.CRITICAL if severity == "critical" else FeedbackPriority.HIGH
        self.announce(f"Warning: {warning}", priority=priority, channel="health", throttle=self._health_warning_cooldown)

    def announce_system_status(self, status: str, component: str = "system") -> None:
        """
        Announce system status changes.

        Args:
            status: Status message
            component: Component name
        """
        if not self.enabled:
            return

        message = f"{component}: {status}"
        self.announce(message, priority=FeedbackPriority.LOW, channel=f"status_{component}", throttle=10.0)

    def announce_gps_update(self, speed_mph: Optional[float] = None, location: Optional[str] = None) -> None:
        """
        Announce GPS updates.

        Args:
            speed_mph: Current GPS speed
            location: Location description
        """
        if not self.enabled:
            return

        if speed_mph is not None:
            message = f"GPS speed: {speed_mph:.1f} miles per hour"
            self.announce(message, priority=FeedbackPriority.LOW, channel="gps", throttle=15.0)

        if location:
            message = f"Location: {location}"
            self.announce(message, priority=FeedbackPriority.LOW, channel="gps_location", throttle=60.0)

    def announce_camera_status(self, status: str, camera_name: Optional[str] = None) -> None:
        """
        Announce camera status.

        Args:
            status: Status message
            camera_name: Name of camera (optional)
        """
        if not self.enabled:
            return

        if camera_name:
            message = f"Camera {camera_name}: {status}"
        else:
            message = f"Camera: {status}"

        self.announce(message, priority=FeedbackPriority.MEDIUM, channel="camera", throttle=10.0)

    def update_performance_metrics(self, metrics: Dict[str, Optional[float]], best_metrics: Dict[str, Optional[float]]) -> None:
        """
        Update and announce performance metrics.

        Args:
            metrics: Current metrics
            best_metrics: Best metrics
        """
        if not self.enabled:
            return

        now = time.time()
        # Throttle performance updates
        if now - self._last_performance_update < 5.0:
            return
        self._last_performance_update = now

        # Check for new bests
        for metric_name, current_value in metrics.items():
            if current_value is None:
                continue

            best_value = best_metrics.get(metric_name)
            if best_value is None or current_value < best_value:
                # New best!
                if metric_name not in self._announced_milestones or not self._announced_milestones[metric_name]:
                    unit = "seconds" if "time" in metric_name.lower() or "lap" in metric_name.lower() else "mph"
                    self.announce_performance(metric_name, current_value, unit, is_best=True)
                    self._announced_milestones[metric_name] = True

    def update_health_status(self, health_score: float, status: str, warnings: list[str]) -> None:
        """
        Update and announce health status.

        Args:
            health_score: Current health score (0-100)
            status: Health status string
            warnings: List of warning messages
        """
        if not self.enabled:
            return

        # Announce status change
        if status != self._last_health_status:
            if status.lower() in ("critical", "warning"):
                self.announce_health_warning(f"Engine health: {status}", severity=status.lower())
            elif status.lower() == "good":
                self.announce_system_status("Engine health: Good", "engine")
            self._last_health_status = status

        # Announce warnings
        for warning in warnings:
            self.announce_health_warning(warning)

    def get_recent_events(self, limit: int = 10) -> list[FeedbackEvent]:
        """Get recent feedback events."""
        return self._event_history[-limit:]

    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()
        self._announced_milestones.clear()

    def set_enabled(self, enabled: bool) -> None:
        """Enable/disable voice feedback."""
        self.enabled = enabled


__all__ = ["VoiceFeedback", "FeedbackPriority", "FeedbackEvent"]

