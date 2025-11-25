"""
================================================================================
DRAG MODE PANEL - Dodge Charger Daytona Scat Pack Style
================================================================================
A high-performance drag racing dashboard inspired by the Dodge Performance Pages.
Features authentic racing aesthetics with dark theme, Dodge red accents, and
real-time performance metrics.
================================================================================
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPainter, QPen, QBrush, QLinearGradient, QRadialGradient
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


# =============================================================================
# COLOR PALETTE - Dodge Charger Inspired
# =============================================================================
class DodgeColors:
    """Authentic Dodge racing color palette."""
    # Primary dark theme
    BACKGROUND = "#0d0d0d"
    PANEL_BG = "#141414"
    PANEL_BORDER = "#2a2a2a"
    
    # Dodge signature colors
    RED = "#ff2a2a"
    RED_GLOW = "#ff4444"
    ORANGE = "#ff6b00"
    AMBER = "#ffaa00"
    
    # Status colors
    GREEN = "#00ff44"
    YELLOW = "#ffff00"
    
    # Text colors
    WHITE = "#ffffff"
    GRAY = "#888888"
    DIM = "#444444"
    
    # Accent
    BLUE_ACCENT = "#00a8ff"


# =============================================================================
# DRAG STATE MACHINE
# =============================================================================
class DragState(Enum):
    """Drag racing state machine."""
    IDLE = "IDLE"
    STAGING = "STAGING"
    READY = "READY"
    LAUNCHED = "LAUNCHED"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"


# =============================================================================
# STAGING LIGHT WIDGET - Christmas Tree
# =============================================================================
class StagingLightWidget(QWidget):
    """Drag racing Christmas tree staging lights."""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(60, 140)
        
        # Light states: 0=off, 1=on
        self.pre_stage = False
        self.staged = False
        self.amber_lights = [False, False, False]  # 3 amber lights
        self.green_light = False
        self.red_light = False
        
    def set_pre_stage(self, on: bool) -> None:
        self.pre_stage = on
        self.update()
        
    def set_staged(self, on: bool) -> None:
        self.staged = on
        self.update()
        
    def set_amber(self, index: int, on: bool) -> None:
        if 0 <= index < 3:
            self.amber_lights[index] = on
            self.update()
            
    def set_green(self, on: bool) -> None:
        self.green_light = on
        self.update()
        
    def set_red(self, on: bool) -> None:
        self.red_light = on
        self.update()
        
    def reset(self) -> None:
        self.pre_stage = False
        self.staged = False
        self.amber_lights = [False, False, False]
        self.green_light = False
        self.red_light = False
        self.update()
        
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background housing
        painter.setPen(QPen(QColor("#333333"), 2))
        painter.setBrush(QColor("#1a1a1a"))
        painter.drawRoundedRect(2, 2, self.width() - 4, self.height() - 4, 8, 8)
        
        cx = self.width() // 2
        light_size = 14
        y_start = 15
        y_spacing = 22
        
        def draw_light(y: int, on: bool, color_on: str, color_off: str) -> None:
            if on:
                # Glow effect
                glow = QRadialGradient(cx, y, light_size)
                glow.setColorAt(0, QColor(color_on))
                glow.setColorAt(0.5, QColor(color_on).darker(150))
                glow.setColorAt(1, QColor("transparent"))
                painter.setBrush(glow)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(cx - light_size, y - light_size, light_size * 2, light_size * 2)
                
                painter.setBrush(QColor(color_on))
                painter.setPen(QPen(QColor("#ffffff"), 1))
            else:
                painter.setBrush(QColor(color_off))
                painter.setPen(QPen(QColor("#333333"), 1))
            
            painter.drawEllipse(cx - light_size // 2, y - light_size // 2, light_size, light_size)
        
        # Pre-stage (blue/white)
        draw_light(y_start, self.pre_stage, "#4488ff", "#222244")
        
        # Staged (blue/white)
        draw_light(y_start + y_spacing, self.staged, "#4488ff", "#222244")
        
        # Amber lights (3)
        for i in range(3):
            draw_light(y_start + y_spacing * (2 + i), self.amber_lights[i], DodgeColors.AMBER, "#332200")
        
        # Green light
        draw_light(y_start + y_spacing * 5, self.green_light, DodgeColors.GREEN, "#003300")
        
        # Red light (foul)
        # draw_light(y_start + y_spacing * 6, self.red_light, DodgeColors.RED, "#330000")


# =============================================================================
# METRIC DISPLAY WIDGET - LAST/BEST Values
# =============================================================================
class DragMetricDisplay(QWidget):
    """Individual drag metric with LAST and BEST values."""
    
    def __init__(self, title: str, suffix: str = "s", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.title = title
        self.suffix = suffix
        self.last_value: Optional[float] = None
        self.best_value: Optional[float] = None
        self.is_new_best = False
        
        self.setMinimumHeight(70)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
    def set_last(self, value: Optional[float]) -> None:
        self.last_value = value
        self.update()
        
    def set_best(self, value: Optional[float]) -> None:
        old_best = self.best_value
        self.best_value = value
        self.is_new_best = old_best is not None and value is not None and value < old_best
        self.update()
        
    def format_value(self, value: Optional[float]) -> str:
        if value is None:
            return "-.---" if "s" in self.suffix else "---.-"
        if "MPH" in self.suffix or "mph" in self.suffix.upper():
            return f"{value:.1f}"
        return f"{value:.3f}"
        
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Background with subtle gradient
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, QColor(DodgeColors.PANEL_BG))
        grad.setColorAt(1, QColor("#0a0a0a"))
        painter.setBrush(grad)
        painter.setPen(QPen(QColor(DodgeColors.PANEL_BORDER), 1))
        painter.drawRoundedRect(1, 1, w - 2, h - 2, 6, 6)
        
        # Title
        title_font = QFont("Arial", 9, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor(DodgeColors.ORANGE))
        painter.drawText(8, 16, self.title)
        
        # LAST value (large, prominent)
        value_font = QFont("Consolas", 18, QFont.Weight.Bold)
        painter.setFont(value_font)
        
        last_text = self.format_value(self.last_value)
        if self.last_value is not None:
            painter.setPen(QColor(DodgeColors.WHITE))
        else:
            painter.setPen(QColor(DodgeColors.DIM))
        
        painter.drawText(8, 42, last_text)
        
        # Suffix
        suffix_font = QFont("Arial", 10)
        painter.setFont(suffix_font)
        painter.setPen(QColor(DodgeColors.GRAY))
        suffix_x = 8 + painter.fontMetrics().horizontalAdvance(last_text) + 4
        # Measure with value font
        painter.setFont(value_font)
        suffix_x = 8 + painter.fontMetrics().horizontalAdvance(last_text) + 4
        painter.setFont(suffix_font)
        painter.drawText(int(suffix_x), 42, self.suffix)
        
        # BEST value (smaller, right side)
        best_text = f"BEST: {self.format_value(self.best_value)}"
        painter.setFont(QFont("Arial", 8))
        
        if self.is_new_best:
            painter.setPen(QColor(DodgeColors.GREEN))
        elif self.best_value is not None:
            painter.setPen(QColor(DodgeColors.AMBER))
        else:
            painter.setPen(QColor(DodgeColors.DIM))
            
        best_width = painter.fontMetrics().horizontalAdvance(best_text)
        painter.drawText(w - best_width - 10, 62, best_text)
        
        # "LAST" label
        painter.setPen(QColor(DodgeColors.GRAY))
        painter.drawText(8, 62, "LAST")


# =============================================================================
# READY INDICATOR - Flashing Status
# =============================================================================
class ReadyIndicator(QWidget):
    """Flashing READY/STAGING/GO indicator."""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(50)
        
        self._state = DragState.IDLE
        self._flash_on = True
        self._opacity = 1.0
        
        # Flash timer
        self._flash_timer = QTimer(self)
        self._flash_timer.timeout.connect(self._toggle_flash)
        self._flash_timer.start(500)  # 500ms flash
        
    def set_state(self, state: DragState) -> None:
        self._state = state
        self.update()
        
    def _toggle_flash(self) -> None:
        if self._state in (DragState.READY, DragState.STAGING):
            self._flash_on = not self._flash_on
            self.update()
            
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Determine text and color based on state
        if self._state == DragState.IDLE:
            text = "DRAG MODE"
            color = DodgeColors.RED
            show = True
        elif self._state == DragState.STAGING:
            text = "STAGING"
            color = DodgeColors.AMBER
            show = self._flash_on
        elif self._state == DragState.READY:
            text = "READY"
            color = DodgeColors.GREEN
            show = self._flash_on
        elif self._state == DragState.LAUNCHED:
            text = "GO!"
            color = DodgeColors.GREEN
            show = True
        elif self._state == DragState.RUNNING:
            text = "RUNNING"
            color = DodgeColors.GREEN
            show = True
        elif self._state == DragState.COMPLETE:
            text = "COMPLETE"
            color = DodgeColors.AMBER
            show = True
        else:
            text = "---"
            color = DodgeColors.GRAY
            show = True
        
        # Background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(DodgeColors.PANEL_BG))
        painter.drawRoundedRect(0, 0, w, h, 8, 8)
        
        if show:
            # Glow effect behind text
            glow_color = QColor(color)
            glow_color.setAlpha(50)
            painter.setBrush(glow_color)
            painter.drawRoundedRect(10, 5, w - 20, h - 10, 4, 4)
            
            # Text
            font = QFont("Impact", 24, QFont.Weight.Bold)
            painter.setFont(font)
            painter.setPen(QColor(color))
            
            text_rect = painter.fontMetrics().boundingRect(text)
            x = (w - text_rect.width()) // 2
            y = (h + text_rect.height()) // 2 - 4
            painter.drawText(x, y, text)
        
        # Border
        painter.setPen(QPen(QColor(color if show else DodgeColors.DIM), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(2, 2, w - 4, h - 4, 6, 6)


# =============================================================================
# MAIN DRAG MODE PANEL
# =============================================================================
class DragModePanel(QFrame):
    """
    Complete Dodge Charger-style Drag Mode dashboard.
    
    Features:
    - Dark racing theme with Dodge red/orange accents
    - Christmas tree staging lights
    - All standard drag metrics with LAST/BEST values
    - Animated READY indicator
    - Real-time performance tracking
    """
    
    METRICS = [
        ("REACTION TIME", "s"),
        ("60 FT", "s"),
        ("330 FT", "s"),
        ("1/8 MILE ET", "s"),
        ("1/8 MILE", "MPH"),
        ("1/4 MILE ET", "s"),
        ("1/4 MILE", "MPH"),
        ("TRAP SPEED", "MPH"),
    ]
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName("dragModePanel")
        
        # Dark theme styling
        self.setStyleSheet(f"""
            QFrame#dragModePanel {{
                background-color: {DodgeColors.BACKGROUND};
                border: 2px solid {DodgeColors.RED};
                border-radius: 10px;
            }}
        """)
        
        self._state = DragState.IDLE
        self._build_ui()
        
        # Demo timer for staging sequence
        self._demo_timer = QTimer(self)
        self._demo_timer.timeout.connect(self._demo_sequence_step)
        self._demo_step = 0
        
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(8)
        
        # ===== HEADER =====
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # Title with racing stripe
        title = QLabel("◀ DRAG MODE ▶")
        title.setFont(QFont("Impact", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"""
            color: {DodgeColors.RED};
            background-color: transparent;
            padding: 4px 12px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)
        
        layout.addLayout(header_layout)
        
        # ===== READY INDICATOR =====
        self.ready_indicator = ReadyIndicator()
        layout.addWidget(self.ready_indicator)
        
        # ===== MAIN CONTENT =====
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)
        
        # Left: Staging lights
        self.staging_lights = StagingLightWidget()
        content_layout.addWidget(self.staging_lights)
        
        # Right: Metrics grid
        metrics_widget = QWidget()
        metrics_layout = QGridLayout(metrics_widget)
        metrics_layout.setContentsMargins(0, 0, 0, 0)
        metrics_layout.setSpacing(6)
        
        self.metric_displays: Dict[str, DragMetricDisplay] = {}
        
        for i, (name, suffix) in enumerate(self.METRICS):
            display = DragMetricDisplay(name, suffix)
            row = i // 2
            col = i % 2
            metrics_layout.addWidget(display, row, col)
            self.metric_displays[name] = display
        
        content_layout.addWidget(metrics_widget, 1)
        layout.addWidget(QWidget())  # Spacer
        layout.addLayout(content_layout)
        
        # ===== FOOTER - G-Force Display =====
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(20)
        
        self.gforce_label = QLabel("G-FORCE: 0.00 G")
        self.gforce_label.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        self.gforce_label.setStyleSheet(f"color: {DodgeColors.AMBER}; background: transparent;")
        footer_layout.addWidget(self.gforce_label)
        
        self.speed_label = QLabel("SPEED: 0 MPH")
        self.speed_label.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        self.speed_label.setStyleSheet(f"color: {DodgeColors.GREEN}; background: transparent;")
        footer_layout.addWidget(self.speed_label)
        
        self.rpm_label = QLabel("RPM: 0")
        self.rpm_label.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        self.rpm_label.setStyleSheet(f"color: {DodgeColors.RED}; background: transparent;")
        footer_layout.addWidget(self.rpm_label)
        
        footer_layout.addStretch()
        layout.addLayout(footer_layout)
        
    # =========================================================================
    # PUBLIC API
    # =========================================================================
    
    def set_state(self, state: DragState) -> None:
        """Set the current drag state."""
        self._state = state
        self.ready_indicator.set_state(state)
        
        if state == DragState.IDLE:
            self.staging_lights.reset()
        elif state == DragState.STAGING:
            self.staging_lights.set_pre_stage(True)
        elif state == DragState.READY:
            self.staging_lights.set_pre_stage(True)
            self.staging_lights.set_staged(True)
            
    def run_staging_sequence(self) -> None:
        """Run the full staging light sequence (for demo/testing)."""
        self._demo_step = 0
        self._demo_timer.start(400)
        
    def _demo_sequence_step(self) -> None:
        """Execute one step of the demo staging sequence."""
        if self._demo_step == 0:
            self.set_state(DragState.STAGING)
        elif self._demo_step == 1:
            self.staging_lights.set_staged(True)
            self.set_state(DragState.READY)
        elif self._demo_step == 2:
            self.staging_lights.set_amber(0, True)
        elif self._demo_step == 3:
            self.staging_lights.set_amber(1, True)
        elif self._demo_step == 4:
            self.staging_lights.set_amber(2, True)
        elif self._demo_step == 5:
            self.staging_lights.set_green(True)
            self.set_state(DragState.LAUNCHED)
        elif self._demo_step == 6:
            self.set_state(DragState.RUNNING)
        elif self._demo_step > 10:
            self.set_state(DragState.COMPLETE)
            self._demo_timer.stop()
            
        self._demo_step += 1
        
    def update_metric(self, name: str, last: Optional[float], best: Optional[float] = None) -> None:
        """Update a specific metric's values."""
        if name in self.metric_displays:
            self.metric_displays[name].set_last(last)
            if best is not None:
                self.metric_displays[name].set_best(best)
                
    def update_from_snapshot(self, snapshot: "PerformanceSnapshot") -> None:
        """Update all metrics from a performance snapshot."""
        # Map snapshot keys to display names
        key_map = {
            "reaction_time": "REACTION TIME",
            "60ft": "60 FT",
            "330ft": "330 FT",
            "eighth_mile_et": "1/8 MILE ET",
            "eighth_mile_speed": "1/8 MILE",
            "quarter_mile_et": "1/4 MILE ET",
            "quarter_mile_speed": "1/4 MILE",
            "trap_speed": "TRAP SPEED",
        }
        
        metrics = getattr(snapshot, 'metrics', {})
        best_metrics = getattr(snapshot, 'best_metrics', {})
        
        for snap_key, display_name in key_map.items():
            if display_name in self.metric_displays:
                last_val = metrics.get(snap_key)
                best_val = best_metrics.get(snap_key)
                self.metric_displays[display_name].set_last(last_val)
                self.metric_displays[display_name].set_best(best_val)
                
    def update_gforce(self, g: float) -> None:
        """Update G-force display."""
        self.gforce_label.setText(f"G-FORCE: {g:.2f} G")
        
    def update_speed(self, mph: float) -> None:
        """Update speed display."""
        self.speed_label.setText(f"SPEED: {int(mph)} MPH")
        
    def update_rpm(self, rpm: int) -> None:
        """Update RPM display."""
        self.rpm_label.setText(f"RPM: {rpm:,}")
        
    def reset(self) -> None:
        """Reset all displays to default state."""
        self.set_state(DragState.IDLE)
        for display in self.metric_displays.values():
            display.set_last(None)
        self.update_gforce(0)
        self.update_speed(0)
        self.update_rpm(0)


