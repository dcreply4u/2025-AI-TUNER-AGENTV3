"""
Backup Manager Service
Auto-backup and version control for ECU tuning files and global configuration
"""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class BackupType(Enum):
    """Backup type classification."""
    ECU_TUNING = "ecu_tuning"
    ECU_CALIBRATION = "ecu_calibration"
    ECU_BINARY = "ecu_binary"
    CONFIGURATION = "configuration"
    SENSOR_CONFIG = "sensor_config"
    DASHBOARD = "dashboard"
    GLOBAL = "global"


@dataclass
class BackupEntry:
    """Backup entry information."""
    backup_id: str
    backup_type: BackupType
    file_path: str
    backup_path: str
    timestamp: float
    file_size: int
    file_hash: str
    description: str = ""
    metadata: Dict[str, any] = field(default_factory=dict)


@dataclass
class BackupSettings:
    """Backup settings configuration."""
    enabled: bool = True
    auto_backup_enabled: bool = True
    max_backups_per_file: int = 50
    backup_interval_seconds: float = 300.0  # 5 minutes
    backup_on_save: bool = True
    backup_on_change: bool = True
    backup_directory: str = "backups"
    compress_backups: bool = True
    keep_daily_backups: int = 30  # Keep 30 days of daily backups
    keep_weekly_backups: int = 12  # Keep 12 weeks of weekly backups
    backup_before_apply: bool = True
    backup_before_burn: bool = True


