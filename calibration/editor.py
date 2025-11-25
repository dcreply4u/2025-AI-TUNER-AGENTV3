"""Calibration binary editor with map modification and checksum support."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import BinaryIO, Sequence

from .checksum import calculate_crc32, verify_checksum

LOGGER = logging.getLogger(__name__)


class CalibrationEditor:
    """
    Editor for ECU calibration binary files.

    Supports map modification, checksum calculation, and safe binary editing.
    """

    def __init__(self, bin_data: bytes | bytearray | BinaryIO) -> None:
        """
        Initialize calibration editor.

        Args:
            bin_data: Calibration binary data or file-like object
        """
        if isinstance(bin_data, (bytes, bytearray)):
            self.data = bytearray(bin_data)
        else:
            self.data = bytearray(bin_data.read())
        self.original_checksum = calculate_crc32(self.data)
        LOGGER.info("Calibration editor initialized: %d bytes, CRC32: %08X", len(self.data), self.original_checksum)

    def modify_map(self, offset: int, values: Sequence[int]) -> None:
        """
        Modify calibration map at specified offset.

        Args:
            offset: Starting byte offset
            values: List of byte values to write
        """
        if offset < 0 or offset + len(values) > len(self.data):
            raise ValueError(f"Offset {offset} or size {len(values)} out of bounds")

        for i, val in enumerate(values):
            if not 0 <= val <= 255:
                raise ValueError(f"Value {val} out of byte range (0-255)")
            self.data[offset + i] = val

        LOGGER.info("Map modified at offset 0x%X: %d bytes", offset, len(values))

    def read_map(self, offset: int, size: int) -> bytes:
        """
        Read calibration map at specified offset.

        Args:
            offset: Starting byte offset
            size: Number of bytes to read

        Returns:
            Binary data
        """
        if offset < 0 or offset + size > len(self.data):
            raise ValueError(f"Offset {offset} or size {size} out of bounds")
        return bytes(self.data[offset:offset + size])

    def save(self, path: str | Path, update_checksum: bool = True, checksum_offset: int = -4) -> None:
        """
        Save calibration to file with optional checksum update.

        Args:
            path: Output file path
            update_checksum: Whether to update embedded checksum
            checksum_offset: Offset where checksum is stored (negative = from end)
        """
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if update_checksum and checksum_offset < 0:
            checksum_offset = len(self.data) + checksum_offset
            new_checksum = calculate_crc32(self.data[:checksum_offset])
            self.data[checksum_offset:checksum_offset + 4] = new_checksum.to_bytes(4, byteorder="little")
            LOGGER.info("Checksum updated: %08X", new_checksum)

        output_path.write_bytes(self.data)
        final_checksum = calculate_crc32(self.data)
        LOGGER.info("Calibration saved: %s (%d bytes, CRC32: %08X)", output_path, len(self.data), final_checksum)

    def verify(self, checksum_offset: int = -4) -> bool:
        """
        Verify calibration checksum.

        Args:
            checksum_offset: Offset where checksum is stored

        Returns:
            True if checksum is valid
        """
        return verify_checksum(self.data, 0, checksum_offset)

    def get_size(self) -> int:
        """Get calibration file size in bytes."""
        return len(self.data)


__all__ = ["CalibrationEditor"]

