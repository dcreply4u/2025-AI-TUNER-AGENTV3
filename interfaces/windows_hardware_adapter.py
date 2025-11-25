"""
Windows Hardware Adapter
Provides Windows-compatible hardware interfaces using USB adapters, Arduino, etc.
"""

from __future__ import annotations

import logging
import platform
import serial
import serial.tools.list_ports
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

LOGGER = logging.getLogger(__name__)

# Check for Windows
IS_WINDOWS = platform.system() == "Windows"

# Try to import Windows-specific libraries
try:
    import usb.core
    import usb.util
    USB_AVAILABLE = True
except ImportError:
    USB_AVAILABLE = False
    LOGGER.warning("pyusb not available - USB device detection limited")

try:
    import ftdi1 as ftdi
    FTDI_AVAILABLE = True
except ImportError:
    FTDI_AVAILABLE = False
    LOGGER.debug("FTDI library not available - FTDI adapters will use serial fallback")


class WindowsAdapterType(Enum):
    """Types of Windows hardware adapters."""
    ARDUINO_SERIAL = "arduino_serial"
    USB_GPIO_FTDI = "usb_gpio_ftdi"
    USB_GPIO_CH340 = "usb_gpio_ch340"
    USB_CAN = "usb_can"
    OBD2 = "obd2"
    USB_ADC = "usb_adc"


@dataclass
class WindowsAdapter:
    """Windows hardware adapter configuration."""
    adapter_type: WindowsAdapterType
    port: Optional[str] = None  # COM port for serial devices
    vid: Optional[int] = None  # USB Vendor ID
    pid: Optional[int] = None  # USB Product ID
    name: str = ""
    connected: bool = False
    device: Any = None  # Device handle


