"""
Unified Adapter Manager

Manages all adapter types (GPIO, OBD2, Serial) with:
- Auto-detection
- Health monitoring
- Auto-configuration
- Connection management
- Performance tracking
"""

from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional, Callable

from services.adapter_database import (
    AdapterConfig,
    AdapterConnection,
    AdapterType,
    get_adapter_database,
)

from interfaces.gpio_adapter_detector import GPIOAdapterDetector
from interfaces.obd2_adapter_detector import OBD2AdapterDetector
from interfaces.serial_adapter_detector import SerialAdapterDetector

LOGGER = logging.getLogger(__name__)


class AdapterHealthMonitor:
    """Monitor adapter health and performance."""
    
    def __init__(self, adapter_name: str) -> None:
        """Initialize health monitor."""
        self.adapter_name = adapter_name
        self.db = get_adapter_database()
        self.error_count = 0
        self.last_error_time = 0.0
        self.last_success_time = time.time()
        self.connection_start_time = time.time()
        
    def log_error(self, error: Exception) -> None:
        """Log adapter error."""
        self.error_count += 1
        self.last_error_time = time.time()
        LOGGER.warning("Adapter %s error: %s", self.adapter_name, error)
        
        # Log to database
        self.db.log_performance_metric(
            self.adapter_name,
            error_rate=1.0,  # Error occurred
        )
    
    def log_success(self) -> None:
        """Log successful operation."""
        self.last_success_time = time.time()
        
    def get_health_score(self) -> float:
        """
        Calculate health score (0.0 to 1.0).
        
        Returns:
            Health score where 1.0 is perfect health
        """
        if self.error_count == 0:
            return 1.0
        
        # Calculate time since last error
        time_since_error = time.time() - self.last_error_time
        time_since_start = time.time() - self.connection_start_time
        
        # Penalize recent errors
        if time_since_error < 60:  # Error in last minute
            return max(0.0, 1.0 - (self.error_count * 0.2))
        elif time_since_error < 300:  # Error in last 5 minutes
            return max(0.0, 1.0 - (self.error_count * 0.1))
        else:
            # Errors are old, reduce penalty
            return max(0.5, 1.0 - (self.error_count * 0.05))
    
    def get_status(self) -> str:
        """Get adapter status string."""
        health = self.get_health_score()
        
        if health >= 0.9:
            return "Healthy"
        elif health >= 0.7:
            return "Degraded"
        elif health >= 0.5:
            return "Warning"
        else:
            return "Critical"


