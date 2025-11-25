"""
Startup Diagnostics Screen

Fast, animated diagnostics screen with status indicators.
"""

from __future__ import annotations

import time
from typing import Optional

try:
    from PySide6.QtCore import QPropertyAnimation, QTimer, Qt, QEasingCurve, Property
    from PySide6.QtGui import QColor, QPainter, QPen
    from PySide6.QtWidgets import (
        QApplication,
        QHBoxLayout,
        QLabel,
        QProgressBar,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
    Property = Property
except ImportError:
    from PySide6.QtCore import QPropertyAnimation, QTimer, Qt, QEasingCurve, Property
    from PySide6.QtGui import QColor, QPainter, QPen
    from PySide6.QtWidgets import (
        QApplication,
        QHBoxLayout,
        QLabel,
        QProgressBar,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

from services.startup_diagnostics import DiagnosticResult, DiagnosticStatus, StartupDiagnostics


class StatusIndicator(QWidget):
    """Animated status indicator (green/red/yellow light)."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self._status = DiagnosticStatus.CHECKING
        self._opacity = 1.0

        # Animation for pulsing effect
        self._animation = QPropertyAnimation(self, b"opacity")
        self._animation.setDuration(1000)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._animation.setStartValue(0.3)
        self._animation.setEndValue(1.0)
        self._animation.setLoopCount(-1)  # Infinite loop

    @Property(float)
    def opacity(self) -> float:
        """Get current opacity."""
        return self._opacity

    @opacity.setter
    def opacity(self, value: float) -> None:
        """Set opacity and trigger repaint."""
        self._opacity = value
        self.update()

    def set_status(self, status: DiagnosticStatus) -> None:
        """Set status and update animation."""
        self._status = status

        if status == DiagnosticStatus.CHECKING:
            self._animation.start()
        elif status == DiagnosticStatus.PASS:
            self._animation.stop()
            self._opacity = 1.0
        elif status == DiagnosticStatus.FAIL:
            self._animation.stop()
            self._opacity = 1.0
        elif status == DiagnosticStatus.WARNING:
            self._animation.setDuration(1500)
            self._animation.start()
        else:  # NOT_AVAILABLE
            self._animation.stop()
            self._opacity = 0.5

        self.update()

    def paintEvent(self, event) -> None:
        """Paint the status indicator."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Determine color based on status
        if self._status == DiagnosticStatus.PASS:
            color = QColor(0, 255, 0)  # Green
        elif self._status == DiagnosticStatus.FAIL:
            color = QColor(255, 0, 0)  # Red
        elif self._status == DiagnosticStatus.WARNING:
            color = QColor(255, 200, 0)  # Yellow/Orange
        elif self._status == DiagnosticStatus.CHECKING:
            color = QColor(100, 100, 255)  # Blue (checking)
        else:  # NOT_AVAILABLE
            color = QColor(128, 128, 128)  # Gray

        # Apply opacity
        color.setAlphaF(self._opacity)

        # Draw circle
        pen = QPen(color, 2)
        painter.setPen(pen)
        painter.setBrush(color)

        # Draw with slight margin
        margin = 2
        painter.drawEllipse(margin, margin, self.width() - margin * 2, self.height() - margin * 2)

        # Add glow effect for active status
        if self._status in [DiagnosticStatus.PASS, DiagnosticStatus.CHECKING]:
            glow_color = QColor(color)
            glow_color.setAlphaF(self._opacity * 0.3)
            pen = QPen(glow_color, 4)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(0, 0, self.width(), self.height())


class DiagnosticItem(QWidget):
    """Single diagnostic item with status indicator."""

    def __init__(self, name: str, category: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.name = name
        self.category = category

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 3, 5, 3)

        # Status indicator
        self.status_indicator = StatusIndicator(self)
        layout.addWidget(self.status_indicator)

        # Name label
        self.name_label = QLabel(self._format_name(name))
        self.name_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(self.name_label)

        # Status message
        self.message_label = QLabel("Checking...")
        self.message_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.message_label, 1)

        # Set initial status
        self.status_indicator.set_status(DiagnosticStatus.CHECKING)

    def _format_name(self, name: str) -> str:
        """Format diagnostic name for display."""
        return name.replace("_", " ").title()

    def update_result(self, result: DiagnosticResult) -> None:
        """Update with diagnostic result."""
        self.status_indicator.set_status(result.status)
        self.message_label.setText(result.message)

        # Update text color based on status
        if result.status == DiagnosticStatus.PASS:
            self.message_label.setStyleSheet("color: #0f0; font-size: 11px;")
        elif result.status == DiagnosticStatus.FAIL:
            self.message_label.setStyleSheet("color: #f00; font-size: 11px;")
        elif result.status == DiagnosticStatus.WARNING:
            self.message_label.setStyleSheet("color: #fa0; font-size: 11px;")
        else:
            self.message_label.setStyleSheet("color: #888; font-size: 11px;")


class DiagnosticsScreen(QWidget):
    """Startup diagnostics screen."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("System Diagnostics")
        self.resize(600, 500)

        # Diagnostics service
        self.diagnostics = StartupDiagnostics()
        self.diagnostics.register_callback(self._on_diagnostic_result)

        # UI Components
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("System Diagnostics")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #fff;")
        layout.addWidget(title)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # Status summary
        self.summary_label = QLabel("Initializing diagnostics...")
        self.summary_label.setStyleSheet("font-size: 12px; color: #aaa;")
        layout.addWidget(self.summary_label)

        # Diagnostic items container
        self.items_layout = QVBoxLayout()
        self.items_layout.setSpacing(5)
        self.diagnostic_items: Dict[str, DiagnosticItem] = {}

        # Create placeholder items
        categories = {
            "hardware": ["Camera", "ECU", "CAN Bus", "OBD", "GPS", "USB Storage"],
            "connectivity": ["Network", "Bluetooth", "WiFi", "LTE"],
            "services": ["Streaming", "Database", "Voice"],
        }

        for category, items in categories.items():
            category_label = QLabel(category.upper())
            category_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #0ff; margin-top: 10px;")
            self.items_layout.addWidget(category_label)

            for item_name in items:
                item = DiagnosticItem(item_name.lower().replace(" ", "_"), category)
                self.diagnostic_items[item_name.lower().replace(" ", "_")] = item
                self.items_layout.addWidget(item)

        layout.addLayout(self.items_layout, 1)

        # Buttons
        button_layout = QHBoxLayout()
        self.skip_btn = QPushButton("Skip")
        self.skip_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.skip_btn)

        self.retry_btn = QPushButton("Retry Checks")
        self.retry_btn.clicked.connect(self._retry_checks)
        self.retry_btn.setEnabled(False)
        button_layout.addWidget(self.retry_btn)

        layout.addLayout(button_layout)

        # Timer for progress updates
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self._update_progress)
        self.start_time = time.time()
        self.expected_duration = 5.0  # Expected duration in seconds

        # Start diagnostics
        self._start_diagnostics()

    def _start_diagnostics(self) -> None:
        """Start diagnostic checks."""
        self.start_time = time.time()
        self.progress_timer.start(50)  # Update every 50ms

        # Run diagnostics in background
        import threading

        thread = threading.Thread(target=self._run_diagnostics, daemon=True)
        thread.start()

    def _run_diagnostics(self) -> None:
        """Run diagnostics in background thread."""
        results = self.diagnostics.check_all(timeout_per_check=2.0)

        # Update UI in main thread
        QTimer.singleShot(0, lambda: self._diagnostics_complete(results))

    def _on_diagnostic_result(self, result: DiagnosticResult) -> None:
        """Handle diagnostic result callback."""
        # Update UI in main thread
        QTimer.singleShot(0, lambda: self._update_item(result))

    def _update_item(self, result: DiagnosticResult) -> None:
        """Update diagnostic item."""
        # Map result name to item name
        item_name = result.name
        if item_name in self.diagnostic_items:
            self.diagnostic_items[item_name].update_result(result)

    def _update_progress(self) -> None:
        """Update progress bar."""
        elapsed = time.time() - self.start_time
        progress = min(int((elapsed / self.expected_duration) * 100), 95)  # Cap at 95% until complete
        self.progress_bar.setValue(progress)

        # Update summary
        summary = self.diagnostics.get_summary()
        if summary["total"] > 0:
            self.summary_label.setText(
                f"Passed: {summary['passed']} | "
                f"Failed: {summary['failed']} | "
                f"Warnings: {summary['warnings']} | "
                f"Not Available: {summary['not_available']}"
            )

    def _diagnostics_complete(self, results: Dict[str, DiagnosticResult]) -> None:
        """Handle diagnostics completion."""
        self.progress_timer.stop()
        self.progress_bar.setValue(100)

        summary = self.diagnostics.get_summary()
        health_score = summary["health_score"]

        if health_score >= 80:
            status_text = "System Ready"
            status_color = "#0f0"
        elif health_score >= 50:
            status_text = "System Operational (Some Issues)"
            status_color = "#fa0"
        else:
            status_text = "System Issues Detected"
            status_color = "#f00"

        self.summary_label.setText(
            f"<b style='color: {status_color}'>{status_text}</b> | "
            f"Health Score: {health_score:.0f}% | "
            f"Checks: {summary['passed']}/{summary['total']} passed"
        )
        self.summary_label.setStyleSheet(f"font-size: 12px; color: {status_color};")

        self.retry_btn.setEnabled(True)

    def _retry_checks(self) -> None:
        """Retry diagnostic checks."""
        # Reset all items
        for item in self.diagnostic_items.values():
            item.status_indicator.set_status(DiagnosticStatus.CHECKING)
            item.message_label.setText("Checking...")
            item.message_label.setStyleSheet("color: #888; font-size: 11px;")

        self.retry_btn.setEnabled(False)
        self._start_diagnostics()

    def accept(self) -> None:
        """Accept and close diagnostics."""
        if hasattr(self, "_on_accept"):
            self._on_accept()
        self.close()
    
    def set_accept_callback(self, callback: callable) -> None:
        """Set callback for when diagnostics is accepted."""
        self._on_accept = callback

    def closeEvent(self, event) -> None:
        """Handle close event."""
        self.progress_timer.stop()
        event.accept()


def show_diagnostics(parent: Optional[QWidget] = None) -> DiagnosticsScreen:
    """Show diagnostics screen."""
    screen = DiagnosticsScreen(parent)
    screen.show()
    return screen


__all__ = ["DiagnosticsScreen", "StatusIndicator", "show_diagnostics"]

