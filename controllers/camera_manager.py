"""
Camera Manager Controller

Integrates camera interfaces with video logging and telemetry synchronization.
"""

from __future__ import annotations

import logging
from typing import Callable, Dict, Optional

from interfaces.camera_interface import CameraConfig, CameraManager as CameraInterfaceManager, Frame
from services.live_streamer import LiveStreamer
from services.video_logger import VideoLogger

try:
    from services.voice_feedback import VoiceFeedback
except ImportError:
    VoiceFeedback = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class CameraManager:
    """Controller for managing cameras and video logging."""

    def __init__(
        self,
        video_logger: Optional[VideoLogger] = None,
        telemetry_sync: Optional[Callable[[], dict]] = None,
        voice_feedback: Optional["VoiceFeedback"] = None,
        live_streamer: Optional[LiveStreamer] = None,
    ) -> None:
        """
        Initialize camera manager.

        Args:
            video_logger: Video logger instance
            telemetry_sync: Function to get current telemetry for frame sync
            voice_feedback: Voice feedback service for announcements
            live_streamer: Live streaming service for YouTube/RTMP
        """
        # Auto-detect USB cameras (but skip network cameras to prevent startup delays)
        LOGGER.info("Initializing CameraManager (auto-detecting USB cameras only)")
        import os
        is_demo_mode = os.environ.get("AITUNER_DEMO_MODE", "false").lower() == "true"
        if is_demo_mode:
            LOGGER.info("Demo mode detected - network cameras will be skipped")
        
        # Auto-detect USB and CSI cameras (fast), but skip network cameras (slow)
        self.camera_manager = CameraInterfaceManager(auto_detect=True, include_network=False)
        LOGGER.debug("CameraInterfaceManager created with USB/CSI auto-detection")
        
        # Log detected cameras
        if self.camera_manager.cameras:
            LOGGER.info("Auto-detected %d camera(s): %s", 
                       len(self.camera_manager.cameras),
                       ", ".join(self.camera_manager.cameras.keys()))
        else:
            LOGGER.info("No cameras auto-detected (this is normal if no camera is connected)")
        
        self.video_logger = video_logger or VideoLogger()
        LOGGER.debug("VideoLogger initialized")
        
        self.live_streamer = live_streamer
        if live_streamer:
            LOGGER.debug("LiveStreamer provided")
        else:
            LOGGER.debug("No LiveStreamer provided")
        
        self.telemetry_sync = telemetry_sync
        self.voice_feedback = voice_feedback
        self.recording = False
        self.session_id: Optional[str] = None
        self.streaming_cameras: Dict[str, str] = {}  # camera_name -> stream_name

        # Set telemetry sync callback
        if self.telemetry_sync:
            self.camera_manager.set_telemetry_sync(self.telemetry_sync)
            LOGGER.debug("Telemetry sync callback set")

    def add_camera(self, config: CameraConfig, notification_callback: Optional[Callable[[str, str], None]] = None) -> bool:
        """
        Add a camera to the manager.
        
        Args:
            config: Camera configuration
            notification_callback: Optional callback for notifications (message, level)
        
        Returns:
            True if camera added successfully
        """
        LOGGER.info("Adding camera: %s (type: %s, source: %s)", 
                   config.name, config.camera_type.value, config.source)
        try:
            success = self.camera_manager.add_camera(config)
            if success:
                LOGGER.info("Camera added successfully: %s", config.name)
                if self.voice_feedback:
                    self.voice_feedback.announce_camera_status(f"Camera {config.name} connected", config.name)
                if self.recording:
                    # Start recording for this camera
                    camera = self.camera_manager.get_camera(config.name)
                    if camera:
                        LOGGER.debug("Starting recording for camera: %s", config.name)
                        self._start_camera_recording(camera)
            else:
                msg = f"Camera '{config.name}' failed to connect - continuing without it"
                LOGGER.warning("%s (type: %s, source: %s)", msg, config.camera_type.value, config.source)
                if notification_callback:
                    notification_callback(msg, "warning")
                if self.voice_feedback:
                    self.voice_feedback.announce_camera_status(f"Failed to connect camera {config.name}", config.name)
            return success
        except Exception as e:
            msg = f"Camera '{config.name}' error: {str(e)} - feature disabled"
            LOGGER.error("%s (type: %s, source: %s)", msg, config.camera_type.value, config.source, exc_info=True)
            if notification_callback:
                notification_callback(msg, "error")
            return False

    def remove_camera(self, name: str) -> None:
        """Remove a camera."""
        if self.recording:
            self.video_logger.stop_recording(name)
            if self.voice_feedback:
                self.voice_feedback.announce_camera_status(f"Recording stopped for {name}", name)
        self.camera_manager.remove_camera(name)
        if self.voice_feedback:
            self.voice_feedback.announce_camera_status(f"Camera {name} disconnected", name)

    def start_recording(self, session_id: str) -> None:
        """
        Start recording all cameras.

        Args:
            session_id: Session identifier for file naming
        """
        if self.recording:
            LOGGER.warning("Recording already in progress")
            if self.voice_feedback:
                self.voice_feedback.announce("Recording already in progress", channel="camera")
            return

        self.session_id = session_id
        self.recording = True

        # Start recording for each camera
        active_cameras = []
        for name, camera in self.camera_manager.cameras.items():
            if camera.config.enabled:
                self._start_camera_recording(camera)
                active_cameras.append(name)

        if self.voice_feedback:
            if active_cameras:
                camera_list = ", ".join(active_cameras)
                self.voice_feedback.announce(f"Recording started on {camera_list}", channel="camera")
            else:
                self.voice_feedback.announce("Recording started, but no cameras are enabled", channel="camera")

        LOGGER.info("Started recording session: %s", session_id)

    def stop_recording(self) -> None:
        """Stop recording all cameras."""
        if not self.recording:
            return

        self.video_logger.stop_all()
        self.recording = False
        session_id = self.session_id
        self.session_id = None

        if self.voice_feedback:
            self.voice_feedback.announce("Recording stopped", channel="camera")

        LOGGER.info("Stopped recording")

    def _start_camera_recording(self, camera: "CameraInterface") -> None:
        """Start recording for a specific camera."""
        if not camera.config.enabled:
            return

        # Get frame dimensions from first frame or use config
        width = camera.config.width
        height = camera.config.height
        fps = camera.config.fps

        # Try to get actual dimensions from camera
        if camera.cap:
            try:
                import cv2
                width = int(camera.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or width
                height = int(camera.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or height
                fps = int(camera.cap.get(cv2.CAP_PROP_FPS)) or fps
            except Exception:
                pass

        # Set up frame callback to log frames
        original_callback = camera.frame_callback

        def frame_handler(frame: Frame) -> None:
            if self.recording:
                # Sync telemetry data to frame
                if self.telemetry_sync:
                    frame.telemetry_sync = self.telemetry_sync()
                self.video_logger.log_frame(frame, camera_name=camera.config.name)
            # Feed frame to live streamer if streaming
            if self.live_streamer and camera.config.name in self.streaming_cameras:
                self.live_streamer.feed_frame(camera.config.name, frame.image)
            if original_callback:
                original_callback(frame)

        camera.frame_callback = frame_handler

        # Start video logger for this camera
        success = self.video_logger.start_recording(
            camera_name=camera.config.name,
            width=width,
            height=height,
            fps=fps,
        )

        if success and self.voice_feedback:
            self.voice_feedback.announce_camera_status(
                f"Recording started at {width}x{height} {fps} FPS",
                camera.config.name,
            )

    def set_telemetry_sync(self, sync_func: Callable[[], dict]) -> None:
        """Update telemetry synchronization function."""
        self.telemetry_sync = sync_func
        self.camera_manager.set_telemetry_sync(sync_func)

    def get_status(self) -> dict:
        """Get status of cameras and recording."""
        return {
            "recording": self.recording,
            "session_id": self.session_id,
            "cameras": self.camera_manager.health_check(),
            "active_recordings": list(self.video_logger.writers.keys()),
        }

    def start_streaming(self, camera_name: str, stream_name: str) -> bool:
        """Start streaming a camera (stream must be started in LiveStreamer first)."""
        if camera_name not in self.camera_manager.cameras:
            return False
        self.streaming_cameras[camera_name] = stream_name
        return True

    def stop_streaming(self, camera_name: str) -> None:
        """Stop streaming a camera."""
        if camera_name in self.streaming_cameras:
            del self.streaming_cameras[camera_name]

    def auto_detect_and_add_cameras(self, include_network: bool = False) -> list[str]:
        """
        Manually trigger camera auto-detection and add detected cameras.
        
        This is useful if a camera is connected after initialization.
        
        Args:
            include_network: If True, also scan for network cameras (slow)
            
        Returns:
            List of camera names that were successfully added
        """
        LOGGER.info("Manually triggering camera auto-detection (include_network=%s)", include_network)
        added = self.camera_manager.auto_detect_and_add_all(include_network=include_network)
        
        if added:
            LOGGER.info("Auto-detected and added %d camera(s): %s", len(added), ", ".join(added))
            # Start recording for newly added cameras if recording is active
            if self.recording:
                for name in added:
                    camera = self.camera_manager.get_camera(name)
                    if camera:
                        self._start_camera_recording(camera)
        else:
            LOGGER.info("No new cameras detected")
        
        return added

    def stop_all(self) -> None:
        """Stop all cameras and recording."""
        self.stop_recording()
        if self.live_streamer:
            self.live_streamer.stop_stream()
        self.streaming_cameras.clear()
        self.camera_manager.stop_all()


# Import cv2 for type hints
try:
    import cv2
    from interfaces.camera_interface import CameraInterface
except ImportError:
    cv2 = None  # type: ignore
    CameraInterface = None  # type: ignore

__all__ = ["CameraManager"]
