"""
Universal Log File Parser
Automatically detects and reads various log file formats:
- Dodge/Chrysler logs
- Holley EFI logs
- Dyno data logs
- OBD-II logs
- CSV/TSV logs
- JSON logs
- Binary logs
"""

from __future__ import annotations

import csv
import json
import logging
import re
import struct
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class LogFormat(Enum):
    """Supported log file formats."""
    UNKNOWN = "unknown"
    DODGE_CHRYSLER = "dodge_chrysler"
    HOLLEY_EFI = "holley_efi"
    DYNO_DYNAMICS = "dyno_dynamics"
    DYNOJET = "dynojet"
    MUSTANG_DYNO = "mustang_dyno"
    OBD2_CSV = "obd2_csv"
    CSV_GENERIC = "csv_generic"
    TSV_GENERIC = "tsv_generic"
    JSON = "json"
    BINARY = "binary"
    MOTEC = "motec"
    AIM = "aim"
    RACELOGIC = "racelogic"


@dataclass
class LogMetadata:
    """Log file metadata."""
    format: LogFormat
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_year: Optional[int] = None
    timestamp: Optional[float] = None
    duration: Optional[float] = None
    sample_rate: Optional[float] = None
    channels: List[str] = field(default_factory=list)
    units: Dict[str, str] = field(default_factory=dict)
    notes: str = ""


@dataclass
class LogData:
    """Parsed log data."""
    metadata: LogMetadata
    data: Dict[str, List[float]]  # Channel name -> values
    time: List[float]  # Time axis
    distance: Optional[List[float]] = None  # Distance axis (if available)


