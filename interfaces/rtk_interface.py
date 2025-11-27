"""
RTK/DGPS Interface
Supports RTK (Real-Time Kinematic) and DGPS (Differential GPS) corrections.
Based on VBOX 3i RTK/DGPS specifications.
"""

from __future__ import annotations

import logging
import socket
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional

LOGGER = logging.getLogger(__name__)


class DGPSMode(Enum):
    """DGPS/RTK correction modes."""
    NONE = "none"  # Standard GPS, no corrections
    RTCM_V3 = "rtcm_v3"  # RTCM v3 (2cm RTK) - RECOMMENDED
    CMR = "cmr"  # CMR (2cm RTK) - Trimble standard
    NTRIP = "ntrip"  # NTRIP (2cm RTK) - Internet-based
    RTCM_V2 = "rtcm_v2"  # RTCM v2 (40cm DGPS) - Local base station
    SBAS = "sbas"  # SBAS (40cm DGPS) - Satellite-based
    MB_BASE = "mb_base"  # Moving Base - Base station
    MB_ROVER = "mb_rover"  # Moving Base - Rover vehicle


class SolutionType(Enum):
    """GPS solution type."""
    NONE = 0  # No solution
    GNSS_ONLY = 1  # GNSS only (standard GPS)
    GNSS_DGPS = 2  # GNSS with DGPS corrections
    RTK_FLOAT = 3  # RTK Float solution
    RTK_FIXED = 4  # RTK Fixed solution (2cm accuracy)
    FIXED_POSITION = 5  # Fixed position mode
    IMU_COAST = 6  # IMU coasting (GPS lost, using IMU)


@dataclass
class RTKStatus:
    """RTK/DGPS status information."""
    mode: DGPSMode
    solution_type: SolutionType
    differential_age: Optional[float] = None  # Age of differential corrections in seconds
    is_locked: bool = False
    position_quality: Optional[float] = None  # Position quality metric
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        """Initialize timestamp."""
        if self.timestamp == 0.0:
            self.timestamp = time.time()

    def to_payload(self) -> dict:
        """Convert to payload dictionary."""
        return {
            "mode": self.mode.value,
            "solution_type": self.solution_type.value,
            "differential_age": self.differential_age,
            "is_locked": self.is_locked,
            "position_quality": self.position_quality,
            "timestamp": self.timestamp,
        }


