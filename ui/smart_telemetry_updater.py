"""
Smart Telemetry Updater

Only updates visible tabs and widgets to reduce CPU usage.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from PySide6.QtWidgets import QTabWidget, QWidget

LOGGER = logging.getLogger(__name__)


class SmartTelemetryUpdater:
    """
    Manages smart telemetry updates - only updates visible widgets.
    """
    
    def __init__(self):
        """Initialize smart telemetry updater."""
        self._registered_widgets: List[QWidget] = []
        self._widget_update_methods: Dict[QWidget, str] = {}  # widget -> method_name
        self._tab_widgets: List[QTabWidget] = []
        self._update_count = 0
        self._skipped_count = 0
    
    def register_widget(self, widget: QWidget, update_method: str = "update_data") -> None:
        """
        Register a widget for telemetry updates.
        
        Args:
            widget: Widget to register
            update_method: Name of the method to call for updates (default: "update_data")
        """
        if widget not in self._registered_widgets:
            self._registered_widgets.append(widget)
            self._widget_update_methods[widget] = update_method
            LOGGER.debug(f"Registered widget for smart updates: {widget.__class__.__name__}")
    
    def register_tab_widget(self, tab_widget: QTabWidget) -> None:
        """
        Register a tab widget to track visible tabs.
        
        Args:
            tab_widget: Tab widget to register
        """
        if tab_widget not in self._tab_widgets:
            self._tab_widgets.append(tab_widget)
            LOGGER.debug(f"Registered tab widget: {tab_widget}")
    
    def is_widget_visible(self, widget: QWidget) -> bool:
        """
        Check if a widget is currently visible.
        
        Args:
            widget: Widget to check
        
        Returns:
            True if widget is visible
        """
        # Check if widget itself is visible
        if not widget.isVisible():
            return False
        
        # Check if widget is in a visible tab
        for tab_widget in self._tab_widgets:
            for i in range(tab_widget.count()):
                tab_widget_instance = tab_widget.widget(i)
                if tab_widget_instance is None:
                    continue
                
                # Check if widget is a child of this tab
                if widget == tab_widget_instance or self._is_child_of(widget, tab_widget_instance):
                    # Only visible if this tab is current
                    if tab_widget.currentIndex() == i:
                        return True
                    else:
                        return False
        
        # If not in a tab, check parent visibility
        parent = widget.parent()
        while parent:
            if not parent.isVisible():
                return False
            parent = parent.parent()
        
        return True
    
    def _is_child_of(self, child: QWidget, parent: QWidget) -> bool:
        """Check if child widget is a descendant of parent."""
        current = child.parent()
        while current:
            if current == parent:
                return True
            current = current.parent()
        return False
    
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """
        Update all visible widgets with telemetry data.
        
        Args:
            data: Telemetry data dictionary
        """
        self._update_count += 1
        
        for widget in self._registered_widgets:
            if not self.is_widget_visible(widget):
                self._skipped_count += 1
                continue
            
            try:
                method_name = self._widget_update_methods.get(widget, "update_data")
                if hasattr(widget, method_name):
                    method = getattr(widget, method_name)
                    method(data)
                else:
                    LOGGER.warning(f"Widget {widget.__class__.__name__} has no method '{method_name}'")
            except Exception as e:
                LOGGER.error(f"Error updating widget {widget.__class__.__name__}: {e}", exc_info=True)
        
        # Log statistics periodically
        if self._update_count % 100 == 0:
            skip_rate = (self._skipped_count / self._update_count * 100) if self._update_count > 0 else 0
            LOGGER.debug(f"Telemetry updates: {self._update_count} total, {self._skipped_count} skipped ({skip_rate:.1f}%)")
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get update statistics.
        
        Returns:
            Dictionary with update statistics
        """
        return {
            "total_updates": self._update_count,
            "skipped_updates": self._skipped_count,
            "registered_widgets": len(self._registered_widgets),
        }

