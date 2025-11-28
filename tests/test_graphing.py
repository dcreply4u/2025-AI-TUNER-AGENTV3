"""
Test Graphing and Visualization

Tests graphing functionality, data plotting, and visualization features.
"""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict

from tests.conftest import sample_data


class TestGraphingData:
    """Test graphing data handling."""
    
    def test_data_preparation(self, sample_data):
        """Test preparing data for graphing."""
        # Simulate time series data
        time_points = np.linspace(0, 10, 100)
        rpm_data = 5000 + 1000 * np.sin(time_points)
        
        assert len(time_points) == len(rpm_data)
        assert rpm_data.min() >= 4000
        assert rpm_data.max() <= 6000
    
    def test_multi_sensor_data(self):
        """Test handling multiple sensor data streams."""
        time_points = np.linspace(0, 10, 100)
        
        data = {
            "rpm": 5000 + 1000 * np.sin(time_points),
            "throttle": 50 + 30 * np.cos(time_points),
            "boost": 10 + 5 * np.sin(time_points * 2),
        }
        
        assert len(data) == 3
        assert all(len(v) == 100 for v in data.values())
    
    def test_data_filtering(self):
        """Test filtering data for graphing."""
        # Create noisy data
        clean_data = np.linspace(0, 100, 1000)
        noise = np.random.normal(0, 5, 1000)
        noisy_data = clean_data + noise
        
        # Simple moving average filter
        window = 10
        filtered = np.convolve(noisy_data, np.ones(window)/window, mode='same')
        
        assert len(filtered) == len(noisy_data)
        assert np.std(filtered) < np.std(noisy_data)  # Should be less noisy


class TestGraphOperations:
    """Test graph operations."""
    
    def test_time_range_selection(self):
        """Test selecting time range for display."""
        time_points = np.linspace(0, 100, 1000)
        data = np.random.randn(1000)
        
        # Select range 20-80
        mask = (time_points >= 20) & (time_points <= 80)
        selected_time = time_points[mask]
        selected_data = data[mask]
        
        assert len(selected_time) < len(time_points)
        assert selected_time.min() >= 20
        assert selected_time.max() <= 80
    
    def test_data_downsampling(self):
        """Test downsampling data for display."""
        original_data = np.random.randn(10000)
        
        # Downsample by factor of 10
        downsampled = original_data[::10]
        
        assert len(downsampled) == len(original_data) // 10
        assert len(downsampled) == 1000
    
    def test_zoom_operations(self):
        """Test zoom operations on graph data."""
        time_points = np.linspace(0, 100, 1000)
        data = np.sin(time_points)
        
        # Zoom to 25-75 range
        zoom_start = 25
        zoom_end = 75
        zoom_mask = (time_points >= zoom_start) & (time_points <= zoom_end)
        
        zoomed_time = time_points[zoom_mask]
        zoomed_data = data[zoom_mask]
        
        assert len(zoomed_time) < len(time_points)
        assert zoomed_time.min() >= zoom_start
        assert zoomed_time.max() <= zoom_end


class TestAdvancedGraphing:
    """Test advanced graphing features."""
    
    def test_xy_plot_data(self):
        """Test X-Y plot data preparation."""
        x_data = np.linspace(0, 100, 1000)
        y_data = x_data ** 2  # Parabolic relationship
        
        assert len(x_data) == len(y_data)
        assert y_data[0] == 0
        assert y_data[-1] == 10000
    
    def test_fft_data(self):
        """Test FFT data preparation."""
        # Create signal with known frequency
        sample_rate = 1000
        duration = 1.0
        frequency = 50
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        signal = np.sin(2 * np.pi * frequency * t)
        
        # FFT
        fft_result = np.fft.fft(signal)
        fft_freq = np.fft.fftfreq(len(signal), 1/sample_rate)
        
        # Find peak frequency
        peak_idx = np.argmax(np.abs(fft_result))
        peak_freq = abs(fft_freq[peak_idx])
        
        assert abs(peak_freq - frequency) < 5  # Should be close to 50Hz
    
    def test_histogram_data(self):
        """Test histogram data preparation."""
        data = np.random.normal(100, 15, 1000)
        
        # Create histogram
        counts, bins = np.histogram(data, bins=20)
        
        assert len(counts) == 20
        assert len(bins) == 21
        assert sum(counts) == len(data)
    
    def test_math_channel_calculation(self):
        """Test math channel calculations."""
        rpm = np.array([5000, 6000, 7000])
        throttle = np.array([50, 60, 70])
        
        # Calculate power estimate: rpm * throttle / 1000
        power = (rpm * throttle) / 1000
        
        assert len(power) == len(rpm)
        assert power[0] == 250.0
        assert power[1] == 360.0
        assert power[2] == 490.0


class TestGraphExport:
    """Test graph export functionality."""
    
    def test_export_graph_data(self, temp_dir):
        """Test exporting graph data."""
        time_points = np.linspace(0, 10, 100)
        data = {
            "time": time_points,
            "rpm": 5000 + 1000 * np.sin(time_points),
        }
        
        # Export to CSV
        output_file = temp_dir / "graph_data.csv"
        import csv
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['time', 'rpm'])
            for t, r in zip(data['time'], data['rpm']):
                writer.writerow([t, r])
        
        assert output_file.exists()
        assert output_file.stat().st_size > 0
    
    def test_export_multiple_series(self, temp_dir):
        """Test exporting multiple data series."""
        time_points = np.linspace(0, 10, 100)
        data = {
            "time": time_points,
            "rpm": 5000 + 1000 * np.sin(time_points),
            "throttle": 50 + 30 * np.cos(time_points),
            "boost": 10 + 5 * np.sin(time_points * 2),
        }
        
        output_file = temp_dir / "multi_series.csv"
        import csv
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['time', 'rpm', 'throttle', 'boost'])
            for i in range(len(time_points)):
                writer.writerow([
                    data['time'][i],
                    data['rpm'][i],
                    data['throttle'][i],
                    data['boost'][i],
                ])
        
        assert output_file.exists()
        
        # Verify can read back
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 100
            assert 'rpm' in rows[0]

