"""
HUD-style Slider Controls
Vertical sliders with cyan glow effects
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

from ui.hud_theme import HUDTheme, HUDColors


class HUDSlider(QWidget):
    """Vertical slider with HUD styling."""
    
    valueChanged = Signal(float)
    
    def __init__(
        self,
        label: str = "",
        min_value: float = 0.0,
        max_value: float = 100.0,
        value: float = 50.0,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.theme = HUDTheme()
        self.label = label
        self.min_value = min_value
        self.max_value = max_value
        self._value = value
        self.dragging = False
        self.setMinimumSize(40, 120)
        self.setMaximumSize(50, 200)
        
    def set_value(self, value: float) -> None:
        """Set slider value."""
        self._value = max(self.min_value, min(self.max_value, value))
        self.update()
        self.valueChanged.emit(self._value)
        
    def mousePressEvent(self, event) -> None:  # noqa: N802
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self._update_value_from_pos(event.y())
            
    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        """Handle mouse move."""
        if self.dragging:
            self._update_value_from_pos(event.y())
            
    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        """Handle mouse release."""
        self.dragging = False
        
    def _update_value_from_pos(self, y: int) -> None:
        """Update value from mouse Y position."""
        height = self.height() - 20  # Account for margins
        y_pos = max(10, min(height + 10, y))
        normalized = 1.0 - (y_pos - 10) / height  # Invert (top = max)
        self.set_value(self.min_value + normalized * (self.max_value - self.min_value))
        
    def paintEvent(self, event) -> None:  # noqa: N802
        """Draw slider."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Calculate slider position
        range_span = self.max_value - self.min_value
        normalized = (self._value - self.min_value) / range_span if range_span > 0 else 0
        slider_y = 10 + (1.0 - normalized) * (height - 20)
        
        # Draw track (background)
        track_color = QColor(self.theme.colors.grid_blue_dim)
        track_color.setAlpha(100)
        pen = QPen(track_color, 3)
        painter.setPen(pen)
        painter.drawLine(width // 2, 10, width // 2, height - 10)
        
        # Draw filled portion (glowing cyan)
        fill_color = QColor(self.theme.colors.electric_cyan)
        fill_color.setAlpha(150)
        pen = QPen(fill_color, 4)
        painter.setPen(pen)
        painter.drawLine(width // 2, int(slider_y), width // 2, height - 10)
        
        # Draw slider handle
        handle_color = QColor(self.theme.colors.electric_cyan)
        brush = QBrush(handle_color)
        painter.setBrush(brush)
        painter.setPen(QPen(handle_color, 2))
        painter.drawEllipse(width // 2 - 8, int(slider_y) - 8, 16, 16)
        
        # Draw value text
        font = QFont("Consolas", 8)
        painter.setFont(font)
        value_text = f"{int(self._value)}"
        text_color = QColor(self.theme.colors.electric_cyan)
        painter.setPen(text_color)
        text_rect = painter.fontMetrics().boundingRect(value_text)
        painter.drawText(
            width // 2 - text_rect.width() // 2,
            height - 2,
            value_text,
        )
        
        # Draw label if provided
        if self.label:
            font = QFont("Consolas", 7)
            painter.setFont(font)
            label_rect = painter.fontMetrics().boundingRect(self.label)
            painter.drawText(
                width // 2 - label_rect.width() // 2,
                8,
                self.label,
            )


class SliderStack(QWidget):
    """Stack of vertical sliders."""
    
    def __init__(self, labels: list[str] | None = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.theme = HUDTheme()
        self.setup_ui(labels or ["A", "B", "C", "D"])
        
    def setup_ui(self, labels: list[str]) -> None:
        """Setup UI with sliders."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        
        self.sliders = []
        for label in labels:
            slider = HUDSlider(label, 0, 100, 50)
            self.sliders.append(slider)
            layout.addWidget(slider)
            
        layout.addStretch()


__all__ = ["HUDSlider", "SliderStack"]


