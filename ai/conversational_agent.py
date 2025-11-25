from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional

from services.performance_tracker import PerformanceSnapshot

MPH_TO_KMH = 1.60934


@dataclass
class AgentContext:
    telemetry: Dict[str, float] = field(default_factory=dict)
    health: Dict[str, float | str] = field(default_factory=dict)
    last_fix: Optional[Dict[str, float]] = None
    last_snapshot: Optional[PerformanceSnapshot] = None
    updated_at: float = field(default_factory=time.time)


class ConversationalAgent:
    """Rule-based conversational layer for quick spoken insights."""

    def __init__(self) -> None:
        self.context = AgentContext()

    # ------------------------------------------------------------------ #
    # Context ingestion
    # ------------------------------------------------------------------ #
    def update_context(
        self,
        telemetry: Optional[Dict[str, float]] = None,
        health: Optional[Dict[str, float | str]] = None,
        gps_fix: Optional[Dict[str, float]] = None,
        performance: Optional[PerformanceSnapshot] = None,
    ) -> None:
        if telemetry:
            self.context.telemetry = dict(telemetry)
        if health:
            self.context.health = dict(health)
        if gps_fix:
            self.context.last_fix = dict(gps_fix)
        if performance:
            self.context.last_snapshot = performance
        self.context.updated_at = time.time()

    # ------------------------------------------------------------------ #
    # Response generation
    # ------------------------------------------------------------------ #
    def answer(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        if not prompt_lower.strip():
            return "I didn't catch that. Could you repeat the question?"

        if any(keyword in prompt_lower for keyword in ("coolant", "temperature", "heat")):
            return self._coolant_summary()
        if "oil" in prompt_lower or "pressure" in prompt_lower:
            return self._oil_summary()
        if "health" in prompt_lower or "status" in prompt_lower:
            return self._health_summary()
        if "speed" in prompt_lower or "performance" in prompt_lower or "zero" in prompt_lower:
            return self._performance_summary()
        if "where" in prompt_lower or "location" in prompt_lower or "find" in prompt_lower:
            return self._location_summary()
        if "summary" in prompt_lower or "update" in prompt_lower:
            return self._overall_summary()
        if "ethanol" in prompt_lower or "flex" in prompt_lower:
            return self._ethanol_summary()
        if "meth" in prompt_lower or "methanol" in prompt_lower:
            return self._methanol_summary()
        if "nitrous" in prompt_lower or "bottle" in prompt_lower:
            return self._nitrous_summary()
        if "transbrake" in prompt_lower:
            return self._transbrake_summary()

        return (
            "I'm monitoring telemetry, GPS, and health metrics. "
            "Try asking about coolant temperature, health status, or vehicle location."
        )

    # ------------------------------------------------------------------ #
    # Individual summaries
    # ------------------------------------------------------------------ #
    def _coolant_summary(self) -> str:
        value = self._get_metric(("Coolant_Temp", "CoolantTemp", "Engine_Coolant_Temp"))
        if value is None:
            return "I don't have a coolant temperature reading yet."
        return f"Coolant temperature is holding at {value:.1f} degrees Celsius."

    def _oil_summary(self) -> str:
        value = self._get_metric(("Oil_Pressure", "OilPressure"))
        if value is None:
            return "Oil pressure data hasn't arrived yet."
        return f"Oil pressure is currently {value:.1f} kilopascals."

    def _health_summary(self) -> str:
        health = self.context.health
        if not health:
            return "I haven't computed a health score yet."
        score = health.get("score")
        status = str(health.get("status", "unknown")).title()
        if score is None:
            return f"Overall engine health is {status.lower()}."
        return f"Engine health is {status.lower()} with a score of {float(score)*100:0.0f} percent."

    def _performance_summary(self) -> str:
        snapshot = self.context.last_snapshot
        if not snapshot:
            return "No performance run is active yet."
        metrics = snapshot.metrics
        interesting = []
        for key in ("0-60 mph", "0-100 mph", "1/4 mile"):
            value = metrics.get(key)
            if value:
                interesting.append(f"{key} in {value:0.2f} seconds")
        if not interesting:
            return "I'm waiting for enough acceleration data to report performance."
        return "Latest run: " + ", ".join(interesting) + "."

    def _location_summary(self) -> str:
        fix = self.context.last_fix
        if not fix:
            return "Location beacons are offline right now."
        lat = fix.get("lat")
        lon = fix.get("lon")
        speed = fix.get("speed_mps", 0.0) * 2.23694
        return (
            f"The vehicle is near {lat:.5f}, {lon:.5f} traveling at {speed:0.1f} miles per hour."
        )

    def _overall_summary(self) -> str:
        parts = [
            self._health_summary(),
            self._coolant_summary(),
            self._performance_summary(),
        ]
        return " ".join(parts)

    def _ethanol_summary(self) -> str:
        value = self._get_metric(("Ethanol_Content", "FlexFuel_Percent", "Fuel_EthanolPercent"))
        if value is None:
            return "I don't have a flex-fuel reading yet."
        return f"Ethanol blend is measuring {value:.1f} percent."

    def _methanol_summary(self) -> str:
        flow = self._get_metric(("Methanol_Flow", "MethInjection_Duty"))
        level = self._get_metric(("Methanol_Level", "Meth_Tank_Level"))
        if flow is None and level is None:
            return "Methanol system data isn't available right now."
        parts = []
        if flow is not None:
            parts.append(f"Injection duty is {flow:.0f} percent")
        if level is not None:
            parts.append(f"tank level sits at {level:.0f} percent")
        return " and ".join(parts) + "."

    def _nitrous_summary(self) -> str:
        pressure = self._get_metric(("Nitrous_Bottle_Pressure", "Nitrous_Pressure"))
        armed = self._get_metric(("Nitrous_Solenoid_State", "Nitrous_Solenoid"))
        if pressure is None and armed is None:
            return "Nitrous system status is offline."
        status = "armed" if armed and armed > 0.5 else "disarmed"
        if pressure is None:
            return f"Nitrous system is currently {status}."
        return f"Nitrous system is {status} with bottle pressure at {pressure:.0f} psi."

    def _transbrake_summary(self) -> str:
        state = self._get_metric(("TransBrake_State", "TransBrake"))
        if state is None:
            return "Transbrake telemetry is not connected."
        return "Transbrake is engaged." if state > 0.5 else "Transbrake is released."

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _get_metric(self, keys: tuple[str, ...]) -> Optional[float]:
        for key in keys:
            if key in self.context.telemetry:
                return float(self.context.telemetry[key])
        return None


__all__ = ["ConversationalAgent"]

