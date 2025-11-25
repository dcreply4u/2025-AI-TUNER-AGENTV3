"""
Camera Quick Widget

A small, cool-looking widget for instant camera recording control.
Designed for quick access when in a rush.
"""

from __future__ import annotations

import time
from typing import Optional

try:
    from PySide6.QtCore import Qt, QTimer, Signal
    from PySide6.QtGui import QColor, QPainter, QPen
    from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget
except ImportError:
    try:
        from PySide6.QtCore import Qt, QTimer, Signal as Signal
        from PySide6.QtGui import QColor, QPainter, QPen
        from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget
    except ImportError:
        from PyQt5.QtCore import Qt, QTimer, Signal as Signal
        from PyQt5.QtGui import QColor, QPainter, QPen
        from PyQt5.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget


class CameraQuickWidget(QWidget):
    """Small, sleek camera recording widget with instant start/stop."""

    # Signal emitted when recording state changes
    recording_changed = Signal(bool)

    def __init__(self, camera_manager=None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.camera_manager = camera_manager
        self.is_recording = False
        self.recording_start_time: Optional[float] = None

        # Widget styling
        self.setFixedSize(120, 120)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Recording indicator label
        self.status_label = QLabel("READY")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(
            """
            QLabel {
                font-size: 10px;
                font-weight: bold;
                color: #00ff00;
                background: transparent;
            }
        """
        )
        layout.addWidget(self.status_label)

        # Time display
        self.time_label = QLabel("00:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #ffffff;
                background: transparent;
            }
        """
        )
        layout.addWidget(self.time_label)

        # Camera count label
        self.camera_count_label = QLabel("0 CAM")
        self.camera_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_count_label.setStyleSheet(
            """
            QLabel {
                font-size: 9px;
                color: #888888;
                background: transparent;
            }
        """
        )
        layout.addWidget(self.camera_count_label)

        # Update timer for recording time
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_recording_time)
        self.update_timer.setInterval(100)  # Update every 100ms

        # Set widget style
        self._update_style()

        # Make widget clickable
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event) -> None:
        """Handle mouse click to toggle recording."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_recording()
        super().mousePressEvent(event)

    def toggle_recording(self) -> None:
        """Toggle recording state."""
        if not self.camera_manager:
            return

        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self) -> None:
        """Start recording."""
        if not self.camera_manager:
            return

        try:
            session_id = time.strftime("%Y%m%d_%H%M%S")
            self.camera_manager.start_recording(session_id)
            self.is_recording = True
            self.recording_start_time = time.time()
            self.update_timer.start()
            self._update_style()
            self.recording_changed.emit(True)
        except Exception as e:
            print(f"Error starting recording: {e}")

    def stop_recording(self) -> None:
        """Stop recording."""
        if not self.camera_manager:
            return

        try:
            self.camera_manager.stop_recording()
            self.is_recording = False
            self.recording_start_time = None
            self.update_timer.stop()
            self.time_label.setText("00:00")
            self._update_style()
            self.recording_changed.emit(False)
        except Exception as e:
            print(f"Error stopping recording: {e}")

    def _update_recording_time(self) -> None:
        """Update recording time display."""
        if self.recording_start_time:
            elapsed = time.time() - self.recording_start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            self.time_label.setText(f"{minutes:02d}:{seconds:02d}")

    def _update_style(self) -> None:
        """Update widget style based on recording state."""
        if self.is_recording:
            # Recording style - red pulsing
            self.status_label.setText("REC")
            self.status_label.setStyleSheet(
                """
                QLabel {
                    font-size: 10px;
                    font-weight: bold;
                    color: #ff0000;
                    background: transparent;
                }
            """
            )
            self.setStyleSheet(
                """
                QWidget {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #2a0000, stop:1 #1a0000);
                    border: 2px solid #ff0000;
                    border-radius: 10px;
                }
            """
            )
        else:
            # Ready style - green
            self.status_label.setText("READY")
            self.status_label.setStyleSheet(
                """
                QLabel {
                    font-size: 10px;
                    font-weight: bold;
                    color: #00ff00;
                    background: transparent;
                }
            """
            )
            self.setStyleSheet(
                """
                QWidget {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #002a00, stop:1 #001a00);
                    border: 2px solid #00ff00;
                    border-radius: 10px;
                }
            """
            )

    def paintEvent(self, event) -> None:
        """Custom paint event for pulsing effect when recording."""
        super().paintEvent(event)

        if self.is_recording:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Pulsing red circle indicator
            pulse_alpha = int(128 + 127 * abs(time.time() % 1.0 - 0.5) * 2)
            pen = QPen(QColor(255, 0, 0, pulse_alpha))
            pen.setWidth(3)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            # Draw pulsing circle
            margin = 5
            painter.drawEllipse(margin, margin, self.width() - 2 * margin, self.height() - 2 * margin)

    def update_camera_count(self, count: int) -> None:
        """Update camera count display."""
        self.camera_count_label.setText(f"{count} CAM" if count > 0 else "NO CAM")

    def set_camera_manager(self, camera_manager) -> None:
        """Set camera manager."""
        self.camera_manager = camera_manager
        if camera_manager:
            # Update camera count
            camera_count = len(camera_manager.camera_manager.cameras) if hasattr(camera_manager, "camera_manager") else 0
            self.update_camera_count(camera_count)


__all__ = ["CameraQuickWidget"]

