"""
Advanced HUD Widgets - Neo-Cyberpunk Design
Fragmented rings, segmented data arrays, parametric displays
"""

from __future__ import annotations

import math
import random
from typing import Optional

from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPolygonF
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy

from ui.hud_theme import HUDTheme, HUDColors


class FragmentedRingWidget(QWidget):
    """Large fragmented cyan circular ring with radiating lines - central focal anchor."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.theme = HUDTheme()
        self.setMinimumSize(300, 300)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self._rotation = 0.0
        
        # Start rotation animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_rotation)
        self.timer.start(50)  # 20 FPS
        
    def _update_rotation(self) -> None:
        """Slowly rotate the ring."""
        self._rotation += 0.5
        if self._rotation >= 360:
            self._rotation = 0
        self.update()
        
    def paintEvent(self, event) -> None:  # noqa: N802
        """Draw fragmented ring with radiating lines."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        center_x = width // 2
        center_y = height // 2
        radius = min(width, height) // 2 - 20
        
        # Draw background (transparent)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        
        # Draw fragmented ring (segmented, not continuous)
        cyan = QColor(self.theme.colors.electric_cyan)
        pen = QPen(cyan, 3)
        painter.setPen(pen)
        
        # Create 12 segments with gaps
        segment_count = 12
        segment_angle = 360 / segment_count
        gap_angle = 15  # Gap between segments
        
        for i in range(segment_count):
            start_angle = (i * segment_angle + self._rotation) % 360
            arc_span = segment_angle - gap_angle
            
            # Draw arc segment
            rect_x = center_x - radius
            rect_y = center_y - radius
            painter.drawArc(
                rect_x, rect_y, radius * 2, radius * 2,
                int(start_angle * 16),
                int(arc_span * 16),
            )
        
        # Draw radiating lines (thin, precise)
        inner_radius = radius * 0.6
        outer_radius = radius * 1.2
        line_count = 24
        
        pen = QPen(cyan, 1)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        
        for i in range(line_count):
            angle = (i * (360 / line_count) + self._rotation) * math.pi / 180
            x1 = center_x + inner_radius * math.cos(angle)
            y1 = center_y + inner_radius * math.sin(angle)
            x2 = center_x + outer_radius * math.cos(angle)
            y2 = center_y + outer_radius * math.sin(angle)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))


class TimelineBarWidget(QWidget):
    """Top navigation/timeline bar with segmented data array and status bars."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.theme = HUDTheme()
        self.setMinimumHeight(60)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self._data_values = [random.randint(0, 100) for _ in range(50)]
        
        # Animate data
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_data)
        self.timer.start(200)
        
    def _update_data(self) -> None:
        """Update timeline data."""
        self._data_values = [random.randint(0, 100) for _ in range(50)]
        self.update()
        
    def paintEvent(self, event) -> None:  # noqa: N802
        """Draw timeline bar."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Fill background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        
        # Draw segmented data array (tiny cyan and orange rectangles)
        block_width = width / len(self._data_values)
        cyan = QColor(self.theme.colors.electric_cyan)
        orange = QColor(self.theme.colors.vibrant_traffic_orange)
        
        for i, value in enumerate(self._data_values):
            x = i * block_width
            block_height = (value / 100) * (height - 30)
            y = height - 20 - block_height
            
            color = cyan if i % 2 == 0 else orange
            brush = QBrush(color)
            painter.fillRect(int(x), int(y), int(block_width - 1), int(block_height), brush)
        
        # Draw two horizontal status bars on the left
        bar_y = 10
        bar_height = 15
        bar_width = 120
        
        # First bar (mostly cyan - 724)
        cyan_width = int(bar_width * 0.85)
        painter.fillRect(10, bar_y, cyan_width, bar_height, cyan)
        painter.fillRect(10 + cyan_width, bar_y, bar_width - cyan_width, bar_height, orange)
        
        font = QFont(self.theme.font_family, 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor(self.theme.colors.text_primary))
        painter.drawText(10, bar_y + bar_height + 12, "724")
        
        # Second bar (mostly orange - 78)
        orange_width = int(bar_width * 0.65)
        painter.fillRect(10, bar_y + 25, orange_width, bar_height, orange)
        painter.fillRect(10 + orange_width, bar_y + 25, bar_width - orange_width, bar_height, cyan)
        painter.drawText(10, bar_y + bar_height + 37, "78")


