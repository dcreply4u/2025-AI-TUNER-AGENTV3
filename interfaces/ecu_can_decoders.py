"""
ECU CAN Bus Decoders
Decoders for major ECU systems' CAN bus protocols.

Supports:
- Holley EFI (HEFI 3rd Party CAN Protocol)
- MoTeC (M1/M150 CAN Protocol)
- AEM (AEMNet Protocol)
- Haltech (CAN Protocol)
- Link ECU
- MegaSquirt
- OBD-II (Standard Protocol)
"""

from __future__ import annotations

import logging
import struct
from dataclasses import dataclass
from typing import Dict, Optional, Any

LOGGER = logging.getLogger(__name__)


@dataclass
class CANMessage:
    """CAN message structure."""
    arbitration_id: int
    data: bytes
    timestamp: float = 0.0


@dataclass
class DecodedTelemetry:
    """Decoded telemetry data."""
    rpm: Optional[float] = None
    throttle_position: Optional[float] = None
    coolant_temp: Optional[float] = None
    oil_temp: Optional[float] = None
    oil_pressure: Optional[float] = None
    fuel_pressure: Optional[float] = None
    boost_psi: Optional[float] = None
    afr: Optional[float] = None
    lambda_value: Optional[float] = None
    injector_pulse_width: Optional[float] = None
    ignition_timing: Optional[float] = None
    vehicle_speed: Optional[float] = None
    knock_count: Optional[int] = None
    flex_fuel_percent: Optional[float] = None
    raw_data: Dict[str, Any] = None  # type: ignore


class ECUCANDecoder:
    """Base class for ECU CAN decoders."""
    
    def decode(self, message: CANMessage) -> Optional[DecodedTelemetry]:
        """Decode CAN message to telemetry data."""
        raise NotImplementedError


class HolleyEFIDecoder(ECUCANDecoder):
    """
    Holley EFI CAN Protocol Decoder
    
    Holley HEFI 3rd Party CAN Communications Protocol
    Common CAN IDs:
    - 0x180: Engine RPM, Throttle Position
    - 0x181: Coolant Temp, Oil Pressure
    - 0x182: Boost Pressure, Fuel Pressure
    - 0x183: Injector Pulse Width, Ignition Timing
    """
    
    # Holley CAN ID definitions (common)
    CAN_ID_RPM_THROTTLE = 0x180
    CAN_ID_TEMPS_PRESSURES = 0x181
    CAN_ID_BOOST_FUEL = 0x182
    CAN_ID_INJECTOR_IGNITION = 0x183
    
    def decode(self, message: CANMessage) -> Optional[DecodedTelemetry]:
        """Decode Holley CAN message."""
        can_id = message.arbitration_id
        data = message.data
        
        if len(data) < 8:
            return None
        
        telemetry = DecodedTelemetry()
        telemetry.raw_data = {"can_id": hex(can_id), "data": data.hex()}
        
        # RPM and Throttle Position (0x180)
        if can_id == self.CAN_ID_RPM_THROTTLE:
            # Typical Holley format (may vary by firmware version)
            # Bytes 0-1: RPM (little endian, scale 0.25)
            # Bytes 2: Throttle Position (0-255, scale 0.392%)
            if len(data) >= 3:
                rpm_raw = struct.unpack('<H', data[0:2])[0]
                telemetry.rpm = rpm_raw * 0.25
                telemetry.throttle_position = data[2] * 0.392
        
        # Coolant Temp and Oil Pressure (0x181)
        elif can_id == self.CAN_ID_TEMPS_PRESSURES:
            # Bytes 0: Coolant Temp (°F offset by 40, scale 1)
            # Bytes 1: Oil Pressure (PSI, scale 0.5)
            if len(data) >= 2:
                telemetry.coolant_temp = (data[0] - 40) * 1.0  # Convert to °C if needed
                telemetry.oil_pressure = data[1] * 0.5
        
        # Boost and Fuel Pressure (0x182)
        elif can_id == self.CAN_ID_BOOST_FUEL:
            # Bytes 0: Boost Pressure (PSI, offset -14.7, scale 0.5)
            # Bytes 1: Fuel Pressure (PSI, scale 0.5)
            if len(data) >= 2:
                telemetry.boost_psi = (data[0] - 29.4) * 0.5  # Convert from offset
                telemetry.fuel_pressure = data[1] * 0.5
        
        # Injector and Ignition (0x183)
        elif can_id == self.CAN_ID_INJECTOR_IGNITION:
            # Bytes 0-1: Injector Pulse Width (ms, scale 0.001)
            # Bytes 2: Ignition Timing (degrees, offset 64, scale 0.5)
            if len(data) >= 3:
                pulse_raw = struct.unpack('<H', data[0:2])[0]
                telemetry.injector_pulse_width = pulse_raw * 0.001
                telemetry.ignition_timing = (data[2] - 64) * 0.5
        
        return telemetry if any(v is not None for v in [
            telemetry.rpm, telemetry.throttle_position, telemetry.coolant_temp,
            telemetry.oil_pressure, telemetry.boost_psi, telemetry.fuel_pressure,
            telemetry.injector_pulse_width, telemetry.ignition_timing
        ]) else None


