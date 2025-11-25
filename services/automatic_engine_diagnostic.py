"""
Automatic Engine Diagnostic System
Automatically diagnoses engine problems and suggests fixes.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

LOGGER = logging.getLogger(__name__)


class ProblemSeverity(Enum):
    """Problem severity levels."""
    CRITICAL = "critical"  # Engine won't run or severe damage risk
    HIGH = "high"  # Engine runs poorly, needs immediate attention
    MEDIUM = "medium"  # Performance issue, should be addressed
    LOW = "low"  # Minor issue, can be addressed later
    INFO = "info"  # Informational, optimization opportunity


class ProblemCategory(Enum):
    """Problem categories."""
    FUEL = "fuel"
    IGNITION = "ignition"
    AIR_INTAKE = "air_intake"
    EXHAUST = "exhaust"
    COOLING = "cooling"
    LUBRICATION = "lubrication"
    EMISSIONS = "emissions"
    SENSOR = "sensor"
    TUNING = "tuning"
    MECHANICAL = "mechanical"


@dataclass
class DiagnosticProblem:
    """Diagnosed engine problem."""
    problem_id: str
    category: ProblemCategory
    severity: ProblemSeverity
    title: str
    description: str
    detected_at: float
    symptoms: List[str] = field(default_factory=list)
    root_cause: Optional[str] = None
    affected_parameters: List[str] = field(default_factory=list)
    confidence: float = 0.0  # 0.0 - 1.0
    data_evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DiagnosticFix:
    """Fix for a diagnosed problem."""
    fix_id: str
    problem_id: str
    parameter_name: str
    current_value: float
    recommended_value: float
    fix_type: str  # "adjust", "replace", "calibrate", "reset"
    description: str
    safety_level: str = "safe"  # safe, caution, warning
    estimated_improvement: str = ""
    requires_approval: bool = True


@dataclass
class DiagnosticReport:
    """Complete diagnostic report."""
    report_id: str
    timestamp: float
    engine_type: str  # gasoline, diesel
    problems: List[DiagnosticProblem]
    fixes: List[DiagnosticFix]
    overall_health_score: float  # 0.0 - 100.0
    summary: str
    recommendations: List[str] = field(default_factory=list)
    can_auto_fix: bool = False


class AutomaticEngineDiagnostic:
    """
    Automatic engine diagnostic system.
    
    Features:
    - Automatic problem detection
    - Root cause analysis
    - Fix recommendations
    - Auto-fix capability
    - Health scoring
    - Beginner-friendly reports
    """
    
    def __init__(self):
        """Initialize automatic engine diagnostic."""
        self.diagnostic_rules: List[Dict[str, Any]] = []
        self._initialize_diagnostic_rules()
    
    def diagnose_engine(
        self,
        telemetry_data: Dict[str, Any],
        current_parameters: Dict[str, float],
        vehicle_info: Optional[Dict[str, Any]] = None,
        is_diesel: bool = False,
    ) -> DiagnosticReport:
        """
        Perform automatic engine diagnosis.
        
        Args:
            telemetry_data: Current telemetry data
            current_parameters: Current ECU parameters
            vehicle_info: Optional vehicle information
            is_diesel: Whether engine is diesel
        
        Returns:
            DiagnosticReport
        """
        problems = []
        fixes = []
        
        # Run diagnostic checks
        problems.extend(self._check_fuel_system(telemetry_data, current_parameters, is_diesel))
        problems.extend(self._check_ignition_system(telemetry_data, current_parameters, is_diesel))
        problems.extend(self._check_air_intake(telemetry_data, current_parameters))
        problems.extend(self._check_exhaust(telemetry_data, current_parameters, is_diesel))
        problems.extend(self._check_cooling(telemetry_data))
        problems.extend(self._check_sensors(telemetry_data))
        problems.extend(self._check_tuning(telemetry_data, current_parameters, is_diesel))
        
        # Generate fixes for problems
        for problem in problems:
            problem_fixes = self._generate_fixes(problem, telemetry_data, current_parameters, is_diesel)
            fixes.extend(problem_fixes)
        
        # Calculate health score
        health_score = self._calculate_health_score(problems)
        
        # Determine if auto-fix is safe
        can_auto_fix = all(
            f.safety_level == "safe" and not f.requires_approval
            for f in fixes
        ) and len(fixes) > 0
        
        # Generate summary
        summary = self._generate_summary(problems, fixes, health_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(problems, fixes)
        
        report = DiagnosticReport(
            report_id=f"diagnostic_{int(time.time())}",
            timestamp=time.time(),
            engine_type="diesel" if is_diesel else "gasoline",
            problems=problems,
            fixes=fixes,
            overall_health_score=health_score,
            summary=summary,
            recommendations=recommendations,
            can_auto_fix=can_auto_fix,
        )
        
        LOGGER.info("Engine diagnosis complete: %d problems, %d fixes, health: %.1f%%",
                   len(problems), len(fixes), health_score)
        
        return report
    
    def _check_fuel_system(
        self,
        telemetry: Dict[str, Any],
        parameters: Dict[str, float],
        is_diesel: bool,
    ) -> List[DiagnosticProblem]:
        """Check fuel system."""
        problems = []
        
        # Check AFR/Lambda
        afr = telemetry.get("afr", telemetry.get("lambda", 0))
        if afr > 0:
            if is_diesel:
                # Diesel AFR range: 18-22 typically
                if afr < 16:
                    problems.append(DiagnosticProblem(
                        problem_id=f"fuel_rich_{int(time.time())}",
                        category=ProblemCategory.FUEL,
                        severity=ProblemSeverity.HIGH,
                        title="Fuel Mixture Too Rich",
                        description=f"Air-fuel ratio is {afr:.1f}, which is too rich for diesel. This can cause excessive smoke and poor efficiency.",
                        detected_at=time.time(),
                        symptoms=["Excessive smoke", "Poor fuel economy", "Reduced power"],
                        root_cause="Fuel quantity too high or air intake restricted",
                        affected_parameters=["fuel_quantity", "injection_pressure"],
                        confidence=0.85,
                        data_evidence={"afr": afr, "normal_range": "18-22"},
                    ))
                elif afr > 24:
                    problems.append(DiagnosticProblem(
                        problem_id=f"fuel_lean_{int(time.time())}",
                        category=ProblemCategory.FUEL,
                        severity=ProblemSeverity.CRITICAL,
                        title="Fuel Mixture Too Lean",
                        description=f"Air-fuel ratio is {afr:.1f}, which is dangerously lean. This can cause engine damage.",
                        detected_at=time.time(),
                        symptoms=["High EGT", "Engine knock", "Potential damage"],
                        root_cause="Insufficient fuel delivery",
                        affected_parameters=["fuel_quantity", "injection_pressure"],
                        confidence=0.90,
                        data_evidence={"afr": afr, "normal_range": "18-22"},
                    ))
            else:
                # Gasoline AFR range: 12.5-15.0 typically
                if afr < 12.0:
                    problems.append(DiagnosticProblem(
                        problem_id=f"fuel_rich_{int(time.time())}",
                        category=ProblemCategory.FUEL,
                        severity=ProblemSeverity.MEDIUM,
                        title="Fuel Mixture Too Rich",
                        description=f"Air-fuel ratio is {afr:.1f}, which is too rich. This causes poor fuel economy and may foul plugs.",
                        detected_at=time.time(),
                        symptoms=["Poor fuel economy", "Black smoke", "Fouled spark plugs"],
                        root_cause="Fuel map too rich or injector issue",
                        affected_parameters=["afr_target", "fuel_map"],
                        confidence=0.80,
                        data_evidence={"afr": afr, "normal_range": "12.5-15.0"},
                    ))
                elif afr > 16.0:
                    problems.append(DiagnosticProblem(
                        problem_id=f"fuel_lean_{int(time.time())}",
                        category=ProblemCategory.FUEL,
                        severity=ProblemSeverity.HIGH,
                        title="Fuel Mixture Too Lean",
                        description=f"Air-fuel ratio is {afr:.1f}, which is too lean. This can cause engine damage.",
                        detected_at=time.time(),
                        symptoms=["Engine knock", "High EGT", "Potential damage"],
                        root_cause="Fuel map too lean or fuel delivery issue",
                        affected_parameters=["afr_target", "fuel_map"],
                        confidence=0.85,
                        data_evidence={"afr": afr, "normal_range": "12.5-15.0"},
                    ))
        
        # Check fuel pressure
        fuel_pressure = telemetry.get("fuel_pressure", telemetry.get("rail_pressure", 0))
        if fuel_pressure > 0:
            if is_diesel:
                # Diesel: typically 15,000-30,000 PSI
                if fuel_pressure < 10000:
                    problems.append(DiagnosticProblem(
                        problem_id=f"low_fuel_pressure_{int(time.time())}",
                        category=ProblemCategory.FUEL,
                        severity=ProblemSeverity.HIGH,
                        title="Low Fuel Pressure",
                        description=f"Fuel pressure is {fuel_pressure:.0f} PSI, which is below normal range (15,000-30,000 PSI).",
                        detected_at=time.time(),
                        symptoms=["Poor atomization", "Reduced power", "Rough idle"],
                        root_cause="Fuel pump issue or leak",
                        affected_parameters=["injection_pressure"],
                        confidence=0.75,
                    ))
            else:
                # Gasoline: typically 40-60 PSI
                if fuel_pressure < 30:
                    problems.append(DiagnosticProblem(
                        problem_id=f"low_fuel_pressure_{int(time.time())}",
                        category=ProblemCategory.FUEL,
                        severity=ProblemSeverity.HIGH,
                        title="Low Fuel Pressure",
                        description=f"Fuel pressure is {fuel_pressure:.1f} PSI, which is below normal (40-60 PSI).",
                        detected_at=time.time(),
                        symptoms=["Lean condition", "Poor performance", "Hard starting"],
                        root_cause="Fuel pump or regulator issue",
                        affected_parameters=["fuel_pressure"],
                        confidence=0.80,
                    ))
        
        return problems
    
    def _check_ignition_system(
        self,
        telemetry: Dict[str, Any],
        parameters: Dict[str, float],
        is_diesel: bool,
    ) -> List[DiagnosticProblem]:
        """Check ignition system (gasoline) or injection timing (diesel)."""
        problems = []
        
        if is_diesel:
            # Check injection timing
            timing = parameters.get("injection_timing", telemetry.get("injection_timing", 0))
            if timing < -5 or timing > 25:
                problems.append(DiagnosticProblem(
                    problem_id=f"timing_issue_{int(time.time())}",
                    category=ProblemCategory.IGNITION,
                    severity=ProblemSeverity.MEDIUM,
                    title="Injection Timing Out of Range",
                    description=f"Injection timing is {timing:.1f} degrees, which may be outside optimal range.",
                    detected_at=time.time(),
                    symptoms=["Reduced power", "Poor efficiency", "Increased emissions"],
                    root_cause="Timing map needs adjustment",
                    affected_parameters=["injection_timing"],
                    confidence=0.70,
                ))
        else:
            # Check ignition timing (gasoline)
            timing = parameters.get("ignition_timing", telemetry.get("ignition_timing", 0))
            knock = telemetry.get("knock", telemetry.get("knock_sensor", 0))
            
            if knock > 5:  # Significant knock
                problems.append(DiagnosticProblem(
                    problem_id=f"engine_knock_{int(time.time())}",
                    category=ProblemCategory.IGNITION,
                    severity=ProblemSeverity.CRITICAL,
                    title="Engine Knock Detected",
                    description=f"Engine knock detected ({knock:.1f}). This can cause engine damage.",
                    detected_at=time.time(),
                    symptoms=["Knocking sound", "Potential engine damage"],
                    root_cause="Ignition timing too advanced or low octane fuel",
                    affected_parameters=["ignition_timing"],
                    confidence=0.95,
                    data_evidence={"knock": knock, "timing": timing},
                ))
        
        return problems
    
    def _check_air_intake(
        self,
        telemetry: Dict[str, Any],
        parameters: Dict[str, float],
    ) -> List[DiagnosticProblem]:
        """Check air intake system."""
        problems = []
        
        # Check IAT (Intake Air Temperature)
        iat = telemetry.get("iat", telemetry.get("intake_temp", 0))
        if iat > 150:  # Fahrenheit - too hot
            problems.append(DiagnosticProblem(
                problem_id=f"high_iat_{int(time.time())}",
                category=ProblemCategory.AIR_INTAKE,
                severity=ProblemSeverity.MEDIUM,
                title="High Intake Air Temperature",
                description=f"Intake air temperature is {iat:.0f}°F, which is high. This reduces power and increases knock risk.",
                detected_at=time.time(),
                symptoms=["Reduced power", "Increased knock risk"],
                root_cause="Intercooler not working or heat soak",
                affected_parameters=[],
                confidence=0.75,
            ))
        
        # Check boost (if turbocharged)
        boost = telemetry.get("boost_pressure", telemetry.get("boost_psi", 0))
        if boost > 0:
            # Check if boost is consistent
            # This would need historical data, simplified for now
            pass
        
        return problems
    
    def _check_exhaust(
        self,
        telemetry: Dict[str, Any],
        parameters: Dict[str, float],
        is_diesel: bool,
    ) -> List[DiagnosticProblem]:
        """Check exhaust system."""
        problems = []
        
        # Check EGT (Exhaust Gas Temperature)
        egt = telemetry.get("egt", telemetry.get("exhaust_temp", 0))
        if egt > 0:
            if is_diesel:
                if egt > 1650:  # Fahrenheit - critical for diesel
                    problems.append(DiagnosticProblem(
                        problem_id=f"high_egt_{int(time.time())}",
                        category=ProblemCategory.EXHAUST,
                        severity=ProblemSeverity.CRITICAL,
                        title="Critical Exhaust Gas Temperature",
                        description=f"EGT is {egt:.0f}°F, which is dangerously high. Engine damage is imminent.",
                        detected_at=time.time(),
                        symptoms=["Extremely high exhaust temp", "Risk of engine damage"],
                        root_cause="Too much fuel, too much boost, or exhaust restriction",
                        affected_parameters=["fuel_quantity", "boost_pressure"],
                        confidence=0.95,
                    ))
                elif egt > 1400:
                    problems.append(DiagnosticProblem(
                        problem_id=f"high_egt_warning_{int(time.time())}",
                        category=ProblemCategory.EXHAUST,
                        severity=ProblemSeverity.HIGH,
                        title="High Exhaust Gas Temperature",
                        description=f"EGT is {egt:.0f}°F, which is high. Monitor closely.",
                        detected_at=time.time(),
                        symptoms=["High exhaust temp"],
                        root_cause="Fuel/boost ratio needs adjustment",
                        affected_parameters=["fuel_quantity", "boost_pressure"],
                        confidence=0.80,
                    ))
        
        return problems
    
    def _check_cooling(self, telemetry: Dict[str, Any]) -> List[DiagnosticProblem]:
        """Check cooling system."""
        problems = []
        
        coolant_temp = telemetry.get("coolant_temp", telemetry.get("water_temp", 0))
        if coolant_temp > 220:  # Fahrenheit - overheating
            problems.append(DiagnosticProblem(
                problem_id=f"overheating_{int(time.time())}",
                category=ProblemCategory.COOLING,
                severity=ProblemSeverity.CRITICAL,
                title="Engine Overheating",
                description=f"Coolant temperature is {coolant_temp:.0f}°F, which indicates overheating.",
                detected_at=time.time(),
                symptoms=["High coolant temp", "Risk of engine damage"],
                root_cause="Cooling system issue",
                affected_parameters=[],
                confidence=0.90,
            ))
        elif coolant_temp > 200:
            problems.append(DiagnosticProblem(
                problem_id=f"high_coolant_temp_{int(time.time())}",
                category=ProblemCategory.COOLING,
                severity=ProblemSeverity.MEDIUM,
                title="High Coolant Temperature",
                description=f"Coolant temperature is {coolant_temp:.0f}°F, which is elevated.",
                detected_at=time.time(),
                symptoms=["Elevated coolant temp"],
                root_cause="Cooling system needs attention",
                affected_parameters=[],
                confidence=0.70,
            ))
        
        return problems
    
    def _check_sensors(self, telemetry: Dict[str, Any]) -> List[DiagnosticProblem]:
        """Check sensor readings."""
        problems = []
        
        # Check for stuck sensors (values not changing)
        # This would need historical data, simplified for now
        
        # Check for out-of-range values
        rpm = telemetry.get("rpm", 0)
        if rpm > 0 and rpm < 500:  # Very low RPM
            problems.append(DiagnosticProblem(
                problem_id=f"low_rpm_{int(time.time())}",
                category=ProblemCategory.SENSOR,
                severity=ProblemSeverity.MEDIUM,
                title="Low RPM Reading",
                description=f"RPM is {rpm:.0f}, which seems low. Check sensor or engine condition.",
                detected_at=time.time(),
                symptoms=["Low RPM"],
                root_cause="Sensor issue or engine problem",
                affected_parameters=[],
                confidence=0.60,
            ))
        
        return problems
    
    def _check_tuning(
        self,
        telemetry: Dict[str, Any],
        parameters: Dict[str, float],
        is_diesel: bool,
    ) -> List[DiagnosticProblem]:
        """Check tuning parameters."""
        problems = []
        
        # Check if parameters are within reasonable ranges
        # This is simplified - would need vehicle-specific limits
        
        return problems
    
    def _generate_fixes(
        self,
        problem: DiagnosticProblem,
        telemetry: Dict[str, Any],
        parameters: Dict[str, float],
        is_diesel: bool,
    ) -> List[DiagnosticFix]:
        """Generate fixes for a problem."""
        fixes = []
        
        # Generate fixes based on problem type
        if problem.category == ProblemCategory.FUEL:
            if "rich" in problem.title.lower():
                # Fix rich condition
                if is_diesel:
                    current_fuel = parameters.get("fuel_quantity", 0)
                    if current_fuel > 0:
                        fixes.append(DiagnosticFix(
                            fix_id=f"fix_{problem.problem_id}",
                            problem_id=problem.problem_id,
                            parameter_name="fuel_quantity",
                            current_value=current_fuel,
                            recommended_value=current_fuel * 0.95,  # Reduce fuel by 5%
                            fix_type="adjust",
                            description="Reduce fuel quantity to correct rich condition",
                            safety_level="safe",
                            estimated_improvement="Better AFR, reduced smoke",
                            requires_approval=False,
                        ))
                else:
                    current_afr = parameters.get("afr_target", 14.7)
                    if current_afr < 14.0:
                        fixes.append(DiagnosticFix(
                            fix_id=f"fix_{problem.problem_id}",
                            problem_id=problem.problem_id,
                            parameter_name="afr_target",
                            current_value=current_afr,
                            recommended_value=14.5,  # Leaner target
                            fix_type="adjust",
                            description="Adjust AFR target to correct rich condition",
                            safety_level="safe",
                            estimated_improvement="Better fuel economy, reduced smoke",
                            requires_approval=False,
                        ))
            
            elif "lean" in problem.title.lower():
                # Fix lean condition
                if is_diesel:
                    current_fuel = parameters.get("fuel_quantity", 0)
                    if current_fuel > 0:
                        fixes.append(DiagnosticFix(
                            fix_id=f"fix_{problem.problem_id}",
                            problem_id=problem.problem_id,
                            parameter_name="fuel_quantity",
                            current_value=current_fuel,
                            recommended_value=current_fuel * 1.05,  # Increase fuel by 5%
                            fix_type="adjust",
                            description="Increase fuel quantity to correct lean condition",
                            safety_level="caution",
                            estimated_improvement="Better AFR, safer operation",
                            requires_approval=True,
                        ))
                else:
                    current_afr = parameters.get("afr_target", 14.7)
                    if current_afr > 15.0:
                        fixes.append(DiagnosticFix(
                            fix_id=f"fix_{problem.problem_id}",
                            problem_id=problem.problem_id,
                            parameter_name="afr_target",
                            current_value=current_afr,
                            recommended_value=14.2,  # Richer target
                            fix_type="adjust",
                            description="Adjust AFR target to correct lean condition",
                            safety_level="caution",
                            estimated_improvement="Safer operation, reduced knock risk",
                            requires_approval=True,
                        ))
        
        elif problem.category == ProblemCategory.IGNITION:
            if "knock" in problem.title.lower():
                # Fix knock by retarding timing
                current_timing = parameters.get("ignition_timing", 0)
                fixes.append(DiagnosticFix(
                    fix_id=f"fix_{problem.problem_id}",
                    problem_id=problem.problem_id,
                    parameter_name="ignition_timing",
                    current_value=current_timing,
                    recommended_value=current_timing - 3.0,  # Retard 3 degrees
                    fix_type="adjust",
                    description="Retard ignition timing to eliminate knock",
                    safety_level="safe",
                    estimated_improvement="Eliminate knock, protect engine",
                    requires_approval=False,
                ))
        
        elif problem.category == ProblemCategory.EXHAUST:
            if "egt" in problem.title.lower() and is_diesel:
                # Fix high EGT
                current_fuel = parameters.get("fuel_quantity", 0)
                current_boost = parameters.get("boost_pressure", 0)
                
                if current_fuel > 0:
                    fixes.append(DiagnosticFix(
                        fix_id=f"fix_{problem.problem_id}_fuel",
                        problem_id=problem.problem_id,
                        parameter_name="fuel_quantity",
                        current_value=current_fuel,
                        recommended_value=current_fuel * 0.97,  # Reduce fuel slightly
                        fix_type="adjust",
                        description="Reduce fuel quantity to lower EGT",
                        safety_level="safe",
                        estimated_improvement="Lower EGT, safer operation",
                        requires_approval=False,
                    ))
        
        return fixes
    
    def _calculate_health_score(self, problems: List[DiagnosticProblem]) -> float:
        """Calculate overall engine health score."""
        if not problems:
            return 100.0
        
        # Weight by severity
        severity_weights = {
            ProblemSeverity.CRITICAL: 30.0,
            ProblemSeverity.HIGH: 20.0,
            ProblemSeverity.MEDIUM: 10.0,
            ProblemSeverity.LOW: 5.0,
            ProblemSeverity.INFO: 1.0,
        }
        
        total_deduction = sum(severity_weights.get(p.severity, 0) for p in problems)
        health_score = max(0.0, 100.0 - total_deduction)
        
        return health_score
    
    def _generate_summary(
        self,
        problems: List[DiagnosticProblem],
        fixes: List[DiagnosticFix],
        health_score: float,
    ) -> str:
        """Generate human-readable summary."""
        critical_count = sum(1 for p in problems if p.severity == ProblemSeverity.CRITICAL)
        high_count = sum(1 for p in problems if p.severity == ProblemSeverity.HIGH)
        
        summary = f"Engine Health Score: {health_score:.1f}%\n\n"
        
        if critical_count > 0:
            summary += f"⚠️ CRITICAL: {critical_count} critical problem(s) detected requiring immediate attention.\n"
        
        if high_count > 0:
            summary += f"⚠️ HIGH: {high_count} high-priority problem(s) detected.\n"
        
        summary += f"\nTotal Problems: {len(problems)}\n"
        summary += f"Recommended Fixes: {len(fixes)}\n"
        
        if health_score >= 80:
            summary += "\nEngine is in good condition."
        elif health_score >= 60:
            summary += "\nEngine has some issues that should be addressed."
        else:
            summary += "\nEngine has significant issues requiring attention."
        
        return summary
    
    def _generate_recommendations(
        self,
        problems: List[DiagnosticProblem],
        fixes: List[DiagnosticFix],
    ) -> List[str]:
        """Generate recommendations."""
        recommendations = []
        
        # Prioritize critical problems
        critical = [p for p in problems if p.severity == ProblemSeverity.CRITICAL]
        if critical:
            recommendations.append("Address critical problems immediately to prevent engine damage.")
        
        # Group by category
        categories = {}
        for problem in problems:
            if problem.category not in categories:
                categories[problem.category] = []
            categories[problem.category].append(problem)
        
        for category, probs in categories.items():
            if len(probs) > 1:
                recommendations.append(f"Multiple {category.value} issues detected - consider comprehensive {category.value} system check.")
        
        # Auto-fix recommendations
        safe_fixes = [f for f in fixes if f.safety_level == "safe" and not f.requires_approval]
        if safe_fixes:
            recommendations.append(f"{len(safe_fixes)} safe fix(es) can be applied automatically.")
        
        return recommendations
    
    def _initialize_diagnostic_rules(self) -> None:
        """Initialize diagnostic rules."""
        # Rules would be loaded from configuration
        # For now, rules are embedded in check methods
        pass


