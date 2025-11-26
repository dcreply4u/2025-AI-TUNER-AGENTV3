"""
Hard Drive Manager for AI Tuner Agent

Manages hard drive setup, mounting, and integration with the application.
Supports running the application from hard drive with USB backup sync.
"""

from __future__ import annotations

import logging
import subprocess
import time
from pathlib import Path
from typing import Optional

LOGGER = logging.getLogger(__name__)


class HDDManager:
    """
    Manages hard drive operations for AI Tuner Agent.
    
    Features:
    - Auto-detection of hard drive
    - Mount point management
    - Path resolution (HDD vs USB vs local)
    - Sync coordination
    """
    
    DEFAULT_MOUNT_POINT = Path("/mnt/aituner_hdd")
    DEFAULT_PROJECT_PATH = DEFAULT_MOUNT_POINT / "AITUNER" / "2025-AI-TUNER-AGENTV3"
    
    def __init__(self, mount_point: Optional[Path] = None) -> None:
        """
        Initialize HDD manager.
        
        Args:
            mount_point: Custom mount point (default: /mnt/aituner_hdd)
        """
        self.mount_point = Path(mount_point) if mount_point else self.DEFAULT_MOUNT_POINT
        self.project_path = self.mount_point / "AITUNER" / "2025-AI-TUNER-AGENTV3"
        self._is_mounted: Optional[bool] = None
        self._last_check = 0.0
        
    def is_mounted(self, force_check: bool = False) -> bool:
        """
        Check if hard drive is mounted.
        
        Args:
            force_check: Force re-check (don't use cache)
            
        Returns:
            True if mounted, False otherwise
        """
        # Cache check for 5 seconds
        if not force_check and self._is_mounted is not None:
            if time.time() - self._last_check < 5.0:
                return self._is_mounted
        
        try:
            # Check if mount point exists and is a mount point
            if not self.mount_point.exists():
                self._is_mounted = False
                return False
            
            # Check if it's actually mounted (not just a directory)
            result = subprocess.run(
                ["mountpoint", "-q", str(self.mount_point)],
                capture_output=True,
                timeout=1.0,
            )
            self._is_mounted = (result.returncode == 0)
            self._last_check = time.time()
            return self._is_mounted
        except Exception as e:
            LOGGER.debug("Error checking mount status: %s", e)
            self._is_mounted = False
            return False
    
    def get_project_path(self) -> Optional[Path]:
        """
        Get the project path on hard drive.
        
        Returns:
            Path to project on HDD, or None if not available
        """
        if not self.is_mounted():
            return None
        
        if self.project_path.exists():
            return self.project_path
        
        return None
    
    def get_storage_path(self, subdirectory: str = "") -> Optional[Path]:
        """
        Get storage path on hard drive.
        
        Args:
            subdirectory: Subdirectory within storage (e.g., "logs", "sessions")
            
        Returns:
            Path to storage directory, or None if HDD not available
        """
        if not self.is_mounted():
            return None
        
        storage_path = self.mount_point / "AITUNER" / "storage"
        if subdirectory:
            storage_path = storage_path / subdirectory
        
        storage_path.mkdir(parents=True, exist_ok=True)
        return storage_path
    
    def get_logs_path(self, log_type: str = "telemetry") -> Optional[Path]:
        """
        Get logs path on hard drive.
        
        Args:
            log_type: Type of log (telemetry, video, gps, etc.)
            
        Returns:
            Path to log directory, or None if HDD not available
        """
        return self.get_storage_path(f"logs/{log_type}")
    
    def get_sessions_path(self) -> Optional[Path]:
        """Get sessions path on hard drive."""
        return self.get_storage_path("sessions")
    
    def trigger_sync(self) -> bool:
        """
        Trigger manual sync between USB and HDD.
        
        Returns:
            True if sync triggered successfully
        """
        try:
            # Try to run system sync script
            result = subprocess.run(
                ["sudo", "/usr/local/bin/aituner_sync.sh"],
                capture_output=True,
                timeout=300,  # 5 minute timeout
                text=True,
            )
            
            if result.returncode == 0:
                LOGGER.info("HDD sync completed successfully")
                return True
            else:
                LOGGER.warning("HDD sync had errors: %s", result.stderr)
                return False
        except FileNotFoundError:
            # System script doesn't exist, try local script
            sync_script = Path(__file__).parent.parent / "scripts" / "sync_usb_hdd.sh"
            if sync_script.exists():
                try:
                    result = subprocess.run(
                        ["bash", str(sync_script)],
                        capture_output=True,
                        timeout=300,
                        text=True,
                    )
                    return result.returncode == 0
                except Exception as e:
                    LOGGER.error("Error running sync script: %s", e)
                    return False
            else:
                LOGGER.warning("Sync script not found")
                return False
        except Exception as e:
            LOGGER.error("Error triggering sync: %s", e)
            return False
    
    def get_status(self) -> dict:
        """
        Get HDD status.
        
        Returns:
            Dictionary with HDD status information
        """
        is_mounted = self.is_mounted()
        project_path = self.get_project_path()
        
        status = {
            "mounted": is_mounted,
            "mount_point": str(self.mount_point),
            "project_available": project_path is not None,
        }
        
        if project_path:
            status["project_path"] = str(project_path)
            # Get disk usage
            try:
                import shutil
                total, used, free = shutil.disk_usage(self.mount_point)
                status["disk_total_gb"] = total / (1024**3)
                status["disk_used_gb"] = used / (1024**3)
                status["disk_free_gb"] = free / (1024**3)
                status["disk_usage_percent"] = (used / total) * 100
            except Exception as e:
                LOGGER.debug("Error getting disk usage: %s", e)
        
        return status


__all__ = ["HDDManager"]

