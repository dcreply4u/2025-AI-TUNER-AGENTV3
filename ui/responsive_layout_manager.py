"""
Global Responsive Layout Manager
Implements fluid layouts, breakpoints, and adaptive UI elements across the entire application.
"""

from __future__ import annotations

import json
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Tuple, Callable

from PySide6.QtCore import QObject, QSize, QPoint, QSettings, Signal, QTimer
from PySide6.QtWidgets import QWidget, QSizePolicy, QApplication
from PySide6.QtGui import QScreen

LOGGER = logging.getLogger(__name__)


class Breakpoint(Enum):
    """Screen size breakpoints for responsive design."""
    XS = 480   # Extra small (mobile)
    SM = 768   # Small (tablet portrait)
    MD = 1024  # Medium (tablet landscape)
    LG = 1280  # Large (desktop)
    XL = 1920  # Extra large (large desktop)
    XXL = 2560 # 2K/4K displays


class ResponsiveLayoutManager(QObject):
    """
    Global responsive layout manager for the entire application.
    
    Features:
    - Fluid layouts with relative units
    - Breakpoint-based responsive design
    - Window size/position persistence
    - Dynamic font and spacing scaling
    - Adaptive graph sizing
    - Content prioritization
    """
    
    # Signal emitted when breakpoint changes
    breakpoint_changed = Signal(Breakpoint)
    
    # Signal emitted when window is resized
    window_resized = Signal(QSize)
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.settings = QSettings("AITuner", "AI-Tuner-Agent")
        self.config_file = Path("config/responsive_ui.json")
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Current breakpoint
        self.current_breakpoint: Breakpoint = Breakpoint.LG
        self.last_window_size: Optional[QSize] = None
        self.last_window_position: Optional[QPoint] = None
        
        # Responsive configuration
        self.config = self._load_config()
        
        # Base sizes (for 1280x720 reference)
        self.base_width = 1280
        self.base_height = 720
        
        # Scale factors
        self.width_scale = 1.0
        self.height_scale = 1.0
        self.font_scale = 1.0
        
        # Register for application events
        if QApplication.instance():
            QApplication.instance().installEventFilter(self)
    
    def _load_config(self) -> Dict:
        """Load responsive UI configuration."""
        default_config = {
            "save_window_state": True,
            "default_width": 1280,
            "default_height": 720,
            "min_width": 800,
            "min_height": 600,
            "font_scaling": True,
            "breakpoints": {
                "xs": {"font_scale": 0.8, "spacing_scale": 0.7},
                "sm": {"font_scale": 0.9, "spacing_scale": 0.8},
                "md": {"font_scale": 1.0, "spacing_scale": 0.9},
                "lg": {"font_scale": 1.0, "spacing_scale": 1.0},
                "xl": {"font_scale": 1.1, "spacing_scale": 1.1},
                "xxl": {"font_scale": 1.2, "spacing_scale": 1.2},
            },
            "graph_config": {
                "min_height": 200,
                "aspect_ratio": None,  # None = flexible, or "16:9" etc.
                "y_axis_min_width": 60,
                "y_axis_max_width": 120,
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                LOGGER.warning("Failed to load responsive UI config: %s", e)
        
        return default_config
    
    def save_config(self) -> None:
        """Save responsive UI configuration."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            LOGGER.error("Failed to save responsive UI config: %s", e)
    
    def get_breakpoint(self, width: int) -> Breakpoint:
        """Determine breakpoint based on window width."""
        if width < Breakpoint.XS.value:
            return Breakpoint.XS
        elif width < Breakpoint.SM.value:
            return Breakpoint.SM
        elif width < Breakpoint.MD.value:
            return Breakpoint.MD
        elif width < Breakpoint.LG.value:
            return Breakpoint.LG
        elif width < Breakpoint.XL.value:
            return Breakpoint.XL
        else:
            return Breakpoint.XXL
    
    def update_breakpoint(self, width: int) -> None:
        """Update current breakpoint and emit signal if changed."""
        new_breakpoint = self.get_breakpoint(width)
        if new_breakpoint != self.current_breakpoint:
            old_breakpoint = self.current_breakpoint
            self.current_breakpoint = new_breakpoint
            LOGGER.info("Breakpoint changed: %s -> %s (width: %d)", 
                       old_breakpoint.name, new_breakpoint.name, width)
            self.breakpoint_changed.emit(new_breakpoint)
    
    def get_scale_factors(self, window_size: QSize) -> Tuple[float, float, float]:
        """
        Calculate scale factors based on window size.
        
        Returns:
            (width_scale, height_scale, font_scale)
        """
        width_scale = window_size.width() / self.base_width
        height_scale = window_size.height() / self.base_height
        
        # Use average for font scaling to maintain aspect
        font_scale = (width_scale + height_scale) / 2.0
        
        # Clamp font scale to reasonable range
        font_scale = max(0.7, min(1.5, font_scale))
        
        # Apply breakpoint-specific scaling
        bp_config = self.config["breakpoints"].get(
            self.current_breakpoint.name.lower(), {}
        )
        if bp_config.get("font_scale"):
            font_scale *= bp_config["font_scale"]
        
        return width_scale, height_scale, font_scale
    
    def scaled_size(self, base_size: int, use_width: bool = True) -> int:
        """
        Get scaled size based on current window dimensions.
        
        Args:
            base_size: Base size in pixels (for 1280x720 reference)
            use_width: If True, scale based on width; if False, scale based on height
        """
        if use_width:
            return int(base_size * self.width_scale)
        else:
            return int(base_size * self.height_scale)
    
    def scaled_font_size(self, base_font_size: int) -> int:
        """Get scaled font size based on current window dimensions."""
        return int(base_font_size * self.font_scale)
    
    def scaled_spacing(self, base_spacing: int) -> int:
        """Get scaled spacing based on current window dimensions."""
        bp_config = self.config["breakpoints"].get(
            self.current_breakpoint.name.lower(), {}
        )
        spacing_scale = bp_config.get("spacing_scale", 1.0)
        return int(base_spacing * spacing_scale * min(self.width_scale, self.height_scale))
    
    def apply_to_window(self, window: QWidget) -> None:
        """Apply responsive settings to a window."""
        # Set minimum size
        min_width = self.config.get("min_width", 800)
        min_height = self.config.get("min_height", 600)
        window.setMinimumSize(min_width, min_height)
        
        # Restore or set default size
        if self.config.get("save_window_state", True):
            self.restore_window_state(window)
        else:
            default_width = self.config.get("default_width", 1280)
            default_height = self.config.get("default_height", 720)
            window.resize(default_width, default_height)
        
        # Update scale factors
        self.width_scale, self.height_scale, self.font_scale = self.get_scale_factors(
            window.size()
        )
        self.update_breakpoint(window.width())
        
        # Connect resize events
        def on_resize(size: QSize):
            self.width_scale, self.height_scale, self.font_scale = self.get_scale_factors(size)
            self.update_breakpoint(size.width())
            self.window_resized.emit(size)
            if self.config.get("save_window_state", True):
                self.save_window_state(window)
        
        # Use a timer to debounce resize events
        self._resize_timer = QTimer()
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(lambda: on_resize(window.size()))
        
        # Connect window resize
        window.resizeEvent = lambda event: (
            super(QWidget, window).resizeEvent(event),
            self._resize_timer.start(100)  # Debounce 100ms
        )
    
    def save_window_state(self, window: QWidget) -> None:
        """Save window size and position."""
        if not self.config.get("save_window_state", True):
            return
        
        try:
            size = window.size()
            pos = window.pos()
            
            self.settings.setValue("window/size", size)
            self.settings.setValue("window/position", pos)
            self.settings.setValue("window/maximized", window.isMaximized())
            
            self.last_window_size = size
            self.last_window_position = pos
        except Exception as e:
            LOGGER.warning("Failed to save window state: %s", e)
    
    def restore_window_state(self, window: QWidget) -> None:
        """Restore window size and position."""
        if not self.config.get("save_window_state", True):
            return
        
        try:
            # Restore size
            saved_size = self.settings.value("window/size")
            if saved_size:
                window.resize(saved_size)
            else:
                default_width = self.config.get("default_width", 1280)
                default_height = self.config.get("default_height", 720)
                window.resize(default_width, default_height)
            
            # Restore position
            saved_pos = self.settings.value("window/position")
            if saved_pos:
                # Ensure window is on screen
                screen = QApplication.primaryScreen()
                if screen:
                    screen_geometry = screen.availableGeometry()
                    # Clamp position to screen bounds
                    x = max(0, min(saved_pos.x(), screen_geometry.width() - 100))
                    y = max(0, min(saved_pos.y(), screen_geometry.height() - 100))
                    window.move(x, y)
            
            # Restore maximized state
            if self.settings.value("window/maximized", False, type=bool):
                QTimer.singleShot(100, window.showMaximized)
        except Exception as e:
            LOGGER.warning("Failed to restore window state: %s", e)
    
    def get_graph_config(self) -> Dict:
        """Get responsive configuration for graphs."""
        return self.config.get("graph_config", {})
    
    def configure_graph_responsive(self, plot_widget) -> None:
        """Configure a graph widget for responsive behavior."""
        graph_config = self.get_graph_config()
        
        # Set size policy for flexible resizing
        plot_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        
        # Configure minimum height
        min_height = graph_config.get("min_height", 200)
        plot_widget.setMinimumHeight(self.scaled_size(min_height, use_width=False))
        
        # Configure Y-axis width based on breakpoint
        y_axis_min = graph_config.get("y_axis_min_width", 60)
        y_axis_max = graph_config.get("y_axis_max_width", 120)
        
        # Scale Y-axis width based on window size
        y_axis_width = int(y_axis_min + (y_axis_max - y_axis_min) * 
                          min(1.0, (self.width_scale - 0.5) / 1.5))
        y_axis_width = max(y_axis_min, min(y_axis_max, y_axis_width))
        
        plot_item = plot_widget.getPlotItem()
        if plot_item:
            left_axis = plot_item.getAxis("left")
            if left_axis:
                left_axis.setWidth(y_axis_width)
                # Update margins
                plot_item.layout.setContentsMargins(
                    y_axis_width + 10, 10, 10, 45
                )
    
    def get_responsive_stylesheet(self, base_stylesheet: str) -> str:
        """
        Apply responsive scaling to a stylesheet.
        Replaces fixed pixel values with scaled values.
        """
        # This is a simplified version - in production, you'd want more sophisticated parsing
        import re
        
        def scale_px(match):
            value = int(match.group(1))
            scaled = self.scaled_size(value)
            return f"{scaled}px"
        
        def scale_font(match):
            value = int(match.group(1))
            scaled = self.scaled_font_size(value)
            return f"{scaled}px"
        
        # Scale font sizes
        result = re.sub(r'font-size:\s*(\d+)px', scale_font, base_stylesheet)
        # Scale spacing (padding, margin)
        result = re.sub(r'(padding|margin)(-top|-bottom|-left|-right)?:\s*(\d+)px', 
                       lambda m: f"{m.group(1)}{m.group(2) or ''}: {self.scaled_spacing(int(m.group(3)))}px",
                       result)
        
        return result


# Global instance
_responsive_manager: Optional[ResponsiveLayoutManager] = None


def get_responsive_manager() -> ResponsiveLayoutManager:
    """Get or create the global responsive layout manager."""
    global _responsive_manager
    if _responsive_manager is None:
        _responsive_manager = ResponsiveLayoutManager()
    return _responsive_manager


def scaled_size(base_size: int, use_width: bool = True) -> int:
    """Get scaled size using global responsive manager."""
    return get_responsive_manager().scaled_size(base_size, use_width)


def scaled_font_size(base_font_size: int) -> int:
    """Get scaled font size using global responsive manager."""
    return get_responsive_manager().scaled_font_size(base_font_size)


def scaled_spacing(base_spacing: int) -> int:
    """Get scaled spacing using global responsive manager."""
    return get_responsive_manager().scaled_spacing(base_spacing)


def get_current_breakpoint() -> Breakpoint:
    """Get current breakpoint."""
    return get_responsive_manager().current_breakpoint


__all__ = [
    "ResponsiveLayoutManager",
    "Breakpoint",
    "get_responsive_manager",
    "scaled_size",
    "scaled_font_size",
    "scaled_spacing",
    "get_current_breakpoint",
]

