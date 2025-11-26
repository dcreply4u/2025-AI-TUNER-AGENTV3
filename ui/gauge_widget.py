"""
Racing Gauge Widget - Realistic analog racing instrument gauges.

Features:
- Rotating needle with smooth animation
- Tick marks with numeric labels
- Colored warning/danger zones
- Dark racing theme with bezel effect
- Digital value readout
- Customizable ranges and colors
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPoint,
    QPointF,
    QPropertyAnimation,
    QRectF,
    Qt,
    QTimer,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.theme_manager import Style


class RacingGauge(QWidget):
    """
    Realistic analog racing gauge with rotating needle.
    
    Features:
    - Smooth needle animation
    - Tick marks with labels
    - Colored zones (normal, warning, danger)
    - Dark racing theme with metallic bezel
    - Digital value display
    """

    def __init__(
        self,
        title: str = "Gauge",
        min_value: float = 0.0,
        max_value: float = 100.0,
        unit: str = "",
        parent: Optional[QWidget] = None,
        warning_value: Optional[float] = None,
        danger_value: Optional[float] = None,
        major_ticks: int = 10,
        minor_ticks: int = 5,
        needle_color: str = "#ff4444",
        accent_color: str = "#3498db",  # Default fallback - actual usage should use Style.scrollbar()
    ) -> None:
        super().__init__(parent)
        
        self.title = title
        self.min_value = min_value
        self.max_value = max_value
        self.unit = unit
        self._value = min_value
        self._animated_value = min_value
        
        # Warning/danger zones
        self.warning_value = warning_value
        self.danger_value = danger_value
        
        # Tick configuration
        self.major_ticks = major_ticks
        self.minor_ticks = minor_ticks
        
        # Colors
        self.needle_color = needle_color
        self.accent_color = accent_color
        self.normal_color = "#27ae60"
        self.warning_color = "#f39c12"
        self.danger_color = "#e74c3c"
        
        # Gauge arc angles (in degrees)
        self.start_angle = 225  # Top-left
        self.end_angle = -45    # Bottom-right
        self.arc_span = self.start_angle - self.end_angle  # 270 degrees
        
        # Fixed size to prevent jitter
        self.setFixedSize(145, 160)
        
        # Animation
        self._animation = QPropertyAnimation(self, b"animatedValue")
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.Type.OutQuad)
    
    def get_animated_value(self) -> float:
        return self._animated_value
    
    def set_animated_value(self, value: float) -> None:
        self._animated_value = value
        self.update()

    animatedValue = Property(float, get_animated_value, set_animated_value)
    
    def set_value(self, value: float) -> None:
        """Set gauge value with smooth animation."""
        self._value = max(self.min_value, min(self.max_value, value))
        
        # Animate to new value
        self._animation.stop()
        self._animation.setStartValue(self._animated_value)
        self._animation.setEndValue(self._value)
        self._animation.start()
    
    def set_value_instant(self, value: float) -> None:
        """Set gauge value instantly without animation."""
        self._value = max(self.min_value, min(self.max_value, value))
        self._animated_value = self._value
        self.update()

    def _value_to_angle(self, value: float) -> float:
        """Convert value to angle in degrees."""
        value_range = self.max_value - self.min_value
        if value_range == 0:
            return self.start_angle
        
        ratio = (value - self.min_value) / value_range
        return self.start_angle - (ratio * self.arc_span)
    
    def paintEvent(self, event) -> None:  # noqa: N802
        """Paint the racing gauge."""
        try:
            painter = QPainter(self)
            if not painter.isActive():
                return
                
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

            # Calculate dimensions
            width = self.width()
            height = self.height()
            size = min(width, height - 20)
            
            if size < 50:
                return
                
            center_x = width // 2
            center_y = (height - 20) // 2 + 5
            radius = (size - 20) // 2
            
            # Draw components
            self._draw_bezel(painter, center_x, center_y, radius)
            self._draw_face(painter, center_x, center_y, radius)
            self._draw_zones(painter, center_x, center_y, radius)
            self._draw_ticks(painter, center_x, center_y, radius)
            self._draw_needle(painter, center_x, center_y, radius)
            self._draw_center_hub(painter, center_x, center_y, radius)
            self._draw_value_display(painter, center_x, center_y, radius)
            self._draw_title(painter, width, height)
            
        except Exception as e:
            print(f"[WARN] RacingGauge.paintEvent error: {e}")
    
    def _draw_bezel(self, painter: QPainter, cx: int, cy: int, radius: int) -> None:
        """Draw metallic bezel ring."""
        # Outer bezel gradient
        bezel_radius = radius + 8
        gradient = QRadialGradient(cx, cy, bezel_radius)
        gradient.setColorAt(0.85, QColor("#3d3d3d"))
        gradient.setColorAt(0.90, QColor("#5a5a5a"))
        gradient.setColorAt(0.95, QColor("#2a2a2a"))
        gradient.setColorAt(1.0, QColor("#1a1a1a"))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor("#0a0a0a"), 2))
        painter.drawEllipse(cx - bezel_radius, cy - bezel_radius, 
                           bezel_radius * 2, bezel_radius * 2)
    
    def _draw_face(self, painter: QPainter, cx: int, cy: int, radius: int) -> None:
        """Draw gauge face (background)."""
        # Main face with subtle gradient
        gradient = QRadialGradient(cx, cy - radius // 3, radius * 1.5)
        gradient.setColorAt(0, QColor("#1e2530"))
        gradient.setColorAt(0.7, QColor("#0f1318"))
        gradient.setColorAt(1, QColor("#080a0d"))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)
    
    def _draw_zones(self, painter: QPainter, cx: int, cy: int, radius: int) -> None:
        """Draw colored warning/danger zones on the arc."""
        zone_radius = radius - 8
        zone_width = 6
        
        # Calculate zone angles
        if self.warning_value is not None and self.danger_value is not None:
            # Normal zone (green)
            normal_start = self._value_to_angle(self.min_value)
            normal_end = self._value_to_angle(self.warning_value)
            self._draw_arc_zone(painter, cx, cy, zone_radius, zone_width,
                               normal_start, normal_end, self.normal_color, 80)
            
            # Warning zone (amber)
            warning_start = normal_end
            warning_end = self._value_to_angle(self.danger_value)
            self._draw_arc_zone(painter, cx, cy, zone_radius, zone_width,
                               warning_start, warning_end, self.warning_color, 120)
            
            # Danger zone (red)
            danger_start = warning_end
            danger_end = self._value_to_angle(self.max_value)
            self._draw_arc_zone(painter, cx, cy, zone_radius, zone_width,
                               danger_start, danger_end, self.danger_color, 180)
        
        elif self.danger_value is not None:
            # Only danger zone
            danger_start = self._value_to_angle(self.danger_value)
            danger_end = self._value_to_angle(self.max_value)
            self._draw_arc_zone(painter, cx, cy, zone_radius, zone_width,
                               danger_start, danger_end, self.danger_color, 180)
    
    def _draw_arc_zone(
        self,
        painter: QPainter,
        cx: int,
        cy: int,
        radius: int,
        width: int,
        start_angle: float,
        end_angle: float,
        color: str,
        alpha: int = 150,
    ) -> None:
        """Draw a colored arc zone."""
        zone_color = QColor(color)
        zone_color.setAlpha(alpha)
        
        pen = QPen(zone_color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap)
        painter.setPen(pen)
        
        rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
        span = start_angle - end_angle
        
        # Qt uses 1/16th of a degree
        painter.drawArc(rect, int(end_angle * 16), int(span * 16))
    
    def _draw_ticks(self, painter: QPainter, cx: int, cy: int, radius: int) -> None:
        """Draw tick marks and labels."""
        value_range = self.max_value - self.min_value
        major_step = value_range / self.major_ticks
        
        for i in range(self.major_ticks + 1):
            value = self.min_value + i * major_step
            angle = self._value_to_angle(value)
            angle_rad = math.radians(angle)
            
            # Major tick
            inner_radius = radius - 18
            outer_radius = radius - 6
            
            x1 = cx + inner_radius * math.cos(angle_rad)
            y1 = cy - inner_radius * math.sin(angle_rad)
            x2 = cx + outer_radius * math.cos(angle_rad)
            y2 = cy - outer_radius * math.sin(angle_rad)
            
            # Tick color based on zone
            tick_color = self._get_zone_color(value)
            painter.setPen(QPen(QColor(tick_color), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

            # Label
            label_radius = radius - 28
            label_x = cx + label_radius * math.cos(angle_rad)
            label_y = cy - label_radius * math.sin(angle_rad)
            
            painter.setPen(QColor("#cccccc"))
            font = QFont("Arial", 8, QFont.Weight.Bold)
            painter.setFont(font)
            
            # Format label
            if value_range >= 1000:
                label = f"{int(value / 1000)}"
            elif value_range >= 100:
                label = f"{int(value)}"
            else:
                label = f"{value:.0f}"
            
            label_rect = painter.fontMetrics().boundingRect(label)
            painter.drawText(
                int(label_x - label_rect.width() / 2),
                int(label_y + label_rect.height() / 4),
                label,
            )
            
            # Minor ticks between major ticks
            if i < self.major_ticks:
                minor_step = major_step / self.minor_ticks
                for j in range(1, self.minor_ticks):
                    minor_value = value + j * minor_step
                    minor_angle = self._value_to_angle(minor_value)
                    minor_rad = math.radians(minor_angle)
                    
                    minor_inner = radius - 12
                    minor_outer = radius - 6
                    
                    mx1 = cx + minor_inner * math.cos(minor_rad)
                    my1 = cy - minor_inner * math.sin(minor_rad)
                    mx2 = cx + minor_outer * math.cos(minor_rad)
                    my2 = cy - minor_outer * math.sin(minor_rad)
                    
                    painter.setPen(QPen(QColor("#555555"), 1))
                    painter.drawLine(QPointF(mx1, my1), QPointF(mx2, my2))
    
    def _get_zone_color(self, value: float) -> str:
        """Get color based on value zone."""
        if self.danger_value is not None and value >= self.danger_value:
            return self.danger_color
        if self.warning_value is not None and value >= self.warning_value:
            return self.warning_color
        return "#ffffff"
    
    def _draw_needle(self, painter: QPainter, cx: int, cy: int, radius: int) -> None:
        """Draw the gauge needle."""
        angle = self._value_to_angle(self._animated_value)
        angle_rad = math.radians(angle)
        
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(-angle)
        
        # Needle dimensions
        needle_length = radius - 15
        needle_width = 4
        tail_length = 15
        
        # Create needle shape
        needle = QPolygonF([
            QPointF(-tail_length, needle_width / 2),
            QPointF(-tail_length, -needle_width / 2),
            QPointF(needle_length - 10, -needle_width / 2),
            QPointF(needle_length, 0),
            QPointF(needle_length - 10, needle_width / 2),
        ])
        
        # Needle gradient
        gradient = QLinearGradient(-tail_length, 0, needle_length, 0)
        gradient.setColorAt(0, QColor("#333333"))
        gradient.setColorAt(0.3, QColor(self.needle_color))
        gradient.setColorAt(0.7, QColor(self.needle_color))
        gradient.setColorAt(1, QColor("#ffffff"))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor("#111111"), 1))
        painter.drawPolygon(needle)
        
        # Needle glow effect
        glow_color = QColor(self.needle_color)
        glow_color.setAlpha(50)
        painter.setPen(QPen(glow_color, 3))
        painter.drawLine(QPointF(0, 0), QPointF(needle_length - 5, 0))
        
        painter.restore()
    
    def _draw_center_hub(self, painter: QPainter, cx: int, cy: int, radius: int) -> None:
        """Draw center hub/cap."""
        hub_radius = 12
        
        # Outer ring
        gradient = QRadialGradient(cx, cy, hub_radius)
        gradient.setColorAt(0, QColor("#555555"))
        gradient.setColorAt(0.5, QColor("#333333"))
        gradient.setColorAt(1, QColor("#111111"))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor("#666666"), 1))
        painter.drawEllipse(cx - hub_radius, cy - hub_radius, 
                           hub_radius * 2, hub_radius * 2)
        
        # Inner cap
        inner_radius = 6
        gradient2 = QRadialGradient(cx - 2, cy - 2, inner_radius)
        gradient2.setColorAt(0, QColor("#888888"))
        gradient2.setColorAt(1, QColor("#333333"))
        
        painter.setBrush(QBrush(gradient2))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(cx - inner_radius, cy - inner_radius,
                           inner_radius * 2, inner_radius * 2)
    
    def _draw_value_display(self, painter: QPainter, cx: int, cy: int, radius: int) -> None:
        """Draw digital value display - using centralized style system."""
        # Value box
        box_width = 60
        box_height = 20
        box_x = cx - box_width // 2
        box_y = cy + radius // 3
        
        # Box background
        painter.setBrush(QBrush(QColor("#0a0a0a")))
        painter.setPen(QPen(QColor(Style.gauge_border()), 1))  # Uses Style.gauge_border - change in ThemeColors to update globally
        painter.drawRoundedRect(box_x, box_y, box_width, box_height, 3, 3)
        
        # Value text - uses centralized style
        painter.setPen(QColor(Style.gauge_value()))  # Uses Style.gauge_value - change in ThemeColors to update globally
        font = QFont("Consolas", 11, QFont.Weight.Bold)
        painter.setFont(font)
        
        # Format value
        if abs(self._animated_value) >= 1000:
            value_text = f"{self._animated_value:.0f}"
        elif abs(self._animated_value) >= 100:
            value_text = f"{self._animated_value:.0f}"
        else:
            value_text = f"{self._animated_value:.1f}"
        
        text_rect = painter.fontMetrics().boundingRect(value_text)
        painter.drawText(
            box_x + (box_width - text_rect.width()) // 2,
            box_y + 15,
            value_text,
        )
    
    def _draw_title(self, painter: QPainter, width: int, height: int) -> None:
        """Draw gauge title and unit - using centralized style system."""
        painter.setPen(QColor(Style.gauge_title()))  # Uses Style.gauge_title - change in ThemeColors to update globally
        font = QFont("Arial", 9, QFont.Weight.Bold)
        painter.setFont(font)
        
        title_with_unit = self.title
        if self.unit:
            title_with_unit += f" ({self.unit})"
        
        title_rect = painter.fontMetrics().boundingRect(title_with_unit)
        painter.drawText(
            (width - title_rect.width()) // 2,
            height - 5,
            title_with_unit,
        )


class GaugePanel(QWidget):
    """
    Panel containing selectable racing gauges for telemetry display.
    
    Features:
    - 6 customizable gauge slots
    - 12 available gauge types to choose from
    - Dropdown selectors to swap gauges
    """
    
    # All available gauge configurations
    GAUGE_CONFIGS = {
        "RPM": {"title": "RPM", "min": 0, "max": 8000, "unit": "x1000", "warn": 6000, "danger": 7000, "ticks": 8, "color": "#ff4444"},
        "Speed": {"title": "SPEED", "min": 0, "max": 200, "unit": "MPH", "ticks": 10, "color": "#3498db"},
        "Boost": {"title": "BOOST", "min": -10, "max": 30, "unit": "PSI", "warn": 20, "danger": 25, "ticks": 8, "color": "#f39c12"},
        "CoolantTemp": {"title": "COOLANT", "min": 100, "max": 260, "unit": "°F", "warn": 220, "danger": 240, "ticks": 8, "color": "#27ae60"},
        "OilPressure": {"title": "OIL PSI", "min": 0, "max": 100, "unit": "PSI", "warn": 20, "ticks": 10, "color": "#9b59b6"},
        "OilTemp": {"title": "OIL °F", "min": 100, "max": 300, "unit": "°F", "warn": 250, "danger": 280, "ticks": 10, "color": "#e67e22"},
        "Throttle": {"title": "THROTTLE", "min": 0, "max": 100, "unit": "%", "ticks": 10, "color": "#1abc9c"},
        "Voltage": {"title": "VOLTS", "min": 10, "max": 16, "unit": "V", "warn": 12, "ticks": 6, "color": "#3498db"},
        "FuelPressure": {"title": "FUEL PSI", "min": 0, "max": 80, "unit": "PSI", "warn": 30, "ticks": 8, "color": "#e74c3c"},
        "IAT": {"title": "IAT", "min": 0, "max": 200, "unit": "°F", "warn": 140, "danger": 160, "ticks": 10, "color": "#1abc9c"},
        "AFR": {"title": "AFR", "min": 10, "max": 18, "unit": ":1", "warn": 11, "danger": 15, "ticks": 8, "color": "#9b59b6"},
        "EGT": {"title": "EGT", "min": 0, "max": 2000, "unit": "°F", "warn": 1500, "danger": 1800, "ticks": 10, "color": "#e74c3c"},
    }

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        # Note: Stylesheet uses f-string to inject Style colors
        # Change colors in ThemeColors to update globally
        self.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a1f2e, stop:1 #0f1318);
                border: 2px solid #2a3040;
                border-radius: 8px;
            }}
            QComboBox {{
                background: #2a3040;
                color: {Style.gauge_title()};
                border: 1px solid #3a4050;
                border-radius: 3px;
                padding: 1px 2px;
                font-size: 8px;
                font-weight: bold;
            }}
            QComboBox:hover {{ border: 1px solid {Style.title()}; }}
            QComboBox::drop-down {{ border: none; width: 12px; }}
            QComboBox::down-arrow {{ border-left: 3px solid transparent; border-right: 3px solid transparent; border-top: 4px solid {Style.gauge_title()}; }}
            QComboBox QAbstractItemView {{ background: #1a1f2e; color: #fff; selection-background-color: {Style.title()}; font-size: 9px; }}
        """)
        
        # Fixed size to prevent jitter
        self.setFixedSize(310, 540)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Title - using centralized style system
        # Change Style.title() in ThemeColors to update globally
        title = QLabel("🏎️ LIVE GAUGES")
        title.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: bold; 
            color: {Style.title()}; 
            padding: 2px;
            background: transparent;
            border: none;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFixedHeight(22)
        layout.addWidget(title)

        # Current gauge selections (user can change these)
        self.selected_gauges = ["RPM", "Speed", "Boost", "CoolantTemp", "OilPressure", "Throttle"]
        
        # Grid for gauges
        self.grid = QGridLayout()
        self.grid.setSpacing(4)
        self.grid.setContentsMargins(2, 0, 2, 0)

        # Create gauge widgets dict
        self.gauges: Dict[str, RacingGauge] = {}
        self.gauge_widgets: List[Tuple[RacingGauge, QComboBox]] = []
        
        # Create 6 gauge slots with selectors
        for i in range(6):
            row, col = divmod(i, 2)
            gauge_key = self.selected_gauges[i]
            
            # Create container for gauge + selector
            container = QWidget()
            container.setStyleSheet("background: transparent; border: none;")
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(1)
            
            # Create gauge
            gauge = self._create_gauge(gauge_key)
            self.gauges[gauge_key] = gauge
            container_layout.addWidget(gauge)

            # Create selector dropdown
            selector = QComboBox()
            selector.setFixedHeight(16)
            for name in self.GAUGE_CONFIGS.keys():
                selector.addItem(name)
            selector.setCurrentText(gauge_key)
            selector.currentTextChanged.connect(lambda text, idx=i: self._on_gauge_changed(idx, text))
            container_layout.addWidget(selector)
            
            self.gauge_widgets.append((gauge, selector))
            self.grid.addWidget(container, row, col)

        layout.addLayout(self.grid)

        # Demo timer
        self.demo_timer = QTimer(self)
        self.demo_timer.timeout.connect(self._update_demo_data)
        self.demo_time = 0.0
        self._timer_started = False
        
        # Initialize with demo values
        self._update_demo_data()
        
    def _create_gauge(self, gauge_key: str) -> RacingGauge:
        """Create a gauge from configuration."""
        cfg = self.GAUGE_CONFIGS.get(gauge_key, self.GAUGE_CONFIGS["RPM"])
        return RacingGauge(
            title=cfg["title"],
            min_value=cfg["min"],
            max_value=cfg["max"],
            unit=cfg["unit"],
            warning_value=cfg.get("warn"),
            danger_value=cfg.get("danger"),
            major_ticks=cfg.get("ticks", 10),
            needle_color=cfg["color"],
            accent_color=cfg["color"],
        )
    
    def _on_gauge_changed(self, slot_idx: int, new_gauge: str) -> None:
        """Handle gauge selection change."""
        if slot_idx >= len(self.gauge_widgets):
            return
        
        old_gauge, selector = self.gauge_widgets[slot_idx]
        old_key = self.selected_gauges[slot_idx]
        
        # Remove old gauge from dict
        if old_key in self.gauges:
            del self.gauges[old_key]
        
        # Get container
        row, col = divmod(slot_idx, 2)
        container = self.grid.itemAtPosition(row, col).widget()
        container_layout = container.layout()
        
        # Remove old gauge widget
        container_layout.removeWidget(old_gauge)
        old_gauge.deleteLater()
        
        # Create new gauge
        new_gauge_widget = self._create_gauge(new_gauge)
        self.gauges[new_gauge] = new_gauge_widget
        self.gauge_widgets[slot_idx] = (new_gauge_widget, selector)
        self.selected_gauges[slot_idx] = new_gauge
        
        # Insert at position 0 (before selector)
        container_layout.insertWidget(0, new_gauge_widget)

    def update_data(self, data: Dict[str, float]) -> None:
        """Update gauges with real telemetry data."""
        key_mapping = {
            "RPM": "RPM", "Engine_RPM": "RPM",
            "Speed": "Speed", "Vehicle_Speed": "Speed",
            "Boost": "Boost", "Boost_Pressure": "Boost",
            "CoolantTemp": "CoolantTemp", "Coolant_Temp": "CoolantTemp",
            "OilPressure": "OilPressure", "Oil_Pressure": "OilPressure",
            "OilTemp": "OilTemp", "Oil_Temp": "OilTemp",
            "Throttle": "Throttle", "Throttle_Position": "Throttle",
            "Voltage": "Voltage", "Battery_Voltage": "Voltage",
            "FuelPressure": "FuelPressure", "Fuel_Pressure": "FuelPressure",
            "IAT": "IAT", "Intake_Air_Temp": "IAT",
            "AFR": "AFR", "Air_Fuel_Ratio": "AFR",
            "EGT": "EGT", "Exhaust_Gas_Temp": "EGT",
        }

        for data_key, gauge_key in key_mapping.items():
            if data_key in data and gauge_key in self.gauges:
                self.gauges[gauge_key].set_value(data[data_key])

    def _update_demo_data(self) -> None:
        """Generate demo data for gauges."""
        if self._timer_started:
            self.demo_time += 0.1
        else:
            self.demo_time = 1.0
        
        t = self.demo_time

        # Simulate driving patterns
        # Acceleration phase
        phase = (t % 20)
        
        if phase < 5:
            # Accelerating
            rpm_base = 2000 + phase * 1000
            speed_base = phase * 15
            throttle = 80 + random.uniform(-5, 5)
            boost = 5 + phase * 3
        elif phase < 10:
            # High speed cruise
            rpm_base = 5500 + math.sin(t * 2) * 500
            speed_base = 70 + math.sin(t * 0.5) * 10
            throttle = 40 + random.uniform(-10, 10)
            boost = 12 + math.sin(t) * 3
        elif phase < 15:
            # Deceleration
            rpm_base = 5500 - (phase - 10) * 800
            speed_base = 70 - (phase - 10) * 12
            throttle = 10 + random.uniform(-5, 5)
            boost = -2 + random.uniform(-2, 2)
        else:
            # Idle
            rpm_base = 800 + random.uniform(-50, 50)
            speed_base = random.uniform(0, 5)
            throttle = random.uniform(0, 5)
            boost = -5 + random.uniform(-2, 2)
        
        demo_data = {
            "RPM": max(0, min(8000, rpm_base + random.uniform(-100, 100))),
            "Speed": max(0, min(200, speed_base + random.uniform(-2, 2))),
            "Boost": max(-10, min(30, boost)),
            "CoolantTemp": 180 + math.sin(t * 0.1) * 15 + random.uniform(-2, 2),
            "OilPressure": 45 + math.sin(t * 0.15) * 10 + random.uniform(-2, 2),
            "OilTemp": 200 + math.sin(t * 0.08) * 20 + random.uniform(-3, 3),
            "Throttle": max(0, min(100, throttle)),
            "Voltage": 13.8 + math.sin(t * 0.2) * 0.5 + random.uniform(-0.1, 0.1),
            "FuelPressure": 45 + math.sin(t * 0.12) * 5 + random.uniform(-1, 1),
            "IAT": 90 + math.sin(t * 0.05) * 20 + random.uniform(-2, 2),
            "AFR": 14.7 + math.sin(t * 0.3) * 1.5 + random.uniform(-0.2, 0.2),
            "EGT": 1200 + math.sin(t * 0.07) * 200 + random.uniform(-20, 20),
        }
        
        self.update_data(demo_data)
        
    def start_demo(self) -> None:
        """Start demo mode."""
        self._timer_started = True
        self.demo_timer.start(100)

    def stop_demo(self) -> None:
        """Stop demo mode."""
        self._timer_started = False
        self.demo_timer.stop()


# Keep old class name for backwards compatibility
CircularGauge = RacingGauge

__all__ = ["GaugePanel", "RacingGauge", "CircularGauge"]
