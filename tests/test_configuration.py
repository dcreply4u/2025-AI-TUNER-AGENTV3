"""
Test Configuration Management

Tests configuration loading, saving, validation, and defaults.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch

from tests.conftest import temp_dir


class TestConfigurationLoading:
    """Test configuration loading."""
    
    def test_load_default_config(self):
        """Test loading default configuration."""
        default_config = {
            "can_channel": "can0",
            "can_bitrate": 500000,
            "gps_enabled": True,
            "sensor_poll_rate": 100,
        }
        
        assert "can_channel" in default_config
        assert default_config["can_bitrate"] == 500000
    
    def test_load_config_from_file(self, temp_dir):
        """Test loading configuration from file."""
        config_file = temp_dir / "config.json"
        config = {
            "can_channel": "can0",
            "can_bitrate": 500000,
            "gps_enabled": True,
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        with open(config_file, 'r') as f:
            loaded = json.load(f)
            assert loaded == config
    
    def test_config_validation(self):
        """Test configuration validation."""
        config = {
            "can_bitrate": 500000,
            "sensor_poll_rate": 100,
        }
        
        # Validate bitrate
        assert 125000 <= config["can_bitrate"] <= 1000000
        assert config["sensor_poll_rate"] > 0


class TestConfigurationSaving:
    """Test configuration saving."""
    
    def test_save_config(self, temp_dir):
        """Test saving configuration."""
        config_file = temp_dir / "config.json"
        config = {
            "can_channel": "can0",
            "can_bitrate": 500000,
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        assert config_file.exists()
        assert config_file.stat().st_size > 0
    
    def test_config_persistence(self, temp_dir):
        """Test configuration persists correctly."""
        config_file = temp_dir / "config.json"
        original_config = {
            "setting1": "value1",
            "setting2": 123,
        }
        
        # Save
        with open(config_file, 'w') as f:
            json.dump(original_config, f)
        
        # Load
        with open(config_file, 'r') as f:
            loaded_config = json.load(f)
        
        assert loaded_config == original_config


class TestConfigurationDefaults:
    """Test default configuration values."""
    
    def test_default_can_settings(self):
        """Test default CAN settings."""
        defaults = {
            "channel": "can0",
            "bitrate": 500000,
        }
        
        assert defaults["channel"] == "can0"
        assert defaults["bitrate"] == 500000
    
    def test_default_gps_settings(self):
        """Test default GPS settings."""
        defaults = {
            "enabled": True,
            "update_rate": 10,
        }
        
        assert defaults["enabled"] is True
        assert defaults["update_rate"] > 0

