"""
Resource Optimizer

Main coordinator for all resource optimizations.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Optional

from PySide6.QtCore import QObject, QTimer, Signal

from .disk_manager import DiskManager
from .memory_manager import MemoryManager
from .performance_manager import PerformanceManager
from .ui_optimizer import UIOptimizer

LOGGER = logging.getLogger(__name__)


class ResourceOptimizer(QObject):
    """Main resource optimization coordinator."""

    # Signals
    memory_warning = Signal(float)  # Emits memory percentage
    disk_warning = Signal(float)  # Emits disk percentage
    optimization_complete = Signal(dict)  # Emits optimization results

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """Initialize resource optimizer."""
        super().__init__(parent)

        # Initialize managers
        self.memory_manager = MemoryManager(max_memory_mb=512.0, cleanup_threshold=0.8)
        self.disk_manager = DiskManager(max_disk_usage_mb=10240.0, cleanup_threshold=0.9)
        self.performance_manager = PerformanceManager(monitoring_interval=10.0)
        self.ui_optimizer = UIOptimizer()

        # Optimization timers
        self.memory_check_timer = QTimer(self)
        self.memory_check_timer.timeout.connect(self._check_memory)
        self.memory_check_timer.start(30000)  # Check every 30 seconds

        self.disk_check_timer = QTimer(self)
        self.disk_check_timer.timeout.connect(self._check_disk)
        self.disk_check_timer.start(300000)  # Check every 5 minutes

        self.cleanup_timer = QTimer(self)
        self.cleanup_timer.timeout.connect(self._periodic_cleanup)
        self.cleanup_timer.start(3600000)  # Cleanup every hour

        # Start performance monitoring
        self.performance_manager.start_monitoring()

        # Register cleanup callbacks
        self.memory_manager.register_cleanup(self._memory_cleanup)

        LOGGER.info("Resource optimizer initialized")

    def _check_memory(self) -> None:
        """Check memory usage and trigger cleanup if needed."""
        usage = self.memory_manager.get_memory_usage()

        if self.memory_manager.should_cleanup():
            self.memory_warning.emit(usage["percent"])
            result = self.memory_manager.cleanup(aggressive=False)
            LOGGER.info("Memory cleanup: freed %.2f MB", result["freed_mb"])

    def _check_disk(self) -> None:
        """Check disk usage and trigger cleanup if needed."""
        usage = self.disk_manager.get_disk_usage()

        if self.disk_manager.should_cleanup():
            self.disk_warning.emit(usage["percent"])
            self._disk_cleanup()

    def _memory_cleanup(self) -> None:
        """Memory cleanup callback."""
        # Unload unused UI widgets
        self.ui_optimizer.unload_unused_widgets()

    def _disk_cleanup(self) -> None:
        """Perform disk cleanup."""
        results = {
            "old_files": self.disk_manager.cleanup_old_files("logs"),
            "compressed_logs": self.disk_manager.compress_old_logs("logs", days_old=7),
            "temp_files": self.disk_manager.cleanup_temp_files(["cache", "tmp"]),
        }

        total_freed = sum(r.get("freed_mb", 0) for r in results.values())
        LOGGER.info("Disk cleanup: freed %.2f MB", total_freed)

        self.optimization_complete.emit(results)

    def _periodic_cleanup(self) -> None:
        """Periodic comprehensive cleanup."""
        LOGGER.info("Starting periodic cleanup")

        # Memory cleanup
        memory_result = self.memory_manager.cleanup(aggressive=True)

        # Disk cleanup
        disk_results = {
            "old_files": self.disk_manager.cleanup_old_files("logs"),
            "compressed": self.disk_manager.compress_old_logs("logs"),
        }

        # Database optimization
        db_result = self.disk_manager.optimize_database("data/local.db")

        results = {
            "memory": memory_result,
            "disk": disk_results,
            "database": db_result,
        }

        self.optimization_complete.emit(results)
        LOGGER.info("Periodic cleanup complete")

    def optimize_ui_widget(self, widget) -> None:
        """Optimize a UI widget."""
        self.ui_optimizer.optimize_widget(widget)

    def register_lazy_widget(self, name: str, widget_class, *args, **kwargs) -> None:
        """Register a widget for lazy loading."""
        self.ui_optimizer.register_lazy_widget(name, widget_class, *args, **kwargs)

    def get_memory_stats(self) -> dict:
        """Get memory statistics."""
        return self.memory_manager.get_memory_usage()

    def get_disk_stats(self) -> dict:
        """Get disk statistics."""
        return self.disk_manager.get_disk_usage()

    def get_performance_stats(self) -> dict:
        """Get performance statistics."""
        return self.performance_manager.get_performance_summary()

    def force_cleanup(self) -> dict:
        """Force immediate cleanup."""
        memory_result = self.memory_manager.cleanup(aggressive=True)
        disk_results = self._disk_cleanup()

        return {
            "memory": memory_result,
            "disk": disk_results,
        }

    def shutdown(self) -> None:
        """Shutdown optimizer."""
        self.memory_check_timer.stop()
        self.disk_check_timer.stop()
        self.cleanup_timer.stop()
        self.performance_manager.stop_monitoring()
        self.performance_manager.shutdown()


__all__ = ["ResourceOptimizer"]

