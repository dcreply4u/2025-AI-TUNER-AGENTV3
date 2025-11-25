"""
Application Optimizer

Main optimizer that coordinates all optimization systems.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import List, Optional

from core.memory_optimizer import LazyLoader, MemoryOptimizer
from core.performance_manager import PerformanceManager
from core.ui_optimizer import UIOptimizer
from services.disk_cleanup import DiskCleanup

LOGGER = logging.getLogger(__name__)


class AppOptimizer:
    """Main application optimizer coordinating all optimization systems."""

    def __init__(
        self,
        target_memory_mb: float = 200.0,
        max_disk_usage_mb: float = 5000.0,
        log_directories: Optional[List[str]] = None,
    ) -> None:
        """
        Initialize application optimizer.

        Args:
            target_memory_mb: Target memory usage
            max_disk_usage_mb: Maximum disk usage before cleanup
            log_directories: Directories to monitor for disk usage
        """
        # Memory optimization
        self.memory_optimizer = MemoryOptimizer(target_memory_mb=target_memory_mb)
        self.memory_optimizer.start()

        # Performance monitoring
        self.performance_manager = PerformanceManager()
        self.performance_manager.start_monitoring()

        # UI optimization
        self.ui_optimizer: Optional[UIOptimizer] = None

        # Disk cleanup
        self.disk_cleanup = DiskCleanup(max_disk_usage_mb=max_disk_usage_mb)
        self.log_directories = log_directories or ["logs", "cache", "data"]

        # Optimization thread
        self.optimization_thread: Optional[threading.Thread] = None
        self.running = False

    def set_ui_optimizer(self, ui_optimizer: UIOptimizer) -> None:
        """Set UI optimizer instance."""
        self.ui_optimizer = ui_optimizer

    def start(self) -> None:
        """Start all optimization systems."""
        if self.running:
            return

        self.running = True
        self.optimization_thread = threading.Thread(target=self._optimization_loop, daemon=True)
        self.optimization_thread.start()
        LOGGER.info("Application optimizer started")

    def stop(self) -> None:
        """Stop all optimization systems."""
        self.running = False
        self.memory_optimizer.stop()
        self.performance_manager.stop_monitoring()

        if self.optimization_thread:
            self.optimization_thread.join(timeout=5)

        LOGGER.info("Application optimizer stopped")

    def _optimization_loop(self) -> None:
        """Main optimization loop."""
        while self.running:
            try:
                # Check memory usage
                mem_usage = self.memory_optimizer.get_memory_usage()
                if mem_usage["used_mb"] > self.memory_optimizer.target_memory_mb * 1.5:
                    LOGGER.info("Memory usage high (%.2f MB), forcing cleanup", mem_usage["used_mb"])
                    self.memory_optimizer.force_cleanup()

                # Check disk usage periodically
                if time.time() % 3600 < 60:  # Once per hour
                    self.disk_cleanup.cleanup_if_needed(self.log_directories)

                # Check performance metrics
                perf_summary = self.performance_manager.get_performance_summary()
                if perf_summary.get("average_cpu_percent", 0) > 80:
                    LOGGER.warning("High CPU usage detected: %.1f%%", perf_summary["average_cpu_percent"])

                time.sleep(60)  # Check every minute
            except Exception as e:
                LOGGER.error("Error in optimization loop: %s", e)
                time.sleep(60)

    def optimize_now(self) -> dict:
        """
        Force immediate optimization.

        Returns:
            Optimization results
        """
        results = {
            "memory": self.memory_optimizer.force_cleanup(),
            "disk": self.disk_cleanup.cleanup_if_needed(self.log_directories),
            "performance": self.performance_manager.get_performance_summary(),
        }

        # Clear lazy loader cache
        LazyLoader.clear_cache()

        # Clear UI cache if available
        if self.ui_optimizer:
            self.ui_optimizer.clear_cache()

        return results

    def get_status(self) -> dict:
        """Get optimization status."""
        return {
            "memory": self.memory_optimizer.get_memory_usage(),
            "performance": self.performance_manager.get_performance_summary(),
            "disk": {
                directory: self.disk_cleanup.get_disk_usage(directory)
                for directory in self.log_directories
            },
        }


__all__ = ["AppOptimizer"]

