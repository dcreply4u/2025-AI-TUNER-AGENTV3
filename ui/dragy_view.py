from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Tuple, TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from services.performance_tracker import PerformanceSnapshot


class MetricTile(QWidget):
    """Simple metric tile for drag racing performance data."""
    
    TILE_HEIGHT = 85
    
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.metric_title = title
        
        # Fixed size
        self.setFixedHeight(self.TILE_HEIGHT)
        self.setMinimumWidth(100)
        
        # White background
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor("#ffffff"))
        self.setPalette(palette)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)
        
        # Title
        self.title_label = QLabel(f"🏎️ {title}")
        self.title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #2c3e50; background-color: #e8f4f8; padding: 3px 6px; border-radius: 3px;")
        layout.addWidget(self.title_label)
        
        # Value
        self.value_label = QLabel("--")
        self.value_label.setFont(QFont("Consolas", 18, QFont.Weight.Bold))
        self.value_label.setStyleSheet("color: #34495e;")
        layout.addWidget(self.value_label)
        
        # Best
        self.best_label = QLabel("🏆 Best: --")
        self.best_label.setFont(QFont("Arial", 8))
        self.best_label.setStyleSheet("color: #27ae60;")
        layout.addWidget(self.best_label)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor("#bdc3c7"), 1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 6, 6)

    def set_value(self, value: Optional[float], suffix: str = "s") -> None:
        if value is None:
            self.value_label.setText("--")
            self.value_label.setStyleSheet("color: #bdc3c7;")
        else:
            self.value_label.setText(f"{value:0.3f}{suffix}")
            self.value_label.setStyleSheet("color: #2c3e50;")

    def set_best(self, value: Optional[float], suffix: str = "s") -> None:
        if value is None:
            self.best_label.setText("🏆 Best: --")
            self.best_label.setStyleSheet("color: #95a5a6;")
        else:
            self.best_label.setText(f"🏆 Best: {value:0.3f}{suffix}")
            self.best_label.setStyleSheet("color: #27ae60; font-weight: bold;")


class MiniMapWidget(QWidget):
    """Simple GPS track map."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(80)
        self.points: List[Tuple[float, float]] = []
        
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor("#1a1f2e"))
        self.setPalette(palette)

    def set_points(self, points: Iterable[Tuple[float, float]]) -> None:
        self.points = list(points)
        self.update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.fillRect(self.rect(), QColor("#1a1f2e"))
        
        pen = QPen(QColor("#bdc3c7"), 1)
        painter.setPen(pen)
        painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 6, 6)
        
        if len(self.points) < 2:
            painter.setPen(QColor("#7f8c8d"))
            painter.setFont(QFont("Arial", 9))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "📍 Awaiting GPS...")
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

        pen = QPen(QColor("#3498db"), 2)
        painter.setPen(pen)
        prev = transform(*self.points[0])
        for lat, lon in self.points[1:]:
            curr = transform(lat, lon)
            painter.drawLine(prev[0], prev[1], curr[0], curr[1])
            prev = curr

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#e74c3c"))
        painter.drawEllipse(prev[0] - 4, prev[1] - 4, 8, 8)
        
        start = transform(*self.points[0])
        painter.setBrush(QColor("#27ae60"))
        painter.drawEllipse(start[0] - 3, start[1] - 3, 6, 6)


class DragyPerformanceView(QWidget):
    """Dashboard for drag racing performance metrics."""

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
        
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor("#ffffff"))
        self.setPalette(palette)
        
        # Main layout - no stretch
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        
        # Header
        header = QLabel("🏁 Drag Performance")
        header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header.setStyleSheet("color: #2c3e50;")
        header.setFixedHeight(20)
        layout.addWidget(header)

        # === TILES CONTAINER (fixed height) ===
        tiles_container = QWidget()
        tiles_container.setFixedHeight(MetricTile.TILE_HEIGHT * 2 + 8)  # 2 rows + spacing
        
        tile_grid = QGridLayout(tiles_container)
        tile_grid.setContentsMargins(0, 0, 0, 0)
        tile_grid.setSpacing(6)
        
        self.tiles: Dict[str, MetricTile] = {}
        for index, key in enumerate(self.METRIC_KEYS):
            tile = MetricTile(key)
            row = index // 3
            col = index % 3
            tile_grid.addWidget(tile, row, col)
            self.tiles[key] = tile

        layout.addWidget(tiles_container)
        
        # === INFO SECTION (below tiles) ===
        self.distance_label = QLabel("📏 Distance: 0.00 mi")
        self.distance_label.setFont(QFont("Arial", 9))
        self.distance_label.setStyleSheet("color: #7f8c8d;")
        self.distance_label.setFixedHeight(16)
        layout.addWidget(self.distance_label)

        self.status_label = QLabel("📍 Awaiting GPS fix…")
        self.status_label.setFont(QFont("Arial", 9))
        self.status_label.setStyleSheet("color: #95a5a6;")
        self.status_label.setFixedHeight(16)
        layout.addWidget(self.status_label)

        # === MAP SECTION ===
        map_label = QLabel("🗺️ Track Map")
        map_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        map_label.setStyleSheet("color: #7f8c8d;")
        map_label.setFixedHeight(16)
        layout.addWidget(map_label)
        
        self.map_widget = MiniMapWidget()
        layout.addWidget(self.map_widget)
        
        # Push everything up
        layout.addStretch()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        pen = QPen(QColor("#bdc3c7"), 1)
        painter.setPen(pen)
        painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 8, 8)

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
    """Container exposing legacy API."""

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
        best_metrics: Optional[Dict[str, float]] = None,
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
