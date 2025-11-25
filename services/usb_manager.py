"""
USB Manager Service

Automatically detects USB drives, prompts for formatting/configuration,
and creates timestamped directory structures for logging and recording.
"""

from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class USBDevice:
    """Represents a detected USB device."""

    def __init__(self, mount_point: str, device_path: str, label: str = "", size_gb: float = 0.0, filesystem: str = "") -> None:
        self.mount_point = mount_point
        self.device_path = device_path
        self.label = label or Path(mount_point).name
        self.size_gb = size_gb
        self.filesystem = filesystem
        self.detected_at = time.time()

    def __repr__(self) -> str:
        return f"USBDevice({self.label}, {self.mount_point}, {self.size_gb:.1f}GB)"


class USBManager:
    """Manages USB device detection, formatting, and directory setup."""

    # Standard directory structure
    DIRECTORY_STRUCTURE = {
        "logs": ["telemetry", "video", "gps", "diagnostics"],
        "sessions": [],
        "backup": [],
        "config": [],
    }

    def __init__(
        self,
        auto_setup: bool = True,
        prompt_format: bool = True,
        base_mount_path: str = "/media",
        on_device_detected: Optional[Callable[[USBDevice], None]] = None,
    ) -> None:
        """
        Initialize USB manager.

        Args:
            auto_setup: Automatically set up directories on detection
            prompt_format: Prompt before formatting USB drives
            base_mount_path: Base path for mounted USB devices
            on_device_detected: Callback when USB device is detected
        """
        self.auto_setup = auto_setup
        self.prompt_format = prompt_format
        self.base_mount_path = Path(base_mount_path)
        self.on_device_detected = on_device_detected

        self.detected_devices: Dict[str, USBDevice] = {}
        self.active_device: Optional[USBDevice] = None
        self.session_base_path: Optional[Path] = None

        # Platform-specific detection
        self.platform = platform.system().lower()
        self._last_scan = 0.0
        self._scan_interval = 2.0  # Scan every 2 seconds

    def scan_for_devices(self) -> List[USBDevice]:
        """
        Scan for USB devices.

        Returns:
            List of detected USB devices
        """
        devices = []
        now = time.time()

        # Throttle scans
        if now - self._last_scan < self._scan_interval:
            return list(self.detected_devices.values())

        self._last_scan = now

        if self.platform == "linux":
            devices = self._scan_linux()
        elif self.platform == "windows":
            devices = self._scan_windows()
        elif self.platform == "darwin":  # macOS
            devices = self._scan_macos()

        # Update detected devices
        for device in devices:
            if device.mount_point not in self.detected_devices:
                self.detected_devices[device.mount_point] = device
                LOGGER.info("Detected USB device: %s", device)
                if self.on_device_detected:
                    try:
                        self.on_device_detected(device)
                    except Exception as e:
                        LOGGER.error("Error in device detection callback: %s", e)

        return list(self.detected_devices.values())

    def _scan_linux(self) -> List[USBDevice]:
        """Scan for USB devices on Linux."""
        devices = []

        # Check common mount points
        mount_points = [
            self.base_mount_path,
            Path("/mnt"),
            Path("/run/media"),
        ]

        for mount_base in mount_points:
            if not mount_base.exists():
                continue

            for item in mount_base.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    mount_point = str(item)
                    try:
                        # Check if it's a USB device by checking /sys/block
                        device_path = self._get_linux_device_path(mount_point)
                        if device_path:
                            size_gb = self._get_device_size(mount_point)
                            filesystem = self._get_filesystem(mount_point)
                            device = USBDevice(
                                mount_point=mount_point,
                                device_path=device_path,
                                label=item.name,
                                size_gb=size_gb,
                                filesystem=filesystem,
                            )
                            devices.append(device)
                    except Exception as e:
                        LOGGER.debug("Error checking mount point %s: %s", mount_point, e)

        return devices

    def _scan_windows(self) -> List[USBDevice]:
        """Scan for USB devices on Windows."""
        devices = []

        # Windows drive letters
        import string

        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                try:
                    # Check if it's removable
                    if self._is_removable_windows(drive):
                        size_gb = self._get_device_size(drive)
                        filesystem = self._get_filesystem(drive)
                        device = USBDevice(
                            mount_point=drive,
                            device_path=drive,
                            label=f"Drive {letter}",
                            size_gb=size_gb,
                            filesystem=filesystem,
                        )
                        devices.append(device)
                except Exception as e:
                    LOGGER.debug("Error checking drive %s: %s", drive, e)

        return devices

    def _scan_macos(self) -> List[USBDevice]:
        """Scan for USB devices on macOS."""
        devices = []

        # macOS mount points
        mount_points = [
            Path("/Volumes"),
        ]

        for mount_base in mount_points:
            if not mount_base.exists():
                continue

            for item in mount_base.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    mount_point = str(item)
                    try:
                        size_gb = self._get_device_size(mount_point)
                        filesystem = self._get_filesystem(mount_point)
                        device = USBDevice(
                            mount_point=mount_point,
                            device_path=mount_point,
                            label=item.name,
                            size_gb=size_gb,
                            filesystem=filesystem,
                        )
                        devices.append(device)
                    except Exception as e:
                        LOGGER.debug("Error checking mount point %s: %s", mount_point, e)

        return devices

    def _get_linux_device_path(self, mount_point: str) -> Optional[str]:
        """Get device path for Linux mount point."""
        try:
            result = subprocess.run(
                ["findmnt", "-n", "-o", "SOURCE", mount_point],
                capture_output=True,
                text=True,
                timeout=1,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    def _is_removable_windows(self, drive: str) -> bool:
        """Check if Windows drive is removable."""
        try:
            import win32api  # type: ignore

            drive_type = win32api.GetDriveType(drive)
            return drive_type == 2  # DRIVE_REMOVABLE
        except ImportError:
            # Fallback: assume removable if it exists
            return True
        except Exception:
            return False

    def _get_device_size(self, path: str) -> float:
        """Get device size in GB."""
        try:
            stat = shutil.disk_usage(path)
            size_gb = stat.total / (1024**3)
            return size_gb
        except Exception:
            return 0.0

    def _get_filesystem(self, path: str) -> str:
        """Get filesystem type."""
        if self.platform == "linux":
            try:
                result = subprocess.run(
                    ["findmnt", "-n", "-o", "FSTYPE", path],
                    capture_output=True,
                    text=True,
                    timeout=1,
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except Exception:
                pass
        elif self.platform == "windows":
            try:
                result = subprocess.run(
                    ["fsutil", "fsinfo", "volumeinfo", path],
                    capture_output=True,
                    text=True,
                    timeout=1,
                )
                if result.returncode == 0:
                    # Parse output for filesystem type
                    for line in result.stdout.split("\n"):
                        if "File System Name" in line:
                            return line.split(":")[-1].strip()
            except Exception:
                pass
        return "unknown"

    def setup_device(self, device: USBDevice, format_if_needed: bool = False) -> bool:
        """
        Set up a USB device with directory structure.

        Args:
            device: USB device to set up
            format_if_needed: Format device if needed

        Returns:
            True if setup successful
        """
        try:
            mount_path = Path(device.mount_point)

            # Check if writable
            if not os.access(mount_path, os.W_OK):
                LOGGER.error("USB device %s is not writable", device.mount_point)
                return False

            # Create directory structure
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_dir = mount_path / "sessions" / timestamp
            session_dir.mkdir(parents=True, exist_ok=True)

            # Create standard directories
            for main_dir, subdirs in self.DIRECTORY_STRUCTURE.items():
                main_path = mount_path / main_dir
                main_path.mkdir(exist_ok=True)

                for subdir in subdirs:
                    (main_path / subdir).mkdir(exist_ok=True)

            # Create session-specific directories
            (session_dir / "telemetry").mkdir(exist_ok=True)
            (session_dir / "video").mkdir(exist_ok=True)
            (session_dir / "gps").mkdir(exist_ok=True)
            (session_dir / "diagnostics").mkdir(exist_ok=True)

            # Create config file
            config_file = mount_path / "config" / "device_info.txt"
            with open(config_file, "w") as f:
                f.write(f"Device Label: {device.label}\n")
                f.write(f"Mount Point: {device.mount_point}\n")
                f.write(f"Size: {device.size_gb:.2f} GB\n")
                f.write(f"Filesystem: {device.filesystem}\n")
                f.write(f"Setup Date: {datetime.now().isoformat()}\n")
                f.write(f"Session Base: {session_dir}\n")

            self.active_device = device
            self.session_base_path = session_dir

            LOGGER.info("USB device set up: %s -> %s", device.mount_point, session_dir)
            return True

        except Exception as e:
            LOGGER.error("Error setting up USB device %s: %s", device.mount_point, e)
            return False

    def format_device(self, device: USBDevice, filesystem: str = "exfat", label: str = "AITUNER") -> bool:
        """
        Format a USB device.

        Args:
            device: USB device to format
            filesystem: Filesystem type (exfat, fat32, ntfs)
            label: Volume label

        Returns:
            True if formatting successful
        """
        if self.platform != "linux":
            LOGGER.warning("Formatting only supported on Linux")
            return False

        try:
            # Unmount first
            subprocess.run(["umount", device.mount_point], check=False, timeout=5)

            # Format based on filesystem
            if filesystem == "exfat":
                cmd = ["mkfs.exfat", "-n", label, device.device_path]
            elif filesystem == "fat32":
                cmd = ["mkfs.vfat", "-F", "32", "-n", label, device.device_path]
            elif filesystem == "ntfs":
                cmd = ["mkfs.ntfs", "-L", label, device.device_path]
            else:
                LOGGER.error("Unsupported filesystem: %s", filesystem)
                return False

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                LOGGER.info("Formatted USB device: %s", device.device_path)
                return True
            else:
                LOGGER.error("Formatting failed: %s", result.stderr)
                return False

        except Exception as e:
            LOGGER.error("Error formatting USB device: %s", e)
            return False

    def get_session_path(self, subdirectory: str = "", fallback: Optional[Path] = None) -> Path:
        """
        Get path for current session, with automatic fallback to local disk if USB unavailable.

        Args:
            subdirectory: Subdirectory within session (e.g., "telemetry", "video")
            fallback: Fallback path if USB not available

        Returns:
            Path to session directory (always returns a valid path, never None)
        """
        if self.session_base_path:
            if subdirectory:
                return self.session_base_path / subdirectory
            return self.session_base_path

        # Fallback to local disk storage with timestamp
        if fallback is None:
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fallback = Path("logs") / "sessions" / timestamp
        if subdirectory:
            fallback = fallback / subdirectory
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback

    def get_logs_path(self, log_type: str = "telemetry", fallback: Optional[Path] = None) -> Path:
        """
        Get path for logs, with automatic fallback to local disk if USB unavailable.

        Args:
            log_type: Type of log (telemetry, video, gps, diagnostics)
            fallback: Fallback path if USB not available (defaults to local "logs" directory)

        Returns:
            Path to log directory (always returns a valid path, never None)
        """
        if self.active_device:
            log_path = Path(self.active_device.mount_point) / "logs" / log_type
            log_path.mkdir(parents=True, exist_ok=True)
            return log_path

        # Fallback to local disk storage
        if fallback is None:
            fallback = Path("logs") / log_type
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


__all__ = ["USBManager", "USBDevice"]

