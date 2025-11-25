"""
Adapter Database

SQLite database for storing:
- GPIO adapter configurations
- OBD2 adapter configurations
- Serial adapter configurations
- Adapter capabilities and features
- Connection history
- Performance metrics
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any

LOGGER = logging.getLogger(__name__)


class AdapterType(str, Enum):
    """Adapter type enumeration."""
    GPIO = "gpio"
    OBD2 = "obd2"
    SERIAL = "serial"
    CAN = "can"
    I2C = "i2c"
    SPI = "spi"


class ConnectionType(str, Enum):
    """Connection type enumeration."""
    USB = "usb"
    WIRELESS = "wireless"
    BLUETOOTH = "bluetooth"
    ETHERNET = "ethernet"
    WIFI = "wifi"
    BUILTIN = "builtin"


@dataclass
class AdapterCapabilities:
    """Adapter capabilities."""
    max_gpio_pins: int = 0
    max_adc_channels: int = 0
    max_pwm_channels: int = 0
    supports_i2c: bool = False
    supports_spi: bool = False
    supports_uart: bool = False
    supports_can: bool = False
    max_baud_rate: int = 0
    voltage_levels: List[str] = None  # e.g., ["3.3V", "5V"]
    protocols: List[str] = None  # e.g., ["OBD2", "CAN", "J1939"]
    
    def __post_init__(self):
        if self.voltage_levels is None:
            self.voltage_levels = []
        if self.protocols is None:
            self.protocols = []


@dataclass
class AdapterConfig:
    """Adapter configuration."""
    name: str
    adapter_type: AdapterType
    connection_type: ConnectionType
    vendor: str
    model: str
    serial_number: Optional[str] = None
    device_path: Optional[str] = None  # /dev/ttyUSB0, COM3, etc.
    capabilities: Optional[AdapterCapabilities] = None
    driver: Optional[str] = None  # Driver module name
    metadata: Dict[str, Any] = None
    enabled: bool = True
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = AdapterCapabilities()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AdapterConnection:
    """Adapter connection record."""
    adapter_name: str
    connected_at: float
    disconnected_at: Optional[float] = None
    connection_duration: Optional[float] = None
    status: str = "connected"  # connected, disconnected, error
    error_count: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    messages_sent: int = 0
    messages_received: int = 0


class AdapterDatabase:
    """SQLite database for adapter management."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """
        Initialize adapter database.
        
        Args:
            db_path: Path to database file (default: data/adapters.db)
        """
        if db_path is None:
            db_path = Path("data") / "adapters.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Adapter configurations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS adapters (
                name TEXT PRIMARY KEY,
                adapter_type TEXT NOT NULL,
                connection_type TEXT NOT NULL,
                vendor TEXT NOT NULL,
                model TEXT NOT NULL,
                serial_number TEXT,
                device_path TEXT,
                capabilities TEXT,
                driver TEXT,
                metadata TEXT,
                enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Connection history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS connection_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                adapter_name TEXT NOT NULL,
                connected_at REAL NOT NULL,
                disconnected_at REAL,
                connection_duration REAL,
                status TEXT DEFAULT 'connected',
                error_count INTEGER DEFAULT 0,
                bytes_sent INTEGER DEFAULT 0,
                bytes_received INTEGER DEFAULT 0,
                messages_sent INTEGER DEFAULT 0,
                messages_received INTEGER DEFAULT 0,
                FOREIGN KEY (adapter_name) REFERENCES adapters(name)
            )
        """)
        
        # Performance metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                adapter_name TEXT NOT NULL,
                timestamp REAL NOT NULL,
                latency_ms REAL,
                throughput_bytes_per_sec REAL,
                error_rate REAL,
                cpu_usage REAL,
                memory_usage REAL,
                FOREIGN KEY (adapter_name) REFERENCES adapters(name)
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_adapters_type 
            ON adapters(adapter_type)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_connections_adapter 
            ON connection_history(adapter_name, connected_at)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_metrics_adapter_time 
            ON performance_metrics(adapter_name, timestamp)
        """)
        
        conn.commit()
        conn.close()
        
        LOGGER.info("Adapter database initialized: %s", self.db_path)

    def add_adapter(self, config: AdapterConfig) -> bool:
        """Add or update adapter configuration."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            capabilities_json = json.dumps(asdict(config.capabilities)) if config.capabilities else "{}"
            metadata_json = json.dumps(config.metadata) if config.metadata else "{}"
            
            cursor.execute("""
                INSERT OR REPLACE INTO adapters 
                (name, adapter_type, connection_type, vendor, model, serial_number,
                 device_path, capabilities, driver, metadata, enabled, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                config.name,
                config.adapter_type.value,
                config.connection_type.value,
                config.vendor,
                config.model,
                config.serial_number,
                config.device_path,
                capabilities_json,
                config.driver,
                metadata_json,
                1 if config.enabled else 0,
            ))
            
            conn.commit()
            LOGGER.info("Added adapter: %s (%s %s)", config.name, config.vendor, config.model)
            return True
        except Exception as e:
            LOGGER.error("Failed to add adapter: %s", e)
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_adapter(self, name: str) -> Optional[AdapterConfig]:
        """Get adapter configuration."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT name, adapter_type, connection_type, vendor, model, serial_number,
                       device_path, capabilities, driver, metadata, enabled
                FROM adapters
                WHERE name = ?
            """, (name,))
            
            row = cursor.fetchone()
            if row:
                capabilities = json.loads(row[7]) if row[7] else {}
                metadata = json.loads(row[9]) if row[9] else {}
                
                return AdapterConfig(
                    name=row[0],
                    adapter_type=AdapterType(row[1]),
                    connection_type=ConnectionType(row[2]),
                    vendor=row[3],
                    model=row[4],
                    serial_number=row[5],
                    device_path=row[6],
                    capabilities=AdapterCapabilities(**capabilities) if capabilities else AdapterCapabilities(),
                    driver=row[8],
                    metadata=metadata,
                    enabled=bool(row[10]),
                )
            return None
        except Exception as e:
            LOGGER.error("Failed to get adapter: %s", e)
            return None
        finally:
            conn.close()

    def list_adapters(self, adapter_type: Optional[AdapterType] = None,
                     enabled_only: bool = False) -> List[AdapterConfig]:
        """List all adapters."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if adapter_type:
                if enabled_only:
                    cursor.execute("""
                        SELECT name, adapter_type, connection_type, vendor, model, serial_number,
                               device_path, capabilities, driver, metadata, enabled
                        FROM adapters
                        WHERE adapter_type = ? AND enabled = 1
                        ORDER BY name
                    """, (adapter_type.value,))
                else:
                    cursor.execute("""
                        SELECT name, adapter_type, connection_type, vendor, model, serial_number,
                               device_path, capabilities, driver, metadata, enabled
                        FROM adapters
                        WHERE adapter_type = ?
                        ORDER BY name
                    """, (adapter_type.value,))
            else:
                if enabled_only:
                    cursor.execute("""
                        SELECT name, adapter_type, connection_type, vendor, model, serial_number,
                               device_path, capabilities, driver, metadata, enabled
                        FROM adapters
                        WHERE enabled = 1
                        ORDER BY name
                    """)
                else:
                    cursor.execute("""
                        SELECT name, adapter_type, connection_type, vendor, model, serial_number,
                               device_path, capabilities, driver, metadata, enabled
                        FROM adapters
                        ORDER BY name
                    """)
            
            adapters = []
            for row in cursor.fetchall():
                capabilities = json.loads(row[7]) if row[7] else {}
                metadata = json.loads(row[9]) if row[9] else {}
                
                adapters.append(AdapterConfig(
                    name=row[0],
                    adapter_type=AdapterType(row[1]),
                    connection_type=ConnectionType(row[2]),
                    vendor=row[3],
                    model=row[4],
                    serial_number=row[5],
                    device_path=row[6],
                    capabilities=AdapterCapabilities(**capabilities) if capabilities else AdapterCapabilities(),
                    driver=row[8],
                    metadata=metadata,
                    enabled=bool(row[10]),
                ))
            
            return adapters
        except Exception as e:
            LOGGER.error("Failed to list adapters: %s", e)
            return []
        finally:
            conn.close()

    def log_connection(self, connection: AdapterConnection) -> bool:
        """Log adapter connection."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO connection_history
                (adapter_name, connected_at, disconnected_at, connection_duration,
                 status, error_count, bytes_sent, bytes_received, messages_sent, messages_received)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                connection.adapter_name,
                connection.connected_at,
                connection.disconnected_at,
                connection.connection_duration,
                connection.status,
                connection.error_count,
                connection.bytes_sent,
                connection.bytes_received,
                connection.messages_sent,
                connection.messages_received,
            ))
            
            conn.commit()
            return True
        except Exception as e:
            LOGGER.error("Failed to log connection: %s", e)
            conn.rollback()
            return False
        finally:
            conn.close()

    def log_performance_metric(self, adapter_name: str, latency_ms: Optional[float] = None,
                             throughput: Optional[float] = None, error_rate: Optional[float] = None,
                             cpu_usage: Optional[float] = None, memory_usage: Optional[float] = None) -> bool:
        """Log performance metric."""
        import time
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO performance_metrics
                (adapter_name, timestamp, latency_ms, throughput_bytes_per_sec, 
                 error_rate, cpu_usage, memory_usage)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                adapter_name,
                time.time(),
                latency_ms,
                throughput,
                error_rate,
                cpu_usage,
                memory_usage,
            ))
            
            conn.commit()
            return True
        except Exception as e:
            LOGGER.error("Failed to log performance metric: %s", e)
            conn.rollback()
            return False
        finally:
            conn.close()

    def delete_adapter(self, name: str) -> bool:
        """Delete adapter and all associated data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Delete performance metrics
            cursor.execute("DELETE FROM performance_metrics WHERE adapter_name = ?", (name,))
            
            # Delete connection history
            cursor.execute("DELETE FROM connection_history WHERE adapter_name = ?", (name,))
            
            # Delete adapter
            cursor.execute("DELETE FROM adapters WHERE name = ?", (name,))
            
            conn.commit()
            LOGGER.info("Deleted adapter: %s", name)
            return True
        except Exception as e:
            LOGGER.error("Failed to delete adapter: %s", e)
            conn.rollback()
            return False
        finally:
            conn.close()


# Global database instance
_db_instance: Optional[AdapterDatabase] = None


def get_adapter_database(db_path: Optional[Path] = None) -> AdapterDatabase:
    """Get or create global adapter database instance."""
    global _db_instance
    
    if _db_instance is None:
        _db_instance = AdapterDatabase(db_path)
    
    return _db_instance


__all__ = [
    "AdapterDatabase",
    "AdapterConfig",
    "AdapterCapabilities",
    "AdapterConnection",
    "AdapterType",
    "ConnectionType",
    "get_adapter_database",
]






