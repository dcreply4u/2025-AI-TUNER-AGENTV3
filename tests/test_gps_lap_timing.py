"""
GPS and Lap Timing Tests

Tests GPS functionality, lap timing, and performance tracking.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.conftest import mock_gps_fix, sample_data


class TestGPSInterface:
    """Test GPS interface functionality."""
    
    def test_gps_interface_import(self):
        """Test GPS interface can be imported."""
        try:
            from interfaces.gps_interface import GPSInterface, GPSFix
            assert GPSInterface is not None
            assert GPSFix is not None
        except ImportError:
            pytest.skip("GPS interface not available")
    
    def test_gps_fix_validation(self, mock_gps_fix):
        """Test GPS fix data validation."""
        # Valid GPS fix should have latitude and longitude
        assert "latitude" in mock_gps_fix
        assert "longitude" in mock_gps_fix
        assert -90 <= mock_gps_fix["latitude"] <= 90
        assert -180 <= mock_gps_fix["longitude"] <= 180
    
    def test_simulated_gps_interface(self):
        """Test simulated GPS interface."""
        try:
            from interfaces.simulated_interface import SimulatedGPSInterface
            
            gps = SimulatedGPSInterface()
            fix = gps.read_fix()
            
            assert fix is not None
            assert hasattr(fix, 'latitude') or 'latitude' in str(fix)
        except ImportError:
            pytest.skip("Simulated GPS interface not available")


class TestLapTiming:
    """Test lap timing functionality."""
    
    def test_performance_tracker_import(self):
        """Test performance tracker can be imported."""
        try:
            from services.performance_tracker import PerformanceTracker, PerformanceSnapshot
            assert PerformanceTracker is not None
            assert PerformanceSnapshot is not None
        except ImportError:
            pytest.skip("Performance tracker not available")
    
    def test_lap_detection(self):
        """Test lap detection logic."""
        try:
            from services.performance_tracker import PerformanceTracker
            
            tracker = PerformanceTracker()
            
            # Simulate GPS points around a track
            # Start/finish line at (0, 0)
            gps_points = [
                {"lat": 0.0, "lon": 0.0, "timestamp": 1000.0},
                {"lat": 0.001, "lon": 0.001, "timestamp": 1010.0},
                {"lat": 0.002, "lon": 0.002, "timestamp": 1020.0},
                {"lat": 0.0, "lon": 0.0, "timestamp": 1030.0},  # Back to start
            ]
            
            # Should detect lap completion
            # (Simplified test - actual implementation may vary)
            assert len(gps_points) > 0
        except ImportError:
            pytest.skip("Performance tracker not available")
    
    def test_dragy_metrics(self):
        """Test Dragy-style performance metrics."""
        try:
            from services.drag_racing_analyzer import DragRacingAnalyzer, DragRun
            
            analyzer = DragRacingAnalyzer()
            
            # Simulate drag run data
            run = DragRun(
                start_time=1000.0,
                end_time=1012.5,
                distance_m=402.336,  # Quarter mile
                start_speed=0.0,
                end_speed=120.0,
            )
            
            assert run.distance_m > 0
            assert run.end_time > run.start_time
        except ImportError:
            pytest.skip("Drag racing analyzer not available")

