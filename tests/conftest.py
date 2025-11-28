"""
Pytest Configuration and Fixtures

Provides shared fixtures and configuration for all tests.
"""

import pytest
import sys
import logging
from pathlib import Path
from typing import Generator, Dict, Any
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging for tests
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise during tests
    format='%(name)s - %(levelname)s - %(message)s'
)


@pytest.fixture(scope="session")
def project_root_path() -> Path:
    """Return project root path."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="function")
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp(prefix="aituner_test_"))
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="function")
def sample_data() -> Dict[str, Any]:
    """Provide sample telemetry data for testing."""
    return {
        "rpm": 6500.0,
        "throttle": 85.5,
        "boost": 12.3,
        "coolant_temp": 185.0,
        "oil_temp": 210.0,
        "oil_pressure": 45.2,
        "afr": 12.8,
        "egt": 1450.0,
        "speed": 120.5,
        "lat": 40.7128,
        "lon": -74.0060,
        "altitude": 100.0,
        "timestamp": 1234567890.123,
    }


@pytest.fixture(scope="function")
def sample_can_message() -> Dict[str, Any]:
    """Provide sample CAN message for testing."""
    return {
        "arbitration_id": 0x180,
        "data": bytes([0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0]),
        "timestamp": 1234567890.123,
        "channel": "can0",
        "message_type": "standard",
        "dlc": 8,
    }


@pytest.fixture(scope="function")
def mock_gps_fix() -> Dict[str, Any]:
    """Provide mock GPS fix for testing."""
    return {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "altitude": 100.0,
        "speed": 120.5,
        "heading": 45.0,
        "satellites": 12,
        "hdop": 1.2,
        "fix_quality": 2,
        "timestamp": 1234567890.123,
    }
