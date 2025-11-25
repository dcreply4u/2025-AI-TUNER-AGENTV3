"""
Lap Detection Service

Automatically detects laps using GPS coordinates and start/finish line detection.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

LOGGER = logging.getLogger(__name__)


@dataclass
class Lap:
    """Lap data structure."""

    lap_number: int
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None  # seconds
    start_lat: float = 0.0
    start_lon: float = 0.0
    end_lat: float = 0.0
    end_lon: float = 0.0
    max_speed: float = 0.0  # mph
    avg_speed: float = 0.0  # mph
    distance: float = 0.0  # meters
    sectors: List[float] = field(default_factory=list)  # Sector times in seconds


@dataclass
class TrackPoint:
    """GPS track point."""

    latitude: float
    longitude: float
    timestamp: float
    speed: float = 0.0  # mph


class LapDetector:
    """Detects laps using GPS start/finish line crossing."""

    def __init__(
        self,
        start_finish_lat: float,
        start_finish_lon: float,
        detection_radius: float = 50.0,  # meters
        min_lap_time: float = 30.0,  # seconds (minimum valid lap time)
        sector_count: int = 3,  # Number of sectors per lap
    ) -> None:
        """
        Initialize lap detector.

        Args:
            start_finish_lat: Start/finish line latitude
            start_finish_lon: Start/finish line longitude
            detection_radius: Radius for start/finish detection (meters)
            min_lap_time: Minimum valid lap time (seconds)
            sector_count: Number of sectors to track
        """
        self.start_finish_lat = start_finish_lat
        self.start_finish_lon = start_finish_lon
        self.detection_radius = detection_radius
        self.min_lap_time = min_lap_time
        self.sector_count = sector_count

        self.current_lap: Optional[Lap] = None
        self.completed_laps: List[Lap] = []
        self.track_points: List[TrackPoint] = []
        self.last_crossing_time: float = 0.0
        self.sector_markers: List[Tuple[float, float]] = []  # Sector GPS coordinates
        self.current_sector: int = 0
        self.sector_start_time: float = 0.0

    def update(self, lat: float, lon: float, speed: float = 0.0, timestamp: Optional[float] = None) -> Optional[Lap]:
        """
        Update with new GPS position and detect lap completion.

        Args:
            lat: Latitude
            lon: Longitude
            speed: Current speed (mph)
            timestamp: Timestamp (defaults to current time)

        Returns:
            Completed Lap if lap was just finished, None otherwise
        """
        if timestamp is None:
            timestamp = time.time()

        # Add track point
        point = TrackPoint(latitude=lat, longitude=lon, timestamp=timestamp, speed=speed)
        self.track_points.append(point)

        # Check distance to start/finish line
        distance = self._haversine_distance(lat, lon, self.start_finish_lat, self.start_finish_lon)

        if distance <= self.detection_radius:
            # Near start/finish line
            time_since_last_crossing = timestamp - self.last_crossing_time

            if self.current_lap is None:
                # Starting new lap
                self.current_lap = Lap(
                    lap_number=len(self.completed_laps) + 1,
                    start_time=timestamp,
                    start_lat=lat,
                    start_lon=lon,
                    max_speed=speed,
                    avg_speed=speed,
                )
                self.current_sector = 0
                self.sector_start_time = timestamp
                self.last_crossing_time = timestamp
                LOGGER.info("Lap %d started", self.current_lap.lap_number)
                return None

            elif time_since_last_crossing >= self.min_lap_time:
                # Completing lap
                if self.current_lap:
                    self.current_lap.end_time = timestamp
                    self.current_lap.end_lat = lat
                    self.current_lap.end_lon = lon
                    self.current_lap.duration = timestamp - self.current_lap.start_time

                    # Calculate lap statistics
                    self._calculate_lap_stats(self.current_lap)

                    completed_lap = self.current_lap
                    self.completed_laps.append(completed_lap)
                    self.current_lap = None
                    self.last_crossing_time = timestamp

                    LOGGER.info("Lap %d completed: %.2f seconds", completed_lap.lap_number, completed_lap.duration)
                    return completed_lap

        # Update current lap statistics
        if self.current_lap:
            if speed > self.current_lap.max_speed:
                self.current_lap.max_speed = speed

            # Update sector times if sector markers are defined
            if self.sector_markers and self.current_sector < len(self.sector_markers):
                sector_lat, sector_lon = self.sector_markers[self.current_sector]
                sector_distance = self._haversine_distance(lat, lon, sector_lat, sector_lon)
                if sector_distance <= self.detection_radius:
                    sector_time = timestamp - self.sector_start_time
                    if len(self.current_lap.sectors) <= self.current_sector:
                        self.current_lap.sectors.append(sector_time)
                    else:
                        self.current_lap.sectors[self.current_sector] = sector_time
                    self.current_sector += 1
                    self.sector_start_time = timestamp
                    LOGGER.info("Sector %d completed: %.2f seconds", self.current_sector, sector_time)

        return None

    def set_sector_markers(self, markers: List[Tuple[float, float]]) -> None:
        """
        Set sector marker GPS coordinates.

        Args:
            markers: List of (lat, lon) tuples for each sector marker
        """
        self.sector_markers = markers
        LOGGER.info("Set %d sector markers", len(markers))

    def reset_session(self) -> None:
        """Reset lap detection session."""
        self.current_lap = None
        self.completed_laps.clear()
        self.track_points.clear()
        self.last_crossing_time = 0.0
        self.current_sector = 0
        self.sector_start_time = 0.0
        LOGGER.info("Lap detection session reset")

    def get_current_lap(self) -> Optional[Lap]:
        """Get current lap in progress."""
        if self.current_lap:
            # Update current lap duration
            current_time = time.time()
            self.current_lap.duration = current_time - self.current_lap.start_time
        return self.current_lap

    def get_best_lap(self) -> Optional[Lap]:
        """Get best (fastest) completed lap."""
        if not self.completed_laps:
            return None
        return min(self.completed_laps, key=lambda lap: lap.duration or float("inf"))

    def get_lap_count(self) -> int:
        """Get number of completed laps."""
        return len(self.completed_laps)

    def get_track_points(self) -> List[TrackPoint]:
        """Get all recorded track points."""
        return list(self.track_points)

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two GPS coordinates using Haversine formula.

        Returns:
            Distance in meters
        """
        R = 6371000  # Earth radius in meters

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def _calculate_lap_stats(self, lap: Lap) -> None:
        """Calculate lap statistics from track points."""
        if not self.track_points or lap.start_time is None or lap.end_time is None:
            return

        # Filter track points for this lap
        lap_points = [
            p for p in self.track_points
            if lap.start_time <= p.timestamp <= lap.end_time
        ]

        if not lap_points:
            return

        # Calculate average speed
        speeds = [p.speed for p in lap_points if p.speed > 0]
        if speeds:
            lap.avg_speed = sum(speeds) / len(speeds)

        # Calculate distance (sum of distances between consecutive points)
        total_distance = 0.0
        for i in range(len(lap_points) - 1):
            p1 = lap_points[i]
            p2 = lap_points[i + 1]
            total_distance += self._haversine_distance(p1.latitude, p1.longitude, p2.latitude, p2.longitude)
        lap.distance = total_distance


__all__ = ["Lap", "TrackPoint", "LapDetector"]

