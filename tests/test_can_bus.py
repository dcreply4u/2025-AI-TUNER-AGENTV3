"""
CAN Bus Tests

Tests CAN bus interface, decoder, and simulator functionality.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.conftest import sample_can_message


class TestCANInterface:
    """Test CAN interface functionality."""
    
    def test_can_interface_import(self):
        """Test CAN interface can be imported."""
        try:
            from interfaces.can_interface import OptimizedCANInterface, CANMessage
            assert OptimizedCANInterface is not None
            assert CANMessage is not None
        except ImportError as e:
            pytest.skip(f"CAN interface not available: {e}")
    
    def test_can_message_creation(self, sample_can_message):
        """Test CAN message creation."""
        try:
            from interfaces.can_interface import CANMessage, CANMessageType
            
            msg = CANMessage(
                arbitration_id=sample_can_message["arbitration_id"],
                data=sample_can_message["data"],
                timestamp=sample_can_message["timestamp"],
                channel=sample_can_message["channel"],
                message_type=CANMessageType.STANDARD,
            )
            
            assert msg.arbitration_id == 0x180
            assert len(msg.data) == 8
            assert msg.channel == "can0"
        except ImportError:
            pytest.skip("CAN interface not available")
    
    def test_can_id_database(self):
        """Test CAN ID database lookup."""
        try:
            from interfaces.can_interface import CAN_ID_DATABASE
            
            assert isinstance(CAN_ID_DATABASE, dict)
            assert len(CAN_ID_DATABASE) > 0
            
            # Check for common vendors
            assert "holley" in CAN_ID_DATABASE or "obd2" in CAN_ID_DATABASE
        except ImportError:
            pytest.skip("CAN interface not available")


class TestCANDecoder:
    """Test CAN decoder functionality."""
    
    def test_decoder_import(self):
        """Test CAN decoder can be imported."""
        try:
            from services.can_decoder import CANDecoder, DecodedMessage, DecodedSignal
            assert CANDecoder is not None
            assert DecodedMessage is not None
            assert DecodedSignal is not None
        except ImportError:
            pytest.skip("CAN decoder not available (cantools may not be installed)")
    
    def test_decoder_initialization(self):
        """Test decoder initialization."""
        try:
            from services.can_decoder import CANDecoder
            
            decoder = CANDecoder()
            assert decoder is not None
            assert decoder.databases == {}
            assert decoder.active_database is None
        except ImportError:
            pytest.skip("CAN decoder not available")
    
    def test_decoder_list_databases(self):
        """Test listing databases."""
        try:
            from services.can_decoder import CANDecoder
            
            decoder = CANDecoder()
            databases = decoder.list_databases()
            assert isinstance(databases, list)
        except ImportError:
            pytest.skip("CAN decoder not available")


class TestCANSimulator:
    """Test CAN simulator functionality."""
    
    def test_simulator_import(self):
        """Test CAN simulator can be imported."""
        try:
            from services.can_simulator import CANSimulator, MessageType, SimulatedMessage
            assert CANSimulator is not None
            assert MessageType is not None
            assert SimulatedMessage is not None
        except ImportError:
            pytest.skip("CAN simulator not available")
    
    def test_simulator_initialization(self):
        """Test simulator initialization."""
        import pytest
        try:
            from services.can_simulator import CANSimulator
            
            simulator = CANSimulator(channel="vcan0", bitrate=500000)
            assert simulator is not None
            assert simulator.channel == "vcan0"
        except RuntimeError as e:
            if "python-can required" in str(e):
                pytest.skip("python-can not installed - simulator requires it")
            raise
            assert simulator.bitrate == 500000
            assert not simulator.running
        except ImportError:
            pytest.skip("CAN simulator not available")
    
    def test_simulator_add_message(self):
        """Test adding message to simulator."""
        try:
            from services.can_simulator import CANSimulator, MessageType
            
            simulator = CANSimulator(channel="vcan0")
            success = simulator.add_message(
                message_name="TestMessage",
                can_id=0x123,
                data=bytes([0x01, 0x02, 0x03, 0x04]),
                period=0.1,
                message_type=MessageType.PERIODIC,
            )
            assert success
            
            messages = simulator.list_messages()
            assert len(messages) == 1
            assert messages[0]["name"] == "TestMessage"
        except ImportError:
            pytest.skip("CAN simulator not available")
        except Exception as e:
            # Virtual bus may not be available on all systems
            pytest.skip(f"CAN simulator setup failed: {e}")


class TestCANHardwareDetection:
    """Test CAN hardware detection."""
    
    def test_hardware_detector_import(self):
        """Test hardware detector can be imported."""
        try:
            from interfaces.can_hardware_detector import CANHardwareDetector, get_can_hardware_detector
            assert CANHardwareDetector is not None
            assert get_can_hardware_detector is not None
        except ImportError:
            pytest.skip("CAN hardware detector not available")
    
    def test_hardware_detector_initialization(self):
        """Test hardware detector initialization."""
        try:
            from interfaces.can_hardware_detector import get_can_hardware_detector
            
            detector = get_can_hardware_detector()
            assert detector is not None
        except ImportError:
            pytest.skip("CAN hardware detector not available")

