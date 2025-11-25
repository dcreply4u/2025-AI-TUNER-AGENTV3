"""
Unified I/O Manager

Manages I/O from multiple devices (reTerminal DM, Treehopper, etc.)
and presents a unified interface.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

LOGGER = logging.getLogger(__name__)

from interfaces.treehopper_adapter import TreehopperAdapter, get_treehopper_adapter
from core.hardware_platform import get_hardware_config, HardwareConfig

# Try to import GPIO libraries for reTerminal DM
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


class UnifiedIOManager:
    """
    Manages I/O from multiple devices (reTerminal DM, BeagleBone Black, Treehopper).
    
    Provides unified pin numbering:
    - Pins 0-39: reTerminal DM GPIO (40 pins)
    - Pins 0-64: BeagleBone Black GPIO (65 pins)
    - Pins 40-59: Treehopper GPIO (when used with reTerminal DM)
    - Pins 65-84: Treehopper GPIO (when used with BeagleBone Black)
    """
    
    # Pin mapping - reTerminal DM
    RETERMINAL_GPIO_START = 0
    RETERMINAL_GPIO_END = 39
    RETERMINAL_GPIO_COUNT = 40
    
    # Pin mapping - BeagleBone Black
    BEAGLEBONE_GPIO_START = 0
    BEAGLEBONE_GPIO_END = 64
    BEAGLEBONE_GPIO_COUNT = 65
    
    # Pin mapping - Treehopper (with reTerminal DM)
    TREEHOPPER_RETERMINAL_START = 40
    TREEHOPPER_RETERMINAL_END = 59
    TREEHOPPER_RETERMINAL_COUNT = 20
    
    # Pin mapping - Treehopper (with BeagleBone Black)
    TREEHOPPER_BEAGLEBONE_START = 65
    TREEHOPPER_BEAGLEBONE_END = 84
    TREEHOPPER_BEAGLEBONE_COUNT = 20
    
    # ADC channel mapping
    RETERMINAL_ADC_START = 0
    RETERMINAL_ADC_END = 6  # 7 channels (0-6)
    RETERMINAL_ADC_COUNT = 7
    
    BEAGLEBONE_ADC_START = 0
    BEAGLEBONE_ADC_END = 6  # 7 channels (0-6) - built-in
    BEAGLEBONE_ADC_COUNT = 7
    
    TREEHOPPER_ADC_START = 7
    TREEHOPPER_ADC_END = 14  # 8 channels (7-14)
    TREEHOPPER_ADC_COUNT = 8
    
    TOTAL_ADC_CHANNELS = 15
    
    def __init__(self) -> None:
        """Initialize unified I/O manager."""
        self.hardware_config: Optional[HardwareConfig] = None
        self.treehopper: Optional[TreehopperAdapter] = None
        
        # Device status
        self.reterminal_available = False
        self.beaglebone_available = False
        self.treehopper_available = False
        self.platform_type: str = "unknown"  # "reterminal", "beaglebone", "other"
        
        # Pin assignments
        self.pin_assignments: Dict[int, Dict[str, Any]] = {}  # pin -> {device, local_pin, mode}
        
        # Detect devices
        self._detect_devices()
    
    def _detect_devices(self) -> None:
        """Detect all available I/O devices."""
        # Detect base platform (reTerminal DM, BeagleBone Black, etc.)
        try:
            self.hardware_config = get_hardware_config()
            if self.hardware_config and self.hardware_config.gpio_available:
                platform_name = self.hardware_config.platform_name.lower()
                if "reterminal" in platform_name:
                    self.reterminal_available = True
                    self.platform_type = "reterminal"
                    LOGGER.info("reTerminal DM detected - GPIO available")
                elif "beaglebone" in platform_name:
                    self.beaglebone_available = True
                    self.platform_type = "beaglebone"
                    LOGGER.info("BeagleBone Black detected - GPIO and ADC available")
                elif platform.system() == "Windows":
                    # Windows platform - GPIO available via Treehopper
                    self.platform_type = "windows"
                    if self.hardware_config.gpio_available:
                        LOGGER.info("Windows detected - GPIO available via Treehopper")
                    else:
                        LOGGER.info("Windows detected - GPIO available when Treehopper is connected")
                else:
                    # Other platform (Pi, Jetson, etc.)
                    self.platform_type = "other"
                    LOGGER.info("%s detected - GPIO available", self.hardware_config.platform_name)
        except Exception as e:
            LOGGER.warning("Failed to detect base platform: %s", e)
        
        # Detect Treehopper
        try:
            self.treehopper = get_treehopper_adapter()
            if self.treehopper and self.treehopper.is_connected():
                self.treehopper_available = True
                LOGGER.info("Treehopper detected - additional I/O available")
        except Exception as e:
            LOGGER.warning("Failed to detect Treehopper: %s", e)
        
        # Log total capabilities
        total_gpio = self.get_total_gpio_pins()
        total_adc = self.get_total_adc_channels()
        LOGGER.info("Unified I/O Manager initialized: %d GPIO pins, %d ADC channels", total_gpio, total_adc)
    
    def get_total_gpio_pins(self) -> int:
        """Get total available GPIO pins."""
        total = 0
        if self.reterminal_available:
            total += self.RETERMINAL_GPIO_COUNT
        elif self.beaglebone_available:
            total += self.BEAGLEBONE_GPIO_COUNT
        
        if self.treehopper_available:
            if self.reterminal_available:
                total += self.TREEHOPPER_RETERMINAL_COUNT
            elif self.beaglebone_available:
                total += self.TREEHOPPER_BEAGLEBONE_COUNT
            else:
                # Treehopper alone (Windows, Pi without GPIO, etc.)
                total += self.TREEHOPPER_RETERMINAL_COUNT
        
        return total
    
    def get_total_adc_channels(self) -> int:
        """Get total available ADC channels."""
        total = 0
        if self.reterminal_available:
            total += self.RETERMINAL_ADC_COUNT
        elif self.beaglebone_available:
            total += self.BEAGLEBONE_ADC_COUNT
        
        if self.treehopper_available:
            total += self.TREEHOPPER_ADC_COUNT
        
        return total
    
    def _resolve_pin(self, pin: int) -> Tuple[Optional[str], Optional[int]]:
        """
        Resolve unified pin to device and local pin.
        
        Args:
            pin: Unified pin number
        
        Returns:
            Tuple of (device_name, local_pin) or (None, None) if invalid
        """
        # Determine pin ranges based on platform
        if self.reterminal_available:
            base_end = self.RETERMINAL_GPIO_END
            treehopper_start = self.TREEHOPPER_RETERMINAL_START
            treehopper_end = self.TREEHOPPER_RETERMINAL_END
            base_count = self.RETERMINAL_GPIO_COUNT
        elif self.beaglebone_available:
            base_end = self.BEAGLEBONE_GPIO_END
            treehopper_start = self.TREEHOPPER_BEAGLEBONE_START
            treehopper_end = self.TREEHOPPER_BEAGLEBONE_END
            base_count = self.BEAGLEBONE_GPIO_COUNT
        else:
            # Unknown platform or Treehopper only
            if self.treehopper_available:
                # Treehopper only - use reTerminal mapping
                if pin < 0 or pin >= self.TREEHOPPER_RETERMINAL_COUNT:
                    LOGGER.error("Invalid pin number: %d (must be 0-%d)", pin, self.TREEHOPPER_RETERMINAL_COUNT - 1)
                    return None, None
                return "treehopper", pin
            else:
                LOGGER.error("No I/O devices available")
                return None, None
        
        # Check if pin is in base platform range
        if pin <= base_end:
            if self.reterminal_available:
                return "reterminal", pin - self.RETERMINAL_GPIO_START
            elif self.beaglebone_available:
                return "beaglebone", pin - self.BEAGLEBONE_GPIO_START
            else:
                LOGGER.error("Base platform not available for pin %d", pin)
                return None, None
        
        # Check if pin is in Treehopper range
        elif treehopper_start <= pin <= treehopper_end:
            if not self.treehopper_available:
                LOGGER.error("Treehopper not available for pin %d", pin)
                return None, None
            return "treehopper", pin - treehopper_start
        
        else:
            max_pin = treehopper_end if self.treehopper_available else base_end
            LOGGER.error("Invalid pin number: %d (must be 0-%d)", pin, max_pin)
            return None, None
    
    def _resolve_adc_channel(self, channel: int) -> Tuple[Optional[str], Optional[int]]:
        """
        Resolve unified ADC channel to device and local channel.
        
        Args:
            channel: Unified ADC channel (0-14)
        
        Returns:
            Tuple of (device_name, local_channel) or (None, None) if invalid
        """
        if channel < 0 or channel > self.TREEHOPPER_ADC_END:
            LOGGER.error("Invalid ADC channel: %d (must be 0-%d)", channel, self.TREEHOPPER_ADC_END)
            return None, None
        
        # Determine base platform ADC range
        if self.reterminal_available:
            base_end = self.RETERMINAL_ADC_END
            base_start = self.RETERMINAL_ADC_START
        elif self.beaglebone_available:
            base_end = self.BEAGLEBONE_ADC_END
            base_start = self.BEAGLEBONE_ADC_START
        else:
            # Treehopper only
            if self.treehopper_available:
                if channel < self.TREEHOPPER_ADC_START:
                    LOGGER.error("Invalid ADC channel: %d (Treehopper channels start at %d)", 
                               channel, self.TREEHOPPER_ADC_START)
                    return None, None
                return "treehopper", channel - self.TREEHOPPER_ADC_START
            else:
                LOGGER.error("No ADC devices available")
                return None, None
        
        if channel <= base_end:
            # Base platform ADC
            if self.reterminal_available:
                return "reterminal", channel - self.RETERMINAL_ADC_START
            elif self.beaglebone_available:
                return "beaglebone", channel - self.BEAGLEBONE_ADC_START
            else:
                LOGGER.error("Base platform not available for ADC channel %d", channel)
                return None, None
        else:
            # Treehopper ADC
            if not self.treehopper_available:
                LOGGER.error("Treehopper not available for ADC channel %d", channel)
                return None, None
            return "treehopper", channel - self.TREEHOPPER_ADC_START
    
    def configure_gpio(self, pin: int, mode: str) -> bool:
        """
        Configure GPIO pin as input/output.
        
        Args:
            pin: Unified pin number (0-59)
            mode: Mode ('input' or 'output')
        
        Returns:
            True if configured successfully
        """
        device, local_pin = self._resolve_pin(pin)
        if not device or local_pin is None:
            return False
        
        try:
            if device == "reterminal":
                if not RPI_GPIO_AVAILABLE:
                    LOGGER.error("GPIO library not available for reTerminal DM")
                    return False
                
                GPIO.setmode(GPIO.BCM)
                if mode == "input":
                    GPIO.setup(local_pin, GPIO.IN)
                elif mode == "output":
                    GPIO.setup(local_pin, GPIO.OUT)
                else:
                    LOGGER.error("Invalid mode for reTerminal DM: %s", mode)
                    return False
                
                self.pin_assignments[pin] = {
                    "device": device,
                    "local_pin": local_pin,
                    "mode": mode,
                }
                LOGGER.info("Configured reTerminal DM pin %d (unified %d) as %s", local_pin, pin, mode)
                return True
            
            elif device == "beaglebone":
                # BeagleBone Black uses sysfs GPIO
                try:
                    gpio_path = Path(f"/sys/class/gpio/gpio{local_pin}")
                    if not gpio_path.exists():
                        # Export GPIO pin
                        Path("/sys/class/gpio/export").write_text(str(local_pin))
                        time.sleep(0.1)  # Wait for export
                    
                    # Set direction
                    direction_path = gpio_path / "direction"
                    direction_path.write_text("in" if mode == "input" else "out")
                    
                    self.pin_assignments[pin] = {
                        "device": device,
                        "local_pin": local_pin,
                        "mode": mode,
                    }
                    LOGGER.info("Configured BeagleBone Black pin %d (unified %d) as %s", local_pin, pin, mode)
                    return True
                except Exception as e:
                    LOGGER.error("Failed to configure BeagleBone Black pin %d: %s", local_pin, e)
                    return False
            
            elif device == "treehopper":
                if not self.treehopper:
                    return False
                
                # Treehopper uses different mode names
                treehopper_mode = "input" if mode == "input" else "output"
                success = self.treehopper.configure_pin(local_pin, treehopper_mode)
                
                if success:
                    self.pin_assignments[pin] = {
                        "device": device,
                        "local_pin": local_pin,
                        "mode": mode,
                    }
                    LOGGER.info("Configured Treehopper pin %d (unified %d) as %s", local_pin, pin, mode)
                
                return success
            
            return False
            
        except Exception as e:
            LOGGER.error("Failed to configure pin %d: %s", pin, e)
            return False
    
    def read_gpio(self, pin: int) -> Optional[bool]:
        """
        Read GPIO pin.
        
        Args:
            pin: Unified pin number (0-59)
        
        Returns:
            Pin state (True/False) or None if error
        """
        device, local_pin = self._resolve_pin(pin)
        if not device or local_pin is None:
            return None
        
        try:
            if device == "reterminal":
                if not RPI_GPIO_AVAILABLE:
                    return None
                value = GPIO.input(local_pin)
                return value == GPIO.HIGH
            
            elif device == "beaglebone":
                # BeagleBone Black sysfs GPIO read
                try:
                    gpio_path = Path(f"/sys/class/gpio/gpio{local_pin}")
                    value_path = gpio_path / "value"
                    value = int(value_path.read_text().strip())
                    return value == 1
                except Exception as e:
                    LOGGER.error("Failed to read BeagleBone Black pin %d: %s", local_pin, e)
                    return None
            
            elif device == "treehopper":
                if not self.treehopper:
                    return None
                return self.treehopper.read_digital(local_pin)
            
            return None
            
        except Exception as e:
            LOGGER.error("Failed to read pin %d: %s", pin, e)
            return None
    
    def write_gpio(self, pin: int, value: bool) -> bool:
        """
        Write GPIO pin.
        
        Args:
            pin: Unified pin number (0-59)
            value: Value to write (True/False)
        
        Returns:
            True if written successfully
        """
        device, local_pin = self._resolve_pin(pin)
        if not device or local_pin is None:
            return False
        
        try:
            if device == "reterminal":
                if not RPI_GPIO_AVAILABLE:
                    return False
                GPIO.output(local_pin, GPIO.HIGH if value else GPIO.LOW)
                return True
            
            elif device == "beaglebone":
                # BeagleBone Black sysfs GPIO write
                try:
                    gpio_path = Path(f"/sys/class/gpio/gpio{local_pin}")
                    value_path = gpio_path / "value"
                    value_path.write_text("1" if value else "0")
                    return True
                except Exception as e:
                    LOGGER.error("Failed to write BeagleBone Black pin %d: %s", local_pin, e)
                    return False
            
            elif device == "treehopper":
                if not self.treehopper:
                    return False
                return self.treehopper.write_digital(local_pin, value)
            
            return False
            
        except Exception as e:
            LOGGER.error("Failed to write pin %d: %s", pin, e)
            return False
    
    def read_analog(self, channel: int) -> Optional[float]:
        """
        Read analog channel.
        
        Args:
            channel: Unified ADC channel (0-14)
        
        Returns:
            Voltage in volts or None if error
        """
        device, local_channel = self._resolve_adc_channel(channel)
        if not device or local_channel is None:
            return None
        
        try:
            if device == "reterminal":
                # reTerminal DM ADC would be via I2C ADC board (ADS1115, etc.)
                # This would need to be implemented via analog_sensor.py
                # For now, return None
                LOGGER.warning("reTerminal DM ADC reading not yet implemented via unified I/O")
                return None
            
            elif device == "beaglebone":
                # BeagleBone Black has built-in 12-bit ADC
                try:
                    # ADC channels are in /sys/bus/iio/devices/iio:device0/
                    adc_path = Path(f"/sys/bus/iio/devices/iio:device0/in_voltage{local_channel}_raw")
                    if adc_path.exists():
                        raw_value = int(adc_path.read_text().strip())
                        # Convert to voltage (0-1.8V reference, 12-bit = 4096 steps)
                        voltage = (raw_value / 4096.0) * 1.8
                        return voltage
                    else:
                        LOGGER.warning("BeagleBone Black ADC channel %d not available", local_channel)
                        return None
                except Exception as e:
                    LOGGER.error("Failed to read BeagleBone Black ADC channel %d: %s", local_channel, e)
                    return None
            
            elif device == "treehopper":
                if not self.treehopper:
                    return None
                return self.treehopper.read_analog(local_channel)
            
            return None
            
        except Exception as e:
            LOGGER.error("Failed to read ADC channel %d: %s", channel, e)
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get unified I/O manager status.
        
        Returns:
            Dictionary with status information
        """
        status = {
            "platform_type": self.platform_type,
            "reterminal_available": self.reterminal_available,
            "beaglebone_available": self.beaglebone_available,
            "treehopper_available": self.treehopper_available,
            "total_gpio_pins": self.get_total_gpio_pins(),
            "total_adc_channels": self.get_total_adc_channels(),
            "configured_pins": len(self.pin_assignments),
        }
        
        if self.treehopper:
            status["treehopper_status"] = self.treehopper.get_status()
        
        return status


# Global unified I/O manager instance
_unified_io_manager: Optional[UnifiedIOManager] = None


def get_unified_io_manager() -> UnifiedIOManager:
    """Get or create unified I/O manager instance."""
    global _unified_io_manager
    if _unified_io_manager is None:
        _unified_io_manager = UnifiedIOManager()
    return _unified_io_manager


__all__ = [
    "UnifiedIOManager",
    "get_unified_io_manager",
]

