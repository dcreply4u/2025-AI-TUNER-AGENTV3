"""
GPIO Adapter Detection and Support

Auto-detects and supports various GPIO adapters:
- reTerminal DM (built-in)
- Raspberry Pi GPIO
- BeagleBone Black GPIO
- MCP23017 (I2C GPIO expander)
- PCF8574 (I2C GPIO expander)
- FT232H (USB GPIO)
- CH341 (USB GPIO)
- Adafruit GPIO boards
- SparkFun GPIO boards
- Custom GPIO adapters
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from services.adapter_database import (
    AdapterCapabilities,
    AdapterConfig,
    AdapterType,
    ConnectionType,
    get_adapter_database,
)

LOGGER = logging.getLogger(__name__)


class GPIOAdapterDetector:
    """GPIO adapter auto-detection system."""
    
    def __init__(self) -> None:
        """Initialize GPIO adapter detector."""
        self.detected_adapters: Dict[str, AdapterConfig] = {}
        self.db = get_adapter_database()
    
    def detect_all(self) -> List[AdapterConfig]:
        """
        Detect all available GPIO adapters.
        
        Returns:
            List of detected adapter configurations
        """
        adapters = []
        
        # Detect built-in GPIO
        adapters.extend(self._detect_builtin_gpio())
        
        # Detect I2C GPIO expanders
        adapters.extend(self._detect_i2c_gpio())
        
        # Detect USB GPIO adapters
        adapters.extend(self._detect_usb_gpio())
        
        # Load from database
        adapters.extend(self._load_known_adapters())
        
        # Store detected adapters
        for adapter in adapters:
            self.detected_adapters[adapter.name] = adapter
            self.db.add_adapter(adapter)
        
        return adapters
    
    def _detect_builtin_gpio(self) -> List[AdapterConfig]:
        """Detect built-in GPIO (reTerminal DM, Raspberry Pi, BeagleBone)."""
        adapters = []
        
        # Check for reTerminal DM
        if self._is_reterminal_dm():
            adapters.append(AdapterConfig(
                name="reTerminal_DM_GPIO",
                adapter_type=AdapterType.GPIO,
                connection_type=ConnectionType.BUILTIN,
                vendor="Seeed Studio",
                model="reTerminal DM",
                capabilities=AdapterCapabilities(
                    max_gpio_pins=40,
                    max_adc_channels=0,  # Would need ADC board
                    max_pwm_channels=6,
                    supports_i2c=True,
                    supports_spi=True,
                    supports_uart=True,
                    voltage_levels=["3.3V"],
                ),
                driver="reterminal_gpio",
                metadata={"platform": "reterminal_dm"},
            ))
        
        # Check for Raspberry Pi
        elif self._is_raspberry_pi():
            model = self._get_raspberry_pi_model()
            adapters.append(AdapterConfig(
                name="Raspberry_Pi_GPIO",
                adapter_type=AdapterType.GPIO,
                connection_type=ConnectionType.BUILTIN,
                vendor="Raspberry Pi Foundation",
                model=model or "Raspberry Pi",
                capabilities=AdapterCapabilities(
                    max_gpio_pins=40 if "4" in (model or "") else 26,
                    max_adc_channels=0,  # Would need ADC HAT
                    max_pwm_channels=2,
                    supports_i2c=True,
                    supports_spi=True,
                    supports_uart=True,
                    voltage_levels=["3.3V"],
                ),
                driver="raspberry_pi_gpio",
                metadata={"platform": "raspberry_pi", "model": model},
            ))
        
        # Check for BeagleBone Black
        elif self._is_beaglebone_black():
            adapters.append(AdapterConfig(
                name="BeagleBone_Black_GPIO",
                adapter_type=AdapterType.GPIO,
                connection_type=ConnectionType.BUILTIN,
                vendor="BeagleBoard.org",
                model="BeagleBone Black",
                capabilities=AdapterCapabilities(
                    max_gpio_pins=65,
                    max_adc_channels=7,
                    max_pwm_channels=8,
                    supports_i2c=True,
                    supports_spi=True,
                    supports_uart=True,
                    supports_can=True,
                    voltage_levels=["3.3V"],
                ),
                driver="beaglebone_gpio",
                metadata={"platform": "beaglebone_black"},
            ))
        
        return adapters
    
    def _detect_i2c_gpio(self) -> List[AdapterConfig]:
        """Detect I2C GPIO expanders."""
        adapters = []
        
        try:
            # Try to scan I2C bus
            result = subprocess.run(
                ['i2cdetect', '-y', '1'],
                capture_output=True,
                text=True,
                timeout=2,
            )
            
            if result.returncode == 0:
                # MCP23017 (common address: 0x20-0x27)
                for addr in range(0x20, 0x28):
                    if hex(addr) in result.stdout:
                        adapters.append(AdapterConfig(
                            name=f"MCP23017_GPIO_{hex(addr)}",
                            adapter_type=AdapterType.GPIO,
                            connection_type=ConnectionType.I2C,
                            vendor="Microchip",
                            model="MCP23017",
                            device_path=f"i2c-1@{hex(addr)}",
                            capabilities=AdapterCapabilities(
                                max_gpio_pins=16,
                                voltage_levels=["3.3V", "5V"],
                            ),
                            driver="mcp23017",
                            metadata={"i2c_address": hex(addr)},
                        ))
                
                # PCF8574 (common address: 0x20-0x27)
                for addr in range(0x20, 0x28):
                    if hex(addr) in result.stdout:
                        adapters.append(AdapterConfig(
                            name=f"PCF8574_GPIO_{hex(addr)}",
                            adapter_type=AdapterType.GPIO,
                            connection_type=ConnectionType.I2C,
                            vendor="NXP",
                            model="PCF8574",
                            device_path=f"i2c-1@{hex(addr)}",
                            capabilities=AdapterCapabilities(
                                max_gpio_pins=8,
                                voltage_levels=["3.3V", "5V"],
                            ),
                            driver="pcf8574",
                            metadata={"i2c_address": hex(addr)},
                        ))
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return adapters
    
    def _detect_usb_gpio(self) -> List[AdapterConfig]:
        """Detect USB GPIO adapters."""
        adapters = []
        
        # Check for FT232H (FTDI)
        if self._check_usb_device("0403", "6014"):  # FT232H VID:PID
            adapters.append(AdapterConfig(
                name="FT232H_GPIO",
                adapter_type=AdapterType.GPIO,
                connection_type=ConnectionType.USB,
                vendor="FTDI",
                model="FT232H",
                capabilities=AdapterCapabilities(
                    max_gpio_pins=13,
                    max_pwm_channels=4,
                    supports_i2c=True,
                    supports_spi=True,
                    voltage_levels=["3.3V", "5V"],
                ),
                driver="ft232h",
            ))
        
        # Check for CH341 (WCH)
        if self._check_usb_device("1a86", "5523"):  # CH341 VID:PID
            adapters.append(AdapterConfig(
                name="CH341_GPIO",
                adapter_type=AdapterType.GPIO,
                connection_type=ConnectionType.USB,
                vendor="WCH",
                model="CH341",
                capabilities=AdapterCapabilities(
                    max_gpio_pins=8,
                    voltage_levels=["3.3V", "5V"],
                ),
                driver="ch341",
            ))
        
        # Check for Adafruit FT232H
        if self._check_usb_device("0403", "6014"):
            # Could be Adafruit board
            adapters.append(AdapterConfig(
                name="Adafruit_FT232H_GPIO",
                adapter_type=AdapterType.GPIO,
                connection_type=ConnectionType.USB,
                vendor="Adafruit",
                model="FT232H Breakout",
                capabilities=AdapterCapabilities(
                    max_gpio_pins=13,
                    max_pwm_channels=4,
                    supports_i2c=True,
                    supports_spi=True,
                    voltage_levels=["3.3V", "5V"],
                ),
                driver="adafruit_ft232h",
            ))
        
        return adapters
    
    def _is_reterminal_dm(self) -> bool:
        """Check if running on reTerminal DM."""
        try:
            if Path("/proc/device-tree/model").exists():
                model = Path("/proc/device-tree/model").read_text().lower()
                return "reterminal" in model or "seeed" in model
        except Exception:
            pass
        return False
    
    def _is_raspberry_pi(self) -> bool:
        """Check if running on Raspberry Pi."""
        try:
            if Path("/proc/device-tree/model").exists():
                model = Path("/proc/device-tree/model").read_text().lower()
                return "raspberry pi" in model
        except Exception:
            pass
        return False
    
    def _get_raspberry_pi_model(self) -> Optional[str]:
        """Get Raspberry Pi model."""
        try:
            if Path("/proc/device-tree/model").exists():
                return Path("/proc/device-tree/model").read_text().strip()
        except Exception:
            pass
        return None
    
    def _is_beaglebone_black(self) -> bool:
        """Check if running on BeagleBone Black."""
        try:
            if Path("/proc/device-tree/model").exists():
                model = Path("/proc/device-tree/model").read_text().lower()
                return "beaglebone" in model or "am335x" in model
        except Exception:
            pass
        return False
    
    def _check_usb_device(self, vid: str, pid: str) -> bool:
        """Check if USB device is connected."""
        try:
            if Path("/sys/bus/usb/devices").exists():
                for device_path in Path("/sys/bus/usb/devices").iterdir():
                    id_vendor = device_path / "idVendor"
                    id_product = device_path / "idProduct"
                    if id_vendor.exists() and id_product.exists():
                        if (id_vendor.read_text().strip() == vid and
                            id_product.read_text().strip() == pid):
                            return True
        except Exception:
            pass
        return False
    
    def _load_known_adapters(self) -> List[AdapterConfig]:
        """Load known adapters from database."""
        return self.db.list_adapters(adapter_type=AdapterType.GPIO, enabled_only=True)
    
    def get_adapter(self, name: str) -> Optional[AdapterConfig]:
        """Get adapter by name."""
        if name in self.detected_adapters:
            return self.detected_adapters[name]
        return self.db.get_adapter(name)


__all__ = ["GPIOAdapterDetector"]






