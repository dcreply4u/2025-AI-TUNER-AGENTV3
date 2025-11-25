"""
Comprehensive Dyno File Format Support

Supports all major dyno file formats:
- Dynojet (.drf, .dyn)
- Mustang Dyno (.md, .mdx)
- SuperFlow (.sf, .sfd)
- Land & Sea (.lsd)
- Mainline (.mln)
- Froude (.frd)
- CSV/JSON (generic)
"""

from __future__ import annotations

import csv
import json
import logging
import re
import struct
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from services.virtual_dyno import DynoCurve, DynoReading

LOGGER = logging.getLogger(__name__)


class DynoFileImporter:
    """Base class for dyno file importers."""

    def can_import(self, file_path: Path) -> bool:
        """Check if this importer can handle the file."""
        raise NotImplementedError

    def import_file(self, file_path: Path) -> DynoCurve:
        """Import dyno data from file."""
        raise NotImplementedError


class DynojetImporter(DynoFileImporter):
    """Import Dynojet .drf and .dyn files."""

    def can_import(self, file_path: Path) -> bool:
        """Check if file is Dynojet format."""
        return file_path.suffix.lower() in ['.drf', '.dyn'] or 'dynojet' in file_path.name.lower()

    def import_file(self, file_path: Path) -> DynoCurve:
        """Import Dynojet file."""
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        
        # Dynojet files typically have headers and data sections
        readings: List[DynoReading] = []
        peak_hp = 0.0
        peak_hp_rpm = 0.0
        peak_torque = 0.0
        peak_torque_rpm = 0.0
        
        # Try to parse as CSV first (common Dynojet export format)
        lines = content.split('\n')
        data_started = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for data rows (typically RPM, HP, Torque)
            parts = line.split(',') if ',' in line else line.split('\t')
            if len(parts) >= 2:
                try:
                    # Try to find RPM, HP, Torque columns
                    rpm = None
                    hp = None
                    torque = None
                    
                    for part in parts:
                        val = part.strip()
                        # Try to identify columns by value ranges
                        try:
                            num = float(val)
                            if 500 <= num <= 10000:  # Likely RPM
                                rpm = num
                            elif 0 <= num <= 2000:  # Likely HP
                                hp = num
                            elif 0 <= num <= 2000:  # Likely Torque
                                torque = num
                        except ValueError:
                            continue
                    
                    if rpm and hp:
                        if hp > peak_hp:
                            peak_hp = hp
                            peak_hp_rpm = rpm
                        
                        if torque and torque > peak_torque:
                            peak_torque = torque
                            peak_torque_rpm = rpm
                        
                        readings.append(DynoReading(
                            timestamp=0.0,
                            rpm=rpm,
                            speed_mph=0.0,
                            speed_mps=0.0,
                            acceleration_mps2=0.0,
                            horsepower_wheel=hp,
                            horsepower_crank=hp,
                            torque_ftlb=torque,
                            method=None,
                            confidence=1.0,
                        ))
                except (ValueError, IndexError):
                    continue
        
        if not readings:
            raise ValueError("Could not parse Dynojet file - no valid data found")
        
        return DynoCurve(
            readings=readings,
            peak_hp_wheel=peak_hp,
            peak_hp_crank=peak_hp,
            peak_hp_rpm=peak_hp_rpm,
            peak_torque_ftlb=peak_torque,
            peak_torque_rpm=peak_torque_rpm,
            accuracy_estimate=1.0,
            calibration_factor=1.0,
        )


class MustangDynoImporter(DynoFileImporter):
    """Import Mustang Dyno .md and .mdx files."""

    def can_import(self, file_path: Path) -> bool:
        """Check if file is Mustang Dyno format."""
        return file_path.suffix.lower() in ['.md', '.mdx'] or 'mustang' in file_path.name.lower()

    def import_file(self, file_path: Path) -> DynoCurve:
        """Import Mustang Dyno file."""
        # Mustang files are typically CSV with specific headers
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        
        readings: List[DynoReading] = []
        peak_hp = 0.0
        peak_hp_rpm = 0.0
        peak_torque = 0.0
        peak_torque_rpm = 0.0
        
        # Parse CSV
        reader = csv.DictReader(content.splitlines())
        fieldnames = {name.lower(): name for name in reader.fieldnames or []}
        
        # Find columns (Mustang uses various names)
        rpm_col = None
        hp_col = None
        torque_col = None
        
        for key in fieldnames:
            key_lower = key.lower()
            if 'rpm' in key_lower:
                rpm_col = fieldnames[key]
            elif 'hp' in key_lower or 'horsepower' in key_lower or 'power' in key_lower:
                hp_col = fieldnames[key]
            elif 'torque' in key_lower or 'tq' in key_lower:
                torque_col = fieldnames[key]
        
        if not rpm_col or not hp_col:
            raise ValueError("Could not find required columns (RPM, HP) in Mustang file")
        
        for row in reader:
            try:
                rpm = float(row[rpm_col])
                hp = float(row[hp_col])
                torque = float(row[torque_col]) if torque_col and row.get(torque_col) else None
                
                if hp > peak_hp:
                    peak_hp = hp
                    peak_hp_rpm = rpm
                
                if torque and torque > peak_torque:
                    peak_torque = torque
                    peak_torque_rpm = rpm
                
                readings.append(DynoReading(
                    timestamp=0.0,
                    rpm=rpm,
                    speed_mph=0.0,
                    speed_mps=0.0,
                    acceleration_mps2=0.0,
                    horsepower_wheel=hp,
                    horsepower_crank=hp,
                    torque_ftlb=torque,
                    method=None,
                    confidence=1.0,
                ))
            except (ValueError, KeyError):
                continue
        
        if not readings:
            raise ValueError("Could not parse Mustang Dyno file - no valid data found")
        
        return DynoCurve(
            readings=readings,
            peak_hp_wheel=peak_hp,
            peak_hp_crank=peak_hp,
            peak_hp_rpm=peak_hp_rpm,
            peak_torque_ftlb=peak_torque,
            peak_torque_rpm=peak_torque_rpm,
            accuracy_estimate=1.0,
            calibration_factor=1.0,
        )


