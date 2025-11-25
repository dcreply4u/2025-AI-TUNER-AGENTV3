"""
Futuristic HUD Widgets
High-tech interface components with glowing effects
"""

from __future__ import annotations

import math
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy

from ui.hud_theme import HUDTheme, HUDColors


class GridBackgroundWidget(QWidget):
    """Widget with electric blue grid pattern background."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.theme = HUDTheme()
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        
    def paintEvent(self, event) -> None:  # noqa: N802
        """Draw grid pattern background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fill with dark background
        painter.fillRect(self.rect(), QColor(self.theme.colors.background_dark))
        
        # Draw grid pattern
        spacing = self.theme.grid_spacing
        grid_color = QColor(self.theme.colors.grid_blue_dim)
        grid_color.setAlpha(50)  # Semi-transparent
        
        pen = QPen(grid_color, 1)
        painter.setPen(pen)
        
        # Vertical lines
        x = 0
        while x < self.width():
            painter.drawLine(x, 0, x, self.height())
            x += spacing
        
        # Horizontal lines
        y = 0
        while y < self.height():
            painter.drawLine(0, y, self.width(), y)
            y += spacing


class HUDLabel(QLabel):
    """HUD-style label with glowing text."""
    
    def __init__(
        self,
        text: str = "",
        color: str = "#00ffff",
        font_size: int = 12,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(text, parent)
        self.color = color
        self.font_size = font_size
        self._apply_style()
        
    def _apply_style(self) -> None:
        """Apply HUD styling."""
        theme = HUDTheme()
        self.setStyleSheet(f"""
            QLabel {{
                color: {self.color};
                font-family: {theme.font_family};
                font-size: {self.font_size}pt;
                font-weight: bold;
                background: transparent;
                border: none;
            }}
        """)


class RadialGauge(QWidget):
    """Circular gauge with radial bar and percentage."""
    
    def __init__(
        self,
        title: str = "",
        min_value: float = 0.0,
        max_value: float = 100.0,
        value: float = 0.0,
        color: str = "#00ffff",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.title = title
        self.min_value = min_value
        self.max_value = max_value
        self._value = value
        self.color = color
        self.setMinimumSize(80, 80)
        self.setMaximumSize(100, 100)
        
    def set_value(self, value: float) -> None:
        """Update gauge value."""
        self._value = max(self.min_value, min(self.max_value, value))
        self.update()
        
    def paintEvent(self, event) -> None:  # noqa: N802
        """Draw radial gauge."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        size = min(width, height) - 10
        x = (width - size) // 2
        y = (height - size) // 2
        
        # Calculate angle
        range_span = self.max_value - self.min_value
        normalized = (self._value - self.min_value) / range_span if range_span > 0 else 0
        angle = normalized * 360
        
        # Draw background arc
        bg_color = QColor(self.color)
        bg_color.setAlpha(30)
        pen = QPen(bg_color, 3)
        painter.setPen(pen)
        painter.drawArc(x, y, size, size, 0, 360 * 16)
        
        # Draw value arc
        value_color = QColor(self.color)
        pen = QPen(value_color, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(x, y, size, size, -90 * 16, int(-angle * 16))
        
        # Draw percentage text
        painter.setPen(QColor(self.color))
        font = QFont("Consolas", 10, QFont.Weight.Bold)
        painter.setFont(font)
        text = f"{int(self._value)}%"
        text_rect = painter.fontMetrics().boundingRect(text)
        painter.drawText(
            width // 2 - text_rect.width() // 2,
            height // 2 + text_rect.height() // 2,
            text,
        )
        
        # Draw title
        if self.title:
            font = QFont("Consolas", 8)
            painter.setFont(font)
            title_rect = painter.fontMetrics().boundingRect(self.title)
            painter.drawText(
                width // 2 - title_rect.width() // 2,
                height - 5,
                self.title,
            )


class ProcessorStatusWidget(QWidget):
    """Processor status indicators with circular gauges."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.theme = HUDTheme()
        self.setup_ui()
        self._start_update_timer()
        
    def setup_ui(self) -> None:
        """Setup UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Title
        title = HUDLabel("PROCESSOR LIST", self.theme.colors.orange_accent, 14)
        layout.addWidget(title)
        
        # Gauges grid
        gauges_layout = QHBoxLayout()
        gauges_layout.setSpacing(10)
        
        self.gauges = []
        for i in range(4):
            gauge = RadialGauge(f"CPU{i+1}", 0, 100, 50 + i * 10, self.theme.colors.electric_cyan)
            self.gauges.append(gauge)
            gauges_layout.addWidget(gauge)
            
        layout.addLayout(gauges_layout)
        layout.addStretch()
        
    def _start_update_timer(self) -> None:
        """Start update timer for demo data."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_values)
        self.timer.start(500)  # Update every 500ms
        
    def _update_values(self) -> None:
        """Update gauge values with demo data."""
        import random
        for gauge in self.gauges:
            current = gauge._value
            change = random.uniform(-5, 5)
            new_value = max(0, min(100, current + change))
            gauge.set_value(new_value)


class VerticalBarChart(QWidget):
    """Vertical bar chart with multi-color bars."""
    
    def __init__(
        self,
        values: list[float] | None = None,
        colors: list[str] | None = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.values = values or [0.0] * 10
        self.colors = colors or ["#00ffff"] * 10
        self.setMinimumSize(200, 150)
        
    def set_values(self, values: list[float]) -> None:
        """Update chart values."""
        self.values = values
        self.update()
        
    def paintEvent(self, event) -> None:  # noqa: N802
        """Draw bar chart."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        bar_count = len(self.values)
        bar_width = (width - 20) / bar_count
        max_value = max(self.values) if self.values else 1.0
        
        x = 10
        for i, value in enumerate(self.values):
            bar_height = (value / max_value) * (height - 20) if max_value > 0 else 0
            y = height - 10 - bar_height
            
            color = QColor(self.colors[i % len(self.colors)])
            brush = QBrush(color)
            painter.fillRect(int(x), int(y), int(bar_width - 2), int(bar_height), brush)
            
            # Add glow effect
            glow_color = QColor(color)
            glow_color.setAlpha(100)
            pen = QPen(glow_color, 2)
            painter.setPen(pen)
            painter.drawRect(int(x), int(y), int(bar_width - 2), int(bar_height))
            
            x += bar_width


class NetworkFlowWidget(QWidget):
    """Network flow visualization with data nodes."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.theme = HUDTheme()
        self.setMinimumSize(200, 150)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        
    def paintEvent(self, event) -> None:  # noqa: N802
        """Draw network flow visualization."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Fill background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        
        # Draw title
        font = QFont(self.theme.font_family, 12, QFont.Weight.Bold)
        painter.setFont(font)
        title = "NETWORK FLOW 157920"
        painter.setPen(QColor(self.theme.colors.electric_cyan))
        painter.drawText(10, 20, title)
        
        # Draw data nodes (hexagonal/circular)
        node_size = 12
        nodes = [
            (50, 50), (120, 50), (190, 50),
            (50, 100), (120, 100), (190, 100),
            (85, 75), (155, 75),
        ]
        
        for i, (x, y) in enumerate(nodes):
            # Node color (alternating)
            color = QColor(self.theme.colors.electric_cyan if i % 2 == 0 else self.theme.colors.text_primary)
            brush = QBrush(color)
            painter.setBrush(brush)
            painter.setPen(QPen(color, 1))
            painter.drawEllipse(x - node_size // 2, y - node_size // 2, node_size, node_size)
            
            # Connection lines
            if i < len(nodes) - 1:
                next_x, next_y = nodes[i + 1]
                line_color = QColor(self.theme.colors.grid_blue_dim)
                line_color.setAlpha(100)
                painter.setPen(QPen(line_color, 1))
                painter.drawLine(x, y, next_x, next_y)
        
        # Draw wireframe car view (small, bottom right)
        car_x = width - 80
        car_y = height - 60
        car_width = 60
        car_height = 40
        
        # Simple wireframe representation
        cyan_pen = QPen(QColor(self.theme.colors.electric_cyan), 1)
        cyan_pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(cyan_pen)
        painter.drawRect(car_x, car_y, car_width, car_height)
        painter.drawLine(car_x, car_y + car_height // 2, car_x + car_width, car_y + car_height // 2)
        painter.drawLine(car_x + car_width // 2, car_y, car_x + car_width // 2, car_y + car_height)
        
        # Data list (vertical text)
        font = QFont(self.theme.font_family, 8)
        painter.setFont(font)
        data_items = ["NODE_01: ACTIVE", "NODE_02: ACTIVE", "NODE_03: STANDBY"]
        for i, item in enumerate(data_items):
            painter.setPen(QColor(self.theme.colors.text_cyan))
            painter.drawText(10, 130 + i * 15, item)


__all__ = [
    "GridBackgroundWidget",
    "HUDLabel",
    "RadialGauge",
    "ProcessorStatusWidget",
    "VerticalBarChart",
    "NetworkFlowWidget",
]

