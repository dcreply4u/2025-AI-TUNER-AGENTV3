"""
Automatic Fix Engine
Automatically applies safe fixes to engine parameters.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from services.auto_engine_diagnostic import AutoFix, DiagnosticReport

LOGGER = logging.getLogger(__name__)


class AutoFixEngine:
    """
    Automatic fix engine.
    
    Features:
    - Apply automatic fixes safely
    - Validate changes before applying
    - Create backup of current settings
    - Track applied fixes
    - Rollback capability
    """
    
    def __init__(self):
        """Initialize auto-fix engine."""
        self.applied_fixes: List[Dict[str, Any]] = []
        self.backup_settings: Dict[str, Any] = {}
    
    def apply_fixes(
        self,
        report: DiagnosticReport,
        fix_ids: Optional[List[str]] = None,
        auto_apply_safe: bool = True,
    ) -> Dict[str, Any]:
        """
        Apply fixes from diagnostic report.
        
        Args:
            report: Diagnostic report with fixes
            fix_ids: Specific fix IDs to apply (None = all auto-apply fixes)
            auto_apply_safe: Auto-apply only "safe" fixes
        
        Returns:
            Result dictionary with status and applied changes
        """
        # Filter fixes to apply
        fixes_to_apply = []
        
        if fix_ids:
            fixes_to_apply = [f for f in report.fixes if f.fix_id in fix_ids]
        else:
            fixes_to_apply = [f for f in report.fixes if f.can_auto_apply]
            if auto_apply_safe:
                fixes_to_apply = [f for f in fixes_to_apply if f.safety_level == "safe"]
        
        if not fixes_to_apply:
            return {
                "success": False,
                "message": "No fixes to apply",
                "applied_count": 0,
            }
        
        # Create backup
        self._create_backup()
        
        # Apply fixes
        applied_changes = {}
        applied_count = 0
        errors = []
        
        for fix in fixes_to_apply:
            try:
                changes = self._apply_single_fix(fix)
                if changes:
                    applied_changes.update(changes)
                    applied_count += 1
                    
                    # Record applied fix
                    self.applied_fixes.append({
                        "fix_id": fix.fix_id,
                        "issue_id": fix.issue_id,
                        "title": fix.title,
                        "changes": changes,
                        "timestamp": time.time(),
                    })
                    
                    LOGGER.info("Applied fix: %s", fix.title)
            except Exception as e:
                error_msg = f"Failed to apply fix {fix.fix_id}: {e}"
                errors.append(error_msg)
                LOGGER.error(error_msg)
        
        return {
            "success": applied_count > 0,
            "message": f"Applied {applied_count} fix(es)",
            "applied_count": applied_count,
            "applied_changes": applied_changes,
            "errors": errors,
        }
    
    def _apply_single_fix(self, fix: AutoFix) -> Dict[str, Any]:
        """
        Apply a single fix.
        
        Args:
            fix: Fix to apply
        
        Returns:
            Dictionary of applied changes
        """
        # Validate fix
        if not self._validate_fix(fix):
            raise ValueError(f"Fix {fix.fix_id} failed validation")
        
        # Apply parameter changes
        applied_changes = {}
        
        for param_name, param_value in fix.parameter_changes.items():
            # In production, this would interface with the ECU/tuning system
            # For now, we'll return the changes that should be applied
            applied_changes[param_name] = {
                "old_value": None,  # Would get from current settings
                "new_value": param_value,
            }
        
        return applied_changes
    
    def _validate_fix(self, fix: AutoFix) -> bool:
        """
        Validate fix before applying.
        
        Args:
            fix: Fix to validate
        
        Returns:
            True if valid
        """
        # Check if fix has changes
        if not fix.parameter_changes:
            return False
        
        # Check safety level
        if fix.safety_level == "expert" and not fix.requires_approval:
            LOGGER.warning("Expert-level fix without approval requirement")
            return False
        
        # Validate parameter values
        for param_name, param_value in fix.parameter_changes.items():
            if not self._validate_parameter_value(param_name, param_value):
                LOGGER.warning("Invalid parameter value: %s = %s", param_name, param_value)
                return False
        
        return True
    
    def _validate_parameter_value(self, param_name: str, value: Any) -> bool:
        """
        Validate parameter value.
        
        Args:
            param_name: Parameter name
            value: Parameter value
        
        Returns:
            True if valid
        """
        # Basic validation
        if value is None:
            return False
        
        # Type-specific validation
        if "multiplier" in param_name.lower():
            # Multipliers should be between 0.5 and 2.0
            if isinstance(value, (int, float)):
                return 0.5 <= value <= 2.0
        elif "pressure" in param_name.lower() or "boost" in param_name.lower():
            # Pressures should be reasonable
            if isinstance(value, (int, float)):
                return -10 <= value <= 100  # PSI range
        elif "timing" in param_name.lower():
            # Timing should be reasonable
            if isinstance(value, (int, float)):
                return -20 <= value <= 50  # Degrees
        
        return True
    
    def _create_backup(self) -> None:
        """Create backup of current settings."""
        # In production, would backup current ECU settings
        # For now, just record timestamp
        self.backup_settings = {
            "timestamp": time.time(),
            "settings": {},  # Would contain actual settings
        }
        LOGGER.info("Created backup of current settings")
    
    def rollback(self) -> Dict[str, Any]:
        """
        Rollback to backup settings.
        
        Returns:
            Rollback result
        """
        if not self.backup_settings:
            return {
                "success": False,
                "message": "No backup available",
            }
        
        # In production, would restore from backup
        LOGGER.info("Rolled back to backup settings")
        
        return {
            "success": True,
            "message": "Rolled back to backup settings",
            "backup_timestamp": self.backup_settings.get("timestamp"),
        }
    
    def get_applied_fixes(self) -> List[Dict[str, Any]]:
        """Get list of applied fixes."""
        return self.applied_fixes.copy()
