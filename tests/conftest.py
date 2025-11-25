"""
Pytest configuration and fixtures.

Provides common test fixtures and setup for all tests.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock

from core.config_manager import ConfigManager
from core.data_validator import DataValidator
from core.error_handler import ErrorHandler
from services.data_logger import DataLogger
from services.performance_tracker import PerformanceTracker


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def config_manager(temp_dir):
    """Create a ConfigManager with temporary config file."""
    config_file = temp_dir / "test_config.json"
    return ConfigManager(config_file=str(config_file))


@pytest.fixture
def data_validator():
    """Create a DataValidator instance."""
    return DataValidator()


@pytest.fixture
def error_handler():
    """Create an ErrorHandler instance."""
    return ErrorHandler()


@pytest.fixture
def data_logger(temp_dir):
    """Create a DataLogger with temporary log directory."""
    log_dir = temp_dir / "logs"
    return DataLogger(log_dir=str(log_dir))


@pytest.fixture
def performance_tracker():
    """Create a PerformanceTracker instance."""
    return PerformanceTracker()


@pytest.fixture
def mock_can_bus():
    """Create a mock CAN bus."""
    mock = MagicMock()
    mock.recv.return_value = None
    return mock


@pytest.fixture
def mock_gps_interface():
    """Create a mock GPS interface."""
    mock = MagicMock()
    mock.read_fix.return_value = None
    return mock


@pytest.fixture
def mock_obd_interface():
    """Create a mock OBD interface."""
    mock = MagicMock()
    mock.read_data.return_value = {}
    mock.is_connected.return_value = True
    return mock


@pytest.fixture
def sample_telemetry_data():
    """Sample telemetry data for testing."""
    return {
        "Engine_RPM": 3000.0,
        "Coolant_Temp": 90.0,
        "Oil_Pressure": 45.0,
        "Boost_Pressure": 10.0,
        "Vehicle_Speed": 60.0,
        "Throttle_Position": 50.0,
        "Lambda": 1.0,
    }


@pytest.fixture
def sample_invalid_telemetry_data():
    """Sample invalid telemetry data for testing."""
    return {
        "Engine_RPM": 50000.0,  # Invalid: too high
        "Coolant_Temp": 200.0,  # Invalid: too high
        "Oil_Pressure": -10.0,  # Invalid: negative
        "Vehicle_Speed": 500.0,  # Invalid: too high
    }

