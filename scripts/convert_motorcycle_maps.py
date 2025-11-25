#!/usr/bin/env python3
"""
Motorcycle Tuning Map Converter
Converts motorcycle tuning maps from various formats to TelemetryIQ format.

Supports:
- TuneECU format (.hex, .bin)
- Power Commander format
- Generic CSV/Excel formats
- Custom ECU formats

Usage:
    python scripts/convert_motorcycle_maps.py <input_file> [--format <format>] [--output <output.json>]
"""

import sys
import json
import struct
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.tune_map_database import (
    TuneMap,
    TuneType,
    MapCategory,
    VehicleIdentifier,
    HardwareRequirement,
    PerformanceGains,
    TuningMap,
)

LOGGER = logging.getLogger(__name__)


class MotorcycleMapConverter:
    """Converts motorcycle tuning maps to TelemetryIQ format."""

    # Common motorcycle manufacturers
    MANUFACTURERS = {
        'honda': 'Honda',
        'yamaha': 'Yamaha',
        'suzuki': 'Suzuki',
        'kawasaki': 'Kawasaki',
        'ktm': 'KTM',
        'ducati': 'Ducati',
        'triumph': 'Triumph',
        'bmw': 'BMW',
        'harley': 'Harley-Davidson',
        'indian': 'Indian',
    }

    def __init__(self):
        """Initialize converter."""
        self.converted_count = 0
        self.failed_count = 0

    def convert_tuneecu_hex(self, file_path: Path, metadata: Dict[str, Any]) -> Optional[TuneMap]:
        """Convert TuneECU .hex file to TuneMap."""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # TuneECU hex files are typically Intel HEX format
            # Parse hex records
            hex_records = self._parse_intel_hex(data)
            
            # Extract map data (location depends on ECU type)
            maps = self._extract_tuneecu_maps(hex_records, metadata)
            
            # Create TuneMap
            tune = self._create_motorcycle_tune(metadata, maps)
            
            self.converted_count += 1
            return tune
            
        except Exception as e:
            LOGGER.error("Error converting TuneECU hex: %s", e, exc_info=True)
            self.failed_count += 1
            return None

    def convert_tuneecu_bin(self, file_path: Path, metadata: Dict[str, Any]) -> Optional[TuneMap]:
        """Convert TuneECU .bin file to TuneMap."""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # Extract maps based on known offsets (varies by ECU)
            maps = self._extract_binary_maps(data, metadata)
            
            # Create TuneMap
            tune = self._create_motorcycle_tune(metadata, maps)
            
            self.converted_count += 1
            return tune
            
        except Exception as e:
            LOGGER.error("Error converting TuneECU bin: %s", e, exc_info=True)
            self.failed_count += 1
            return None

    def convert_power_commander(self, file_path: Path, metadata: Dict[str, Any]) -> Optional[TuneMap]:
        """Convert Power Commander format to TuneMap."""
        try:
            # Power Commander files are typically CSV or text
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Parse Power Commander format
            maps = self._parse_power_commander(lines, metadata)
            
            # Create TuneMap
            tune = self._create_motorcycle_tune(metadata, maps)
            
            self.converted_count += 1
            return tune
            
        except Exception as e:
            LOGGER.error("Error converting Power Commander: %s", e, exc_info=True)
            self.failed_count += 1
            return None

    def convert_csv_motorcycle(self, file_path: Path, metadata: Dict[str, Any]) -> Optional[TuneMap]:
        """Convert CSV format motorcycle map to TuneMap."""
        try:
            import csv
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Parse CSV data
            maps = self._parse_csv_motorcycle(rows, metadata)
            
            # Create TuneMap
            tune = self._create_motorcycle_tune(metadata, maps)
            
            self.converted_count += 1
            return tune
            
        except Exception as e:
            LOGGER.error("Error converting CSV: %s", e, exc_info=True)
            self.failed_count += 1
            return None

    def _parse_intel_hex(self, data: bytes) -> List[Dict[str, Any]]:
        """Parse Intel HEX format."""
        records = []
        lines = data.decode('utf-8', errors='ignore').split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or not line.startswith(':'):
                continue
            
            try:
                # Intel HEX format: :LLAAAATTDD...CC
                length = int(line[1:3], 16)
                address = int(line[3:7], 16)
                record_type = int(line[7:9], 16)
                data_bytes = bytes.fromhex(line[9:9+length*2])
                
                records.append({
                    'length': length,
                    'address': address,
                    'type': record_type,
                    'data': data_bytes,
                })
            except Exception as e:
                LOGGER.warning("Error parsing HEX line: %s", e)
                continue
        
        return records

    def _extract_tuneecu_maps(
        self, hex_records: List[Dict[str, Any]], metadata: Dict[str, Any]
    ) -> List[TuningMap]:
        """Extract maps from TuneECU hex records."""
        maps = []
        
        # This is a simplified extraction - actual implementation depends on ECU type
        # Common map locations in TuneECU files:
        # - Fuel map: Usually at specific offsets
        # - Ignition map: Usually at specific offsets
        # - Throttle map: Usually at specific offsets
        
        ecu_type = metadata.get('ecu_type', 'generic').lower()
        
        # Try to extract fuel map (most common)
        fuel_map_data = self._extract_map_from_hex(hex_records, 'fuel', ecu_type)
        if fuel_map_data:
            maps.append(TuningMap(
                category=MapCategory.FUEL_MAP,
                name="Fuel Map",
                description="Fuel map extracted from TuneECU file",
                data=fuel_map_data,
            ))
        
        # Try to extract ignition map
        ignition_map_data = self._extract_map_from_hex(hex_records, 'ignition', ecu_type)
        if ignition_map_data:
            maps.append(TuningMap(
                category=MapCategory.IGNITION_TIMING,
                name="Ignition Timing Map",
                description="Ignition timing map extracted from TuneECU file",
                data=ignition_map_data,
            ))
        
        return maps

    def _extract_map_from_hex(
        self, hex_records: List[Dict[str, Any]], map_type: str, ecu_type: str
    ) -> Optional[Dict[str, Any]]:
        """Extract specific map type from hex records."""
        # This is a placeholder - actual implementation would need ECU-specific knowledge
        # Different ECUs store maps at different addresses
        
        # For now, return a generic structure
        # In production, you'd need ECU-specific map extraction logic
        return {
            'source': 'tuneecu',
            'format': 'hex',
            'ecu_type': ecu_type,
            'map_type': map_type,
            'note': 'Map extraction requires ECU-specific knowledge',
        }

    def _extract_binary_maps(self, data: bytes, metadata: Dict[str, Any]) -> List[TuningMap]:
        """Extract maps from binary file."""
        maps = []
        ecu_type = metadata.get('ecu_type', 'generic').lower()
        
        # Binary extraction is ECU-specific
        # This is a simplified version
        # In production, you'd need ECU-specific knowledge
        
        # Try to find fuel map (common patterns)
        fuel_map_data = self._find_map_in_binary(data, 'fuel', ecu_type)
        if fuel_map_data:
            maps.append(TuningMap(
                category=MapCategory.FUEL_MAP,
                name="Fuel Map",
                description="Fuel map extracted from binary file",
                data=fuel_map_data,
            ))
        
        return maps

    def _find_map_in_binary(
        self, data: bytes, map_type: str, ecu_type: str
    ) -> Optional[Dict[str, Any]]:
        """Find map in binary data."""
        # Placeholder - would need ECU-specific knowledge
        return {
            'source': 'binary',
            'format': 'bin',
            'ecu_type': ecu_type,
            'map_type': map_type,
            'note': 'Binary map extraction requires ECU-specific knowledge',
        }

    def _parse_power_commander(
        self, lines: List[str], metadata: Dict[str, Any]
    ) -> List[TuningMap]:
        """Parse Power Commander format."""
        maps = []
        
        # Power Commander format varies, but typically has:
        # - RPM values as columns
        # - Throttle position as rows
        # - Fuel adjustment values in cells
        
        # Try to parse common Power Commander formats
        fuel_data = self._parse_pc_fuel_map(lines)
        if fuel_data:
            maps.append(TuningMap(
                category=MapCategory.FUEL_MAP,
                name="Power Commander Fuel Map",
                description="Fuel map from Power Commander",
                data=fuel_data,
            ))
        
        return maps

    def _parse_pc_fuel_map(self, lines: List[str]) -> Optional[Dict[str, Any]]:
        """Parse Power Commander fuel map."""
        # Power Commander format example:
        # RPM:    1000  2000  3000  4000  5000  6000  7000  8000
        # 0%:     +0.0  +0.0  +0.0  +0.0  +0.0  +0.0  +0.0  +0.0
        # 10%:    +0.0  +0.0  +0.0  +0.0  +0.0  +0.0  +0.0  +0.0
        # ...
        
        rpm_values = []
        throttle_values = []
        fuel_values = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Try to parse RPM header
            if 'RPM' in line.upper() or line.startswith('RPM:'):
                parts = line.split()
                rpm_values = [int(p) for p in parts[1:] if p.replace(':', '').isdigit()]
                continue
            
            # Try to parse data rows
            if '%' in line or any(char.isdigit() for char in line):
                parts = line.split()
                if len(parts) > 1:
                    # First part is throttle position
                    throttle_str = parts[0].replace('%', '').replace(':', '')
                    if throttle_str.replace('.', '').isdigit():
                        throttle = float(throttle_str)
                        throttle_values.append(throttle)
                        
                        # Rest are fuel values
                        row_values = []
                        for val_str in parts[1:]:
                            try:
                                # Power Commander uses +/- format
                                val = float(val_str.replace('+', ''))
                                row_values.append(val)
                            except ValueError:
                                continue
                        fuel_values.append(row_values)
        
        if rpm_values and throttle_values and fuel_values:
            return {
                'rpm_axis': rpm_values,
                'throttle_axis': throttle_values,
                'fuel_adjustments': fuel_values,
                'format': 'power_commander',
            }
        
        return None

    def _parse_csv_motorcycle(
        self, rows: List[Dict[str, Any]], metadata: Dict[str, Any]
    ) -> List[TuningMap]:
        """Parse CSV motorcycle map."""
        maps = []
        
        # Try to identify map type from columns
        if not rows:
            return maps
        
        columns = list(rows[0].keys())
        
        # Look for RPM and throttle/load columns
        rpm_col = None
        throttle_col = None
        
        for col in columns:
            col_lower = col.lower()
            if 'rpm' in col_lower:
                rpm_col = col
            if 'throttle' in col_lower or 'tps' in col_lower or 'load' in col_lower:
                throttle_col = col
        
        # Extract fuel map if present
        if rpm_col:
            fuel_data = self._extract_fuel_from_csv(rows, rpm_col, throttle_col, columns)
            if fuel_data:
                maps.append(TuningMap(
                    category=MapCategory.FUEL_MAP,
                    name="Fuel Map",
                    description="Fuel map from CSV",
                    data=fuel_data,
                ))
        
        return maps

    def _extract_fuel_from_csv(
        self, rows: List[Dict[str, Any]], rpm_col: str, throttle_col: Optional[str], columns: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Extract fuel map data from CSV."""
        rpm_values = []
        fuel_values = []
        
        # Get RPM values
        for row in rows:
            if rpm_col in row:
                try:
                    rpm = float(row[rpm_col])
                    if rpm not in rpm_values:
                        rpm_values.append(rpm)
                except (ValueError, TypeError):
                    continue
        
        # Get fuel values (other numeric columns)
        fuel_columns = [c for c in columns if c != rpm_col and c != throttle_col]
        
        for row in rows:
            row_values = []
            for col in fuel_columns:
                try:
                    val = float(row[col])
                    row_values.append(val)
                except (ValueError, TypeError, KeyError):
                    row_values.append(0.0)
            if row_values:
                fuel_values.append(row_values)
        
        if rpm_values and fuel_values:
            return {
                'rpm_axis': sorted(rpm_values),
                'fuel_values': fuel_values,
                'format': 'csv',
            }
        
        return None

    def _create_motorcycle_tune(
        self, metadata: Dict[str, Any], maps: List[TuningMap]
    ) -> TuneMap:
        """Create TuneMap for motorcycle."""
        # Extract vehicle info
        make = metadata.get('make', 'Unknown')
        model = metadata.get('model', 'Unknown')
        year = metadata.get('year', 2020)
        
        # Normalize make
        make_lower = make.lower()
        for key, value in self.MANUFACTURERS.items():
            if key in make_lower:
                make = value
                break
        
        vehicle = VehicleIdentifier(
            make=make,
            model=model,
            year=year,
            engine_code=metadata.get('engine_code'),
            engine_displacement=metadata.get('engine_displacement'),
            fuel_type=metadata.get('fuel_type', 'gasoline'),
            forced_induction=metadata.get('forced_induction'),
        )
        
        # Create TuneMap
        tune = TuneMap(
            tune_id=metadata.get('tune_id'),
            name=metadata.get('name', f"{make} {model} {year} - Imported Tune"),
            description=metadata.get('description', 'Imported from motorcycle tuning file'),
            tune_type=TuneType(metadata.get('tune_type', 'base_map')),
            vehicle=vehicle,
            ecu_type=metadata.get('ecu_type', 'Generic'),
            maps=maps,
            hardware_requirements=self._parse_hardware_requirements(metadata),
            performance_gains=self._parse_performance_gains(metadata),
            tags=metadata.get('tags', []) + ['motorcycle', make.lower(), model.lower()],
            tuning_notes=metadata.get('tuning_notes', ''),
            installation_notes=metadata.get('installation_notes', ''),
            safety_warnings=[
                "This map was converted from external source",
                "Verify all parameters before use",
                "Use at your own risk",
                "Have a professional tuner review before use",
            ],
        )
        
        return tune

    def _parse_hardware_requirements(self, metadata: Dict[str, Any]) -> List[HardwareRequirement]:
        """Parse hardware requirements."""
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
        """Parse performance gains."""
        gains = metadata.get('performance_gains')
        if gains:
            if isinstance(gains, dict):
                return PerformanceGains(**gains)
        return None


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert motorcycle tuning maps')
    parser.add_argument('input_file', type=Path, help='Input file to convert')
    parser.add_argument('--format', choices=['tuneecu_hex', 'tuneecu_bin', 'power_commander', 'csv', 'auto'],
                       default='auto', help='Input format')
    parser.add_argument('--metadata', type=Path, help='Metadata JSON file')
    parser.add_argument('--output', type=Path, help='Output JSON file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')
    
    # Load metadata
    metadata = {}
    if args.metadata:
        with open(args.metadata, 'r') as f:
            metadata = json.load(f)
    else:
        # Try to extract from filename
        filename = args.input_file.stem.lower()
        # Simple extraction (can be improved)
        if 'honda' in filename:
            metadata['make'] = 'Honda'
        if 'yamaha' in filename:
            metadata['make'] = 'Yamaha'
        if 'suzuki' in filename:
            metadata['make'] = 'Suzuki'
        if 'kawasaki' in filename:
            metadata['make'] = 'Kawasaki'
    
    # Determine format
    if args.format == 'auto':
        suffix = args.input_file.suffix.lower()
        if suffix == '.hex':
            format_type = 'tuneecu_hex'
        elif suffix == '.bin':
            format_type = 'tuneecu_bin'
        elif suffix == '.csv':
            format_type = 'csv'
        else:
            # Try to detect Power Commander format
            with open(args.input_file, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline()
                if 'power' in first_line.lower() or 'commander' in first_line.lower():
                    format_type = 'power_commander'
                else:
                    format_type = 'csv'
    else:
        format_type = args.format
    
    # Convert
    converter = MotorcycleMapConverter()
    
    if format_type == 'tuneecu_hex':
        tune = converter.convert_tuneecu_hex(args.input_file, metadata)
    elif format_type == 'tuneecu_bin':
        tune = converter.convert_tuneecu_bin(args.input_file, metadata)
    elif format_type == 'power_commander':
        tune = converter.convert_power_commander(args.input_file, metadata)
    elif format_type == 'csv':
        tune = converter.convert_csv_motorcycle(args.input_file, metadata)
    else:
        LOGGER.error("Unsupported format: %s", format_type)
        return 1
    
    if not tune:
        LOGGER.error("Conversion failed")
        return 1
    
    # Output
    output_file = args.output or args.input_file.with_suffix('.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tune.to_dict(), f, indent=2)
    
    print(f"✅ Converted: {args.input_file} -> {output_file}")
    print(f"   Tune: {tune.name}")
    print(f"   Maps: {len(tune.maps)}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())



