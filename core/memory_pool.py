"""
Memory Pool Allocator

Efficient memory management with:
- Pre-allocated memory pools
- Zero-allocation object reuse
- Memory fragmentation reduction
- Thread-safe allocation
"""

from __future__ import annotations

import logging
import threading
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

LOGGER = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class PoolStats:
    """Memory pool statistics."""

    total_allocated: int = 0
    total_freed: int = 0
    current_allocated: int = 0
    pool_hits: int = 0
    pool_misses: int = 0
    allocations: int = 0
    deallocations: int = 0


class MemoryPool(Generic[T]):
    """Thread-safe memory pool for object reuse."""

    def __init__(
        self,
        factory: Callable[[], T],
        initial_size: int = 10,
        max_size: int = 100,
        reset_fn: Optional[Callable[[T], None]] = None,
    ):
        """
        Initialize memory pool.

        Args:
            factory: Function to create new objects
            initial_size: Initial pool size
            max_size: Maximum pool size
            reset_fn: Function to reset object state before reuse
        """
        self.factory = factory
        self.max_size = max_size
        self.reset_fn = reset_fn

        # Pool of available objects
        self.pool: deque[T] = deque(maxlen=max_size)
        self._lock = threading.Lock()
        self.stats = PoolStats()

        # Pre-allocate initial objects
        for _ in range(initial_size):
            obj = self.factory()
            self.pool.append(obj)
            self.stats.total_allocated += 1

    def acquire(self) -> T:
        """
        Acquire object from pool.

        Returns:
            Object from pool or newly created
        """
        with self._lock:
            if self.pool:
                obj = self.pool.popleft()
                self.stats.pool_hits += 1
                self.stats.current_allocated += 1
                self.stats.allocations += 1

                # Reset object if reset function provided
                if self.reset_fn:
                    self.reset_fn(obj)

                return obj
            else:
                # Pool empty, create new object
                obj = self.factory()
                self.stats.pool_misses += 1
                self.stats.total_allocated += 1
                self.stats.current_allocated += 1
                self.stats.allocations += 1
                return obj

    def release(self, obj: T) -> None:
        """
        Release object back to pool.

        Args:
            obj: Object to release
        """
        with self._lock:
            if len(self.pool) < self.max_size:
                self.pool.append(obj)
                self.stats.current_allocated -= 1
                self.stats.deallocations += 1
            else:
                # Pool full, discard object
                self.stats.total_freed += 1
                self.stats.current_allocated -= 1
                self.stats.deallocations += 1

    def get_stats(self) -> PoolStats:
        """Get pool statistics."""
        with self._lock:
            return PoolStats(**self.stats.__dict__)

    def clear(self) -> None:
        """Clear pool."""
        with self._lock:
            self.pool.clear()
            self.stats.current_allocated = 0


class MemoryPoolManager:
    """Manager for multiple memory pools."""

    def __init__(self):
        """Initialize pool manager."""
        self.pools: Dict[str, MemoryPool[Any]] = {}
        self._lock = threading.Lock()

    def register_pool(
        self,
        name: str,
        factory: Callable[[], T],
        initial_size: int = 10,
        max_size: int = 100,
        reset_fn: Optional[Callable[[T], None]] = None,
    ) -> MemoryPool[T]:
        """
        Register a new memory pool.

        Args:
            name: Pool name
            factory: Object factory function
            initial_size: Initial pool size
            max_size: Maximum pool size
            reset_fn: Reset function

        Returns:
            Created memory pool
        """
        with self._lock:
            pool = MemoryPool(factory, initial_size, max_size, reset_fn)
            self.pools[name] = pool
            return pool

    def get_pool(self, name: str) -> Optional[MemoryPool[Any]]:
        """Get pool by name."""
        with self._lock:
            return self.pools.get(name)

    def get_all_stats(self) -> Dict[str, PoolStats]:
        """Get statistics for all pools."""
        with self._lock:
            return {name: pool.get_stats() for name, pool in self.pools.items()}

    def clear_all(self) -> None:
        """Clear all pools."""
        with self._lock:
            for pool in self.pools.values():
                pool.clear()


# Global pool manager instance
_pool_manager: Optional[MemoryPoolManager] = None
_manager_lock = threading.Lock()


def get_pool_manager() -> MemoryPoolManager:
    """Get global pool manager instance."""
    global _pool_manager
    with _manager_lock:
        if _pool_manager is None:
            _pool_manager = MemoryPoolManager()
        return _pool_manager


__all__ = ["MemoryPool", "MemoryPoolManager", "PoolStats", "get_pool_manager"]

