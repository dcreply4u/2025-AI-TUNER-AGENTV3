"""
Multi-ECU Detection & Intelligence System
Detects multiple ECUs, piggyback systems, OEM ECUs, and conflicts
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

try:
    import can
    CAN_AVAILABLE = True
except ImportError:
    CAN_AVAILABLE = False
    can = None  # type: ignore

from services.can_vendor_detector import CANVendor, CANVendorDetector

LOGGER = logging.getLogger(__name__)


class ECUType(Enum):
    """ECU type classification."""
    STANDALONE = "standalone"  # Full replacement ECU
    PIGGYBACK = "piggyback"  # Intercepts/modifies signals
    OEM = "oem"  # Original equipment manufacturer
    TUNING_MODULE = "tuning_module"  # Performance tuning module
    UNKNOWN = "unknown"


class ECUConflictType(Enum):
    """Types of ECU conflicts."""
    NONE = "none"
    CAN_ID_COLLISION = "can_id_collision"  # Multiple ECUs using same CAN ID
    SIGNAL_INTERFERENCE = "signal_interference"  # Conflicting signals
    DUAL_CONTROL = "dual_control"  # Multiple ECUs trying to control same function
    PIGGYBACK_CONFLICT = "piggyback_conflict"  # Piggyback interfering with main ECU


@dataclass
class DetectedECU:
    """Detected ECU information."""
    ecu_id: str  # Unique identifier
    vendor: CANVendor
    ecu_type: ECUType
    can_ids: Set[int] = field(default_factory=set)
    can_bitrate: Optional[int] = None
    description: str = ""
    detected_at: float = field(default_factory=time.time)
    confidence: float = 0.0  # 0-1
    is_active: bool = True
    is_primary: bool = False  # Primary/controlling ECU
    message_rate: float = 0.0  # Messages per second
    signal_count: int = 0
    conflicts: List[ECUConflictType] = field(default_factory=list)
    metadata: Dict[str, any] = field(default_factory=dict)


@dataclass
class PiggybackSystem:
    """Detected piggyback system information."""
    name: str
    ecu_id: str
    can_ids: Set[int]
    intercepts_signals: List[str] = field(default_factory=list)
    modifies_signals: List[str] = field(default_factory=list)
    description: str = ""
    confidence: float = 0.0


class MultiECUDetector:
    """
    Advanced multi-ECU detection system.
    
    Features:
    - Detects multiple ECUs on CAN bus
    - Identifies piggyback systems (JB4, RaceChip, etc.)
    - Detects OEM ECUs
    - Identifies conflicts and interference
    - Monitors ECU activity
    """
    
    # Known piggyback system signatures
    PIGGYBACK_SIGNATURES = {
        "JB4": {
            "can_ids": {0x500, 0x501, 0x502},
            "description": "Burger Motorsports JB4",
            "intercepts": ["MAP", "TPS", "Boost"],
            "modifies": ["Fuel", "Ignition", "Boost"],
        },
        "RaceChip": {
            "can_ids": {0x510, 0x511},
            "description": "RaceChip Performance Module",
            "intercepts": ["MAP", "TPS"],
            "modifies": ["Boost", "Fuel"],
        },
        "Unichip": {
            "can_ids": {0x520, 0x521},
            "description": "Unichip Piggyback",
            "intercepts": ["MAP", "TPS", "RPM"],
            "modifies": ["Fuel", "Ignition"],
        },
        "APR": {
            "can_ids": {0x530},
            "description": "APR Tuning Module",
            "intercepts": ["MAP", "Boost"],
            "modifies": ["Boost", "Fuel"],
        },
        "Cobb": {
            "can_ids": {0x540, 0x541},
            "description": "Cobb Accessport",
            "intercepts": ["MAP", "TPS", "RPM"],
            "modifies": ["Fuel", "Ignition", "Boost"],
        },
    }
    
    # OEM ECU patterns (common CAN IDs)
    OEM_PATTERNS = {
        "BMW": {
            "can_ids": {0x12F, 0x130, 0x1A0, 0x1A6, 0x1D0, 0x1D2},
            "description": "BMW DME/ECU",
        },
        "Audi/VW": {
            "can_ids": {0x7E0, 0x7E1, 0x7E8, 0x7E9},
            "description": "Audi/VW ECU",
        },
        "Ford": {
            "can_ids": {0x7E0, 0x7E1, 0x7E8, 0x7E9},
            "description": "Ford PCM",
        },
        "GM": {
            "can_ids": {0x7E0, 0x7E1, 0x7E8, 0x7E9},
            "description": "GM ECM",
        },
        "Toyota": {
            "can_ids": {0x7E0, 0x7E1, 0x7E8, 0x7E9},
            "description": "Toyota ECU",
        },
        "Honda": {
            "can_ids": {0x7E0, 0x7E1, 0x7E8, 0x7E9},
            "description": "Honda ECU",
        },
    }
    
    def __init__(self, can_channel: str = "can0", bitrate: int = 500000):
        """
        Initialize multi-ECU detector.
        
        Args:
            can_channel: CAN bus channel
            bitrate: CAN bus bitrate
        """
        self.can_channel = can_channel
        self.bitrate = bitrate
        self.bus: Optional[can.interface.Bus] = None
        self.detected_ecus: List[DetectedECU] = []
        self.piggyback_systems: List[PiggybackSystem] = []
        self.can_vendor_detector = CANVendorDetector(can_channel=can_channel, bitrate=bitrate)
        self.detection_samples: List[Dict] = []
        self.message_stats: Dict[int, Dict] = {}  # CAN ID -> stats
    
    def detect_all_ecus(self, sample_time: float = 10.0) -> List[DetectedECU]:
        """
        Detect all ECUs on CAN bus.
        
        Args:
            sample_time: Time to sample CAN bus (seconds)
            
        Returns:
            List of detected ECUs
        """
        LOGGER.info("Starting multi-ECU detection (sample_time=%.1fs)...", sample_time)
        
        if not CAN_AVAILABLE:
            LOGGER.warning("CAN library not available")
            return []
        
        # Connect to CAN bus
        if not self._connect():
            return []
        
        # Sample CAN messages
        self._sample_can_messages(sample_time)
        
        # Detect standalone ECUs
        self._detect_standalone_ecus()
        
        # Detect piggyback systems
        self._detect_piggyback_systems()
        
        # Detect OEM ECUs
        self._detect_oem_ecus()
        
        # Analyze conflicts
        self._analyze_conflicts()
        
        # Determine primary ECU
        self._determine_primary_ecu()
        
        LOGGER.info("Multi-ECU detection complete: %d ECUs, %d piggybacks detected",
                   len(self.detected_ecus), len(self.piggyback_systems))
        
        return self.detected_ecus
    
    def _connect(self) -> bool:
        """Connect to CAN bus."""
        try:
            if self.bus:
                self.bus.shutdown()
            self.bus = can.interface.Bus(channel=self.can_channel, bustype="socketcan", bitrate=self.bitrate)
            return True
        except Exception as e:
            LOGGER.error("Failed to connect to CAN bus: %s", e)
            return False
    
    def _sample_can_messages(self, sample_time: float) -> None:
        """Sample CAN messages for analysis."""
        self.detection_samples = []
        self.message_stats = {}
        
        start_time = time.time()
        message_count = 0
        
        try:
            while time.time() - start_time < sample_time:
                try:
                    msg = self.bus.recv(timeout=0.1)
                    if msg:
                        can_id = msg.arbitration_id
                        
                        # Store sample
                        self.detection_samples.append({
                            "arbitration_id": can_id,
                            "data": msg.data,
                            "timestamp": time.time(),
                            "dlc": msg.dlc,
                        })
                        
                        # Update statistics
                        if can_id not in self.message_stats:
                            self.message_stats[can_id] = {
                                "count": 0,
                                "first_seen": time.time(),
                                "last_seen": time.time(),
                                "data_samples": [],
                            }
                        
                        stats = self.message_stats[can_id]
                        stats["count"] += 1
                        stats["last_seen"] = time.time()
                        if len(stats["data_samples"]) < 10:
                            stats["data_samples"].append(msg.data)
                        
                        message_count += 1
                except can.CanError:
                    continue
                except Exception as e:
                    LOGGER.debug("Error receiving CAN message: %s", e)
                    continue
        except Exception as e:
            LOGGER.error("Error sampling CAN messages: %s", e)
        finally:
            if self.bus:
                elapsed = time.time() - start_time
                LOGGER.info("Sampled %d CAN messages in %.2fs (%.1f msg/s)",
                           message_count, elapsed, message_count / elapsed if elapsed > 0 else 0)
    
    def _detect_standalone_ecus(self) -> None:
        """Detect standalone aftermarket ECUs."""
        # Use existing vendor detector
        detected_vendor = self.can_vendor_detector.detect_vendor(sample_time=0)  # Already sampled
        
        if detected_vendor and detected_vendor != CANVendor.UNKNOWN:
            # Get CAN IDs for this vendor
            signature = self.can_vendor_detector.VENDOR_SIGNATURES.get(detected_vendor)
            if signature:
                can_ids = set()
                for can_id in self.message_stats.keys():
                    if can_id in signature.can_ids:
                        can_ids.add(can_id)
                
                # Calculate message rate
                total_messages = sum(self.message_stats[cid]["count"] for cid in can_ids)
                sample_time = max(1.0, time.time() - min(s.get("first_seen", time.time()) for s in self.message_stats.values() if s))
                message_rate = total_messages / sample_time if sample_time > 0 else 0
                
                ecu = DetectedECU(
                    ecu_id=f"{detected_vendor.value}_primary",
                    vendor=detected_vendor,
                    ecu_type=ECUType.STANDALONE,
                    can_ids=can_ids,
                    can_bitrate=self.bitrate,
                    description=signature.description,
                    confidence=0.9,
                    is_active=True,
                    is_primary=True,
                    message_rate=message_rate,
                    signal_count=len(can_ids),
                )
                self.detected_ecus.append(ecu)
    
    def _detect_piggyback_systems(self) -> None:
        """Detect piggyback tuning systems."""
        detected_can_ids = set(self.message_stats.keys())
        
        for piggyback_name, signature in self.PIGGYBACK_SIGNATURES.items():
            piggyback_can_ids = signature["can_ids"]
            
            # Check if any piggyback CAN IDs are present
            matching_ids = detected_can_ids.intersection(piggyback_can_ids)
            
            if matching_ids:
                # Calculate confidence based on message count
                total_piggyback_messages = sum(
                    self.message_stats[cid]["count"] for cid in matching_ids
                )
                total_messages = sum(s["count"] for s in self.message_stats.values())
                confidence = min(0.95, total_piggyback_messages / max(1, total_messages * 0.01))
                
                if confidence > 0.3:  # Threshold for detection
                    piggyback = PiggybackSystem(
                        name=piggyback_name,
                        ecu_id=f"piggyback_{piggyback_name.lower()}",
                        can_ids=matching_ids,
                        intercepts_signals=signature["intercepts"],
                        modifies_signals=signature["modifies"],
                        description=signature["description"],
                        confidence=confidence,
                    )
                    self.piggyback_systems.append(piggyback)
                    
                    # Also add as detected ECU
                    ecu = DetectedECU(
                        ecu_id=piggyback.ecu_id,
                        vendor=CANVendor.GENERIC,
                        ecu_type=ECUType.PIGGYBACK,
                        can_ids=matching_ids,
                        description=piggyback.description,
                        confidence=confidence,
                        is_active=True,
                        is_primary=False,
                        message_rate=total_piggyback_messages / 10.0,  # Estimate
                        signal_count=len(matching_ids),
                        metadata={
                            "intercepts": signature["intercepts"],
                            "modifies": signature["modifies"],
                        }
                    )
                    self.detected_ecus.append(ecu)
    
    def _detect_oem_ecus(self) -> None:
        """Detect OEM ECUs."""
        detected_can_ids = set(self.message_stats.keys())
        
        for oem_name, pattern in self.OEM_PATTERNS.items():
            oem_can_ids = pattern["can_ids"]
            
            # Check for OBD-II patterns (common across OEMs)
            obd_ids = {0x7DF, 0x7E0, 0x7E1, 0x7E8, 0x7E9, 0x7EA}
            matching_ids = detected_can_ids.intersection(obd_ids)
            
            if matching_ids:
                # Check if this looks like OEM (not aftermarket)
                # OEM ECUs typically have lower message rates and specific patterns
                total_oem_messages = sum(
                    self.message_stats[cid]["count"] for cid in matching_ids
                )
                
                # OEM ECUs often have diagnostic/service messages
                has_diagnostic_pattern = any(
                    cid in {0x7DF, 0x7E0, 0x7E1} for cid in matching_ids
                )
                
                if has_diagnostic_pattern or total_oem_messages > 10:
                    confidence = min(0.85, total_oem_messages / max(1, len(self.detection_samples) * 0.1))
                    
                    ecu = DetectedECU(
                        ecu_id=f"oem_{oem_name.lower()}",
                        vendor=CANVendor.OBD2,
                        ecu_type=ECUType.OEM,
                        can_ids=matching_ids,
                        description=f"{oem_name} OEM ECU",
                        confidence=confidence,
                        is_active=True,
                        is_primary=False,  # OEM is usually not primary if aftermarket ECU present
                        message_rate=total_oem_messages / 10.0,
                        signal_count=len(matching_ids),
                        metadata={"manufacturer": oem_name},
                    )
                    self.detected_ecus.append(ecu)
    
    def _analyze_conflicts(self) -> None:
        """Analyze conflicts between detected ECUs."""
        # Check for CAN ID collisions
        can_id_usage: Dict[int, List[DetectedECU]] = {}
        for ecu in self.detected_ecus:
            for can_id in ecu.can_ids:
                if can_id not in can_id_usage:
                    can_id_usage[can_id] = []
                can_id_usage[can_id].append(ecu)
        
        # Identify collisions
        for can_id, ecus in can_id_usage.items():
            if len(ecus) > 1:
                # Multiple ECUs using same CAN ID
                for ecu in ecus:
                    ecu.conflicts.append(ECUConflictType.CAN_ID_COLLISION)
                    ecu.metadata["collision_with"] = [e.ecu_id for e in ecus if e != ecu]
        
        # Check for piggyback conflicts
        for piggyback in self.piggyback_systems:
            # Find standalone ECUs that might conflict
            for ecu in self.detected_ecus:
                if ecu.ecu_type == ECUType.STANDALONE:
                    # Check if piggyback intercepts signals that standalone controls
                    if any(signal in piggyback.intercepts_signals for signal in ["MAP", "TPS", "Boost"]):
                        ecu.conflicts.append(ECUConflictType.PIGGYBACK_CONFLICT)
                        ecu.metadata["piggyback_conflict"] = piggyback.name
        
        # Check for dual control (multiple ECUs trying to control same function)
        standalone_ecus = [e for e in self.detected_ecus if e.ecu_type == ECUType.STANDALONE]
        if len(standalone_ecus) > 1:
            for ecu in standalone_ecus:
                ecu.conflicts.append(ECUConflictType.DUAL_CONTROL)
                ecu.metadata["other_standalone_ecus"] = [e.ecu_id for e in standalone_ecus if e != ecu]
    
    def _determine_primary_ecu(self) -> None:
        """Determine which ECU is primary/controlling."""
        # Primary is usually the standalone ECU with highest message rate
        standalone_ecus = [e for e in self.detected_ecus if e.ecu_type == ECUType.STANDALONE]
        
        if standalone_ecus:
            # Primary is the one with highest message rate
            primary = max(standalone_ecus, key=lambda e: e.message_rate)
            primary.is_primary = True
            
            # Mark others as non-primary
            for ecu in standalone_ecus:
                if ecu != primary:
                    ecu.is_primary = False
    
    def get_conflict_summary(self) -> Dict[str, any]:
        """Get summary of detected conflicts."""
        conflicts = {
            "total_conflicts": 0,
            "can_id_collisions": 0,
            "piggyback_conflicts": 0,
            "dual_control": 0,
            "affected_ecus": [],
        }
        
        for ecu in self.detected_ecus:
            if ecu.conflicts:
                conflicts["total_conflicts"] += len(ecu.conflicts)
                conflicts["affected_ecus"].append(ecu.ecu_id)
                
                for conflict in ecu.conflicts:
                    if conflict == ECUConflictType.CAN_ID_COLLISION:
                        conflicts["can_id_collisions"] += 1
                    elif conflict == ECUConflictType.PIGGYBACK_CONFLICT:
                        conflicts["piggyback_conflicts"] += 1
                    elif conflict == ECUConflictType.DUAL_CONTROL:
                        conflicts["dual_control"] += 1
        
        return conflicts
    
    def get_recommendations(self) -> List[str]:
        """Get recommendations based on detected ECUs and conflicts."""
        recommendations = []
        
        # Check for conflicts
        conflicts = self.get_conflict_summary()
        if conflicts["total_conflicts"] > 0:
            if conflicts["can_id_collisions"] > 0:
                recommendations.append(
                    "WARNING: CAN ID collisions detected. Multiple ECUs using same CAN IDs. "
                    "This can cause communication errors."
                )
            if conflicts["piggyback_conflicts"] > 0:
                recommendations.append(
                    "WARNING: Piggyback system detected alongside standalone ECU. "
                    "Ensure piggyback is properly configured to avoid signal interference."
                )
            if conflicts["dual_control"] > 0:
                recommendations.append(
                    "WARNING: Multiple standalone ECUs detected. Only one should be active/controlling."
                )
        
        # Check for piggyback systems
        if self.piggyback_systems:
            recommendations.append(
                f"INFO: {len(self.piggyback_systems)} piggyback system(s) detected. "
                "Monitor for signal interference."
            )
        
        # Check for OEM ECU
        oem_ecus = [e for e in self.detected_ecus if e.ecu_type == ECUType.OEM]
        if oem_ecus:
            recommendations.append(
                f"INFO: OEM ECU detected. Ensure aftermarket ECU is properly configured "
                "to work with OEM systems."
            )
        
        # Primary ECU recommendation
        primary_ecus = [e for e in self.detected_ecus if e.is_primary]
        if primary_ecus:
            primary = primary_ecus[0]
            recommendations.append(
                f"Primary ECU: {primary.vendor.value.upper()} ({primary.description})"
            )
        
        return recommendations
    
    def shutdown(self) -> None:
        """Shutdown CAN bus connection."""
        if self.bus:
            try:
                self.bus.shutdown()
            except Exception:
                pass
            self.bus = None
















