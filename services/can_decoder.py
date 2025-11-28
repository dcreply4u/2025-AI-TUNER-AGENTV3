"""
CAN Message Decoder Service using cantools

Provides comprehensive CAN message decoding using DBC files:
- DBC file loading and management
- Message decoding with signal extraction
- Signal value scaling and unit conversion
- Support for multiple DBC files
- Message encoding for sending
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import cantools
    CANTOOLS_AVAILABLE = True
except ImportError:
    CANTOOLS_AVAILABLE = False
    cantools = None  # type: ignore

from interfaces.can_interface import CANMessage

LOGGER = logging.getLogger(__name__)


class DecodedSignal:
    """Decoded CAN signal with metadata."""
    
    def __init__(
        self,
        name: str,
        value: float,
        raw_value: int,
        unit: Optional[str] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        choices: Optional[Dict[int, str]] = None,
    ):
        self.name = name
        self.value = value
        self.raw_value = raw_value
        self.unit = unit or ""
        self.min_value = min_value
        self.max_value = max_value
        self.choices = choices or {}
        self.choice_string = choices.get(int(value)) if choices else None
    
    def __repr__(self) -> str:
        if self.choice_string:
            return f"{self.name}={self.choice_string} ({self.value})"
        unit_str = f" {self.unit}" if self.unit else ""
        return f"{self.name}={self.value:.3f}{unit_str}"


class DecodedMessage:
    """Decoded CAN message with signals."""
    
    def __init__(
        self,
        message_name: str,
        can_id: int,
        signals: List[DecodedSignal],
        timestamp: float,
        channel: str,
        is_extended: bool = False,
    ):
        self.message_name = message_name
        self.can_id = can_id
        self.signals = signals
        self.timestamp = timestamp
        self.channel = channel
        self.is_extended = is_extended
    
    def get_signal(self, name: str) -> Optional[DecodedSignal]:
        """Get a signal by name."""
        for signal in self.signals:
            if signal.name == name:
                return signal
        return None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "message_name": self.message_name,
            "can_id": hex(self.can_id),
            "can_id_decimal": self.can_id,
            "timestamp": self.timestamp,
            "channel": self.channel,
            "is_extended": self.is_extended,
            "signals": {
                sig.name: {
                    "value": sig.value,
                    "raw_value": sig.raw_value,
                    "unit": sig.unit,
                    "choice": sig.choice_string,
                }
                for sig in self.signals
            },
        }


class CANDecoder:
    """CAN message decoder using cantools DBC files."""
    
    def __init__(self):
        """Initialize CAN decoder."""
        if not CANTOOLS_AVAILABLE:
            LOGGER.warning("cantools not available. Install with: pip install cantools")
        
        self.databases: Dict[str, "cantools.database.Database"] = {}
        self.active_database: Optional[str] = None
        self.message_cache: Dict[int, Tuple[str, "cantools.database.Message"]] = {}
    
    def load_dbc(self, dbc_path: str, name: Optional[str] = None) -> bool:
        """
        Load a DBC file.
        
        Args:
            dbc_path: Path to DBC file
            name: Optional name for this database (defaults to filename)
        
        Returns:
            True if loaded successfully
        """
        if not CANTOOLS_AVAILABLE:
            LOGGER.error("cantools not available")
            return False
        
        dbc_path_obj = Path(dbc_path)
        if not dbc_path_obj.exists():
            LOGGER.error(f"DBC file not found: {dbc_path}")
            return False
        
        try:
            database = cantools.database.load_file(str(dbc_path))
            db_name = name or dbc_path_obj.stem
            self.databases[db_name] = database
            
            # Build message cache for this database
            for message in database.messages:
                self.message_cache[message.frame_id] = (db_name, message)
            
            # Set as active if first database
            if self.active_database is None:
                self.active_database = db_name
            
            LOGGER.info(f"Loaded DBC file: {dbc_path} ({len(database.messages)} messages)")
            return True
        
        except Exception as e:
            LOGGER.error(f"Failed to load DBC file {dbc_path}: {e}")
            return False
    
    def unload_dbc(self, name: str) -> bool:
        """
        Unload a DBC database.
        
        Args:
            name: Database name
        
        Returns:
            True if unloaded successfully
        """
        if name not in self.databases:
            return False
        
        # Remove from cache
        to_remove = [
            can_id for can_id, (db_name, _) in self.message_cache.items()
            if db_name == name
        ]
        for can_id in to_remove:
            del self.message_cache[can_id]
        
        del self.databases[name]
        
        # Reset active database if needed
        if self.active_database == name:
            self.active_database = next(iter(self.databases.keys())) if self.databases else None
        
        LOGGER.info(f"Unloaded DBC database: {name}")
        return True
    
    def set_active_database(self, name: str) -> bool:
        """
        Set the active database for decoding.
        
        Args:
            name: Database name
        
        Returns:
            True if set successfully
        """
        if name not in self.databases:
            LOGGER.error(f"Database not found: {name}")
            return False
        
        self.active_database = name
        LOGGER.info(f"Active DBC database set to: {name}")
        return True
    
    def decode_message(self, can_msg: CANMessage) -> Optional[DecodedMessage]:
        """
        Decode a CAN message using loaded DBC files.
        
        Args:
            can_msg: CAN message to decode
        
        Returns:
            Decoded message or None if not found
        """
        if not CANTOOLS_AVAILABLE or not self.message_cache:
            return None
        
        can_id = can_msg.arbitration_id
        
        # Check cache first
        if can_id not in self.message_cache:
            return None
        
        db_name, message = self.message_cache[can_id]
        
        try:
            # Decode using cantools
            decoded_signals = message.decode(can_msg.data)
            
            # Convert to DecodedSignal objects
            signals = []
            for signal_name, value in decoded_signals.items():
                signal = message.get_signal_by_name(signal_name)
                if signal:
                    # Get raw value (need to extract from data)
                    raw_value = self._extract_raw_signal_value(
                        can_msg.data,
                        signal.start,
                        signal.length,
                        signal.byte_order == "big_endian",
                        signal.is_signed,
                    )
                    
                    signals.append(DecodedSignal(
                        name=signal_name,
                        value=value,
                        raw_value=raw_value,
                        unit=signal.unit,
                        min_value=signal.minimum,
                        max_value=signal.maximum,
                        choices=signal.choices,
                    ))
            
            return DecodedMessage(
                message_name=message.name,
                can_id=can_id,
                signals=signals,
                timestamp=can_msg.timestamp,
                channel=can_msg.channel,
                is_extended=message.is_extended_frame,
            )
        
        except Exception as e:
            LOGGER.debug(f"Failed to decode CAN ID 0x{can_id:X}: {e}")
            return None
    
    def _extract_raw_signal_value(
        self,
        data: bytes,
        start_bit: int,
        length: int,
        big_endian: bool,
        is_signed: bool,
    ) -> int:
        """Extract raw signal value from data bytes."""
        # Simplified extraction - cantools handles this internally
        # This is a fallback for display purposes
        try:
            start_byte = start_bit // 8
            start_bit_in_byte = start_bit % 8
            
            if big_endian:
                # Motorola/Big Endian
                value = 0
                bits_remaining = length
                current_bit = start_bit_in_byte
                current_byte = start_byte
                
                while bits_remaining > 0:
                    bits_in_this_byte = min(8 - current_bit, bits_remaining)
                    mask = ((1 << bits_in_this_byte) - 1) << current_bit
                    byte_value = (data[current_byte] & mask) >> current_bit
                    value |= byte_value << (length - bits_remaining)
                    bits_remaining -= bits_in_this_byte
                    current_bit = 0
                    current_byte += 1
            else:
                # Intel/Little Endian
                value = 0
                bits_remaining = length
                current_bit = start_bit_in_byte
                current_byte = start_byte
                shift = 0
                
                while bits_remaining > 0:
                    bits_in_this_byte = min(8 - current_bit, bits_remaining)
                    mask = ((1 << bits_in_this_byte) - 1) << current_bit
                    byte_value = (data[current_byte] & mask) >> current_bit
                    value |= byte_value << shift
                    shift += bits_in_this_byte
                    bits_remaining -= bits_in_this_byte
                    current_bit = 0
                    current_byte += 1
            
            # Apply sign extension if needed
            if is_signed and value & (1 << (length - 1)):
                value -= (1 << length)
            
            return value
        
        except Exception:
            return 0
    
    def encode_message(
        self,
        message_name: str,
        signals: Dict[str, float],
        database_name: Optional[str] = None,
    ) -> Optional[bytes]:
        """
        Encode a CAN message from signal values.
        
        Args:
            message_name: Name of the message in DBC
            signals: Dictionary of signal names to values
            database_name: Optional database name (uses active if None)
        
        Returns:
            Encoded data bytes or None
        """
        if not CANTOOLS_AVAILABLE:
            return None
        
        db_name = database_name or self.active_database
        if db_name not in self.databases:
            return None
        
        database = self.databases[db_name]
        
        try:
            message = database.get_message_by_name(message_name)
            encoded_data = message.encode(signals)
            return encoded_data
        except Exception as e:
            LOGGER.error(f"Failed to encode message {message_name}: {e}")
            return None
    
    def get_message_info(self, can_id: int) -> Optional[Dict]:
        """
        Get information about a CAN message.
        
        Args:
            can_id: CAN ID
        
        Returns:
            Message information dictionary or None
        """
        if can_id not in self.message_cache:
            return None
        
        db_name, message = self.message_cache[can_id]
        
        return {
            "name": message.name,
            "can_id": can_id,
            "can_id_hex": hex(can_id),
            "length": message.length,
            "is_extended": message.is_extended_frame,
            "database": db_name,
            "signals": [
                {
                    "name": sig.name,
                    "start": sig.start,
                    "length": sig.length,
                    "unit": sig.unit or "",
                    "min": sig.minimum,
                    "max": sig.maximum,
                }
                for sig in message.signals
            ],
            "comment": message.comment or "",
        }
    
    def list_messages(self, database_name: Optional[str] = None) -> List[Dict]:
        """
        List all messages in a database.
        
        Args:
            database_name: Optional database name (uses active if None)
        
        Returns:
            List of message information dictionaries
        """
        if not CANTOOLS_AVAILABLE:
            return []
        
        db_name = database_name or self.active_database
        if db_name not in self.databases:
            return []
        
        database = self.databases[db_name]
        messages = []
        
        for message in database.messages:
            messages.append({
                "name": message.name,
                "can_id": message.frame_id,
                "can_id_hex": hex(message.frame_id),
                "length": message.length,
                "is_extended": message.is_extended_frame,
                "signal_count": len(message.signals),
            })
        
        return sorted(messages, key=lambda x: x["can_id"])
    
    def list_databases(self) -> List[str]:
        """List all loaded database names."""
        return list(self.databases.keys())
    
    def get_active_database(self) -> Optional[str]:
        """Get the active database name."""
        return self.active_database


__all__ = ["CANDecoder", "DecodedMessage", "DecodedSignal"]

