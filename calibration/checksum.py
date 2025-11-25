"""Checksum calculation utilities for calibration files."""

from __future__ import annotations

import zlib
from typing import BinaryIO


def calculate_crc32(data: bytes | bytearray | BinaryIO) -> int:
    """
    Calculate CRC32 checksum for calibration data.

    Args:
        data: Binary data or file-like object

    Returns:
        32-bit CRC32 value
    """
    if isinstance(data, (bytes, bytearray)):
        return zlib.crc32(data) & 0xFFFFFFFF
    else:
        content = data.read()
        return zlib.crc32(content) & 0xFFFFFFFF


def verify_checksum(data: bytes | bytearray, expected_checksum: int, offset: int = -4) -> bool:
    """
    Verify checksum embedded in calibration data.

    Args:
        data: Calibration binary data
        expected_checksum: Expected checksum value (or None to extract from data)
        offset: Offset where checksum is stored (negative = from end)

    Returns:
        True if checksum matches
    """
    if offset < 0:
        offset = len(data) + offset

    embedded_checksum = int.from_bytes(data[offset:offset + 4], byteorder="little")
    calculated = calculate_crc32(data[:offset])
    return embedded_checksum == calculated


__all__ = ["calculate_crc32", "verify_checksum"]

