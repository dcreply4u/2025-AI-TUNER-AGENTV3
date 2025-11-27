"""
Optimized Live Streaming Service

High-performance, low-latency video streaming with hardware acceleration,
smart frame buffering, and adaptive bitrate.
"""

from __future__ import annotations

import logging
import platform
import subprocess
import threading
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from queue import Queue, Empty
from typing import Callable, Dict, Optional

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

LOGGER = logging.getLogger(__name__)


class HardwareAccel(Enum):
    """Hardware acceleration types."""

    NONE = "none"
    NVENC = "nvenc"  # NVIDIA
    QSV = "qsv"  # Intel QuickSync
    VIDEOTOOLBOX = "videotoolbox"  # macOS
    VAAPI = "vaapi"  # Linux
    AUTO = "auto"


@dataclass
class OptimizedStreamConfig:
    """Optimized streaming configuration."""

    platform: str
    rtmp_url: str
    stream_key: str = ""
    width: int = 1280  # Lower default for better performance
    height: int = 720
    fps: int = 30
    bitrate: str = "2000k"  # Adaptive
    max_bitrate: str = "4000k"
    min_bitrate: str = "1000k"
    hardware_accel: HardwareAccel = HardwareAccel.AUTO
    low_latency: bool = True
    buffer_size: int = 2  # Small buffer for low latency
    drop_frames: bool = True  # Drop frames if buffer full
    enable_overlay: bool = True


