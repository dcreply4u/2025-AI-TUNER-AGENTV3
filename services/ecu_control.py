"""
ECU Control Module

Provides full ECU control capabilities:
- Read/write ECU files and settings
- Backup and restore functionality
- Validation and safety checks
- Engine control parameters
- Change tracking and rollback
- Safety warnings for potentially harmful changes
"""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

LOGGER = logging.getLogger(__name__)


class ECUOperation(Enum):
    """ECU operation types."""

    READ = "read"
    WRITE = "write"
    BACKUP = "backup"
    RESTORE = "restore"
    RESET = "reset"
    VALIDATE = "validate"


class SafetyLevel(Enum):
    """Safety levels for ECU changes."""

    SAFE = "safe"
    CAUTION = "caution"
    WARNING = "warning"
    DANGEROUS = "dangerous"
    CRITICAL = "critical"


@dataclass
class ECUParameter:
    """ECU parameter definition."""

    name: str
    category: str  # fuel, ignition, boost, etc.
    current_value: Any
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    default_value: Optional[Any] = None
    unit: str = ""
    description: str = ""
    safety_level: SafetyLevel = SafetyLevel.SAFE
    dependencies: List[str] = field(default_factory=list)  # Other parameters this depends on


@dataclass
class ECUChange:
    """Record of an ECU change."""

    parameter_name: str
    old_value: Any
    new_value: Any
    timestamp: float = field(default_factory=time.time)
    user: str = "system"
    validated: bool = False
    safety_warnings: List[str] = field(default_factory=list)


@dataclass
class ECUBackup:
    """ECU backup file information."""

    backup_id: str
    timestamp: float
    file_path: Path
    file_hash: str
    ecu_type: str
    vehicle_info: Dict[str, Any]
    validated: bool = False
    validation_errors: List[str] = field(default_factory=list)


