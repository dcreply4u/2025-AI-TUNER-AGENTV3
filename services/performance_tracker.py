from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

MPS_TO_MPH = 2.23694


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in meters between two WGS84 coordinates."""
    r = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


@dataclass
class PerformanceSnapshot:
    metrics: Dict[str, Optional[float]]
    best_metrics: Dict[str, Optional[float]]
    total_distance_m: float
    track_points: List[Tuple[float, float]]
    last_update: float


class PerformanceTracker:
    """Computes Dragy-style acceleration metrics and stores GPS traces."""

    SPEED_TARGETS = (10, 30, 60, 100)  # mph
    DISTANCE_TARGETS = {
        "60ft": 18.288,  # 60 feet in meters
        "1/8 mile": 201.168,
        "1/4 mile": 402.336,
        "1/2 mile": 804.672,  # 1/2 mile in meters
    }

    def __init__(self) -> None:
        self.reset_session()
        self.best_metrics: Dict[str, Optional[float]] = {
            f"0-{target} mph": None for target in self.SPEED_TARGETS
        }
        self.best_metrics.update({name: None for name in self.DISTANCE_TARGETS})

    def reset_session(self) -> None:
        self.session_start: Optional[float] = None
        self.event_times: Dict[str, Optional[float]] = {
            f"0-{target} mph": None for target in self.SPEED_TARGETS
        }
        self.event_times.update({name: None for name in self.DISTANCE_TARGETS})
        self.last_speed_mph: float = 0.0
        self.last_timestamp: Optional[float] = None
        self._last_motion_timestamp: Optional[float] = None
        self.distance_m: float = 0.0
        self.track: List[Tuple[float, float]] = []

    def _record_metric(self, name: str, value: float) -> None:
        previous = self.best_metrics.get(name)
        if previous is None or value < previous:
            self.best_metrics[name] = value

    def update_speed(self, speed_value: float, timestamp: Optional[float] = None) -> None:
        """Update tracker with latest speed reading (mph)."""
        timestamp = timestamp or time.time()
        if speed_value < 0:
            speed_value = 0.0

        if self.session_start is None and speed_value > 1.0:
            self.session_start = timestamp

        if self.session_start is not None:
            elapsed = timestamp - self.session_start
            for target in self.SPEED_TARGETS:
                key = f"0-{target} mph"
                if self.event_times[key] is None and speed_value >= target:
                    self.event_times[key] = elapsed
                    self._record_metric(key, elapsed)

        if self.last_timestamp is not None:
            dt = max(timestamp - self.last_timestamp, 0.0)
            avg_speed_mps = ((self.last_speed_mph + speed_value) / 2.0) * 0.44704
            self.distance_m += avg_speed_mps * dt
            for name, threshold in self.DISTANCE_TARGETS.items():
                if self.event_times[name] is None and self.distance_m >= threshold:
                    duration = (timestamp - (self.session_start or timestamp))
                    self.event_times[name] = duration
                    self._record_metric(name, duration)

        self.last_speed_mph = speed_value
        self.last_timestamp = timestamp
        if speed_value > 1.0:
            self._last_motion_timestamp = timestamp
        elif (
            self._last_motion_timestamp
            and self.session_start
            and (timestamp - self._last_motion_timestamp) > 5
        ):
            self.reset_session()

    def update_gps(self, lat: float, lon: float) -> None:
        self.track.append((lat, lon))
        if len(self.track) > 2000:
            self.track.pop(0)

    def ingest_fix(self, fix: Dict[str, float]) -> PerformanceSnapshot:
        """Convenience helper to feed a GPS fix dict (lat/lon/speed/timestamp)."""
        speed_mps = float(fix.get("speed_mps", 0.0) or 0.0)
        timestamp = float(fix.get("timestamp", time.time()))
        self.update_speed(speed_mps * MPS_TO_MPH, timestamp)
        lat = fix.get("lat") or fix.get("latitude")
        lon = fix.get("lon") or fix.get("longitude")
        if lat is not None and lon is not None:
            self.update_gps(float(lat), float(lon))
        return self.snapshot()

    def snapshot(self) -> PerformanceSnapshot:
        return PerformanceSnapshot(
            metrics=dict(self.event_times),
            best_metrics=dict(self.best_metrics),
            total_distance_m=self.distance_m,
            track_points=list(self.track),
            last_update=self.last_timestamp or time.time(),
        )


__all__ = ["PerformanceTracker", "PerformanceSnapshot"]

