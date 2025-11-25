#!/usr/bin/env python3
"""
Tuning Map Validator
Validates tuning maps for safety, compatibility, and correctness.

Checks:
- Required fields present
- Data format correctness
- Value ranges (safety limits)
- Vehicle compatibility
- Map consistency

Usage:
    python scripts/validate_tuning_map.py <map_file> [--strict] [--fix]
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.tune_map_database import TuneMap, TuningMap, MapCategory

LOGGER = logging.getLogger(__name__)


class TuningMapValidator:
    """Validates tuning maps."""

    # Safety limits for common parameters
    SAFETY_LIMITS = {
        'afr_min': 10.0,  # Too rich
        'afr_max': 18.0,  # Too lean
        'ignition_advance_max': 45.0,  # Degrees
        'ignition_retard_min': -10.0,  # Degrees
        'rpm_limit_max': 15000,  # RPM
        'boost_max': 50.0,  # PSI
        'temperature_max': 250.0,  # Celsius
    }

    def __init__(self, strict: bool = False):
        """Initialize validator."""
        self.strict = strict
        self.errors = []
        self.warnings = []
        self.fixes = []

    def validate(self, tune: TuneMap) -> bool:
        """Validate a TuneMap."""
        self.errors = []
        self.warnings = []
        self.fixes = []

        # Validate required fields
        self._validate_required_fields(tune)

        # Validate vehicle info
        self._validate_vehicle(tune.vehicle)

        # Validate maps
        for map_obj in tune.maps:
            self._validate_map(map_obj)

        # Validate safety warnings
        self._validate_safety_warnings(tune)

        # Validate performance gains
        if tune.performance_gains:
            self._validate_performance_gains(tune.performance_gains)

        # Check for inconsistencies
        self._check_consistency(tune)

        return len(self.errors) == 0

    def _validate_required_fields(self, tune: TuneMap) -> None:
        """Validate required fields are present."""
        if not tune.name:
            self.errors.append("Missing required field: name")
        
        if not tune.vehicle:
            self.errors.append("Missing required field: vehicle")
        
        if not tune.ecu_type:
            self.warnings.append("Missing ECU type - may affect compatibility")
        
        if not tune.maps:
            self.errors.append("No maps defined in tune")
        
        if not tune.safety_warnings:
            self.warnings.append("No safety warnings - recommended for user safety")

    def _validate_vehicle(self, vehicle) -> None:
        """Validate vehicle information."""
        if not vehicle.make or vehicle.make.lower() == 'unknown':
            self.warnings.append("Vehicle make is unknown or missing")
        
        if not vehicle.model or vehicle.model.lower() == 'unknown':
            self.warnings.append("Vehicle model is unknown or missing")
        
        if not vehicle.year or vehicle.year < 1900 or vehicle.year > 2100:
            self.warnings.append(f"Vehicle year seems invalid: {vehicle.year}")
        
        if vehicle.engine_displacement and (vehicle.engine_displacement < 0.1 or vehicle.engine_displacement > 10.0):
            self.warnings.append(f"Engine displacement seems invalid: {vehicle.engine_displacement}L")

    def _validate_map(self, map_obj: TuningMap) -> None:
        """Validate a TuningMap."""
        if not map_obj.name:
            self.errors.append(f"Map missing name: {map_obj.category}")
        
        if not map_obj.data:
            self.errors.append(f"Map missing data: {map_obj.name}")
            return
        
        # Validate based on map category
        if map_obj.category == MapCategory.FUEL_MAP:
            self._validate_fuel_map(map_obj)
        elif map_obj.category == MapCategory.IGNITION_TIMING:
            self._validate_ignition_map(map_obj)
        elif map_obj.category == MapCategory.RPM_LIMITER:
            self._validate_rpm_limiter(map_obj)
        elif map_obj.category == MapCategory.BOOST_CONTROL:
            self._validate_boost_map(map_obj)

    def _validate_fuel_map(self, map_obj: TuningMap) -> None:
        """Validate fuel map."""
        data = map_obj.data
        
        # Check for AFR values
        if 'afr_target' in data or 'afr_values' in data:
            afr_values = data.get('afr_values', [])
            if isinstance(data.get('afr_target'), (int, float)):
                afr_values = [data['afr_target']]
            
            for afr in afr_values:
                if isinstance(afr, (int, float)):
                    if afr < self.SAFETY_LIMITS['afr_min']:
                        self.errors.append(f"AFR too rich (dangerous): {afr}")
                    elif afr > self.SAFETY_LIMITS['afr_max']:
                        self.errors.append(f"AFR too lean (dangerous): {afr}")
        
        # Check for fuel values array
        if 'values' in data:
            values = data['values']
            if isinstance(values, list):
                # Check for reasonable values
                for row in values:
                    if isinstance(row, list):
                        for val in row:
                            if isinstance(val, (int, float)):
                                # Fuel values are typically 0-100% or similar
                                if val < -50 or val > 200:
                                    self.warnings.append(f"Fuel value seems extreme: {val}")

    def _validate_ignition_map(self, map_obj: TuningMap) -> None:
        """Validate ignition timing map."""
        data = map_obj.data
        
        # Check for timing values
        timing_values = []
        if 'timing_advance' in data:
            timing_values = [data['timing_advance']]
        elif 'timing_values' in data:
            timing_values = data['timing_values']
        elif 'values' in data:
            # Flatten 2D array
            if isinstance(data['values'], list):
                for row in data['values']:
                    if isinstance(row, list):
                        timing_values.extend(row)
        
        for timing in timing_values:
            if isinstance(timing, (int, float)):
                if timing > self.SAFETY_LIMITS['ignition_advance_max']:
                    self.errors.append(f"Ignition advance too high (dangerous): {timing}°")
                elif timing < self.SAFETY_LIMITS['ignition_retard_min']:
                    self.warnings.append(f"Ignition timing very retarded: {timing}°")

    def _validate_rpm_limiter(self, map_obj: TuningMap) -> None:
        """Validate RPM limiter."""
        data = map_obj.data
        
        rpm_limit = None
        if 'rev_limit' in data:
            rpm_limit = data['rev_limit']
        elif 'rpm_limit' in data:
            rpm_limit = data['rpm_limit']
        
        if rpm_limit:
            if isinstance(rpm_limit, (int, float)):
                if rpm_limit > self.SAFETY_LIMITS['rpm_limit_max']:
                    self.errors.append(f"RPM limit too high (dangerous): {rpm_limit}")
                elif rpm_limit < 1000:
                    self.warnings.append(f"RPM limit very low: {rpm_limit}")

    def _validate_boost_map(self, map_obj: TuningMap) -> None:
        """Validate boost control map."""
        data = map_obj.data
        
        boost_values = []
        if 'boost_target' in data:
            boost_values = [data['boost_target']]
        elif 'boost_values' in data:
            boost_values = data['boost_values']
        
        for boost in boost_values:
            if isinstance(boost, (int, float)):
                if boost > self.SAFETY_LIMITS['boost_max']:
                    self.errors.append(f"Boost pressure too high (dangerous): {boost} PSI")

    def _validate_safety_warnings(self, tune: TuneMap) -> None:
        """Validate safety warnings are appropriate."""
        if not tune.safety_warnings:
            self.warnings.append("No safety warnings - highly recommended")
            if not self.strict:
                self.fixes.append({
                    'field': 'safety_warnings',
                    'value': [
                        "This tune has not been validated",
                        "Use at your own risk",
                        "Have a professional tuner review before use",
                    ],
                })
        
        # Check for critical warnings
        warning_text = ' '.join(tune.safety_warnings).lower()
        if 'risk' not in warning_text and 'danger' not in warning_text:
            self.warnings.append("Safety warnings should mention risk/danger")

    def _validate_performance_gains(self, gains) -> None:
        """Validate performance gains claims."""
        if gains.hp_gain and gains.hp_gain > 500:
            self.warnings.append(f"HP gain seems very high: {gains.hp_gain} HP")
        
        if gains.torque_gain and gains.torque_gain > 500:
            self.warnings.append(f"Torque gain seems very high: {gains.torque_gain} lb-ft")

    def _check_consistency(self, tune: TuneMap) -> None:
        """Check for consistency issues."""
        # Check if tune type matches content
        if tune.tune_type.value == 'base_map' and tune.performance_gains:
            if tune.performance_gains.hp_gain and tune.performance_gains.hp_gain > 0:
                self.warnings.append("Base map claims performance gains - should be 0 for base maps")
        
        # Check if maps are consistent
        fuel_maps = [m for m in tune.maps if m.category == MapCategory.FUEL_MAP]
        ignition_maps = [m for m in tune.maps if m.category == MapCategory.IGNITION_TIMING]
        
        if fuel_maps and not ignition_maps:
            self.warnings.append("Has fuel map but no ignition map - may be incomplete")
        
        # Check vehicle/ECU compatibility
        if tune.vehicle.forced_induction == 'turbo' and not any(
            m.category == MapCategory.BOOST_CONTROL for m in tune.maps
        ):
            self.warnings.append("Turbo vehicle but no boost control map")

    def get_report(self) -> str:
        """Get validation report."""
        lines = []
        lines.append("=" * 60)
        lines.append("Tuning Map Validation Report")
        lines.append("=" * 60)
        lines.append("")
        
        if self.errors:
            lines.append(f"❌ ERRORS: {len(self.errors)}")
            for error in self.errors:
                lines.append(f"   - {error}")
            lines.append("")
        
        if self.warnings:
            lines.append(f"⚠️  WARNINGS: {len(self.warnings)}")
            for warning in self.warnings:
                lines.append(f"   - {warning}")
            lines.append("")
        
        if self.fixes:
            lines.append(f"🔧 SUGGESTED FIXES: {len(self.fixes)}")
            for fix in self.fixes:
                lines.append(f"   - {fix['field']}: {fix['value']}")
            lines.append("")
        
        if not self.errors and not self.warnings:
            lines.append("✅ Validation passed - no issues found!")
        elif not self.errors:
            lines.append("✅ Validation passed with warnings")
        else:
            lines.append("❌ Validation failed - fix errors before use")
        
        return "\n".join(lines)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate tuning maps')
    parser.add_argument('map_file', type=Path, help='Map file to validate')
    parser.add_argument('--strict', action='store_true', help='Strict validation (warnings as errors)')
    parser.add_argument('--fix', action='store_true', help='Apply suggested fixes')
    parser.add_argument('--output', type=Path, help='Output fixed file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')
    
    # Load map
    try:
        with open(args.map_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        tune = TuneMap.from_dict(data)
    except Exception as e:
        LOGGER.error("Error loading map: %s", e)
        return 1
    
    # Validate
    validator = TuningMapValidator(strict=args.strict)
    is_valid = validator.validate(tune)
    
    # Print report
    print(validator.get_report())
    
    # Apply fixes if requested
    if args.fix and validator.fixes:
        for fix in validator.fixes:
            setattr(tune, fix['field'], fix['value'])
        
        output_file = args.output or args.map_file.with_name(f"{args.map_file.stem}_fixed.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tune.to_dict(), f, indent=2)
        print(f"\n✅ Fixed map saved to: {output_file}")
    
    return 0 if is_valid else 1


if __name__ == "__main__":
    sys.exit(main())



