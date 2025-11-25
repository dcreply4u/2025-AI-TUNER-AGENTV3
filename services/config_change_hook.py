"""
Configuration Change Hook
Global hook system for monitoring configuration changes across the application
"""

from __future__ import annotations

import logging
from typing import Callable, Dict, Optional

from services.config_version_control import ChangeType, ChangeSeverity
from services.intelligent_config_monitor import IntelligentConfigMonitor

LOGGER = logging.getLogger(__name__)


class ConfigChangeHook:
    """
    Global configuration change hook system.
    Provides centralized monitoring of all configuration changes.
    """
    
    _instance: Optional['ConfigChangeHook'] = None
    _monitor: Optional[IntelligentConfigMonitor] = None
    _callbacks: list[Callable] = []
    
    @classmethod
    def get_instance(cls) -> 'ConfigChangeHook':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Initialize config change hook."""
        if ConfigChangeHook._monitor is None:
            try:
                from services.config_version_control import ConfigVersionControl
                config_vc = ConfigVersionControl()
                ConfigChangeHook._monitor = IntelligentConfigMonitor(config_vc=config_vc)
            except Exception as e:
                LOGGER.error("Failed to initialize config monitor: %s", e)
    
    def register_callback(self, callback: Callable) -> None:
        """Register a callback for configuration changes."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)
    
    def notify_change(
        self,
        change_type: ChangeType,
        category: str,
        parameter: str,
        old_value: any,
        new_value: any,
        telemetry: Optional[Dict[str, float]] = None,
    ) -> list:
        """
        Notify about a configuration change.
        
        Returns:
            List of warnings generated
        """
        if not self._monitor:
            return []
        
        # Monitor change
        warnings = self._monitor.monitor_change(
            change_type=change_type,
            category=category,
            parameter=parameter,
            old_value=old_value,
            new_value=new_value,
            telemetry=telemetry,
        )
        
        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(warnings, {
                    "change_type": change_type,
                    "category": category,
                    "parameter": parameter,
                    "old_value": old_value,
                    "new_value": new_value,
                })
            except Exception as e:
                LOGGER.error("Error in config change callback: %s", e)
        
        return warnings
    
    def get_monitor(self) -> Optional[IntelligentConfigMonitor]:
        """Get the configuration monitor instance."""
        return self._monitor
















