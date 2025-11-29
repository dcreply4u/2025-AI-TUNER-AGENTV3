from __future__ import annotations

"""
Tuning Suggestion Service
-------------------------

Generates high‑level tuning and setup suggestions from a SessionAnalysisReport.

This is deliberately conservative and acts as scaffolding for the Chat Advisor:
it does NOT change maps directly – it only produces human‑readable advice that
an experienced tuner can review.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

from .session_analysis_service import SessionAnalysisReport, SessionAnomaly


@dataclass
class TuningSuggestion:
    """Represents a single tuning or setup suggestion."""

    category: str  # "fuel", "ignition", "boost", "cooling", "safety", etc.
    message: str
    rationale: str
    severity: str = "info"  # "info" | "warning" | "critical"
    details: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Ensure details is at least an empty dict
        if data.get("details") is None:
            data["details"] = {}
        return data


class TuningSuggestionService:
    """
    Convert session anomalies into structured tuning/setup suggestions.
    """

    def suggest_from_session(self, report: SessionAnalysisReport) -> List[TuningSuggestion]:
        suggestions: List[TuningSuggestion] = []

        for anomaly in report.anomalies:
            s = self._suggest_for_anomaly(anomaly)
            if s:
                suggestions.extend(s)

        return suggestions

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _suggest_for_anomaly(self, anomaly: SessionAnomaly) -> List[TuningSuggestion]:
        t = anomaly.type
        out: List[TuningSuggestion] = []

        if t == "afr_lean":
            afr_max = anomaly.details.get("afr_max")
            out.append(
                TuningSuggestion(
                    category="fuel",
                    severity="warning",
                    message="AFR appears lean under load in the latest session.",
                    rationale=(
                        "The session analysis detected AFR values leaner than ~8% over stoich. "
                        "Under high load this can increase knock risk and exhaust temperatures."
                    ),
                    details={"afr_max": afr_max, "afr_avg": anomaly.details.get("afr_avg")},
                )
            )
            out.append(
                TuningSuggestion(
                    category="safety",
                    severity="info",
                    message="Consider enriching the fuel map slightly in the high‑load RPM range.",
                    rationale=(
                        "A small enrichment (e.g. 2‑5% more fuel) in the affected RPM/load cells can "
                        "add safety margin while you validate the behaviour across multiple runs."
                    ),
                    details={},
                )
            )

        elif t == "afr_rich":
            afr_min = anomaly.details.get("afr_min")
            out.append(
                TuningSuggestion(
                    category="fuel",
                    severity="info",
                    message="AFR dipped quite rich in parts of the session.",
                    rationale=(
                        "Running very rich can reduce power and increase fuel consumption. "
                        "If this is not intentional for safety (e.g. high boost), you may be able "
                        "to lean those cells slightly while monitoring knock and EGT."
                    ),
                    details={"afr_min": afr_min, "afr_avg": anomaly.details.get("afr_avg")},
                )
            )

        elif t == "coolant_overtemp":
            clt_max = anomaly.details.get("coolant_max_c")
            out.append(
                TuningSuggestion(
                    category="cooling",
                    severity="warning",
                    message="Coolant temperature exceeded typical safe track limits.",
                    rationale=(
                        "Sustained coolant temperatures above ~105 °C can reduce engine life "
                        "and increase knock sensitivity."
                    ),
                    details={"coolant_max_c": clt_max},
                )
            )
            out.append(
                TuningSuggestion(
                    category="cooling",
                    severity="info",
                    message="Consider richer mixtures, less ignition advance, or improved airflow/cooling.",
                    rationale=(
                        "Richer mixtures and slightly reduced ignition advance can help reduce "
                        "combustion temperatures. Also review radiator ducting, fan control, and "
                        "coolant mixture for track use."
                    ),
                    details={},
                )
            )

        elif t == "egt_high":
            egt_max = anomaly.details.get("egt_max_c")
            out.append(
                TuningSuggestion(
                    category="safety",
                    severity="warning",
                    message="Exhaust gas temperature reached a high level.",
                    rationale=(
                        "High EGT (around or above 900 °C) can indicate that the engine is working "
                        "very hard, potentially with lean mixtures or too much timing under boost."
                    ),
                    details={"egt_max_c": egt_max},
                )
            )
            out.append(
                TuningSuggestion(
                    category="ignition",
                    severity="info",
                    message="Review ignition timing and AFR in the high‑load cells where EGT is highest.",
                    rationale=(
                        "Reducing ignition timing slightly and/or enriching the mixture in the affected "
                        "cells can lower EGT and add safety margin."
                    ),
                    details={},
                )
            )

        elif t == "boost_high":
            boost_info = anomaly.details
            out.append(
                TuningSuggestion(
                    category="boost",
                    severity="info",
                    message="Boost pressure peaked higher than a typical conservative street/track target.",
                    rationale=(
                        "Higher boost increases cylinder pressure and temperature, which can demand "
                        "better fuel, more conservative ignition timing, and strong mechanical margins."
                    ),
                    details=boost_info,
                )
            )
            out.append(
                TuningSuggestion(
                    category="boost",
                    severity="info",
                    message="If reliability is a priority, consider lowering boost slightly or adding safeguards.",
                    rationale=(
                        "You can use boost control targets, gear/temperature compensations, and failsafes "
                        "to keep boost in a range the engine and fuel system can comfortably support."
                    ),
                    details={},
                )
            )

        return out


__all__ = ["TuningSuggestionService", "TuningSuggestion"]


