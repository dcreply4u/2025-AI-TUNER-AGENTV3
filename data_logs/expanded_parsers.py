"""
Expanded Data Logger File Format Support

Additional parsers for:
- AEM (AEMLog, AEMData)
- Racepak (.rpk, .rpd)
- RaceCapture (.rcp)
- AIM (.aim, .vbo)
- MoTeC (expanded)
- Holley (expanded)
- Haltech (expanded)
"""

from __future__ import annotations

import csv
import json
import logging
import struct
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from data_logs.ingestor import DataLogParser, ParsedLogSession, SupportedProtocol, _CSVLogParser, _safe_float

LOGGER = logging.getLogger(__name__)


class AEMDataLogParser(_CSVLogParser):
    """Parser for AEM data logger files."""

    name = "AEM"
    vendor_marker = "aem"
    supported_extensions = (".csv", ".aem", ".aemlog", ".aemdata")

    def sniff(self, sample: str) -> float:
        """Detect AEM files."""
        sample_lower = sample.lower()
        if "aem" in sample_lower or "aemlog" in sample_lower:
            return 0.95
        # AEM files often have specific headers
        if any(header in sample_lower for header in ["time", "rpm", "map", "tps", "lambda"]):
            return 0.7
        return 0.3

    def parse(self, path: Path) -> ParsedLogSession:
        """Parse AEM data logger file."""
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
                if numeric is not None:
                    cleaned[key.strip()] = numeric
            if cleaned:
                records.append(cleaned)
        
        protocol = SupportedProtocol.CAN if any("can" in h.lower() for h in headers) else SupportedProtocol.UNKNOWN
        
        return ParsedLogSession(
            vendor=self.name,
            source_file=path,
            protocol=protocol,
            channels=headers,
            records=records,
            metadata={"records": str(len(records)), "format": "AEM"},
        )


class RacepakDataLogParser(_CSVLogParser):
    """Parser for Racepak data logger files."""

    name = "Racepak"
    vendor_marker = "racepak"
    supported_extensions = (".rpk", ".rpd", ".csv")

    def sniff(self, sample: str) -> float:
        """Detect Racepak files."""
        sample_lower = sample.lower()
        if "racepak" in sample_lower:
            return 0.95
        # Racepak files often have specific structure
        if "racepak" in sample_lower or ".rpk" in sample_lower:
            return 0.9
        return 0.2

    def parse(self, path: Path) -> ParsedLogSession:
        """Parse Racepak file."""
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
                if numeric is not None:
                    cleaned[key.strip()] = numeric
            if cleaned:
                records.append(cleaned)
        
        protocol = SupportedProtocol.CAN
        
        return ParsedLogSession(
            vendor=self.name,
            source_file=path,
            protocol=protocol,
            channels=headers,
            records=records,
            metadata={"records": str(len(records)), "format": "Racepak"},
        )


class RaceCaptureParser(_CSVLogParser):
    """Parser for RaceCapture data logger files."""

    name = "RaceCapture"
    vendor_marker = "racecapture"
    supported_extensions = (".rcp", ".csv", ".json")

    def sniff(self, sample: str) -> float:
        """Detect RaceCapture files."""
        sample_lower = sample.lower()
        if "racecapture" in sample_lower or "race capture" in sample_lower:
            return 0.95
        # RaceCapture JSON format
        if sample.strip().startswith("{") and "racecapture" in sample_lower:
            return 0.9
        return 0.2

    def parse(self, path: Path) -> ParsedLogSession:
        """Parse RaceCapture file."""
        if path.suffix.lower() == '.json':
            return self._parse_json(path)
        return self._parse_csv(path)

    def _parse_csv(self, path: Path) -> ParsedLogSession:
        """Parse RaceCapture CSV."""
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
                if numeric is not None:
                    cleaned[key.strip()] = numeric
            if cleaned:
                records.append(cleaned)
        
        return ParsedLogSession(
            vendor=self.name,
            source_file=path,
            protocol=SupportedProtocol.CAN,
            channels=headers,
            records=records,
            metadata={"records": str(len(records)), "format": "RaceCapture"},
        )

    def _parse_json(self, path: Path) -> ParsedLogSession:
        """Parse RaceCapture JSON."""
        data = json.loads(path.read_text(errors="ignore"))
        records: List[Dict[str, float]] = []
        channels: List[str] = []
        
        if isinstance(data, dict):
            # RaceCapture JSON format
            if "samples" in data:
                samples = data["samples"]
                if samples and isinstance(samples[0], dict):
                    channels = list(samples[0].keys())
                    for sample in samples:
                        cleaned = {
                            str(key): float(value)
                            for key, value in sample.items()
                            if isinstance(value, (int, float))
                        }
                        if cleaned:
                            records.append(cleaned)
        
        return ParsedLogSession(
            vendor=self.name,
            source_file=path,
            protocol=SupportedProtocol.CAN,
            channels=channels,
            records=records,
            metadata={"records": str(len(records)), "format": "RaceCapture JSON"},
        )


class AIMDataLogParser(_CSVLogParser):
    """Parser for AIM data logger files."""

    name = "AIM"
    vendor_marker = "aim"
    supported_extensions = (".aim", ".vbo", ".csv")

    def sniff(self, sample: str) -> float:
        """Detect AIM files."""
        sample_lower = sample.lower()
        if "aim" in sample_lower or ".vbo" in sample_lower:
            return 0.95
        return 0.2

    def parse(self, path: Path) -> ParsedLogSession:
        """Parse AIM file."""
        # AIM .vbo files are binary, .aim/.csv are text
        if path.suffix.lower() == '.vbo':
            return self._parse_vbo(path)
        return self._parse_text(path)

    def _parse_text(self, path: Path) -> ParsedLogSession:
        """Parse AIM text format."""
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
                if numeric is not None:
                    cleaned[key.strip()] = numeric
            if cleaned:
                records.append(cleaned)
        
        return ParsedLogSession(
            vendor=self.name,
            source_file=path,
            protocol=SupportedProtocol.CAN,
            channels=headers,
            records=records,
            metadata={"records": str(len(records)), "format": "AIM"},
        )

    def _parse_vbo(self, path: Path) -> ParsedLogSession:
        """Parse AIM VBO binary format (placeholder - would need format spec)."""
        # VBO files are binary and would require format specification
        LOGGER.warning("AIM VBO binary format parsing not fully implemented")
        raise NotImplementedError("AIM VBO binary format parsing requires format specification")


class ExpandedDataLogAutoParser:
    """Expanded auto-parser with all supported formats."""

    def __init__(self) -> None:
        """Initialize with all parsers."""
        from data_logs.ingestor import (
            DataLogAutoParser,
            HaltechDataLogParser,
            HolleyDataLogParser,
            MotecDataLogParser,
            GenericJSONParser,
        )
        
        self.parsers: List[DataLogParser] = [
            HolleyDataLogParser(),
            HaltechDataLogParser(),
            MotecDataLogParser(),
            AEMDataLogParser(),
            RacepakDataLogParser(),
            RaceCaptureParser(),
            AIMDataLogParser(),
            GenericJSONParser(),
        ]

    def detect(self, path: Path) -> DataLogParser:
        """Auto-detect file format."""
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
        return self.parsers[0]

    def parse(self, file_path: str | Path) -> ParsedLogSession:
        """Parse data logger file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(path)
        parser = self.detect(path)
        return parser.parse(path)


__all__ = [
    "AEMDataLogParser",
    "RacepakDataLogParser",
    "RaceCaptureParser",
    "AIMDataLogParser",
    "ExpandedDataLogAutoParser",
]






