"""
Fuel & Additive Management System

Comprehensive monitoring and control for:
- Nitrous Oxide (N2O)
- Nitromethane (Nitro)
- Methanol Injection
- E85/Flex Fuel

Provides real-time advice and automatic control for optimal performance and safety.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from services.voice_feedback import FeedbackPriority, VoiceFeedback

LOGGER = logging.getLogger(__name__)


class FuelAdditiveType(Enum):
    """Types of fuel additives."""

    NITROUS_OXIDE = "nitrous_oxide"  # N2O
    NITROMETHANE = "nitromethane"  # Nitro
    METHANOL = "methanol"
    E85 = "e85"  # Flex fuel


class AdditiveAdvice(Enum):
    """Types of additive advice."""

    INCREASE = "increase"
    DECREASE = "decrease"
    MAINTAIN = "maintain"
    STOP = "stop"
    REFILL = "refill"
    SAFETY_WARNING = "safety_warning"


@dataclass
class FuelAdditiveStatus:
    """Status of a fuel additive system."""

    additive_type: FuelAdditiveType
    current_level: float  # Percentage or PSI
    flow_rate: float  # Current flow rate
    pressure: Optional[float] = None  # Pressure (for nitrous/nitro)
    temperature: Optional[float] = None  # Temperature
    active: bool = False
    health_status: str = "good"  # good, warning, critical


@dataclass
class FuelAdditiveRecommendation:
    """Recommendation for fuel/additive adjustment."""

    additive_type: FuelAdditiveType
    advice: AdditiveAdvice
    message: str
    priority: FeedbackPriority
    current_value: float
    recommended_value: Optional[float] = None
    reason: str = ""
    confidence: float = 0.0
    auto_apply: bool = False
    safety_critical: bool = False


class FuelAdditiveManager:
    """
    Comprehensive Fuel & Additive Management System.

    UNIQUE FEATURE: No one has done comprehensive fuel/additive management with AI!
    This monitors and optimizes nitrous, nitro, methanol, and E85 in real-time.
    """

    def __init__(
        self,
        voice_feedback: Optional[VoiceFeedback] = None,
        auto_control_enabled: bool = False,
    ) -> None:
        """
        Initialize fuel/additive manager.

        Args:
            voice_feedback: Voice feedback for announcements
            auto_control_enabled: Enable automatic control
        """
        self.voice_feedback = voice_feedback
        self.auto_control_enabled = auto_control_enabled

        # System status
        self.additive_status: Dict[FuelAdditiveType, FuelAdditiveStatus] = {}

        # Safety limits
        self.safety_limits = {
            FuelAdditiveType.NITROUS_OXIDE: {
                "min_pressure_psi": 750,
                "max_pressure_psi": 1100,
                "min_lambda": 0.85,
                "max_lambda": 1.05,
            },
            FuelAdditiveType.NITROMETHANE: {
                "min_pressure_psi": 800,
                "max_pressure_psi": 1200,
                "min_lambda": 0.70,  # Nitro runs much richer
                "max_lambda": 0.85,
                "max_percentage": 90,  # Max nitro percentage in fuel
            },
            FuelAdditiveType.METHANOL: {
                "min_tank_level": 10,  # %
                "min_flow_rate": 0.5,  # L/min
                "max_flow_rate": 10.0,  # L/min
            },
            FuelAdditiveType.E85: {
                "min_ethanol_percent": 51,  # E85 minimum
                "max_ethanol_percent": 100,
                "optimal_range": (70, 90),
            },
        }

        # Performance targets
        self.performance_targets = {
            FuelAdditiveType.NITROUS_OXIDE: {
                "optimal_lambda_range": (0.92, 0.98),
                "optimal_boost_range": (15, 30),
            },
            FuelAdditiveType.NITROMETHANE: {
                "optimal_lambda_range": (0.72, 0.78),
                "optimal_percentage": 90,  # For maximum power
            },
            FuelAdditiveType.METHANOL: {
                "optimal_flow_range": (2.0, 5.0),  # L/min
                "optimal_boost_range": (20, 35),
            },
            FuelAdditiveType.E85: {
                "optimal_percent_range": (70, 90),
                "optimal_boost_range": (15, 30),
            },
        }

    def analyze_and_advise(self, telemetry: Dict[str, float]) -> List[FuelAdditiveRecommendation]:
        """
        Analyze all fuel/additive systems and provide recommendations.

        Args:
            telemetry: Current telemetry data

        Returns:
            List of recommendations
        """
        recommendations = []

        # Analyze each additive system
        if "NitrousBottlePressure" in telemetry:
            nitrous_rec = self._analyze_nitrous_oxide(telemetry)
            if nitrous_rec:
                recommendations.append(nitrous_rec)

        if "NitroMethanePercentage" in telemetry or "NitroPercentage" in telemetry:
            nitro_rec = self._analyze_nitromethane(telemetry)
            if nitro_rec:
                recommendations.append(nitro_rec)

        if "MethInjectionDuty" in telemetry or "MethTankLevel" in telemetry:
            meth_rec = self._analyze_methanol(telemetry)
            if meth_rec:
                recommendations.append(meth_rec)

        if "FlexFuelPercent" in telemetry or "EthanolContent" in telemetry:
            e85_rec = self._analyze_e85(telemetry)
            if e85_rec:
                recommendations.append(e85_rec)

        # Safety checks (highest priority)
        safety_recs = self._check_safety(telemetry)
        recommendations = safety_recs + recommendations

        # Apply automatic control if enabled
        if self.auto_control_enabled:
            for rec in recommendations:
                if rec.auto_apply:
                    self._apply_recommendation(rec)

        # Provide voice feedback
        for rec in recommendations:
            if rec.priority in [FeedbackPriority.HIGH, FeedbackPriority.CRITICAL]:
                self._announce_recommendation(rec)

        return recommendations

    def _analyze_nitrous_oxide(self, telemetry: Dict) -> Optional[FuelAdditiveRecommendation]:
        """Analyze nitrous oxide system."""
        nitrous_pressure = telemetry.get("NitrousBottlePressure", 0)
        nitrous_solenoid = telemetry.get("NitrousSolenoidState", 0)
        lambda_value = telemetry.get("Lambda", 1.0)
        boost = telemetry.get("Boost_Pressure", 0)
        rpm = telemetry.get("Engine_RPM", 0)
        throttle = telemetry.get("Throttle_Position", 0)

        limits = self.safety_limits[FuelAdditiveType.NITROUS_OXIDE]
        targets = self.performance_targets[FuelAdditiveType.NITROUS_OXIDE]

        # Safety: Low pressure
        if nitrous_pressure < limits["min_pressure_psi"] and nitrous_solenoid == 1:
            return FuelAdditiveRecommendation(
                additive_type=FuelAdditiveType.NITROUS_OXIDE,
                advice=AdditiveAdvice.STOP,
                message=f"STOP NITROUS! Low bottle pressure ({nitrous_pressure:.0f} PSI). Refill required.",
                priority=FeedbackPriority.CRITICAL,
                current_value=nitrous_pressure,
                reason="Nitrous pressure too low - unsafe operation",
                confidence=0.95,
                auto_apply=True,
                safety_critical=True,
            )

        # Safety: Too lean with nitrous
        if lambda_value > limits["max_lambda"] and nitrous_solenoid == 1:
            return FuelAdditiveRecommendation(
                additive_type=FuelAdditiveType.NITROUS_OXIDE,
                advice=AdditiveAdvice.STOP,
                message=f"STOP NITROUS! Too lean (λ={lambda_value:.2f}) - extreme danger!",
                priority=FeedbackPriority.CRITICAL,
                current_value=nitrous_pressure,
                reason="Too lean with nitrous - risk of catastrophic failure",
                confidence=0.98,
                auto_apply=True,
                safety_critical=True,
            )

        # Performance: Conditions optimal for nitrous
        if (
            throttle > 90
            and rpm > 5000
            and boost > targets["optimal_boost_range"][0]
            and limits["min_lambda"] <= lambda_value <= limits["max_lambda"]
            and nitrous_pressure > limits["min_pressure_psi"]
            and nitrous_solenoid == 0
        ):
            return FuelAdditiveRecommendation(
                additive_type=FuelAdditiveType.NITROUS_OXIDE,
                advice=AdditiveAdvice.INCREASE,
                message="Conditions optimal. Activate nitrous for maximum power.",
                priority=FeedbackPriority.MEDIUM,
                current_value=0,
                recommended_value=1,  # Activate
                reason="Optimal conditions for nitrous - can safely activate",
                confidence=0.85,
                auto_apply=self.auto_control_enabled,
            )

        return None

    def _analyze_nitromethane(self, telemetry: Dict) -> Optional[FuelAdditiveRecommendation]:
        """Analyze nitromethane (nitro) system."""
        nitro_percent = telemetry.get("NitroMethanePercentage", telemetry.get("NitroPercentage", 0))
        nitro_pressure = telemetry.get("NitroPressure", 0)
        lambda_value = telemetry.get("Lambda", 1.0)
        boost = telemetry.get("Boost_Pressure", 0)
        rpm = telemetry.get("Engine_RPM", 0)

        limits = self.safety_limits[FuelAdditiveType.NITROMETHANE]
        targets = self.performance_targets[FuelAdditiveType.NITROMETHANE]

        # Safety: Low pressure
        if nitro_pressure < limits["min_pressure_psi"] and nitro_percent > 0:
            return FuelAdditiveRecommendation(
                additive_type=FuelAdditiveType.NITROMETHANE,
                advice=AdditiveAdvice.REFILL,
                message=f"CRITICAL: Nitro pressure low ({nitro_pressure:.0f} PSI). Refill immediately!",
                priority=FeedbackPriority.CRITICAL,
                current_value=nitro_pressure,
                reason="Nitro pressure too low - unsafe",
                confidence=0.95,
                auto_apply=False,
                safety_critical=True,
            )

        # Safety: Too lean for nitro (nitro needs to run rich)
        if lambda_value > limits["max_lambda"] and nitro_percent > 50:
            return FuelAdditiveRecommendation(
                additive_type=FuelAdditiveType.NITROMETHANE,
                advice=AdditiveAdvice.DECREASE,
                message=f"REDUCE NITRO! Too lean (λ={lambda_value:.2f}). Nitro requires rich mixture!",
                priority=FeedbackPriority.CRITICAL,
                current_value=nitro_percent,
                recommended_value=max(0, nitro_percent - 10),
                reason="Too lean for nitro - extreme danger",
                confidence=0.98,
                auto_apply=True,
                safety_critical=True,
            )

        # Performance: Increase nitro percentage
        if (
            nitro_percent < targets["optimal_percentage"]
            and limits["min_lambda"] <= lambda_value <= limits["max_lambda"]
            and boost > 20
            and rpm > 6000
        ):
            recommended = min(limits["max_percentage"], nitro_percent + 5)
            return FuelAdditiveRecommendation(
                additive_type=FuelAdditiveType.NITROMETHANE,
                advice=AdditiveAdvice.INCREASE,
                message=f"Increase nitro to {recommended:.0f}%. Conditions optimal for maximum power.",
                priority=FeedbackPriority.MEDIUM,
                current_value=nitro_percent,
                recommended_value=recommended,
                reason="Optimal conditions - can increase nitro percentage",
                confidence=0.8,
                auto_apply=self.auto_control_enabled,
            )

        # Too rich - reduce nitro
        if lambda_value < limits["min_lambda"] and nitro_percent > 50:
            recommended = max(50, nitro_percent - 5)
            return FuelAdditiveRecommendation(
                additive_type=FuelAdditiveType.NITROMETHANE,
                advice=AdditiveAdvice.DECREASE,
                message=f"Reduce nitro to {recommended:.0f}%. Mixture too rich.",
                priority=FeedbackPriority.MEDIUM,
                current_value=nitro_percent,
                recommended_value=recommended,
                reason="Too rich - wasting nitro",
                confidence=0.75,
                auto_apply=self.auto_control_enabled,
            )

        return None

    def _analyze_methanol(self, telemetry: Dict) -> Optional[FuelAdditiveRecommendation]:
        """Analyze methanol injection system."""
        meth_duty = telemetry.get("MethInjectionDuty", 0)
        meth_tank_level = telemetry.get("MethTankLevel", 100)
        meth_flow_rate = telemetry.get("MethFlowRate", 0)
        lambda_value = telemetry.get("Lambda", 1.0)
        boost = telemetry.get("Boost_Pressure", 0)
        intake_temp = telemetry.get("Intake_Temp", 50)

        limits = self.safety_limits[FuelAdditiveType.METHANOL]
        targets = self.performance_targets[FuelAdditiveType.METHANOL]

        # Safety: Low tank level
        if meth_tank_level < limits["min_tank_level"] and meth_duty > 0:
            return FuelAdditiveRecommendation(
                additive_type=FuelAdditiveType.METHANOL,
                advice=AdditiveAdvice.REFILL,
                message=f"CRITICAL: Methanol tank low ({meth_tank_level:.0f}%). Refill immediately!",
                priority=FeedbackPriority.CRITICAL,
                current_value=meth_tank_level,
                reason="Methanol tank nearly empty",
                confidence=0.95,
                auto_apply=False,
                safety_critical=True,
            )

        # Safety: Low flow rate but high duty
        if meth_duty > 50 and meth_flow_rate < limits["min_flow_rate"]:
            return FuelAdditiveRecommendation(
                additive_type=FuelAdditiveType.METHANOL,
                advice=AdditiveAdvice.STOP,
                message=f"STOP METHANOL! Low flow rate ({meth_flow_rate:.2f} L/min). Check pump/system!",
                priority=FeedbackPriority.HIGH,
                current_value=meth_flow_rate,
                reason="Methanol flow insufficient - pump may be failing",
                confidence=0.9,
                auto_apply=True,
                safety_critical=True,
            )

        # Performance: Increase methanol for high boost
        if (
            boost > targets["optimal_boost_range"][0]
            and meth_duty < 70
            and meth_tank_level > 20
            and intake_temp > 60
        ):
            recommended = min(100, meth_duty + 15)
            return FuelAdditiveRecommendation(
                additive_type=FuelAdditiveType.METHANOL,
                advice=AdditiveAdvice.INCREASE,
                message=f"Increase methanol to {recommended:.0f}%. High boost requires more cooling.",
                priority=FeedbackPriority.MEDIUM,
                current_value=meth_duty,
                recommended_value=recommended,
                reason="High boost requires more methanol for cooling",
                confidence=0.8,
                auto_apply=self.auto_control_enabled,
            )

        # Reduce methanol if not needed
        if boost < 10 and meth_duty > 30:
            recommended = max(0, meth_duty - 20)
            return FuelAdditiveRecommendation(
                additive_type=FuelAdditiveType.METHANOL,
                advice=AdditiveAdvice.DECREASE,
                message=f"Reduce methanol to {recommended:.0f}%. Low boost - methanol not needed.",
                priority=FeedbackPriority.LOW,
                current_value=meth_duty,
                recommended_value=recommended,
                reason="Low boost - saving methanol",
                confidence=0.85,
                auto_apply=self.auto_control_enabled,
            )

        return None

    def _analyze_e85(self, telemetry: Dict) -> Optional[FuelAdditiveRecommendation]:
        """Analyze E85/flex fuel system."""
        ethanol_percent = telemetry.get("FlexFuelPercent", telemetry.get("EthanolContent", 0))
        lambda_value = telemetry.get("Lambda", 1.0)
        boost = telemetry.get("Boost_Pressure", 0)
        knock_count = telemetry.get("Knock_Count", 0)

        limits = self.safety_limits[FuelAdditiveType.E85]
        targets = self.performance_targets[FuelAdditiveType.E85]

        # Safety: Ethanol content too low for E85
        if ethanol_percent < limits["min_ethanol_percent"]:
            return FuelAdditiveRecommendation(
                additive_type=FuelAdditiveType.E85,
                advice=AdditiveAdvice.REFILL,
                message=f"WARNING: Ethanol content low ({ethanol_percent:.0f}%). Not true E85. Refill with proper E85.",
                priority=FeedbackPriority.HIGH,
                current_value=ethanol_percent,
                reason="Ethanol content below E85 specification",
                confidence=0.9,
                auto_apply=False,
            )

        # Performance: Increase ethanol for high boost
        if (
            boost > targets["optimal_boost_range"][0]
            and ethanol_percent < targets["optimal_percent_range"][1]
            and knock_count == 0
        ):
            return FuelAdditiveRecommendation(
                additive_type=FuelAdditiveType.E85,
                advice=AdditiveAdvice.INCREASE,
                message=f"Higher ethanol content recommended ({targets['optimal_percent_range'][1]:.0f}%+). Better for high boost.",
                priority=FeedbackPriority.MEDIUM,
                current_value=ethanol_percent,
                recommended_value=targets["optimal_percent_range"][1],
                reason="High boost benefits from higher ethanol content",
                confidence=0.75,
                auto_apply=False,  # Can't auto-adjust fuel blend
            )

        # Optimal range
        if targets["optimal_percent_range"][0] <= ethanol_percent <= targets["optimal_percent_range"][1]:
            return FuelAdditiveRecommendation(
                additive_type=FuelAdditiveType.E85,
                advice=AdditiveAdvice.MAINTAIN,
                message=f"E85 content optimal at {ethanol_percent:.0f}%. Maintain current blend.",
                priority=FeedbackPriority.LOW,
                current_value=ethanol_percent,
                recommended_value=ethanol_percent,
                reason="Ethanol content in optimal range",
                confidence=0.9,
                auto_apply=False,
            )

        return None

    def _check_safety(self, telemetry: Dict) -> List[FuelAdditiveRecommendation]:
        """Check for critical safety issues across all systems."""
        safety_recs = []

        lambda_value = telemetry.get("Lambda", 1.0)
        knock_count = telemetry.get("Knock_Count", 0)

        # Critical: Extreme lean with any additive active
        nitrous_active = telemetry.get("NitrousSolenoidState", 0) == 1
        nitro_percent = telemetry.get("NitroMethanePercentage", telemetry.get("NitroPercentage", 0))
        meth_duty = telemetry.get("MethInjectionDuty", 0)

        if lambda_value > 1.2 and (nitrous_active or nitro_percent > 0 or meth_duty > 50):
            safety_recs.append(
                FuelAdditiveRecommendation(
                    additive_type=FuelAdditiveType.NITROUS_OXIDE,  # Generic
                    advice=AdditiveAdvice.STOP,
                    message="CRITICAL: Extreme lean condition with additives active! STOP ALL ADDITIVES IMMEDIATELY!",
                    priority=FeedbackPriority.CRITICAL,
                    current_value=lambda_value,
                    reason="Extreme lean with additives - catastrophic failure risk",
                    confidence=0.99,
                    auto_apply=True,
                    safety_critical=True,
                )
            )

        # Critical: Severe knock with additives
        if knock_count > 15 and (nitrous_active or nitro_percent > 50):
            safety_recs.append(
                FuelAdditiveRecommendation(
                    additive_type=FuelAdditiveType.NITROUS_OXIDE,
                    advice=AdditiveAdvice.STOP,
                    message=f"CRITICAL: Severe knock ({knock_count} events) with additives! Reduce power immediately!",
                    priority=FeedbackPriority.CRITICAL,
                    current_value=knock_count,
                    reason="Severe knock with additives - engine damage imminent",
                    confidence=0.98,
                    auto_apply=True,
                    safety_critical=True,
                )
            )

        return safety_recs

    def _apply_recommendation(self, recommendation: FuelAdditiveRecommendation) -> bool:
        """Apply a recommendation automatically."""
        # This would interface with actual controllers
        LOGGER.info(
            f"Auto-adjusting {recommendation.additive_type.value}: "
            f"{recommendation.current_value} -> {recommendation.recommended_value}"
        )
        # TODO: Interface with actual hardware controllers
        return True

    def _announce_recommendation(self, recommendation: FuelAdditiveRecommendation) -> None:
        """Announce recommendation via voice."""
        if self.voice_feedback:
            self.voice_feedback.announce(
                recommendation.message,
                priority=recommendation.priority,
                channel="fuel_additive",
                throttle=3.0,
            )

    def get_system_status(self) -> Dict[str, Dict]:
        """Get status of all fuel/additive systems."""
        status = {}
        for additive_type, additive_status in self.additive_status.items():
            status[additive_type.value] = {
                "level": additive_status.current_level,
                "active": additive_status.active,
                "health": additive_status.health_status,
            }
        return status


__all__ = [
    "FuelAdditiveManager",
    "FuelAdditiveType",
    "AdditiveAdvice",
    "FuelAdditiveStatus",
    "FuelAdditiveRecommendation",
]

