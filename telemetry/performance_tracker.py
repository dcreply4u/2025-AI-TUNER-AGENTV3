from __future__ import annotations

import json
import statistics
import time
from collections import deque
from pathlib import Path
from typing import Deque, Dict, List, Optional, Tuple

MPH_TO_MPS = 0.44704
QUARTER_MILE_METERS = 402.336


class PerformanceTracker:
    """Computes Dragy-style acceleration metrics from streaming GPS samples."""

    SPEED_TARGETS_MPH: Dict[str, float] = {
        "0-30 mph": 30.0,
        "0-60 mph": 60.0,
        "0-100 mph": 100.0,
    }
    SEGMENT_TARGETS: Dict[str, Tuple[float, float]] = {
        "60-130 mph": (60.0, 130.0),
    }

    def __init__(self, history_path: str | Path = "data_logs/performance_runs.json") -> None:
        self.history_path = Path(history_path)
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        self.history: List[Dict[str, float]] = self._load_history()
        self._best_cache: Dict[str, float] = self._build_best_cache(self.history)

        self._state = "idle"
        self._start_time: float | None = None
        self._start_distance: float = 0.0
        self._distance_accumulator = 0.0
        self._last_timestamp: float | None = None
        self._last_speed_mps: float = 0.0
        self._idle_timer: float = 0.0
        self._segment_hits: Dict[str, float] = {}
        self._segment_state: Dict[str, float] = {}
        self._run_points: Deque[Tuple[float, float]] = deque(maxlen=10_000)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def update(self, sample: Dict[str, float]) -> Dict[str, float]:
        """Return any newly-earned metrics for the active run."""
        timestamp = sample.get("timestamp", time.time())
        speed_mps = self._extract_speed(sample)
        speed_mph = speed_mps / MPH_TO_MPS

        self._integrate_distance(timestamp, speed_mps)
        self._run_points.append((timestamp, speed_mph))

        metrics: Dict[str, float] = {}
        self._handle_state_machine(speed_mph, timestamp)

        if self._state != "running" or self._start_time is None:
            return metrics

        # Straight-line metrics (0-60, etc.)
        for label, target_speed in self.SPEED_TARGETS_MPH.items():
            if label in self._segment_hits:
                continue
            if speed_mph >= target_speed:
                delta = timestamp - self._start_time
                metrics[label] = round(delta, 3)
                self._segment_hits[label] = delta
                self._update_best(label, delta)

        # Rolling segments (60-130, etc.)
        for label, (start_speed, end_speed) in self.SEGMENT_TARGETS.items():
            start_key = f"{label}_start"
            if label in self._segment_hits:
                continue
            if start_key not in self._segment_state and speed_mph >= start_speed:
                self._segment_state[start_key] = timestamp
            if start_key in self._segment_state and speed_mph >= end_speed:
                delta = timestamp - self._segment_state[start_key]
                metrics[label] = round(delta, 3)
                self._segment_hits[label] = delta
                self._update_best(label, delta)

        # Distance-based metrics
        run_distance = self._distance_accumulator - self._start_distance
        if "1/4 mile" not in self._segment_hits and run_distance >= QUARTER_MILE_METERS:
            delta = timestamp - self._start_time
            metrics["1/4 mile"] = round(delta, 3)
            self._segment_hits["1/4 mile"] = delta
            self._update_best("1/4 mile", delta)

        return metrics

    def best_metrics(self) -> Dict[str, float]:
        return dict(self._best_cache)

    def recent_runs(self, limit: int = 5) -> List[Dict[str, float]]:
        return self.history[-limit:]

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _handle_state_machine(self, speed_mph: float, timestamp: float) -> None:
        if speed_mph < 1.0:
            self._idle_timer += self._delta_time(timestamp)
        else:
            self._idle_timer = 0.0

        if self._state == "idle":
            if speed_mph > 1.5:
                self._start_run(timestamp)
            return

        if self._state == "running" and self._idle_timer > 3.0:
            self._finalize_run(timestamp)
            self._state = "idle"

    def _start_run(self, timestamp: float) -> None:
        self._state = "running"
        self._start_time = timestamp
        self._start_distance = self._distance_accumulator
        self._segment_hits.clear()
        self._segment_state.clear()
        self._run_points.clear()

    def _finalize_run(self, timestamp: float) -> None:
        if not self._segment_hits or self._start_time is None:
            self._state = "idle"
            return

        run_summary = {
            "started_at": self._start_time,
            "duration": timestamp - self._start_time,
            **{k: float(v) for k, v in self._segment_hits.items()},
        }
        self.history.append(run_summary)
        self._persist_history()
        self._start_time = None

    def _integrate_distance(self, timestamp: float, speed_mps: float) -> None:
        if self._last_timestamp is None:
            self._last_timestamp = timestamp
            self._last_speed_mps = speed_mps
            return
        delta_t = max(0.0, timestamp - self._last_timestamp)
        avg_speed = 0.5 * (self._last_speed_mps + speed_mps)
        self._distance_accumulator += avg_speed * delta_t
        self._last_timestamp = timestamp
        self._last_speed_mps = speed_mps

    def _delta_time(self, timestamp: float) -> float:
        if self._last_timestamp is None:
            return 0.0
        return max(0.0, timestamp - self._last_timestamp)

    @staticmethod
    def _extract_speed(sample: Dict[str, float]) -> float:
        if "speed_mps" in sample:
            return float(sample["speed_mps"])
        if "speed_kph" in sample:
            return float(sample["speed_kph"]) / 3.6
        if "speed_mph" in sample:
            return float(sample["speed_mph"]) * MPH_TO_MPS
        if "speed" in sample:
            return float(sample["speed"])
        return 0.0

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #
    def _load_history(self) -> List[Dict[str, float]]:
        if not self.history_path.exists():
            return []
        try:
            return json.loads(self.history_path.read_text())
        except json.JSONDecodeError:
            return []

    def _persist_history(self) -> None:
        data = json.dumps(self.history[-500:], indent=2)
        self.history_path.write_text(data)

    def _build_best_cache(self, history: List[Dict[str, float]]) -> Dict[str, float]:
        cache: Dict[str, float] = {}
        for run in history:
            for key, value in run.items():
                if key in {"started_at", "duration"}:
                    continue
                if key not in cache or value < cache[key]:
                    cache[key] = value
        return cache

    def _update_best(self, metric: str, value: float) -> None:
        best = self._best_cache.get(metric)
        if best is None or value < best:
            self._best_cache[metric] = value


__all__ = ["PerformanceTracker"]

