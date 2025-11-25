"""
Disk Cleanup Service

Manages disk usage, cleans old files, and compresses data.
"""

from __future__ import annotations

import gzip
import logging
import os
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class DiskCleanup:
    """Manages disk cleanup and compression."""

    def __init__(
        self,
        max_disk_usage_mb: float = 5000.0,
        cleanup_interval_hours: float = 24.0,
        retention_days: int = 30,
    ) -> None:
        """
        Initialize disk cleanup service.

        Args:
            max_disk_usage_mb: Maximum disk usage in MB before cleanup
            cleanup_interval_hours: Hours between automatic cleanups
            retention_days: Days to retain data
        """
        self.max_disk_usage_mb = max_disk_usage_mb
        self.cleanup_interval_hours = cleanup_interval_hours
        self.retention_days = retention_days
        self.last_cleanup = 0.0

    def cleanup_old_files(
        self,
        directory: str | Path,
        pattern: str = "*",
        older_than_days: Optional[int] = None,
    ) -> Dict[str, int]:
        """
        Clean up old files.

        Args:
            directory: Directory to clean
            pattern: File pattern to match
            older_than_days: Delete files older than this (None = use retention_days)

        Returns:
            Statistics about cleanup
        """
        directory = Path(directory)
        if not directory.exists():
            return {"deleted": 0, "freed_mb": 0}

        older_than_days = older_than_days or self.retention_days
        cutoff_time = time.time() - (older_than_days * 24 * 3600)

        deleted_count = 0
        freed_bytes = 0

        for file_path in directory.rglob(pattern):
            if not file_path.is_file():
                continue

            try:
                file_mtime = file_path.stat().st_mtime
                if file_mtime < cutoff_time:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    deleted_count += 1
                    freed_bytes += file_size
            except Exception as e:
                LOGGER.warning("Failed to delete %s: %s", file_path, e)

        freed_mb = freed_bytes / (1024 * 1024)
        LOGGER.info("Cleaned %d files, freed %.2f MB", deleted_count, freed_mb)

        return {
            "deleted": deleted_count,
            "freed_mb": freed_mb,
        }

    def compress_old_logs(self, log_directory: str | Path, compress_after_days: int = 7) -> Dict[str, int]:
        """
        Compress old log files.

        Args:
            log_directory: Directory containing logs
            compress_after_days: Compress files older than this

        Returns:
            Statistics about compression
        """
        log_directory = Path(log_directory)
        if not log_directory.exists():
            return {"compressed": 0, "freed_mb": 0}

        cutoff_time = time.time() - (compress_after_days * 24 * 3600)
        compressed_count = 0
        freed_bytes = 0

        for file_path in log_directory.rglob("*.csv"):
            if file_path.suffix == ".gz":
                continue  # Already compressed

            try:
                file_mtime = file_path.stat().st_mtime
                if file_mtime < cutoff_time:
                    # Compress file
                    original_size = file_path.stat().st_size

                    with open(file_path, "rb") as f_in:
                        with gzip.open(f"{file_path}.gz", "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)

                    compressed_size = Path(f"{file_path}.gz").stat().st_size
                    file_path.unlink()

                    compressed_count += 1
                    freed_bytes += original_size - compressed_size
            except Exception as e:
                LOGGER.warning("Failed to compress %s: %s", file_path, e)

        freed_mb = freed_bytes / (1024 * 1024)
        LOGGER.info("Compressed %d files, freed %.2f MB", compressed_count, freed_mb)

        return {
            "compressed": compressed_count,
            "freed_mb": freed_mb,
        }

    def get_disk_usage(self, directory: str | Path) -> Dict[str, float]:
        """
        Get disk usage for a directory.

        Args:
            directory: Directory to check

        Returns:
            Disk usage statistics
        """
        directory = Path(directory)
        if not directory.exists():
            return {"used_mb": 0, "file_count": 0}

        total_bytes = 0
        file_count = 0

        for file_path in directory.rglob("*"):
            if file_path.is_file():
                try:
                    total_bytes += file_path.stat().st_size
                    file_count += 1
                except Exception:
                    pass

        return {
            "used_mb": total_bytes / (1024 * 1024),
            "file_count": file_count,
        }

    def cleanup_if_needed(self, directories: List[str | Path]) -> Dict[str, Any]:
        """
        Cleanup if disk usage exceeds threshold.

        Args:
            directories: Directories to check and clean

        Returns:
            Cleanup results
        """
        now = time.time()

        # Check if cleanup is needed
        if now - self.last_cleanup < (self.cleanup_interval_hours * 3600):
            return {"skipped": True, "reason": "Too soon since last cleanup"}

        total_usage = 0.0
        for directory in directories:
            usage = self.get_disk_usage(directory)
            total_usage += usage["used_mb"]

        if total_usage < self.max_disk_usage_mb:
            return {"skipped": True, "reason": "Disk usage within limits", "usage_mb": total_usage}

        # Perform cleanup
        results = {
            "usage_before_mb": total_usage,
            "cleanup_results": [],
        }

        for directory in directories:
            # Clean old files
            cleanup_result = self.cleanup_old_files(directory)
            results["cleanup_results"].append(cleanup_result)

            # Compress old logs
            compress_result = self.compress_old_logs(directory)
            results["cleanup_results"].append(compress_result)

        # Calculate total freed
        total_freed = sum(r.get("freed_mb", 0) for r in results["cleanup_results"])
        results["freed_mb"] = total_freed

        # Check usage after cleanup
        total_usage_after = 0.0
        for directory in directories:
            usage = self.get_disk_usage(directory)
            total_usage_after += usage["used_mb"]

        results["usage_after_mb"] = total_usage_after
        self.last_cleanup = now

        LOGGER.info(
            "Disk cleanup: freed %.2f MB, usage: %.2f MB -> %.2f MB",
            total_freed,
            total_usage,
            total_usage_after,
        )

        return results

    def optimize_database(self, db_path: str | Path) -> Dict[str, Any]:
        """
        Optimize database file (SQLite VACUUM).

        Args:
            db_path: Path to database file

        Returns:
            Optimization results
        """
        db_path = Path(db_path)
        if not db_path.exists():
            return {"optimized": False, "reason": "Database not found"}

        try:
            import sqlite3

            before_size = db_path.stat().st_size

            conn = sqlite3.connect(str(db_path))
            conn.execute("VACUUM")
            conn.execute("ANALYZE")
            conn.close()

            after_size = db_path.stat().st_size
            freed_mb = (before_size - after_size) / (1024 * 1024)

            LOGGER.info("Database optimized: freed %.2f MB", freed_mb)

            return {
                "optimized": True,
                "freed_mb": freed_mb,
                "before_mb": before_size / (1024 * 1024),
                "after_mb": after_size / (1024 * 1024),
            }
        except Exception as e:
            LOGGER.error("Failed to optimize database: %s", e)
            return {"optimized": False, "error": str(e)}


__all__ = ["DiskCleanup"]

