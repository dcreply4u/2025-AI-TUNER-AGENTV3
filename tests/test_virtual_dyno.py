"""
Virtual Dyno Tests

Tests virtual dyno calculations and horsepower estimation.
"""

import pytest
import sys
import numpy as np
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.conftest import sample_data


class TestVirtualDyno:
    """Test virtual dyno functionality."""
    
    def test_virtual_dyno_import(self):
        """Test virtual dyno can be imported."""
        try:
            from services.virtual_dyno import VirtualDyno, DynoReading, VehicleSpecs
            assert VirtualDyno is not None
            assert DynoReading is not None
            assert VehicleSpecs is not None
        except ImportError:
            pytest.skip("Virtual dyno not available")
    
    def test_dyno_calculation(self):
        """Test basic dyno calculation."""
        try:
            from services.virtual_dyno import VirtualDyno, VehicleSpecs
            
            specs = VehicleSpecs(
                weight_kg=1500.0,
                drag_coefficient=0.35,
                frontal_area_m2=2.0,
            )
            
            dyno = VirtualDyno(specs)
            
            # Simulate acceleration data
            time_points = np.linspace(0, 10, 100)
            speeds = 10 * time_points  # Linear acceleration
            
            # Calculate power
            power = dyno.calculate_power(speeds, time_points)
            
            assert len(power) == len(speeds)
            assert all(p >= 0 for p in power)  # Power should be non-negative
        except ImportError:
            pytest.skip("Virtual dyno not available")
    
    def test_dyno_reading_creation(self):
        """Test dyno reading creation."""
        try:
            from services.virtual_dyno import DynoReading
            
            reading = DynoReading(
                rpm=6000.0,
                horsepower=400.0,
                torque=350.0,
                timestamp=1234567890.0,
            )
            
            assert reading.rpm == 6000.0
            assert reading.horsepower == 400.0
            assert reading.torque == 350.0
        except ImportError:
            pytest.skip("Virtual dyno not available")


class TestDynoAnalyzer:
    """Test dyno analyzer functionality."""
    
    def test_dyno_analyzer_import(self):
        """Test dyno analyzer can be imported."""
        try:
            from services.dyno_analyzer import DynoAnalyzer
            assert DynoAnalyzer is not None
        except ImportError:
            pytest.skip("Dyno analyzer not available")
    
    def test_power_band_analysis(self):
        """Test power band analysis."""
        try:
            from services.dyno_analyzer import DynoAnalyzer
            
            analyzer = DynoAnalyzer()
            
            # Simulate dyno curve
            rpm_data = np.linspace(2000, 8000, 100)
            power_data = 300 + 100 * np.sin((rpm_data - 2000) / 6000 * np.pi)
            
            analysis = analyzer.analyze_power_band(rpm_data, power_data)
            
            assert analysis is not None
            assert "peak_power" in analysis or "max_power" in str(analysis)
        except ImportError:
            pytest.skip("Dyno analyzer not available")

