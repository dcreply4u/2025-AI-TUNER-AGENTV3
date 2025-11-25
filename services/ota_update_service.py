"""
Over-the-Air (OTA) Update Service
Enables remote software updates without physical access.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import time
import zipfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class UpdateStatus(Enum):
    """Update status."""
    IDLE = "idle"
    CHECKING = "checking"
    DOWNLOADING = "downloading"
    VERIFYING = "verifying"
    INSTALLING = "installing"
    COMPLETE = "complete"
    FAILED = "failed"
    ROLLBACK = "rollback"


@dataclass
class UpdateInfo:
    """Update package information."""
    version: str
    release_date: float
    changelog: str
    download_url: str
    file_size: int
    checksum: str
    min_version: Optional[str] = None  # Minimum current version required
    dependencies: List[str] = field(default_factory=list)
    critical: bool = False  # Critical security update
    delta_update: bool = False  # Delta update vs full update
    base_version: Optional[str] = None  # For delta updates


@dataclass
class UpdateProgress:
    """Update progress information."""
    status: UpdateStatus
    progress_percent: float = 0.0
    current_step: str = ""
    error_message: Optional[str] = None
    downloaded_bytes: int = 0
    total_bytes: int = 0


class OTAUpdateService:
    """
    Over-the-Air update service.
    
    Handles:
    - Checking for updates
    - Downloading update packages
    - Verifying integrity
    - Installing updates
    - Rollback on failure
    """
    
    def __init__(
        self,
        update_server_url: str,
        app_version: str,
        install_directory: Optional[Path] = None,
        backup_directory: Optional[Path] = None,
        auto_check: bool = True,
        check_interval: int = 3600,  # 1 hour
    ):
        """
        Initialize OTA update service.
        
        Args:
            update_server_url: URL of update server
            app_version: Current application version
            install_directory: Directory to install updates (default: project root)
            backup_directory: Directory for backups (default: install_dir/backups)
            auto_check: Automatically check for updates
            check_interval: Interval between auto-checks (seconds)
        """
        self.update_server_url = update_server_url.rstrip('/')
        self.app_version = app_version
        self.install_directory = install_directory or Path(__file__).parent.parent
        self.backup_directory = backup_directory or (self.install_directory / "backups" / "ota")
        self.backup_directory.mkdir(parents=True, exist_ok=True)
        
        self.auto_check = auto_check
        self.check_interval = check_interval
        self.last_check_time = 0.0
        
        self.current_update: Optional[UpdateInfo] = None
        self.update_progress = UpdateProgress(status=UpdateStatus.IDLE)
        self.progress_callback: Optional[Callable[[UpdateProgress], None]] = None
        
        # Update history
        self.update_history_file = self.install_directory / "data" / "update_history.json"
        self.update_history: List[Dict[str, Any]] = []
        self._load_update_history()
    
    def _load_update_history(self) -> None:
        """Load update history."""
        try:
            if self.update_history_file.exists():
                with open(self.update_history_file, 'r') as f:
                    self.update_history = json.load(f)
        except Exception as e:
            LOGGER.warning("Failed to load update history: %s", e)
            self.update_history = []
    
    def _save_update_history(self) -> None:
        """Save update history."""
        try:
            self.update_history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.update_history_file, 'w') as f:
                json.dump(self.update_history, f, indent=2)
        except Exception as e:
            LOGGER.error("Failed to save update history: %s", e)
    
    def check_for_updates(self, force: bool = False) -> Optional[UpdateInfo]:
        """
        Check for available updates.
        
        Args:
            force: Force check even if recently checked
        
        Returns:
            UpdateInfo if update available, None otherwise
        """
        if not REQUESTS_AVAILABLE:
            LOGGER.error("requests library not available for OTA updates")
            return None
        
        # Rate limiting
        current_time = time.time()
        if not force and (current_time - self.last_check_time) < 60:  # Min 1 minute between checks
            LOGGER.debug("Update check rate limited")
            return None
        
        self.last_check_time = current_time
        self.update_progress.status = UpdateStatus.CHECKING
        self._notify_progress()
        
        try:
            # Request update info from server
            url = f"{self.update_server_url}/api/updates/check"
            params = {
                "current_version": self.app_version,
                "platform": sys.platform,
                "architecture": self._get_architecture(),
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("update_available"):
                update_info = UpdateInfo(
                    version=data["version"],
                    release_date=data.get("release_date", time.time()),
                    changelog=data.get("changelog", ""),
                    download_url=data["download_url"],
                    file_size=data.get("file_size", 0),
                    checksum=data.get("checksum", ""),
                    min_version=data.get("min_version"),
                    dependencies=data.get("dependencies", []),
                    critical=data.get("critical", False),
                    delta_update=data.get("delta_update", False),
                    base_version=data.get("base_version"),
                )
                
                # Check if version is newer
                if self._is_newer_version(update_info.version, self.app_version):
                    self.current_update = update_info
                    LOGGER.info("Update available: %s", update_info.version)
                    return update_info
                else:
                    LOGGER.debug("No update available (current: %s, server: %s)", 
                               self.app_version, update_info.version)
            
            self.update_progress.status = UpdateStatus.IDLE
            self._notify_progress()
            return None
            
        except requests.RequestException as e:
            LOGGER.error("Failed to check for updates: %s", e)
            self.update_progress.status = UpdateStatus.IDLE
            self.update_progress.error_message = f"Network error: {e}"
            self._notify_progress()
            return None
        except Exception as e:
            LOGGER.error("Error checking for updates: %s", e, exc_info=True)
            self.update_progress.status = UpdateStatus.IDLE
            self.update_progress.error_message = str(e)
            self._notify_progress()
            return None
    
    def download_update(self, update_info: Optional[UpdateInfo] = None) -> bool:
        """
        Download update package.
        
        Args:
            update_info: Update info (uses current_update if None)
        
        Returns:
            True if download successful
        """
        if not REQUESTS_AVAILABLE:
            LOGGER.error("requests library not available")
            return False
        
        if update_info is None:
            update_info = self.current_update
        
        if not update_info:
            LOGGER.error("No update info available")
            return False
        
        self.update_progress.status = UpdateStatus.DOWNLOADING
        self.update_progress.total_bytes = update_info.file_size
        self.update_progress.downloaded_bytes = 0
        self._notify_progress()
        
        try:
            # Create download directory
            download_dir = self.install_directory / "downloads" / "ota"
            download_dir.mkdir(parents=True, exist_ok=True)
            download_file = download_dir / f"update_{update_info.version}.zip"
            
            # Download with progress tracking
            response = requests.get(update_info.download_url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(download_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        self.update_progress.downloaded_bytes += len(chunk)
                        if update_info.file_size > 0:
                            self.update_progress.progress_percent = (
                                self.update_progress.downloaded_bytes / update_info.file_size * 100
                            )
                        self._notify_progress()
            
            # Verify file size
            if download_file.stat().st_size != update_info.file_size:
                LOGGER.error("Downloaded file size mismatch")
                download_file.unlink()
                return False
            
            # Verify checksum
            if not self._verify_checksum(download_file, update_info.checksum):
                LOGGER.error("Checksum verification failed")
                download_file.unlink()
                return False
            
            # Store update file path
            self.current_update_file = download_file
            LOGGER.info("Update downloaded successfully: %s", download_file)
            return True
            
        except requests.RequestException as e:
            LOGGER.error("Failed to download update: %s", e)
            self.update_progress.status = UpdateStatus.FAILED
            self.update_progress.error_message = f"Download failed: {e}"
            self._notify_progress()
            return False
        except Exception as e:
            LOGGER.error("Error downloading update: %s", e, exc_info=True)
            self.update_progress.status = UpdateStatus.FAILED
            self.update_progress.error_message = str(e)
            self._notify_progress()
            return False
    
    def install_update(
        self,
        update_info: Optional[UpdateInfo] = None,
        require_approval: bool = True,
    ) -> bool:
        """
        Install downloaded update.
        
        Args:
            update_info: Update info (uses current_update if None)
            require_approval: Require user approval before installing
        
        Returns:
            True if installation successful
        """
        if update_info is None:
            update_info = self.current_update
        
        if not update_info:
            LOGGER.error("No update info available")
            return False
        
        if not hasattr(self, 'current_update_file') or not self.current_update_file.exists():
            LOGGER.error("Update file not found")
            return False
        
        # Create backup before installing
        backup_path = self._create_backup()
        if not backup_path:
            LOGGER.error("Failed to create backup")
            return False
        
        self.update_progress.status = UpdateStatus.INSTALLING
        self.update_progress.progress_percent = 0.0
        self.update_progress.current_step = "Extracting update package"
        self._notify_progress()
        
        try:
            # Extract update package
            extract_dir = self.install_directory / "downloads" / "ota" / f"extract_{update_info.version}"
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(self.current_update_file, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            self.update_progress.progress_percent = 30.0
            self.update_progress.current_step = "Installing files"
            self._notify_progress()
            
            # Install files (copy to install directory)
            self._install_files(extract_dir, update_info)
            
            self.update_progress.progress_percent = 80.0
            self.update_progress.current_step = "Running post-install scripts"
            self._notify_progress()
            
            # Run post-install scripts if any
            self._run_post_install_scripts(extract_dir)
            
            self.update_progress.progress_percent = 100.0
            self.update_progress.status = UpdateStatus.COMPLETE
            self.update_progress.current_step = "Update complete"
            self._notify_progress()
            
            # Record in history
            self.update_history.append({
                "version": update_info.version,
                "installed_at": time.time(),
                "backup_path": str(backup_path),
            })
            self._save_update_history()
            
            # Cleanup
            shutil.rmtree(extract_dir, ignore_errors=True)
            
            LOGGER.info("Update installed successfully: %s", update_info.version)
            return True
            
        except Exception as e:
            LOGGER.error("Update installation failed: %s", e, exc_info=True)
            self.update_progress.status = UpdateStatus.FAILED
            self.update_progress.error_message = str(e)
            self._notify_progress()
            
            # Attempt rollback
            self.rollback_update(backup_path)
            return False
    
    def rollback_update(self, backup_path: Optional[Path] = None) -> bool:
        """
        Rollback to previous version.
        
        Args:
            backup_path: Path to backup (uses latest if None)
        
        Returns:
            True if rollback successful
        """
        if backup_path is None:
            # Find latest backup
            backups = sorted(self.backup_directory.glob("backup_*"), reverse=True)
            if not backups:
                LOGGER.error("No backups found for rollback")
                return False
            backup_path = backups[0]
        
        if not backup_path.exists():
            LOGGER.error("Backup path does not exist: %s", backup_path)
            return False
        
        self.update_progress.status = UpdateStatus.ROLLBACK
        self.update_progress.current_step = "Rolling back to previous version"
        self._notify_progress()
        
        try:
            # Restore from backup
            if backup_path.is_file() and backup_path.suffix == '.zip':
                # Extract backup
                with zipfile.ZipFile(backup_path, 'r') as zip_ref:
                    zip_ref.extractall(self.install_directory)
            else:
                # Copy backup directory
                shutil.copytree(backup_path, self.install_directory, dirs_exist_ok=True)
            
            self.update_progress.status = UpdateStatus.COMPLETE
            self.update_progress.current_step = "Rollback complete"
            self._notify_progress()
            
            LOGGER.info("Rollback successful: %s", backup_path)
            return True
            
        except Exception as e:
            LOGGER.error("Rollback failed: %s", e, exc_info=True)
            self.update_progress.status = UpdateStatus.FAILED
            self.update_progress.error_message = f"Rollback failed: {e}"
            self._notify_progress()
            return False
    
    def _create_backup(self) -> Optional[Path]:
        """Create backup of current installation."""
        try:
            timestamp = int(time.time())
            backup_name = f"backup_{self.app_version}_{timestamp}"
            backup_path = self.backup_directory / backup_name
            
            # Create backup as zip
            backup_zip = backup_path.with_suffix('.zip')
            
            with zipfile.ZipFile(backup_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Backup important files/directories
                important_paths = [
                    'services',
                    'ui',
                    'core',
                    'interfaces',
                    'config.py',
                    'requirements.txt',
                ]
                
                for path_name in important_paths:
                    path = self.install_directory / path_name
                    if path.exists():
                        if path.is_file():
                            zipf.write(path, path_name)
                        else:
                            for file_path in path.rglob('*'):
                                if file_path.is_file():
                                    arcname = file_path.relative_to(self.install_directory)
                                    zipf.write(file_path, arcname)
            
            LOGGER.info("Backup created: %s", backup_zip)
            return backup_zip
            
        except Exception as e:
            LOGGER.error("Failed to create backup: %s", e)
            return None
    
    def _install_files(self, extract_dir: Path, update_info: UpdateInfo) -> None:
        """Install files from update package."""
        # Look for manifest or install instructions
        manifest_file = extract_dir / "update_manifest.json"
        
        if manifest_file.exists():
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)
            
            # Install files according to manifest
            for file_info in manifest.get("files", []):
                src = extract_dir / file_info["source"]
                dst = self.install_directory / file_info["destination"]
                
                if src.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    if src.is_file():
                        shutil.copy2(src, dst)
                    else:
                        shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            # Default: copy all files to install directory
            for item in extract_dir.iterdir():
                if item.name not in ['update_manifest.json', 'post_install.sh']:
                    dst = self.install_directory / item.name
                    if item.is_file():
                        shutil.copy2(item, dst)
                    else:
                        shutil.copytree(item, dst, dirs_exist_ok=True)
    
    def _run_post_install_scripts(self, extract_dir: Path) -> None:
        """Run post-install scripts if any."""
        script_file = extract_dir / "post_install.sh"
        if script_file.exists() and script_file.is_file():
            try:
                # Make executable
                os.chmod(script_file, 0o755)
                # Run script
                result = subprocess.run(
                    [str(script_file)],
                    cwd=self.install_directory,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if result.returncode != 0:
                    LOGGER.warning("Post-install script returned non-zero: %s", result.stderr)
            except Exception as e:
                LOGGER.warning("Failed to run post-install script: %s", e)
    
    def _verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """Verify file checksum."""
        if not expected_checksum:
            return True  # Skip if no checksum provided
        
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            calculated = sha256_hash.hexdigest()
            return calculated.lower() == expected_checksum.lower()
        except Exception as e:
            LOGGER.error("Checksum verification error: %s", e)
            return False
    
    def _is_newer_version(self, new_version: str, current_version: str) -> bool:
        """Check if new version is newer than current."""
        try:
            # Simple version comparison (can be enhanced)
            new_parts = [int(x) for x in new_version.split('.')]
            current_parts = [int(x) for x in current_version.split('.')]
            
            # Pad to same length
            max_len = max(len(new_parts), len(current_parts))
            new_parts.extend([0] * (max_len - len(new_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))
            
            return new_parts > current_parts
        except Exception:
            # Fallback: string comparison
            return new_version > current_version
    
    def _get_architecture(self) -> str:
        """Get system architecture."""
        import platform
        machine = platform.machine().lower()
        if 'arm' in machine or 'aarch' in machine:
            return 'arm64'
        elif 'x86_64' in machine or 'amd64' in machine:
            return 'x86_64'
        else:
            return machine
    
    def set_progress_callback(self, callback: Callable[[UpdateProgress], None]) -> None:
        """Set callback for progress updates."""
        self.progress_callback = callback
    
    def _notify_progress(self) -> None:
        """Notify progress callback."""
        if self.progress_callback:
            try:
                self.progress_callback(self.update_progress)
            except Exception as e:
                LOGGER.warning("Progress callback error: %s", e)
    
    def get_update_history(self) -> List[Dict[str, Any]]:
        """Get update history."""
        return self.update_history.copy()
    
    def get_current_progress(self) -> UpdateProgress:
        """Get current update progress."""
        return self.update_progress



