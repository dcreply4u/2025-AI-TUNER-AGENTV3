"""
OBD2 Adapter Detection and Support

Auto-detects and supports various OBD2 adapters:
- ELM327 (wired/wireless/Bluetooth)
- OBDLink (wired/wireless)
- Carista
- Veepeak
- BAFX Products
- OBD Solutions
- PLX Devices
- Kiwi
- And many more...
"""

from __future__ import annotations

import logging
import re
import serial
import serial.tools.list_ports
from typing import Dict, List, Optional, Tuple

from services.adapter_database import (
    AdapterCapabilities,
    AdapterConfig,
    AdapterType,
    ConnectionType,
    get_adapter_database,
)

LOGGER = logging.getLogger(__name__)


# Known OBD2 adapter VID:PID mappings
OBD2_ADAPTERS = {
    # ELM327 variants
    ("0403", "6001"): ("ELM327", "FTDI", ConnectionType.USB),
    ("1a86", "7523"): ("ELM327", "CH340", ConnectionType.USB),
    ("10c4", "ea60"): ("ELM327", "Silicon Labs", ConnectionType.USB),
    
    # OBDLink
    ("0403", "6001"): ("OBDLink", "ScanTool.net", ConnectionType.USB),
    ("1a86", "7523"): ("OBDLink", "ScanTool.net", ConnectionType.USB),
    
    # Carista
    ("0403", "6001"): ("Carista", "Carista", ConnectionType.USB),
    
    # Veepeak
    ("1a86", "7523"): ("Veepeak", "Veepeak", ConnectionType.USB),
    
    # BAFX Products
    ("0403", "6001"): ("BAFX", "BAFX Products", ConnectionType.USB),
    
    # PLX Devices
    ("0403", "6001"): ("PLX", "PLX Devices", ConnectionType.USB),
}


