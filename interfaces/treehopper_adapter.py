"""
Treehopper USB Interface Adapter

Provides interface to Treehopper USB device for GPIO, ADC, PWM, I2C, SPI, UART.
"""

from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional, Tuple, Any

LOGGER = logging.getLogger(__name__)

# Try to import USB HID libraries
try:
    import hid
    HID_AVAILABLE = True
except ImportError:
    HID_AVAILABLE = False
    hid = None  # type: ignore
    LOGGER.warning("hid library not available - Treehopper support limited")

# Treehopper USB HID Vendor/Product IDs
# Note: These are placeholder values - need to get actual Treehopper VID/PID
TREEHOPPER_VID = 0x1D50  # Placeholder - actual Treehopper VID
TREEHOPPER_PID = 0x6080  # Placeholder - actual Treehopper PID


class TreehopperAdapter:
    """
    Treehopper USB interface adapter.
    
    Provides:
    - Digital I/O (20 pins)
    - Analog input (ADC)
    - PWM output
    - SPI communication
    - I2C communication
    - UART communication
    """
    
    # Treehopper capabilities
    GPIO_PINS = 20
    ADC_CHANNELS = 8  # Approximate - depends on Treehopper model
    PWM_CHANNELS = 8  # Approximate
    I2C_BUSES = 1
    SPI_BUSES = 1
    UART_PORTS = 1
    
    def __init__(self) -> None:
        """Initialize Treehopper adapter."""
        self.device: Optional[Any] = None
        self.connected = False
        self.pin_configs: Dict[int, str] = {}  # pin -> mode (input/output/analog/pwm)
        self.i2c_devices: Dict[int, Any] = {}  # address -> device handle
        self.spi_devices: Dict[int, Any] = {}  # cs -> device handle
        
        # Try to detect and connect
        self._detect_and_connect()
    
    def _detect_and_connect(self) -> bool:
        """
        Detect and connect to Treehopper USB device.
        
        Returns:
            True if connected successfully
        """
        if not HID_AVAILABLE:
            LOGGER.warning("HID library not available - Treehopper detection disabled")
            return False
        
        try:
            # Enumerate USB HID devices
            devices = hid.enumerate()
            
            for device_info in devices:
                vid = device_info.get('vendor_id', 0)
                pid = device_info.get('product_id', 0)
                
                # Check if it's a Treehopper (using placeholder VID/PID)
                # In real implementation, use actual Treehopper VID/PID
                if vid == TREEHOPPER_VID and pid == TREEHOPPER_PID:
                    try:
                        self.device = hid.Device(vid, pid)
                        self.connected = True
                        LOGGER.info("Treehopper detected and connected (VID: 0x%04X, PID: 0x%04X)", vid, pid)
                        return True
                    except Exception as e:
                        LOGGER.error("Failed to open Treehopper device: %s", e)
                        continue
                
                # Also check by product name (fallback)
                product_name = device_info.get('product_string', '').lower()
                if 'treehopper' in product_name:
                    try:
                        self.device = hid.Device(vid, pid)
                        self.connected = True
                        LOGGER.info("Treehopper detected by name: %s", product_name)
                        return True
                    except Exception as e:
                        LOGGER.error("Failed to open Treehopper device: %s", e)
                        continue
            
            LOGGER.debug("Treehopper not found in USB devices")
            return False
            
        except Exception as e:
            LOGGER.error("Error detecting Treehopper: %s", e)
            return False
    
    def is_connected(self) -> bool:
        """Check if Treehopper is connected."""
        if not self.connected or not self.device:
            return False
        
        # Try to verify connection
        try:
            # Would send a ping/status command here
            # For now, just check if device exists
            return True
        except Exception:
            self.connected = False
            return False
    
    def configure_pin(self, pin: int, mode: str) -> bool:
        """
        Configure pin as input/output/analog/PWM.
        
        Args:
            pin: Pin number (0-19)
            mode: Mode ('input', 'output', 'analog', 'pwm')
        
        Returns:
            True if configured successfully
        """
        if not self.is_connected():
            LOGGER.warning("Treehopper not connected - cannot configure pin")
            return False
        
        if pin < 0 or pin >= self.GPIO_PINS:
            LOGGER.error("Invalid pin number: %d (must be 0-%d)", pin, self.GPIO_PINS - 1)
            return False
        
        if mode not in ['input', 'output', 'analog', 'pwm']:
            LOGGER.error("Invalid mode: %s", mode)
            return False
        
        try:
            # In real implementation, send USB HID command to configure pin
            # For now, just store configuration
            self.pin_configs[pin] = mode
            LOGGER.info("Configured Treehopper pin %d as %s", pin, mode)
            return True
        except Exception as e:
            LOGGER.error("Failed to configure pin %d: %s", pin, e)
            return False
    
    def read_digital(self, pin: int) -> Optional[bool]:
        """
        Read digital pin.
        
        Args:
            pin: Pin number (0-19)
        
        Returns:
            Pin state (True/False) or None if error
        """
        if not self.is_connected():
            return None
        
        if pin not in self.pin_configs or self.pin_configs[pin] != 'input':
            LOGGER.warning("Pin %d not configured as input", pin)
            return None
        
        try:
            # In real implementation, send USB HID command to read pin
            # For now, return simulated value
            # TODO: Implement actual USB HID communication
            return False
        except Exception as e:
            LOGGER.error("Failed to read digital pin %d: %s", pin, e)
            return None
    
    def write_digital(self, pin: int, value: bool) -> bool:
        """
        Write digital pin.
        
        Args:
            pin: Pin number (0-19)
            value: Value to write (True/False)
        
        Returns:
            True if written successfully
        """
        if not self.is_connected():
            return False
        
        if pin not in self.pin_configs or self.pin_configs[pin] != 'output':
            LOGGER.warning("Pin %d not configured as output", pin)
            return False
        
        try:
            # In real implementation, send USB HID command to write pin
            # TODO: Implement actual USB HID communication
            LOGGER.debug("Writing pin %d = %s", pin, value)
            return True
        except Exception as e:
            LOGGER.error("Failed to write digital pin %d: %s", pin, e)
            return False
    
    def read_analog(self, pin: int) -> Optional[float]:
        """
        Read analog pin (0-3.3V).
        
        Args:
            pin: Pin number (0-7 for ADC channels)
        
        Returns:
            Voltage in volts (0-3.3) or None if error
        """
        if not self.is_connected():
            return None
        
        if pin < 0 or pin >= self.ADC_CHANNELS:
            LOGGER.error("Invalid ADC channel: %d (must be 0-%d)", pin, self.ADC_CHANNELS - 1)
            return None
        
        try:
            # In real implementation, send USB HID command to read ADC
            # For now, return simulated value
            # TODO: Implement actual USB HID communication
            return 0.0
        except Exception as e:
            LOGGER.error("Failed to read analog pin %d: %s", pin, e)
            return None
    
    def write_pwm(self, pin: int, duty_cycle: float) -> bool:
        """
        Write PWM signal.
        
        Args:
            pin: Pin number (0-7 for PWM channels)
            duty_cycle: Duty cycle (0.0-1.0)
        
        Returns:
            True if written successfully
        """
        if not self.is_connected():
            return False
        
        if pin < 0 or pin >= self.PWM_CHANNELS:
            LOGGER.error("Invalid PWM channel: %d (must be 0-%d)", pin, self.PWM_CHANNELS - 1)
            return False
        
        if duty_cycle < 0.0 or duty_cycle > 1.0:
            LOGGER.error("Invalid duty cycle: %.2f (must be 0.0-1.0)", duty_cycle)
            return False
        
        try:
            # In real implementation, send USB HID command to set PWM
            # TODO: Implement actual USB HID communication
            LOGGER.debug("Setting PWM pin %d to %.2f%%", pin, duty_cycle * 100)
            return True
        except Exception as e:
            LOGGER.error("Failed to write PWM pin %d: %s", pin, e)
            return False
    
    def i2c_scan(self) -> List[int]:
        """
        Scan I2C bus for devices.
        
        Returns:
            List of I2C addresses found
        """
        if not self.is_connected():
            return []
        
        try:
            # In real implementation, scan I2C bus via Treehopper
            # TODO: Implement actual I2C scan
            return []
        except Exception as e:
            LOGGER.error("Failed to scan I2C bus: %s", e)
            return []
    
    def i2c_read(self, address: int, register: int, length: int = 1) -> Optional[bytes]:
        """
        Read from I2C device.
        
        Args:
            address: I2C device address
            register: Register address
            length: Number of bytes to read
        
        Returns:
            Data bytes or None if error
        """
        if not self.is_connected():
            return None
        
        try:
            # In real implementation, send I2C read command via Treehopper
            # TODO: Implement actual I2C communication
            return b'\x00' * length
        except Exception as e:
            LOGGER.error("Failed to read I2C address 0x%02X: %s", address, e)
            return None
    
    def i2c_write(self, address: int, register: int, data: bytes) -> bool:
        """
        Write to I2C device.
        
        Args:
            address: I2C device address
            register: Register address
            data: Data bytes to write
        
        Returns:
            True if written successfully
        """
        if not self.is_connected():
            return False
        
        try:
            # In real implementation, send I2C write command via Treehopper
            # TODO: Implement actual I2C communication
            return True
        except Exception as e:
            LOGGER.error("Failed to write I2C address 0x%02X: %s", address, e)
            return False
    
    def spi_transfer(self, data: bytes, cs: int = 0) -> Optional[bytes]:
        """
        SPI data transfer.
        
        Args:
            data: Data to send
            cs: Chip select pin (0-7)
        
        Returns:
            Received data or None if error
        """
        if not self.is_connected():
            return None
        
        try:
            # In real implementation, send SPI transfer command via Treehopper
            # TODO: Implement actual SPI communication
            return b'\x00' * len(data)
        except Exception as e:
            LOGGER.error("Failed SPI transfer: %s", e)
            return None
    
    def disconnect(self) -> None:
        """Disconnect from Treehopper."""
        if self.device:
            try:
                self.device.close()
            except Exception:
                pass
            self.device = None
        self.connected = False
        LOGGER.info("Treehopper disconnected")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get Treehopper status.
        
        Returns:
            Dictionary with status information
        """
        return {
            "connected": self.is_connected(),
            "gpio_pins": self.GPIO_PINS,
            "adc_channels": self.ADC_CHANNELS,
            "pwm_channels": self.PWM_CHANNELS,
            "configured_pins": len(self.pin_configs),
            "i2c_devices": len(self.i2c_devices),
            "spi_devices": len(self.spi_devices),
        }


# Global Treehopper instance
_treehopper_adapter: Optional[TreehopperAdapter] = None


def get_treehopper_adapter() -> Optional[TreehopperAdapter]:
    """Get or create Treehopper adapter instance."""
    global _treehopper_adapter
    if _treehopper_adapter is None:
        _treehopper_adapter = TreehopperAdapter()
    return _treehopper_adapter if _treehopper_adapter.is_connected() else None


__all__ = [
    "TreehopperAdapter",
    "get_treehopper_adapter",
]









