"""
Wheel Slip Widget - Visual display for drag racing wheel slip monitoring.

Displays:
- Current slip percentage with color-coded gauge
- Optimal slip range indicator
- Real-time status (Low/Optimal/Excessive/Critical)
- Historical slip graph
- Traction control recommendations
"""

from __future__ import annotations

import math
from collections import deque
from typing import Deque, Optional

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class WheelSlipGauge(QWidget):
    """
    Circular gauge specifically designed for wheel slip visualization.
    
    Features:
    - Arc gauge from -20% to 50% slip
    - Color zones: Blue (low), Green (optimal), Orange (moderate), Red (excessive)
    - Optimal range indicator band
    - Large digital readout
    """
    
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        optimal_min: float = 5.0,
        optimal_max: float = 12.0,
    ) -> None:
        super().__init__(parent)
        
        self.min_value = -20.0  # Lockup (braking)
        self.max_value = 50.0   # Excessive spin
        self.current_value = 0.0
        self.optimal_min = optimal_min
        self.optimal_max = optimal_max
        
        # Colors
        self.lockup_color = "#2c3e50"      # Dark gray-blue
        self.low_color = "#3498db"          # Blue
        self.optimal_color = "#27ae60"      # Green
        self.moderate_color = "#f39c12"     # Orange
        self.excessive_color = "#e74c3c"    # Red
        self.critical_color = "#8e44ad"     # Purple
        self.background_color = "#1a1f35"
        self.text_color = "#ffffff"
        
        self.setMinimumSize(160, 180)
        self.setMaximumSize(200, 220)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
    def set_value(self, value: float) -> None:
        """Update the displayed slip percentage."""
        self.current_value = max(self.min_value, min(self.max_value, value))
        self.update()
    
    def set_optimal_range(self, min_val: float, max_val: float) -> None:
        """Set the optimal slip range."""
        self.optimal_min = min_val
        self.optimal_max = max_val
        self.update()
    
    def _get_color_for_value(self, value: float) -> QColor:
        """Get the appropriate color for a slip value."""
        if value < -5:
            return QColor(self.lockup_color)
        elif value < self.optimal_min:
            return QColor(self.low_color)
        elif value <= self.optimal_max:
            return QColor(self.optimal_color)
        elif value <= 20:
            return QColor(self.moderate_color)
        elif value <= 35:
            return QColor(self.excessive_color)
        else:
            return QColor(self.critical_color)
    
    def _value_to_angle(self, value: float) -> float:
        """Convert value to angle (in degrees)."""
        # 270 degree arc from -135 to 135 degrees
        range_span = self.max_value - self.min_value
        normalized = (value - self.min_value) / range_span
        return -135 + (normalized * 270)
    
    def paintEvent(self, event) -> None:  # noqa: N802
        """Paint the wheel slip gauge."""
        try:
            if self.width() < 20 or self.height() < 20:
                return
            
            painter = QPainter(self)
            if not painter.isActive():
                return
            
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            width = self.width()
            height = self.height()
            size = min(width, height) - 40
            if size <= 0:
                return
            
            x = (width - size) // 2
            y = (height - size) // 2 + 15
            
            # Draw background arc
            bg_color = QColor(self.background_color)
            bg_color.setAlpha(100)
            pen = QPen(bg_color, 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawArc(x, y, size, size, -135 * 16, 270 * 16)
            
            # Draw color zones
            self._draw_zone(painter, x, y, size, -20, 0, self.lockup_color, 10)
            self._draw_zone(painter, x, y, size, 0, self.optimal_min, self.low_color, 10)
            self._draw_zone(painter, x, y, size, self.optimal_min, self.optimal_max, self.optimal_color, 14)  # Thicker optimal zone
            self._draw_zone(painter, x, y, size, self.optimal_max, 20, self.moderate_color, 10)
            self._draw_zone(painter, x, y, size, 20, 35, self.excessive_color, 10)
            self._draw_zone(painter, x, y, size, 35, 50, self.critical_color, 10)
            
            # Draw current value indicator (needle)
            current_angle = self._value_to_angle(self.current_value)
            needle_color = self._get_color_for_value(self.current_value)
            
            # Draw needle as a line from center
            center_x = x + size // 2
            center_y = y + size // 2
            needle_length = size // 2 - 8
            
            angle_rad = math.radians(current_angle - 90)  # Adjust for Qt coordinate system
            end_x = center_x + needle_length * math.cos(angle_rad)
            end_y = center_y + needle_length * math.sin(angle_rad)
            
            # Needle shadow
            shadow_pen = QPen(QColor(0, 0, 0, 80), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(shadow_pen)
            painter.drawLine(int(center_x + 2), int(center_y + 2), int(end_x + 2), int(end_y + 2))
            
            # Needle
            needle_pen = QPen(needle_color, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(needle_pen)
            painter.drawLine(int(center_x), int(center_y), int(end_x), int(end_y))
            
            # Center dot
            painter.setBrush(QBrush(needle_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(center_x - 6), int(center_y - 6), 12, 12)
            
            # Draw value text
            painter.setPen(QColor(self.text_color))
            font = QFont("Arial", 18, QFont.Weight.Bold)
            painter.setFont(font)
            
            # Format value with sign
            if self.current_value >= 0:
                value_text = f"+{self.current_value:.1f}%"
            else:
                value_text = f"{self.current_value:.1f}%"
            
            text_rect = painter.fontMetrics().boundingRect(value_text)
            painter.drawText(
                width // 2 - text_rect.width() // 2,
                height - 25,
                value_text,
            )
            
            # Draw title
            font = QFont("Arial", 10, QFont.Weight.Bold)
            painter.setFont(font)
            title_text = "WHEEL SLIP"
            title_rect = painter.fontMetrics().boundingRect(title_text)
            painter.drawText(
                width // 2 - title_rect.width() // 2,
                18,
                title_text,
            )
            
            # Draw status text
            status = self._get_status_text()
            status_color = self._get_color_for_value(self.current_value)
            painter.setPen(status_color)
            font = QFont("Arial", 9, QFont.Weight.Bold)
            painter.setFont(font)
            status_rect = painter.fontMetrics().boundingRect(status)
            painter.drawText(
                width // 2 - status_rect.width() // 2,
                height - 8,
                status,
            )
            
        except Exception as e:
            print(f"[WARN] WheelSlipGauge.paintEvent error: {e}")
    
    def _draw_zone(
        self,
        painter: QPainter,
        x: int,
        y: int,
        size: int,
        start_val: float,
        end_val: float,
        color: str,
        width: int,
    ) -> None:
        """Draw a colored zone on the gauge."""
        start_angle = self._value_to_angle(start_val)
        end_angle = self._value_to_angle(end_val)
        span = end_angle - start_angle
        
        pen = QPen(QColor(color), width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        # Qt uses 1/16th of a degree, and positive angles go counter-clockwise
        painter.drawArc(x, y, size, size, int(-start_angle * 16), int(-span * 16))
    
    def _get_status_text(self) -> str:
        """Get status text for current value."""
        if self.current_value < -5:
            return "LOCKUP"
        elif self.current_value < self.optimal_min:
            return "LOW"
        elif self.current_value <= self.optimal_max:
            return "OPTIMAL"
        elif self.current_value <= 20:
            return "MODERATE"
        elif self.current_value <= 35:
            return "EXCESSIVE"
        else:
            return "CRITICAL"


class SlipHistoryGraph(QWidget):
    """
    Mini graph showing slip history over time.
    """
    
    def __init__(self, parent: Optional[QWidget] = None, history_size: int = 60) -> None:
        super().__init__(parent)
        
        self.history: Deque[float] = deque(maxlen=history_size)
        self.optimal_min = 5.0
        self.optimal_max = 12.0
        
        self.setMinimumSize(200, 60)
        self.setMaximumHeight(80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Fill with zeros initially
        for _ in range(history_size):
            self.history.append(0.0)
    
    def add_value(self, value: float) -> None:
        """Add a new slip value to history."""
        self.history.append(value)
        self.update()
    
    def set_optimal_range(self, min_val: float, max_val: float) -> None:
        """Set optimal range for visualization."""
        self.optimal_min = min_val
        self.optimal_max = max_val
        self.update()
    
    def paintEvent(self, event) -> None:  # noqa: N802
        """Paint the history graph."""
        try:
            if not self.history or self.width() < 20:
                return
            
            painter = QPainter(self)
            if not painter.isActive():
                return
            
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            width = self.width()
            height = self.height()
            padding = 5
            
            # Background
            painter.fillRect(0, 0, width, height, QColor("#1a1f35"))
            
            # Draw optimal zone band
            y_range = 70.0  # -20 to 50
            y_scale = (height - 2 * padding) / y_range
            
            optimal_top = height - padding - (self.optimal_max + 20) * y_scale
            optimal_bottom = height - padding - (self.optimal_min + 20) * y_scale
            
            optimal_zone = QColor("#27ae60")
            optimal_zone.setAlpha(40)
            painter.fillRect(
                int(padding),
                int(optimal_top),
                int(width - 2 * padding),
                int(optimal_bottom - optimal_top),
                optimal_zone,
            )
            
            # Draw zero line
            zero_y = height - padding - (0 + 20) * y_scale
            pen = QPen(QColor("#ffffff"), 1, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawLine(int(padding), int(zero_y), int(width - padding), int(zero_y))
            
            # Draw slip line
            if len(self.history) < 2:
                return
            
            points = list(self.history)
            x_step = (width - 2 * padding) / (len(points) - 1)
            
            path = QPainterPath()
            for i, value in enumerate(points):
                x = padding + i * x_step
                y = height - padding - (value + 20) * y_scale
                y = max(padding, min(height - padding, y))
                
                if i == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
            
            # Get color based on latest value
            latest = points[-1]
            if latest < self.optimal_min:
                color = QColor("#3498db")
            elif latest <= self.optimal_max:
                color = QColor("#27ae60")
            elif latest <= 20:
                color = QColor("#f39c12")
            else:
                color = QColor("#e74c3c")
            
            pen = QPen(color, 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawPath(path)
            
        except Exception as e:
            print(f"[WARN] SlipHistoryGraph.paintEvent error: {e}")


class WheelSlipPanel(QFrame):
    """
    Complete wheel slip monitoring panel.
    
    Contains:
    - Slip gauge
    - Status indicators
    - History graph
    - Statistics
    - Recommendations
    """
    
    slip_threshold_exceeded = Signal(float)  # Emitted when slip exceeds warning threshold
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self.setProperty("class", "metric-tile")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
            }
            QLabel {
                background: transparent;
                color: #2c3e50;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        self.setMinimumSize(280, 380)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("🏁 Wheel Slip Monitor")
        title.setStyleSheet("font-size: 14px; font-weight: 700; color: #2c3e50;")
        layout.addWidget(title)
        
        # Gauge
        self.gauge = WheelSlipGauge(self)
        gauge_container = QWidget()
        gauge_layout = QHBoxLayout(gauge_container)
        gauge_layout.addStretch()
        gauge_layout.addWidget(self.gauge)
        gauge_layout.addStretch()
        layout.addWidget(gauge_container)
        
        # Stats group
        stats_group = QGroupBox("Statistics")
        stats_layout = QGridLayout(stats_group)
        stats_layout.setSpacing(6)
        
        # Stats labels
        self.avg_label = QLabel("Avg: --")
        self.max_label = QLabel("Max: --")
        self.optimal_time_label = QLabel("Optimal: --%")
        self.status_label = QLabel("Status: Ready")
        
        stats_layout.addWidget(self.avg_label, 0, 0)
        stats_layout.addWidget(self.max_label, 0, 1)
        stats_layout.addWidget(self.optimal_time_label, 1, 0)
        stats_layout.addWidget(self.status_label, 1, 1)
        
        layout.addWidget(stats_group)
        
        # History graph
        graph_group = QGroupBox("Slip History (60s)")
        graph_layout = QVBoxLayout(graph_group)
        self.history_graph = SlipHistoryGraph(self)
        graph_layout.addWidget(self.history_graph)
        layout.addWidget(graph_group)
        
        # Recommendation area
        self.recommendation_label = QLabel("")
        self.recommendation_label.setWordWrap(True)
        self.recommendation_label.setStyleSheet(
            "padding: 8px; background: #f8f9fa; border-radius: 4px; color: #2c3e50;"
        )
        self.recommendation_label.hide()
        layout.addWidget(self.recommendation_label)
        
        layout.addStretch()
        
        # Demo timer for testing
        self.demo_timer = QTimer(self)
        self.demo_timer.timeout.connect(self._update_demo_data)
        self.demo_time = 0.0
        
        # Track stats
        self._slip_history: Deque[float] = deque(maxlen=1000)
        self._max_slip = 0.0
        self._optimal_count = 0
        self._total_count = 0
    
    def update_slip(
        self,
        slip_percentage: float,
        status: str = "",
        recommendation: str = "",
    ) -> None:
        """
        Update the panel with new slip data.
        
        Args:
            slip_percentage: Current wheel slip percentage
            status: Status string (optional)
            recommendation: Traction recommendation (optional)
        """
        # Update gauge
        self.gauge.set_value(slip_percentage)
        
        # Update history
        self.history_graph.add_value(slip_percentage)
        self._slip_history.append(slip_percentage)
        
        # Update stats
        self._total_count += 1
        self._max_slip = max(self._max_slip, slip_percentage)
        
        optimal_min, optimal_max = self.gauge.optimal_min, self.gauge.optimal_max
        if optimal_min <= slip_percentage <= optimal_max:
            self._optimal_count += 1
        
        # Update labels
        avg_slip = sum(self._slip_history) / len(self._slip_history) if self._slip_history else 0
        self.avg_label.setText(f"Avg: {avg_slip:.1f}%")
        self.max_label.setText(f"Max: {self._max_slip:.1f}%")
        
        optimal_pct = (self._optimal_count / self._total_count * 100) if self._total_count > 0 else 0
        self.optimal_time_label.setText(f"Optimal: {optimal_pct:.1f}%")
        
        if status:
            self.status_label.setText(f"Status: {status}")
        
        # Update recommendation
        if recommendation:
            self.recommendation_label.setText(f"💡 {recommendation}")
            self.recommendation_label.show()
            
            # Color based on severity
            if "immediate" in recommendation.lower() or "critical" in recommendation.lower():
                self.recommendation_label.setStyleSheet(
                    "padding: 8px; background: #ffebee; border-radius: 4px; color: #c62828;"
                )
            elif "reduce" in recommendation.lower():
                self.recommendation_label.setStyleSheet(
                    "padding: 8px; background: #fff3e0; border-radius: 4px; color: #e65100;"
                )
            else:
                self.recommendation_label.setStyleSheet(
                    "padding: 8px; background: #e8f5e9; border-radius: 4px; color: #2e7d32;"
                )
        else:
            self.recommendation_label.hide()
        
        # Emit warning signal if needed
        if slip_percentage > 20:
            self.slip_threshold_exceeded.emit(slip_percentage)
    
    def set_optimal_range(self, min_val: float, max_val: float) -> None:
        """Set the optimal slip range."""
        self.gauge.set_optimal_range(min_val, max_val)
        self.history_graph.set_optimal_range(min_val, max_val)
    
    def reset_stats(self) -> None:
        """Reset statistics for a new run."""
        self._slip_history.clear()
        self._max_slip = 0.0
        self._optimal_count = 0
        self._total_count = 0
        self.avg_label.setText("Avg: --")
        self.max_label.setText("Max: --")
        self.optimal_time_label.setText("Optimal: --%")
        self.status_label.setText("Status: Ready")
        self.recommendation_label.hide()
    
    def start_demo(self) -> None:
        """Start demo mode with simulated data."""
        self.demo_timer.start(100)  # 10 Hz updates
    
    def stop_demo(self) -> None:
        """Stop demo mode."""
        self.demo_timer.stop()
    
    def _update_demo_data(self) -> None:
        """Generate demo slip data."""
        import math
        import random
        
        self.demo_time += 0.1
        t = self.demo_time
        
        # Simulate a drag launch pattern
        phase = (t % 15)  # 15 second cycle
        
        if phase < 2:
            # Launch phase - high slip
            base_slip = 15 + 10 * math.sin(phase * 3)
        elif phase < 5:
            # Accelerating - moderate slip
            base_slip = 8 + 5 * math.sin(phase * 2)
        elif phase < 10:
            # Cruising - optimal slip
            base_slip = 7 + 3 * math.sin(phase)
        else:
            # Coasting - low slip
            base_slip = 2 + 2 * math.sin(phase * 0.5)
        
        # Add noise
        slip = base_slip + random.uniform(-2, 2)
        slip = max(-5, min(45, slip))
        
        # Generate status
        if slip < 5:
            status = "Low"
            rec = ""
        elif slip <= 12:
            status = "Optimal"
            rec = ""
        elif slip <= 20:
            status = "Moderate"
            rec = "Consider reducing throttle slightly"
        else:
            status = "Excessive"
            rec = "Reduce throttle to optimize traction!"
        
        self.update_slip(slip, status, rec)


__all__ = [
    "WheelSlipPanel",
    "WheelSlipGauge",
    "SlipHistoryGraph",
]






