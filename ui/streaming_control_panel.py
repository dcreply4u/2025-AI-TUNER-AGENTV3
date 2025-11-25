"""
Streaming Control Panel - Modern camera and streaming controls.

Matches the light theme design of other panels (Wheel Slip Monitor, System Status).

Features:
- Live streaming status with animated indicators
- Camera selection with preview info
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
    QGroupBox,
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
        size: int = 14,
        color: str = "#27ae60",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        
        self.indicator_size = size
        self.base_color = color
        self.is_active = False
        self._pulse_phase = 0.0
        
        self.setFixedSize(size + 10, size + 10)
        
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
            glow_radius = radius + 3 + int(pulse * 2)
            
            glow = QRadialGradient(cx, cy, glow_radius)
            glow_color = QColor(color)
            glow_color.setAlpha(int(80 * pulse))
            glow.setColorAt(0, glow_color)
            glow_color.setAlpha(0)
            glow.setColorAt(1, glow_color)
            
            painter.setBrush(QBrush(glow))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(cx - glow_radius, cy - glow_radius, 
                               glow_radius * 2, glow_radius * 2)
        
        # Main indicator
        gradient = QRadialGradient(cx - 2, cy - 2, radius)
        lighter = QColor(color).lighter(140)
        gradient.setColorAt(0, lighter)
        gradient.setColorAt(0.7, color)
        gradient.setColorAt(1, color.darker(110))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(color.darker(130), 1))
        painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)


class StreamingStatusCard(QFrame):
    """Status card showing streaming/recording state."""
    
    def __init__(self, title: str, icon: str = "📡", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)
        
        # Left: indicator
        self.indicator = PulsingIndicator(12, "#95a5a6")
        layout.addWidget(self.indicator)
        
        # Center: text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 14px; background: transparent;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #7f8c8d; font-size: 10px; font-weight: bold; background: transparent;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        text_layout.addLayout(header_layout)
        
        # Status and time
        status_row = QHBoxLayout()
        status_row.setSpacing(10)
        
        self.status_label = QLabel("OFFLINE")
        self.status_label.setStyleSheet("color: #95a5a6; font-size: 12px; font-weight: bold; background: transparent;")
        status_row.addWidget(self.status_label)
        
        self.time_label = QLabel("--:--")
        self.time_label.setStyleSheet("color: #3498db; font-size: 14px; font-weight: bold; background: transparent; font-family: Consolas;")
        status_row.addWidget(self.time_label)
        status_row.addStretch()
        
        text_layout.addLayout(status_row)
        layout.addLayout(text_layout, 1)
    
    def set_status(self, status: str, time_str: str, active: bool, color: str = "#27ae60") -> None:
        """Update status display."""
        self.status_label.setText(status)
        self.time_label.setText(time_str)
        self.indicator.set_active(active, color)
        
        if active:
            self.status_label.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: bold; background: transparent;")
            self.time_label.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold; background: transparent; font-family: Consolas;")
        else:
            self.status_label.setStyleSheet("color: #95a5a6; font-size: 12px; font-weight: bold; background: transparent;")
            self.time_label.setStyleSheet("color: #3498db; font-size: 14px; font-weight: bold; background: transparent; font-family: Consolas;")


class StreamingControlPanel(QFrame):
    """
    Complete streaming control panel with light theme design.
    
    Matches the style of Wheel Slip Monitor and other panels.
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
        self.is_streaming = False
        self.is_recording = False
        
        self.setProperty("class", "metric-tile")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
            }
            QLabel {
                background: transparent;
                color: #2c3e50;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                background: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                color: #2c3e50;
            }
            QComboBox {
                background-color: #ffffff;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 11px;
                min-width: 150px;
            }
            QComboBox:hover {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #3498db;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #2c3e50;
                selection-background-color: #3498db;
                selection-color: #ffffff;
                border: 1px solid #bdc3c7;
            }
        """)
        
        # Match other panel sizes
        self.setMinimumSize(280, 420)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Header
        header = QLabel("📡 Streaming Center")
        header.setStyleSheet("font-size: 14px; font-weight: 700; color: #2c3e50;")
        layout.addWidget(header)
        
        # Status cards
        status_row = QHBoxLayout()
        status_row.setSpacing(10)
        
        self.stream_status = StreamingStatusCard("STREAM", "📺")
        self.record_status = StreamingStatusCard("RECORD", "⏺️")
        
        status_row.addWidget(self.stream_status, 1)
        status_row.addWidget(self.record_status, 1)
        layout.addLayout(status_row)
        
        # Camera Selection Group
        camera_group = QGroupBox("📹 Camera Source")
        camera_layout = QVBoxLayout(camera_group)
        camera_layout.setContentsMargins(10, 15, 10, 10)
        camera_layout.setSpacing(8)
        
        self.camera_combo = QComboBox()
        self.camera_combo.addItem("Select Camera...", None)
        camera_layout.addWidget(self.camera_combo)
        
        # Camera info row
        camera_info = QHBoxLayout()
        camera_info.setSpacing(15)
        
        self.resolution_label = QLabel("Resolution: --")
        self.resolution_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        camera_info.addWidget(self.resolution_label)
        
        self.fps_label = QLabel("FPS: --")
        self.fps_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        camera_info.addWidget(self.fps_label)
        camera_info.addStretch()
        
        camera_layout.addLayout(camera_info)
        layout.addWidget(camera_group)
        
        # Quality Selection Group
        quality_group = QGroupBox("⚙️ Stream Quality")
        quality_layout = QVBoxLayout(quality_group)
        quality_layout.setContentsMargins(10, 15, 10, 10)
        quality_layout.setSpacing(8)
        
        # Quality buttons grid
        quality_grid = QGridLayout()
        quality_grid.setSpacing(8)
        
        self.quality_buttons: Dict[str, QPushButton] = {}
        self.selected_quality = "1080p30"
        
        qualities = [
            ("720p30", "📺 720p 30fps", "2.5 Mbps"),
            ("1080p30", "🖥️ 1080p 30fps", "4.5 Mbps"),
            ("1080p60", "🎮 1080p 60fps", "6 Mbps"),
            ("4k30", "📽️ 4K 30fps", "13 Mbps"),
        ]
        
        for i, (key, label, bitrate) in enumerate(qualities):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(key == self.selected_quality)
            btn.setProperty("bitrate", bitrate)
            btn.clicked.connect(lambda checked, k=key: self._select_quality(k))
            self._update_quality_button_style(btn, key == self.selected_quality)
            self.quality_buttons[key] = btn
            quality_grid.addWidget(btn, i // 2, i % 2)
        
        quality_layout.addLayout(quality_grid)
        
        # Bitrate info
        self.bitrate_label = QLabel("📊 Bitrate: 4.5 Mbps")
        self.bitrate_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        quality_layout.addWidget(self.bitrate_label)
        
        layout.addWidget(quality_group)
        
        # Controls Group
        controls_group = QGroupBox("🎬 Controls")
        controls_layout = QVBoxLayout(controls_group)
        controls_layout.setContentsMargins(10, 15, 10, 10)
        controls_layout.setSpacing(10)
        
        # Stream button
        self.stream_btn = QPushButton("▶️  Start Stream")
        self.stream_btn.setMinimumHeight(40)
        self.stream_btn.clicked.connect(self._toggle_stream)
        self._update_stream_button()
        controls_layout.addWidget(self.stream_btn)
        
        # Record button
        self.record_btn = QPushButton("⏺️  Start Recording")
        self.record_btn.setMinimumHeight(40)
        self.record_btn.clicked.connect(self._toggle_record)
        self._update_record_button()
        controls_layout.addWidget(self.record_btn)
        
        layout.addWidget(controls_group)
        
        # Stats Group
        stats_group = QGroupBox("📊 Stream Info")
        stats_layout = QGridLayout(stats_group)
        stats_layout.setContentsMargins(10, 15, 10, 10)
        stats_layout.setSpacing(8)
        
        self.stats_labels: Dict[str, QLabel] = {}
        
        stats = [
            ("viewers", "👁️ Viewers:", "0"),
            ("bitrate", "📶 Bitrate:", "-- kbps"),
            ("dropped", "⚠️ Dropped:", "0 frames"),
            ("uptime", "⏱️ Uptime:", "--:--:--"),
        ]
        
        for i, (key, label, default) in enumerate(stats):
            name_label = QLabel(label)
            name_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")
            
            value_label = QLabel(default)
            value_label.setStyleSheet("color: #2c3e50; font-size: 11px; font-weight: bold;")
            self.stats_labels[key] = value_label
            
            stats_layout.addWidget(name_label, i // 2, (i % 2) * 2)
            stats_layout.addWidget(value_label, i // 2, (i % 2) * 2 + 1)
        
        layout.addWidget(stats_group)
        
        layout.addStretch()
        
        # Update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(1000)
    
    def _update_quality_button_style(self, btn: QPushButton, selected: bool) -> None:
        """Update quality button style."""
        if selected:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 10px;
                    font-weight: bold;
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #ecf0f1;
                    color: #7f8c8d;
                    border: 1px solid #bdc3c7;
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    border-color: #3498db;
                    color: #2c3e50;
                }
            """)
    
    def _select_quality(self, quality: str) -> None:
        """Handle quality selection."""
        self.selected_quality = quality
        
        for key, btn in self.quality_buttons.items():
            btn.setChecked(key == quality)
            self._update_quality_button_style(btn, key == quality)
        
        bitrate = self.quality_buttons[quality].property("bitrate")
        self.bitrate_label.setText(f"📊 Bitrate: {bitrate}")
    
    def _update_stream_button(self) -> None:
        """Update stream button appearance."""
        if self.is_streaming:
            self.stream_btn.setText("⏹️  Stop Stream")
            self.stream_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
        else:
            self.stream_btn.setText("▶️  Start Stream")
            self.stream_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
    
    def _update_record_button(self) -> None:
        """Update record button appearance."""
        if self.is_recording:
            self.record_btn.setText("⏹️  Stop Recording")
            self.record_btn.setStyleSheet("""
                QPushButton {
                    background-color: #c0392b;
                    color: white;
                    border: 2px solid #e74c3c;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                }
            """)
        else:
            self.record_btn.setText("⏺️  Start Recording")
            self.record_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #229954;
                }
            """)
    
    def _toggle_stream(self) -> None:
        """Toggle streaming state."""
        if self.is_streaming:
            self._stop_stream()
        else:
            self._start_stream()
    
    def _toggle_record(self) -> None:
        """Toggle recording state."""
        if self.is_recording:
            self._stop_record()
        else:
            self._start_record()
    
    def _start_stream(self) -> None:
        """Start streaming."""
        camera = self.camera_combo.currentData()
        if not camera:
            return
        
        self.streaming_start_time = time.time()
        self.is_streaming = True
        self._update_stream_button()
        self.stream_status.set_status("LIVE", "00:00:00", True, "#e74c3c")
    
    def _stop_stream(self) -> None:
        """Stop streaming."""
        self.streaming_start_time = None
        self.is_streaming = False
        self._update_stream_button()
        self.stream_status.set_status("OFFLINE", "--:--", False)
        self._reset_stats()
    
    def _start_record(self) -> None:
        """Start recording."""
        if self.camera_manager:
            try:
                session_id = time.strftime("%Y%m%d_%H%M%S")
                self.camera_manager.start_recording(session_id)
            except Exception as e:
                print(f"Recording error: {e}")
        
        self.recording_start_time = time.time()
        self.is_recording = True
        self._update_record_button()
        self.record_status.set_status("REC", "00:00:00", True, "#e74c3c")
    
    def _stop_record(self) -> None:
        """Stop recording."""
        if self.camera_manager:
            try:
                self.camera_manager.stop_recording()
            except Exception as e:
                print(f"Stop recording error: {e}")
        
        self.recording_start_time = None
        self.is_recording = False
        self._update_record_button()
        self.record_status.set_status("STOPPED", "--:--", False)
    
    def _update_display(self) -> None:
        """Update time displays."""
        if self.streaming_start_time:
            elapsed = time.time() - self.streaming_start_time
            h, m, s = int(elapsed // 3600), int((elapsed % 3600) // 60), int(elapsed % 60)
            time_str = f"{h:02d}:{m:02d}:{s:02d}"
            self.stream_status.time_label.setText(time_str)
            self.stats_labels["uptime"].setText(time_str)
            
            # Simulated stats
            import random
            self.stats_labels["viewers"].setText(str(random.randint(10, 150)))
            self.stats_labels["bitrate"].setText(f"{4500 + random.randint(-200, 200)} kbps")
            self.stats_labels["dropped"].setText(f"{random.randint(0, 3)} frames")
        
        if self.recording_start_time:
            elapsed = time.time() - self.recording_start_time
            m, s = int(elapsed // 60), int(elapsed % 60)
            self.record_status.time_label.setText(f"{m:02d}:{s:02d}")
    
    def _reset_stats(self) -> None:
        """Reset statistics display."""
        self.stats_labels["viewers"].setText("0")
        self.stats_labels["bitrate"].setText("-- kbps")
        self.stats_labels["dropped"].setText("0 frames")
        self.stats_labels["uptime"].setText("--:--:--")
    
    def set_camera_manager(self, camera_manager) -> None:
        """Set camera manager reference."""
        self.camera_manager = camera_manager
        if camera_manager and hasattr(camera_manager, "camera_manager"):
            cameras = list(camera_manager.camera_manager.cameras.keys())
            self.set_cameras(cameras)
    
    def set_cameras(self, cameras: List[str]) -> None:
        """Update available cameras."""
        current = self.camera_combo.currentData()
        self.camera_combo.clear()
        self.camera_combo.addItem("Select Camera...", None)
        
        for i, cam in enumerate(cameras):
            icon = "📷" if "front" in cam.lower() else "🎬"
            self.camera_combo.addItem(f"{icon} {cam}", cam)
        
        # Restore selection
        if current:
            idx = self.camera_combo.findData(current)
            if idx >= 0:
                self.camera_combo.setCurrentIndex(idx)
        
        # Update info
        if cameras:
            self.resolution_label.setText("Resolution: 1920x1080")
            self.fps_label.setText("FPS: 30")


__all__ = [
    "StreamingControlPanel",
    "StreamingStatusCard",
    "PulsingIndicator",
]
