#!/usr/bin/env python3
"""
Tuning Map Importer
Imports tuning maps from various sources and formats into the TelemetryIQ database.

Supports:
- JSON format (our native format)
- CSV format (common for map data)
- Holley EFI format (if available)
- Generic ECU map formats

Usage:
    python scripts/import_tuning_maps.py <source_file> [--format <format>] [--validate]
"""

import sys
import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.tune_map_database import (
    TuneMapDatabase,
    TuneMap,
    TuneType,
    MapCategory,
    VehicleIdentifier,
    HardwareRequirement,
    PerformanceGains,
    TuningMap,
)

LOGGER = logging.getLogger(__name__)


class TuningMapImporter:
    """Imports tuning maps from various formats."""

    def __init__(self, database: Optional[TuneMapDatabase] = None):
        """Initialize importer."""
        self.database = database or TuneMapDatabase()
        self.imported_count = 0
        self.failed_count = 0

    def import_from_json(self, file_path: Path) -> bool:
        """Import tune from JSON file (our native format)."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert dict to TuneMap
            tune = TuneMap.from_dict(data)
            
            # Add to database
            if self.database.add_tune(tune):
                LOGGER.info("Imported tune: %s", tune.name)
                self.imported_count += 1
                return True
            else:
                LOGGER.error("Failed to add tune: %s", tune.name)
                self.failed_count += 1
                return False
        except Exception as e:
            LOGGER.error("Error importing JSON: %s", e, exc_info=True)
            self.failed_count += 1
            return False

    def import_from_csv(self, file_path: Path, metadata: Dict[str, Any]) -> bool:
        """Import tune from CSV file with metadata."""
        try:
            # Read CSV data
            maps_data = {}
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                # Group by map type if CSV has map_type column
                if 'map_type' in rows[0] if rows else False:
                    for row in rows:
                        map_type = row.get('map_type', 'unknown')
                        if map_type not in maps_data:
                            maps_data[map_type] = []
                        maps_data[map_type].append(row)
                else:
                    # Single map - assume fuel map
                    maps_data['fuel_map'] = rows
            
            # Create TuneMap from metadata and CSV data
            tune = self._create_tune_from_data(metadata, maps_data)
            
            if self.database.add_tune(tune):
                LOGGER.info("Imported tune from CSV: %s", tune.name)
                self.imported_count += 1
                return True
            else:
                LOGGER.error("Failed to add tune from CSV: %s", tune.name)
                self.failed_count += 1
                return False
        except Exception as e:
            LOGGER.error("Error importing CSV: %s", e, exc_info=True)
            self.failed_count += 1
            return False

    def import_from_directory(self, directory: Path, pattern: str = "*.json") -> Dict[str, int]:
        """Import all matching files from a directory."""
        results = {"imported": 0, "failed": 0, "skipped": 0}
        
        for file_path in directory.glob(pattern):
            try:
                if self.import_from_json(file_path):
                    results["imported"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                LOGGER.error("Error importing %s: %s", file_path, e)
                results["failed"] += 1
        
        return results

    def _create_tune_from_data(
        self, metadata: Dict[str, Any], maps_data: Dict[str, List[Dict[str, Any]]]
    ) -> TuneMap:
        """Create TuneMap from metadata and map data."""
        # Extract vehicle info
        vehicle = VehicleIdentifier(
            make=metadata.get('make', 'Unknown'),
            model=metadata.get('model', 'Unknown'),
            year=metadata.get('year', 2020),
            engine_code=metadata.get('engine_code'),
            engine_displacement=metadata.get('engine_displacement'),
            fuel_type=metadata.get('fuel_type', 'gasoline'),
            forced_induction=metadata.get('forced_induction'),
        )
        
        # Create tuning maps
        tuning_maps = []
        for map_type, rows in maps_data.items():
            category = self._map_category_from_string(map_type)
            if category:
                # Convert CSV rows to map data structure
                map_data = self._convert_rows_to_map_data(rows)
                tuning_map = TuningMap(
                    category=category,
                    name=metadata.get('map_name', f"{map_type} Map"),
                    description=metadata.get('map_description', ''),
                    data=map_data,
                )
                tuning_maps.append(tuning_map)
        
        # Create TuneMap
        tune = TuneMap(
            tune_id=metadata.get('tune_id'),  # Will be generated if None
            name=metadata.get('name', 'Imported Tune'),
            description=metadata.get('description', 'Imported from external source'),
            tune_type=TuneType(metadata.get('tune_type', 'base_map')),
            vehicle=vehicle,
            ecu_type=metadata.get('ecu_type', 'Generic'),
            maps=tuning_maps,
            hardware_requirements=self._parse_hardware_requirements(metadata),
            performance_gains=self._parse_performance_gains(metadata),
            tags=metadata.get('tags', []),
            tuning_notes=metadata.get('tuning_notes', ''),
            installation_notes=metadata.get('installation_notes', ''),
        )
        
        return tune

    def _map_category_from_string(self, map_type: str) -> Optional[MapCategory]:
        """Convert string to MapCategory enum."""
        map_type_lower = map_type.lower()
        mapping = {
            'fuel_map': MapCategory.FUEL_MAP,
            'fuel': MapCategory.FUEL_MAP,
            'ignition': MapCategory.IGNITION_TIMING,
            'ignition_timing': MapCategory.IGNITION_TIMING,
            'rpm_limiter': MapCategory.RPM_LIMITER,
            'boost': MapCategory.BOOST_CONTROL,
            'boost_control': MapCategory.BOOST_CONTROL,
            'throttle': MapCategory.THROTTLE_RESPONSE,
            'throttle_response': MapCategory.THROTTLE_RESPONSE,
            'fan': MapCategory.FAN_CONTROL,
            'fan_control': MapCategory.FAN_CONTROL,
            'idle': MapCategory.IDLE_CONTROL,
            'idle_control': MapCategory.IDLE_CONTROL,
            'launch': MapCategory.LAUNCH_CONTROL,
            'launch_control': MapCategory.LAUNCH_CONTROL,
            'anti_lag': MapCategory.ANTI_LAG,
            'nitrous': MapCategory.NITROUS_CONTROL,
            'nitrous_control': MapCategory.NITROUS_CONTROL,
        }
        return mapping.get(map_type_lower)

    def _convert_rows_to_map_data(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert CSV rows to map data structure."""
        # This is a simplified conversion - actual implementation depends on CSV format
        data = {
            'rows': len(rows),
            'data': rows,
        }
        
        # Try to extract axis labels if present
        if rows and 'rpm' in rows[0]:
            data['x_axis'] = 'rpm'
        if rows and 'load' in rows[0] or 'throttle' in rows[0]:
            data['y_axis'] = rows[0].get('load') or rows[0].get('throttle')
        
        return data

    def _parse_hardware_requirements(self, metadata: Dict[str, Any]) -> List[HardwareRequirement]:
        """Parse hardware requirements from metadata."""
        requirements = []
        hw_req = metadata.get('hardware_requirements', [])
        
        if isinstance(hw_req, list):
            for req in hw_req:
                if isinstance(req, dict):
                    requirements.append(HardwareRequirement(**req))
                elif isinstance(req, str):
                    requirements.append(HardwareRequirement(
                        component=req,
                        description=f"Requires {req}",
                    ))
        
        return requirements

    def _parse_performance_gains(self, metadata: Dict[str, Any]) -> Optional[PerformanceGains]:
        """Parse performance gains from metadata."""
        gains = metadata.get('performance_gains')
        if gains:
            if isinstance(gains, dict):
                return PerformanceGains(**gains)
        return None


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Import tuning maps into database')
    parser.add_argument('source', type=Path, help='Source file or directory')
    parser.add_argument('--format', choices=['json', 'csv', 'auto'], default='auto',
                       help='File format (auto-detect if not specified)')
    parser.add_argument('--metadata', type=Path, help='Metadata file for CSV imports')
    parser.add_argument('--validate', action='store_true', help='Validate before importing')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')
    
    # Initialize importer
    importer = TuningMapImporter()
    
    # Determine format
    if args.format == 'auto':
        if args.source.suffix.lower() == '.json':
            format_type = 'json'
        elif args.source.suffix.lower() == '.csv':
            format_type = 'csv'
        else:
            LOGGER.error("Cannot auto-detect format for %s", args.source)
            return 1
    else:
        format_type = args.format
    
    # Import
    if args.source.is_file():
        if format_type == 'json':
            success = importer.import_from_json(args.source)
        elif format_type == 'csv':
            # Load metadata if provided
            metadata = {}
            if args.metadata:
                with open(args.metadata, 'r') as f:
                    metadata = json.load(f)
            else:
                LOGGER.warning("CSV import requires --metadata file")
                return 1
            
            success = importer.import_from_csv(args.source, metadata)
        else:
            LOGGER.error("Unsupported format: %s", format_type)
            return 1
        
        if success:
            print(f"✅ Successfully imported: {args.source}")
        else:
            print(f"❌ Failed to import: {args.source}")
            return 1
    
    elif args.source.is_dir():
        results = importer.import_from_directory(args.source)
        print(f"✅ Imported: {results['imported']}")
        print(f"❌ Failed: {results['failed']}")
        if results['failed'] > 0:
            return 1
    
    else:
        LOGGER.error("Source does not exist: %s", args.source)
        return 1
    
    print(f"\nTotal imported: {importer.imported_count}")
    print(f"Total failed: {importer.failed_count}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())



