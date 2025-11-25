"""
Disk Manager

Manages disk usage, cleanup, and optimization.
"""

from __future__ import annotations

import gzip
import logging
import os
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class DiskManager:
    """Manages disk usage and cleanup."""

    def __init__(
        self,
        max_disk_usage_mb: float = 10240.0,  # 10GB default
        cleanup_threshold: float = 0.9,  # Cleanup at 90% usage
        retention_days: int = 30,  # Keep data for 30 days
    ) -> None:
        """
        Initialize disk manager.

        Args:
            max_disk_usage_mb: Maximum disk usage in MB
            cleanup_threshold: Threshold (0-1) to trigger cleanup
            retention_days: Days to retain data
        """
        self.max_disk_usage_mb = max_disk_usage_mb
        self.cleanup_threshold = cleanup_threshold
        self.retention_days = retention_days

    def get_disk_usage(self, path: str | Path = ".") -> Dict[str, float]:
        """Get disk usage for a path."""
        path = Path(path)
        stat = shutil.disk_usage(path)

        return {
            "total_gb": stat.total / (1024**3),
            "used_gb": stat.used / (1024**3),
            "free_gb": stat.free / (1024**3),
            "percent": (stat.used / stat.total) * 100,
        }

    def should_cleanup(self, path: str | Path = ".") -> bool:
        """Check if cleanup is needed."""
        usage = self.get_disk_usage(path)
        return usage["percent"] > (self.cleanup_threshold * 100)

    def cleanup_old_files(self, directory: str | Path, pattern: str = "*") -> Dict[str, int]:
        """
        Clean up old files.

        Args:
            directory: Directory to clean
            pattern: File pattern to match

        Returns:
            Cleanup statistics
        """
        directory = Path(directory)
        if not directory.exists():
            return {"deleted": 0, "freed_mb": 0}

        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        deleted = 0
        freed_bytes = 0

        for file_path in directory.glob(pattern):
            try:
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date:
                        size = file_path.stat().st_size
                        file_path.unlink()
                        deleted += 1
                        freed_bytes += size
            except Exception as e:
                LOGGER.error("Error deleting file %s: %s", file_path, e)

        return {
            "deleted": deleted,
            "freed_mb": freed_bytes / (1024 * 1024),
        }

    def compress_old_logs(self, directory: str | Path, days_old: int = 7) -> Dict[str, int]:
        """
        Compress old log files.

        Args:
            directory: Directory containing logs
            days_old: Compress files older than this many days

        Returns:
            Compression statistics
        """
        directory = Path(directory)
        if not directory.exists():
            return {"compressed": 0, "freed_mb": 0}

        cutoff_date = datetime.now() - timedelta(days=days_old)
        compressed = 0
        freed_bytes = 0

        for file_path in directory.glob("*.csv"):
            try:
                if file_path.is_file() and not file_path.name.endswith(".gz"):
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date:
                        original_size = file_path.stat().st_size

                        # Compress
                        with open(file_path, "rb") as f_in:
                            with gzip.open(f"{file_path}.gz", "wb") as f_out:
                                shutil.copyfileobj(f_in, f_out)

                        compressed_size = Path(f"{file_path}.gz").stat().st_size
                        file_path.unlink()

                        compressed += 1
                        freed_bytes += original_size - compressed_size
            except Exception as e:
                LOGGER.error("Error compressing file %s: %s", file_path, e)

        return {
            "compressed": compressed,
            "freed_mb": freed_bytes / (1024 * 1024),
        }

    def optimize_database(self, db_path: str | Path) -> Dict[str, Any]:
        """
        Optimize SQLite database.

        Args:
            db_path: Path to database file

        Returns:
            Optimization statistics
        """
        db_path = Path(db_path)
        if not db_path.exists():
            return {"optimized": False, "freed_mb": 0}

        try:
            before_size = db_path.stat().st_size

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Vacuum to reclaim space
            cursor.execute("VACUUM")

            # Analyze for better query planning
            cursor.execute("ANALYZE")

            conn.commit()
            conn.close()

            after_size = db_path.stat().st_size
            freed_bytes = before_size - after_size

            return {
                "optimized": True,
                "freed_mb": freed_bytes / (1024 * 1024),
                "before_mb": before_size / (1024 * 1024),
                "after_mb": after_size / (1024 * 1024),
            }
        except Exception as e:
            LOGGER.error("Error optimizing database %s: %s", db_path, e)
            return {"optimized": False, "error": str(e)}

    def cleanup_temp_files(self, temp_dirs: List[str | Path]) -> Dict[str, int]:
        """
        Clean up temporary files.

        Args:
            temp_dirs: List of temporary directories

        Returns:
            Cleanup statistics
        """
        deleted = 0
        freed_bytes = 0

        for temp_dir in temp_dirs:
            temp_path = Path(temp_dir)
            if not temp_path.exists():
                continue

            for file_path in temp_path.rglob("*"):
                try:
                    if file_path.is_file():
                        size = file_path.stat().st_size
                        file_path.unlink()
                        deleted += 1
                        freed_bytes += size
                except Exception as e:
                    LOGGER.debug("Error deleting temp file %s: %s", file_path, e)

        return {
            "deleted": deleted,
            "freed_mb": freed_bytes / (1024 * 1024),
        }

    def get_largest_files(self, directory: str | Path, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get largest files in a directory.

        Args:
            directory: Directory to scan
            limit: Number of files to return

        Returns:
            List of file info dictionaries
        """
        directory = Path(directory)
        if not directory.exists():
            return []

        files = []
        for file_path in directory.rglob("*"):
            try:
                if file_path.is_file():
                    size = file_path.stat().st_size
                    files.append(
                        {
                            "path": str(file_path),
                            "size_mb": size / (1024 * 1024),
                            "modified": datetime.fromtimestamp(file_path.stat().st_mtime),
                        }
                    )
            except Exception:
                continue

        # Sort by size and return top N
        files.sort(key=lambda x: x["size_mb"], reverse=True)
        return files[:limit]


__all__ = ["DiskManager"]