class UniversalLogParser:
    """
    Universal log file parser with automatic format detection.
    
    Supports multiple log formats and can automatically detect
    the format based on file content.
    """
    
    def __init__(self):
        """Initialize universal log parser."""
        self.parsers = {
            LogFormat.DODGE_CHRYSLER: self._parse_dodge_chrysler,
            LogFormat.HOLLEY_EFI: self._parse_holley_efi,
            LogFormat.DYNO_DYNAMICS: self._parse_dyno_dynamics,
            LogFormat.DYNOJET: self._parse_dynojet,
            LogFormat.MUSTANG_DYNO: self._parse_mustang_dyno,
            LogFormat.OBD2_CSV: self._parse_obd2_csv,
            LogFormat.CSV_GENERIC: self._parse_csv_generic,
            LogFormat.TSV_GENERIC: self._parse_tsv_generic,
            LogFormat.JSON: self._parse_json,
            LogFormat.MOTEC: self._parse_motec,
            LogFormat.AIM: self._parse_aim,
            LogFormat.RACELOGIC: self._parse_racelogic,
        }
    
    def detect_format(self, file_path: Path) -> LogFormat:
        """
        Automatically detect log file format.
        
        Args:
            file_path: Path to log file
        
        Returns:
            Detected LogFormat
        """
        # Check file extension
        ext = file_path.suffix.lower()
        
        if ext == '.json':
            return LogFormat.JSON
        elif ext in ['.csv']:
            # Need to check content
            pass
        elif ext in ['.tsv', '.txt']:
            # Need to check content
            pass
        elif ext in ['.bin', '.dat']:
            return LogFormat.BINARY
        
        # Read first few lines to detect format
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_lines = [f.readline() for _ in range(10)]
                content = '\n'.join(first_lines)
            
            # Check for Dodge/Chrysler format
            if 'Dodge' in content or 'Chrysler' in content or 'PCM' in content:
                return LogFormat.DODGE_CHRYSLER
            
            # Check for Holley EFI format
            if 'Holley' in content or 'HEFI' in content or 'Terminator' in content:
                return LogFormat.HOLLEY_EFI
            
            # Check for Motec format
            if 'MoTec' in content or 'M1' in content:
                return LogFormat.MOTEC
            
            # Check for AIM format
            if 'AIM' in content or 'RaceStudio' in content:
                return LogFormat.AIM
            
            # Check for RaceLogic format
            if 'RaceLogic' in content or 'VBOX' in content:
                return LogFormat.RACELOGIC
            
            # Check for dyno formats
            if 'Dyno Dynamics' in content:
                return LogFormat.DYNO_DYNAMICS
            if 'DynoJet' in content or 'DJ' in content:
                return LogFormat.DYNOJET
            if 'Mustang' in content and 'Dyno' in content:
                return LogFormat.MUSTANG_DYNO
            
            # Check for OBD-II CSV
            if 'OBD' in content or 'PID' in content:
                return LogFormat.OBD2_CSV
            
            # Check for tab-separated
            if '\t' in first_lines[0] if first_lines else False:
                return LogFormat.TSV_GENERIC
            
            # Default to CSV
            if ',' in first_lines[0] if first_lines else False:
                return LogFormat.CSV_GENERIC
            
        except Exception as e:
            LOGGER.warning("Failed to detect format: %s", e)
        
        return LogFormat.UNKNOWN
    
    def parse_file(self, file_path: Path, format: Optional[LogFormat] = None) -> LogData:
        """
        Parse log file.
        
        Args:
            file_path: Path to log file
            format: Optional format (auto-detected if None)
        
        Returns:
            Parsed LogData
        """
        if format is None:
            format = self.detect_format(file_path)
        
        if format == LogFormat.UNKNOWN:
            raise ValueError(f"Unknown log format: {file_path}")
        
        parser = self.parsers.get(format)
        if not parser:
            raise ValueError(f"Parser not available for format: {format}")
        
        LOGGER.info("Parsing %s as %s", file_path, format.value)
        return parser(file_path)
    
    def _parse_dodge_chrysler(self, file_path: Path) -> LogData:
        """Parse Dodge/Chrysler log file."""
        data = {}
        time = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Find header row
            header_idx = None
            for i, line in enumerate(lines):
                if 'Time' in line or 'TIME' in line:
                    header_idx = i
                    break
            
            if header_idx is None:
                raise ValueError("Header not found in Dodge log")
            
            # Parse header
            header = lines[header_idx].strip().split(',')
            channels = [h.strip() for h in header]
            
            # Initialize data dict
            for channel in channels:
                data[channel] = []
            
            # Parse data rows
            for line in lines[header_idx + 1:]:
                if not line.strip():
                    continue
                
                values = line.strip().split(',')
                if len(values) != len(channels):
                    continue
                
                try:
                    for i, val in enumerate(values):
                        if channels[i].lower() in ['time', 'timestamp']:
                            time.append(float(val))
                        else:
                            data[channels[i]].append(float(val))
                except ValueError:
                    continue
            
            # Create metadata
            metadata = LogMetadata(
                format=LogFormat.DODGE_CHRYSLER,
                channels=channels,
                sample_rate=self._calculate_sample_rate(time) if time else None,
            )
            
            return LogData(metadata=metadata, data=data, time=time)
            
        except Exception as e:
            LOGGER.error("Failed to parse Dodge log: %s", e)
            raise
    
    def _parse_holley_efi(self, file_path: Path) -> LogData:
        """Parse Holley EFI log file."""
        data = {}
        time = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Holley logs are typically CSV with specific format
            lines = content.split('\n')
            
            # Find data section
            data_start = None
            for i, line in enumerate(lines):
                if line.startswith('Time,') or 'RPM,' in line:
                    data_start = i
                    break
            
            if data_start is None:
                raise ValueError("Data section not found in Holley log")
            
            # Parse header
            header = lines[data_start].strip().split(',')
            channels = [h.strip() for h in header]
            
            # Initialize data dict
            for channel in channels:
                data[channel] = []
            
            # Parse data
            for line in lines[data_start + 1:]:
                if not line.strip() or line.startswith('#'):
                    continue
                
                values = line.strip().split(',')
                if len(values) != len(channels):
                    continue
                
                try:
                    for i, val in enumerate(values):
                        if channels[i].lower() == 'time':
                            time.append(float(val))
                        else:
                            data[channels[i]].append(float(val))
                except ValueError:
                    continue
            
            metadata = LogMetadata(
                format=LogFormat.HOLLEY_EFI,
                channels=channels,
                sample_rate=self._calculate_sample_rate(time) if time else None,
            )
            
            return LogData(metadata=metadata, data=data, time=time)
            
        except Exception as e:
            LOGGER.error("Failed to parse Holley log: %s", e)
            raise
    
    def _parse_dyno_dynamics(self, file_path: Path) -> LogData:
        """Parse Dyno Dynamics log file."""
        # Similar structure to CSV
        return self._parse_csv_generic(file_path)
    
    def _parse_dynojet(self, file_path: Path) -> LogData:
        """Parse DynoJet log file."""
        return self._parse_csv_generic(file_path)
    
    def _parse_mustang_dyno(self, file_path: Path) -> LogData:
        """Parse Mustang Dyno log file."""
        return self._parse_csv_generic(file_path)
    
    def _parse_obd2_csv(self, file_path: Path) -> LogData:
        """Parse OBD-II CSV log file."""
        return self._parse_csv_generic(file_path)
    
    def _parse_csv_generic(self, file_path: Path) -> LogData:
        """Parse generic CSV log file."""
        data = {}
        time = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                
                # Get channels from header
                channels = reader.fieldnames or []
                
                # Initialize data dict
                for channel in channels:
                    data[channel] = []
                
                # Parse rows
                for row in reader:
                    for channel in channels:
                        val = row.get(channel, '0')
                        try:
                            if channel.lower() in ['time', 'timestamp', 't']:
                                time.append(float(val))
                            else:
                                data[channel].append(float(val))
                        except (ValueError, TypeError):
                            if channel.lower() in ['time', 'timestamp', 't']:
                                time.append(0.0)
                            else:
                                data[channel].append(0.0)
            
            metadata = LogMetadata(
                format=LogFormat.CSV_GENERIC,
                channels=list(channels),
                sample_rate=self._calculate_sample_rate(time) if time else None,
            )
            
            return LogData(metadata=metadata, data=data, time=time)
            
        except Exception as e:
            LOGGER.error("Failed to parse CSV log: %s", e)
            raise
    
    def _parse_tsv_generic(self, file_path: Path) -> LogData:
        """Parse generic TSV log file."""
        data = {}
        time = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f, delimiter='\t')
                
                channels = reader.fieldnames or []
                
                for channel in channels:
                    data[channel] = []
                
                for row in reader:
                    for channel in channels:
                        val = row.get(channel, '0')
                        try:
                            if channel.lower() in ['time', 'timestamp', 't']:
                                time.append(float(val))
                            else:
                                data[channel].append(float(val))
                        except (ValueError, TypeError):
                            if channel.lower() in ['time', 'timestamp', 't']:
                                time.append(0.0)
                            else:
                                data[channel].append(0.0)
            
            metadata = LogMetadata(
                format=LogFormat.TSV_GENERIC,
                channels=list(channels),
                sample_rate=self._calculate_sample_rate(time) if time else None,
            )
            
            return LogData(metadata=metadata, data=data, time=time)
            
        except Exception as e:
            LOGGER.error("Failed to parse TSV log: %s", e)
            raise
    
    def _parse_json(self, file_path: Path) -> LogData:
        """Parse JSON log file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(json_data, dict):
                # Assume structure: {"time": [...], "channels": {...}}
                time = json_data.get("time", [])
                data = json_data.get("channels", json_data.get("data", {}))
            elif isinstance(json_data, list):
                # Assume array of objects
                if not json_data:
                    raise ValueError("Empty JSON log")
                
                # Get channels from first object
                channels = list(json_data[0].keys())
                data = {ch: [] for ch in channels}
                time = []
                
                for obj in json_data:
                    for channel in channels:
                        val = obj.get(channel, 0)
                        if channel.lower() in ['time', 'timestamp', 't']:
                            time.append(float(val))
                        else:
                            data[channel].append(float(val))
            else:
                raise ValueError("Unsupported JSON structure")
            
            metadata = LogMetadata(
                format=LogFormat.JSON,
                channels=list(data.keys()),
                sample_rate=self._calculate_sample_rate(time) if time else None,
            )
            
            return LogData(metadata=metadata, data=data, time=time)
            
        except Exception as e:
            LOGGER.error("Failed to parse JSON log: %s", e)
            raise
    
    def _parse_motec(self, file_path: Path) -> LogData:
        """Parse MoTeC log file."""
        # MoTeC files are typically binary or specific text format
        # This is a simplified parser
        return self._parse_csv_generic(file_path)
    
    def _parse_aim(self, file_path: Path) -> LogData:
        """Parse AIM log file."""
        return self._parse_csv_generic(file_path)
    
    def _parse_racelogic(self, file_path: Path) -> LogData:
        """Parse RaceLogic log file."""
        return self._parse_csv_generic(file_path)
    
    def _calculate_sample_rate(self, time: List[float]) -> Optional[float]:
        """Calculate sample rate from time data."""
        if not time or len(time) < 2:
            return None
        
        if NUMPY_AVAILABLE:
            intervals = np.diff(time)
            return float(1.0 / np.mean(intervals))
        else:
            intervals = [time[i+1] - time[i] for i in range(len(time)-1)]
            avg_interval = sum(intervals) / len(intervals) if intervals else 0
            return 1.0 / avg_interval if avg_interval > 0 else None


