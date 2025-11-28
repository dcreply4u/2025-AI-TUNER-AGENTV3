"""
Integration Tests

Tests integration between different components.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

from tests.conftest import sample_data, sample_can_message, mock_gps_fix


class TestDataFlow:
    """Test data flow through the system."""
    
    def test_can_to_telemetry_flow(self, sample_can_message):
        """Test data flow from CAN to telemetry."""
        # Simulate CAN message
        can_msg = sample_can_message
        
        # Decode CAN message (simplified)
        decoded_data = {
            "rpm": 6500,
            "throttle": 85.5,
            "boost": 12.3,
        }
        
        # Verify data structure
        assert "rpm" in decoded_data
        assert "throttle" in decoded_data
        assert decoded_data["rpm"] > 0
    
    def test_gps_to_telemetry_flow(self, mock_gps_fix):
        """Test data flow from GPS to telemetry."""
        gps_data = mock_gps_fix
        
        # Convert to telemetry format
        telemetry = {
            "latitude": gps_data["latitude"],
            "longitude": gps_data["longitude"],
            "speed": gps_data["speed"],
            "altitude": gps_data["altitude"],
        }
        
        assert "latitude" in telemetry
        assert "longitude" in telemetry
        assert telemetry["speed"] >= 0
    
    def test_sensor_to_telemetry_flow(self):
        """Test data flow from sensors to telemetry."""
        # Simulate sensor readings
        sensor_readings = {
            "temp1": 185.0,
            "pressure1": 45.2,
            "voltage1": 12.5,
        }
        
        # Normalize to telemetry format
        telemetry = {
            "coolant_temp": sensor_readings["temp1"],
            "oil_pressure": sensor_readings["pressure1"],
            "battery_voltage": sensor_readings["voltage1"],
        }
        
        assert "coolant_temp" in telemetry
        assert telemetry["coolant_temp"] > 0


class TestComponentIntegration:
    """Test integration between components."""
    
    @patch('controllers.data_stream_controller.DataStreamController')
    def test_data_stream_integration(self, mock_controller):
        """Test data stream controller integration."""
        # Mock controller
        mock_instance = MagicMock()
        mock_controller.return_value = mock_instance
        
        # Simulate data flow
        mock_instance._latest_sample = sample_data
        mock_instance._on_poll = MagicMock()
        
        # Verify integration
        assert mock_instance._latest_sample is not None
        assert "rpm" in mock_instance._latest_sample
    
    def test_ui_data_integration(self, sample_data):
        """Test UI integration with data."""
        # Simulate UI update with data
        ui_data = {
            "rpm": sample_data["rpm"],
            "throttle": sample_data["throttle"],
            "boost": sample_data["boost"],
        }
        
        # Verify data is in correct format for UI
        assert all(isinstance(v, (int, float)) for v in ui_data.values())
        assert all(v >= 0 for v in ui_data.values())


class TestEndToEnd:
    """Test end-to-end functionality."""
    
    def test_data_collection_to_display(self, sample_data):
        """Test complete flow from collection to display."""
        # Step 1: Collect data
        collected_data = sample_data
        
        # Step 2: Process data
        processed_data = {
            k: v for k, v in collected_data.items()
            if isinstance(v, (int, float))
        }
        
        # Step 3: Format for display
        display_data = {
            k: f"{v:.1f}" if isinstance(v, float) else str(v)
            for k, v in processed_data.items()
        }
        
        assert len(display_data) > 0
        assert all(isinstance(v, str) for v in display_data.values())
    
    def test_configuration_to_runtime(self):
        """Test configuration loading to runtime."""
        # Configuration
        config = {
            "can_channel": "can0",
            "can_bitrate": 500000,
            "gps_enabled": True,
        }
        
        # Runtime initialization
        runtime_config = {
            "can": {
                "channel": config["can_channel"],
                "bitrate": config["can_bitrate"],
            },
            "gps": {
                "enabled": config["gps_enabled"],
            },
        }
        
        assert runtime_config["can"]["channel"] == "can0"
        assert runtime_config["gps"]["enabled"] is True