class BackupManager:
    """
    Comprehensive backup manager for ECU tuning files and configuration.
    
    Features:
    - Auto-backup on file save/change
    - Version control with revert capability
    - Configurable backup retention
    - File integrity checking (hash)
    - Backup compression
    - Global and per-file backup settings
    """
    
    def __init__(self, backup_dir: Optional[str] = None, settings: Optional[BackupSettings] = None):
        """
        Initialize backup manager.
        
        Args:
            backup_dir: Backup directory path
            settings: Backup settings
        """
        self.settings = settings or BackupSettings()
        
        # Setup backup directory
        if backup_dir:
            self.backup_dir = Path(backup_dir)
        else:
            self.backup_dir = Path(self.settings.backup_directory)
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.backup_dir / "ecu_tuning").mkdir(exist_ok=True)
        (self.backup_dir / "ecu_calibration").mkdir(exist_ok=True)
        (self.backup_dir / "ecu_binary").mkdir(exist_ok=True)
        (self.backup_dir / "configuration").mkdir(exist_ok=True)
        (self.backup_dir / "sensor_config").mkdir(exist_ok=True)
        (self.backup_dir / "dashboard").mkdir(exist_ok=True)
        (self.backup_dir / "global").mkdir(exist_ok=True)
        
        # Backup registry (in-memory index)
        self.backup_registry: Dict[str, List[BackupEntry]] = {}
        self._load_registry()
        
        # Last backup times (for interval-based backups)
        self.last_backup_times: Dict[str, float] = {}
    
    def create_backup(
        self,
        file_path: str,
        backup_type: BackupType,
        description: str = "",
        metadata: Optional[Dict[str, any]] = None,
        force: bool = False
    ) -> Optional[BackupEntry]:
        """
        Create a backup of a file.
        
        Args:
            file_path: Path to file to backup
            backup_type: Type of backup
            description: Optional description
            metadata: Optional metadata
            force: Force backup even if settings disabled
            
        Returns:
            BackupEntry if successful, None otherwise
        """
        if not self.settings.enabled and not force:
            return None
        
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            LOGGER.warning("File does not exist for backup: %s", file_path)
            return None
        
        # Check backup interval
        if not force and self.settings.auto_backup_enabled:
            last_backup = self.last_backup_times.get(file_path, 0)
            if time.time() - last_backup < self.settings.backup_interval_seconds:
                return None  # Too soon since last backup
        
        try:
            # Calculate file hash
            file_hash = self._calculate_file_hash(file_path_obj)
            
            # Check if identical backup already exists
            existing_backups = self.backup_registry.get(file_path, [])
            if existing_backups:
                latest = existing_backups[-1]
                if latest.file_hash == file_hash:
                    LOGGER.debug("File unchanged, skipping backup: %s", file_path)
                    return latest  # Return existing backup
            
            # Generate backup filename
            timestamp = time.time()
            backup_id = f"{int(timestamp)}_{hashlib.md5(file_path.encode()).hexdigest()[:8]}"
            backup_filename = f"{file_path_obj.stem}_{backup_id}{file_path_obj.suffix}"
            
            # Determine backup subdirectory
            backup_subdir = self.backup_dir / backup_type.value
            backup_path = backup_subdir / backup_filename
            
            # Copy file
            shutil.copy2(file_path_obj, backup_path)
            
            # Compress if enabled
            if self.settings.compress_backups:
                compressed_path = backup_path.with_suffix(backup_path.suffix + ".gz")
                import gzip
                with open(backup_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                backup_path.unlink()  # Remove uncompressed
                backup_path = compressed_path
            
            # Create backup entry
            backup_entry = BackupEntry(
                backup_id=backup_id,
                backup_type=backup_type,
                file_path=str(file_path_obj.absolute()),
                backup_path=str(backup_path.absolute()),
                timestamp=timestamp,
                file_size=file_path_obj.stat().st_size,
                file_hash=file_hash,
                description=description or f"Auto-backup at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}",
                metadata=metadata or {},
            )
            
            # Add to registry
            if file_path not in self.backup_registry:
                self.backup_registry[file_path] = []
            self.backup_registry[file_path].append(backup_entry)
            
            # Enforce max backups per file
            backups = self.backup_registry[file_path]
            if len(backups) > self.settings.max_backups_per_file:
                # Remove oldest backups
                to_remove = backups[:-self.settings.max_backups_per_file]
                for old_backup in to_remove:
                    try:
                        Path(old_backup.backup_path).unlink()
                    except Exception:
                        pass
                self.backup_registry[file_path] = backups[-self.settings.max_backups_per_file:]
            
            # Update last backup time
            self.last_backup_times[file_path] = timestamp
            
            # Save registry
            self._save_registry()
            
            LOGGER.info("Created backup: %s -> %s", file_path, backup_path)
            return backup_entry
            
        except Exception as e:
            LOGGER.error("Failed to create backup for %s: %s", file_path, e)
            return None
    
    def get_backups(self, file_path: str) -> List[BackupEntry]:
        """
        Get all backups for a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            List of backup entries (newest first)
        """
        backups = self.backup_registry.get(file_path, [])
        return sorted(backups, key=lambda b: b.timestamp, reverse=True)
    
    def revert_to_backup(self, backup_entry: BackupEntry, create_backup: bool = True) -> bool:
        """
        Revert a file to a previous backup.
        
        Args:
            backup_entry: Backup entry to revert to
            create_backup: Create backup of current file before reverting
            
        Returns:
            True if successful
        """
        try:
            file_path = Path(backup_entry.file_path)
            backup_path = Path(backup_entry.backup_path)
            
            if not backup_path.exists():
                LOGGER.error("Backup file does not exist: %s", backup_path)
                return False
            
            # Create backup of current file if it exists
            if create_backup and file_path.exists():
                self.create_backup(
                    str(file_path),
                    backup_entry.backup_type,
                    description="Pre-revert backup",
                    force=True
                )
            
            # Decompress if needed
            if backup_path.suffix == ".gz":
                import gzip
                temp_path = backup_path.with_suffix("")
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(temp_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                backup_path = temp_path
            
            # Restore file
            shutil.copy2(backup_path, file_path)
            
            # Cleanup temp file if decompressed
            if backup_path.suffix == "" and Path(backup_entry.backup_path).suffix == ".gz":
                backup_path.unlink()
            
            LOGGER.info("Reverted file to backup: %s (backup: %s)", file_path, backup_entry.backup_id)
            return True
            
        except Exception as e:
            LOGGER.error("Failed to revert file: %s", e)
            return False
    
    def delete_backup(self, backup_entry: BackupEntry) -> bool:
        """Delete a backup entry."""
        try:
            backup_path = Path(backup_entry.backup_path)
            if backup_path.exists():
                backup_path.unlink()
            
            # Remove from registry
            if backup_entry.file_path in self.backup_registry:
                backups = self.backup_registry[backup_entry.file_path]
                self.backup_registry[backup_entry.file_path] = [
                    b for b in backups if b.backup_id != backup_entry.backup_id
                ]
            
            self._save_registry()
            return True
        except Exception as e:
            LOGGER.error("Failed to delete backup: %s", e)
            return False
    
    def cleanup_old_backups(self) -> int:
        """
        Cleanup old backups based on retention settings.
        
        Returns:
            Number of backups deleted
        """
        deleted_count = 0
        current_time = time.time()
        
        # Daily backups (keep N days)
        daily_threshold = current_time - (self.settings.keep_daily_backups * 24 * 3600)
        
        # Weekly backups (keep N weeks)
        weekly_threshold = current_time - (self.settings.keep_weekly_backups * 7 * 24 * 3600)
        
        for file_path, backups in list(self.backup_registry.items()):
            # Keep most recent backups
            backups_to_keep = []
            backups_to_delete = []
            
            for backup in sorted(backups, key=lambda b: b.timestamp, reverse=True):
                age = current_time - backup.timestamp
                
                # Always keep recent backups
                if age < 7 * 24 * 3600:  # Less than 1 week
                    backups_to_keep.append(backup)
                # Keep daily backups within threshold
                elif age < daily_threshold:
                    # Keep one per day
                    day = int(backup.timestamp / (24 * 3600))
                    if not any(int(b.timestamp / (24 * 3600)) == day for b in backups_to_keep):
                        backups_to_keep.append(backup)
                    else:
                        backups_to_delete.append(backup)
                # Keep weekly backups within threshold
                elif age < weekly_threshold:
                    # Keep one per week
                    week = int(backup.timestamp / (7 * 24 * 3600))
                    if not any(int(b.timestamp / (7 * 24 * 3600)) == week for b in backups_to_keep):
                        backups_to_keep.append(backup)
                    else:
                        backups_to_delete.append(backup)
                else:
                    backups_to_delete.append(backup)
            
            # Delete old backups
            for backup in backups_to_delete:
                if self.delete_backup(backup):
                    deleted_count += 1
            
            # Update registry
            self.backup_registry[file_path] = backups_to_keep
        
        self._save_registry()
        LOGGER.info("Cleaned up %d old backups", deleted_count)
        return deleted_count
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _save_registry(self) -> None:
        """Save backup registry to disk."""
        registry_path = self.backup_dir / "backup_registry.json"
        try:
            registry_data = {}
            for file_path, backups in self.backup_registry.items():
                registry_data[file_path] = [
                    {
                        "backup_id": b.backup_id,
                        "backup_type": b.backup_type.value,
                        "backup_path": b.backup_path,
                        "timestamp": b.timestamp,
                        "file_size": b.file_size,
                        "file_hash": b.file_hash,
                        "description": b.description,
                        "metadata": b.metadata,
                    }
                    for b in backups
                ]
            
            with open(registry_path, 'w') as f:
                json.dump(registry_data, f, indent=2)
        except Exception as e:
            LOGGER.error("Failed to save backup registry: %s", e)
    
    def _load_registry(self) -> None:
        """Load backup registry from disk."""
        registry_path = self.backup_dir / "backup_registry.json"
        if not registry_path.exists():
            return
        
        try:
            with open(registry_path, 'r') as f:
                registry_data = json.load(f)
            
            for file_path, backups_data in registry_data.items():
                self.backup_registry[file_path] = [
                    BackupEntry(
                        backup_id=b["backup_id"],
                        backup_type=BackupType(b["backup_type"]),
                        file_path=file_path,
                        backup_path=b["backup_path"],
                        timestamp=b["timestamp"],
                        file_size=b["file_size"],
                        file_hash=b["file_hash"],
                        description=b.get("description", ""),
                        metadata=b.get("metadata", {}),
                    )
                    for b in backups_data
                ]
        except Exception as e:
            LOGGER.error("Failed to load backup registry: %s", e)
    
    def get_backup_statistics(self) -> Dict[str, any]:
        """Get backup statistics."""
        total_backups = sum(len(backups) for backups in self.backup_registry.values())
        total_files = len(self.backup_registry)
        total_size = 0
        
        for backups in self.backup_registry.values():
            for backup in backups:
                backup_path = Path(backup.backup_path)
                if backup_path.exists():
                    total_size += backup_path.stat().st_size
        
        return {
            "total_backups": total_backups,
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "backup_directory": str(self.backup_dir),
        }
















