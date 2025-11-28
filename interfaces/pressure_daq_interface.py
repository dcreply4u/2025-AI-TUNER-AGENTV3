"""
Pressure Data Acquisition Interface

Supports various DAQ systems for cylinder pressure measurement:
- AEM Series 2 (CAN bus)
- Motec (CAN bus)
- Racepak (CAN bus or Serial)
- Generic CAN bus DAQ
- Serial/Ethernet DAQ systems
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
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


class DAQType(Enum):
    """DAQ system types."""
    AEM_SERIES_2 = "aem_series_2"
    MOTEC = "motec"
    RACEPAK = "racepak"
    GENERIC_CAN = "generic_can"
    SERIAL = "serial"
    ETHERNET = "ethernet"
    CUSTOM = "custom"


@dataclass
class DAQConfig:
    """Configuration for DAQ system."""
    daq_type: DAQType
    interface: str  # "can0", "can1", "/dev/ttyUSB0", "192.168.1.100", etc.
    bitrate: Optional[int] = None  # CAN bitrate (if CAN)
    channel_count: int = 8  # Number of pressure channels
    sampling_rate_hz: int = 10000  # Sampling rate per channel
    tdc_sync_channel: Optional[int] = None  # TDC sync signal channel
    unit: str = "psi"  # Pressure unit


@dataclass
class PressureSample:
    """Single pressure sample from DAQ."""
    channel: int  # Channel number (1-based, corresponds to cylinder)
    pressure: float  # Pressure value
    timestamp: float  # Timestamp in seconds
    crank_angle: Optional[float] = None  # Crank angle in degrees (if synchronized)
    rpm: Optional[float] = None  # Engine RPM (if available)
    tdc_sync: bool = False  # TDC sync pulse detected


class PressureDAQInterface(ABC):
    """
    Abstract base class for pressure DAQ interfaces.
    
    All DAQ implementations should inherit from this class.
    """
    
    def __init__(self, config: DAQConfig) -> None:
        """
        Initialize DAQ interface.
        
        Args:
            config: DAQ configuration
        """
        self.config = config
        self.connected = False
        self.running = False
        self.callback: Optional[Callable[[List[PressureSample]], None]] = None
        
    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to DAQ system.
        
        Returns:
            True if connection successful
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from DAQ system."""
        pass
    
    @abstractmethod
    def start_acquisition(self) -> bool:
        """
        Start data acquisition.
        
        Returns:
            True if started successfully
        """
        pass
    
    @abstractmethod
    def stop_acquisition(self) -> None:
        """Stop data acquisition."""
        pass
    
    @abstractmethod
    def read_samples(self, count: int = 100) -> List[PressureSample]:
        """
        Read pressure samples from DAQ.
        
        Args:
            count: Number of samples to read
            
        Returns:
            List of pressure samples
        """
        pass
    
    def set_callback(self, callback: Callable[[List[PressureSample]], None]) -> None:
        """
        Set callback function for real-time data streaming.
        
        Args:
            callback: Function to call with new samples
        """
        self.callback = callback


