"""
Automatic Engine Diagnostic System
Automatically diagnoses engine issues and provides fixes.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class IssueSeverity(Enum):
    """Issue severity levels."""
    CRITICAL = "critical"  # Engine won't run or severe damage risk
    HIGH = "high"  # Engine runs poorly, significant issues
    MEDIUM = "medium"  # Performance degradation
    LOW = "low"  # Minor optimization opportunities
    INFO = "info"  # Informational only


class IssueCategory(Enum):
    """Issue categories."""
    FUEL = "fuel"
    IGNITION = "ignition"
    AIR_INTAKE = "air_intake"
    EXHAUST = "exhaust"
    COOLING = "cooling"
    LUBRICATION = "lubrication"
    SENSOR = "sensor"
    TUNING = "tuning"
    EMISSIONS = "emissions"
    TURBO = "turbo"
    GENERAL = "general"


@dataclass
class DiagnosticIssue:
    """Diagnostic issue."""
    issue_id: str
    title: str
    description: str
    severity: IssueSeverity
    category: IssueCategory
    affected_parameters: List[str] = field(default_factory=list)
    current_values: Dict[str, Any] = field(default_factory=dict)
    expected_values: Dict[str, Any] = field(default_factory=dict)
    symptoms: List[str] = field(default_factory=list)
    possible_causes: List[str] = field(default_factory=list)
    confidence: float = 0.0  # 0.0 - 1.0
    detected_at: float = field(default_factory=time.time)


@dataclass
class AutoFix:
    """Automatic fix recommendation."""
    fix_id: str
    issue_id: str
    title: str
    description: str
    parameter_changes: Dict[str, Any] = field(default_factory=dict)
    safety_level: str = "safe"  # safe, caution, expert
    can_auto_apply: bool = True
    estimated_improvement: str = ""
    requires_approval: bool = True
    confidence: float = 0.0


@dataclass
class DiagnosticReport:
    """Complete diagnostic report."""
    report_id: str
    timestamp: float
    engine_type: str
    issues: List[DiagnosticIssue]
    fixes: List[AutoFix]
    overall_health_score: float  # 0.0 - 100.0
    summary: str
    recommendations: List[str] = field(default_factory=list)
    can_auto_fix: bool = False
    auto_fix_count: int = 0


class AutoEngineDiagnostic:
    """
    Automatic engine diagnostic system.
    
    Features:
    - Automatic issue detection
    - Beginner-friendly diagnostics
    - Auto-fix recommendations
    - Safety checks
    - Comprehensive reports
    """
    
    def __init__(self):
        """Initialize diagnostic system."""
        self.diagnostic_rules: List[Dict[str, Any]] = []
        self._load_diagnostic_rules()
    
    def diagnose_engine(
        self,
        telemetry_data: Dict[str, Any],
        vehicle_info: Optional[Dict[str, Any]] = None,
        is_diesel: bool = False,
    ) -> DiagnosticReport:
        """
        Perform automatic engine diagnosis.
        
        Args:
            telemetry_data: Current telemetry data
            vehicle_info: Optional vehicle information
            is_diesel: Whether engine is diesel
        
        Returns:
            DiagnosticReport
        """
        issues = []
        
        # Run diagnostic checks
        issues.extend(self._check_fuel_system(telemetry_data, is_diesel))
        issues.extend(self._check_ignition_system(telemetry_data, is_diesel))
        issues.extend(self._check_air_intake(telemetry_data, is_diesel))
        issues.extend(self._check_exhaust(telemetry_data, is_diesel))
        issues.extend(self._check_cooling(telemetry_data))
        issues.extend(self._check_sensors(telemetry_data))
        issues.extend(self._check_tuning(telemetry_data, is_diesel))
        
        if is_diesel:
            issues.extend(self._check_diesel_specific(telemetry_data))
        
        # Generate fixes
        fixes = self._generate_fixes(issues, telemetry_data, is_diesel)
        
        # Calculate health score
        health_score = self._calculate_health_score(issues)
        
        # Generate summary
        summary = self._generate_summary(issues, fixes, health_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(issues, fixes)
        
        # Check if auto-fix is possible
        can_auto_fix = any(f.can_auto_apply for f in fixes)
        auto_fix_count = sum(1 for f in fixes if f.can_auto_apply)
        
        return DiagnosticReport(
            report_id=f"diagnostic_{int(time.time())}",
            timestamp=time.time(),
            engine_type="diesel" if is_diesel else "gasoline",
            issues=issues,
            fixes=fixes,
            overall_health_score=health_score,
            summary=summary,
            recommendations=recommendations,
            can_auto_fix=can_auto_fix,
            auto_fix_count=auto_fix_count,
        )
    
    def _check_fuel_system(
        self,
        telemetry: Dict[str, Any],
        is_diesel: bool,
    ) -> List[DiagnosticIssue]:
        """Check fuel system."""
        issues = []
        
        # Check fuel pressure
        if is_diesel:
            fuel_pressure = telemetry.get("rail_pressure", telemetry.get("injection_pressure", 0))
            if fuel_pressure < 5000:  # PSI - too low for diesel
                issues.append(DiagnosticIssue(
                    issue_id="fuel_pressure_low",
                    title="Low Fuel Pressure",
                    description=f"Fuel pressure is {fuel_pressure:.0f} PSI, which is below normal operating range.",
                    severity=IssueSeverity.HIGH,
                    category=IssueCategory.FUEL,
                    affected_parameters=["rail_pressure", "injection_pressure"],
                    current_values={"fuel_pressure": fuel_pressure},
                    expected_values={"fuel_pressure": ">10000 PSI"},
                    symptoms=["Hard starting", "Rough idle", "Power loss"],
                    possible_causes=["Fuel pump failure", "Clogged fuel filter", "Leak in fuel system"],
                    confidence=0.85,
                ))
        else:
            fuel_pressure = telemetry.get("fuel_pressure", 0)
            if 0 < fuel_pressure < 30:  # PSI - too low for gasoline
                issues.append(DiagnosticIssue(
                    issue_id="fuel_pressure_low",
                    title="Low Fuel Pressure",
                    description=f"Fuel pressure is {fuel_pressure:.1f} PSI, which is below normal (35-45 PSI).",
                    severity=IssueSeverity.HIGH,
                    category=IssueCategory.FUEL,
                    affected_parameters=["fuel_pressure"],
                    current_values={"fuel_pressure": fuel_pressure},
                    expected_values={"fuel_pressure": "35-45 PSI"},
                    symptoms=["Hard starting", "Hesitation", "Power loss"],
                    possible_causes=["Fuel pump failure", "Clogged fuel filter", "Regulator issue"],
                    confidence=0.80,
                ))
        
        # Check air-fuel ratio
        afr = telemetry.get("afr", telemetry.get("lambda", 0))
        if afr > 0:
            if is_diesel:
                if afr < 14.0:  # Too rich for diesel
                    issues.append(DiagnosticIssue(
                        issue_id="afr_too_rich",
                        title="Air-Fuel Ratio Too Rich",
                        description=f"AFR is {afr:.1f}, indicating too much fuel (normal: 18-22).",
                        severity=IssueSeverity.MEDIUM,
                        category=IssueCategory.FUEL,
                        affected_parameters=["afr", "lambda"],
                        current_values={"afr": afr},
                        expected_values={"afr": "18-22"},
                        symptoms=["Black smoke", "Poor fuel economy", "Rough running"],
                        possible_causes=["Injector issues", "Tuning too rich", "Sensor failure"],
                        confidence=0.75,
                    ))
            else:
                if afr < 12.0:  # Too rich for gasoline
                    issues.append(DiagnosticIssue(
                        issue_id="afr_too_rich",
                        title="Air-Fuel Ratio Too Rich",
                        description=f"AFR is {afr:.1f}, indicating too much fuel (normal: 14.7).",
                        severity=IssueSeverity.MEDIUM,
                        category=IssueCategory.FUEL,
                        affected_parameters=["afr", "lambda"],
                        current_values={"afr": afr},
                        expected_values={"afr": "14.7"},
                        symptoms=["Black smoke", "Poor fuel economy", "Rough idle"],
                        possible_causes=["Injector leak", "Tuning too rich", "Sensor failure"],
                        confidence=0.75,
                    ))
        
        return issues
    
    def _check_ignition_system(
        self,
        telemetry: Dict[str, Any],
        is_diesel: bool,
    ) -> List[DiagnosticIssue]:
        """Check ignition system (gasoline only)."""
        issues = []
        
        if is_diesel:
            return issues  # No ignition system for diesel
        
        # Check timing
        timing = telemetry.get("timing_advance", telemetry.get("ignition_timing", 0))
        if timing < -10 or timing > 40:
            issues.append(DiagnosticIssue(
                issue_id="timing_out_of_range",
                title="Ignition Timing Out of Range",
                description=f"Ignition timing is {timing:.1f} degrees, outside normal range.",
                severity=IssueSeverity.HIGH,
                category=IssueCategory.IGNITION,
                affected_parameters=["timing_advance", "ignition_timing"],
                current_values={"timing": timing},
                expected_values={"timing": "10-30 degrees"},
                symptoms=["Knocking", "Power loss", "Poor fuel economy"],
                possible_causes=["Timing belt/chain issue", "Sensor failure", "Tuning error"],
                confidence=0.80,
            ))
        
        # Check for misfires
        misfire_count = telemetry.get("misfire_count", 0)
        if misfire_count > 0:
            issues.append(DiagnosticIssue(
                issue_id="misfires_detected",
                title="Engine Misfires Detected",
                description=f"Detected {misfire_count} misfire(s).",
                severity=IssueSeverity.HIGH,
                category=IssueCategory.IGNITION,
                affected_parameters=["misfire_count"],
                current_values={"misfire_count": misfire_count},
                expected_values={"misfire_count": 0},
                symptoms=["Rough running", "Power loss", "Check engine light"],
                possible_causes=["Spark plug failure", "Coil failure", "Fuel injector issue"],
                confidence=0.90,
            ))
        
        return issues
    
    def _check_air_intake(
        self,
        telemetry: Dict[str, Any],
        is_diesel: bool,
    ) -> List[DiagnosticIssue]:
        """Check air intake system."""
        issues = []
        
        # Check boost pressure
        boost = telemetry.get("boost_pressure", telemetry.get("boost_psi", 0))
        if boost < 0:
            issues.append(DiagnosticIssue(
                issue_id="boost_vacuum",
                title="Boost Pressure Below Zero",
                description=f"Boost pressure is {boost:.1f} PSI, indicating vacuum leak or turbo issue.",
                severity=IssueSeverity.MEDIUM,
                category=IssueCategory.AIR_INTAKE,
                affected_parameters=["boost_pressure"],
                current_values={"boost": boost},
                expected_values={"boost": ">0 PSI"},
                symptoms=["Power loss", "Poor throttle response"],
                possible_causes=["Vacuum leak", "Turbo failure", "Intercooler leak"],
                confidence=0.70,
            ))
        
        # Check IAT (Intake Air Temperature)
        iat = telemetry.get("iat", telemetry.get("intake_temp", 0))
        if iat > 150:  # Fahrenheit - too hot
            issues.append(DiagnosticIssue(
                issue_id="iat_too_high",
                title="Intake Air Temperature Too High",
                description=f"IAT is {iat:.0f}°F, which can cause power loss and detonation.",
                severity=IssueSeverity.MEDIUM,
                category=IssueCategory.AIR_INTAKE,
                affected_parameters=["iat", "intake_temp"],
                current_values={"iat": iat},
                expected_values={"iat": "<120°F"},
                symptoms=["Power loss", "Heat soak", "Detonation risk"],
                possible_causes=["Intercooler not working", "Heat soak", "Hot air intake"],
                confidence=0.75,
            ))
        
        return issues
    
    def _check_exhaust(
        self,
        telemetry: Dict[str, Any],
        is_diesel: bool,
    ) -> List[DiagnosticIssue]:
        """Check exhaust system."""
        issues = []
        
        # Check EGT (Exhaust Gas Temperature)
        egt = telemetry.get("egt", telemetry.get("exhaust_temp", 0))
        if is_diesel:
            if egt > 1650:  # Fahrenheit - critical for diesel
                issues.append(DiagnosticIssue(
                    issue_id="egt_critical",
                    title="Exhaust Temperature Critical",
                    description=f"EGT is {egt:.0f}°F, which is dangerously high (max: 1650°F).",
                    severity=IssueSeverity.CRITICAL,
                    category=IssueCategory.EXHAUST,
                    affected_parameters=["egt", "exhaust_temp"],
                    current_values={"egt": egt},
                    expected_values={"egt": "<1650°F"},
                    symptoms=["Risk of engine damage", "Turbo damage risk"],
                    possible_causes=["Too much fuel", "Too much boost", "Restricted exhaust"],
                    confidence=0.95,
                ))
        
        # Check backpressure
        backpressure = telemetry.get("exhaust_backpressure", 0)
        if backpressure > 5:  # PSI - too high
            issues.append(DiagnosticIssue(
                issue_id="exhaust_backpressure_high",
                title="High Exhaust Backpressure",
                description=f"Exhaust backpressure is {backpressure:.1f} PSI, indicating restriction.",
                severity=IssueSeverity.MEDIUM,
                category=IssueCategory.EXHAUST,
                affected_parameters=["exhaust_backpressure"],
                current_values={"backpressure": backpressure},
                expected_values={"backpressure": "<2 PSI"},
                symptoms=["Power loss", "Poor fuel economy"],
                possible_causes=["Clogged DPF", "Clogged catalytic converter", "Restricted exhaust"],
                confidence=0.70,
            ))
        
        return issues
    
    def _check_cooling(self, telemetry: Dict[str, Any]) -> List[DiagnosticIssue]:
        """Check cooling system."""
        issues = []
        
        coolant_temp = telemetry.get("coolant_temp", telemetry.get("ect", 0))
        if coolant_temp > 230:  # Fahrenheit - overheating
            issues.append(DiagnosticIssue(
                issue_id="overheating",
                title="Engine Overheating",
                description=f"Coolant temperature is {coolant_temp:.0f}°F, indicating overheating.",
                severity=IssueSeverity.CRITICAL,
                category=IssueCategory.COOLING,
                affected_parameters=["coolant_temp", "ect"],
                current_values={"coolant_temp": coolant_temp},
                expected_values={"coolant_temp": "180-210°F"},
                symptoms=["Engine damage risk", "Power loss", "Warning lights"],
                possible_causes=["Coolant leak", "Thermostat failure", "Water pump failure", "Radiator clogged"],
                confidence=0.90,
            ))
        elif coolant_temp < 160:  # Too cold
            issues.append(DiagnosticIssue(
                issue_id="coolant_too_cold",
                title="Engine Running Too Cold",
                description=f"Coolant temperature is {coolant_temp:.0f}°F, engine not reaching operating temperature.",
                severity=IssueSeverity.LOW,
                category=IssueCategory.COOLING,
                affected_parameters=["coolant_temp", "ect"],
                current_values={"coolant_temp": coolant_temp},
                expected_values={"coolant_temp": "180-210°F"},
                symptoms=["Poor fuel economy", "Increased emissions"],
                possible_causes=["Thermostat stuck open", "Cooling system issue"],
                confidence=0.70,
            ))
        
        return issues
    
    def _check_sensors(self, telemetry: Dict[str, Any]) -> List[DiagnosticIssue]:
        """Check sensor readings."""
        issues = []
        
        # Check for sensor failures (implausible values)
        rpm = telemetry.get("rpm", 0)
        if rpm < 0 or rpm > 10000:
            issues.append(DiagnosticIssue(
                issue_id="rpm_sensor_fault",
                title="RPM Sensor Fault",
                description=f"RPM reading is {rpm:.0f}, which is implausible.",
                severity=IssueSeverity.HIGH,
                category=IssueCategory.SENSOR,
                affected_parameters=["rpm"],
                current_values={"rpm": rpm},
                expected_values={"rpm": "0-8000"},
                symptoms=["Erratic readings", "Engine control issues"],
                possible_causes=["Sensor failure", "Wiring issue", "ECU problem"],
                confidence=0.85,
            ))
        
        return issues
    
    def _check_tuning(
        self,
        telemetry: Dict[str, Any],
        is_diesel: bool,
    ) -> List[DiagnosticIssue]:
        """Check tuning parameters."""
        issues = []
        
        # Check for tuning that's too aggressive
        boost = telemetry.get("boost_pressure", 0)
        if boost > 30:  # Very high boost
            issues.append(DiagnosticIssue(
                issue_id="boost_too_high",
                title="Boost Pressure Very High",
                description=f"Boost pressure is {boost:.1f} PSI, which may be too aggressive.",
                severity=IssueSeverity.MEDIUM,
                category=IssueCategory.TUNING,
                affected_parameters=["boost_pressure"],
                current_values={"boost": boost},
                expected_values={"boost": "<25 PSI (stock)"},
                symptoms=["Risk of engine damage", "Turbo stress"],
                possible_causes=["Tuning too aggressive", "Boost controller issue"],
                confidence=0.65,
            ))
        
        return issues
    
    def _check_diesel_specific(self, telemetry: Dict[str, Any]) -> List[DiagnosticIssue]:
        """Check diesel-specific issues."""
        issues = []
        
        # Check DPF pressure
        dpf_pressure = telemetry.get("dpf_pressure", 0)
        if dpf_pressure > 10:  # PSI - clogged
            issues.append(DiagnosticIssue(
                issue_id="dpf_clogged",
                title="DPF Clogged",
                description=f"DPF pressure is {dpf_pressure:.1f} PSI, indicating clogging.",
                severity=IssueSeverity.HIGH,
                category=IssueCategory.EMISSIONS,
                affected_parameters=["dpf_pressure"],
                current_values={"dpf_pressure": dpf_pressure},
                expected_values={"dpf_pressure": "<5 PSI"},
                symptoms=["Power loss", "Poor fuel economy", "Regeneration needed"],
                possible_causes=["DPF needs regeneration", "DPF needs replacement"],
                confidence=0.80,
            ))
        
        # Check EGR position
        egr_position = telemetry.get("egr_position", telemetry.get("egr_valve", 0))
        if egr_position > 80:  # % - stuck open
            issues.append(DiagnosticIssue(
                issue_id="egr_stuck_open",
                title="EGR Valve Stuck Open",
                description=f"EGR position is {egr_position:.0f}%, indicating valve may be stuck.",
                severity=IssueSeverity.MEDIUM,
                category=IssueCategory.EMISSIONS,
                affected_parameters=["egr_position", "egr_valve"],
                current_values={"egr_position": egr_position},
                expected_values={"egr_position": "0-50%"},
                symptoms=["Power loss", "Rough idle", "Increased emissions"],
                possible_causes=["EGR valve failure", "Carbon buildup"],
                confidence=0.70,
            ))
        
        return issues
    
    def _generate_fixes(
        self,
        issues: List[DiagnosticIssue],
        telemetry: Dict[str, Any],
        is_diesel: bool,
    ) -> List[AutoFix]:
        """Generate automatic fixes for issues."""
        fixes = []
        
        for issue in issues:
            fix = self._create_fix_for_issue(issue, telemetry, is_diesel)
            if fix:
                fixes.append(fix)
        
        return fixes
    
    def _create_fix_for_issue(
        self,
        issue: DiagnosticIssue,
        telemetry: Dict[str, Any],
        is_diesel: bool,
    ) -> Optional[AutoFix]:
        """Create fix for specific issue."""
        parameter_changes = {}
        can_auto_apply = False
        safety_level = "safe"
        
        if issue.issue_id == "fuel_pressure_low":
            # Can't auto-fix hardware issues
            return AutoFix(
                fix_id=f"fix_{issue.issue_id}",
                issue_id=issue.issue_id,
                title="Check Fuel System",
                description="Inspect fuel pump, filter, and lines. Replace components as needed.",
                can_auto_apply=False,
                requires_approval=True,
                confidence=0.80,
            )
        
        elif issue.issue_id == "afr_too_rich":
            # Can adjust fuel tuning
            current_afr = issue.current_values.get("afr", 0)
            if is_diesel:
                target_afr = 20.0
            else:
                target_afr = 14.7
            
            # Calculate fuel adjustment
            fuel_adjustment = (current_afr / target_afr) - 1.0
            parameter_changes["fuel_multiplier"] = 1.0 - (fuel_adjustment * 0.1)  # Reduce fuel by 10% of difference
            
            can_auto_apply = True
            safety_level = "safe"
        
        elif issue.issue_id == "timing_out_of_range":
            # Can adjust timing
            current_timing = issue.current_values.get("timing", 0)
            if current_timing < 0:
                target_timing = 10.0
            else:
                target_timing = 20.0
            
            parameter_changes["ignition_timing"] = target_timing
            can_auto_apply = True
            safety_level = "caution"
        
        elif issue.issue_id == "boost_too_high":
            # Can reduce boost
            current_boost = issue.current_values.get("boost", 0)
            target_boost = min(current_boost * 0.9, 25.0)  # Reduce by 10% or cap at 25 PSI
            parameter_changes["boost_limit"] = target_boost
            can_auto_apply = True
            safety_level = "caution"
        
        elif issue.issue_id == "egt_critical":
            # Must reduce fuel or boost
            current_egt = issue.current_values.get("egt", 0)
            if current_egt > 1650:
                # Reduce fuel by 5%
                parameter_changes["fuel_multiplier"] = 0.95
                parameter_changes["boost_limit"] = telemetry.get("boost_pressure", 0) * 0.9
                can_auto_apply = True
                safety_level = "expert"  # Critical - needs expert approval
        
        elif issue.issue_id == "coolant_too_cold":
            # Can't auto-fix hardware
            return AutoFix(
                fix_id=f"fix_{issue.issue_id}",
                issue_id=issue.issue_id,
                title="Check Thermostat",
                description="Inspect thermostat. May need replacement if stuck open.",
                can_auto_apply=False,
                requires_approval=True,
                confidence=0.75,
            )
        
        else:
            # Generic fix - inspection required
            return AutoFix(
                fix_id=f"fix_{issue.issue_id}",
                issue_id=issue.issue_id,
                title=f"Fix {issue.title}",
                description="Manual inspection and repair required.",
                can_auto_apply=False,
                requires_approval=True,
                confidence=0.60,
            )
        
        if parameter_changes:
            return AutoFix(
                fix_id=f"fix_{issue.issue_id}",
                issue_id=issue.issue_id,
                title=f"Auto-Fix: {issue.title}",
                description=f"Automatically adjust parameters to resolve: {issue.description}",
                parameter_changes=parameter_changes,
                safety_level=safety_level,
                can_auto_apply=can_auto_apply,
                estimated_improvement="Should resolve issue and improve engine operation",
                requires_approval=safety_level != "safe",
                confidence=0.75,
            )
        
        return None
    
    def _calculate_health_score(self, issues: List[DiagnosticIssue]) -> float:
        """Calculate overall engine health score."""
        if not issues:
            return 100.0
        
        severity_weights = {
            IssueSeverity.CRITICAL: -30.0,
            IssueSeverity.HIGH: -15.0,
            IssueSeverity.MEDIUM: -5.0,
            IssueSeverity.LOW: -2.0,
            IssueSeverity.INFO: 0.0,
        }
        
        score = 100.0
        for issue in issues:
            score += severity_weights.get(issue.severity, 0.0)
        
        return max(0.0, min(100.0, score))
    
    def _generate_summary(
        self,
        issues: List[DiagnosticIssue],
        fixes: List[AutoFix],
        health_score: float,
    ) -> str:
        """Generate diagnostic summary."""
        critical_count = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        high_count = sum(1 for i in issues if i.severity == IssueSeverity.HIGH)
        auto_fix_count = sum(1 for f in fixes if f.can_auto_apply)
        
        summary_parts = [
            f"Engine Health Score: {health_score:.0f}/100",
            f"Found {len(issues)} issue(s): {critical_count} critical, {high_count} high priority",
        ]
        
        if auto_fix_count > 0:
            summary_parts.append(f"{auto_fix_count} issue(s) can be automatically fixed")
        
        if health_score < 50:
            summary_parts.append("Engine requires immediate attention")
        elif health_score < 75:
            summary_parts.append("Engine has some issues that should be addressed")
        else:
            summary_parts.append("Engine is in good condition")
        
        return ". ".join(summary_parts)
    
    def _generate_recommendations(
        self,
        issues: List[DiagnosticIssue],
        fixes: List[AutoFix],
    ) -> List[str]:
        """Generate recommendations."""
        recommendations = []
        
        # Prioritize critical issues
        critical_issues = [i for i in issues if i.severity == IssueSeverity.CRITICAL]
        if critical_issues:
            recommendations.append("Address critical issues immediately to prevent engine damage")
        
        # Auto-fix recommendations
        auto_fixes = [f for f in fixes if f.can_auto_apply]
        if auto_fixes:
            recommendations.append(f"Apply {len(auto_fixes)} automatic fix(es) to improve engine operation")
        
        # Maintenance recommendations
        if any(i.category == IssueCategory.FUEL for i in issues):
            recommendations.append("Consider fuel system maintenance (filter, pump check)")
        
        if any(i.category == IssueCategory.COOLING for i in issues):
            recommendations.append("Inspect cooling system (thermostat, coolant level, radiator)")
        
        return recommendations
    
    def _load_diagnostic_rules(self) -> None:
        """Load diagnostic rules (placeholder for future expansion)."""
        # Can be expanded with ML-based rules
        pass

