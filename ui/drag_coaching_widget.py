"""
Drag Racing Coaching Widget

Displays real-time coaching advice for improving drag racing times.
"""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

from services.drag_racing_analyzer import DragCoachingAdvice, DragSegment


class DragCoachingWidget(QWidget):
    """Widget that displays drag racing coaching advice."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self) -> None:
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Title
        title = QLabel("Drag Racing Coach")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title.setFont(title_font)
        title.setStyleSheet("color: #4285f4; margin-bottom: 10px;")
        layout.addWidget(title)

        # Scroll area for advice
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        self.advice_container = QWidget()
        self.advice_layout = QVBoxLayout(self.advice_container)
        self.advice_layout.setSpacing(8)
        self.advice_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll.setWidget(self.advice_container)
        layout.addWidget(scroll)

        # Initial message
        self.empty_label = QLabel("No coaching advice yet.\nComplete a run to get tips!")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: #9aa0a6; font-size: 12px; padding: 20px;")
        self.advice_layout.addWidget(self.empty_label)

    def update_advice(self, advice_list: List[DragCoachingAdvice]) -> None:
        """Update the coaching advice display."""
        # Clear existing advice
        while self.advice_layout.count():
            item = self.advice_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not advice_list:
            self.empty_label = QLabel("No coaching advice yet.\nComplete a run to get tips!")
            self.empty_label.setAlignment(Qt.AlignCenter)
            self.empty_label.setStyleSheet("color: #9aa0a6; font-size: 12px; padding: 20px;")
            self.advice_layout.addWidget(self.empty_label)
            return

        # Sort by priority (HIGH first)
        sorted_advice = sorted(advice_list, key=lambda a: a.priority.value, reverse=True)

        for advice in sorted_advice:
            advice_widget = self._create_advice_widget(advice)
            self.advice_layout.addWidget(advice_widget)

        self.advice_layout.addStretch()

    def _create_advice_widget(self, advice: DragCoachingAdvice) -> QWidget:
        """Create a widget for a single piece of advice."""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background: #f8f9fa;
                border-radius: 8px;
                padding: 12px;
                margin: 4px;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header with metric and time
        header_text = f"{advice.metric}"
        if advice.current_time:
            header_text += f": {advice.current_time:.3f}s"
        if advice.best_time:
            header_text += f" (Best: {advice.best_time:.3f}s)"
        
        header = QLabel(header_text)
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(11)
        header.setFont(header_font)
        
        # Color by priority
        if advice.priority.value == "high":
            header.setStyleSheet("color: #ea4335;")
        elif advice.priority.value == "medium":
            header.setStyleSheet("color: #fbbc04;")
        else:
            header.setStyleSheet("color: #34a853;")
        
        layout.addWidget(header)

        # Advice message
        message = QLabel(advice.advice)
        message.setWordWrap(True)
        message.setStyleSheet("color: #202124; font-size: 11px; margin-top: 4px;")
        layout.addWidget(message)

        # Improvement potential
        if advice.improvement_potential > 0:
            improvement = QLabel(f"Potential improvement: {advice.improvement_potential:.2f}s")
            improvement.setStyleSheet("color: #34a853; font-size: 10px; font-weight: bold; margin-top: 4px;")
            layout.addWidget(improvement)

        # Actionable steps
        if advice.actionable_steps:
            steps_label = QLabel("Actionable Steps:")
            steps_label.setStyleSheet("color: #5f6368; font-size: 10px; font-weight: bold; margin-top: 8px;")
            layout.addWidget(steps_label)

            for step in advice.actionable_steps:
                step_label = QLabel(f"• {step}")
                step_label.setWordWrap(True)
                step_label.setStyleSheet("color: #5f6368; font-size: 10px; margin-left: 10px;")
                layout.addWidget(step_label)

        return widget

    def clear(self) -> None:
        """Clear all advice."""
        self.update_advice([])


__all__ = ["DragCoachingWidget"]