class TelemetryDataBlock(QWidget):
    """Rectangular data block with paired numerical readouts."""
    
    def __init__(
        self,
        label: str,
        cyan_value: int,
        orange_value: int,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.theme = HUDTheme()
        self.label = label
        self.cyan_value = cyan_value
        self.orange_value = orange_value
        self.setMinimumSize(120, 50)
        self.setMaximumHeight(60)
        
    def update_values(self, cyan: int, orange: int) -> None:
        """Update display values."""
        self.cyan_value = cyan
        self.orange_value = orange
        self.update()
        
    def paintEvent(self, event) -> None:  # noqa: N802
        """Draw data block."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Draw border
        cyan = QColor(self.theme.colors.electric_cyan)
        cyan.setAlpha(100)
        pen = QPen(cyan, 1)
        painter.setPen(pen)
        painter.drawRect(0, 0, width - 1, height - 1)
        
        # Draw values
        font = QFont(self.theme.font_family, 14, QFont.Weight.Bold)
        painter.setFont(font)
        
        # Cyan value (left)
        painter.setPen(QColor(self.theme.colors.electric_cyan))
        painter.drawText(10, 20, str(self.cyan_value))
        
        # Orange value (right)
        painter.setPen(QColor(self.theme.colors.vibrant_traffic_orange))
        orange_text = str(self.orange_value)
        text_width = painter.fontMetrics().boundingRect(orange_text).width()
        painter.drawText(width - text_width - 10, 20, orange_text)
        
        # Label (bottom)
        font = QFont(self.theme.font_family, 8)
        painter.setFont(font)
        painter.setPen(QColor(self.theme.colors.text_dim))
        label_width = painter.fontMetrics().boundingRect(self.label).width()
        painter.drawText((width - label_width) // 2, height - 5, self.label)


class VerticalSegmentedBarGraph(QWidget):
    """Large vertical segmented bar graphs (4 columns) with cyan/orange."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.theme = HUDTheme()
        self.setMinimumSize(300, 200)
        self._values = [[random.randint(20, 100) for _ in range(8)] for _ in range(4)]
        
        # Animate
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_values)
        self.timer.start(300)
        
    def _update_values(self) -> None:
        """Update bar values."""
        for col in self._values:
            for i in range(len(col)):
                col[i] = max(20, min(100, col[i] + random.randint(-5, 5)))
        self.update()
        
    def paintEvent(self, event) -> None:  # noqa: N802
        """Draw segmented bar graphs."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        col_count = len(self._values)
        col_width = (width - 20) / col_count
        segment_count = len(self._values[0])
        
        cyan = QColor(self.theme.colors.electric_cyan)
        orange = QColor(self.theme.colors.vibrant_traffic_orange)
        
        for col_idx, col_values in enumerate(self._values):
            x = 10 + col_idx * col_width
            segment_height = (height - 20) / segment_count
            
            for seg_idx, value in enumerate(col_values):
                y = 10 + seg_idx * segment_height
                bar_height = (value / 100) * segment_height
                
                # Alternate cyan/orange
                color = cyan if seg_idx % 2 == 0 else orange
                brush = QBrush(color)
                painter.fillRect(int(x), int(y), int(col_width - 2), int(bar_height), brush)
                
                # Glow effect
                glow_color = QColor(color)
                glow_color.setAlpha(150)
                pen = QPen(glow_color, 1)
                painter.setPen(pen)
                painter.drawRect(int(x), int(y), int(col_width - 2), int(bar_height))


class ParametricDisplay(QWidget):
    """Large circular display with complex radial slices and inner/outer rings."""
    
    def __init__(
        self,
        title: str,
        value: float = 50.0,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.theme = HUDTheme()
        self.title = title
        self._value = value
        self.setMinimumSize(120, 120)
        self.setMaximumSize(150, 150)
        
    def set_value(self, value: float) -> None:
        """Update value."""
        self._value = max(0, min(100, value))
        self.update()
        
    def paintEvent(self, event) -> None:  # noqa: N802
        """Draw parametric display."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        center_x = width // 2
        center_y = height // 2
        outer_radius = min(width, height) // 2 - 10
        inner_radius = outer_radius * 0.5
        
        # Draw outer ring (segmented)
        cyan = QColor(self.theme.colors.electric_cyan)
        orange = QColor(self.theme.colors.vibrant_traffic_orange)
        
        # Outer ring segments
        segment_count = 16
        segment_angle = 360 / segment_count
        for i in range(segment_count):
            start_angle = i * segment_angle
            color = cyan if i % 2 == 0 else orange
            pen = QPen(color, 4)
            painter.setPen(pen)
            
            rect_x = center_x - outer_radius
            rect_y = center_y - outer_radius
            painter.drawArc(
                rect_x, rect_y, outer_radius * 2, outer_radius * 2,
                int(start_angle * 16),
                int(segment_angle * 16),
            )
        
        # Inner ring
        pen = QPen(cyan, 2)
        painter.setPen(pen)
        inner_rect_x = center_x - inner_radius
        inner_rect_y = center_y - inner_radius
        painter.drawArc(
            inner_rect_x, inner_rect_y, inner_radius * 2, inner_radius * 2,
            0, 360 * 16,
        )
        
        # Value arc (based on _value)
        value_angle = (self._value / 100) * 360
        pen = QPen(orange, 3)
        painter.setPen(pen)
        painter.drawArc(
            inner_rect_x, inner_rect_y, inner_radius * 2, inner_radius * 2,
            -90 * 16, int(-value_angle * 16),
        )
        
        # Center value text
        font = QFont(self.theme.font_family, 12, QFont.Weight.Bold)
        painter.setFont(font)
        value_text = f"{int(self._value)}"
        text_rect = painter.fontMetrics().boundingRect(value_text)
        painter.setPen(QColor(self.theme.colors.text_primary))
        painter.drawText(
            center_x - text_rect.width() // 2,
            center_y + text_rect.height() // 2,
            value_text,
        )
        
        # Title
        font = QFont(self.theme.font_family, 8)
        painter.setFont(font)
        title_rect = painter.fontMetrics().boundingRect(self.title)
        painter.setPen(QColor(self.theme.colors.text_dim))
        painter.drawText(
            center_x - title_rect.width() // 2,
            height - 5,
            self.title,
        )


