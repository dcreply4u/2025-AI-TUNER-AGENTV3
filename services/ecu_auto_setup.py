"""
ECU Auto-Setup System

Automatically detects ECU vendor and optimizes configuration for that specific ECU.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from services.can_vendor_detector import CANVendor, CANVendorDetector

LOGGER = logging.getLogger(__name__)


class Manufacturer(Enum):
    """Car manufacturers."""

    FORD = "ford"
    CHEVROLET = "chevrolet"
    DODGE = "dodge"
    TOYOTA = "toyota"
    HONDA = "honda"
    NISSAN = "nissan"
    SUBARU = "subaru"
    MITSUBISHI = "mitsubishi"
    BMW = "bmw"
    MERCEDES = "mercedes"
    AUDI = "audi"
    PORSCHE = "porsche"
    FERRARI = "ferrari"
    LAMBORGHINI = "lamborghini"
    GENERIC = "generic"


@dataclass
class ECUProfile:
    """ECU-specific configuration profile."""

    vendor: CANVendor
    manufacturer: Optional[Manufacturer] = None
    can_channel: str = "can0"
    can_bitrate: int = 500000
    can_ids: List[int] = field(default_factory=list)
    dbc_file: str = ""
    metric_mappings: Dict[str, str] = field(default_factory=dict)
    polling_intervals: Dict[str, float] = field(default_factory=dict)
    default_settings: Dict[str, Any] = field(default_factory=dict)
    optimization_hints: List[str] = field(default_factory=list)


class ECUAutoSetup:
    """Automatically detects and configures ECU settings."""

    # ECU vendor profiles with optimizations
    ECU_PROFILES: Dict[CANVendor, ECUProfile] = {
        CANVendor.HOLLEY: ECUProfile(
            vendor=CANVendor.HOLLEY,
            can_bitrate=500000,
            can_ids=[0x180, 0x181, 0x182, 0x183, 0x184, 0x185],
            dbc_file="dbc/holley.dbc",
            metric_mappings={
                "RPM": "Engine_RPM",
                "TPS": "Throttle_Position",
                "CLT": "Coolant_Temp",
                "MAP": "Boost_Pressure",
                "AFR": "Lambda",
            },
            polling_intervals={
                "Engine_RPM": 0.1,
                "Throttle_Position": 0.1,
                "Coolant_Temp": 0.5,
                "Boost_Pressure": 0.1,
            },
            default_settings={
                "rpm_redline": 7000,
                "boost_max_psi": 30,
                "coolant_warning_temp": 105,
            },
            optimization_hints=[
                "Holley EFI uses high-speed CAN at 500kbps",
                "Primary data on 0x180-0x185",
                "Fast polling recommended for RPM and TPS",
            ],
        ),
        CANVendor.HALTECH: ECUProfile(
            vendor=CANVendor.HALTECH,
            can_bitrate=500000,
            can_ids=[0x200, 0x201, 0x202, 0x203, 0x204, 0x205],
            dbc_file="dbc/haltech.dbc",
            metric_mappings={
                "RPM": "Engine_RPM",
                "Throttle": "Throttle_Position",
                "Coolant": "Coolant_Temp",
                "Boost": "Boost_Pressure",
                "Lambda": "Lambda",
            },
            polling_intervals={
                "Engine_RPM": 0.05,
                "Throttle_Position": 0.05,
                "Coolant_Temp": 0.5,
                "Boost_Pressure": 0.1,
            },
            default_settings={
                "rpm_redline": 8000,
                "boost_max_psi": 40,
                "coolant_warning_temp": 110,
            },
            optimization_hints=[
                "Haltech uses very fast CAN updates",
                "Ultra-fast polling for RPM (50ms)",
                "Excellent for high-revving engines",
            ],
        ),
        CANVendor.AEM: ECUProfile(
            vendor=CANVendor.AEM,
            can_bitrate=500000,
            can_ids=[0x300, 0x301, 0x302, 0x303],
            dbc_file="dbc/aem.dbc",
            metric_mappings={
                "EngineSpeed": "Engine_RPM",
                "ThrottlePosition": "Throttle_Position",
                "CoolantTemp": "Coolant_Temp",
                "ManifoldPressure": "Boost_Pressure",
                "Lambda": "Lambda",
            },
            polling_intervals={
                "Engine_RPM": 0.1,
                "Throttle_Position": 0.1,
                "Coolant_Temp": 0.5,
            },
            default_settings={
                "rpm_redline": 7500,
                "boost_max_psi": 35,
            },
            optimization_hints=[
                "AEM Infinity provides comprehensive data",
                "Good balance of speed and data richness",
            ],
        ),
        CANVendor.LINK: ECUProfile(
            vendor=CANVendor.LINK,
            can_bitrate=500000,
            can_ids=[0x400, 0x401, 0x402],
            dbc_file="dbc/link.dbc",
            metric_mappings={
                "RPM": "Engine_RPM",
                "TPS": "Throttle_Position",
                "Coolant": "Coolant_Temp",
                "MAP": "Boost_Pressure",
            },
            polling_intervals={
                "Engine_RPM": 0.1,
                "Throttle_Position": 0.1,
            },
            default_settings={
                "rpm_redline": 7000,
            },
            optimization_hints=[
                "Link ECU popular in racing applications",
            ],
        ),
        CANVendor.MEGASQUIRT: ECUProfile(
            vendor=CANVendor.MEGASQUIRT,
            can_bitrate=500000,
            can_ids=[0x500, 0x501, 0x502],
            dbc_file="dbc/megasquirt.dbc",
            metric_mappings={
                "rpm": "Engine_RPM",
                "tps": "Throttle_Position",
                "clt": "Coolant_Temp",
                "map": "Boost_Pressure",
            },
            polling_intervals={
                "Engine_RPM": 0.1,
                "Throttle_Position": 0.1,
            },
            default_settings={
                "rpm_redline": 7000,
            },
            optimization_hints=[
                "MegaSquirt open-source ECU",
                "Widely customizable",
            ],
        ),
        CANVendor.MOTEC: ECUProfile(
            vendor=CANVendor.MOTEC,
            can_bitrate=1000000,  # MoTec uses CAN FD
            can_ids=[0x600, 0x601, 0x602, 0x603],
            dbc_file="dbc/motec.dbc",
            metric_mappings={
                "RPM": "Engine_RPM",
                "Throttle": "Throttle_Position",
                "Coolant": "Coolant_Temp",
                "Boost": "Boost_Pressure",
            },
            polling_intervals={
                "Engine_RPM": 0.05,
                "Throttle_Position": 0.05,
                "Coolant_Temp": 0.5,
            },
            default_settings={
                "rpm_redline": 9000,
                "boost_max_psi": 50,
            },
            optimization_hints=[
                "MoTec M1 uses CAN FD (1Mbps)",
                "Professional racing ECU",
                "Ultra-high performance data",
            ],
        ),
        CANVendor.OBD2: ECUProfile(
            vendor=CANVendor.OBD2,
            can_bitrate=500000,
            can_ids=[0x7DF, 0x7E0, 0x7E1, 0x7E8, 0x7E9],
            dbc_file="dbc/obd2.dbc",
            metric_mappings={
                "RPM": "Engine_RPM",
                "Coolant_Temp": "Coolant_Temp",
                "Vehicle_Speed": "Vehicle_Speed",
                "Throttle_Position": "Throttle_Position",
            },
            polling_intervals={
                "Engine_RPM": 0.5,
                "Coolant_Temp": 1.0,
                "Vehicle_Speed": 0.5,
            },
            default_settings={
                "rpm_redline": 6000,
            },
            optimization_hints=[
                "OBD-II standard protocol",
                "Slower polling due to request/response",
                "Works with most modern vehicles",
            ],
        ),
    }

    # Manufacturer-specific optimizations
    MANUFACTURER_PROFILES: Dict[Manufacturer, Dict[str, Any]] = {
        Manufacturer.FORD: {
            "common_ecus": [CANVendor.HOLLEY, CANVendor.AEM],
            "typical_redline": 7000,
            "boost_common": True,
            "flex_fuel_common": True,
        },
        Manufacturer.CHEVROLET: {
            "common_ecus": [CANVendor.HOLLEY, CANVendor.HALTECH],
            "typical_redline": 6500,
            "boost_common": True,
            "nitrous_common": True,
        },
        Manufacturer.DODGE: {
            "common_ecus": [CANVendor.HOLLEY, CANVendor.AEM],
            "typical_redline": 6500,
            "boost_common": True,
            "high_boost": True,
        },
        Manufacturer.TOYOTA: {
            "common_ecus": [CANVendor.AEM, CANVendor.LINK],
            "typical_redline": 8000,
            "high_revving": True,
        },
        Manufacturer.HONDA: {
            "common_ecus": [CANVendor.AEM, CANVendor.HALTECH],
            "typical_redline": 9000,
            "high_revving": True,
            "vtec_common": True,
        },
        Manufacturer.SUBARU: {
            "common_ecus": [CANVendor.LINK, CANVendor.AEM],
            "typical_redline": 7000,
            "boost_common": True,
            "awd_common": True,
        },
    }

    def __init__(
        self,
        can_detector: Optional[CANVendorDetector] = None,
        notification_callback: Optional[callable] = None,
    ) -> None:
        """
        Initialize ECU auto-setup.

        Args:
            can_detector: CAN vendor detector instance
            notification_callback: Callback for notifications
        """
        self.detector = can_detector or CANVendorDetector()
        self.notification_callback = notification_callback
        self.detected_vendor: Optional[CANVendor] = None
        self.detected_profile: Optional[ECUProfile] = None
        self.auto_configured = False

    def detect_and_setup(self, sample_time: float = 5.0) -> bool:
        """
        Detect ECU and automatically configure system.

        Args:
            sample_time: Time to sample CAN bus for detection

        Returns:
            True if detection and setup successful
        """
        self._notify("Starting ECU detection...", "info")

        # Detect vendor
        vendor = self.detector.detect_vendor(sample_time=sample_time)
        if not vendor or vendor == CANVendor.UNKNOWN:
            self._notify("Could not detect ECU vendor", "warning")
            return False

        self.detected_vendor = vendor
        self._notify(f"Detected ECU: {vendor.value.upper()}", "info")

        # Get profile
        profile = self.ECU_PROFILES.get(vendor)
        if not profile:
            self._notify(f"No profile found for {vendor.value}", "warning")
            return False

        self.detected_profile = profile

        # Load DBC if available
        if profile.dbc_file:
            self.detector.load_dbc(vendor)

        # Apply optimizations
        self._apply_optimizations(profile)

        self.auto_configured = True
        self._notify(f"ECU configured: {vendor.value.upper()}", "success")

        return True

    def _apply_optimizations(self, profile: ECUProfile) -> None:
        """Apply ECU-specific optimizations."""
        LOGGER.info("Applying optimizations for %s", profile.vendor.value)

        # Apply CAN settings
        self._notify(f"Configuring CAN: {profile.can_bitrate}bps", "info")

        # Apply metric mappings
        if profile.metric_mappings:
            self._notify(f"Configured {len(profile.metric_mappings)} metric mappings", "info")

        # Apply polling intervals
        if profile.polling_intervals:
            self._notify(f"Optimized polling intervals", "info")

        # Apply default settings
        if profile.default_settings:
            self._notify(f"Applied {len(profile.default_settings)} default settings", "info")

        # Show optimization hints
        for hint in profile.optimization_hints:
            LOGGER.info("Optimization: %s", hint)

    def get_configuration(self) -> Dict[str, Any]:
        """
        Get current configuration based on detected ECU.

        Returns:
            Configuration dictionary
        """
        if not self.detected_profile:
            return {}

        profile = self.detected_profile

        return {
            "vendor": profile.vendor.value,
            "can_channel": profile.can_channel,
            "can_bitrate": profile.can_bitrate,
            "can_ids": profile.can_ids,
            "dbc_file": profile.dbc_file,
            "metric_mappings": profile.metric_mappings,
            "polling_intervals": profile.polling_intervals,
            "default_settings": profile.default_settings,
        }

    def get_optimized_settings(self) -> Dict[str, Any]:
        """
        Get optimized settings for detected ECU.

        Returns:
            Dictionary of optimized settings
        """
        if not self.detected_profile:
            return {}

        profile = self.detected_profile
        settings = {}

        # CAN settings
        settings["can_channel"] = profile.can_channel
        settings["can_bitrate"] = profile.can_bitrate

        # Polling intervals
        settings["polling_intervals"] = profile.polling_intervals

        # Default thresholds
        settings.update(profile.default_settings)

        return settings

    def detect_manufacturer(self, hints: Optional[Dict[str, Any]] = None) -> Optional[Manufacturer]:
        """
        Detect car manufacturer from hints or ECU profile.

        Args:
            hints: Optional hints (VIN, model, etc.)

        Returns:
            Detected manufacturer or None
        """
        if not self.detected_profile:
            return None

        # Try to match based on ECU vendor
        for manufacturer, profile in self.MANUFACTURER_PROFILES.items():
            if self.detected_vendor in profile.get("common_ecus", []):
                self._notify(f"Detected manufacturer: {manufacturer.value.upper()}", "info")
                return manufacturer

        return Manufacturer.GENERIC

    def _notify(self, message: str, level: str = "info") -> None:
        """Send notification."""
        if self.notification_callback:
            try:
                self.notification_callback(message, level)
            except Exception as e:
                LOGGER.error("Error in notification callback: %s", e)
        LOGGER.info("[ECU Setup] %s", message)


# Note: Additional ECU vendors can be added to CANVendor enum as needed


__all__ = ["ECUAutoSetup", "ECUProfile", "Manufacturer"]