class OptimizedStreamer:
    """Optimized live streamer with hardware acceleration and low latency."""

    def __init__(self, notification_callback: Optional[Callable[[str, str], None]] = None) -> None:
        """
        Initialize optimized streamer.

        Args:
            notification_callback: Callback for notifications
        """
        self.notification_callback = notification_callback
        self.active_streams: Dict[str, subprocess.Popen] = {}
        self.stream_configs: Dict[str, OptimizedStreamConfig] = {}
        self.frame_queues: Dict[str, Queue] = {}
        self.stream_threads: Dict[str, threading.Thread] = {}
        self.stats: Dict[str, Dict] = {}
        self._lock = threading.Lock()

        # Detect hardware acceleration
        self.hw_accel = self._detect_hardware_accel()

    def _detect_hardware_accel(self) -> HardwareAccel:
        """Detect available hardware acceleration."""
        system = platform.system().lower()

        # Check for NVIDIA
        try:
            result = subprocess.run(
                ["nvidia-smi"],
                capture_output=True,
                timeout=1,
            )
            if result.returncode == 0:
                self._notify("NVIDIA GPU detected - using NVENC acceleration", "info")
                return HardwareAccel.NVENC
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Check for Intel QuickSync (Linux)
        if system == "linux":
            try:
                result = subprocess.run(
                    ["vainfo"],
                    capture_output=True,
                    timeout=1,
                )
                if result.returncode == 0:
                    self._notify("Intel QuickSync detected - using VAAPI acceleration", "info")
                    return HardwareAccel.VAAPI
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

        # Check for VideoToolbox (macOS)
        if system == "darwin":
            self._notify("Using VideoToolbox acceleration", "info")
            return HardwareAccel.VIDEOTOOLBOX

        self._notify("No hardware acceleration detected - using software encoding", "warning")
        return HardwareAccel.NONE

    def _notify(self, message: str, level: str = "info") -> None:
        """Send notification."""
        if self.notification_callback:
            try:
                self.notification_callback(message, level)
            except Exception:
                pass

    def start_stream(
        self,
        camera_name: str,
        config: OptimizedStreamConfig,
        frame_callback: Optional[callable] = None,
    ) -> bool:
        """
        Start optimized streaming.

        Args:
            camera_name: Camera name
            config: Stream configuration
            frame_callback: Frame callback
        """
        if camera_name in self.active_streams:
            LOGGER.warning("Stream already active: %s", camera_name)
            return False

        # Override hardware accel if auto
        if config.hardware_accel == HardwareAccel.AUTO:
            config.hardware_accel = self.hw_accel

        # Build RTMP URL
        rtmp_url = self._build_rtmp_url(config)

        # Create frame queue (small for low latency)
        frame_queue = Queue(maxsize=config.buffer_size)
        self.frame_queues[camera_name] = frame_queue

        # Start FFmpeg with optimized settings
        try:
            ffmpeg_process = self._start_optimized_ffmpeg(config, rtmp_url)
            if not ffmpeg_process:
                return False

            with self._lock:
                self.active_streams[camera_name] = ffmpeg_process
                self.stream_configs[camera_name] = config
                self.stats[camera_name] = {
                    "frames_sent": 0,
                    "frames_dropped": 0,
                    "start_time": time.time(),
                    "last_fps": 0.0,
                }

            # Start frame producer thread
            producer_thread = threading.Thread(
                target=self._frame_producer,
                args=(camera_name, frame_callback),
                daemon=True,
            )
            producer_thread.start()

            # Start frame consumer thread
            consumer_thread = threading.Thread(
                target=self._frame_consumer,
                args=(camera_name,),
                daemon=True,
            )
            consumer_thread.start()
            self.stream_threads[camera_name] = consumer_thread

            self._notify(f"Started streaming {camera_name} ({config.hardware_accel.value})", "info")
            LOGGER.info("Started optimized stream: %s", camera_name)
            return True

        except Exception as e:
            LOGGER.error("Failed to start stream: %s", e)
            self._notify(f"Stream start failed: {str(e)}", "error")
            return False

    def _parse_bitrate(self, bitrate_str: str) -> int:
        """Parse bitrate string (e.g., '2000k') to integer in kbps."""
        try:
            bitrate_str = str(bitrate_str).lower().strip()
            if bitrate_str.endswith('k'):
                return int(bitrate_str[:-1])
            elif bitrate_str.endswith('m'):
                return int(bitrate_str[:-1]) * 1000
            else:
                # Assume it's already in kbps if no suffix
                return int(bitrate_str)
        except (ValueError, AttributeError) as e:
            LOGGER.warning(f"Invalid bitrate format: {bitrate_str}, using default 2000kbps. Error: {e}")
            return 2000
    
    def _start_optimized_ffmpeg(self, config: OptimizedStreamConfig, rtmp_url: str) -> Optional[subprocess.Popen]:
        """Start FFmpeg with optimized low-latency settings."""
        # Base command
        cmd = ["ffmpeg"]

        # Input settings (raw video from stdin)
        cmd.extend([
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{config.width}x{config.height}",
            "-pix_fmt", "bgr24",
            "-r", str(config.fps),
            "-i", "-",
        ])

        # Hardware acceleration encoding
        if config.hardware_accel == HardwareAccel.NVENC:
            cmd.extend([
                "-c:v", "h264_nvenc",
                "-preset", "llhp",  # Low latency high performance
                "-tune", "ll",
                "-rc", "vbr",
                "-b:v", config.bitrate,
                "-maxrate", config.max_bitrate,
                "-bufsize", str(self._parse_bitrate(config.bitrate) * 2) + "k",
                "-gpu", "0",
            ])
        elif config.hardware_accel == HardwareAccel.VAAPI:
            cmd.extend([
                "-vaapi_device", "/dev/dri/renderD128",
                "-vf", f"format=nv12,hwupload",
                "-c:v", "h264_vaapi",
                "-b:v", config.bitrate,
                "-maxrate", config.max_bitrate,
                "-bufsize", str(self._parse_bitrate(config.bitrate) * 2) + "k",
            ])
        elif config.hardware_accel == HardwareAccel.VIDEOTOOLBOX:
            cmd.extend([
                "-c:v", "h264_videotoolbox",
                "-b:v", config.bitrate,
                "-maxrate", config.max_bitrate,
                "-allow_sw", "1",
            ])
        else:
            # Software encoding with ultra-fast preset
            cmd.extend([
                "-c:v", "libx264",
                "-preset", "ultrafast",  # Fastest encoding
                "-tune", "zerolatency",  # Zero latency tuning
                "-profile:v", "baseline",  # Baseline profile for compatibility
                "-b:v", config.bitrate,
                "-maxrate", config.max_bitrate,
                "-bufsize", str(self._parse_bitrate(config.bitrate) * 1) + "k",  # Smaller buffer
                "-g", str(config.fps),  # GOP = 1 second
                "-keyint_min", str(config.fps),  # Keyframe every second
            ])

        # Low latency settings
        if config.low_latency:
            cmd.extend([
                "-flags", "+low_delay",
                "-strict", "experimental",
                "-fflags", "+nobuffer+flush_packets",
                "-flush_packets", "1",
            ])

        # Output settings
        cmd.extend([
            "-f", "flv",
            "-flvflags", "no_duration_filesize",
            rtmp_url,
        ])

        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,  # Unbuffered for low latency
            )

            # Start error monitoring thread
            threading.Thread(
                target=self._monitor_ffmpeg_errors,
                args=(camera_name, process),
                daemon=True,
            ).start()

            return process
        except Exception as e:
            LOGGER.error("Failed to start FFmpeg: %s", e)
            return None

    def _frame_producer(self, camera_name: str, frame_callback: Optional[callable]) -> None:
        """Producer thread: captures frames and adds to queue."""
        queue = self.frame_queues.get(camera_name)
        if not queue:
            return

        target_fps = self.stream_configs.get(camera_name)
        if not target_fps:
            return
        target_fps = target_fps.fps

        frame_interval = 1.0 / target_fps
        last_frame_time = time.time()

        while camera_name in self.active_streams:
            try:
                # Get frame from callback
                frame = None
                if frame_callback:
                    frame = frame_callback()

                if frame is None:
                    time.sleep(0.001)  # Small sleep to avoid busy wait
                    continue

                # Frame rate limiting
                now = time.time()
                elapsed = now - last_frame_time
                if elapsed < frame_interval:
                    time.sleep(frame_interval - elapsed)

                # Try to add to queue (non-blocking)
                try:
                    queue.put_nowait(frame)
                    last_frame_time = time.time()
                except:
                    # Queue full - drop frame if enabled
                    if self.stream_configs.get(camera_name, OptimizedStreamConfig("", "")).drop_frames:
                        if camera_name in self.stats:
                            self.stats[camera_name]["frames_dropped"] += 1
                    else:
                        # Block until space available
                        queue.put(frame, timeout=0.1)
                        last_frame_time = time.time()

            except Exception as e:
                LOGGER.error("Frame producer error for %s: %s", camera_name, e)
                time.sleep(0.01)

    def _frame_consumer(self, camera_name: str) -> None:
        """Consumer thread: reads from queue and sends to FFmpeg."""
        queue = self.frame_queues.get(camera_name)
        process = self.active_streams.get(camera_name)
        config = self.stream_configs.get(camera_name)

        if not queue or not process or not config:
            return

        frame_count = 0
        last_stats_time = time.time()

        try:
            while camera_name in self.active_streams and process.poll() is None:
                try:
                    # Get frame with timeout
                    frame = queue.get(timeout=0.1)
                except Empty:
                    continue

                # Validate frame is a numpy array
                if not isinstance(frame, np.ndarray) or len(frame.shape) < 2:
                    LOGGER.warning("Invalid frame format for %s", camera_name)
                    continue
                
                # Resize if needed (optimized)
                if frame.shape[:2] != (config.height, config.width):
                    frame = cv2.resize(frame, (config.width, config.height), interpolation=cv2.INTER_LINEAR)

                # Write to FFmpeg (non-blocking check first)
                if process.stdin and not process.stdin.closed:
                    try:
                        process.stdin.write(frame.tobytes())
                        process.stdin.flush()

                        frame_count += 1
                        if camera_name in self.stats:
                            self.stats[camera_name]["frames_sent"] += 1

                    except BrokenPipeError:
                        LOGGER.error("FFmpeg pipe broken for %s", camera_name)
                        break
                    except Exception as e:
                        LOGGER.error("Error writing frame: %s", e)
                        break

                # Update stats
                now = time.time()
                if now - last_stats_time > 5.0:
                    if camera_name in self.stats:
                        elapsed = now - last_stats_time
                        fps = frame_count / elapsed if elapsed > 0 else 0
                        self.stats[camera_name]["last_fps"] = fps
                        LOGGER.debug("Stream %s: %.1f FPS, %d dropped", camera_name, fps, self.stats[camera_name]["frames_dropped"])
                    frame_count = 0
                    last_stats_time = now

        except Exception as e:
            LOGGER.error("Frame consumer error for %s: %s", camera_name, e)
        finally:
            if camera_name in self.active_streams:
                self._stop_stream(camera_name)

    def _monitor_ffmpeg_errors(self, camera_name: str, process: subprocess.Popen) -> None:
        """Monitor FFmpeg stderr for errors."""
        if not process.stderr:
            return

        try:
            for line in iter(process.stderr.readline, b""):
                line_str = line.decode("utf-8", errors="ignore").strip()
                if line_str:
                    if "error" in line_str.lower() or "failed" in line_str.lower():
                        LOGGER.error("FFmpeg error for %s: %s", camera_name, line_str)
                        self._notify(f"Stream error: {line_str[:50]}", "error")
        except Exception:
            pass

    def _build_rtmp_url(self, config: OptimizedStreamConfig) -> str:
        """Build RTMP URL."""
        if config.stream_key:
            return f"{config.rtmp_url}/{config.stream_key}"
        return config.rtmp_url

    def stop_stream(self, camera_name: Optional[str] = None) -> None:
        """Stop streaming."""
        with self._lock:
            if camera_name:
                self._stop_stream(camera_name)
            else:
                for name in list(self.active_streams.keys()):
                    self._stop_stream(name)

    def _stop_stream(self, camera_name: str) -> None:
        """Stop a specific stream and clean up all resources."""
        if camera_name not in self.active_streams:
            LOGGER.warning(f"Stream {camera_name} not found in active streams")
            return
        
        process = self.active_streams[camera_name]
        try:
            # Close stdin to signal FFmpeg to stop gracefully
            if process.stdin:
                try:
                    process.stdin.close()
                except Exception as e:
                    LOGGER.debug(f"Error closing stdin for {camera_name}: {e}")
            
            # Terminate process gracefully
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate
                LOGGER.warning(f"Stream {camera_name} didn't terminate, forcing kill")
                try:
                    process.kill()
                    process.wait(timeout=2)
                except Exception as e:
                    LOGGER.error(f"Error killing stream process {camera_name}: {e}")
            
            # Close stdout and stderr pipes
            if process.stdout:
                try:
                    process.stdout.close()
                except Exception:
                    pass
            if process.stderr:
                try:
                    process.stderr.close()
                except Exception:
                    pass
                    
        except Exception as e:
            LOGGER.error("Error stopping stream %s: %s", camera_name, e)
            # Force cleanup even if there was an error
            try:
                if process and process.poll() is None:  # Process still running
                    process.kill()
            except Exception:
                pass

        # Clean up references (always, even if process cleanup failed)
        try:
            del self.active_streams[camera_name]
        except KeyError:
            pass
        if camera_name in self.stream_configs:
            del self.stream_configs[camera_name]
        if camera_name in self.frame_queues:
            del self.frame_queues[camera_name]
        if camera_name in self.stream_threads:
            del self.stream_threads[camera_name]

        LOGGER.info("Stopped stream: %s", camera_name)

    def get_stream_stats(self, camera_name: Optional[str] = None) -> Dict:
        """Get streaming statistics."""
        if camera_name:
            return self.stats.get(camera_name, {})
        return dict(self.stats)

    def feed_frame(self, camera_name: str, frame: "np.ndarray") -> bool:
        """Feed a frame directly (alternative to callback)."""
        queue = self.frame_queues.get(camera_name)
        if not queue:
            return False

        try:
            queue.put_nowait(frame)
            return True
        except:
            # Queue full
            if camera_name in self.stats:
                self.stats[camera_name]["frames_dropped"] += 1
            return False


__all__ = ["OptimizedStreamer", "OptimizedStreamConfig", "HardwareAccel"]

