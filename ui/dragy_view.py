from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Tuple, TYPE_CHECKING

from PySide6.QtCore import Qt  # type: ignore
from PySide6.QtGui import QColor, QPainter, QPen, QFont  # type: ignore
from PySide6.QtWidgets import (  # type: ignore
    QFrame,
    QGridLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

try:
    from ui.responsive_layout_manager import get_responsive_manager, scaled_size, scaled_font_size, scaled_spacing
    RESPONSIVE_AVAILABLE = True
except ImportError:
    RESPONSIVE_AVAILABLE = False
    get_responsive_manager = None
    scaled_size = lambda x, use_width=True: x
    scaled_font_size = lambda x: x
    scaled_spacing = lambda x: x

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from services.performance_tracker import PerformanceSnapshot


class MetricTile(QFrame):
    """Modern styled metric tile for drag racing performance data."""
    
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName("metricTile")
        
        # Modern light theme styling
        self.setStyleSheet("""
            QFrame#metricTile {
                background-color: #ffffff;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        
        # Title
        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet("""
            font-size: 10px; 
            font-weight: bold;
            color: #7f8c8d; 
            letter-spacing: 1px;
            background: transparent;
        """)
        layout.addWidget(self.title_label)
        
        # Value - prominent display
        self.value_label = QLabel("--")
        self.value_label.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            color: #2c3e50;
            background: transparent;
            font-family: Consolas, monospace;
        """)
        layout.addWidget(self.value_label)
        
        # Best time
        self.best_label = QLabel("Best: --")
        self.best_label.setStyleSheet("""
            font-size: 10px; 
            color: #27ae60;
            background: transparent;
        """)
        layout.addWidget(self.best_label)

    def set_value(self, value: Optional[float], suffix: str = "s") -> None:
        if value is None:
            self.value_label.setText("--")
            self.value_label.setStyleSheet("""
                font-size: 24px; 
                font-weight: bold; 
                color: #bdc3c7;
                background: transparent;
                font-family: Consolas, monospace;
            """)
        else:
            self.value_label.setText(f"{value:0.3f}{suffix}")
            self.value_label.setStyleSheet("""
                font-size: 24px; 
                font-weight: bold; 
                color: #2c3e50;
                background: transparent;
                font-family: Consolas, monospace;
            """)

    def set_best(self, value: Optional[float], suffix: str = "s") -> None:
        if value is None:
            self.best_label.setText("Best: --")
            self.best_label.setStyleSheet("""
                font-size: 10px; 
                color: #bdc3c7;
                background: transparent;
            """)
        else:
            self.best_label.setText(f"🏆 Best: {value:0.3f}{suffix}")
            self.best_label.setStyleSheet("""
                font-size: 10px; 
                color: #27ae60;
                font-weight: bold;
                background: transparent;
            """)


class MiniMapWidget(QWidget):
    """Simple painter-based breadcrumb map for GPS traces with modern styling."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(150)
        self.points: List[Tuple[float, float]] = []
        self.setStyleSheet("""
            background-color: #1a1f2e;
            border: 1px solid #bdc3c7;
            border-radius: 8px;
        """)

    def set_points(self, points: Iterable[Tuple[float, float]]) -> None:
        self.points = list(points)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dark background for the track map
        painter.fillRect(self.rect(), QColor("#1a1f2e"))
        
        # Draw "No GPS Data" if no points
        if len(self.points) < 2:
            painter.setPen(QColor("#7f8c8d"))
            font = QFont("Arial", 11)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "📍 Awaiting GPS data...")
            return

        lats = [p[0] for p in self.points]
        lons = [p[1] for p in self.points]
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
        lat_range = max(max_lat - min_lat, 1e-6)
        lon_range = max(max_lon - min_lon, 1e-6)

        def transform(lat: float, lon: float) -> Tuple[int, int]:
            x = (lon - min_lon) / lon_range
            y = (lat - min_lat) / lat_range
            return (
                int(x * (self.width() - 20) + 10),
                int(self.height() - (y * (self.height() - 20) + 10)),
            )

        # Draw track line with gradient effect
        pen = QPen(QColor("#3498db"), 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        prev = transform(*self.points[0])
        for i, (lat, lon) in enumerate(self.points[1:]):
            curr = transform(lat, lon)
            # Gradient from blue to cyan as track progresses
            progress = i / len(self.points)
            color = QColor()
            color.setRgbF(0.2 + 0.1 * progress, 0.6 + 0.3 * progress, 0.8 + 0.2 * progress)
            pen.setColor(color)
            painter.setPen(pen)
            painter.drawLine(prev[0], prev[1], curr[0], curr[1])
            prev = curr

        # Current position indicator (pulsing dot effect)
        painter.setPen(Qt.PenStyle.NoPen)
        # Outer glow
        painter.setBrush(QColor(231, 76, 60, 100))
        painter.drawEllipse(prev[0] - 8, prev[1] - 8, 16, 16)
        # Inner dot
        painter.setBrush(QColor("#e74c3c"))
        painter.drawEllipse(prev[0] - 5, prev[1] - 5, 10, 10)
        
        # Start position
        start = transform(*self.points[0])
        painter.setBrush(QColor("#27ae60"))
        painter.drawEllipse(start[0] - 4, start[1] - 4, 8, 8)


class DragyPerformanceView(QFrame):
    """Dashboard-style widget inspired by Dragy performance UIs with modern styling."""

    METRIC_KEYS = [
        "60ft",
        "0-30 mph",
        "0-60 mph",
        "1/8 mile",
        "1/4 mile",
        "1/2 mile",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # Header
        header = QLabel("🏁 Drag Performance")
        header.setStyleSheet("font-size: 14px; font-weight: 700; color: #2c3e50; background: transparent;")
        layout.addWidget(header)

        # Metric tiles grid
        self.tiles: Dict[str, MetricTile] = {}
        tile_grid = QGridLayout()
        tile_grid.setSpacing(8)
        
        for index, key in enumerate(self.METRIC_KEYS):
            tile = MetricTile(key)
            tile.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            row = index // 3
            col = index % 3
            tile_grid.addWidget(tile, row, col)
            self.tiles[key] = tile

        layout.addLayout(tile_grid)

        # Stats row
        stats_row = QVBoxLayout()
        stats_row.setSpacing(4)
        
        self.distance_label = QLabel("📏 Distance: 0.00 mi")
        self.distance_label.setStyleSheet("color: #7f8c8d; font-size: 11px; background: transparent;")
        stats_row.addWidget(self.distance_label)

        self.status_label = QLabel("📍 Awaiting GPS fix…")
        self.status_label.setStyleSheet("color: #95a5a6; font-size: 11px; background: transparent;")
        stats_row.addWidget(self.status_label)
        
        layout.addLayout(stats_row)

        # Track map
        map_label = QLabel("🗺️ Track Map")
        map_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #7f8c8d; margin-top: 8px; background: transparent;")
        layout.addWidget(map_label)
        
        self.map_widget = MiniMapWidget()
        layout.addWidget(self.map_widget)

    def update_snapshot(self, snapshot: Optional["PerformanceSnapshot"]) -> None:
        if snapshot is None:
            return
        for key, tile in self.tiles.items():
            tile.set_value(snapshot.metrics.get(key))
            tile.set_best(snapshot.best_metrics.get(key))
        miles = snapshot.total_distance_m / 1609.34
        self.distance_label.setText(f"📏 Distance: {miles:0.2f} mi")
        self.map_widget.set_points(snapshot.track_points)

    def update_metrics(self, snapshot: Optional["PerformanceSnapshot"]) -> None:
        self.update_snapshot(snapshot)

    def update_track(self, points: Iterable[Tuple[float, float]]) -> None:
        self.map_widget.set_points(points)

    def set_status(self, text: str) -> None:
        self.status_label.setText(f"📍 {text}")


class DragyView(QWidget):
    """Simple container that exposes the legacy `set_status` / `update_fix` API."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.performance = DragyPerformanceView()
        layout.addWidget(self.performance)

    def set_status(self, text: str) -> None:
        self.performance.set_status(text)

    def update_fix(
        self,
        fix: Optional[Dict[str, float]],
        snapshot: Optional["PerformanceSnapshot"],
        best_metrics: Optional[Dict[str, float]] = None,  # kept for backward compat
    ) -> None:
        if snapshot:
            if best_metrics:
                snapshot.best_metrics.update(best_metrics)
            self.performance.update_snapshot(snapshot)
        if fix:
            self.performance.set_status(
                f"Lat {fix.get('lat', 0):.5f}, Lon {fix.get('lon', 0):.5f}, "
                f"{fix.get('speed_mps', 0.0) * 2.23694:0.1f} mph"
            )

    def update_snapshot(self, snapshot: "PerformanceSnapshot") -> None:
        self.performance.update_snapshot(snapshot)


__all__ = ["DragyPerformanceView", "DragyView"]
