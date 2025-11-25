"""
Database Manager

Provides fast local database (SQLite) as primary with cloud database fallback.
Integrated with notification system for status updates.
"""

from __future__ import annotations

import logging
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import psycopg2
    from psycopg2 import pool
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    psycopg2 = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class DatabaseType(Enum):
    """Database types."""

    LOCAL = "local"
    CLOUD = "cloud"


@dataclass
class DatabaseConfig:
    """Database configuration."""

    local_db_path: str | Path = "data/local.db"
    cloud_enabled: bool = False
    cloud_type: str = "postgresql"  # postgresql, mysql, etc.
    cloud_host: str = ""
    cloud_port: int = 5432
    cloud_database: str = ""
    cloud_user: str = ""
    cloud_password: str = ""
    cloud_ssl: bool = True
    connection_pool_size: int = 5
    sync_interval: float = 30.0  # Seconds between syncs


class DatabaseManager:
    """Manages local and cloud databases with automatic failover."""

    def __init__(
        self,
        config: DatabaseConfig,
        notification_callback: Optional[callable] = None,
    ) -> None:
        """
        Initialize database manager.

        Args:
            config: Database configuration
            notification_callback: Callback for notifications (voice_feedback, etc.)
        """
        self.config = config
        self.notification_callback = notification_callback

        # Local database (SQLite)
        self.local_db_path = Path(config.local_db_path)
        self.local_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.local_conn: Optional[sqlite3.Connection] = None

        # Cloud database connection pool
        self.cloud_pool: Optional[Any] = None
        self.cloud_available = False

        # Sync state
        self.sync_thread: Optional[threading.Thread] = None
        self.syncing = False
        self._lock = threading.Lock()

        # Initialize databases
        self._init_local_db()
        if config.cloud_enabled:
            self._init_cloud_db()

        # Start sync thread if cloud is enabled
        if config.cloud_enabled and self.cloud_available:
            self._start_sync_thread()

    def _init_local_db(self) -> None:
        """Initialize local SQLite database."""
        try:
            self.local_conn = sqlite3.connect(
                str(self.local_db_path),
                check_same_thread=False,
                timeout=10.0,
            )
            self.local_conn.row_factory = sqlite3.Row

            # Enable WAL mode for better concurrency
            self.local_conn.execute("PRAGMA journal_mode=WAL")
            self.local_conn.execute("PRAGMA synchronous=NORMAL")
            self.local_conn.execute("PRAGMA cache_size=10000")
            self.local_conn.execute("PRAGMA temp_store=MEMORY")

            # Create tables
            self._create_local_tables()

            self._notify("Local database initialized", level="info")
            LOGGER.info("Local database initialized: %s", self.local_db_path)
        except Exception as e:
            LOGGER.error("Failed to initialize local database: %s", e)
            self._notify(f"Local database error: {str(e)}", level="error")

    def _init_cloud_db(self) -> None:
        """Initialize cloud database connection."""
        if not POSTGRES_AVAILABLE:
            LOGGER.warning("PostgreSQL driver not available, cloud database disabled")
            self._notify("Cloud database unavailable (driver missing)", level="warning")
            return

        try:
            if self.config.cloud_type == "postgresql":
                self.cloud_pool = pool.ThreadedConnectionPool(
                    1,
                    self.config.connection_pool_size,
                    host=self.config.cloud_host,
                    port=self.config.cloud_port,
                    database=self.config.cloud_database,
                    user=self.config.cloud_user,
                    password=self.config.cloud_password,
                    sslmode="require" if self.config.cloud_ssl else "prefer",
                )

                # Test connection
                conn = self.cloud_pool.getconn()
                conn.close()
                self.cloud_pool.putconn(conn)

                # Create tables
                self._create_cloud_tables()

                self.cloud_available = True
                self._notify("Cloud database connected", level="info")
                LOGGER.info("Cloud database initialized")
            else:
                LOGGER.warning("Unsupported cloud database type: %s", self.config.cloud_type)
        except Exception as e:
            LOGGER.error("Failed to initialize cloud database: %s", e)
            self.cloud_available = False
            self._notify(f"Cloud database connection failed: {str(e)}", level="warning")

    def _create_local_tables(self) -> None:
        """Create tables in local database."""
        cursor = self.local_conn.cursor()

        # Telemetry data table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                session_id TEXT,
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                synced INTEGER DEFAULT 0,
                created_at REAL DEFAULT (julianday('now'))
            )
        """
        )

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_synced ON telemetry(synced)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_session ON telemetry(session_id)")

        # Sessions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                start_time REAL NOT NULL,
                end_time REAL,
                vehicle_profile TEXT,
                total_samples INTEGER DEFAULT 0,
                synced INTEGER DEFAULT 0
            )
        """
        )

        # Events/notifications table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                event_type TEXT NOT NULL,
                severity TEXT,
                message TEXT,
                component TEXT,
                data TEXT,
                synced INTEGER DEFAULT 0
            )
        """
        )

        # Performance metrics table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                session_id TEXT,
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                synced INTEGER DEFAULT 0
            )
        """
        )

        self.local_conn.commit()

    def _create_cloud_tables(self) -> None:
        """Create tables in cloud database."""
        if not self.cloud_available:
            return

        conn = self.cloud_pool.getconn()
        try:
            cursor = conn.cursor()

            # Telemetry data table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS telemetry (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    session_id TEXT,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """
            )

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_session ON telemetry(session_id)")

            # Sessions table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    vehicle_profile TEXT,
                    total_samples INTEGER DEFAULT 0
                )
            """
            )

            # Events table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT,
                    message TEXT,
                    component TEXT,
                    data JSONB
                )
            """
            )

            # Performance metrics table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    session_id TEXT,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL
                )
            """
            )

            conn.commit()
        finally:
            self.cloud_pool.putconn(conn)

    def _notify(self, message: str, level: str = "info") -> None:
        """Send notification via callback."""
        if self.notification_callback:
            try:
                self.notification_callback(message, level)
            except Exception as e:
                LOGGER.error("Error in notification callback: %s", e)

    @contextmanager
    def get_connection(self, prefer_cloud: bool = False):
        """
        Get database connection with automatic failover.

        Args:
            prefer_cloud: Prefer cloud if available

        Yields:
            Database connection
        """
        # Try cloud first if preferred and available
        if prefer_cloud and self.cloud_available:
            try:
                conn = self.cloud_pool.getconn()
                try:
                    yield (conn, DatabaseType.CLOUD)
                finally:
                    self.cloud_pool.putconn(conn)
                return
            except Exception as e:
                LOGGER.warning("Cloud database unavailable, falling back to local: %s", e)
                self.cloud_available = False
                self._notify("Switched to local database", level="warning")

        # Use local database
        if self.local_conn:
            yield (self.local_conn, DatabaseType.LOCAL)
        else:
            raise RuntimeError("No database connection available")

    def insert_telemetry(
        self,
        session_id: str,
        timestamp: float,
        metrics: Dict[str, float],
        sync_to_cloud: bool = True,
    ) -> bool:
        """
        Insert telemetry data.

        Args:
            session_id: Session identifier
            timestamp: Timestamp
            metrics: Dictionary of metric values
            sync_to_cloud: Whether to sync to cloud

        Returns:
            True if inserted successfully
        """
        try:
            with self.get_connection() as (conn, db_type):
                if db_type == DatabaseType.LOCAL:
                    cursor = conn.cursor()
                    for metric_name, value in metrics.items():
                        cursor.execute(
                            """
                            INSERT INTO telemetry (timestamp, session_id, metric_name, value, synced)
                            VALUES (?, ?, ?, ?, ?)
                        """,
                            (timestamp, session_id, metric_name, value, 0 if sync_to_cloud else 1),
                        )
                    conn.commit()
                    return True
                else:  # Cloud
                    cursor = conn.cursor()
                    for metric_name, value in metrics.items():
                        cursor.execute(
                            """
                            INSERT INTO telemetry (timestamp, session_id, metric_name, value)
                            VALUES (to_timestamp(%s), %s, %s, %s)
                        """,
                            (timestamp, session_id, metric_name, value),
                        )
                    conn.commit()
                    return True
        except (sqlite3.Error, psycopg2.Error if POSTGRES_AVAILABLE else Exception) as e:
            LOGGER.error("Failed to insert telemetry: %s", e, exc_info=True)
            return False
        except Exception as e:
            LOGGER.error("Unexpected error inserting telemetry: %s", e, exc_info=True)
            return False

    def query_telemetry(
        self,
        session_id: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        metric_names: Optional[List[str]] = None,
        limit: int = 1000,
        use_cloud: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Query telemetry data.

        Args:
            session_id: Filter by session ID
            start_time: Start timestamp
            end_time: End timestamp
            metric_names: Filter by metric names
            limit: Maximum results
            use_cloud: Use cloud database if available

        Returns:
            List of telemetry records
        """
        try:
            with self.get_connection(prefer_cloud=use_cloud) as (conn, db_type):
                if db_type == DatabaseType.LOCAL:
                    query = "SELECT * FROM telemetry WHERE 1=1"
                    params = []

                    if session_id:
                        query += " AND session_id = ?"
                        params.append(session_id)

                    if start_time:
                        query += " AND timestamp >= ?"
                        params.append(start_time)

                    if end_time:
                        query += " AND timestamp <= ?"
                        params.append(end_time)

                    if metric_names:
                        placeholders = ",".join("?" * len(metric_names))
                        query += f" AND metric_name IN ({placeholders})"
                        params.extend(metric_names)

                    query += " ORDER BY timestamp DESC LIMIT ?"
                    params.append(limit)

                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    rows = cursor.fetchall()

                    return [dict(row) for row in rows]
                else:  # Cloud
                    query = "SELECT * FROM telemetry WHERE 1=1"
                    params = []

                    if session_id:
                        query += " AND session_id = %s"
                        params.append(session_id)

                    if start_time:
                        query += " AND timestamp >= to_timestamp(%s)"
                        params.append(start_time)

                    if end_time:
                        query += " AND timestamp <= to_timestamp(%s)"
                        params.append(end_time)

                    if metric_names:
                        placeholders = ",".join("%s" * len(metric_names))
                        query += f" AND metric_name IN ({placeholders})"
                        params.extend(metric_names)

                    query += " ORDER BY timestamp DESC LIMIT %s"
                    params.append(limit)

                    cursor = conn.cursor(cursor_factory=RealDictCursor)
                    cursor.execute(query, params)
                    rows = cursor.fetchall()

                    return [dict(row) for row in rows]
        except (sqlite3.Error, psycopg2.Error if POSTGRES_AVAILABLE else Exception) as e:
            LOGGER.error("Failed to query telemetry: %s", e, exc_info=True)
            return []
        except Exception as e:
            LOGGER.error("Unexpected error querying telemetry: %s", e, exc_info=True)
            return []

    def insert_event(
        self,
        event_type: str,
        message: str,
        severity: str = "info",
        component: str = "",
        data: Optional[Dict] = None,
    ) -> bool:
        """
        Insert an event/notification.

        Args:
            event_type: Type of event
            message: Event message
            severity: Severity level
            component: Component name
            data: Additional data

        Returns:
            True if inserted successfully
        """
        timestamp = time.time()

        try:
            with self.get_connection() as (conn, db_type):
                if db_type == DatabaseType.LOCAL:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO events (timestamp, event_type, severity, message, component, data, synced)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            timestamp,
                            event_type,
                            severity,
                            message,
                            component,
                            str(data) if data else None,
                            0 if self.cloud_available else 1,
                        ),
                    )
                    conn.commit()
                else:  # Cloud
                    import json

                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO events (timestamp, event_type, severity, message, component, data)
                        VALUES (to_timestamp(%s), %s, %s, %s, %s, %s)
                    """,
                        (
                            timestamp,
                            event_type,
                            severity,
                            message,
                            component,
                            json.dumps(data) if data else None,
                        ),
                    )
                    conn.commit()

            # Also trigger notification callback
            self._notify(message, level=severity)
            return True
        except Exception as e:
            LOGGER.error("Failed to insert event: %s", e)
            return False

    def _start_sync_thread(self) -> None:
        """Start background sync thread."""
        if self.syncing:
            return

        self.syncing = True
        self.sync_thread = threading.Thread(target=self._sync_worker, daemon=True)
        self.sync_thread.start()
        LOGGER.info("Started database sync thread")

    def _sync_worker(self) -> None:
        """Background worker that syncs local to cloud."""
        while self.syncing:
            try:
                if not self.cloud_available:
                    time.sleep(self.config.sync_interval)
                    continue

                # Sync unsynced telemetry
                self._sync_telemetry()

                # Sync unsynced events
                self._sync_events()

                # Sync unsynced sessions
                self._sync_sessions()

                time.sleep(self.config.sync_interval)
            except Exception as e:
                LOGGER.error("Error in sync worker: %s", e)
                time.sleep(self.config.sync_interval)

    def _sync_telemetry(self) -> None:
        """Sync unsynced telemetry to cloud."""
        if not self.local_conn or not self.cloud_available:
            return

        try:
            cursor = self.local_conn.cursor()
            cursor.execute("SELECT * FROM telemetry WHERE synced = 0 LIMIT 100")
            rows = cursor.fetchall()

            if not rows:
                return

            conn = self.cloud_pool.getconn()
            try:
                cloud_cursor = conn.cursor()
                for row in rows:
                    cloud_cursor.execute(
                        """
                        INSERT INTO telemetry (timestamp, session_id, metric_name, value)
                        VALUES (to_timestamp(%s), %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """,
                        (row["timestamp"], row["session_id"], row["metric_name"], row["value"]),
                    )

                conn.commit()

                # Mark as synced
                ids = [row["id"] for row in rows]
                placeholders = ",".join("?" * len(ids))
                cursor.execute(f"UPDATE telemetry SET synced = 1 WHERE id IN ({placeholders})", ids)
                self.local_conn.commit()

                LOGGER.debug("Synced %d telemetry records", len(rows))
            finally:
                self.cloud_pool.putconn(conn)
        except Exception as e:
            LOGGER.error("Failed to sync telemetry: %s", e)

    def _sync_events(self) -> None:
        """Sync unsynced events to cloud."""
        if not self.local_conn or not self.cloud_available:
            return

        try:
            cursor = self.local_conn.cursor()
            cursor.execute("SELECT * FROM events WHERE synced = 0 LIMIT 100")
            rows = cursor.fetchall()

            if not rows:
                return

            conn = self.cloud_pool.getconn()
            try:
                import json

                cloud_cursor = conn.cursor()
                for row in rows:
                    data = json.loads(row["data"]) if row["data"] else None
                    cloud_cursor.execute(
                        """
                        INSERT INTO events (timestamp, event_type, severity, message, component, data)
                        VALUES (to_timestamp(%s), %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """,
                        (
                            row["timestamp"],
                            row["event_type"],
                            row["severity"],
                            row["message"],
                            row["component"],
                            json.dumps(data) if data else None,
                        ),
                    )

                conn.commit()

                # Mark as synced
                ids = [row["id"] for row in rows]
                placeholders = ",".join("?" * len(ids))
                cursor.execute(f"UPDATE events SET synced = 1 WHERE id IN ({placeholders})", ids)
                self.local_conn.commit()

                LOGGER.debug("Synced %d events", len(rows))
            finally:
                self.cloud_pool.putconn(conn)
        except Exception as e:
            LOGGER.error("Failed to sync events: %s", e)

    def _sync_sessions(self) -> None:
        """Sync unsynced sessions to cloud."""
        if not self.local_conn or not self.cloud_available:
            return

        try:
            cursor = self.local_conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE synced = 0")
            rows = cursor.fetchall()

            if not rows:
                return

            conn = self.cloud_pool.getconn()
            try:
                cloud_cursor = conn.cursor()
                for row in rows:
                    cloud_cursor.execute(
                        """
                        INSERT INTO sessions (session_id, start_time, end_time, vehicle_profile, total_samples)
                        VALUES (%s, to_timestamp(%s), to_timestamp(%s), %s, %s)
                        ON CONFLICT (session_id) DO UPDATE
                        SET end_time = EXCLUDED.end_time, total_samples = EXCLUDED.total_samples
                    """,
                        (
                            row["session_id"],
                            row["start_time"],
                            row["end_time"],
                            row["vehicle_profile"],
                            row["total_samples"],
                        ),
                    )

                conn.commit()

                # Mark as synced
                session_ids = [row["session_id"] for row in rows]
                placeholders = ",".join("?" * len(session_ids))
                cursor.execute(f"UPDATE sessions SET synced = 1 WHERE session_id IN ({placeholders})", session_ids)
                self.local_conn.commit()

                LOGGER.debug("Synced %d sessions", len(rows))
            finally:
                self.cloud_pool.putconn(conn)
        except Exception as e:
            LOGGER.error("Failed to sync sessions: %s", e)

    def close(self) -> None:
        """Close database connections."""
        self.syncing = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)

        if self.local_conn:
            self.local_conn.close()

        if self.cloud_pool:
            self.cloud_pool.closeall()


__all__ = ["DatabaseManager", "DatabaseConfig", "DatabaseType"]

