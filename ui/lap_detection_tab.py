"""
Lap Detection & Track Map Tab
Real-time GPS track visualization, lap detection, and lap time tracking
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import QColor, QPen, QBrush, QPainter, QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSpinBox,
    QDoubleSpinBox,
    QLineEdit,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsTextItem,
    QGraphicsPathItem,
    QGraphicsItem,
    QSplitter,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size
from ui.racing_ui_theme import get_racing_theme, RacingColor

LOGGER = logging.getLogger(__name__)

try:
    from services.lap_detector import LapDetector, Lap, TrackPoint
    from interfaces.gps_interface import GPSInterface
except ImportError:
    LapDetector = None
    Lap = None
    TrackPoint = None
    GPSInterface = None


class TrackMapWidget(QGraphicsView):
    """Interactive track map widget showing GPS path and lap markers."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        
        # Track data
        self.track_points: List[TrackPoint] = []
        self.laps: List[Lap] = []
        self.current_lap: Optional[Lap] = None
        self.start_finish_pos: Optional[Tuple[float, float]] = None
        self.sector_markers: List[Tuple[float, float]] = []
        
        # Display settings
        self.show_path = True
        self.show_laps = True
        self.show_sectors = True
        self.show_start_finish = True
        
        # Color scheme
        self.path_color = QColor(0, 255, 0)  # Green
        self.lap_color = QColor(0, 255, 255)  # Cyan
        self.best_lap_color = QColor(255, 255, 0)  # Yellow
        self.start_finish_color = QColor(255, 0, 0)  # Red
        self.sector_color = QColor(255, 165, 0)  # Orange
        
        # Graphics items
        self.path_item: Optional[QGraphicsPathItem] = None
        self.lap_items: List[QGraphicsItem] = []
        self.start_finish_item: Optional[QGraphicsEllipseItem] = None
        
        self.setStyleSheet("background-color: #0a0a0a; border: 1px solid #404040;")
        
    def update_track(self, track_points: List[TrackPoint], laps: List[Lap], current_lap: Optional[Lap]) -> None:
        """Update track map with new data."""
        self.track_points = track_points
        self.laps = laps
        self.current_lap = current_lap
        self._redraw()
        
    def set_start_finish(self, lat: float, lon: float) -> None:
        """Set start/finish line position."""
        self.start_finish_pos = (lat, lon)
        self._redraw()
        
    def set_sector_markers(self, markers: List[Tuple[float, float]]) -> None:
        """Set sector marker positions."""
        self.sector_markers = markers
        self._redraw()
        
    def _redraw(self) -> None:
        """Redraw the track map."""
        self.scene.clear()
        self.lap_items.clear()
        
        if not self.track_points:
            return
            
        # Calculate bounds
        lats = [p.latitude for p in self.track_points]
        lons = [p.longitude for p in self.track_points]
        
        if not lats or not lons:
            return
            
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
        
        # Add padding
        lat_range = max_lat - min_lat
        lon_range = max_lon - min_lon
        padding = max(lat_range, lon_range) * 0.1
        
        min_lat -= padding
        max_lat += padding
        min_lon -= padding
        max_lon += padding
        
        # Get view size
        view_rect = self.viewport().rect()
        width = view_rect.width()
        height = view_rect.height()
        
        # Scale factors
        scale_x = width / (max_lon - min_lon) if max_lon != min_lon else 1
        scale_y = height / (max_lat - min_lat) if max_lat != min_lat else 1
        
        def to_scene(lat: float, lon: float) -> QPointF:
            """Convert GPS coordinates to scene coordinates."""
            x = (lon - min_lon) * scale_x
            y = height - (lat - min_lat) * scale_y  # Flip Y axis
            return QPointF(x, y)
        
        # Draw track path
        if self.show_path and len(self.track_points) > 1:
            from PySide6.QtGui import QPainterPath
            path = QPainterPath()
            first_point = to_scene(self.track_points[0].latitude, self.track_points[0].longitude)
            path.moveTo(first_point)
            
            for point in self.track_points[1:]:
                scene_point = to_scene(point.latitude, point.longitude)
                path.lineTo(scene_point)
                
            pen = QPen(self.path_color, 2)
            self.path_item = QGraphicsPathItem(path)
            self.path_item.setPen(pen)
            self.scene.addItem(self.path_item)
        
        # Draw start/finish line
        if self.show_start_finish and self.start_finish_pos:
            lat, lon = self.start_finish_pos
            center = to_scene(lat, lon)
            radius = 10
            circle = QGraphicsEllipseItem(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
            circle.setPen(QPen(self.start_finish_color, 2))
            circle.setBrush(QBrush(self.start_finish_color))
            self.scene.addItem(circle)
            
            # Label
            label = QGraphicsTextItem("S/F")
            label.setDefaultTextColor(self.start_finish_color)
            label.setPos(center.x() + radius + 5, center.y() - 10)
            self.scene.addItem(label)
        
        # Draw sector markers
        if self.show_sectors:
            for i, (lat, lon) in enumerate(self.sector_markers):
                center = to_scene(lat, lon)
                radius = 8
                circle = QGraphicsEllipseItem(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
                circle.setPen(QPen(self.sector_color, 2))
                circle.setBrush(QBrush(self.sector_color))
                self.scene.addItem(circle)
                
                label = QGraphicsTextItem(f"S{i+1}")
                label.setDefaultTextColor(self.sector_color)
                label.setPos(center.x() + radius + 5, center.y() - 10)
                self.scene.addItem(label)
        
        # Draw laps
        if self.show_laps:
            best_lap = None
            if self.laps:
                best_lap = min(self.laps, key=lambda l: l.duration or float('inf'))
            
            for lap in self.laps:
                if not lap.start_lat or not lap.start_lon:
                    continue
                    
                # Get lap points
                lap_points = [p for p in self.track_points 
                             if lap.start_time <= p.timestamp <= (lap.end_time or float('inf'))]
                
                if len(lap_points) < 2:
                    continue
                
                # Draw lap path
                from PySide6.QtGui import QPainterPath
                lap_path = QPainterPath()
                first = to_scene(lap_points[0].latitude, lap_points[0].longitude)
                lap_path.moveTo(first)
                
                for point in lap_points[1:]:
                    scene_point = to_scene(point.latitude, point.longitude)
                    lap_path.lineTo(scene_point)
                
                # Use different color for best lap
                color = self.best_lap_color if lap == best_lap else self.lap_color
                pen = QPen(color, 3)
                lap_item = QGraphicsPathItem(lap_path)
                lap_item.setPen(pen)
                self.scene.addItem(lap_item)
                self.lap_items.append(lap_item)
        
        # Draw current lap
        if self.current_lap:
            current_points = [p for p in self.track_points 
                            if p.timestamp >= self.current_lap.start_time]
            
            if len(current_points) > 1:
                from PySide6.QtGui import QPainterPath
                current_path = QPainterPath()
                first = to_scene(current_points[0].latitude, current_points[0].longitude)
                current_path.moveTo(first)
                
                for point in current_points[1:]:
                    scene_point = to_scene(point.latitude, point.longitude)
                    current_path.lineTo(scene_point)
                
                pen = QPen(QColor(255, 255, 255), 4)  # White for current lap
                current_item = QGraphicsPathItem(current_path)
                current_item.setPen(pen)
                self.scene.addItem(current_item)
        
        # Fit scene to view
        self.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)


class LapDetectionTab(QWidget):
    """Lap Detection & Track Map tab."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.lap_detector: Optional[LapDetector] = None
        self.gps_interface: Optional[GPSInterface] = None
        
        # Update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(100)  # 10 Hz update
        
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup lap detection tab UI."""
        main_layout = QVBoxLayout(self)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        theme = get_racing_theme()
        self.setStyleSheet(f"background-color: {theme.bg_primary};")
        
        # Control bar
        control_bar = self._create_control_bar()
        main_layout.addWidget(control_bar)
        
        # Splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Settings and lap list
        left_panel = self._create_settings_panel()
        splitter.addWidget(left_panel)
        
        # Center: Track map
        center_panel = self._create_map_panel()
        splitter.addWidget(center_panel)
        
        # Right: Lap times and statistics
        right_panel = self._create_stats_panel()
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 1)
        
        main_layout.addWidget(splitter, stretch=1)
        
    def _create_control_bar(self) -> QWidget:
        """Create control bar."""
        bar = QWidget()
        theme = get_racing_theme()
        padding = get_scaled_size(5)
        bar.setStyleSheet(f"background-color: {theme.bg_secondary}; padding: {padding}px; border: 1px solid {theme.border_default};")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(get_scaled_size(10), padding, get_scaled_size(10), padding)
        
        title = QLabel("Lap Detection & Track Map")
        title_font = get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: {theme.text_primary};")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Start detection button
        self.start_btn = QPushButton("Start Detection")
        btn_font = get_scaled_font_size(11)
        self.start_btn.setStyleSheet(f"background-color: {theme.status_optimal}; color: #000000; padding: 5px 10px; font-weight: bold; font-size: {btn_font}px;")
        self.start_btn.clicked.connect(self._start_detection)
        layout.addWidget(self.start_btn)
        
        # Stop detection button
        self.stop_btn = QPushButton("Stop Detection")
        self.stop_btn.setStyleSheet(f"background-color: {theme.status_critical}; color: #ffffff; padding: 5px 10px; font-size: {btn_font}px;")
        self.stop_btn.clicked.connect(self._stop_detection)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)
        
        # Reset button
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setStyleSheet(f"background-color: {theme.bg_tertiary}; color: {theme.text_primary}; padding: 5px 10px; font-size: {btn_font}px;")
        self.reset_btn.clicked.connect(self._reset_session)
        layout.addWidget(self.reset_btn)
        
        return bar
        
    def _create_settings_panel(self) -> QWidget:
        """Create settings panel."""
        panel = QWidget()
        theme = get_racing_theme()
        panel.setStyleSheet(f"background-color: {theme.bg_secondary}; border: 1px solid {theme.border_default};")
        panel.setMaximumWidth(get_scaled_size(300))
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(get_scaled_size(10), get_scaled_size(10), get_scaled_size(10), get_scaled_size(10))
        layout.setSpacing(get_scaled_size(15))
        
        # Start/Finish line settings
        sf_group = QGroupBox("Start/Finish Line")
        sf_layout = QVBoxLayout()
        
        sf_layout.addWidget(QLabel("Latitude:"))
        self.sf_lat = QDoubleSpinBox()
        self.sf_lat.setRange(-90, 90)
        self.sf_lat.setDecimals(6)
        self.sf_lat.setStyleSheet(f"color: {theme.text_primary}; background-color: {theme.bg_tertiary};")
        sf_layout.addWidget(self.sf_lat)
        
        sf_layout.addWidget(QLabel("Longitude:"))
        self.sf_lon = QDoubleSpinBox()
        self.sf_lon.setRange(-180, 180)
        self.sf_lon.setDecimals(6)
        self.sf_lon.setStyleSheet(f"color: {theme.text_primary}; background-color: {theme.bg_tertiary};")
        sf_layout.addWidget(self.sf_lon)
        
        # Use current GPS button
        use_gps_btn = QPushButton("Use Current GPS")
        use_gps_btn.setStyleSheet(f"background-color: {theme.bg_tertiary}; color: {theme.text_primary}; padding: 5px;")
        use_gps_btn.clicked.connect(self._use_current_gps)
        sf_layout.addWidget(use_gps_btn)
        
        sf_group.setLayout(sf_layout)
        layout.addWidget(sf_group)
        
        # Detection settings
        det_group = QGroupBox("Detection Settings")
        det_layout = QVBoxLayout()
        
        det_layout.addWidget(QLabel("Detection Radius (m):"))
        self.detection_radius = QDoubleSpinBox()
        self.detection_radius.setRange(10, 500)
        self.detection_radius.setValue(50)
        self.detection_radius.setSuffix(" m")
        self.detection_radius.setStyleSheet(f"color: {theme.text_primary}; background-color: {theme.bg_tertiary};")
        det_layout.addWidget(self.detection_radius)
        
        det_layout.addWidget(QLabel("Min Lap Time (s):"))
        self.min_lap_time = QDoubleSpinBox()
        self.min_lap_time.setRange(10, 300)
        self.min_lap_time.setValue(30)
        self.min_lap_time.setSuffix(" s")
        self.min_lap_time.setStyleSheet(f"color: {theme.text_primary}; background-color: {theme.bg_tertiary};")
        det_layout.addWidget(self.min_lap_time)
        
        det_group.setLayout(det_layout)
        layout.addWidget(det_group)
        
        layout.addStretch()
        return panel
        
    def _create_map_panel(self) -> QWidget:
        """Create track map panel."""
        panel = QWidget()
        theme = get_racing_theme()
        panel.setStyleSheet(f"background-color: {theme.bg_secondary}; border: 1px solid {theme.border_default};")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(get_scaled_size(10), get_scaled_size(10), get_scaled_size(10), get_scaled_size(10))
        
        # Track map widget
        self.track_map = TrackMapWidget()
        layout.addWidget(self.track_map)
        
        # Status label
        self.map_status_label = QLabel("No GPS data")
        status_font = get_scaled_font_size(12)
        self.map_status_label.setStyleSheet(f"font-size: {status_font}px; color: {theme.text_secondary}; padding: 5px;")
        self.map_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.map_status_label)
        
        return panel
        
    def _create_stats_panel(self) -> QWidget:
        """Create statistics panel."""
        panel = QWidget()
        theme = get_racing_theme()
        panel.setStyleSheet(f"background-color: {theme.bg_secondary}; border: 1px solid {theme.border_default};")
        panel.setMaximumWidth(get_scaled_size(300))
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(get_scaled_size(10), get_scaled_size(10), get_scaled_size(10), get_scaled_size(10))
        layout.setSpacing(get_scaled_size(15))
        
        # Current lap info
        current_group = QGroupBox("Current Lap")
        current_layout = QVBoxLayout()
        
        self.current_lap_time_label = QLabel("Lap Time: --:--.---")
        current_font = get_scaled_font_size(16)
        self.current_lap_time_label.setStyleSheet(f"font-size: {current_font}px; font-weight: bold; color: {theme.accent_neon_blue};")
        current_layout.addWidget(self.current_lap_time_label)
        
        self.current_lap_number_label = QLabel("Lap #: --")
        self.current_lap_number_label.setStyleSheet(f"font-size: {get_scaled_font_size(12)}px; color: {theme.text_secondary};")
        current_layout.addWidget(self.current_lap_number_label)
        
        current_group.setLayout(current_layout)
        layout.addWidget(current_group)
        
        # Best lap info
        best_group = QGroupBox("Best Lap")
        best_layout = QVBoxLayout()
        
        self.best_lap_time_label = QLabel("Time: --:--.---")
        best_font = get_scaled_font_size(14)
        self.best_lap_time_label.setStyleSheet(f"font-size: {best_font}px; font-weight: bold; color: {theme.accent_neon_yellow};")
        best_layout.addWidget(self.best_lap_time_label)
        
        self.best_lap_number_label = QLabel("Lap #: --")
        self.best_lap_number_label.setStyleSheet(f"font-size: {get_scaled_font_size(12)}px; color: {theme.text_secondary};")
        best_layout.addWidget(self.best_lap_number_label)
        
        best_group.setLayout(best_layout)
        layout.addWidget(best_group)
        
        # Lap times table
        laps_group = QGroupBox("Lap Times")
        laps_layout = QVBoxLayout()
        
        self.lap_table = QTableWidget()
        self.lap_table.setColumnCount(3)
        self.lap_table.setHorizontalHeaderLabels(["Lap", "Time", "Speed"])
        self.lap_table.horizontalHeader().setStretchLastSection(True)
        self.lap_table.setStyleSheet(f"color: {theme.text_primary}; background-color: {theme.bg_tertiary};")
        self.lap_table.setAlternatingRowColors(True)
        laps_layout.addWidget(self.lap_table)
        
        laps_group.setLayout(laps_layout)
        layout.addWidget(laps_group)
        
        layout.addStretch()
        return panel
        
    def _start_detection(self) -> None:
        """Start lap detection."""
        if not LapDetector:
            LOGGER.error("LapDetector not available")
            return
            
        lat = self.sf_lat.value()
        lon = self.sf_lon.value()
        
        if lat == 0 and lon == 0:
            LOGGER.warning("Start/finish line not set")
            return
            
        self.lap_detector = LapDetector(
            start_finish_lat=lat,
            start_finish_lon=lon,
            detection_radius=self.detection_radius.value(),
            min_lap_time=self.min_lap_time.value(),
        )
        
        self.track_map.set_start_finish(lat, lon)
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
    def _stop_detection(self) -> None:
        """Stop lap detection."""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
    def _reset_session(self) -> None:
        """Reset lap detection session."""
        if self.lap_detector:
            self.lap_detector.reset_session()
        self.track_map.track_points.clear()
        self.track_map.laps.clear()
        self.track_map.current_lap = None
        self.track_map._redraw()
        self._update_display()
        
    def _use_current_gps(self) -> None:
        """Use current GPS position for start/finish line."""
        # This would get GPS from GPSInterface
        # For now, placeholder
        pass
        
    def _update_display(self) -> None:
        """Update display with latest data."""
        if not self.lap_detector:
            return
            
        # Update track map
        track_points = self.lap_detector.get_track_points()
        laps = self.lap_detector.completed_laps
        current_lap = self.lap_detector.get_current_lap()
        
        self.track_map.update_track(track_points, laps, current_lap)
        
        # Update current lap display
        if current_lap:
            minutes = int(current_lap.duration // 60) if current_lap.duration else 0
            seconds = (current_lap.duration % 60) if current_lap.duration else 0
            self.current_lap_time_label.setText(f"Lap Time: {minutes:02d}:{seconds:05.2f}")
            self.current_lap_number_label.setText(f"Lap #: {current_lap.lap_number}")
        else:
            self.current_lap_time_label.setText("Lap Time: --:--.---")
            self.current_lap_number_label.setText("Lap #: --")
        
        # Update best lap
        best_lap = self.lap_detector.get_best_lap()
        if best_lap and best_lap.duration:
            minutes = int(best_lap.duration // 60)
            seconds = best_lap.duration % 60
            self.best_lap_time_label.setText(f"Time: {minutes:02d}:{seconds:05.2f}")
            self.best_lap_number_label.setText(f"Lap #: {best_lap.lap_number}")
        else:
            self.best_lap_time_label.setText("Time: --:--.---")
            self.best_lap_number_label.setText("Lap #: --")
        
        # Update lap table
        self.lap_table.setRowCount(len(laps))
        for i, lap in enumerate(laps):
            self.lap_table.setItem(i, 0, QTableWidgetItem(str(lap.lap_number)))
            
            if lap.duration:
                minutes = int(lap.duration // 60)
                seconds = lap.duration % 60
                time_str = f"{minutes:02d}:{seconds:05.2f}"
            else:
                time_str = "--:--.---"
            self.lap_table.setItem(i, 1, QTableWidgetItem(time_str))
            
            speed_str = f"{lap.max_speed:.1f} mph" if lap.max_speed else "--"
            self.lap_table.setItem(i, 2, QTableWidgetItem(speed_str))
            
    def update_gps(self, lat: float, lon: float, speed: float) -> None:
        """Update with GPS data."""
        if self.lap_detector:
            self.lap_detector.update(lat, lon, speed)
            self._update_display()


__all__ = ["LapDetectionTab", "TrackMapWidget"]







