"""
Connection Manager for Theft Tracking

Manages multiple connection types (WiFi, Cellular) with automatic failover.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable, Dict, List

from interfaces.cellular_modem_interface import CellularModem, CellularModemDetector

LOGGER = logging.getLogger(__name__)


class ConnectionPriority(str, Enum):
    """Connection priority."""
    CELLULAR_FIRST = "cellular_first"  # Try cellular first, fallback to WiFi
    WIFI_FIRST = "wifi_first"  # Try WiFi first, fallback to cellular
    CELLULAR_ONLY = "cellular_only"  # Only use cellular
    WIFI_ONLY = "wifi_only"  # Only use WiFi


class ConnectionStatus(str, Enum):
    """Connection status."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ERROR = "error"


@dataclass
class ConnectionInfo:
    """Connection information."""
    connection_type: str  # "cellular", "wifi", "local"
    status: ConnectionStatus
    signal_strength: Optional[int] = None
    last_success: Optional[float] = None
    last_failure: Optional[float] = None
    error_count: int = 0


class ConnectionManager:
    """Manages connections for theft tracking."""
    
    def __init__(
        self,
        priority: ConnectionPriority = ConnectionPriority.WIFI_FIRST,
        enable_cellular: bool = False,
        cellular_port: Optional[str] = None,
    ) -> None:
        """
        Initialize connection manager.
        
        Args:
            priority: Connection priority strategy
            enable_cellular: Enable cellular modem (if available)
            cellular_port: Cellular modem port (auto-detect if None)
        """
        self.priority = priority
        self.enable_cellular = enable_cellular
        
        # Cellular modem
        self.cellular_modem: Optional[CellularModem] = None
        self.cellular_available = False
        
        # WiFi status
        self.wifi_available = False
        self.wifi_connected = False
        
        # Current connection
        self.current_connection: Optional[ConnectionInfo] = None
        self.connection_callbacks: List[Callable[[ConnectionInfo], None]] = []
        
        # Initialize connections
        self._initialize_connections(cellular_port)
    
    def _initialize_connections(self, cellular_port: Optional[str] = None) -> None:
        """Initialize available connections."""
        # Check WiFi
        self._check_wifi()
        
        # Check Cellular (if enabled)
        if self.enable_cellular:
            self._initialize_cellular(cellular_port)
        
        # Select best connection
        self._select_connection()
    
    def _check_wifi(self) -> None:
        """Check WiFi availability."""
        try:
            import subprocess
            
            # Check WiFi connection (Linux)
            result = subprocess.run(
                ["nmcli", "-t", "-f", "STATE", "device", "status"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            
            if result.returncode == 0:
                # Check if any WiFi device is connected
                for line in result.stdout.split("\n"):
                    if "wifi" in line.lower() and "connected" in line.lower():
                        self.wifi_available = True
                        self.wifi_connected = True
                        return
                
                # WiFi available but not connected
                self.wifi_available = True
                self.wifi_connected = False
            else:
                # Try alternative method
                import socket
                try:
                    socket.create_connection(("8.8.8.8", 53), timeout=2)
                    self.wifi_available = True
                    self.wifi_connected = True
                except OSError:
                    self.wifi_available = False
                    self.wifi_connected = False
        except Exception as e:
            LOGGER.warning("Failed to check WiFi: %s", e)
            self.wifi_available = False
            self.wifi_connected = False
    
    def _initialize_cellular(self, port: Optional[str] = None) -> None:
        """Initialize cellular modem."""
        if port:
            # Use specified port
            ports_to_try = [port]
        else:
            # Auto-detect
            modems = CellularModemDetector.detect_modems()
            ports_to_try = [m["port"] for m in modems]
        
        for port_to_try in ports_to_try:
            try:
                modem = CellularModem(port=port_to_try)
                if modem.connect():
                    if modem.is_available():
                        self.cellular_modem = modem
                        self.cellular_available = True
                        LOGGER.info("Cellular modem initialized: %s", port_to_try)
                        return
                    else:
                        modem.disconnect()
            except Exception as e:
                LOGGER.warning("Failed to initialize cellular modem on %s: %s", port_to_try, e)
        
        LOGGER.info("Cellular modem not available")
    
    def _select_connection(self) -> None:
        """Select best available connection based on priority."""
        if self.priority == ConnectionPriority.CELLULAR_ONLY:
            if self.cellular_available:
                self.current_connection = ConnectionInfo(
                    connection_type="cellular",
                    status=ConnectionStatus.CONNECTED,
                    signal_strength=self.cellular_modem.signal_strength if self.cellular_modem else None,
                )
            else:
                self.current_connection = ConnectionInfo(
                    connection_type="none",
                    status=ConnectionStatus.DISCONNECTED,
                )
        
        elif self.priority == ConnectionPriority.WIFI_ONLY:
            if self.wifi_connected:
                self.current_connection = ConnectionInfo(
                    connection_type="wifi",
                    status=ConnectionStatus.CONNECTED,
                )
            else:
                self.current_connection = ConnectionInfo(
                    connection_type="none",
                    status=ConnectionStatus.DISCONNECTED,
                )
        
        elif self.priority == ConnectionPriority.CELLULAR_FIRST:
            if self.cellular_available:
                self.current_connection = ConnectionInfo(
                    connection_type="cellular",
                    status=ConnectionStatus.CONNECTED,
                    signal_strength=self.cellular_modem.signal_strength if self.cellular_modem else None,
                )
            elif self.wifi_connected:
                self.current_connection = ConnectionInfo(
                    connection_type="wifi",
                    status=ConnectionStatus.CONNECTED,
                )
            else:
                self.current_connection = ConnectionInfo(
                    connection_type="local",
                    status=ConnectionStatus.DISCONNECTED,
                )
        
        else:  # WIFI_FIRST (default)
            if self.wifi_connected:
                self.current_connection = ConnectionInfo(
                    connection_type="wifi",
                    status=ConnectionStatus.CONNECTED,
                )
            elif self.cellular_available:
                self.current_connection = ConnectionInfo(
                    connection_type="cellular",
                    status=ConnectionStatus.CONNECTED,
                    signal_strength=self.cellular_modem.signal_strength if self.cellular_modem else None,
                )
            else:
                self.current_connection = ConnectionInfo(
                    connection_type="local",
                    status=ConnectionStatus.DISCONNECTED,
                )
        
        # Notify callbacks
        if self.current_connection:
            for callback in self.connection_callbacks:
                try:
                    callback(self.current_connection)
                except Exception as e:
                    LOGGER.error("Error in connection callback: %s", e)
    
    def get_current_connection(self) -> Optional[ConnectionInfo]:
        """Get current connection information."""
        # Refresh connection status
        self._check_wifi()
        if self.cellular_modem:
            self.cellular_modem._check_network_status()
        
        # Re-select connection
        self._select_connection()
        
        return self.current_connection
    
    def upload_location(self, url: str, data: Dict) -> bool:
        """
        Upload location data using current connection.
        
        Args:
            url: Upload URL
            data: Location data dictionary
            
        Returns:
            True if successful
        """
        if not self.current_connection:
            return False
        
        if self.current_connection.connection_type == "cellular" and self.cellular_modem:
            # Use cellular modem
            response = self.cellular_modem.send_data(url, data)
            if response:
                self.current_connection.last_success = time.time()
                self.current_connection.error_count = 0
                return True
            else:
                self.current_connection.last_failure = time.time()
                self.current_connection.error_count += 1
                # Try failover
                if self.priority != ConnectionPriority.CELLULAR_ONLY:
                    self._try_failover()
                return False
        
        elif self.current_connection.connection_type == "wifi":
            # Use WiFi (HTTP request)
            try:
                import requests
                response = requests.post(url, json=data, timeout=5)
                if response.status_code == 200:
                    self.current_connection.last_success = time.time()
                    self.current_connection.error_count = 0
                    return True
                else:
                    self.current_connection.last_failure = time.time()
                    self.current_connection.error_count += 1
                    # Try failover
                    if self.priority != ConnectionPriority.WIFI_ONLY:
                        self._try_failover()
                    return False
            except Exception as e:
                LOGGER.warning("WiFi upload failed: %s", e)
                self.current_connection.last_failure = time.time()
                self.current_connection.error_count += 1
                # Try failover
                if self.priority != ConnectionPriority.WIFI_ONLY:
                    self._try_failover()
                return False
        
        else:
            # Local only - store for later upload
            return False
    
    def _try_failover(self) -> None:
        """Try to failover to alternative connection."""
        if self.current_connection.connection_type == "wifi":
            # Try cellular
            if self.cellular_available:
                LOGGER.info("Failing over from WiFi to Cellular")
                self.priority = ConnectionPriority.CELLULAR_FIRST
                self._select_connection()
        elif self.current_connection.connection_type == "cellular":
            # Try WiFi
            if self.wifi_connected:
                LOGGER.info("Failing over from Cellular to WiFi")
                self.priority = ConnectionPriority.WIFI_FIRST
                self._select_connection()
    
    def register_connection_callback(self, callback: Callable[[ConnectionInfo], None]) -> None:
        """Register callback for connection status changes."""
        self.connection_callbacks.append(callback)
    
    def enable_cellular_tracking(self, port: Optional[str] = None) -> bool:
        """Enable cellular tracking (upgrade from WiFi to Hybrid)."""
        if not self.enable_cellular:
            self.enable_cellular = True
            self._initialize_cellular(port)
            self._select_connection()
            return self.cellular_available
        return True
    
    def disable_cellular_tracking(self) -> None:
        """Disable cellular tracking (downgrade to WiFi only)."""
        if self.cellular_modem:
            self.cellular_modem.disconnect()
            self.cellular_modem = None
        self.enable_cellular = False
        self.cellular_available = False
        self._select_connection()


__all__ = [
    "ConnectionManager",
    "ConnectionPriority",
    "ConnectionStatus",
    "ConnectionInfo",
]

