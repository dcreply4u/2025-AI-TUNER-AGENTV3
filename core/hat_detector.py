"""
Raspberry Pi HAT Detection Module

Detects installed HATs on Raspberry Pi platforms, particularly Pi 5.
Supports detection of:
- CAN bus HATs (single and dual)
- GPS HATs
- IMU sensors
- GPIO expanders
- ADC boards
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

LOGGER = logging.getLogger(__name__)


@dataclass
class DetectedHAT:
    """Information about a detected HAT."""
    name: str
    type: str  # "can", "gps", "imu", "gpio_expander", "adc", "combined"
    capabilities: Dict[str, any]
    detected_via: str  # How it was detected
    spi_bus: Optional[int] = None
    i2c_address: Optional[int] = None


@dataclass
class HATConfiguration:
    """Complete HAT configuration for a Pi."""
    can_hats: List[DetectedHAT]
    gps_hats: List[DetectedHAT]
    imu_sensors: List[DetectedHAT]
    gpio_expanders: List[DetectedHAT]
    adc_boards: List[DetectedHAT]
    combined_hats: List[DetectedHAT]  # HATs with multiple features
    
    @property
    def total_can_buses(self) -> int:
        """Total number of CAN buses available."""
        return len(self.can_hats) + sum(
            hat.capabilities.get("can_count", 0) for hat in self.combined_hats
        )
    
    @property
    def has_gps(self) -> bool:
        """Check if GPS is available."""
        return len(self.gps_hats) > 0 or any(
            "gps" in hat.capabilities for hat in self.combined_hats
        )
    
    @property
    def has_imu(self) -> bool:
        """Check if IMU is available."""
        return len(self.imu_sensors) > 0 or any(
            "imu" in hat.capabilities or "gyro" in hat.capabilities 
            for hat in self.combined_hats
        )


class HATDetector:
    """Detects installed HATs on Raspberry Pi."""
    
    @staticmethod
    def detect_all_hats() -> HATConfiguration:
        """
        Detect all installed HATs.
        
        Returns:
            HATConfiguration with all detected HATs
        """
        config = HATConfiguration(
            can_hats=[],
            gps_hats=[],
            imu_sensors=[],
            gpio_expanders=[],
            adc_boards=[],
            combined_hats=[],
        )
        
        # Detect CAN HATs
        config.can_hats = HATDetector._detect_can_hats()
        
        # Detect GPS HATs
        config.gps_hats = HATDetector._detect_gps_hats()
        
        # Detect IMU sensors
        config.imu_sensors = HATDetector._detect_imu_sensors()
        
        # Detect GPIO expanders
        config.gpio_expanders = HATDetector._detect_gpio_expanders()
        
        # Detect ADC boards
        config.adc_boards = HATDetector._detect_adc_boards()
        
        # Detect combined HATs (like PiCAN with GPS/IMU)
        config.combined_hats = HATDetector._detect_combined_hats()
        
        LOGGER.info(
            "HAT Detection: %d CAN, %d GPS, %d IMU, %d GPIO expanders, %d ADC, %d combined",
            len(config.can_hats), len(config.gps_hats), len(config.imu_sensors),
            len(config.gpio_expanders), len(config.adc_boards), len(config.combined_hats)
        )
        
        return config
    
    @staticmethod
    def _detect_can_hats() -> List[DetectedHAT]:
        """Detect CAN bus HATs."""
        can_hats = []
        
        # Method 1: Check for CAN interfaces in /sys/class/net
        can_interfaces = list(Path("/sys/class/net").glob("can*"))
        if can_interfaces:
            for can_if in can_interfaces:
                can_name = can_if.name
                # Try to identify the HAT type from device tree
                hat_info = HATDetector._identify_can_hat(can_name)
                if hat_info:
                    can_hats.append(hat_info)
        
        # Method 2: Check device tree overlays for CAN HATs
        device_tree_hats = HATDetector._detect_can_from_device_tree()
        for hat in device_tree_hats:
            # Avoid duplicates
            if not any(h.name == hat.name for h in can_hats):
                can_hats.append(hat)
        
        # Method 3: Check SPI devices for MCP2515/MCP2518FD
        spi_can_hats = HATDetector._detect_can_from_spi()
        for hat in spi_can_hats:
            if not any(h.name == hat.name for h in can_hats):
                can_hats.append(hat)
        
        return can_hats
    
    @staticmethod
    def _identify_can_hat(can_interface: str) -> Optional[DetectedHAT]:
        """Identify CAN HAT from interface name."""
        try:
            # Check device tree for HAT identification
            device_path = Path(f"/sys/class/net/{can_interface}/device")
            if device_path.exists():
                # Try to find compatible string
                compatible_path = device_path / "of_node" / "compatible"
                if compatible_path.exists():
                    compatible = compatible_path.read_text().strip()
                    
                    # MCP2515 (CAN 2.0B, 1 Mbps) - PiCAN, PiCAN2, PiCAN3
                    if "mcp2515" in compatible.lower():
                        return DetectedHAT(
                            name="PiCAN/MCP2515 CAN HAT",
                            type="can",
                            capabilities={
                                "can_standard": "2.0B",
                                "max_bitrate": 1000000,
                                "can_fd": False,
                            },
                            detected_via=f"device_tree:{can_interface}",
                        )
                    
                    # MCP2518FD (CAN FD, 5 Mbps) - Custom dual CAN FD HAT
                    if "mcp2518fd" in compatible.lower():
                        return DetectedHAT(
                            name="MCP2518FD CAN FD HAT",
                            type="can",
                            capabilities={
                                "can_standard": "FD",
                                "max_bitrate": 5000000,
                                "can_fd": True,
                            },
                            detected_via=f"device_tree:{can_interface}",
                        )
        except Exception as e:
            LOGGER.debug("Failed to identify CAN HAT for %s: %s", can_interface, e)
        
        # Fallback: Generic CAN HAT
        return DetectedHAT(
            name=f"Generic CAN HAT ({can_interface})",
            type="can",
            capabilities={
                "can_standard": "Unknown",
                "max_bitrate": 1000000,
                "can_fd": False,
            },
            detected_via=f"interface:{can_interface}",
        )
    
    @staticmethod
    def _detect_can_from_device_tree() -> List[DetectedHAT]:
        """Detect CAN HATs from device tree overlays."""
        hats = []
        
        try:
            # Check /boot/config.txt for CAN overlays
            config_path = Path("/boot/config.txt")
            if config_path.exists():
                config_text = config_path.read_text()
                
                # Look for CAN overlay configurations
                if "dtoverlay=mcp2515" in config_text.lower():
                    hats.append(DetectedHAT(
                        name="MCP2515 CAN HAT (from config)",
                        type="can",
                        capabilities={
                            "can_standard": "2.0B",
                            "max_bitrate": 1000000,
                            "can_fd": False,
                        },
                        detected_via="config.txt",
                    ))
                
                if "dtoverlay=mcp2518fd" in config_text.lower():
                    hats.append(DetectedHAT(
                        name="MCP2518FD CAN FD HAT (from config)",
                        type="can",
                        capabilities={
                            "can_standard": "FD",
                            "max_bitrate": 5000000,
                            "can_fd": True,
                        },
                        detected_via="config.txt",
                    ))
        except Exception as e:
            LOGGER.debug("Failed to detect CAN from device tree: %s", e)
        
        return hats
    
    @staticmethod
    def _detect_can_from_spi() -> List[DetectedHAT]:
        """Detect CAN HATs from SPI devices."""
        hats = []
        
        try:
            # Check SPI devices
            spi_path = Path("/sys/bus/spi/devices")
            if spi_path.exists():
                for spi_dev in spi_path.iterdir():
                    device_name = spi_dev.name
                    # MCP2515 typically shows as spi0.x or spi1.x
                    if "mcp2515" in device_name.lower():
                        hats.append(DetectedHAT(
                            name="MCP2515 CAN HAT (SPI)",
                            type="can",
                            capabilities={
                                "can_standard": "2.0B",
                                "max_bitrate": 1000000,
                                "can_fd": False,
                            },
                            detected_via=f"spi:{device_name}",
                            spi_bus=int(device_name.split('.')[0].replace('spi', '')) if '.' in device_name else None,
                        ))
                    elif "mcp2518fd" in device_name.lower():
                        hats.append(DetectedHAT(
                            name="MCP2518FD CAN FD HAT (SPI)",
                            type="can",
                            capabilities={
                                "can_standard": "FD",
                                "max_bitrate": 5000000,
                                "can_fd": True,
                            },
                            detected_via=f"spi:{device_name}",
                            spi_bus=int(device_name.split('.')[0].replace('spi', '')) if '.' in device_name else None,
                        ))
        except Exception as e:
            LOGGER.debug("Failed to detect CAN from SPI: %s", e)
        
        return hats
    
    @staticmethod
    def _detect_gps_hats() -> List[DetectedHAT]:
        """Detect GPS HATs."""
        gps_hats = []
        
        # Method 1: Check for GPS devices on UART
        try:
            # Check /dev for GPS devices
            uart_devices = list(Path("/dev").glob("ttyAMA*"))
            uart_devices.extend(Path("/dev").glob("ttyUSB*"))
            uart_devices.extend(Path("/dev").glob("ttyACM*"))
            
            for uart_dev in uart_devices:
                # Try to identify GPS module
                # This is heuristic - actual detection would need to query the device
                # Common GPS modules: MTK3339, L76K, MAX-7Q
                gps_info = HATDetector._identify_gps_device(uart_dev)
                if gps_info:
                    gps_hats.append(gps_info)
        except Exception as e:
            LOGGER.debug("Failed to detect GPS from UART: %s", e)
        
        # Method 2: Check I2C for GPS modules (some use I2C)
        try:
            i2c_gps = HATDetector._detect_gps_from_i2c()
            gps_hats.extend(i2c_gps)
        except Exception as e:
            LOGGER.debug("Failed to detect GPS from I2C: %s", e)
        
        return gps_hats
    
    @staticmethod
    def _identify_gps_device(uart_dev: Path) -> Optional[DetectedHAT]:
        """Try to identify GPS device from UART."""
        # This is a placeholder - actual implementation would need to:
        # 1. Open the UART
        # 2. Send NMEA queries
        # 3. Parse responses to identify module
        
        # For now, return generic GPS if UART exists
        # In production, this would be more sophisticated
        return DetectedHAT(
            name=f"GPS HAT ({uart_dev.name})",
            type="gps",
            capabilities={
                "protocol": "NMEA",
                "update_rate": "Unknown",
            },
            detected_via=f"uart:{uart_dev.name}",
        )
    
    @staticmethod
    def _detect_gps_from_i2c() -> List[DetectedHAT]:
        """Detect GPS modules on I2C bus."""
        gps_hats = []
        
        try:
            # Use i2cdetect to scan I2C bus
            result = subprocess.run(
                ["i2cdetect", "-y", "1"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            
            if result.returncode == 0:
                # Parse i2cdetect output for known GPS addresses
                # Common GPS I2C addresses: 0x42 (NEO-6M), 0x10 (some modules)
                output = result.stdout
                # This would need actual parsing of i2cdetect output
                # For now, return empty list
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        except Exception as e:
            LOGGER.debug("Failed to detect GPS from I2C: %s", e)
        
        return gps_hats
    
    @staticmethod
    def _detect_imu_sensors() -> List[DetectedHAT]:
        """Detect IMU sensors (accelerometer, gyroscope, magnetometer)."""
        imu_sensors = []
        
        # Method 1: Check I2C for common IMU chips
        try:
            # Common IMU I2C addresses:
            # MPU6050: 0x68, 0x69
            # MPU9250: 0x68, 0x69
            # BNO085: 0x4A, 0x4B
            # LSM6DS3: 0x6A, 0x6B
            
            result = subprocess.run(
                ["i2cdetect", "-y", "1"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                
                # Check for MPU6050/MPU9250 (0x68, 0x69)
                if "68" in output or "69" in output:
                    imu_sensors.append(DetectedHAT(
                        name="MPU6050/MPU9250 IMU",
                        type="imu",
                        capabilities={
                            "accelerometer": True,
                            "gyroscope": True,
                            "magnetometer": "MPU9250" if "9250" in output else False,
                        },
                        detected_via="i2c",
                        i2c_address=0x68,
                    ))
                
                # Check for BNO085 (0x4A, 0x4B)
                if "4a" in output or "4b" in output:
                    imu_sensors.append(DetectedHAT(
                        name="BNO085 IMU",
                        type="imu",
                        capabilities={
                            "accelerometer": True,
                            "gyroscope": True,
                            "magnetometer": True,
                            "9_axis": True,
                        },
                        detected_via="i2c",
                        i2c_address=0x4A,
                    ))
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        except Exception as e:
            LOGGER.debug("Failed to detect IMU from I2C: %s", e)
        
        return imu_sensors
    
    @staticmethod
    def _detect_gpio_expanders() -> List[DetectedHAT]:
        """Detect GPIO expander chips (MCP23017, etc.)."""
        expanders = []
        
        try:
            # MCP23017 I2C addresses: 0x20-0x27
            result = subprocess.run(
                ["i2cdetect", "-y", "1"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                
                # Check for MCP23017 (0x20-0x27)
                mcp_addresses = ["20", "21", "22", "23", "24", "25", "26", "27"]
                for addr in mcp_addresses:
                    if addr in output:
                        expanders.append(DetectedHAT(
                            name="MCP23017 GPIO Expander",
                            type="gpio_expander",
                            capabilities={
                                "gpio_pins": 16,
                                "ports": 2,
                            },
                            detected_via="i2c",
                            i2c_address=int(addr, 16),
                        ))
                        break  # Only add once
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        except Exception as e:
            LOGGER.debug("Failed to detect GPIO expander: %s", e)
        
        return expanders
    
    @staticmethod
    def _detect_adc_boards() -> List[DetectedHAT]:
        """Detect ADC boards (ADS1115, MCP3008, etc.)."""
        adc_boards = []
        
        try:
            # ADS1115 I2C addresses: 0x48, 0x49, 0x4A, 0x4B
            result = subprocess.run(
                ["i2cdetect", "-y", "1"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                
                # Check for ADS1115 (0x48-0x4B)
                ads_addresses = ["48", "49", "4a", "4b"]
                for addr in ads_addresses:
                    if addr in output:
                        adc_boards.append(DetectedHAT(
                            name="ADS1115 ADC",
                            type="adc",
                            capabilities={
                                "channels": 4,
                                "resolution": 16,
                                "bits": 16,
                            },
                            detected_via="i2c",
                            i2c_address=int(addr, 16),
                        ))
                        break
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        except Exception as e:
            LOGGER.debug("Failed to detect ADC board: %s", e)
        
        return adc_boards
    
    @staticmethod
    def _detect_combined_hats() -> List[DetectedHAT]:
        """Detect combined HATs (like PiCAN with GPS/IMU)."""
        combined = []
        
        # Check for PiCAN with GPS, Gyro, Accelerometer
        # This HAT has:
        # - CAN bus (MCP2515)
        # - GPS (MTK3339 on UART)
        # - IMU (gyro + accel)
        
        # Detection heuristic: If we have CAN + GPS + IMU all detected,
        # it might be a combined HAT
        # In practice, this would need more sophisticated detection
        
        # For now, check device tree for known combined HAT identifiers
        try:
            if Path("/proc/device-tree").exists():
                # Look for PiCAN-specific identifiers
                # This is placeholder - actual detection would be more specific
                pass
        except Exception:
            pass
        
        return combined


__all__ = ["HATDetector", "DetectedHAT", "HATConfiguration"]