class OBD2AdapterDetector:
    """OBD2 adapter auto-detection system."""
    
    def __init__(self) -> None:
        """Initialize OBD2 adapter detector."""
        self.detected_adapters: Dict[str, AdapterConfig] = {}
        self.db = get_adapter_database()
    
    def detect_all(self) -> List[AdapterConfig]:
        """
        Detect all available OBD2 adapters.
        
        Returns:
            List of detected adapter configurations
        """
        adapters = []
        
        # Detect USB OBD2 adapters
        adapters.extend(self._detect_usb_obd2())
        
        # Detect Bluetooth OBD2 adapters
        adapters.extend(self._detect_bluetooth_obd2())
        
        # Detect WiFi OBD2 adapters
        adapters.extend(self._detect_wifi_obd2())
        
        # Detect serial OBD2 adapters
        adapters.extend(self._detect_serial_obd2())
        
        # Load from database
        adapters.extend(self._load_known_adapters())
        
        # Store detected adapters
        for adapter in adapters:
            self.detected_adapters[adapter.name] = adapter
            self.db.add_adapter(adapter)
        
        return adapters
    
    def _detect_usb_obd2(self) -> List[AdapterConfig]:
        """Detect USB OBD2 adapters."""
        adapters = []
        
        try:
            ports = serial.tools.list_ports.comports()
            
            for port in ports:
                # Check VID:PID
                vid = f"{port.vid:04x}" if port.vid else None
                pid = f"{port.pid:04x}" if port.pid else None
                
                if vid and pid and (vid, pid) in OBD2_ADAPTERS:
                    model, vendor, conn_type = OBD2_ADAPTERS[(vid, pid)]
                    
                    # Try to identify by description
                    description = port.description.lower()
                    if self._is_obd2_adapter(description):
                        adapters.append(AdapterConfig(
                            name=f"{model}_{port.device}",
                            adapter_type=AdapterType.OBD2,
                            connection_type=conn_type,
                            vendor=vendor,
                            model=model,
                            device_path=port.device,
                            serial_number=port.serial_number,
                            capabilities=AdapterCapabilities(
                                protocols=["OBD2", "CAN"],
                                max_baud_rate=115200,
                            ),
                            driver="elm327" if "elm" in model.lower() else "obd2",
                            metadata={
                                "vid": vid,
                                "pid": pid,
                                "description": port.description,
                                "manufacturer": port.manufacturer,
                            },
                        ))
                
                # Check by description/name
                elif self._is_obd2_adapter(port.description.lower()):
                    model = self._identify_model_from_description(port.description)
                    vendor = self._identify_vendor_from_description(port.description)
                    
                    adapters.append(AdapterConfig(
                        name=f"{model}_{port.device}",
                        adapter_type=AdapterType.OBD2,
                        connection_type=ConnectionType.USB,
                        vendor=vendor,
                        model=model,
                        device_path=port.device,
                        serial_number=port.serial_number,
                        capabilities=AdapterCapabilities(
                            protocols=["OBD2", "CAN"],
                            max_baud_rate=115200,
                        ),
                        driver="elm327",
                        metadata={
                            "description": port.description,
                            "manufacturer": port.manufacturer,
                        },
                    ))
        except Exception as e:
            LOGGER.warning("Failed to detect USB OBD2 adapters: %s", e)
        
        return adapters
    
    def _detect_bluetooth_obd2(self) -> List[AdapterConfig]:
        """Detect Bluetooth OBD2 adapters."""
        adapters = []
        
        try:
            # Try to use bluetoothctl or similar
            import subprocess
            
            # Check for common Bluetooth OBD2 device names
            result = subprocess.run(
                ['bluetoothctl', 'devices'],
                capture_output=True,
                text=True,
                timeout=5,
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'OBD' in line.upper() or 'ELM327' in line.upper():
                        # Extract device MAC and name
                        match = re.search(r'([0-9A-F:]{17})\s+(.+)', line)
                        if match:
                            mac = match.group(1)
                            name = match.group(2)
                            
                            model = self._identify_model_from_description(name)
                            vendor = self._identify_vendor_from_description(name)
                            
                            adapters.append(AdapterConfig(
                                name=f"{model}_BT_{mac.replace(':', '_')}",
                                adapter_type=AdapterType.OBD2,
                                connection_type=ConnectionType.BLUETOOTH,
                                vendor=vendor,
                                model=model,
                                device_path=mac,
                                capabilities=AdapterCapabilities(
                                    protocols=["OBD2", "CAN"],
                                    max_baud_rate=115200,
                                ),
                                driver="elm327_bt",
                                metadata={
                                    "bluetooth_mac": mac,
                                    "device_name": name,
                                },
                            ))
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        except Exception as e:
            LOGGER.warning("Failed to detect Bluetooth OBD2 adapters: %s", e)
        
        return adapters
    
    def _detect_wifi_obd2(self) -> List[AdapterConfig]:
        """Detect WiFi OBD2 adapters."""
        adapters = []
        
        # WiFi OBD2 adapters typically appear as network devices
        # They usually have SSIDs like "OBD", "ELM327", etc.
        # This would require network scanning which is platform-specific
        # For now, we'll add a placeholder that can be extended
        
        # Check for known WiFi OBD2 SSIDs in system
        try:
            import subprocess
            
            # On Linux, check for known WiFi networks
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'SSID', 'device', 'wifi', 'list'],
                capture_output=True,
                text=True,
                timeout=5,
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    ssid = line.strip()
                    if self._is_obd2_wifi_ssid(ssid):
                        adapters.append(AdapterConfig(
                            name=f"OBD2_WiFi_{ssid}",
                            adapter_type=AdapterType.OBD2,
                            connection_type=ConnectionType.WIFI,
                            vendor="Unknown",
                            model="WiFi OBD2",
                            device_path=ssid,
                            capabilities=AdapterCapabilities(
                                protocols=["OBD2", "CAN"],
                                max_baud_rate=115200,
                            ),
                            driver="elm327_wifi",
                            metadata={"ssid": ssid},
                        ))
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        except Exception as e:
            LOGGER.warning("Failed to detect WiFi OBD2 adapters: %s", e)
        
        return adapters
    
    def _detect_serial_obd2(self) -> List[AdapterConfig]:
        """Detect serial OBD2 adapters."""
        adapters = []
        
        try:
            ports = serial.tools.list_ports.comports()
            
            for port in ports:
                # Try to identify OBD2 adapters by attempting communication
                if self._test_obd2_port(port.device):
                    model = self._identify_model_from_description(port.description)
                    vendor = self._identify_vendor_from_description(port.description)
                    
                    adapters.append(AdapterConfig(
                        name=f"{model}_{port.device}",
                        adapter_type=AdapterType.OBD2,
                        connection_type=ConnectionType.USB,
                        vendor=vendor,
                        model=model,
                        device_path=port.device,
                        capabilities=AdapterCapabilities(
                            protocols=["OBD2", "CAN"],
                            max_baud_rate=115200,
                        ),
                        driver="elm327",
                        metadata={
                            "description": port.description,
                        },
                    ))
        except Exception as e:
            LOGGER.warning("Failed to detect serial OBD2 adapters: %s", e)
        
        return adapters
    
    def _is_obd2_adapter(self, description: str) -> bool:
        """Check if description indicates OBD2 adapter."""
        obd2_keywords = [
            'obd', 'elm327', 'obdlink', 'carista', 'veepeak',
            'bafx', 'plx', 'kiwi', 'scantool', 'autel',
            'innova', 'bluedriver', 'foseal',
        ]
        return any(keyword in description.lower() for keyword in obd2_keywords)
    
    def _is_obd2_wifi_ssid(self, ssid: str) -> bool:
        """Check if SSID indicates OBD2 WiFi adapter."""
        obd2_ssid_patterns = ['obd', 'elm327', 'scantool']
        return any(pattern in ssid.lower() for pattern in obd2_ssid_patterns)
    
    def _identify_model_from_description(self, description: str) -> str:
        """Identify OBD2 adapter model from description."""
        description_lower = description.lower()
        
        if 'elm327' in description_lower:
            return "ELM327"
        elif 'obdlink' in description_lower:
            return "OBDLink"
        elif 'carista' in description_lower:
            return "Carista"
        elif 'veepeak' in description_lower:
            return "Veepeak"
        elif 'bafx' in description_lower:
            return "BAFX"
        elif 'plx' in description_lower:
            return "PLX"
        elif 'kiwi' in description_lower:
            return "Kiwi"
        else:
            return "OBD2 Adapter"
    
    def _identify_vendor_from_description(self, description: str) -> str:
        """Identify vendor from description."""
        description_lower = description.lower()
        
        if 'elm327' in description_lower:
            return "ELM Electronics"
        elif 'obdlink' in description_lower or 'scantool' in description_lower:
            return "ScanTool.net"
        elif 'carista' in description_lower:
            return "Carista"
        elif 'veepeak' in description_lower:
            return "Veepeak"
        elif 'bafx' in description_lower:
            return "BAFX Products"
        elif 'plx' in description_lower:
            return "PLX Devices"
        else:
            return "Unknown"
    
    def _test_obd2_port(self, port: str) -> bool:
        """Test if port is an OBD2 adapter by sending ATZ command."""
        try:
            ser = serial.Serial(port, 115200, timeout=1)
            ser.write(b"ATZ\r\n")  # Reset command
            response = ser.read(100)
            ser.close()
            
            # Check for ELM327 response
            if b"ELM327" in response or b"OK" in response:
                return True
        except Exception:
            pass
        return False
    
    def _load_known_adapters(self) -> List[AdapterConfig]:
        """Load known adapters from database."""
        return self.db.list_adapters(adapter_type=AdapterType.OBD2, enabled_only=True)
    
    def get_adapter(self, name: str) -> Optional[AdapterConfig]:
        """Get adapter by name."""
        if name in self.detected_adapters:
            return self.detected_adapters[name]
        return self.db.get_adapter(name)


__all__ = ["OBD2AdapterDetector"]






