"""
Track Learning AI Tab
Dedicated tab for AI track learning and optimal racing line
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
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size

try:
    from services.track_learning_ai import TrackLearningAI, TrackProfile
except ImportError:
    TrackLearningAI = None
    TrackProfile = None


class TrackLearningTab(QWidget):
    """Track Learning AI tab with track profiles and optimal lines."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.track_ai: Optional[TrackLearningAI] = None
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup track learning tab UI."""
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
        
        # Left: Track list and settings
        left_panel = self._create_tracks_panel()
        content_layout.addWidget(left_panel, stretch=1)
        
        # Center: Track map and optimal line
        center_panel = self._create_map_panel()
        content_layout.addWidget(center_panel, stretch=2)
        
        # Right: Learning stats and recommendations
        right_panel = self._create_stats_panel()
        content_layout.addWidget(right_panel, stretch=1)
        
        main_layout.addLayout(content_layout, stretch=1)
        
        # Import/Export bar
        from ui.module_feature_helper import add_import_export_bar
        add_import_export_bar(self, main_layout)
        
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
        
        title = QLabel("Track Learning AI")
        title_font = get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Start learning button
        self.start_learning_btn = QPushButton("Start Learning")
        btn_padding_v = get_scaled_size(5)
        btn_padding_h = get_scaled_size(10)
        btn_font = get_scaled_font_size(11)
        self.start_learning_btn.setStyleSheet(f"background-color: #00ff00; color: #000000; padding: {btn_padding_v}px {btn_padding_h}px; font-weight: bold; font-size: {btn_font}px;")
        layout.addWidget(self.start_learning_btn)
        
        # Stop learning button
        self.stop_learning_btn = QPushButton("Stop Learning")
        self.stop_learning_btn.setStyleSheet(f"background-color: #ff0000; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px; font-size: {btn_font}px;")
        layout.addWidget(self.stop_learning_btn)
        
        return bar
        
    def _create_tracks_panel(self) -> QWidget:
        """Create tracks panel."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        panel.setMaximumWidth(get_scaled_size(250))
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(15)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # Track list
        tracks_group = QGroupBox("Learned Tracks")
        group_font = get_scaled_font_size(12)
        group_border = get_scaled_size(1)
        group_radius = get_scaled_size(3)
        group_margin = get_scaled_size(10)
        tracks_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        tracks_layout = QVBoxLayout()
        
        self.track_list = QListWidget()
        self.track_list.setStyleSheet("""
            QListWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                border: 1px solid #404040;
            }
        """)
        tracks_layout.addWidget(self.track_list)
        
        tracks_group.setLayout(tracks_layout)
        layout.addWidget(tracks_group)
        
        # Learning settings
        settings_group = QGroupBox("Learning Settings")
        settings_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(get_scaled_size(10))
        
        # Auto-learn
        from PySide6.QtWidgets import QCheckBox
        self.auto_learn = QCheckBox("Auto-Learn on Track")
        self.auto_learn.setChecked(True)
        self.auto_learn.setStyleSheet("color: #ffffff;")
        settings_layout.addWidget(self.auto_learn)
        
        # Confidence threshold
        settings_layout.addWidget(QLabel("Confidence Threshold:"))
        self.confidence = QComboBox()
        self.confidence.addItems(["Low (1 lap)", "Medium (3 laps)", "High (5+ laps)"])
        self.confidence.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.confidence)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        return panel
        
    def _create_map_panel(self) -> QWidget:
        """Create track map panel."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        # Track map placeholder
        map_label = QLabel("Track Map & Optimal Racing Line")
        map_font = get_scaled_font_size(14)
        map_label.setStyleSheet(f"font-size: {map_font}px; font-weight: bold; color: #ffffff; padding: {get_scaled_size(20)}px;")
        map_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(map_label, stretch=1)
        
        # Braking points
        braking_group = QGroupBox("Braking Points")
        group_font = get_scaled_font_size(12)
        group_border = get_scaled_size(1)
        group_radius = get_scaled_size(3)
        group_margin = get_scaled_size(10)
        braking_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        braking_layout = QVBoxLayout()
        
        self.braking_label = QLabel("No track selected")
        braking_font = get_scaled_font_size(11)
        self.braking_label.setStyleSheet(f"font-size: {braking_font}px; color: #9aa0a6;")
        self.braking_label.setWordWrap(True)
        braking_layout.addWidget(self.braking_label)
        
        braking_group.setLayout(braking_layout)
        layout.addWidget(braking_group)
        
        return panel
        
    def _create_stats_panel(self) -> QWidget:
        """Create stats panel."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        panel.setMaximumWidth(get_scaled_size(250))
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(15)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # Learning stats
        stats_group = QGroupBox("Learning Statistics")
        group_font = get_scaled_font_size(12)
        group_border = get_scaled_size(1)
        group_radius = get_scaled_size(3)
        group_margin = get_scaled_size(10)
        stats_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(get_scaled_size(8))
        
        self.laps_label = QLabel("Laps Learned: 0")
        stats_font = get_scaled_font_size(11)
        self.laps_label.setStyleSheet(f"font-size: {stats_font}px; color: #ffffff;")
        stats_layout.addWidget(self.laps_label)
        
        self.confidence_label = QLabel("Confidence: 0%")
        self.confidence_label.setStyleSheet(f"font-size: {stats_font}px; color: #ffffff;")
        stats_layout.addWidget(self.confidence_label)
        
        self.optimal_time_label = QLabel("Optimal Lap: --")
        self.optimal_time_label.setStyleSheet(f"font-size: {stats_font}px; color: #ffffff;")
        stats_layout.addWidget(self.optimal_time_label)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Recommendations
        rec_group = QGroupBox("Recommendations")
        rec_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        rec_layout = QVBoxLayout()
        
        self.rec_label = QLabel("Start learning a track to get recommendations")
        rec_font = get_scaled_font_size(10)
        self.rec_label.setStyleSheet(f"font-size: {rec_font}px; color: #9aa0a6;")
        self.rec_label.setWordWrap(True)
        rec_layout.addWidget(self.rec_label)
        
        rec_group.setLayout(rec_layout)
        layout.addWidget(rec_group)
        
        layout.addStretch()
        return panel
        
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update track learning tab with telemetry data."""
        if not self.track_ai:
            if TrackLearningAI:
                try:
                    self.track_ai = TrackLearningAI()
                except Exception:
                    pass
        
        # Update learning if active
        if self.track_ai and self.auto_learn.isChecked():
            # Process GPS and telemetry for track learning
            pass


__all__ = ["TrackLearningTab"]