class ECUControl:
    """Comprehensive ECU control module."""

    # Safety rules for parameter changes
    SAFETY_RULES = {
        "fuel_map": {
            "max_change_percent": 20.0,  # Max 20% change at once
            "requires_validation": True,
            "warning_threshold": 15.0,
        },
        "ignition_timing": {
            "max_change_degrees": 5.0,
            "requires_validation": True,
            "warning_threshold": 3.0,
        },
        "boost_pressure": {
            "max_change_psi": 5.0,
            "requires_validation": True,
            "warning_threshold": 3.0,
        },
        "rev_limit": {
            "max_change_rpm": 500,
            "requires_validation": True,
            "warning_threshold": 300,
        },
        "idle_speed": {
            "max_change_rpm": 200,
            "requires_validation": False,
            "warning_threshold": 100,
        },
    }

    def __init__(
        self,
        backup_dir: str | Path = "backups/ecu",
        notification_callback: Optional[callable] = None,
    ) -> None:
        """
        Initialize ECU control module.

        Args:
            backup_dir: Directory for ECU backups
            notification_callback: Callback for notifications
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.notification_callback = notification_callback

        # ECU state
        self.current_parameters: Dict[str, ECUParameter] = {}
        self.change_history: List[ECUChange] = []
        self.backups: Dict[str, ECUBackup] = {}
        self.ecu_type: Optional[str] = None
        self.ecu_connected = False

        # Safety limits
        self.safety_enabled = True
        self.auto_backup = True

    def connect_ecu(self, ecu_type: str, connection_params: Dict[str, Any]) -> bool:
        """
        Connect to ECU.

        Args:
            ecu_type: Type of ECU (Holley, Haltech, AEM, etc.)
            connection_params: Connection parameters

        Returns:
            True if connected successfully
        """
        try:
            # Simulate ECU connection (would be vendor-specific)
            self.ecu_type = ecu_type
            self.ecu_connected = True

            # Load current parameters
            self._load_current_parameters()

            self._notify(f"Connected to {ecu_type} ECU", level="info")
            LOGGER.info("Connected to ECU: %s", ecu_type)
            return True
        except Exception as e:
            LOGGER.error("Failed to connect to ECU: %s", e)
            self._notify(f"ECU connection failed: {str(e)}", level="error")
            return False

    def disconnect_ecu(self) -> None:
        """Disconnect from ECU."""
        self.ecu_connected = False
        self._notify("Disconnected from ECU", level="info")

    def read_ecu_file(self, file_path: Optional[str | Path] = None) -> Dict[str, Any]:
        """
        Read ECU file.

        Args:
            file_path: Path to ECU file (None = read from connected ECU)

        Returns:
            ECU file data
        """
        if file_path:
            # Read from file
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"ECU file not found: {file_path}")

            with open(path, "rb") as f:
                data = f.read()

            return self._parse_ecu_file(data)
        else:
            # Read from connected ECU
            if not self.ecu_connected:
                raise RuntimeError("ECU not connected")

            # This would be vendor-specific implementation
            return self._read_from_ecu()

    def backup_ecu(self, description: str = "") -> ECUBackup:
        """
        Create backup of current ECU state.

        Args:
            description: Optional description for backup

        Returns:
            Backup information
        """
        if not self.ecu_connected:
            raise RuntimeError("ECU not connected")

        backup_id = f"backup_{int(time.time())}"
        timestamp = time.time()

        # Read current ECU state
        ecu_data = self.read_ecu_file()

        # Save to file
        backup_file = self.backup_dir / f"{backup_id}.ecu"
        with open(backup_file, "w") as f:
            json.dump(
                {
                    "backup_id": backup_id,
                    "timestamp": timestamp,
                    "description": description,
                    "ecu_type": self.ecu_type,
                    "parameters": {name: asdict(param) for name, param in self.current_parameters.items()},
                    "ecu_data": ecu_data,
                },
                f,
                indent=2,
            )

        # Calculate file hash for validation
        file_hash = self._calculate_file_hash(backup_file)

        # Validate backup
        validation_errors = self._validate_backup(backup_file)

        backup = ECUBackup(
            backup_id=backup_id,
            timestamp=timestamp,
            file_path=backup_file,
            file_hash=file_hash,
            ecu_type=self.ecu_type or "unknown",
            vehicle_info={},  # Would be populated from ECU
            validated=len(validation_errors) == 0,
            validation_errors=validation_errors,
        )

        self.backups[backup_id] = backup

        self._notify(f"ECU backup created: {backup_id}", level="info")
        LOGGER.info("Created ECU backup: %s", backup_id)

        return backup

    def restore_ecu(self, backup_id: str, validate: bool = True) -> bool:
        """
        Restore ECU from backup.

        Args:
            backup_id: Backup identifier
            validate: Validate backup before restoring

        Returns:
            True if restored successfully
        """
        if backup_id not in self.backups:
            raise ValueError(f"Backup not found: {backup_id}")

        backup = self.backups[backup_id]

        if validate and not backup.validated:
            # Re-validate
            validation_errors = self._validate_backup(backup.file_path)
            if validation_errors:
                self._notify(f"Backup validation failed: {', '.join(validation_errors)}", level="error")
                return False

        try:
            # Load backup data
            with open(backup.file_path, "r") as f:
                backup_data = json.load(f)

            # Restore parameters
            parameters = backup_data.get("parameters", {})
            for name, param_data in parameters.items():
                self.set_parameter(name, param_data.get("current_value"))

            # Write to ECU
            self._write_to_ecu(backup_data.get("ecu_data", {}))

            self._notify(f"ECU restored from backup: {backup_id}", level="info")
            LOGGER.info("Restored ECU from backup: %s", backup_id)
            return True
        except Exception as e:
            LOGGER.error("Failed to restore ECU: %s", e)
            self._notify(f"ECU restore failed: {str(e)}", level="error")
            return False

    def set_parameter(
        self,
        parameter_name: str,
        new_value: Any,
        validate: bool = True,
        auto_backup: Optional[bool] = None,
    ) -> Tuple[bool, List[str]]:
        """
        Set an ECU parameter with safety checks.

        Args:
            parameter_name: Parameter name
            new_value: New value
            validate: Validate change before applying
            auto_backup: Auto-backup before change (None = use default)

        Returns:
            Tuple of (success, warnings)
        """
        if not self.ecu_connected:
            raise RuntimeError("ECU not connected")

        if parameter_name not in self.current_parameters:
            raise ValueError(f"Unknown parameter: {parameter_name}")

        param = self.current_parameters[parameter_name]
        old_value = param.current_value

        # Auto-backup if enabled
        if (auto_backup is None and self.auto_backup) or auto_backup:
            self.backup_ecu(description=f"Auto-backup before changing {parameter_name}")

        # Validate change
        warnings = []
        if validate:
            validation_result = self._validate_parameter_change(parameter_name, old_value, new_value)
            warnings = validation_result["warnings"]

            if validation_result["safety_level"] == SafetyLevel.CRITICAL:
                self._notify(f"CRITICAL: Change to {parameter_name} is too dangerous", level="critical")
                return False, warnings

            if validation_result["safety_level"] == SafetyLevel.DANGEROUS:
                self._notify(f"DANGEROUS: Change to {parameter_name} may cause damage", level="error")
                # Still allow but with strong warning
                warnings.insert(0, f"DANGEROUS change to {parameter_name}")

        # Apply change
        try:
            param.current_value = new_value
            self._write_parameter_to_ecu(parameter_name, new_value)

            # Record change
            change = ECUChange(
                parameter_name=parameter_name,
                old_value=old_value,
                new_value=new_value,
                validated=validate,
                safety_warnings=warnings,
            )
            self.change_history.append(change)

            # Keep history limited
            if len(self.change_history) > 1000:
                self.change_history.pop(0)

            self._notify(f"Changed {parameter_name}: {old_value} -> {new_value}", level="info")
            LOGGER.info("Changed parameter %s: %s -> %s", parameter_name, old_value, new_value)

            return True, warnings
        except Exception as e:
            LOGGER.error("Failed to set parameter: %s", e)
            self._notify(f"Failed to change {parameter_name}: {str(e)}", level="error")
            return False, [str(e)]

    def reset_ecu(self, reset_type: str = "soft") -> bool:
        """
        Reset ECU.

        Args:
            reset_type: Type of reset (soft, hard, factory)

        Returns:
            True if reset successful
        """
        if not self.ecu_connected:
            raise RuntimeError("ECU not connected")

        # Backup before reset
        if self.auto_backup:
            self.backup_ecu(description=f"Pre-reset backup ({reset_type})")

        try:
            if reset_type == "factory":
                # Restore factory defaults
                self._reset_to_factory()
            elif reset_type == "hard":
                # Hard reset (clears all custom settings)
                self._hard_reset()
            else:  # soft
                # Soft reset (restarts ECU)
                self._soft_reset()

            self._notify(f"ECU reset ({reset_type})", level="info")
            LOGGER.info("ECU reset: %s", reset_type)
            return True
        except Exception as e:
            LOGGER.error("ECU reset failed: %s", e)
            self._notify(f"ECU reset failed: {str(e)}", level="error")
            return False

    def validate_ecu_file(self, file_path: str | Path) -> Tuple[bool, List[str]]:
        """
        Validate an ECU file.

        Args:
            file_path: Path to ECU file

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        path = Path(file_path)
        if not path.exists():
            return False, [f"File not found: {file_path}"]

        try:
            with open(path, "r") as f:
                data = json.load(f)

            # Check required fields
            required_fields = ["ecu_type", "parameters", "ecu_data"]
            for field in required_fields:
                if field not in data:
                    errors.append(f"Missing required field: {field}")

            # Validate parameters
            if "parameters" in data:
                for name, param_data in data["parameters"].items():
                    param_errors = self._validate_parameter_data(name, param_data)
                    errors.extend(param_errors)

            # Check file integrity
            file_hash = self._calculate_file_hash(path)
            stored_hash = data.get("file_hash")
            if stored_hash and file_hash != stored_hash:
                errors.append("File integrity check failed (hash mismatch)")

        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {str(e)}")
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        return len(errors) == 0, errors

    def get_safety_analysis(self, parameter_name: str, new_value: Any) -> Dict[str, Any]:
        """
        Analyze safety of a parameter change.

        Args:
            parameter_name: Parameter name
            new_value: Proposed new value

        Returns:
            Safety analysis dictionary
        """
        if parameter_name not in self.current_parameters:
            return {"error": f"Unknown parameter: {parameter_name}"}

        param = self.current_parameters[parameter_name]
        old_value = param.current_value

        result = self._validate_parameter_change(parameter_name, old_value, new_value)

        return {
            "parameter": parameter_name,
            "old_value": old_value,
            "new_value": new_value,
            "safety_level": result["safety_level"].value,
            "warnings": result["warnings"],
            "recommendations": result.get("recommendations", []),
            "safe": result["safety_level"] in [SafetyLevel.SAFE, SafetyLevel.CAUTION],
        }

    def rollback_change(self, change_index: Optional[int] = None) -> bool:
        """
        Rollback a change.

        Args:
            change_index: Index of change to rollback (None = last change)

        Returns:
            True if rolled back successfully
        """
        if not self.change_history:
            return False

        if change_index is None:
            change_index = len(self.change_history) - 1

        if change_index >= len(self.change_history):
            return False

        change = self.change_history[change_index]

        # Restore old value
        success, _ = self.set_parameter(
            change.parameter_name,
            change.old_value,
            validate=False,
            auto_backup=False,
        )

        if success:
            # Remove from history
            self.change_history.pop(change_index)
            self._notify(f"Rolled back change to {change.parameter_name}", level="info")

        return success

    def _validate_parameter_change(
        self, parameter_name: str, old_value: Any, new_value: Any
    ) -> Dict[str, Any]:
        """Validate a parameter change."""
        param = self.current_parameters[parameter_name]
        warnings = []
        recommendations = []
        safety_level = param.safety_level

        # Check bounds
        if param.min_value is not None and new_value < param.min_value:
            warnings.append(f"{parameter_name} below minimum: {new_value} < {param.min_value}")
            safety_level = SafetyLevel.DANGEROUS

        if param.max_value is not None and new_value > param.max_value:
            warnings.append(f"{parameter_name} above maximum: {new_value} > {param.max_value}")
            safety_level = SafetyLevel.CRITICAL

        # Check category-specific rules
        category = param.category
        if category in self.SAFETY_RULES:
            rules = self.SAFETY_RULES[category]

            # Calculate change percentage
            if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)) and old_value != 0:
                change_percent = abs((new_value - old_value) / old_value) * 100

                if "max_change_percent" in rules and change_percent > rules["max_change_percent"]:
                    warnings.append(
                        f"Large change to {parameter_name}: {change_percent:.1f}% (max: {rules['max_change_percent']}%)"
                    )
                    safety_level = SafetyLevel.WARNING

                if "warning_threshold" in rules and change_percent > rules["warning_threshold"]:
                    warnings.append(f"Significant change to {parameter_name}: {change_percent:.1f}%")
                    if safety_level == SafetyLevel.SAFE:
                        safety_level = SafetyLevel.CAUTION

            # Check absolute change
            if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
                change_abs = abs(new_value - old_value)

                for key, threshold in rules.items():
                    if "max_change" in key.lower() and change_abs > threshold:
                        warnings.append(f"Large absolute change to {parameter_name}: {change_abs} (max: {threshold})")
                        safety_level = SafetyLevel.WARNING

        # Check dependencies
        for dep in param.dependencies:
            if dep in self.current_parameters:
                dep_param = self.current_parameters[dep]
                recommendations.append(f"Consider adjusting {dep} when changing {parameter_name}")

        return {
            "safety_level": safety_level,
            "warnings": warnings,
            "recommendations": recommendations,
        }

    def _validate_backup(self, backup_file: Path) -> List[str]:
        """Validate a backup file."""
        errors = []

        if not backup_file.exists():
            return [f"Backup file not found: {backup_file}"]

        try:
            with open(backup_file, "r") as f:
                data = json.load(f)

            # Check required fields
            if "ecu_type" not in data:
                errors.append("Missing ecu_type")
            if "parameters" not in data:
                errors.append("Missing parameters")

            # Validate file hash
            file_hash = self._calculate_file_hash(backup_file)
            stored_hash = data.get("file_hash")
            if stored_hash and file_hash != stored_hash:
                errors.append("File integrity check failed")

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        return errors

    def _validate_parameter_data(self, name: str, data: Dict) -> List[str]:
        """Validate parameter data structure."""
        errors = []

        required_fields = ["name", "category", "current_value"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Parameter {name} missing field: {field}")

        return errors

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _load_current_parameters(self) -> None:
        """Load current parameters from ECU."""
        # This would be vendor-specific
        # For now, create example parameters
        self.current_parameters = {
            "fuel_map_base": ECUParameter(
                name="fuel_map_base",
                category="fuel_map",
                current_value=14.7,
                min_value=10.0,
                max_value=20.0,
                default_value=14.7,
                unit="AFR",
                description="Base fuel map value",
                safety_level=SafetyLevel.WARNING,
            ),
            "ignition_timing": ECUParameter(
                name="ignition_timing",
                category="ignition_timing",
                current_value=15.0,
                min_value=-10.0,
                max_value=45.0,
                default_value=15.0,
                unit="degrees",
                description="Ignition timing advance",
                safety_level=SafetyLevel.WARNING,
            ),
            "boost_target": ECUParameter(
                name="boost_target",
                category="boost_pressure",
                current_value=15.0,
                min_value=0.0,
                max_value=30.0,
                default_value=10.0,
                unit="PSI",
                description="Target boost pressure",
                safety_level=SafetyLevel.DANGEROUS,
            ),
            "rev_limit": ECUParameter(
                name="rev_limit",
                category="rev_limit",
                current_value=7000,
                min_value=3000,
                max_value=10000,
                default_value=6500,
                unit="RPM",
                description="Engine rev limit",
                safety_level=SafetyLevel.DANGEROUS,
            ),
        }

    def _read_from_ecu(self) -> Dict[str, Any]:
        """Read data from connected ECU (vendor-specific)."""
        # This would be vendor-specific implementation
        return {"ecu_type": self.ecu_type, "data": "..."}

    def _write_to_ecu(self, data: Dict[str, Any]) -> None:
        """Write data to ECU (vendor-specific)."""
        # This would be vendor-specific implementation
        pass

    def _write_parameter_to_ecu(self, parameter_name: str, value: Any) -> None:
        """Write single parameter to ECU."""
        # This would be vendor-specific implementation
        pass

    def _soft_reset(self) -> None:
        """Perform soft reset."""
        # Vendor-specific implementation
        pass

    def _hard_reset(self) -> None:
        """Perform hard reset."""
        # Vendor-specific implementation
        pass

    def _reset_to_factory(self) -> None:
        """Reset to factory defaults."""
        # Restore all parameters to defaults
        for param in self.current_parameters.values():
            if param.default_value is not None:
                param.current_value = param.default_value
                self._write_parameter_to_ecu(param.name, param.default_value)

    def _parse_ecu_file(self, data: bytes) -> Dict[str, Any]:
        """Parse ECU file data (vendor-specific)."""
        # This would be vendor-specific file format parsing
        return {"raw_data": data.hex()}

    def batch_set_parameters(
        self,
        parameters: Dict[str, Any],
        validate: bool = True,
        auto_backup: bool = True,
    ) -> Dict[str, Tuple[bool, List[str]]]:
        """
        Set multiple parameters at once.

        Args:
            parameters: Dictionary of parameter_name -> value
            validate: Validate each change
            auto_backup: Create backup before changes

        Returns:
            Dictionary of parameter_name -> (success, warnings)
        """
        results = {}

        # Single backup for all changes
        if auto_backup and self.auto_backup:
            self.backup_ecu(description=f"Auto-backup before batch change ({len(parameters)} parameters)")

        for param_name, new_value in parameters.items():
            success, warnings = self.set_parameter(
                param_name,
                new_value,
                validate=validate,
                auto_backup=False,  # Already backed up
            )
            results[param_name] = (success, warnings)

        return results

    def get_parameter_comparison(self, backup_id: str) -> Dict[str, Dict[str, Any]]:
        """
        Compare current parameters with a backup.

        Args:
            backup_id: Backup to compare with

        Returns:
            Dictionary of parameter_name -> {old_value, new_value, difference}
        """
        if backup_id not in self.backups:
            return {}

        backup = self.backups[backup_id]
        with open(backup.file_path, "r") as f:
            backup_data = json.load(f)

        backup_params = backup_data.get("parameters", {})
        comparison = {}

        for name, param in self.current_parameters.items():
            backup_param = backup_params.get(name, {})
            backup_value = backup_param.get("current_value")

            if backup_value is not None:
                current_value = param.current_value
                if isinstance(current_value, (int, float)) and isinstance(backup_value, (int, float)):
                    difference = current_value - backup_value
                    percent_change = (difference / backup_value * 100) if backup_value != 0 else 0
                else:
                    difference = None
                    percent_change = None

                comparison[name] = {
                    "old_value": backup_value,
                    "new_value": current_value,
                    "difference": difference,
                    "percent_change": percent_change,
                }

        return comparison

    def export_parameters(self, file_path: str | Path) -> bool:
        """
        Export current parameters to file.

        Args:
            file_path: Path to export file

        Returns:
            True if exported successfully
        """
        try:
            data = {
                "ecu_type": self.ecu_type,
                "timestamp": time.time(),
                "parameters": {name: asdict(param) for name, param in self.current_parameters.items()},
            }

            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)

            LOGGER.info("Exported parameters to %s", file_path)
            return True
        except Exception as e:
            LOGGER.error("Failed to export parameters: %s", e)
            return False

    def import_parameters(self, file_path: str | Path, apply: bool = False) -> Dict[str, Any]:
        """
        Import parameters from file.

        Args:
            file_path: Path to import file
            apply: Apply imported parameters immediately

        Returns:
            Imported parameters dictionary
        """
        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            parameters = data.get("parameters", {})

            if apply:
                for name, param_data in parameters.items():
                    if name in self.current_parameters:
                        value = param_data.get("current_value")
                        if value is not None:
                            self.set_parameter(name, value)

            LOGGER.info("Imported parameters from %s", file_path)
            return parameters
        except Exception as e:
            LOGGER.error("Failed to import parameters: %s", e)
            return {}

    def _notify(self, message: str, level: str = "info") -> None:
        """Send notification."""
        if self.notification_callback:
            try:
                self.notification_callback(message, level)
            except Exception as e:
                LOGGER.error("Error in notification callback: %s", e)


__all__ = [
    "ECUControl",
    "ECUParameter",
    "ECUChange",
    "ECUBackup",
    "ECUOperation",
    "SafetyLevel",
]

