"""
Video/Overlay Tab
Dedicated tab for video logging and telemetry overlay configuration
"""

from __future__ import annotations

from typing import Dict, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QCheckBox,
    QComboBox,
    QSpinBox,
    QSizePolicy,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size

try:
    from services.video_logger import VideoLogger
    from services.video_overlay import VideoOverlay
except ImportError:
    VideoLogger = None
    VideoOverlay = None


class VideoOverlayTab(QWidget):
    """Video/Overlay tab for video logging and telemetry overlay."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.video_logger: Optional[VideoLogger] = None
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup video/overlay tab UI."""
        main_layout = QVBoxLayout(self)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        self.setStyleSheet("background-color: #1a1a1a;")
        
        # Control bar
        control_bar = self._create_control_bar()
        main_layout.addWidget(control_bar)
        
        # Content layout
        content_layout = QHBoxLayout()
        content_layout.setSpacing(get_scaled_size(15))
        
        # Left: Recording settings
        left_panel = self._create_recording_panel()
        content_layout.addWidget(left_panel, stretch=1)
        
        # Center: Overlay preview and settings
        center_panel = self._create_overlay_panel()
        content_layout.addWidget(center_panel, stretch=2)
        
        # Right: Output settings
        right_panel = self._create_output_panel()
        content_layout.addWidget(right_panel, stretch=1)
        
        main_layout.addLayout(content_layout, stretch=1)
        
        # Graphing tab
        from PySide6.QtWidgets import QTabWidget
        bottom_tabs = QTabWidget()
        bottom_tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #404040; background-color: #1a1a1a; }
            QTabBar::tab { background-color: #2a2a2a; color: #ffffff; padding: 6px 12px; }
            QTabBar::tab:selected { background-color: #1a1a1a; border-bottom: 2px solid #0080ff; }
        """)
        
        # Graphing tab
        from ui.module_feature_helper import add_graphing_tab
        graph_widget = add_graphing_tab(bottom_tabs, "Video Overlay")
        self.video_graph = graph_widget
        
        # Import/Export tab
        from ui.module_feature_helper import add_import_export_tab
        add_import_export_tab(bottom_tabs, "Video Overlay")
        
        main_layout.addWidget(bottom_tabs, stretch=1)
        
    def _create_control_bar(self) -> QWidget:
        """Create control bar."""
        bar = QWidget()
        padding = get_scaled_size(5)
        border = get_scaled_size(1)
        bar.setStyleSheet(f"background-color: #2a2a2a; padding: {padding}px; border: {border}px solid #404040;")
        layout = QHBoxLayout(bar)
        margin_h = get_scaled_size(10)
        margin_v = get_scaled_size(5)
        layout.setContentsMargins(margin_h, margin_v, margin_h, margin_v)
        
        title = QLabel("Video Logger & Overlay")
        title_font = get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Start recording button
        self.start_rec_btn = QPushButton("Start Recording")
        btn_padding_v = get_scaled_size(5)
        btn_padding_h = get_scaled_size(10)
        btn_font = get_scaled_font_size(11)
        self.start_rec_btn.setStyleSheet(f"background-color: #ff0000; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px; font-weight: bold; font-size: {btn_font}px;")
        layout.addWidget(self.start_rec_btn)
        
        # Stop recording button
        self.stop_rec_btn = QPushButton("Stop Recording")
        self.stop_rec_btn.setStyleSheet(f"background-color: #404040; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px; font-size: {btn_font}px;")
        layout.addWidget(self.stop_rec_btn)
        
        return bar
        
    def _create_recording_panel(self) -> QWidget:
        """Create recording settings panel."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        panel.setMaximumWidth(get_scaled_size(250))
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(15)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # Recording settings
        rec_group = QGroupBox("Recording Settings")
        group_font = get_scaled_font_size(12)
        group_border = get_scaled_size(1)
        group_radius = get_scaled_size(3)
        group_margin = get_scaled_size(10)
        rec_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        rec_layout = QVBoxLayout()
        rec_layout.setSpacing(get_scaled_size(10))
        
        # FPS
        rec_layout.addWidget(QLabel("Frame Rate (FPS):"))
        self.fps = QSpinBox()
        self.fps.setRange(15, 60)
        self.fps.setValue(30)
        self.fps.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        rec_layout.addWidget(self.fps)
        
        # Resolution
        rec_layout.addWidget(QLabel("Resolution:"))
        self.resolution = QComboBox()
        self.resolution.addItems(["720p", "1080p", "1440p", "4K"])
        self.resolution.setCurrentIndex(1)
        self.resolution.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        rec_layout.addWidget(self.resolution)
        
        # Auto-start
        self.auto_start = QCheckBox("Auto-Start on Run")
        self.auto_start.setChecked(False)
        self.auto_start.setStyleSheet("color: #ffffff;")
        rec_layout.addWidget(self.auto_start)
        
        rec_group.setLayout(rec_layout)
        layout.addWidget(rec_group)
        
        # Status
        status_group = QGroupBox("Recording Status")
        status_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("Not Recording")
        status_font = get_scaled_font_size(14)
        self.status_label.setStyleSheet(f"font-size: {status_font}px; font-weight: bold; color: #ffaa00; padding: {get_scaled_size(5)}px;")
        status_layout.addWidget(self.status_label)
        
        self.duration_label = QLabel("Duration: 0:00")
        duration_font = get_scaled_font_size(11)
        self.duration_label.setStyleSheet(f"font-size: {duration_font}px; color: #9aa0a6;")
        status_layout.addWidget(self.duration_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        layout.addStretch()
        return panel
        
    def _create_overlay_panel(self) -> QWidget:
        """Create overlay settings panel."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        # Overlay settings
        overlay_group = QGroupBox("Telemetry Overlay Settings")
        group_font = get_scaled_font_size(12)
        group_border = get_scaled_size(1)
        group_radius = get_scaled_size(3)
        group_margin = get_scaled_size(10)
        overlay_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        overlay_layout = QVBoxLayout()
        overlay_layout.setSpacing(get_scaled_size(10))
        
        # Enable overlay
        self.enable_overlay = QCheckBox("Enable Telemetry Overlay")
        self.enable_overlay.setChecked(True)
        self.enable_overlay.setStyleSheet("color: #ffffff;")
        self.enable_overlay.toggled.connect(self._update_preview)
        overlay_layout.addWidget(self.enable_overlay)
        
        # Overlay style
        overlay_layout.addWidget(QLabel("Overlay Style:"))
        self.overlay_style = QComboBox()
        self.overlay_style.addItems(["Racing", "Minimal", "Classic", "Modern"])
        self.overlay_style.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        self.overlay_style.currentTextChanged.connect(self._update_preview)
        overlay_layout.addWidget(self.overlay_style)
        
        # Widget selection
        overlay_layout.addWidget(QLabel("Display Widgets:"))
        widgets_layout = QVBoxLayout()
        
        self.show_rpm = QCheckBox("RPM")
        self.show_rpm.setChecked(True)
        self.show_rpm.setStyleSheet("color: #ffffff;")
        self.show_rpm.toggled.connect(self._update_preview)
        widgets_layout.addWidget(self.show_rpm)
        
        self.show_speed = QCheckBox("Speed")
        self.show_speed.setChecked(True)
        self.show_speed.setStyleSheet("color: #ffffff;")
        self.show_speed.toggled.connect(self._update_preview)
        widgets_layout.addWidget(self.show_speed)
        
        self.show_boost = QCheckBox("Boost")
        self.show_boost.setChecked(True)
        self.show_boost.setStyleSheet("color: #ffffff;")
        self.show_boost.toggled.connect(self._update_preview)
        widgets_layout.addWidget(self.show_boost)
        
        self.show_afr = QCheckBox("AFR")
        self.show_afr.setChecked(True)
        self.show_afr.setStyleSheet("color: #ffffff;")
        self.show_afr.toggled.connect(self._update_preview)
        widgets_layout.addWidget(self.show_afr)
        
        # Additional widgets
        self.show_lap_time = QCheckBox("Lap Time")
        self.show_lap_time.setChecked(False)
        self.show_lap_time.setStyleSheet("color: #ffffff;")
        self.show_lap_time.toggled.connect(self._update_preview)
        widgets_layout.addWidget(self.show_lap_time)
        
        self.show_throttle = QCheckBox("Throttle")
        self.show_throttle.setChecked(False)
        self.show_throttle.setStyleSheet("color: #ffffff;")
        self.show_throttle.toggled.connect(self._update_preview)
        widgets_layout.addWidget(self.show_throttle)
        
        self.show_coolant = QCheckBox("Coolant Temp")
        self.show_coolant.setChecked(False)
        self.show_coolant.setStyleSheet("color: #ffffff;")
        self.show_coolant.toggled.connect(self._update_preview)
        widgets_layout.addWidget(self.show_coolant)
        
        overlay_layout.addLayout(widgets_layout)
        
        overlay_group.setLayout(overlay_layout)
        layout.addWidget(overlay_group)
        
        # Video preview with overlay
        preview_group = QGroupBox("Live Preview")
        preview_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        preview_layout = QVBoxLayout()
        
        from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
        from PySide6.QtGui import QImage, QPixmap, QPainter
        from PySide6.QtCore import QTimer
        
        # Video preview widget
        self.preview_view = QGraphicsView()
        self.preview_scene = QGraphicsScene()
        self.preview_view.setScene(self.preview_scene)
        self.preview_view.setStyleSheet("background-color: #000000; border: 1px solid #404040;")
        self.preview_view.setMinimumHeight(get_scaled_size(200))
        preview_layout.addWidget(self.preview_view)
        
        # Preview controls
        preview_controls = QHBoxLayout()
        
        self.preview_enable = QCheckBox("Enable Preview")
        self.preview_enable.setChecked(True)
        self.preview_enable.setStyleSheet("color: #ffffff;")
        preview_controls.addWidget(self.preview_enable)
        
        preview_controls.addStretch()
        
        # Refresh preview button
        refresh_btn = QPushButton("Refresh Preview")
        refresh_btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 5px;")
        refresh_btn.clicked.connect(self._refresh_preview)
        preview_controls.addWidget(refresh_btn)
        
        preview_layout.addLayout(preview_controls)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group, stretch=1)
        
        # Preview update timer
        self.preview_timer = QTimer(self)
        self.preview_timer.timeout.connect(self._update_preview)
        if self.preview_enable.isChecked():
            self.preview_timer.start(100)  # 10 FPS preview
        
        return panel
        
    def _create_output_panel(self) -> QWidget:
        """Create output settings panel."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        panel.setMaximumWidth(get_scaled_size(250))
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(15)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # Output settings
        output_group = QGroupBox("Output Settings")
        group_font = get_scaled_font_size(12)
        group_border = get_scaled_size(1)
        group_radius = get_scaled_size(3)
        group_margin = get_scaled_size(10)
        output_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        output_layout = QVBoxLayout()
        output_layout.setSpacing(get_scaled_size(10))
        
        # Output directory
        output_layout.addWidget(QLabel("Output Directory:"))
        from PySide6.QtWidgets import QLineEdit
        self.output_dir = QLineEdit("logs/video")
        self.output_dir.setStyleSheet("color: #ffffff; background-color: #2a2a2a; padding: 5px;")
        output_layout.addWidget(self.output_dir)
        
        # Browse button
        browse_btn = QPushButton("Browse...")
        browse_btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 5px;")
        output_layout.addWidget(browse_btn)
        
        # Sync telemetry
        self.sync_telemetry = QCheckBox("Sync with Telemetry Data")
        self.sync_telemetry.setChecked(True)
        self.sync_telemetry.setStyleSheet("color: #ffffff;")
        output_layout.addWidget(self.sync_telemetry)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        layout.addStretch()
        return panel
        
    def _refresh_preview(self) -> None:
        """Refresh preview display."""
        self._update_preview()
        
    def _update_preview(self) -> None:
        """Update preview with current overlay settings."""
        if not self.preview_enable.isChecked():
            return
            
        try:
            from services.video_overlay import VideoOverlay, OverlayStyle, TelemetryData
            import numpy as np
            
            # Create test frame
            test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            test_frame.fill(50)  # Dark gray background
            
            # Create overlay
            style_map = {
                "Racing": OverlayStyle.RACING,
                "Minimal": OverlayStyle.MINIMAL,
                "Classic": OverlayStyle.CLASSIC,
                "Modern": OverlayStyle.MODERN,
            }
            style = style_map.get(self.overlay_style.currentText(), OverlayStyle.RACING)
            
            enabled_widgets = []
            if self.show_rpm.isChecked():
                enabled_widgets.append("rpm")
            if self.show_speed.isChecked():
                enabled_widgets.append("speed")
            if self.show_boost.isChecked():
                enabled_widgets.append("boost")
            if self.show_afr.isChecked():
                enabled_widgets.append("afr")
                
            overlay = VideoOverlay(style=style, enabled_widgets=enabled_widgets if enabled_widgets else None)
            
            # Create test telemetry
            test_telemetry = TelemetryData(
                speed_mph=125.5,
                rpm=6500.0,
                boost_psi=28.5,
                throttle=95.0,
                coolant_temp=195.0,
                lap_time=125.432,
                lap_number=5,
            )
            
            # Render overlay
            if self.enable_overlay.isChecked():
                overlay_frame = overlay.render(test_frame, test_telemetry)
            else:
                overlay_frame = test_frame
            
            # Convert to QPixmap
            height, width, channel = overlay_frame.shape
            bytes_per_line = 3 * width
            q_image = QImage(overlay_frame.data, width, height, bytes_per_line, QImage.Format.Format_BGR888)
            pixmap = QPixmap.fromImage(q_image)
            
            # Update scene
            self.preview_scene.clear()
            self.preview_scene.addPixmap(pixmap)
            self.preview_view.fitInView(self.preview_scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
            
        except Exception as e:
            # Show placeholder if preview fails
            from PySide6.QtWidgets import QGraphicsTextItem
            self.preview_scene.clear()
            text = QGraphicsTextItem("Preview Unavailable\n(Enable overlay and select widgets)")
            text.setDefaultTextColor(Qt.GlobalColor.white)
            self.preview_scene.addItem(text)
            
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update video/overlay tab with telemetry data."""
        if self.video_logger and hasattr(self.video_logger, 'update_telemetry'):
            try:
                self.video_logger.update_telemetry(data)
            except Exception:
                pass
        # Update preview if enabled
        if self.preview_enable.isChecked():
            self._update_preview()


__all__ = ["VideoOverlayTab"]