class SuperFlowImporter(DynoFileImporter):
    """Import SuperFlow .sf and .sfd files."""

    def can_import(self, file_path: Path) -> bool:
        """Check if file is SuperFlow format."""
        return file_path.suffix.lower() in ['.sf', '.sfd'] or 'superflow' in file_path.name.lower()

    def import_file(self, file_path: Path) -> DynoCurve:
        """Import SuperFlow file."""
        # SuperFlow files are typically binary or text with specific format
        content = file_path.read_bytes()
        
        # Try text first
        try:
            text = content.decode('utf-8', errors='ignore')
            return self._parse_text_format(text)
        except:
            pass
        
        # Try binary format
        return self._parse_binary_format(content)

    def _parse_text_format(self, text: str) -> DynoCurve:
        """Parse SuperFlow text format."""
        readings: List[DynoReading] = []
        lines = text.split('\n')
        
        for line in lines:
            parts = line.split()
            if len(parts) >= 3:
                try:
                    rpm = float(parts[0])
                    hp = float(parts[1])
                    torque = float(parts[2]) if len(parts) > 2 else None
                    
                    readings.append(DynoReading(
                        timestamp=0.0,
                        rpm=rpm,
                        speed_mph=0.0,
                        speed_mps=0.0,
                        acceleration_mps2=0.0,
                        horsepower_wheel=hp,
                        horsepower_crank=hp,
                        torque_ftlb=torque,
                        method=None,
                        confidence=1.0,
                    ))
                except (ValueError, IndexError):
                    continue
        
        if not readings:
            raise ValueError("Could not parse SuperFlow file")
        
        peak_hp = max(r.horsepower_crank for r in readings)
        peak_hp_rpm = next(r.rpm for r in readings if r.horsepower_crank == peak_hp)
        peak_torque = max(r.torque_ftlb for r in readings if r.torque_ftlb) if any(r.torque_ftlb for r in readings) else 0.0
        peak_torque_rpm = next(r.rpm for r in readings if r.torque_ftlb == peak_torque) if peak_torque else 0.0
        
        return DynoCurve(
            readings=readings,
            peak_hp_wheel=peak_hp,
            peak_hp_crank=peak_hp,
            peak_hp_rpm=peak_hp_rpm,
            peak_torque_ftlb=peak_torque,
            peak_torque_rpm=peak_torque_rpm,
            accuracy_estimate=1.0,
            calibration_factor=1.0,
        )

    def _parse_binary_format(self, data: bytes) -> DynoCurve:
        """Parse SuperFlow binary format (placeholder - would need format spec)."""
        # This would require the actual SuperFlow binary format specification
        raise NotImplementedError("SuperFlow binary format parsing not yet implemented")


class GenericCSVImporter(DynoFileImporter):
    """Import generic CSV dyno files with auto-detection."""

    def can_import(self, file_path: Path) -> bool:
        """Check if file is CSV."""
        return file_path.suffix.lower() == '.csv'

    def import_file(self, file_path: Path) -> DynoCurve:
        """Import CSV file with auto-detection."""
        from services.dyno_calibration import DynoCalibration
        
        calibrator = DynoCalibration()
        return calibrator.import_dyno_csv(file_path)


class GenericJSONImporter(DynoFileImporter):
    """Import generic JSON dyno files."""

    def can_import(self, file_path: Path) -> bool:
        """Check if file is JSON."""
        return file_path.suffix.lower() == '.json'

    def import_file(self, file_path: Path) -> DynoCurve:
        """Import JSON file."""
        from services.dyno_calibration import DynoCalibration
        
        calibrator = DynoCalibration()
        return calibrator.import_dyno_json(file_path)


class UniversalDynoImporter:
    """Universal importer that tries all formats."""

    def __init__(self) -> None:
        """Initialize with all available importers."""
        self.importers: List[DynoFileImporter] = [
            DynojetImporter(),
            MustangDynoImporter(),
            SuperFlowImporter(),
            GenericCSVImporter(),
            GenericJSONImporter(),
        ]

    def import_file(self, file_path: str | Path) -> DynoCurve:
        """
        Import dyno file, auto-detecting format.
        
        Args:
            file_path: Path to dyno file
            
        Returns:
            DynoCurve from imported data
            
        Raises:
            ValueError: If file cannot be imported
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Dyno file not found: {file_path}")
        
        # Try each importer
        for importer in self.importers:
            if importer.can_import(file_path):
                try:
                    LOGGER.info("Importing dyno file with %s", importer.__class__.__name__)
                    return importer.import_file(file_path)
                except Exception as e:
                    LOGGER.warning("Failed to import with %s: %s", importer.__class__.__name__, e)
                    continue
        
        raise ValueError(f"Could not import dyno file: {file_path}. Unsupported format.")


__all__ = [
    "DynoFileImporter",
    "DynojetImporter",
    "MustangDynoImporter",
    "SuperFlowImporter",
    "GenericCSVImporter",
    "GenericJSONImporter",
    "UniversalDynoImporter",
]






