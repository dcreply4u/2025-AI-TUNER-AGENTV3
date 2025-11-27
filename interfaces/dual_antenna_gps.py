"""
Dual Antenna GPS Interface
Supports dual antenna GPS systems for slip angle calculation and enhanced accuracy.
Based on VBOX 3i Dual Antenna specifications.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from interfaces.gps_interface import GPSInterface, GPSFix

LOGGER = logging.getLogger(__name__)


class DualAntennaStatus(Enum):
    """Dual antenna lock status."""
    DISABLED = "disabled"
    ENABLED_NO_LOCK = "enabled_no_lock"
    LOCKED = "locked"
    ERROR = "error"


@dataclass
class DualAntennaFix:
    """GPS fix from dual antenna system."""
    antenna_a: GPSFix  # Primary antenna
    antenna_b: Optional[GPSFix]  # Secondary antenna (optional)
    separation_distance_m: float  # Distance between antennas
    slip_angle_deg: Optional[float] = None  # Slip angle from dual antenna
    roll_angle_deg: Optional[float] = None  # Roll angle from dual antenna
    pitch_angle_deg: Optional[float] = None  # Pitch angle from dual antenna
    dual_lock_status: DualAntennaStatus = DualAntennaStatus.DISABLED
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        """Calculate derived values."""
        if self.timestamp == 0.0:
            self.timestamp = time.time()
        
        if self.antenna_b is not None:
            self._calculate_angles()

    def _calculate_angles(self) -> None:
        """Calculate slip, roll, and pitch angles from dual antenna positions."""
        if self.antenna_b is None:
            return

        # Calculate vector between antennas
        lat_diff = self.antenna_b.latitude - self.antenna_a.latitude
        lon_diff = self.antenna_b.longitude - self.antenna_a.longitude

        # Convert to meters (approximate)
        lat_m = lat_diff * 111320.0  # meters per degree latitude
        lon_m = lon_diff * 111320.0 * math.cos(math.radians(self.antenna_a.latitude))

        # Calculate distance
        distance = math.sqrt(lat_m**2 + lon_m**2)

        # Calculate heading from antenna A to B
        heading_ab = math.degrees(math.atan2(lon_m, lat_m))
        if heading_ab < 0:
            heading_ab += 360.0

        # Calculate slip angle (difference between vehicle heading and antenna heading)
        vehicle_heading = self.antenna_a.heading
        self.slip_angle_deg = heading_ab - vehicle_heading
        if self.slip_angle_deg > 180:
            self.slip_angle_deg -= 360
        elif self.slip_angle_deg < -180:
            self.slip_angle_deg += 360

        # Calculate roll angle (lateral tilt)
        # Assuming antennas are mounted front-to-back or side-to-side
        # This is a simplified calculation - actual implementation depends on antenna orientation
        if abs(lat_m) > abs(lon_m):
            # Front-to-back mounting
            self.roll_angle_deg = None  # Roll not measurable with front-to-back
            self.pitch_angle_deg = math.degrees(math.asin(
                (self.antenna_b.altitude_m or 0.0 - (self.antenna_a.altitude_m or 0.0)) / distance
            )) if distance > 0 else None
        else:
            # Side-to-side mounting
            self.roll_angle_deg = math.degrees(math.asin(
                (self.antenna_b.altitude_m or 0.0 - (self.antenna_a.altitude_m or 0.0)) / distance
            )) if distance > 0 else None
            self.pitch_angle_deg = None  # Pitch not measurable with side-to-side

        # Update lock status
        if distance > 0 and abs(distance - self.separation_distance_m) < 0.1:
            self.dual_lock_status = DualAntennaStatus.LOCKED
        else:
            self.dual_lock_status = DualAntennaStatus.ENABLED_NO_LOCK

    def to_payload(self) -> dict:
        """Convert to payload dictionary."""
        payload = {
            "antenna_a": self.antenna_a.to_payload(),
            "timestamp": self.timestamp,
            "separation_distance_m": self.separation_distance_m,
            "dual_lock_status": self.dual_lock_status.value,
        }
        
        if self.antenna_b is not None:
            payload["antenna_b"] = self.antenna_b.to_payload()
        
        if self.slip_angle_deg is not None:
            payload["slip_angle_deg"] = self.slip_angle_deg
        
        if self.roll_angle_deg is not None:
            payload["roll_angle_deg"] = self.roll_angle_deg
        
        if self.pitch_angle_deg is not None:
            payload["pitch_angle_deg"] = self.pitch_angle_deg

        return payload


class DualAntennaGPS:
    """
    Dual antenna GPS system for slip angle calculation and enhanced accuracy.
    
    Features:
    - Primary antenna (A) and secondary antenna (B)
    - Slip angle calculation
    - Roll/pitch angle calculation
    - Dual antenna lock detection
    - Orientation testing
    """

    def __init__(
        self,
        antenna_a_port: str = "/dev/ttyUSB1",
        antenna_b_port: Optional[str] = None,
        antenna_a_baudrate: int = 9600,
        antenna_b_baudrate: int = 9600,
        separation_distance_m: float = 1.0,
        orientation: str = "front_to_back",  # "front_to_back" or "side_to_side"
    ) -> None:
        """
        Initialize dual antenna GPS system.
        
        Args:
            antenna_a_port: Serial port for primary antenna (A)
            antenna_b_port: Serial port for secondary antenna (B) (None to disable)
            antenna_a_baudrate: Baud rate for antenna A
            antenna_b_baudrate: Baud rate for antenna B
            separation_distance_m: Distance between antennas in meters
            orientation: Antenna orientation ("front_to_back" or "side_to_side")
        """
        self.separation_distance_m = separation_distance_m
        self.orientation = orientation
        self.enabled = antenna_b_port is not None

        # Initialize primary antenna (always required)
        self.antenna_a = GPSInterface(
            port=antenna_a_port,
            baudrate=antenna_a_baudrate,
        )

        # Initialize secondary antenna (optional)
        self.antenna_b: Optional[GPSInterface] = None
        if antenna_b_port:
            try:
                self.antenna_b = GPSInterface(
                    port=antenna_b_port,
                    baudrate=antenna_b_baudrate,
                )
                LOGGER.info(f"Dual antenna GPS enabled: A={antenna_a_port}, B={antenna_b_port}")
            except Exception as e:
                LOGGER.warning(f"Failed to initialize antenna B: {e}")
                self.antenna_b = None
                self.enabled = False
        else:
            LOGGER.info("Dual antenna GPS disabled (single antenna mode)")

    def close(self) -> None:
        """Close both GPS interfaces."""
        self.antenna_a.close()
        if self.antenna_b:
            self.antenna_b.close()

    def read_fix(self) -> Optional[DualAntennaFix]:
        """
        Read GPS fix from both antennas.
        
        Returns:
            DualAntennaFix if both antennas have valid fixes, None otherwise
        """
        # Read primary antenna (required)
        fix_a = self.antenna_a.read_fix()
        if fix_a is None:
            return None

        # Read secondary antenna (optional)
        fix_b: Optional[GPSFix] = None
        if self.antenna_b:
            fix_b = self.antenna_b.read_fix()
            if fix_b is None:
                # Return single antenna fix if B is not available
                return DualAntennaFix(
                    antenna_a=fix_a,
                    antenna_b=None,
                    separation_distance_m=self.separation_distance_m,
                    dual_lock_status=DualAntennaStatus.ENABLED_NO_LOCK,
                )

        # Create dual antenna fix
        return DualAntennaFix(
            antenna_a=fix_a,
            antenna_b=fix_b,
            separation_distance_m=self.separation_distance_m,
        )

    def set_separation_distance(self, distance_m: float) -> None:
        """Set antenna separation distance in meters."""
        self.separation_distance_m = distance_m
        LOGGER.info(f"Antenna separation set to {distance_m}m")

    def set_orientation(self, orientation: str) -> None:
        """Set antenna orientation."""
        if orientation not in ("front_to_back", "side_to_side"):
            raise ValueError(f"Invalid orientation: {orientation}")
        self.orientation = orientation
        LOGGER.info(f"Antenna orientation set to {orientation}")

    def get_status(self) -> dict:
        """Get dual antenna system status."""
        status = {
            "enabled": self.enabled,
            "separation_distance_m": self.separation_distance_m,
            "orientation": self.orientation,
            "antenna_a_connected": self.antenna_a is not None,
            "antenna_b_connected": self.antenna_b is not None,
        }
        return status


__all__ = ["DualAntennaGPS", "DualAntennaFix", "DualAntennaStatus"]


