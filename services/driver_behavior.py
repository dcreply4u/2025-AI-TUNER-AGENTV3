"""
Driver Behavior Analysis Service

Advanced driver behavior scoring, event detection, and safety monitoring.
Used for fleet management, insurance telematics, and safety programs.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Deque, Dict, List, Optional, Tuple

import numpy as np

LOGGER = logging.getLogger(__name__)

try:
    from scipy import signal
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    signal = None  # type: ignore


class BehaviorEvent(Enum):
    """Driver behavior event types."""

    HARD_BRAKING = "hard_braking"
    RAPID_ACCELERATION = "rapid_acceleration"
    HARSH_CORNERING = "harsh_cornering"
    SPEEDING = "speeding"
    IDLING = "idling"
    DISTRACTION = "distraction"
    SEATBELT_VIOLATION = "seatbelt_violation"
    FATIGUE = "fatigue"


@dataclass
class BehaviorEventRecord:
    """Record of a driver behavior event."""

    event_type: BehaviorEvent
    timestamp: float
    severity: float  # 0-1, where 1 is most severe
    location: Optional[Tuple[float, float]] = None  # (lat, lon)
    speed: Optional[float] = None  # mph
    g_force: Optional[float] = None
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DriverScore:
    """Driver behavior score and metrics."""

    overall_score: float  # 0-100, higher is better
    safety_score: float  # 0-100
    efficiency_score: float  # 0-100
    compliance_score: float  # 0-100
    event_count: Dict[BehaviorEvent, int] = field(default_factory=dict)
    total_events: int = 0
    total_driving_time: float = 0.0  # seconds
    total_distance: float = 0.0  # miles
    average_speed: float = 0.0  # mph
    idle_time: float = 0.0  # seconds
    speeding_instances: int = 0
    hard_braking_count: int = 0
    rapid_acceleration_count: int = 0
    harsh_cornering_count: int = 0
    last_updated: float = field(default_factory=time.time)


class DriverBehaviorAnalyzer:
    """
    Advanced driver behavior analysis with real-time event detection and scoring.

    Features:
    - Hard braking detection (G-force analysis)
    - Rapid acceleration detection
    - Harsh cornering detection
    - Speeding detection (GPS-based)
    - Idle time tracking
    - Fatigue detection (driving time)
    - Driver scoring algorithm
    - Real-time event alerts
    """

    # Thresholds
    HARD_BRAKE_THRESHOLD = -0.5  # G-force (negative = deceleration)
    RAPID_ACCEL_THRESHOLD = 0.4  # G-force (positive = acceleration)
    HARSH_CORNER_THRESHOLD = 0.3  # Lateral G-force
    SPEEDING_THRESHOLD = 5.0  # mph over speed limit
    IDLE_THRESHOLD = 0.5  # mph (below this = idle)
    IDLE_TIME_THRESHOLD = 30.0  # seconds (idle warning after this)
    FATIGUE_THRESHOLD = 8.0 * 3600  # 8 hours in seconds

    # Scoring weights
    SAFETY_WEIGHT = 0.5
    EFFICIENCY_WEIGHT = 0.3
    COMPLIANCE_WEIGHT = 0.2

    def __init__(
        self,
        speed_limit: Optional[float] = None,
        enable_fatigue_detection: bool = True,
        enable_distraction_detection: bool = False,
    ) -> None:
        """
        Initialize driver behavior analyzer.

        Args:
            speed_limit: Speed limit in mph (None = use GPS speed limit)
            enable_fatigue_detection: Enable fatigue detection based on driving time
            enable_distraction_detection: Enable distraction detection (requires additional sensors)
        """
        self.speed_limit = speed_limit
        self.enable_fatigue_detection = enable_fatigue_detection
        self.enable_distraction_detection = enable_distraction_detection

        # State tracking
        self.events: List[BehaviorEventRecord] = []
        self.current_score = DriverScore(
            overall_score=100.0,
            safety_score=100.0,
            efficiency_score=100.0,
            compliance_score=100.0,
        )

        # Real-time data buffers
        self.speed_history: Deque[float] = deque(maxlen=100)
        self.accel_history: Deque[float] = deque(maxlen=100)
        self.lateral_g_history: Deque[float] = deque(maxlen=100)
        self.timestamps: Deque[float] = deque(maxlen=100)

        # Tracking variables
        self.last_speed: float = 0.0
        self.last_timestamp: float = time.time()
        self.idle_start_time: Optional[float] = None
        self.driving_start_time: Optional[float] = None
        self.total_driving_time: float = 0.0
        self.total_idle_time: float = 0.0
        self.total_distance: float = 0.0

        # Event callbacks
        self.event_callbacks: List[callable] = []

    def update(
        self,
        speed: float,  # mph
        acceleration: Optional[float] = None,  # G-force
        lateral_g: Optional[float] = None,  # G-force
        location: Optional[Tuple[float, float]] = None,  # (lat, lon)
        speed_limit: Optional[float] = None,
        timestamp: Optional[float] = None,
    ) -> List[BehaviorEventRecord]:
        """
        Update analyzer with new telemetry data.

        Args:
            speed: Current speed (mph)
            acceleration: Longitudinal acceleration (G-force)
            lateral_g: Lateral acceleration (G-force)
            location: GPS location (lat, lon)
            speed_limit: Current speed limit (mph)
            timestamp: Timestamp (defaults to current time)

        Returns:
            List of detected events
        """
        if timestamp is None:
            timestamp = time.time()

        detected_events: List[BehaviorEventRecord] = []

        # Calculate acceleration if not provided
        if acceleration is None and len(self.speed_history) > 0:
            dt = timestamp - self.timestamps[-1] if self.timestamps else 1.0
            if dt > 0:
                speed_change = speed - self.last_speed
                acceleration = (speed_change / dt) * 0.045  # Convert to G-force (mph/s to G)

        # Update history
        self.speed_history.append(speed)
        self.timestamps.append(timestamp)
        if acceleration is not None:
            self.accel_history.append(acceleration)
        if lateral_g is not None:
            self.lateral_g_history.append(lateral_g)

        # Detect events
        if acceleration is not None:
            # Hard braking
            if acceleration < self.HARD_BRAKE_THRESHOLD:
                severity = min(abs(acceleration) / abs(self.HARD_BRAKE_THRESHOLD), 1.0)
                event = BehaviorEventRecord(
                    event_type=BehaviorEvent.HARD_BRAKING,
                    timestamp=timestamp,
                    severity=severity,
                    location=location,
                    speed=speed,
                    g_force=acceleration,
                    description=f"Hard braking detected: {acceleration:.2f}G at {speed:.1f} mph",
                )
                detected_events.append(event)
                self.current_score.hard_braking_count += 1

            # Rapid acceleration
            elif acceleration > self.RAPID_ACCEL_THRESHOLD:
                severity = min(acceleration / self.RAPID_ACCEL_THRESHOLD, 1.0)
                event = BehaviorEventRecord(
                    event_type=BehaviorEvent.RAPID_ACCELERATION,
                    timestamp=timestamp,
                    severity=severity,
                    location=location,
                    speed=speed,
                    g_force=acceleration,
                    description=f"Rapid acceleration detected: {acceleration:.2f}G at {speed:.1f} mph",
                )
                detected_events.append(event)
                self.current_score.rapid_acceleration_count += 1

        # Harsh cornering
        if lateral_g is not None and abs(lateral_g) > self.HARSH_CORNER_THRESHOLD:
            severity = min(abs(lateral_g) / self.HARSH_CORNER_THRESHOLD, 1.0)
            event = BehaviorEventRecord(
                event_type=BehaviorEvent.HARSH_CORNERING,
                timestamp=timestamp,
                severity=severity,
                location=location,
                speed=speed,
                g_force=lateral_g,
                description=f"Harsh cornering detected: {abs(lateral_g):.2f}G at {speed:.1f} mph",
            )
            detected_events.append(event)
            self.current_score.harsh_cornering_count += 1

        # Speeding detection
        effective_speed_limit = speed_limit or self.speed_limit
        if effective_speed_limit and speed > effective_speed_limit + self.SPEEDING_THRESHOLD:
            over_speed = speed - effective_speed_limit
            severity = min(over_speed / 20.0, 1.0)  # Max severity at 20+ mph over
            event = BehaviorEventRecord(
                event_type=BehaviorEvent.SPEEDING,
                timestamp=timestamp,
                severity=severity,
                location=location,
                speed=speed,
                description=f"Speeding: {speed:.1f} mph in {effective_speed_limit:.0f} mph zone (+{over_speed:.1f} mph)",
                metadata={"speed_limit": effective_speed_limit, "over_speed": over_speed},
            )
            detected_events.append(event)
            self.current_score.speeding_instances += 1

        # Idle detection
        if speed < self.IDLE_THRESHOLD:
            if self.idle_start_time is None:
                self.idle_start_time = timestamp
            else:
                idle_duration = timestamp - self.idle_start_time
                if idle_duration > self.IDLE_TIME_THRESHOLD:
                    # Only create event once per idle period
                    if not any(
                        e.event_type == BehaviorEvent.IDLING
                        and (timestamp - e.timestamp) < 60.0
                        for e in self.events
                    ):
                        event = BehaviorEventRecord(
                            event_type=BehaviorEvent.IDLING,
                            timestamp=timestamp,
                            severity=min(idle_duration / 300.0, 1.0),  # Max at 5 minutes
                            location=location,
                            speed=speed,
                            description=f"Idling detected: {idle_duration:.0f} seconds",
                            metadata={"idle_duration": idle_duration},
                        )
                        detected_events.append(event)
        else:
            if self.idle_start_time is not None:
                idle_duration = timestamp - self.idle_start_time
                self.total_idle_time += idle_duration
                self.idle_start_time = None

        # Update driving time and distance
        if speed > self.IDLE_THRESHOLD:
            if self.driving_start_time is None:
                self.driving_start_time = timestamp
            dt = timestamp - self.last_timestamp if self.last_timestamp else 0.0
            if dt > 0:
                self.total_driving_time += dt
                # Estimate distance (average speed method)
                avg_speed = (speed + self.last_speed) / 2.0
                self.total_distance += avg_speed * (dt / 3600.0)  # Convert to miles
        else:
            if self.driving_start_time is not None:
                self.driving_start_time = None

        # Fatigue detection
        if self.enable_fatigue_detection and self.total_driving_time > self.FATIGUE_THRESHOLD:
            if not any(
                e.event_type == BehaviorEvent.FATIGUE
                and (timestamp - e.timestamp) < 3600.0
                for e in self.events
            ):
                event = BehaviorEventRecord(
                    event_type=BehaviorEvent.FATIGUE,
                    timestamp=timestamp,
                    severity=min(self.total_driving_time / (12.0 * 3600.0), 1.0),  # Max at 12 hours
                    location=location,
                    description=f"Extended driving time: {self.total_driving_time / 3600.0:.1f} hours",
                    metadata={"driving_time": self.total_driving_time},
                )
                detected_events.append(event)

        # Store events and update score
        for event in detected_events:
            self.events.append(event)
            self.current_score.event_count[event.event_type] = (
                self.current_score.event_count.get(event.event_type, 0) + 1
            )
            self.current_score.total_events += 1

            # Trigger callbacks
            for callback in self.event_callbacks:
                try:
                    callback(event)
                except Exception as e:
                    LOGGER.error("Error in behavior event callback: %s", e)

        # Update tracking variables
        self.last_speed = speed
        self.last_timestamp = timestamp

        # Recalculate scores
        self._update_scores()

        return detected_events

    def _update_scores(self) -> None:
        """Update driver scores based on events and metrics."""
        # Safety score (based on events)
        safety_penalty = 0.0
        if self.current_score.total_events > 0:
            # Penalize based on event severity and frequency
            total_severity = sum(e.severity for e in self.events[-100:])  # Last 100 events
            event_rate = self.current_score.total_events / max(self.total_driving_time / 3600.0, 0.1)
            safety_penalty = min(total_severity * 10.0 + event_rate * 5.0, 100.0)

        self.current_score.safety_score = max(0.0, 100.0 - safety_penalty)

        # Efficiency score (based on idle time and speeding)
        idle_penalty = (self.total_idle_time / max(self.total_driving_time, 1.0)) * 50.0
        speeding_penalty = min(self.current_score.speeding_instances * 2.0, 30.0)
        self.current_score.efficiency_score = max(0.0, 100.0 - idle_penalty - speeding_penalty)

        # Compliance score (based on violations)
        violation_count = (
            self.current_score.speeding_instances
            + self.current_score.hard_braking_count
            + self.current_score.harsh_cornering_count
        )
        compliance_penalty = min(violation_count * 3.0, 100.0)
        self.current_score.compliance_score = max(0.0, 100.0 - compliance_penalty)

        # Overall score (weighted average)
        self.current_score.overall_score = (
            self.current_score.safety_score * self.SAFETY_WEIGHT
            + self.current_score.efficiency_score * self.EFFICIENCY_WEIGHT
            + self.current_score.compliance_score * self.COMPLIANCE_WEIGHT
        )

        # Update metrics
        self.current_score.total_driving_time = self.total_driving_time
        self.current_score.total_distance = self.total_distance
        self.current_score.idle_time = self.total_idle_time
        if self.total_driving_time > 0:
            self.current_score.average_speed = (
                self.total_distance / (self.total_driving_time / 3600.0)
            )
        self.current_score.last_updated = time.time()

    def get_score(self) -> DriverScore:
        """Get current driver score."""
        return self.current_score

    def get_recent_events(
        self, event_type: Optional[BehaviorEvent] = None, limit: int = 50
    ) -> List[BehaviorEventRecord]:
        """
        Get recent behavior events.

        Args:
            event_type: Filter by event type (None = all types)
            limit: Maximum number of events to return

        Returns:
            List of recent events
        """
        events = self.events[-limit:] if limit else self.events
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events

    def get_statistics(self) -> Dict[str, Any]:
        """Get driver behavior statistics."""
        return {
            "overall_score": self.current_score.overall_score,
            "safety_score": self.current_score.safety_score,
            "efficiency_score": self.current_score.efficiency_score,
            "compliance_score": self.current_score.compliance_score,
            "total_events": self.current_score.total_events,
            "total_driving_time_hours": self.total_driving_time / 3600.0,
            "total_distance_miles": self.total_distance,
            "idle_time_hours": self.total_idle_time / 3600.0,
            "average_speed_mph": self.current_score.average_speed,
            "event_counts": {
                event_type.value: count
                for event_type, count in self.current_score.event_count.items()
            },
        }

    def reset_session(self) -> None:
        """Reset current session (keep historical events)."""
        self.current_score = DriverScore(
            overall_score=100.0,
            safety_score=100.0,
            efficiency_score=100.0,
            compliance_score=100.0,
        )
        self.total_driving_time = 0.0
        self.total_idle_time = 0.0
        self.total_distance = 0.0
        self.driving_start_time = None
        self.idle_start_time = None
        self.last_speed = 0.0
        self.last_timestamp = time.time()

    def register_event_callback(self, callback: callable) -> None:
        """
        Register callback for behavior events.

        Args:
            callback: Function to call when event is detected (receives BehaviorEventRecord)
        """
        self.event_callbacks.append(callback)


__all__ = [
    "BehaviorEvent",
    "BehaviorEventRecord",
    "DriverScore",
    "DriverBehaviorAnalyzer",
]









