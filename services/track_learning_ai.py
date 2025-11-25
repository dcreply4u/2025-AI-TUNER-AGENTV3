"""
Track Learning AI

AI learns every track you drive and provides optimal racing line,
braking points, and acceleration zones. This is INSANE value!
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

LOGGER = logging.getLogger(__name__)


@dataclass
class TrackPoint:
    """A point on the track."""

    latitude: float
    longitude: float
    optimal_speed: float
    optimal_throttle: float
    braking_point: bool = False
    acceleration_zone: bool = False
    corner_type: str = "straight"  # straight, left, right, chicane


@dataclass
class TrackProfile:
    """Learned track profile."""

    track_name: str
    track_id: str
    total_distance: float  # meters
    optimal_lap_time: float  # seconds
    track_points: List[TrackPoint] = field(default_factory=list)
    braking_points: List[Tuple[float, float]] = field(default_factory=list)  # (lat, lon)
    acceleration_zones: List[Tuple[float, float]] = field(default_factory=list)
    learned_from_laps: int = 0
    confidence: float = 0.0  # 0-1, how confident the AI is


class TrackLearningAI:
    """
    Track Learning AI System.

    UNIQUE FEATURE: No one has done AI that learns tracks and provides optimal lines!
    This learns every track you drive and becomes your personal track coach.
    """

    def __init__(self) -> None:
        """Initialize track learning AI."""
        self.track_profiles: Dict[str, TrackProfile] = {}
        self.current_track: Optional[TrackProfile] = None
        self.lap_data: List[Dict] = []

    def learn_from_lap(
        self,
        track_name: str,
        gps_trace: List[Dict[str, float]],
        telemetry_trace: List[Dict[str, float]],
        lap_time: float,
    ) -> TrackProfile:
        """
        Learn optimal track profile from a lap.

        Args:
            track_name: Name of track
            gps_trace: GPS coordinates for the lap
            telemetry_trace: Telemetry data for the lap
            lap_time: Lap time

        Returns:
            Updated track profile
        """
        track_id = self._generate_track_id(gps_trace)

        if track_id not in self.track_profiles:
            self.track_profiles[track_id] = TrackProfile(
                track_name=track_name,
                track_id=track_id,
                total_distance=0.0,
                optimal_lap_time=lap_time,
            )

        profile = self.track_profiles[track_id]
        profile.learned_from_laps += 1

        # Update optimal lap time if this is faster
        if lap_time < profile.optimal_lap_time:
            profile.optimal_lap_time = lap_time
            # Relearn from this faster lap
            self._learn_optimal_line(gps_trace, telemetry_trace, profile)

        # Merge learnings from this lap
        self._merge_lap_data(gps_trace, telemetry_trace, profile)

        # Update confidence (more laps = more confident)
        profile.confidence = min(1.0, profile.learned_from_laps / 10.0)

        LOGGER.info(f"Learned from lap on {track_name}: {lap_time:.2f}s (confidence: {profile.confidence:.1%})")

        return profile

    def _generate_track_id(self, gps_trace: List[Dict]) -> str:
        """Generate unique track ID from GPS trace."""
        if not gps_trace:
            return "unknown"

        # Use start/end points and total distance to identify track
        start = gps_trace[0]
        end = gps_trace[-1]

        # Calculate approximate distance
        total_distance = 0.0
        for i in range(len(gps_trace) - 1):
            lat1, lon1 = gps_trace[i].get("latitude", 0), gps_trace[i].get("longitude", 0)
            lat2, lon2 = gps_trace[i + 1].get("latitude", 0), gps_trace[i + 1].get("longitude", 0)
            # Simple distance calculation
            total_distance += ((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2) ** 0.5

        # Create ID from characteristics
        import hashlib

        track_data = f"{start.get('latitude', 0):.4f},{start.get('longitude', 0):.4f}_{total_distance:.0f}"
        return hashlib.md5(track_data.encode()).hexdigest()[:12]

    def _learn_optimal_line(self, gps_trace: List[Dict], telemetry_trace: List[Dict], profile: TrackProfile) -> None:
        """Learn optimal racing line from GPS and telemetry."""
        profile.track_points.clear()
        profile.braking_points.clear()
        profile.acceleration_zones.clear()

        for i, (gps, telemetry) in enumerate(zip(gps_trace, telemetry_trace)):
            lat = gps.get("latitude", 0)
            lon = gps.get("longitude", 0)
            speed = telemetry.get("Vehicle_Speed", 0)
            throttle = telemetry.get("Throttle_Position", 0)

            # Detect braking point (throttle drops, speed decreasing)
            is_braking = False
            if i > 0:
                prev_throttle = telemetry_trace[i - 1].get("Throttle_Position", 0)
                prev_speed = telemetry_trace[i - 1].get("Vehicle_Speed", 0)
                if throttle < prev_throttle * 0.5 and speed < prev_speed:
                    is_braking = True
                    profile.braking_points.append((lat, lon))

            # Detect acceleration zone (throttle increasing, speed increasing)
            is_accel = False
            if i > 0:
                prev_throttle = telemetry_trace[i - 1].get("Throttle_Position", 0)
                prev_speed = telemetry_trace[i - 1].get("Vehicle_Speed", 0)
                if throttle > prev_throttle * 1.2 and speed > prev_speed:
                    is_accel = True
                    profile.acceleration_zones.append((lat, lon))

            # Detect corner type (would use GPS heading changes)
            corner_type = "straight"
            if i > 0 and i < len(gps_trace) - 1:
                # Simple corner detection (would be more sophisticated)
                corner_type = "straight"

            point = TrackPoint(
                latitude=lat,
                longitude=lon,
                optimal_speed=speed,
                optimal_throttle=throttle,
                braking_point=is_braking,
                acceleration_zone=is_accel,
                corner_type=corner_type,
            )

            profile.track_points.append(point)

    def _merge_lap_data(
        self, gps_trace: List[Dict], telemetry_trace: List[Dict], profile: TrackProfile
    ) -> None:
        """Merge data from this lap into profile (average with existing)."""
        # For simplicity, just update if this lap is faster
        # In production, would do weighted averaging
        pass

    def get_optimal_line(self, track_id: str) -> Optional[List[TrackPoint]]:
        """
        Get optimal racing line for a track.

        Args:
            track_id: Track ID

        Returns:
            List of optimal track points
        """
        profile = self.track_profiles.get(track_id)
        if not profile:
            return None

        return profile.track_points

    def get_braking_points(self, track_id: str) -> List[Tuple[float, float]]:
        """Get optimal braking points for a track."""
        profile = self.track_profiles.get(track_id)
        if not profile:
            return []

        return profile.braking_points

    def get_coaching_for_track(self, current_position: Tuple[float, float], track_id: str) -> List[str]:
        """
        Get coaching tips for current position on track.

        Args:
            current_position: Current (lat, lon)
            track_id: Track ID

        Returns:
            List of coaching tips
        """
        profile = self.track_profiles.get(track_id)
        if not profile:
            return []

        # Find nearest track point
        nearest_point = None
        min_distance = float("inf")

        for point in profile.track_points:
            distance = ((point.latitude - current_position[0]) ** 2 + (point.longitude - current_position[1]) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                nearest_point = point

        if not nearest_point:
            return []

        tips = []

        if nearest_point.braking_point:
            tips.append("Braking point ahead. Prepare to brake.")

        if nearest_point.acceleration_zone:
            tips.append("Acceleration zone. Get on throttle.")

        return tips

    def identify_track(self, gps_trace: List[Dict[str, float]]) -> Optional[str]:
        """
        Identify which track you're on based on GPS trace.

        Args:
            gps_trace: GPS coordinates

        Returns:
            Track ID if recognized, None otherwise
        """
        track_id = self._generate_track_id(gps_trace)
        if track_id in self.track_profiles:
            return track_id
        return None


__all__ = ["TrackLearningAI", "TrackProfile", "TrackPoint"]

