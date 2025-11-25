"""
Fleet Theft Tracking Integration

Integrates theft tracking with fleet management platform.
"""

from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional

from services.theft_tracking_service import TheftTrackingService, TheftAlert
from services.fleet_management import FleetManagement, FleetVehicle

LOGGER = logging.getLogger(__name__)


class FleetTheftTracking:
    """Fleet-wide theft tracking integration."""
    
    def __init__(self, fleet_manager: FleetManagement) -> None:
        """
        Initialize fleet theft tracking.
        
        Args:
            fleet_manager: Fleet management instance
        """
        self.fleet_manager = fleet_manager
        self.tracking_services: Dict[str, TheftTrackingService] = {}
        
        # Register alert callback for all vehicles
        self._setup_alert_handling()
    
    def register_vehicle(self, vehicle_id: str, tracking_service: TheftTrackingService) -> None:
        """Register vehicle for theft tracking."""
        self.tracking_services[vehicle_id] = tracking_service
        
        # Register alert callback
        tracking_service.register_alert_callback(
            lambda alert: self._handle_theft_alert(vehicle_id, alert)
        )
        
        # Update fleet vehicle with tracking status
        vehicle = self.fleet_manager.get_vehicle(vehicle_id)
        if vehicle:
            vehicle.custom_metadata["theft_tracking_enabled"] = True
            self.fleet_manager.update_vehicle(vehicle)
        
        LOGGER.info("Registered vehicle for theft tracking: %s", vehicle_id)
    
    def unregister_vehicle(self, vehicle_id: str) -> None:
        """Unregister vehicle from theft tracking."""
        if vehicle_id in self.tracking_services:
            del self.tracking_services[vehicle_id]
        
        # Update fleet vehicle
        vehicle = self.fleet_manager.get_vehicle(vehicle_id)
        if vehicle:
            vehicle.custom_metadata["theft_tracking_enabled"] = False
            self.fleet_manager.update_vehicle(vehicle)
        
        LOGGER.info("Unregistered vehicle from theft tracking: %s", vehicle_id)
    
    def start_tracking_all(self) -> Dict[str, bool]:
        """Start tracking for all registered vehicles."""
        results = {}
        for vehicle_id, service in self.tracking_services.items():
            results[vehicle_id] = service.start_tracking()
        return results
    
    def stop_tracking_all(self) -> None:
        """Stop tracking for all vehicles."""
        for service in self.tracking_services.values():
            service.stop_tracking_service()
    
    def get_all_locations(self) -> Dict[str, Optional[Dict]]:
        """Get current locations for all tracked vehicles."""
        locations = {}
        for vehicle_id, service in self.tracking_services.items():
            location = service.get_current_location()
            if location:
                locations[vehicle_id] = {
                    "timestamp": location.timestamp,
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "speed_mps": location.speed_mps,
                    "heading": location.heading,
                    "altitude_m": location.altitude_m,
                    "connection_type": location.connection_type,
                }
            else:
                locations[vehicle_id] = None
        return locations
    
    def get_all_alerts(self, limit_per_vehicle: int = 10) -> Dict[str, List[Dict]]:
        """Get recent alerts for all vehicles."""
        all_alerts = {}
        for vehicle_id, service in self.tracking_services.items():
            alerts = service.get_recent_alerts(limit_per_vehicle)
            all_alerts[vehicle_id] = [
                {
                    "alert_type": alert.alert_type,
                    "timestamp": alert.timestamp,
                    "latitude": alert.location[0],
                    "longitude": alert.location[1],
                    "message": alert.message,
                    "severity": alert.severity,
                    "acknowledged": alert.acknowledged,
                }
                for alert in alerts
            ]
        return all_alerts
    
    def get_vehicles_in_alert(self) -> List[str]:
        """Get list of vehicles with unacknowledged alerts."""
        vehicles_in_alert = []
        for vehicle_id, service in self.tracking_services.items():
            alerts = service.get_recent_alerts(limit=1)
            if alerts and not alerts[0].acknowledged:
                vehicles_in_alert.append(vehicle_id)
        return vehicles_in_alert
    
    def _setup_alert_handling(self) -> None:
        """Setup alert handling for fleet."""
        # This would integrate with notification systems, etc.
        pass
    
    def _handle_theft_alert(self, vehicle_id: str, alert: TheftAlert) -> None:
        """Handle theft alert from vehicle."""
        LOGGER.critical(
            "THEFT ALERT - Vehicle: %s, Type: %s, Location: %.6f, %.6f, Message: %s",
            vehicle_id,
            alert.alert_type,
            alert.location[0],
            alert.location[1],
            alert.message,
        )
        
        # Update fleet vehicle status
        vehicle = self.fleet_manager.get_vehicle(vehicle_id)
        if vehicle:
            vehicle.status = "alert"
            vehicle.location = alert.location
            vehicle.custom_metadata["last_alert"] = {
                "type": alert.alert_type,
                "timestamp": alert.timestamp,
                "message": alert.message,
                "severity": alert.severity,
            }
            self.fleet_manager.update_vehicle(vehicle)
        
        # Here you would:
        # - Send push notification to mobile app
        # - Send email/SMS alert
        # - Log to security system
        # - Notify law enforcement (if configured)
    
    def set_geofence_for_vehicle(self, vehicle_id: str, geofence_name: str,
                                 center_lat: float, center_lon: float,
                                 radius_meters: float) -> bool:
        """Set geofence for vehicle."""
        if vehicle_id not in self.tracking_services:
            return False
        
        from services.theft_tracking_service import Geofence
        
        geofence = Geofence(
            name=geofence_name,
            center_lat=center_lat,
            center_lon=center_lon,
            radius_meters=radius_meters,
        )
        
        self.tracking_services[vehicle_id].add_geofence(geofence)
        return True
    
    def mark_vehicle_parked(self, vehicle_id: str, lat: float, lon: float) -> bool:
        """Mark vehicle as parked."""
        if vehicle_id not in self.tracking_services:
            return False
        
        self.tracking_services[vehicle_id].mark_parked(lat, lon)
        return True
    
    def mark_vehicle_unparked(self, vehicle_id: str) -> bool:
        """Mark vehicle as unparked."""
        if vehicle_id not in self.tracking_services:
            return False
        
        self.tracking_services[vehicle_id].mark_unparked()
        return True


__all__ = ["FleetTheftTracking"]






