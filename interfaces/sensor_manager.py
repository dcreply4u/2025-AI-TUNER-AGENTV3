"""
Unified Sensor Manager

Manages all sensor types (CAN, analog, digital, serial, I2C) in one place.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional, Any

from interfaces.analog_sensor import AnalogSensorConfig, AnalogSensorManager, SensorType
from interfaces.digital_sensor import DigitalSensorConfig, DigitalSensorManager, PullMode
from interfaces.unified_io_manager import get_unified_io_manager, UnifiedIOManager

# Import sensor database
try:
    from services.sensor_database import get_sensor_database, SensorConfig as DBSensorConfig, SensorReading
    SENSOR_DB_AVAILABLE = True
except ImportError:
    SENSOR_DB_AVAILABLE = False
    LOGGER.warning("Sensor database not available")

LOGGER = logging.getLogger(__name__)


class SensorManager:
    """Unified manager for all sensor types."""

    def __init__(self) -> None:
        """Initialize sensor manager."""
        self.analog_manager = AnalogSensorManager()
        self.digital_manager = DigitalSensorManager()
        self.can_interfaces: Dict[str, Any] = {}  # CAN interfaces by channel
        self.serial_interfaces: Dict[str, Any] = {}  # Serial interfaces by port
        
        # Unified I/O manager (for reTerminal DM + Treehopper)
        self.io_manager: Optional[UnifiedIOManager] = None
        try:
            self.io_manager = get_unified_io_manager()
            LOGGER.info("Unified I/O Manager initialized: %d GPIO, %d ADC", 
                       self.io_manager.get_total_gpio_pins(),
                       self.io_manager.get_total_adc_channels())
        except Exception as e:
            LOGGER.warning("Failed to initialize Unified I/O Manager: %s", e)
        
        # Sensor database
        self.sensor_db = None
        if SENSOR_DB_AVAILABLE:
            try:
                self.sensor_db = get_sensor_database()
                LOGGER.info("Sensor database initialized")
            except Exception as e:
                LOGGER.warning("Failed to initialize sensor database: %s", e)

    def add_analog_sensor(self, config: AnalogSensorConfig) -> bool:
        """Add an analog sensor."""
        result = self.analog_manager.add_sensor(config)
        
        # Also save to database
        if result and self.sensor_db:
            try:
                db_config = DBSensorConfig(
                    name=config.name,
                    sensor_type="analog",
                    channel=config.channel,
                    unit=config.unit,
                    min_value=config.min_value,
                    max_value=config.max_value,
                    calibration_offset=config.offset,
                    calibration_scale=1.0,
                    metadata={'sensor_type': config.sensor_type.value if hasattr(config.sensor_type, 'value') else str(config.sensor_type)},
                )
                self.sensor_db.add_sensor_config(db_config)
            except Exception as e:
                LOGGER.warning("Failed to save sensor to database: %s", e)
        
        return result

    def add_digital_sensor(self, config: DigitalSensorConfig) -> bool:
        """Add a digital sensor."""
        return self.digital_manager.add_sensor(config)

    def read_all_sensors(self) -> Dict[str, float | bool]:
        """
        Read all sensors.

        Returns:
            Dictionary of all sensor values
        """
        data = {}

        # Read analog sensors
        analog_data = self.analog_manager.read_all()
        for name, value in analog_data.items():
            if value is not None:
                data[name] = value

        # Read digital sensors
        digital_data = self.digital_manager.read_all()
        for name, value in digital_data.items():
            data[name] = value

        # Read CAN sensors (if any)
        for channel, can_iface in self.can_interfaces.items():
            try:
                can_data = can_iface.read_data()
                for key, value in can_data.items():
                    data[f"CAN_{channel}_{key}"] = value
            except Exception as e:
                LOGGER.error("Error reading CAN channel %s: %s", channel, e)

        return data

    def get_sensor_config_template(self, sensor_type: str) -> Dict:
        """
        Get configuration template for a sensor type.

        Args:
            sensor_type: Type of sensor (analog_pressure, digital_switch, etc.)

        Returns:
            Configuration template dictionary
        """
        if sensor_type.startswith("analog_"):
            sensor_subtype = sensor_type.replace("analog_", "")
            return {
                "name": f"{sensor_subtype}_sensor",
                "channel": 0,
                "sensor_type": sensor_subtype,
                "min_voltage": 0.0,
                "max_voltage": 5.0,
                "min_value": 0.0,
                "max_value": 100.0,
                "unit": "psi" if "pressure" in sensor_subtype else "°C" if "temp" in sensor_subtype else "",
            }
        elif sensor_type.startswith("digital_"):
            return {
                "name": f"{sensor_type.replace('digital_', '')}_switch",
                "pin": 18,
                "pull": "up",
                "active_low": False,
            }
        else:
            return {}


__all__ = ["SensorManager"]

