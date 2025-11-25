"""
Enhanced UI Widgets

Polished, modern widgets with consistent styling and animations.
Also provides shared layout and sizing helpers to keep the UI responsive.
"""

from __future__ import annotations

from typing import Optional

try:
    from PySide6.QtCore import QPropertyAnimation, QRect, Qt, QTimer, Property
    from PySide6.QtGui import QColor, QFont, QPainter, QPen
    from PySide6.QtWidgets import (
        QBoxLayout,
        QFrame,
        QHBoxLayout,
        QLabel,
        QProgressBar,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # Fallback for PyQt6
    from PyQt6.QtCore import QPropertyAnimation, QRect, Qt, QTimer, pyqtProperty as Property
    from PyQt6.QtGui import QColor, QFont, QPainter, QPen
    from PyQt6.QtWidgets import (
        QBoxLayout,
        QFrame,
        QHBoxLayout,
        QLabel,
        QProgressBar,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )


# ---------------------------------------------------------------------------
# Global layout / sizing helpers
# ---------------------------------------------------------------------------


def make_expanding(widget: QWidget) -> QWidget:
    """
    Make a widget expand in both directions within layouts.

    This is the default for major panels and graph containers.
    """
    widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    return widget


def make_hgrow(widget: QWidget) -> QWidget:
    """
    Make a widget expand horizontally but stay height-preferred.

    Good for toolbars, status bars, and button rows.
    """
    widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    return widget


def make_vgrow(widget: QWidget) -> QWidget:
    """
    Make a widget expand vertically but stay width-preferred.
    """
    widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
    return widget


def apply_standard_margins(
    layout: QBoxLayout,
    margin: int = 8,
    spacing: int = 6,
) -> QBoxLayout:
    """
    Apply consistent margins and spacing to a layout.
    """
    layout.setContentsMargins(margin, margin, margin, margin)
    layout.setSpacing(spacing)
    return layout


# ---------------------------------------------------------------------------
# Enhanced widgets
# ---------------------------------------------------------------------------


class MetricCard(QFrame):
    """Enhanced metric display card with animations."""

    def __init__(
        self,
        title: str,
        value: str = "--",
        unit: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setProperty("class", "metric-tile")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumHeight(100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        # Title
        self.title_label = QLabel(title.upper())
        self.title_label.setProperty("class", "subheading")
        # Note: font sizes are intentionally relative-ish; they are still
        # overridden by the global theme stylesheet.
        self.title_label.setStyleSheet(
            "font-size: 11px; color: #9aa0a6; font-weight: 600;"
        )
        layout.addWidget(self.title_label)

        # Value and unit
        value_layout = QHBoxLayout()
        value_layout.setContentsMargins(0, 0, 0, 0)
        value_layout.setSpacing(4)

        self.value_label = QLabel(value)
        # This will be blended with theme font-size-base; 32px is an upper
        # bound and will be scaled by the OS/Qt when window is smaller.
        self.value_label.setStyleSheet(
            "font-size: 32px; font-weight: 700; color: #00e0ff;"
        )
        value_layout.addWidget(self.value_label)

        if unit:
            self.unit_label = QLabel(unit)
            self.unit_label.setStyleSheet(
                "font-size: 16px; color: #9aa0a6; padding-top: 8px;"
            )
            value_layout.addWidget(self.unit_label)

        value_layout.addStretch()
        layout.addLayout(value_layout)

        # Trend indicator (optional)
        self.trend_label = QLabel()
        self.trend_label.setStyleSheet("font-size: 10px;")
        layout.addWidget(self.trend_label)

    def set_value(self, value: str, unit: str = "") -> None:
        """Update value."""
        self.value_label.setText(value)
        if unit and hasattr(self, "unit_label"):
            self.unit_label.setText(unit)

    def set_trend(self, trend: str, color: str = "#9aa0a6") -> None:
        """Set trend indicator."""
        self.trend_label.setText(trend)
        self.trend_label.setStyleSheet(f"font-size: 10px; color: {color};")


class StatusIndicator(QWidget):
    """Animated status indicator."""

    def __init__(self, size: int = 12, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.status = "ok"  # ok, warning, error
        self._pulse_animation = None

    def set_status(self, status: str) -> None:
        """Set status (ok, warning, error)."""
        self.status = status
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        """Paint status indicator."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color_map = {
            "ok": QColor("#00ff88"),
            "warning": QColor("#ffaa00"),
            "error": QColor("#ff4444"),
        }

        color = color_map.get(self.status, QColor("#9aa0a6"))
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(self.rect())


class AnimatedProgressBar(QProgressBar):
    """Progress bar with smooth animations."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._animated_value = 0
        self.animation = QPropertyAnimation(self, b"animatedValue")
        self.animation.setDuration(500)  # 500ms animation

    def setValue(self, value: int) -> None:  # noqa: N802
        """Set value with animation."""
        self.animation.stop()
        self.animation.setStartValue(self._animated_value)
        self.animation.setEndValue(value)
        self.animation.start()

    def get_animated_value(self) -> int:
        """Get animated value."""
        return self._animated_value

    def set_animated_value(self, value: int) -> None:
        """Set animated value."""
        self._animated_value = value
        super().setValue(value)

    animatedValue = Property(int, get_animated_value, set_animated_value)


class InfoPanel(QFrame):
    """Information panel with icon and text."""

    def __init__(
        self,
        title: str,
        message: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setProperty("class", "metric-tile")
        self.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        self.title_label = QLabel(title)
        self.title_label.setProperty("class", "heading")
        layout.addWidget(self.title_label)

        if message:
            self.message_label = QLabel(message)
            self.message_label.setWordWrap(True)
            self.message_label.setStyleSheet("color: #b0b8c4;")
            layout.addWidget(self.message_label)


class SectionHeader(QWidget):
    """Section header with divider line."""

    def __init__(self, text: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 8)

        self.label = QLabel(text.upper())
        self.label.setProperty("class", "heading")
        layout.addWidget(self.label)

        # Divider line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #2d3748;")
        layout.addWidget(line, 1)


__all__ = [
    "MetricCard",
    "StatusIndicator",
    "AnimatedProgressBar",
    "InfoPanel",
    "SectionHeader",
    "make_expanding",
    "make_hgrow",
    "make_vgrow",
    "apply_standard_margins",
]
