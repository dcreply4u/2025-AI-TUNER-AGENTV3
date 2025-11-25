from __future__ import annotations

from typing import Callable, Dict, Mapping, MutableSequence, Optional

from ml import ModelLoader


class AIAgent:
    """Fuses EMS + sensor data and optionally runs ML inference."""

    def __init__(self, model_path: str | None = None) -> None:
        self.latest_ems_data: Dict[str, float] = {}
        self.latest_sensor_data: Dict[str, float] = {}
        self.model_loader = ModelLoader(model_path) if model_path else None
        self.observers: MutableSequence[Callable[[Dict[str, float]], None]] = []

    def register_observer(self, callback: Callable[[Dict[str, float]], None]) -> None:
        self.observers.append(callback)

    def process_ems_data(self, data: Mapping[str, float]) -> None:
        self.latest_ems_data.update(data)
        self._run_ai_logic()

    def process_sensor_data(self, data: Mapping[str, float]) -> None:
        self.latest_sensor_data.update(data)
        self._run_ai_logic()

    def _run_ai_logic(self) -> None:
        combined = {**self.latest_ems_data, **self.latest_sensor_data}
        if not combined:
            return

        prediction = None
        if self.model_loader:
            try:
                prediction = self.model_loader.predict(list(combined.values()))
            except Exception as exc:
                prediction = f"prediction_failed: {exc}"

        payload = {"data": combined, "prediction": prediction}
        for observer in self.observers:
            observer(payload)


__all__ = ["AIAgent"]

