"""
Analog Sensor Interface

Handles analog sensors connected via ADC (Analog-to-Digital Converter).
Supports I2C and SPI ADC boards.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

try:
    import board
    import busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    ADAFRUIT_AVAILABLE = True
except ImportError:
    ADAFRUIT_AVAILABLE = False
    # Fallback for testing
    board = None  # type: ignore
    busio = None  # type: ignore
    ADS = None  # type: ignore
    AnalogIn = None  # type: ignore

try:
    import RPi.GPIO as GPIO
    RPI_GPIO_AVAILABLE = True
except ImportError:
    RPI_GPIO_AVAILABLE = False
    GPIO = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class SensorType(Enum):
    """Types of analog sensors."""

    PRESSURE = "pressure"
    TEMPERATURE = "temperature"
    VOLTAGE = "voltage"
    CURRENT = "current"
    POSITION = "position"
    GENERIC = "generic"


@dataclass
class AnalogSensorConfig:
    """Configuration for an analog sensor."""

    name: str
    channel: int  # ADC channel (0-3 for ADS1115)
    sensor_type: SensorType
    min_voltage: float = 0.0  # Voltage at minimum value
    max_voltage: float = 5.0  # Voltage at maximum value
    min_value: float = 0.0  # Minimum sensor value
    max_value: float = 100.0  # Maximum sensor value
    unit: str = ""
    offset: float = 0.0  # Calibration offset
    scale: float = 1.0  # Calibration scale factor


class AnalogSensorInterface:
    """Interface for analog sensors via ADC."""

    def __init__(
        self,
        config: AnalogSensorConfig,
        i2c_address: int = 0x48,
        adc_type: str = "ADS1115",
    ) -> None:
        """
        Initialize analog sensor interface.

        Args:
            config: Sensor configuration
            i2c_address: I2C address of ADC board
            adc_type: Type of ADC (ADS1115, ADS1015, MCP3008, etc.)
        """
        self.config = config
        self.i2c_address = i2c_address
        self.adc_type = adc_type
        self.channel: Optional[AnalogIn] = None
        self.i2c: Optional[Any] = None
        self.ads: Optional[Any] = None

        if ADAFRUIT_AVAILABLE:
            self._init_adc()

    def _init_adc(self) -> None:
        """Initialize ADC board."""
        try:
            # Initialize I2C bus
            self.i2c = busio.I2C(board.SCL, board.SDA)

            # Initialize ADC
            if self.adc_type == "ADS1115":
                self.ads = ADS.ADS1115(self.i2c, address=self.i2c_address)
            else:
                LOGGER.warning("Unsupported ADC type: %s", self.adc_type)
                return

            # Create analog input channel
            channel_map = {
                0: ADS.P0,
                1: ADS.P1,
                2: ADS.P2,
                3: ADS.P3,
            }
            adc_channel = channel_map.get(self.config.channel, ADS.P0)
            self.channel = AnalogIn(self.ads, adc_channel)

            LOGGER.info("Initialized analog sensor %s on channel %d", self.config.name, self.config.channel)
        except Exception as e:
            LOGGER.error("Failed to initialize ADC: %s", e)
            self.channel = None

    def read_voltage(self) -> Optional[float]:
        """
        Read raw voltage from sensor.

        Returns:
            Voltage in volts, or None if read failed
        """
        if not self.channel:
            return None

        try:
            return self.channel.voltage
        except Exception as e:
            LOGGER.error("Failed to read voltage from %s: %s", self.config.name, e)
            return None

    def read(self) -> Optional[float]:
        """
        Read sensor value in configured units.

        Returns:
            Sensor value in configured units, or None if read failed
        """
        voltage = self.read_voltage()
        if voltage is None:
            return None

        # Map voltage to sensor value
        voltage_range = self.config.max_voltage - self.config.min_voltage
        if voltage_range == 0:
            return None

        # Linear interpolation
        normalized = (voltage - self.config.min_voltage) / voltage_range
        value = self.config.min_value + normalized * (self.config.max_value - self.config.min_value)

        # Apply calibration
        value = (value + self.config.offset) * self.config.scale

        return value

    def calibrate(self, known_value: float) -> None:
        """
        Calibrate sensor with known value.

        Args:
            known_value: Known sensor value for calibration
        """
        voltage = self.read_voltage()
        if voltage is None:
            return

        # Calculate offset
        expected_voltage = (
            self.config.min_voltage
            + ((known_value - self.config.min_value) / (self.config.max_value - self.config.min_value))
            * (self.config.max_voltage - self.config.min_voltage)
        )
        self.config.offset = voltage - expected_voltage
        LOGGER.info("Calibrated %s: offset = %.3f", self.config.name, self.config.offset)


class AnalogSensorManager:
    """Manages multiple analog sensors."""

    def __init__(self) -> None:
        """Initialize sensor manager."""
        self.sensors: dict[str, AnalogSensorInterface] = {}

    def add_sensor(self, config: AnalogSensorConfig) -> bool:
        """
        Add an analog sensor.

        Args:
            config: Sensor configuration

        Returns:
            True if added successfully
        """
        try:
            sensor = AnalogSensorInterface(config)
            self.sensors[config.name] = sensor
            return True
        except Exception as e:
            LOGGER.error("Failed to add sensor %s: %s", config.name, e)
            return False

    def read_sensor(self, name: str) -> Optional[float]:
        """
        Read value from a sensor.

        Args:
            name: Sensor name

        Returns:
            Sensor value or None
        """
        sensor = self.sensors.get(name)
        if sensor:
            return sensor.read()
        return None

    def read_all(self) -> dict[str, Optional[float]]:
        """
        Read all sensors.

        Returns:
            Dictionary of sensor values
        """
        return {name: sensor.read() for name, sensor in self.sensors.items()}


__all__ = [
    "AnalogSensorInterface",
    "AnalogSensorConfig",
    "AnalogSensorManager",
    "SensorType",
]

