from __future__ import annotations

from typing import Callable, List, Mapping, Sequence, Tuple


def _first(data: Mapping[str, float], *keys: str) -> float | None:
    for key in keys:
        value = data.get(key)
        if value is not None:
            return value
    return None


class TuningAdvisor:
    """Rule-based advisor that emits human-friendly tuning suggestions."""

    def __init__(self, rules: Sequence[Tuple[str, Callable[[Mapping[str, float]], bool], str]] | None = None) -> None:
        self.rules = list(
            rules
            or [
                (
                    "High RPM with low throttle",
                    lambda d: d.get("RPM", 0) > 4000 and d.get("Throttle", 0) < 20,
                    "Possible clutch slip or drivetrain loss detected.",
                ),
                (
                    "High coolant temperature",
                    lambda d: d.get("CoolantTemp", 0) > 105,
                    "Engine running hot — inspect cooling system or enrich mixture.",
                ),
                (
                    "Low speed, high throttle",
                    lambda d: d.get("Speed", 0) < 10 and d.get("Throttle", 0) > 70,
                    "Likely traction loss — consider traction control adjustments.",
                ),
                (
                    "Low ethanol content for boost",
                    lambda d: (_first(d, "Boost_Pressure", "Manifold_Pressure", "Boost") or 0) > 120
                    and (_first(d, "Ethanol_Content", "FlexFuel_Percent", "Fuel_EthanolPercent") or 100) < 70,
                    "Ethanol content is low for high boost—reduce load or switch to pump fuel.",
                ),
                (
                    "Methanol flow insufficient",
                    lambda d: (_first(d, "Boost_Pressure", "Manifold_Pressure", "Boost") or 0) > 120
                    and (_first(d, "Methanol_Flow", "MethInjection_Duty") or 0) < 20,
                    "Methanol injection duty is low while in boost—check pump, filters, or tank level.",
                ),
                (
                    "Nitrous bottle pressure low",
                    lambda d: (_first(d, "Nitrous_Solenoid_State", "Nitrous_Solenoid") or 0) > 0.5
                    and (_first(d, "Nitrous_Bottle_Pressure", "Nitrous_Pressure") or 2000) < 850,
                    "Nitrous system armed but bottle pressure is low—heat or refill bottle before next pass.",
                ),
                (
                    "Transbrake dragging",
                    lambda d: (_first(d, "TransBrake_State", "TransBrake") or 0) > 0.5
                    and (d.get("Speed", 0) or 0) > 5,
                    "Transbrake appears engaged while the car is moving—inspect release and wiring.",
                ),
            ]
        )

    def evaluate(self, data: Mapping[str, float]) -> List[str]:
        suggestions: List[str] = []
        for name, predicate, advice in self.rules:
            try:
                if predicate(data):
                    suggestions.append(advice)
            except Exception:
                continue
        return suggestions


__all__ = ["TuningAdvisor"]

