"""
Model Optimization Utilities

Provides model compression, quantization, and optimization for edge devices.
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

try:
    import torch
    TORCH_AVAILABLE = True
except Exception:
    TORCH_AVAILABLE = False

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False

LOGGER = logging.getLogger(__name__)


class ModelOptimizer:
    """Optimizes models for edge device deployment."""

    @staticmethod
    def quantize_model(model: Any, dtype: str = "int8") -> Any:
        """
        Quantize model to reduce size and speed up inference.

        Args:
            model: Model to quantize
            dtype: Target dtype ("int8", "int16", "float16")

        Returns:
            Quantized model
        """
        if not TORCH_AVAILABLE or not isinstance(model, torch.nn.Module):
            LOGGER.warning("Quantization only supported for PyTorch models")
            return model

        try:
            model.eval()
            if dtype == "int8":
                # Dynamic quantization (no calibration needed)
                quantized = torch.quantization.quantize_dynamic(
                    model, {torch.nn.LSTM, torch.nn.Linear}, dtype=torch.qint8
                )
                return quantized
            elif dtype == "float16":
                # Half precision
                return model.half()
            else:
                return model
        except Exception as e:
            LOGGER.warning(f"Quantization failed: {e}")
            return model

    @staticmethod
    def prune_model(model: Any, pruning_ratio: float = 0.2) -> Any:
        """
        Prune model to remove unnecessary connections.

        Args:
            model: Model to prune
            pruning_ratio: Fraction of connections to remove (0-1)

        Returns:
            Pruned model
        """
        if not TORCH_AVAILABLE or not isinstance(model, torch.nn.Module):
            LOGGER.warning("Pruning only supported for PyTorch models")
            return model

        try:
            # Simple magnitude-based pruning
            for module in model.modules():
                if isinstance(module, torch.nn.Linear):
                    # Calculate threshold
                    weights = module.weight.data
                    threshold = np.percentile(np.abs(weights.cpu().numpy()), pruning_ratio * 100)

                    # Create mask
                    mask = torch.abs(weights) > threshold
                    module.weight.data *= mask.float()

            return model
        except Exception as e:
            LOGGER.warning(f"Pruning failed: {e}")
            return model

    @staticmethod
    def compress_sklearn_model(model: Any, compression_ratio: float = 0.5) -> Any:
        """
        Compress scikit-learn models by reducing estimators.

        Args:
            model: scikit-learn model
            compression_ratio: Fraction of estimators to keep (0-1)

        Returns:
            Compressed model
        """
        if not SKLEARN_AVAILABLE:
            return model

        if isinstance(model, IsolationForest):
            # Reduce number of estimators
            original_n = model.n_estimators
            new_n = max(10, int(original_n * compression_ratio))
            if new_n < original_n:
                # Create new model with fewer estimators
                compressed = IsolationForest(
                    n_estimators=new_n,
                    contamination=model.contamination,
                    random_state=model.random_state,
                    max_samples=model.max_samples,
                )
                LOGGER.info(f"Compressed IsolationForest: {original_n} -> {new_n} estimators")
                return compressed

        return model

    @staticmethod
    def optimize_for_inference(model: Any) -> Any:
        """
        Apply all optimizations for inference.

        Args:
            model: Model to optimize

        Returns:
            Optimized model
        """
        if TORCH_AVAILABLE and isinstance(model, torch.nn.Module):
            model.eval()
            # Fuse operations if possible
            try:
                torch.jit.script(model)
            except Exception:
                pass

        return model

    @staticmethod
    def get_model_size(model: Any) -> Dict[str, float]:
        """
        Get model size information.

        Returns:
            Dictionary with size information (MB, parameters, etc.)
        """
        size_info = {
            "size_mb": 0.0,
            "parameters": 0,
            "compressed": False,
        }

        if TORCH_AVAILABLE and isinstance(model, torch.nn.Module):
            # Count parameters
            total_params = sum(p.numel() for p in model.parameters())
            size_info["parameters"] = total_params

            # Estimate size (rough)
            param_size = sum(p.numel() * p.element_size() for p in model.parameters())
            buffer_size = sum(b.numel() * b.element_size() for b in model.buffers())
            size_info["size_mb"] = (param_size + buffer_size) / (1024 * 1024)

        elif SKLEARN_AVAILABLE:
            # Estimate size from pickle
            try:
                pickled = pickle.dumps(model)
                size_info["size_mb"] = len(pickled) / (1024 * 1024)
            except Exception:
                pass

        return size_info


class InferenceCache:
    """Caching system for model inference to speed up repeated predictions."""

    def __init__(self, max_size: int = 1000, ttl: float = 60.0) -> None:
        """
        Initialize inference cache.

        Args:
            max_size: Maximum cache size
            ttl: Time-to-live in seconds
        """
        self.cache: Dict[str, tuple[Any, float]] = {}
        self.max_size = max_size
        self.ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        """Get cached result if available and not expired."""
        if key not in self.cache:
            return None

        result, timestamp = self.cache[key]
        import time
        if time.time() - timestamp > self.ttl:
            del self.cache[key]
            return None

        return result

    def set(self, key: str, value: Any) -> None:
        """Cache a result."""
        import time
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]

        self.cache[key] = (value, time.time())

    def clear(self) -> None:
        """Clear cache."""
        self.cache.clear()


__all__ = ["ModelOptimizer", "InferenceCache"]

