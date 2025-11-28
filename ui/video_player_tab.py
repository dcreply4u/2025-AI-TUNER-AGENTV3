"""
Video Player Tab
Comprehensive video player with play, pause, rewind, slow motion, replay, and USB camera capture
"""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import Qt, QTimer, Signal, QThread, QObject
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QFileDialog,
    QGroupBox,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QMessageBox,
    QSizePolicy,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size

LOGGER = logging.getLogger(__name__)

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    np = None
    CV2_AVAILABLE = False

try:
    from services.usb_camera_manager import USBCameraManager
    CAMERA_MANAGER_AVAILABLE = True
except ImportError:
    USBCameraManager = None
    CAMERA_MANAGER_AVAILABLE = False


class VideoPlayerThread(QThread):
    """Thread for video playback to prevent UI blocking."""
    
    frame_ready = Signal(QImage)
    playback_finished = Signal()
    position_changed = Signal(int)  # Current frame position
    
    def __init__(self, video_path: str, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.video_path = video_path
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_playing = False
        self.is_paused = False
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 30.0
        self.playback_speed = 1.0  # 1.0 = normal, 0.5 = half speed, 2.0 = double speed
        self._stop_requested = False
        
    def run(self) -> None:
        """Main playback loop."""
        if not CV2_AVAILABLE:
            LOGGER.error("OpenCV not available for video playback")
            return
            
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            LOGGER.error(f"Failed to open video: {self.video_path}")
            return
            
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        
        frame_delay_ms = int(1000.0 / (self.fps * self.playback_speed))
        
        while not self._stop_requested:
            if not self.is_playing or self.is_paused:
                time.sleep(0.01)  # Small delay when paused
                continue
                
            ret, frame = self.cap.read()
            if not ret:
                # End of video
                self.is_playing = False
                self.playback_finished.emit()
                break
                
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            
            self.frame_ready.emit(qt_image)
            self.position_changed.emit(self.current_frame)
            
            self.current_frame += 1
            
            # Sleep based on playback speed
            time.sleep(frame_delay_ms / 1000.0)
            
        if self.cap:
            self.cap.release()
            
    def set_position(self, frame_number: int) -> None:
        """Seek to a specific frame."""
        if self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            self.current_frame = frame_number
            
    def set_playback_speed(self, speed: float) -> None:
        """Set playback speed (0.25, 0.5, 1.0, 2.0, 4.0)."""
        self.playback_speed = speed
        
    def stop(self) -> None:
        """Stop playback."""
        self._stop_requested = True
        self.is_playing = False
        self.is_paused = False


class CameraCaptureThread(QThread):
    """Thread for capturing video from USB camera."""
    
    frame_ready = Signal(QImage)
    
    def __init__(self, camera_id: str, width: int = 1920, height: int = 1080, fps: int = 30, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.fps = fps
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_capturing = False
        self._stop_requested = False
        
    def run(self) -> None:
        """Main capture loop."""
        if not CV2_AVAILABLE:
            LOGGER.error("OpenCV not available for camera capture")
            return
            
        self.cap = cv2.VideoCapture(int(self.camera_id))
        if not self.cap.isOpened():
            LOGGER.error(f"Failed to open camera: {self.camera_id}")
            return
            
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        
        frame_delay_ms = int(1000.0 / self.fps)
        
        while not self._stop_requested:
            if not self.is_capturing:
                time.sleep(0.01)
                continue
                
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.01)
                continue
                
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            
            self.frame_ready.emit(qt_image)
            
            time.sleep(frame_delay_ms / 1000.0)
            
        if self.cap:
            self.cap.release()
            
    def stop(self) -> None:
        """Stop capture."""
        self._stop_requested = True
        self.is_capturing = False


class VideoPlayerTab(QWidget):
    """Comprehensive video player with playback controls and USB camera capture."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        
        self.video_path: Optional[str] = None
        self.playback_thread: Optional[VideoPlayerThread] = None
        self.capture_thread: Optional[CameraCaptureThread] = None
        self.video_writer: Optional[cv2.VideoWriter] = None
        self.is_recording = False
        
        self.camera_manager: Optional[USBCameraManager] = None
        if CAMERA_MANAGER_AVAILABLE and USBCameraManager:
            try:
                self.camera_manager = USBCameraManager()
                self.camera_manager.detect_all_cameras()
            except Exception as e:
                LOGGER.warning(f"Failed to initialize camera manager: {e}")
        
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup video player UI."""
        main_layout = QVBoxLayout(self)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        self.setStyleSheet("background-color: #1a1a1a;")
        
        # Top controls
        top_controls = self._create_top_controls()
        main_layout.addWidget(top_controls)
        
        # Video display
        video_display = self._create_video_display()
        main_layout.addWidget(video_display, stretch=1)
        
        # Playback controls
        playback_controls = self._create_playback_controls()
        main_layout.addWidget(playback_controls)
        
        # Camera capture section
        camera_section = self._create_camera_section()
        main_layout.addWidget(camera_section)
        
    def _create_top_controls(self) -> QWidget:
        """Create top control bar."""
        bar = QWidget()
        bar.setStyleSheet("background-color: #2a2a2a; padding: 5px; border: 1px solid #404040;")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # File selection
        self.file_label = QLabel("No video loaded")
        self.file_label.setStyleSheet("color: #ffffff; font-size: 12px;")
        layout.addWidget(self.file_label)
        
        load_btn = QPushButton("Load Video")
        load_btn.setStyleSheet("background-color: #0080ff; color: #ffffff; padding: 5px 15px; font-weight: bold;")
        load_btn.clicked.connect(self._load_video)
        layout.addWidget(load_btn)
        
        # Quick access to USB drive (E:)
        usb_btn = QPushButton("Browse USB (E:)")
        usb_btn.setStyleSheet("background-color: #00aa00; color: #ffffff; padding: 5px 15px;")
        usb_btn.clicked.connect(self._load_from_usb)
        layout.addWidget(usb_btn)
        
        layout.addStretch()
        
        # Playback speed selector
        speed_label = QLabel("Speed:")
        speed_label.setStyleSheet("color: #ffffff; font-size: 11px;")
        layout.addWidget(speed_label)
        
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.25x", "0.5x", "1x", "2x", "4x"])
        self.speed_combo.setCurrentIndex(2)  # 1x
        self.speed_combo.setStyleSheet("color: #ffffff; background-color: #2a2a2a; padding: 3px;")
        self.speed_combo.currentIndexChanged.connect(self._on_speed_changed)
        layout.addWidget(self.speed_combo)
        
        return bar
        
    def _create_video_display(self) -> QWidget:
        """Create video display widget."""
        group = QGroupBox("Video Display")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.video_label = QLabel("No video loaded")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(get_scaled_size(640), get_scaled_size(360))
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #000000;
                color: #606060;
                border: 2px solid #404040;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.video_label, stretch=1)
        
        return group
        
    def _create_playback_controls(self) -> QWidget:
        """Create playback control bar."""
        bar = QWidget()
        bar.setStyleSheet("background-color: #2a2a2a; padding: 5px; border: 1px solid #404040;")
        layout = QVBoxLayout(bar)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Progress slider
        slider_layout = QHBoxLayout()
        
        self.position_label = QLabel("00:00")
        self.position_label.setStyleSheet("color: #ffffff; font-size: 11px; min-width: 50px;")
        slider_layout.addWidget(self.position_label)
        
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background-color: #404040;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background-color: #0080ff;
                width: 16px;
                height: 16px;
                border-radius: 8px;
                margin: -5px 0;
            }
            QSlider::handle:horizontal:hover {
                background-color: #00a0ff;
            }
        """)
        self.progress_slider.sliderPressed.connect(self._on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self._on_slider_released)
        self.progress_slider.valueChanged.connect(self._on_slider_changed)
        slider_layout.addWidget(self.progress_slider, stretch=1)
        
        self.duration_label = QLabel("00:00")
        self.duration_label.setStyleSheet("color: #ffffff; font-size: 11px; min-width: 50px;")
        slider_layout.addWidget(self.duration_label)
        
        layout.addLayout(slider_layout)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        controls_layout.addStretch()
        
        # Rewind button
        self.rewind_btn = QPushButton("⏪ Rewind")
        self.rewind_btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 5px 15px;")
        self.rewind_btn.clicked.connect(self._rewind)
        controls_layout.addWidget(self.rewind_btn)
        
        # Play/Pause button
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.setStyleSheet("background-color: #00aa00; color: #ffffff; padding: 5px 20px; font-weight: bold;")
        self.play_btn.clicked.connect(self._toggle_play_pause)
        controls_layout.addWidget(self.play_btn)
        
        # Replay button
        self.replay_btn = QPushButton("⏮ Replay")
        self.replay_btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 5px 15px;")
        self.replay_btn.clicked.connect(self._replay)
        controls_layout.addWidget(self.replay_btn)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        return bar
        
    def _create_camera_section(self) -> QWidget:
        """Create USB camera capture section."""
        group = QGroupBox("USB Camera Capture")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Camera selection
        camera_layout = QHBoxLayout()
        camera_layout.addWidget(QLabel("Camera:"))
        
        self.camera_combo = QComboBox()
        self.camera_combo.setStyleSheet("color: #ffffff; background-color: #2a2a2a; padding: 3px;")
        self._update_camera_list()
        camera_layout.addWidget(self.camera_combo, stretch=1)
        
        refresh_cameras_btn = QPushButton("Refresh")
        refresh_cameras_btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 3px 10px;")
        refresh_cameras_btn.clicked.connect(self._update_camera_list)
        camera_layout.addWidget(refresh_cameras_btn)
        
        layout.addLayout(camera_layout)
        
        # Capture controls
        capture_layout = QHBoxLayout()
        
        self.start_capture_btn = QPushButton("Start Capture")
        self.start_capture_btn.setStyleSheet("background-color: #00aa00; color: #ffffff; padding: 5px 15px; font-weight: bold;")
        self.start_capture_btn.clicked.connect(self._start_capture)
        capture_layout.addWidget(self.start_capture_btn)
        
        self.stop_capture_btn = QPushButton("Stop Capture")
        self.stop_capture_btn.setStyleSheet("background-color: #aa0000; color: #ffffff; padding: 5px 15px;")
        self.stop_capture_btn.setEnabled(False)
        self.stop_capture_btn.clicked.connect(self._stop_capture)
        capture_layout.addWidget(self.stop_capture_btn)
        
        self.record_btn = QPushButton("Record")
        self.record_btn.setStyleSheet("background-color: #ff0000; color: #ffffff; padding: 5px 15px; font-weight: bold;")
        self.record_btn.clicked.connect(self._toggle_record)
        capture_layout.addWidget(self.record_btn)
        
        capture_layout.addStretch()
        
        layout.addLayout(capture_layout)
        
        return group
        
    def _update_camera_list(self) -> None:
        """Update camera combo box with detected cameras."""
        self.camera_combo.clear()
        
        if not self.camera_manager:
            self.camera_combo.addItem("No camera manager available")
            return
            
        cameras = self.camera_manager.list_cameras()
        if not cameras:
            self.camera_combo.addItem("No cameras detected")
            return
            
        for camera in cameras:
            self.camera_combo.addItem(f"{camera.model} ({camera.device_id})", camera.device_id)
            
    def _load_video(self) -> None:
        """Load a video file."""
        # Try to detect USB drives first
        import platform
        start_path = str(Path.home())
        
        if platform.system() == "Windows":
            # Check for USB drives (E:, F:, etc.)
            import string
            for drive_letter in string.ascii_uppercase:
                drive_path = Path(f"{drive_letter}:")
                if drive_path.exists() and drive_path.is_dir():
                    # Check if it's a removable drive
                    try:
                        import win32api
                        drive_type = win32api.GetDriveType(f"{drive_letter}:\\")
                        if drive_type == 2:  # DRIVE_REMOVABLE
                            start_path = str(drive_path)
                            break
                    except ImportError:
                        # Fallback: check common USB drive paths
                        if drive_letter in ['E', 'F', 'G', 'H']:
                            start_path = str(drive_path)
                            break
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Video File",
            start_path,
            "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv);;All Files (*)"
        )
        
        self._load_video_file(file_path)
        
    def _load_from_usb(self) -> None:
        """Load video from USB drive (E:)."""
        usb_path = Path("E:/DCIM/100ADVID")
        if not usb_path.exists():
            # Try alternative paths
            for alt_path in [Path("E:/"), Path("F:/"), Path("G:/")]:
                if alt_path.exists():
                    usb_path = alt_path
                    break
            else:
                QMessageBox.warning(self, "USB Not Found", "USB drive not found. Please use 'Load Video' to browse manually.")
                return
                
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Video from USB Drive",
            str(usb_path),
            "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv);;All Files (*)"
        )
        
        self._load_video_file(file_path)
        
    def _load_video_file(self, file_path: Optional[str]) -> None:
        """Internal method to load a video file."""
        if not file_path:
            return
            
        self.video_path = file_path
        self.file_label.setText(f"Video: {Path(file_path).name}")
        
        # Stop any existing playback
        if self.playback_thread:
            self.playback_thread.stop()
            self.playback_thread.wait()
            
        # Load video info
        if CV2_AVAILABLE:
            cap = cv2.VideoCapture(file_path)
            if cap.isOpened():
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
                duration_sec = total_frames / fps
                
                self.progress_slider.setMaximum(total_frames)
                self.duration_label.setText(self._format_time(duration_sec))
                
                # Show first frame
                ret, frame = cap.read()
                if ret:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb_frame.shape
                    bytes_per_line = ch * w
                    qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                    pixmap = QPixmap.fromImage(qt_image)
                    self.video_label.setPixmap(pixmap.scaled(
                        self.video_label.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    ))
                    
                cap.release()
                
    def _toggle_play_pause(self) -> None:
        """Toggle play/pause."""
        if not self.video_path:
            QMessageBox.warning(self, "No Video", "Please load a video file first.")
            return
            
        if not self.playback_thread:
            # Start new playback
            self.playback_thread = VideoPlayerThread(self.video_path)
            self.playback_thread.frame_ready.connect(self._on_frame_ready)
            self.playback_thread.playback_finished.connect(self._on_playback_finished)
            self.playback_thread.position_changed.connect(self._on_position_changed)
            self.playback_thread.start()
            
        if self.playback_thread.is_paused:
            self.playback_thread.is_paused = False
            self.playback_thread.is_playing = True
            self.play_btn.setText("⏸ Pause")
            self.play_btn.setStyleSheet("background-color: #ffaa00; color: #ffffff; padding: 5px 20px; font-weight: bold;")
        else:
            if not self.playback_thread.is_playing:
                self.playback_thread.is_playing = True
                self.play_btn.setText("⏸ Pause")
                self.play_btn.setStyleSheet("background-color: #ffaa00; color: #ffffff; padding: 5px 20px; font-weight: bold;")
            else:
                self.playback_thread.is_paused = True
                self.play_btn.setText("▶ Play")
                self.play_btn.setStyleSheet("background-color: #00aa00; color: #ffffff; padding: 5px 20px; font-weight: bold;")
                
    def _rewind(self) -> None:
        """Rewind 10 seconds."""
        if not self.playback_thread:
            return
            
        fps = self.playback_thread.fps
        frames_to_rewind = int(10 * fps)
        new_frame = max(0, self.playback_thread.current_frame - frames_to_rewind)
        self.playback_thread.set_position(new_frame)
        
    def _replay(self) -> None:
        """Restart video from beginning."""
        if not self.playback_thread:
            if self.video_path:
                self._toggle_play_pause()
            return
            
        self.playback_thread.set_position(0)
        if not self.playback_thread.is_playing:
            self._toggle_play_pause()
            
    def _on_speed_changed(self, index: int) -> None:
        """Handle playback speed change."""
        speeds = [0.25, 0.5, 1.0, 2.0, 4.0]
        if 0 <= index < len(speeds):
            speed = speeds[index]
            if self.playback_thread:
                self.playback_thread.set_playback_speed(speed)
                
    def _on_frame_ready(self, image: QImage) -> None:
        """Handle new frame from playback thread."""
        pixmap = QPixmap.fromImage(image)
        self.video_label.setPixmap(pixmap.scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))
        
    def _on_position_changed(self, frame: int) -> None:
        """Handle position change from playback thread."""
        if self.playback_thread:
            fps = self.playback_thread.fps
            time_sec = frame / fps
            self.position_label.setText(self._format_time(time_sec))
            self.progress_slider.setValue(frame)
            
    def _on_playback_finished(self) -> None:
        """Handle playback finished."""
        self.play_btn.setText("▶ Play")
        self.play_btn.setStyleSheet("background-color: #00aa00; color: #ffffff; padding: 5px 20px; font-weight: bold;")
        
    def _on_slider_pressed(self) -> None:
        """Handle slider pressed (seeking)."""
        pass
        
    def _on_slider_released(self) -> None:
        """Handle slider released (seek to position)."""
        if self.playback_thread:
            frame = self.progress_slider.value()
            self.playback_thread.set_position(frame)
            
    def _on_slider_changed(self, value: int) -> None:
        """Handle slider value changed."""
        pass
        
    def _start_capture(self) -> None:
        """Start capturing from USB camera."""
        if not CV2_AVAILABLE:
            QMessageBox.warning(self, "OpenCV Not Available", "OpenCV is required for camera capture.")
            return
            
        # Get camera ID from combo box
        camera_id = None
        current_index = self.camera_combo.currentIndex()
        if current_index >= 0:
            camera_id = self.camera_combo.itemData(current_index)
            if not camera_id:
                # Fallback: try to extract from text
                text = self.camera_combo.currentText()
                # Extract device ID from text like "Model (0)"
                import re
                match = re.search(r'\((\d+)\)', text)
                if match:
                    camera_id = match.group(1)
                    
        if not camera_id:
            QMessageBox.warning(self, "No Camera", "Please select a camera.")
            return
            
        if self.capture_thread:
            self._stop_capture()
            
        self.capture_thread = CameraCaptureThread(camera_id, width=1920, height=1080, fps=30)
        self.capture_thread.frame_ready.connect(self._on_capture_frame_ready)
        self.capture_thread.is_capturing = True
        self.capture_thread.start()
        
        self.start_capture_btn.setEnabled(False)
        self.stop_capture_btn.setEnabled(True)
        
    def _stop_capture(self) -> None:
        """Stop capturing from USB camera."""
        if self.capture_thread:
            self.capture_thread.stop()
            self.capture_thread.wait()
            self.capture_thread = None
            
        if self.is_recording and self.video_writer:
            self.video_writer.release()
            self.video_writer = None
            self.is_recording = False
            self.record_btn.setText("Record")
            self.record_btn.setStyleSheet("background-color: #ff0000; color: #ffffff; padding: 5px 15px; font-weight: bold;")
            
        self.start_capture_btn.setEnabled(True)
        self.stop_capture_btn.setEnabled(False)
        
    def _toggle_record(self) -> None:
        """Toggle video recording."""
        if not self.capture_thread or not self.capture_thread.is_capturing:
            QMessageBox.warning(self, "Not Capturing", "Please start camera capture first.")
            return
            
        if not self.is_recording:
            # Start recording
            output_path = QFileDialog.getSaveFileName(
                self,
                "Save Video",
                str(Path.home() / "captured_video.mp4"),
                "Video Files (*.mp4);;All Files (*)"
            )[0]
            
            if not output_path:
                return
                
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            self.video_writer = cv2.VideoWriter(output_path, fourcc, 30.0, (1920, 1080))
            
            if not self.video_writer.isOpened():
                QMessageBox.warning(self, "Error", "Failed to open video writer.")
                return
                
            self.is_recording = True
            self.record_btn.setText("Stop Recording")
            self.record_btn.setStyleSheet("background-color: #aa0000; color: #ffffff; padding: 5px 15px; font-weight: bold;")
        else:
            # Stop recording
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None
            self.is_recording = False
            self.record_btn.setText("Record")
            self.record_btn.setStyleSheet("background-color: #ff0000; color: #ffffff; padding: 5px 15px; font-weight: bold;")
            
    def _on_capture_frame_ready(self, image: QImage) -> None:
        """Handle new frame from camera capture."""
        pixmap = QPixmap.fromImage(image)
        self.video_label.setPixmap(pixmap.scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))
        
        # Record frame if recording
        if self.is_recording and self.video_writer and CV2_AVAILABLE:
            # Convert QImage to numpy array
            img = image.convertToFormat(QImage.Format.Format_RGB888)
            width = img.width()
            height = img.height()
            ptr = img.bits()
            ptr.setsize(img.sizeInBytes())
            arr = np.array(ptr).reshape((height, width, 3))
            # Convert RGB to BGR for OpenCV
            bgr_frame = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
            self.video_writer.write(bgr_frame)
            
    def _format_time(self, seconds: float) -> str:
        """Format time in MM:SS format."""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
        
    def closeEvent(self, event) -> None:
        """Cleanup on close."""
        if self.playback_thread:
            self.playback_thread.stop()
            self.playback_thread.wait()
        if self.capture_thread:
            self.capture_thread.stop()
            self.capture_thread.wait()
        if self.video_writer:
            self.video_writer.release()
        event.accept()


__all__ = ["VideoPlayerTab"]

