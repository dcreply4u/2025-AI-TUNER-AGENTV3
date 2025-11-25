"""
Theft Tracking API Endpoints

REST API for mobile app and fleet management platform integration.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from services.theft_tracking_service import (
    TheftTrackingService,
    LocationUpdate,
    TheftAlert,
    Geofence,
)

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/api/theft-tracking", tags=["theft-tracking"])


# Pydantic models for API
class LocationResponse(BaseModel):
    """Location response model."""
    vehicle_id: str
    timestamp: float
    latitude: float
    longitude: float
    speed_mps: float
    heading: float
    altitude_m: Optional[float] = None
    connection_type: str


class AlertResponse(BaseModel):
    """Alert response model."""
    alert_type: str
    timestamp: float
    latitude: float
    longitude: float
    message: str
    severity: str
    acknowledged: bool


class GeofenceRequest(BaseModel):
    """Geofence request model."""
    name: str
    center_lat: float
    center_lon: float
    radius_meters: float
    enabled: bool = True
    alert_on_exit: bool = True
    alert_on_enter: bool = False


class GeofenceResponse(BaseModel):
    """Geofence response model."""
    name: str
    center_lat: float
    center_lon: float
    radius_meters: float
    enabled: bool
    alert_on_exit: bool
    alert_on_enter: bool


# Global tracking services (in production, use dependency injection)
_tracking_services: Dict[str, TheftTrackingService] = {}


def get_tracking_service(vehicle_id: str) -> Optional[TheftTrackingService]:
    """Get tracking service for vehicle."""
    return _tracking_services.get(vehicle_id)


@router.get("/vehicles/{vehicle_id}/location", response_model=LocationResponse)
async def get_current_location(vehicle_id: str):
    """Get current vehicle location."""
    service = get_tracking_service(vehicle_id)
    if not service:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    location = service.get_current_location()
    if not location:
        raise HTTPException(status_code=404, detail="Location not available")
    
    return LocationResponse(
        vehicle_id=vehicle_id,
        timestamp=location.timestamp,
        latitude=location.latitude,
        longitude=location.longitude,
        speed_mps=location.speed_mps,
        heading=location.heading,
        altitude_m=location.altitude_m,
        connection_type=location.connection_type,
    )


@router.get("/vehicles/{vehicle_id}/location/history")
async def get_location_history(
    vehicle_id: str,
    start_time: Optional[float] = Query(None),
    end_time: Optional[float] = Query(None),
    limit: int = Query(100, le=1000),
):
    """Get location history."""
    service = get_tracking_service(vehicle_id)
    if not service:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    history = service.get_location_history(start_time, end_time)
    
    # Limit results
    if len(history) > limit:
        history = history[-limit:]
    
    return [
        {
            "timestamp": loc.timestamp,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "speed_mps": loc.speed_mps,
            "heading": loc.heading,
            "altitude_m": loc.altitude_m,
            "connection_type": loc.connection_type,
        }
        for loc in history
    ]


@router.get("/vehicles/{vehicle_id}/alerts", response_model=List[AlertResponse])
async def get_alerts(vehicle_id: str, limit: int = Query(10, le=100)):
    """Get recent theft alerts."""
    service = get_tracking_service(vehicle_id)
    if not service:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    alerts = service.get_recent_alerts(limit)
    
    return [
        AlertResponse(
            alert_type=alert.alert_type,
            timestamp=alert.timestamp,
            latitude=alert.location[0],
            longitude=alert.location[1],
            message=alert.message,
            severity=alert.severity,
            acknowledged=alert.acknowledged,
        )
        for alert in alerts
    ]


@router.post("/vehicles/{vehicle_id}/geofences", response_model=GeofenceResponse)
async def add_geofence(vehicle_id: str, geofence: GeofenceRequest):
    """Add geofence for vehicle."""
    service = get_tracking_service(vehicle_id)
    if not service:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    gf = Geofence(
        name=geofence.name,
        center_lat=geofence.center_lat,
        center_lon=geofence.center_lon,
        radius_meters=geofence.radius_meters,
        enabled=geofence.enabled,
        alert_on_exit=geofence.alert_on_exit,
        alert_on_enter=geofence.alert_on_enter,
    )
    
    service.add_geofence(gf)
    
    return GeofenceResponse(
        name=gf.name,
        center_lat=gf.center_lat,
        center_lon=gf.center_lon,
        radius_meters=gf.radius_meters,
        enabled=gf.enabled,
        alert_on_exit=gf.alert_on_exit,
        alert_on_enter=gf.alert_on_enter,
    )


@router.delete("/vehicles/{vehicle_id}/geofences/{geofence_name}")
async def remove_geofence(vehicle_id: str, geofence_name: str):
    """Remove geofence."""
    service = get_tracking_service(vehicle_id)
    if not service:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    service.remove_geofence(geofence_name)
    return {"status": "deleted"}


@router.post("/vehicles/{vehicle_id}/park")
async def mark_parked(vehicle_id: str, lat: float, lon: float):
    """Mark vehicle as parked."""
    service = get_tracking_service(vehicle_id)
    if not service:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    service.mark_parked(lat, lon)
    return {"status": "parked", "location": {"lat": lat, "lon": lon}}


@router.post("/vehicles/{vehicle_id}/unpark")
async def mark_unparked(vehicle_id: str):
    """Mark vehicle as unparked."""
    service = get_tracking_service(vehicle_id)
    if not service:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    service.mark_unparked()
    return {"status": "unparked"}


@router.post("/vehicles/{vehicle_id}/tracking/start")
async def start_tracking(vehicle_id: str):
    """Start tracking for vehicle."""
    service = get_tracking_service(vehicle_id)
    if not service:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    success = service.start_tracking()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to start tracking")
    
    return {"status": "started"}


@router.post("/vehicles/{vehicle_id}/tracking/stop")
async def stop_tracking(vehicle_id: str):
    """Stop tracking for vehicle."""
    service = get_tracking_service(vehicle_id)
    if not service:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    service.stop_tracking_service()
    return {"status": "stopped"}


@router.post("/vehicles/{vehicle_id}/upgrade/cellular")
async def upgrade_to_cellular(
    vehicle_id: str,
    cellular_port: Optional[str] = Query(None, description="Cellular modem port (auto-detect if not provided)")
):
    """Upgrade to cellular tracking (Option 1)."""
    service = get_tracking_service(vehicle_id)
    if not service:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    success = service.upgrade_to_cellular(cellular_port)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to enable cellular tracking")
    
    return {
        "status": "upgraded",
        "tracking_type": "cellular",
        "cellular_available": service.is_cellular_available(),
    }


@router.post("/vehicles/{vehicle_id}/downgrade/wifi")
async def downgrade_to_wifi(vehicle_id: str):
    """Downgrade to WiFi-only tracking (Option 2)."""
    service = get_tracking_service(vehicle_id)
    if not service:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    service.downgrade_to_wifi()
    
    return {
        "status": "downgraded",
        "tracking_type": "wifi",
        "wifi_available": service.is_wifi_available(),
    }


@router.get("/vehicles/{vehicle_id}/connection/status")
async def get_connection_status(vehicle_id: str):
    """Get connection status."""
    service = get_tracking_service(vehicle_id)
    if not service:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    conn_info = service.get_connection_status()
    if not conn_info:
        raise HTTPException(status_code=404, detail="Connection status not available")
    
    return {
        "connection_type": conn_info.connection_type,
        "status": conn_info.status.value,
        "signal_strength": conn_info.signal_strength,
        "cellular_available": service.is_cellular_available(),
        "wifi_available": service.is_wifi_available(),
    }


def register_tracking_service(vehicle_id: str, service: TheftTrackingService) -> None:
    """Register tracking service (for dependency injection)."""
    _tracking_services[vehicle_id] = service


__all__ = ["router", "register_tracking_service"]

