from __future__ import annotations

import csv
import os
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Mapping


class DataLogger:
    """Thread-safe CSV logger for streaming telemetry."""

    # Track recent files for easy email access
    _recent_files: list[Path] = []
    _max_recent_files = 20

    def __init__(self, log_dir: str | Path = "logs") -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.file_path = self.log_dir / f"session_{timestamp}.csv"
        self._fields_written = False
        self._lock = RLock()
        
        # Add to recent files
        with self._lock:
            DataLogger._recent_files.insert(0, self.file_path)
            # Keep only the most recent files
            DataLogger._recent_files = DataLogger._recent_files[:DataLogger._max_recent_files]

    def log(self, data: Mapping[str, float]) -> None:
        if not data:
            return
        with self._lock:
            with self.file_path.open("a", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(data.keys()))
                if not self._fields_written:
                    writer.writeheader()
                    self._fields_written = True
                writer.writerow(data)

    @classmethod
    def get_recent_files(cls, limit: int = 10) -> list[Path]:
        """Get list of recent log files."""
        return cls._recent_files[:limit]


__all__ = ["DataLogger"]

