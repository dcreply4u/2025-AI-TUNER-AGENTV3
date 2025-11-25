"""
Hardware Interface Manager
Comprehensive support for external inputs: GPIO breakout boards, Arduino, I2C/SPI sensors, serial devices
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any

LOGGER = logging.getLogger(__name__)


class InterfaceType(Enum):
    """Hardware interface types."""
    GPIO_DIRECT = "gpio_direct"  # Direct GPIO (RPi, Jetson)
    GPIO_BREAKOUT = "gpio_breakout"  # GPIO breakout board
    ARDUINO = "arduino"  # Arduino as GPIO breakout
    I2C = "i2c"  # I2C bus
    SPI = "spi"  # SPI bus
    SERIAL = "serial"  # Serial/UART
    USB_SERIAL = "usb_serial"  # USB serial device
    CAN = "can"  # CAN bus
    PWM = "pwm"  # PWM input/output


class BreakoutBoardType(Enum):
    """Supported GPIO breakout board types."""
    RASPBERRY_PI = "raspberry_pi"
    JETSON = "jetson"
    ARDUINO_UNO = "arduino_uno"
    ARDUINO_MEGA = "arduino_mega"
    ARDUINO_NANO = "arduino_nano"
    ESP32 = "esp32"
    PICO = "pico"
    ADAFRUIT_FEATHER = "adafruit_feather"
    CUSTOM = "custom"


@dataclass
class GPIOConfig:
    """GPIO pin configuration."""
    pin: int
    mode: str  # "input", "output", "pwm"
    pull: str = "none"  # "up", "down", "none"
    active_low: bool = False
    debounce_ms: int = 50
    pwm_frequency: Optional[int] = None  # For PWM mode
    pwm_duty_cycle: Optional[float] = None  # 0-100


@dataclass
class HardwareInterface:
    """Hardware interface configuration."""
    interface_id: str
    interface_type: InterfaceType
    board_type: Optional[BreakoutBoardType] = None
    name: str = ""
    description: str = ""
    enabled: bool = True
    
    # Connection parameters
    device_path: Optional[str] = None  # /dev/ttyUSB0, /dev/i2c-1, etc.
    i2c_address: Optional[int] = None
    baud_rate: Optional[int] = None
    can_channel: Optional[str] = None
    can_bitrate: Optional[int] = None
    
    # GPIO pins
    gpio_pins: Dict[int, GPIOConfig] = field(default_factory=dict)
    
    # Status
    connected: bool = False
    last_update: float = field(default_factory=time.time)
    error_count: int = 0


class HardwareInterfaceManager:
    """
    Comprehensive hardware interface manager.
    
    Supports:
    - GPIO breakout boards (RPi, Jetson, Arduino, ESP32, etc.)
    - I2C/SPI expansion boards
    - Serial/UART devices
    - USB serial devices
    - CAN bus interfaces
    - PWM inputs/outputs
    """
    
    def __init__(self):
        """Initialize hardware interface manager."""
        self.interfaces: Dict[str, HardwareInterface] = {}
        self._gpio_handlers: Dict[str, Any] = {}
        self._i2c_buses: Dict[str, Any] = {}
        self._serial_ports: Dict[str, Any] = {}
        self._can_buses: Dict[str, Any] = {}
        
        # Auto-detect available hardware
        self._detect_hardware()
    
    def _detect_hardware(self) -> None:
        """Auto-detect available hardware interfaces."""
        LOGGER.info("Detecting hardware interfaces...")
        
        # Detect GPIO interfaces
        self._detect_gpio_interfaces()
        
        # Detect I2C devices
        self._detect_i2c_devices()
        
        # Detect serial devices
        self._detect_serial_devices()
        
        # Detect CAN interfaces
        self._detect_can_interfaces()
        
        LOGGER.info("Detected %d hardware interfaces", len(self.interfaces))
    
    def _detect_gpio_interfaces(self) -> None:
        """Detect GPIO interfaces (RPi, Jetson, etc.)."""
        # Try Raspberry Pi GPIO
        try:
            import RPi.GPIO as GPIO
            interface = HardwareInterface(
                interface_id="gpio_rpi",
                interface_type=InterfaceType.GPIO_DIRECT,
                board_type=BreakoutBoardType.RASPBERRY_PI,
                name="Raspberry Pi GPIO",
                description="Built-in GPIO pins",
            )
            self.interfaces[interface.interface_id] = interface
            self._gpio_handlers[interface.interface_id] = GPIO
            LOGGER.info("Detected Raspberry Pi GPIO")
        except ImportError:
            pass
        
        # Try Jetson GPIO
        try:
            import Jetson.GPIO as GPIO
            interface = HardwareInterface(
                interface_id="gpio_jetson",
                interface_type=InterfaceType.GPIO_DIRECT,
                board_type=BreakoutBoardType.JETSON,
                name="Jetson GPIO",
                description="Built-in GPIO pins",
            )
            self.interfaces[interface.interface_id] = interface
            self._gpio_handlers[interface.interface_id] = GPIO
            LOGGER.info("Detected Jetson GPIO")
        except ImportError:
            pass
        
        # Try Arduino via serial
        self._detect_arduino()
    
    def _detect_arduino(self) -> None:
        """Detect Arduino boards connected via USB serial."""
        try:
            import serial.tools.list_ports
            
            ports = serial.tools.list_ports.comports()
            for port in ports:
                # Check for Arduino-like devices
                if any(keyword in port.description.lower() for keyword in ['arduino', 'ch340', 'ch341', 'ftdi', 'cp210']):
                    board_type = BreakoutBoardType.ARDUINO_UNO
                    if 'mega' in port.description.lower():
                        board_type = BreakoutBoardType.ARDUINO_MEGA
                    elif 'nano' in port.description.lower():
                        board_type = BreakoutBoardType.ARDUINO_NANO
                    
                    interface = HardwareInterface(
                        interface_id=f"arduino_{port.device}",
                        interface_type=InterfaceType.ARDUINO,
                        board_type=board_type,
                        name=f"Arduino {port.description}",
                        description=f"Arduino board on {port.device}",
                        device_path=port.device,
                        baud_rate=115200,  # Default Arduino baud rate
                    )
                    self.interfaces[interface.interface_id] = interface
                    LOGGER.info("Detected Arduino: %s on %s", port.description, port.device)
        except ImportError:
            LOGGER.warning("pyserial not available for Arduino detection")
        except Exception as e:
            LOGGER.error("Error detecting Arduino: %s", e)
    
    def _detect_i2c_devices(self) -> None:
        """Detect I2C devices."""
        try:
            import board
            import busio
            
            # Try to initialize I2C bus
            i2c = busio.I2C(board.SCL, board.SDA)
            
            interface = HardwareInterface(
                interface_id="i2c_main",
                interface_type=InterfaceType.I2C,
                name="I2C Bus",
                description="Main I2C bus (SDA/SCL)",
                device_path="/dev/i2c-1",
            )
            self.interfaces[interface.interface_id] = interface
            self._i2c_buses[interface.interface_id] = i2c
            
            # Scan for I2C devices
            try:
                i2c.try_lock()
                devices = i2c.scan()
                i2c.unlock()
                LOGGER.info("Detected I2C bus with %d devices", len(devices))
            except Exception:
                pass
        except ImportError:
            LOGGER.warning("adafruit-blinka not available for I2C")
        except Exception as e:
            LOGGER.debug("I2C not available: %s", e)
    
    def _detect_serial_devices(self) -> None:
        """Detect serial/UART devices."""
        try:
            import serial.tools.list_ports
            
            ports = serial.tools.list_ports.comports()
            for port in ports:
                # Skip Arduino (already detected)
                if any(keyword in port.description.lower() for keyword in ['arduino', 'ch340', 'ch341']):
                    continue
                
                interface = HardwareInterface(
                    interface_id=f"serial_{port.device}",
                    interface_type=InterfaceType.USB_SERIAL,
                    name=f"Serial Device: {port.description}",
                    description=f"USB serial device on {port.device}",
                    device_path=port.device,
                    baud_rate=9600,  # Default
                )
                self.interfaces[interface.interface_id] = interface
                LOGGER.info("Detected serial device: %s on %s", port.description, port.device)
        except ImportError:
            LOGGER.warning("pyserial not available for serial detection")
        except Exception as e:
            LOGGER.error("Error detecting serial devices: %s", e)
    
    def _detect_can_interfaces(self) -> None:
        """Detect CAN bus interfaces."""
        try:
            import can
            
            # Get available CAN interfaces
            interfaces = can.detect_available_configs()
            for iface in interfaces:
                interface = HardwareInterface(
                    interface_id=f"can_{iface.get('interface', 'unknown')}",
                    interface_type=InterfaceType.CAN,
                    name=f"CAN {iface.get('interface', 'unknown')}",
                    description=f"CAN bus interface",
                    can_channel=iface.get('channel', 'can0'),
                    can_bitrate=iface.get('bitrate', 500000),
                )
                self.interfaces[interface.interface_id] = interface
                LOGGER.info("Detected CAN interface: %s", iface.get('interface'))
        except ImportError:
            LOGGER.warning("python-can not available for CAN detection")
        except Exception as e:
            LOGGER.debug("CAN not available: %s", e)
    
    def add_interface(self, interface: HardwareInterface) -> bool:
        """Add a hardware interface."""
        self.interfaces[interface.interface_id] = interface
        return True
    
    def get_interface(self, interface_id: str) -> Optional[HardwareInterface]:
        """Get interface by ID."""
        return self.interfaces.get(interface_id)
    
    def list_interfaces(self, interface_type: Optional[InterfaceType] = None) -> List[HardwareInterface]:
        """List all interfaces, optionally filtered by type."""
        interfaces = list(self.interfaces.values())
        if interface_type:
            interfaces = [i for i in interfaces if i.interface_type == interface_type]
        return interfaces
    
    def configure_gpio_pin(
        self,
        interface_id: str,
        pin: int,
        mode: str = "input",
        pull: str = "none",
        active_low: bool = False,
        debounce_ms: int = 50,
    ) -> bool:
        """
        Configure a GPIO pin.
        
        Args:
            interface_id: Interface ID
            pin: Pin number
            mode: "input", "output", or "pwm"
            pull: "up", "down", or "none"
            active_low: Active low signal
            debounce_ms: Debounce time in milliseconds
        """
        interface = self.get_interface(interface_id)
        if not interface:
            LOGGER.error("Interface not found: %s", interface_id)
            return False
        
        if interface.interface_type not in [InterfaceType.GPIO_DIRECT, InterfaceType.GPIO_BREAKOUT, InterfaceType.ARDUINO]:
            LOGGER.error("Interface %s does not support GPIO", interface_id)
            return False
        
        gpio_config = GPIOConfig(
            pin=pin,
            mode=mode,
            pull=pull,
            active_low=active_low,
            debounce_ms=debounce_ms,
        )
        
        interface.gpio_pins[pin] = gpio_config
        
        # Apply configuration to hardware
        if interface.interface_type == InterfaceType.GPIO_DIRECT:
            return self._configure_direct_gpio(interface, gpio_config)
        elif interface.interface_type == InterfaceType.ARDUINO:
            return self._configure_arduino_gpio(interface, gpio_config)
        
        return True
    
    def _configure_direct_gpio(self, interface: HardwareInterface, config: GPIOConfig) -> bool:
        """Configure direct GPIO (RPi, Jetson)."""
        try:
            GPIO = self._gpio_handlers.get(interface.interface_id)
            if not GPIO:
                return False
            
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Set pull resistor
            if config.pull == "up":
                pull_mode = GPIO.PUD_UP
            elif config.pull == "down":
                pull_mode = GPIO.PUD_DOWN
            else:
                pull_mode = GPIO.PUD_OFF
            
            # Configure pin
            if config.mode == "input":
                GPIO.setup(config.pin, GPIO.IN, pull_up_down=pull_mode)
            elif config.mode == "output":
                GPIO.setup(config.pin, GPIO.OUT)
            elif config.mode == "pwm":
                GPIO.setup(config.pin, GPIO.OUT)
                # PWM would be handled separately
            
            LOGGER.info("Configured GPIO pin %d on %s as %s", config.pin, interface.name, config.mode)
            return True
        except Exception as e:
            LOGGER.error("Failed to configure GPIO pin: %s", e)
            return False
    
    def _configure_arduino_gpio(self, interface: HardwareInterface, config: GPIOConfig) -> bool:
        """Configure Arduino GPIO via serial command."""
        try:
            import serial
            
            if not interface.device_path:
                return False
            
            # Open serial connection
            ser = serial.Serial(interface.device_path, interface.baud_rate or 115200, timeout=1)
            time.sleep(2)  # Wait for Arduino to reset
            
            # Send configuration command
            # Format: "CONFIG:pin:mode:pull:active_low"
            command = f"CONFIG:{config.pin}:{config.mode}:{config.pull}:{1 if config.active_low else 0}\n"
            ser.write(command.encode())
            
            response = ser.readline().decode().strip()
            ser.close()
            
            if "OK" in response:
                LOGGER.info("Configured Arduino pin %d as %s", config.pin, config.mode)
                return True
            else:
                LOGGER.error("Arduino configuration failed: %s", response)
                return False
        except Exception as e:
            LOGGER.error("Failed to configure Arduino GPIO: %s", e)
            return False
    
    def read_gpio(self, interface_id: str, pin: int) -> Optional[bool]:
        """Read GPIO pin value."""
        interface = self.get_interface(interface_id)
        if not interface:
            return None
        
        config = interface.gpio_pins.get(pin)
        if not config or config.mode != "input":
            LOGGER.warning("Pin %d not configured as input", pin)
            return None
        
        if interface.interface_type == InterfaceType.GPIO_DIRECT:
            return self._read_direct_gpio(interface, pin, config)
        elif interface.interface_type == InterfaceType.ARDUINO:
            return self._read_arduino_gpio(interface, pin)
        
        return None
    
    def _read_direct_gpio(self, interface: HardwareInterface, pin: int, config: GPIOConfig) -> Optional[bool]:
        """Read direct GPIO pin."""
        try:
            GPIO = self._gpio_handlers.get(interface.interface_id)
            if not GPIO:
                return None
            
            value = GPIO.input(pin)
            
            if config.active_low:
                return value == GPIO.LOW
            return value == GPIO.HIGH
        except Exception as e:
            LOGGER.error("Failed to read GPIO pin %d: %s", pin, e)
            return None
    
    def _read_arduino_gpio(self, interface: HardwareInterface, pin: int) -> Optional[bool]:
        """Read Arduino GPIO via serial."""
        try:
            import serial
            
            if not interface.device_path:
                return None
            
            ser = serial.Serial(interface.device_path, interface.baud_rate or 115200, timeout=1)
            
            # Send read command
            command = f"READ:{pin}\n"
            ser.write(command.encode())
            
            response = ser.readline().decode().strip()
            ser.close()
            
            if response.startswith("VALUE:"):
                value = int(response.split(":")[1])
                return value == 1
            return None
        except Exception as e:
            LOGGER.error("Failed to read Arduino GPIO: %s", e)
            return None
    
    def write_gpio(self, interface_id: str, pin: int, value: bool) -> bool:
        """Write GPIO pin value."""
        interface = self.get_interface(interface_id)
        if not interface:
            return False
        
        config = interface.gpio_pins.get(pin)
        if not config or config.mode != "output":
            LOGGER.warning("Pin %d not configured as output", pin)
            return False
        
        if interface.interface_type == InterfaceType.GPIO_DIRECT:
            return self._write_direct_gpio(interface, pin, value)
        elif interface.interface_type == InterfaceType.ARDUINO:
            return self._write_arduino_gpio(interface, pin, value)
        
        return False
    
    def _write_direct_gpio(self, interface: HardwareInterface, pin: int, value: bool) -> bool:
        """Write direct GPIO pin."""
        try:
            GPIO = self._gpio_handlers.get(interface.interface_id)
            if not GPIO:
                return False
            
            GPIO.output(pin, GPIO.HIGH if value else GPIO.LOW)
            return True
        except Exception as e:
            LOGGER.error("Failed to write GPIO pin %d: %s", pin, e)
            return False
    
    def _write_arduino_gpio(self, interface: HardwareInterface, pin: int, value: bool) -> bool:
        """Write Arduino GPIO via serial."""
        try:
            import serial
            
            if not interface.device_path:
                return False
            
            ser = serial.Serial(interface.device_path, interface.baud_rate or 115200, timeout=1)
            
            # Send write command
            command = f"WRITE:{pin}:{1 if value else 0}\n"
            ser.write(command.encode())
            
            response = ser.readline().decode().strip()
            ser.close()
            
            return "OK" in response
        except Exception as e:
            LOGGER.error("Failed to write Arduino GPIO: %s", e)
            return False
    
    def read_analog(self, interface_id: str, channel: int) -> Optional[float]:
        """Read analog value from ADC."""
        interface = self.get_interface(interface_id)
        if not interface:
            return None
        
        if interface.interface_type == InterfaceType.I2C:
            return self._read_i2c_adc(interface, channel)
        
        return None
    
    def _read_i2c_adc(self, interface: HardwareInterface, channel: int) -> Optional[float]:
        """Read from I2C ADC (e.g., ADS1115)."""
        try:
            from adafruit_ads1x15.ads1115 import ADS1115
            from adafruit_ads1x15.analog_in import AnalogIn
            import board
            import busio
            
            i2c = self._i2c_buses.get(interface.interface_id)
            if not i2c:
                i2c = busio.I2C(board.SCL, board.SDA)
                self._i2c_buses[interface.interface_id] = i2c
            
            ads = ADS1115(i2c, address=interface.i2c_address or 0x48)
            
            channel_map = {
                0: AnalogIn(ads, ADS1115.P0),
                1: AnalogIn(ads, ADS1115.P1),
                2: AnalogIn(ads, ADS1115.P2),
                3: AnalogIn(ads, ADS1115.P3),
            }
            
            analog_channel = channel_map.get(channel)
            if analog_channel:
                return analog_channel.voltage
            
            return None
        except ImportError:
            LOGGER.warning("adafruit-circuitpython-ads1x15 not available")
            return None
        except Exception as e:
            LOGGER.error("Failed to read I2C ADC: %s", e)
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all interfaces."""
        status = {
            "total_interfaces": len(self.interfaces),
            "connected": sum(1 for i in self.interfaces.values() if i.connected),
            "interfaces": []
        }
        
        for interface in self.interfaces.values():
            status["interfaces"].append({
                "id": interface.interface_id,
                "type": interface.interface_type.value,
                "name": interface.name,
                "connected": interface.connected,
                "enabled": interface.enabled,
                "gpio_pins": len(interface.gpio_pins),
            })
        
        return status
















