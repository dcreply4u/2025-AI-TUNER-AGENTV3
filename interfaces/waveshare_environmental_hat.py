"""
Waveshare Environmental Sensor HAT Interface

Supports the Waveshare Environmental Sensor HAT for Raspberry Pi, which includes:
- BME280: Temperature, Humidity, Barometric Pressure
- Light Sensor
- Noise Sensor  
- 3-axis Accelerometer/Gyroscope/Magnetometer (LSM6DS3)

This interface provides environmental data for:
- Virtual dyno corrections (SAE J1349, DIN 70020)
- Density altitude calculations
- Weather-adaptive tuning
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any

LOGGER = logging.getLogger(__name__)

# Try to import hardware libraries
try:
    import smbus2
    SMBUS_AVAILABLE = True
except ImportError:
    SMBUS_AVAILABLE = False
    smbus2 = None  # type: ignore

try:
    import board
    import busio
    import adafruit_bme280
    ADAFRUIT_AVAILABLE = True
except ImportError:
    ADAFRUIT_AVAILABLE = False
    board = None  # type: ignore
    busio = None  # type: ignore
    adafruit_bme280 = None  # type: ignore

# Simulator mode
SIMULATOR_MODE = False


@dataclass
class EnvironmentalReading:
    """Environmental sensor reading."""
    
    timestamp: float
    temperature_c: float  # Temperature in Celsius
    humidity_percent: float  # Relative humidity (0-100)
    pressure_kpa: float  # Barometric pressure in kPa
    pressure_hpa: float  # Barometric pressure in hPa (hectopascals)
    light_lux: Optional[float] = None  # Light level in lux
    noise_db: Optional[float] = None  # Noise level in dB
    accel_x: Optional[float] = None  # Accelerometer X (m/s²)
    accel_y: Optional[float] = None  # Accelerometer Y (m/s²)
    accel_z: Optional[float] = None  # Accelerometer Z (m/s²)
    gyro_x: Optional[float] = None  # Gyroscope X (rad/s)
    gyro_y: Optional[float] = None  # Gyroscope Y (rad/s)
    gyro_z: Optional[float] = None  # Gyroscope Z (rad/s)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for telemetry."""
        return {
            "timestamp": self.timestamp,
            "ambient_temp_c": self.temperature_c,
            "ambient_temp_f": (self.temperature_c * 9/5) + 32,
            "humidity_percent": self.humidity_percent,
            "barometric_pressure_kpa": self.pressure_kpa,
            "barometric_pressure_hpa": self.pressure_hpa,
            "barometric_pressure_psi": self.pressure_kpa * 0.145038,
            "light_lux": self.light_lux,
            "noise_db": self.noise_db,
            "accel_x": self.accel_x,
            "accel_y": self.accel_y,
            "accel_z": self.accel_z,
            "gyro_x": self.gyro_x,
            "gyro_y": self.gyro_y,
            "gyro_z": self.gyro_z,
        }


