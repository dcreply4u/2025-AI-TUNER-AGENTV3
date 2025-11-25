"""
Serial Adapter Detection and Support

Auto-detects and supports various serial adapters:
- USB-to-Serial (FTDI, CH340, CP210x, PL2303, etc.)
- Bluetooth Serial
- WiFi Serial
- RS232/RS485 adapters
- Multi-port serial adapters
"""

from __future__ import annotations

import logging
import serial
import serial.tools.list_ports
from typing import Dict, List, Optional

from services.adapter_database import (
    AdapterCapabilities,
    AdapterConfig,
    AdapterType,
    ConnectionType,
    get_adapter_database,
)

LOGGER = logging.getLogger(__name__)


# Known serial adapter VID:PID mappings
SERIAL_ADAPTERS = {
    # FTDI
    ("0403", "6001"): ("FT232", "FTDI", ConnectionType.USB),
    ("0403", "6010"): ("FT2232", "FTDI", ConnectionType.USB),
    ("0403", "6011"): ("FT4232", "FTDI", ConnectionType.USB),
    ("0403", "6014"): ("FT232H", "FTDI", ConnectionType.USB),
    ("0403", "6015"): ("FT231X", "FTDI", ConnectionType.USB),
    
    # CH340/CH341 (WCH)
    ("1a86", "7523"): ("CH340", "WCH", ConnectionType.USB),
    ("1a86", "5523"): ("CH341", "WCH", ConnectionType.USB),
    
    # CP210x (Silicon Labs)
    ("10c4", "ea60"): ("CP2102", "Silicon Labs", ConnectionType.USB),
    ("10c4", "ea61"): ("CP2103", "Silicon Labs", ConnectionType.USB),
    ("10c4", "ea70"): ("CP2104", "Silicon Labs", ConnectionType.USB),
    ("10c4", "ea71"): ("CP2105", "Silicon Labs", ConnectionType.USB),
    
    # PL2303 (Prolific)
    ("067b", "2303"): ("PL2303", "Prolific", ConnectionType.USB),
    ("067b", "23a3"): ("PL2303", "Prolific", ConnectionType.USB),
    
    # Arduino
    ("2341", "0036"): ("Arduino Uno", "Arduino", ConnectionType.USB),
    ("2341", "0043"): ("Arduino Mega", "Arduino", ConnectionType.USB),
    
    # ESP32/ESP8266
    ("10c4", "ea60"): ("ESP32", "Espressif", ConnectionType.USB),
    ("1a86", "7523"): ("ESP8266", "Espressif", ConnectionType.USB),
}


