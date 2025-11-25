"""
Performance and stress tests.
"""

import pytest
import time
import threading

from services.data_logger import DataLogger
from core.data_validator import DataValidator
from core.performance_manager import PerformanceManager


class TestPerformance:
    """Performance test suite."""

    def test_high_throughput_logging(self, temp_dir):
        """Test logging performance under high throughput."""
        logger = DataLogger(log_dir=str(temp_dir / "logs"))

        start_time = time.time()
        num_samples = 1000

        for i in range(num_samples):
            data = {
                "Engine_RPM": 3000.0 + i,
                "Coolant_Temp": 90.0,
                "timestamp": time.time(),
            }
            logger.log(data)

        elapsed = time.time() - start_time
        throughput = num_samples / elapsed

        # Should handle at least 100 samples per second
        assert throughput > 100, f"Throughput too low: {throughput:.2f} samples/sec"

    def test_concurrent_validation(self, data_validator):
        """Test concurrent data validation."""
        import concurrent.futures

        def validate_data(data):
            return data_validator.validate(data)

        test_data = [
            {"Engine_RPM": 3000.0 + i, "Coolant_Temp": 90.0} for i in range(100)
        ]

        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(validate_data, test_data))

        elapsed = time.time() - start_time

        # All should complete
        assert len(results) == 100
        # Should be reasonably fast
        assert elapsed < 5.0

    def test_memory_usage(self, temp_dir):
        """Test memory usage during extended logging."""
        logger = DataLogger(log_dir=str(temp_dir / "logs"))
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB

        # Log many samples
        for i in range(10000):
            data = {
                "Engine_RPM": 3000.0,
                "Coolant_Temp": 90.0,
                "iteration": i,
            }
            logger.log(data)

        final_memory = process.memory_info().rss / (1024 * 1024)  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (< 50 MB for 10k samples)
        assert memory_increase < 50, f"Memory increase too high: {memory_increase:.2f} MB"

    def test_performance_monitoring(self):
        """Test performance monitoring overhead."""
        manager = PerformanceManager(monitoring_interval=1.0)

        start_time = time.time()
        manager.start_monitoring()

        # Let it run for a bit
        time.sleep(3)

        metrics = manager.get_current_metrics()
        manager.stop_monitoring()

        elapsed = time.time() - start_time

        # Should have collected some metrics
        assert len(manager.resource_history) > 0
        # Monitoring overhead should be minimal
        assert elapsed < 5.0

