"""
Theft Tracking Factory

Easy factory methods for creating tracking services with Option 1 or Option 2.
"""

from __future__ import annotations

import logging
from typing import Optional

from services.theft_tracking_service import TheftTrackingService
from services.connection_manager import ConnectionPriority
from interfaces.gps_interface import GPSInterface
from services.geo_logger import GeoLogger

LOGGER = logging.getLogger(__name__)


def create_wifi_tracking(
    vehicle_id: str,
    gps_interface: Optional[GPSInterface] = None,
    update_interval: float = 15.0,
) -> TheftTrackingService:
    """
    Create WiFi-based tracking service (Option 2 - Default).
    
    Uses WiFi for location uploads when available, stores locally when offline.
    Cost: $0 (uses existing hardware)
    
    Args:
        vehicle_id: Unique vehicle identifier
        gps_interface: GPS interface (auto-initialized if None)
        update_interval: GPS update interval in seconds
        
    Returns:
        TheftTrackingService configured for WiFi tracking
    """
    LOGGER.info("Creating WiFi-based tracking (Option 2) for vehicle: %s", vehicle_id)
    
    return TheftTrackingService(
        vehicle_id=vehicle_id,
        gps_interface=gps_interface,
        update_interval=update_interval,
        enable_cellular=False,  # WiFi only
        connection_priority=ConnectionPriority.WIFI_FIRST,
    )


def create_cellular_tracking(
    vehicle_id: str,
    gps_interface: Optional[GPSInterface] = None,
    cellular_port: Optional[str] = None,
    update_interval: float = 15.0,
) -> TheftTrackingService:
    """
    Create cellular-based tracking service (Option 1 - Premium).
    
    Uses cellular modem for always-on tracking, WiFi as fallback.
    Cost: $30-70 hardware + $5-20/month
    
    Args:
        vehicle_id: Unique vehicle identifier
        gps_interface: GPS interface (auto-initialized if None)
        cellular_port: Cellular modem port (auto-detect if None)
        update_interval: GPS update interval in seconds
        
    Returns:
        TheftTrackingService configured for cellular tracking
    """
    LOGGER.info("Creating cellular-based tracking (Option 1) for vehicle: %s", vehicle_id)
    
    return TheftTrackingService(
        vehicle_id=vehicle_id,
        gps_interface=gps_interface,
        update_interval=update_interval,
        enable_cellular=True,  # Enable cellular
        cellular_port=cellular_port,
        connection_priority=ConnectionPriority.CELLULAR_FIRST,
    )


def create_hybrid_tracking(
    vehicle_id: str,
    gps_interface: Optional[GPSInterface] = None,
    cellular_port: Optional[str] = None,
    update_interval: float = 15.0,
    priority: ConnectionPriority = ConnectionPriority.WIFI_FIRST,
) -> TheftTrackingService:
    """
    Create hybrid tracking service (Option 3 - Best Coverage).
    
    Uses both WiFi and Cellular with automatic failover.
    Cost: $0-70 hardware + $0-20/month
    
    Args:
        vehicle_id: Unique vehicle identifier
        gps_interface: GPS interface (auto-initialized if None)
        cellular_port: Cellular modem port (auto-detect if None)
        update_interval: GPS update interval in seconds
        priority: Connection priority (WIFI_FIRST or CELLULAR_FIRST)
        
    Returns:
        TheftTrackingService configured for hybrid tracking
    """
    LOGGER.info("Creating hybrid tracking (Option 3) for vehicle: %s", vehicle_id)
    
    return TheftTrackingService(
        vehicle_id=vehicle_id,
        gps_interface=gps_interface,
        update_interval=update_interval,
        enable_cellular=True,  # Enable cellular
        cellular_port=cellular_port,
        connection_priority=priority,
    )


def upgrade_to_cellular(tracking_service: TheftTrackingService, cellular_port: Optional[str] = None) -> bool:
    """
    Upgrade existing WiFi tracking to cellular (Option 1).
    
    Args:
        tracking_service: Existing tracking service
        cellular_port: Cellular modem port (auto-detect if None)
        
    Returns:
        True if upgrade successful
    """
    return tracking_service.upgrade_to_cellular(cellular_port)


def downgrade_to_wifi(tracking_service: TheftTrackingService) -> None:
    """
    Downgrade cellular tracking to WiFi-only (Option 2).
    
    Args:
        tracking_service: Existing tracking service
    """
    tracking_service.downgrade_to_wifi()


__all__ = [
    "create_wifi_tracking",
    "create_cellular_tracking",
    "create_hybrid_tracking",
    "upgrade_to_cellular",
    "downgrade_to_wifi",
]






