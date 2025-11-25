from __future__ import annotations

"""\
=========================================================
AI Insight Panel – where alerts get the spotlight they deserve
=========================================================
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class AIInsightPanel(QFrame):
    """Rich text widget for AI-driven alerts with modern styling."""

    def __init__(self, parent: QWidget | None = None) -> None:
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
        layout.setSpacing(8)
        
        # Header
        header = QLabel("🤖 AI Insights")
        header.setStyleSheet("font-size: 14px; font-weight: 700; color: #2c3e50;")
        layout.addWidget(header)

        # Text area with proper styling
        self.text_box = QTextEdit()
        self.text_box.setObjectName("aiInsightTextBox")
        self.text_box.setReadOnly(True)
        self.text_box.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                color: #2c3e50;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                padding: 8px;
                font-size: 11px;
                line-height: 1.4;
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
        self.text_box.setMinimumHeight(80)
        layout.addWidget(self.text_box)

    def update_insight(self, message: str, level: str | None = None) -> None:
        """Add a new insight message with color coding."""
        level = (level or "").lower()
        
        # Auto-detect level from message content
        msg_lower = message.lower()
        if "warning" in msg_lower or "warn" in msg_lower:
            level = "warning"
        elif "error" in msg_lower or "fail" in msg_lower:
            level = "error"
        elif "success" in msg_lower or "ready" in msg_lower or "complete" in msg_lower:
            level = "success"
        
        # Color coding
        if level == "error":
            html = f"<div style='color:#e74c3c; margin: 4px 0;'>❌ {message}</div>"
        elif level == "warning":
            html = f"<div style='color:#f39c12; margin: 4px 0;'>⚠️ {message}</div>"
        elif level == "success":
            html = f"<div style='color:#27ae60; margin: 4px 0;'>✅ {message}</div>"
        else:
            html = f"<div style='color:#2c3e50; margin: 4px 0;'>💡 {message}</div>"
        
        self.text_box.append(html)
        
        # Scroll to bottom
        scrollbar = self.text_box.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_insights(self, message: str, level: str | None = None) -> None:
        """Alias for update_insight (compatibility)."""
        self.update_insight(message, level)

    def clear_insights(self) -> None:
        """Clear all insights."""
        self.text_box.clear()


__all__ = ["AIInsightPanel"]
