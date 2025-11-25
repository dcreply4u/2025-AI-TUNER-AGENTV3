"""
USB Camera Manager
Enhanced USB camera support with auto-detection and driver management for common cameras
"""

from __future__ import annotations

import logging
import platform
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

LOGGER = logging.getLogger(__name__)

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None  # type: ignore

try:
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False


class CameraVendor(Enum):
    """Common USB camera vendors."""
    LOGITECH = "logitech"
    MICROSOFT = "microsoft"
    CREATIVE = "creative"
    RAZER = "razer"
    CORSAIR = "corsair"
    GENERIC_UVC = "generic_uvc"
    UNKNOWN = "unknown"


class CameraDriver(Enum):
    """Camera driver types."""
    UVC = "uvc"  # USB Video Class (standard)
    V4L2 = "v4l2"  # Video4Linux2 (Linux)
    DIRECTSHOW = "directshow"  # Windows DirectShow
    AVFOUNDATION = "avfoundation"  # macOS AVFoundation
    MSMF = "msmf"  # Windows Media Foundation


@dataclass
class USBCameraInfo:
    """USB camera information."""
    device_id: str  # Device index or path
    vendor: CameraVendor
    model: str
    driver: CameraDriver
    capabilities: Dict[str, any] = field(default_factory=dict)
    supported_resolutions: List[Tuple[int, int]] = field(default_factory=list)
    max_fps: int = 30
    is_uvc: bool = True
    device_path: Optional[str] = None  # /dev/video0, etc.
    vendor_id: Optional[str] = None
    product_id: Optional[str] = None
    serial_number: Optional[str] = None


