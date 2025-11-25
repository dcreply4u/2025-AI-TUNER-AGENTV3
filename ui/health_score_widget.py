from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget


STATUS_COLORS = {
    "excellent": "#28a745",
    "good": "#17a2b8",
    "fair": "#ffc107",
    "poor": "#fd7e14",
    "critical": "#dc3545",
}


class HealthScoreWidget(QWidget):
    """Compact widget that visualizes the engine health score."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        # White background with border to match other widgets
        self.setStyleSheet("background-color: #ffffff; border: 1px solid #bdc3c7; border-radius: 6px;")
        # Set minimum size to ensure all elements are visible
        self.setMinimumHeight(100)
        self.setMinimumWidth(300)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.title = QLabel("Engine Health")
        self.title.setAlignment(Qt.AlignLeft)
        self.title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; background-color: transparent;")
        self.title.setMinimumHeight(20)
        layout.addWidget(self.title)

        self.score_bar = QProgressBar()
        self.score_bar.setRange(0, 100)
        self.score_bar.setFormat("%p%")
        self.score_bar.setTextVisible(True)
        self.score_bar.setValue(0)  # Start at 0
        self.score_bar.setMinimumHeight(24)
        self.score_bar.setMaximumHeight(24)  # Fixed height for consistency
        # Hide progress bar initially - only show when there's actual data
        self.score_bar.setVisible(False)
        # Style the progress bar for light theme - minimal styling
        self.score_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #ecf0f1;
                text-align: center;
                color: #2c3e50;
                font-weight: bold;
                height: 24px;
                min-height: 24px;
                max-height: 24px;
            }
            QProgressBar::chunk {
                background-color: transparent;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.score_bar)

        self.status_label = QLabel("Status: n/a")
        self.status_label.setAlignment(Qt.AlignLeft)
        self.status_label.setStyleSheet("font-size: 12px; color: #5f6c7b; background-color: #ffffff; border: 1px solid #bdc3c7; border-radius: 4px; padding: 4px 8px;")
        self.status_label.setMinimumHeight(24)
        self.status_label.setMaximumHeight(24)
        layout.addWidget(self.status_label)
        
        # Add stretch to push content to top
        layout.addStretch()

    def update_score(self, score_payload: dict | None) -> None:
        if not score_payload:
            # Hide progress bar when there's no data
            self.score_bar.setVisible(False)
            self.score_bar.setValue(0)
            self.status_label.setText("Status: n/a")
            return

        score_value = int(round(score_payload.get("score", 0.0) * 100))
        status = score_payload.get("status", "unknown")
        color = STATUS_COLORS.get(status, "#6c757d")

        # Only show progress bar if there's an actual score value
        if score_value > 0:
            self.score_bar.setVisible(True)
            self.score_bar.setValue(score_value)
            # Update only the chunk color, keep the rest of the styling
            self.score_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid #bdc3c7;
                    border-radius: 4px;
                    background-color: #ecf0f1;
                    text-align: center;
                    color: #2c3e50;
                    font-weight: bold;
                    height: 24px;
                    min-height: 24px;
                    max-height: 24px;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 3px;
                }}
            """)
            self.status_label.setText(f"Status: {status.title()} ({score_value}%)")
        else:
            # Hide progress bar if score is 0
            self.score_bar.setVisible(False)
            self.status_label.setText("Status: n/a")


__all__ = ["HealthScoreWidget"]

