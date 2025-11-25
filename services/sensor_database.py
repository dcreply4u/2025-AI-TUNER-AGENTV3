"""
Sensor Database

SQLite database for storing:
- Sensor configurations
- Calibration data
- Historical readings
- Sensor metadata
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

LOGGER = logging.getLogger(__name__)


@dataclass
class SensorConfig:
    """Sensor configuration."""
    name: str
    sensor_type: str  # analog, digital, can, serial
    channel: Optional[int] = None
    pin: Optional[int] = None
    unit: str = ""
    min_value: float = 0.0
    max_value: float = 100.0
    calibration_offset: float = 0.0
    calibration_scale: float = 1.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SensorReading:
    """Sensor reading record."""
    sensor_name: str
    value: float
    timestamp: float
    unit: str = ""
    quality: float = 1.0  # 0.0-1.0, data quality indicator


class SensorDatabase:
    """SQLite database for sensor data."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """
        Initialize sensor database.
        
        Args:
            db_path: Path to database file (default: data/sensors.db)
        """
        if db_path is None:
            db_path = Path("data") / "sensors.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sensor configurations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_configs (
                name TEXT PRIMARY KEY,
                sensor_type TEXT NOT NULL,
                channel INTEGER,
                pin INTEGER,
                unit TEXT,
                min_value REAL,
                max_value REAL,
                calibration_offset REAL DEFAULT 0.0,
                calibration_scale REAL DEFAULT 1.0,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Sensor readings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_name TEXT NOT NULL,
                value REAL NOT NULL,
                timestamp REAL NOT NULL,
                unit TEXT,
                quality REAL DEFAULT 1.0,
                FOREIGN KEY (sensor_name) REFERENCES sensor_configs(name)
            )
        """)
        
        # Calibration history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calibration_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_name TEXT NOT NULL,
                offset REAL,
                scale REAL,
                reference_value REAL,
                measured_value REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (sensor_name) REFERENCES sensor_configs(name)
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_readings_sensor_time 
            ON sensor_readings(sensor_name, timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_readings_timestamp 
            ON sensor_readings(timestamp)
        """)
        
        conn.commit()
        conn.close()
        
        LOGGER.info("Sensor database initialized: %s", self.db_path)

    def add_sensor_config(self, config: SensorConfig) -> bool:
        """
        Add or update sensor configuration.
        
        Args:
            config: Sensor configuration
            
        Returns:
            True if successful
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            metadata_json = json.dumps(config.metadata) if config.metadata else "{}"
            
            cursor.execute("""
                INSERT OR REPLACE INTO sensor_configs 
                (name, sensor_type, channel, pin, unit, min_value, max_value,
                 calibration_offset, calibration_scale, metadata, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                config.name,
                config.sensor_type,
                config.channel,
                config.pin,
                config.unit,
                config.min_value,
                config.max_value,
                config.calibration_offset,
                config.calibration_scale,
                metadata_json,
            ))
            
            conn.commit()
            LOGGER.info("Added sensor config: %s", config.name)
            return True
        except Exception as e:
            LOGGER.error("Failed to add sensor config: %s", e)
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_sensor_config(self, name: str) -> Optional[SensorConfig]:
        """
        Get sensor configuration.
        
        Args:
            name: Sensor name
            
        Returns:
            SensorConfig or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT name, sensor_type, channel, pin, unit, min_value, max_value,
                       calibration_offset, calibration_scale, metadata
                FROM sensor_configs
                WHERE name = ?
            """, (name,))
            
            row = cursor.fetchone()
            if row:
                metadata = json.loads(row[9]) if row[9] else {}
                return SensorConfig(
                    name=row[0],
                    sensor_type=row[1],
                    channel=row[2],
                    pin=row[3],
                    unit=row[4] or "",
                    min_value=row[5],
                    max_value=row[6],
                    calibration_offset=row[7],
                    calibration_scale=row[8],
                    metadata=metadata,
                )
            return None
        except Exception as e:
            LOGGER.error("Failed to get sensor config: %s", e)
            return None
        finally:
            conn.close()

    def list_sensor_configs(self, sensor_type: Optional[str] = None) -> List[SensorConfig]:
        """
        List all sensor configurations.
        
        Args:
            sensor_type: Filter by sensor type (optional)
            
        Returns:
            List of SensorConfig
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if sensor_type:
                cursor.execute("""
                    SELECT name, sensor_type, channel, pin, unit, min_value, max_value,
                           calibration_offset, calibration_scale, metadata
                    FROM sensor_configs
                    WHERE sensor_type = ?
                    ORDER BY name
                """, (sensor_type,))
            else:
                cursor.execute("""
                    SELECT name, sensor_type, channel, pin, unit, min_value, max_value,
                           calibration_offset, calibration_scale, metadata
                    FROM sensor_configs
                    ORDER BY name
                """)
            
            configs = []
            for row in cursor.fetchall():
                metadata = json.loads(row[9]) if row[9] else {}
                configs.append(SensorConfig(
                    name=row[0],
                    sensor_type=row[1],
                    channel=row[2],
                    pin=row[3],
                    unit=row[4] or "",
                    min_value=row[5],
                    max_value=row[6],
                    calibration_offset=row[7],
                    calibration_scale=row[8],
                    metadata=metadata,
                ))
            
            return configs
        except Exception as e:
            LOGGER.error("Failed to list sensor configs: %s", e)
            return []
        finally:
            conn.close()

    def add_reading(self, reading: SensorReading) -> bool:
        """
        Add sensor reading.
        
        Args:
            reading: Sensor reading
            
        Returns:
            True if successful
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO sensor_readings 
                (sensor_name, value, timestamp, unit, quality)
                VALUES (?, ?, ?, ?, ?)
            """, (
                reading.sensor_name,
                reading.value,
                reading.timestamp,
                reading.unit,
                reading.quality,
            ))
            
            conn.commit()
            return True
        except Exception as e:
            LOGGER.error("Failed to add reading: %s", e)
            conn.rollback()
            return False
        finally:
            conn.close()

    def add_readings_batch(self, readings: List[SensorReading]) -> int:
        """
        Add multiple readings in batch.
        
        Args:
            readings: List of sensor readings
            
        Returns:
            Number of readings added
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.executemany("""
                INSERT INTO sensor_readings 
                (sensor_name, value, timestamp, unit, quality)
                VALUES (?, ?, ?, ?, ?)
            """, [
                (r.sensor_name, r.value, r.timestamp, r.unit, r.quality)
                for r in readings
            ])
            
            conn.commit()
            count = len(readings)
            LOGGER.debug("Added %d readings to database", count)
            return count
        except Exception as e:
            LOGGER.error("Failed to add readings batch: %s", e)
            conn.rollback()
            return 0
        finally:
            conn.close()

    def get_readings(self, sensor_name: str, 
                    start_time: Optional[float] = None,
                    end_time: Optional[float] = None,
                    limit: Optional[int] = None) -> List[SensorReading]:
        """
        Get sensor readings.
        
        Args:
            sensor_name: Sensor name
            start_time: Start timestamp (optional)
            end_time: End timestamp (optional)
            limit: Maximum number of readings (optional)
            
        Returns:
            List of SensorReading
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT sensor_name, value, timestamp, unit, quality
                FROM sensor_readings
                WHERE sensor_name = ?
            """
            params = [sensor_name]
            
            if start_time is not None:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time is not None:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            query += " ORDER BY timestamp DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor.execute(query, params)
            
            readings = []
            for row in cursor.fetchall():
                readings.append(SensorReading(
                    sensor_name=row[0],
                    value=row[1],
                    timestamp=row[2],
                    unit=row[3] or "",
                    quality=row[4],
                ))
            
            return readings
        except Exception as e:
            LOGGER.error("Failed to get readings: %s", e)
            return []
        finally:
            conn.close()

    def update_calibration(self, sensor_name: str, offset: float, scale: float,
                          reference_value: Optional[float] = None,
                          measured_value: Optional[float] = None,
                          notes: Optional[str] = None) -> bool:
        """
        Update sensor calibration.
        
        Args:
            sensor_name: Sensor name
            offset: Calibration offset
            scale: Calibration scale
            reference_value: Reference value (optional)
            measured_value: Measured value (optional)
            notes: Calibration notes (optional)
            
        Returns:
            True if successful
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Update sensor config
            cursor.execute("""
                UPDATE sensor_configs
                SET calibration_offset = ?, calibration_scale = ?, updated_at = CURRENT_TIMESTAMP
                WHERE name = ?
            """, (offset, scale, sensor_name))
            
            # Add to calibration history
            cursor.execute("""
                INSERT INTO calibration_history
                (sensor_name, offset, scale, reference_value, measured_value, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sensor_name, offset, scale, reference_value, measured_value, notes))
            
            conn.commit()
            LOGGER.info("Updated calibration for sensor: %s", sensor_name)
            return True
        except Exception as e:
            LOGGER.error("Failed to update calibration: %s", e)
            conn.rollback()
            return False
        finally:
            conn.close()

    def delete_sensor(self, name: str) -> bool:
        """
        Delete sensor configuration and all associated data.
        
        Args:
            name: Sensor name
            
        Returns:
            True if successful
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Delete readings
            cursor.execute("DELETE FROM sensor_readings WHERE sensor_name = ?", (name,))
            
            # Delete calibration history
            cursor.execute("DELETE FROM calibration_history WHERE sensor_name = ?", (name,))
            
            # Delete config
            cursor.execute("DELETE FROM sensor_configs WHERE name = ?", (name,))
            
            conn.commit()
            LOGGER.info("Deleted sensor: %s", name)
            return True
        except Exception as e:
            LOGGER.error("Failed to delete sensor: %s", e)
            conn.rollback()
            return False
        finally:
            conn.close()


# Global database instance
_db_instance: Optional[SensorDatabase] = None


def get_sensor_database(db_path: Optional[Path] = None) -> SensorDatabase:
    """
    Get or create global sensor database instance.
    
    Args:
        db_path: Path to database file (optional)
        
    Returns:
        SensorDatabase instance
    """
    global _db_instance
    
    if _db_instance is None:
        _db_instance = SensorDatabase(db_path)
    
    return _db_instance


__all__ = [
    "SensorDatabase",
    "SensorConfig",
    "SensorReading",
    "get_sensor_database",
]






