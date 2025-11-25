from __future__ import annotations

import logging
import struct
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Mapping, MutableSequence, Optional

try:
    import can
except Exception:  # pragma: no cover - optional dependency
    can = None  # type: ignore

# Import ECU-specific decoders
try:
    from interfaces.ecu_can_decoders import (
        get_decoder,
        auto_detect_ecu_type,
        CANMessage as DecoderCANMessage,
        DecodedTelemetry,
    )
    ECU_DECODERS_AVAILABLE = True
except ImportError:
    ECU_DECODERS_AVAILABLE = False
    get_decoder = None  # type: ignore
    auto_detect_ecu_type = None  # type: ignore

LOGGER = logging.getLogger(__name__)


@dataclass
class EMSDecoder:
    """Simple container for arbitration-id specific decoder callbacks."""

    arbitration_id: int
    parser: Callable[[bytes], Mapping[str, float]]


def _default_decoders() -> Dict[int, EMSDecoder]:
    return {
        0x100: EMSDecoder(0x100, lambda data: {"rpm": struct.unpack(">H", data[0:2])[0]}),
        0x101: EMSDecoder(0x101, lambda data: {"throttle": data[0]}),
        0x102: EMSDecoder(
            0x102, lambda data: {"coolant_temp": struct.unpack(">H", data[0:2])[0] / 10.0}
        ),
    }


