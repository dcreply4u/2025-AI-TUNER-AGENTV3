"""
Race Setup Recommender
----------------------
Curated recommendations for common racing scenarios (drag, time attack, endurance)
that can be injected into the AI advisor responses.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

import logging


LOGGER = logging.getLogger(__name__)


@dataclass
class SetupScenario:
    """Reference tuning scenario."""

    name: str
    keywords: List[str]
    recommendations: Dict[str, str]


class RaceSetupRecommender:
    """
    Lightweight knowledge helper that surfaces race-engineering tips based on
    question keywords and (optional) telemetry context.
    """

    def __init__(self) -> None:
        self.scenarios: List[SetupScenario] = [
            SetupScenario(
                name="Drag Launch & Traction",
                keywords=["drag", "launch", "60ft", "traction", "wheel hop"],
                recommendations={
                    "Chassis": "Stiffen rear compression + soften rebound 1-2 clicks to keep the tire planted.",
                    "Tires": "Target 12-14 psi on drag radials; pre-heat to ~140°F for consistency.",
                    "Power Delivery": "Pull 1-2° timing in first 0.5s if knock or spin is detected, then ramp back in.",
                    "Weight Transfer": "Raise front ride height 5-8 mm to allow more transfer on launch.",
                },
            ),
            SetupScenario(
                name="Road Course – Mid-Corner Balance",
                keywords=[
                    "mid corner",
                    "understeer",
                    "oversteer",
                    "time attack",
                    "apex",
                    "road course",
                    "track day",
                ],
                recommendations={
                    "Aero": "Increase rear wing angle 1° if high-speed entry oversteer, or trim front splitter for turn-in bite.",
                    "Damping": "Add 2 clicks rebound to the axle that feels lazy; soften compression on opposite corner to keep platform neutral.",
                    "Tires": "Stagger pressures so hot temps land at 34 psi front / 32 psi rear for R-compound baseline.",
                    "Brake Bias": "Shift 1% forward if entry instability shows up alongside knock-retard spikes from engine braking.",
                },
            ),
            SetupScenario(
                name="Endurance / Heat Management",
                keywords=[
                    "endurance",
                    "heat soak",
                    "fuel stint",
                    "long run",
                    "24h",
                    "12h",
                    "thermal",
                ],
                recommendations={
                    "Cooling": "Add ducting to brakes + oil cooler; ensure coolant delta stays <20°C across stint.",
                    "Fueling": "Lean cruise AFR by 0.2 during safety car or FCY to extend stint length.",
                    "Drivetrain": "Lower boost target 1-2 psi in hottest part of day; log gearbox temps for predictive pit calls.",
                    "Driver Aids": "Enable gentle throttle maps for tired stints to avoid spikes that trigger knock control.",
                },
            ),
        ]

    def get_recommendation(self, question: str, telemetry: Optional[Dict[str, float]] = None) -> Optional[str]:
        """Return a formatted recommendation block."""
        if not question:
            return None

        telemetry = telemetry or {}
        lower_question = question.lower()
        matched = self._match_scenarios(lower_question)

        if not matched:
            return None

        sections = []
        for scenario in matched:
            sections.append(f"**{scenario.name}**")
            for area, tip in scenario.recommendations.items():
                sections.append(f"- *{area}*: {tip}")

            # Telemetry-aware hints (very lightweight for now)
            if telemetry:
                rpm = telemetry.get("RPM") or telemetry.get("Engine_RPM")
                if rpm and rpm > 7000 and "drag" in scenario.name.lower():
                    sections.append(
                        "- *Telemetry Insight*: High RPM launch detected; ensure converter lockup strategy delays until 200ft."
                    )
                tire_temp = telemetry.get("Tire_Temp_Front_Left")
                if tire_temp and tire_temp > 200 and "road course" in scenario.name.lower():
                    sections.append(
                        "- *Telemetry Insight*: Front tire temps above 200°F, consider 1 psi drop + front camber increase."
                    )

        return "\n".join(sections)

    def _match_scenarios(self, question: str) -> List[SetupScenario]:
        """Return ordered list of matching scenarios."""
        matches: List[SetupScenario] = []
        for scenario in self.scenarios:
            for kw in scenario.keywords:
                if re.search(rf"\b{re.escape(kw)}\b", question):
                    matches.append(scenario)
                    break

        # Limit to two scenarios to avoid overly long responses
        return matches[:2]

