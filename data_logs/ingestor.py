from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Protocol, Sequence


class SupportedProtocol(str, Enum):
    CAN = "CAN"
    CAN_FD = "CAN-FD"
    SERIAL = "Serial"
    ANALOG = "Analog"
    UNKNOWN = "Unknown"


@dataclass
class ParsedLogSession:
    vendor: str
    source_file: Path
    protocol: SupportedProtocol
    channels: Sequence[str]
    records: List[Dict[str, float]]
    metadata: Dict[str, str]


class DataLogParser(Protocol):
    name: str
    supported_extensions: Sequence[str]

    def sniff(self, sample: str) -> float:
        """Return confidence score between 0.0 and 1.0."""

    def parse(self, path: Path) -> ParsedLogSession:
        ...


def _infer_protocol(headers: Sequence[str], sample: str) -> SupportedProtocol:
    lowered = " ".join(headers + list(sample.splitlines()[:3])).lower()
    if "can-fd" in lowered or "can fd" in lowered:
        return SupportedProtocol.CAN_FD
    if any(keyword in lowered for keyword in ("can id", "arbitration", "can bus")):
        return SupportedProtocol.CAN
    if any(keyword in lowered for keyword in ("rs232", "serial", "com port")):
        return SupportedProtocol.SERIAL
    if any(keyword in lowered for keyword in ("analog", "voltage", "thermistor")):
        return SupportedProtocol.ANALOG
    return SupportedProtocol.UNKNOWN


def _safe_float(value: str) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class _CSVLogParser:
    """Shared helpers for CSV-based vendor logs."""

    vendor_marker: str = ""
    name: str = ""
    supported_extensions: Sequence[str] = (".csv",)

    def sniff(self, sample: str) -> float:
        return 0.9 if self.vendor_marker and self.vendor_marker.lower() in sample.lower() else 0.2

    def parse(self, path: Path) -> ParsedLogSession:
        text = path.read_text(errors="ignore")
        reader = csv.DictReader(text.splitlines())
        headers = reader.fieldnames or []
        records: List[Dict[str, float]] = []
        for row in reader:
            cleaned: Dict[str, float] = {}
            for key, value in row.items():
                if value is None or key is None:
                    continue
                numeric = _safe_float(value)
                if numeric is None:
                    continue
                cleaned[key.strip()] = numeric
            if cleaned:
                records.append(cleaned)
        protocol = _infer_protocol(headers, text)
        return ParsedLogSession(
            vendor=self.name,
            source_file=path,
            protocol=protocol,
            channels=headers,
            records=records,
            metadata={"records": str(len(records))},
        )


class HolleyDataLogParser(_CSVLogParser):
    name = "Holley EFI"
    vendor_marker = "holley"
    supported_extensions = (".csv", ".vpr", ".hpl")


class HaltechDataLogParser(_CSVLogParser):
    name = "Haltech"
    vendor_marker = "haltech"
    supported_extensions = (".csv", ".dat")


class MotecDataLogParser(_CSVLogParser):
    name = "MoTeC"
    vendor_marker = "motec"
    supported_extensions = (".csv", ".ld", ".mdat")


class GenericJSONParser:
    name = "Generic JSON"
    supported_extensions = (".json",)

    def sniff(self, sample: str) -> float:
        stripped = sample.strip()
        return 0.7 if stripped.startswith("{") or stripped.startswith("[") else 0.0

    def parse(self, path: Path) -> ParsedLogSession:
        payload = json.loads(path.read_text())
        records: List[Dict[str, float]] = []
        channels: List[str] = []
        if isinstance(payload, list):
            for entry in payload:
                if isinstance(entry, dict):
                    cleaned = {
                        str(key): float(value)
                        for key, value in entry.items()
                        if isinstance(value, (int, float))
                    }
                    if cleaned:
                        records.append(cleaned)
        elif isinstance(payload, dict):
            channels = list(payload.keys())
        if records and not channels:
            channels = list(records[0].keys())
        protocol = _infer_protocol(channels, json.dumps(payload)[:200])
        return ParsedLogSession(
            vendor=self.name,
            source_file=path,
            protocol=protocol,
            channels=channels,
            records=records,
            metadata={"records": str(len(records))},
        )


class DataLogAutoParser:
    """Registers vendor parsers and auto-detects based on file sniffing."""

    def __init__(self, extra_parsers: Iterable[DataLogParser] | None = None) -> None:
        self.parsers: List[DataLogParser] = [
            HolleyDataLogParser(),
            HaltechDataLogParser(),
            MotecDataLogParser(),
            GenericJSONParser(),
        ]
        if extra_parsers:
            self.parsers.extend(extra_parsers)

    def detect(self, path: Path) -> DataLogParser:
        sample = path.read_text(errors="ignore")[:2000]
        candidates = sorted(
            (
                (parser.sniff(sample), parser)
                for parser in self.parsers
                if path.suffix.lower() in parser.supported_extensions
            ),
            key=lambda item: item[0],
            reverse=True,
        )
        if candidates and candidates[0][0] > 0:
            return candidates[0][1]
        # fallback to first parser that claims default confidence
        return self.parsers[0]

    def parse(self, file_path: str | Path) -> ParsedLogSession:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(path)
        parser = self.detect(path)
        return parser.parse(path)

