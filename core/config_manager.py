"""
Configuration Management System

Handles persistent storage, profile management, and configuration validation.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger(__name__)

# Optional encryption support
try:
    from core.file_encryption import EncryptedFileManager
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False
    EncryptedFileManager = None  # type: ignore


@dataclass
class VehicleProfile:
    """Vehicle configuration profile."""

    name: str
    vehicle_type: str = "car"
    ecu_vendor: str = "generic"
    can_channel: str = "can0"
    can_bitrate: int = 500000
    obd_port: str = "/dev/ttyUSB0"
    obd_baud: int = 115200
    gps_enabled: bool = True
    cameras: List[Dict[str, Any]] = field(default_factory=list)
    overlay_config: Dict[str, Any] = field(default_factory=dict)
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AppConfig:
    """Application-wide configuration."""

    default_profile: Optional[str] = None
    profiles: Dict[str, VehicleProfile] = field(default_factory=dict)
    ui_settings: Dict[str, Any] = field(default_factory=dict)
    cloud_settings: Dict[str, Any] = field(default_factory=dict)
    voice_settings: Dict[str, Any] = field(default_factory=dict)
    storage_settings: Dict[str, Any] = field(default_factory=dict)


class ConfigManager:
    """Manages application configuration with persistence."""

    def __init__(
        self,
        config_file: str | Path = "config/app_config.json",
        encryption_manager: Optional["EncryptedFileManager"] = None,
    ) -> None:
        """
        Initialize configuration manager.

        Args:
            config_file: Path to configuration file
            encryption_manager: Optional encryption manager for encrypted config files
        """
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.config = AppConfig()
        self.encryption_manager = encryption_manager
        
        # Auto-initialize encryption if enabled
        if not self.encryption_manager and ENCRYPTION_AVAILABLE:
            encryption_enabled = os.environ.get("AI_TUNER_ENCRYPTION_ENABLED", "false").lower() == "true"
            if encryption_enabled:
                use_yubikey = os.environ.get("AI_TUNER_USE_YUBIKEY", "false").lower() == "true"
                password = os.environ.get("AI_TUNER_ENCRYPTION_PASSWORD")
                if EncryptedFileManager:
                    self.encryption_manager = EncryptedFileManager(
                        encryption_enabled=True,
                        use_yubikey=use_yubikey,
                        password=password,
                    )
        
        self._load()

    def _load(self) -> None:
        """Load configuration from file (with encryption support)."""
        # Check for encrypted version first
        encrypted_file = self.config_file.with_suffix(self.config_file.suffix + '.encrypted')
        file_to_load = encrypted_file if encrypted_file.exists() else self.config_file
        
        if not file_to_load.exists():
            LOGGER.info("Configuration file not found, using defaults")
            self._save()  # Create default config
            return

        try:
            # Read file (encrypted or plain)
            if self.encryption_manager and file_to_load.suffix == '.encrypted':
                # Read encrypted file
                data_bytes = self.encryption_manager.read_file(file_to_load, encrypted=True)
                if data_bytes:
                    data = json.loads(data_bytes.decode('utf-8'))
                else:
                    raise ValueError("Failed to decrypt configuration file")
            else:
                # Read plain file
                with open(file_to_load, "r") as f:
                    data = json.load(f)

            # Load profiles
            if "profiles" in data:
                self.config.profiles = {
                    name: VehicleProfile(**profile_data) for name, profile_data in data["profiles"].items()
                }

            # Load other settings
            self.config.default_profile = data.get("default_profile")
            self.config.ui_settings = data.get("ui_settings", {})
            self.config.cloud_settings = data.get("cloud_settings", {})
            self.config.voice_settings = data.get("voice_settings", {})
            self.config.storage_settings = data.get("storage_settings", {})

            LOGGER.info("Configuration loaded from %s", self.config_file)
        except Exception as e:
            LOGGER.error("Failed to load configuration: %s", e)
            LOGGER.info("Using default configuration")

    def _save(self) -> bool:
        """Save configuration to file (with encryption support)."""
        try:
            data = {
                "default_profile": self.config.default_profile,
                "profiles": {name: asdict(profile) for name, profile in self.config.profiles.items()},
                "ui_settings": self.config.ui_settings,
                "cloud_settings": self.config.cloud_settings,
                "voice_settings": self.config.voice_settings,
                "storage_settings": self.config.storage_settings,
            }

            # Save with encryption if enabled
            if self.encryption_manager and self.encryption_manager.encryption.encryption_enabled:
                # Save encrypted
                data_json = json.dumps(data, indent=2)
                success = self.encryption_manager.write_text_file(
                    self.config_file,
                    data_json,
                    encrypt=True,
                )
                if success:
                    LOGGER.info("Configuration saved (encrypted) to %s", self.config_file)
                    return True
            else:
                # Save plain
                with open(self.config_file, "w") as f:
                    json.dump(data, f, indent=2)
                LOGGER.info("Configuration saved to %s", self.config_file)
                return True

        except Exception as e:
            LOGGER.error("Failed to save configuration: %s", e)
            return False

    def create_profile(self, name: str, **kwargs) -> VehicleProfile:
        """
        Create a new vehicle profile.

        Args:
            name: Profile name
            **kwargs: Profile settings

        Returns:
            Created profile
        """
        profile = VehicleProfile(name=name, **kwargs)
        self.config.profiles[name] = profile
        self._save()
        LOGGER.info("Created profile: %s", name)
        return profile

    def get_profile(self, name: Optional[str] = None) -> Optional[VehicleProfile]:
        """
        Get a profile by name or default profile.

        Args:
            name: Profile name (None for default)

        Returns:
            Profile or None if not found
        """
        if name is None:
            name = self.config.default_profile

        if name and name in self.config.profiles:
            return self.config.profiles[name]
        return None

    def update_profile(self, name: str, **kwargs) -> bool:
        """
        Update a profile.

        Args:
            name: Profile name
            **kwargs: Settings to update

        Returns:
            True if updated successfully
        """
        if name not in self.config.profiles:
            return False

        profile = self.config.profiles[name]
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        self._save()
        LOGGER.info("Updated profile: %s", name)
        return True

    def delete_profile(self, name: str) -> bool:
        """
        Delete a profile.

        Args:
            name: Profile name

        Returns:
            True if deleted successfully
        """
        if name not in self.config.profiles:
            return False

        del self.config.profiles[name]

        # Clear default if it was the deleted profile
        if self.config.default_profile == name:
            self.config.default_profile = None

        self._save()
        LOGGER.info("Deleted profile: %s", name)
        return True

    def list_profiles(self) -> List[str]:
        """List all profile names."""
        return list(self.config.profiles.keys())

    def set_default_profile(self, name: str) -> bool:
        """
        Set default profile.

        Args:
            name: Profile name

        Returns:
            True if set successfully
        """
        if name not in self.config.profiles:
            return False

        self.config.default_profile = name
        self._save()
        return True

    def get_setting(self, category: str, key: str, default: Any = None) -> Any:
        """
        Get a setting value.

        Args:
            category: Setting category (ui_settings, cloud_settings, etc.)
            key: Setting key
            default: Default value if not found

        Returns:
            Setting value
        """
        settings = getattr(self.config, category, {})
        return settings.get(key, default)

    def set_setting(self, category: str, key: str, value: Any) -> None:
        """
        Set a setting value.

        Args:
            category: Setting category
            key: Setting key
            value: Setting value
        """
        settings = getattr(self.config, category, {})
        settings[key] = value
        setattr(self.config, category, settings)
        self._save()

    def export_config(self, export_path: str | Path) -> bool:
        """
        Export configuration to a file.

        Args:
            export_path: Path to export file

        Returns:
            True if exported successfully
        """
        try:
            export_path = Path(export_path)
            with open(export_path, "w") as f:
                json.dump(
                    {
                        "default_profile": self.config.default_profile,
                        "profiles": {name: asdict(profile) for name, profile in self.config.profiles.items()},
                        "ui_settings": self.config.ui_settings,
                        "cloud_settings": self.config.cloud_settings,
                        "voice_settings": self.config.voice_settings,
                        "storage_settings": self.config.storage_settings,
                    },
                    f,
                    indent=2,
                )
            LOGGER.info("Configuration exported to %s", export_path)
            return True
        except Exception as e:
            LOGGER.error("Failed to export configuration: %s", e)
            return False

    def import_config(self, import_path: str | Path) -> bool:
        """
        Import configuration from a file.

        Args:
            import_path: Path to import file

        Returns:
            True if imported successfully
        """
        try:
            import_path = Path(import_path)
            with open(import_path, "r") as f:
                data = json.load(f)

            # Merge imported data
            if "profiles" in data:
                self.config.profiles.update(
                    {name: VehicleProfile(**profile_data) for name, profile_data in data["profiles"].items()}
                )

            if "default_profile" in data:
                self.config.default_profile = data["default_profile"]

            for category in ["ui_settings", "cloud_settings", "voice_settings", "storage_settings"]:
                if category in data:
                    getattr(self.config, category).update(data[category])

            self._save()
            LOGGER.info("Configuration imported from %s", import_path)
            return True
        except Exception as e:
            LOGGER.error("Failed to import configuration: %s", e)
            return False

    def validate_config(self) -> tuple[bool, List[str]]:
        """
        Validate configuration.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Validate default profile exists
        if self.config.default_profile and self.config.default_profile not in self.config.profiles:
            errors.append(f"Default profile '{self.config.default_profile}' does not exist")

        # Validate profiles
        for name, profile in self.config.profiles.items():
            if not profile.name:
                errors.append(f"Profile '{name}' has no name")
            if profile.can_bitrate not in [125000, 250000, 500000, 1000000]:
                errors.append(f"Profile '{name}' has invalid CAN bitrate: {profile.can_bitrate}")

        return len(errors) == 0, errors


__all__ = ["ConfigManager", "VehicleProfile", "AppConfig"]