class WaveshareEnvironmentalHAT:
    """
    Interface for Waveshare Environmental Sensor HAT.
    
    Supports both hardware and simulator modes.
    """
    
    # BME280 I2C address (default)
    BME280_ADDRESS = 0x76
    
    # I2C bus (usually 1 on Raspberry Pi)
    I2C_BUS = 1
    
    def __init__(
        self,
        i2c_bus: int = 1,
        bme280_address: int = 0x76,
        use_simulator: bool = False,
    ) -> None:
        """
        Initialize Waveshare Environmental Sensor HAT.
        
        Args:
            i2c_bus: I2C bus number (usually 1 on Raspberry Pi)
            bme280_address: BME280 I2C address (0x76 or 0x77)
            use_simulator: Use simulator instead of hardware
        """
        self.i2c_bus = i2c_bus
        self.bme280_address = bme280_address
        self.use_simulator = use_simulator or SIMULATOR_MODE
        self.connected = False
        
        # Hardware objects
        self.bus: Optional[Any] = None
        self.bme280: Optional[Any] = None
        self.i2c: Optional[Any] = None
        
        # Simulator state
        self._sim_temp = 20.0
        self._sim_humidity = 50.0
        self._sim_pressure = 101.325  # kPa (sea level)
        
        LOGGER.info(f"Waveshare Environmental HAT initialized (simulator={self.use_simulator})")
    
    def connect(self) -> bool:
        """
        Connect to the sensor HAT.
        
        Returns:
            True if connected successfully
        """
        if self.use_simulator:
            self.connected = True
            LOGGER.info("Waveshare Environmental HAT: Using simulator mode")
            return True
        
        # Try Adafruit library first (preferred)
        if ADAFRUIT_AVAILABLE:
            try:
                self.i2c = busio.I2C(board.SCL, board.SDA)
                self.bme280 = adafruit_bme280.Adafruit_BME280_I2C(
                    self.i2c,
                    address=self.bme280_address
                )
                # Configure oversampling and filter
                self.bme280.overscan_pressure = adafruit_bme280.OVERSCAN_X1
                self.bme280.overscan_temperature = adafruit_bme280.OVERSCAN_X1
                self.bme280.overscan_humidity = adafruit_bme280.OVERSCAN_X1
                self.bme280.filter = adafruit_bme280.FILTER_X16
                
                # Test read
                _ = self.bme280.temperature
                self.connected = True
                LOGGER.info("Waveshare Environmental HAT: Connected via Adafruit library")
                return True
            except Exception as e:
                LOGGER.warning(f"Failed to connect via Adafruit library: {e}")
        
        # Fallback to smbus2
        if SMBUS_AVAILABLE:
            try:
                self.bus = smbus2.SMBus(self.i2c_bus)
                # Test connection by reading BME280 chip ID
                chip_id = self.bus.read_byte_data(self.bme280_address, 0xD0)
                if chip_id == 0x60:  # BME280 chip ID
                    self.connected = True
                    LOGGER.info("Waveshare Environmental HAT: Connected via smbus2")
                    return True
                else:
                    LOGGER.warning(f"Unexpected chip ID: 0x{chip_id:02X} (expected 0x60)")
            except Exception as e:
                LOGGER.warning(f"Failed to connect via smbus2: {e}")
        
        # If all hardware methods fail, use simulator
        LOGGER.warning("Hardware connection failed, falling back to simulator")
        self.use_simulator = True
        self.connected = True
        return True
    
    def disconnect(self) -> None:
        """Disconnect from the sensor HAT."""
        if self.bus:
            try:
                self.bus.close()
            except Exception:
                pass
            self.bus = None
        
        if self.i2c:
            try:
                self.i2c.deinit()
            except Exception:
                pass
            self.i2c = None
        
        self.bme280 = None
        self.connected = False
        LOGGER.info("Waveshare Environmental HAT: Disconnected")
    
    def is_connected(self) -> bool:
        """Check if connected to the sensor HAT."""
        return self.connected
    
    def read(self) -> Optional[EnvironmentalReading]:
        """
        Read all environmental sensors.
        
        Returns:
            EnvironmentalReading object, or None if error
        """
        if not self.connected:
            if not self.connect():
                return None
        
        timestamp = time.time()
        
        if self.use_simulator:
            return self._read_simulator(timestamp)
        
        # Read from hardware
        try:
            if self.bme280 and hasattr(self.bme280, 'temperature'):
                # Adafruit library
                temp_c = self.bme280.temperature
                humidity = self.bme280.relative_humidity
                pressure_hpa = self.bme280.pressure
                pressure_kpa = pressure_hpa / 10.0
                
                # Update simulator state for consistency
                self._sim_temp = temp_c
                self._sim_humidity = humidity
                self._sim_pressure = pressure_kpa
                
                return EnvironmentalReading(
                    timestamp=timestamp,
                    temperature_c=temp_c,
                    humidity_percent=humidity,
                    pressure_kpa=pressure_kpa,
                    pressure_hpa=pressure_hpa,
                    # Light and noise sensors not yet implemented
                    # Accelerometer/gyroscope not yet implemented
                )
            elif self.bus:
                # smbus2 implementation
                return self._read_bme280_smbus(timestamp)
            else:
                return None
        except Exception as e:
            LOGGER.error(f"Error reading environmental sensors: {e}")
            return None
    
    def _read_bme280_smbus(self, timestamp: float) -> Optional[EnvironmentalReading]:
        """Read BME280 using smbus2 (basic implementation)."""
        try:
            # BME280 reading via smbus2 (simplified - full implementation would
            # require calibration data reading and compensation algorithms)
            # For now, return simulator data
            LOGGER.warning("Full smbus2 BME280 implementation not yet complete, using simulator")
            return self._read_simulator(timestamp)
        except Exception as e:
            LOGGER.error(f"Error reading BME280 via smbus2: {e}")
            return None
    
    def _read_simulator(self, timestamp: float) -> EnvironmentalReading:
        """Generate simulated environmental readings."""
        import random
        
        # Simulate realistic variations
        temp_variation = random.uniform(-0.5, 0.5)
        humidity_variation = random.uniform(-2.0, 2.0)
        pressure_variation = random.uniform(-0.1, 0.1)
        
        return EnvironmentalReading(
            timestamp=timestamp,
            temperature_c=self._sim_temp + temp_variation,
            humidity_percent=max(0, min(100, self._sim_humidity + humidity_variation)),
            pressure_kpa=self._sim_pressure + pressure_variation,
            pressure_hpa=(self._sim_pressure + pressure_variation) * 10.0,
            light_lux=random.uniform(100, 1000),  # Simulated light
            noise_db=random.uniform(30, 60),  # Simulated noise
        )
    
    def set_simulator_values(
        self,
        temperature_c: Optional[float] = None,
        humidity_percent: Optional[float] = None,
        pressure_kpa: Optional[float] = None,
    ) -> None:
        """
        Set simulator values (for testing).
        
        Args:
            temperature_c: Temperature in Celsius
            humidity_percent: Relative humidity (0-100)
            pressure_kpa: Barometric pressure in kPa
        """
        if temperature_c is not None:
            self._sim_temp = temperature_c
        if humidity_percent is not None:
            self._sim_humidity = humidity_percent
        if pressure_kpa is not None:
            self._sim_pressure = pressure_kpa
        
        LOGGER.info(f"Simulator values updated: T={self._sim_temp}°C, H={self._sim_humidity}%, P={self._sim_pressure}kPa")
    
    def get_environmental_conditions(self) -> Optional[Dict[str, float]]:
        """
        Get environmental conditions in format expected by VirtualDyno.
        
        Returns:
            Dictionary with temperature_c, humidity_percent, barometric_pressure_kpa
        """
        reading = self.read()
        if not reading:
            return None
        
        return {
            "temperature_c": reading.temperature_c,
            "humidity_percent": reading.humidity_percent,
            "barometric_pressure_kpa": reading.pressure_kpa,
        }


# Global instance
_global_environmental_hat: Optional[WaveshareEnvironmentalHAT] = None


def get_environmental_hat(
    use_simulator: bool = False,
    i2c_bus: int = 1,
    bme280_address: int = 0x76,
) -> WaveshareEnvironmentalHAT:
    """
    Get or create global environmental HAT instance.
    
    Args:
        use_simulator: Use simulator instead of hardware
        i2c_bus: I2C bus number
        bme280_address: BME280 I2C address
        
    Returns:
        WaveshareEnvironmentalHAT instance
    """
    global _global_environmental_hat
    
    if _global_environmental_hat is None:
        _global_environmental_hat = WaveshareEnvironmentalHAT(
            i2c_bus=i2c_bus,
            bme280_address=bme280_address,
            use_simulator=use_simulator,
        )
    
    return _global_environmental_hat


__all__ = [
    "WaveshareEnvironmentalHAT",
    "EnvironmentalReading",
    "get_environmental_hat",
]

