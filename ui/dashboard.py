from __future__ import annotations

import time
from typing import Mapping

from logging_utils import get_logger


class Dashboard:
    """Lightweight CLI dashboard for quick telemetry checks."""

    def __init__(self, min_interval: float = 1.0) -> None:
        self.min_interval = max(min_interval, 0.1)
        self.last_update = 0.0
        self.logger = get_logger("dashboard")

    def _format_snapshot(self, data: Mapping[str, float]) -> str:
        parts = []
        for key, value in data.items():
            if isinstance(value, (int, float)):
                parts.append(f"{key}={value:.2f}")
            else:
                parts.append(f"{key}={value}")
        return ", ".join(parts)

    def update(self, data: Mapping[str, float]) -> None:
        """Rate-limited console update."""
        now = time.time()
        if (now - self.last_update) < self.min_interval:
            return
        snapshot = self._format_snapshot(data)
        self.logger.info("[Dashboard] %s", snapshot)
        self.last_update = now

    def clear(self) -> None:
        self.logger.info("[Dashboard] Cleared telemetry view.")


__all__ = ["Dashboard"]

