from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget


class StatusBar(QWidget):
    """Simple QWidget that mirrors a status-line indicator."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(16)

        self.status_label = QLabel("Status: Idle")
        self.connectivity_label = QLabel("Link: --")
        self.connectivity_label.setStyleSheet("color: #6c757d;")

        layout.addWidget(self.status_label, 1)
        layout.addWidget(self.connectivity_label, 2)

    def update_status(self, text: str) -> None:
        self.status_label.setText(f"Status: {text}")

    def update_connectivity(self, text: str) -> None:
        self.connectivity_label.setText(f"Link: {text}")


__all__ = ["StatusBar"]

