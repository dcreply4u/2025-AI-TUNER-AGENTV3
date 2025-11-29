from __future__ import annotations

"""
Session Analysis Service
------------------------

Light‑weight telemetry analysis that summarizes the latest logged session for
the Chat Advisor / AI Racing Coach.

This is NOT a full MoTeC‑grade i2 replacement – it provides quick, structured
insights that the Chat Advisor can turn into natural‑language answers such as:

- "You had lean AFR spikes on the main straight around 5200–5800 RPM."
- "Coolant temperature peaked at 106 °C near the end of the session."
- "Boost peaked at 23.5 psi, which is above your configured target."
"""

import csv
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .data_logger import DataLogger

LOGGER = logging.getLogger(__name__)


@dataclass
class SessionAnomaly:
    """Represents a single anomaly detected in a session."""

    type: str
    message: str
    severity: str = "info"  # "info" | "warning" | "critical"
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChannelSummary:
    """Simple statistics for a single telemetry channel."""

    name: str
    min: float
    max: float
    avg: float


@dataclass
class SessionAnalysisReport:
    """
    High‑level summary of a session that the Chat Advisor can consume.

    The goal is to keep this JSON‑serialisable and easy to feed into an LLM or
    rule‑based advisor.
    """

    log_file: Optional[str]
    sample_count: int
    duration_s: Optional[float]
    channel_summaries: List[ChannelSummary] = field(default_factory=list)
    anomalies: List[SessionAnomaly] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "log_file": self.log_file,
            "sample_count": self.sample_count,
            "duration_s": self.duration_s,
            "channel_summaries": [asdict(c) for c in self.channel_summaries],
            "anomalies": [asdict(a) for a in self.anomalies],
        }