class SerialAdapterDetector:
    """Serial adapter auto-detection system."""
    
    def __init__(self) -> None:
        """Initialize serial adapter detector."""
        self.detected_adapters: Dict[str, AdapterConfig] = {}
        self.db = get_adapter_database()
    
    def detect_all(self) -> List[AdapterConfig]:
        """
        Detect all available serial adapters.
        
        Returns:
            List of detected adapter configurations
        """
        adapters = []
        
        # Detect USB serial adapters
        adapters.extend(self._detect_usb_serial())
        
        # Detect Bluetooth serial adapters
        adapters.extend(self._detect_bluetooth_serial())
        
        # Detect WiFi serial adapters
        adapters.extend(self._detect_wifi_serial())
        
        # Load from database
        adapters.extend(self._load_known_adapters())
        
        # Store detected adapters
        for adapter in adapters:
            self.detected_adapters[adapter.name] = adapter
            self.db.add_adapter(adapter)
        
        return adapters
    
    def _detect_usb_serial(self) -> List[AdapterConfig]:
        """Detect USB serial adapters."""
        adapters = []
        
        try:
            ports = serial.tools.list_ports.comports()
            
            for port in ports:
                # Skip if already identified as OBD2
                if 'obd' in port.description.lower():
                    continue
                
                # Check VID:PID
                vid = f"{port.vid:04x}" if port.vid else None
                pid = f"{port.pid:04x}" if port.pid else None
                
                if vid and pid and (vid, pid) in SERIAL_ADAPTERS:
                    model, vendor, conn_type = SERIAL_ADAPTERS[(vid, pid)]
                    
                    # Determine capabilities based on model
                    capabilities = self._get_capabilities_for_model(model)
                    
                    adapters.append(AdapterConfig(
                        name=f"{model}_{port.device}",
                        adapter_type=AdapterType.SERIAL,
                        connection_type=conn_type,
                        vendor=vendor,
                        model=model,
                        device_path=port.device,
                        serial_number=port.serial_number,
                        capabilities=capabilities,
                        driver=self._get_driver_for_model(model),
                        metadata={
                            "vid": vid,
                            "pid": pid,
                            "description": port.description,
                            "manufacturer": port.manufacturer,
                        },
                    ))
                
                # Generic USB serial port
                elif port.vid and port.pid:
                    adapters.append(AdapterConfig(
                        name=f"USB_Serial_{port.device}",
                        adapter_type=AdapterType.SERIAL,
                        connection_type=ConnectionType.USB,
                        vendor=port.manufacturer or "Unknown",
                        model=port.description or "USB Serial",
                        device_path=port.device,
                        serial_number=port.serial_number,
                        capabilities=AdapterCapabilities(
                            max_baud_rate=115200,
                            supports_uart=True,
                        ),
                        driver="generic_serial",
                        metadata={
                            "description": port.description,
                            "manufacturer": port.manufacturer,
                        },
                    ))
        except Exception as e:
            LOGGER.warning("Failed to detect USB serial adapters: %s", e)
        
        return adapters
    
    def _detect_bluetooth_serial(self) -> List[AdapterConfig]:
        """Detect Bluetooth serial adapters."""
        adapters = []
        
        try:
            import subprocess
            
            # Check for Bluetooth serial devices
            result = subprocess.run(
                ['bluetoothctl', 'devices'],
                capture_output=True,
                text=True,
                timeout=5,
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'serial' in line.lower() or 'sp' in line.lower():
                        # Extract device MAC and name
                        import re
                        match = re.search(r'([0-9A-F:]{17})\s+(.+)', line)
                        if match:
                            mac = match.group(1)
                            name = match.group(2)
                            
                            adapters.append(AdapterConfig(
                                name=f"BT_Serial_{mac.replace(':', '_')}",
                                adapter_type=AdapterType.SERIAL,
                                connection_type=ConnectionType.BLUETOOTH,
                                vendor="Unknown",
                                model="Bluetooth Serial",
                                device_path=mac,
                                capabilities=AdapterCapabilities(
                                    max_baud_rate=115200,
                                    supports_uart=True,
                                ),
                                driver="bluetooth_serial",
                                metadata={
                                    "bluetooth_mac": mac,
                                    "device_name": name,
                                },
                            ))
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        except Exception as e:
            LOGGER.warning("Failed to detect Bluetooth serial adapters: %s", e)
        
        return adapters
    
    def _detect_wifi_serial(self) -> List[AdapterConfig]:
        """Detect WiFi serial adapters."""
        adapters = []
        
        # WiFi serial adapters (like ESP8266/ESP32 in AP mode)
        # Typically appear as network devices with specific SSIDs
        try:
            import subprocess
            
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'SSID', 'device', 'wifi', 'list'],
                capture_output=True,
                text=True,
                timeout=5,
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    ssid = line.strip()
                    if self._is_serial_wifi_ssid(ssid):
                        adapters.append(AdapterConfig(
                            name=f"WiFi_Serial_{ssid}",
                            adapter_type=AdapterType.SERIAL,
                            connection_type=ConnectionType.WIFI,
                            vendor="Unknown",
                            model="WiFi Serial",
                            device_path=ssid,
                            capabilities=AdapterCapabilities(
                                max_baud_rate=115200,
                                supports_uart=True,
                            ),
                            driver="wifi_serial",
                            metadata={"ssid": ssid},
                        ))
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        except Exception as e:
            LOGGER.warning("Failed to detect WiFi serial adapters: %s", e)
        
        return adapters
    
    def _get_capabilities_for_model(self, model: str) -> AdapterCapabilities:
        """Get capabilities for specific adapter model."""
        capabilities_map = {
            "FT232H": AdapterCapabilities(
                max_baud_rate=12000000,
                supports_uart=True,
                supports_i2c=True,
                supports_spi=True,
                voltage_levels=["3.3V", "5V"],
            ),
            "FT2232": AdapterCapabilities(
                max_baud_rate=12000000,
                supports_uart=True,
                supports_i2c=True,
                supports_spi=True,
                voltage_levels=["3.3V", "5V"],
            ),
            "CP2102": AdapterCapabilities(
                max_baud_rate=921600,
                supports_uart=True,
                voltage_levels=["3.3V"],
            ),
            "CP2103": AdapterCapabilities(
                max_baud_rate=921600,
                supports_uart=True,
                voltage_levels=["3.3V"],
            ),
            "CH340": AdapterCapabilities(
                max_baud_rate=2000000,
                supports_uart=True,
                voltage_levels=["3.3V", "5V"],
            ),
            "PL2303": AdapterCapabilities(
                max_baud_rate=115200,
                supports_uart=True,
                voltage_levels=["3.3V", "5V"],
            ),
        }
        
        return capabilities_map.get(model, AdapterCapabilities(
            max_baud_rate=115200,
            supports_uart=True,
        ))
    
    def _get_driver_for_model(self, model: str) -> str:
        """Get driver name for model."""
        driver_map = {
            "FT232": "ftdi",
            "FT2232": "ftdi",
            "FT232H": "ftdi",
            "CH340": "ch340",
            "CH341": "ch341",
            "CP2102": "cp210x",
            "CP2103": "cp210x",
            "PL2303": "pl2303",
        }
        return driver_map.get(model, "generic_serial")
    
    def _is_serial_wifi_ssid(self, ssid: str) -> bool:
        """Check if SSID indicates serial WiFi adapter."""
        serial_ssid_patterns = ['esp', 'arduino', 'serial', 'uart']
        return any(pattern in ssid.lower() for pattern in serial_ssid_patterns)
    
    def _load_known_adapters(self) -> List[AdapterConfig]:
        """Load known adapters from database."""
        return self.db.list_adapters(adapter_type=AdapterType.SERIAL, enabled_only=True)
    
    def get_adapter(self, name: str) -> Optional[AdapterConfig]:
        """Get adapter by name."""
        if name in self.detected_adapters:
            return self.detected_adapters[name]
        return self.db.get_adapter(name)


__all__ = ["SerialAdapterDetector"]






