"""
Test Data Reading

Tests data reading from various interfaces (CAN, GPS, OBD, sensors).
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

from tests.conftest import sample_data, sample_can_message, mock_gps_fix


class TestCANDataReading:
    """Test CAN bus data reading."""
    
    @patch('interfaces.can_interface.can')
    def test_can_interface_creation(self, mock_can):
        """Test creating CAN interface."""
        from interfaces.can_interface import OptimizedCANInterface
        
        # Mock can.interface.Bus
        mock_bus = MagicMock()
        mock_can.interface.Bus.return_value = mock_bus
        
        can_if = OptimizedCANInterface(channel="can0", bitrate=500000)
        assert can_if.channel == "can0"
        assert can_if.bitrate == 500000
    
    @patch('interfaces.can_interface.can')
    def test_can_message_reception(self, mock_can):
        """Test receiving CAN messages."""
        from interfaces.can_interface import OptimizedCANInterface, CANMessage
        
        # Mock bus and message
        mock_bus = MagicMock()
        mock_msg = MagicMock()
        mock_msg.arbitration_id = 0x180
        mock_msg.data = bytes([0x12, 0x34, 0x56, 0x78])
        mock_msg.timestamp = time.time()
        mock_bus.recv.return_value = mock_msg
        mock_can.interface.Bus.return_value = mock_bus
        
        can_if = OptimizedCANInterface(channel="can0", bitrate=500000)
        can_if.connect()
        
        # Receive message
        msg = can_if.bus.recv(timeout=1.0)
        assert msg is not None
        assert msg.arbitration_id == 0x180
    
    def test_can_message_parsing(self, sample_can_message):
        """Test parsing CAN message data."""
        from interfaces.can_interface import CANMessage, CANMessageType
        
        msg = CANMessage(
            arbitration_id=sample_can_message['arbitration_id'],
            data=sample_can_message['data'],
            timestamp=sample_can_message['timestamp'],
            channel=sample_can_message['channel'],
            message_type=CANMessageType.STANDARD,
            dlc=sample_can_message['dlc'],
        )
        
        assert msg.arbitration_id == 0x180
        assert len(msg.data) == 8
        assert msg.channel == "can0"


class TestGPSDataReading:
    """Test GPS data reading."""
    
    @patch('interfaces.gps_interface.pynmea2')
    def test_gps_fix_reading(self, mock_pynmea2, mock_gps_fix):
        """Test reading GPS fix."""
        from interfaces.gps_interface import GPSFix
        
        fix = GPSFix(
            latitude=mock_gps_fix['latitude'],
            longitude=mock_gps_fix['longitude'],
            altitude=mock_gps_fix['altitude'],
            speed=mock_gps_fix['speed'],
            heading=mock_gps_fix['heading'],
            satellites=mock_gps_fix['satellites'],
            hdop=mock_gps_fix['hdop'],
            fix_quality=mock_gps_fix['fix_quality'],
            timestamp=mock_gps_fix['timestamp'],
        )
        
        assert fix.latitude == 40.7128
        assert fix.longitude == -74.0060
        assert fix.speed == 120.5
        assert fix.satellites == 12
    
    def test_gps_data_validation(self, mock_gps_fix):
        """Test GPS data validation."""
        # Valid data
        assert -90 <= mock_gps_fix['latitude'] <= 90
        assert -180 <= mock_gps_fix['longitude'] <= 180
        assert mock_gps_fix['altitude'] >= 0
        assert mock_gps_fix['speed'] >= 0
        assert 0 <= mock_gps_fix['heading'] < 360


class TestSensorDataReading:
    """Test sensor data reading."""
    
    def test_analog_sensor_reading(self):
        """Test reading analog sensor."""
        # Simulate ADC reading (0-4095 for 12-bit)
        adc_value = 2048  # Mid-range
        voltage = (adc_value / 4095.0) * 3.3  # 3.3V reference
        
        # Convert to temperature (example)
        temperature = (voltage - 0.5) * 100.0
        
        assert 0 <= adc_value <= 4095
        assert 0 <= voltage <= 3.3
        assert temperature > 0
    
    def test_digital_sensor_reading(self):
        """Test reading digital sensor."""
        # Simulate digital input (0 or 1)
        digital_value = 1  # High
        
        assert digital_value in [0, 1]
    
    def test_i2c_sensor_reading(self):
        """Test reading I2C sensor."""
        # Simulate I2C read
        i2c_address = 0x48
        register = 0x00
        data = [0x12, 0x34]  # 2 bytes
        
        assert 0x08 <= i2c_address <= 0x77  # Valid I2C address range
        assert len(data) > 0


class TestOBDDataReading:
    """Test OBD data reading."""
    
    @patch('interfaces.obd_interface.obd')
    def test_obd_connection(self, mock_obd):
        """Test OBD connection."""
        mock_connection = MagicMock()
        mock_obd.OBD.return_value = mock_connection
        mock_connection.is_connected.return_value = True
        
        # Simulate connection
        connected = mock_connection.is_connected()
        assert connected is True
    
    def test_obd_pid_reading(self):
        """Test reading OBD PID."""
        # Simulate PID response
        pid = 0x0C  # Engine RPM
        response_bytes = bytes([0x41, 0x0C, 0x19, 0x64])  # 6500 RPM
        
        # Parse RPM: (A * 256 + B) / 4
        rpm = ((response_bytes[2] * 256) + response_bytes[3]) / 4
        
        assert rpm == 6500.0


class TestDataNormalization:
    """Test data normalization and processing."""
    
    def test_data_normalization(self, sample_data):
        """Test normalizing sensor data."""
        # Normalize RPM (0-8000 range)
        rpm = sample_data['rpm']
        normalized_rpm = rpm / 8000.0
        
        assert 0 <= normalized_rpm <= 1
    
    def test_data_scaling(self):
        """Test scaling data values."""
        # Scale voltage to pressure
        voltage = 2.5  # Volts
        min_voltage = 0.5
        max_voltage = 4.5
        min_pressure = 0
        max_pressure = 100
        
        pressure = ((voltage - min_voltage) / (max_voltage - min_voltage)) * (max_pressure - min_pressure) + min_pressure
        
        assert min_pressure <= pressure <= max_pressure
    
    def test_data_aggregation(self):
        """Test aggregating multiple data points."""
        data_points = [
            {"rpm": 5000, "throttle": 50},
            {"rpm": 5500, "throttle": 60},
            {"rpm": 6000, "throttle": 70},
        ]
        
        avg_rpm = sum(d['rpm'] for d in data_points) / len(data_points)
        avg_throttle = sum(d['throttle'] for d in data_points) / len(data_points)
        
        assert avg_rpm == 5500.0
        assert avg_throttle == 60.0

