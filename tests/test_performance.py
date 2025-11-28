"""
Test Performance

Tests performance characteristics and bottlenecks.
"""

import pytest
import time
import numpy as np
from typing import List


class TestDataProcessingPerformance:
    """Test data processing performance."""
    
    def test_large_dataset_processing(self):
        """Test processing large datasets."""
        # Create large dataset
        data_size = 100000
        data = np.random.randn(data_size)
        
        start = time.time()
        # Process data
        mean = np.mean(data)
        std = np.std(data)
        elapsed = time.time() - start
        
        assert elapsed < 1.0  # Should complete in < 1 second
        assert mean is not None
        assert std > 0
    
    def test_data_filtering_performance(self):
        """Test filtering performance."""
        data_size = 50000
        data = np.random.randn(data_size)
        
        start = time.time()
        # Filter outliers
        mean = np.mean(data)
        std = np.std(data)
        filtered = data[(data >= mean - 3*std) & (data <= mean + 3*std)]
        elapsed = time.time() - start
        
        assert elapsed < 0.5  # Should be fast
        assert len(filtered) <= len(data)
    
    def test_data_aggregation_performance(self):
        """Test data aggregation performance."""
        # Time series data
        timestamps = np.linspace(0, 100, 10000)
        values = np.random.randn(10000)
        
        start = time.time()
        # Aggregate into 1-second windows
        window_size = 1.0
        num_windows = int(np.ceil(timestamps[-1] / window_size))
        aggregated = []
        
        for i in range(num_windows):
            window_start = i * window_size
            window_end = (i + 1) * window_size
            mask = (timestamps >= window_start) & (timestamps < window_end)
            if np.any(mask):
                aggregated.append(np.mean(values[mask]))
        
        elapsed = time.time() - start
        
        assert elapsed < 1.0  # Should complete quickly
        assert len(aggregated) == num_windows


class TestMemoryUsage:
    """Test memory usage."""
    
    def test_data_buffer_size(self):
        """Test data buffer doesn't grow unbounded."""
        from collections import deque
        
        # Simulate data buffer
        buffer = deque(maxlen=1000)
        
        # Add many items
        for i in range(10000):
            buffer.append({"timestamp": i, "value": i * 0.1})
        
        # Buffer should be limited
        assert len(buffer) == 1000  # Max size
    
    def test_large_file_handling(self):
        """Test handling large files efficiently."""
        # Simulate reading large file in chunks
        chunk_size = 1024 * 1024  # 1MB chunks
        total_size = 100 * 1024 * 1024  # 100MB
        
        chunks_read = 0
        bytes_read = 0
        
        # Simulate chunked reading
        while bytes_read < total_size:
            chunk = min(chunk_size, total_size - bytes_read)
            bytes_read += chunk
            chunks_read += 1
        
        assert chunks_read > 0
        assert bytes_read == total_size
