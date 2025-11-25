from __future__ import annotations

"""\
=========================================================
AI Insight Panel – where alerts get the spotlight they deserve
=========================================================
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget


class AIInsightPanel(QWidget):
    """Rich text widget for AI-driven alerts."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("AI Insights", alignment=Qt.AlignLeft))

        self.text_box = QTextEdit()
        self.text_box.setObjectName("aiInsightTextBox")
        self.text_box.setReadOnly(True)
        layout.addWidget(self.text_box)

    def update_insight(self, message: str, level: str | None = None) -> None:
        level = (level or "").lower()
        if "warning" in message.lower():
            level = "warning"
        if level == "warning":
            html = f"<span style='color:#d9534f;font-weight:bold;'>{message}</span>"
        elif level == "success":
            html = f"<span style='color:#28a745;'>{message}</span>"
        else:
            html = message
        self.text_box.append(html)


__all__ = ["AIInsightPanel"]