# =============================================================================
# COMPACT VERSION FOR SIDEBAR
# =============================================================================
class DragModeCompactPanel(QFrame):
    """
    Compact version of Drag Mode for sidebar integration.
    Shows key metrics in a smaller footprint.
    """
    
    KEY_METRICS = [
        ("0-60", "s"),
        ("1/8 MI", "s"),
        ("1/4 MI", "s"),
        ("TRAP", "MPH"),
    ]
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName("dragModeCompact")
        
        self.setStyleSheet(f"""
            QFrame#dragModeCompact {{
                background-color: {DodgeColors.BACKGROUND};
                border: 1px solid {DodgeColors.RED};
                border-radius: 8px;
            }}
        """)
        
        self._build_ui()
        
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 8)
        layout.setSpacing(4)
        
        # Header
        header = QLabel("🏁 DRAG MODE")
        header.setFont(QFont("Impact", 12, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {DodgeColors.RED}; background: transparent;")
        layout.addWidget(header)
        
        # Ready indicator (compact)
        self.ready_label = QLabel("READY")
        self.ready_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        self.ready_label.setStyleSheet(f"""
            color: {DodgeColors.GREEN};
            background-color: #001a00;
            border: 1px solid {DodgeColors.GREEN};
            border-radius: 4px;
            padding: 2px 8px;
        """)
        self.ready_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ready_label.setFixedHeight(22)
        layout.addWidget(self.ready_label)
        
        # Metrics grid (2x2)
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(4)
        
        self.metric_labels: Dict[str, QLabel] = {}
        
        for i, (name, suffix) in enumerate(self.KEY_METRICS):
            container = QWidget()
            container.setStyleSheet(f"""
                background-color: {DodgeColors.PANEL_BG};
                border: 1px solid {DodgeColors.PANEL_BORDER};
                border-radius: 4px;
            """)
            
            clayout = QVBoxLayout(container)
            clayout.setContentsMargins(4, 2, 4, 2)
            clayout.setSpacing(0)
            
            title = QLabel(name)
            title.setFont(QFont("Arial", 7, QFont.Weight.Bold))
            title.setStyleSheet(f"color: {DodgeColors.ORANGE}; background: transparent; border: none;")
            clayout.addWidget(title)
            
            value = QLabel(f"-.--- {suffix}")
            value.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
            value.setStyleSheet(f"color: {DodgeColors.WHITE}; background: transparent; border: none;")
            clayout.addWidget(value)
            
            self.metric_labels[name] = value
            
            row, col = i // 2, i % 2
            metrics_grid.addWidget(container, row, col)
            
        layout.addLayout(metrics_grid)
        
    def update_metric(self, name: str, value: Optional[float], suffix: str = "s") -> None:
        """Update a metric value."""
        if name in self.metric_labels:
            if value is None:
                self.metric_labels[name].setText(f"-.--- {suffix}")
                self.metric_labels[name].setStyleSheet(f"color: {DodgeColors.DIM}; background: transparent; border: none;")
            else:
                if "MPH" in suffix:
                    self.metric_labels[name].setText(f"{value:.1f} {suffix}")
                else:
                    self.metric_labels[name].setText(f"{value:.3f} {suffix}")
                self.metric_labels[name].setStyleSheet(f"color: {DodgeColors.WHITE}; background: transparent; border: none;")
                
    def set_ready_state(self, state: str, color: str = DodgeColors.GREEN) -> None:
        """Update the ready indicator state."""
        self.ready_label.setText(state)
        bg_color = QColor(color).darker(400).name()
        self.ready_label.setStyleSheet(f"""
            color: {color};
            background-color: {bg_color};
            border: 1px solid {color};
            border-radius: 4px;
            padding: 2px 8px;
        """)


__all__ = [
    "DragModePanel",
    "DragModeCompactPanel", 
    "DragState",
    "DodgeColors",
]





