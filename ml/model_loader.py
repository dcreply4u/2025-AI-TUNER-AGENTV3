from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Sequence

try:
    import joblib
except Exception:  # pragma: no cover - optional dependency
    joblib = None  # type: ignore


class ModelLoader:
    """Handles loading and caching of edge AI/ML models."""

    def __init__(self, model_path: str | Path = "models/default_model.pkl") -> None:
        self.model_path = Path(model_path)
        self.model: Any | None = None

    def load_model(self, force_reload: bool = False) -> Any:
        """Load the model from disk and cache it in memory."""
        if self.model and not force_reload:
            return self.model
        if not joblib:
            raise RuntimeError("joblib is required to load serialized models.")
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        self.model = joblib.load(self.model_path)
        print(f"[ModelLoader] Loaded model from {self.model_path}")
        return self.model

    def predict(self, input_data: Sequence[float] | Iterable[float]) -> Any:
        """Run inference on the provided input vector."""
        if not self.model:
            self.load_model()
        if not hasattr(self.model, "predict"):
            raise AttributeError("Loaded model does not expose a predict() method.")
        return self.model.predict([list(input_data)])


__all__ = ["ModelLoader"]


