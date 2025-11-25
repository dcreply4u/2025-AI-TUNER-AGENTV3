from __future__ import annotations

"""\
==============================================================
Predictive Fault Detector – Edge anomaly radar for telemetry
==============================================================
`PredictiveFaultDetector` wraps an IsolationForest (with graceful fallbacks when
scikit-learn/joblib are absent) to provide low-latency anomaly detection on rolling
telemetry windows.  It can learn from historical sessions, export buffers for offline
analysis, and emit warnings that the UI can style up in real time.
"""

import json
from pathlib import Path
from typing import Iterable, List, Mapping, Optional, Sequence

import numpy as np

try:
    from joblib import dump, load
except Exception:  # pragma: no cover - optional dependency
    dump = load = None  # type: ignore

try:
    from sklearn.ensemble import IsolationForest
except Exception:  # pragma: no cover - optional dependency
    IsolationForest = None  # type: ignore


class PredictiveFaultDetector:
    """IsolationForest-based anomaly detector with lightweight fallbacks."""

    def __init__(
        self,
        model_path: str | Path = "models/fault_predictor.joblib",
        features: Sequence[str] | None = None,
        contamination: float = 0.05,
        max_buffer: int = 512,
    ) -> None:
        self.model_path = Path(model_path)
        self.features = list(features or ["Engine_RPM", "Throttle_Position", "Coolant_Temp", "Vehicle_Speed"])
        self.contamination = contamination
        self.max_buffer = max_buffer
        self.buffer: List[List[float]] = []
        self.model = None
        self._trained = False
        self.min_training_samples = max(60, len(self.features) * 15)

        self._load_or_initialize_model()

    def _load_or_initialize_model(self) -> None:
        if self.model_path.exists() and load:
            try:
                self.model = load(self.model_path)
                # Assume persisted models were already trained
                self._trained = True
                return
            except Exception:
                pass

        if IsolationForest:
            self.model = IsolationForest(
                n_estimators=200,
                contamination=self.contamination,
                random_state=42,
            )
            self._trained = False

    def update(self, data: Mapping[str, float]) -> Optional[str]:
        """Update the rolling buffer and run inference if enough samples exist."""
        if not all(key in data for key in self.features):
            return None

        sample = [float(data[key]) for key in self.features]
        self.buffer.append(sample)
        if len(self.buffer) > self.max_buffer:
            self.buffer.pop(0)

        if len(self.buffer) < 20:
            return None
        buffer_array = np.array(self.buffer, dtype=float)

        if self.model:
            if not self._trained and len(self.buffer) >= self.min_training_samples:
                self._train_from_buffer(buffer_array)

            if not self._trained:
                # Not enough data to run the heavy model yet
                return None

            try:
                prediction = self.model.predict(np.array([sample], dtype=float))
                return "Anomaly Detected" if prediction[0] == -1 else None
            except AttributeError:
                # Model not fitted yet (sklearn raises AttributeError for estimators_)
                self._trained = False
                self._train_from_buffer(buffer_array)
                return None
            except Exception:
                # Any other errors fall back to heuristic detection
                pass

        # Lightweight fallback: z-score on rolling buffer
        arr = np.array(self.buffer[-50:])
        z_scores = np.abs((np.array(sample) - arr.mean(axis=0)) / (arr.std(axis=0) + 1e-6))
        if np.any(z_scores > 3.5):
            return "Anomaly Detected (fallback heuristic)"
        return None

    def train(self, historical_data: Iterable[Mapping[str, float]]) -> None:
        rows = []
        for row in historical_data:
            if all(feature in row for feature in self.features):
                rows.append([float(row[feature]) for feature in self.features])

        if not rows:
            raise ValueError("No valid rows provided for training.")

        if not self.model and IsolationForest:
            self._load_or_initialize_model()

        if self.model:
            self.model.fit(np.array(rows))
            self._trained = True
            if dump:
                self.model_path.parent.mkdir(parents=True, exist_ok=True)
                dump(self.model, self.model_path)

    def export_buffer(self, destination: str | Path) -> None:
        Path(destination).write_text(
            json.dumps({"features": self.features, "buffer": self.buffer}, indent=2)
        )

    def _train_from_buffer(self, buffer_array: np.ndarray) -> bool:
        """Train the isolation forest from the current rolling buffer."""
        if not self.model or len(buffer_array) < self.min_training_samples:
            return False

        try:
            train_data = buffer_array[-self.min_training_samples :]
            self.model.fit(train_data)
            self._trained = True
            if dump:
                self.model_path.parent.mkdir(parents=True, exist_ok=True)
                dump(self.model, self.model_path)
            return True
        except Exception:
            self._trained = False
            return False


__all__ = ["PredictiveFaultDetector"]

