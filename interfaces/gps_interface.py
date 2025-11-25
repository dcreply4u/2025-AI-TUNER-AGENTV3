from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

try:  # Optional runtime deps for real GNSS hardware
    import serial  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    serial = None  # type: ignore

try:
    import pynmea2  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pynmea2 = None  # type: ignore


@dataclass
class GPSFix:
    latitude: float
    longitude: float
    speed_mps: float
    heading: float
    timestamp: float
    altitude_m: Optional[float] = None  # Altitude in meters (from GPS)
    altitude_ft: Optional[float] = None  # Altitude in feet

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
        return payload


class GPSInterface:
    """Simple NMEA 0183 reader for USB/serial GPS modules."""

    def __init__(
        self,
        port: str = "/dev/ttyUSB1",
        baudrate: int = 9600,
        timeout: float = 0.3,
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial = None
        self._connect()

    def _connect(self) -> None:
        if not serial:
            raise RuntimeError("pyserial is not installed – GPS unavailable.")
        if not os.path.exists(self.port):
            raise FileNotFoundError(f"GPS serial port {self.port} not found.")
        self._serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)

    def close(self) -> None:
        if self._serial and self._serial.is_open:
            self._serial.close()

    def read_fix(self) -> Optional[GPSFix]:
        if not self._serial:
            return None

        try:
            line = self._serial.readline().decode("ascii", errors="ignore").strip()
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

        return GPSFix(
            latitude=float(latitude),
            longitude=float(longitude),
            speed_mps=speed_mps,
            heading=heading,
            timestamp=time.time(),
            altitude_m=altitude_m,
        )


__all__ = ["GPSInterface", "GPSFix"]