class WindowsHardwareAdapter:
    """
    Windows-compatible hardware adapter.
    
    Supports:
    - Arduino via serial (USB)
    - FTDI USB GPIO adapters
    - CH340 USB GPIO adapters
    - USB-CAN adapters
    - OBD-II adapters
    - USB ADC boards
    """
    
    # Known USB device IDs
    ARDUINO_VID_PIDS = [
        (0x2341, 0x0043),  # Arduino Uno
        (0x2341, 0x0001),  # Arduino Uno (old bootloader)
        (0x2341, 0x0036),  # Arduino Leonardo
        (0x2341, 0x0010),  # Arduino Mega 2560
        (0x1A86, 0x7523),  # CH340 (Arduino clones)
        (0x1A86, 0x5523),  # CH341
    ]
    
    FTDI_VID_PIDS = [
        (0x0403, 0x6014),  # FT232H
        (0x0403, 0x6010),  # FT2232H
        (0x0403, 0x6001),  # FT232
    ]
    
    CH340_VID_PIDS = [
        (0x1A86, 0x7523),  # CH340
        (0x1A86, 0x5523),  # CH341
    ]
    
    def __init__(self):
        """Initialize Windows hardware adapter."""
        self.adapters: Dict[str, WindowsAdapter] = {}
        self.serial_ports: Dict[str, serial.Serial] = {}
        
    def detect_adapters(self) -> List[WindowsAdapter]:
        """
        Detect all connected Windows-compatible adapters.
        
        Returns:
            List of detected adapters
        """
        detected = []
        
        # Detect serial devices (Arduino, etc.)
        detected.extend(self._detect_serial_devices())
        
        # Detect USB GPIO adapters
        if USB_AVAILABLE:
            detected.extend(self._detect_usb_gpio())
        
        return detected
    
    def _detect_serial_devices(self) -> List[WindowsAdapter]:
        """Detect serial devices (Arduino, etc.)."""
        adapters = []
        
        try:
            ports = serial.tools.list_ports.comports()
            for port in ports:
                # Check if it's an Arduino
                if self._is_arduino(port):
                    adapter = WindowsAdapter(
                        adapter_type=WindowsAdapterType.ARDUINO_SERIAL,
                        port=port.device,
                        vid=port.vid,
                        pid=port.pid,
                        name=f"Arduino ({port.description})",
                    )
                    adapters.append(adapter)
                    LOGGER.info(f"Detected Arduino on {port.device}")
                
                # Check if it's CH340 (GPIO adapter)
                elif port.vid and port.pid and (port.vid, port.pid) in self.CH340_VID_PIDS:
                    adapter = WindowsAdapter(
                        adapter_type=WindowsAdapterType.USB_GPIO_CH340,
                        port=port.device,
                        vid=port.vid,
                        pid=port.pid,
                        name=f"CH340 GPIO ({port.description})",
                    )
                    adapters.append(adapter)
                    LOGGER.info(f"Detected CH340 GPIO adapter on {port.device}")
        except Exception as e:
            LOGGER.error(f"Error detecting serial devices: {e}")
        
        return adapters
    
    def _is_arduino(self, port) -> bool:
        """Check if serial port is an Arduino."""
        if not port.vid or not port.pid:
            return False
        
        # Check VID/PID
        if (port.vid, port.pid) in self.ARDUINO_VID_PIDS:
            return True
        
        # Check description
        desc_lower = (port.description or "").lower()
        if "arduino" in desc_lower:
            return True
        
        return False
    
    def _detect_usb_gpio(self) -> List[WindowsAdapter]:
        """Detect USB GPIO adapters."""
        adapters = []
        
        if not USB_AVAILABLE:
            return adapters
        
        try:
            # Detect FTDI devices
            if FTDI_AVAILABLE:
                adapters.extend(self._detect_ftdi_devices())
            else:
                # Fallback: detect via USB IDs
                devices = usb.core.find(find_all=True)
                for device in devices:
                    if (device.idVendor, device.idProduct) in self.FTDI_VID_PIDS:
                        adapter = WindowsAdapter(
                            adapter_type=WindowsAdapterType.USB_GPIO_FTDI,
                            vid=device.idVendor,
                            pid=device.idProduct,
                            name=f"FTDI GPIO (VID:{device.idVendor:04X} PID:{device.idProduct:04X})",
                        )
                        adapters.append(adapter)
        except Exception as e:
            LOGGER.error(f"Error detecting USB GPIO adapters: {e}")
        
        return adapters
    
    def _detect_ftdi_devices(self) -> List[WindowsAdapter]:
        """Detect FTDI devices using libftdi."""
        adapters = []
        try:
            # This would use ftdi library if available
            # For now, return empty - can be implemented with ftdi library
            pass
        except Exception as e:
            LOGGER.error(f"Error detecting FTDI devices: {e}")
        return adapters
    
    def connect_arduino(self, port: str, baudrate: int = 115200) -> Optional[serial.Serial]:
        """
        Connect to Arduino via serial.
        
        Args:
            port: COM port (e.g., "COM3")
            baudrate: Serial baud rate (default 115200)
            
        Returns:
            Serial connection object or None if failed
        """
        try:
            ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=1.0,
                write_timeout=1.0,
            )
            self.serial_ports[port] = ser
            LOGGER.info(f"Connected to Arduino on {port}")
            return ser
        except Exception as e:
            LOGGER.error(f"Failed to connect to Arduino on {port}: {e}")
            return None
    
    def read_arduino_pin(self, port: str, pin: int) -> Optional[bool]:
        """
        Read digital pin from Arduino.
        
        Args:
            port: COM port
            pin: Pin number
            
        Returns:
            Pin state (True/False) or None if error
        """
        if port not in self.serial_ports:
            return None
        
        try:
            ser = self.serial_ports[port]
            # Send command to read pin (Arduino firmware specific)
            command = f"READ:{pin}\n"
            ser.write(command.encode())
            
            # Read response
            response = ser.readline().decode().strip()
            if response.startswith("PIN:"):
                value = response.split(":")[1]
                return value == "1"
        except Exception as e:
            LOGGER.error(f"Error reading Arduino pin {pin}: {e}")
        
        return None
    
    def write_arduino_pin(self, port: str, pin: int, value: bool) -> bool:
        """
        Write digital pin on Arduino.
        
        Args:
            port: COM port
            pin: Pin number
            value: Pin state (True/False)
            
        Returns:
            True if successful
        """
        if port not in self.serial_ports:
            return False
        
        try:
            ser = self.serial_ports[port]
            command = f"WRITE:{pin}:{1 if value else 0}\n"
            ser.write(command.encode())
            return True
        except Exception as e:
            LOGGER.error(f"Error writing Arduino pin {pin}: {e}")
            return False
    
    def read_arduino_analog(self, port: str, pin: int) -> Optional[float]:
        """
        Read analog pin from Arduino.
        
        Args:
            port: COM port
            pin: Analog pin number (A0-A5)
            
        Returns:
            Analog value (0-1023 for 10-bit, or voltage) or None if error
        """
        if port not in self.serial_ports:
            return None
        
        try:
            ser = self.serial_ports[port]
            command = f"ANALOG:{pin}\n"
            ser.write(command.encode())
            
            response = ser.readline().decode().strip()
            if response.startswith("ANALOG:"):
                value = float(response.split(":")[1])
                return value
        except Exception as e:
            LOGGER.error(f"Error reading Arduino analog pin {pin}: {e}")
        
        return None
    
    def disconnect(self, port: str) -> None:
        """Disconnect from adapter."""
        if port in self.serial_ports:
            try:
                self.serial_ports[port].close()
                del self.serial_ports[port]
                LOGGER.info(f"Disconnected from {port}")
            except Exception as e:
                LOGGER.error(f"Error disconnecting from {port}: {e}")
    
    def disconnect_all(self) -> None:
        """Disconnect from all adapters."""
        for port in list(self.serial_ports.keys()):
            self.disconnect(port)


__all__ = ["WindowsHardwareAdapter", "WindowsAdapter", "WindowsAdapterType"]











