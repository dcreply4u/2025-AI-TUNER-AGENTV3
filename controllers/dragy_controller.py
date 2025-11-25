from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import QObject, QTimer

from interfaces import GPSInterface
from services import GeoLogger, PerformanceTracker
from ui.dragy_view import DragyView

LOGGER = logging.getLogger(__name__)


class DragyController(QObject):
    """Polls the GPS interface and feeds samples into the Dragy-style UI."""

    def __init__(
        self,
        view: DragyView,
        gps: Optional[GPSInterface] = None,
        tracker: Optional[PerformanceTracker] = None,
        geo_logger: Optional[GeoLogger] = None,
        poll_interval_ms: int = 200,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.view = view
        if gps:
            self.gps = gps
        else:
            try:
                self.gps = GPSInterface()
            except Exception as exc:  # pragma: no cover - hardware optional
                LOGGER.error("GPS interface unavailable: %s", exc)
                self.view.set_status("GPS unavailable")
                self.gps = None
        self.tracker = tracker or PerformanceTracker()
        self.geo_logger = geo_logger or GeoLogger()
        self.timer = QTimer(self)
        self.timer.setInterval(poll_interval_ms)
        self.timer.timeout.connect(self._poll)

    def start(self) -> None:
        self.timer.start()
        self.view.set_status("Listening to GPS…")

    def stop(self) -> None:
        if self.timer.isActive():
            self.timer.stop()
        self.view.set_status("Paused")

    # ------------------------------------------------------------------ #
    # Internal polling
    # ------------------------------------------------------------------ #
    def _poll(self) -> None:
        if not self.gps:
            self.view.set_status("GPS disabled")
            self.stop()
            return
        try:
            fix = self.gps.read_fix()
        except Exception as exc:  # pragma: no cover - hardware specific
            LOGGER.error("GPS read failure: %s", exc)
            self.view.set_status("GPS read error")
            return
        if not fix:
            return
        payload = fix.to_payload()
        self.geo_logger.log(payload)
        snapshot = self.tracker.ingest_fix(payload)
        self.view.update_fix(payload, snapshot)


__all__ = ["DragyController"]

