"""
Memory Manager

Manages memory usage, cleanup, and optimization.
"""

from __future__ import annotations

import gc
import logging
import sys
import tracemalloc
import weakref
from collections import deque
from typing import Any, Callable, Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class MemoryManager:
    """Manages memory usage and cleanup."""

    def __init__(self, max_memory_mb: float = 512.0, cleanup_threshold: float = 0.8) -> None:
        """
        Initialize memory manager.

        Args:
            max_memory_mb: Maximum memory usage in MB
            cleanup_threshold: Threshold (0-1) to trigger cleanup
        """
        self.max_memory_mb = max_memory_mb
        self.cleanup_threshold = cleanup_threshold
        self.cleanup_callbacks: List[Callable[[], None]] = []
        self.object_registry: weakref.WeakSet = weakref.WeakSet()
        self.large_objects: deque = deque(maxlen=100)  # Track large objects

        # Enable memory tracking
        try:
            tracemalloc.start()
            self.tracking_enabled = True
        except Exception:
            self.tracking_enabled = False
            LOGGER.warning("Memory tracking not available")

    def register_cleanup(self, callback: Callable[[], None]) -> None:
        """Register a cleanup callback."""
        self.cleanup_callbacks.append(callback)

    def register_object(self, obj: Any) -> None:
        """Register an object for tracking."""
        self.object_registry.add(obj)

    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        return {
            "rss_mb": memory_info.rss / (1024 * 1024),  # Resident Set Size
            "vms_mb": memory_info.vms / (1024 * 1024),  # Virtual Memory Size
            "percent": process.memory_percent(),
        }

    def should_cleanup(self) -> bool:
        """Check if cleanup is needed."""
        usage = self.get_memory_usage()
        memory_percent = usage["percent"]
        return memory_percent > (self.cleanup_threshold * 100)

    def cleanup(self, aggressive: bool = False) -> Dict[str, Any]:
        """
        Perform memory cleanup.

        Args:
            aggressive: Use aggressive cleanup (more thorough but slower)

        Returns:
            Cleanup statistics
        """
        before = self.get_memory_usage()

        # Run registered cleanup callbacks
        for callback in self.cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                LOGGER.error("Error in cleanup callback: %s", e)

        # Clear large object cache
        self.large_objects.clear()

        # Force garbage collection
        if aggressive:
            collected = gc.collect(2)  # Collect generation 2
            gc.collect(1)  # Collect generation 1
            gc.collect(0)  # Collect generation 0
        else:
            collected = gc.collect()

        after = self.get_memory_usage()

        freed_mb = before["rss_mb"] - after["rss_mb"]

        result = {
            "before_mb": before["rss_mb"],
            "after_mb": after["rss_mb"],
            "freed_mb": freed_mb,
            "gc_collected": collected,
            "aggressive": aggressive,
        }

        LOGGER.info("Memory cleanup: freed %.2f MB", freed_mb)
        return result

    def get_memory_snapshot(self) -> Optional[Dict[str, Any]]:
        """Get memory snapshot for analysis."""
        if not self.tracking_enabled:
            return None

        try:
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics("lineno")

            total_size = sum(stat.size for stat in top_stats)
            top_10 = [
                {
                    "file": stat.traceback[0].filename if stat.traceback else "unknown",
                    "size_mb": stat.size / (1024 * 1024),
                    "count": stat.count,
                }
                for stat in top_stats[:10]
            ]

            return {
                "total_mb": total_size / (1024 * 1024),
                "top_allocations": top_10,
            }
        except Exception as e:
            LOGGER.error("Error getting memory snapshot: %s", e)
            return None

    def optimize_imports(self) -> None:
        """Optimize imports by removing unused modules."""
        # This would need to be called carefully
        # Could remove unused modules from sys.modules
        pass


class CircularBuffer:
    """Memory-efficient circular buffer."""

    def __init__(self, max_size: int):
        self.max_size = max_size
        self.buffer: deque = deque(maxlen=max_size)

    def append(self, item: Any) -> None:
        """Append item, automatically removing oldest if full."""
        self.buffer.append(item)

    def get_all(self) -> list:
        """Get all items."""
        return list(self.buffer)

    def clear(self) -> None:
        """Clear buffer."""
        self.buffer.clear()


__all__ = ["MemoryManager", "CircularBuffer"]

