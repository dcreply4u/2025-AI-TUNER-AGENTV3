"""
Advice Panel

Displays intelligent tuning advice after each run.
"""

from __future__ import annotations

from typing import Optional

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor
    from PySide6.QtWidgets import (
        QLabel,
        QScrollArea,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor
    from PySide6.QtWidgets import (
        QLabel,
        QScrollArea,
        QVBoxLayout,
        QWidget,
    )

from ai.intelligent_advisor import AdviceCategory, AdvicePriority, TuningAdvice


class AdviceCard(QWidget):
    """Individual advice card widget."""

    def __init__(self, advice: TuningAdvice, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.advice = advice

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)

        # Priority color
        priority_colors = {
            AdvicePriority.CRITICAL: "#ff4444",
            AdvicePriority.HIGH: "#ff8800",
            AdvicePriority.MEDIUM: "#ffaa00",
            AdvicePriority.LOW: "#44aa44",
        }
        color = priority_colors.get(advice.priority, "#888888")

        # Title with priority indicator
        title_text = f"[{advice.priority.value.upper()}] {advice.title}"
        title = QLabel(title_text)
        title.setStyleSheet(f"font-weight: bold; font-size: 13px; color: {color};")
        layout.addWidget(title)

        # Description
        desc = QLabel(advice.description)
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 11px; color: #333; margin-top: 4px;")
        layout.addWidget(desc)

        # Reasoning
        if advice.reasoning:
            reasoning = QLabel(f"<i>Why:</i> {advice.reasoning}")
            reasoning.setWordWrap(True)
            reasoning.setStyleSheet("font-size: 10px; color: #666; margin-top: 4px;")
            layout.addWidget(reasoning)

        # Suggested action
        action = QLabel(f"<b>Action:</b> {advice.suggested_action}")
        action.setWordWrap(True)
        action.setStyleSheet("font-size: 11px; color: #0066cc; margin-top: 6px; padding: 6px; background: #e6f2ff; border-radius: 4px;")
        layout.addWidget(action)

        # Expected improvement
        if advice.expected_improvement:
            improvement = QLabel(f"<b>Expected:</b> {advice.expected_improvement}")
            improvement.setWordWrap(True)
            improvement.setStyleSheet("font-size: 10px; color: #006600; margin-top: 4px;")
            layout.addWidget(improvement)

        # Historical basis
        if advice.historical_basis:
            historical = QLabel(f"<i>Based on:</i> {advice.historical_basis}")
            historical.setWordWrap(True)
            historical.setStyleSheet("font-size: 9px; color: #888; margin-top: 4px; font-style: italic;")
            layout.addWidget(historical)

        # Confidence indicator
        confidence_text = f"Confidence: {int(advice.confidence * 100)}%"
        confidence = QLabel(confidence_text)
        confidence.setStyleSheet("font-size: 9px; color: #999; margin-top: 4px;")
        layout.addWidget(confidence)

        # Set card style
        self.setStyleSheet(
            f"""
            QWidget {{
                background: white;
                border: 2px solid {color};
                border-radius: 6px;
                margin: 4px;
            }}
        """
        )


class AdvicePanel(QWidget):
    """Panel displaying tuning advice."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Tuning Advice")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Header
        header = QLabel("Intelligent Tuning Advice")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #333; margin-bottom: 8px;")
        layout.addWidget(header)

        # Scroll area for advice cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.addStretch()

        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)

        # Empty state
        self.empty_label = QLabel("No advice yet. Complete a run to get recommendations.")
        self.empty_label.setStyleSheet("font-size: 12px; color: #999; padding: 20px;")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.insertWidget(0, self.empty_label)

    def display_advice(self, advice_list: list[TuningAdvice]) -> None:
        """
        Display list of advice.

        Args:
            advice_list: List of tuning advice to display
        """
        # Clear existing advice (except empty label)
        for i in reversed(range(self.content_layout.count())):
            item = self.content_layout.itemAt(i)
            if item and item.widget() and not isinstance(item.widget(), QLabel):
                item.widget().deleteLater()

        # Hide empty label if we have advice
        if advice_list:
            self.empty_label.hide()
        else:
            self.empty_label.show()
            return

        # Add advice cards
        for advice in advice_list:
            card = AdviceCard(advice)
            self.content_layout.insertWidget(self.content_layout.count() - 1, card)

    def clear(self) -> None:
        """Clear all advice."""
        for i in reversed(range(self.content_layout.count())):
            item = self.content_layout.itemAt(i)
            if item and item.widget() and not isinstance(item.widget(), QLabel):
                item.widget().deleteLater()
        self.empty_label.show()


__all__ = ["AdvicePanel", "AdviceCard"]

