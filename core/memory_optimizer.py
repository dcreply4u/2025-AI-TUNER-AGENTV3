"""
Memory Optimizer

Aggressive memory management to keep the application lightweight.
"""

from __future__ import annotations

import gc
import logging
import sys
import threading
import time
import weakref
from collections import deque
from typing import Any, Callable, Dict, Optional

import psutil

LOGGER = logging.getLogger(__name__)


class MemoryOptimizer:
    """Manages memory usage and cleanup."""

    def __init__(self, target_memory_mb: float = 200.0, cleanup_interval: float = 30.0) -> None:
        """
        Initialize memory optimizer.

        Args:
            target_memory_mb: Target memory usage in MB
            cleanup_interval: Interval for automatic cleanup (seconds)
        """
        self.target_memory_mb = target_memory_mb
        self.cleanup_interval = cleanup_interval
        self.running = False
        self.cleanup_thread: Optional[threading.Thread] = None

        # Weak references for automatic cleanup
        self.weak_refs: Dict[str, weakref.ref] = {}
        self.cache_size_limit = 100  # Max items in cache
        self.caches: Dict[str, deque] = {}

    def start(self) -> None:
        """Start automatic memory cleanup."""
        if self.running:
            return

        self.running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        LOGGER.info("Memory optimizer started")

    def stop(self) -> None:
        """Stop memory optimizer."""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=2)

    def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while self.running:
            try:
                self.force_cleanup()
                time.sleep(self.cleanup_interval)
            except Exception as e:
                LOGGER.error("Error in memory cleanup: %s", e)
                time.sleep(self.cleanup_interval)

    def force_cleanup(self) -> Dict[str, Any]:
        """
        Force aggressive memory cleanup.

        Returns:
            Cleanup statistics
        """
        before = self.get_memory_usage()

        # Clear weak references to dead objects
        dead_keys = [k for k, ref in self.weak_refs.items() if ref() is None]
        for key in dead_keys:
            del self.weak_refs[key]

        # Trim caches
        for cache_name, cache in self.caches.items():
            while len(cache) > self.cache_size_limit:
                cache.popleft()

        # Force garbage collection
        collected = gc.collect()

        after = self.get_memory_usage()
        freed = before["used_mb"] - after["used_mb"]

        LOGGER.debug("Memory cleanup: freed %.2f MB, collected %d objects", freed, collected)

        return {
            "before_mb": before["used_mb"],
            "after_mb": after["used_mb"],
            "freed_mb": freed,
            "gc_collected": collected,
        }

    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage."""
        process = psutil.Process()
        mem_info = process.memory_info()
        return {
            "used_mb": mem_info.rss / (1024 * 1024),
            "available_mb": psutil.virtual_memory().available / (1024 * 1024),
            "percent": process.memory_percent(),
        }

    def register_cache(self, name: str, max_size: int = 100) -> deque:
        """
        Register a cache with size limit.

        Args:
            name: Cache name
            max_size: Maximum cache size

        Returns:
            Cache deque
        """
        cache = deque(maxlen=max_size)
        self.caches[name] = cache
        return cache

    def register_weak_ref(self, name: str, obj: Any) -> None:
        """Register a weak reference for automatic cleanup."""
        self.weak_refs[name] = weakref.ref(obj)

    def clear_cache(self, name: Optional[str] = None) -> None:
        """Clear cache(s)."""
        if name:
            if name in self.caches:
                self.caches[name].clear()
        else:
            for cache in self.caches.values():
                cache.clear()


class LazyLoader:
    """Lazy loading utility for UI components and modules."""

    _loaded_modules: Dict[str, Any] = {}
    _loading_locks: Dict[str, threading.Lock] = {}

    @classmethod
    def load_module(cls, module_name: str) -> Any:
        """
        Lazy load a module.

        Args:
            module_name: Module name to load

        Returns:
            Loaded module
        """
        if module_name in cls._loaded_modules:
            return cls._loaded_modules[module_name]

        if module_name not in cls._loading_locks:
            cls._loading_locks[module_name] = threading.Lock()

        with cls._loading_locks[module_name]:
            # Double-check after acquiring lock
            if module_name in cls._loaded_modules:
                return cls._loaded_modules[module_name]

            try:
                module = __import__(module_name, fromlist=[""])
                cls._loaded_modules[module_name] = module
                return module
            except ImportError as e:
                LOGGER.error("Failed to load module %s: %s", module_name, e)
                raise

    @classmethod
    def clear_cache(cls) -> None:
        """Clear loaded modules cache."""
        cls._loaded_modules.clear()


__all__ = ["MemoryOptimizer", "LazyLoader"]

