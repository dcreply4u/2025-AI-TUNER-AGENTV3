"""
Vehicle Theft Tracking & Recovery Service

Features:
- Continuous GPS tracking
- Geofencing alerts
- Tamper detection
- Real-time location updates
- Location history
- Mobile app integration
- Fleet management integration
"""

from __future__ import annotations

import logging
import time
import threading
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Callable, Tuple

from interfaces.gps_interface import GPSInterface, GPSFix
from services.geo_logger import GeoLogger
from services.fleet_management import FleetVehicle
from services.connection_manager import (
    ConnectionManager,
    ConnectionPriority,
    ConnectionInfo,
)

LOGGER = logging.getLogger(__name__)


class TrackingMode(str, Enum):
    """Tracking mode."""
    CONTINUOUS = "continuous"  # Always tracking
    ON_DEMAND = "on_demand"  # Track only when requested
    SCHEDULED = "scheduled"  # Track at specific times
    EVENT_BASED = "event_based"  # Track on specific events


class ConnectionType(str, Enum):
    """Connection type for location updates."""
    CELLULAR = "cellular"
    WIFI = "wifi"
    BLUETOOTH = "bluetooth"
    LOCAL_ONLY = "local_only"


@dataclass
class Geofence:
    """Geofence definition."""
    name: str
    center_lat: float
    center_lon: float
    radius_meters: float
    enabled: bool = True
    alert_on_exit: bool = True
    alert_on_enter: bool = False


@dataclass
class LocationUpdate:
    """Location update record."""
    timestamp: float
    latitude: float
    longitude: float
    speed_mps: float
    heading: float
    altitude_m: Optional[float] = None
    connection_type: str = "local"
    uploaded: bool = False


@dataclass
class TheftAlert:
    """Theft alert."""
    alert_type: str  # geofence_violation, unauthorized_movement, tamper, power_loss
    timestamp: float
    location: Tuple[float, float]  # (lat, lon)
    message: str
    severity: str = "high"  # low, medium, high, critical
    acknowledged: bool = False


