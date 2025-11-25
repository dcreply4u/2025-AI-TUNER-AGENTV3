"""CAN bus telemetry logger with SQLite storage."""

from __future__ import annotations

import logging
import sqlite3
import time
from pathlib import Path
from threading import Event, Thread
from typing import Iterator

try:
    import can
except ImportError:
    can = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class CANDataLogger:
    """
    CAN bus data logger with SQLite storage and live streaming.

    Logs CAN messages to SQLite database and provides iterator interface.
    """

    def __init__(self, db_path: str | Path = "telemetry/buffer.sqlite", channel: str = "can0", bustype: str = "socketcan") -> None:
        """
        Initialize CAN data logger.

        Args:
            db_path: SQLite database path
            channel: CAN channel name
            bustype: CAN bus type
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.channel = channel
        self.bustype = bustype

        self.conn: sqlite3.Connection | None = None
        self.cursor: sqlite3.Cursor | None = None
        self.bus: "can.Bus | None" = None
        self._active = False
        self._stop_event = Event()
        self._stream_thread: Thread | None = None

        self._init_database()

    def _init_database(self) -> None:
        """Initialize SQLite database schema."""
        try:
            self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self.cursor = self.conn.cursor()
            self.cursor.execute(
                "CREATE TABLE IF NOT EXISTS logs ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "timestamp REAL, "
                "pid TEXT, "
                "value REAL, "
                "data BLOB"
                ")"
            )
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON logs(timestamp)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_pid ON logs(pid)")
            self.conn.commit()
            LOGGER.info("Database initialized: %s", self.db_path)
        except Exception as e:
            LOGGER.error("Failed to initialize database: %s", e)
            raise

    def connect(self) -> bool:
        """Connect to CAN bus."""
        if not can:
            LOGGER.error("python-can not installed")
            return False

        try:
            self.bus = can.interface.Bus(channel=self.channel, bustype=self.bustype)
            LOGGER.info("Connected to CAN bus: %s", self.channel)
            return True
        except Exception as e:
            LOGGER.error("Failed to connect to CAN bus: %s", e)
            return False

    def is_active(self) -> bool:
        """Check if logger is actively streaming."""
        return self._active and self.bus is not None

    def log_pid(self, pid: str, value: float, data: bytes | None = None) -> None:
        """
        Log a PID value to database.

        Args:
            pid: Parameter ID (hex string)
            value: Numeric value
            data: Raw CAN data (optional)
        """
        if not self.cursor:
            return

        try:
            self.cursor.execute(
                "INSERT INTO logs (timestamp, pid, value, data) VALUES (?, ?, ?, ?)",
                (time.time(), pid, value, data),
            )
            self.conn.commit()
        except Exception as e:
            LOGGER.error("Failed to log PID: %s", e)

    def stream(self) -> Iterator["can.Message"]:
        """
        Stream CAN messages (blocking iterator).

        Yields:
            CAN message objects
        """
        if not self.bus and not self.connect():
            raise RuntimeError("Cannot connect to CAN bus")

        self._active = True
        self._stop_event.clear()

        try:
            while not self._stop_event.is_set():
                if not self.bus:
                    break
                msg = self.bus.recv(timeout=0.1)
                if msg:
                    pid = hex(msg.arbitration_id)
                    value = int.from_bytes(msg.data, "big") if msg.data else 0.0
                    self.log_pid(pid, value, msg.data)
                    yield msg
        except KeyboardInterrupt:
            LOGGER.info("Stream interrupted")
        except Exception as e:
            LOGGER.error("Stream error: %s", e)
        finally:
            self._active = False

    def start_background_stream(self) -> None:
        """Start streaming in background thread."""
        if self._stream_thread and self._stream_thread.is_alive():
            return

        self._stream_thread = Thread(target=self._background_stream, daemon=True)
        self._stream_thread.start()
        LOGGER.info("Background stream started")

    def _background_stream(self) -> None:
        """Background streaming thread."""
        try:
            for _ in self.stream():
                if self._stop_event.is_set():
                    break
        except Exception as e:
            LOGGER.error("Background stream error: %s", e)

    def stop(self) -> None:
        """Stop streaming."""
        self._stop_event.set()
        self._active = False
        if self._stream_thread:
            self._stream_thread.join(timeout=2.0)

    def close(self) -> None:
        """Close database and CAN bus connections."""
        self.stop()
        if self.bus:
            self.bus.shutdown()
            self.bus = None
        if self.conn:
            self.conn.close()
            self.conn = None


__all__ = ["CANDataLogger"]

