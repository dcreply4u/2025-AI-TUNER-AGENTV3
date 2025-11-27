"""
NUCLEO-H755ZI-Q Interface

Provides seamless integration with the STM32H755ZI development board
for real-time sensor data acquisition and control.

Supports multiple communication interfaces:
- UART (Serial) - Recommended for initial integration
- SPI - High-speed data streaming
- I2C - Multi-device sensor expansion
- CAN - Direct automotive ECU communication
- USB - Plug-and-play connectivity
- Ethernet - Network-based integration
"""

from __future__ import annotations

import json
import logging
import struct
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    serial = None  # type: ignore

try:
    import spidev
    SPI_AVAILABLE = True
except ImportError:
    SPI_AVAILABLE = False
    spidev = None  # type: ignore

try:
    import smbus
    I2C_AVAILABLE = True
except ImportError:
    I2C_AVAILABLE = False
    smbus = None  # type: ignore

try:
    from interfaces.can_interface import CANMessage, CANMessageType, OptimizedCANInterface
    CAN_AVAILABLE = True
except ImportError:
    CAN_AVAILABLE = False
    CANMessage = None  # type: ignore
    CANMessageType = None  # type: ignore
    OptimizedCANInterface = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class NucleoConnectionType(Enum):
    """Connection types for NUCLEO board."""
    UART = "uart"
    SPI = "spi"
    I2C = "i2c"
    CAN = "can"
    USB = "usb"
    ETHERNET = "ethernet"


class NucleoSensorType(Enum):
    """Sensor types supported by NUCLEO."""
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    RPM = "rpm"
    VOLTAGE = "voltage"
    CURRENT = "current"
    ANALOG = "analog"
    DIGITAL = "digital"
    CAN_MESSAGE = "can_message"


@dataclass
class NucleoSensorConfig:
    """Configuration for a sensor on NUCLEO board."""
    name: str
    sensor_type: NucleoSensorType
    channel: int
    unit: str = ""
    min_value: float = 0.0
    max_value: float = 100.0
    scale: float = 1.0
    offset: float = 0.0


@dataclass
class NucleoSensorReading:
    """Sensor reading from NUCLEO board."""
    name: str
    value: float
    unit: str
    timestamp: float
    quality: float = 1.0  # 0.0-1.0, signal quality/confidence


@dataclass
class NucleoStatus:
    """Status information from NUCLEO board."""
    connected: bool
    uptime: float
    cpu_usage_m7: float  # M7 core usage %
    cpu_usage_m4: float  # M4 core usage %
    memory_free: int  # Free memory in bytes
    error_count: int
    last_error: Optional[str] = None