class DataFlowCluster(QWidget):
    """Tight grid of interconnected segmented circular rings and boxes."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.theme = HUDTheme()
        self.setMinimumSize(250, 150)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self._center_value = 12
        
        # Animate center value
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_value)
        self.timer.start(1000)
        
    def _update_value(self) -> None:
        """Update center value."""
        self._center_value = random.randint(10, 15)
        self.update()
        
    def paintEvent(self, event) -> None:  # noqa: N802
        """Draw data flow cluster."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Fill background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        
        cyan = QColor(self.theme.colors.electric_cyan)
        orange = QColor(self.theme.colors.vibrant_traffic_orange)
        
        # Draw grid of nodes
        node_size = 20
        spacing = 35
        start_x = 20
        start_y = 20
        
        nodes = []
        for row in range(3):
            for col in range(4):
                x = start_x + col * spacing
                y = start_y + row * spacing
                nodes.append((x, y))
        
        # Draw connections
        pen = QPen(cyan, 1)
        pen.setStyle(Qt.PenStyle.DashLine)
        cyan.setAlpha(80)
        pen.setColor(cyan)
        painter.setPen(pen)
        
        for i, (x1, y1) in enumerate(nodes):
            if i < len(nodes) - 1:
                x2, y2 = nodes[i + 1]
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        # Draw nodes (segmented rings and boxes)
        for i, (x, y) in enumerate(nodes):
            if i == 6:  # Center node (larger, shows value)
                # Draw larger segmented ring
                radius = node_size
                pen = QPen(cyan, 2)
                painter.setPen(pen)
                painter.drawArc(
                    int(x - radius), int(y - radius),
                    radius * 2, radius * 2,
                    0, 270 * 16,  # 3/4 circle
                )
                pen = QPen(orange, 2)
                painter.setPen(pen)
                painter.drawArc(
                    int(x - radius), int(y - radius),
                    radius * 2, radius * 2,
                    270 * 16, 90 * 16,  # 1/4 circle
                )
                
                # Draw value
                font = QFont(self.theme.font_family, 10, QFont.Weight.Bold)
                painter.setFont(font)
                value_text = str(self._center_value)
                text_rect = painter.fontMetrics().boundingRect(value_text)
                painter.setPen(QColor(self.theme.colors.text_primary))
                painter.drawText(
                    int(x - text_rect.width() // 2),
                    int(y + text_rect.height() // 2),
                    value_text,
                )
            else:
                # Draw small segmented ring or box
                if i % 2 == 0:
                    # Ring
                    radius = node_size // 2
                    pen = QPen(cyan if i % 4 == 0 else orange, 1)
                    painter.setPen(pen)
                    painter.drawArc(
                        int(x - radius), int(y - radius),
                        radius * 2, radius * 2,
                        0, 360 * 16,
                    )
                else:
                    # Box
                    size = node_size // 2
                    color = cyan if i % 4 == 1 else orange
                    brush = QBrush(color)
                    painter.fillRect(
                        int(x - size), int(y - size),
                        size * 2, size * 2,
                        brush,
                    )


class WaveformEqualizerWidget(QWidget):
    """Vertical equalizer bars with horizontal waveform display."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.theme = HUDTheme()
        self.setMinimumSize(400, 120)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self._bar_values = [random.randint(10, 90) for _ in range(20)]
        self._waveform_points = [random.randint(40, 60) for _ in range(100)]
        
        # Animate
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_data)
        self.timer.start(100)
        
    def _update_data(self) -> None:
        """Update bar and waveform data."""
        self._bar_values = [max(10, min(90, v + random.randint(-3, 3))) for v in self._bar_values]
        self._waveform_points = [max(40, min(60, v + random.randint(-2, 2))) for v in self._waveform_points]
        self.update()
        
    def paintEvent(self, event) -> None:  # noqa: N802
        """Draw equalizer and waveform."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Fill background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        
        cyan = QColor(self.theme.colors.electric_cyan)
        orange = QColor(self.theme.colors.vibrant_traffic_orange)
        
        # Draw vertical equalizer bars (left side)
        bar_count = len(self._bar_values)
        bar_width = (width * 0.6) / bar_count
        bar_area_height = height - 30
        
        for i, value in enumerate(self._bar_values):
            x = i * bar_width
            bar_height = (value / 100) * bar_area_height
            y = bar_area_height - bar_height
            
            color = cyan if i % 2 == 0 else orange
            brush = QBrush(color)
            painter.fillRect(int(x), int(y), int(bar_width - 1), int(bar_height), brush)
        
        # Draw horizontal waveform (right side, thin orange line)
        waveform_x_start = int(width * 0.65)
        waveform_width = width - waveform_x_start - 10
        waveform_height = 20
        waveform_y = height - 25
        
        pen = QPen(orange, 2)
        painter.setPen(pen)
        
        point_count = len(self._waveform_points)
        if point_count > 1:
            points = []
            for i, value in enumerate(self._waveform_points):
                x = waveform_x_start + (i / (point_count - 1)) * waveform_width
                y = waveform_y + (value / 100) * waveform_height
                points.append(QPointF(x, y))
            
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])


__all__ = [
    "FragmentedRingWidget",
    "TimelineBarWidget",
    "TelemetryDataBlock",
    "VerticalSegmentedBarGraph",
    "ParametricDisplay",
    "DataFlowCluster",
    "WaveformEqualizerWidget",
]

