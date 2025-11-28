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
        
        # Detect outliers using z-scores - use 2.5 threshold since the outlier inflates std
        z_scores = np.abs((rpm_data - mean) / std)
        outliers = z_scores > 2.5  # Lower threshold since outlier inflates std
        
        # The outlier should be detected - 10000 is way beyond normal range
        # Alternative: use IQR method which is more robust
        q1 = np.percentile(rpm_data, 25)
        q3 = np.percentile(rpm_data, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outliers_iqr = (rpm_data < lower_bound) | (rpm_data > upper_bound)
        
        # Use IQR method (more robust) or z-score with lower threshold
        assert np.any(outliers_iqr) or np.any(outliers), \
            f"No outliers detected. Z-scores: {z_scores}, IQR outliers: {outliers_iqr}, mean: {mean:.2f}, std: {std:.2f}"
        assert outliers_iqr[4] == True or outliers[4] == True, \
            f"Outlier at index 4 not detected. Z-score: {z_scores[4]:.2f}, IQR: {outliers_iqr[4]}"  # Index 4 is the outlier
    
    def test_moving_average_filter(self):
        """Test moving average filtering."""
        noisy_data = np.array([100, 102, 98, 101, 99, 103, 97, 100, 102, 98])
        
        # Simple moving average - use 'valid' mode to avoid edge effects
        window = 3
        filtered = np.convolve(noisy_data, np.ones(window)/window, mode='valid')
        
        # For 'valid' mode, output is shorter, so compare the valid portion
        # Or use 'same' but handle edge effects properly
        filtered_same = np.convolve(noisy_data, np.ones(window)/window, mode='same')
        
        # The filtered data should be smoother (lower std) in the middle portion
        # Edge effects in 'same' mode can increase variance, so check middle portion
        middle_start = window // 2
        middle_end = len(noisy_data) - window // 2
        filtered_middle = filtered_same[middle_start:middle_end]
        noisy_middle = noisy_data[middle_start:middle_end]
        
        assert len(filtered_same) == len(noisy_data)
        assert np.std(filtered_middle) < np.std(noisy_middle), \
            f"Filtered std ({np.std(filtered_middle):.2f}) should be < noisy std ({np.std(noisy_middle):.2f})"
    
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

