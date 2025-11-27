"""
CAN Hardware Detection

Detects and verifies CAN hardware interfaces (Waveshare CAN HAT, etc.)
on the Raspberry Pi.
"""

from __future__ import annotations

import logging
import subprocess
from typing import Dict, List, Optional, Tuple

LOGGER = logging.getLogger(__name__)


class CANHardwareInfo:
    """Information about a CAN hardware interface."""
    
    def __init__(
        self,
        interface: str,
        bitrate: Optional[int] = None,
        state: str = "unknown",
        hardware_type: Optional[str] = None,
    ):
        self.interface = interface  # e.g., "can0", "can1"
        self.bitrate = bitrate
        self.state = state  # "up", "down", "unknown"
        self.hardware_type = hardware_type  # "waveshare", "mcp2515", "native", etc.
    
    def __repr__(self) -> str:
        return f"CANHardwareInfo({self.interface}, {self.bitrate}bps, {self.state}, {self.hardware_type})"


class CANHardwareDetector:
    """Detects and identifies CAN hardware interfaces."""
    
    # Known CAN hardware identifiers
    WAVESHARE_MCP2515 = "waveshare_mcp2515"
    WAVESHARE_MCP2518FD = "waveshare_mcp2518fd"
    NATIVE = "native"  # Built-in CAN (e.g., reTerminal DM)
    UNKNOWN = "unknown"
    
    def __init__(self):
        """Initialize CAN hardware detector."""
        self.detected_interfaces: Dict[str, CANHardwareInfo] = {}
    
    def detect_all(self) -> Dict[str, CANHardwareInfo]:
        """
        Detect all available CAN interfaces.
        
        Returns:
            Dictionary mapping interface names to CANHardwareInfo
        """
        self.detected_interfaces = {}
        
        # Check for CAN interfaces using ip command
        try:
            result = subprocess.run(
                ["ip", "link", "show", "type", "can"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            
            if result.returncode == 0:
                interfaces = self._parse_ip_link_output(result.stdout)
                for interface, info in interfaces.items():
                    hardware_type = self._identify_hardware(interface)
                    info.hardware_type = hardware_type
                    self.detected_interfaces[interface] = info
                    LOGGER.info(f"Detected CAN interface: {interface} ({hardware_type})")
        except FileNotFoundError:
            LOGGER.warning("'ip' command not found. Cannot detect CAN interfaces.")
        except subprocess.TimeoutExpired:
            LOGGER.warning("Timeout detecting CAN interfaces")
        except Exception as e:
            LOGGER.error(f"Error detecting CAN interfaces: {e}")
        
        # Also check /sys/class/net for CAN interfaces
        self._check_sys_net()
        
        return self.detected_interfaces
    
    def _parse_ip_link_output(self, output: str) -> Dict[str, CANHardwareInfo]:
        """Parse output from 'ip link show type can'."""
        interfaces = {}
        current_interface = None
        current_state = "unknown"
        current_bitrate = None
        
        for line in output.split('\n'):
            line = line.strip()
            
            # Interface name (e.g., "1: can0: <NOARP,UP,LOWER_UP>")
            if ': can' in line and ':' in line:
                parts = line.split(':')
                if len(parts) >= 2:
                    interface_name = parts[1].strip().split()[0]  # Extract "can0"
                    if interface_name.startswith('can'):
                        current_interface = interface_name
                        # Check state
                        if 'UP' in line:
                            current_state = "up"
                        elif 'DOWN' in line:
                            current_state = "down"
            
            # Bitrate (e.g., "bitrate 500000")
            elif 'bitrate' in line.lower():
                try:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.lower() == 'bitrate' and i + 1 < len(parts):
                            current_bitrate = int(parts[i + 1])
                            break
                except (ValueError, IndexError):
                    pass
            
            # End of interface block - save info
            if current_interface and line == '' and current_interface not in interfaces:
                interfaces[current_interface] = CANHardwareInfo(
                    interface=current_interface,
                    bitrate=current_bitrate,
                    state=current_state,
                )
                current_interface = None
                current_state = "unknown"
                current_bitrate = None
        
        # Save last interface if any
        if current_interface and current_interface not in interfaces:
            interfaces[current_interface] = CANHardwareInfo(
                interface=current_interface,
                bitrate=current_bitrate,
                state=current_state,
            )
        
        return interfaces
    
    def _check_sys_net(self) -> None:
        """Check /sys/class/net for CAN interfaces."""
        try:
            import os
            sys_net_path = "/sys/class/net"
            if not os.path.exists(sys_net_path):
                return
            
            for item in os.listdir(sys_net_path):
                if item.startswith('can'):
                    if item not in self.detected_interfaces:
                        # Check if interface is up
                        operstate_path = os.path.join(sys_net_path, item, "operstate")
                        state = "unknown"
                        if os.path.exists(operstate_path):
                            try:
                                with open(operstate_path, 'r') as f:
                                    state = f.read().strip().lower()
                            except Exception:
                                pass
                        
                        # Get bitrate if available
                        bitrate = None
                        bitrate_path = os.path.join(sys_net_path, item, "bitrate")
                        if os.path.exists(bitrate_path):
                            try:
                                with open(bitrate_path, 'r') as f:
                                    bitrate = int(f.read().strip())
                            except Exception:
                                pass
                        
                        hardware_type = self._identify_hardware(item)
                        self.detected_interfaces[item] = CANHardwareInfo(
                            interface=item,
                            bitrate=bitrate,
                            state=state,
                            hardware_type=hardware_type,
                        )
                        LOGGER.info(f"Detected CAN interface from /sys: {item} ({hardware_type})")
        except Exception as e:
            LOGGER.debug(f"Error checking /sys/class/net: {e}")
    
    def _identify_hardware(self, interface: str) -> str:
        """
        Identify the type of CAN hardware.
        
        Args:
            interface: CAN interface name (e.g., "can0")
        
        Returns:
            Hardware type identifier
        """
        # Check device tree for hardware info
        try:
            # Check for MCP2515 (common in Waveshare HATs)
            result = subprocess.run(
                ["dmesg"],
                capture_output=True,
                text=True,
                timeout=1,
            )
            
            if result.returncode == 0:
                dmesg_output = result.stdout.lower()
                
                # Check for Waveshare/MCP2515
                if 'mcp2515' in dmesg_output or 'waveshare' in dmesg_output:
                    if 'mcp2518' in dmesg_output or 'fd' in dmesg_output:
                        return self.WAVESHARE_MCP2518FD
                    return self.WAVESHARE_MCP2515
                
                # Check for native CAN (reTerminal DM, etc.)
                if 'can' in dmesg_output and ('native' in dmesg_output or 'flexcan' in dmesg_output):
                    return self.NATIVE
        
        except Exception:
            pass
        
        # Check /proc/device-tree for hardware info
        try:
            import os
            device_tree_path = "/proc/device-tree"
            if os.path.exists(device_tree_path):
                # Look for CAN-related device tree entries
                for root, dirs, files in os.walk(device_tree_path):
                    for name in files + dirs:
                        if 'can' in name.lower() or 'mcp2515' in name.lower() or 'waveshare' in name.lower():
                            if 'mcp2518' in name.lower() or 'fd' in name.lower():
                                return self.WAVESHARE_MCP2518FD
                            elif 'mcp2515' in name.lower():
                                return self.WAVESHARE_MCP2515
        
        except Exception:
            pass
        
        # Default to unknown
        return self.UNKNOWN
    
    def get_interface_info(self, interface: str) -> Optional[CANHardwareInfo]:
        """Get information about a specific CAN interface."""
        if not self.detected_interfaces:
            self.detect_all()
        
        return self.detected_interfaces.get(interface)
    
    def is_waveshare(self, interface: str = "can0") -> bool:
        """Check if the specified interface is a Waveshare CAN HAT."""
        info = self.get_interface_info(interface)
        if info:
            return info.hardware_type in (self.WAVESHARE_MCP2515, self.WAVESHARE_MCP2518FD)
        return False
    
    def list_interfaces(self) -> List[str]:
        """List all detected CAN interface names."""
        if not self.detected_interfaces:
            self.detect_all()
        
        return list(self.detected_interfaces.keys())
    
    def verify_interface(self, interface: str) -> Tuple[bool, str]:
        """
        Verify that a CAN interface exists and is usable.
        
        Args:
            interface: CAN interface name (e.g., "can0")
        
        Returns:
            Tuple of (is_available, message)
        """
        if not self.detected_interfaces:
            self.detect_all()
        
        if interface not in self.detected_interfaces:
            return False, f"CAN interface {interface} not found"
        
        info = self.detected_interfaces[interface]
        
        if info.state != "up":
            return False, f"CAN interface {interface} is {info.state}"
        
        return True, f"CAN interface {interface} is available ({info.hardware_type})"


# Global detector instance
_detector: Optional[CANHardwareDetector] = None


def get_can_hardware_detector() -> CANHardwareDetector:
    """Get or create the global CAN hardware detector."""
    global _detector
    if _detector is None:
        _detector = CANHardwareDetector()
    return _detector


def detect_can_hardware() -> Dict[str, CANHardwareInfo]:
    """Convenience function to detect all CAN hardware."""
    return get_can_hardware_detector().detect_all()


def is_waveshare_can(interface: str = "can0") -> bool:
    """Convenience function to check if interface is Waveshare."""
    return get_can_hardware_detector().is_waveshare(interface)


__all__ = [
    "CANHardwareDetector",
    "CANHardwareInfo",
    "get_can_hardware_detector",
    "detect_can_hardware",
    "is_waveshare_can",
]

