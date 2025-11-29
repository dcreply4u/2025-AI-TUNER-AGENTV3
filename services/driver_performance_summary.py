from __future__ import annotations

"""
Driver Performance Summary Service
----------------------------------

Converts a PerformanceSnapshot into a compact, human‑readable summary that the
Chat Advisor can use to talk about straight‑line performance and distance.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

from .performance_tracker import PerformanceSnapshot


@dataclass
class DriverPerformanceSummary:
    """High‑level summary of acceleration and distance metrics."""

    best_0_60_s: Optional[float]
    best_quarter_mile_s: Optional[float]
    best_half_mile_s: Optional[float]
    total_distance_km: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DriverPerformanceSummaryService:
    """
    Build simple summaries from a PerformanceSnapshot.

    This does not try to replace full race‑analysis tools; it just exposes the
    key Dragy‑style numbers that are already computed by PerformanceTracker.
    """

    def summarize(self, snapshot: PerformanceSnapshot) -> DriverPerformanceSummary:
        metrics = snapshot.metrics
        best = snapshot.best_metrics

        # 0–60 mph
        best_0_60 = best.get("0-60") or best.get("0-60 mph") or metrics.get("0-60 mph")

        # Quarter/half mile
        best_qtr = best.get("1/4 mile") or metrics.get("1/4 mile")
        best_half = best.get("1/2 mile") or metrics.get("1/2 mile")

        total_km = (snapshot.total_distance_m or 0.0) / 1000.0

        return DriverPerformanceSummary(
            best_0_60_s=best_0_60,
            best_quarter_mile_s=best_qtr,
            best_half_mile_s=best_half,
            total_distance_km=total_km,
        )


__all__ = ["DriverPerformanceSummaryService", "DriverPerformanceSummary"]


