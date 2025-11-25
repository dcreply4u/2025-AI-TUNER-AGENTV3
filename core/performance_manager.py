"""
Performance Manager

Manages system resources, thread pools, memory, and performance optimization.
"""

from __future__ import annotations

import gc
import logging
import os
import psutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from queue import Queue
from typing import Callable, Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of system resources."""

    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    THREADS = "threads"


@dataclass
class ResourceUsage:
    """Resource usage information."""

    resource_type: ResourceType
    current: float
    max_available: float
    percentage: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot."""

    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    active_threads: int
    timestamp: float = field(default_factory=time.time)


class ThreadPoolManager:
    """Manages thread pools for concurrent operations."""

    def __init__(self, max_workers: Optional[int] = None) -> None:
        """
        Initialize thread pool manager.

        Args:
            max_workers: Maximum number of worker threads (None = auto)
        """
        if max_workers is None:
            # Use CPU count, but limit to reasonable number
            max_workers = min(os.cpu_count() or 4, 8)

        self.max_workers = max_workers
        self.executor: Optional[ThreadPoolExecutor] = None
        self._lock = threading.Lock()

    def get_executor(self) -> ThreadPoolExecutor:
        """Get or create thread pool executor."""
        with self._lock:
            if self.executor is None or self.executor._shutdown:
                self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
            return self.executor

    def submit(self, fn: Callable, *args, **kwargs):
        """Submit a task to the thread pool."""
        executor = self.get_executor()
        return executor.submit(fn, *args, **kwargs)

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown thread pool."""
        with self._lock:
            if self.executor:
                self.executor.shutdown(wait=wait)
                self.executor = None


class PerformanceManager:
    """Manages system performance and resources."""

    def __init__(self, monitoring_interval: float = 5.0) -> None:
        """
        Initialize performance manager.

        Args:
            monitoring_interval: Interval for performance monitoring (seconds)
        """
        self.monitoring_interval = monitoring_interval
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None

        self.thread_pool = ThreadPoolManager()
        self.resource_history: List[PerformanceMetrics] = []
        self.max_history = 1000

        # Resource limits
        self.cpu_warning_threshold = 80.0
        self.memory_warning_threshold = 85.0
        self.disk_warning_threshold = 90.0

        # Callbacks
        self.warning_callbacks: List[Callable[[ResourceUsage], None]] = []

    def start_monitoring(self) -> None:
        """Start performance monitoring."""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        LOGGER.info("Started performance monitoring")

    def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        LOGGER.info("Stopped performance monitoring")

    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while self.monitoring:
            try:
                metrics = self.get_current_metrics()
                self.resource_history.append(metrics)

                # Trim history
                if len(self.resource_history) > self.max_history:
                    self.resource_history.pop(0)

                # Check for warnings
                self._check_resource_warnings(metrics)

                time.sleep(self.monitoring_interval)
            except Exception as e:
                LOGGER.error("Error in performance monitoring: %s", e)
                time.sleep(self.monitoring_interval)

    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        process = psutil.Process()

        # CPU
        cpu_percent = process.cpu_percent(interval=0.1)

        # Memory
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        memory_used_mb = memory_info.rss / (1024 * 1024)
        system_memory = psutil.virtual_memory()
        memory_available_mb = system_memory.available / (1024 * 1024)

        # Disk
        disk_usage = psutil.disk_usage("/")
        disk_usage_percent = disk_usage.percent

        # Threads
        active_threads = threading.active_count()

        return PerformanceMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            memory_available_mb=memory_available_mb,
            disk_usage_percent=disk_usage_percent,
            active_threads=active_threads,
        )

    def _check_resource_warnings(self, metrics: PerformanceMetrics) -> None:
        """Check for resource warnings and trigger callbacks."""
        warnings = []

        if metrics.cpu_percent > self.cpu_warning_threshold:
            warnings.append(
                ResourceUsage(
                    resource_type=ResourceType.CPU,
                    current=metrics.cpu_percent,
                    max_available=100.0,
                    percentage=metrics.cpu_percent,
                )
            )

        if metrics.memory_percent > self.memory_warning_threshold:
            warnings.append(
                ResourceUsage(
                    resource_type=ResourceType.MEMORY,
                    current=metrics.memory_percent,
                    max_available=100.0,
                    percentage=metrics.memory_percent,
                )
            )

        if metrics.disk_usage_percent > self.disk_warning_threshold:
            warnings.append(
                ResourceUsage(
                    resource_type=ResourceType.DISK,
                    current=metrics.disk_usage_percent,
                    max_available=100.0,
                    percentage=metrics.disk_usage_percent,
                )
            )

        # Trigger callbacks
        for warning in warnings:
            for callback in self.warning_callbacks:
                try:
                    callback(warning)
                except Exception as e:
                    LOGGER.error("Error in warning callback: %s", e)

    def optimize_memory(self) -> Dict[str, Any]:
        """
        Optimize memory usage.

        Returns:
            Dictionary with optimization results
        """
        before = self.get_current_metrics()

        # Force garbage collection
        collected = gc.collect()

        # Clear caches if possible
        # (This would need to be implemented per-module)

        after = self.get_current_metrics()

        freed_mb = before.memory_used_mb - after.memory_used_mb

        result = {
            "gc_collected": collected,
            "memory_freed_mb": freed_mb,
            "before_mb": before.memory_used_mb,
            "after_mb": after.memory_used_mb,
        }

        LOGGER.info("Memory optimization: freed %.2f MB", freed_mb)
        return result

    def get_resource_usage(self, resource_type: ResourceType) -> Optional[ResourceUsage]:
        """Get current usage for a specific resource."""
        metrics = self.get_current_metrics()

        if resource_type == ResourceType.CPU:
            return ResourceUsage(
                resource_type=ResourceType.CPU,
                current=metrics.cpu_percent,
                max_available=100.0,
                percentage=metrics.cpu_percent,
            )
        elif resource_type == ResourceType.MEMORY:
            return ResourceUsage(
                resource_type=ResourceType.MEMORY,
                current=metrics.memory_percent,
                max_available=100.0,
                percentage=metrics.memory_percent,
            )
        elif resource_type == ResourceType.DISK:
            return ResourceUsage(
                resource_type=ResourceType.DISK,
                current=metrics.disk_usage_percent,
                max_available=100.0,
                percentage=metrics.disk_usage_percent,
            )
        elif resource_type == ResourceType.THREADS:
            return ResourceUsage(
                resource_type=ResourceType.THREADS,
                current=float(metrics.active_threads),
                max_available=100.0,  # Arbitrary max
                percentage=(metrics.active_threads / 100.0) * 100,
            )

        return None

    def register_warning_callback(self, callback: Callable[[ResourceUsage], None]) -> None:
        """Register a callback for resource warnings."""
        self.warning_callbacks.append(callback)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if not self.resource_history:
            return {}

        recent = self.resource_history[-10:] if len(self.resource_history) >= 10 else self.resource_history

        avg_cpu = sum(m.cpu_percent for m in recent) / len(recent)
        avg_memory = sum(m.memory_percent for m in recent) / len(recent)
        avg_disk = sum(m.disk_usage_percent for m in recent) / len(recent)

        return {
            "average_cpu_percent": avg_cpu,
            "average_memory_percent": avg_memory,
            "average_disk_percent": avg_disk,
            "current_threads": recent[-1].active_threads if recent else 0,
            "samples": len(recent),
        }

    def submit_task(self, fn: Callable, *args, **kwargs):
        """Submit a task to the thread pool."""
        return self.thread_pool.submit(fn, *args, **kwargs)

    def shutdown(self) -> None:
        """Shutdown performance manager."""
        self.stop_monitoring()
        self.thread_pool.shutdown()


__all__ = ["PerformanceManager", "ResourceUsage", "ResourceType", "PerformanceMetrics", "ThreadPoolManager"]

