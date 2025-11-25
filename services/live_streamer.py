"""
Live Streaming Service

Streams video feeds to YouTube, Twitch, or other RTMP services.
Supports multiple camera selection and concurrent streaming.
"""

from __future__ import annotations

import logging
import subprocess
import threading
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

from interfaces.camera_interface import CameraInterface, Frame

# Import optimized streamer
try:
    from .optimized_streamer import OptimizedStreamer, OptimizedStreamConfig, HardwareAccel
    OPTIMIZED_STREAMER_AVAILABLE = True
except ImportError:
    OPTIMIZED_STREAMER_AVAILABLE = False
    OptimizedStreamer = None  # type: ignore
    OptimizedStreamConfig = None  # type: ignore
    HardwareAccel = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class StreamingPlatform(Enum):
    """Supported streaming platforms."""

    YOUTUBE = "youtube"
    TWITCH = "twitch"
    FACEBOOK = "facebook"
    CUSTOM_RTMP = "custom_rtmp"


@dataclass
class StreamConfig:
    """Streaming configuration."""

    platform: StreamingPlatform
    rtmp_url: str
    stream_key: str = ""
    width: int = 1920
    height: int = 1080
    fps: int = 30
    bitrate: str = "2500k"  # Video bitrate
    audio_bitrate: str = "128k"  # Audio bitrate (if audio enabled)
    preset: str = "veryfast"  # FFmpeg encoding preset
    enable_overlay: bool = True  # Enable telemetry overlay


