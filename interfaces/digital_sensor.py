"""
Digital Sensor Interface

Handles digital sensors (switches, relays, on/off sensors) via GPIO.
"""

from __future__ import annotations

import logging
import platform
from dataclasses import dataclass
from enum import Enum
from typing import Optional

try:
    import RPi.GPIO as GPIO
    RPI_GPIO_AVAILABLE = True
except ImportError:
    try:
        import Jetson.GPIO as GPIO
        RPI_GPIO_AVAILABLE = True
    except ImportError:
        RPI_GPIO_AVAILABLE = False
        GPIO = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class PullMode(Enum):
    """GPIO pull resistor mode."""

    UP = "up"
    DOWN = "down"
    NONE = "none"


@dataclass
class DigitalSensorConfig:
    """Configuration for a digital sensor."""

    name: str
    pin: int  # GPIO pin number
    pull: PullMode = PullMode.UP
    active_low: bool = False  # True if sensor is active when LOW
    debounce_ms: int = 50  # Debounce time in milliseconds


class DigitalSensorInterface:
    """Interface for digital sensors via GPIO."""

    def __init__(self, config: DigitalSensorConfig) -> None:
        """
        Initialize digital sensor interface.

        Args:
            config: Sensor configuration
        """
        self.config = config
        self.initialized = False

        # Check platform and use appropriate GPIO method
        if RPI_GPIO_AVAILABLE:
            self._init_gpio()
        elif platform.system() == "Windows":
            # Use Windows hardware adapter
            self._init_windows_gpio()
        else:
            LOGGER.warning("GPIO not available, digital sensor %s will be simulated", config.name)

    def _init_gpio(self) -> None:
        """Initialize GPIO pin."""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

            # Set pull resistor
            pull_mode = GPIO.PUD_UP if self.config.pull == PullMode.UP else GPIO.PUD_DOWN if self.config.pull == PullMode.DOWN else GPIO.PUD_OFF

            # Configure pin as input
            GPIO.setup(self.config.pin, GPIO.IN, pull_up_down=pull_mode)

            self.initialized = True
            LOGGER.info("Initialized digital sensor %s on pin %d", self.config.name, self.config.pin)
        except Exception as e:
            LOGGER.error("Failed to initialize GPIO pin %d: %s", self.config.pin, e)
            self.initialized = False
    
    def _init_windows_gpio(self) -> None:
        """Initialize GPIO using Windows hardware adapter."""
        # For Windows, GPIO is handled via adapters (Arduino, USB GPIO, etc.)
        # Pin mapping would be configured separately
        # For now, mark as initialized - actual reading will use adapter
        self.initialized = True
        LOGGER.info("Initialized digital sensor %s for Windows adapter (pin %d)", 
                   self.config.name, self.config.pin)

    def read(self) -> bool:
        """
        Read digital sensor state.

        Returns:
            True if sensor is active, False otherwise
        """
        # Try Windows adapter first
        if platform.system() == "Windows" and self.initialized:
            # Would need adapter configuration to map pin to adapter/port
            # For now, return simulated value
            # TODO: Implement adapter pin mapping
            return False
        
        if not RPI_GPIO_AVAILABLE or not self.initialized:
            # Simulate for testing
            return False

        try:
            value = GPIO.input(self.config.pin)
            if self.config.active_low:
                return value == GPIO.LOW
            return value == GPIO.HIGH
        except Exception as e:
            LOGGER.error("Failed to read digital sensor %s: %s", self.config.name, e)
            return False

    def read_raw(self) -> Optional[int]:
        """
        Read raw GPIO value.

        Returns:
            GPIO value (0 or 1), or None if read failed
        """
        if not RPI_GPIO_AVAILABLE or not self.initialized:
            return None

        try:
            return GPIO.input(self.config.pin)
        except Exception as e:
            LOGGER.error("Failed to read raw GPIO pin %d: %s", self.config.pin, e)
            return None

    def cleanup(self) -> None:
        """Cleanup GPIO resources."""
        if RPI_GPIO_AVAILABLE and self.initialized:
            try:
                GPIO.cleanup(self.config.pin)
            except Exception:
                pass


class DigitalSensorManager:
    """Manages multiple digital sensors."""

    def __init__(self) -> None:
        """Initialize sensor manager."""
        self.sensors: dict[str, DigitalSensorInterface] = {}

    def add_sensor(self, config: DigitalSensorConfig) -> bool:
        """
        Add a digital sensor.

        Args:
            config: Sensor configuration

        Returns:
            True if added successfully
        """
        try:
            sensor = DigitalSensorInterface(config)
            self.sensors[config.name] = sensor
            return True
        except Exception as e:
            LOGGER.error("Failed to add digital sensor %s: %s", config.name, e)
            return False

    def read_sensor(self, name: str) -> bool:
        """
        Read value from a sensor.

        Args:
            name: Sensor name

        Returns:
            Sensor state (True/False)
        """
        sensor = self.sensors.get(name)
        if sensor:
            return sensor.read()
        return False

    def read_all(self) -> dict[str, bool]:
        """
        Read all sensors.

        Returns:
            Dictionary of sensor states
        """
        return {name: sensor.read() for name, sensor in self.sensors.items()}

    def cleanup(self) -> None:
        """Cleanup all GPIO resources."""
        for sensor in self.sensors.values():
            sensor.cleanup()


__all__ = [
    "DigitalSensorInterface",
    "DigitalSensorConfig",
    "DigitalSensorManager",
    "PullMode",
]

