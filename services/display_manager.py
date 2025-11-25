"""
Display Manager Service

Manages external monitor output, display detection, and multi-monitor support.
"""

from __future__ import annotations

import logging
import platform
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional

try:
    from PySide6.QtCore import QRect
    from PySide6.QtGui import QScreen
    from PySide6.QtWidgets import QApplication, QWidget
except ImportError:
    try:
        from PySide6.QtCore import QRect
        from PySide6.QtGui import QScreen
        from PySide6.QtWidgets import QApplication, QWidget
    except ImportError:
        # Fallback - make QScreen optional for demo
        QScreen = None  # type: ignore
        QRect = None  # type: ignore
        QApplication = None  # type: ignore
        QWidget = None  # type: ignore

LOGGER = logging.getLogger(__name__)


@dataclass
class DisplayInfo:
    """Information about a display."""

    name: str
    geometry: QRect
    available: bool = True
    primary: bool = False
    index: int = 0


class DisplayManager:
    """Manages display output and external monitor configuration."""

    def __init__(self, app: Optional[QApplication] = None) -> None:
        """
        Initialize display manager.

        Args:
            app: QApplication instance (auto-detected if None)
        """
        self.app = app or QApplication.instance()
        if not self.app:
            raise RuntimeError("QApplication instance required for display management")

        self.displays: List[DisplayInfo] = []
        self.active_display: Optional[DisplayInfo] = None
        self._refresh_displays()

    def _refresh_displays(self) -> None:
        """Refresh list of available displays."""
        self.displays = []
        screens = self.app.screens()

        for idx, screen in enumerate(screens):
            geometry = screen.geometry()
            is_primary = screen == self.app.primaryScreen()

            display = DisplayInfo(
                name=screen.name() or f"Display {idx + 1}",
                geometry=geometry,
                available=True,
                primary=is_primary,
                index=idx,
            )
            self.displays.append(display)

        LOGGER.info("Detected %d display(s)", len(self.displays))

    def get_displays(self) -> List[DisplayInfo]:
        """Get list of available displays."""
        self._refresh_displays()
        return self.displays

    def get_primary_display(self) -> Optional[DisplayInfo]:
        """Get primary display."""
        for display in self.displays:
            if display.primary:
                return display
        return self.displays[0] if self.displays else None

    def get_external_displays(self) -> List[DisplayInfo]:
        """Get list of external (non-primary) displays."""
        return [d for d in self.displays if not d.primary]

    def move_window_to_display(self, window: QWidget, display: DisplayInfo, fullscreen: bool = False) -> bool:
        """
        Move window to specified display.

        Args:
            window: Window widget to move
            display: Target display
            fullscreen: Whether to make window fullscreen

        Returns:
            True if successful
        """
        try:
            # Get screen object
            screens = self.app.screens()
            if display.index >= len(screens):
                LOGGER.error("Display index out of range")
                return False

            screen = screens[display.index]
            geometry = screen.geometry()

            # Move window to display
            window.setGeometry(geometry)
            if fullscreen:
                window.showFullScreen()
            else:
                window.showMaximized()

            self.active_display = display
            LOGGER.info("Moved window to display: %s", display.name)
            return True

        except Exception as e:
            LOGGER.error("Error moving window to display: %s", e)
            return False

    def create_fullscreen_window(self, widget: QWidget, display: Optional[DisplayInfo] = None) -> QWidget:
        """
        Create a fullscreen window on specified display.

        Args:
            widget: Widget to display fullscreen
            display: Target display (uses primary if None)

        Returns:
            Fullscreen window widget
        """
        if display is None:
            display = self.get_primary_display()

        if not display:
            LOGGER.error("No display available")
            return widget

        # Create container window
        container = QWidget()
        container.setWindowTitle("AI Tuner - External Display")
        container.setWindowFlags(
            container.windowFlags()
            | 0x00000080  # Qt::FramelessWindowHint equivalent
            | 0x00000001  # Qt::WindowStaysOnTopHint equivalent
        )

        # Set geometry to display
        screens = self.app.screens()
        if display.index < len(screens):
            screen = screens[display.index]
            container.setGeometry(screen.geometry())
            container.showFullScreen()

        # Add widget to container
        from PySide6.QtWidgets import QVBoxLayout

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widget)

        self.active_display = display
        LOGGER.info("Created fullscreen window on display: %s", display.name)
        return container

    def configure_display_output(self, display: DisplayInfo, resolution: Optional[tuple] = None) -> bool:
        """
        Configure display output (Linux-specific using xrandr).

        Args:
            display: Display to configure
            resolution: Target resolution (width, height) or None for auto

        Returns:
            True if successful
        """
        if platform.system().lower() != "linux":
            LOGGER.warning("Display configuration only supported on Linux")
            return False

        try:
            # Use xrandr to configure display
            if resolution:
                width, height = resolution
                cmd = [
                    "xrandr",
                    "--output",
                    display.name,
                    "--mode",
                    f"{width}x{height}",
                ]
            else:
                cmd = ["xrandr", "--output", display.name, "--auto"]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                LOGGER.info("Configured display %s", display.name)
                self._refresh_displays()
                return True
            else:
                LOGGER.error("Failed to configure display: %s", result.stderr)
                return False

        except Exception as e:
            LOGGER.error("Error configuring display: %s", e)
            return False

    def get_display_info(self) -> Dict:
        """Get information about all displays."""
        return {
            "displays": [
                {
                    "name": d.name,
                    "index": d.index,
                    "primary": d.primary,
                    "geometry": {
                        "x": d.geometry.x(),
                        "y": d.geometry.y(),
                        "width": d.geometry.width(),
                        "height": d.geometry.height(),
                    },
                }
                for d in self.displays
            ],
            "active": self.active_display.name if self.active_display else None,
        }


__all__ = ["DisplayManager", "DisplayInfo"]