class NucleoInterface:
    """
    Interface for NUCLEO-H755ZI-Q development board.
    
    Provides real-time sensor data acquisition and control
    through multiple communication interfaces.
    """
    
    # NUCLEO board identification
    NUCLEO_VID_PID = [
        ("0483", "374b"),  # STM32 Virtual COM Port
        ("0483", "5740"),  # STM32 DFU
    ]
    
    def __init__(
        self,
        connection_type: NucleoConnectionType = NucleoConnectionType.UART,
        port: Optional[str] = None,
        baudrate: int = 921600,
        timeout: float = 1.0,
        auto_detect: bool = True,
        sensor_configs: Optional[List[NucleoSensorConfig]] = None,
    ):
        """
        Initialize NUCLEO interface.
        
        Args:
            connection_type: Communication interface to use
            port: Serial port path (auto-detected if None)
            baudrate: UART baudrate (921600 recommended)
            timeout: Communication timeout in seconds
            auto_detect: Auto-detect NUCLEO board
            sensor_configs: List of sensor configurations
        """
        self.connection_type = connection_type
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.auto_detect = auto_detect
        
        self.connected = False
        self._interface = None
        self._lock = threading.Lock()
        self._sensor_configs: Dict[str, NucleoSensorConfig] = {}
        self._last_readings: Dict[str, NucleoSensorReading] = {}
        self._status = NucleoStatus(
            connected=False,
            uptime=0.0,
            cpu_usage_m7=0.0,
            cpu_usage_m4=0.0,
            memory_free=0,
            error_count=0,
        )
        
        # Threading
        self._read_thread: Optional[threading.Thread] = None
        self._running = False
        self._data_callback: Optional[Callable[[Dict[str, float]], None]] = None
        
        # CAN integration
        self._can_enabled = False
        self._can_callback: Optional[Callable[[CANMessage], None]] = None
        self._can_interface: Optional[OptimizedCANInterface] = None
        self._can_monitoring = False
        
        # Load sensor configurations
        if sensor_configs:
            for config in sensor_configs:
                self._sensor_configs[config.name] = config
    
    def connect(self) -> bool:
        """Connect to NUCLEO board."""
        try:
            if self.connection_type == NucleoConnectionType.UART:
                return self._connect_uart()
            elif self.connection_type == NucleoConnectionType.SPI:
                return self._connect_spi()
            elif self.connection_type == NucleoConnectionType.I2C:
                return self._connect_i2c()
            else:
                LOGGER.error(f"Connection type {self.connection_type} not yet implemented")
                return False
        except Exception as e:
            LOGGER.error(f"Failed to connect to NUCLEO: {e}", exc_info=True)
            return False
    
    def _connect_uart(self) -> bool:
        """Connect via UART/Serial."""
        if not SERIAL_AVAILABLE:
            LOGGER.error("pyserial not available. Install with: pip install pyserial")
            return False
        
        # Auto-detect port if not specified
        if not self.port and self.auto_detect:
            self.port = self._detect_nucleo_port()
            if not self.port:
                LOGGER.warning("NUCLEO board not detected. Available ports:")
                for port in serial.tools.list_ports.comports():
                    LOGGER.info(f"  - {port.device}: {port.description}")
                return False
        
        if not self.port:
            LOGGER.error("No serial port specified")
            return False
        
        try:
            self._interface = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
            )
            
            # Flush buffers
            self._interface.reset_input_buffer()
            self._interface.reset_output_buffer()
            
            # Test connection
            if self._ping():
                self.connected = True
                self._status.connected = True
                self._start_read_thread()
                LOGGER.info(f"NUCLEO connected via UART on {self.port} at {self.baudrate} baud")
                return True
            else:
                LOGGER.warning("NUCLEO did not respond to ping")
                self._interface.close()
                self._interface = None
                return False
                
        except serial.SerialException as e:
            LOGGER.error(f"Serial connection failed: {e}")
            return False
    
    def _connect_spi(self) -> bool:
        """Connect via SPI."""
        if not SPI_AVAILABLE:
            LOGGER.error("spidev not available. Install with: pip install spidev")
            return False
        
        try:
            # SPI bus 0, device 0 (CE0)
            self._interface = spidev.SpiDev()
            self._interface.open(0, 0)  # Bus 0, Device 0
            self._interface.max_speed_hz = 8000000  # 8MHz
            self._interface.mode = 0b00  # SPI mode 0
            
            # Test connection
            if self._ping():
                self.connected = True
                self._status.connected = True
                self._start_read_thread()
                LOGGER.info("NUCLEO connected via SPI")
                return True
            else:
                self._interface.close()
                self._interface = None
                return False
                
        except Exception as e:
            LOGGER.error(f"SPI connection failed: {e}")
            return False
    
    def _connect_i2c(self) -> bool:
        """Connect via I2C."""
        if not I2C_AVAILABLE:
            LOGGER.error("smbus not available. Install with: pip install smbus")
            return False
        
        try:
            # I2C bus 1, address 0x48 (default for NUCLEO)
            self._interface = smbus.SMBus(1)
            self._i2c_address = 0x48  # Default address
            
            # Test connection
            if self._ping():
                self.connected = True
                self._status.connected = True
                self._start_read_thread()
                LOGGER.info(f"NUCLEO connected via I2C at address 0x{self._i2c_address:02x}")
                return True
            else:
                self._interface = None
                return False
                
        except Exception as e:
            LOGGER.error(f"I2C connection failed: {e}")
            return False
    
    def _detect_nucleo_port(self) -> Optional[str]:
        """Auto-detect NUCLEO board serial port."""
        if not SERIAL_AVAILABLE:
            return None
        
        for port in serial.tools.list_ports.comports():
            # Check VID:PID
            vid_pid = (f"{port.vid:04x}" if port.vid else None,
                      f"{port.pid:04x}" if port.pid else None)
            
            if vid_pid in self.NUCLEO_VID_PID:
                LOGGER.info(f"Detected NUCLEO board on {port.device}")
                return port.device
            
            # Also check description
            desc_lower = port.description.lower() if port.description else ""
            if "stm32" in desc_lower or "nucleo" in desc_lower:
                LOGGER.info(f"Detected STM32/NUCLEO device on {port.device}")
                return port.device
        
        return None
    
    def _ping(self) -> bool:
        """Ping NUCLEO board to test connection."""
        try:
            if self.connection_type == NucleoConnectionType.UART:
                # Send ping command
                cmd = {"cmd": "ping", "timestamp": time.time()}
                response = self._send_command_uart(cmd, timeout=0.5)
                return response is not None and response.get("status") == "ok"
            elif self.connection_type == NucleoConnectionType.SPI:
                # Send ping via SPI
                return self._send_command_spi({"cmd": "ping"}) is not None
            elif self.connection_type == NucleoConnectionType.I2C:
                # Send ping via I2C
                return self._send_command_i2c({"cmd": "ping"}) is not None
            elif self.connection_type == NucleoConnectionType.CAN:
                # For CAN, we still need base connection (UART/SPI/I2C)
                # So ping via that connection
                if self._interface:
                    return self._send_command_uart({"cmd": "ping"}) is not None
            return False
        except Exception:
            return False
    
    def disconnect(self) -> None:
        """Disconnect from NUCLEO board."""
        # Disable CAN gateway if enabled
        if self._can_enabled:
            self.disable_can_gateway()
        
        self._running = False
        
        if self._read_thread and self._read_thread.is_alive():
            self._read_thread.join(timeout=2.0)
        
        if self._interface:
            try:
                if self.connection_type == NucleoConnectionType.UART:
                    self._interface.close()
                elif self.connection_type == NucleoConnectionType.SPI:
                    self._interface.close()
                elif self.connection_type == NucleoConnectionType.I2C:
                    pass  # I2C doesn't need explicit close
            except Exception as e:
                LOGGER.error(f"Error closing interface: {e}")
            finally:
                self._interface = None
        
        self.connected = False
        self._status.connected = False
        LOGGER.info("NUCLEO disconnected")
    
    def is_connected(self) -> bool:
        """Check if connected to NUCLEO board."""
        return self.connected and self._interface is not None
    
    def read_sensors(self, sensor_list: Optional[List[str]] = None) -> Dict[str, float]:
        """
        Read sensor values from NUCLEO board.
        
        Args:
            sensor_list: List of sensor names to read (None = all)
        
        Returns:
            Dictionary of sensor name -> value
        """
        if not self.is_connected():
            return {}
        
        try:
            if self.connection_type == NucleoConnectionType.UART:
                cmd = {
                    "cmd": "read_sensors",
                    "sensors": sensor_list or list(self._sensor_configs.keys()),
                    "timestamp": time.time(),
                }
                response = self._send_command_uart(cmd)
                if response and "data" in response:
                    return response["data"]
            elif self.connection_type == NucleoConnectionType.SPI:
                cmd = {"cmd": "read_sensors", "sensors": sensor_list}
                response = self._send_command_spi(cmd)
                if response and "data" in response:
                    return response["data"]
            elif self.connection_type == NucleoConnectionType.I2C:
                cmd = {"cmd": "read_sensors", "sensors": sensor_list}
                response = self._send_command_i2c(cmd)
                if response and "data" in response:
                    return response["data"]
        except Exception as e:
            LOGGER.error(f"Error reading sensors: {e}")
            self._status.error_count += 1
            self._status.last_error = str(e)
        
        return {}
    
    def read_sensor(self, sensor_name: str) -> Optional[float]:
        """Read a single sensor value."""
        readings = self.read_sensors([sensor_name])
        return readings.get(sensor_name)
    
    def send_command(self, command: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Send command to NUCLEO board.
        
        Args:
            command: Command dictionary
        
        Returns:
            Response dictionary or None
        """
        if not self.is_connected():
            return None
        
        try:
            if self.connection_type == NucleoConnectionType.UART:
                return self._send_command_uart(command)
            elif self.connection_type == NucleoConnectionType.SPI:
                return self._send_command_spi(command)
            elif self.connection_type == NucleoConnectionType.I2C:
                return self._send_command_i2c(command)
        except Exception as e:
            LOGGER.error(f"Error sending command: {e}")
            self._status.error_count += 1
            self._status.last_error = str(e)
        
        return None
    
    def _send_command_uart(self, command: Dict[str, Any], timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Send command via UART."""
        if not self._interface:
            return None
        
        try:
            # Serialize command to JSON
            cmd_json = json.dumps(command) + "\n"
            cmd_bytes = cmd_json.encode('utf-8')
            
            # Send command
            self._interface.write(cmd_bytes)
            self._interface.flush()
            
            # Read response
            timeout_orig = self._interface.timeout
            if timeout:
                self._interface.timeout = timeout
            
            try:
                response_line = self._interface.readline()
                if response_line:
                    response_str = response_line.decode('utf-8').strip()
                    return json.loads(response_str)
            finally:
                self._interface.timeout = timeout_orig
            
        except Exception as e:
            LOGGER.error(f"UART command error: {e}")
        
        return None
    
    def _send_command_spi(self, command: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send command via SPI."""
        if not self._interface:
            return None
        
        try:
            # Serialize command to JSON
            cmd_json = json.dumps(command)
            cmd_bytes = cmd_json.encode('utf-8')
            
            # SPI frame format: [length: 2 bytes][data: N bytes]
            length_bytes = struct.pack('<H', len(cmd_bytes))
            frame = length_bytes + cmd_bytes
            
            # Send and receive
            response = self._interface.xfer2(list(frame))
            
            # Parse response (simplified - actual implementation depends on STM32 firmware)
            if len(response) > 2:
                resp_length = struct.unpack('<H', bytes(response[:2]))[0]
                resp_data = bytes(response[2:2+resp_length])
                return json.loads(resp_data.decode('utf-8'))
            
        except Exception as e:
            LOGGER.error(f"SPI command error: {e}")
        
        return None
    
    def _send_command_i2c(self, command: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send command via I2C."""
        if not self._interface:
            return None
        
        try:
            # Serialize command to JSON
            cmd_json = json.dumps(command)
            cmd_bytes = cmd_json.encode('utf-8')
            
            # I2C write (register 0x00 = command register)
            self._interface.write_i2c_block_data(self._i2c_address, 0x00, list(cmd_bytes))
            
            # Small delay
            time.sleep(0.01)
            
            # I2C read (register 0x01 = response register)
            response_bytes = self._interface.read_i2c_block_data(self._i2c_address, 0x01, 256)
            response_str = bytes(response_bytes).decode('utf-8').rstrip('\x00')
            
            return json.loads(response_str)
            
        except Exception as e:
            LOGGER.error(f"I2C command error: {e}")
        
        return None
    
    def set_data_callback(self, callback: Callable[[Dict[str, float]], None]) -> None:
        """Set callback for continuous sensor data updates."""
        self._data_callback = callback
    
    def _start_read_thread(self) -> None:
        """Start background thread for continuous data reading."""
        if self._read_thread and self._read_thread.is_alive():
            return
        
        self._running = True
        self._read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._read_thread.start()
    
    def _read_loop(self) -> None:
        """Background loop for reading sensor data."""
        while self._running and self.connected:
            try:
                # Read all sensors
                readings = self.read_sensors()
                
                if readings and self._data_callback:
                    self._data_callback(readings)
                
                # Update last readings
                timestamp = time.time()
                for name, value in readings.items():
                    config = self._sensor_configs.get(name)
                    unit = config.unit if config else ""
                    self._last_readings[name] = NucleoSensorReading(
                        name=name,
                        value=value,
                        unit=unit,
                        timestamp=timestamp,
                    )
                
                # Small delay to prevent CPU spinning
                time.sleep(0.01)  # 100Hz update rate
                
            except Exception as e:
                LOGGER.error(f"Error in read loop: {e}")
                time.sleep(0.1)
    
    def get_status(self) -> NucleoStatus:
        """Get NUCLEO board status."""
        if self.is_connected():
            # Request status from board
            response = self.send_command({"cmd": "get_status"})
            if response and "status" in response:
                status_data = response["status"]
                self._status.uptime = status_data.get("uptime", 0.0)
                self._status.cpu_usage_m7 = status_data.get("cpu_m7", 0.0)
                self._status.cpu_usage_m4 = status_data.get("cpu_m4", 0.0)
                self._status.memory_free = status_data.get("memory_free", 0)
        
        return self._status
    
    def add_sensor_config(self, config: NucleoSensorConfig) -> None:
        """Add sensor configuration."""
        self._sensor_configs[config.name] = config
    
    def get_last_reading(self, sensor_name: str) -> Optional[NucleoSensorReading]:
        """Get last reading for a sensor."""
        return self._last_readings.get(sensor_name)
    
    # ========== CAN Integration Methods ==========
    
    def enable_can_gateway(
        self,
        can_bitrate: int = 500000,
        can_channel: str = "can1",
        message_callback: Optional[Callable[[CANMessage], None]] = None,
    ) -> bool:
        """
        Enable CAN gateway mode on NUCLEO.
        
        The NUCLEO will act as a CAN gateway, forwarding messages
        between its onboard CAN controller and the Pi.
        
        Args:
            can_bitrate: CAN bus bitrate (default: 500000)
            can_channel: CAN channel name on NUCLEO (can1 or can2)
            message_callback: Callback for received CAN messages
        
        Returns:
            True if CAN gateway enabled successfully
        """
        if not CAN_AVAILABLE:
            LOGGER.error("CAN interface not available")
            return False
        
        self._can_callback = message_callback
        
        # If not connected, connect first (UART recommended for control)
        if not self.connected:
            if self.connection_type == NucleoConnectionType.CAN:
                # For CAN mode, we need base connection first
                if not self._interface:
                    if self.auto_detect:
                        self.port = self._detect_nucleo_port()
                    if self.port and SERIAL_AVAILABLE:
                        try:
                            self._interface = serial.Serial(
                                port=self.port,
                                baudrate=self.baudrate,
                                timeout=self.timeout,
                            )
                        except Exception as e:
                            LOGGER.error(f"Failed to establish base connection for CAN: {e}")
                            return False
            
            if not self.connect():
                return False
        
        # Enable CAN on NUCLEO
        try:
            response = self.send_command({
                "cmd": "enable_can",
                "bitrate": can_bitrate,
                "channel": can_channel,
            })
            
            if response and response.get("status") == "ok":
                self._can_enabled = True
                self._start_can_monitoring()
                LOGGER.info(f"NUCLEO CAN gateway enabled on {can_channel} @ {can_bitrate} bps")
                return True
            else:
                LOGGER.error("Failed to enable CAN gateway on NUCLEO")
                return False
        except Exception as e:
            LOGGER.error(f"Failed to enable CAN gateway: {e}")
            return False
    
    def send_can_message(
        self,
        arbitration_id: int,
        data: bytes,
        extended: bool = False,
    ) -> bool:
        """
        Send CAN message through NUCLEO's CAN controller.
        
        Args:
            arbitration_id: CAN ID
            data: Message data (up to 8 bytes for standard, 64 for CAN FD)
            extended: Use extended 29-bit ID (default: False)
        
        Returns:
            True if message sent successfully
        """
        if not self._can_enabled:
            LOGGER.warning("CAN gateway not enabled")
            return False
        
        try:
            response = self.send_command({
                "cmd": "send_can",
                "id": arbitration_id,
                "data": list(data),
                "extended": extended,
            })
            
            return response is not None and response.get("status") == "ok"
        except Exception as e:
            LOGGER.error(f"Error sending CAN message: {e}")
            return False
    
    def _start_can_monitoring(self) -> None:
        """Start background thread for monitoring CAN messages from NUCLEO."""
        if self._can_monitoring:
            return
        
        self._can_monitoring = True
        can_thread = threading.Thread(target=self._can_monitor_loop, daemon=True)
        can_thread.start()
    
    def _can_monitor_loop(self) -> None:
        """Background loop for receiving CAN messages from NUCLEO."""
        while self._can_monitoring and self.connected and self._can_enabled:
            try:
                # Request CAN messages from NUCLEO
                response = self.send_command({"cmd": "read_can", "count": 10})
                
                if response and "messages" in response:
                    for msg_data in response["messages"]:
                        # Convert to CANMessage
                        can_msg = CANMessage(
                            arbitration_id=msg_data["id"],
                            data=bytes(msg_data["data"]),
                            timestamp=msg_data.get("timestamp", time.time()),
                            channel=msg_data.get("channel", "nucleo_can"),
                            message_type=CANMessageType.EXTENDED if msg_data.get("extended") else CANMessageType.STANDARD,
                            dlc=len(msg_data["data"]),
                        )
                        
                        # Call callback if set
                        if self._can_callback:
                            try:
                                self._can_callback(can_msg)
                            except Exception as e:
                                LOGGER.error(f"Error in CAN callback: {e}")
                
                time.sleep(0.01)  # 100Hz polling
                
            except Exception as e:
                LOGGER.error(f"Error in CAN monitor loop: {e}")
                time.sleep(0.1)
    
    def disable_can_gateway(self) -> None:
        """Disable CAN gateway mode."""
        self._can_monitoring = False
        
        if self.connected:
            try:
                self.send_command({"cmd": "disable_can"})
            except Exception:
                pass
        
        self._can_enabled = False
        LOGGER.info("NUCLEO CAN gateway disabled")
    
    def get_can_statistics(self) -> Optional[Dict[str, Any]]:
        """Get CAN bus statistics from NUCLEO."""
        if not self._can_enabled:
            return None
        
        try:
            response = self.send_command({"cmd": "get_can_stats"})
            if response and "stats" in response:
                return response["stats"]
        except Exception as e:
            LOGGER.error(f"Error getting CAN statistics: {e}")
        
        return None


__all__ = [
    "NucleoInterface",
    "NucleoConnectionType",
    "NucleoSensorType",
    "NucleoSensorConfig",
    "NucleoSensorReading",
    "NucleoStatus",
]

