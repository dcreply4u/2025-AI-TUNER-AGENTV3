"""
Streaming Control Panel - Modern racing-style camera and streaming controls.

Features:
- Live streaming status with animated indicators
- Camera selection with preview thumbnails
- Stream quality presets
- One-click recording controls
- Real-time stream statistics
"""

from __future__ import annotations

import math
import time
from typing import Dict, List, Optional

from PySide6.QtCore import Property, QPropertyAnimation, QTimer, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class PulsingIndicator(QWidget):
    """Animated pulsing status indicator."""
    
    def __init__(
        self,
        size: int = 16,
        color: str = "#27ae60",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        
        self.indicator_size = size
        self.base_color = color
        self.is_active = False
        self._pulse_phase = 0.0
        
        self.setFixedSize(size + 8, size + 8)
        
        # Pulse animation timer
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self._update_pulse)
    
    def set_active(self, active: bool, color: Optional[str] = None) -> None:
        """Set indicator active state."""
        self.is_active = active
        if color:
            self.base_color = color
        
        if active:
            self.pulse_timer.start(50)
        else:
            self.pulse_timer.stop()
        self.update()
    
    def _update_pulse(self) -> None:
        """Update pulse animation."""
        self._pulse_phase = (self._pulse_phase + 0.15) % (2 * math.pi)
        self.update()
    
    def paintEvent(self, event) -> None:  # noqa: N802
        """Paint the indicator."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        cx = self.width() // 2
        cy = self.height() // 2
        radius = self.indicator_size // 2
        
        color = QColor(self.base_color)
        
        if self.is_active:
            # Pulsing glow
            pulse = 0.5 + 0.5 * math.sin(self._pulse_phase)
            glow_radius = radius + 4 + int(pulse * 3)
            
            glow = QRadialGradient(cx, cy, glow_radius)
            glow_color = QColor(color)
            glow_color.setAlpha(int(100 * pulse))
            glow.setColorAt(0, glow_color)
            glow_color.setAlpha(0)
            glow.setColorAt(1, glow_color)
            
            painter.setBrush(QBrush(glow))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(cx - glow_radius, cy - glow_radius, 
                               glow_radius * 2, glow_radius * 2)
        
        # Main indicator
        gradient = QRadialGradient(cx - 2, cy - 2, radius)
        lighter = QColor(color).lighter(150)
        gradient.setColorAt(0, lighter)
        gradient.setColorAt(0.7, color)
        gradient.setColorAt(1, color.darker(120))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(color.darker(150), 1))
        painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)


class StreamingStatusCard(QFrame):
    """Status card showing streaming/recording state."""
    
    def __init__(self, title: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e2530, stop:1 #0f1318);
                border: 1px solid #2a3040;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)
        
        # Header
        header = QHBoxLayout()
        
        self.indicator = PulsingIndicator(12, "#555555")
        header.addWidget(self.indicator)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #888; font-size: 10px; font-weight: bold; background: transparent;")
        header.addWidget(title_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Status text
        self.status_label = QLabel("OFFLINE")
        self.status_label.setStyleSheet("color: #555; font-size: 14px; font-weight: bold; background: transparent;")
        layout.addWidget(self.status_label)
        
        # Duration/Info
        self.info_label = QLabel("--:--")
        self.info_label.setStyleSheet("color: #00e0ff; font-size: 18px; font-weight: bold; background: transparent; font-family: Consolas;")
        layout.addWidget(self.info_label)
    
    def set_status(self, status: str, info: str, active: bool, color: str = "#27ae60") -> None:
        """Update status display."""
        self.status_label.setText(status)
        self.info_label.setText(info)
        self.indicator.set_active(active, color)
        
        if active:
            self.status_label.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold; background: transparent;")
        else:
            self.status_label.setStyleSheet("color: #555; font-size: 14px; font-weight: bold; background: transparent;")


class CameraSelector(QFrame):
    """Modern camera selection widget."""
    
    camera_changed = Signal(str)
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e2530, stop:1 #0f1318);
                border: 1px solid #2a3040;
                border-radius: 8px;
            }
            QComboBox {
                background-color: #0f1318;
                color: #ffffff;
                border: 1px solid #3a4050;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 11px;
                font-weight: bold;
            }
            QComboBox:hover {
                border-color: #00e0ff;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #00e0ff;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e2530;
                color: #ffffff;
                selection-background-color: #00e0ff;
                selection-color: #000000;
                border: 1px solid #3a4050;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("📹 CAMERA SOURCE")
        title.setStyleSheet("color: #00e0ff; font-size: 11px; font-weight: bold; background: transparent;")
        layout.addWidget(title)
        
        # Camera dropdown
        self.camera_combo = QComboBox()
        self.camera_combo.addItem("🎥 Select Camera...", None)
        self.camera_combo.currentIndexChanged.connect(self._on_camera_changed)
        layout.addWidget(self.camera_combo)
        
        # Camera status
        self.status_row = QHBoxLayout()
        
        self.resolution_label = QLabel("--")
        self.resolution_label.setStyleSheet("color: #888; font-size: 10px; background: transparent;")
        self.status_row.addWidget(self.resolution_label)
        
        self.fps_label = QLabel("-- FPS")
        self.fps_label.setStyleSheet("color: #888; font-size: 10px; background: transparent;")
        self.status_row.addWidget(self.fps_label)
        
        self.status_row.addStretch()
        layout.addLayout(self.status_row)
    
    def set_cameras(self, cameras: List[str]) -> None:
        """Update available cameras."""
        current = self.camera_combo.currentData()
        self.camera_combo.clear()
        self.camera_combo.addItem("🎥 Select Camera...", None)
        
        for i, cam in enumerate(cameras):
            icon = "📷" if i == 0 else "🎬"
            self.camera_combo.addItem(f"{icon} {cam}", cam)
        
        # Restore selection
        if current:
            idx = self.camera_combo.findData(current)
            if idx >= 0:
                self.camera_combo.setCurrentIndex(idx)
    
    def _on_camera_changed(self, index: int) -> None:
        """Handle camera selection change."""
        camera = self.camera_combo.currentData()
        if camera:
            self.camera_changed.emit(camera)
            self.resolution_label.setText("1920x1080")
            self.fps_label.setText("30 FPS")
        else:
            self.resolution_label.setText("--")
            self.fps_label.setText("-- FPS")


class QualitySelector(QFrame):
    """Stream quality preset selector."""
    
    quality_changed = Signal(str)
    
    QUALITY_PRESETS = {
        "720p30": {"label": "720p 30fps", "bitrate": "2.5 Mbps", "icon": "📺"},
        "1080p30": {"label": "1080p 30fps", "bitrate": "4.5 Mbps", "icon": "🖥️"},
        "1080p60": {"label": "1080p 60fps", "bitrate": "6 Mbps", "icon": "🎮"},
        "4k30": {"label": "4K 30fps", "bitrate": "13 Mbps", "icon": "📽️"},
    }
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e2530, stop:1 #0f1318);
                border: 1px solid #2a3040;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("⚙️ STREAM QUALITY")
        title.setStyleSheet("color: #00e0ff; font-size: 11px; font-weight: bold; background: transparent;")
        layout.addWidget(title)
        
        # Quality buttons grid
        grid = QGridLayout()
        grid.setSpacing(6)
        
        self.quality_buttons: Dict[str, QPushButton] = {}
        self.selected_quality = "1080p30"
        
        for i, (key, preset) in enumerate(self.QUALITY_PRESETS.items()):
            btn = QPushButton(f"{preset['icon']} {preset['label']}")
            btn.setCheckable(True)
            btn.setChecked(key == self.selected_quality)
            btn.clicked.connect(lambda checked, k=key: self._select_quality(k))
            btn.setStyleSheet(self._get_button_style(key == self.selected_quality))
            self.quality_buttons[key] = btn
            grid.addWidget(btn, i // 2, i % 2)
        
        layout.addLayout(grid)
        
        # Bitrate info
        self.bitrate_label = QLabel(f"📊 Bitrate: {self.QUALITY_PRESETS[self.selected_quality]['bitrate']}")
        self.bitrate_label.setStyleSheet("color: #888; font-size: 10px; background: transparent;")
        layout.addWidget(self.bitrate_label)
    
    def _get_button_style(self, selected: bool) -> str:
        """Get button style based on selection state."""
        if selected:
            return """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #00e0ff, stop:1 #0099aa);
                    color: #000;
                    border: none;
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 10px;
                    font-weight: bold;
                }
            """
        return """
            QPushButton {
                background: #1a1f2e;
                color: #888;
                border: 1px solid #3a4050;
                border-radius: 4px;
                padding: 8px;
                font-size: 10px;
            }
            QPushButton:hover {
                border-color: #00e0ff;
                color: #fff;
            }
        """
    
    def _select_quality(self, quality: str) -> None:
        """Handle quality selection."""
        self.selected_quality = quality
        
        for key, btn in self.quality_buttons.items():
            btn.setChecked(key == quality)
            btn.setStyleSheet(self._get_button_style(key == quality))
        
        self.bitrate_label.setText(f"📊 Bitrate: {self.QUALITY_PRESETS[quality]['bitrate']}")
        self.quality_changed.emit(quality)


class StreamControlButtons(QFrame):
    """Control buttons for streaming and recording."""
    
    start_stream_clicked = Signal()
    stop_stream_clicked = Signal()
    start_record_clicked = Signal()
    stop_record_clicked = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e2530, stop:1 #0f1318);
                border: 1px solid #2a3040;
                border-radius: 8px;
            }
        """)
        
        self.is_streaming = False
        self.is_recording = False
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("🎬 CONTROLS")
        title.setStyleSheet("color: #00e0ff; font-size: 11px; font-weight: bold; background: transparent;")
        layout.addWidget(title)
        
        # Stream button
        self.stream_btn = QPushButton("▶️ START STREAM")
        self.stream_btn.setMinimumHeight(45)
        self.stream_btn.clicked.connect(self._toggle_stream)
        self._update_stream_button()
        layout.addWidget(self.stream_btn)
        
        # Record button
        self.record_btn = QPushButton("⏺️ START RECORDING")
        self.record_btn.setMinimumHeight(45)
        self.record_btn.clicked.connect(self._toggle_record)
        self._update_record_button()
        layout.addWidget(self.record_btn)
    
    def _toggle_stream(self) -> None:
        """Toggle streaming state."""
        if self.is_streaming:
            self.stop_stream_clicked.emit()
        else:
            self.start_stream_clicked.emit()
    
    def _toggle_record(self) -> None:
        """Toggle recording state."""
        if self.is_recording:
            self.stop_record_clicked.emit()
        else:
            self.start_record_clicked.emit()
    
    def set_streaming(self, streaming: bool) -> None:
        """Set streaming state."""
        self.is_streaming = streaming
        self._update_stream_button()
    
    def set_recording(self, recording: bool) -> None:
        """Set recording state."""
        self.is_recording = recording
        self._update_record_button()
    
    def _update_stream_button(self) -> None:
        """Update stream button appearance."""
        if self.is_streaming:
            self.stream_btn.setText("⏹️ STOP STREAM")
            self.stream_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #c0392b, stop:1 #922b21);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #e74c3c, stop:1 #c0392b);
                }
            """)
        else:
            self.stream_btn.setText("▶️ START STREAM")
            self.stream_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #c0392b, stop:1 #922b21);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #e74c3c, stop:1 #c0392b);
                }
            """)
    
    def _update_record_button(self) -> None:
        """Update record button appearance."""
        if self.is_recording:
            self.record_btn.setText("⏹️ STOP RECORDING")
            self.record_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #e74c3c, stop:1 #c0392b);
                    color: white;
                    border: 2px solid #ff6b6b;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                }
            """)
        else:
            self.record_btn.setText("⏺️ START RECORDING")
            self.record_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #27ae60, stop:1 #1e8449);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #2ecc71, stop:1 #27ae60);
                }
            """)