class TheftTrackingService:
    """Vehicle theft tracking and recovery service."""
    
    def __init__(
        self,
        vehicle_id: str,
        gps_interface: Optional[GPSInterface] = None,
        geo_logger: Optional[GeoLogger] = None,
        update_interval: float = 15.0,  # seconds
        enable_geofencing: bool = True,
        enable_cellular: bool = False,  # Option 1: Cellular GPS
        cellular_port: Optional[str] = None,
        connection_priority: ConnectionPriority = ConnectionPriority.WIFI_FIRST,  # Option 2: WiFi First
    ) -> None:
        """
        Initialize theft tracking service.
        
        Args:
            vehicle_id: Unique vehicle identifier
            gps_interface: GPS interface (auto-initialized if None)
            geo_logger: Geo logger (auto-initialized if None)
            update_interval: GPS update interval in seconds
            enable_geofencing: Enable geofence monitoring
            enable_cellular: Enable cellular modem (Option 1)
            cellular_port: Cellular modem port (auto-detect if None)
            connection_priority: Connection priority (WIFI_FIRST = Option 2, CELLULAR_FIRST = Option 1)
        """
        self.vehicle_id = vehicle_id
        self.update_interval = update_interval
        self.enable_geofencing = enable_geofencing
        
        # GPS interface
        self.gps_interface = gps_interface
        self.gps_available = False
        
        # Geo logger
        if geo_logger is None:
            geo_logger = GeoLogger(f"geo_history_{vehicle_id}.db")
        self.geo_logger = geo_logger
        
        # Connection manager (handles WiFi + Cellular)
        self.connection_manager = ConnectionManager(
            priority=connection_priority,
            enable_cellular=enable_cellular,
            cellular_port=cellular_port,
        )
        
        # Tracking state
        self.tracking_enabled = False
        self.tracking_mode = TrackingMode.CONTINUOUS
        self.tracking_thread: Optional[threading.Thread] = None
        self.stop_tracking = False
        
        # Location data
        self.current_location: Optional[LocationUpdate] = None
        self.location_history: List[LocationUpdate] = []
        self.max_history = 1000
        
        # Geofences
        self.geofences: Dict[str, Geofence] = {}
        self.last_known_location: Optional[Tuple[float, float]] = None
        
        # Alerts
        self.alerts: List[TheftAlert] = []
        self.alert_callbacks: List[Callable[[TheftAlert], None]] = []
        
        # Theft detection
        self.parked_location: Optional[Tuple[float, float]] = None
        self.parked_timestamp: Optional[float] = None
        self.movement_threshold_meters = 50.0  # Alert if moved more than 50m
        self.unauthorized_movement_enabled = True
        
        # Tamper detection
        self.last_gps_fix_time: Optional[float] = None
        self.gps_timeout_seconds = 60.0  # Alert if no GPS for 60 seconds
        self.tamper_detection_enabled = True
        
        # Cloud upload
        self.cloud_upload_enabled = False
        self.cloud_upload_url: Optional[str] = None
        
        # Initialize GPS if not provided
        if self.gps_interface is None:
            self._init_gps()
        
        # Register connection status callback
        self.connection_manager.register_connection_callback(self._on_connection_change)
    
    def _init_gps(self) -> None:
        """Initialize GPS interface."""
        try:
            self.gps_interface = GPSInterface()
            self.gps_available = True
            LOGGER.info("GPS interface initialized")
        except Exception as e:
            LOGGER.warning("Failed to initialize GPS: %s", e)
            self.gps_available = False
    
    def start_tracking(self) -> bool:
        """Start continuous tracking."""
        if self.tracking_enabled:
            return True
        
        if not self.gps_available:
            LOGGER.error("GPS not available - cannot start tracking")
            return False
        
        self.tracking_enabled = True
        self.stop_tracking = False
        
        # Start tracking thread
        self.tracking_thread = threading.Thread(
            target=self._tracking_loop,
            daemon=True,
            name=f"TheftTracking-{self.vehicle_id}",
        )
        self.tracking_thread.start()
        
        LOGGER.info("Theft tracking started for vehicle: %s", self.vehicle_id)
        return True
    
    def stop_tracking_service(self) -> None:
        """Stop tracking service."""
        self.tracking_enabled = False
        self.stop_tracking = True
        
        if self.tracking_thread:
            self.tracking_thread.join(timeout=5.0)
        
        LOGGER.info("Theft tracking stopped for vehicle: %s", self.vehicle_id)
    
    def _tracking_loop(self) -> None:
        """Main tracking loop."""
        while not self.stop_tracking and self.tracking_enabled:
            try:
                # Read GPS fix
                if self.gps_interface:
                    fix = self.gps_interface.read_fix()
                    
                    if fix:
                        self._process_gps_fix(fix)
                        self.last_gps_fix_time = time.time()
                    else:
                        # Check for GPS timeout (tamper detection)
                        if self.tamper_detection_enabled:
                            self._check_gps_timeout()
                
                # Sleep until next update
                time.sleep(self.update_interval)
                
            except Exception as e:
                LOGGER.error("Error in tracking loop: %s", e)
                time.sleep(self.update_interval)
    
    def _process_gps_fix(self, fix: GPSFix) -> None:
        """Process GPS fix and check for alerts."""
        # Get current connection type
        conn_info = self.connection_manager.get_current_connection()
        conn_type = conn_info.connection_type if conn_info else "local"
        
        # Create location update
        location = LocationUpdate(
            timestamp=fix.timestamp,
            latitude=fix.latitude,
            longitude=fix.longitude,
            speed_mps=fix.speed_mps,
            heading=fix.heading,
            altitude_m=fix.altitude_m,
            connection_type=conn_type,
        )
        
        # Update current location
        self.current_location = location
        
        # Add to history
        self.location_history.append(location)
        if len(self.location_history) > self.max_history:
            self.location_history.pop(0)
        
        # Log to geo logger
        self.geo_logger.log(fix.to_payload())
        
        # Check geofences
        if self.enable_geofencing:
            self._check_geofences(fix.latitude, fix.longitude)
        
        # Check unauthorized movement
        if self.unauthorized_movement_enabled:
            self._check_unauthorized_movement(fix.latitude, fix.longitude)
        
        # Upload to cloud if enabled
        if self.cloud_upload_enabled:
            self._upload_location(location)
        
        # Update last known location
        self.last_known_location = (fix.latitude, fix.longitude)
    
    def _check_geofences(self, lat: float, lon: float) -> None:
        """Check if location violates any geofences."""
        import math
        
        for name, geofence in self.geofences.items():
            if not geofence.enabled:
                continue
            
            # Calculate distance from center
            distance = self._calculate_distance(
                lat, lon,
                geofence.center_lat, geofence.center_lon
            )
            
            # Check if outside geofence
            if distance > geofence.radius_meters:
                if geofence.alert_on_exit:
                    self._create_alert(
                        "geofence_violation",
                        (lat, lon),
                        f"Vehicle left geofence: {name}",
                        "high"
                    )
            else:
                if geofence.alert_on_enter:
                    self._create_alert(
                        "geofence_enter",
                        (lat, lon),
                        f"Vehicle entered geofence: {name}",
                        "medium"
                    )
    
    def _check_unauthorized_movement(self, lat: float, lon: float) -> None:
        """Check for unauthorized movement when vehicle should be parked."""
        if self.parked_location is None:
            # Vehicle is not marked as parked
            return
        
        # Calculate distance from parked location
        distance = self._calculate_distance(
            lat, lon,
            self.parked_location[0], self.parked_location[1]
        )
        
        # Check if moved beyond threshold
        if distance > self.movement_threshold_meters:
            self._create_alert(
                "unauthorized_movement",
                (lat, lon),
                f"Vehicle moved {distance:.0f}m from parked location",
                "critical"
            )
    
    def _check_gps_timeout(self) -> None:
        """Check if GPS has timed out (possible tampering)."""
        if self.last_gps_fix_time is None:
            return
        
        time_since_fix = time.time() - self.last_gps_fix_time
        
        if time_since_fix > self.gps_timeout_seconds:
            self._create_alert(
                "tamper",
                self.last_known_location or (0.0, 0.0),
                f"GPS signal lost for {time_since_fix:.0f} seconds - possible tampering",
                "high"
            )
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in meters (Haversine formula)."""
        import math
        
        R = 6371000  # Earth radius in meters
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_phi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _create_alert(self, alert_type: str, location: Tuple[float, float],
                     message: str, severity: str = "high") -> None:
        """Create and dispatch theft alert."""
        alert = TheftAlert(
            alert_type=alert_type,
            timestamp=time.time(),
            location=location,
            message=message,
            severity=severity,
        )
        
        # Add to alerts list
        self.alerts.append(alert)
        if len(self.alerts) > 100:
            self.alerts.pop(0)
        
        # Call registered callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                LOGGER.error("Error in alert callback: %s", e)
        
        LOGGER.warning("Theft alert: %s - %s", alert_type, message)
    
    def _upload_location(self, location: LocationUpdate) -> None:
        """Upload location to cloud API using connection manager."""
        if not self.cloud_upload_url:
            return
        
        payload = {
            "vehicle_id": self.vehicle_id,
            "timestamp": location.timestamp,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "speed_mps": location.speed_mps,
            "heading": location.heading,
            "altitude_m": location.altitude_m,
            "connection_type": location.connection_type,
        }
        
        # Use connection manager to upload (handles WiFi/Cellular automatically)
        success = self.connection_manager.upload_location(self.cloud_upload_url, payload)
        
        if success:
            location.uploaded = True
            LOGGER.debug("Location uploaded via %s", location.connection_type)
        else:
            LOGGER.debug("Location queued for upload (connection unavailable)")
    
    def _on_connection_change(self, conn_info: ConnectionInfo) -> None:
        """Handle connection status change."""
        LOGGER.info("Connection changed: %s (%s)", conn_info.connection_type, conn_info.status)
        
        # If connection lost, create alert
        if conn_info.status == ConnectionStatus.DISCONNECTED:
            if self.last_known_location:
                self._create_alert(
                    "connection_lost",
                    self.last_known_location,
                    f"Connection lost: {conn_info.connection_type}",
                    "medium"
                )
    
    def add_geofence(self, geofence: Geofence) -> None:
        """Add geofence."""
        self.geofences[geofence.name] = geofence
        LOGGER.info("Added geofence: %s", geofence.name)
    
    def remove_geofence(self, name: str) -> None:
        """Remove geofence."""
        if name in self.geofences:
            del self.geofences[name]
            LOGGER.info("Removed geofence: %s", name)
    
    def mark_parked(self, lat: float, lon: float) -> None:
        """Mark vehicle as parked at location."""
        self.parked_location = (lat, lon)
        self.parked_timestamp = time.time()
        LOGGER.info("Vehicle marked as parked at: %.6f, %.6f", lat, lon)
    
    def mark_unparked(self) -> None:
        """Mark vehicle as no longer parked."""
        self.parked_location = None
        self.parked_timestamp = None
        LOGGER.info("Vehicle marked as unparked")
    
    def get_current_location(self) -> Optional[LocationUpdate]:
        """Get current location."""
        return self.current_location
    
    def get_location_history(self, start_time: Optional[float] = None,
                            end_time: Optional[float] = None) -> List[LocationUpdate]:
        """Get location history."""
        if not start_time and not end_time:
            return self.location_history.copy()
        
        filtered = []
        for location in self.location_history:
            if start_time and location.timestamp < start_time:
                continue
            if end_time and location.timestamp > end_time:
                continue
            filtered.append(location)
        
        return filtered
    
    def get_recent_alerts(self, limit: int = 10) -> List[TheftAlert]:
        """Get recent alerts."""
        return self.alerts[-limit:] if len(self.alerts) > limit else self.alerts.copy()
    
    def register_alert_callback(self, callback: Callable[[TheftAlert], None]) -> None:
        """Register callback for theft alerts."""
        self.alert_callbacks.append(callback)
    
    def enable_cloud_upload(self, upload_url: str) -> None:
        """Enable cloud location upload."""
        self.cloud_upload_enabled = True
        self.cloud_upload_url = upload_url
        LOGGER.info("Cloud upload enabled: %s", upload_url)
    
    def disable_cloud_upload(self) -> None:
        """Disable cloud location upload."""
        self.cloud_upload_enabled = False
        self.cloud_upload_url = None
    
    def upgrade_to_cellular(self, cellular_port: Optional[str] = None) -> bool:
        """
        Upgrade to cellular tracking (Option 1).
        
        Args:
            cellular_port: Cellular modem port (auto-detect if None)
            
        Returns:
            True if cellular modem successfully enabled
        """
        success = self.connection_manager.enable_cellular_tracking(cellular_port)
        if success:
            # Switch to cellular-first priority
            self.connection_manager.priority = ConnectionPriority.CELLULAR_FIRST
            self.connection_manager._select_connection()
            LOGGER.info("Upgraded to cellular tracking (Option 1)")
        else:
            LOGGER.warning("Failed to enable cellular tracking - falling back to WiFi")
        return success
    
    def downgrade_to_wifi(self) -> None:
        """Downgrade to WiFi-only tracking (Option 2)."""
        self.connection_manager.disable_cellular_tracking()
        self.connection_manager.priority = ConnectionPriority.WIFI_FIRST
        self.connection_manager._select_connection()
        LOGGER.info("Downgraded to WiFi tracking (Option 2)")
    
    def get_connection_status(self) -> Optional[ConnectionInfo]:
        """Get current connection status."""
        return self.connection_manager.get_current_connection()
    
    def is_cellular_available(self) -> bool:
        """Check if cellular modem is available."""
        return self.connection_manager.cellular_available
    
    def is_wifi_available(self) -> bool:
        """Check if WiFi is available."""
        return self.connection_manager.wifi_connected


__all__ = [
    "TheftTrackingService",
    "TrackingMode",
    "ConnectionType",
    "Geofence",
    "LocationUpdate",
    "TheftAlert",
]

