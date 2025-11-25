from __future__ import annotations

import random
import threading
import time
from typing import Callable, Dict, Iterable, Mapping, MutableSequence


class ExternalSensorInterface:
    """Interfaces with external sensors or simulators."""

    def __init__(self, read_interval: float = 0.1) -> None:
        self.listeners: MutableSequence[Callable[[Mapping[str, float]], None]] = []
        self.read_interval = read_interval
        self.running = False
        self._stop_event = threading.Event()

    def add_listener(self, callback: Callable[[Mapping[str, float]], None]) -> None:
        self.listeners.append(callback)

    def read_sensors(self) -> Dict[str, float]:
        """Simulate sensor data; override for hardware drivers."""
        return {
            "oil_temp": round(random.uniform(80, 100), 2),
            "tire_pressure": round(random.uniform(30, 35), 2),
            "ambient_temp": round(random.uniform(20, 25), 2),
        }

    def run(self) -> None:
        self.running = True
        self._stop_event.clear()
        print("[ExternalSensorInterface] Starting sensor read loop")
        try:
            while not self._stop_event.is_set():
                data = self.read_sensors()
                for callback in self.listeners:
                    callback(data)
                time.sleep(self.read_interval)
        except KeyboardInterrupt:
            print("[ExternalSensorInterface] Stopped by user")
        finally:
            self.running = False

    def stop(self) -> None:
        self._stop_event.set()


__all__ = ["ExternalSensorInterface"]