class StreamStatsPanel(QFrame):
    """Real-time stream statistics display."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e2530, stop:1 #0f1318);
                border: 1px solid #2a3040;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("📊 STREAM INFO")
        title.setStyleSheet("color: #00e0ff; font-size: 11px; font-weight: bold; background: transparent;")
        layout.addWidget(title)
        
        # Stats grid
        stats_layout = QGridLayout()
        stats_layout.setSpacing(6)
        
        self.stats_labels: Dict[str, QLabel] = {}
        
        stats = [
            ("viewers", "👁️ Viewers", "0"),
            ("bitrate", "📶 Bitrate", "-- kbps"),
            ("dropped", "⚠️ Dropped", "0 frames"),
            ("uptime", "⏱️ Uptime", "--:--:--"),
        ]
        
        for i, (key, label, default) in enumerate(stats):
            name_label = QLabel(label)
            name_label.setStyleSheet("color: #888; font-size: 9px; background: transparent;")
            
            value_label = QLabel(default)
            value_label.setStyleSheet("color: #fff; font-size: 11px; font-weight: bold; background: transparent;")
            self.stats_labels[key] = value_label
            
            stats_layout.addWidget(name_label, i, 0)
            stats_layout.addWidget(value_label, i, 1)
        
        layout.addLayout(stats_layout)
    
    def update_stats(
        self,
        viewers: int = 0,
        bitrate: float = 0,
        dropped: int = 0,
        uptime: str = "--:--:--",
    ) -> None:
        """Update stream statistics."""
        self.stats_labels["viewers"].setText(str(viewers))
        self.stats_labels["bitrate"].setText(f"{bitrate:.0f} kbps" if bitrate > 0 else "-- kbps")
        self.stats_labels["dropped"].setText(f"{dropped} frames")
        self.stats_labels["uptime"].setText(uptime)


class StreamingControlPanel(QFrame):
    """
    Complete streaming control panel with modern racing-style design.
    
    Combines:
    - Camera selection
    - Stream quality settings
    - Recording/streaming controls
    - Real-time statistics
    """
    
    def __init__(
        self,
        live_streamer=None,
        camera_manager=None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        
        self.live_streamer = live_streamer
        self.camera_manager = camera_manager
        self.recording_start_time: Optional[float] = None
        self.streaming_start_time: Optional[float] = None
        
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame#StreamingControlPanel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #12161f, stop:1 #0a0d12);
                border: 2px solid #1a2030;
                border-radius: 10px;
            }
        """)
        self.setObjectName("StreamingControlPanel")
        
        self.setMinimumSize(290, 550)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header
        header = QLabel("📡 STREAMING CENTER")
        header.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #00e0ff;
            padding: 5px;
            background: transparent;
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Status cards row
        status_row = QHBoxLayout()
        status_row.setSpacing(8)
        
        self.stream_status = StreamingStatusCard("STREAM")
        self.record_status = StreamingStatusCard("RECORD")
        
        status_row.addWidget(self.stream_status)
        status_row.addWidget(self.record_status)
        layout.addLayout(status_row)
        
        # Camera selector
        self.camera_selector = CameraSelector()
        layout.addWidget(self.camera_selector)
        
        # Quality selector
        self.quality_selector = QualitySelector()
        layout.addWidget(self.quality_selector)
        
        # Control buttons
        self.controls = StreamControlButtons()
        self.controls.start_stream_clicked.connect(self._start_stream)
        self.controls.stop_stream_clicked.connect(self._stop_stream)
        self.controls.start_record_clicked.connect(self._start_record)
        self.controls.stop_record_clicked.connect(self._stop_record)
        layout.addWidget(self.controls)
        
        # Stats panel
        self.stats_panel = StreamStatsPanel()
        layout.addWidget(self.stats_panel)
        
        layout.addStretch()
        
        # Update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(1000)
        
        # Demo timer for stats simulation
        self.demo_timer = QTimer(self)
        self.demo_timer.timeout.connect(self._update_demo_stats)
    
    def set_camera_manager(self, camera_manager) -> None:
        """Set camera manager reference."""
        self.camera_manager = camera_manager
        if camera_manager and hasattr(camera_manager, "camera_manager"):
            cameras = list(camera_manager.camera_manager.cameras.keys())
            self.camera_selector.set_cameras(cameras)
    
    def set_cameras(self, cameras: List[str]) -> None:
        """Update available cameras."""
        self.camera_selector.set_cameras(cameras)
    
    def _start_stream(self) -> None:
        """Start streaming."""
        camera = self.camera_selector.camera_combo.currentData()
        if not camera:
            return
        
        # Start stream (implementation depends on live_streamer)
        self.streaming_start_time = time.time()
        self.controls.set_streaming(True)
        self.stream_status.set_status("LIVE", "00:00:00", True, "#e74c3c")
        self.demo_timer.start(1000)
    
    def _stop_stream(self) -> None:
        """Stop streaming."""
        self.streaming_start_time = None
        self.controls.set_streaming(False)
        self.stream_status.set_status("OFFLINE", "--:--", False)
        self.demo_timer.stop()
        self.stats_panel.update_stats()
    
    def _start_record(self) -> None:
        """Start recording."""
        if self.camera_manager:
            try:
                session_id = time.strftime("%Y%m%d_%H%M%S")
                self.camera_manager.start_recording(session_id)
            except Exception as e:
                print(f"Recording error: {e}")
        
        self.recording_start_time = time.time()
        self.controls.set_recording(True)
        self.record_status.set_status("REC", "00:00:00", True, "#e74c3c")
    
    def _stop_record(self) -> None:
        """Stop recording."""
        if self.camera_manager:
            try:
                self.camera_manager.stop_recording()
            except Exception as e:
                print(f"Stop recording error: {e}")
        
        self.recording_start_time = None
        self.controls.set_recording(False)
        self.record_status.set_status("STOPPED", "--:--", False)
    
    def _update_display(self) -> None:
        """Update time displays."""
        if self.streaming_start_time:
            elapsed = time.time() - self.streaming_start_time
            h, m, s = int(elapsed // 3600), int((elapsed % 3600) // 60), int(elapsed % 60)
            self.stream_status.info_label.setText(f"{h:02d}:{m:02d}:{s:02d}")
            self.stats_panel.update_stats(uptime=f"{h:02d}:{m:02d}:{s:02d}")
        
        if self.recording_start_time:
            elapsed = time.time() - self.recording_start_time
            m, s = int(elapsed // 60), int(elapsed % 60)
            self.record_status.info_label.setText(f"{m:02d}:{s:02d}")
    
    def _update_demo_stats(self) -> None:
        """Update demo statistics."""
        import random
        
        self.stats_panel.update_stats(
            viewers=random.randint(10, 150),
            bitrate=4500 + random.uniform(-200, 200),
            dropped=random.randint(0, 5),
        )


__all__ = [
    "StreamingControlPanel",
    "CameraSelector",
    "QualitySelector",
    "StreamControlButtons",
    "StreamStatsPanel",
    "StreamingStatusCard",
    "PulsingIndicator",
]

