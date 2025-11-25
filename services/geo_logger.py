from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, List, Tuple


class GeoLogger:
    """Persists GPS breadcrumbs for theft recovery and map replay."""

    def __init__(self, db_path: str | Path = "geo_history.db") -> None:
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS geo_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                latitude REAL,
                longitude REAL,
                speed_mps REAL,
                heading REAL
            )
            """
        )
        self.conn.commit()

    def log(self, fix: dict) -> None:
        self.conn.execute(
            "INSERT INTO geo_log (timestamp, latitude, longitude, speed_mps, heading) VALUES (?, ?, ?, ?, ?)",
            (
                fix.get("timestamp"),
                fix.get("lat"),
                fix.get("lon"),
                fix.get("speed_mps"),
                fix.get("heading"),
            ),
        )
        self.conn.commit()

    def fetch_recent(self, limit: int = 500) -> List[Tuple[float, float]]:
        cursor = self.conn.execute(
            "SELECT latitude, longitude FROM geo_log ORDER BY id DESC LIMIT ?", (limit,)
        )
        return [(row[0], row[1]) for row in cursor.fetchall()][::-1]

    def vacuum(self) -> None:
        self.conn.execute("VACUUM")


__all__ = ["GeoLogger"]

