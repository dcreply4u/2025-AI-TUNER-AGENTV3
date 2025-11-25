"""
Local Buffer Module
Handles local SQLite database buffering for offline telemetry storage
"""

import json
import sqlite3
import time


class LocalBuffer:
    """SQLite-based buffer for storing telemetry data when offline"""
    
    def __init__(self, db_path="telemetry_buffer.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS buffer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                payload TEXT
            )
        """)

    def add(self, payload):
        """Add a payload to the buffer"""
        self.conn.execute(
            "INSERT INTO buffer (timestamp, payload) VALUES (?, ?)",
            (int(time.time()), json.dumps(payload))
        )
        self.conn.commit()

    def flush(self, publisher):
        """Flush buffered data to publisher"""
        cursor = self.conn.execute("SELECT id, payload FROM buffer ORDER BY id ASC")
        rows = cursor.fetchall()
        for row_id, payload in rows:
            if publisher.publish(json.loads(payload)):
                self.conn.execute("DELETE FROM buffer WHERE id=?", (row_id,))
                self.conn.commit()

