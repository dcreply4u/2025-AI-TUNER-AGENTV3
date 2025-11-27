"""
ADAS (Advanced Driver Assistance Systems) Manager
Implements ADAS testing modes based on VBOX 3i specifications.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

LOGGER = logging.getLogger(__name__)


class ADASMode(Enum):
    """ADAS mode types."""
    OFF = "off"
    ONE_TARGET = "one_target"
    TWO_TARGET = "two_target"
    THREE_TARGET = "three_target"
    STATIC_POINT = "static_point"
    LANE_DEPARTURE = "lane_departure"
    MULTI_STATIC_POINT = "multi_static_point"
    MB_BASE = "mb_base"  # Moving Base - Base station
    MB_ROVER = "mb_rover"  # Moving Base - Rover


class ADASSubmode(Enum):
    """ADAS submode types."""
    SUBJECT = "subject"
    TARGET_1 = "target_1"
    TARGET_2 = "target_2"
    TARGET_3 = "target_3"
    LANE_1 = "lane_1"
    LANE_2 = "lane_2"
    LANE_3 = "lane_3"


@dataclass
class VehiclePosition:
    """Vehicle position data."""
    latitude: float
    longitude: float
    altitude: float
    heading: float
    speed: float
    timestamp: float

    def distance_to(self, other: "VehiclePosition") -> float:
        """Calculate distance to another position in meters."""
        # Haversine formula
        R = 6371000  # Earth radius in meters
        lat1_rad = math.radians(self.latitude)
        lat2_rad = math.radians(other.latitude)
        dlat = math.radians(other.latitude - self.latitude)
        dlon = math.radians(other.longitude - self.longitude)
        
        a = (
            math.sin(dlat / 2) ** 2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c

    def bearing_to(self, other: "VehiclePosition") -> float:
        """Calculate bearing to another position in degrees."""
        lat1_rad = math.radians(self.latitude)
        lat2_rad = math.radians(other.latitude)
        dlon = math.radians(other.longitude - self.longitude)
        
        y = math.sin(dlon) * math.cos(lat2_rad)
        x = (
            math.cos(lat1_rad) * math.sin(lat2_rad) -
            math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)
        )
        
        bearing = math.degrees(math.atan2(y, x))
        return (bearing + 360) % 360


@dataclass
class ADASData:
    """ADAS calculation data."""
    # Vehicle separation (meters)
    separation_distance: float
    
    # Relative position
    relative_x: float  # Forward distance (meters)
    relative_y: float  # Lateral distance (meters)
    relative_z: float  # Vertical distance (meters)
    
    # Relative velocity (m/s)
    relative_speed: float
    
    # Time to collision (seconds)
    ttc: Optional[float] = None
    
    # Lane position
    lane_offset: Optional[float] = None  # Lateral offset from lane center (meters)
    
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        """Initialize timestamp."""
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class ADASManager:
    """
    ADAS Manager for testing and measurement.
    
    Supports:
    - 1/2/3 Target modes
    - Static point mode
    - Lane departure mode
    - Multi static point mode
    - Moving base mode
    """

    def __init__(self) -> None:
        """Initialize ADAS manager."""
        self.mode = ADASMode.OFF
        self.submode: Optional[ADASSubmode] = None
        self.smoothing_enabled = False
        self.smoothing_distance = 10.0  # meters
        self.speed_threshold = 5.0  # m/s
        
        # Subject vehicle position
        self.subject_position: Optional[VehiclePosition] = None
        
        # Target vehicle positions
        self.target_positions: List[VehiclePosition] = []
        
        # Static points
        self.static_points: List[VehiclePosition] = []
        
        # Lane definitions
        self.lane_centers: List[Tuple[float, float]] = []  # List of (lat, lon) points
        
        # Last heading (for smoothing)
        self.last_heading: Optional[float] = None

    def set_mode(self, mode: ADASMode, submode: Optional[ADASSubmode] = None) -> None:
        """
        Set ADAS mode.
        
        Args:
            mode: ADAS mode
            submode: ADAS submode (if applicable)
        """
        self.mode = mode
        self.submode = submode
        LOGGER.info(f"ADAS mode set to {mode.value}, submode: {submode.value if submode else 'None'}")

    def update_subject_position(
        self,
        latitude: float,
        longitude: float,
        altitude: float,
        heading: float,
        speed: float,
    ) -> None:
        """
        Update subject vehicle position.
        
        Args:
            latitude: Latitude (degrees)
            longitude: Longitude (degrees)
            altitude: Altitude (meters)
            heading: Heading (degrees)
            speed: Speed (m/s)
        """
        # Apply smoothing if enabled
        if self.smoothing_enabled and self.last_heading is not None:
            if speed < self.speed_threshold:
                # Lock heading to last value when below speed threshold
                heading = self.last_heading
            else:
                # Smooth heading over smoothing distance
                # Simplified - full implementation would use distance-based smoothing
                heading = 0.7 * self.last_heading + 0.3 * heading

        self.subject_position = VehiclePosition(
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            heading=heading,
            speed=speed,
            timestamp=time.time(),
        )
        self.last_heading = heading

    def update_target_position(
        self,
        target_index: int,
        latitude: float,
        longitude: float,
        altitude: float,
        heading: float,
        speed: float,
    ) -> None:
        """
        Update target vehicle position.
        
        Args:
            target_index: Target index (0, 1, or 2)
            latitude: Latitude (degrees)
            longitude: Longitude (degrees)
            altitude: Altitude (meters)
            heading: Heading (degrees)
            speed: Speed (m/s)
        """
        position = VehiclePosition(
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            heading=heading,
            speed=speed,
            timestamp=time.time(),
        )
        
        # Ensure list is large enough
        while len(self.target_positions) <= target_index:
            self.target_positions.append(position)
        
        self.target_positions[target_index] = position

    def calculate_adas_data(self) -> Optional[ADASData]:
        """
        Calculate ADAS data based on current mode.
        
        Returns:
            ADASData or None if calculation not possible
        """
        if self.mode == ADASMode.OFF or self.subject_position is None:
            return None

        if self.mode == ADASMode.ONE_TARGET:
            if len(self.target_positions) >= 1:
                return self._calculate_target_data(self.target_positions[0])
        
        elif self.mode == ADASMode.TWO_TARGET:
            if len(self.target_positions) >= 2:
                # Return data for primary target (target 1)
                return self._calculate_target_data(self.target_positions[0])
        
        elif self.mode == ADASMode.THREE_TARGET:
            if len(self.target_positions) >= 3:
                # Return data for primary target (target 1)
                return self._calculate_target_data(self.target_positions[0])
        
        elif self.mode == ADASMode.STATIC_POINT:
            if len(self.static_points) >= 1:
                return self._calculate_static_point_data(self.static_points[0])
        
        elif self.mode == ADASMode.LANE_DEPARTURE:
            return self._calculate_lane_departure_data()

        return None

    def _calculate_target_data(self, target: VehiclePosition) -> ADASData:
        """Calculate ADAS data for target vehicle."""
        if self.subject_position is None:
            return ADASData(0, 0, 0, 0, 0)

        # Calculate separation distance
        separation = self.subject_position.distance_to(target)

        # Calculate relative position (simplified - full implementation would use local coordinates)
        lat_diff = target.latitude - self.subject_position.latitude
        lon_diff = target.longitude - self.subject_position.longitude
        
        # Convert to meters
        relative_y = lat_diff * 111320.0
        relative_x = lon_diff * 111320.0 * math.cos(math.radians(self.subject_position.latitude))
        relative_z = target.altitude - self.subject_position.altitude

        # Calculate relative speed
        relative_speed = target.speed - self.subject_position.speed

        # Calculate time to collision
        ttc = None
        if relative_speed < 0 and separation > 0:  # Approaching
            ttc = separation / abs(relative_speed)

        return ADASData(
            separation_distance=separation,
            relative_x=relative_x,
            relative_y=relative_y,
            relative_z=relative_z,
            relative_speed=relative_speed,
            ttc=ttc,
        )

    def _calculate_static_point_data(self, point: VehiclePosition) -> ADASData:
        """Calculate ADAS data for static point."""
        if self.subject_position is None:
            return ADASData(0, 0, 0, 0, 0)

        separation = self.subject_position.distance_to(point)
        
        lat_diff = point.latitude - self.subject_position.latitude
        lon_diff = point.longitude - self.subject_position.longitude
        
        relative_y = lat_diff * 111320.0
        relative_x = lon_diff * 111320.0 * math.cos(math.radians(self.subject_position.latitude))
        relative_z = point.altitude - self.subject_position.altitude

        return ADASData(
            separation_distance=separation,
            relative_x=relative_x,
            relative_y=relative_y,
            relative_z=relative_z,
            relative_speed=-self.subject_position.speed,  # Static point, relative speed is negative of subject speed
        )

    def _calculate_lane_departure_data(self) -> Optional[ADASData]:
        """Calculate lane departure data."""
        if self.subject_position is None or len(self.lane_centers) < 2:
            return None

        # Find nearest lane center point
        min_distance = float('inf')
        nearest_lane_index = 0
        
        for i, (lat, lon) in enumerate(self.lane_centers):
            point = VehiclePosition(lat, lon, 0, 0, 0, time.time())
            distance = self.subject_position.distance_to(point)
            if distance < min_distance:
                min_distance = distance
                nearest_lane_index = i

        # Calculate lateral offset
        lane_point = VehiclePosition(
            self.lane_centers[nearest_lane_index][0],
            self.lane_centers[nearest_lane_index][1],
            0, 0, 0, time.time()
        )
        
        # Simplified lateral offset calculation
        lat_diff = self.subject_position.latitude - lane_point.latitude
        lane_offset = lat_diff * 111320.0

        return ADASData(
            separation_distance=min_distance,
            relative_x=0,
            relative_y=lane_offset,
            relative_z=0,
            relative_speed=0,
            lane_offset=lane_offset,
        )

    def add_static_point(
        self,
        latitude: float,
        longitude: float,
        altitude: float = 0.0,
    ) -> None:
        """Add static point for measurement."""
        point = VehiclePosition(
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            heading=0.0,
            speed=0.0,
            timestamp=time.time(),
        )
        self.static_points.append(point)
        LOGGER.info(f"Static point added: ({latitude}, {longitude})")

    def set_lane_centers(self, lane_centers: List[Tuple[float, float]]) -> None:
        """Set lane center points for lane departure mode."""
        self.lane_centers = lane_centers
        LOGGER.info(f"Lane centers set: {len(lane_centers)} points")

    def set_smoothing(self, enabled: bool, distance: float = 10.0, speed_threshold: float = 5.0) -> None:
        """Set ADAS smoothing parameters."""
        self.smoothing_enabled = enabled
        self.smoothing_distance = distance
        self.speed_threshold = speed_threshold
        LOGGER.info(f"ADAS smoothing: enabled={enabled}, distance={distance}m, threshold={speed_threshold}m/s")

    def get_status(self) -> dict:
        """Get ADAS manager status."""
        return {
            "mode": self.mode.value,
            "submode": self.submode.value if self.submode else None,
            "smoothing_enabled": self.smoothing_enabled,
            "subject_connected": self.subject_position is not None,
            "target_count": len(self.target_positions),
            "static_point_count": len(self.static_points),
        }


__all__ = [
    "ADASManager",
    "ADASMode",
    "ADASSubmode",
    "ADASData",
    "VehiclePosition",
]


