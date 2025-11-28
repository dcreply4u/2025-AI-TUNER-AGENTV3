"""
CAN Bus Simulator Service

Provides CAN bus simulation capabilities using python-can's virtual interface:
- Virtual CAN bus creation
- Message generation from DBC files
- Periodic message transmission
- Event-driven message simulation
- Integration with cantools for DBC-based message encoding
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Set

try:
    import can
    CAN_AVAILABLE = True
except ImportError:
    CAN_AVAILABLE = False
    can = None  # type: ignore

try:
    import cantools
    CANTOOLS_AVAILABLE = True
except ImportError:
    CANTOOLS_AVAILABLE = False
    cantools = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class MessageType(Enum):
    """Message transmission type."""
    PERIODIC = "periodic"  # Send at regular intervals
    ON_DEMAND = "on_demand"  # Send when requested
    EVENT_DRIVEN = "event_driven"  # Send on trigger


@dataclass
class SimulatedMessage:
    """Configuration for a simulated CAN message."""
    message_name: str  # Name from DBC or custom name
    can_id: int
    data: bytes = field(default_factory=lambda: bytes(8))
    period: float = 0.1  # Period in seconds (for periodic messages)
    enabled: bool = True
    message_type: MessageType = MessageType.PERIODIC
    signal_values: Dict[str, float] = field(default_factory=dict)  # For DBC-based encoding
    dbc_database: Optional[str] = None  # DBC database name if using DBC
    last_sent: float = field(default_factory=time.time)
    send_count: int = 0


class CANSimulator:
    """CAN bus simulator using python-can virtual interface."""
    
    def __init__(
        self,
        channel: str = "vcan0",
        bitrate: int = 500000,
        dbc_decoder: Optional["CANDecoder"] = None,
    ):
        """
        Initialize CAN simulator.
        
        Args:
            channel: Virtual CAN channel name (default: "vcan0")
            bitrate: CAN bitrate (default: 500000)
            dbc_decoder: Optional CANDecoder instance for DBC-based encoding
        """
        if not CAN_AVAILABLE:
            raise RuntimeError("python-can required. Install with: pip install python-can")
        
        self.channel = channel
        self.bitrate = bitrate
        self.dbc_decoder = dbc_decoder
        
        # Virtual CAN bus
        self.bus: Optional["can.Bus"] = None
        
        # Simulated messages
        self.messages: Dict[str, SimulatedMessage] = {}
        self.messages_lock = threading.Lock()
        
        # Simulation state
        self.running = False
        self.simulator_thread: Optional[threading.Thread] = None
        
        # Statistics
        self.total_sent = 0
        self.start_time: Optional[float] = None
    
    def create_virtual_bus(self) -> bool:
        """
        Create a virtual CAN bus interface.
        
        Returns:
            True if created successfully
        """
        try:
            # Try to use virtual interface (works on all platforms)
            self.bus = can.interface.Bus(
                bustype="virtual",
                channel=self.channel,
                bitrate=self.bitrate,
            )
            LOGGER.info(f"Created virtual CAN bus: {self.channel} @ {self.bitrate} bps")
            return True
        except Exception as e:
            LOGGER.error(f"Failed to create virtual CAN bus: {e}")
            # Fallback: try socketcan vcan (Linux only)
            if hasattr(can.interface, 'Bus'):
                try:
                    self.bus = can.interface.Bus(
                        bustype="socketcan",
                        channel=self.channel,
                        bitrate=self.bitrate,
                    )
                    LOGGER.info(f"Created socketcan virtual bus: {self.channel}")
                    return True
                except Exception as e2:
                    LOGGER.error(f"Failed to create socketcan virtual bus: {e2}")
            return False
    
    def add_message(
        self,
        message_name: str,
        can_id: int,
        data: Optional[bytes] = None,
        period: float = 0.1,
        message_type: MessageType = MessageType.PERIODIC,
        signal_values: Optional[Dict[str, float]] = None,
        dbc_database: Optional[str] = None,
    ) -> bool:
        """
        Add a message to simulate.
        
        Args:
            message_name: Name identifier for the message
            can_id: CAN ID
            data: Raw data bytes (if not using DBC)
            period: Period in seconds for periodic messages
            message_type: Message transmission type
            signal_values: Signal values for DBC-based encoding
            dbc_database: DBC database name if using DBC
        
        Returns:
            True if added successfully
        """
        if data is None:
            data = bytes(8)
        
        if signal_values is None:
            signal_values = {}
        
        msg = SimulatedMessage(
            message_name=message_name,
            can_id=can_id,
            data=data,
            period=period,
            message_type=message_type,
            signal_values=signal_values,
            dbc_database=dbc_database,
        )
        
        with self.messages_lock:
            self.messages[message_name] = msg
        
        LOGGER.info(f"Added simulated message: {message_name} (ID: 0x{can_id:X})")
        return True
    
    def add_dbc_message(
        self,
        message_name: str,
        signal_values: Dict[str, float],
        period: float = 0.1,
        dbc_database: Optional[str] = None,
    ) -> bool:
        """
        Add a message from DBC file.
        
        Args:
            message_name: Message name from DBC
            signal_values: Dictionary of signal names to values
            period: Period in seconds
            dbc_database: DBC database name (uses active if None)
        
        Returns:
            True if added successfully
        """
        if not self.dbc_decoder or not CANTOOLS_AVAILABLE:
            LOGGER.error("DBC decoder not available")
            return False
        
        # Get message info from DBC
        db_name = dbc_database or self.dbc_decoder.get_active_database()
        if not db_name:
            LOGGER.error("No active DBC database")
            return False
        
        # Encode message
        encoded_data = self.dbc_decoder.encode_message(message_name, signal_values, db_name)
        if encoded_data is None:
            LOGGER.error(f"Failed to encode message: {message_name}")
            return False
        
        # Get CAN ID from DBC
        messages = self.dbc_decoder.list_messages(db_name)
        can_id = None
        for msg_info in messages:
            if msg_info["name"] == message_name:
                can_id = msg_info["can_id"]
                break
        
        if can_id is None:
            LOGGER.error(f"Message not found in DBC: {message_name}")
            return False
        
        return self.add_message(
            message_name=message_name,
            can_id=can_id,
            data=encoded_data,
            period=period,
            message_type=MessageType.PERIODIC,
            signal_values=signal_values,
            dbc_database=db_name,
        )
    
    def update_message_signals(
        self,
        message_name: str,
        signal_values: Dict[str, float],
    ) -> bool:
        """
        Update signal values for a DBC-based message.
        
        Args:
            message_name: Message name
            signal_values: Updated signal values
        
        Returns:
            True if updated successfully
        """
        with self.messages_lock:
            if message_name not in self.messages:
                return False
            
            msg = self.messages[message_name]
            
            # Update signal values
            msg.signal_values.update(signal_values)
            
            # Re-encode if using DBC
            if msg.dbc_database and self.dbc_decoder:
                encoded_data = self.dbc_decoder.encode_message(
                    message_name,
                    msg.signal_values,
                    msg.dbc_database,
                )
                if encoded_data:
                    msg.data = encoded_data
            
            return True
    
    def remove_message(self, message_name: str) -> bool:
        """Remove a simulated message."""
        with self.messages_lock:
            if message_name in self.messages:
                del self.messages[message_name]
                LOGGER.info(f"Removed simulated message: {message_name}")
                return True
            return False
    
    def enable_message(self, message_name: str) -> bool:
        """Enable a simulated message."""
        with self.messages_lock:
            if message_name in self.messages:
                self.messages[message_name].enabled = True
                return True
            return False
    
    def disable_message(self, message_name: str) -> bool:
        """Disable a simulated message."""
        with self.messages_lock:
            if message_name in self.messages:
                self.messages[message_name].enabled = False
                return True
            return False
    
    def send_message(self, message_name: str) -> bool:
        """
        Send a message on demand.
        
        Args:
            message_name: Message name to send
        
        Returns:
            True if sent successfully
        """
        if not self.bus:
            return False
        
        with self.messages_lock:
            if message_name not in self.messages:
                return False
            
            msg = self.messages[message_name]
        
        try:
            can_msg = can.Message(
                arbitration_id=msg.can_id,
                data=msg.data,
                is_extended_id=False,
            )
            self.bus.send(can_msg)
            msg.last_sent = time.time()
            msg.send_count += 1
            self.total_sent += 1
            return True
        except Exception as e:
            LOGGER.error(f"Failed to send message {message_name}: {e}")
            return False
    
    def start(self) -> bool:
        """Start the CAN simulator."""
        if self.running:
            return True
        
        if not self.bus:
            if not self.create_virtual_bus():
                return False
        
        self.running = True
        self.start_time = time.time()
        self.simulator_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.simulator_thread.start()
        LOGGER.info("CAN simulator started")
        return True
    
    def stop(self) -> None:
        """Stop the CAN simulator."""
        self.running = False
        
        if self.simulator_thread:
            self.simulator_thread.join(timeout=2)
        
        if self.bus:
            self.bus.shutdown()
            self.bus = None
        
        LOGGER.info("CAN simulator stopped")
    
    def _simulation_loop(self) -> None:
        """Main simulation loop for periodic messages."""
        while self.running:
            try:
                now = time.time()
                
                with self.messages_lock:
                    messages_to_send = []
                    for msg in self.messages.values():
                        if not msg.enabled or msg.message_type != MessageType.PERIODIC:
                            continue
                        
                        if now - msg.last_sent >= msg.period:
                            messages_to_send.append(msg.message_name)
                
                # Send messages outside the lock
                for msg_name in messages_to_send:
                    self.send_message(msg_name)
                
                # Sleep to avoid busy-waiting
                time.sleep(0.01)  # 10ms resolution
                
            except Exception as e:
                LOGGER.error(f"Error in simulation loop: {e}")
                time.sleep(0.1)
    
    def get_statistics(self) -> Dict:
        """Get simulator statistics."""
        runtime = time.time() - self.start_time if self.start_time else 0
        messages_per_second = self.total_sent / runtime if runtime > 0 else 0
        
        with self.messages_lock:
            enabled_count = sum(1 for msg in self.messages.values() if msg.enabled)
            total_messages = len(self.messages)
        
        return {
            "total_sent": self.total_sent,
            "runtime_seconds": runtime,
            "messages_per_second": messages_per_second,
            "enabled_messages": enabled_count,
            "total_messages": total_messages,
            "channel": self.channel,
            "running": self.running,
        }
    
    def list_messages(self) -> List[Dict]:
        """List all configured messages."""
        with self.messages_lock:
            return [
                {
                    "name": msg.message_name,
                    "can_id": msg.can_id,
                    "can_id_hex": hex(msg.can_id),
                    "period": msg.period,
                    "enabled": msg.enabled,
                    "message_type": msg.message_type.value,
                    "send_count": msg.send_count,
                    "dbc_database": msg.dbc_database,
                }
                for msg in self.messages.values()
            ]


__all__ = ["CANSimulator", "SimulatedMessage", "MessageType"]