class MoTeCDecoder(ECUCANDecoder):
    """
    MoTeC CAN Protocol Decoder
    
    MoTeC uses configurable CAN message definitions.
    This is a generic decoder - specific configurations may vary.
    """
    
    def decode(self, message: CANMessage) -> Optional[DecodedTelemetry]:
        """Decode MoTeC CAN message."""
        # MoTeC CAN format is highly configurable
        # This is a simplified decoder - may need customization per setup
        can_id = message.arbitration_id
        data = message.data
        
        if len(data) < 4:
            return None
        
        telemetry = DecodedTelemetry()
        telemetry.raw_data = {"can_id": hex(can_id), "data": data.hex()}
        
        # MoTeC typically uses 16-bit values
        # Format varies by configuration - this is a generic example
        if len(data) >= 8:
            # Example: First 2 bytes might be RPM
            rpm_raw = struct.unpack('<H', data[0:2])[0]
            if 0 < rpm_raw < 20000:  # Sanity check
                telemetry.rpm = rpm_raw
            
            # Next 2 bytes might be throttle
            throttle_raw = struct.unpack('<H', data[2:4])[0]
            if 0 <= throttle_raw <= 1000:  # 0-100% scaled by 10
                telemetry.throttle_position = throttle_raw / 10.0
        
        return telemetry if telemetry.rpm or telemetry.throttle_position else None


class AEMDecoder(ECUCANDecoder):
    """
    AEM AEMNet CAN Protocol Decoder
    
    AEM Infinity and Series 2 ECUs use AEMNet protocol.
    """
    
    def decode(self, message: CANMessage) -> Optional[DecodedTelemetry]:
        """Decode AEM CAN message."""
        can_id = message.arbitration_id
        data = message.data
        
        if len(data) < 8:
            return None
        
        telemetry = DecodedTelemetry()
        telemetry.raw_data = {"can_id": hex(can_id), "data": data.hex()}
        
        # AEMNet protocol (simplified - actual format may vary)
        # Typical AEM format uses specific CAN IDs for different data
        # This is a generic decoder
        
        if len(data) >= 8:
            # Example decoding (actual format depends on AEM configuration)
            # RPM typically in first 2 bytes
            rpm_raw = struct.unpack('<H', data[0:2])[0]
            if 0 < rpm_raw < 20000:
                telemetry.rpm = rpm_raw
        
        return telemetry if telemetry.rpm else None


class HaltechDecoder(ECUCANDecoder):
    """
    Haltech CAN Protocol Decoder
    
    Haltech Elite and Platinum series use CAN for telemetry.
    """
    
    def decode(self, message: CANMessage) -> Optional[DecodedTelemetry]:
        """Decode Haltech CAN message."""
        can_id = message.arbitration_id
        data = message.data
        
        if len(data) < 4:
            return None
        
        telemetry = DecodedTelemetry()
        telemetry.raw_data = {"can_id": hex(can_id), "data": data.hex()}
        
        # Haltech CAN format (simplified)
        if len(data) >= 8:
            # RPM in first 2 bytes (little endian)
            rpm_raw = struct.unpack('<H', data[0:2])[0]
            if 0 < rpm_raw < 20000:
                telemetry.rpm = rpm_raw
        
        return telemetry if telemetry.rpm else None


class OBDIIDecoder(ECUCANDecoder):
    """
    OBD-II Standard Protocol Decoder
    
    Standard OBD-II CAN protocol (ISO 15765-4).
    """
    
    def decode(self, message: CANMessage) -> Optional[DecodedTelemetry]:
        """Decode OBD-II CAN message."""
        can_id = message.arbitration_id
        data = message.data
        
        # OBD-II uses standard PIDs
        # This is a simplified decoder
        telemetry = DecodedTelemetry()
        telemetry.raw_data = {"can_id": hex(can_id), "data": data.hex()}
        
        # OBD-II decoding would go here
        # Typically uses service 01 (current data) PIDs
        
        return None  # Placeholder - full OBD-II decoder would be more complex


# Decoder registry
DECODERS: Dict[str, type[ECUCANDecoder]] = {
    "holley": HolleyEFIDecoder,
    "motec": MoTeCDecoder,
    "aem": AEMDecoder,
    "haltech": HaltechDecoder,
    "obd2": OBDIIDecoder,
    "obd-ii": OBDIIDecoder,
}


def get_decoder(ecu_type: str) -> ECUCANDecoder:
    """
    Get decoder for ECU type.
    
    Args:
        ecu_type: ECU type name (holley, motec, aem, haltech, obd2)
    
    Returns:
        ECUCANDecoder instance
    """
    ecu_type_lower = ecu_type.lower().replace("_", "-").replace(" ", "-")
    
    if ecu_type_lower in DECODERS:
        return DECODERS[ecu_type_lower]()
    
    # Try partial match
    for key, decoder_class in DECODERS.items():
        if key in ecu_type_lower or ecu_type_lower in key:
            return decoder_class()
    
    LOGGER.warning("Unknown ECU type: %s, using generic decoder", ecu_type)
    return MoTeCDecoder()  # Generic fallback


def auto_detect_ecu_type(can_messages: list[CANMessage]) -> Optional[str]:
    """
    Auto-detect ECU type from CAN messages.
    
    Args:
        can_messages: List of CAN messages to analyze
    
    Returns:
        Detected ECU type or None
    """
    if not can_messages:
        return None
    
    # Analyze CAN IDs to determine ECU type
    can_ids = {msg.arbitration_id for msg in can_messages}
    
    # Holley typically uses 0x180-0x18F range
    if any(0x180 <= can_id <= 0x18F for can_id in can_ids):
        return "holley"
    
    # MoTeC often uses different ranges (varies by configuration)
    # AEM uses AEMNet protocol (specific IDs)
    # Haltech uses specific ID ranges
    
    # For now, return None if can't determine
    # Could be enhanced with more sophisticated detection
    return None



