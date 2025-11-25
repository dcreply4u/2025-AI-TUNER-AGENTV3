"""
Tests for ConfigManager.
"""

import pytest

from core.config_manager import ConfigManager, VehicleProfile


class TestConfigManager:
    """Test suite for ConfigManager."""

    def test_create_profile(self, config_manager):
        """Test creating a profile."""
        profile = config_manager.create_profile("Test Vehicle", vehicle_type="car", ecu_vendor="Holley")

        assert profile.name == "Test Vehicle"
        assert profile.vehicle_type == "car"
        assert profile.ecu_vendor == "Holley"
        assert "Test Vehicle" in config_manager.list_profiles()

    def test_get_profile(self, config_manager):
        """Test getting a profile."""
        config_manager.create_profile("Test Vehicle")
        profile = config_manager.get_profile("Test Vehicle")

        assert profile is not None
        assert profile.name == "Test Vehicle"

    def test_update_profile(self, config_manager):
        """Test updating a profile."""
        config_manager.create_profile("Test Vehicle", ecu_vendor="Holley")
        success = config_manager.update_profile("Test Vehicle", ecu_vendor="Haltech")

        assert success
        profile = config_manager.get_profile("Test Vehicle")
        assert profile.ecu_vendor == "Haltech"

    def test_delete_profile(self, config_manager):
        """Test deleting a profile."""
        config_manager.create_profile("Test Vehicle")
        assert "Test Vehicle" in config_manager.list_profiles()

        success = config_manager.delete_profile("Test Vehicle")
        assert success
        assert "Test Vehicle" not in config_manager.list_profiles()

    def test_set_default_profile(self, config_manager):
        """Test setting default profile."""
        config_manager.create_profile("Test Vehicle")
        success = config_manager.set_default_profile("Test Vehicle")

        assert success
        assert config_manager.config.default_profile == "Test Vehicle"

    def test_settings(self, config_manager):
        """Test getting and setting configuration values."""
        config_manager.set_setting("ui_settings", "theme", "dark")
        value = config_manager.get_setting("ui_settings", "theme")

        assert value == "dark"

    def test_export_import(self, config_manager, temp_dir):
        """Test exporting and importing configuration."""
        config_manager.create_profile("Test Vehicle")

        export_path = temp_dir / "exported_config.json"
        success = config_manager.export_config(export_path)
        assert success
        assert export_path.exists()

        # Create new manager and import
        new_manager = ConfigManager(config_file=str(temp_dir / "imported_config.json"))
        success = new_manager.import_config(export_path)
        assert success
        assert "Test Vehicle" in new_manager.list_profiles()

    def test_validation(self, config_manager):
        """Test configuration validation."""
        config_manager.create_profile("Test Vehicle", can_bitrate=500000)
        is_valid, errors = config_manager.validate_config()

        assert is_valid
        assert len(errors) == 0

    def test_invalid_config(self, config_manager):
        """Test validation of invalid configuration."""
        config_manager.config.default_profile = "NonExistent"
        is_valid, errors = config_manager.validate_config()

        assert not is_valid
        assert len(errors) > 0