class USBCameraManager:
    """
    Enhanced USB camera manager with auto-detection and driver support.
    
    Supports:
    - Auto-detection of USB cameras
    - Vendor-specific optimizations
    - Driver management
    - Capability detection
    - Resolution and FPS enumeration
    """
    
    # Common camera vendor IDs (USB VID:PID)
    VENDOR_IDS = {
        "046d": CameraVendor.LOGITECH,  # Logitech
        "045e": CameraVendor.MICROSOFT,  # Microsoft
        "041e": CameraVendor.CREATIVE,   # Creative Labs
        "1532": CameraVendor.RAZER,     # Razer
        "1b1c": CameraVendor.CORSAIR,   # Corsair
    }
    
    # Common camera models
    CAMERA_MODELS = {
        CameraVendor.LOGITECH: [
            "C920", "C922", "C930e", "C270", "C310", "BRIO", "HD Pro C920",
            "StreamCam", "C615", "C505", "C525", "C910"
        ],
        CameraVendor.MICROSOFT: [
            "LifeCam HD-3000", "LifeCam Studio", "LifeCam Cinema",
            "Surface Camera", "Xbox Live Vision"
        ],
        CameraVendor.CREATIVE: [
            "Live! Cam Sync", "Live! Cam HD", "Live! Cam Chat HD"
        ],
    }
    
    def __init__(self):
        """Initialize USB camera manager."""
        self.detected_cameras: Dict[str, USBCameraInfo] = {}
        self.active_cameras: Dict[str, any] = {}  # cv2.VideoCapture objects
        self.platform = platform.system().lower()
        self._last_scan = 0.0
        self._scan_interval = 5.0  # Scan every 5 seconds
    
    def detect_all_cameras(self) -> List[USBCameraInfo]:
        """
        Detect all USB cameras.
        
        Returns:
            List of detected USB camera information
        """
        now = time.time()
        if now - self._last_scan < self._scan_interval:
            return list(self.detected_cameras.values())
        
        self._last_scan = now
        cameras = []
        
        if not CV2_AVAILABLE:
            LOGGER.warning("OpenCV not available, cannot detect cameras")
            return cameras
        
        if self.platform == "linux":
            cameras = self._detect_linux_cameras()
        elif self.platform == "windows":
            cameras = self._detect_windows_cameras()
        elif self.platform == "darwin":
            cameras = self._detect_macos_cameras()
        else:
            cameras = self._detect_generic_cameras()
        
        # Update detected cameras
        for camera in cameras:
            if camera.device_id not in self.detected_cameras:
                self.detected_cameras[camera.device_id] = camera
                LOGGER.info("Detected USB camera: %s %s on %s", camera.vendor.value, camera.model, camera.device_id)
        
        return list(self.detected_cameras.values())
    
    def _detect_linux_cameras(self) -> List[USBCameraInfo]:
        """Detect cameras on Linux using v4l2."""
        cameras = []
        
        # Check /dev/video* devices
        video_devices = sorted(Path("/dev").glob("video*"))
        
        for video_dev in video_devices:
            try:
                device_id = str(video_dev)
                device_index = int(video_dev.name.replace("video", ""))
                
                # Get device info using v4l2-ctl if available
                vendor, model, vid, pid = self._get_linux_camera_info(video_dev)
                
                # Test camera with OpenCV
                cap = cv2.VideoCapture(device_index)
                if not cap.isOpened():
                    cap.release()
                    continue
                
                # Get capabilities
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
                fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
                
                # Try to get supported resolutions
                resolutions = self._get_supported_resolutions(cap)
                
                cap.release()
                
                camera = USBCameraInfo(
                    device_id=str(device_index),
                    vendor=vendor,
                    model=model,
                    driver=CameraDriver.V4L2,
                    device_path=device_id,
                    vendor_id=vid,
                    product_id=pid,
                    supported_resolutions=resolutions or [(width, height)],
                    max_fps=fps,
                )
                cameras.append(camera)
                
            except Exception as e:
                LOGGER.debug("Error detecting camera %s: %s", video_dev, e)
                continue
        
        return cameras
    
    def _get_linux_camera_info(self, device_path: Path) -> Tuple[CameraVendor, str, Optional[str], Optional[str]]:
        """Get camera vendor/model info using v4l2-ctl."""
        vendor = CameraVendor.UNKNOWN
        model = "USB Camera"
        vid = None
        pid = None
        
        try:
            # Try v4l2-ctl to get device info
            result = subprocess.run(
                ["v4l2-ctl", "--device", str(device_path), "--info"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                
                # Extract vendor/model
                for line in output.split("\n"):
                    if "card" in line:
                        model = line.split(":")[-1].strip()
                    if "bus info" in line and "usb" in line:
                        # Extract VID:PID from bus info
                        parts = line.split(":")
                        for part in parts:
                            if "usb" in part:
                                # Format: usb-0000:01:00.0-1.2 or usb-0000:01:00.0-1.2:1.0
                                # Try to get VID:PID from sysfs
                                pass
                
                # Try to get VID:PID from sysfs
                sysfs_path = Path(f"/sys/class/video4linux/{device_path.name}")
                if sysfs_path.exists():
                    device_link = sysfs_path.resolve()
                    usb_path = device_link.parent.parent
                    if "usb" in str(usb_path):
                        vid_file = usb_path / "idVendor"
                        pid_file = usb_path / "idProduct"
                        if vid_file.exists():
                            vid = vid_file.read_text().strip()
                        if pid_file.exists():
                            pid = pid_file.read_text().strip()
                        
                        if vid and vid.lower() in self.VENDOR_IDS:
                            vendor = self.VENDOR_IDS[vid.lower()]
                
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            LOGGER.debug("Could not get camera info via v4l2-ctl: %s", e)
        
        # Try to identify from model name
        if vendor == CameraVendor.UNKNOWN and model:
            model_lower = model.lower()
            for ven, models in self.CAMERA_MODELS.items():
                for cam_model in models:
                    if cam_model.lower() in model_lower:
                        vendor = ven
                        break
                if vendor != CameraVendor.UNKNOWN:
                    break
        
        return vendor, model, vid, pid
    
    def _detect_windows_cameras(self) -> List[USBCameraInfo]:
        """Detect cameras on Windows."""
        cameras = []
        
        if not CV2_AVAILABLE:
            return cameras
        
        # Windows: Try device indices 0-9
        for i in range(10):
            try:
                # Suppress OpenCV errors
                import os
                import sys
                old_stderr = sys.stderr
                try:
                    sys.stderr = open(os.devnull, 'w')
                    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)  # Try DirectShow first
                    if not cap.isOpened():
                        cap = cv2.VideoCapture(i, cv2.CAP_MSMF)  # Try Media Foundation
                    
                    if not cap.isOpened():
                        sys.stderr.close()
                        sys.stderr = old_stderr
                        continue
                    
                    # Get capabilities
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
                    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
                    
                    # Try to get device name
                    backend = cap.getBackendName()
                    driver = CameraDriver.DIRECTSHOW if "DSHOW" in backend else CameraDriver.MSMF
                    
                    # Get supported resolutions
                    resolutions = self._get_supported_resolutions(cap)
                    
                    cap.release()
                    sys.stderr.close()
                    sys.stderr = old_stderr
                    
                    # Try to get device info from Windows registry or WMI
                    vendor, model = self._get_windows_camera_info(i)
                    
                    camera = USBCameraInfo(
                        device_id=str(i),
                        vendor=vendor,
                        model=model,
                        driver=driver,
                        supported_resolutions=resolutions or [(width, height)],
                        max_fps=fps,
                    )
                    cameras.append(camera)
                    
                except Exception:
                    if sys.stderr != old_stderr:
                        try:
                            sys.stderr.close()
                        except Exception:
                            pass
                    sys.stderr = old_stderr
                    continue
                    
            except Exception as e:
                LOGGER.debug("Error detecting Windows camera %d: %s", i, e)
                continue
        
        return cameras
    
    def _get_windows_camera_info(self, device_index: int) -> Tuple[CameraVendor, str]:
        """Get camera vendor/model info on Windows."""
        vendor = CameraVendor.UNKNOWN
        model = "USB Camera"
        
        try:
            import winreg
            
            # Query Windows registry for camera info
            key_path = f"SYSTEM\\CurrentControlSet\\Enum\\USB"
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                
                # Iterate through USB devices
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey = winreg.OpenKey(key, subkey_name)
                        
                        try:
                            # Check if it's a camera device
                            device_desc = winreg.QueryValueEx(subkey, "DeviceDesc")[0]
                            if "camera" in device_desc.lower() or "webcam" in device_desc.lower():
                                # Extract vendor and model
                                parts = device_desc.split(";")
                                if len(parts) >= 2:
                                    model = parts[1].strip()
                                    
                                    # Check vendor
                                    vendor_str = parts[0].lower()
                                    if "logitech" in vendor_str:
                                        vendor = CameraVendor.LOGITECH
                                    elif "microsoft" in vendor_str:
                                        vendor = CameraVendor.MICROSOFT
                                    elif "creative" in vendor_str:
                                        vendor = CameraVendor.CREATIVE
                                    elif "razer" in vendor_str:
                                        vendor = CameraVendor.RAZER
                                    elif "corsair" in vendor_str:
                                        vendor = CameraVendor.CORSAIR
                                
                                break
                        except Exception:
                            pass
                        
                        subkey.Close()
                        i += 1
                    except OSError:
                        break
                
                key.Close()
            except Exception:
                pass
                
        except ImportError:
            LOGGER.debug("winreg not available")
        except Exception as e:
            LOGGER.debug("Error getting Windows camera info: %s", e)
        
        return vendor, model
    
    def _detect_macos_cameras(self) -> List[USBCameraInfo]:
        """Detect cameras on macOS."""
        cameras = []
        
        if not CV2_AVAILABLE:
            return cameras
        
        # macOS: Try device indices
        for i in range(10):
            try:
                import os
                import sys
                old_stderr = sys.stderr
                try:
                    sys.stderr = open(os.devnull, 'w')
                    cap = cv2.VideoCapture(i, cv2.CAP_AVFOUNDATION)
                    
                    if not cap.isOpened():
                        sys.stderr.close()
                        sys.stderr = old_stderr
                        continue
                    
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
                    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
                    
                    resolutions = self._get_supported_resolutions(cap)
                    
                    cap.release()
                    sys.stderr.close()
                    sys.stderr = old_stderr
                    
                    # Try to get device info
                    vendor, model = self._get_macos_camera_info(i)
                    
                    camera = USBCameraInfo(
                        device_id=str(i),
                        vendor=vendor,
                        model=model,
                        driver=CameraDriver.AVFOUNDATION,
                        supported_resolutions=resolutions or [(width, height)],
                        max_fps=fps,
                    )
                    cameras.append(camera)
                    
                except Exception:
                    if sys.stderr != old_stderr:
                        try:
                            sys.stderr.close()
                        except Exception:
                            pass
                    sys.stderr = old_stderr
                    continue
                    
            except Exception as e:
                LOGGER.debug("Error detecting macOS camera %d: %s", i, e)
                continue
        
        return cameras
    
    def _get_macos_camera_info(self, device_index: int) -> Tuple[CameraVendor, str]:
        """Get camera vendor/model info on macOS."""
        vendor = CameraVendor.UNKNOWN
        model = "USB Camera"
        
        try:
            # Use system_profiler to get USB device info
            result = subprocess.run(
                ["system_profiler", "SPUSBDataType"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                
                # Look for camera-related devices
                if "camera" in output or "webcam" in output:
                    # Try to extract vendor/model
                    lines = output.split("\n")
                    for i, line in enumerate(lines):
                        if "camera" in line or "webcam" in line:
                            # Look for vendor/model in nearby lines
                            for j in range(max(0, i-5), min(len(lines), i+5)):
                                if "vendor id" in lines[j] or "product id" in lines[j]:
                                    # Extract info
                                    pass
                            
                            if "logitech" in line:
                                vendor = CameraVendor.LOGITECH
                            elif "microsoft" in line:
                                vendor = CameraVendor.MICROSOFT
        except Exception as e:
            LOGGER.debug("Error getting macOS camera info: %s", e)
        
        return vendor, model
    
    def _detect_generic_cameras(self) -> List[USBCameraInfo]:
        """Generic camera detection (fallback)."""
        cameras = []
        
        if not CV2_AVAILABLE:
            return cameras
        
        # Try device indices 0-9
        for i in range(10):
            try:
                import os
                import sys
                old_stderr = sys.stderr
                try:
                    sys.stderr = open(os.devnull, 'w')
                    cap = cv2.VideoCapture(i)
                    
                    if not cap.isOpened():
                        sys.stderr.close()
                        sys.stderr = old_stderr
                        continue
                    
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
                    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
                    
                    resolutions = self._get_supported_resolutions(cap)
                    
                    cap.release()
                    sys.stderr.close()
                    sys.stderr = old_stderr
                    
                    camera = USBCameraInfo(
                        device_id=str(i),
                        vendor=CameraVendor.GENERIC_UVC,
                        model="USB Camera",
                        driver=CameraDriver.UVC,
                        supported_resolutions=resolutions or [(width, height)],
                        max_fps=fps,
                    )
                    cameras.append(camera)
                    
                except Exception:
                    if sys.stderr != old_stderr:
                        try:
                            sys.stderr.close()
                        except Exception:
                            pass
                    sys.stderr = old_stderr
                    continue
                    
            except Exception as e:
                LOGGER.debug("Error detecting camera %d: %s", i, e)
                continue
        
        return cameras
    
    def _get_supported_resolutions(self, cap: any) -> List[Tuple[int, int]]:
        """Get supported resolutions for camera."""
        resolutions = []
        
        if not CV2_AVAILABLE:
            return resolutions
        
        # Common resolutions to test
        test_resolutions = [
            (640, 480),
            (800, 600),
            (1024, 768),
            (1280, 720),
            (1280, 960),
            (1600, 1200),
            (1920, 1080),
            (2560, 1440),
            (3840, 2160),
        ]
        
        current_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        current_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Always include current resolution
        if current_width > 0 and current_height > 0:
            resolutions.append((current_width, current_height))
        
        # Test other resolutions
        for width, height in test_resolutions:
            if (width, height) in resolutions:
                continue
            
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if actual_width == width and actual_height == height:
                resolutions.append((width, height))
        
        # Restore original resolution
        if resolutions:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, current_width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, current_height)
        
        return sorted(set(resolutions), key=lambda x: x[0] * x[1])
    
    def open_camera(self, device_id: str, width: Optional[int] = None, height: Optional[int] = None, fps: Optional[int] = None) -> Optional[any]:
        """
        Open a camera with specified settings.
        
        Args:
            device_id: Camera device ID
            width: Desired width
            height: Desired height
            fps: Desired FPS
            
        Returns:
            cv2.VideoCapture object or None
        """
        if not CV2_AVAILABLE:
            return None
        
        camera_info = self.detected_cameras.get(device_id)
        if not camera_info:
            LOGGER.warning("Camera %s not detected", device_id)
            return None
        
        try:
            device_index = int(device_id) if device_id.isdigit() else 0
            
            # Select backend based on platform and driver
            backend = None
            if self.platform == "linux":
                backend = cv2.CAP_V4L2
            elif self.platform == "windows":
                if camera_info.driver == CameraDriver.DIRECTSHOW:
                    backend = cv2.CAP_DSHOW
                else:
                    backend = cv2.CAP_MSMF
            elif self.platform == "darwin":
                backend = cv2.CAP_AVFOUNDATION
            
            if backend:
                cap = cv2.VideoCapture(device_index, backend)
            else:
                cap = cv2.VideoCapture(device_index)
            
            if not cap.isOpened():
                return None
            
            # Set resolution
            if width and height:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            # Set FPS
            if fps:
                cap.set(cv2.CAP_PROP_FPS, fps)
            
            # Apply vendor-specific optimizations
            self._apply_vendor_optimizations(cap, camera_info)
            
            self.active_cameras[device_id] = cap
            return cap
            
        except Exception as e:
            LOGGER.error("Failed to open camera %s: %s", device_id, e)
            return None
    
    def _apply_vendor_optimizations(self, cap: any, camera_info: USBCameraInfo) -> None:
        """Apply vendor-specific camera optimizations."""
        if not CV2_AVAILABLE:
            return
        
        # Logitech optimizations
        if camera_info.vendor == CameraVendor.LOGITECH:
            # Enable auto-focus (if supported)
            try:
                cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            except Exception:
                pass
            
            # Set auto-exposure
            try:
                cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Manual mode
            except Exception:
                pass
        
        # Microsoft LifeCam optimizations
        elif camera_info.vendor == CameraVendor.MICROSOFT:
            # Set exposure
            try:
                cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
            except Exception:
                pass
    
    def close_camera(self, device_id: str) -> bool:
        """Close a camera."""
        cap = self.active_cameras.get(device_id)
        if cap:
            cap.release()
            del self.active_cameras[device_id]
            return True
        return False
    
    def get_camera_info(self, device_id: str) -> Optional[USBCameraInfo]:
        """Get camera information."""
        return self.detected_cameras.get(device_id)
    
    def list_cameras(self) -> List[USBCameraInfo]:
        """List all detected cameras."""
        return list(self.detected_cameras.values())
















