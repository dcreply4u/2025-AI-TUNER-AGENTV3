"""AI tuning engine using ONNX runtime for real-time calibration adjustments."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Sequence

import numpy as np

try:
    import onnxruntime as ort
except ImportError:
    ort = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class AITuningEngine:
    """
    AI-powered tuning engine using ONNX models.

    Suggests calibration adjustments based on telemetry data (RPM, load, AFR).
    """

    def __init__(self, model_path: str | Path = "ai_engine/model.onnx") -> None:
        """
        Initialize AI tuning engine.

        Args:
            model_path: Path to ONNX model file
        """
        self.model_path = Path(model_path)
        self.session: "ort.InferenceSession | None" = None
        self.input_name: str | None = None
        self._loaded = False

        if ort:
            self._load_model()
        else:
            LOGGER.warning("ONNX Runtime not available - AI tuning will use fallback heuristics")

    def _load_model(self) -> None:
        """Load ONNX model."""
        if not self.model_path.exists():
            LOGGER.warning("ONNX model not found at %s - using fallback", self.model_path)
            return

        try:
            self.session = ort.InferenceSession(str(self.model_path))
            if self.session.get_inputs():
                self.input_name = self.session.get_inputs()[0].name
            self._loaded = True
            LOGGER.info("AI Tuning Engine loaded: %s", self.model_path)
        except Exception as e:
            LOGGER.error("Failed to load ONNX model: %s", e)
            self.session = None

    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._loaded and self.session is not None

    def suggest_adjustments(self, telemetry_batch: Sequence[Sequence[float]]) -> np.ndarray:
        """
        Suggest tuning adjustments based on telemetry.

        Args:
            telemetry_batch: List of [RPM, load, AFR] tuples

        Returns:
            Array of suggested adjustments (e.g., fuel/ignition timing changes)
        """
        inputs = np.array(telemetry_batch, dtype=np.float32)

        if self.is_loaded() and self.input_name:
            try:
                outputs = self.session.run(None, {self.input_name: inputs})
                adjustments = outputs[0]
                LOGGER.info("AI suggested adjustments: %s", adjustments)
                return adjustments
            except Exception as e:
                LOGGER.error("ONNX inference failed: %s", e)

        # Fallback: Heuristic-based adjustments
        LOGGER.debug("Using fallback heuristic tuning")
        return self._heuristic_adjustments(inputs)

    def _heuristic_adjustments(self, telemetry: np.ndarray) -> np.ndarray:
        """
        Fallback heuristic tuning when ONNX model unavailable.

        Simple rule-based adjustments:
        - Lean AFR (< 14.0) -> reduce fuel
        - Rich AFR (> 15.0) -> increase fuel
        - High load -> advance timing
        - High RPM -> adjust fuel curve

        Args:
            telemetry: Array of [RPM, load, AFR] values

        Returns:
            Adjustment array
        """
        adjustments = []
        for row in telemetry:
            rpm, load, afr = row[0], row[1], row[2]

            # Fuel adjustment based on AFR
            fuel_adj = 0.0
            if afr < 14.0:  # Rich
                fuel_adj = -2.0 * (14.0 - afr)  # Reduce fuel
            elif afr > 15.0:  # Lean
                fuel_adj = 1.5 * (afr - 15.0)  # Increase fuel

            # Timing adjustment based on load
            timing_adj = load * 2.0  # Advance timing with load

            # Boost adjustment (if applicable)
            boost_adj = 0.0
            if load > 0.8:
                boost_adj = (load - 0.8) * 5.0

            adjustments.append([fuel_adj, timing_adj, boost_adj])

        return np.array(adjustments, dtype=np.float32)


__all__ = ["AITuningEngine"]