class LiveStreamer:
    """Manages live streaming to RTMP services."""

    # Platform RTMP base URLs
    PLATFORM_URLS = {
        StreamingPlatform.YOUTUBE: "rtmp://a.rtmp.youtube.com/live2",
        StreamingPlatform.TWITCH: "rtmp://live.twitch.tv/app",
        StreamingPlatform.FACEBOOK: "rtmp://rtmp-api.facebook.com/rtmp",
    }

    def __init__(self, notification_callback: Optional[Callable[[str, str], None]] = None, use_optimized: bool = True) -> None:
        """
        Initialize live streamer.
        
        Args:
            notification_callback: Optional callback for notifications (message, level)
            use_optimized: Use optimized streamer if available (recommended)
        """
        self.notification_callback = notification_callback
        self.enabled = True
        self.use_optimized = use_optimized and OPTIMIZED_STREAMER_AVAILABLE
        self.optimized_streamer = None  # Initialize to None
        self._lock = threading.Lock()
        self.active_streams: Dict[str, subprocess.Popen] = {}
        self.stream_configs: Dict[str, StreamConfig] = {}
        self.stream_threads: Dict[str, threading.Thread] = {}
        self.running = False
        
        if cv2 is None:
            self.enabled = False
            msg = "Live streaming unavailable: OpenCV not installed"
            LOGGER.warning(msg)
            if notification_callback:
                notification_callback(msg, "warning")
            return

        # Check for FFmpeg
        if not self._check_ffmpeg():
            self.enabled = False
            msg = "Live streaming unavailable: FFmpeg not found. Install FFmpeg to enable streaming."
            LOGGER.warning(msg)
            if notification_callback:
                notification_callback(msg, "warning")
            return

        # Use optimized streamer if available
        if self.use_optimized and OPTIMIZED_STREAMER_AVAILABLE:
            try:
                self.optimized_streamer = OptimizedStreamer(notification_callback)
                LOGGER.info("Using optimized streamer with hardware acceleration")
            except Exception as e:
                LOGGER.warning(f"Failed to initialize optimized streamer: {e}")
                self.optimized_streamer = None
                self.use_optimized = False
        else:
            self.optimized_streamer = None
            LOGGER.info("Using standard streamer")

        # When everything initializes correctly, dictionaries are already set up above
    
    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                timeout=2,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def start_stream(
        self,
        camera_name: str,
        config: StreamConfig,
        frame_callback: Optional[callable] = None,
    ) -> bool:
        """
        Start streaming from a camera.

        Args:
            camera_name: Name of camera to stream
            config: Streaming configuration
            frame_callback: Optional callback to get frames

        Returns:
            True if stream started successfully
        """
        if not self.enabled:
            if self.notification_callback:
                self.notification_callback("Live streaming is disabled - check dependencies", "warning")
            return False
        if camera_name in self.active_streams:
            LOGGER.warning("Stream already active for camera: %s", camera_name)
            return False

        # Use optimized streamer if available
        if self.use_optimized and self.optimized_streamer:
            # Convert to optimized config
            opt_config = OptimizedStreamConfig(
                platform=config.platform.value,
                rtmp_url=self._build_rtmp_url(config),
                stream_key=config.stream_key,
                width=config.width,
                height=config.height,
                fps=config.fps,
                bitrate=config.bitrate,
                max_bitrate=str(int(config.bitrate.replace("k", "")) * 2) + "k",
                min_bitrate=str(int(config.bitrate.replace("k", "")) // 2) + "k",
                hardware_accel=HardwareAccel.AUTO,
                low_latency=True,
                enable_overlay=config.enable_overlay,
            )
            return self.optimized_streamer.start_stream(camera_name, opt_config, frame_callback)

        # Fallback to standard streamer
        rtmp_url = self._build_rtmp_url(config)

        try:
            ffmpeg_process = self._start_ffmpeg_stream(config, rtmp_url)
            if not ffmpeg_process:
                return False

            with self._lock:
                self.active_streams[camera_name] = ffmpeg_process
                self.stream_configs[camera_name] = config
                self.running = True

            thread = threading.Thread(
                target=self._stream_worker,
                args=(camera_name, frame_callback),
                daemon=True,
            )
            thread.start()
            self.stream_threads[camera_name] = thread

            LOGGER.info("Started streaming %s to %s", camera_name, config.platform.value)
            return True

        except Exception as e:
            LOGGER.error("Failed to start stream: %s", e)
            return False

    def stop_stream(self, camera_name: Optional[str] = None) -> None:
        """
        Stop streaming.

        Args:
            camera_name: Name of camera to stop (None = all cameras)
        """
        # Use optimized streamer if available
        if self.use_optimized and self.optimized_streamer:
            self.optimized_streamer.stop_stream(camera_name)
            return

        with self._lock:
            if camera_name:
                if camera_name in self.active_streams:
                    self._stop_stream_process(camera_name)
            else:
                # Stop all streams
                for name in list(self.active_streams.keys()):
                    self._stop_stream_process(name)
                self.running = False

    def _stop_stream_process(self, camera_name: str) -> None:
        """Stop a specific stream process."""
        if camera_name in self.active_streams:
            process = self.active_streams[camera_name]
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception as e:
                LOGGER.error("Error stopping stream %s: %s", camera_name, e)

            del self.active_streams[camera_name]
            if camera_name in self.stream_configs:
                del self.stream_configs[camera_name]
            if camera_name in self.stream_threads:
                del self.stream_threads[camera_name]

            LOGGER.info("Stopped streaming %s", camera_name)

    def _build_rtmp_url(self, config: StreamConfig) -> str:
        """Build RTMP URL from configuration."""
        if config.platform == StreamingPlatform.CUSTOM_RTMP:
            return config.rtmp_url

        base_url = self.PLATFORM_URLS.get(config.platform)
        if not base_url:
            raise ValueError(f"Unknown platform: {config.platform}")

        if config.stream_key:
            return f"{base_url}/{config.stream_key}"
        return base_url

    def _start_ffmpeg_stream(self, config: StreamConfig, rtmp_url: str) -> Optional[subprocess.Popen]:
        """Start FFmpeg process for streaming."""
        # FFmpeg command for H.264 streaming
        cmd = [
            "ffmpeg",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{config.width}x{config.height}",
            "-pix_fmt", "bgr24",
            "-r", str(config.fps),
            "-i", "-",  # Read from stdin
            "-c:v", "libx264",
            "-preset", config.preset,
            "-b:v", config.bitrate,
            "-maxrate", config.bitrate,
            "-bufsize", str(int(config.bitrate.replace("k", "")) * 2) + "k",
            "-g", str(config.fps * 2),  # GOP size
            "-f", "flv",
            rtmp_url,
        ]

        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
            )
            return process
        except FileNotFoundError:
            LOGGER.error("FFmpeg not found. Please install FFmpeg to enable streaming.")
            return None
        except Exception as e:
            LOGGER.error("Failed to start FFmpeg: %s", e)
            return None

    def _stream_worker(self, camera_name: str, frame_callback: Optional[callable]) -> None:
        """Worker thread that feeds frames to FFmpeg."""
        config = self.stream_configs.get(camera_name)
        if not config:
            return

        process = self.active_streams.get(camera_name)
        if not process or not process.stdin:
            return

        frame_count = 0
        last_fps_check = time.time()

        try:
            while camera_name in self.active_streams and process.poll() is None:
                # Get frame from callback or camera
                frame = None
                if frame_callback:
                    frame = frame_callback()

                if frame is None:
                    time.sleep(0.01)
                    continue

                # Resize if needed
                if frame.shape[:2] != (config.height, config.width):
                    frame = cv2.resize(frame, (config.width, config.height))

                # Write frame to FFmpeg stdin
                try:
                    process.stdin.write(frame.tobytes())
                    process.stdin.flush()
                except BrokenPipeError:
                    LOGGER.error("FFmpeg process ended unexpectedly for %s", camera_name)
                    break
                except Exception as e:
                    LOGGER.error("Error writing frame: %s", e)
                    break

                frame_count += 1

                # Log FPS periodically
                now = time.time()
                if now - last_fps_check > 5.0:
                    fps = frame_count / (now - last_fps_check)
                    LOGGER.debug("Streaming %s at %.1f FPS", camera_name, fps)
                    frame_count = 0
                    last_fps_check = now

        except Exception as e:
            LOGGER.error("Stream worker error for %s: %s", camera_name, e)
        finally:
            if camera_name in self.active_streams:
                self._stop_stream_process(camera_name)

    def feed_frame(self, camera_name: str, frame: "np.ndarray") -> bool:
        """
        Feed a frame to an active stream.

        Args:
            camera_name: Name of camera
            frame: Video frame (BGR format)

        Returns:
            True if frame was fed successfully
        """
        if camera_name not in self.active_streams:
            return False

        process = self.active_streams.get(camera_name)
        if not process or not process.stdin:
            return False

        try:
            config = self.stream_configs[camera_name]
            # Resize if needed
            if frame.shape[:2] != (config.height, config.width):
                frame = cv2.resize(frame, (config.width, config.height))

            process.stdin.write(frame.tobytes())
            process.stdin.flush()
            return True
        except Exception as e:
            LOGGER.error("Error feeding frame: %s", e)
            return False

    def is_streaming(self, camera_name: Optional[str] = None) -> bool:
        """Check if streaming is active."""
        if camera_name:
            return camera_name in self.active_streams
        return len(self.active_streams) > 0

    def get_stream_status(self) -> Dict[str, Dict]:
        """Get status of all active streams."""
        # Use optimized streamer if available
        if self.use_optimized and self.optimized_streamer:
            stats = self.optimized_streamer.get_stream_stats()
            return {
                name: {
                    "active": True,
                    "fps": stats.get(name, {}).get("last_fps", 0),
                    "frames_sent": stats.get(name, {}).get("frames_sent", 0),
                    "frames_dropped": stats.get(name, {}).get("frames_dropped", 0),
                }
                for name in stats.keys()
            }

        status = {}
        for camera_name, process in self.active_streams.items():
            status[camera_name] = {
                "active": process.poll() is None,
                "platform": self.stream_configs.get(camera_name, {}).platform.value if camera_name in self.stream_configs else "unknown",
            }
        return status


__all__ = ["LiveStreamer", "StreamConfig", "StreamingPlatform"]

