"""
Performance Optimization Utilities

Provides utilities for lazy loading, update batching, and performance monitoring.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from functools import wraps
from threading import Thread
from typing import Any, Callable, Dict, Optional

from PySide6.QtCore import QObject, QTimer, Signal

LOGGER = logging.getLogger(__name__)


class LazyLoader:
    """Helper for lazy loading of expensive modules."""
    
    _cache: Dict[str, Any] = {}
    
    @classmethod
    def load(cls, module_path: str, attribute: Optional[str] = None):
        """
        Lazy load a module or attribute.
        
        Args:
            module_path: Full module path (e.g., 'ui.dyno_tab')
            attribute: Optional attribute name (e.g., 'DynoTab')
        
        Returns:
            Loaded module or attribute
        """
        cache_key = f"{module_path}.{attribute}" if attribute else module_path
        
        if cache_key in cls._cache:
            return cls._cache[cache_key]
        
        try:
            module = __import__(module_path, fromlist=[attribute] if attribute else [])
            result = getattr(module, attribute) if attribute else module
            cls._cache[cache_key] = result
            LOGGER.debug(f"Lazy loaded: {cache_key}")
            return result
        except (ImportError, AttributeError) as e:
            LOGGER.warning(f"Failed to lazy load {cache_key}: {e}")
            return None


class UpdateBatcher(QObject):
    """
    Batches multiple updates together to reduce UI refresh overhead.
    """
    
    update_ready = Signal(dict)  # Emitted when batched update is ready
    
    def __init__(self, batch_window_ms: int = 100, parent: Optional[QObject] = None):
        """
        Initialize update batcher.
        
        Args:
            batch_window_ms: Time window in milliseconds to collect updates
            parent: Parent QObject
        """
        super().__init__(parent)
        self.batch_window_ms = batch_window_ms
        self._pending_updates: Dict[str, Any] = {}
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._flush_batch)
        self._last_flush_time = time.time()
    
    def add_update(self, key: str, value: Any) -> None:
        """
        Add an update to the batch.
        
        Args:
            key: Update key/identifier
            value: Update value
        """
        self._pending_updates[key] = value
        
        # Start timer if not already running
        if not self._timer.isActive():
            self._timer.start(self.batch_window_ms)
    
    def _flush_batch(self) -> None:
        """Flush pending updates and emit signal."""
        if self._pending_updates:
            updates = self._pending_updates.copy()
            self._pending_updates.clear()
            self._last_flush_time = time.time()
            self.update_ready.emit(updates)
    
    def flush_now(self) -> None:
        """Immediately flush any pending updates."""
        if self._timer.isActive():
            self._timer.stop()
        self._flush_batch()


class CircularBuffer:
    """
    Circular buffer with fixed size for efficient data storage.
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize circular buffer.
        
        Args:
            max_size: Maximum number of items to store
        """
        self.max_size = max_size
        self._buffer = deque(maxlen=max_size)
        self._size = 0
    
    def append(self, item: Any) -> None:
        """Add item to buffer (automatically removes oldest if full)."""
        self._buffer.append(item)
        self._size = len(self._buffer)
    
    def extend(self, items: list) -> None:
        """Add multiple items to buffer."""
        for item in items:
            self.append(item)
    
    def get_all(self) -> list:
        """Get all items as a list."""
        return list(self._buffer)
    
    def get_recent(self, count: int) -> list:
        """Get the most recent N items."""
        return list(self._buffer)[-count:]
    
    def clear(self) -> None:
        """Clear all items."""
        self._buffer.clear()
        self._size = 0
    
    def __len__(self) -> int:
        return self._size
    
    def __iter__(self):
        return iter(self._buffer)


class Throttle:
    """
    Throttle function calls to maximum rate.
    """
    
    def __init__(self, max_calls_per_second: float = 10.0):
        """
        Initialize throttler.
        
        Args:
            max_calls_per_second: Maximum calls per second
        """
        self.min_interval = 1.0 / max_calls_per_second
        self._last_call_time = 0.0
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to throttle function calls."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            elapsed = current_time - self._last_call_time
            
            if elapsed >= self.min_interval:
                self._last_call_time = current_time
                return func(*args, **kwargs)
            # Otherwise, skip the call
        
        return wrapper


def throttle(max_calls_per_second: float = 10.0):
    """
    Decorator to throttle function calls.
    
    Args:
        max_calls_per_second: Maximum calls per second
    
    Example:
        @throttle(5.0)  # Max 5 calls per second
        def update_graph(data):
            ...
    """
    def decorator(func: Callable) -> Callable:
        throttler = Throttle(max_calls_per_second)
        return throttler(func)
    return decorator


class PerformanceMonitor:
    """
    Monitor and log performance metrics.
    """
    
    def __init__(self, enabled: bool = True):
        """
        Initialize performance monitor.
        
        Args:
            enabled: Whether monitoring is enabled
        """
        self.enabled = enabled
        self._metrics: Dict[str, list] = {}
    
    def record_timing(self, operation: str, duration: float) -> None:
        """
        Record timing for an operation.
        
        Args:
            operation: Operation name
            duration: Duration in seconds
        """
        if not self.enabled:
            return
        
        if operation not in self._metrics:
            self._metrics[operation] = []
        
        self._metrics[operation].append(duration)
        
        # Keep only last 100 measurements
        if len(self._metrics[operation]) > 100:
            self._metrics[operation].pop(0)
    
    def get_average_time(self, operation: str) -> Optional[float]:
        """
        Get average time for an operation.
        
        Args:
            operation: Operation name
        
        Returns:
            Average time in seconds, or None if no data
        """
        if operation not in self._metrics or not self._metrics[operation]:
            return None
        
        times = self._metrics[operation]
        return sum(times) / len(times)
    
    def get_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Get statistics for all operations.
        
        Returns:
            Dictionary mapping operation names to stats
        """
        stats = {}
        for operation, times in self._metrics.items():
            if times:
                stats[operation] = {
                    "avg": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times),
                    "count": len(times),
                }
        return stats


# Global performance monitor instance
_perf_monitor = PerformanceMonitor(enabled=False)


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance."""
    return _perf_monitor


def enable_performance_monitoring(enabled: bool = True) -> None:
    """Enable or disable performance monitoring."""
    global _perf_monitor
    _perf_monitor.enabled = enabled


def measure_time(operation: str):
    """
    Decorator to measure function execution time.
    
    Args:
        operation: Operation name for logging
    
    Example:
        @measure_time("update_telemetry")
        def update_telemetry(data):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                _perf_monitor.record_timing(operation, duration)
                if _perf_monitor.enabled and duration > 0.1:  # Log slow operations
                    LOGGER.debug(f"{operation} took {duration:.3f}s")
        return wrapper
    return decorator


def defer_to_background(func: Callable, *args, **kwargs) -> Thread:
    """
    Run a function in a background thread.
    
    Args:
        func: Function to run
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        Thread object
    """
    def run():
        try:
            func(*args, **kwargs)
        except Exception as e:
            LOGGER.error(f"Background task failed: {e}", exc_info=True)
    
    thread = Thread(target=run, daemon=True)
    thread.start()
    return thread

