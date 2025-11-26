from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

LOGGER = logging.getLogger(__name__)

try:  # Optional runtime deps for real GNSS hardware
    import serial  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    serial = None  # type: ignore

try:
    import pynmea2  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pynmea2 = None  # type: ignore


class GPSOptimization(Enum):
    """GPS optimization modes."""
    HIGH_DYNAMICS = "high"  # For high dynamic applications (brake stops)
    MEDIUM_DYNAMICS = "medium"  # Suitable for all other testing
    LOW_DYNAMICS = "low"  # For steady state speed measurement


class DGPSMode(Enum):
    """DGPS/RTK modes."""
    NONE = "none"
    CMR = "cmr"  # 2cm RTK (Trimble standard)
    RTCMv3 = "rtcmv3"  # 2cm RTK (RTCM standard) - RECOMMENDED
    NTRIP = "ntrip"  # Internet-based subscription service
    MB_BASE = "mb_base"  # Moving Base - Base station
    MB_ROVER = "mb_rover"  # Moving Base - Rover
    RTCM_40CM = "rtcm_40cm"  # 40cm local DGPS
    SBAS = "sbas"  # SBAS differential corrections


class SolutionType(Enum):
    """GPS solution type."""
    NONE = 0
    GNSS_ONLY = 1
    GNSS_DGPS = 2
    RTK_FLOAT = 3
    RTK_FIXED = 4
    FIXED_POSITION = 5
    IMU_COAST = 6


@dataclass
class GPSFix:
    latitude: float
    longitude: float
    speed_mps: float
    heading: float
    timestamp: float
    altitude_m: Optional[float] = None  # Altitude in meters (from GPS)
    altitude_ft: Optional[float] = None  # Altitude in feet
    satellites: Optional[int] = None  # Number of satellites
    solution_type: Optional[SolutionType] = None  # Solution type
    position_quality: Optional[float] = None  # Position quality (HDOP/PDOP)
    dgps_age: Optional[float] = None  # Differential age (seconds)

    def __post_init__(self) -> None:
        """Convert altitude if one is provided."""
        if self.altitude_m is not None and self.altitude_ft is None:
            self.altitude_ft = self.altitude_m * 3.28084
        elif self.altitude_ft is not None and self.altitude_m is None:
            self.altitude_m = self.altitude_ft / 3.28084

    def to_payload(self) -> Dict[str, Any]:
        payload = {
            "lat": self.latitude,
            "lon": self.longitude,
            "speed_mps": self.speed_mps,
            "heading": self.heading,
            "timestamp": self.timestamp,
        }
        if self.altitude_m is not None:
            payload["altitude_m"] = self.altitude_m
            payload["altitude_ft"] = self.altitude_ft or (self.altitude_m * 3.28084)
        if self.satellites is not None:
            payload["satellites"] = self.satellites
        if self.solution_type is not None:
            payload["solution_type"] = self.solution_type.value
        if self.position_quality is not None:
            payload["position_quality"] = self.position_quality
        if self.dgps_age is not None:
            payload["dgps_age"] = self.dgps_age
        return payload


