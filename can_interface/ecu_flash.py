"""ECU flash manager for reading and writing ECU memory via CAN/UDS."""

from __future__ import annotations

import logging
from typing import BinaryIO

try:
    import can
except ImportError:
    can = None  # type: ignore

from interfaces.obd_interface import OBDInterface

LOGGER = logging.getLogger(__name__)


class ECUFlashManager:
    """
    Manages ECU memory read/write operations via CAN/UDS.

    Supports both direct CAN bus access and OBD-II/UDS protocols.
    """

    def __init__(
        self,
        channel: str = "can0",
        bustype: str = "socketcan",
        use_uds: bool = True,
    ) -> None:
        """
        Initialize ECU flash manager.

        Args:
            channel: CAN channel name
            bustype: CAN bus type (socketcan, slcan, etc.)
            use_uds: Whether to use UDS protocol for advanced operations
        """
        self.channel = channel
        self.bustype = bustype
        self.use_uds = use_uds
        self.bus: "can.Bus | None" = None
        self.uds_manager = None
        self._connected = False

        if use_uds:
            try:
                # Import UDS manager if available
                import sys
                import os
                parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                uds_path = os.path.join(parent_dir, "CAN and UDS Communication", "uds_manager.py")
                if os.path.exists(uds_path):
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("uds_manager", uds_path)
                    uds_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(uds_module)
                    self.uds_manager = uds_module.UDSManager(channel=channel, bitrate=500000)
                    LOGGER.info("UDS manager initialized")
            except Exception as e:
                LOGGER.warning("UDS manager not available: %s", e)

    def connect(self) -> bool:
        """Connect to CAN bus."""
        if not can:
            LOGGER.error("python-can not installed")
            return False

        try:
            self.bus = can.interface.Bus(channel=self.channel, bustype=self.bustype)
            self._connected = True
            LOGGER.info("Connected to CAN bus: %s", self.channel)
            return True
        except Exception as e:
            LOGGER.error("Failed to connect to CAN bus: %s", e)
            self._connected = False
            return False

    def is_connected(self) -> bool:
        """Check if connected to CAN bus."""
        return self._connected and self.bus is not None

    def read_ecu(self, start_addr: int, size: int) -> bytes:
        """
        Read ECU memory at specified address.

        Args:
            start_addr: Starting address (hex)
            size: Number of bytes to read

        Returns:
            Binary data from ECU
        """
        if not self.is_connected() and not self.connect():
            raise RuntimeError("Not connected to CAN bus")

        if self.uds_manager:
            # Use UDS ReadMemoryByAddress (0x23)
            try:
                data = self.uds_manager.read_memory_by_address(start_addr, size)
                if data:
                    return bytes(data)
            except Exception as e:
                LOGGER.warning("UDS read failed, falling back to CAN: %s", e)

        # Fallback: Direct CAN read (simplified - actual implementation depends on ECU protocol)
        # This is a placeholder - real implementation would send CAN frames
        LOGGER.warning("Direct CAN read not fully implemented - returning empty data")
        return b"\x00" * size

    def write_ecu(self, start_addr: int, data: bytes | BinaryIO) -> bool:
        """
        Write data to ECU memory.

        Args:
            start_addr: Starting address (hex)
            data: Binary data to write

        Returns:
            True if successful
        """
        if isinstance(data, (bytes, bytearray)):
            bin_data = data
        else:
            bin_data = data.read()

        if not self.is_connected() and not self.connect():
            raise RuntimeError("Not connected to CAN bus")

        if self.uds_manager:
            # Use UDS WriteMemoryByAddress (0x3D)
            try:
                result = self.uds_manager.write_memory_by_address(start_addr, bin_data)
                if result:
                    LOGGER.info("ECU write successful via UDS: %d bytes at 0x%X", len(bin_data), start_addr)
                    return True
            except Exception as e:
                LOGGER.warning("UDS write failed, falling back to CAN: %s", e)

        # Fallback: Direct CAN write (simplified)
        LOGGER.warning("Direct CAN write not fully implemented")
        return False

    def close(self) -> None:
        """Close CAN bus connection."""
        if self.bus:
            self.bus.shutdown()
            self.bus = None
        self._connected = False
        if self.uds_manager:
            try:
                self.uds_manager.close()
            except Exception:
                pass


__all__ = ["ECUFlashManager"]

