"""
Cellular Modem Interface

Supports various cellular modems for GPS tracking:
- SIM800L (2G)
- SIM7600 (4G LTE)
- SIM7000 (LTE Cat-M1/NB-IoT)
- Quectel EC25 (4G LTE)
- And other AT command compatible modems
"""

from __future__ import annotations

import logging
import serial
import time
from typing import Optional, Dict, List

LOGGER = logging.getLogger(__name__)


class CellularModem:
    """Cellular modem interface for GPS tracking."""
    
    def __init__(
        self,
        port: str = "/dev/ttyUSB2",
        baudrate: int = 115200,
        timeout: float = 5.0,
    ) -> None:
        """
        Initialize cellular modem.
        
        Args:
            port: Serial port (e.g., /dev/ttyUSB2, COM3)
            baudrate: Serial baud rate
            timeout: Command timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial: Optional[serial.Serial] = None
        self.connected = False
        self.network_registered = False
        self.signal_strength = 0
        self.imei: Optional[str] = None
        self.operator: Optional[str] = None
        
    def connect(self) -> bool:
        """Connect to cellular modem."""
        try:
            self._serial = serial.Serial(
                self.port,
                self.baudrate,
                timeout=self.timeout,
                write_timeout=self.timeout,
            )
            
            # Wait for modem to be ready
            time.sleep(2)
            
            # Test connection with AT command
            if self.send_command("AT", expected="OK"):
                self.connected = True
                self._initialize_modem()
                LOGGER.info("Cellular modem connected: %s", self.port)
                return True
            else:
                self._serial.close()
                self._serial = None
                return False
        except Exception as e:
            LOGGER.error("Failed to connect to cellular modem: %s", e)
            return False
    
    def disconnect(self) -> None:
        """Disconnect from cellular modem."""
        if self._serial and self._serial.is_open:
            self._serial.close()
        self.connected = False
        self.network_registered = False
        LOGGER.info("Cellular modem disconnected")
    
    def _initialize_modem(self) -> None:
        """Initialize modem and get status."""
        # Get IMEI
        response = self.send_command("AT+GSN")
        if response and len(response) > 0:
            self.imei = response[0].strip()
        
        # Check network registration
        self._check_network_status()
        
        # Get signal strength
        self._get_signal_strength()
        
        # Get operator
        response = self.send_command("AT+COPS?")
        if response:
            for line in response:
                if "+COPS:" in line:
                    # Parse operator name
                    parts = line.split(",")
                    if len(parts) > 2:
                        self.operator = parts[2].strip('"')
    
    def _check_network_status(self) -> bool:
        """Check if modem is registered on network."""
        response = self.send_command("AT+CREG?")
        if response:
            for line in response:
                if "+CREG:" in line:
                    # Parse registration status
                    parts = line.split(",")
                    if len(parts) > 1:
                        status = int(parts[1].strip())
                        # 1 = registered home network, 5 = registered roaming
                        self.network_registered = status in [1, 5]
                        return self.network_registered
        return False
    
    def _get_signal_strength(self) -> int:
        """Get signal strength (0-31, 99 = unknown)."""
        response = self.send_command("AT+CSQ")
        if response:
            for line in response:
                if "+CSQ:" in line:
                    # Parse signal strength
                    parts = line.split(":")
                    if len(parts) > 1:
                        value = parts[1].split(",")[0].strip()
                        try:
                            self.signal_strength = int(value)
                            return self.signal_strength
                        except ValueError:
                            pass
        return 0
    
    def send_command(self, command: str, expected: Optional[str] = None, timeout: Optional[float] = None) -> Optional[List[str]]:
        """
        Send AT command to modem.
        
        Args:
            command: AT command (without \r\n)
            expected: Expected response (optional)
            timeout: Command timeout (optional)
            
        Returns:
            List of response lines or None if failed
        """
        if not self._serial or not self._serial.is_open:
            return None
        
        try:
            # Clear input buffer
            self._serial.reset_input_buffer()
            
            # Send command
            cmd = f"{command}\r\n"
            self._serial.write(cmd.encode())
            
            # Read response
            response_lines = []
            cmd_timeout = timeout or self.timeout
            start_time = time.time()
            
            while time.time() - start_time < cmd_timeout:
                if self._serial.in_waiting > 0:
                    line = self._serial.readline().decode("utf-8", errors="ignore").strip()
                    if line:
                        response_lines.append(line)
                        # Check for final response
                        if line in ["OK", "ERROR", "NO CARRIER", "NO ANSWER", "NO DIALTONE"]:
                            break
                        if expected and expected in line:
                            break
                time.sleep(0.1)
            
            if expected:
                # Check if expected response found
                found = any(expected in line for line in response_lines)
                if not found:
                    LOGGER.warning("Expected response '%s' not found in: %s", expected, response_lines)
                    return None
            
            return response_lines if response_lines else None
            
        except Exception as e:
            LOGGER.error("Error sending command '%s': %s", command, e)
            return None
    
    def send_sms(self, phone_number: str, message: str) -> bool:
        """Send SMS message."""
        # Set SMS text mode
        if not self.send_command("AT+CMGF=1", expected="OK"):
            return False
        
        # Send SMS
        cmd = f'AT+CMGS="{phone_number}"'
        response = self.send_command(cmd, expected=">")
        if not response:
            return False
        
        # Send message content
        self._serial.write(f"{message}\x1A".encode())
        time.sleep(2)
        
        # Check for OK
        response = self._serial.read(100).decode("utf-8", errors="ignore")
        return "OK" in response
    
    def send_data(self, url: str, data: Dict, method: str = "POST") -> Optional[str]:
        """
        Send HTTP data via cellular connection.
        
        Args:
            url: HTTP URL
            data: Data dictionary (will be JSON encoded)
            method: HTTP method (GET, POST)
            
        Returns:
            Response body or None if failed
        """
        import json
        
        # Initialize HTTP service
        if not self.send_command("AT+HTTPINIT", expected="OK"):
            return None
        
        # Set HTTP parameters
        if not self.send_command(f'AT+HTTPPARA="URL","{url}"', expected="OK"):
            return None
        
        # Set content type
        if not self.send_command('AT+HTTPPARA="CONTENT","application/json"', expected="OK"):
            return None
        
        # Set data
        json_data = json.dumps(data)
        if not self.send_command(f'AT+HTTPDATA={len(json_data)},10000', expected="DOWNLOAD"):
            return None
        
        # Send data
        self._serial.write(json_data.encode())
        time.sleep(1)
        
        # Execute HTTP request
        if method == "POST":
            response = self.send_command("AT+HTTPACTION=1", timeout=30)
        else:
            response = self.send_command("AT+HTTPACTION=0", timeout=30)
        
        if not response:
            return None
        
        # Read response
        time.sleep(2)
        response = self.send_command("AT+HTTPREAD", timeout=10)
        
        # Terminate HTTP service
        self.send_command("AT+HTTPTERM")
        
        if response:
            # Parse response (format varies by modem)
            return "\n".join(response)
        
        return None
    
    def get_status(self) -> Dict:
        """Get modem status."""
        self._check_network_status()
        self._get_signal_strength()
        
        return {
            "connected": self.connected,
            "network_registered": self.network_registered,
            "signal_strength": self.signal_strength,
            "imei": self.imei,
            "operator": self.operator,
            "port": self.port,
        }
    
    def is_available(self) -> bool:
        """Check if cellular modem is available and working."""
        if not self.connected:
            return False
        
        # Check network registration
        if not self._check_network_status():
            return False
        
        # Check signal strength
        signal = self._get_signal_strength()
        if signal == 99 or signal < 5:  # Unknown or very weak signal
            return False
        
        return True


class CellularModemDetector:
    """Auto-detect cellular modems."""
    
    @staticmethod
    def detect_modems() -> List[Dict]:
        """
        Detect available cellular modems.
        
        Returns:
            List of detected modem information
        """
        modems = []
        
        try:
            import serial.tools.list_ports
            
            ports = serial.tools.list_ports.comports()
            
            for port in ports:
                # Check for known cellular modem VID:PID
                vid = f"{port.vid:04x}" if port.vid else None
                pid = f"{port.pid:04x}" if port.pid else None
                
                # Known cellular modem identifiers
                cellular_modems = {
                    ("1e0e", "9001"): "Quectel EC25",
                    ("2c7c", "0125"): "Quectel EC25",
                    ("1e0e", "9003"): "Quectel EC20",
                    ("2c7c", "0121"): "Quectel EC21",
                    ("0403", "6001"): "SIM800L (via FTDI)",
                    ("1a86", "7523"): "SIM800L (via CH340)",
                }
                
                if vid and pid and (vid, pid) in cellular_modems:
                    model = cellular_modems[(vid, pid)]
                    modems.append({
                        "port": port.device,
                        "model": model,
                        "vendor": port.manufacturer or "Unknown",
                        "description": port.description,
                        "vid": vid,
                        "pid": pid,
                    })
                elif "sim" in port.description.lower() or "quectel" in port.description.lower():
                    # Generic detection by description
                    modems.append({
                        "port": port.device,
                        "model": "Cellular Modem",
                        "vendor": port.manufacturer or "Unknown",
                        "description": port.description,
                        "vid": vid,
                        "pid": pid,
                    })
        except Exception as e:
            LOGGER.warning("Failed to detect cellular modems: %s", e)
        
        return modems
    
    @staticmethod
    def test_modem(port: str) -> bool:
        """Test if port is a working cellular modem."""
        try:
            modem = CellularModem(port=port)
            if modem.connect():
                available = modem.is_available()
                modem.disconnect()
                return available
        except Exception:
            pass
        return False


__all__ = ["CellularModem", "CellularModemDetector"]






