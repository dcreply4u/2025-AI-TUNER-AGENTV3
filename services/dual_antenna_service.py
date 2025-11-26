"""
Dual Antenna Service
Calculates slip angle and vehicle attitude from dual GPS antenna system.
Based on VBOX 3i Dual Antenna specifications.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass
from typing import Optional, Tuple

from interfaces.gps_interface import GPSFix

LOGGER = logging.getLogger(__name__)


@dataclass
class SlipAngleData:
    """Slip angle data from dual antenna."""
    # Slip angles (degrees)
    slip_angle_front_left: float
    slip_angle_front_right: float
    slip_angle_rear_left: float
    slip_angle_rear_right: float
    slip_angle_cog: float  # Center of gravity
    
    # Vehicle attitude (degrees)
    pitch_angle: float
    roll_angle: float
    heading: float
    
    # Dual antenna status
    dual_antenna_locked: bool
    antenna_separation: float  # meters
    
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        """Initialize timestamp."""
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class DualAntennaService:
    """
    Dual antenna service for slip angle and attitude calculation.
    
    Calculates:
    - Slip angle (front/rear, left/right, COG)
    - Vehicle pitch and roll from antenna separation
    - Heading from dual antenna
    """
    
    def __init__(
        self,
        antenna_separation: float = 1.0,  # meters
        wheelbase: float = 2.7,  # meters (typical car)
        track_width: float = 1.5,  # meters (typical car)
    ) -> None:
        """
        Initialize dual antenna service.
        
        Args:
            antenna_separation: Distance between antennas (meters)
            wheelbase: Vehicle wheelbase (meters)
            track_width: Vehicle track width (meters)
        """
        self.antenna_separation = antenna_separation
        self.wheelbase = wheelbase
        self.track_width = track_width
        
        self.dual_antenna_locked = False
        self.last_fix_a: Optional[GPSFix] = None
        self.last_fix_b: Optional[GPSFix] = None
        
    def update(
        self,
        fix_a: GPSFix,
        fix_b: Optional[GPSFix] = None,
    ) -> Optional[SlipAngleData]:
        """
        Update with GPS fixes and calculate slip angle.
        
        Args:
            fix_a: Primary antenna fix (Antenna A)
            fix_b: Secondary antenna fix (Antenna B) - optional
            
        Returns:
            SlipAngleData or None if calculation not possible
        """
        self.last_fix_a = fix_a
        
        # If no secondary antenna, can't calculate dual antenna features
        if fix_b is None:
            self.dual_antenna_locked = False
            return None
        
        self.last_fix_b = fix_b
        self.dual_antenna_locked = True
        
        # Calculate heading from dual antenna
        heading = self._calculate_heading(fix_a, fix_b)
        
        # Calculate pitch and roll from antenna positions
        pitch, roll = self._calculate_attitude(fix_a, fix_b)
        
        # Calculate slip angles (simplified - full implementation would use vehicle geometry)
        slip_data = self._calculate_slip_angles(fix_a, fix_b, heading, pitch, roll)
        
        return SlipAngleData(
            slip_angle_front_left=slip_data[0],
            slip_angle_front_right=slip_data[1],
            slip_angle_rear_left=slip_data[2],
            slip_angle_rear_right=slip_data[3],
            slip_angle_cog=slip_data[4],
            pitch_angle=pitch,
            roll_angle=roll,
            heading=heading,
            dual_antenna_locked=True,
            antenna_separation=self.antenna_separation,
        )
    
    def _calculate_heading(self, fix_a: GPSFix, fix_b: GPSFix) -> float:
        """
        Calculate vehicle heading from dual antenna positions.
        
        Args:
            fix_a: Primary antenna fix
            fix_b: Secondary antenna fix
            
        Returns:
            Heading in degrees (0-360)
        """
        # Calculate bearing from antenna A to antenna B
        lat1_rad = math.radians(fix_a.latitude)
        lat2_rad = math.radians(fix_b.latitude)
        dlon = math.radians(fix_b.longitude - fix_a.longitude)
        
        y = math.sin(dlon) * math.cos(lat2_rad)
        x = (
            math.cos(lat1_rad) * math.sin(lat2_rad) -
            math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)
        )
        
        bearing = math.degrees(math.atan2(y, x))
        return (bearing + 360) % 360
    
    def _calculate_attitude(
        self,
        fix_a: GPSFix,
        fix_b: GPSFix,
    ) -> Tuple[float, float]:
        """
        Calculate vehicle pitch and roll from dual antenna positions.
        
        Args:
            fix_a: Primary antenna fix
            fix_b: Secondary antenna fix
            
        Returns:
            Tuple of (pitch, roll) in degrees
        """
        # Calculate distance between antennas
        distance = self._haversine_distance(
            fix_a.latitude, fix_a.longitude,
            fix_b.latitude, fix_b.longitude
        )
        
        # Calculate altitude difference
        alt_a = fix_a.altitude_m or 0.0
        alt_b = fix_b.altitude_m or 0.0
        alt_diff = alt_b - alt_a
        
        # Calculate pitch (forward/backward tilt)
        # Simplified: assumes antennas are aligned front-to-back
        pitch = math.degrees(math.asin(alt_diff / max(distance, 0.01)))
        
        # Calculate roll (left/right tilt)
        # Simplified: would need lateral antenna separation for accurate roll
        roll = 0.0  # Placeholder - would need antenna geometry
        
        return (pitch, roll)
    
    def _calculate_slip_angles(
        self,
        fix_a: GPSFix,
        fix_b: GPSFix,
        heading: float,
        pitch: float,
        roll: float,
    ) -> Tuple[float, float, float, float, float]:
        """
        Calculate slip angles for all wheel positions.
        
        Args:
            fix_a: Primary antenna fix
            fix_b: Secondary antenna fix
            heading: Vehicle heading
            pitch: Vehicle pitch
            roll: Vehicle roll
            
        Returns:
            Tuple of (front_left, front_right, rear_left, rear_right, cog) slip angles
        """
        # Simplified slip angle calculation
        # Full implementation would use:
        # - Vehicle speed vector
        # - Vehicle heading
        # - Wheel positions relative to antennas
        # - Lateral velocity from dual antenna
        
        # For now, return placeholder values
        # Real implementation would calculate from vehicle dynamics
        cog_slip = 0.0  # Would calculate from heading vs velocity vector
        
        # Distribute slip to wheels (simplified)
        front_left = cog_slip + roll * 0.1
        front_right = cog_slip - roll * 0.1
        rear_left = cog_slip + roll * 0.1
        rear_right = cog_slip - roll * 0.1
        
        return (front_left, front_right, rear_left, rear_right, cog_slip)
    
    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """Calculate distance between two GPS coordinates in meters."""
        R = 6371000  # Earth radius in meters
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (
            math.sin(dlat / 2) ** 2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def get_status(self) -> dict:
        """Get dual antenna service status."""
        return {
            "dual_antenna_locked": self.dual_antenna_locked,
            "antenna_separation": self.antenna_separation,
            "has_fix_a": self.last_fix_a is not None,
            "has_fix_b": self.last_fix_b is not None,
        }


__all__ = ["DualAntennaService", "SlipAngleData"]

