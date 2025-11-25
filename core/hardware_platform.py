"""
Hardware Platform Detection and Configuration

Detects the hardware platform (Raspberry Pi, reTerminal DM, Jetson, etc.)
and provides platform-specific configuration.
"""

from __future__ import annotations

import logging
import os
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

LOGGER = logging.getLogger(__name__)


@dataclass
class HardwareConfig:
    """Platform-specific hardware configuration."""

    platform_name: str
    can_channels: List[str]
    can_bitrate: int = 500000
    gpio_available: bool = True
    display_size: tuple[int, int] = (1280, 720)  # width, height
    touchscreen: bool = False
    has_onboard_can: bool = False
    power_management: bool = False
    button_pins: Dict[str, int] = None  # type: ignore
    has_treehopper: bool = False  # Treehopper USB device connected
    total_gpio_pins: int = 40  # Base platform GPIO (may increase with Treehopper)
    total_adc_channels: int = 7  # Base platform ADC (may increase with Treehopper)

    def __post_init__(self) -> None:
        if self.button_pins is None:
            self.button_pins = {}


class HardwareDetector:
    """Detects hardware platform and returns appropriate configuration."""

    @staticmethod
    def detect() -> HardwareConfig:
        """
        Detect the current hardware platform.

        Returns:
            HardwareConfig instance with platform-specific settings
        """
        machine = platform.machine().lower()
        uname = os.uname()

        # Check for reTerminal DM (CM4-based with dual CAN)
        if HardwareDetector._is_reterminal_dm():
            LOGGER.info("Detected Seeed reTerminal DM platform")
            config = HardwareDetector._reterminal_dm_config()
        # Check for BeagleBone Black (built-in dual CAN, PRU, ADC)
        elif HardwareDetector._is_beaglebone_black():
            LOGGER.info("Detected BeagleBone Black platform")
            config = HardwareDetector._beaglebone_black_config()
        # Check for Jetson
        elif HardwareDetector._is_jetson():
            LOGGER.info("Detected NVIDIA Jetson platform")
            config = HardwareDetector._jetson_config()
        # Check for Raspberry Pi 5 (check before generic Pi)
        elif HardwareDetector._is_raspberry_pi_5():
            LOGGER.info("Detected Raspberry Pi 5 platform")
            config = HardwareDetector._raspberry_pi_5_config()
        # Check for Raspberry Pi (generic - Pi 4, CM4, etc.)
        elif HardwareDetector._is_raspberry_pi():
            LOGGER.info("Detected Raspberry Pi platform")
            config = HardwareDetector._raspberry_pi_config()
        # Check for Windows
        elif platform.system() == "Windows":
            LOGGER.info("Detected Windows platform")
            config = HardwareDetector._windows_config()
        # Default fallback (generic Linux)
        else:
            LOGGER.warning("Unknown platform, using generic Linux defaults")
            config = HardwareDetector._generic_config()
        
        # Check for Treehopper (additional I/O device)
        try:
            from interfaces.treehopper_adapter import get_treehopper_adapter
            treehopper = get_treehopper_adapter()
            if treehopper and treehopper.is_connected():
                config.has_treehopper = True
                config.total_gpio_pins = config.total_gpio_pins + 20  # Add Treehopper pins
                config.total_adc_channels = config.total_adc_channels + 8  # Add Treehopper ADC
                LOGGER.info("Treehopper detected - total I/O: %d GPIO, %d ADC", 
                           config.total_gpio_pins, config.total_adc_channels)
        except Exception as e:
            LOGGER.debug("Treehopper detection skipped: %s", e)
        
        return config

    @staticmethod
    def _is_reterminal_dm() -> bool:
        """Check if running on Seeed reTerminal DM."""
        # reTerminal DM uses CM4, check for Seeed-specific identifiers
        try:
            # Check device tree model
            if Path("/proc/device-tree/model").exists():
                model = Path("/proc/device-tree/model").read_text().lower()
                if "reterminal" in model or "seeed" in model:
                    return True

            # Check for dual CAN interfaces (reTerminal DM has can0 and can1)
            can_interfaces = list(Path("/sys/class/net").glob("can*"))
            if len(can_interfaces) >= 2:
                # Additional check: reTerminal DM has specific GPIO layout
                if Path("/sys/firmware/devicetree/base/compatible").exists():
                    compatible = Path("/sys/firmware/devicetree/base/compatible").read_text()
                    if "seeed" in compatible.lower():
                        return True

            # Check for reTerminal DM specific files
            if Path("/opt/reterminal").exists() or Path("/usr/local/bin/reterminal").exists():
                return True
        except Exception:
            pass
        return False

    @staticmethod
    def _is_jetson() -> bool:
        """Check if running on NVIDIA Jetson."""
        try:
            if Path("/proc/device-tree/model").exists():
                model = Path("/proc/device-tree/model").read_text().lower()
                if "jetson" in model or "tegra" in model:
                    return True
        except Exception:
            pass
        return False

    @staticmethod
    def _is_beaglebone_black() -> bool:
        """Check if running on BeagleBone Black."""
        try:
            # Check device tree model
            if Path("/proc/device-tree/model").exists():
                model = Path("/proc/device-tree/model").read_text().lower()
                if "beaglebone" in model or "am335x" in model:
                    return True
            
            # Check CPU info
            if Path("/proc/cpuinfo").exists():
                cpuinfo = Path("/proc/cpuinfo").read_text()
                if "am335x" in cpuinfo.lower() or "beaglebone" in cpuinfo.lower():
                    return True
            
            # Check for BeagleBone-specific files
            if Path("/sys/class/gpio/gpiochip0").exists():
                # Check compatible string
                if Path("/sys/firmware/devicetree/base/compatible").exists():
                    compatible = Path("/sys/firmware/devicetree/base/compatible").read_text()
                    if "am335x" in compatible.lower() or "beaglebone" in compatible.lower():
                        return True
        except Exception:
            pass
        return False

    @staticmethod
    def _is_raspberry_pi_5() -> bool:
        """Check if running on Raspberry Pi 5."""
        try:
            if Path("/proc/device-tree/model").exists():
                model = Path("/proc/device-tree/model").read_text().lower()
                # Pi 5 has specific model identifiers
                if "raspberry pi 5" in model or "rpi 5" in model:
                    return True
                # Check for Pi 5 revision code (BCM2712)
                if "raspberry pi" in model:
                    # Check revision code in /proc/cpuinfo or device tree
                    if Path("/proc/cpuinfo").exists():
                        cpuinfo = Path("/proc/cpuinfo").read_text()
                        # Pi 5 uses BCM2712 (vs BCM2711 for Pi 4)
                        if "bcm2712" in cpuinfo.lower():
                            return True
                    # Check device tree compatible string
                    if Path("/proc/device-tree/compatible").exists():
                        compatible = Path("/proc/device-tree/compatible").read_text().lower()
                        if "bcm2712" in compatible:
                            return True
        except Exception:
            pass
        return False

    @staticmethod
    def _is_raspberry_pi() -> bool:
        """Check if running on Raspberry Pi (generic - Pi 4, CM4, etc.)."""
        try:
            if Path("/proc/device-tree/model").exists():
                model = Path("/proc/device-tree/model").read_text().lower()
                if "raspberry pi" in model:
                    # Exclude Pi 5 (already checked)
                    if "raspberry pi 5" not in model and "rpi 5" not in model:
                        return True
            # Fallback: check CPU info
            if Path("/proc/cpuinfo").exists():
                cpuinfo = Path("/proc/cpuinfo").read_text()
                if ("raspberry pi" in cpuinfo.lower() or "bcm" in cpuinfo.lower()) and "bcm2712" not in cpuinfo.lower():
                    return True
        except Exception:
            pass
        return False

    @staticmethod
    def _reterminal_dm_config() -> HardwareConfig:
        """Configuration for Seeed reTerminal DM."""
        return HardwareConfig(
            platform_name="reTerminal DM",
            can_channels=["can0", "can1"],  # Dual CAN FD
            can_bitrate=500000,  # Standard CAN, can be upgraded to CAN FD
            gpio_available=True,
            display_size=(1280, 800),  # 10.1" panel resolution
            touchscreen=True,
            has_onboard_can=True,
            power_management=True,
            total_gpio_pins=40,  # 40-pin GPIO header
            total_adc_channels=7,  # Via ADC HAT
            button_pins={
                # reTerminal DM has physical buttons - map common ones
                "home": 5,  # GPIO5 typically used for home button
                "back": 6,  # GPIO6 for back button
                "function": 13,  # GPIO13 for function button
            },
        )

    @staticmethod
    def _beaglebone_black_config() -> HardwareConfig:
        """Configuration for BeagleBone Black."""
        # Check for CAN interfaces (BeagleBone Black has dual CAN, may need cape)
        can_channels = []
        if Path("/sys/class/net/can0").exists():
            can_channels.append("can0")
        if Path("/sys/class/net/can1").exists():
            can_channels.append("can1")
        # BeagleBone Black has 2x CAN controllers, but may need CAN cape
        if not can_channels:
            can_channels = ["can0", "can1"]  # Assume CAN cape installed
        
        return HardwareConfig(
            platform_name="BeagleBone Black",
            can_channels=can_channels,
            can_bitrate=500000,
            gpio_available=True,
            display_size=(1280, 720),  # External display (HDMI or LCD cape)
            touchscreen=False,  # Depends on display
            has_onboard_can=True,  # Built-in CAN controllers (via cape)
            power_management=True,
            total_gpio_pins=65,  # 65+ GPIO pins available
            total_adc_channels=7,  # 7x 12-bit ADC built-in
        )

    @staticmethod
    def _jetson_config() -> HardwareConfig:
        """Configuration for NVIDIA Jetson platforms."""
        # Jetson typically needs USB-CAN or external CAN interface
        can_channels = []
        if Path("/sys/class/net/can0").exists():
            can_channels.append("can0")
        if Path("/sys/class/net/can1").exists():
            can_channels.append("can1")
        if not can_channels:
            can_channels = ["can0"]  # Default, may need USB-CAN adapter

        return HardwareConfig(
            platform_name="NVIDIA Jetson",
            can_channels=can_channels,
            can_bitrate=500000,
            gpio_available=True,
            display_size=(1920, 1080),  # Common Jetson display
            touchscreen=False,  # Depends on display
            has_onboard_can=len(can_channels) > 0,
            power_management=True,
        )

    @staticmethod
    def _raspberry_pi_5_config() -> HardwareConfig:
        """Configuration for Raspberry Pi 5 with HAT detection."""
        # Detect installed HATs
        hat_config = None
        try:
            from core.hat_detector import HATDetector
            hat_config = HATDetector.detect_all_hats()
            LOGGER.info("HAT detection completed: %d CAN buses, GPS: %s, IMU: %s",
                       hat_config.total_can_buses, hat_config.has_gps, hat_config.has_imu)
        except Exception as e:
            LOGGER.debug("HAT detection failed, using fallback: %s", e)
        
        # Determine CAN channels from HATs or fallback detection
        can_channels = []
        can_bitrate = 500000
        has_can_fd = False
        
        if hat_config and hat_config.total_can_buses > 0:
            # Use detected CAN buses
            can_interfaces = sorted(Path("/sys/class/net").glob("can*"))
            for can_if in can_interfaces[:hat_config.total_can_buses]:
                can_channels.append(can_if.name)
            
            # Check if any CAN HAT supports CAN FD
            all_can_hats = hat_config.can_hats + [
                h for h in hat_config.combined_hats if "can" in h.capabilities
            ]
            has_can_fd = any(
                hat.capabilities.get("can_fd", False) for hat in all_can_hats
            )
            if has_can_fd:
                can_bitrate = 5000000  # CAN FD supports up to 5 Mbps
        else:
            # Fallback: detect CAN interfaces directly
            if Path("/sys/class/net/can0").exists():
                can_channels.append("can0")
            if Path("/sys/class/net/can1").exists():
                can_channels.append("can1")
            if not can_channels:
                can_channels = ["can0"]  # Default, assumes CAN HAT installed
        
        # Calculate GPIO pins (base + expanders)
        total_gpio = 40  # Pi 5 base GPIO
        if hat_config:
            for expander in hat_config.gpio_expanders:
                total_gpio += expander.capabilities.get("gpio_pins", 0)
        
        # Calculate ADC channels
        total_adc = 0
        if hat_config:
            for adc in hat_config.adc_boards:
                total_adc += adc.capabilities.get("channels", 0)
        if total_adc == 0:
            total_adc = 7  # Default assumption
        
        # Determine platform name with HAT info
        platform_name = "Raspberry Pi 5"
        if hat_config:
            hat_summary = []
            if hat_config.total_can_buses > 0:
                hat_summary.append(f"{hat_config.total_can_buses}x CAN")
            if hat_config.has_gps:
                hat_summary.append("GPS")
            if hat_config.has_imu:
                hat_summary.append("IMU")
            if hat_summary:
                platform_name = f"Raspberry Pi 5 ({', '.join(hat_summary)})"

        return HardwareConfig(
            platform_name=platform_name,
            can_channels=can_channels,
            can_bitrate=can_bitrate,
            gpio_available=True,
            display_size=(1920, 1080),  # Pi 5 supports higher resolutions
            touchscreen=False,  # Depends on display
            has_onboard_can=len(can_channels) > 0,
            power_management=True,  # Pi 5 has better power management
            total_gpio_pins=total_gpio,
            total_adc_channels=total_adc,
        )

    @staticmethod
    def _raspberry_pi_config() -> HardwareConfig:
        """Configuration for Raspberry Pi (Pi 4, CM4, etc.)."""
        # Pi typically needs CAN HAT
        can_channels = []
        if Path("/sys/class/net/can0").exists():
            can_channels.append("can0")
        if Path("/sys/class/net/can1").exists():
            can_channels.append("can1")
        if not can_channels:
            can_channels = ["can0"]  # Default, assumes CAN HAT installed

        return HardwareConfig(
            platform_name="Raspberry Pi",
            can_channels=can_channels,
            can_bitrate=500000,
            gpio_available=True,
            display_size=(1280, 720),  # Common Pi display
            touchscreen=False,  # Depends on display
            has_onboard_can=len(can_channels) > 0,
            power_management=False,
        )

    @staticmethod
    def _windows_config() -> HardwareConfig:
        """Configuration for Windows platform."""
        # Windows typically needs USB-CAN adapter
        can_channels = []
        # Check for USB-CAN adapters (would need specific detection)
        # For now, assume USB-CAN adapter available
        can_channels = ["can0"]  # Default assumption

        # Check if Treehopper is available (provides GPIO/ADC on Windows)
        gpio_available = False
        try:
            from interfaces.treehopper_adapter import get_treehopper_adapter
            treehopper = get_treehopper_adapter()
            if treehopper and treehopper.is_connected():
                gpio_available = True
                LOGGER.info("Treehopper detected on Windows - GPIO/ADC available")
        except Exception:
            # Treehopper not available, but GPIO can still be enabled if Treehopper is connected later
            # The unified_io_manager will handle Treehopper detection at runtime
            pass

        return HardwareConfig(
            platform_name="Windows",
            can_channels=can_channels,
            can_bitrate=500000,
            gpio_available=gpio_available,  # Available via Treehopper USB adapter
            display_size=(1920, 1080),  # Typical Windows display
            touchscreen=False,  # Depends on display
            has_onboard_can=False,
            power_management=False,
            total_gpio_pins=20,  # Treehopper provides 20 GPIO pins
            total_adc_channels=8,  # Treehopper provides 8 ADC channels
        )

    @staticmethod
    def _generic_config() -> HardwareConfig:
        """Generic Linux configuration (fallback)."""
        can_channels = []
        if Path("/sys/class/net/can0").exists():
            can_channels.append("can0")
        if not can_channels:
            can_channels = ["can0"]  # Default assumption

        return HardwareConfig(
            platform_name="Generic Linux",
            can_channels=can_channels,
            can_bitrate=500000,
            gpio_available=False,
            display_size=(1280, 720),
            touchscreen=False,
            has_onboard_can=False,
            power_management=False,
        )


# Global hardware config instance
_hardware_config: Optional[HardwareConfig] = None


def get_hardware_config() -> HardwareConfig:
    """Get or detect hardware configuration."""
    global _hardware_config
    if _hardware_config is None:
        _hardware_config = HardwareDetector.detect()
    return _hardware_config


__all__ = ["HardwareConfig", "HardwareDetector", "get_hardware_config"]

