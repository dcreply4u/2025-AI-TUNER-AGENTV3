"""
Offline Capabilities Manager

Handles offline mode, sync queue, and local caching.
"""

from __future__ import annotations

import json
import logging
import queue
import sqlite3
import threading
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class SyncStatus(Enum):
    """Sync status for data items."""

    PENDING = "pending"
    SYNCING = "syncing"
    SYNCED = "synced"
    FAILED = "failed"


@dataclass
class SyncItem:
    """Item in sync queue."""

    item_id: str
    item_type: str  # telemetry, video, gps, etc.
    data: Dict[str, Any]
    timestamp: float
    status: SyncStatus = SyncStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    priority: int = 0  # Higher priority syncs first


class OfflineManager:
    """Manages offline capabilities and sync queue."""

    def __init__(self, cache_dir: str | Path = "cache", db_file: str | Path = "cache/sync_queue.db") -> None:
        """
        Initialize offline manager.

        Args:
            cache_dir: Directory for local cache
            db_file: SQLite database file for sync queue
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.db_file = Path(db_file)
        self.db_file.parent.mkdir(parents=True, exist_ok=True)

        self.sync_queue: queue.PriorityQueue = queue.PriorityQueue()
        self.sync_thread: Optional[threading.Thread] = None
        self.running = False
        self._lock = threading.Lock()

        # Connectivity callback
        self.connectivity_callback: Optional[Callable[[], bool]] = None

        # Initialize database
        self._init_database()

        # Load pending items from database
        self._load_pending_items()

    def _init_database(self) -> None:
        """Initialize SQLite database for sync queue."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sync_queue (
                item_id TEXT PRIMARY KEY,
                item_type TEXT NOT NULL,
                data TEXT NOT NULL,
                timestamp REAL NOT NULL,
                status TEXT NOT NULL,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                priority INTEGER DEFAULT 0,
                created_at REAL DEFAULT (julianday('now'))
            )
        """
        )

        conn.commit()
        conn.close()

    def _load_pending_items(self) -> None:
        """Load pending items from database into queue."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM sync_queue WHERE status IN ('pending', 'failed') ORDER BY priority DESC, timestamp ASC")
        rows = cursor.fetchall()

        for row in rows:
            item = SyncItem(
                item_id=row[0],
                item_type=row[1],
                data=json.loads(row[2]),
                timestamp=row[3],
                status=SyncStatus(row[4]),
                retry_count=row[5],
                max_retries=row[6],
                priority=row[7],
            )
            # Use negative priority for max-heap behavior
            self.sync_queue.put((-item.priority, item.timestamp, item))

        conn.close()
        LOGGER.info("Loaded %d pending sync items", len(rows))

    def queue_for_sync(
        self,
        item_type: str,
        data: Dict[str, Any],
        priority: int = 0,
        timestamp: Optional[float] = None,
    ) -> str:
        """
        Queue an item for synchronization.

        Args:
            item_type: Type of item (telemetry, video, gps, etc.)
            data: Data to sync
            priority: Sync priority (higher = sync first)
            timestamp: Item timestamp (defaults to now)

        Returns:
            Item ID
        """
        item_id = f"{item_type}_{int((timestamp or time.time()) * 1000)}"
        timestamp = timestamp or time.time()

        item = SyncItem(
            item_id=item_id,
            item_type=item_type,
            data=data,
            timestamp=timestamp,
            priority=priority,
        )

        # Save to database
        self._save_item_to_db(item)

        # Add to queue
        self.sync_queue.put((-priority, timestamp, item))

        LOGGER.debug("Queued item for sync: %s (priority: %d)", item_id, priority)
        return item_id

    def _save_item_to_db(self, item: SyncItem) -> None:
        """Save item to database."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO sync_queue 
            (item_id, item_type, data, timestamp, status, retry_count, max_retries, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                item.item_id,
                item.item_type,
                json.dumps(item.data),
                item.timestamp,
                item.status.value,
                item.retry_count,
                item.max_retries,
                item.priority,
            ),
        )

        conn.commit()
        conn.close()

    def _update_item_status(self, item_id: str, status: SyncStatus, retry_count: Optional[int] = None) -> None:
        """Update item status in database."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        if retry_count is not None:
            cursor.execute(
                "UPDATE sync_queue SET status = ?, retry_count = ? WHERE item_id = ?",
                (status.value, retry_count, item_id),
            )
        else:
            cursor.execute("UPDATE sync_queue SET status = ? WHERE item_id = ?", (status.value, item_id))

        conn.commit()
        conn.close()

    def start_sync_worker(self, sync_callback: Callable[[SyncItem], bool]) -> None:
        """
        Start background sync worker.

        Args:
            sync_callback: Function to call for each item (returns True if successful)
        """
        if self.running:
            return

        self.running = True
        self.sync_callback = sync_callback

        self.sync_thread = threading.Thread(target=self._sync_worker, daemon=True)
        self.sync_thread.start()
        LOGGER.info("Started sync worker")

    def stop_sync_worker(self) -> None:
        """Stop sync worker."""
        self.running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        LOGGER.info("Stopped sync worker")

    def _sync_worker(self) -> None:
        """Background worker that processes sync queue."""
        while self.running:
            try:
                # Check connectivity
                if self.connectivity_callback and not self.connectivity_callback():
                    time.sleep(5)  # Wait for connectivity
                    continue

                # Get item from queue (with timeout)
                try:
                    _, _, item = self.sync_queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                # Update status to syncing
                self._update_item_status(item.item_id, SyncStatus.SYNCING)

                # Attempt sync
                try:
                    success = self.sync_callback(item)
                    if success:
                        self._update_item_status(item.item_id, SyncStatus.SYNCED)
                        # Remove from database
                        self._remove_item_from_db(item.item_id)
                        LOGGER.debug("Synced item: %s", item.item_id)
                    else:
                        item.retry_count += 1
                        if item.retry_count >= item.max_retries:
                            self._update_item_status(item.item_id, SyncStatus.FAILED, item.retry_count)
                            LOGGER.warning("Failed to sync item after %d retries: %s", item.max_retries, item.item_id)
                        else:
                            self._update_item_status(item.item_id, SyncStatus.PENDING, item.retry_count)
                            # Re-queue with lower priority
                            item.priority = max(0, item.priority - 1)
                            self.sync_queue.put((-item.priority, item.timestamp, item))
                except Exception as e:
                    LOGGER.error("Error syncing item %s: %s", item.item_id, e)
                    item.retry_count += 1
                    if item.retry_count >= item.max_retries:
                        self._update_item_status(item.item_id, SyncStatus.FAILED, item.retry_count)
                    else:
                        self._update_item_status(item.item_id, SyncStatus.PENDING, item.retry_count)
                        self.sync_queue.put((-item.priority, item.timestamp, item))

            except Exception as e:
                LOGGER.error("Error in sync worker: %s", e)
                time.sleep(1)

    def _remove_item_from_db(self, item_id: str) -> None:
        """Remove item from database."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sync_queue WHERE item_id = ?", (item_id,))
        conn.commit()
        conn.close()

    def get_sync_stats(self) -> Dict[str, Any]:
        """Get sync queue statistics."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute("SELECT status, COUNT(*) FROM sync_queue GROUP BY status")
        status_counts = dict(cursor.fetchall())

        cursor.execute("SELECT COUNT(*) FROM sync_queue")
        total = cursor.fetchone()[0]

        conn.close()

        return {
            "total": total,
            "pending": status_counts.get(SyncStatus.PENDING.value, 0),
            "syncing": status_counts.get(SyncStatus.SYNCING.value, 0),
            "synced": status_counts.get(SyncStatus.SYNCED.value, 0),
            "failed": status_counts.get(SyncStatus.FAILED.value, 0),
        }

    def clear_synced_items(self) -> None:
        """Clear successfully synced items from database."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sync_queue WHERE status = ?", (SyncStatus.SYNCED.value,))
        conn.commit()
        conn.close()
        LOGGER.info("Cleared synced items from database")

    def set_connectivity_callback(self, callback: Callable[[], bool]) -> None:
        """Set callback to check connectivity."""
        self.connectivity_callback = callback


__all__ = ["OfflineManager", "SyncItem", "SyncStatus"]

