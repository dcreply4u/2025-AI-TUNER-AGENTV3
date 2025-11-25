"""
Notification Widget

Displays alerts and notifications for system events, missing drivers,
and feature availability.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Optional

try:
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtWidgets import (
        QLabel,
        QScrollArea,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtWidgets import (
        QLabel,
        QScrollArea,
        QVBoxLayout,
        QWidget,
    )


class NotificationLevel(Enum):
    """Notification severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class NotificationWidget(QWidget):
    """Widget that displays system notifications and alerts."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMaximumHeight(200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Scroll area for notifications
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.notification_container = QWidget()
        self.notification_layout = QVBoxLayout(self.notification_container)
        self.notification_layout.setContentsMargins(0, 0, 0, 0)
        self.notification_layout.addStretch()

        scroll.setWidget(self.notification_container)
        layout.addWidget(scroll)

        self.notifications: list[tuple[float, QLabel]] = []
        self.max_notifications = 20
        self.auto_remove_seconds = 10.0  # Auto-remove after 10 seconds

        # Timer for auto-removal
        self.cleanup_timer = QTimer(self)
        self.cleanup_timer.timeout.connect(self._cleanup_old_notifications)
        self.cleanup_timer.start(1000)  # Check every second

    def show_notification(self, message: str, level: NotificationLevel = NotificationLevel.INFO, duration: float = 10.0) -> None:
        """
        Show a notification.

        Args:
            message: Notification message
            level: Severity level
            duration: Auto-remove duration in seconds
        """
        label = QLabel(message)
        label.setWordWrap(True)
        label.setContentsMargins(8, 4, 8, 4)

        # Style based on level
        if level == NotificationLevel.ERROR:
            label.setStyleSheet("background-color: #ff4444; color: white; border-radius: 4px;")
        elif level == NotificationLevel.WARNING:
            label.setStyleSheet("background-color: #ffaa00; color: white; border-radius: 4px;")
        elif level == NotificationLevel.SUCCESS:
            label.setStyleSheet("background-color: #44ff44; color: black; border-radius: 4px;")
        else:  # INFO
            label.setStyleSheet("background-color: #4444ff; color: white; border-radius: 4px;")

        # Insert at top
        self.notification_layout.insertWidget(0, label)
        self.notifications.append((time.time() + duration, label))

        # Limit number of notifications
        if len(self.notifications) > self.max_notifications:
            _, old_label = self.notifications.pop(0)
            old_label.deleteLater()

    def _cleanup_old_notifications(self) -> None:
        """Remove old notifications."""
        now = time.time()
        to_remove = []
        for i, (expiry, label) in enumerate(self.notifications):
            if now >= expiry:
                to_remove.append(i)

        # Remove in reverse order to maintain indices
        for i in reversed(to_remove):
            _, label = self.notifications.pop(i)
            label.deleteLater()

    def clear_all(self) -> None:
        """Clear all notifications."""
        for _, label in self.notifications:
            label.deleteLater()
        self.notifications.clear()


__all__ = ["NotificationWidget", "NotificationLevel"]

