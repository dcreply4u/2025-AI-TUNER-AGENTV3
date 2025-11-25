"""
Wireframe Car Model Widget
3D-style wireframe visualization with battery pack highlighting
"""

from __future__ import annotations

import math
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush
from PySide6.QtWidgets import QWidget

from ui.hud_theme import HUDTheme, HUDColors


class WireframeCarWidget(QWidget):
    """Wireframe visualization of electric car chassis with battery pack."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.theme = HUDTheme()
        self.battery_charge = 85.0  # Battery charge percentage
        self.setMinimumSize(400, 300)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        
        # Animation timer for pulsing effects
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self._update_pulse)
        self.pulse_phase = 0.0
        self.pulse_timer.start(50)  # 20 FPS
        
    def set_battery_charge(self, charge: float) -> None:
        """Update battery charge (0-100)."""
        self.battery_charge = max(0.0, min(100.0, charge))
        self.update()
        
    def _update_pulse(self) -> None:
        """Update pulse animation."""
        self.pulse_phase += 0.1
        if self.pulse_phase > 2 * math.pi:
            self.pulse_phase = 0.0
        self.update()
        
    def paintEvent(self, event) -> None:  # noqa: N802
        """Draw wireframe car model."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Fill with transparent background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        
        # Calculate car dimensions (centered, low-slung sports car)
        car_width = width * 0.7
        car_height = height * 0.5
        car_x = (width - car_width) // 2
        car_y = (height - car_height) // 2
        
        # Draw chassis outline (wireframe)
        cyan_pen = QPen(QColor(self.theme.colors.electric_cyan), 2)
        cyan_pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(cyan_pen)
        
        # Main body rectangle (low, wide)
        body_rect = (car_x, car_y + car_height * 0.3, car_width, car_height * 0.4)
        painter.drawRect(*body_rect)
        
        # Front section
        front_x = car_x
        front_y = car_y + car_height * 0.4
        front_width = car_width * 0.25
        front_height = car_height * 0.2
        painter.drawRect(front_x, front_y, front_width, front_height)
        
        # Rear section
        rear_x = car_x + car_width * 0.75
        rear_y = car_y + car_height * 0.4
        rear_width = car_width * 0.25
        rear_height = car_height * 0.2
        painter.drawRect(rear_x, rear_y, rear_width, rear_height)
        
        # Internal structure lines
        # Horizontal cross members
        for i in range(3):
            y_offset = car_height * 0.1 * (i + 1)
            painter.drawLine(
                car_x + 10,
                car_y + car_height * 0.3 + y_offset,
                car_x + car_width - 10,
                car_y + car_height * 0.3 + y_offset,
            )
        
        # Vertical supports
        for i in range(4):
            x_offset = car_width * 0.2 * (i + 1)
            painter.drawLine(
                car_x + x_offset,
                car_y + car_height * 0.3,
                car_x + x_offset,
                car_y + car_height * 0.7,
            )
        
        # Battery pack (central, in floor) - HIGHLIGHTED
        battery_x = car_x + car_width * 0.3
        battery_y = car_y + car_height * 0.6
        battery_width = car_width * 0.4
        battery_height = car_height * 0.15
        
        # Pulsing glow effect
        pulse_alpha = int(150 + 50 * math.sin(self.pulse_phase))
        
        # Battery pack glow
        battery_glow = QColor(self.theme.colors.lime_green)
        battery_glow.setAlpha(pulse_alpha)
        brush = QBrush(battery_glow)
        painter.fillRect(
            int(battery_x),
            int(battery_y),
            int(battery_width),
            int(battery_height),
            brush,
        )
        
        # Battery pack outline (bright lime green)
        battery_pen = QPen(QColor(self.theme.colors.lime_green), 3)
        painter.setPen(battery_pen)
        painter.drawRect(
            int(battery_x),
            int(battery_y),
            int(battery_width),
            int(battery_height),
        )
        
        # Battery cells (segmented)
        cell_count = 8
        cell_width = battery_width / cell_count
        for i in range(cell_count):
            cell_x = battery_x + i * cell_width
            painter.drawLine(
                int(cell_x),
                int(battery_y),
                int(cell_x),
                int(battery_y + battery_height),
            )
        
        # Battery charge indicator text
        font = QFont("Consolas", 12, QFont.Weight.Bold)
        painter.setFont(font)
        charge_text = f"{int(self.battery_charge)}%"
        painter.setPen(QColor(self.theme.colors.lime_green))
        text_rect = painter.fontMetrics().boundingRect(charge_text)
        painter.drawText(
            int(battery_x + battery_width // 2 - text_rect.width() // 2),
            int(battery_y + battery_height // 2 + text_rect.height() // 2),
            charge_text,
        )
        
        # Other mechanical components (subtle cyan glow)
        component_color = QColor(self.theme.colors.electric_cyan)
        component_color.setAlpha(80)
        component_pen = QPen(component_color, 1)
        painter.setPen(component_pen)
        
        # Motor locations (front and rear)
        motor_size = 15
        # Front motor
        painter.drawEllipse(
            int(front_x + front_width // 2 - motor_size // 2),
            int(front_y + front_height // 2 - motor_size // 2),
            motor_size,
            motor_size,
        )
        # Rear motor
        painter.drawEllipse(
            int(rear_x + rear_width // 2 - motor_size // 2),
            int(rear_y + rear_height // 2 - motor_size // 2),
            motor_size,
            motor_size,
        )


__all__ = ["WireframeCarWidget"]


