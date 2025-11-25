"""
Advice Panel

Displays intelligent tuning advice after each run.
Modern styled to match other panels.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

try:
    from ai.intelligent_advisor import AdviceCategory, AdvicePriority, TuningAdvice
except ImportError:
    # Create stub classes if not available
    from enum import Enum
    from dataclasses import dataclass
    
    class AdvicePriority(Enum):
        CRITICAL = "critical"
        HIGH = "high"
        MEDIUM = "medium"
        LOW = "low"
    
    class AdviceCategory(Enum):
        PERFORMANCE = "performance"
        SAFETY = "safety"
        EFFICIENCY = "efficiency"
    
    @dataclass
    class TuningAdvice:
        title: str = ""
        description: str = ""
        priority: AdvicePriority = AdvicePriority.LOW
        category: AdviceCategory = AdviceCategory.PERFORMANCE
        reasoning: str = ""
        suggested_action: str = ""
        expected_improvement: str = ""
        historical_basis: str = ""
        confidence: float = 0.0


class AdviceCard(QFrame):
    """Individual advice card widget with modern styling."""

    def __init__(self, advice: TuningAdvice, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.advice = advice

        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Priority colors (consistent with other panels)
        priority_colors = {
            AdvicePriority.CRITICAL: "#e74c3c",
            AdvicePriority.HIGH: "#f39c12",
            AdvicePriority.MEDIUM: "#3498db",
            AdvicePriority.LOW: "#27ae60",
        }
        color = priority_colors.get(advice.priority, "#7f8c8d")

        # Priority icon
        priority_icons = {
            AdvicePriority.CRITICAL: "🚨",
            AdvicePriority.HIGH: "⚠️",
            AdvicePriority.MEDIUM: "💡",
            AdvicePriority.LOW: "✅",
        }
        icon = priority_icons.get(advice.priority, "📌")

        # Title with priority indicator
        title_text = f"{icon} {advice.title}"
        title = QLabel(title_text)
        title.setStyleSheet(f"font-weight: bold; font-size: 12px; color: {color}; background: transparent;")
        layout.addWidget(title)

        # Description
        desc = QLabel(advice.description)
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 11px; color: #2c3e50; margin-top: 4px; background: transparent;")
        layout.addWidget(desc)

        # Reasoning
        if advice.reasoning:
            reasoning = QLabel(f"<i>Why:</i> {advice.reasoning}")
            reasoning.setWordWrap(True)
            reasoning.setStyleSheet("font-size: 10px; color: #7f8c8d; margin-top: 4px; background: transparent;")
            layout.addWidget(reasoning)

        # Suggested action
        action = QLabel(f"<b>Action:</b> {advice.suggested_action}")
        action.setWordWrap(True)
        action.setStyleSheet("""
            font-size: 11px; 
            color: #2980b9; 
            margin-top: 6px; 
            padding: 8px; 
            background: #ebf5fb; 
            border-radius: 4px;
            border-left: 3px solid #3498db;
        """)
        layout.addWidget(action)

        # Expected improvement
        if advice.expected_improvement:
            improvement = QLabel(f"📈 <b>Expected:</b> {advice.expected_improvement}")
            improvement.setWordWrap(True)
            improvement.setStyleSheet("font-size: 10px; color: #27ae60; margin-top: 4px; background: transparent;")
            layout.addWidget(improvement)

        # Confidence indicator
        confidence_pct = int(advice.confidence * 100)
        confidence_color = "#27ae60" if confidence_pct >= 70 else "#f39c12" if confidence_pct >= 40 else "#e74c3c"
        confidence = QLabel(f"🎯 Confidence: {confidence_pct}%")
        confidence.setStyleSheet(f"font-size: 9px; color: {confidence_color}; margin-top: 4px; background: transparent;")
        layout.addWidget(confidence)

        # Set card style
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-left: 4px solid {color};
                border-radius: 6px;
                margin: 4px 0;
            }}
        """)


class AdvicePanel(QFrame):
    """Panel displaying tuning advice with modern styling."""

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
        """)
        
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Header
        header = QLabel("🔧 Intelligent Tuning Advice")
        header.setStyleSheet("font-size: 14px; font-weight: 700; color: #2c3e50;")
        layout.addWidget(header)

        # Scroll area for advice cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background: transparent;
            }
            QScrollBar:vertical {
                background-color: #f0f0f0;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #3498db;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)
        self.content_layout.addStretch()

        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)

        # Empty state
        self.empty_label = QLabel("💭 No advice yet.\n\nComplete a run to get AI-powered recommendations.")
        self.empty_label.setStyleSheet("""
            font-size: 12px; 
            color: #95a5a6; 
            padding: 20px;
            background: #f8f9fa;
            border-radius: 6px;
        """)
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.insertWidget(0, self.empty_label)

    def display_advice(self, advice_list: list[TuningAdvice]) -> None:
        """Display list of advice."""
        # Clear existing advice cards
        self._clear_cards()

        # Hide empty label if we have advice
        if advice_list:
            self.empty_label.hide()
        else:
            self.empty_label.show()
            return

        # Add advice cards (sorted by priority)
        priority_order = {
            AdvicePriority.CRITICAL: 0,
            AdvicePriority.HIGH: 1,
            AdvicePriority.MEDIUM: 2,
            AdvicePriority.LOW: 3,
        }
        sorted_advice = sorted(advice_list, key=lambda a: priority_order.get(a.priority, 99))
        
        for advice in sorted_advice:
            card = AdviceCard(advice)
            self.content_layout.insertWidget(self.content_layout.count() - 1, card)

    def _clear_cards(self) -> None:
        """Clear advice cards but keep empty label."""
        for i in reversed(range(self.content_layout.count())):
            item = self.content_layout.itemAt(i)
            widget = item.widget() if item else None
            if widget and widget != self.empty_label:
                widget.deleteLater()

    def clear(self) -> None:
        """Clear all advice."""
        self._clear_cards()
        self.empty_label.show()

    def update_insight(self, message: str, level: str | None = None) -> None:
        """Compatibility method for update_insight calls."""
        # Create a simple advice from the message
        priority = AdvicePriority.LOW
        if level == "warning":
            priority = AdvicePriority.HIGH
        elif level == "error":
            priority = AdvicePriority.CRITICAL
        elif level == "success":
            priority = AdvicePriority.LOW
        
        advice = TuningAdvice(
            title="System Message",
            description=message,
            priority=priority,
            suggested_action="Review and take appropriate action",
            confidence=0.8,
        )
        self.display_advice([advice])


__all__ = ["AdvicePanel", "AdviceCard"]
