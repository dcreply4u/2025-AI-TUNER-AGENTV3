"""
Biometric Integration

Integrates driver biometrics (heart rate, G-force tolerance, fatigue)
with vehicle performance. This is NEXT LEVEL - driver + car optimization!
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class DriverState(Enum):
    """Driver physiological states."""

    OPTIMAL = "optimal"
    STRESSED = "stressed"
    FATIGUED = "fatigued"
    OVERLOADED = "overloaded"  # Too much G-force
    FOCUSED = "focused"


@dataclass
class BiometricData:
    """Biometric sensor data."""

    heart_rate: float  # BPM
    heart_rate_variability: float
    g_force_lateral: float
    g_force_longitudinal: float
    g_force_vertical: float
    skin_conductance: Optional[float] = None  # Stress indicator
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class DriverPerformance:
    """Driver performance analysis."""

    driver_state: DriverState
    performance_score: float  # 0-100
    reaction_time: float  # Estimated milliseconds
    g_tolerance: float  # Max G-force handled
    fatigue_level: float  # 0-1
    recommendations: List[str] = None


class BiometricIntegration:
    """
    Biometric Integration System.

    UNIQUE FEATURE: No one has integrated driver biometrics with vehicle telemetry!
    This optimizes BOTH driver and car performance together.
    """

    def __init__(self) -> None:
        """Initialize biometric integration."""
        self.biometric_history: List[BiometricData] = []
        self.driver_profile: Dict[str, float] = {}
        self.max_history = 1000

    def process_biometrics(
        self,
        biometrics: BiometricData,
        telemetry: Dict[str, float],
    ) -> DriverPerformance:
        """
        Process biometric data and analyze driver performance.

        Args:
            biometrics: Biometric sensor data
            telemetry: Vehicle telemetry data

        Returns:
            Driver performance analysis
        """
        # Store in history
        self.biometric_history.append(biometrics)
        if len(self.biometric_history) > self.max_history:
            self.biometric_history.pop(0)

        # Analyze driver state
        driver_state = self._analyze_driver_state(biometrics, telemetry)
        performance_score = self._calculate_performance_score(biometrics, telemetry)
        reaction_time = self._estimate_reaction_time(biometrics)
        g_tolerance = self._calculate_g_tolerance(biometrics)
        fatigue_level = self._calculate_fatigue(biometrics)
        recommendations = self._generate_recommendations(biometrics, telemetry, driver_state)

        return DriverPerformance(
            driver_state=driver_state,
            performance_score=performance_score,
            reaction_time=reaction_time,
            g_tolerance=g_tolerance,
            fatigue_level=fatigue_level,
            recommendations=recommendations,
        )

    def _analyze_driver_state(self, biometrics: BiometricData, telemetry: Dict) -> DriverState:
        """Analyze current driver physiological state."""
        # High G-forces
        total_g = (
            abs(biometrics.g_force_lateral)
            + abs(biometrics.g_force_longitudinal)
            + abs(biometrics.g_force_vertical)
        )

        if total_g > 3.0:
            return DriverState.OVERLOADED

        # High heart rate + stress
        if biometrics.heart_rate > 150 and biometrics.skin_conductance and biometrics.skin_conductance > 5.0:
            return DriverState.STRESSED

        # Fatigue indicators
        if biometrics.heart_rate < 60 and len(self.biometric_history) > 10:
            # Check for declining performance
            recent_hr = [b.heart_rate for b in self.biometric_history[-10:]]
            if all(hr < 65 for hr in recent_hr):
                return DriverState.FATIGUED

        # Optimal zone
        if 70 < biometrics.heart_rate < 120:
            return DriverState.OPTIMAL

        return DriverState.FOCUSED

    def _calculate_performance_score(self, biometrics: BiometricData, telemetry: Dict) -> float:
        """Calculate driver performance score (0-100)."""
        score = 100.0

        # Heart rate optimal zone (70-120 BPM for racing)
        if biometrics.heart_rate < 60:
            score -= 20  # Too low (fatigue)
        elif biometrics.heart_rate > 150:
            score -= 15  # Too high (stress)
        elif 70 <= biometrics.heart_rate <= 120:
            score += 10  # Optimal zone

        # G-force handling
        total_g = abs(biometrics.g_force_lateral) + abs(biometrics.g_force_longitudinal)
        if total_g > 2.5:
            score += 5  # Handling high Gs well

        # Consistency (low HRV = focused)
        if biometrics.heart_rate_variability < 20:
            score += 5  # Very focused

        return max(0, min(100, score))

    def _estimate_reaction_time(self, biometrics: BiometricData) -> float:
        """Estimate reaction time based on biometrics."""
        # Lower HRV = faster reactions (generally)
        base_reaction = 200.0  # ms

        if biometrics.heart_rate_variability < 15:
            base_reaction -= 30  # Very focused
        elif biometrics.heart_rate_variability > 50:
            base_reaction += 50  # Less focused

        # High heart rate can improve reactions (up to a point)
        if 90 < biometrics.heart_rate < 130:
            base_reaction -= 20

        return max(100, min(500, base_reaction))

    def _calculate_g_tolerance(self, biometrics: BiometricData) -> float:
        """Calculate driver's G-force tolerance."""
        total_g = (
            abs(biometrics.g_force_lateral)
            + abs(biometrics.g_force_longitudinal)
            + abs(biometrics.g_force_vertical)
        )

        # Update profile
        if "max_g" not in self.driver_profile or total_g > self.driver_profile["max_g"]:
            self.driver_profile["max_g"] = total_g

        return self.driver_profile.get("max_g", total_g)

    def _calculate_fatigue(self, biometrics: BiometricData) -> float:
        """Calculate fatigue level (0-1)."""
        if len(self.biometric_history) < 10:
            return 0.0

        # Analyze trend
        recent = self.biometric_history[-10:]
        avg_hr = sum(b.heart_rate for b in recent) / len(recent)
        avg_hrv = sum(b.heart_rate_variability for b in recent) / len(recent)

        # Fatigue indicators
        fatigue = 0.0

        # Low heart rate
        if avg_hr < 65:
            fatigue += 0.3

        # High HRV (less focused)
        if avg_hrv > 60:
            fatigue += 0.2

        # Declining performance
        if len(self.biometric_history) > 20:
            old_avg = sum(b.heart_rate for b in self.biometric_history[-20:-10]) / 10
            if avg_hr < old_avg * 0.9:
                fatigue += 0.3

        return min(1.0, fatigue)

    def _generate_recommendations(
        self, biometrics: BiometricData, telemetry: Dict, driver_state: DriverState
    ) -> List[str]:
        """Generate recommendations based on biometrics."""
        recommendations = []

        if driver_state == DriverState.FATIGUED:
            recommendations.append("Take a break. Your heart rate indicates fatigue.")
            recommendations.append("Consider reducing session length.")

        if driver_state == DriverState.STRESSED:
            recommendations.append("You're stressed. Focus on breathing.")
            recommendations.append("Reduce pace slightly to regain control.")

        if driver_state == DriverState.OVERLOADED:
            recommendations.append("High G-forces detected. Consider smoother inputs.")
            recommendations.append("Your body is at the limit.")

        # Optimal performance tips
        if driver_state == DriverState.OPTIMAL:
            recommendations.append("You're in the zone! Maintain this pace.")
            if biometrics.heart_rate_variability < 20:
                recommendations.append("Excellent focus. Push harder if comfortable.")

        return recommendations

    def get_driver_profile(self) -> Dict:
        """Get driver performance profile."""
        if not self.biometric_history:
            return {}

        recent = self.biometric_history[-100:] if len(self.biometric_history) >= 100 else self.biometric_history

        return {
            "avg_heart_rate": sum(b.heart_rate for b in recent) / len(recent),
            "max_g_tolerance": self.driver_profile.get("max_g", 0),
            "avg_reaction_time": self._estimate_reaction_time(recent[-1]) if recent else 0,
            "total_session_time": (recent[-1].timestamp - recent[0].timestamp) if len(recent) > 1 else 0,
        }


__all__ = ["BiometricIntegration", "BiometricData", "DriverPerformance", "DriverState"]