class EMSDataInterface:
    """
    SocketCAN reader that decodes EMS frames and streams dict payloads.
    
    Supports multiple ECU systems via CAN bus:
    - Holley EFI (HEFI 3rd Party CAN Protocol)
    - MoTeC (M1/M150 CAN Protocol)
    - AEM (AEMNet Protocol)
    - Haltech (CAN Protocol)
    - Link ECU, MegaSquirt, OBD-II, and more
    """

    def __init__(
        self,
        can_interface: str = "can0",
        bitrate: int = 500_000,
        decoders: Optional[Iterable[EMSDecoder]] = None,
        auto_configure: bool = True,
        ecu_type: Optional[str] = None,
        auto_detect_ecu: bool = True,
    ) -> None:
        self.can_interface = can_interface
        self.bitrate = bitrate
        self.decoders = {decoder.arbitration_id: decoder for decoder in (decoders or _default_decoders().values())}
        self.auto_configure = auto_configure
        self.bus: "can.BusABC | None" = None
        self.listeners: MutableSequence[Callable[[Mapping[str, float]], None]] = []
        self.running = False
        self._stop_event = threading.Event()
        
        # ECU-specific decoder support
        self.ecu_type = ecu_type
        self.auto_detect_ecu = auto_detect_ecu
        self.ecu_decoder = None
        if ECU_DECODERS_AVAILABLE and ecu_type and get_decoder:
            try:
                self.ecu_decoder = get_decoder(ecu_type)
                LOGGER.info("Using ECU decoder for: %s", ecu_type)
            except Exception as e:
                LOGGER.warning("Failed to load ECU decoder: %s", e)
        
        # Buffer for auto-detection
        self._recent_messages: MutableSequence["can.Message"] = []
        self._max_recent_messages = 100

    def setup_can_interface(self) -> None:
        if not can:
            raise RuntimeError("python-can is required for EMSDataInterface.")
        if sys.platform.startswith("linux") and self.auto_configure:
            cmds = [
                ["sudo", "ip", "link", "set", self.can_interface, "down"],
                [
                    "sudo",
                    "ip",
                    "link",
                    "set",
                    self.can_interface,
                    "type",
                    "can",
                    "bitrate",
                    str(self.bitrate),
                ],
                ["sudo", "ip", "link", "set", self.can_interface, "up"],
            ]
            for cmd in cmds:
                try:
                    subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception as exc:
                    LOGGER.warning("Failed to execute %s: %s", cmd, exc)
        self.bus = can.interface.Bus(self.can_interface, bustype="socketcan")

    def add_listener(self, callback: Callable[[Mapping[str, float]], None]) -> None:
        self.listeners.append(callback)

    def decode_message(self, message: "can.Message") -> Mapping[str, float]:
        """Decode CAN message using available decoders."""
        # Try ECU-specific decoder first
        if self.ecu_decoder and ECU_DECODERS_AVAILABLE:
            try:
                decoder_msg = DecoderCANMessage(
                    arbitration_id=message.arbitration_id,
                    data=message.data,
                    timestamp=message.timestamp or time.time(),
                )
                decoded = self.ecu_decoder.decode(decoder_msg)
                if decoded:
                    # Convert DecodedTelemetry to dict
                    result = {}
                    if decoded.rpm is not None:
                        result["rpm"] = decoded.rpm
                    if decoded.throttle_position is not None:
                        result["throttle"] = decoded.throttle_position
                    if decoded.coolant_temp is not None:
                        result["coolant_temp"] = decoded.coolant_temp
                    if decoded.oil_pressure is not None:
                        result["oil_pressure"] = decoded.oil_pressure
                    if decoded.boost_psi is not None:
                        result["boost_psi"] = decoded.boost_psi
                    if decoded.afr is not None:
                        result["afr"] = decoded.afr
                    if decoded.ignition_timing is not None:
                        result["ignition_timing"] = decoded.ignition_timing
                    if decoded.vehicle_speed is not None:
                        result["vehicle_speed"] = decoded.vehicle_speed
                    if result:
                        return result
            except Exception as exc:
                LOGGER.debug("ECU decoder failed for 0x%X: %s", message.arbitration_id, exc)
        
        # Fallback to standard decoder
        decoder = self.decoders.get(message.arbitration_id)
        if not decoder:
            return {}
        try:
            return decoder.parser(message.data)
        except Exception as exc:
            LOGGER.error("Failed to decode message 0x%X: %s", message.arbitration_id, exc)
            return {}
    
    def detect_ecu_type(self) -> Optional[str]:
        """
        Auto-detect ECU type from CAN messages.
        
        Returns:
            Detected ECU type or None
        """
        if not ECU_DECODERS_AVAILABLE or not auto_detect_ecu_type:
            return None
        
        if not self._recent_messages:
            return None
        
        try:
            decoder_messages = [
                DecoderCANMessage(
                    arbitration_id=msg.arbitration_id,
                    data=msg.data,
                    timestamp=msg.timestamp or time.time(),
                )
                for msg in self._recent_messages
            ]
            detected = auto_detect_ecu_type(decoder_messages)
            if detected:
                LOGGER.info("Auto-detected ECU type: %s", detected)
                self.ecu_type = detected
                if get_decoder:
                    self.ecu_decoder = get_decoder(detected)
            return detected
        except Exception as e:
            LOGGER.warning("ECU auto-detection failed: %s", e)
            return None

    def run(self) -> None:
        if not self.bus:
            self.setup_can_interface()
        if not self.bus:
            LOGGER.error("CAN bus not initialized; aborting EMSDataInterface run loop.")
            return

        self.running = True
        self._stop_event.clear()
        LOGGER.info("Listening on %s (%s bps)", self.can_interface, self.bitrate)
        
        # Auto-detect ECU if enabled and not already set
        if self.auto_detect_ecu and not self.ecu_type and ECU_DECODERS_AVAILABLE:
            LOGGER.info("Auto-detecting ECU type...")
            detection_timeout = time.time() + 5.0  # 5 second detection window
        
        try:
            while not self._stop_event.is_set():
                message = self.bus.recv(timeout=1)
                if not message:
                    continue
                
                # Store recent messages for auto-detection
                if self.auto_detect_ecu and not self.ecu_type:
                    self._recent_messages.append(message)
                    if len(self._recent_messages) > self._max_recent_messages:
                        self._recent_messages.pop(0)
                    
                    # Try detection after collecting some messages
                    if time.time() < detection_timeout and len(self._recent_messages) >= 10:
                        self.detect_ecu_type()
                
                data = self.decode_message(message)
                if data:
                    for callback in self.listeners:
                        callback(data)
                time.sleep(0.005)
        except KeyboardInterrupt:
            LOGGER.info("EMSDataInterface stopped by user.")
        finally:
            self.running = False

    def stop(self) -> None:
        self._stop_event.set()


__all__ = ["EMSDataInterface", "EMSDecoder"]


