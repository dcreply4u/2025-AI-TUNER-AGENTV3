"""
Boost & Nitrous Advisor with Automatic Control

Monitors boost and nitrous systems, provides real-time advice,
and can automatically adjust boost/nitrous based on conditions.
This is CRITICAL for performance and safety!

NOTE: For comprehensive fuel/additive management including methanol and E85,
see FuelAdditiveManager which handles all fuel systems together.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from services.voice_feedback import FeedbackPriority, VoiceFeedback

LOGGER = logging.getLogger(__name__)


class BoostNitrousAdvice(Enum):
    """Types of boost/nitrous advice."""

    INCREASE_BOOST = "increase_boost"
    DECREASE_BOOST = "decrease_boost"
    MAINTAIN_BOOST = "maintain_boost"
    SPRAY_NITROUS = "spray_nitrous"
    REDUCE_NITROUS = "reduce_nitrous"
    STOP_NITROUS = "stop_nitrous"
    SAFETY_WARNING = "safety_warning"


@dataclass
class BoostNitrousRecommendation:
    """Boost/nitrous recommendation with automatic control option."""

    advice_type: BoostNitrousAdvice
    message: str
    priority: FeedbackPriority
    current_boost: float
    recommended_boost: Optional[float] = None
    current_nitrous_duty: float = 0.0
    recommended_nitrous_duty: Optional[float] = None
    reason: str = ""
    confidence: float = 0.0
    auto_apply: bool = False
    safety_critical: bool = False


class BoostNitrousAdvisor:
    """
    Boost & Nitrous Advisor with Automatic Control.

    UNIQUE FEATURE: Real-time boost/nitrous optimization with automatic control!
    This monitors conditions and automatically adjusts for maximum performance and safety.
    """

    def __init__(
        self,
        voice_feedback: Optional[VoiceFeedback] = None,
        auto_control_enabled: bool = False,
        max_boost_psi: float = 30.0,
        max_nitrous_duty: float = 100.0,
    ) -> None:
        """
        Initialize boost/nitrous advisor.

        Args:
            voice_feedback: Voice feedback for announcements
            auto_control_enabled: Enable automatic boost/nitrous control
            max_boost_psi: Maximum safe boost (PSI)
            max_nitrous_duty: Maximum nitrous duty cycle (%)
        """
        self.voice_feedback = voice_feedback
        self.auto_control_enabled = auto_control_enabled
        self.max_boost_psi = max_boost_psi
        self.max_nitrous_duty = max_nitrous_duty

        # Hardware controllers (optional - will be None if not available)
        self.boost_controller: Optional[Any] = None
        self.nitrous_controller: Optional[Any] = None
        try:
            from interfaces.boost_controller import BoostController
            self.boost_controller = BoostController()
            if not self.boost_controller.connect():
                self.boost_controller = None
                LOGGER.debug("Boost controller hardware not available")
        except Exception as e:
            LOGGER.debug(f"Boost controller interface unavailable: {e}")
        
        try:
            # Nitrous controller would be similar - create if needed
            # For now, we'll use CAN-based control if available
            from interfaces.can_interface import CANInterface
            can_interface = CANInterface()
            if can_interface.connect():
                self.nitrous_controller = can_interface  # Use CAN for nitrous control
            else:
                self.nitrous_controller = None
        except Exception as e:
            LOGGER.debug(f"Nitrous controller interface unavailable: {e}")

        # Control state
        self.current_boost_target: Optional[float] = None
        self.current_nitrous_duty: float = 0.0
        self.last_adjustment_time: float = 0.0
        self.adjustment_cooldown: float = 2.0  # Seconds between adjustments

        # Safety limits
        self.safety_limits = {
            "max_lambda_under_boost": 1.15,  # Too lean = dangerous
            "min_lambda_under_boost": 0.85,  # Too rich = waste
            "max_coolant_temp": 110.0,  # Celsius
            "max_knock_count": 5,  # Knock events
            "min_fuel_pressure": 40.0,  # PSI
            "min_nitrous_pressure": 750.0,  # PSI
        }

    def analyze_and_advise(
        self,
        telemetry: Dict[str, float],
        conditions: Optional[Dict[str, float]] = None,
    ) -> List[BoostNitrousRecommendation]:
        """
        Analyze current conditions and provide boost/nitrous advice.

        Args:
            telemetry: Current telemetry data
            conditions: Environmental conditions (optional)

        Returns:
            List of recommendations
        """
        recommendations = []

        # Analyze boost
        boost_rec = self._analyze_boost(telemetry, conditions)
        if boost_rec:
            recommendations.append(boost_rec)

        # Analyze nitrous
        nitrous_rec = self._analyze_nitrous(telemetry, conditions)
        if nitrous_rec:
            recommendations.append(nitrous_rec)

        # Safety checks (highest priority)
        safety_rec = self._check_safety(telemetry)
        if safety_rec:
            recommendations.insert(0, safety_rec)  # Put safety first

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

    def _analyze_boost(
        self, telemetry: Dict, conditions: Optional[Dict]
    ) -> Optional[BoostNitrousRecommendation]:
        """Analyze boost and provide recommendations."""
        current_boost = telemetry.get("Boost_Pressure", 0)
        lambda_value = telemetry.get("Lambda", 1.0)
        coolant_temp = telemetry.get("Coolant_Temp", 90)
        knock_count = telemetry.get("Knock_Count", 0)
        fuel_pressure = telemetry.get("Fuel_Pressure", 50)
        rpm = telemetry.get("Engine_RPM", 0)
        throttle = telemetry.get("Throttle_Position", 0)

        # Safety checks first
        if lambda_value > self.safety_limits["max_lambda_under_boost"] and current_boost > 10:
            return BoostNitrousRecommendation(
                advice_type=BoostNitrousAdvice.DECREASE_BOOST,
                message=f"REDUCE BOOST! Too lean (λ={lambda_value:.2f}) - risk of detonation!",
                priority=FeedbackPriority.CRITICAL,
                current_boost=current_boost,
                recommended_boost=max(5, current_boost - 5),
                reason="Too lean under boost - dangerous",
                confidence=0.95,
                auto_apply=True,
                safety_critical=True,
            )

        if knock_count > self.safety_limits["max_knock_count"]:
            return BoostNitrousRecommendation(
                advice_type=BoostNitrousAdvice.DECREASE_BOOST,
                message=f"REDUCE BOOST! Knock detected ({knock_count} events)",
                priority=FeedbackPriority.CRITICAL,
                current_boost=current_boost,
                recommended_boost=max(5, current_boost - 3),
                reason="Knock detected - reduce boost immediately",
                confidence=0.98,
                auto_apply=True,
                safety_critical=True,
            )

        if coolant_temp > self.safety_limits["max_coolant_temp"]:
            return BoostNitrousRecommendation(
                advice_type=BoostNitrousAdvice.DECREASE_BOOST,
                message=f"REDUCE BOOST! Engine overheating ({coolant_temp:.1f}°C)",
                priority=FeedbackPriority.HIGH,
                current_boost=current_boost,
                recommended_boost=max(5, current_boost - 3),
                reason="Engine temperature too high",
                confidence=0.9,
                auto_apply=True,
                safety_critical=True,
            )

        if fuel_pressure < self.safety_limits["min_fuel_pressure"]:
            return BoostNitrousRecommendation(
                advice_type=BoostNitrousAdvice.DECREASE_BOOST,
                message=f"REDUCE BOOST! Low fuel pressure ({fuel_pressure:.1f} PSI)",
                priority=FeedbackPriority.HIGH,
                current_boost=current_boost,
                recommended_boost=max(5, current_boost - 3),
                reason="Insufficient fuel pressure",
                confidence=0.85,
                auto_apply=True,
                safety_critical=True,
            )

        # Performance optimization (if safe)
        if (
            throttle > 80
            and rpm > 4000
            and lambda_value > 0.92
            and lambda_value < 1.05
            and coolant_temp < 100
            and knock_count == 0
            and current_boost < self.max_boost_psi - 2
        ):
            # Conditions are optimal - can increase boost
            recommended = min(self.max_boost_psi, current_boost + 2)
            return BoostNitrousRecommendation(
                advice_type=BoostNitrousAdvice.INCREASE_BOOST,
                message=f"Increase boost to {recommended:.1f} PSI. Conditions optimal.",
                priority=FeedbackPriority.MEDIUM,
                current_boost=current_boost,
                recommended_boost=recommended,
                reason="Optimal conditions - can safely increase boost",
                confidence=0.8,
                auto_apply=self.auto_control_enabled,
            )

        # Too rich - can increase boost slightly
        if lambda_value < 0.88 and current_boost < self.max_boost_psi - 1:
            recommended = min(self.max_boost_psi, current_boost + 1)
            return BoostNitrousRecommendation(
                advice_type=BoostNitrousAdvice.INCREASE_BOOST,
                message=f"Mixture too rich. Increase boost to {recommended:.1f} PSI.",
                priority=FeedbackPriority.LOW,
                current_boost=current_boost,
                recommended_boost=recommended,
                reason="Too rich - can lean out with more boost",
                confidence=0.7,
                auto_apply=self.auto_control_enabled,
            )

        # Boost is good
        if 0.92 <= lambda_value <= 1.05 and knock_count == 0:
            return BoostNitrousRecommendation(
                advice_type=BoostNitrousAdvice.MAINTAIN_BOOST,
                message=f"Boost optimal at {current_boost:.1f} PSI. Maintain current level.",
                priority=FeedbackPriority.LOW,
                current_boost=current_boost,
                recommended_boost=current_boost,
                reason="Boost and mixture are optimal",
                confidence=0.9,
                auto_apply=False,
            )

        return None

    def _analyze_nitrous(
        self, telemetry: Dict, conditions: Optional[Dict]
    ) -> Optional[BoostNitrousRecommendation]:
        """Analyze nitrous and provide recommendations."""
        nitrous_pressure = telemetry.get("NitrousBottlePressure", 0)
        nitrous_solenoid = telemetry.get("NitrousSolenoidState", 0)
        current_nitrous_duty = telemetry.get("MethInjectionDuty", 0)  # Using meth duty as proxy
        lambda_value = telemetry.get("Lambda", 1.0)
        boost = telemetry.get("Boost_Pressure", 0)
        rpm = telemetry.get("Engine_RPM", 0)
        throttle = telemetry.get("Throttle_Position", 0)

        # Safety: Low nitrous pressure
        if nitrous_pressure < self.safety_limits["min_nitrous_pressure"] and nitrous_solenoid == 1:
            return BoostNitrousRecommendation(
                advice_type=BoostNitrousAdvice.STOP_NITROUS,
                message=f"STOP NITROUS! Low bottle pressure ({nitrous_pressure:.0f} PSI)",
                priority=FeedbackPriority.CRITICAL,
                current_boost=boost,
                current_nitrous_duty=current_nitrous_duty,
                recommended_nitrous_duty=0,
                reason="Nitrous pressure too low - unsafe",
                confidence=0.95,
                auto_apply=True,
                safety_critical=True,
            )

        # Safety: Too lean with nitrous
        if lambda_value > 1.1 and nitrous_solenoid == 1:
            return BoostNitrousRecommendation(
                advice_type=BoostNitrousAdvice.REDUCE_NITROUS,
                message=f"REDUCE NITROUS! Too lean (λ={lambda_value:.2f}) - dangerous!",
                priority=FeedbackPriority.CRITICAL,
                current_boost=boost,
                current_nitrous_duty=current_nitrous_duty,
                recommended_nitrous_duty=max(0, current_nitrous_duty - 20),
                reason="Too lean with nitrous - risk of detonation",
                confidence=0.95,
                auto_apply=True,
                safety_critical=True,
            )

        # Performance: Conditions good for nitrous
        if (
            throttle > 90
            and rpm > 5000
            and boost > 15
            and lambda_value > 0.90
            and lambda_value < 1.0
            and nitrous_pressure > 800
            and current_nitrous_duty < self.max_nitrous_duty - 10
        ):
            recommended = min(self.max_nitrous_duty, current_nitrous_duty + 15)
            return BoostNitrousRecommendation(
                advice_type=BoostNitrousAdvice.SPRAY_NITROUS,
                message=f"Increase nitrous to {recommended:.0f}%. Conditions optimal for power.",
                priority=FeedbackPriority.MEDIUM,
                current_boost=boost,
                current_nitrous_duty=current_nitrous_duty,
                recommended_nitrous_duty=recommended,
                reason="Optimal conditions - can safely increase nitrous",
                confidence=0.8,
                auto_apply=self.auto_control_enabled,
            )

        # Too rich with nitrous - reduce
        if lambda_value < 0.85 and current_nitrous_duty > 20:
            recommended = max(0, current_nitrous_duty - 15)
            return BoostNitrousRecommendation(
                advice_type=BoostNitrousAdvice.REDUCE_NITROUS,
                message=f"Reduce nitrous to {recommended:.0f}%. Mixture too rich.",
                priority=FeedbackPriority.MEDIUM,
                current_boost=boost,
                current_nitrous_duty=current_nitrous_duty,
                recommended_nitrous_duty=recommended,
                reason="Too rich - wasting nitrous",
                confidence=0.75,
                auto_apply=self.auto_control_enabled,
            )

        return None

    def _check_safety(self, telemetry: Dict) -> Optional[BoostNitrousRecommendation]:
        """Check for critical safety issues."""
        lambda_value = telemetry.get("Lambda", 1.0)
        knock_count = telemetry.get("Knock_Count", 0)
        coolant_temp = telemetry.get("Coolant_Temp", 90)
        boost = telemetry.get("Boost_Pressure", 0)

        # Critical: Extreme lean condition
        if lambda_value > 1.2 and boost > 5:
            return BoostNitrousRecommendation(
                advice_type=BoostNitrousAdvice.SAFETY_WARNING,
                message="CRITICAL: Extreme lean condition! Reduce boost/nitrous immediately!",
                priority=FeedbackPriority.CRITICAL,
                current_boost=boost,
                recommended_boost=max(0, boost - 10),
                reason="Extreme lean - immediate danger",
                confidence=0.99,
                auto_apply=True,
                safety_critical=True,
            )

        # Critical: Multiple knock events
        if knock_count > 10:
            return BoostNitrousRecommendation(
                advice_type=BoostNitrousAdvice.SAFETY_WARNING,
                message=f"CRITICAL: Severe knock detected ({knock_count} events)! Reduce power immediately!",
                priority=FeedbackPriority.CRITICAL,
                current_boost=boost,
                recommended_boost=max(0, boost - 8),
                reason="Severe knock - engine damage risk",
                confidence=0.98,
                auto_apply=True,
                safety_critical=True,
            )

        return None

    def _apply_recommendation(self, recommendation: BoostNitrousRecommendation) -> bool:
        """
        Apply a boost/nitrous recommendation automatically.

        Args:
            recommendation: Recommendation to apply

        Returns:
            True if applied successfully
        """
        now = time.time()
        if now - self.last_adjustment_time < self.adjustment_cooldown:
            return False

        self.last_adjustment_time = now

        # Apply boost adjustment
        if recommendation.recommended_boost is not None:
            self.current_boost_target = recommendation.recommended_boost
            # This would interface with boost controller
            LOGGER.info(
                f"Auto-adjusting boost: {recommendation.current_boost:.1f} -> {recommendation.recommended_boost:.1f} PSI"
            )
            # Interface with boost controller hardware
            if self.boost_controller:
                success = self.boost_controller.set_boost_target(recommendation.recommended_boost)
                if not success:
                    LOGGER.warning("Failed to set boost target via hardware controller")
            else:
                LOGGER.debug("Boost controller not available, using software target only")

        # Apply nitrous adjustment
        if recommendation.recommended_nitrous_duty is not None:
            self.current_nitrous_duty = recommendation.recommended_nitrous_duty
            # Interface with nitrous controller
            LOGGER.info(
                f"Auto-adjusting nitrous: {recommendation.current_nitrous_duty:.0f}% -> {recommendation.recommended_nitrous_duty:.0f}%"
            )
            # Interface with nitrous controller via CAN or direct control
            if self.nitrous_controller:
                success = self.nitrous_controller.set_duty_cycle(recommendation.recommended_nitrous_duty)
                if not success:
                    LOGGER.warning("Failed to set nitrous duty via hardware controller")
            else:
                LOGGER.debug("Nitrous controller not available, using software target only")

        return True

    def _announce_recommendation(self, recommendation: BoostNitrousRecommendation) -> None:
        """Announce recommendation via voice."""
        if self.voice_feedback:
            self.voice_feedback.announce(
                recommendation.message,
                priority=recommendation.priority,
                channel="boost_nitrous",
                throttle=3.0,
            )

    def set_boost_target(self, target_psi: float) -> bool:
        """
        Manually set boost target.

        Args:
            target_psi: Target boost in PSI

        Returns:
            True if set successfully
        """
        if target_psi > self.max_boost_psi:
            LOGGER.warning(f"Boost target {target_psi} exceeds maximum {self.max_boost_psi}")
            return False

        self.current_boost_target = target_psi
        # Interface with boost controller
        if self.boost_controller:
            success = self.boost_controller.set_boost_target(target_psi)
            if not success:
                LOGGER.warning("Failed to set boost target via hardware controller")
        LOGGER.info(f"Boost target set to {target_psi:.1f} PSI")
        return True

    def set_nitrous_duty(self, duty_percent: float) -> bool:
        """
        Manually set nitrous duty cycle.

        Args:
            duty_percent: Nitrous duty cycle (0-100%)

        Returns:
            True if set successfully
        """
        if duty_percent > self.max_nitrous_duty:
            LOGGER.warning(f"Nitrous duty {duty_percent} exceeds maximum {self.max_nitrous_duty}")
            return False

        self.current_nitrous_duty = duty_percent
        # Interface with nitrous controller
        if self.nitrous_controller:
            # If using CAN interface, send nitrous control message
            if hasattr(self.nitrous_controller, 'send_message'):
                # CAN message format for nitrous control (would be controller-specific)
                # Example: ID 0x300, data: [duty_cycle_byte, ...]
                duty_byte = int(duty_percent * 2.55)  # Convert 0-100% to 0-255
                try:
                    self.nitrous_controller.send_message(0x300, [duty_byte, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
                except Exception as e:
                    LOGGER.warning(f"Failed to set nitrous duty via hardware: {e}")
        LOGGER.info(f"Nitrous duty set to {duty_percent:.0f}%")
        return True

    def get_current_settings(self) -> Dict[str, float]:
        """Get current boost/nitrous settings."""
        return {
            "boost_target_psi": self.current_boost_target or 0.0,
            "nitrous_duty_percent": self.current_nitrous_duty,
            "max_boost_psi": self.max_boost_psi,
            "max_nitrous_duty": self.max_nitrous_duty,
            "auto_control_enabled": self.auto_control_enabled,
        }


__all__ = ["BoostNitrousAdvisor", "BoostNitrousAdvice", "BoostNitrousRecommendation"]

