"""
Dyno Calibration - Import/Export Real Dyno Data

Allows importing real dyno runs to calibrate virtual dyno for maximum accuracy.
Supports common dyno file formats (CSV, JSON, etc.)
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from services.virtual_dyno import DynoCurve, DynoReading, EnvironmentalConditions

LOGGER = logging.getLogger(__name__)

# Import universal dyno importer for expanded format support
try:
    from services.dyno_file_importers import UniversalDynoImporter
    UNIVERSAL_IMPORTER_AVAILABLE = True
except ImportError:
    UNIVERSAL_IMPORTER_AVAILABLE = False
    LOGGER.warning("Universal dyno importer not available - limited format support")


class DynoCalibration:
    """
    Import/export real dyno data for calibration.
    
    Supports:
    - CSV import (common dyno format)
    - JSON import
    - Manual entry
    - Export calibration data
    """

    def import_dyno_csv(
        self,
        file_path: str | Path,
        rpm_column: str = "RPM",
        hp_column: str = "HP",
        torque_column: Optional[str] = "Torque",
    ) -> DynoCurve:
        """
        Import dyno data from CSV file.
        
        Common formats:
        - Mustang Dyno: RPM, HP, Torque
        - Dynojet: RPM, HP, Torque
        - Custom: Specify column names
        
        Args:
            file_path: Path to CSV file
            rpm_column: Name of RPM column
            hp_column: Name of HP column
            torque_column: Name of torque column (optional)
            
        Returns:
            DynoCurve from imported data
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Dyno file not found: {file_path}")
        
        readings: List[DynoReading] = []
        peak_hp = 0.0
        peak_hp_rpm = 0.0
        peak_torque = 0.0
        peak_torque_rpm = 0.0
        
        with open(file_path, 'r', encoding='utf-8') as f:
            # Try to detect delimiter
            sample = f.read(1024)
            f.seek(0)
            delimiter = ',' if ',' in sample else '\t' if '\t' in sample else ','
            
            reader = csv.DictReader(f, delimiter=delimiter)
            
            # Normalize column names (case-insensitive)
            fieldnames = {name.lower(): name for name in reader.fieldnames or []}
            
            rpm_key = None
            hp_key = None
            torque_key = None
            
            # Find matching columns
            for key in fieldnames:
                if rpm_column.lower() in key:
                    rpm_key = fieldnames[key]
                if hp_column.lower() in key or 'horsepower' in key:
                    hp_key = fieldnames[key]
                if torque_column and (torque_column.lower() in key or 'torque' in key):
                    torque_key = fieldnames[key]
            
            if not rpm_key or not hp_key:
                raise ValueError(f"Could not find required columns: {rpm_column}, {hp_column}")
            
            # Read data
            for row in reader:
                try:
                    rpm = float(row[rpm_key])
                    hp = float(row[hp_key])
                    torque = float(row[torque_key]) if torque_key and row.get(torque_key) else None
                    
                    # Track peaks
                    if hp > peak_hp:
                        peak_hp = hp
                        peak_hp_rpm = rpm
                    
                    if torque and torque > peak_torque:
                        peak_torque = torque
                        peak_torque_rpm = rpm
                    
                    reading = DynoReading(
                        timestamp=0.0,  # Not available in CSV
                        rpm=rpm,
                        speed_mph=0.0,  # Not available
                        speed_mps=0.0,
                        acceleration_mps2=0.0,
                        horsepower_wheel=hp,  # Assume wheel HP from dyno
                        horsepower_crank=hp,  # Will be corrected if needed
                        torque_ftlb=torque,
                        method=None,  # Real dyno
                        confidence=1.0,  # High confidence (real dyno)
                    )
                    readings.append(reading)
                except (ValueError, KeyError) as e:
                    LOGGER.warning("Skipping invalid row: %s", e)
                    continue
        
        curve = DynoCurve(
            readings=readings,
            peak_hp_wheel=peak_hp,
            peak_hp_crank=peak_hp,
            peak_hp_rpm=peak_hp_rpm,
            peak_torque_ftlb=peak_torque,
            peak_torque_rpm=peak_torque_rpm,
            accuracy_estimate=1.0,  # Real dyno = 100% accurate
            calibration_factor=1.0,
        )
        
        LOGGER.info(
            "Imported dyno curve: %d readings, Peak HP: %.1f @ %.0f RPM",
            len(readings),
            peak_hp,
            peak_hp_rpm,
        )
        
        return curve

    def import_dyno_json(self, file_path: str | Path) -> DynoCurve:
        """
        Import dyno data from JSON file.
        
        Expected format:
        {
            "readings": [
                {"rpm": 2000, "hp": 150, "torque": 200},
                ...
            ],
            "peak_hp": 500,
            "peak_hp_rpm": 6000,
            ...
        }
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Dyno file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        readings = []
        for reading_data in data.get("readings", []):
            reading = DynoReading(
                timestamp=reading_data.get("timestamp", 0.0),
                rpm=reading_data.get("rpm"),
                speed_mph=reading_data.get("speed_mph", 0.0),
                speed_mps=reading_data.get("speed_mps", 0.0),
                acceleration_mps2=reading_data.get("acceleration_mps2", 0.0),
                horsepower_wheel=reading_data.get("horsepower_wheel", 0.0),
                horsepower_crank=reading_data.get("horsepower_crank", 0.0),
                torque_ftlb=reading_data.get("torque_ftlb"),
                method=None,
                confidence=1.0,
            )
            readings.append(reading)
        
        curve = DynoCurve(
            readings=readings,
            peak_hp_wheel=data.get("peak_hp_wheel", 0.0),
            peak_hp_crank=data.get("peak_hp_crank", 0.0),
            peak_hp_rpm=data.get("peak_hp_rpm", 0.0),
            peak_torque_ftlb=data.get("peak_torque_ftlb", 0.0),
            peak_torque_rpm=data.get("peak_torque_rpm", 0.0),
            accuracy_estimate=1.0,
            calibration_factor=data.get("calibration_factor", 1.0),
        )
        
        return curve

    def export_dyno_csv(self, curve: DynoCurve, file_path: str | Path) -> None:
        """Export dyno curve to CSV file."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["RPM", "HP_Crank", "HP_Wheel", "Torque_ftlb"])
            
            # Sort by RPM
            sorted_readings = sorted(
                [r for r in curve.readings if r.rpm is not None],
                key=lambda x: x.rpm or 0,
            )
            
            for reading in sorted_readings:
                writer.writerow([
                    reading.rpm or 0,
                    reading.horsepower_crank,
                    reading.horsepower_wheel,
                    reading.torque_ftlb or 0,
                ])
        
        LOGGER.info("Exported dyno curve to: %s", file_path)

    def export_dyno_json(self, curve: DynoCurve, file_path: str | Path) -> None:
        """Export dyno curve to JSON file."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "readings": [
                {
                    "timestamp": r.timestamp,
                    "rpm": r.rpm,
                    "speed_mph": r.speed_mph,
                    "speed_mps": r.speed_mps,
                    "acceleration_mps2": r.acceleration_mps2,
                    "horsepower_wheel": r.horsepower_wheel,
                    "horsepower_crank": r.horsepower_crank,
                    "torque_ftlb": r.torque_ftlb,
                    "confidence": r.confidence,
                }
                for r in curve.readings
            ],
            "peak_hp_wheel": curve.peak_hp_wheel,
            "peak_hp_crank": curve.peak_hp_crank,
            "peak_hp_rpm": curve.peak_hp_rpm,
            "peak_torque_ftlb": curve.peak_torque_ftlb,
            "peak_torque_rpm": curve.peak_torque_rpm,
            "accuracy_estimate": curve.accuracy_estimate,
            "calibration_factor": curve.calibration_factor,
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        LOGGER.info("Exported dyno curve to: %s", file_path)

    def import_dyno_file(self, file_path: str | Path) -> DynoCurve:
        """
        Import dyno file with automatic format detection.
        
        Supports all formats via UniversalDynoImporter:
        - Dynojet (.drf, .dyn)
        - Mustang Dyno (.md, .mdx)
        - SuperFlow (.sf, .sfd)
        - CSV/JSON (generic)
        
        Args:
            file_path: Path to dyno file
            
        Returns:
            DynoCurve from imported data
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Dyno file not found: {file_path}")
        
        # Try universal importer first (supports all formats)
        if UNIVERSAL_IMPORTER_AVAILABLE:
            try:
                importer = UniversalDynoImporter()
                return importer.import_file(file_path)
            except Exception as e:
                LOGGER.warning("Universal importer failed, trying fallback: %s", e)
        
        # Fallback to CSV/JSON
        suffix = file_path.suffix.lower()
        if suffix == '.csv':
            return self.import_dyno_csv(file_path)
        elif suffix == '.json':
            return self.import_dyno_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}. Use CSV or JSON, or install expanded format support.")


__all__ = ["DynoCalibration"]

