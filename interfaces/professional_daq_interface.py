"""
Professional DAQ Interface - Chassis and Engine Sensors

Provides interfaces for professional-grade data acquisition sensors:
- Suspension travel sensors
- Steering angle sensors
- EGT sensors (per-cylinder)
- Fuel pressure sensors (pre/post regulator)
- Oil pressure and temperature sensors
- Knock detection systems
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable

LOGGER = logging.getLogger(__name__)

# Try to import CAN library
try:
    import can
    CAN_AVAILABLE = True
except ImportError:
    CAN_AVAILABLE = False
    can = None  # type: ignore


class SensorType(Enum):
    """Professional DAQ sensor types."""
    SUSPENSION_TRAVEL = "suspension_travel"
    STEERING_ANGLE = "steering_angle"
    EGT = "egt"  # Exhaust Gas Temperature
    FUEL_PRESSURE = "fuel_pressure"
    OIL_PRESSURE = "oil_pressure"
    OIL_TEMPERATURE = "oil_temperature"
    KNOCK_DETECTION = "knock_detection"


@dataclass
class SuspensionReading:
    """Suspension travel reading."""
    front_left_mm: float
    front_right_mm: float
    rear_left_mm: float
    rear_right_mm: float
    timestamp: float = field(default_factory=time.time)
    
    def calculate_roll(self, track_width_front_mm: float) -> float:
        """Calculate roll angle in degrees."""
        import math
        delta = self.front_right_mm - self.front_left_mm
        return math.degrees(math.atan(delta / track_width_front_mm))
    
    def calculate_pitch(self, wheelbase_mm: float) -> float:
        """Calculate pitch angle in degrees."""
        import math
        front_avg = (self.front_left_mm + self.front_right_mm) / 2.0
        rear_avg = (self.rear_left_mm + self.rear_right_mm) / 2.0
        delta = front_avg - rear_avg
        return math.degrees(math.atan(delta / wheelbase_mm))
    
    def calculate_heave(self) -> float:
        """Calculate heave (average travel)."""
        return (self.front_left_mm + self.front_right_mm + 
                self.rear_left_mm + self.rear_right_mm) / 4.0


@dataclass
class SteeringAngleReading:
    """Steering angle reading."""
    angle_degrees: float  # -720 to +720 degrees
    rate_deg_per_sec: float  # Rate of change
    timestamp: float = field(default_factory=time.time)
    
    def normalize(self) -> float:
        """Normalize to -1.0 to +1.0 range."""
        return max(-1.0, min(1.0, self.angle_degrees / 720.0))


@dataclass
class EGTReading:
    """Exhaust Gas Temperature reading (per cylinder)."""
    cylinder_temperatures: Dict[int, float]  # Cylinder number -> Temperature (°C)
    average_temp: float
    max_temp: float
    min_temp: float
    delta_max: float  # Maximum difference between cylinders
    timestamp: float = field(default_factory=time.time)
    
    def get_balance_percentage(self) -> float:
        """Calculate balance percentage (0-100, higher = more balanced)."""
        if self.average_temp == 0:
            return 0.0
        return max(0.0, min(100.0, 100.0 - (self.delta_max / self.average_temp * 100.0)))


@dataclass
class FuelPressureReading:
    """Fuel pressure reading (pre and post regulator)."""
    pre_regulator_psi: float
    post_regulator_psi: float
    delta_psi: float  # Pressure drop across regulator
    timestamp: float = field(default_factory=time.time)
    
    def calculate_regulator_efficiency(self) -> float:
        """Calculate regulator efficiency (0-100%)."""
        if self.pre_regulator_psi == 0:
            return 0.0
        return (self.delta_psi / self.pre_regulator_psi) * 100.0


@dataclass
class OilSystemReading:
    """Oil pressure and temperature reading."""
    pressure_psi: float
    temperature_celsius: float
    timestamp: float = field(default_factory=time.time)
    
    def is_safe(self) -> tuple[bool, str]:
        """
        Check if oil system is operating safely.
        
        Returns:
            Tuple of (is_safe, warning_message)
        """
        # Check temperature
        if self.temperature_celsius < 60:
            return False, "Oil too cold - avoid high RPM"
        elif self.temperature_celsius > 130:
            return False, "CRITICAL: Oil temperature too high - shutdown immediately"
        elif self.temperature_celsius > 120:
            return False, "WARNING: Oil temperature high - reduce load"
        
        # Check pressure (basic - should be RPM-dependent)
        if self.pressure_psi < 5:
            return False, "CRITICAL: Oil pressure too low - shutdown immediately"
        elif self.pressure_psi < 10:
            return False, "WARNING: Oil pressure low"
        
        return True, "OK"


@dataclass
class KnockReading:
    """Knock detection reading."""
    level: float  # 0-100 scale
    frequency_hz: float  # Dominant knock frequency
    cylinder: Optional[int] = None  # Cylinder number if multi-cylinder detection
    severity: str = "none"  # none, low, medium, high, critical
    timestamp: float = field(default_factory=time.time)
    
    def is_critical(self) -> bool:
        """Check if knock level is critical."""
        return self.level > 40 or self.severity in ["high", "critical"]


class ProfessionalDAQInterface(ABC):
    """
    Abstract base class for professional DAQ interfaces.
    
    Supports various DAQ systems and sensor types.
    """
    
    def __init__(self, config: Dict[str, any]) -> None:
        """
        Initialize professional DAQ interface.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.connected = False
        self.running = False
        self.callbacks: Dict[str, List[Callable]] = {}
        
    @abstractmethod
    def connect(self) -> bool:
        """Connect to DAQ system."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from DAQ system."""
        pass
    
    @abstractmethod
    def start_acquisition(self) -> bool:
        """Start data acquisition."""
        pass
    
    @abstractmethod
    def stop_acquisition(self) -> None:
        """Stop data acquisition."""
        pass
    
    def register_callback(self, sensor_type: SensorType, callback: Callable) -> None:
        """Register callback for sensor data."""
        if sensor_type.value not in self.callbacks:
            self.callbacks[sensor_type.value] = []
        self.callbacks[sensor_type.value].append(callback)
    
    def _notify_callbacks(self, sensor_type: SensorType, data: any) -> None:
        """Notify registered callbacks of new data."""
        if sensor_type.value in self.callbacks:
            for callback in self.callbacks[sensor_type.value]:
                try:
                    callback(data)
                except Exception as e:
                    LOGGER.error(f"Error in callback for {sensor_type.value}: {e}")


