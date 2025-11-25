"""
Keyboard Shortcuts System
Provides keyboard shortcuts for TelemetryIQ operations
"""

from __future__ import annotations

from typing import Dict, Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut


class ShortcutManager:
    """Manages keyboard shortcuts for the application."""
    
    _instance: Optional['ShortcutManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ShortcutManager, cls).__new__(cls)
            cls._instance._shortcuts: Dict[str, QShortcut] = {}
            cls._instance._callbacks: Dict[str, Callable] = {}
        return cls._instance
    
    def register_shortcut(
        self,
        key: str,
        callback: Callable,
        parent,
        description: str = ""
    ) -> None:
        """
        Register a keyboard shortcut.
        
        Args:
            key: Key sequence (e.g., "Ctrl+H", "V", "P")
            callback: Function to call when shortcut is triggered
            parent: Parent widget for the shortcut
            description: Optional description for tooltips
        """
        shortcut = QShortcut(QKeySequence(key), parent)
        shortcut.activated.connect(callback)
        self._shortcuts[key] = shortcut
        self._callbacks[key] = callback
        
    def get_shortcut_help(self) -> str:
        """Get help text for all registered shortcuts."""
        help_text = "Keyboard Shortcuts:\n\n"
        for key, callback in self._callbacks.items():
            help_text += f"{key}: {callback.__name__ if hasattr(callback, '__name__') else 'Action'}\n"
        return help_text


# Global shortcut manager instance
_shortcut_manager = ShortcutManager()


def register_shortcut(key: str, callback: Callable, parent, description: str = "") -> None:
    """Register a keyboard shortcut."""
    _shortcut_manager.register_shortcut(key, callback, parent, description)


def get_shortcut_manager() -> ShortcutManager:
    """Get the global shortcut manager."""
    return _shortcut_manager


# Standard TelemetryIQ shortcuts
STANDARD_SHORTCUTS = {
    "P": "Live Logger (P Key)",
    "V": "Toggle 2D/3D View",
    "Ctrl+H": "Horizontal Interpolation",
    "Ctrl+V": "Vertical Interpolation",
    "Ctrl+S": "Table Smoothing",
    "A": "Local Autotune",
    "Ctrl+U": "Update Controller",
    "Ctrl+B": "Burn",
    "Ctrl+E": "Export Data",
    "F1": "Help / Shortcuts",
}


__all__ = ["ShortcutManager", "register_shortcut", "get_shortcut_manager", "STANDARD_SHORTCUTS"]