class UnifiedAdapterManager:
    """Unified manager for all adapter types."""
    
    def __init__(self) -> None:
        """Initialize unified adapter manager."""
        self.db = get_adapter_database()
        
        # Detectors
        self.gpio_detector = GPIOAdapterDetector()
        self.obd2_detector = OBD2AdapterDetector()
        self.serial_detector = SerialAdapterDetector()
        
        # Active adapters
        self.active_adapters: Dict[str, AdapterConfig] = {}
        self.health_monitors: Dict[str, AdapterHealthMonitor] = {}
        self.connections: Dict[str, AdapterConnection] = {}
        
        # Auto-detection enabled
        self.auto_detection_enabled = True
        
    def detect_all_adapters(self) -> Dict[AdapterType, List[AdapterConfig]]:
        """
        Detect all available adapters.
        
        Returns:
            Dictionary mapping adapter type to list of adapters
        """
        adapters = {
            AdapterType.GPIO: [],
            AdapterType.OBD2: [],
            AdapterType.SERIAL: [],
        }
        
        if self.auto_detection_enabled:
            LOGGER.info("Detecting all adapters...")
            
            # Detect GPIO adapters
            try:
                adapters[AdapterType.GPIO] = self.gpio_detector.detect_all()
                LOGGER.info("Detected %d GPIO adapters", len(adapters[AdapterType.GPIO]))
            except Exception as e:
                LOGGER.error("Failed to detect GPIO adapters: %s", e)
            
            # Detect OBD2 adapters
            try:
                adapters[AdapterType.OBD2] = self.obd2_detector.detect_all()
                LOGGER.info("Detected %d OBD2 adapters", len(adapters[AdapterType.OBD2]))
            except Exception as e:
                LOGGER.error("Failed to detect OBD2 adapters: %s", e)
            
            # Detect Serial adapters
            try:
                adapters[AdapterType.SERIAL] = self.serial_detector.detect_all()
                LOGGER.info("Detected %d Serial adapters", len(adapters[AdapterType.SERIAL]))
            except Exception as e:
                LOGGER.error("Failed to detect Serial adapters: %s", e)
        
        return adapters
    
    def get_adapter(self, name: str) -> Optional[AdapterConfig]:
        """Get adapter by name."""
        # Check active adapters
        if name in self.active_adapters:
            return self.active_adapters[name]
        
        # Check database
        return self.db.get_adapter(name)
    
    def list_adapters(self, adapter_type: Optional[AdapterType] = None,
                     enabled_only: bool = True) -> List[AdapterConfig]:
        """List all adapters."""
        return self.db.list_adapters(adapter_type=adapter_type, enabled_only=enabled_only)
    
    def activate_adapter(self, name: str) -> bool:
        """
        Activate adapter.
        
        Args:
            name: Adapter name
            
        Returns:
            True if successful
        """
        adapter = self.get_adapter(name)
        if not adapter:
            LOGGER.error("Adapter not found: %s", name)
            return False
        
        if not adapter.enabled:
            LOGGER.warning("Adapter is disabled: %s", name)
            return False
        
        # Create connection record
        connection = AdapterConnection(
            adapter_name=name,
            connected_at=time.time(),
            status="connected",
        )
        self.connections[name] = connection
        
        # Add to active adapters
        self.active_adapters[name] = adapter
        
        # Create health monitor
        self.health_monitors[name] = AdapterHealthMonitor(name)
        
        LOGGER.info("Activated adapter: %s", name)
        return True
    
    def deactivate_adapter(self, name: str) -> bool:
        """
        Deactivate adapter.
        
        Args:
            name: Adapter name
            
        Returns:
            True if successful
        """
        if name not in self.active_adapters:
            return False
        
        # Update connection record
        if name in self.connections:
            connection = self.connections[name]
            connection.disconnected_at = time.time()
            connection.connection_duration = connection.disconnected_at - connection.connected_at
            connection.status = "disconnected"
            
            # Log to database
            self.db.log_connection(connection)
        
        # Remove from active
        del self.active_adapters[name]
        if name in self.health_monitors:
            del self.health_monitors[name]
        if name in self.connections:
            del self.connections[name]
        
        LOGGER.info("Deactivated adapter: %s", name)
        return True
    
    def get_adapter_health(self, name: str) -> Optional[Dict]:
        """Get adapter health information."""
        if name not in self.health_monitors:
            return None
        
        monitor = self.health_monitors[name]
        return {
            "health_score": monitor.get_health_score(),
            "status": monitor.get_status(),
            "error_count": monitor.error_count,
            "last_error_time": monitor.last_error_time,
            "last_success_time": monitor.last_success_time,
            "uptime": time.time() - monitor.connection_start_time,
        }
    
    def log_adapter_error(self, name: str, error: Exception) -> None:
        """Log adapter error."""
        if name in self.health_monitors:
            self.health_monitors[name].log_error(error)
    
    def log_adapter_success(self, name: str) -> None:
        """Log adapter success."""
        if name in self.health_monitors:
            self.health_monitors[name].log_success()
    
    def auto_configure_adapter(self, name: str) -> bool:
        """
        Auto-configure adapter with optimal settings.
        
        Args:
            name: Adapter name
            
        Returns:
            True if successful
        """
        adapter = self.get_adapter(name)
        if not adapter:
            return False
        
        # Apply auto-configuration based on adapter type
        if adapter.adapter_type == AdapterType.OBD2:
            return self._auto_configure_obd2(adapter)
        elif adapter.adapter_type == AdapterType.SERIAL:
            return self._auto_configure_serial(adapter)
        elif adapter.adapter_type == AdapterType.GPIO:
            return self._auto_configure_gpio(adapter)
        
        return True
    
    def _auto_configure_obd2(self, adapter: AdapterConfig) -> bool:
        """Auto-configure OBD2 adapter."""
        # OBD2 adapters typically use 115200 baud
        # Additional configuration would be done through ELM327 commands
        LOGGER.info("Auto-configured OBD2 adapter: %s", adapter.name)
        return True
    
    def _auto_configure_serial(self, adapter: AdapterConfig) -> bool:
        """Auto-configure serial adapter."""
        # Serial adapters use various baud rates
        # Default to 115200 if not specified
        if adapter.capabilities and adapter.capabilities.max_baud_rate == 0:
            adapter.capabilities.max_baud_rate = 115200
            self.db.add_adapter(adapter)
        
        LOGGER.info("Auto-configured serial adapter: %s", adapter.name)
        return True
    
    def _auto_configure_gpio(self, adapter: AdapterConfig) -> bool:
        """Auto-configure GPIO adapter."""
        # GPIO adapters typically need pin configuration
        # This would be handled by the GPIO interface
        LOGGER.info("Auto-configured GPIO adapter: %s", adapter.name)
        return True
    
    def get_recommended_adapter(self, adapter_type: AdapterType,
                               criteria: Optional[Dict] = None) -> Optional[AdapterConfig]:
        """
        Get recommended adapter based on criteria.
        
        Args:
            adapter_type: Type of adapter needed
            criteria: Optional criteria (e.g., {"max_gpio_pins": 20})
            
        Returns:
            Recommended adapter or None
        """
        adapters = self.list_adapters(adapter_type=adapter_type, enabled_only=True)
        
        if not adapters:
            return None
        
        # If no criteria, return first available
        if not criteria:
            return adapters[0] if adapters else None
        
        # Score adapters based on criteria
        best_adapter = None
        best_score = -1
        
        for adapter in adapters:
            score = 0
            
            # Check health
            health = self.get_adapter_health(adapter.name)
            if health:
                score += health["health_score"] * 10
            
            # Check capabilities
            if adapter.capabilities:
                if "max_gpio_pins" in criteria:
                    if adapter.capabilities.max_gpio_pins >= criteria["max_gpio_pins"]:
                        score += 5
                
                if "supports_i2c" in criteria and criteria["supports_i2c"]:
                    if adapter.capabilities.supports_i2c:
                        score += 3
            
            # Prefer built-in adapters
            if adapter.connection_type.value == "builtin":
                score += 2
            
            if score > best_score:
                best_score = score
                best_adapter = adapter
        
        return best_adapter
    
    def enable_auto_detection(self, enabled: bool = True) -> None:
        """Enable or disable auto-detection."""
        self.auto_detection_enabled = enabled
        LOGGER.info("Auto-detection %s", "enabled" if enabled else "disabled")


# Global manager instance
_manager_instance: Optional[UnifiedAdapterManager] = None


def get_unified_adapter_manager() -> UnifiedAdapterManager:
    """Get or create global unified adapter manager."""
    global _manager_instance
    
    if _manager_instance is None:
        _manager_instance = UnifiedAdapterManager()
    
    return _manager_instance


__all__ = [
    "UnifiedAdapterManager",
    "AdapterHealthMonitor",
    "get_unified_adapter_manager",
]






