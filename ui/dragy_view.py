from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Tuple, TYPE_CHECKING

from PySide6.QtCore import Qt  # type: ignore
from PySide6.QtGui import QColor, QPainter, QPen  # type: ignore
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
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("metricTile")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(scaled_spacing(8), scaled_spacing(6), scaled_spacing(8), scaled_spacing(6))
        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet("font-size: 11px; color: #9aa0a6;")
        self.value_label = QLabel("--")
        self.value_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #00e0ff;")
        self.best_label = QLabel("Best: --")
        self.best_label.setStyleSheet("font-size: 11px; color: #5f6368;")
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.best_label)

    def set_value(self, value: Optional[float], suffix: str = "s") -> None:
        if value is None:
            self.value_label.setText("--")
        else:
            self.value_label.setText(f"{value:0.2f}{suffix}")

    def set_best(self, value: Optional[float], suffix: str = "s") -> None:
        if value is None:
            self.best_label.setText("Best: --")
        else:
            self.best_label.setText(f"Best: {value:0.2f}{suffix}")


class MiniMapWidget(QWidget):
    """Simple painter-based breadcrumb map for GPS traces."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(180)
        self.points: List[Tuple[float, float]] = []

    def set_points(self, points: Iterable[Tuple[float, float]]) -> None:
        self.points = list(points)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#0d1117"))
        if len(self.points) < 2:
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
                int(x * (self.width() - 10) + 5),
                int(self.height() - (y * (self.height() - 10) + 5)),
            )

        pen = QPen(QColor("#00e0ff"), 2)
        painter.setPen(pen)
        prev = transform(*self.points[0])
        for lat, lon in self.points[1:]:
            curr = transform(lat, lon)
            painter.drawLine(prev[0], prev[1], curr[0], curr[1])
            prev = curr

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#ff6b6b"))
        painter.drawEllipse(prev[0] - 4, prev[1] - 4, 8, 8)


class DragyPerformanceView(QWidget):
    """Dashboard-style widget inspired by Dragy performance UIs."""

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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(scaled_spacing(0), scaled_spacing(0), scaled_spacing(0), scaled_spacing(0))

        self.tiles: Dict[str, MetricTile] = {}
        tile_grid = QGridLayout()
        tile_grid.setSpacing(scaled_spacing(10))
        for index, key in enumerate(self.METRIC_KEYS):
            tile = MetricTile(key)
            # Use Expanding policy for responsive behavior
            tile.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            row = index // 3
            col = index % 3
            tile_grid.addWidget(tile, row, col)
            self.tiles[key] = tile

        layout.addLayout(tile_grid)

        self.distance_label = QLabel("Distance: 0.00 mi")
        self.distance_label.setStyleSheet("color: #9aa0a6; font-size: 12px;")
        layout.addWidget(self.distance_label)

        self.status_label = QLabel("Awaiting GPS fix…")
        self.status_label.setStyleSheet("color: #5f6368; font-size: 11px;")
        layout.addWidget(self.status_label)

        self.map_widget = MiniMapWidget()
        layout.addWidget(self.map_widget)

    def update_snapshot(self, snapshot: Optional["PerformanceSnapshot"]) -> None:
        if snapshot is None:
            return
        for key, tile in self.tiles.items():
            tile.set_value(snapshot.metrics.get(key))
            tile.set_best(snapshot.best_metrics.get(key))
        miles = snapshot.total_distance_m / 1609.34
        self.distance_label.setText(f"Distance: {miles:0.2f} mi")
        self.map_widget.set_points(snapshot.track_points)

    def update_metrics(self, snapshot: Optional["PerformanceSnapshot"]) -> None:
        self.update_snapshot(snapshot)

    def update_track(self, points: Iterable[Tuple[float, float]]) -> None:
        self.map_widget.set_points(points)

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)


class DragyView(QWidget):
    """Simple container that exposes the legacy `set_status` / `update_fix` API."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
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

