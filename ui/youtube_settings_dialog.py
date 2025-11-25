"""
YouTube Settings Dialog

Configuration dialog for YouTube live streaming settings.
"""

from __future__ import annotations

from typing import Optional

try:
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QGroupBox,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QGroupBox,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )

from services.live_streamer import StreamConfig, StreamingPlatform


class YouTubeSettingsDialog(QDialog):
    """Dialog for configuring YouTube streaming settings."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("YouTube Streaming Settings")
        self.resize(500, 600)

        layout = QVBoxLayout(self)

        # Platform selection
        platform_group = QGroupBox("Streaming Platform")
        platform_layout = QFormLayout(platform_group)

        self.platform_combo = QComboBox()
        for platform in StreamingPlatform:
            self.platform_combo.addItem(platform.value.title(), platform)
        self.platform_combo.setCurrentText("Youtube")
        self.platform_combo.currentIndexChanged.connect(self._on_platform_changed)
        platform_layout.addRow("Platform:", self.platform_combo)

        layout.addWidget(platform_group)

        # Stream credentials
        credentials_group = QGroupBox("Stream Credentials")
        credentials_layout = QFormLayout(credentials_group)

        self.stream_key_input = QLineEdit()
        self.stream_key_input.setPlaceholderText("Enter your stream key")
        self.stream_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        credentials_layout.addRow("Stream Key:", self.stream_key_input)

        # Show/hide stream key button
        show_key_btn = QPushButton("Show")
        show_key_btn.setMaximumWidth(60)
        show_key_btn.clicked.connect(self._toggle_stream_key_visibility)
        self._stream_key_visible = False
        credentials_layout.addRow("", show_key_btn)

        # Custom RTMP URL (for custom platforms)
        self.custom_rtmp_input = QLineEdit()
        self.custom_rtmp_input.setPlaceholderText("rtmp://example.com/live")
        self.custom_rtmp_input.setVisible(False)
        credentials_layout.addRow("Custom RTMP URL:", self.custom_rtmp_input)

        layout.addWidget(credentials_group)

        # Video settings
        video_group = QGroupBox("Video Settings")
        video_layout = QFormLayout(video_group)

        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["720p", "1080p", "1440p", "4K"])
        self.resolution_combo.setCurrentText("1080p")
        self.resolution_combo.currentIndexChanged.connect(self._on_resolution_changed)
        video_layout.addRow("Resolution:", self.resolution_combo)

        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["30", "60"])
        self.fps_combo.setCurrentText("30")
        video_layout.addRow("Frame Rate:", self.fps_combo)

        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["1000k", "2500k", "4000k", "6000k", "8000k"])
        self.bitrate_combo.setCurrentText("2500k")
        video_layout.addRow("Bitrate:", self.bitrate_combo)

        layout.addWidget(video_group)

        # Encoding settings
        encoding_group = QGroupBox("Encoding Settings")
        encoding_layout = QFormLayout(encoding_group)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["ultrafast", "veryfast", "faster", "fast", "medium"])
        self.preset_combo.setCurrentText("veryfast")
        encoding_layout.addRow("Encoding Preset:", self.preset_combo)

        layout.addWidget(encoding_group)

        # Overlay settings
        overlay_group = QGroupBox("Overlay Settings")
        overlay_layout = QFormLayout(overlay_group)

        self.overlay_cb = QCheckBox("Enable Telemetry Overlay")
        self.overlay_cb.setChecked(True)
        overlay_layout.addRow("", self.overlay_cb)

        layout.addWidget(overlay_group)

        # Help/Info
        help_label = QLabel(
            "<b>How to get your YouTube Stream Key:</b><br>"
            "1. Go to YouTube Studio<br>"
            "2. Click 'Go Live'<br>"
            "3. Copy your Stream Key<br>"
            "4. Paste it above"
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(help_label)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Load saved settings
        self._load_settings()

    def _on_platform_changed(self) -> None:
        """Handle platform selection change."""
        platform = self.platform_combo.currentData()
        if platform == StreamingPlatform.CUSTOM_RTMP:
            self.custom_rtmp_input.setVisible(True)
            self.stream_key_input.setPlaceholderText("Optional stream key")
        else:
            self.custom_rtmp_input.setVisible(False)
            if platform == StreamingPlatform.YOUTUBE:
                self.stream_key_input.setPlaceholderText("Enter your YouTube stream key")
            elif platform == StreamingPlatform.TWITCH:
                self.stream_key_input.setPlaceholderText("Enter your Twitch stream key")
            else:
                self.stream_key_input.setPlaceholderText("Enter your stream key")

    def _on_resolution_changed(self) -> None:
        """Handle resolution change - update bitrate recommendations."""
        resolution = self.resolution_combo.currentText()
        fps = int(self.fps_combo.currentText())

        # Recommended bitrates
        recommendations = {
            "720p": "2500k" if fps == 30 else "4000k",
            "1080p": "4000k" if fps == 30 else "6000k",
            "1440p": "6000k" if fps == 30 else "8000k",
            "4K": "8000k" if fps == 30 else "12000k",
        }

        recommended = recommendations.get(resolution, "2500k")
        idx = self.bitrate_combo.findText(recommended)
        if idx >= 0:
            self.bitrate_combo.setCurrentIndex(idx)

    def _toggle_stream_key_visibility(self) -> None:
        """Toggle stream key visibility."""
        self._stream_key_visible = not self._stream_key_visible
        if self._stream_key_visible:
            self.stream_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.sender().setText("Hide")  # type: ignore
        else:
            self.stream_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.sender().setText("Show")  # type: ignore

    def _validate_and_accept(self) -> None:
        """Validate settings before accepting."""
        platform = self.platform_combo.currentData()

        if platform == StreamingPlatform.CUSTOM_RTMP:
            if not self.custom_rtmp_input.text().strip():
                QMessageBox.warning(self, "Invalid Settings", "Please enter a custom RTMP URL.")
                return
        else:
            if not self.stream_key_input.text().strip():
                QMessageBox.warning(self, "Invalid Settings", "Please enter your stream key.")
                return

        self.accept()

    def get_stream_config(self) -> Optional[StreamConfig]:
        """Get stream configuration from dialog."""
        platform = self.platform_combo.currentData()
        stream_key = self.stream_key_input.text().strip()

        # Parse resolution
        resolution = self.resolution_combo.currentText()
        width, height = self._parse_resolution(resolution)
        fps = int(self.fps_combo.currentText())

        # Build RTMP URL
        if platform == StreamingPlatform.CUSTOM_RTMP:
            rtmp_url = self.custom_rtmp_input.text().strip()
        else:
            # Will be built by LiveStreamer
            rtmp_url = ""

        config = StreamConfig(
            platform=platform,
            rtmp_url=rtmp_url,
            stream_key=stream_key,
            width=width,
            height=height,
            fps=fps,
            bitrate=self.bitrate_combo.currentText(),
            preset=self.preset_combo.currentText(),
            enable_overlay=self.overlay_cb.isChecked(),
        )

        return config

    def _parse_resolution(self, resolution: str) -> tuple[int, int]:
        """Parse resolution string to width/height."""
        resolutions = {
            "720p": (1280, 720),
            "1080p": (1920, 1080),
            "1440p": (2560, 1440),
            "4K": (3840, 2160),
        }
        return resolutions.get(resolution, (1920, 1080))

    def _load_settings(self) -> None:
        """Load saved settings (placeholder - would load from config file)."""
        # TODO: Load from persistent storage
        pass

    def _save_settings(self) -> None:
        """Save settings (placeholder - would save to config file)."""
        # TODO: Save to persistent storage
        pass


__all__ = ["YouTubeSettingsDialog"]

