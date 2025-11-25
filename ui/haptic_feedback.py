"""
Haptic Feedback Support
Provides tactile feedback for button presses and critical warnings.
"""

from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication

LOGGER = logging.getLogger(__name__)

# Try to import platform-specific haptic libraries
try:
    import platform
    if platform.system() == "Windows":
        try:
            import win32api
            import win32con
            WINDOWS_HAPTIC_AVAILABLE = True
        except ImportError:
            WINDOWS_HAPTIC_AVAILABLE = False
    elif platform.system() == "Linux":
        # Linux haptic support (if available)
        WINDOWS_HAPTIC_AVAILABLE = False
    else:
        WINDOWS_HAPTIC_AVAILABLE = False
except Exception:
    WINDOWS_HAPTIC_AVAILABLE = False


class HapticFeedback(QObject):
    """Provides haptic feedback for UI interactions."""
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.enabled = True
    
    def is_available(self) -> bool:
        """Check if haptic feedback is available."""
        return WINDOWS_HAPTIC_AVAILABLE
    
    def enable(self) -> None:
        """Enable haptic feedback."""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable haptic feedback."""
        self.enabled = False
    
    def button_press(self) -> None:
        """Provide haptic feedback for button press."""
        if not self.enabled or not self.is_available():
            return
        
        try:
            if WINDOWS_HAPTIC_AVAILABLE:
                # Windows vibration (if supported)
                # This is a placeholder - actual implementation would use
                # appropriate Windows API calls or gamepad vibration
                pass
        except Exception as e:
            LOGGER.debug("Haptic feedback error: %s", e)
    
    def warning(self) -> None:
        """Provide haptic feedback for warning."""
        if not self.enabled or not self.is_available():
            return
        
        # Stronger vibration for warnings
        self.button_press()
        QTimer.singleShot(100, self.button_press)  # Double pulse
    
    def critical(self) -> None:
        """Provide haptic feedback for critical alert."""
        if not self.enabled or not self.is_available():
            return
        
        # Triple pulse for critical
        self.button_press()
        QTimer.singleShot(100, self.button_press)
        QTimer.singleShot(200, self.button_press)
    
    def success(self) -> None:
        """Provide haptic feedback for success."""
        if not self.enabled or not self.is_available():
            return
        
        # Single short pulse
        self.button_press()


# Global haptic feedback instance
_haptic_feedback: Optional[HapticFeedback] = None


def get_haptic_feedback() -> HapticFeedback:
    """Get global haptic feedback instance."""
    global _haptic_feedback
    if _haptic_feedback is None:
        _haptic_feedback = HapticFeedback()
    return _haptic_feedback



