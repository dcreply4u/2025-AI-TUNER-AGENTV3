from __future__ import annotations

import math
import random
from typing import Dict, Optional

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget


class CircularGauge(QWidget):
    """Circular gauge widget for displaying telemetry values."""

    def __init__(
        self,
        title: str,
        min_value: float = 0.0,
        max_value: float = 100.0,
        unit: str = "",
        parent: Optional[QWidget] = None,
        needle_color: Optional[str] = None,
        background_color: Optional[str] = None,
        scale_color: Optional[str] = None,
        text_color: Optional[str] = None,
        warning_zone_color: Optional[str] = None,
        critical_zone_color: Optional[str] = None,
    ) -> None:
        super().__init__(parent)
        self.title = title
        self.min_value = min_value
        self.max_value = max_value
        self.unit = unit
        self.current_value = min_value
        
        # Customizable colors (with defaults)
        self.needle_color = needle_color or "#00e0ff"
        self.background_color = background_color or "#1a1f35"
        self.scale_color = scale_color or "#ffffff"
        self.text_color = text_color or "#ffffff"
        self.warning_zone_color = warning_zone_color or "#ffaa00"
        self.critical_zone_color = critical_zone_color or "#ff4444"
        
        self.setMinimumSize(80, 90)
        self.setMaximumSize(90, 100)
        # Ensure gauge is visible with proper background
        self.setStyleSheet("background-color: transparent; border: none;")
        # Ensure gauge paints properly
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)  # Allow transparency
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)  # Custom painting
    
    def set_customization(
        self,
        needle_color: Optional[str] = None,
        background_color: Optional[str] = None,
        scale_color: Optional[str] = None,
        text_color: Optional[str] = None,
        warning_zone_color: Optional[str] = None,
        critical_zone_color: Optional[str] = None,
    ) -> None:
        """Update gauge customization colors."""
        if needle_color:
            self.needle_color = needle_color
        if background_color:
            self.background_color = background_color
        if scale_color:
            self.scale_color = scale_color
        if text_color:
            self.text_color = text_color
        if warning_zone_color:
            self.warning_zone_color = warning_zone_color
        if critical_zone_color:
            self.critical_zone_color = critical_zone_color
        self.update()

    def set_value(self, value: float) -> None:
        """Update gauge value."""
        self.current_value = max(self.min_value, min(self.max_value, value))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        """Paint the circular gauge."""
        try:
            # Safety check - don't paint if widget is too small or not ready
            if self.width() < 10 or self.height() < 10:
                return
            
            painter = QPainter(self)
            if not painter.isActive():
                return
                
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            width = self.width()
            height = self.height()
            size = min(width, height) - 20
            if size <= 0:
                return
                
            x = (width - size) // 2
            y = (height - size) // 2 + 10

            # Calculate angle (270 degrees arc, from -135 to 135)
            range_span = self.max_value - self.min_value
            normalized = (self.current_value - self.min_value) / range_span if range_span > 0 else 0
            angle = -135 + (normalized * 270)

            # Draw background arc (lighter, thinner - using scale color)
            # Use QColor with alpha for transparency (QPen doesn't have setOpacity in PySide6)
            bg_color = QColor(self.scale_color)
            bg_color.setAlpha(128)  # 50% opacity for better visibility
            pen = QPen(bg_color, 4, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawArc(x, y, size, size, -135 * 16, 270 * 16)

            # Draw value arc with customizable needle color - make it thicker and more vibrant
            color = QColor(self.needle_color)
            
            pen = QPen(color, 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)  # Thicker line
            painter.setPen(pen)
            painter.drawArc(x, y, size, size, -135 * 16, int(angle * 16))

            # Draw center value (larger, cleaner - using customizable text color)
            painter.setPen(QColor(self.text_color))
            font = QFont("Arial", 12, QFont.Weight.Bold)  # Slightly larger for visibility
            painter.setFont(font)
            value_text = f"{self.current_value:.0f}"
            if self.unit:
                value_text += f" {self.unit}"
            text_rect = painter.fontMetrics().boundingRect(value_text)
            painter.drawText(
                width // 2 - text_rect.width() // 2,
                height // 2 + 3,
                value_text,
            )

            # Draw title below (using customizable text color, make it darker and bolder)
            font = QFont("Arial", 9, QFont.Weight.Bold)  # Larger and bolder
            painter.setFont(font)
            # Use darker color for title for better visibility
            title_color = QColor(self.text_color)
            if title_color.lightness() > 200:  # If too light, make it darker
                title_color = QColor("#2c3e50")
            painter.setPen(title_color)
            title_rect = painter.fontMetrics().boundingRect(self.title)
            painter.drawText(
                width // 2 - title_rect.width() // 2,
                height - 8,
                self.title,
            )
        except Exception as e:
            # Silently fail to prevent crashes - just log to console
            print(f"[WARN] CircularGauge.paintEvent error: {e}")
            import traceback
            traceback.print_exc()


class GaugePanel(QWidget):
    """Panel containing multiple gauges for telemetry display."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        # Set background and ensure visibility with solid styling - match main UI theme
        # Use white background to match main window, ensure it's visible
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff; 
                border: 1px solid #bdc3c7; 
                border-radius: 6px;
                padding: 10px;
            }
        """)
        # Ensure opaque background and proper z-ordering
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)
        # Ensure it doesn't float above other widgets
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop, False)
        self.setMinimumSize(260, 320)  # Increased height to show all 6 gauges in 3 rows
        self.setMaximumSize(280, 350)
        # Ensure proper size policy to respect layout
        from PySide6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Title (dark text on light background to match main UI)
        title = QLabel("Live Gauges")
        title.setStyleSheet("font-size: 13px; font-weight: 700; color: #2c3e50; padding: 3px; background: transparent;")
        layout.addWidget(title)

        # Grid layout for gauges - 2 columns for better visibility
        grid = QGridLayout()
        grid.setSpacing(10)  # Increased spacing for better visibility
        grid.setContentsMargins(5, 5, 5, 5)

        # Create gauges with vibrant colors for visibility on light background
        self.gauges: Dict[str, CircularGauge] = {}
        
        # Row 1: RPM (Red) and Speed (Blue)
        rpm_gauge = CircularGauge(
            "RPM", min_value=0, max_value=8000, unit="rpm",
            needle_color="#e74c3c",  # Bright red
            scale_color="#c0392b",  # Darker red for scale
            text_color="#2c3e50"  # Dark text for visibility
        )
        self.gauges["RPM"] = rpm_gauge
        grid.addWidget(rpm_gauge, 0, 0)

        speed_gauge = CircularGauge(
            "Speed", min_value=0, max_value=200, unit="mph",
            needle_color="#3498db",  # Bright blue
            scale_color="#2980b9",  # Darker blue for scale
            text_color="#2c3e50"  # Dark text for visibility
        )
        self.gauges["Speed"] = speed_gauge
        grid.addWidget(speed_gauge, 0, 1)

        # Row 2: Boost (Orange) and Coolant (Green)
        boost_gauge = CircularGauge(
            "Boost", min_value=-5, max_value=30, unit="psi",
            needle_color="#f39c12",  # Bright orange
            scale_color="#e67e22",  # Darker orange for scale
            text_color="#2c3e50"  # Dark text for visibility
        )
        self.gauges["Boost"] = boost_gauge
        grid.addWidget(boost_gauge, 1, 0)

        coolant_gauge = CircularGauge(
            "Coolant", min_value=70, max_value=120, unit="°F",
            needle_color="#27ae60",  # Bright green
            scale_color="#229954",  # Darker green for scale
            text_color="#2c3e50"  # Dark text for visibility
        )
        self.gauges["CoolantTemp"] = coolant_gauge
        grid.addWidget(coolant_gauge, 1, 1)

        # Row 3: Oil Pressure (Purple) and Throttle (Cyan)
        oil_gauge = CircularGauge(
            "Oil Press", min_value=20, max_value=80, unit="psi",
            needle_color="#9b59b6",  # Bright purple
            scale_color="#8e44ad",  # Darker purple for scale
            text_color="#2c3e50"  # Dark text for visibility
        )
        self.gauges["OilPressure"] = oil_gauge
        grid.addWidget(oil_gauge, 2, 0)

        throttle_gauge = CircularGauge(
            "Throttle", min_value=0, max_value=100, unit="%",
            needle_color="#1abc9c",  # Bright cyan/turquoise
            scale_color="#16a085",  # Darker cyan for scale
            text_color="#2c3e50"  # Dark text for visibility
        )
        self.gauges["Throttle"] = throttle_gauge
        grid.addWidget(throttle_gauge, 2, 1)

        layout.addLayout(grid)

        # Demo data timer (for fake data updates)
        # Don't start timer until widget is shown to prevent crashes
        self.demo_timer = QTimer(self)
        self.demo_timer.timeout.connect(self._update_demo_data)
        self.demo_time = 0.0
        self._timer_started = False
        
        # Set initial demo values so gauges show data immediately
        self._update_demo_data()
        
        # Force initial paint to ensure gauges are visible
        self.update()
        for gauge in self.gauges.values():
            gauge.setVisible(True)  # Ensure gauges are visible
            gauge.update()
            gauge.show()  # Ensure gauges are visible
            gauge.repaint()  # Force immediate repaint

    def update_data(self, data: Dict[str, float]) -> None:
        """Update gauges with real telemetry data."""
        # Map data keys to gauge keys
        key_mapping = {
            "RPM": "RPM",
            "Engine_RPM": "RPM",
            "Speed": "Speed",
            "Vehicle_Speed": "Speed",
            "Boost": "Boost",
            "Boost_Pressure": "Boost",
            "CoolantTemp": "CoolantTemp",
            "Coolant_Temp": "CoolantTemp",
            "OilPressure": "OilPressure",
            "Oil_Pressure": "OilPressure",
            "Throttle": "Throttle",
            "Throttle_Position": "Throttle",
            "DensityAltitude": "DensityAltitude",
            "Density_Altitude": "DensityAltitude",
            "DA": "DensityAltitude",
            "density_altitude_ft": "DensityAltitude",
        }

        for data_key, gauge_key in key_mapping.items():
            if data_key in data and gauge_key in self.gauges:
                self.gauges[gauge_key].set_value(data[data_key])

    def _update_demo_data(self) -> None:
        """Generate and update demo data for gauges."""
        import math
        import time

        # Only increment time if timer is running (not on initial call)
        if self._timer_started:
            self.demo_time += 0.1
        else:
            # Set initial time to a non-zero value for better initial display
            self.demo_time = 1.0
        
        t = self.demo_time

        # Generate realistic demo values
        demo_data = {
            "RPM": 800 + math.sin(t * 0.5) * 2000 + math.sin(t * 2) * 500,
            "Speed": max(0, 30 + math.sin(t * 0.3) * 40 + random.uniform(-5, 5)),
            "Boost": -1 + math.sin(t * 0.4) * 8 + random.uniform(-2, 2),
            "CoolantTemp": 85 + math.sin(t * 0.1) * 10 + random.uniform(-2, 2),
            "OilPressure": 45 + math.sin(t * 0.2) * 10 + random.uniform(-2, 2),
            "Throttle": 25 + math.sin(t * 0.3) * 30 + random.uniform(-5, 5),
        }

        # Clamp values to gauge ranges
        demo_data["RPM"] = max(0, min(8000, demo_data["RPM"]))
        demo_data["Speed"] = max(0, min(200, demo_data["Speed"]))
        demo_data["Boost"] = max(-5, min(30, demo_data["Boost"]))
        demo_data["CoolantTemp"] = max(70, min(120, demo_data["CoolantTemp"]))
        demo_data["OilPressure"] = max(20, min(80, demo_data["OilPressure"]))
        demo_data["Throttle"] = max(0, min(100, demo_data["Throttle"]))

        # Update all gauges with the demo data
        self.update_data(demo_data)
        
        # Force a repaint to ensure values are visible immediately
        for gauge in self.gauges.values():
            gauge.update()

    def stop_demo(self) -> None:
        """Stop demo data updates."""
        if self.demo_timer:
            self.demo_timer.stop()


__all__ = ["GaugePanel", "CircularGauge"]