class AnalogDAQInterface(ProfessionalDAQInterface):
    """
    Analog sensor DAQ interface.
    
    Reads analog sensors via ADC board (ADS1115, MCP3008, etc.).
    """
    
    def __init__(self, config: Dict[str, any]) -> None:
        super().__init__(config)
        self.adc = None
        self.sensor_channels: Dict[str, int] = config.get("sensor_channels", {})
        
    def connect(self) -> bool:
        """Connect to ADC board."""
        try:
            # Try ADS1115 first (I2C)
            if self.config.get("adc_type") == "ads1115":
                import adafruit_ads1x15.ads1115 as ADS
                from adafruit_ads1x15.analog_in import AnalogIn
                import board
                import busio
                
                i2c = busio.I2C(board.SCL, board.SDA)
                ads = ADS.ADS1115(i2c)
                self.adc = ads
                LOGGER.info("Connected to ADS1115 ADC")
                return True
            # Add other ADC types as needed
            return False
        except Exception as e:
            LOGGER.error(f"Failed to connect to ADC: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from ADC."""
        self.adc = None
        self.connected = False
    
    def start_acquisition(self) -> bool:
        """Start data acquisition."""
        if not self.connected:
            return False
        self.running = True
        return True
    
    def stop_acquisition(self) -> None:
        """Stop data acquisition."""
        self.running = False
    
    def read_suspension(self) -> Optional[SuspensionReading]:
        """Read suspension travel sensors."""
        if not self.running or not self.adc:
            return None
        
        try:
            # Read each channel
            fl = self._read_analog_channel(self.sensor_channels.get("suspension_fl", 0))
            fr = self._read_analog_channel(self.sensor_channels.get("suspension_fr", 1))
            rl = self._read_analog_channel(self.sensor_channels.get("suspension_rl", 2))
            rr = self._read_analog_channel(self.sensor_channels.get("suspension_rr", 3))
            
            reading = SuspensionReading(
                front_left_mm=fl,
                front_right_mm=fr,
                rear_left_mm=rl,
                rear_right_mm=rr
            )
            
            self._notify_callbacks(SensorType.SUSPENSION_TRAVEL, reading)
            return reading
        except Exception as e:
            LOGGER.error(f"Error reading suspension: {e}")
            return None
    
    def read_steering_angle(self) -> Optional[SteeringAngleReading]:
        """Read steering angle sensor."""
        if not self.running or not self.adc:
            return None
        
        try:
            channel = self.sensor_channels.get("steering_angle", 4)
            angle = self._read_analog_channel(channel)
            
            # Calculate rate (would need previous reading for accurate rate)
            rate = 0.0  # Placeholder
            
            reading = SteeringAngleReading(
                angle_degrees=angle,
                rate_deg_per_sec=rate
            )
            
            self._notify_callbacks(SensorType.STEERING_ANGLE, reading)
            return reading
        except Exception as e:
            LOGGER.error(f"Error reading steering angle: {e}")
            return None
    
    def read_egt(self, num_cylinders: int = 8) -> Optional[EGTReading]:
        """Read EGT sensors for all cylinders."""
        if not self.running or not self.adc:
            return None
        
        try:
            temps = {}
            for cyl in range(1, num_cylinders + 1):
                channel = self.sensor_channels.get(f"egt_cyl_{cyl}", None)
                if channel is not None:
                    temp = self._read_analog_channel(channel)
                    temps[cyl] = temp
            
            if not temps:
                return None
            
            avg = sum(temps.values()) / len(temps)
            max_temp = max(temps.values())
            min_temp = min(temps.values())
            delta = max_temp - min_temp
            
            reading = EGTReading(
                cylinder_temperatures=temps,
                average_temp=avg,
                max_temp=max_temp,
                min_temp=min_temp,
                delta_max=delta
            )
            
            self._notify_callbacks(SensorType.EGT, reading)
            return reading
        except Exception as e:
            LOGGER.error(f"Error reading EGT: {e}")
            return None
    
    def read_fuel_pressure(self) -> Optional[FuelPressureReading]:
        """Read fuel pressure sensors (pre and post regulator)."""
        if not self.running or not self.adc:
            return None
        
        try:
            pre_channel = self.sensor_channels.get("fuel_pressure_pre", None)
            post_channel = self.sensor_channels.get("fuel_pressure_post", None)
            
            if pre_channel is None or post_channel is None:
                return None
            
            pre = self._read_analog_channel(pre_channel)
            post = self._read_analog_channel(post_channel)
            delta = pre - post
            
            reading = FuelPressureReading(
                pre_regulator_psi=pre,
                post_regulator_psi=post,
                delta_psi=delta
            )
            
            self._notify_callbacks(SensorType.FUEL_PRESSURE, reading)
            return reading
        except Exception as e:
            LOGGER.error(f"Error reading fuel pressure: {e}")
            return None
    
    def read_oil_system(self) -> Optional[OilSystemReading]:
        """Read oil pressure and temperature."""
        if not self.running or not self.adc:
            return None
        
        try:
            pressure_channel = self.sensor_channels.get("oil_pressure", None)
            temp_channel = self.sensor_channels.get("oil_temperature", None)
            
            if pressure_channel is None or temp_channel is None:
                return None
            
            pressure = self._read_analog_channel(pressure_channel)
            temperature = self._read_analog_channel(temp_channel)
            
            reading = OilSystemReading(
                pressure_psi=pressure,
                temperature_celsius=temperature
            )
            
            self._notify_callbacks(SensorType.OIL_PRESSURE, reading)
            self._notify_callbacks(SensorType.OIL_TEMPERATURE, reading)
            return reading
        except Exception as e:
            LOGGER.error(f"Error reading oil system: {e}")
            return None
    
    def _read_analog_channel(self, channel: int) -> float:
        """Read analog channel and convert to physical units."""
        if not self.adc:
            return 0.0
        
        # Placeholder - actual implementation depends on ADC type
        # Would read raw ADC value and convert based on sensor calibration
        return 0.0


class CANDaqInterface(ProfessionalDAQInterface):
    """
    CAN bus DAQ interface.
    
    Reads professional DAQ sensors via CAN bus (AEM, Motec, Racepak, etc.).
    """
    
    def __init__(self, config: Dict[str, any]) -> None:
        super().__init__(config)
        self.bus: Optional[can.Bus] = None
        self.message_ids: Dict[str, int] = config.get("message_ids", {})
        
    def connect(self) -> bool:
        """Connect to CAN bus."""
        if not CAN_AVAILABLE:
            LOGGER.error("python-can library not available")
            return False
        
        try:
            self.bus = can.Bus(
                interface='socketcan',
                channel=self.config.get("can_interface", "can0"),
                bitrate=self.config.get("bitrate", 500000)
            )
            self.connected = True
            LOGGER.info(f"Connected to CAN bus DAQ: {self.config.get('can_interface', 'can0')}")
            return True
        except Exception as e:
            LOGGER.error(f"Failed to connect to CAN bus DAQ: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from CAN bus."""
        if self.bus:
            try:
                self.bus.shutdown()
            except Exception as e:
                LOGGER.warning(f"Error during CAN bus shutdown: {e}")
            finally:
                self.bus = None
                self.connected = False
    
    def start_acquisition(self) -> bool:
        """Start data acquisition."""
        if not self.connected:
            return False
        self.running = True
        return True
    
    def stop_acquisition(self) -> None:
        """Stop data acquisition."""
        self.running = False
    
    def read_suspension(self) -> Optional[SuspensionReading]:
        """Read suspension travel from CAN bus."""
        if not self.running or not self.bus:
            return None
        
        try:
            msg_id = self.message_ids.get("suspension", None)
            if msg_id is None:
                return None
            
            msg = self.bus.recv(timeout=0.1)
            if msg and msg.arbitration_id == msg_id:
                # Decode CAN message (format depends on DAQ system)
                # Example: 4x 16-bit values for FL, FR, RL, RR
                if len(msg.data) >= 8:
                    fl = int.from_bytes(msg.data[0:2], byteorder='little', signed=False) / 10.0
                    fr = int.from_bytes(msg.data[2:4], byteorder='little', signed=False) / 10.0
                    rl = int.from_bytes(msg.data[4:6], byteorder='little', signed=False) / 10.0
                    rr = int.from_bytes(msg.data[6:8], byteorder='little', signed=False) / 10.0
                    
                    reading = SuspensionReading(
                        front_left_mm=fl,
                        front_right_mm=fr,
                        rear_left_mm=rl,
                        rear_right_mm=rr
                    )
                    
                    self._notify_callbacks(SensorType.SUSPENSION_TRAVEL, reading)
                    return reading
        except Exception as e:
            LOGGER.error(f"Error reading suspension from CAN: {e}")
        
        return None
    
    # Similar methods for other sensors would be implemented here


def create_professional_daq_interface(config: Dict[str, any]) -> ProfessionalDAQInterface:
    """
    Factory function to create appropriate professional DAQ interface.
    
    Args:
        config: DAQ configuration
        
    Returns:
        ProfessionalDAQInterface instance
    """
    interface_type = config.get("interface_type", "analog").lower()
    
    if interface_type == "can" or interface_type == "can_bus":
        return CANDaqInterface(config)
    elif interface_type == "analog":
        return AnalogDAQInterface(config)
    else:
        raise ValueError(f"Unsupported DAQ interface type: {interface_type}")

