"""
Parameter Limit Monitoring Algorithm

Constantly checks sensor readings against user-defined or factory-defined
safe limits. Provides immediate alerts if any critical parameter exceeds
safe operating ranges.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

LOGGER = logging.getLogger(__name__)


class LimitSeverity(Enum):
    """Limit violation severity."""

    CRITICAL = "critical"  # Immediate danger - system should take action
    WARNING = "warning"  # Approaching limit - user should be aware
    CAUTION = "caution"  # Getting close to limit
    NORMAL = "normal"  # Within safe range


@dataclass
class ParameterLimit:
    """Parameter limit definition."""

    parameter_name: str
    min_safe: Optional[float] = None  # Minimum safe value
    max_safe: Optional[float] = None  # Maximum safe value
    min_warning: Optional[float] = None  # Warning threshold (approaching min)
    max_warning: Optional[float] = None  # Warning threshold (approaching max)
    min_caution: Optional[float] = None  # Caution threshold
    max_caution: Optional[float] = None  # Caution threshold
    unit: str = ""
    description: str = ""
    auto_action: Optional[str] = None  # "reduce_boost", "limit_rpm", etc.


@dataclass
class LimitViolation:
    """Detected limit violation."""

    parameter_name: str
    current_value: float
    limit_type: str  # "min_safe", "max_safe", "min_warning", etc.
    limit_value: float
    severity: LimitSeverity
    timestamp: float
    duration: float = 0.0  # How long violation has been active
    recommendation: str = ""


@dataclass
class LimitStatus:
    """Current status of all monitored parameters."""

    parameters: Dict[str, ParameterLimit]
    violations: List[LimitViolation]
    timestamp: float = field(default_factory=time.time)
    overall_status: LimitSeverity = LimitSeverity.NORMAL


class ParameterLimitMonitor:
    """Parameter limit monitoring algorithm."""

    def __init__(self, limits: Optional[Dict[str, ParameterLimit]] = None):
        """
        Initialize parameter limit monitor.

        Args:
            limits: Dictionary of parameter limits
        """
        self.limits = limits or self._get_default_limits()
        self.violation_history: Dict[str, List[LimitViolation]] = {}
        self.current_violations: Dict[str, LimitViolation] = {}
        self.violation_start_times: Dict[str, float] = {}

    def check_parameters(self, data: Dict[str, float]) -> LimitStatus:
        """
        Check all parameters against limits.

        Args:
            data: Current sensor data

        Returns:
            LimitStatus with all violations
        """
        violations = []
        overall_severity = LimitSeverity.NORMAL

        for parameter_name, limit in self.limits.items():
            if parameter_name not in data:
                continue

            current_value = float(data[parameter_name])
            violation = self._check_parameter(parameter_name, current_value, limit)

            if violation:
                violations.append(violation)
                self._update_violation_tracking(parameter_name, violation)

                # Update overall severity (highest wins)
                if violation.severity.value > overall_severity.value:
                    overall_severity = violation.severity
            else:
                # Clear violation if it was active
                if parameter_name in self.current_violations:
                    del self.current_violations[parameter_name]
                if parameter_name in self.violation_start_times:
                    del self.violation_start_times[parameter_name]

        return LimitStatus(
            parameters=self.limits,
            violations=violations,
            overall_status=overall_severity,
        )

    def _check_parameter(
        self, parameter_name: str, current_value: float, limit: ParameterLimit
    ) -> Optional[LimitViolation]:
        """Check a single parameter against its limits."""
        timestamp = time.time()

        # Check critical limits first (min/max safe)
        if limit.min_safe is not None and current_value < limit.min_safe:
            return LimitViolation(
                parameter_name=parameter_name,
                current_value=current_value,
                limit_type="min_safe",
                limit_value=limit.min_safe,
                severity=LimitSeverity.CRITICAL,
                timestamp=timestamp,
                recommendation=f"{parameter_name} below critical minimum ({limit.min_safe} {limit.unit}). "
                "Immediate action required.",
            )

        if limit.max_safe is not None and current_value > limit.max_safe:
            return LimitViolation(
                parameter_name=parameter_name,
                current_value=current_value,
                limit_type="max_safe",
                limit_value=limit.max_safe,
                severity=LimitSeverity.CRITICAL,
                timestamp=timestamp,
                recommendation=f"{parameter_name} above critical maximum ({limit.max_safe} {limit.unit}). "
                "Immediate action required.",
            )

        # Check warning limits
        if limit.min_warning is not None and current_value < limit.min_warning:
            return LimitViolation(
                parameter_name=parameter_name,
                current_value=current_value,
                limit_type="min_warning",
                limit_value=limit.min_warning,
                severity=LimitSeverity.WARNING,
                timestamp=timestamp,
                recommendation=f"{parameter_name} approaching minimum limit ({limit.min_warning} {limit.unit}). "
                "Monitor closely.",
            )

        if limit.max_warning is not None and current_value > limit.max_warning:
            return LimitViolation(
                parameter_name=parameter_name,
                current_value=current_value,
                limit_type="max_warning",
                limit_value=limit.max_warning,
                severity=LimitSeverity.WARNING,
                timestamp=timestamp,
                recommendation=f"{parameter_name} approaching maximum limit ({limit.max_warning} {limit.unit}). "
                "Monitor closely.",
            )

        # Check caution limits
        if limit.min_caution is not None and current_value < limit.min_caution:
            return LimitViolation(
                parameter_name=parameter_name,
                current_value=current_value,
                limit_type="min_caution",
                limit_value=limit.min_caution,
                severity=LimitSeverity.CAUTION,
                timestamp=timestamp,
                recommendation=f"{parameter_name} getting close to minimum ({limit.min_caution} {limit.unit}).",
            )

        if limit.max_caution is not None and current_value > limit.max_caution:
            return LimitViolation(
                parameter_name=parameter_name,
                current_value=current_value,
                limit_type="max_caution",
                limit_value=limit.max_caution,
                severity=LimitSeverity.CAUTION,
                timestamp=timestamp,
                recommendation=f"{parameter_name} getting close to maximum ({limit.max_caution} {limit.unit}).",
            )

        return None

    def _update_violation_tracking(self, parameter_name: str, violation: LimitViolation) -> None:
        """Update violation tracking for duration calculation."""
        if parameter_name not in self.current_violations:
            # New violation
            self.current_violations[parameter_name] = violation
            self.violation_start_times[parameter_name] = violation.timestamp
        else:
            # Update existing violation duration
            start_time = self.violation_start_times[parameter_name]
            violation.duration = violation.timestamp - start_time
            self.current_violations[parameter_name] = violation

        # Add to history
        if parameter_name not in self.violation_history:
            self.violation_history[parameter_name] = []
        self.violation_history[parameter_name].append(violation)

    def add_limit(self, limit: ParameterLimit) -> None:
        """Add or update a parameter limit."""
        self.limits[limit.parameter_name] = limit

    def remove_limit(self, parameter_name: str) -> None:
        """Remove a parameter limit."""
        if parameter_name in self.limits:
            del self.limits[parameter_name]

    def get_violation_summary(self) -> Dict[str, Any]:
        """Get summary of current violations."""
        critical_count = sum(
            1 for v in self.current_violations.values() if v.severity == LimitSeverity.CRITICAL
        )
        warning_count = sum(
            1 for v in self.current_violations.values() if v.severity == LimitSeverity.WARNING
        )
        caution_count = sum(
            1 for v in self.current_violations.values() if v.severity == LimitSeverity.CAUTION
        )

        return {
            "total_violations": len(self.current_violations),
            "critical": critical_count,
            "warnings": warning_count,
            "cautions": caution_count,
            "violations": [
                {
                    "parameter": v.parameter_name,
                    "value": v.current_value,
                    "limit": v.limit_value,
                    "severity": v.severity.value,
                    "duration": v.duration,
                }
                for v in self.current_violations.values()
            ],
        }

    def _get_default_limits(self) -> Dict[str, ParameterLimit]:
        """Get default parameter limits for common sensors."""
        return {
            "Coolant_Temp": ParameterLimit(
                parameter_name="Coolant_Temp",
                min_safe=160.0,
                max_safe=240.0,
                min_warning=170.0,
                max_warning=220.0,
                min_caution=175.0,
                max_caution=210.0,
                unit="°F",
                description="Engine coolant temperature",
                auto_action="reduce_power",
            ),
            "Oil_Pressure": ParameterLimit(
                parameter_name="Oil_Pressure",
                min_safe=15.0,
                max_safe=100.0,
                min_warning=20.0,
                max_warning=90.0,
                min_caution=25.0,
                max_caution=80.0,
                unit="psi",
                description="Engine oil pressure",
                auto_action="reduce_rpm",
            ),
            "Boost_Pressure": ParameterLimit(
                parameter_name="Boost_Pressure",
                min_safe=-5.0,
                max_safe=35.0,
                min_warning=0.0,
                max_warning=30.0,
                min_caution=5.0,
                max_caution=25.0,
                unit="psi",
                description="Turbo boost pressure",
                auto_action="reduce_boost",
            ),
            "AFR": ParameterLimit(
                parameter_name="AFR",
                min_safe=11.0,
                max_safe=16.5,
                min_warning=12.0,
                max_warning=16.0,
                min_caution=12.5,
                max_caution=15.5,
                unit=":1",
                description="Air-fuel ratio",
                auto_action="enrich_fuel",
            ),
            "Engine_RPM": ParameterLimit(
                parameter_name="Engine_RPM",
                min_safe=500.0,
                max_safe=9000.0,
                min_warning=800.0,
                max_warning=8500.0,
                min_caution=1000.0,
                max_caution=8000.0,
                unit="rpm",
                description="Engine RPM",
                auto_action="limit_rpm",
            ),
        }


__all__ = [
    "ParameterLimitMonitor",
    "ParameterLimit",
    "LimitViolation",
    "LimitStatus",
    "LimitSeverity",
]



