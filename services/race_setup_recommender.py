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
            SetupScenario(
                name="Suspension Tuning & Damping",
                keywords=[
                    "suspension",
                    "damping",
                    "shock",
                    "damper",
                    "bump",
                    "rebound",
                    "compression",
                    "spring",
                    "ride height",
                    "roll",
                    "pitch",
                ],
                recommendations={
                    "Bump/Compression": "Stiffen compression if bottoming out or excessive body roll. Soften if losing traction over bumps.",
                    "Rebound": "Increase rebound if car feels bouncy or unsettled. Decrease if suspension not returning quickly enough.",
                    "Balance": "If oversteer: soften rear compression, stiffen front rebound. If understeer: opposite approach.",
                    "Ride Height": "Lower center of gravity improves handling but watch for bottoming. Raise if scraping or losing travel.",
                    "Roll Stiffness": "Stiffer sway bars reduce roll but can hurt mechanical grip. Adjust based on tire temp spread.",
                },
            ),
            SetupScenario(
                name="Autocross / Tight Technical Courses",
                keywords=[
                    "autocross",
                    "solo",
                    "tight",
                    "technical",
                    "slalom",
                    "transition",
                ],
                recommendations={
                    "Suspension": "Softer overall setup for better mechanical grip. Quick transitions benefit from stiffer sway bars.",
                    "Alignment": "More aggressive camber (-2.5° to -3.5° front) for cornering grip. Toe-out front for turn-in response.",
                    "Tires": "Higher pressures (36-40 psi hot) for responsive feel. Monitor temps - should be even across tread.",
                    "Power Delivery": "Smooth throttle maps to avoid wheelspin on tight exits. Traction control may help if available.",
                },
            ),
        ]

    def get_recommendation(self, question: str, telemetry: Optional[Dict[str, float]] = None) -> Optional[str]:
        """Return a formatted recommendation block with enhanced telemetry analysis."""
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

            # Enhanced telemetry-aware insights
            telemetry_insights = self._analyze_telemetry(telemetry, scenario)
            if telemetry_insights:
                sections.extend(telemetry_insights)

        return "\n".join(sections)
    
    def _analyze_telemetry(self, telemetry: Dict[str, float], scenario: SetupScenario) -> List[str]:
        """Analyze telemetry data and generate contextual insights."""
        insights = []
        
        if not telemetry:
            return insights
        
        scenario_lower = scenario.name.lower()
        
        # Tire temperature analysis (all corners)
        tire_temps = self._get_tire_temps(telemetry)
        if tire_temps:
            insights.extend(self._analyze_tire_temps(tire_temps, scenario_lower))
        
        # G-force analysis
        lat_g = telemetry.get("GForce_Lateral") or telemetry.get("LatG") or telemetry.get("Lateral_G")
        long_g = telemetry.get("GForce_Longitudinal") or telemetry.get("LongG") or telemetry.get("Longitudinal_G")
        if lat_g is not None or long_g is not None:
            insights.extend(self._analyze_gforces(lat_g, long_g, scenario_lower))
        
        # Suspension travel analysis (if available)
        suspension_data = self._get_suspension_data(telemetry)
        if suspension_data:
            insights.extend(self._analyze_suspension(suspension_data, scenario_lower))
        
        # RPM and power delivery analysis
        rpm = telemetry.get("RPM") or telemetry.get("Engine_RPM") or telemetry.get("RPM_Engine")
        if rpm:
            insights.extend(self._analyze_rpm(rpm, scenario_lower))
        
        # Boost pressure analysis
        boost = telemetry.get("Boost") or telemetry.get("Boost_Pressure") or telemetry.get("MAP")
        if boost is not None:
            insights.extend(self._analyze_boost(boost, scenario_lower))
        
        # Temperature deltas (coolant, oil, EGT)
        temp_insights = self._analyze_temperatures(telemetry, scenario_lower)
        if temp_insights:
            insights.extend(temp_insights)
        
        return insights
    
    def _get_tire_temps(self, telemetry: Dict[str, float]) -> Optional[Dict[str, float]]:
        """Extract tire temperature data from telemetry."""
        temps = {}
        tire_keys = [
            ("FL", ["Tire_Temp_Front_Left", "TireTemp_FL", "TireTemp_FrontLeft", "FL_TireTemp"]),
            ("FR", ["Tire_Temp_Front_Right", "TireTemp_FR", "TireTemp_FrontRight", "FR_TireTemp"]),
            ("RL", ["Tire_Temp_Rear_Left", "TireTemp_RL", "TireTemp_RearLeft", "RL_TireTemp"]),
            ("RR", ["Tire_Temp_Rear_Right", "TireTemp_RR", "TireTemp_RearRight", "RR_TireTemp"]),
        ]
        
        for corner, keys in tire_keys:
            for key in keys:
                if key in telemetry:
                    temps[corner] = telemetry[key]
                    break
        
        return temps if temps else None
    
    def _analyze_tire_temps(self, temps: Dict[str, float], scenario: str) -> List[str]:
        """Analyze tire temperatures and provide recommendations."""
        insights = []
        
        if "road course" in scenario or "time attack" in scenario:
            # Check for temperature spread (indicates camber/pressure issues)
            if len(temps) >= 2:
                front_temps = [v for k, v in temps.items() if k.startswith("F")]
                rear_temps = [v for k, v in temps.items() if k.startswith("R")]
                
                if front_temps and len(front_temps) >= 2:
                    temp_spread = max(front_temps) - min(front_temps)
                    if temp_spread > 30:
                        insights.append(
                            "- *Telemetry Insight*: Front tire temp spread >30°F indicates camber or pressure imbalance. "
                            "Adjust camber to even out temps, or check for brake bias issues."
                        )
                
                if rear_temps and len(rear_temps) >= 2:
                    temp_spread = max(rear_temps) - min(rear_temps)
                    if temp_spread > 30:
                        insights.append(
                            "- *Telemetry Insight*: Rear tire temp spread >30°F - check alignment and rear sway bar settings."
                        )
                
                # Overall temperature analysis
                if temps:  # Prevent division by zero
                    avg_temp = sum(temps.values()) / len(temps)
                    if avg_temp > 200:
                        insights.append(
                            "- *Telemetry Insight*: Average tire temps >200°F - consider reducing pressure 1-2 psi or "
                            "increasing camber 0.5° to reduce heat buildup."
                        )
                    elif avg_temp < 150:
                        insights.append(
                            "- *Telemetry Insight*: Tire temps <150°F - tires may not be in optimal operating window. "
                            "Consider lower starting pressure or more aggressive warm-up lap."
                        )
        
        elif "drag" in scenario:
            # Drag-specific tire temp analysis
            if len(temps) >= 2:
                rear_tires = [v for k, v in temps.items() if k.startswith("R")]
                if rear_tires:  # Prevent division by zero
                    rear_avg = sum(rear_tires) / len(rear_tires)
                    if rear_avg < 140:
                        insights.append(
                            "- *Telemetry Insight*: Rear tire temps <140°F - pre-heat tires more aggressively for better 60ft times."
                        )
                    elif rear_avg > 180:
                        insights.append(
                            "- *Telemetry Insight*: Rear tire temps >180°F - may be overheating. Reduce burnout time or check tire pressure."
                        )
        
        return insights
    
    def _analyze_gforces(self, lat_g: Optional[float], long_g: Optional[float], scenario: str) -> List[str]:
        """Analyze G-force data for handling insights."""
        insights = []
        
        if "road course" in scenario or "time attack" in scenario:
            if lat_g is not None:
                if lat_g > 1.2:
                    insights.append(
                        "- *Telemetry Insight*: Sustained lateral G >1.2g detected - excellent grip. "
                        "Consider optimizing aero balance if entry/exit feels unstable at these loads."
                    )
                elif lat_g < 0.8:
                    insights.append(
                        "- *Telemetry Insight*: Lateral G <0.8g suggests room for improvement. "
                        "Check tire pressures, alignment, and suspension settings for more grip."
                    )
            
            if long_g is not None:
                if long_g < -0.8:
                    insights.append(
                        "- *Telemetry Insight*: Braking G >0.8g - ensure brake bias is optimized for weight transfer. "
                        "Check for ABS intervention or lock-up events."
                    )
        
        elif "drag" in scenario:
            if long_g is not None and long_g > 0.5:
                insights.append(
                    "- *Telemetry Insight*: Launch acceleration >0.5g - monitor wheel slip. "
                    "If traction is breaking, soften rear compression or reduce launch RPM."
                )
        
        return insights
    
    def _get_suspension_data(self, telemetry: Dict[str, float]) -> Optional[Dict[str, float]]:
        """Extract suspension travel/damper data from telemetry."""
        suspension = {}
        keys = [
            ("FL_Travel", ["Suspension_Travel_FL", "Damper_Travel_FL", "Shock_Travel_FL"]),
            ("FR_Travel", ["Suspension_Travel_FR", "Damper_Travel_FR", "Shock_Travel_FR"]),
            ("RL_Travel", ["Suspension_Travel_RL", "Damper_Travel_RL", "Shock_Travel_RL"]),
            ("RR_Travel", ["Suspension_Travel_RR", "Damper_Travel_RR", "Shock_Travel_RR"]),
        ]
        
        for name, key_variants in keys:
            for key in key_variants:
                if key in telemetry:
                    suspension[name] = telemetry[key]
                    break
        
        return suspension if suspension else None
    
    def _analyze_suspension(self, suspension: Dict[str, float], scenario: str) -> List[str]:
        """Analyze suspension travel data."""
        insights = []
        
        if len(suspension) >= 2:
            front_travel = [v for k, v in suspension.items() if k.startswith("F")]
            rear_travel = [v for k, v in suspension.items() if k.startswith("R")]
            
            if front_travel and max(front_travel) - min(front_travel) > 10:
                insights.append(
                    "- *Telemetry Insight*: Front suspension travel imbalance >10mm detected. "
                    "Check for binding, adjust damping, or verify corner weights."
                )
            
            if rear_travel and max(rear_travel) - min(rear_travel) > 10:
                insights.append(
                    "- *Telemetry Insight*: Rear suspension travel imbalance - may indicate roll stiffness or damping mismatch."
                )
            
            # Check for bottoming out
            if any(v > 90 for v in suspension.values()):
                insights.append(
                    "- *Telemetry Insight*: Suspension travel >90% - risk of bottoming out. "
                    "Consider stiffer springs or higher ride height."
                )
        
        return insights
    
    def _analyze_rpm(self, rpm: float, scenario: str) -> List[str]:
        """Analyze RPM data for power delivery insights."""
        insights = []
        
        if "drag" in scenario:
            if rpm > 7000:
                insights.append(
                    "- *Telemetry Insight*: High RPM launch (>7000) detected. "
                    "Ensure converter lockup strategy delays until 200ft mark for optimal traction."
                )
            elif rpm < 4000:
                insights.append(
                    "- *Telemetry Insight*: Low RPM launch - may benefit from higher stall speed or launch RPM for better 60ft."
                )
        
        return insights
    
    def _analyze_boost(self, boost: float, scenario: str) -> List[str]:
        """Analyze boost pressure data."""
        insights = []
        
        if "endurance" in scenario or "heat" in scenario:
            if boost > 25:
                insights.append(
                    "- *Telemetry Insight*: High boost (>25 PSI) in endurance scenario - consider reducing 1-2 PSI "
                    "during hottest part of day to manage heat and reliability."
                )
        
        return insights
    
    def _analyze_temperatures(self, telemetry: Dict[str, float], scenario: str) -> List[str]:
        """Analyze engine temperature data."""
        insights = []
        
        if "endurance" in scenario or "heat" in scenario:
            coolant = telemetry.get("CoolantTemp") or telemetry.get("Coolant_Temp")
            oil = telemetry.get("OilTemp") or telemetry.get("Oil_Temp")
            egt = telemetry.get("EGT") or telemetry.get("Exhaust_Gas_Temp")
            
            if coolant and coolant > 220:
                insights.append(
                    "- *Telemetry Insight*: Coolant temp >220°F - check radiator airflow, consider reducing boost or timing."
                )
            
            if oil and oil > 250:
                insights.append(
                    "- *Telemetry Insight*: Oil temp >250°F - critical for endurance. Add oil cooler capacity or reduce load."
                )
            
            if egt and egt > 1600:
                insights.append(
                    "- *Telemetry Insight*: EGT >1600°F - very high. Rich AFR or reduce timing to protect exhaust valves."
                )
            
            # Temperature delta analysis
            if coolant and oil:
                delta = abs(coolant - oil)
                if delta > 30:
                    insights.append(
                        "- *Telemetry Insight*: Coolant-oil temp delta >30°F - check oil cooler efficiency or thermostat operation."
                    )
        
        return insights

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

