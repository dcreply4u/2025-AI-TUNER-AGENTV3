"""
ECU Auto-Configuration Controller

Automatically detects ECU and configures the entire system on startup.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from PySide6.QtCore import QObject, QTimer, Signal

from core.config_manager import ConfigManager
from services.ecu_auto_setup import ECUAutoSetup, Manufacturer
from services.voice_feedback import VoiceFeedback

LOGGER = logging.getLogger(__name__)


class ECUAutoConfigController(QObject):
    """Controller for automatic ECU detection and configuration."""

    # Signals
    ecu_detected = Signal(str)  # Emits vendor name
    configuration_complete = Signal(dict)  # Emits configuration
    detection_failed = Signal(str)  # Emits error message

    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        voice_feedback: Optional[VoiceFeedback] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        """
        Initialize ECU auto-config controller.

        Args:
            config_manager: Configuration manager instance
            voice_feedback: Voice feedback for notifications
            parent: Parent QObject
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.voice_feedback = voice_feedback
        self.ecu_setup = ECUAutoSetup(notification_callback=self._notify)
        self.auto_config_enabled = True
        self.detection_in_progress = False

    def _notify(self, message: str, level: str = "info") -> None:
        """Send notification via voice feedback."""
        if self.voice_feedback:
            from services.voice_feedback import FeedbackPriority

            priority_map = {
                "info": FeedbackPriority.LOW,
                "warning": FeedbackPriority.MEDIUM,
                "error": FeedbackPriority.HIGH,
                "success": FeedbackPriority.MEDIUM,
            }
            priority = priority_map.get(level, FeedbackPriority.LOW)
            self.voice_feedback.announce(message, priority=priority)

        LOGGER.info("[ECU Auto-Config] %s", message)

    def start_auto_detection(self, sample_time: float = 5.0) -> None:
        """
        Start automatic ECU detection and configuration.

        Args:
            sample_time: Time to sample CAN bus
        """
        if self.detection_in_progress:
            LOGGER.warning("ECU detection already in progress")
            return

        if not self.auto_config_enabled:
            LOGGER.info("Auto-configuration disabled")
            return

        self.detection_in_progress = True
        self._notify("Starting automatic ECU detection", "info")

        # Run detection in background (non-blocking)
        QTimer.singleShot(100, lambda: self._run_detection(sample_time))

    def _run_detection(self, sample_time: float) -> None:
        """Run ECU detection (called from timer)."""
        try:
            success = self.ecu_setup.detect_and_setup(sample_time=sample_time)

            if success:
                vendor = self.ecu_setup.detected_vendor
                if vendor:
                    self.ecu_detected.emit(vendor.value)

                    # Get configuration
                    config = self.ecu_setup.get_configuration()
                    self.configuration_complete.emit(config)

                    # Save to config manager
                    self._save_configuration(config)

                    # Detect manufacturer
                    manufacturer = self.ecu_setup.detect_manufacturer()
                    if manufacturer:
                        self._notify(f"Detected manufacturer: {manufacturer.value.upper()}", "info")

                    self._notify("ECU configuration complete", "success")
            else:
                self.detection_failed.emit("Could not detect ECU vendor")
                self._notify("ECU detection failed - using default settings", "warning")

        except Exception as e:
            LOGGER.error("Error during ECU detection: %s", e)
            self.detection_failed.emit(str(e))
            self._notify(f"ECU detection error: {str(e)}", "error")
        finally:
            self.detection_in_progress = False

    def _save_configuration(self, config: dict) -> None:
        """Save detected configuration to config manager."""
        if not self.config_manager:
            return

        try:
            # Get or create profile
            profile_name = f"Auto-{config.get('vendor', 'Unknown')}"
            profile = self.config_manager.get_profile(profile_name)

            if not profile:
                profile = self.config_manager.create_profile(
                    name=profile_name,
                    ecu_vendor=config.get("vendor", "generic"),
                    can_channel=config.get("can_channel", "can0"),
                    can_bitrate=config.get("can_bitrate", 500000),
                )

            # Update with detected settings
            self.config_manager.update_profile(
                profile_name,
                can_bitrate=config.get("can_bitrate", 500000),
                **config.get("default_settings", {}),
            )

            # Set as default if no default exists
            if not self.config_manager.config.default_profile:
                self.config_manager.set_default_profile(profile_name)

            LOGGER.info("Saved ECU configuration to profile: %s", profile_name)
        except Exception as e:
            LOGGER.error("Failed to save configuration: %s", e)

    def get_optimized_settings(self) -> dict:
        """
        Get optimized settings for detected ECU.

        Returns:
            Dictionary of optimized settings
        """
        if not self.ecu_setup.auto_configured:
            return {}

        return self.ecu_setup.get_optimized_settings()

    def apply_to_data_stream(self, data_stream_controller) -> None:
        """
        Apply detected configuration to data stream controller.

        Args:
            data_stream_controller: Data stream controller instance
        """
        if not self.ecu_setup.auto_configured:
            return

        settings = self.get_optimized_settings()

        # Update CAN settings
        if "can_channel" in settings:
            data_stream_controller.settings.can_channel = settings["can_channel"]
        if "can_bitrate" in settings:
            data_stream_controller.settings.can_bitrate = settings["can_bitrate"]

        # Update polling intervals
        if "polling_intervals" in settings:
            # Apply to controller's polling logic
            min_interval = min(settings["polling_intervals"].values()) if settings["polling_intervals"] else 0.5
            data_stream_controller.settings.interval_sec = min_interval

        LOGGER.info("Applied ECU optimizations to data stream controller")

    def get_detection_status(self) -> dict:
        """Get current detection status."""
        return {
            "detected": self.ecu_setup.auto_configured,
            "vendor": self.ecu_setup.detected_vendor.value if self.ecu_setup.detected_vendor else None,
            "in_progress": self.detection_in_progress,
            "configuration": self.ecu_setup.get_configuration() if self.ecu_setup.auto_configured else {},
        }


__all__ = ["ECUAutoConfigController"]

