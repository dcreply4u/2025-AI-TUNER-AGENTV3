"""
CAN Vendor Detection Service

Automatically detects CAN bus vendor IDs and configures vendor-specific
data logging and interpretation.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set

try:
    import can
    import cantools
except ImportError:
    can = None  # type: ignore
    cantools = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class CANVendor(Enum):
    """Known CAN bus vendors."""

    HOLLEY = "holley"
    HALTECH = "haltech"
    AEM = "aem"
    LINK = "link"
    MEGASQUIRT = "megasquirt"
    MOTEC = "motec"
    EMTRON = "emtron"
    FUELTECH = "fueltech"
    RACECAPTURE = "racecapture"
    OBD2 = "obd2"
    GENERIC = "generic"
    UNKNOWN = "unknown"


@dataclass
class VendorSignature:
    """Vendor identification signature."""

    vendor: CANVendor
    can_ids: Set[int]  # Characteristic CAN IDs
    frame_patterns: Dict[int, bytes]  # Expected frame patterns
    dbc_file: Optional[str] = None  # DBC file path for this vendor
    description: str = ""


class CANVendorDetector:
    """Detects CAN bus vendor and configures vendor-specific logging."""

    # Vendor signatures - known CAN IDs and patterns (extended)
    VENDOR_SIGNATURES = {
        CANVendor.HOLLEY: VendorSignature(
            vendor=CANVendor.HOLLEY,
            can_ids={0x180, 0x181, 0x182, 0x183, 0x184, 0x185, 0x186, 0x187},
            frame_patterns={},
            dbc_file="dbc/holley.dbc",
            description="Holley EFI",
        ),
        CANVendor.HALTECH: VendorSignature(
            vendor=CANVendor.HALTECH,
            can_ids={0x200, 0x201, 0x202, 0x203, 0x204, 0x205, 0x206, 0x207},
            frame_patterns={},
            dbc_file="dbc/haltech.dbc",
            description="Haltech ECU",
        ),
        CANVendor.AEM: VendorSignature(
            vendor=CANVendor.AEM,
            can_ids={0x300, 0x301, 0x302, 0x303, 0x304, 0x305},
            frame_patterns={},
            dbc_file="dbc/aem.dbc",
            description="AEM Infinity",
        ),
        CANVendor.LINK: VendorSignature(
            vendor=CANVendor.LINK,
            can_ids={0x400, 0x401, 0x402},
            frame_patterns={},
            dbc_file="dbc/link.dbc",
            description="Link ECU",
        ),
        CANVendor.MEGASQUIRT: VendorSignature(
            vendor=CANVendor.MEGASQUIRT,
            can_ids={0x500, 0x501, 0x502},
            frame_patterns={},
            dbc_file="dbc/megasquirt.dbc",
            description="MegaSquirt",
        ),
        CANVendor.MOTEC: VendorSignature(
            vendor=CANVendor.MOTEC,
            can_ids={0x600, 0x601, 0x602, 0x603},
            frame_patterns={},
            dbc_file="dbc/motec.dbc",
            description="MoTec M1",
        ),
        CANVendor.EMTRON: VendorSignature(
            vendor=CANVendor.EMTRON,
            can_ids={0x700, 0x701, 0x702},
            frame_patterns={},
            dbc_file="dbc/emtron.dbc",
            description="Emtron ECU",
        ),
        CANVendor.FUELTECH: VendorSignature(
            vendor=CANVendor.FUELTECH,
            can_ids={0x800, 0x801, 0x802},
            frame_patterns={},
            dbc_file="dbc/fueltech.dbc",
            description="FuelTech",
        ),
        CANVendor.RACECAPTURE: VendorSignature(
            vendor=CANVendor.RACECAPTURE,
            can_ids={0x100, 0x101, 0x102},
            frame_patterns={},
            dbc_file="dbc/racecapture.dbc",
            description="RaceCapture Pro",
        ),
        CANVendor.OBD2: VendorSignature(
            vendor=CANVendor.OBD2,
            can_ids={0x7DF, 0x7E0, 0x7E1, 0x7E8, 0x7E9, 0x7EA, 0x7EB},
            frame_patterns={},
            dbc_file="dbc/obd2.dbc",
            description="OBD-II",
        ),
    }

    def __init__(
        self,
        can_channel: str = "can0",
        bitrate: int = 500000,
        dbc_dir: str = "dbc",
        notification_callback: Optional[Callable[[str, str], None]] = None,
    ) -> None:
        """
        Initialize CAN vendor detector.

        Args:
            can_channel: CAN interface (e.g., "can0")
            bitrate: CAN bus bitrate
            dbc_dir: Directory containing DBC files
            notification_callback: Optional callback for notifications (message, level)
        """
        self.notification_callback = notification_callback
        self.enabled = True
        
        if can is None:
            self.enabled = False
            msg = "CAN vendor detection unavailable: python-can not installed"
            LOGGER.warning(msg)
            if notification_callback:
                notification_callback(msg, "warning")

        self.can_channel = can_channel
        self.bitrate = bitrate
        self.dbc_dir = Path(dbc_dir)
        self.dbc_dir.mkdir(parents=True, exist_ok=True)

        self.bus: Optional["can.Bus"] = None
        self.detected_vendor: Optional[CANVendor] = None
        self.dbc_database: Optional["cantools.database.Database"] = None
        self.detection_samples: List[Dict] = []
        self._detection_timeout = 5.0  # Seconds to sample for detection

    def detect_vendor(self, sample_time: float = 5.0) -> Optional[CANVendor]:
        """
        Detect CAN bus vendor by sampling messages.

        Args:
            sample_time: Time in seconds to sample CAN messages

        Returns:
            Detected vendor or None if detection failed
        """
        if not self.enabled:
            return None
            
        if not self._connect():
            if self.notification_callback:
                self.notification_callback(f"CAN vendor detection: Could not connect to {self.can_channel}", "warning")
            return None

        self._detection_timeout = sample_time
        self.detection_samples = []
        start_time = time.time()

        LOGGER.info("Sampling CAN bus for vendor detection...")

        try:
            while time.time() - start_time < sample_time:
                try:
                    msg = self.bus.recv(timeout=0.1)
                    if msg:
                        self.detection_samples.append(
                            {
                                "arbitration_id": msg.arbitration_id,
                                "data": msg.data,
                                "timestamp": msg.timestamp,
                            }
                        )
                except can.CanError:
                    continue
        except Exception as e:
            LOGGER.error("Error during vendor detection: %s", e)
            return None

        # Analyze samples to identify vendor
        self.detected_vendor = self._identify_vendor()
        return self.detected_vendor

    def _connect(self) -> bool:
        """Connect to CAN bus."""
        try:
            if self.bus:
                self.bus.shutdown()
            self.bus = can.interface.Bus(channel=self.can_channel, bustype="socketcan", bitrate=self.bitrate)
            return True
        except Exception as e:
            LOGGER.error("Failed to connect to CAN bus %s: %s", self.can_channel, e)
            return False

    def _identify_vendor(self) -> Optional[CANVendor]:
        """Identify vendor from sampled CAN messages with enhanced pattern matching."""
        if not self.detection_samples:
            return CANVendor.UNKNOWN

        # Count CAN IDs and analyze patterns
        can_id_counts: Dict[int, int] = {}
        can_id_patterns: Dict[int, List[bytes]] = {}
        
        for sample in self.detection_samples:
            can_id = sample["arbitration_id"]
            can_id_counts[can_id] = can_id_counts.get(can_id, 0) + 1
            
            # Store data patterns
            if can_id not in can_id_patterns:
                can_id_patterns[can_id] = []
            can_id_patterns[can_id].append(sample["data"])

        # Check for OBD-II patterns first (common across all vehicles)
        obd_ids = {0x7DF, 0x7E0, 0x7E1, 0x7E8, 0x7E9}
        obd_count = sum(can_id_counts.get(cid, 0) for cid in obd_ids)
        if obd_count > len(self.detection_samples) * 0.1:  # At least 10% OBD-II messages
            LOGGER.info("Detected OBD-II protocol (%.1f%% of messages)", (obd_count / len(self.detection_samples)) * 100)
            return CANVendor.OBD2

        # Match against vendor signatures with enhanced scoring
        best_match = None
        best_score = 0

        for vendor, signature in self.VENDOR_SIGNATURES.items():
            if vendor == CANVendor.OBD2:
                continue  # Already checked
            
            score = 0
            matched_ids = 0
            total_signature_ids = len(signature.can_ids) if signature.can_ids else 1

            for can_id in can_id_counts.keys():
                if can_id in signature.can_ids:
                    matched_ids += 1
                    # Weight by frequency and importance
                    frequency = can_id_counts[can_id]
                    score += frequency * (1.0 + (frequency / len(self.detection_samples)))

            # Score based on:
            # 1. Number of matching IDs (coverage)
            # 2. Match ratio (how many of vendor's IDs we see)
            # 3. Message frequency (confidence)
            if matched_ids > 0:
                match_ratio = matched_ids / total_signature_ids
                coverage_score = matched_ids / len(can_id_counts) if can_id_counts else 0
                
                # Combined score favors vendors with high match ratio and good coverage
                combined_score = (score * match_ratio) + (coverage_score * 100)

                if combined_score > best_score:
                    best_score = combined_score
                    best_match = vendor

        if best_match and best_score > 5.0:  # Minimum confidence threshold
            LOGGER.info("Detected CAN vendor: %s (score: %.2f, confidence: %.1f%%)", 
                       best_match.value, best_score, 
                       min(100, (best_score / 50.0) * 100))
            return best_match

        # If we have CAN traffic but can't identify, use generic
        if len(can_id_counts) > 0:
            LOGGER.warning("Could not identify CAN vendor (saw %d unique IDs), using generic", len(can_id_counts))
            return CANVendor.GENERIC

        LOGGER.warning("No CAN traffic detected")
        return CANVendor.UNKNOWN

    def load_dbc(self, vendor: Optional[CANVendor] = None) -> bool:
        """
        Load DBC file for detected or specified vendor.

        Args:
            vendor: Vendor to load DBC for (uses detected vendor if None)

        Returns:
            True if DBC loaded successfully
        """
        if cantools is None:
            LOGGER.warning("cantools not available, DBC parsing disabled")
            return False

        target_vendor = vendor or self.detected_vendor
        if not target_vendor:
            LOGGER.error("No vendor specified or detected")
            return False

        signature = self.VENDOR_SIGNATURES.get(target_vendor)
        if not signature or not signature.dbc_file:
            LOGGER.warning("No DBC file specified for vendor: %s", target_vendor.value)
            return False

        dbc_path = self.dbc_dir / Path(signature.dbc_file).name
        if not dbc_path.exists():
            LOGGER.warning("DBC file not found: %s", dbc_path)
            return False

        try:
            self.dbc_database = cantools.database.load_file(str(dbc_path))
            LOGGER.info("Loaded DBC file: %s", dbc_path)
            return True
        except Exception as e:
            LOGGER.error("Failed to load DBC file %s: %s", dbc_path, e)
            return False

    def decode_message(self, can_id: int, data: bytes) -> Optional[Dict]:
        """
        Decode CAN message using loaded DBC.

        Args:
            can_id: CAN arbitration ID
            data: CAN message data

        Returns:
            Decoded message data or None if decoding failed
        """
        if not self.dbc_database:
            return None

        try:
            message = self.dbc_database.get_message_by_frame_id(can_id)
            decoded = message.decode(data)
            return {
                "name": message.name,
                "signals": decoded,
                "can_id": can_id,
            }
        except Exception:
            return None

    def get_vendor_info(self) -> Dict:
        """Get information about detected vendor."""
        if not self.detected_vendor:
            return {"vendor": "unknown", "description": "No vendor detected"}

        signature = self.VENDOR_SIGNATURES.get(self.detected_vendor)
        return {
            "vendor": self.detected_vendor.value,
            "description": signature.description if signature else "",
            "dbc_loaded": self.dbc_database is not None,
            "samples_collected": len(self.detection_samples),
        }

    def close(self) -> None:
        """Close CAN bus connection."""
        if self.bus:
            self.bus.shutdown()
            self.bus = None


__all__ = ["CANVendorDetector", "CANVendor", "VendorSignature"]

