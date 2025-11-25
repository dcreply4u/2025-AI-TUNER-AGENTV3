"""
Performance Monitor

Monitors system performance metrics for optimization and debugging.
Tracks CPU, memory, disk I/O, and application-specific metrics.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, Optional

try:
    import psutil
except ImportError:
    psutil = None

LOGGER = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot."""

    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_read_mb: float = 0.0
    disk_write_mb: float = 0.0
    network_sent_mb: float = 0.0
    network_recv_mb: float = 0.0
    process_count: int = 0
    temperature: Optional[float] = None


@dataclass
class ApplicationMetrics:
    """Application-specific performance metrics."""

    timestamp: float
    can_messages_per_sec: float = 0.0
    gps_fixes_per_sec: float = 0.0
    frames_per_sec: Dict[str, float] = field(default_factory=dict)
    telemetry_updates_per_sec: float = 0.0
    ai_inference_time_ms: float = 0.0
    ui_update_time_ms: float = 0.0


class PerformanceMonitor:
    """Monitors system and application performance."""

    def __init__(self, history_size: int = 300) -> None:
        """
        Initialize performance monitor.

        Args:
            history_size: Number of historical samples to keep
        """
        if psutil is None:
            LOGGER.warning("psutil not available, performance monitoring will be limited")

        self.history_size = history_size
        self.metrics_history: Deque[PerformanceMetrics] = deque(maxlen=history_size)
        self.app_metrics_history: Deque[ApplicationMetrics] = deque(maxlen=history_size)

        # Counters for rate calculations
        self._can_message_count = 0
        self._gps_fix_count = 0
        self._frame_counts: Dict[str, int] = {}
        self._telemetry_update_count = 0
        self._last_reset_time = time.time()
        self._reset_interval = 1.0  # Reset counters every second

        # Timing measurements
        self._ai_inference_times: Deque[float] = deque(maxlen=100)
        self._ui_update_times: Deque[float] = deque(maxlen=100)

        # Previous I/O stats for delta calculation
        self._prev_disk_io: Optional[Dict] = None
        self._prev_net_io: Optional[Dict] = None

    def collect_system_metrics(self) -> PerformanceMetrics:
        """Collect current system performance metrics."""
        if psutil is None:
            return PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_available_mb=0.0,
            )

        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Memory
            mem = psutil.virtual_memory()
            memory_percent = mem.percent
            memory_used_mb = mem.used / (1024**2)
            memory_available_mb = mem.available / (1024**2)

            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_read_mb = 0.0
            disk_write_mb = 0.0
            if disk_io:
                if self._prev_disk_io:
                    disk_read_mb = (disk_io.read_bytes - self._prev_disk_io["read_bytes"]) / (1024**2)
                    disk_write_mb = (disk_io.write_bytes - self._prev_disk_io["write_bytes"]) / (1024**2)
                self._prev_disk_io = {
                    "read_bytes": disk_io.read_bytes,
                    "write_bytes": disk_io.write_bytes,
                }

            # Network I/O
            net_io = psutil.net_io_counters()
            network_sent_mb = 0.0
            network_recv_mb = 0.0
            if net_io:
                if self._prev_net_io:
                    network_sent_mb = (net_io.bytes_sent - self._prev_net_io["bytes_sent"]) / (1024**2)
                    network_recv_mb = (net_io.bytes_recv - self._prev_net_io["bytes_recv"]) / (1024**2)
                self._prev_net_io = {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                }

            # Process count
            process_count = len(psutil.pids())

            # Temperature (if available)
            temperature = None
            try:
                import subprocess

                result = subprocess.run(
                    ["vcgencmd", "measure_temp"],
                    capture_output=True,
                    text=True,
                    timeout=1,
                )
                if result.returncode == 0:
                    temp_str = result.stdout.strip()
                    # Extract temperature value
                    temp_value = temp_str.split("=")[1].split("'")[0]
                    temperature = float(temp_value)
            except Exception:
                pass

            metrics = PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_read_mb=disk_read_mb,
                disk_write_mb=disk_write_mb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                process_count=process_count,
                temperature=temperature,
            )

            self.metrics_history.append(metrics)
            return metrics

        except Exception as e:
            LOGGER.error("Error collecting system metrics: %s", e)
            return PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_available_mb=0.0,
            )

    def record_can_message(self) -> None:
        """Record a CAN message."""
        self._can_message_count += 1

    def record_gps_fix(self) -> None:
        """Record a GPS fix."""
        self._gps_fix_count += 1

    def record_frame(self, camera_name: str) -> None:
        """Record a video frame."""
        if camera_name not in self._frame_counts:
            self._frame_counts[camera_name] = 0
        self._frame_counts[camera_name] += 1

    def record_telemetry_update(self) -> None:
        """Record a telemetry update."""
        self._telemetry_update_count += 1

    def record_ai_inference(self, time_ms: float) -> None:
        """Record AI inference time."""
        self._ai_inference_times.append(time_ms)

    def record_ui_update(self, time_ms: float) -> None:
        """Record UI update time."""
        self._ui_update_times.append(time_ms)

    def collect_application_metrics(self) -> ApplicationMetrics:
        """Collect application-specific metrics."""
        now = time.time()
        elapsed = now - self._last_reset_time

        if elapsed >= self._reset_interval:
            # Calculate rates
            can_rate = self._can_message_count / elapsed if elapsed > 0 else 0.0
            gps_rate = self._gps_fix_count / elapsed if elapsed > 0 else 0.0
            telemetry_rate = self._telemetry_update_count / elapsed if elapsed > 0 else 0.0

            frame_rates = {}
            for camera_name, count in self._frame_counts.items():
                frame_rates[camera_name] = count / elapsed if elapsed > 0 else 0.0

            # Calculate average inference time
            ai_time = 0.0
            if self._ai_inference_times:
                ai_time = sum(self._ai_inference_times) / len(self._ai_inference_times)

            # Calculate average UI update time
            ui_time = 0.0
            if self._ui_update_times:
                ui_time = sum(self._ui_update_times) / len(self._ui_update_times)

            metrics = ApplicationMetrics(
                timestamp=now,
                can_messages_per_sec=can_rate,
                gps_fixes_per_sec=gps_rate,
                frames_per_sec=frame_rates,
                telemetry_updates_per_sec=telemetry_rate,
                ai_inference_time_ms=ai_time,
                ui_update_time_ms=ui_time,
            )

            self.app_metrics_history.append(metrics)

            # Reset counters
            self._can_message_count = 0
            self._gps_fix_count = 0
            self._frame_counts.clear()
            self._telemetry_update_count = 0
            self._last_reset_time = now

            return metrics
        else:
            # Return last metrics if not enough time has passed
            if self.app_metrics_history:
                return self.app_metrics_history[-1]
            return ApplicationMetrics(timestamp=now)

    def get_average_cpu(self, window: int = 60) -> float:
        """Get average CPU usage over last N samples."""
        if not self.metrics_history:
            return 0.0
        samples = list(self.metrics_history)[-window:]
        return sum(m.cpu_percent for m in samples) / len(samples)

    def get_average_memory(self, window: int = 60) -> float:
        """Get average memory usage over last N samples."""
        if not self.metrics_history:
            return 0.0
        samples = list(self.metrics_history)[-window:]
        return sum(m.memory_percent for m in samples) / len(samples)

    def get_latest_metrics(self) -> Optional[PerformanceMetrics]:
        """Get latest system metrics."""
        return self.metrics_history[-1] if self.metrics_history else None

    def get_latest_app_metrics(self) -> Optional[ApplicationMetrics]:
        """Get latest application metrics."""
        return self.app_metrics_history[-1] if self.app_metrics_history else None

    def is_healthy(self) -> bool:
        """Check if system performance is healthy."""
        latest = self.get_latest_metrics()
        if not latest:
            return True  # No data yet, assume healthy

        # Check thresholds
        if latest.cpu_percent > 90:
            return False
        if latest.memory_percent > 90:
            return False
        if latest.temperature and latest.temperature > 80:
            return False

        return True


__all__ = ["PerformanceMonitor", "PerformanceMetrics", "ApplicationMetrics"]

