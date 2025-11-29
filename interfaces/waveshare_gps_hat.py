"""
Waveshare GPS HAT Interface

Supports Waveshare GPS HAT modules for Raspberry Pi, including:
- L76K GPS module
- MAX-7Q GPS module
- Generic NMEA GPS modules via UART

This interface provides GPS data for:
- Lap timing and track mapping
- Speed and position tracking
- Route logging
- Theft tracking
"""

from __future__ import annotations

import logging
import os
import time
from typing import Optional, Dict, Any

LOGGER = logging.getLogger(__name__)

# Try to import GPS libraries
try:
    import serial  # type: ignore
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    serial = None  # type: ignore

try:
    import pynmea2  # type: ignore
    PYNNMEA2_AVAILABLE = True
except ImportError:
    PYNNMEA2_AVAILABLE = False
    pynmea2 = None  # type: ignore

# Import existing GPS interface
try:
    from interfaces.gps_interface import GPSInterface, GPSFix, GPSOptimization, DGPSMode
except ImportError:
    GPSInterface = None  # type: ignore
    GPSFix = None  # type: ignore
    GPSOptimization = None  # type: ignore
    DGPSMode = None  # type: ignore

# Simulator mode
SIMULATOR_MODE = False


class WaveshareGPSHAT:
    """
    Interface for Waveshare GPS HAT modules.
    
    Supports both hardware and simulator modes.
    Automatically detects common UART ports on Raspberry Pi.
    """
    
    # Common UART ports on Raspberry Pi
    DEFAULT_PORTS = [
        "/dev/ttyAMA0",  # Primary UART on Pi
        "/dev/ttyAMA1",  # Secondary UART on Pi 5
        "/dev/serial0",  # Alias for primary UART
        "/dev/serial1",  # Alias for secondary UART
        "/dev/ttyUSB0",  # USB serial adapter
        "/dev/ttyUSB1",  # USB serial adapter
    ]
    
    # Common baud rates for GPS modules
    DEFAULT_BAUDRATE = 9600
    HIGH_SPEED_BAUDRATE = 115200
    
    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: int = 9600,
        timeout: float = 0.3,
        use_simulator: bool = False,
        auto_detect: bool = True,
    ) -> None:
        """
        Initialize Waveshare GPS HAT.
        
        Args:
            port: Serial port path (None for auto-detect)
            baudrate: Serial baud rate (9600 or 115200)
            timeout: Serial timeout in seconds
            use_simulator: Use simulator instead of hardware
            auto_detect: Automatically detect GPS port if not specified
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.use_simulator = use_simulator or SIMULATOR_MODE
        self.auto_detect = auto_detect
        
        self.connected = False
        self._serial: Optional[Any] = None
        self._gps_interface: Optional[Any] = None
        
        # Simulator state
        self._sim_lat = 37.7749  # Default: San Francisco
        self._sim_lon = -122.4194
        self._sim_speed = 0.0
        self._sim_heading = 0.0
        self._sim_altitude = 0.0
        
        LOGGER.info(f"Waveshare GPS HAT initialized (simulator={self.use_simulator})")
    
    def connect(self) -> bool:
        """
        Connect to the GPS HAT.
        
        Returns:
            True if connected successfully
        """
        if self.use_simulator:
            self.connected = True
            LOGGER.info("Waveshare GPS HAT: Using simulator mode")
            return True
        
        if not SERIAL_AVAILABLE:
            LOGGER.warning("pyserial not available, using simulator")
            self.use_simulator = True
            self.connected = True
            return True
        
        # Auto-detect port if not specified
        if self.port is None and self.auto_detect:
            self.port = self._detect_gps_port()
            if self.port is None:
                LOGGER.warning("Could not auto-detect GPS port, using simulator")
                self.use_simulator = True
                self.connected = True
                return True
        
        if self.port is None:
            LOGGER.warning("No GPS port specified, using simulator")
            self.use_simulator = True
            self.connected = True
            return True
        
        # Try to connect to GPS
        try:
            if not os.path.exists(self.port):
                LOGGER.warning(f"GPS port {self.port} not found, using simulator")
                self.use_simulator = True
                self.connected = True
                return True
            
            # Use existing GPSInterface if available
            if GPSInterface is not None:
                try:
                    self._gps_interface = GPSInterface(
                        port=self.port,
                        baudrate=self.baudrate,
                        timeout=self.timeout,
                    )
                    # Test read
                    test_fix = self._gps_interface.read_fix()
                    if test_fix is not None:
                        self.connected = True
                        LOGGER.info(f"Waveshare GPS HAT: Connected via GPSInterface on {self.port}")
                        return True
                    else:
                        LOGGER.warning("GPS port exists but no data received, using simulator")
                        self.use_simulator = True
                        self.connected = True
                        return True
                except Exception as e:
                    LOGGER.warning(f"Failed to connect via GPSInterface: {e}, trying direct serial")
            
            # Fallback to direct serial connection
            self._serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            # Test read
            test_line = self._serial.readline()
            if test_line:
                self.connected = True
                LOGGER.info(f"Waveshare GPS HAT: Connected via direct serial on {self.port}")
                return True
            else:
                LOGGER.warning("GPS port exists but no data received, using simulator")
                self.use_simulator = True
                self.connected = True
                return True
                
        except Exception as e:
            LOGGER.warning(f"Failed to connect to GPS: {e}, using simulator")
            self.use_simulator = True
            self.connected = True
            return True
    
    def _detect_gps_port(self) -> Optional[str]:
        """
        Auto-detect GPS port by checking common UART devices.
        
        Returns:
            Port path if found, None otherwise
        """
        for port in self.DEFAULT_PORTS:
            if os.path.exists(port):
                # Try to read from it to see if it's a GPS
                try:
                    test_ser = serial.Serial(port, self.baudrate, timeout=0.5)
                    test_line = test_ser.readline().decode('ascii', errors='ignore').strip()
                    test_ser.close()
                    
                    if test_line.startswith('$'):  # NMEA sentence
                        LOGGER.info(f"Auto-detected GPS on {port}")
                        return port
                except Exception:
                    # Try high-speed baud rate
                    try:
                        test_ser = serial.Serial(port, self.HIGH_SPEED_BAUDRATE, timeout=0.5)
                        test_line = test_ser.readline().decode('ascii', errors='ignore').strip()
                        test_ser.close()
                        
                        if test_line.startswith('$'):  # NMEA sentence
                            LOGGER.info(f"Auto-detected GPS on {port} at {self.HIGH_SPEED_BAUDRATE} baud")
                            self.baudrate = self.HIGH_SPEED_BAUDRATE
                            return port
                    except Exception:
                        continue
        
        return None
    
    def disconnect(self) -> None:
        """Disconnect from the GPS HAT."""
        if self._gps_interface:
            try:
                self._gps_interface.close()
            except Exception:
                pass
            self._gps_interface = None
        
        if self._serial:
            try:
                self._serial.close()
            except Exception:
                pass
            self._serial = None
        
        self.connected = False
        LOGGER.info("Waveshare GPS HAT: Disconnected")
    
    def is_connected(self) -> bool:
        """Check if connected to the GPS HAT."""
        return self.connected
    
    def read_fix(self) -> Optional[Any]:
        """
        Read GPS fix.
        
        Returns:
            GPSFix object, or None if error
        """
        if not self.connected:
            if not self.connect():
                return None
        
        if self.use_simulator:
            return self._read_simulator()
        
        # Use GPSInterface if available
        if self._gps_interface:
            try:
                return self._gps_interface.read_fix()
            except Exception as e:
                LOGGER.error(f"Error reading GPS via GPSInterface: {e}")
                return None
        
        # Fallback to direct serial reading
        if self._serial:
            return self._read_serial_direct()
        
        return None
    
    def _read_serial_direct(self) -> Optional[Any]:
        """Read GPS data directly from serial port."""
        if not self._serial or not self._serial.is_open:
            return None
        
        try:
            line = self._serial.readline().decode('ascii', errors='ignore').strip()
            
            if not line.startswith('$'):
                return None
            
            if not PYNNMEA2_AVAILABLE:
                LOGGER.warning("pynmea2 not available for parsing")
                return None
            
            msg = pynmea2.parse(line)
            
            latitude = getattr(msg, "latitude", None)
            longitude = getattr(msg, "longitude", None)
            if latitude is None or longitude is None:
                return None
            
            speed_knots = float(getattr(msg, "spd_over_grnd", 0.0) or 0.0)
            heading = float(getattr(msg, "true_course", 0.0) or 0.0)
            speed_mps = speed_knots * 0.514444
            
            altitude_m = None
            if hasattr(msg, "altitude"):
                try:
                    altitude_m = float(msg.altitude) if msg.altitude else None
                except (ValueError, TypeError):
                    pass
            
            satellites = None
            if hasattr(msg, "num_sats"):
                try:
                    satellites = int(msg.num_sats) if msg.num_sats else None
                except (ValueError, TypeError):
                    pass
            
            # Create GPSFix if available
            if GPSFix is not None:
                return GPSFix(
                    latitude=float(latitude),
                    longitude=float(longitude),
                    speed_mps=speed_mps,
                    heading=heading,
                    timestamp=time.time(),
                    altitude_m=altitude_m,
                    satellites=satellites,
                )
            else:
                # Return dict if GPSFix not available
                return {
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                    "speed_mps": speed_mps,
                    "heading": heading,
                    "timestamp": time.time(),
                    "altitude_m": altitude_m,
                    "satellites": satellites,
                }
                
        except Exception as e:
            LOGGER.error(f"Error reading GPS serial data: {e}")
            return None
    
    def _read_simulator(self) -> Optional[Any]:
        """Generate simulated GPS fix."""
        import random
        
        # Simulate realistic GPS movement
        self._sim_lat += random.uniform(-0.0001, 0.0001)
        self._sim_lon += random.uniform(-0.0001, 0.0001)
        self._sim_speed = random.uniform(0, 50)  # 0-50 m/s
        self._sim_heading = random.uniform(0, 360)
        self._sim_altitude = random.uniform(0, 100)
        
        if GPSFix is not None:
            return GPSFix(
                latitude=self._sim_lat,
                longitude=self._sim_lon,
                speed_mps=self._sim_speed,
                heading=self._sim_heading,
                timestamp=time.time(),
                altitude_m=self._sim_altitude,
                satellites=8,
            )
        else:
            return {
                "latitude": self._sim_lat,
                "longitude": self._sim_lon,
                "speed_mps": self._sim_speed,
                "heading": self._sim_heading,
                "timestamp": time.time(),
                "altitude_m": self._sim_altitude,
                "satellites": 8,
            }
    
    def set_simulator_position(
        self,
        latitude: float,
        longitude: float,
        altitude: float = 0.0,
    ) -> None:
        """
        Set simulator position (for testing).
        
        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees
            altitude: Altitude in meters
        """
        self._sim_lat = latitude
        self._sim_lon = longitude
        self._sim_altitude = altitude
        LOGGER.info(f"Simulator position set: {latitude}, {longitude}, {altitude}m")
    
    def get_status(self) -> Dict[str, Any]:
        """Get GPS HAT status."""
        return {
            "port": self.port,
            "baudrate": self.baudrate,
            "connected": self.connected,
            "simulator": self.use_simulator,
            "serial_available": SERIAL_AVAILABLE,
            "pynmea2_available": PYNNMEA2_AVAILABLE,
        }


# Global instance
_global_gps_hat: Optional[WaveshareGPSHAT] = None


def get_gps_hat(
    port: Optional[str] = None,
    baudrate: int = 9600,
    use_simulator: bool = False,
    auto_detect: bool = True,
) -> WaveshareGPSHAT:
    """
    Get or create global GPS HAT instance.
    
    Args:
        port: Serial port path (None for auto-detect)
        baudrate: Serial baud rate
        use_simulator: Use simulator instead of hardware
        auto_detect: Automatically detect GPS port
        
    Returns:
        WaveshareGPSHAT instance
    """
    global _global_gps_hat
    
    if _global_gps_hat is None:
        _global_gps_hat = WaveshareGPSHAT(
            port=port,
            baudrate=baudrate,
            use_simulator=use_simulator,
            auto_detect=auto_detect,
        )
    
    return _global_gps_hat


__all__ = [
    "WaveshareGPSHAT",
    "get_gps_hat",
]

