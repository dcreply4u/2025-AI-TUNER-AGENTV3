"""
Camera Interface Module

Supports multiple camera sources:
- USB cameras (UVC) - Auto-detected
- RTSP/HTTP streams (WiFi cameras) - Auto-detected
- CSI cameras (Raspberry Pi) - Auto-detected

Automatically detects and configures cameras with optimal settings.
Provides unified interface for video capture with telemetry synchronization.
"""

from __future__ import annotations

import logging
import os
import queue
import re
import socket
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, List, Optional

try:
    import cv2
except ImportError:
    cv2 = None  # type: ignore

try:
    import numpy as np
except ImportError:
    np = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class CameraType(Enum):
    """Camera source types."""

    USB = "usb"
    RTSP = "rtsp"
    HTTP = "http"
    CSI = "csi"


@dataclass
class CameraConfig:
    """Camera configuration."""

    name: str
    camera_type: CameraType
    source: str  # device path, RTSP URL, or HTTP URL
    width: int = 1920
    height: int = 1080
    fps: int = 30
    enabled: bool = True
    position: str = "front"  # front, rear, or other


@dataclass
class Frame:
    """Video frame with metadata."""

    image: "np.ndarray"  # type: ignore
    timestamp: float
    frame_number: int
    camera_name: str
    telemetry_sync: Optional[dict] = None


@dataclass
class DetectedCamera:
    """Detected camera information."""

    name: str
    camera_type: CameraType
    source: str
    width: int
    height: int
    fps: int
    position: str = "unknown"
    capabilities: dict = None  # type: ignore

    def __post_init__(self) -> None:
        if self.capabilities is None:
            self.capabilities = {}


