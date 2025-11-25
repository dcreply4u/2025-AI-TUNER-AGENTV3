"""
UI Scaling Utilities
Provides autoscaling for buttons, tabs, pages, and widgets based on DPI and screen size
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QScreen
from PySide6.QtWidgets import QApplication, QWidget, QSizePolicy


class UIScaler:
    """Utility class for UI scaling based on DPI and screen size."""
    
    _instance: Optional['UIScaler'] = None
    _scale_factor: float = 1.0
    _base_dpi: float = 96.0  # Standard DPI
    
    def __init__(self) -> None:
        """Initialize UI scaler."""
        self._calculate_scale_factor()
        
    @classmethod
    def get_instance(cls) -> 'UIScaler':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _calculate_scale_factor(self) -> None:
        """Calculate scale factor based on screen DPI."""
        app = QApplication.instance()
        if app is None:
            self._scale_factor = 1.0
            return
            
        # Get primary screen
        screen = app.primaryScreen()
        if screen:
            dpi = screen.logicalDotsPerInch()
            # Scale factor: DPI / base DPI, with reasonable bounds
            self._scale_factor = max(0.75, min(2.0, dpi / self._base_dpi))
        else:
            self._scale_factor = 1.0
    
    def scale(self, value: float) -> int:
        """Scale a value by the current scale factor."""
        return int(value * self._scale_factor)
    
    def get_scaled_size(self, base_size: float) -> int:
        """Get scaled size for a base size (alias for scale)."""
        return self.scale(base_size)
    
    def scale_font_size(self, base_size: int) -> int:
        """Scale font size."""
        return max(8, int(base_size * self._scale_factor))
    
    def get_scaled_font_size(self, base_size: int) -> int:
        """Get scaled font size (alias for scale_font_size)."""
        return self.scale_font_size(base_size)
    
    def get_scale_factor(self) -> float:
        """Get current scale factor."""
        return self._scale_factor


def get_scaled_size(base_size: float) -> int:
    """Get scaled size for a base size."""
    scaler = UIScaler.get_instance()
    return scaler.scale(base_size)


def get_scaled_font_size(base_size: int) -> int:
    """Get scaled font size."""
    scaler = UIScaler.get_instance()
    return scaler.scale_font_size(base_size)


def apply_scaling_to_widget(widget: QWidget, base_font_size: Optional[int] = None) -> None:
    """Apply scaling to a widget."""
    scaler = UIScaler.get_instance()
    scale = scaler.get_scale_factor()
    
    # Set size policy for scaling
    size_policy = widget.sizePolicy()
    size_policy.setHorizontalPolicy(QSizePolicy.Policy.Expanding)
    size_policy.setVerticalPolicy(QSizePolicy.Policy.Expanding)
    widget.setSizePolicy(size_policy)
    
    # Scale font if provided
    if base_font_size:
        font = widget.font()
        font.setPixelSize(scaler.scale_font_size(base_font_size))
        widget.setFont(font)


def get_scaled_stylesheet(base_stylesheet: str, font_scale: float = 1.0) -> str:
    """Get scaled stylesheet with relative font sizes."""
    scaler = UIScaler.get_instance()
    scale = scaler.get_scale_factor() * font_scale
    
    # Replace fixed pixel sizes with scaled values
    import re
    
    # Pattern to match font-size: XXpx
    def scale_font_size(match):
        size = float(match.group(1))
        scaled = int(size * scale)
        return f"font-size: {scaled}px"
    
    scaled_stylesheet = re.sub(r'font-size:\s*(\d+(?:\.\d+)?)px', scale_font_size, base_stylesheet)
    
    # Pattern to match padding: XXpx
    def scale_padding(match):
        size = float(match.group(1))
        scaled = int(size * scale)
        return f"padding: {scaled}px"
    
    scaled_stylesheet = re.sub(r'padding:\s*(\d+(?:\.\d+)?)px', scale_padding, scaled_stylesheet)
    
    # Pattern to match border: Xpx
    def scale_border(match):
        size = float(match.group(1))
        scaled = max(1, int(size * scale))
        return f"border: {scaled}px"
    
    scaled_stylesheet = re.sub(r'border:\s*(\d+(?:\.\d+)?)px', scale_border, scaled_stylesheet)
    
    return scaled_stylesheet


__all__ = [
    "UIScaler",
    "get_scaled_size",
    "get_scaled_font_size",
    "apply_scaling_to_widget",
    "get_scaled_stylesheet",
]



