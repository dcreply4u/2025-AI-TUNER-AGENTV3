from __future__ import annotations

"""\
===========================================================
Fault Analyzer – Knowledge-infused DTC insight generation
===========================================================
This module bundles a lightweight, fully in-memory expert system that can turn raw
OBD-II or UDS DTC pairs into human-friendly, action-oriented insights.  While simple,
it provides the scaffolding for layering additional heuristics, cloud lookups, or
LLM-backed explainers without forcing the UI/controller layers to change.
"""

from typing import Dict, Iterable, List, Tuple


class FaultAnalyzer:
    """Simple knowledge-base driven analyzer for DTC codes."""

    DEFAULT_KNOWLEDGE_BASE: Dict[str, str] = {
        "P0300": (
            "Random/Multiple Cylinder Misfire Detected — inspect spark plugs, "
            "coils, and fuel delivery."
        ),
        "P0171": (
            "System Too Lean (Bank 1) — look for vacuum leaks or a faulty MAF sensor."
        ),
        "P0420": (
            "Catalyst System Efficiency Below Threshold — evaluate catalytic "
            "converter and downstream O2 sensors."
        ),
        "P0113": (
            "Intake Air Temperature Sensor Circuit High Input — check the IAT "
            "sensor and wiring."
        ),
        "P0128": (
            "Coolant Thermostat Below Regulating Temperature — thermostat may be "
            "stuck open."
        ),
    }

    def __init__(self, knowledge_base: Dict[str, str] | None = None) -> None:
        self.knowledge_base = dict(self.DEFAULT_KNOWLEDGE_BASE)
        if knowledge_base:
            self.knowledge_base.update(knowledge_base)

    def analyze(self, dtc_list: Iterable[Tuple[str, str | None]]) -> List[str]:
        """Return human-friendly insight strings for each DTC."""
        insights: List[str] = []
        for code, description in dtc_list:
            normalized_code = code.strip().upper()
            insight = self.knowledge_base.get(normalized_code)
            if insight:
                insights.append(f"{normalized_code}: {insight}")
            else:
                desc = description or "No description provided."
                insights.append(f"{normalized_code}: {desc} (no AI insight yet)")
        return insights


__all__ = ["FaultAnalyzer"]