class CameraAutoDetector:
    """Automatically detects and configures cameras."""

    @staticmethod
    def detect_all_cameras(include_network: bool = False) -> List[DetectedCamera]:
        """
        Automatically detect all available cameras.

        Args:
            include_network: If True, scan network for cameras (slow, can spam errors)

        Returns:
            List of detected camera configurations
        """
        LOGGER.info("Starting camera auto-detection (include_network=%s)", include_network)
        start_time = time.time()
        cameras = []
        
        LOGGER.debug("Detecting USB cameras...")
        usb_cameras = CameraAutoDetector._detect_usb_cameras()
        cameras.extend(usb_cameras)
        LOGGER.info("Found %d USB camera(s)", len(usb_cameras))
        
        LOGGER.debug("Detecting CSI cameras...")
        csi_cameras = CameraAutoDetector._detect_csi_cameras()
        cameras.extend(csi_cameras)
        LOGGER.info("Found %d CSI camera(s)", len(csi_cameras))
        
        if include_network:
            LOGGER.debug("Detecting network cameras...")
            network_cameras = CameraAutoDetector._detect_network_cameras()
            cameras.extend(network_cameras)
            LOGGER.info("Found %d network camera(s)", len(network_cameras))
        else:
            LOGGER.debug("Skipping network camera detection (include_network=False)")
        
        elapsed = time.time() - start_time
        LOGGER.info("Camera auto-detection complete: %d total cameras found in %.2fs", len(cameras), elapsed)
        return cameras

    @staticmethod
    def _detect_usb_cameras() -> List[DetectedCamera]:
        """Detect USB/UVC cameras."""
        cameras = []
        if cv2 is None:
            return cameras

        # Scan /dev/video* devices
        video_devices = sorted(Path("/dev").glob("video*"))
        if not video_devices:
            # Try Windows-style detection
            import sys
            import os
            old_stderr = sys.stderr
            for i in range(10):  # Check first 10 indices
                try:
                    # Suppress OpenCV errors during detection
                    sys.stderr = open(os.devnull, 'w')
                    cap = cv2.VideoCapture(i)
                    if cap.isOpened():
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
                        cap.release()

                        # Determine position based on device index
                        position = "front" if i == 0 else "rear" if i == 1 else f"camera{i}"

                        cameras.append(
                            DetectedCamera(
                                name=f"USB Camera {i}",
                                camera_type=CameraType.USB,
                                source=str(i),
                                width=width or 1920,
                                height=height or 1080,
                                fps=fps or 30,
                                position=position,
                            )
                        )
                except Exception:
                    pass  # Camera not available, skip
                finally:
                    sys.stderr.close()
                    sys.stderr = old_stderr
            return cameras

        # Linux: Check each /dev/video* device
        # Limit to first 10 devices to avoid long timeouts on non-existent devices
        checked_count = 0
        max_devices_to_check = 10
        
        for video_dev in video_devices:
            if checked_count >= max_devices_to_check:
                LOGGER.debug("Reached max device check limit (%d), stopping camera detection", max_devices_to_check)
                break
                
            try:
                # Extract device index
                match = re.search(r"video(\d+)", str(video_dev))
                if not match:
                    continue

                dev_idx = int(match.group(1))
                
                # Skip high-numbered devices (likely not cameras) to speed up detection
                if dev_idx > 10:
                    LOGGER.debug("Skipping high-numbered device video%d (likely not a camera)", dev_idx)
                    continue
                
                # Skip if it's a metadata device (videoX usually has videoX and videoXmeta)
                # Only check the main video device, not metadata
                if "meta" in str(video_dev).lower():
                    continue
                
                checked_count += 1
                
                # Suppress OpenCV errors during detection
                import sys
                import os
                old_stderr = sys.stderr
                cap = None
                try:
                    sys.stderr = open(os.devnull, 'w')
                    # Set very short timeout to avoid long waits
                    # Try opening with different backends for better compatibility
                    cap = cv2.VideoCapture(dev_idx, cv2.CAP_V4L2)
                    # Set timeout properties if available
                    try:
                        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 500)  # 500ms timeout
                        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 500)  # 500ms timeout
                    except Exception:
                        pass  # Some backends don't support timeout
                    
                    if not cap.isOpened():
                        # Try without specifying backend
                        if cap:
                            cap.release()
                        cap = cv2.VideoCapture(dev_idx)
                        try:
                            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 500)
                            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 500)
                        except Exception:
                            pass
                    
                    if not cap.isOpened():
                        sys.stderr.close()
                        sys.stderr = old_stderr
                        continue
                    
                    # Try to read a frame to verify camera is actually working (with timeout)
                    # Use threading to enforce timeout
                    import threading
                    frame_result = [None, None]
                    frame_read = threading.Event()
                    
                    def read_frame():
                        try:
                            frame_result[0], frame_result[1] = cap.read()
                        except Exception:
                            pass
                        finally:
                            frame_read.set()
                    
                    read_thread = threading.Thread(target=read_frame, daemon=True)
                    read_thread.start()
                    frame_read.wait(timeout=0.5)  # 500ms timeout
                    
                    if not frame_read.is_set() or not frame_result[0]:
                        # Camera opened but can't read frames - might be a metadata device
                        cap.release()
                        sys.stderr.close()
                        sys.stderr = old_stderr
                        continue
                    
                    sys.stderr.close()
                    sys.stderr = old_stderr
                except Exception as e:
                    if cap:
                        try:
                            cap.release()
                        except Exception:
                            pass
                    if sys.stderr != old_stderr:
                        try:
                            sys.stderr.close()
                        except Exception:
                            pass
                    sys.stderr = old_stderr
                    LOGGER.debug("Error testing camera device %s: %s", video_dev, e)
                    continue

                # Get capabilities
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080
                fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
                
                # If dimensions are 0, try to set and get a common resolution
                if width == 0 or height == 0:
                    for test_w, test_h in [(1920, 1080), (1280, 720), (640, 480)]:
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, test_w)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, test_h)
                        actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        if actual_w > 0 and actual_h > 0:
                            width, height = actual_w, actual_h
                            break

                # Try to get device name from udev
                device_name = CameraAutoDetector._get_device_name(video_dev)

                # Determine position
                position = "front" if dev_idx == 0 else "rear" if dev_idx == 1 else f"camera{dev_idx}"

                cameras.append(
                    DetectedCamera(
                        name=device_name or f"USB Camera {dev_idx}",
                        camera_type=CameraType.USB,
                        source=str(dev_idx),
                        width=width or 1920,
                        height=height or 1080,
                        fps=fps or 30,
                        position=position,
                        capabilities={
                            "device_path": str(video_dev),
                            "backend": cap.getBackendName(),
                        },
                    )
                )

                cap.release()
            except Exception as e:
                LOGGER.debug("Error detecting USB camera %s: %s", video_dev, e)
                continue

        return cameras

    @staticmethod
    def _detect_csi_cameras() -> List[DetectedCamera]:
        """Detect CSI cameras (Raspberry Pi)."""
        cameras = []
        if cv2 is None:
            return cameras

        # Check if we're on a Raspberry Pi
        try:
            if not Path("/proc/device-tree/model").exists():
                return cameras

            model = Path("/proc/device-tree/model").read_text().lower()
            if "raspberry pi" not in model:
                return cameras
        except Exception:
            return cameras

        # Try to detect CSI cameras (typically sensor-id 0 and 1)
        for sensor_id in [0, 1]:
            try:
                # Try GStreamer pipeline
                pipeline = (
                    f"nvarguscamerasrc sensor-id={sensor_id} ! "
                    "video/x-raw(memory:NVMM), width=1920, height=1080, framerate=30/1 ! "
                    "nvvidconv ! video/x-raw, width=1920, height=1080 ! "
                    "videoconvert ! appsink"
                )
                cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

                if cap.isOpened():
                    # Test read
                    ret, _ = cap.read()
                    if ret:
                        position = "front" if sensor_id == 0 else "rear"
                        cameras.append(
                            DetectedCamera(
                                name=f"CSI Camera {sensor_id}",
                                camera_type=CameraType.CSI,
                                source=str(sensor_id),
                                width=1920,
                                height=1080,
                                fps=30,
                                position=position,
                            )
                        )
                    cap.release()
            except Exception as e:
                LOGGER.debug("Error detecting CSI camera %d: %s", sensor_id, e)
                continue

        return cameras

    @staticmethod
    def _detect_network_cameras() -> List[DetectedCamera]:
        """Detect RTSP/HTTP network cameras."""
        cameras = []
        
        # Check if demo mode is active
        import os
        is_demo_mode = os.environ.get("AITUNER_DEMO_MODE", "false").lower() == "true"
        if is_demo_mode:
            LOGGER.info("Skipping network camera detection - demo mode active")
            return cameras

        LOGGER.info("Starting network camera detection...")
        start_time = time.time()

        # Common RTSP ports and paths
        rtsp_ports = [554, 8554]
        rtsp_paths = ["/stream", "/live", "/h264", "/video", "/cam"]

        # Common HTTP/MJPEG paths
        http_ports = [80, 8080, 8081]
        http_paths = ["/mjpeg", "/video", "/stream", "/cam", "/webcam"]

        # Try to discover cameras on local network
        # This is a simplified version - in production, you might use UPnP or mDNS
        local_ip = CameraAutoDetector._get_local_ip()
        
        if not local_ip:
            LOGGER.warning("Could not determine local IP address - skipping network camera detection")
            return cameras

        LOGGER.info("Local IP detected: %s - scanning network for cameras", local_ip)
        
        # Check common IP camera ranges
        base_ips = [local_ip.rsplit(".", 1)[0] + ".", "192.168.1.", "192.168.0."]
        total_ips_to_scan = sum(254 for _ in base_ips)
        scanned_count = 0
        found_count = 0

        for base_ip in base_ips:
            LOGGER.debug("Scanning IP range: %s*", base_ip)
            for last_octet in range(1, 255):
                ip = base_ip + str(last_octet)
                if ip == local_ip:
                    continue
                
                scanned_count += 1
                if scanned_count % 50 == 0:
                    LOGGER.debug("Network scan progress: %d/%d IPs scanned, %d cameras found", 
                                scanned_count, total_ips_to_scan, found_count)

                # Try RTSP
                for port in rtsp_ports:
                    for path in rtsp_paths:
                        url = f"rtsp://{ip}:{port}{path}"
                        if CameraAutoDetector._test_rtsp_url(url, timeout=0.3):  # Very short timeout for scanning
                            cameras.append(
                                DetectedCamera(
                                    name=f"RTSP Camera {ip}",
                                    camera_type=CameraType.RTSP,
                                    source=url,
                                    width=1920,
                                    height=1080,
                                    fps=30,
                                    position="network",
                                )
                            )
                            found_count += 1
                            LOGGER.info("Found RTSP camera: %s at %s", ip, url)
                            break

                # Try HTTP/MJPEG
                for port in http_ports:
                    for path in http_paths:
                        url = f"http://{ip}:{port}{path}"
                        if CameraAutoDetector._test_http_url(url, timeout=0.3):  # Very short timeout for scanning
                            cameras.append(
                                DetectedCamera(
                                    name=f"HTTP Camera {ip}",
                                    camera_type=CameraType.HTTP,
                                    source=url,
                                    width=1920,
                                    height=1080,
                                    fps=30,
                                    position="network",
                                )
                            )
                            found_count += 1
                            LOGGER.info("Found HTTP camera: %s at %s", ip, url)
                            break

        elapsed = time.time() - start_time
        LOGGER.info("Network camera detection complete: scanned %d IPs, found %d cameras in %.2fs", 
                   scanned_count, found_count, elapsed)
        return cameras

    @staticmethod
    def _test_rtsp_url(url: str, timeout: float = 0.5) -> bool:
        """Test if RTSP URL is accessible."""
        if cv2 is None:
            return False

        # Skip network camera tests in demo mode
        import os
        is_demo_mode = os.environ.get("AITUNER_DEMO_MODE", "false").lower() == "true"
        if is_demo_mode:
            return False

        try:
            # Suppress OpenCV errors
            old_stderr = sys.stderr
            try:
                sys.stderr = open(os.devnull, 'w')
                cap = cv2.VideoCapture(url)
                if cap.isOpened():
                    # Set very short timeout to prevent long waits
                    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout * 1000)
                    cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, timeout * 1000)
                    ret, _ = cap.read()
                    cap.release()
                    sys.stderr.close()
                    sys.stderr = old_stderr
                    return ret
                sys.stderr.close()
                sys.stderr = old_stderr
            except Exception:
                if sys.stderr != old_stderr:
                    try:
                        sys.stderr.close()
                    except Exception:
                        pass
                sys.stderr = old_stderr
        except Exception:
            pass
        return False

    @staticmethod
    def _test_http_url(url: str, timeout: float = 0.5) -> bool:
        """Test if HTTP/MJPEG URL is accessible."""
        if cv2 is None:
            LOGGER.debug("OpenCV not available, skipping HTTP test for %s", url)
            return False

        # Skip network camera tests in demo mode
        import os
        is_demo_mode = os.environ.get("AITUNER_DEMO_MODE", "false").lower() == "true"
        if is_demo_mode:
            LOGGER.debug("Demo mode active - skipping HTTP test for %s", url)
            return False

        LOGGER.debug("Testing HTTP URL: %s (timeout: %.1fs)", url, timeout)
        start_time = time.time()
        
        try:
            # Suppress OpenCV errors
            old_stderr = sys.stderr
            try:
                sys.stderr = open(os.devnull, 'w')
                cap = cv2.VideoCapture(url)
                if cap.isOpened():
                    # Set very short timeout to prevent long waits
                    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout * 1000)
                    cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, timeout * 1000)
                    LOGGER.debug("HTTP connection opened, attempting to read frame from %s", url)
                    ret, _ = cap.read()
                    elapsed = time.time() - start_time
                    cap.release()
                    sys.stderr.close()
                    sys.stderr = old_stderr
                    if ret:
                        LOGGER.info("HTTP URL accessible: %s (tested in %.2fs)", url, elapsed)
                    else:
                        LOGGER.debug("HTTP URL opened but frame read failed: %s (tested in %.2fs)", url, elapsed)
                    return ret
                else:
                    elapsed = time.time() - start_time
                    LOGGER.debug("HTTP URL failed to open: %s (tested in %.2fs)", url, elapsed)
                sys.stderr.close()
                sys.stderr = old_stderr
            except Exception as e:
                elapsed = time.time() - start_time
                if sys.stderr != old_stderr:
                    try:
                        sys.stderr.close()
                    except Exception:
                        pass
                sys.stderr = old_stderr
                LOGGER.debug("HTTP test exception for %s: %s (tested in %.2fs)", url, e, elapsed)
        except Exception as e:
            elapsed = time.time() - start_time
            LOGGER.debug("HTTP test outer exception for %s: %s (tested in %.2fs)", url, e, elapsed)
        return False

    @staticmethod
    def _get_device_name(device_path: Path) -> Optional[str]:
        """Get human-readable device name from udev."""
        try:
            # Try to get device info from udev
            result = subprocess.run(
                ["udevadm", "info", "--query=property", "--name", str(device_path)],
                capture_output=True,
                text=True,
                timeout=1.0,
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if line.startswith("ID_MODEL="):
                        return line.split("=", 1)[1].replace("_", " ")
        except Exception:
            pass
        return None

    @staticmethod
    def _get_local_ip() -> Optional[str]:
        """Get local IP address."""
        try:
            # Connect to a remote address to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return None

    @staticmethod
    def auto_configure_camera(detected: DetectedCamera) -> CameraConfig:
        """
        Auto-configure camera with optimal settings.

        Args:
            detected: Detected camera information

        Returns:
            CameraConfig with optimal settings
        """
        # Determine optimal resolution based on camera capabilities
        width = detected.width
        height = detected.height
        fps = detected.fps

        # If camera reports 0x0, try common resolutions
        if width == 0 or height == 0:
            # Try to probe actual capabilities
            if cv2:
                cap = cv2.VideoCapture(int(detected.source) if detected.source.isdigit() else 0)
                if cap.isOpened():
                    # Try common resolutions
                    for test_w, test_h in [(1920, 1080), (1280, 720), (640, 480)]:
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, test_w)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, test_h)
                        actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        if actual_w == test_w and actual_h == test_h:
                            width, height = test_w, test_h
                            break
                    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
                    cap.release()

        # Fallback to reasonable defaults
        if width == 0 or height == 0:
            width, height = 1920, 1080
        if fps == 0:
            fps = 30

        return CameraConfig(
            name=detected.name,
            camera_type=detected.camera_type,
            source=detected.source,
            width=width,
            height=height,
            fps=fps,
            enabled=True,
            position=detected.position,
        )


