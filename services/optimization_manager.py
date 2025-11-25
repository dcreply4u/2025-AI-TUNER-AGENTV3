"""
Optimization Manager
Centralized optimization service for performance improvements
"""

from __future__ import annotations

import functools
import logging
import time
from collections import deque
from typing import Any, Callable, Dict, Optional

LOGGER = logging.getLogger(__name__)


class TelemetryUpdateBatcher:
    """Batch telemetry updates to reduce UI refresh overhead."""
    
    def __init__(self, batch_size: int = 10, batch_timeout: float = 0.1):
        """
        Initialize telemetry update batcher.
        
        Args:
            batch_size: Maximum number of updates to batch
            batch_timeout: Maximum time to wait before flushing (seconds)
        """
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.pending_updates: deque = deque(maxlen=batch_size * 2)
        self.last_flush_time = time.time()
        self.batch_lock = False
    
    def add_update(self, data: Dict[str, float]) -> bool:
        """
        Add telemetry update to batch.
        
        Returns:
            True if batch should be flushed
        """
        self.pending_updates.append((time.time(), data))
        
        # Check if we should flush
        should_flush = (
            len(self.pending_updates) >= self.batch_size or
            (time.time() - self.last_flush_time) >= self.batch_timeout
        )
        
        if should_flush:
            self.last_flush_time = time.time()
        
        return should_flush
    
    def get_batch(self) -> Optional[Dict[str, float]]:
        """Get and clear batched updates (merged)."""
        if not self.pending_updates:
            return None
        
        # Merge all pending updates (latest values win)
        merged = {}
        while self.pending_updates:
            _, data = self.pending_updates.popleft()
            merged.update(data)
        
        return merged


class ConnectionPool:
    """Simple connection pool for database operations."""
    
    def __init__(self, factory: Callable, max_size: int = 5):
        """
        Initialize connection pool.
        
        Args:
            factory: Function to create new connections
            max_size: Maximum pool size
        """
        self.factory = factory
        self.max_size = max_size
        self.pool: deque = deque(maxlen=max_size)
        self.active = 0
    
    def get_connection(self):
        """Get connection from pool or create new one."""
        if self.pool:
            self.active += 1
            return self.pool.popleft()
        else:
            self.active += 1
            return self.factory()
    
    def return_connection(self, conn):
        """Return connection to pool."""
        self.active -= 1
        if len(self.pool) < self.max_size:
            self.pool.append(conn)
        else:
            # Pool is full, close connection
            try:
                conn.close()
            except Exception:
                pass


def throttle(seconds: float):
    """
    Throttle function calls to maximum once per specified seconds.
    
    Args:
        seconds: Minimum time between calls
    """
    def decorator(func: Callable) -> Callable:
        last_called = [0.0]
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            if now - last_called[0] >= seconds:
                last_called[0] = now
                return func(*args, **kwargs)
            return None
        
        return wrapper
    return decorator


def debounce(seconds: float):
    """
    Debounce function calls - only execute after specified seconds of inactivity.
    
    Args:
        seconds: Wait time after last call
    """
    def decorator(func: Callable) -> Callable:
        last_called = [0.0]
        timer = [None]
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            last_called[0] = now
            
            def call_func():
                if time.time() - last_called[0] >= seconds:
                    return func(*args, **kwargs)
                return None
            
            # Cancel previous timer if exists
            if timer[0] is not None:
                try:
                    timer[0].cancel()
                except Exception:
                    pass
            
            # Schedule new call
            import threading
            timer[0] = threading.Timer(seconds, call_func)
            timer[0].start()
        
        return wrapper
    return decorator


class WidgetCache:
    """Cache for frequently accessed widgets to avoid recreation."""
    
    def __init__(self, max_size: int = 50):
        """
        Initialize widget cache.
        
        Args:
            max_size: Maximum number of widgets to cache
        """
        self.cache: Dict[str, Any] = {}
        self.max_size = max_size
        self.access_times: Dict[str, float] = {}
    
    def get(self, key: str, factory: Optional[Callable] = None) -> Optional[Any]:
        """Get widget from cache or create using factory."""
        if key in self.cache:
            self.access_times[key] = time.time()
            return self.cache[key]
        
        if factory:
            widget = factory()
            self.set(key, widget)
            return widget
        
        return None
    
    def set(self, key: str, widget: Any) -> None:
        """Add widget to cache."""
        if len(self.cache) >= self.max_size:
            # Remove least recently used
            if self.access_times:
                lru_key = min(self.access_times.items(), key=lambda x: x[1])[0]
                del self.cache[lru_key]
                del self.access_times[lru_key]
        
        self.cache[key] = widget
        self.access_times[key] = time.time()
    
    def clear(self) -> None:
        """Clear cache."""
        self.cache.clear()
        self.access_times.clear()


class DataBuffer:
    """Efficient circular buffer for telemetry data."""
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize data buffer.
        
        Args:
            max_size: Maximum number of data points
        """
        self.max_size = max_size
        self.buffer: deque = deque(maxlen=max_size)
        self.lock = False
    
    def append(self, data: Dict[str, float]) -> None:
        """Append data point."""
        self.buffer.append((time.time(), data))
    
    def get_recent(self, seconds: float = 1.0) -> list:
        """Get recent data points within specified seconds."""
        cutoff = time.time() - seconds
        return [(t, d) for t, d in self.buffer if t >= cutoff]
    
    def clear(self) -> None:
        """Clear buffer."""
        self.buffer.clear()


class OptimizationManager:
    """
    Centralized optimization manager.
    
    Provides:
    - Telemetry update batching
    - Connection pooling
    - Widget caching
    - Data buffering
    - Throttle/debounce utilities
    """
    
    def __init__(self):
        """Initialize optimization manager."""
        self.telemetry_batcher = TelemetryUpdateBatcher()
        self.widget_cache = WidgetCache()
        self.data_buffers: Dict[str, DataBuffer] = {}
        
        # Statistics
        self.stats = {
            "batched_updates": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }
    
    def get_data_buffer(self, name: str) -> DataBuffer:
        """Get or create data buffer."""
        if name not in self.data_buffers:
            self.data_buffers[name] = DataBuffer()
        return self.data_buffers[name]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get optimization statistics."""
        return {
            **self.stats,
            "cached_widgets": len(self.widget_cache.cache),
            "data_buffers": len(self.data_buffers),
        }


# Global instance
_optimization_manager: Optional[OptimizationManager] = None


def get_optimization_manager() -> OptimizationManager:
    """Get global optimization manager instance."""
    global _optimization_manager
    if _optimization_manager is None:
        _optimization_manager = OptimizationManager()
    return _optimization_manager
















