from __future__ import annotations

"""\
==================================================
OBD Interface – classic dongles, modern ergonomics
==================================================
The `OBDInterface` hides the gritty details of python-OBD setup, streaming, and DTC
management so that higher layers can treat it as a simple telemetry provider.  It also
exposes helper APIs for long-running polling threads and UI-friendly callbacks.
"""

import logging
import threading
import time
from typing import Callable, Dict, List, Mapping

try:
    import obd
except Exception:  # pragma: no cover - optional dependency
    obd = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class OBDInterface:
    """Thin wrapper around python-OBD with streaming helpers."""

    def __init__(self, port_str: str | None = None, poll_interval: float = 0.5) -> None:
        self.connection: "obd.OBD | None" = None
        self.poll_interval = poll_interval
        self.stop_event = threading.Event()
        self.port_str = port_str
        self.commands: Dict[str, "obd.commands.OBDCommand"] = {}
        if obd:
            self._build_command_map()

    def _build_command_map(self) -> None:
        assert obd is not None
        ports = obd.scan_serial()
        default_port = ports[0] if ports else "/dev/ttyUSB0"
        self.port_str = self.port_str or default_port
        self.commands = {
            "RPM": obd.commands.RPM,
            "Throttle": obd.commands.THROTTLE_POS,
            "CoolantTemp": obd.commands.COOLANT_TEMP,
            "Speed": obd.commands.SPEED,
        }

    def connect(self) -> None:
        if not obd:
            raise RuntimeError("python-OBD is not installed.")
        if self.connection and self.connection.is_connected():
            return
        LOGGER.info("Connecting to OBD-II on %s", self.port_str)
        self.connection = obd.OBD(self.port_str or "/dev/ttyUSB0", fast=False)
        LOGGER.info("OBD connection state: %s", self.connection.is_connected())

    def disconnect(self) -> None:
        if self.connection:
            try:
                self.connection.close()
            finally:
                self.connection = None

    def read_data(self) -> Dict[str, float]:
        if not self.connection or not self.connection.is_connected():
            return {}

        data: Dict[str, float] = {}
        for key, command in self.commands.items():
            response = self.connection.query(command)
            if response and not response.is_null():
                try:
                    data[key] = float(getattr(response.value, "magnitude", response.value))
                except Exception:
                    continue
        return data

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

    def get_dtc_codes(self) -> List[tuple[str, str]]:
        if not self.connection or not self.connection.is_connected():
            return []
        response = self.connection.query(obd.commands.GET_DTC)
        return [] if response.is_null() else list(response.value)

    def clear_dtc_codes(self) -> bool:
        if not self.connection or not self.connection.is_connected():
            return False
        self.connection.query(obd.commands.CLEAR_DTC)
        return True


__all__ = ["OBDInterface"]