class CameraInterface:
    """Unified camera interface for multiple source types."""

    def __init__(
        self,
        config: CameraConfig,
        frame_callback: Optional[Callable[[Frame], None]] = None,
    ) -> None:
        """
        Initialize camera interface.

        Args:
            config: Camera configuration
            frame_callback: Optional callback for each captured frame
        """
        if cv2 is None:
            raise RuntimeError("OpenCV (cv2) is required for camera support. Install with: pip install opencv-python")

        self.config = config
        self.frame_callback = frame_callback
        self.cap: Optional["cv2.VideoCapture"] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.frame_queue: queue.Queue[Frame] = queue.Queue(maxsize=30)
        self.frame_count = 0
        self.last_frame_time = 0.0
        self._lock = threading.Lock()

    def start(self) -> bool:
        """Start camera capture with automatic configuration."""
        if self.running:
            return True

        # Don't start if disabled
        if not self.config.enabled:
            return False

        # Skip network cameras in demo/simulated mode to prevent connection errors
        import os
        is_demo_mode = os.environ.get("AITUNER_DEMO_MODE", "false").lower() == "true"
        if is_demo_mode and self.config.camera_type in (CameraType.RTSP, CameraType.HTTP):
            LOGGER.info("Skipping network camera in demo mode: %s (%s) - %s", 
                       self.config.name, self.config.camera_type.value, self.config.source)
            return False
        
        LOGGER.info("Starting camera: %s (type: %s, source: %s, enabled: %s)", 
                   self.config.name, self.config.camera_type.value, self.config.source, self.config.enabled)

        try:
            # Suppress OpenCV errors for missing cameras
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                old_stderr = sys.stderr
                try:
                    sys.stderr = open(os.devnull, 'w')
                    self.cap = self._open_camera()
                    sys.stderr = old_stderr
                except Exception:
                    sys.stderr = old_stderr
                    self.cap = None
                    
            if self.cap is None or not self.cap.isOpened():
                LOGGER.warning("Camera not available: %s (type: %s, source: %s) - this is normal if no camera connected", 
                              self.config.name, self.config.camera_type.value, self.config.source)
                return False

            LOGGER.debug("Camera opened successfully: %s", self.config.name)
            
            # Auto-configure optimal settings
            LOGGER.debug("Auto-configuring camera settings for: %s", self.config.name)
            self._auto_configure_settings()

            # Verify actual settings
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS)) or self.config.fps

            # Update config with actual values
            self.config.width = actual_width if actual_width > 0 else self.config.width
            self.config.height = actual_height if actual_height > 0 else self.config.height
            self.config.fps = actual_fps if actual_fps > 0 else self.config.fps

            LOGGER.debug("Camera settings verified: %s - %dx%d @ %dfps (requested: %dx%d @ %dfps)",
                        self.config.name, actual_width, actual_height, actual_fps,
                        self.config.width, self.config.height, self.config.fps)

            self.running = True
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            LOGGER.info(
                "Camera started successfully: %s (%s) - %dx%d @ %dfps",
                self.config.name,
                self.config.source,
                self.config.width,
                self.config.height,
                self.config.fps,
            )
            return True
        except Exception as e:
            LOGGER.error("Error starting camera %s: %s", self.config.name, e)
            return False

    def _auto_configure_settings(self) -> None:
        """Auto-configure camera settings for optimal performance."""
        if self.cap is None:
            return

        # Set desired resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)

        # Try to set FPS (may not work for all cameras)
        self.cap.set(cv2.CAP_PROP_FPS, self.config.fps)

        # Auto-focus (if supported)
        try:
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
        except Exception:
            pass

        # Auto-exposure (if supported)
        try:
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)  # Auto mode
        except Exception:
            pass

        # Buffer size (reduce latency)
        try:
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass

    def stop(self) -> None:
        """Stop camera capture."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

        if self.cap:
            self.cap.release()
            self.cap = None

        LOGGER.info("Camera stopped: %s", self.config.name)

    def get_frame(self, timeout: float = 1.0) -> Optional[Frame]:
        """Get latest frame from queue."""
        try:
            return self.frame_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def _open_camera(self) -> Optional["cv2.VideoCapture"]:
        """Open camera based on type."""
        if self.config.camera_type == CameraType.USB:
            # USB camera: source is device index or path
            try:
                device_idx = int(self.config.source) if self.config.source.isdigit() else int(self.config.source.split("/")[-1])
                # Suppress OpenCV errors
                import os
                import sys
                # Redirect stderr temporarily to suppress camera errors
                old_stderr = sys.stderr
                try:
                    sys.stderr = open(os.devnull, 'w')
                    cap = cv2.VideoCapture(device_idx)
                    if not cap.isOpened():
                        cap = None
                    sys.stderr.close()
                    sys.stderr = old_stderr
                    return cap
                except Exception:
                    if sys.stderr != old_stderr:
                        try:
                            sys.stderr.close()
                        except Exception:
                            pass
                    sys.stderr = old_stderr
                    return None
            except (ValueError, IndexError):
                # Try as direct path
                try:
                    import os
                    import sys
                    old_stderr = sys.stderr
                    try:
                        sys.stderr = open(os.devnull, 'w')
                        cap = cv2.VideoCapture(self.config.source)
                        if not cap.isOpened():
                            cap = None
                        sys.stderr.close()
                        sys.stderr = old_stderr
                        return cap
                    except Exception:
                        if sys.stderr != old_stderr:
                            try:
                                sys.stderr.close()
                            except Exception:
                                pass
                        sys.stderr = old_stderr
                        return None
                except Exception:
                    return None

        elif self.config.camera_type == CameraType.RTSP:
            # RTSP stream - set short timeout to fail fast
            LOGGER.debug("Opening RTSP camera: %s", self.config.source)
            cap = cv2.VideoCapture(self.config.source)
            if cap.isOpened():
                # Set very short timeout to prevent long waits
                cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 2000)  # 2 seconds
                cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 2000)  # 2 seconds
                LOGGER.debug("RTSP camera opened with 2s timeout: %s", self.config.source)
            else:
                LOGGER.warning("Failed to open RTSP camera: %s", self.config.source)
            return cap

        elif self.config.camera_type == CameraType.HTTP:
            # HTTP/MJPEG stream - set short timeout to fail fast
            LOGGER.debug("Opening HTTP camera: %s", self.config.source)
            cap = cv2.VideoCapture(self.config.source)
            if cap.isOpened():
                # Set very short timeout to prevent long waits
                cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 2000)  # 2 seconds
                cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 2000)  # 2 seconds
                LOGGER.debug("HTTP camera opened with 2s timeout: %s", self.config.source)
            else:
                LOGGER.warning("Failed to open HTTP camera: %s", self.config.source)
            return cap

        elif self.config.camera_type == CameraType.CSI:
            # CSI camera (Raspberry Pi)
            # GStreamer pipeline for CSI
            pipeline = (
                f"nvarguscamerasrc sensor-id={self.config.source} ! "
                "video/x-raw(memory:NVMM), width=1920, height=1080, framerate=30/1 ! "
                "nvvidconv flip-method=0 ! video/x-raw, width=1920, height=1080 ! "
                "videoconvert ! appsink"
            )
            return cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

        return None

    def _capture_loop(self) -> None:
        """Main capture loop running in background thread - OPTIMIZED."""
        # Pre-allocate frame buffer to avoid memory allocation
        target_interval = 1.0 / self.config.fps
        last_frame_time = 0.0

        while self.running and self.cap and self.cap.isOpened():
            try:
                # Use grab() + retrieve() for better performance
                if not self.cap.grab():
                    time.sleep(0.01)
                    continue

                ret, frame = self.cap.retrieve()
                if not ret or frame is None:
                    LOGGER.warning("Failed to retrieve frame from %s", self.config.name)
                    time.sleep(0.01)
                    continue

                timestamp = time.time()
                self.frame_count += 1

                # Only create frame object if needed (optimization)
                if self.frame_callback or not self.frame_queue.empty():
                    frame_obj = Frame(
                        image=frame,
                        timestamp=timestamp,
                        frame_number=self.frame_count,
                        camera_name=self.config.name,
                    )

                    # Add to queue (drop oldest if full - non-blocking)
                    try:
                        self.frame_queue.put_nowait(frame_obj)
                    except queue.Full:
                        try:
                            self.frame_queue.get_nowait()  # Remove oldest
                            self.frame_queue.put_nowait(frame_obj)
                        except queue.Empty:
                            pass

                    # Call callback if provided
                    if self.frame_callback:
                        try:
                            self.frame_callback(frame_obj)
                        except Exception as e:
                            LOGGER.error("Error in frame callback: %s", e)

                self.last_frame_time = timestamp

                # Optimized frame rate limiting
                elapsed = time.time() - timestamp
                sleep_time = target_interval - elapsed
                if sleep_time > 0.001:  # Only sleep if significant
                    time.sleep(sleep_time)
                elif sleep_time < -0.1:  # Falling behind
                    # Skip frame if too far behind
                    if self.frame_count % 2 == 0:
                        continue

            except Exception as e:
                LOGGER.error("Error in capture loop for %s: %s", self.config.name, e)
                time.sleep(0.01)  # Shorter sleep on error

    def is_healthy(self, timeout: float = 5.0) -> bool:
        """Check if camera is healthy (receiving frames)."""
        return (time.time() - self.last_frame_time) < timeout


class CameraManager:
    """Manages multiple camera interfaces with automatic detection."""

    def __init__(self, auto_detect: bool = True, include_network: bool = False) -> None:
        """
        Initialize camera manager.

        Args:
            auto_detect: If True, automatically detect and add all cameras on initialization
            include_network: If True, scan network for cameras (slow, can spam errors)
        """
        LOGGER.info("Initializing CameraManager (auto_detect=%s, include_network=%s)", auto_detect, include_network)
        self.cameras: dict[str, CameraInterface] = {}
        self.telemetry_sync: Optional[Callable[[], dict]] = None

        if auto_detect:
            LOGGER.info("Auto-detection enabled - detecting cameras...")
            self.auto_detect_and_add_all(include_network=include_network)
        else:
            LOGGER.info("Auto-detection disabled - cameras must be added manually")

    def auto_detect_and_add_all(self, include_network: bool = False) -> List[str]:
        """
        Automatically detect all cameras and add them to the manager.

        Args:
            include_network: If True, scan network for cameras (slow, can spam errors)

        Returns:
            List of camera names that were successfully added
        """
        LOGGER.info("Starting auto-detect and add process (include_network=%s)", include_network)
        start_time = time.time()
        
        detected = CameraAutoDetector.detect_all_cameras(include_network=include_network)
        LOGGER.info("Detection phase complete: %d cameras detected", len(detected))
        
        added = []
        failed = []

        for det_cam in detected:
            LOGGER.debug("Processing detected camera: %s (%s)", det_cam.name, det_cam.camera_type.value)
            config = CameraAutoDetector.auto_configure_camera(det_cam)
            if self.add_camera(config):
                added.append(config.name)
                LOGGER.info("Auto-detected and added: %s (%s, %s, source: %s)", 
                           config.name, config.camera_type.value, config.position, config.source)
            else:
                failed.append(det_cam.name)
                LOGGER.warning("Auto-detected but failed to add: %s (%s, source: %s)", 
                             det_cam.name, det_cam.camera_type.value, det_cam.source)

        elapsed = time.time() - start_time
        LOGGER.info("Auto-detection complete: %d cameras found, %d added, %d failed in %.2fs", 
                   len(detected), len(added), len(failed), elapsed)
        return added

    def add_camera(self, config: CameraConfig) -> bool:
        """Add a camera to the manager."""
        if config.name in self.cameras:
            LOGGER.warning("Camera %s already exists", config.name)
            return False

        callback = None
        if self.telemetry_sync:
            callback = lambda frame: setattr(frame, "telemetry_sync", self.telemetry_sync())

        camera = CameraInterface(config, frame_callback=callback)
        if camera.start():
            self.cameras[config.name] = camera
            return True
        return False

    def remove_camera(self, name: str) -> None:
        """Remove a camera."""
        if name in self.cameras:
            self.cameras[name].stop()
            del self.cameras[name]

    def get_camera(self, name: str) -> Optional[CameraInterface]:
        """Get camera by name."""
        return self.cameras.get(name)

    def get_all_frames(self) -> dict[str, Optional[Frame]]:
        """Get latest frame from all cameras."""
        frames = {}
        for name, camera in self.cameras.items():
            frames[name] = camera.get_frame(timeout=0.1)
        return frames

    def stop_all(self) -> None:
        """Stop all cameras."""
        for camera in self.cameras.values():
            camera.stop()
        self.cameras.clear()

    def set_telemetry_sync(self, sync_func: Callable[[], dict]) -> None:
        """Set telemetry synchronization function."""
        self.telemetry_sync = sync_func
        # Update existing cameras
        for camera in self.cameras.values():
            if self.telemetry_sync:
                camera.frame_callback = lambda frame, sync=self.telemetry_sync: setattr(frame, "telemetry_sync", sync())

    def health_check(self) -> dict[str, bool]:
        """Check health of all cameras."""
        return {name: cam.is_healthy() for name, cam in self.cameras.items()}


__all__ = [
    "CameraType",
    "CameraConfig",
    "Frame",
    "DetectedCamera",
    "CameraAutoDetector",
    "CameraInterface",
    "CameraManager",
]
