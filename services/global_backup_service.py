"""
Global Backup Service
Singleton service for easy access to backup functionality from anywhere
"""

from __future__ import annotations

import logging
from typing import Optional

from services.backup_manager import BackupManager, BackupType, BackupEntry, BackupSettings

LOGGER = logging.getLogger(__name__)

# Global backup manager instance
_global_backup_manager: Optional[BackupManager] = None


def get_backup_manager() -> Optional[BackupManager]:
    """Get global backup manager instance."""
    global _global_backup_manager
    if _global_backup_manager is None:
        try:
            _global_backup_manager = BackupManager()
        except Exception as e:
            LOGGER.error("Failed to initialize global backup manager: %s", e)
    return _global_backup_manager


def create_backup(file_path: str, backup_type: BackupType, description: str = "") -> Optional[BackupEntry]:
    """Create backup using global backup manager."""
    manager = get_backup_manager()
    if not manager:
        return None
    return manager.create_backup(file_path, backup_type, description=description)


def get_backups(file_path: str) -> list:
    """Get backups for file using global backup manager."""
    manager = get_backup_manager()
    if not manager:
        return []
    return manager.get_backups(file_path)


def revert_to_backup(backup: BackupEntry) -> bool:
    """Revert file to backup using global backup manager."""
    manager = get_backup_manager()
    if not manager:
        return False
    return manager.revert_to_backup(backup, create_backup=True)
















