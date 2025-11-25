"""
Edge Analytics Module
Handles rolling window analytics for sensor data
"""

import numpy as np


class EdgeAnalytics:
    """Rolling window analytics for sensor metrics"""
    
    def __init__(self, window_size=20):
        self.window_size = window_size
        self.data = {}

    def update(self, metric, value):
        """Update metric with new value"""
        if metric not in self.data:
            self.data[metric] = []
        self.data[metric].append(value)
        if len(self.data[metric]) > self.window_size:
            self.data[metric].pop(0)

    def rolling_average(self, metric):
        """Calculate rolling average for a metric"""
        if metric not in self.data or len(self.data[metric]) == 0:
            return None
        return float(np.mean(self.data[metric]))

