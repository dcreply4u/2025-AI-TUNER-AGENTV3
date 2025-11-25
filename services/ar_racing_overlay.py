"""
AR Racing Overlay

Augmented Reality overlay for racing - see telemetry, racing line,
and coaching tips overlaid on your view. This is NEXT LEVEL!
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

LOGGER = logging.getLogger(__name__)


class AROverlayMode(Enum):
    """AR overlay display modes."""

    MINIMAL = "minimal"  # Just essential metrics
    STANDARD = "standard"  # Standard telemetry
    RACING = "racing"  # Full racing overlay
    COACHING = "coaching"  # Coaching tips overlay


@dataclass
class AROverlayElement:
    """An AR overlay element."""

    element_type: str  # "metric", "coaching", "racing_line", "braking_point"
    position: tuple[float, float]  # (x, y) normalized 0-1
    content: str
    color: tuple[int, int, int]  # BGR
    size: float = 1.0
    opacity: float = 1.0


class ARRacingOverlay:
    """
    AR Racing Overlay System.

    UNIQUE FEATURE: No one has done AR telemetry overlay for racing!
    This overlays telemetry, racing line, and coaching on your view.
    Think Iron Man HUD for racing!
    """

    def __init__(self, mode: AROverlayMode = AROverlayMode.RACING) -> None:
        """
        Initialize AR overlay.

        Args:
            mode: Overlay display mode
        """
        if cv2 is None or np is None:
            raise RuntimeError("OpenCV and NumPy required for AR overlay")

        self.mode = mode
        self.elements: List[AROverlayElement] = []

    def render_overlay(
        self,
        frame: "np.ndarray",
        telemetry: Dict[str, float],
        coaching_tips: Optional[List[str]] = None,
        racing_line: Optional[List[tuple[float, float]]] = None,
    ) -> "np.ndarray":
        """
        Render AR overlay on video frame.

        Args:
            frame: Video frame (BGR format)
            telemetry: Telemetry data
            coaching_tips: List of coaching tips
            racing_line: Racing line coordinates (normalized 0-1)

        Returns:
            Frame with AR overlay
        """
        if frame is None or frame.size == 0:
            return frame

        overlay = frame.copy()
        height, width = frame.shape[:2]

        # Clear previous elements
        self.elements.clear()

        # Add telemetry metrics
        if self.mode in [AROverlayMode.STANDARD, AROverlayMode.RACING]:
            self._add_telemetry_elements(telemetry, width, height)

        # Add coaching tips
        if self.mode == AROverlayMode.COACHING and coaching_tips:
            self._add_coaching_elements(coaching_tips, width, height)

        # Add racing line
        if self.mode == AROverlayMode.RACING and racing_line:
            self._add_racing_line(overlay, racing_line, width, height)

        # Add braking points
        if self.mode == AROverlayMode.RACING:
            self._add_braking_points(overlay, width, height)

        # Render all elements
        for element in self.elements:
            self._render_element(overlay, element, width, height)

        return overlay

    def _add_telemetry_elements(self, telemetry: Dict, width: int, height: int) -> None:
        """Add telemetry metric elements."""
        # Top-left: Speed (large)
        speed = telemetry.get("Vehicle_Speed", 0)
        self.elements.append(
            AROverlayElement(
                element_type="metric",
                position=(0.05, 0.1),
                content=f"{speed:.0f} MPH",
                color=(0, 255, 0),  # Green
                size=2.0,
            )
        )

        # Top-center: RPM
        rpm = telemetry.get("Engine_RPM", 0)
        self.elements.append(
            AROverlayElement(
                element_type="metric",
                position=(0.5, 0.05),
                content=f"RPM: {rpm:.0f}",
                color=(0, 200, 255),  # Orange
                size=1.5,
            )
        )

        # Top-right: Lap time
        lap_time = telemetry.get("lap_time", 0)
        if lap_time:
            minutes = int(lap_time // 60)
            seconds = lap_time % 60
            self.elements.append(
                AROverlayElement(
                    element_type="metric",
                    position=(0.85, 0.1),
                    content=f"{minutes:02d}:{seconds:05.2f}",
                    color=(0, 255, 255),  # Cyan
                    size=1.8,
                )
            )

        # Bottom-left: Critical metrics
        boost = telemetry.get("Boost_Pressure", 0)
        self.elements.append(
            AROverlayElement(
                element_type="metric",
                position=(0.05, 0.9),
                content=f"Boost: {boost:.1f} PSI",
                color=(0, 0, 255) if boost > 20 else (0, 255, 0),  # Red if high
                size=1.2,
            )
        )

        # Bottom-center: Lambda
        lambda_val = telemetry.get("Lambda", 1.0)
        lambda_color = (0, 255, 0)  # Green
        if lambda_val > 1.1:
            lambda_color = (0, 0, 255)  # Red (too lean)
        elif lambda_val < 0.9:
            lambda_color = (0, 165, 255)  # Orange (too rich)

        self.elements.append(
            AROverlayElement(
                element_type="metric",
                position=(0.5, 0.9),
                content=f"λ: {lambda_val:.2f}",
                color=lambda_color,
                size=1.2,
            )
        )

    def _add_coaching_elements(self, tips: List[str], width: int, height: int) -> None:
        """Add coaching tip elements."""
        for i, tip in enumerate(tips[:3]):  # Max 3 tips
            self.elements.append(
                AROverlayElement(
                    element_type="coaching",
                    position=(0.5, 0.3 + i * 0.1),
                    content=tip,
                    color=(0, 255, 255),  # Cyan
                    size=1.0,
                )
            )

    def _add_racing_line(self, overlay: "np.ndarray", racing_line: List[tuple], width: int, height: int) -> None:
        """Draw racing line on overlay."""
        if len(racing_line) < 2:
            return

        points = [(int(x * width), int(y * height)) for x, y in racing_line]
        for i in range(len(points) - 1):
            cv2.line(overlay, points[i], points[i + 1], (0, 255, 0), 2)

    def _add_braking_points(self, overlay: "np.ndarray", width: int, height: int) -> None:
        """Add braking point markers."""
        # Would use GPS data to determine braking points
        # For now, placeholder
        pass

    def _render_element(self, overlay: "np.ndarray", element: AROverlayElement, width: int, height: int) -> None:
        """Render a single overlay element."""
        x = int(element.position[0] * width)
        y = int(element.position[1] * height)

        font_scale = element.size
        thickness = int(element.size)
        color = element.color

        # Draw text with background for readability
        text_size = cv2.getTextSize(element.content, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
        padding = 5

        # Semi-transparent background
        overlay_region = overlay[
            y - text_size[1] - padding : y + padding,
            x - padding : x + text_size[0] + padding,
        ]
        bg = np.full(overlay_region.shape, (0, 0, 0), dtype=np.uint8)
        overlay[y - text_size[1] - padding : y + padding, x - padding : x + text_size[0] + padding] = cv2.addWeighted(
            overlay_region, 1 - 0.7, bg, 0.7, 0
        )

        # Draw text
        cv2.putText(
            overlay,
            element.content,
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            color,
            thickness,
            cv2.LINE_AA,
        )


__all__ = ["ARRacingOverlay", "AROverlayMode", "AROverlayElement"]

