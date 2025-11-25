"""
Configuration module for AI-Tuner Agent.

Provides legacy constant-style settings for the edge agent as well as a
Pydantic-based `Settings` object used by the FastAPI authentication layer.

Automatically detects hardware platform (reTerminal DM, Raspberry Pi, Jetson, etc.)
and configures CAN channels and other hardware-specific settings.
"""

from __future__ import annotations

import os
from pathlib import Path

try:  # Optional dependency; FastAPI stack already brings pydantic in most cases.
    from pydantic import BaseSettings
except Exception:  # pragma: no cover - fallback when pydantic is unavailable
    class BaseSettings:  # type: ignore
        """Lightweight fallback so attribute access still works."""

        def __init__(self, **values):
            for key, value in values.items():
                setattr(self, key, value)

        def dict(self):
            return self.__dict__.copy()

try:  # Loading .env is optional; ignore if python-dotenv is not installed.
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

# Hardware platform detection
try:
    from core import get_hardware_config

    _hw_config = get_hardware_config()
    _default_can_channel = _hw_config.can_channels[0] if _hw_config.can_channels else "can0"
    _default_can_bitrate = _hw_config.can_bitrate
    _platform_name = _hw_config.platform_name
except Exception:
    # Fallback if hardware detection fails
    _default_can_channel = "can0"
    _default_can_bitrate = 500000
    _platform_name = "Unknown"

# General project identity
SYSTEM_NAME = os.getenv("SYSTEM_NAME", "AI Racing Agent v2.0")
PROJECT_NAME = os.getenv("PROJECT_NAME", "AI-Tuner")
DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() in {"1", "true", "yes"}
HARDWARE_PLATFORM = os.getenv("HARDWARE_PLATFORM", _platform_name)

# AWS IoT Core Configuration
AWS_ENDPOINT = os.getenv("AWS_ENDPOINT", "your-iot-endpoint.amazonaws.com")
AWS_PORT = int(os.getenv("AWS_PORT", "8883"))
TOPIC = os.getenv("AI_TUNER_TOPIC", "ai-tuner/telemetry/car001")

# Certificate paths
CA_CERT = os.getenv("CA_CERT", "AmazonRootCA1.pem")
DEVICE_CERT = os.getenv("DEVICE_CERT", "device-cert.pem")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "private-key.pem")

# CAN Bus Configuration (auto-detected from hardware platform)
CAN_CHANNEL = os.getenv("CAN_CHANNEL", _default_can_channel)
CAN_INTERFACE = os.getenv("CAN_INTERFACE", CAN_CHANNEL)
CAN_BUSTYPE = os.getenv("CAN_BUSTYPE", "socketcan")
CAN_BITRATE = int(os.getenv("CAN_BITRATE", str(_default_can_bitrate)))
# Secondary CAN channel (for reTerminal DM dual CAN)
CAN_CHANNEL_SECONDARY = os.getenv("CAN_CHANNEL_SECONDARY", None)
if CAN_CHANNEL_SECONDARY is None:
    try:
        _hw_config = get_hardware_config()
        if len(_hw_config.can_channels) > 1:
            CAN_CHANNEL_SECONDARY = _hw_config.can_channels[1]
    except Exception:
        CAN_CHANNEL_SECONDARY = None

DBC_FILE = os.getenv("DBC_FILE", "vehicle.dbc")
EMS_CAN_IDS = {
    "RPM": int(os.getenv("EMS_ID_RPM", "0x100"), 16),
    "THROTTLE": int(os.getenv("EMS_ID_THROTTLE", "0x101"), 16),
    "COOLANT_TEMP": int(os.getenv("EMS_ID_COOLANT", "0x102"), 16),
}
SENSOR_POLL_INTERVAL = float(os.getenv("SENSOR_POLL_INTERVAL", "0.1"))

# Model Configuration
MODEL_FILE = os.getenv("MODEL_FILE", "edge_model.tflite")
MODEL_PATH = os.getenv("MODEL_PATH", MODEL_FILE)

# Logging Configuration
LOG_FILE = Path(os.getenv("AI_AGENT_LOG_FILE", "logs/ai_agent.log"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# API Server Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))


class Settings(BaseSettings):
    """Security and API-related settings."""

    authjwt_secret_key: str = os.getenv("JWT_SECRET", "")
    authjwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    authjwt_access_token_expires: int = int(os.getenv("JWT_ACCESS_EXPIRES", "3600"))
    authjwt_refresh_token_expires: int = int(os.getenv("JWT_REFRESH_EXPIRES", "86400"))
    
    def __init__(self, **values):
        """Initialize settings with security validation."""
        super().__init__(**values)
        # CRITICAL: Require JWT secret key to be set via environment variable
        if not self.authjwt_secret_key:
            import secrets
            # Generate a secure random key if not provided (for development only)
            # In production, this MUST be set via JWT_SECRET environment variable
            if DEBUG_MODE:
                self.authjwt_secret_key = secrets.token_urlsafe(32)
                import warnings
                warnings.warn(
                    "JWT_SECRET not set! Generated temporary key for development. "
                    "Set JWT_SECRET environment variable in production!",
                    UserWarning
                )
            else:
                raise ValueError(
                    "JWT_SECRET environment variable is required in production. "
                    "Set it to a secure random string (e.g., 32+ characters)."
                )


settings = Settings()


__all__ = [
    "SYSTEM_NAME",
    "PROJECT_NAME",
    "DEBUG_MODE",
    "HARDWARE_PLATFORM",
    "AWS_ENDPOINT",
    "AWS_PORT",
    "TOPIC",
    "CA_CERT",
    "DEVICE_CERT",
    "PRIVATE_KEY",
    "CAN_CHANNEL",
    "CAN_CHANNEL_SECONDARY",
    "CAN_INTERFACE",
    "CAN_BUSTYPE",
    "CAN_BITRATE",
    "DBC_FILE",
    "EMS_CAN_IDS",
    "SENSOR_POLL_INTERVAL",
    "MODEL_FILE",
    "MODEL_PATH",
    "LOG_FILE",
    "LOG_LEVEL",
    "API_BASE_URL",
    "API_HOST",
    "API_PORT",
    "Settings",
    "settings",
]

