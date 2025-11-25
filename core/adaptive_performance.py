"""
Adaptive Performance Optimizer

Dynamically adjusts system parameters based on:
- Current workload
- Resource availability
- Performance metrics
- Historical patterns
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Any, Callable, Dict, List, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class PerformanceMode(Enum):
    """Performance optimization modes."""

    LOW_POWER = "low_power"
    BALANCED = "balanced"
    HIGH_PERFORMANCE = "high_performance"
    TURBO = "turbo"


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot."""

    timestamp: float
    cpu_percent: float
    memory_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_io_mb: float
    active_threads: int
    query_latency_ms: float = 0.0
    cache_hit_rate: float = 0.0


@dataclass
class AdaptiveConfig:
    """Adaptive configuration parameters."""

    cache_size_mb: float = 256.0
    query_batch_size: int = 100
    update_interval_ms: int = 100
    thread_pool_size: int = 4
    prefetch_enabled: bool = True
    compression_enabled: bool = False
    mode: PerformanceMode = PerformanceMode.BALANCED


class AdaptivePerformanceOptimizer:
    """Adaptive performance optimizer."""

    def __init__(
        self,
        initial_config: Optional[AdaptiveConfig] = None,
        adaptation_interval: float = 30.0,
    ):
        """
        Initialize adaptive optimizer.

        Args:
            initial_config: Initial configuration
            adaptation_interval: How often to adapt (seconds)
        """
        self.config = initial_config or AdaptiveConfig()
        self.adaptation_interval = adaptation_interval
        self.last_adaptation = time.time()

        # Metrics history
        self.metrics_history: deque[PerformanceMetrics] = deque(maxlen=100)
        self.performance_targets: Dict[str, float] = {
            "cpu_percent": 70.0,
            "memory_percent": 80.0,
            "query_latency_ms": 50.0,
            "cache_hit_rate": 0.8,
        }

        # Adaptation rules
        self.adaptation_rules: List[Callable[[AdaptiveConfig, PerformanceMetrics], AdaptiveConfig]] = []
        self._register_default_rules()

        self._lock = Lock()
        self.running = False

    def _register_default_rules(self) -> None:
        """Register default adaptation rules."""
        # Rule 1: Adjust cache size based on memory
        def adjust_cache_size(config: AdaptiveConfig, metrics: PerformanceMetrics) -> AdaptiveConfig:
            if metrics.memory_percent > 85:
                config.cache_size_mb = max(64.0, config.cache_size_mb * 0.9)
            elif metrics.memory_percent < 60:
                config.cache_size_mb = min(512.0, config.cache_size_mb * 1.1)
            return config

        # Rule 2: Adjust batch size based on latency
        def adjust_batch_size(config: AdaptiveConfig, metrics: PerformanceMetrics) -> AdaptiveConfig:
            if metrics.query_latency_ms > 100:
                config.query_batch_size = min(500, config.query_batch_size * 1.2)
            elif metrics.query_latency_ms < 20:
                config.query_batch_size = max(50, config.query_batch_size * 0.9)
            return config

        # Rule 3: Adjust update interval based on CPU
        def adjust_update_interval(config: AdaptiveConfig, metrics: PerformanceMetrics) -> AdaptiveConfig:
            if metrics.cpu_percent > 80:
                config.update_interval_ms = min(500, config.update_interval_ms * 1.5)
            elif metrics.cpu_percent < 40:
                config.update_interval_ms = max(50, config.update_interval_ms * 0.8)
            return config

        # Rule 4: Adjust thread pool based on active threads
        def adjust_thread_pool(config: AdaptiveConfig, metrics: PerformanceMetrics) -> AdaptiveConfig:
            if metrics.active_threads > config.thread_pool_size * 1.5:
                config.thread_pool_size = min(16, config.thread_pool_size + 2)
            elif metrics.active_threads < config.thread_pool_size * 0.5:
                config.thread_pool_size = max(2, config.thread_pool_size - 1)
            return config

        # Rule 5: Enable/disable prefetching based on cache hit rate
        def adjust_prefetch(config: AdaptiveConfig, metrics: PerformanceMetrics) -> AdaptiveConfig:
            if metrics.cache_hit_rate < 0.5:
                config.prefetch_enabled = True
            elif metrics.cache_hit_rate > 0.9:
                config.prefetch_enabled = False  # Prefetching not needed
            return config

        self.adaptation_rules = [
            adjust_cache_size,
            adjust_batch_size,
            adjust_update_interval,
            adjust_thread_pool,
            adjust_prefetch,
        ]

    def collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics."""
        if not PSUTIL_AVAILABLE:
            return PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_io_read_mb=0.0,
                disk_io_write_mb=0.0,
                network_io_mb=0.0,
                active_threads=0,
            )

        process = psutil.Process()
        cpu_percent = process.cpu_percent(interval=0.1)
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()

        # Disk I/O
        disk_io = process.io_counters()
        disk_io_read_mb = disk_io.read_bytes / (1024 * 1024) if hasattr(disk_io, "read_bytes") else 0.0
        disk_io_write_mb = disk_io.write_bytes / (1024 * 1024) if hasattr(disk_io, "write_bytes") else 0.0

        # Network I/O
        net_io = psutil.net_io_counters()
        network_io_mb = (net_io.bytes_sent + net_io.bytes_recv) / (1024 * 1024)

        # Active threads
        active_threads = process.num_threads()

        return PerformanceMetrics(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_io_read_mb=disk_io_read_mb,
            disk_io_write_mb=disk_io_write_mb,
            network_io_mb=network_io_mb,
            active_threads=active_threads,
        )

    def adapt(self) -> AdaptiveConfig:
        """
        Adapt configuration based on current metrics.

        Returns:
            Updated configuration
        """
        with self._lock:
            metrics = self.collect_metrics()
            self.metrics_history.append(metrics)

            # Calculate average metrics over recent history
            if len(self.metrics_history) >= 5:
                avg_metrics = self._calculate_average_metrics()
            else:
                avg_metrics = metrics

            # Apply adaptation rules
            new_config = AdaptiveConfig(**self.config.__dict__)
            for rule in self.adaptation_rules:
                new_config = rule(new_config, avg_metrics)

            # Apply mode-specific adjustments
            new_config = self._apply_mode_adjustments(new_config, avg_metrics)

            self.config = new_config
            self.last_adaptation = time.time()

            LOGGER.debug(
                "Adapted configuration: cache=%.1fMB, batch=%d, interval=%dms, threads=%d",
                new_config.cache_size_mb,
                new_config.query_batch_size,
                new_config.update_interval_ms,
                new_config.thread_pool_size,
            )

            return new_config

    def _calculate_average_metrics(self) -> PerformanceMetrics:
        """Calculate average metrics over recent history."""
        recent = list(self.metrics_history)[-10:]  # Last 10 samples
        return PerformanceMetrics(
            timestamp=time.time(),
            cpu_percent=sum(m.cpu_percent for m in recent) / len(recent),
            memory_percent=sum(m.memory_percent for m in recent) / len(recent),
            disk_io_read_mb=sum(m.disk_io_read_mb for m in recent) / len(recent),
            disk_io_write_mb=sum(m.disk_io_write_mb for m in recent) / len(recent),
            network_io_mb=sum(m.network_io_mb for m in recent) / len(recent),
            active_threads=int(sum(m.active_threads for m in recent) / len(recent)),
            query_latency_ms=sum(m.query_latency_ms for m in recent) / len(recent),
            cache_hit_rate=sum(m.cache_hit_rate for m in recent) / len(recent),
        )

    def _apply_mode_adjustments(self, config: AdaptiveConfig, metrics: PerformanceMetrics) -> AdaptiveConfig:
        """Apply mode-specific adjustments."""
        if config.mode == PerformanceMode.LOW_POWER:
            config.cache_size_mb *= 0.7
            config.query_batch_size = max(50, int(config.query_batch_size * 0.8))
            config.update_interval_ms = int(config.update_interval_ms * 1.5)
            config.thread_pool_size = max(2, config.thread_pool_size - 1)
        elif config.mode == PerformanceMode.HIGH_PERFORMANCE:
            config.cache_size_mb = min(512.0, config.cache_size_mb * 1.2)
            config.query_batch_size = min(500, int(config.query_batch_size * 1.2))
            config.update_interval_ms = max(50, int(config.update_interval_ms * 0.8))
            config.thread_pool_size = min(16, config.thread_pool_size + 2)
        elif config.mode == PerformanceMode.TURBO:
            config.cache_size_mb = min(1024.0, config.cache_size_mb * 1.5)
            config.query_batch_size = min(1000, int(config.query_batch_size * 1.5))
            config.update_interval_ms = max(25, int(config.update_interval_ms * 0.6))
            config.thread_pool_size = min(32, config.thread_pool_size + 4)
            config.prefetch_enabled = True
            config.compression_enabled = False  # Trade compression for speed

        return config

    def set_mode(self, mode: PerformanceMode) -> None:
        """Set performance mode."""
        with self._lock:
            self.config.mode = mode
            LOGGER.info("Performance mode set to: %s", mode.value)

    def get_config(self) -> AdaptiveConfig:
        """Get current configuration."""
        with self._lock:
            return AdaptiveConfig(**self.config.__dict__)

    def update_metrics(self, query_latency_ms: float = 0.0, cache_hit_rate: float = 0.0) -> None:
        """Update custom metrics."""
        if self.metrics_history:
            self.metrics_history[-1].query_latency_ms = query_latency_ms
            self.metrics_history[-1].cache_hit_rate = cache_hit_rate

    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance report."""
        with self._lock:
            if not self.metrics_history:
                return {"error": "No metrics collected"}

            recent = list(self.metrics_history)[-10:]
            return {
                "current_config": {
                    "cache_size_mb": self.config.cache_size_mb,
                    "batch_size": self.config.query_batch_size,
                    "update_interval_ms": self.config.update_interval_ms,
                    "thread_pool_size": self.config.thread_pool_size,
                    "mode": self.config.mode.value,
                },
                "recent_metrics": {
                    "avg_cpu_percent": sum(m.cpu_percent for m in recent) / len(recent),
                    "avg_memory_percent": sum(m.memory_percent for m in recent) / len(recent),
                    "avg_query_latency_ms": sum(m.query_latency_ms for m in recent) / len(recent),
                    "avg_cache_hit_rate": sum(m.cache_hit_rate for m in recent) / len(recent),
                },
                "targets": self.performance_targets,
            }


__all__ = ["AdaptivePerformanceOptimizer", "AdaptiveConfig", "PerformanceMode", "PerformanceMetrics"]



