"""
Video Logger Service

Records video streams with telemetry overlays and syncs with telemetry data.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Optional

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

from interfaces.camera_interface import CameraInterface, Frame
from services.video_overlay import TelemetryData, VideoOverlay

LOGGER = logging.getLogger(__name__)


class VideoLogger:
    """Records video with telemetry overlays and syncs with telemetry data."""

    def __init__(
        self,
        output_dir: str | Path = "logs/video",
        enable_overlay: bool = True,
        overlay_style: str = "racing",
        enabled_widgets: Optional[list[str]] = None,
        fps: int = 30,
    ) -> None:
        """
        Initialize video logger.

        Args:
            output_dir: Directory to save video files
            enable_overlay: Enable telemetry overlay on video
            overlay_style: Overlay style (racing, minimal, classic, modern)
            enabled_widgets: List of widget names to display
            fps: Video frame rate
        """
        if cv2 is None:
            raise RuntimeError("OpenCV required for video logging. Install with: pip install opencv-python")

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.enable_overlay = enable_overlay
        self.fps = fps

        # Initialize overlay
        if enable_overlay:
            from services.video_overlay import OverlayStyle

            style_map = {
                "racing": OverlayStyle.RACING,
                "minimal": OverlayStyle.MINIMAL,
                "classic": OverlayStyle.CLASSIC,
                "modern": OverlayStyle.MODERN,
            }
            style = style_map.get(overlay_style, OverlayStyle.RACING)
            self.overlay = VideoOverlay(style=style, enabled_widgets=enabled_widgets)
        else:
            self.overlay = None

        # Recording state
        self.writers: Dict[str, cv2.VideoWriter] = {}
        self.telemetry_sync: Dict[str, list] = {}  # Frame number -> telemetry data
        self.recording = False
        self._lock = threading.Lock()
        self.telemetry_callback: Optional[Callable[[], Dict]] = None

    def start_recording(self, camera_name: str, width: int = 1920, height: int = 1080) -> bool:
        """
        Start recording for a camera.

        Args:
            camera_name: Name of camera to record
            width: Video width
            height: Video height

        Returns:
            True if recording started successfully
        """
        with self._lock:
            if camera_name in self.writers:
                LOGGER.warning("Already recording %s", camera_name)
                return False

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_path = self.output_dir / f"{camera_name}_{timestamp}.mp4"
            sync_path = self.output_dir / f"{camera_name}_{timestamp}_sync.json"

            # Initialize video writer (H.264 codec)
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(str(video_path), fourcc, self.fps, (width, height))

            if not writer.isOpened():
                LOGGER.error("Failed to open video writer for %s", camera_name)
                return False

            self.writers[camera_name] = writer
            self.telemetry_sync[camera_name] = []
            self.recording = True

            LOGGER.info("Started recording %s to %s", camera_name, video_path)
            return True

    def stop_recording(self, camera_name: Optional[str] = None) -> None:
        """
        Stop recording for a camera or all cameras.

        Args:
            camera_name: Name of camera to stop (None = all cameras)
        """
        with self._lock:
            if camera_name:
                if camera_name in self.writers:
                    self.writers[camera_name].release()
                    del self.writers[camera_name]

                    # Save telemetry sync file
                    sync_path = self.output_dir / f"{camera_name}_sync.json"
                    if camera_name in self.telemetry_sync:
                        with open(sync_path, "w") as f:
                            json.dump(self.telemetry_sync[camera_name], f, indent=2)
                        del self.telemetry_sync[camera_name]

                    LOGGER.info("Stopped recording %s", camera_name)
            else:
                # Stop all
                for name, writer in self.writers.items():
                    writer.release()

                    # Save sync files
                    sync_path = self.output_dir / f"{name}_sync.json"
                    if name in self.telemetry_sync:
                        with open(sync_path, "w") as f:
                            json.dump(self.telemetry_sync[name], f, indent=2)

                self.writers.clear()
                self.telemetry_sync.clear()
                self.recording = False
                LOGGER.info("Stopped all recordings")

    def log_frame(self, frame: Frame, camera_name: str) -> None:
        """
        Log a video frame with optional overlay.

        Args:
            frame: Video frame to log
            camera_name: Name of camera
        """
        if not self.recording or camera_name not in self.writers:
            return

        with self._lock:
            writer = self.writers.get(camera_name)
            if not writer:
                return

            # Get telemetry data for overlay
            image = frame.image.copy()
            if self.enable_overlay and self.overlay and frame.telemetry_sync:
                telemetry = self._telemetry_to_overlay_data(frame.telemetry_sync)
                image = self.overlay.render(image, telemetry)

            # Write frame
            writer.write(image)

            # Store telemetry sync data
            if camera_name in self.telemetry_sync:
                self.telemetry_sync[camera_name].append(
                    {
                        "frame_number": frame.frame_number,
                        "timestamp": frame.timestamp,
                        "telemetry": frame.telemetry_sync,
                    }
                )

    def _telemetry_to_overlay_data(self, telemetry: Dict) -> TelemetryData:
        """Convert telemetry dict to TelemetryData for overlay."""
        return TelemetryData(
            timestamp=telemetry.get("timestamp", time.time()),
            lap_time=telemetry.get("lap_time"),
            lap_number=telemetry.get("lap_number"),
            total_distance_mi=telemetry.get("total_distance_mi"),
            speed_mph=telemetry.get("speed_mph") or telemetry.get("Vehicle_Speed"),
            rpm=telemetry.get("rpm") or telemetry.get("Engine_RPM"),
            throttle=telemetry.get("throttle") or telemetry.get("Throttle_Position"),
            boost_psi=telemetry.get("boost_psi") or telemetry.get("Boost_Pressure"),
            coolant_temp=telemetry.get("coolant_temp") or telemetry.get("Coolant_Temp"),
            oil_pressure=telemetry.get("oil_pressure") or telemetry.get("Oil_Pressure"),
            gps_lat=telemetry.get("gps_lat") or telemetry.get("latitude"),
            gps_lon=telemetry.get("gps_lon") or telemetry.get("longitude"),
            gps_speed=telemetry.get("gps_speed") or telemetry.get("speed_mps"),
            gps_heading=telemetry.get("gps_heading") or telemetry.get("heading"),
            e85_percent=telemetry.get("e85_percent") or telemetry.get("FlexFuelPercent"),
            meth_duty=telemetry.get("meth_duty") or telemetry.get("MethInjectionDuty"),
            nitrous_pressure=telemetry.get("nitrous_pressure") or telemetry.get("NitrousBottlePressure"),
            transbrake=telemetry.get("transbrake") or telemetry.get("TransBrakeActive", 0) == 1,
            health_score=telemetry.get("health_score"),
            custom_metrics=telemetry.get("custom_metrics", {}),
        )

    def set_telemetry_callback(self, callback: Callable[[], Dict]) -> None:
        """Set callback to get current telemetry data."""
        self.telemetry_callback = callback

    def configure_overlay(self, **kwargs) -> None:
        """Configure overlay settings."""
        if self.overlay:
            # Update overlay style
            if "style" in kwargs:
                from services.video_overlay import OverlayStyle

                style_map = {
                    "racing": OverlayStyle.RACING,
                    "minimal": OverlayStyle.MINIMAL,
                    "classic": OverlayStyle.CLASSIC,
                    "modern": OverlayStyle.MODERN,
                }
                style = style_map.get(kwargs["style"], OverlayStyle.RACING)
                self.overlay.style = style
                self.overlay._apply_style()

            # Enable/disable widgets
            if "enabled_widgets" in kwargs:
                for name in self.overlay.widgets:
                    self.overlay.disable_widget(name)
                for name in kwargs["enabled_widgets"]:
                    self.overlay.enable_widget(name)

            # Configure individual widgets
            if "widget_config" in kwargs:
                for name, config in kwargs["widget_config"].items():
                    self.overlay.configure_widget(name, **config)


__all__ = ["VideoLogger"]
