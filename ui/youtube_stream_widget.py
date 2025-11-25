"""
YouTube Streaming Widget

Dedicated widget for YouTube live streaming with camera selection,
stream status, and controls.
"""

from __future__ import annotations

from typing import Optional

try:
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

from services.live_streamer import LiveStreamer, StreamConfig, StreamingPlatform


class YouTubeStreamWidget(QWidget):
    """Dedicated widget for YouTube live streaming."""

    def __init__(self, live_streamer: Optional[LiveStreamer] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.live_streamer = live_streamer or LiveStreamer()
        self.setWindowTitle("YouTube Live Stream")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Status display
        status_group = QGroupBox("Stream Status")
        status_layout = QVBoxLayout(status_group)

        self.status_label = QLabel("Status: Offline")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #888;")
        status_layout.addWidget(self.status_label)

        self.viewer_count_label = QLabel("Viewers: 0")
        self.viewer_count_label.setStyleSheet("font-size: 12px; color: #666;")
        status_layout.addWidget(self.viewer_count_label)

        layout.addWidget(status_group)

        # Camera selection
        camera_group = QGroupBox("Camera Selection")
        camera_layout = QFormLayout(camera_group)

        self.camera_combo = QComboBox()
        self.camera_combo.addItem("-- Select Camera --", None)
        camera_layout.addRow("Camera:", self.camera_combo)

        self.overlay_cb = QCheckBox("Show Telemetry Overlay")
        self.overlay_cb.setChecked(True)
        camera_layout.addRow("", self.overlay_cb)

        layout.addWidget(camera_group)

        # Stream quality
        quality_group = QGroupBox("Stream Quality")
        quality_layout = QFormLayout(quality_group)

        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["720p 30fps", "1080p 30fps", "1080p 60fps", "4K 30fps"])
        self.quality_combo.setCurrentText("1080p 30fps")
        quality_layout.addRow("Quality:", self.quality_combo)

        layout.addWidget(quality_group)

        # Controls
        controls_group = QGroupBox("Controls")
        controls_layout = QVBoxLayout(controls_group)

        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Stream")
        self.start_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #c4302b;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #a02020;
            }
            QPushButton:disabled {
                background-color: #666;
            }
        """
        )
        self.start_btn.clicked.connect(self._start_stream)

        self.stop_btn = QPushButton("Stop Stream")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #333;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QPushButton:disabled {
                background-color: #666;
            }
        """
        )
        self.stop_btn.clicked.connect(self._stop_stream)

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self._open_settings)

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.settings_btn)
        controls_layout.addLayout(button_layout)

        layout.addWidget(controls_group)

        # Stream info
        info_group = QGroupBox("Stream Information")
        info_layout = QFormLayout(info_group)

        self.stream_url_label = QLabel("--")
        self.stream_url_label.setWordWrap(True)
        info_layout.addRow("Stream URL:", self.stream_url_label)

        self.stream_key_label = QLabel("--")
        info_layout.addRow("Stream Key:", self.stream_key_label)

        layout.addWidget(info_group)

        layout.addStretch()

        # Status update timer
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)  # Update every second

        self.current_camera = None
        self.stream_config: Optional[StreamConfig] = None

    def set_cameras(self, cameras: list[str]) -> None:
        """Update available cameras."""
        current_selection = self.camera_combo.currentData()
        self.camera_combo.clear()
        self.camera_combo.addItem("-- Select Camera --", None)
        for camera in cameras:
            self.camera_combo.addItem(camera, camera)
        # Restore selection if still available
        if current_selection and current_selection in cameras:
            idx = self.camera_combo.findData(current_selection)
            if idx >= 0:
                self.camera_combo.setCurrentIndex(idx)

    def _start_stream(self) -> None:
        """Start YouTube stream."""
        camera_name = self.camera_combo.currentData()
        if not camera_name:
            self.status_label.setText("Status: Error - No camera selected")
            return

        # Get stream config from settings
        from ui.youtube_settings_dialog import YouTubeSettingsDialog

        dialog = YouTubeSettingsDialog(parent=self)
        if not dialog.exec():
            return

        config = dialog.get_stream_config()
        if not config:
            self.status_label.setText("Status: Error - Invalid configuration")
            return

        # Start stream
        if self.live_streamer.start_stream(camera_name, config):
            self.current_camera = camera_name
            self.stream_config = config
            # Get parent window's camera manager to enable streaming
            parent = self.parent()
            while parent and not hasattr(parent, "camera_manager"):
                parent = parent.parent()
            if parent and hasattr(parent, "camera_manager") and parent.camera_manager:
                parent.camera_manager.start_streaming(camera_name, camera_name)
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText("Status: Streaming")
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #c4302b;")
            self.stream_url_label.setText(config.rtmp_url.split("/")[0] + "//..." if config.rtmp_url else "YouTube")
            self.stream_key_label.setText("***" + config.stream_key[-4:] if len(config.stream_key) > 4 else "***")
        else:
            self.status_label.setText("Status: Error - Failed to start stream")

    def _stop_stream(self) -> None:
        """Stop YouTube stream."""
        if self.current_camera:
            # Get parent window's camera manager to disable streaming
            parent = self.parent()
            while parent and not hasattr(parent, "camera_manager"):
                parent = parent.parent()
            if parent and hasattr(parent, "camera_manager") and parent.camera_manager:
                parent.camera_manager.stop_streaming(self.current_camera)
            self.live_streamer.stop_stream(self.current_camera)
            self.current_camera = None
            self.stream_config = None
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_label.setText("Status: Offline")
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #888;")
            self.stream_url_label.setText("--")
            self.stream_key_label.setText("--")

    def _open_settings(self) -> None:
        """Open YouTube settings dialog."""
        from ui.youtube_settings_dialog import YouTubeSettingsDialog

        dialog = YouTubeSettingsDialog(parent=self)
        dialog.exec()

    def _update_status(self) -> None:
        """Update stream status display."""
        if self.current_camera and self.live_streamer.is_streaming(self.current_camera):
            # Update viewer count (placeholder - would need YouTube API)
            # For now, just show streaming status
            pass

    def get_frame_callback(self) -> Optional[callable]:
        """Get frame callback for streaming."""
        if not self.current_camera:
            return None

        # This would be set by the camera manager
        return None

    def set_frame_callback(self, callback: callable) -> None:
        """Set frame callback for streaming."""
        # This would be called by the camera manager
        pass


__all__ = ["YouTubeStreamWidget"]

