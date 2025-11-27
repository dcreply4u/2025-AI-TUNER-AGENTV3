"""
IMU (Inertial Measurement Unit) Interface
Supports various IMU sensors for motion tracking and Kalman filter integration.
Based on VBOX 3i IMU specifications.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

LOGGER = logging.getLogger(__name__)

# Try to import I2C libraries
try:
    import smbus2  # type: ignore
    I2C_AVAILABLE = True
except ImportError:
    I2C_AVAILABLE = False
    smbus2 = None  # type: ignore

# Try to import Sense HAT (AstroPi) library
try:
    from sense_hat import SenseHat  # type: ignore
    SENSE_HAT_AVAILABLE = True
except ImportError:
    SENSE_HAT_AVAILABLE = False
    SenseHat = None  # type: ignore

# Try to import serial for COM port support
try:
    import serial  # type: ignore
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    serial = None  # type: ignore


class IMUType(Enum):
    """IMU sensor types."""
    MPU6050 = "mpu6050"
    MPU9250 = "mpu9250"
    BNO085 = "bno085"
    IMU04 = "imu04"  # Racelogic IMU04 compatible
    SENSE_HAT = "sense_hat"  # Raspberry Pi Sense HAT / AstroPi (virtual or physical)
    COM_PORT = "com_port"  # COM port-based IMU (for simulators)
    AUTO_DETECT = "auto_detect"  # Auto-detect available IMU


class IMUStatus(Enum):
    """IMU initialization status."""
    NOT_CONNECTED = "not_connected"
    CONNECTED = "connected"
    INITIALIZING = "initializing"  # 30s stationary initialization
    INITIALIZED = "initialized"  # Initialization complete, waiting for movement
    ACTIVE = "active"  # Movement detected, IMU integration working
    ERROR = "error"


@dataclass
class IMUReading:
    """IMU sensor reading."""
    # Accelerometer (m/s²)
    accel_x: float
    accel_y: float
    accel_z: float
    
    # Gyroscope (deg/s)
    gyro_x: float
    gyro_y: float
    gyro_z: float
    
    # Magnetometer (optional, microtesla)
    mag_x: Optional[float] = None
    mag_y: Optional[float] = None
    mag_z: Optional[float] = None
    
    # Temperature (Celsius)
    temperature: Optional[float] = None
    
    # Timestamp
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        """Initialize timestamp."""
        if self.timestamp == 0.0:
            self.timestamp = time.time()

    def to_payload(self) -> dict:
        """Convert to payload dictionary."""
        payload = {
            "accel_x": self.accel_x,
            "accel_y": self.accel_y,
            "accel_z": self.accel_z,
            "gyro_x": self.gyro_x,
            "gyro_y": self.gyro_y,
            "gyro_z": self.gyro_z,
            "timestamp": self.timestamp,
        }
        if self.mag_x is not None:
            payload["mag_x"] = self.mag_x
            payload["mag_y"] = self.mag_y
            payload["mag_z"] = self.mag_z
        if self.temperature is not None:
            payload["temperature"] = self.temperature
        return payload


class IMUInterface:
    """
    IMU hardware interface.
    Supports multiple IMU types via I2C, SPI, or CAN.
    """

    def __init__(
        self,
        imu_type: IMUType = IMUType.MPU6050,
        i2c_bus: int = 1,
        i2c_address: int = 0x68,
        com_port: Optional[str] = None,  # COM port for COM_PORT type
        com_baudrate: int = 115200,  # Baud rate for COM port
    ) -> None:
        """
        Initialize IMU interface.
        
        Args:
            imu_type: Type of IMU sensor
            i2c_bus: I2C bus number
            i2c_address: I2C device address
            com_port: COM port path (e.g., "COM6" on Windows, "/dev/ttyUSB0" on Linux)
            com_baudrate: Baud rate for COM port communication
        """
        self.imu_type = imu_type
        self.i2c_bus = i2c_bus
        self.i2c_address = i2c_address
        self.com_port = com_port
        self.com_baudrate = com_baudrate
        self.bus = None
        self.sense_hat = None  # Sense HAT instance
        self.com_serial = None  # COM port serial connection
        self.status = IMUStatus.NOT_CONNECTED
        self.initialization_start_time: Optional[float] = None
        self.initialization_duration = 30.0  # 30 seconds stationary initialization

        # Auto-detect IMU type if requested
        if imu_type == IMUType.AUTO_DETECT:
            self.imu_type = self._auto_detect_imu()
            LOGGER.info(f"Auto-detected IMU type: {self.imu_type.value}")

        # Initialize based on type
        if self.imu_type == IMUType.SENSE_HAT:
            self._initialize_sense_hat()
        elif self.imu_type == IMUType.COM_PORT:
            self._initialize_com_port()
        elif I2C_AVAILABLE:
            try:
                self.bus = smbus2.SMBus(i2c_bus)
                self._initialize_sensor()
            except Exception as e:
                LOGGER.error(f"Failed to initialize IMU: {e}")
                self.status = IMUStatus.ERROR
        else:
            LOGGER.warning("I2C not available - IMU interface will be simulated")

    def _auto_detect_imu(self) -> IMUType:
        """
        Auto-detect available IMU sensor.
        
        Returns:
            Detected IMU type, or MPU6050 as default
        """
        # Check for Sense HAT first (most common on Pi 5 with AstroPi)
        if SENSE_HAT_AVAILABLE:
            try:
                test_sense = SenseHat()
                # Try to read accelerometer to verify it works
                test_sense.get_accelerometer_raw()
                LOGGER.info("Sense HAT (AstroPi) detected")
                return IMUType.SENSE_HAT
            except Exception:
                pass
        
        # Check I2C for other IMU types
        if I2C_AVAILABLE:
            try:
                bus = smbus2.SMBus(self.i2c_bus)
                # Check for MPU6050/MPU9250 at 0x68
                try:
                    bus.read_byte(0x68)
                    LOGGER.info("MPU6050/MPU9250 detected at 0x68")
                    return IMUType.MPU6050
                except Exception:
                    pass
                bus.close()
            except Exception:
                pass
        
        # Default to MPU6050 if nothing detected
        LOGGER.warning("No IMU detected, defaulting to MPU6050 (simulated)")
        return IMUType.MPU6050

    def _initialize_sense_hat(self) -> None:
        """Initialize Sense HAT (AstroPi) sensor."""
        if not SENSE_HAT_AVAILABLE:
            LOGGER.error("Sense HAT library not available. Install with: pip install sense-hat")
            self.status = IMUStatus.ERROR
            return
        
        try:
            self.sense_hat = SenseHat()
            # Set IMU to use accelerometer, gyroscope, and magnetometer
            self.sense_hat.set_imu_config(True, True, True)  # Compass, Gyro, Accel
            self.status = IMUStatus.CONNECTED
            LOGGER.info("Sense HAT (AstroPi) initialized successfully")
        except Exception as e:
            LOGGER.error(f"Sense HAT initialization failed: {e}")
            self.status = IMUStatus.ERROR

    def _initialize_com_port(self) -> None:
        """Initialize COM port-based IMU (for simulators)."""
        if not SERIAL_AVAILABLE:
            LOGGER.error("pyserial not available. Install with: pip install pyserial")
            self.status = IMUStatus.ERROR
            return
        
        if not self.com_port:
            LOGGER.error("COM port not specified for COM_PORT IMU type")
            self.status = IMUStatus.ERROR
            return
        
        try:
            import os
            if not os.path.exists(self.com_port):
                LOGGER.warning(f"COM port {self.com_port} not found - will attempt connection anyway")
            
            self.com_serial = serial.Serial(
                port=self.com_port,
                baudrate=self.com_baudrate,
                timeout=0.1,
                write_timeout=0.1
            )
            self.status = IMUStatus.CONNECTED
            LOGGER.info(f"COM port IMU initialized: {self.com_port} @ {self.com_baudrate} baud")
        except Exception as e:
            LOGGER.error(f"COM port IMU initialization failed: {e}")
            self.status = IMUStatus.ERROR

    def _initialize_sensor(self) -> None:
        """Initialize the IMU sensor based on type."""
        if self.imu_type == IMUType.MPU6050:
            self._init_mpu6050()
        elif self.imu_type == IMUType.MPU9250:
            self._init_mpu9250()
        elif self.imu_type == IMUType.BNO085:
            self._init_bno085()
        else:
            LOGGER.warning(f"IMU type {self.imu_type} initialization not implemented")

    def _init_mpu6050(self) -> None:
        """Initialize MPU6050 sensor."""
        try:
            # Wake up MPU6050 (set sleep bit to 0)
            self.bus.write_byte_data(self.i2c_address, 0x6B, 0x00)
            self.status = IMUStatus.CONNECTED
            LOGGER.info("MPU6050 initialized")
        except Exception as e:
            LOGGER.error(f"MPU6050 initialization failed: {e}")
            self.status = IMUStatus.ERROR

    def _init_mpu9250(self) -> None:
        """Initialize MPU9250 sensor."""
        try:
            # Similar to MPU6050 but may need additional setup
            self.bus.write_byte_data(self.i2c_address, 0x6B, 0x00)
            self.status = IMUStatus.CONNECTED
            LOGGER.info("MPU9250 initialized")
        except Exception as e:
            LOGGER.error(f"MPU9250 initialization failed: {e}")
            self.status = IMUStatus.ERROR

    def _init_bno085(self) -> None:
        """Initialize BNO085 sensor."""
        # BNO085 uses different protocol (SHTP)
        LOGGER.warning("BNO085 initialization not fully implemented")
        self.status = IMUStatus.CONNECTED

    def read(self) -> Optional[IMUReading]:
        """
        Read IMU data.
        
        Returns:
            IMUReading or None if read failed
        """
        if self.status == IMUStatus.NOT_CONNECTED or self.status == IMUStatus.ERROR:
            return None

        if self.imu_type == IMUType.SENSE_HAT:
            return self._read_sense_hat()
        elif self.imu_type == IMUType.COM_PORT:
            return self._read_com_port()
        elif self.imu_type == IMUType.MPU6050:
            return self._read_mpu6050()
        elif self.imu_type == IMUType.MPU9250:
            return self._read_mpu9250()
        elif self.imu_type == IMUType.BNO085:
            return self._read_bno085()
        else:
            return None

    def _read_mpu6050(self) -> Optional[IMUReading]:
        """Read MPU6050 data."""
        if not self.bus:
            return None

        try:
            # Read accelerometer (0x3B-0x40)
            accel_data = self.bus.read_i2c_block_data(self.i2c_address, 0x3B, 6)
            accel_x = self._twos_complement((accel_data[0] << 8) | accel_data[1], 16) / 16384.0 * 9.81
            accel_y = self._twos_complement((accel_data[2] << 8) | accel_data[3], 16) / 16384.0 * 9.81
            accel_z = self._twos_complement((accel_data[4] << 8) | accel_data[5], 16) / 16384.0 * 9.81

            # Read gyroscope (0x43-0x48)
            gyro_data = self.bus.read_i2c_block_data(self.i2c_address, 0x43, 6)
            gyro_x = self._twos_complement((gyro_data[0] << 8) | gyro_data[1], 16) / 131.0
            gyro_y = self._twos_complement((gyro_data[2] << 8) | gyro_data[3], 16) / 131.0
            gyro_z = self._twos_complement((gyro_data[4] << 8) | gyro_data[5], 16) / 131.0

            # Read temperature (0x41-0x42)
            temp_data = self.bus.read_i2c_block_data(self.i2c_address, 0x41, 2)
            temp_raw = self._twos_complement((temp_data[0] << 8) | temp_data[1], 16)
            temperature = temp_raw / 340.0 + 36.53

            return IMUReading(
                accel_x=accel_x,
                accel_y=accel_y,
                accel_z=accel_z,
                gyro_x=gyro_x,
                gyro_y=gyro_y,
                gyro_z=gyro_z,
                temperature=temperature,
            )
        except Exception as e:
            LOGGER.error(f"MPU6050 read error: {e}")
            return None

    def _read_mpu9250(self) -> Optional[IMUReading]:
        """Read MPU9250 data (includes magnetometer)."""
        # Similar to MPU6050 but includes magnetometer
        reading = self._read_mpu6050()
        if reading and self.bus:
            try:
                # Read magnetometer (different address, 0x0C)
                # Implementation depends on MPU9250 configuration
                pass
            except Exception:
                pass
        return reading

    def _read_sense_hat(self) -> Optional[IMUReading]:
        """
        Read Sense HAT (AstroPi) data.
        
        Sense HAT provides:
        - Accelerometer (m/s²)
        - Gyroscope (rad/s, converted to deg/s)
        - Magnetometer (microtesla)
        - Temperature (Celsius)
        """
        if not self.sense_hat:
            return None
        
        try:
            # Get accelerometer data (m/s²)
            accel_raw = self.sense_hat.get_accelerometer_raw()
            accel_x = accel_raw['x'] * 9.81  # Convert G to m/s²
            accel_y = accel_raw['y'] * 9.81
            accel_z = accel_raw['z'] * 9.81
            
            # Get gyroscope data (rad/s, convert to deg/s)
            gyro_raw = self.sense_hat.get_gyroscope_raw()
            gyro_x = math.degrees(gyro_raw['x'])  # Convert rad/s to deg/s
            gyro_y = math.degrees(gyro_raw['y'])
            gyro_z = math.degrees(gyro_raw['z'])
            
            # Get magnetometer data (microtesla)
            mag_raw = self.sense_hat.get_compass_raw()
            mag_x = mag_raw['x']
            mag_y = mag_raw['y']
            mag_z = mag_raw['z']
            
            # Get temperature (Celsius)
            temperature = self.sense_hat.get_temperature()
            
            return IMUReading(
                accel_x=accel_x,
                accel_y=accel_y,
                accel_z=accel_z,
                gyro_x=gyro_x,
                gyro_y=gyro_y,
                gyro_z=gyro_z,
                mag_x=mag_x,
                mag_y=mag_y,
                mag_z=mag_z,
                temperature=temperature,
            )
        except Exception as e:
            LOGGER.error(f"Sense HAT read error: {e}")
            return None

    def _read_bno085(self) -> Optional[IMUReading]:
        """Read BNO085 data."""
        # BNO085 uses SHTP protocol, more complex
        LOGGER.warning("BNO085 read not fully implemented")
        return None

    def _read_com_port(self) -> Optional[IMUReading]:
        """
        Read IMU data from COM port (for simulators).
        Expects NMEA-like format: $IMUDATA,accel_x,accel_y,accel_z,gyro_x,gyro_y,gyro_z,mag_x,mag_y,mag_z*checksum
        """
        if not self.com_serial or not self.com_serial.is_open:
            return None
        
        try:
            line = self.com_serial.readline().decode("ascii", errors="ignore").strip()
            if not line.startswith("$IMUDATA"):
                return None
            
            # Parse: $IMUDATA,accel_x,accel_y,accel_z,gyro_x,gyro_y,gyro_z,mag_x,mag_y,mag_z*checksum
            # Remove $ and checksum
            if "*" in line:
                line = line.split("*")[0]
            line = line.replace("$IMUDATA,", "")
            
            parts = line.split(",")
            if len(parts) < 9:
                return None
            
            try:
                accel_x = float(parts[0])
                accel_y = float(parts[1])
                accel_z = float(parts[2])
                gyro_x = float(parts[3])
                gyro_y = float(parts[4])
                gyro_z = float(parts[5])
                mag_x = float(parts[6]) if len(parts) > 6 else None
                mag_y = float(parts[7]) if len(parts) > 7 else None
                mag_z = float(parts[8]) if len(parts) > 8 else None
                
                return IMUReading(
                    accel_x=accel_x,
                    accel_y=accel_y,
                    accel_z=accel_z,
                    gyro_x=gyro_x,
                    gyro_y=gyro_y,
                    gyro_z=gyro_z,
                    mag_x=mag_x,
                    mag_y=mag_y,
                    mag_z=mag_z,
                )
            except (ValueError, IndexError) as e:
                LOGGER.debug(f"Failed to parse IMU data: {e}")
                return None
        except Exception as e:
            LOGGER.debug(f"COM port read error: {e}")
            return None

    def _twos_complement(self, value: int, bits: int) -> int:
        """Convert two's complement value."""
        if value & (1 << (bits - 1)):
            value -= 1 << bits
        return value

    def start_initialization(self) -> None:
        """Start 30-second stationary initialization."""
        if self.status == IMUStatus.CONNECTED:
            self.status = IMUStatus.INITIALIZING
            self.initialization_start_time = time.time()
            LOGGER.info("IMU initialization started (30s stationary required)")

    def check_initialization(self) -> bool:
        """
        Check if initialization is complete.
        
        Returns:
            True if initialization complete
        """
        if self.status == IMUStatus.INITIALIZING and self.initialization_start_time:
            elapsed = time.time() - self.initialization_start_time
            if elapsed >= self.initialization_duration:
                self.status = IMUStatus.INITIALIZED
                LOGGER.info("IMU initialization complete - waiting for movement")
                return True
        return False

    def detect_movement(self, threshold: float = 0.1) -> bool:
        """
        Detect if IMU has detected movement.
        
        Args:
            threshold: Acceleration threshold in m/s²
            
        Returns:
            True if movement detected
        """
        reading = self.read()
        if not reading:
            return False

        # Check if acceleration exceeds threshold
        accel_magnitude = (
            reading.accel_x**2 + reading.accel_y**2 + reading.accel_z**2
        ) ** 0.5

        if accel_magnitude > threshold and self.status == IMUStatus.INITIALIZED:
            self.status = IMUStatus.ACTIVE
            LOGGER.info("IMU movement detected - integration active")
            return True

        return False

    def get_status(self) -> dict:
        """Get IMU status."""
        return {
            "imu_type": self.imu_type.value,
            "status": self.status.value,
            "initialization_elapsed": (
                time.time() - self.initialization_start_time
                if self.initialization_start_time
                else None
            ),
        }

    def close(self) -> None:
        """Close IMU interface."""
        if self.bus:
            try:
                self.bus.close()
            except Exception:
                pass
        if self.sense_hat:
            # Sense HAT doesn't need explicit close, but clear reference
            self.sense_hat = None
        if self.com_serial and self.com_serial.is_open:
            try:
                self.com_serial.close()
            except Exception:
                pass
        self.status = IMUStatus.NOT_CONNECTED

    def is_connected(self) -> bool:
        """
        Check if IMU is connected and ready.
        
        Returns:
            True if connected and ready to read
        """
        return self.status in [IMUStatus.CONNECTED, IMUStatus.INITIALIZING, IMUStatus.INITIALIZED, IMUStatus.ACTIVE]

    def connect(self) -> bool:
        """
        Attempt to connect to IMU.
        
        Returns:
            True if connection successful
        """
        if self.imu_type == IMUType.SENSE_HAT:
            self._initialize_sense_hat()
        elif self.imu_type == IMUType.COM_PORT:
            self._initialize_com_port()
        else:
            self._initialize_sensor()
        return self.status == IMUStatus.CONNECTED


__all__ = ["IMUInterface", "IMUReading", "IMUType", "IMUStatus"]


