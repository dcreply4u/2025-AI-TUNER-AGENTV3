"""
GPS Driving Line Analysis

Features:
- Overlay telemetry data on GPS map
- Driving line visualization
- Braking point analysis
- Speed trace overlay
- G-force visualization
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QPen, QBrush
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsPathItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QCheckBox,
)

LOGGER = logging.getLogger(__name__)


@dataclass
class GPSPoint:
    """GPS coordinate with telemetry data."""
    lat: float
    lon: float
    speed: float
    g_force_lateral: float
    g_force_longitudinal: float
    throttle: float
    brake: float
    timestamp: float


@dataclass
class BrakingPoint:
    """Braking point marker."""
    lat: float
    lon: float
    speed: float
    deceleration: float


class GPSDrivingLineWidget(QWidget):
    """GPS driving line analysis widget."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize GPS driving line widget."""
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        self.overlay_speed = QCheckBox("Speed")
        self.overlay_speed.setChecked(True)
        control_layout.addWidget(self.overlay_speed)
        
        self.overlay_gforce = QCheckBox("G-Force")
        self.overlay_gforce.setChecked(True)
        control_layout.addWidget(self.overlay_gforce)
        
        self.overlay_throttle = QCheckBox("Throttle")
        control_layout.addWidget(self.overlay_throttle)
        
        self.overlay_brake = QCheckBox("Brake")
        control_layout.addWidget(self.overlay_brake)
        
        self.overlay_braking_points = QCheckBox("Braking Points")
        self.overlay_braking_points.setChecked(True)
        control_layout.addWidget(self.overlay_braking_points)
        
        update_btn = QPushButton("Update Overlay")
        update_btn.clicked.connect(self._update_overlay)
        control_layout.addWidget(update_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # Map view
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(self.view.RenderHint.Antialiasing)
        layout.addWidget(self.view)
        
        # Data
        self.gps_points: List[GPSPoint] = []
        self.braking_points: List[BrakingPoint] = []
        self.driving_line_path: Optional[QGraphicsPathItem] = None
        
    def load_gps_data(self, points: List[GPSPoint]) -> None:
        """Load GPS data points."""
        self.gps_points = points
        self._detect_braking_points()
        self._update_overlay()
    
    def _detect_braking_points(self) -> None:
        """Detect braking points from GPS data."""
        self.braking_points = []
        
        if len(self.gps_points) < 2:
            return
        
        for i in range(1, len(self.gps_points)):
            prev = self.gps_points[i-1]
            curr = self.gps_points[i]
            
            # Calculate deceleration
            time_delta = curr.timestamp - prev.timestamp
            if time_delta > 0:
                speed_delta = curr.speed - prev.speed
                deceleration = speed_delta / time_delta
                
                # Braking point: significant deceleration
                if deceleration < -2.0:  # m/s² threshold
                    self.braking_points.append(BrakingPoint(
                        lat=curr.lat,
                        lon=curr.lon,
                        speed=curr.speed,
                        deceleration=deceleration,
                    ))
    
    def _update_overlay(self) -> None:
        """Update map overlay."""
        self.scene.clear()
        
        if not self.gps_points:
            return
        
        # Convert GPS to scene coordinates (simplified - would need proper projection)
        scene_points = [self._gps_to_scene(p.lat, p.lon) for p in self.gps_points]
        
        # Draw driving line
        if len(scene_points) > 1:
            from PySide6.QtGui import QPainterPath
            path = QPainterPath()
            path.moveTo(scene_points[0])
            for point in scene_points[1:]:
                path.lineTo(point)
            
            self.driving_line_path = QGraphicsPathItem(path)
            pen = QPen(QColor("#00e0ff"), 3)
            self.driving_line_path.setPen(pen)
            self.scene.addItem(self.driving_line_path)
        
        # Overlay speed (color-coded)
        if self.overlay_speed.isChecked():
            self._overlay_speed_trace(scene_points)
        
        # Overlay G-force
        if self.overlay_gforce.isChecked():
            self._overlay_gforce(scene_points)
        
        # Overlay braking points
        if self.overlay_braking_points.isChecked():
            self._overlay_braking_points()
        
        # Fit view to scene
        self.view.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
    
    def _gps_to_scene(self, lat: float, lon: float) -> QPointF:
        """Convert GPS coordinates to scene coordinates."""
        # Simplified conversion - would need proper map projection
        # For now, use relative coordinates
        if not self.gps_points:
            return QPointF(0, 0)
        
        # Find min/max for scaling
        min_lat = min(p.lat for p in self.gps_points)
        max_lat = max(p.lat for p in self.gps_points)
        min_lon = min(p.lon for p in self.gps_points)
        max_lon = max(p.lon for p in self.gps_points)
        
        # Scale to scene coordinates
        scale_x = 1000.0 / (max_lon - min_lon) if max_lon != min_lon else 1.0
        scale_y = 1000.0 / (max_lat - min_lat) if max_lat != min_lat else 1.0
        
        x = (lon - min_lon) * scale_x
        y = (lat - min_lat) * scale_y
        
        return QPointF(x, y)
    
    def _overlay_speed_trace(self, scene_points: List[QPointF]) -> None:
        """Overlay speed trace with color coding."""
        if len(scene_points) != len(self.gps_points):
            return
        
        max_speed = max(p.speed for p in self.gps_points) if self.gps_points else 1.0
        
        for i, (point, gps_point) in enumerate(zip(scene_points, self.gps_points)):
            # Color based on speed
            speed_ratio = gps_point.speed / max_speed if max_speed > 0 else 0
            color = QColor(
                int(255 * (1 - speed_ratio)),  # Red component
                int(255 * speed_ratio),  # Green component
                0,  # Blue component
            )
            
            # Draw point
            ellipse = QGraphicsEllipseItem(point.x() - 2, point.y() - 2, 4, 4)
            ellipse.setBrush(QBrush(color))
            ellipse.setPen(QPen(Qt.PenStyle.NoPen))
            self.scene.addItem(ellipse)
    
    def _overlay_gforce(self, scene_points: List[QPointF]) -> None:
        """Overlay G-force vectors."""
        if len(scene_points) != len(self.gps_points):
            return
        
        for point, gps_point in zip(scene_points, self.gps_points):
            # Draw G-force vector
            g_lat = gps_point.g_force_lateral
            g_lon = gps_point.g_force_longitudinal
            
            # Scale vector
            scale = 50.0  # pixels per G
            end_x = point.x() + g_lon * scale
            end_y = point.y() + g_lat * scale
            
            line = QGraphicsLineItem(point.x(), point.y(), end_x, end_y)
            pen = QPen(QColor("#ffff00"), 2)
            line.setPen(pen)
            self.scene.addItem(line)
    
    def _overlay_braking_points(self) -> None:
        """Overlay braking point markers."""
        for bp in self.braking_points:
            scene_point = self._gps_to_scene(bp.lat, bp.lon)
            
            # Draw marker
            ellipse = QGraphicsEllipseItem(scene_point.x() - 5, scene_point.y() - 5, 10, 10)
            ellipse.setBrush(QBrush(QColor("#ff0000")))
            ellipse.setPen(QPen(QColor("#ffffff"), 2))
            self.scene.addItem(ellipse)


__all__ = [
    "GPSDrivingLineWidget",
    "GPSPoint",
    "BrakingPoint",
]