class NTRIPClient:
    """
    NTRIP (Networked Transport of RTCM via Internet Protocol) client.
    Connects to NTRIP caster to receive RTCM corrections.
    """

    def __init__(
        self,
        host: str,
        port: int,
        mountpoint: str,
        username: str = "",
        password: str = "",
    ) -> None:
        """
        Initialize NTRIP client.
        
        Args:
            host: NTRIP caster hostname
            port: NTRIP caster port (typically 2101)
            mountpoint: NTRIP mountpoint name
            username: NTRIP username (optional)
            password: NTRIP password (optional)
        """
        self.host = host
        self.port = port
        self.mountpoint = mountpoint
        self.username = username
        self.password = password
        self.socket: Optional[socket.socket] = None
        self.connected = False

    def connect(self) -> bool:
        """Connect to NTRIP caster."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10.0)
            self.socket.connect((self.host, self.port))

            # Send NTRIP request
            request = f"GET /{self.mountpoint} HTTP/1.0\r\n"
            request += f"User-Agent: AI-Tuner-Agent/1.0\r\n"
            if self.username and self.password:
                import base64
                auth = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
                request += f"Authorization: Basic {auth}\r\n"
            request += "\r\n"

            self.socket.send(request.encode())

            # Read response
            response = self.socket.recv(1024).decode()
            if "200 OK" in response or "ICY 200 OK" in response:
                self.connected = True
                LOGGER.info(f"NTRIP connected to {self.host}:{self.port}/{self.mountpoint}")
                return True
            else:
                LOGGER.error(f"NTRIP connection failed: {response}")
                self.socket.close()
                self.socket = None
                return False

        except Exception as e:
            LOGGER.error(f"NTRIP connection error: {e}")
            if self.socket:
                self.socket.close()
                self.socket = None
            return False

    def read_rtcm(self, timeout: float = 1.0) -> Optional[bytes]:
        """
        Read RTCM correction data from NTRIP stream.
        
        Args:
            timeout: Read timeout in seconds
            
        Returns:
            RTCM message bytes or None
        """
        if not self.connected or not self.socket:
            return None

        try:
            self.socket.settimeout(timeout)
            data = self.socket.recv(4096)
            if data:
                return data
            return None
        except socket.timeout:
            return None
        except Exception as e:
            LOGGER.error(f"NTRIP read error: {e}")
            self.connected = False
            return None

    def disconnect(self) -> None:
        """Disconnect from NTRIP caster."""
        if self.socket:
            self.socket.close()
            self.socket = None
        self.connected = False
        LOGGER.info("NTRIP disconnected")


class RTKInterface:
    """
    RTK/DGPS interface for receiving and processing correction data.
    
    Supports:
    - NTRIP (Internet-based RTK)
    - Base station radio link (RTCM v2/v3)
    - SBAS (Satellite-based augmentation)
    """

    def __init__(
        self,
        mode: DGPSMode = DGPSMode.NONE,
        serial_port: Optional[str] = None,
        baudrate: int = 115200,
    ) -> None:
        """
        Initialize RTK/DGPS interface.
        
        Args:
            mode: DGPS/RTK mode
            serial_port: Serial port for base station radio (if using radio link)
            baudrate: Serial baud rate
        """
        self.mode = mode
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.ntrip_client: Optional[NTRIPClient] = None
        self.status = RTKStatus(mode=mode, solution_type=SolutionType.GNSS_ONLY)

    def configure_ntrip(
        self,
        host: str,
        port: int,
        mountpoint: str,
        username: str = "",
        password: str = "",
    ) -> bool:
        """
        Configure NTRIP connection.
        
        Args:
            host: NTRIP caster hostname
            port: NTRIP caster port
            mountpoint: NTRIP mountpoint
            username: NTRIP username
            password: NTRIP password
            
        Returns:
            True if configuration successful
        """
        if self.mode != DGPSMode.NTRIP:
            LOGGER.warning("NTRIP configured but mode is not NTRIP")
            return False

        self.ntrip_client = NTRIPClient(host, port, mountpoint, username, password)
        return True

    def connect(self) -> bool:
        """Connect to RTK/DGPS correction source."""
        if self.mode == DGPSMode.NONE:
            return True  # No connection needed

        if self.mode == DGPSMode.NTRIP:
            if self.ntrip_client:
                return self.ntrip_client.connect()
            else:
                LOGGER.error("NTRIP client not configured")
                return False

        # For base station radio link, serial port should be handled by GPS interface
        if self.mode in (DGPSMode.RTCM_V2, DGPSMode.RTCM_V3, DGPSMode.CMR):
            if self.serial_port:
                LOGGER.info(f"RTK mode {self.mode.value} - using serial port {self.serial_port}")
                return True
            else:
                LOGGER.warning(f"RTK mode {self.mode.value} requires serial port")
                return False

        if self.mode == DGPSMode.SBAS:
            LOGGER.info("SBAS mode - corrections from satellite")
            return True

        return False

    def read_corrections(self) -> Optional[bytes]:
        """
        Read RTCM correction data.
        
        Returns:
            RTCM message bytes or None
        """
        if self.mode == DGPSMode.NTRIP and self.ntrip_client:
            return self.ntrip_client.read_rtcm()

        # For serial-based corrections, this should be handled by GPS interface
        return None

    def update_status(
        self,
        solution_type: SolutionType,
        differential_age: Optional[float] = None,
        position_quality: Optional[float] = None,
    ) -> None:
        """
        Update RTK/DGPS status.
        
        Args:
            solution_type: Current solution type
            differential_age: Age of differential corrections
            position_quality: Position quality metric
        """
        self.status.solution_type = solution_type
        self.status.differential_age = differential_age
        self.status.position_quality = position_quality
        self.status.is_locked = solution_type in (SolutionType.RTK_FIXED, SolutionType.GNSS_DGPS)
        self.status.timestamp = time.time()

    def disconnect(self) -> None:
        """Disconnect from RTK/DGPS correction source."""
        if self.ntrip_client:
            self.ntrip_client.disconnect()

    def get_status(self) -> RTKStatus:
        """Get current RTK/DGPS status."""
        return self.status


__all__ = [
    "RTKInterface",
    "NTRIPClient",
    "DGPSMode",
    "SolutionType",
    "RTKStatus",
]


