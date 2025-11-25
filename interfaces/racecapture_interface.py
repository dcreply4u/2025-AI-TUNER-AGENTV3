from __future__ import annotations

"""\
==========================================================
RaceCapture Interface – track-grade telemetry bridge
==========================================================
Provides a symmetric API to the OBD interface so callers can swap transport layers
without reworking business logic.  Streaming helpers mirror the same callback style to
keep controllers/UI pieces blissfully unaware of the underlying telemetry source.
"""

import logging
import threading
import time
from typing import Callable, Mapping

try:
    from racecapture import RaceCapture
except Exception:  # pragma: no cover - optional dependency
    RaceCapture = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class RaceCaptureInterface:
    """Wrapper around the RaceCapture SDK that mirrors the OBD API."""

    def __init__(self, port: str = "/dev/ttyUSB0", baud: int = 115200, poll_interval: float = 0.5) -> None:
        self.port = port
        self.baud = baud
        self.poll_interval = poll_interval
        self.rc: "RaceCapture | None" = None
        self.stop_event = threading.Event()

    def connect(self) -> None:
        if not RaceCapture:
            raise RuntimeError("RaceCapture SDK not installed.")
        if self.rc:
            return
        LOGGER.info("Connecting to RaceCapture on %s @ %s baud", self.port, self.baud)
        self.rc = RaceCapture(self.port, self.baud)

    def read_data(self) -> Mapping[str, float]:
        if not self.rc:
            return {}
        channels = self.rc.getChannels()
        return {
            "RPM": channels.get("RPM", 0.0),
            "Throttle": channels.get("Throttle", 0.0),
            "CoolantTemp": channels.get("CoolantTemp", 0.0),
            "Speed": channels.get("Speed", 0.0),
        }

    def stream_data(
        self,
        callback: Callable[[Mapping[str, float]], None],
        interval: float | None = None,
        stop_event: threading.Event | None = None,
    ) -> None:
        interval = interval or self.poll_interval
        local_stop = stop_event or self.stop_event
        while not local_stop.is_set():
            payload = self.read_data()
            if payload:
                callback(payload)
            time.sleep(interval)


__all__ = ["RaceCaptureInterface"]