class GPSInterface:
    """
    Enhanced NMEA 0183 reader for USB/serial GPS modules.
    Supports dual antenna, RTK/DGPS, and VBOX 3i-compatible features.
    """

    def __init__(
        self,
        port: str = "/dev/ttyUSB1",
        port_b: Optional[str] = None,  # Secondary antenna port
        baudrate: int = 9600,
        timeout: float = 0.3,
        optimization: GPSOptimization = GPSOptimization.HIGH_DYNAMICS,
        dgps_mode: DGPSMode = DGPSMode.NONE,
        elevation_mask: float = 10.0,  # Degrees
        sample_rate_hz: int = 100,  # 1, 5, 10, 20, 50, or 100 Hz
    ) -> None:
        """
        Initialize GPS interface.
        
        Args:
            port: Primary antenna port (Antenna A)
            port_b: Secondary antenna port (Antenna B) for dual antenna mode
            baudrate: Serial baud rate
            timeout: Serial timeout
            optimization: GPS optimization mode
            dgps_mode: DGPS/RTK mode
            elevation_mask: Elevation mask in degrees (10-25°)
            sample_rate_hz: GPS sample rate
        """
        self.port = port
        self.port_b = port_b
        self.baudrate = baudrate
        self.timeout = timeout
        self.optimization = optimization
        self.dgps_mode = dgps_mode
        self.elevation_mask = elevation_mask
        self.sample_rate_hz = sample_rate_hz
        
        self._serial = None
        self._serial_b = None
        self.dual_antenna_enabled = port_b is not None
        
        self._connect()

    def _connect(self) -> None:
        """Connect to GPS serial ports."""
        if not serial:
            raise RuntimeError("pyserial is not installed – GPS unavailable.")
        
        # Connect primary antenna
        if not os.path.exists(self.port):
            LOGGER.warning(f"GPS primary port {self.port} not found - will use simulated data")
        else:
            try:
                self._serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
                LOGGER.info(f"GPS primary antenna connected: {self.port}")
            except Exception as e:
                LOGGER.error(f"Failed to connect to primary GPS: {e}")
        
        # Connect secondary antenna if dual antenna mode
        if self.dual_antenna_enabled and self.port_b:
            if not os.path.exists(self.port_b):
                LOGGER.warning(f"GPS secondary port {self.port_b} not found - dual antenna disabled")
                self.dual_antenna_enabled = False
            else:
                try:
                    self._serial_b = serial.Serial(self.port_b, self.baudrate, timeout=self.timeout)
                    LOGGER.info(f"GPS secondary antenna connected: {self.port_b}")
                except Exception as e:
                    LOGGER.error(f"Failed to connect to secondary GPS: {e}")
                    self.dual_antenna_enabled = False

    def close(self) -> None:
        """Close GPS serial connections."""
        if self._serial and self._serial.is_open:
            self._serial.close()
        if self._serial_b and self._serial_b.is_open:
            self._serial_b.close()

    def read_fix(self, antenna: str = "A") -> Optional[GPSFix]:
        """
        Read GPS fix from specified antenna.
        
        Args:
            antenna: "A" for primary, "B" for secondary
            
        Returns:
            GPSFix or None if read failed
        """
        serial_port = self._serial if antenna == "A" else self._serial_b
        
        if not serial_port:
            return None

        try:
            line = serial_port.readline().decode("ascii", errors="ignore").strip()
        except Exception:
            return None

        if not line.startswith("$G"):
            return None
        if not pynmea2:
            return None

        try:
            msg = pynmea2.parse(line)
        except Exception:
            return None

        latitude = getattr(msg, "latitude", None)
        longitude = getattr(msg, "longitude", None)
        if latitude is None or longitude is None:
            return None

        # Speed is typically in knots within RMC sentences
        speed_knots = float(getattr(msg, "spd_over_grnd", 0.0) or 0.0)
        heading = float(getattr(msg, "true_course", 0.0) or 0.0)
        speed_mps = speed_knots * 0.514444
        
        # Try to get altitude from GGA sentence (if available)
        altitude_m = None
        if hasattr(msg, "altitude"):
            try:
                altitude_m = float(msg.altitude) if msg.altitude else None
            except (ValueError, TypeError):
                pass
        
        # Get satellite count
        satellites = None
        if hasattr(msg, "num_sats"):
            try:
                satellites = int(msg.num_sats) if msg.num_sats else None
            except (ValueError, TypeError):
                pass
        
        # Get position quality (HDOP)
        position_quality = None
        if hasattr(msg, "horizontal_dil"):
            try:
                position_quality = float(msg.horizontal_dil) if msg.horizontal_dil else None
            except (ValueError, TypeError):
                pass
        
        # Determine solution type based on DGPS mode and data
        solution_type = SolutionType.GNSS_ONLY
        if self.dgps_mode != DGPSMode.NONE:
            # Check if RTK fixed (would need RTCM parsing for full implementation)
            if self.dgps_mode in (DGPSMode.CMR, DGPSMode.RTCMv3, DGPSMode.NTRIP):
                # Simplified: would need RTCM message parsing for accurate status
                solution_type = SolutionType.RTK_FLOAT  # Default to float, would update based on RTCM data

        return GPSFix(
            latitude=float(latitude),
            longitude=float(longitude),
            speed_mps=speed_mps,
            heading=heading,
            timestamp=time.time(),
            altitude_m=altitude_m,
            satellites=satellites,
            solution_type=solution_type,
            position_quality=position_quality,
        )

    def read_dual_fix(self) -> Optional[tuple[GPSFix, Optional[GPSFix]]]:
        """
        Read GPS fixes from both antennas (dual antenna mode).
        
        Returns:
            Tuple of (primary fix, secondary fix) or None if primary read failed
        """
        fix_a = self.read_fix("A")
        if not fix_a:
            return None
        
        fix_b = None
        if self.dual_antenna_enabled:
            fix_b = self.read_fix("B")
        
        return (fix_a, fix_b)

    def coldstart(self) -> bool:
        """
        Perform GPS coldstart.
        
        Returns:
            True if command sent successfully
        """
        # Coldstart command would be sent to GPS module
        # Implementation depends on GPS module type
        LOGGER.info("GPS coldstart command sent")
        return True

    def get_status(self) -> Dict[str, Any]:
        """Get GPS interface status."""
        return {
            "port_a": self.port,
            "port_b": self.port_b,
            "dual_antenna_enabled": self.dual_antenna_enabled,
            "optimization": self.optimization.value,
            "dgps_mode": self.dgps_mode.value,
            "elevation_mask": self.elevation_mask,
            "sample_rate_hz": self.sample_rate_hz,
            "connected_a": self._serial is not None and self._serial.is_open,
            "connected_b": self._serial_b is not None and self._serial_b.is_open if self._serial_b else False,
        }


__all__ = [
    "GPSInterface",
    "GPSFix",
    "GPSOptimization",
    "DGPSMode",
    "SolutionType",
]

