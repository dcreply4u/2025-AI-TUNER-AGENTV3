"""
Video Overlay System

Creates customizable racing-style telemetry overlays on video feeds.
Users can choose which metrics to display and customize positions.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None


class OverlayPosition(Enum):
    """Overlay widget positions."""

    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"
    CENTER = "center"


class OverlayStyle(Enum):
    """Overlay visual styles."""

    RACING = "racing"  # Bold, high contrast
    MINIMAL = "minimal"  # Clean, subtle
    CLASSIC = "classic"  # Traditional racing style
    MODERN = "modern"  # Sleek, futuristic


@dataclass
class OverlayWidget:
    """Individual overlay widget configuration."""

    name: str
    enabled: bool = True
    position: OverlayPosition = OverlayPosition.TOP_LEFT
    font_scale: float = 0.7
    thickness: int = 2
    color: tuple[int, int, int] = (0, 255, 0)  # BGR format
    bg_color: Optional[tuple[int, int, int]] = (0, 0, 0)
    bg_alpha: float = 0.7
    show_label: bool = True
    format_string: Optional[str] = None  # Custom format, e.g., "{value:.1f} mph"


@dataclass
class TelemetryData:
    """Telemetry data for overlay rendering."""

    timestamp: float = field(default_factory=time.time)
    lap_time: Optional[float] = None
    lap_number: Optional[int] = None
    total_distance_mi: Optional[float] = None
    speed_mph: Optional[float] = None
    rpm: Optional[float] = None
    throttle: Optional[float] = None
    boost_psi: Optional[float] = None
    coolant_temp: Optional[float] = None
    oil_pressure: Optional[float] = None
    gps_lat: Optional[float] = None
    gps_lon: Optional[float] = None
    gps_speed: Optional[float] = None
    gps_heading: Optional[float] = None
    e85_percent: Optional[float] = None
    meth_duty: Optional[float] = None
    nitrous_pressure: Optional[float] = None
    transbrake: bool = False
    health_score: Optional[float] = None
    custom_metrics: Dict[str, float] = field(default_factory=dict)


class VideoOverlay:
    """Racing-style telemetry overlay renderer."""

    # Default widget configurations
    DEFAULT_WIDGETS = {
        "lap_time": OverlayWidget("Lap Time", position=OverlayPosition.TOP_LEFT, color=(0, 255, 255)),
        "lap_number": OverlayWidget("Lap", position=OverlayPosition.TOP_LEFT, color=(0, 255, 255)),
        "speed": OverlayWidget("Speed", position=OverlayPosition.TOP_CENTER, color=(0, 255, 0), font_scale=1.2),
        "rpm": OverlayWidget("RPM", position=OverlayPosition.TOP_RIGHT, color=(0, 100, 255)),
        "throttle": OverlayWidget("Throttle", position=OverlayPosition.BOTTOM_LEFT, color=(255, 200, 0)),
        "boost": OverlayWidget("Boost", position=OverlayPosition.BOTTOM_LEFT, color=(255, 0, 0)),
        "coolant": OverlayWidget("Coolant", position=OverlayPosition.BOTTOM_RIGHT, color=(0, 150, 255)),
        "distance": OverlayWidget("Distance", position=OverlayPosition.BOTTOM_CENTER, color=(200, 200, 200)),
        "gps_speed": OverlayWidget("GPS Speed", position=OverlayPosition.TOP_CENTER, color=(0, 255, 255)),
        "gps_coords": OverlayWidget("GPS", position=OverlayPosition.BOTTOM_RIGHT, color=(150, 150, 150), font_scale=0.5),
        "e85": OverlayWidget("E85%", position=OverlayPosition.BOTTOM_LEFT, color=(255, 255, 0)),
        "meth": OverlayWidget("Meth", position=OverlayPosition.BOTTOM_LEFT, color=(0, 255, 255)),
        "nitrous": OverlayWidget("Nitrous", position=OverlayPosition.BOTTOM_LEFT, color=(255, 0, 255)),
        "transbrake": OverlayWidget("Transbrake", position=OverlayPosition.CENTER, color=(255, 0, 0), font_scale=1.5),
        "health": OverlayWidget("Health", position=OverlayPosition.TOP_RIGHT, color=(0, 255, 0)),
    }

    def __init__(self, style: OverlayStyle = OverlayStyle.RACING, enabled_widgets: Optional[List[str]] = None) -> None:
        """
        Initialize video overlay.

        Args:
            style: Visual style for overlay
            enabled_widgets: List of widget names to enable (None = all enabled)
        """
        if cv2 is None or np is None:
            raise RuntimeError("OpenCV and NumPy required for video overlay")

        self.style = style
        self.widgets: Dict[str, OverlayWidget] = {}
        self.enabled_widgets = enabled_widgets or list(self.DEFAULT_WIDGETS.keys())

        # Initialize widgets
        for name, widget in self.DEFAULT_WIDGETS.items():
            self.widgets[name] = OverlayWidget(**widget.__dict__)
            self.widgets[name].enabled = name in self.enabled_widgets

        # Apply style
        self._apply_style()

    def _apply_style(self) -> None:
        """Apply visual style to widgets."""
        if self.style == OverlayStyle.RACING:
            # Bold, high contrast colors
            for widget in self.widgets.values():
                widget.thickness = 2
                widget.bg_alpha = 0.8
        elif self.style == OverlayStyle.MINIMAL:
            # Subtle, clean
            for widget in self.widgets.values():
                widget.font_scale *= 0.8
                widget.bg_alpha = 0.5
                widget.thickness = 1
        elif self.style == OverlayStyle.CLASSIC:
            # Traditional racing style
            for widget in self.widgets.values():
                widget.color = (0, 255, 0)  # Classic green
                widget.bg_color = (0, 0, 0)
                widget.bg_alpha = 0.7
        elif self.style == OverlayStyle.MODERN:
            # Futuristic, sleek
            for widget in self.widgets.values():
                widget.font_scale *= 1.1
                widget.bg_alpha = 0.6

    def enable_widget(self, name: str) -> None:
        """Enable a widget."""
        if name in self.widgets:
            self.widgets[name].enabled = True

    def disable_widget(self, name: str) -> None:
        """Disable a widget."""
        if name in self.widgets:
            self.widgets[name].enabled = False

    def configure_widget(self, name: str, **kwargs) -> None:
        """Configure widget properties."""
        if name not in self.widgets:
            return
        widget = self.widgets[name]
        for key, value in kwargs.items():
            if hasattr(widget, key):
                setattr(widget, key, value)

    def render(self, frame: "np.ndarray", telemetry: TelemetryData) -> "np.ndarray":
        """
        Render overlay on video frame.

        Args:
            frame: Input video frame (BGR format)
            telemetry: Telemetry data to display

        Returns:
            Frame with overlay rendered
        """
        if frame is None or frame.size == 0:
            return frame

        overlay = frame.copy()
        height, width = frame.shape[:2]

        # Render each enabled widget
        for name, widget in self.widgets.items():
            if not widget.enabled:
                continue

            value = self._get_widget_value(name, telemetry)
            if value is None:
                continue

            text = self._format_widget_text(name, value, widget)
            position = self._get_widget_position(name, width, height)

            # Draw background if specified
            if widget.bg_color:
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, widget.font_scale, widget.thickness)[0]
                padding = 5
                x1 = position[0] - padding
                y1 = position[1] - text_size[1] - padding
                x2 = position[0] + text_size[0] + padding
                y2 = position[1] + padding

                # Draw semi-transparent background
                overlay_region = overlay[y1:y2, x1:x2]
                bg = np.full(overlay_region.shape, widget.bg_color, dtype=np.uint8)
                overlay[y1:y2, x1:x2] = cv2.addWeighted(overlay_region, 1 - widget.bg_alpha, bg, widget.bg_alpha, 0)

            # Draw text
            cv2.putText(
                overlay,
                text,
                position,
                cv2.FONT_HERSHEY_SIMPLEX,
                widget.font_scale,
                widget.color,
                widget.thickness,
                cv2.LINE_AA,
            )

        return overlay

    def _get_widget_value(self, name: str, telemetry: TelemetryData) -> Optional[float | str | bool]:
        """Get value for widget from telemetry data."""
        value_map = {
            "lap_time": telemetry.lap_time,
            "lap_number": telemetry.lap_number,
            "speed": telemetry.speed_mph,
            "rpm": telemetry.rpm,
            "throttle": telemetry.throttle,
            "boost": telemetry.boost_psi,
            "coolant": telemetry.coolant_temp,
            "distance": telemetry.total_distance_mi,
            "gps_speed": telemetry.gps_speed,
            "gps_coords": (telemetry.gps_lat, telemetry.gps_lon),
            "e85": telemetry.e85_percent,
            "meth": telemetry.meth_duty,
            "nitrous": telemetry.nitrous_pressure,
            "transbrake": telemetry.transbrake,
            "health": telemetry.health_score,
        }
        return value_map.get(name)

    def _format_widget_text(self, name: str, value: Optional[float | str | bool | tuple], widget: OverlayWidget) -> str:
        """Format widget text with label and value."""
        if value is None:
            return ""

        label = widget.name if widget.show_label else ""
        separator = ": " if label else ""

        # Handle special cases
        if name == "lap_time" and isinstance(value, (int, float)):
            minutes = int(value // 60)
            seconds = value % 60
            formatted = f"{minutes:02d}:{seconds:05.2f}"
        elif name == "gps_coords" and isinstance(value, tuple):
            lat, lon = value
            if lat and lon:
                formatted = f"{lat:.5f}, {lon:.5f}"
            else:
                return ""
        elif name == "transbrake" and isinstance(value, bool):
            formatted = "ACTIVE" if value else ""
            if not value:
                return ""  # Don't show if not active
        elif isinstance(value, bool):
            formatted = "ON" if value else "OFF"
        elif isinstance(value, (int, float)):
            if widget.format_string:
                formatted = widget.format_string.format(value=value)
            else:
                # Auto-format based on widget type
                if name in ("speed", "gps_speed"):
                    formatted = f"{value:.1f} mph"
                elif name == "rpm":
                    formatted = f"{int(value)}"
                elif name in ("throttle", "e85", "meth", "health"):
                    formatted = f"{value:.1f}%"
                elif name == "boost":
                    formatted = f"{value:.1f} psi"
                elif name == "coolant":
                    formatted = f"{value:.1f}°C"
                elif name == "distance":
                    formatted = f"{value:.2f} mi"
                elif name == "nitrous":
                    formatted = f"{value:.0f} psi"
                else:
                    formatted = f"{value:.2f}"
        else:
            formatted = str(value)

        return f"{label}{separator}{formatted}"

    def _get_widget_position(self, name: str, width: int, height: int) -> tuple[int, int]:
        """Get pixel position for widget based on its position enum."""
        widget = self.widgets[name]
        margin = 20

        if widget.position == OverlayPosition.TOP_LEFT:
            return (margin, margin + 30)
        elif widget.position == OverlayPosition.TOP_CENTER:
            return (width // 2 - 100, margin + 30)
        elif widget.position == OverlayPosition.TOP_RIGHT:
            return (width - 200, margin + 30)
        elif widget.position == OverlayPosition.BOTTOM_LEFT:
            return (margin, height - margin)
        elif widget.position == OverlayPosition.BOTTOM_CENTER:
            return (width // 2 - 100, height - margin)
        elif widget.position == OverlayPosition.BOTTOM_RIGHT:
            return (width - 200, height - margin)
        elif widget.position == OverlayPosition.CENTER:
            return (width // 2 - 100, height // 2)
        else:
            return (margin, margin + 30)  # Default to top-left

    def get_config(self) -> Dict[str, Dict]:
        """Get current overlay configuration (for saving/loading)."""
        return {
            name: {
                "enabled": widget.enabled,
                "position": widget.position.value,
                "font_scale": widget.font_scale,
                "color": widget.color,
                "show_label": widget.show_label,
            }
            for name, widget in self.widgets.items()
        }

    def load_config(self, config: Dict[str, Dict]) -> None:
        """Load overlay configuration."""
        for name, settings in config.items():
            if name in self.widgets:
                self.configure_widget(name, **settings)


__all__ = [
    "OverlayPosition",
    "OverlayStyle",
    "OverlayWidget",
    "TelemetryData",
    "VideoOverlay",
]