class SessionAnalysisService:
    """
    Session analysis for recent telemetry logs.

    This service is intentionally simple and safe – it does not modify anything,
    only reads CSV logs produced by `DataLogger` and computes basic statistics
    and anomalies that the Chat Advisor can talk about.
    """

    def __init__(self, log_dir: str | Path = "logs") -> None:
        self.log_dir = Path(log_dir)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def analyze_latest_session(self) -> SessionAnalysisReport:
        """
        Analyze the most recent log file (if any).

        Returns a best‑effort analysis; if no logs are available, the report
        will have sample_count == 0 and no anomalies.
        """
        recent = DataLogger.get_recent_files(limit=1)
        if not recent:
            LOGGER.info("SessionAnalysisService: no recent log files found")
            return SessionAnalysisReport(
                log_file=None,
                sample_count=0,
                duration_s=None,
                channel_summaries=[],
                anomalies=[],
            )

        return self._analyze_log_file(recent[0])

    def analyze_specific_log(self, path: str | Path) -> SessionAnalysisReport:
        """Analyze a specific CSV log file path."""
        return self._analyze_log_file(Path(path))

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _analyze_log_file(self, file_path: Path) -> SessionAnalysisReport:
        if not file_path.exists():
            LOGGER.warning("SessionAnalysisService: log file does not exist: %s", file_path)
            return SessionAnalysisReport(
                log_file=str(file_path),
                sample_count=0,
                duration_s=None,
                channel_summaries=[],
                anomalies=[],
            )

        LOGGER.info("SessionAnalysisService: analyzing log file %s", file_path)

        with file_path.open("r", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            LOGGER.info("SessionAnalysisService: log file is empty: %s", file_path)
            return SessionAnalysisReport(
                log_file=str(file_path),
                sample_count=0,
                duration_s=None,
                channel_summaries=[],
                anomalies=[],
            )

        # Basic numeric stats per channel
        numeric_stats: Dict[str, Tuple[float, float, float, int]] = {}
        first_ts = None
        last_ts = None

        for row in rows:
            for key, value in row.items():
                if key.lower() in {"timestamp", "time", "t"}:
                    # Try to track duration if a timestamp column exists
                    try:
                        ts = float(value)
                    except (TypeError, ValueError):
                        continue
                    if first_ts is None:
                        first_ts = ts
                    last_ts = ts
                    continue

                try:
                    v = float(value)
                except (TypeError, ValueError):
                    continue

                if key not in numeric_stats:
                    numeric_stats[key] = (v, v, v, 1)  # min, max, sum, count
                else:
                    cur_min, cur_max, cur_sum, cur_count = numeric_stats[key]
                    numeric_stats[key] = (
                        min(cur_min, v),
                        max(cur_max, v),
                        cur_sum + v,
                        cur_count + 1,
                    )

        channel_summaries: List[ChannelSummary] = []
        for name, (vmin, vmax, vsum, cnt) in numeric_stats.items():
            avg = vsum / max(cnt, 1)
            channel_summaries.append(ChannelSummary(name=name, min=vmin, max=vmax, avg=avg))

        duration_s: Optional[float] = None
        if first_ts is not None and last_ts is not None and last_ts >= first_ts:
            duration_s = float(last_ts - first_ts)

        anomalies = self._detect_anomalies(channel_summaries)

        return SessionAnalysisReport(
            log_file=str(file_path),
            sample_count=len(rows),
            duration_s=duration_s,
            channel_summaries=channel_summaries,
            anomalies=anomalies,
        )

    def _detect_anomalies(self, summaries: List[ChannelSummary]) -> List[SessionAnomaly]:
        """
        Very simple heuristic anomaly detection.

        This is deliberately conservative – it looks for obvious issues like:
        - AFR very lean or very rich
        - Coolant / EGT very high
        - Boost significantly above a typical "safe" range
        """
        anomalies: List[SessionAnomaly] = []
        # Build quick lookup
        by_name = {s.name.lower(): s for s in summaries}

        def find_any(*names: str) -> Optional[ChannelSummary]:
            for n in names:
                s = by_name.get(n.lower())
                if s:
                    return s
            return None

        # AFR / Lambda checks
        afr_summary = find_any("afr", "AFR", "lambda", "Lambda", "Lambda1", "Lambda2")
        if afr_summary:
            # Approximate bounds – tuners will refine via knowledge base
            if afr_summary.max > 14.7 * 1.08:  # ~8% lean over stoich
                anomalies.append(
                    SessionAnomaly(
                        type="afr_lean",
                        severity="warning",
                        message="AFR peaked leaner than ~8% over stoich.",
                        details={"afr_max": afr_summary.max, "afr_avg": afr_summary.avg},
                    )
                )
            if afr_summary.min < 11.0:
                anomalies.append(
                    SessionAnomaly(
                        type="afr_rich",
                        severity="info",
                        message="AFR dipped richer than ~11.0:1.",
                        details={"afr_min": afr_summary.min, "afr_avg": afr_summary.avg},
                    )
                )

        # Coolant temperature
        clt_summary = find_any("CoolantTemp", "coolant_temp", "CLT", "EngineCoolantTemp")
        if clt_summary and clt_summary.max > 105.0:
            anomalies.append(
                SessionAnomaly(
                    type="coolant_overtemp",
                    severity="warning",
                    message="Coolant temperature exceeded ~105 °C.",
                    details={"coolant_max_c": clt_summary.max},
                )
            )

        # EGT
        egt_summary = find_any("EGT", "EGT1", "EGT2", "ExhaustTemp")
        if egt_summary and egt_summary.max > 900.0:
            anomalies.append(
                SessionAnomaly(
                    type="egt_high",
                    severity="warning",
                    message="Exhaust gas temperature exceeded ~900 °C.",
                    details={"egt_max_c": egt_summary.max},
                )
            )

        # Boost (assume kPa or psi depending on range)
        boost_summary = find_any("Boost", "Boost_Pressure", "MAP", "ManifoldPressure")
        if boost_summary:
            max_val = boost_summary.max
            details = {"boost_max_raw": max_val}
            # If looks like kPa, convert rough psi
            if max_val > 60.0:  # likely kPa absolute or gauge
                details["boost_max_kpa"] = max_val
                details["boost_max_psi_est"] = max_val * 0.145038
                if details["boost_max_psi_est"] > 22.0:
                    anomalies.append(
                        SessionAnomaly(
                            type="boost_high",
                            severity="info",
                            message="Boost pressure peaked above ~22 psi (estimated).",
                            details=details,
                        )
                    )
            else:
                details["boost_max_psi"] = max_val
                if max_val > 22.0:
                    anomalies.append(
                        SessionAnomaly(
                            type="boost_high",
                            severity="info",
                            message="Boost pressure peaked above ~22 psi.",
                            details=details,
                        )
                    )

        return anomalies


__all__ = [
    "SessionAnalysisService",
    "SessionAnalysisReport",
    "SessionAnomaly",
    "ChannelSummary",
]


