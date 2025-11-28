"""
Test Telemetry Processing

Tests telemetry data processing, filtering, and analysis.
"""

import pytest
import numpy as np
from typing import List, Dict

from tests.conftest import sample_data


class TestTelemetryFiltering:
    """Test telemetry data filtering."""
    
    def test_outlier_detection(self):
        """Test detecting outliers in telemetry data."""
        # Normal data with outliers
        rpm_data = np.array([5000, 5100, 5200, 5300, 10000, 5400, 5500])  # 10000 is outlier
        
        # Calculate mean and std
        mean = np.mean(rpm_data)
        std = np.std(rpm_data)
        
        # Detect outliers (beyond 3 standard deviations)
        outliers = np.abs(rpm_data - mean) > 3 * std
        
        assert np.any(outliers)
        assert outliers[4] == True  # Index 4 is the outlier
    
    def test_moving_average_filter(self):
        """Test moving average filtering."""
        noisy_data = np.array([100, 102, 98, 101, 99, 103, 97, 100, 102, 98])
        
        # Simple moving average
        window = 3
        filtered = np.convolve(noisy_data, np.ones(window)/window, mode='same')
        
        assert len(filtered) == len(noisy_data)
        assert np.std(filtered) < np.std(noisy_data)  # Should be smoother
    
    def test_median_filter(self):
        """Test median filtering."""
        data_with_spikes = np.array([100, 100, 100, 500, 100, 100, 100])  # Spike at index 3
        
        # Median filter
        window = 3
        filtered = []
        for i in range(len(data_with_spikes)):
            start = max(0, i - window // 2)
            end = min(len(data_with_spikes), i + window // 2 + 1)
            filtered.append(np.median(data_with_spikes[start:end]))
        
        filtered = np.array(filtered)
        assert filtered[3] < 500  # Spike should be reduced


class TestTelemetryAnalysis:
    """Test telemetry data analysis."""
    
    def test_correlation_analysis(self):
        """Test correlation between sensors."""
        # Create correlated data
        time_points = np.linspace(0, 10, 100)
        throttle = 50 + 30 * np.sin(time_points)
        rpm = 5000 + 2000 * np.sin(time_points)  # Correlated with throttle
        
        # Calculate correlation
        correlation = np.corrcoef(throttle, rpm)[0, 1]
        
        assert correlation > 0.8  # Should be highly correlated
    
    def test_statistical_analysis(self, sample_data):
        """Test statistical analysis of telemetry."""
        # Multiple data points
        rpm_values = [5000, 5500, 6000, 6500, 7000]
        
        mean_rpm = np.mean(rpm_values)
        std_rpm = np.std(rpm_values)
        min_rpm = np.min(rpm_values)
        max_rpm = np.max(rpm_values)
        
        assert mean_rpm == 6000.0
        assert min_rpm == 5000
        assert max_rpm == 7000
        assert std_rpm > 0
    
    def test_trend_analysis(self):
        """Test trend analysis."""
        # Data with trend
        time_points = np.linspace(0, 10, 100)
        temperature = 180 + 2 * time_points  # Increasing trend
        
        # Calculate trend (slope)
        slope = np.polyfit(time_points, temperature, 1)[0]
        
        assert slope > 0  # Positive trend (increasing)
        assert abs(slope - 2.0) < 0.1  # Should be close to 2


class TestTelemetryAggregation:
    """Test telemetry data aggregation."""
    
    def test_time_based_aggregation(self):
        """Test aggregating data over time windows."""
        # Time series data
        timestamps = np.linspace(0, 100, 1000)  # 100 seconds, 1000 points
        rpm_data = 5000 + 1000 * np.sin(timestamps / 10)
        
        # Aggregate into 10-second windows
        window_size = 10
        num_windows = int(np.ceil(timestamps[-1] / window_size))
        
        aggregated = []
        for i in range(num_windows):
            window_start = i * window_size
            window_end = (i + 1) * window_size
            mask = (timestamps >= window_start) & (timestamps < window_end)
            if np.any(mask):
                aggregated.append(np.mean(rpm_data[mask]))
        
        assert len(aggregated) == num_windows
        assert all(4000 <= avg <= 6000 for avg in aggregated)
    
    def test_sensor_aggregation(self, sample_data):
        """Test aggregating multiple sensors."""
        data_points = [
            {"rpm": 5000, "throttle": 50, "boost": 10},
            {"rpm": 5500, "throttle": 60, "boost": 12},
            {"rpm": 6000, "throttle": 70, "boost": 14},
        ]
        
        # Aggregate
        avg_rpm = np.mean([d['rpm'] for d in data_points])
        avg_throttle = np.mean([d['throttle'] for d in data_points])
        avg_boost = np.mean([d['boost'] for d in data_points])
        
        assert avg_rpm == 5500.0
        assert avg_throttle == 60.0
        assert avg_boost == 12.0