class GenericCANDaqInterface(PressureDAQInterface):
    """
    Generic CAN bus DAQ interface.
    
    Supports any CAN-based DAQ system with configurable message IDs.
    """
    
    def __init__(self, config: DAQConfig, message_ids: Dict[int, int]) -> None:
        """
        Initialize generic CAN DAQ.
        
        Args:
            config: DAQ configuration
            message_ids: Dictionary mapping channel number to CAN message ID
        """
        super().__init__(config)
        self.message_ids = message_ids
        self.bus: Optional[can.Bus] = None
        
    def connect(self) -> bool:
        """Connect to CAN bus."""
        if not CAN_AVAILABLE:
            LOGGER.error("python-can library not available")
            return False
        
        try:
            self.bus = can.Bus(
                interface='socketcan',
                channel=self.config.interface,
                bitrate=self.config.bitrate or 500000
            )
            self.connected = True
            LOGGER.info(f"Connected to CAN bus: {self.config.interface}")
            return True
        except Exception as e:
            LOGGER.error(f"Failed to connect to CAN bus: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from CAN bus."""
        try:
            if self.bus:
                self.bus.shutdown()
                self.bus = None
        except Exception as e:
            LOGGER.warning("Error during CAN bus shutdown: %s", e)
        finally:
            self.connected = False
            LOGGER.info("Disconnected from CAN bus")
    
    def start_acquisition(self) -> bool:
        """Start data acquisition."""
        if not self.connected:
            return False
        self.running = True
        LOGGER.info("Started pressure data acquisition")
        return True
    
    def stop_acquisition(self) -> None:
        """Stop data acquisition."""
        self.running = False
        LOGGER.info("Stopped pressure data acquisition")
    
    def read_samples(self, count: int = 100) -> List[PressureSample]:
        """
        Read pressure samples from CAN bus.
        
        Args:
            count: Number of samples to read
            
        Returns:
            List of pressure samples
        """
        if not self.bus or not self.running:
            return []
        
        samples = []
        timeout = 0.1  # 100ms timeout
        
        for _ in range(count):
            try:
                msg = self.bus.recv(timeout=timeout)
                if msg is None:
                    break
                
                # Find which channel this message ID corresponds to
                channel = None
                for ch, msg_id in self.message_ids.items():
                    if msg.arbitration_id == msg_id:
                        channel = ch
                        break
                
                if channel is None:
                    continue
                
                # Decode pressure value (assuming 16-bit value in first 2 bytes)
                if len(msg.data) >= 2:
                    pressure_raw = int.from_bytes(msg.data[0:2], byteorder='little', signed=False)
                    # Scale to PSI (example: 0-65535 maps to 0-2000 PSI)
                    pressure = (pressure_raw / 65535.0) * 2000.0
                    
                    sample = PressureSample(
                        channel=channel,
                        pressure=pressure,
                        timestamp=time.time(),
                        tdc_sync=False  # Would need separate message for TDC
                    )
                    samples.append(sample)
            except Exception as e:
                LOGGER.warning(f"Error reading CAN message: {e}")
                break
        
        return samples


class SerialDaqInterface(PressureDAQInterface):
    """
    Serial/UART DAQ interface.
    
    Supports RS-232/RS-485 DAQ systems.
    """
    
    def __init__(self, config: DAQConfig, baudrate: int = 115200) -> None:
        """
        Initialize serial DAQ.
        
        Args:
            config: DAQ configuration
            baudrate: Serial baud rate
        """
        super().__init__(config)
        self.baudrate = baudrate
        self.serial_port = None
    
    def connect(self) -> bool:
        """Connect to serial port."""
        try:
            import serial
            self.serial_port = serial.Serial(
                port=self.config.interface,
                baudrate=self.baudrate,
                timeout=0.1
            )
            self.connected = True
            LOGGER.info(f"Connected to serial DAQ: {self.config.interface}")
            return True
        except ImportError:
            LOGGER.error("pyserial library not available")
            return False
        except Exception as e:
            LOGGER.error(f"Failed to connect to serial DAQ: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from serial port."""
        try:
            if self.serial_port:
                self.serial_port.close()
        except Exception as e:
            LOGGER.warning("Error during serial port close: %s", e)
        finally:
            self.serial_port = None
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
    
    def read_samples(self, count: int = 100) -> List[PressureSample]:
        """
        Read pressure samples from serial port.
        
        Args:
            count: Number of samples to read
            
        Returns:
            List of pressure samples
        """
        if not self.serial_port or not self.running:
            return []
        
        samples = []
        
        # Example: Read binary data format
        # Format: [header][channel][pressure_high][pressure_low][checksum]
        try:
            while len(samples) < count:
                if self.serial_port.in_waiting >= 5:
                    header = self.serial_port.read(1)
                    if header[0] == 0xAA:  # Header byte
                        channel = self.serial_port.read(1)[0]
                        pressure_high = self.serial_port.read(1)[0]
                        pressure_low = self.serial_port.read(1)[0]
                        checksum = self.serial_port.read(1)[0]
                        
                        # Verify checksum (simple example)
                        calc_checksum = (header[0] + channel + pressure_high + pressure_low) % 256
                        if calc_checksum == checksum:
                            pressure_raw = (pressure_high << 8) | pressure_low
                            pressure = (pressure_raw / 65535.0) * 2000.0  # Scale to PSI
                            
                            sample = PressureSample(
                                channel=channel,
                                pressure=pressure,
                                timestamp=time.time()
                            )
                            samples.append(sample)
        except Exception as e:
            LOGGER.warning(f"Error reading serial data: {e}")
        
        return samples


class AEMSeries2Interface(PressureDAQInterface):
    """
    AEM Series 2 DAQ interface (CAN bus).
    
    AEM Series 2 uses CAN bus for data transmission.
    """
    
    def __init__(self, config: DAQConfig) -> None:
        """Initialize AEM Series 2 interface."""
        super().__init__(config)
        self.bus: Optional[can.Bus] = None
        # AEM Series 2 CAN message IDs (example - actual IDs may vary)
        self.base_id = 0x180  # Base ID for pressure channels
        
    def connect(self) -> bool:
        """Connect to AEM Series 2 via CAN."""
        if not CAN_AVAILABLE:
            LOGGER.error("python-can library not available")
            return False
        
        try:
            self.bus = can.Bus(
                interface='socketcan',
                channel=self.config.interface,
                bitrate=self.config.bitrate or 500000
            )
            self.connected = True
            LOGGER.info(f"Connected to AEM Series 2: {self.config.interface}")
            return True
        except Exception as e:
            LOGGER.error(f"Failed to connect to AEM Series 2: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from AEM Series 2."""
        try:
            if self.bus:
                self.bus.shutdown()
                self.bus = None
        except Exception as e:
            LOGGER.warning("Error during AEM Series 2 shutdown: %s", e)
        finally:
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
    
    def read_samples(self, count: int = 100) -> List[PressureSample]:
        """
        Read pressure samples from AEM Series 2.
        
        AEM Series 2 format (example):
        - Message ID: 0x180 + channel (0-7)
        - Data: [pressure_high, pressure_low, rpm_high, rpm_low, ...]
        """
        if not self.bus or not self.running:
            return []
        
        samples = []
        timeout = 0.1
        
        for _ in range(count):
            try:
                msg = self.bus.recv(timeout=timeout)
                if msg is None:
                    break
                
                # Check if this is an AEM pressure message
                if self.base_id <= msg.arbitration_id < self.base_id + self.config.channel_count:
                    channel = msg.arbitration_id - self.base_id + 1
                    
                    if len(msg.data) >= 4:
                        # Decode pressure (16-bit, little-endian)
                        pressure_raw = int.from_bytes(msg.data[0:2], byteorder='little', signed=False)
                        pressure = (pressure_raw / 65535.0) * 2000.0  # Scale to PSI
                        
                        # Decode RPM (if available)
                        rpm_raw = int.from_bytes(msg.data[2:4], byteorder='little', signed=False)
                        rpm = rpm_raw if rpm_raw > 0 else None
                        
                        sample = PressureSample(
                            channel=channel,
                            pressure=pressure,
                            timestamp=time.time(),
                            rpm=rpm
                        )
                        samples.append(sample)
            except Exception as e:
                LOGGER.warning(f"Error reading AEM message: {e}")
                break
        
        return samples


def create_daq_interface(config: DAQConfig, **kwargs) -> PressureDAQInterface:
    """
    Factory function to create appropriate DAQ interface.
    
    Args:
        config: DAQ configuration
        **kwargs: Additional parameters for specific DAQ types
        
    Returns:
        PressureDAQInterface instance
    """
    if config.daq_type == DAQType.AEM_SERIES_2:
        return AEMSeries2Interface(config)
    elif config.daq_type == DAQType.GENERIC_CAN:
        message_ids = kwargs.get('message_ids', {})
        return GenericCANDaqInterface(config, message_ids)
    elif config.daq_type == DAQType.SERIAL:
        baudrate = kwargs.get('baudrate', 115200)
        return SerialDaqInterface(config, baudrate)
    else:
        raise ValueError(f"Unsupported DAQ type: {config.daq_type}")

