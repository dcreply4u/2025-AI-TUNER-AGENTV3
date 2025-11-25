"""
Diagnostics Widget

Visual diagnostics panel with animated status indicators.
Tap/click to run instant diagnostics.
"""

from __future__ import annotations

import time
from typing import Optional

try:
    from PySide6.QtCore import QPropertyAnimation, QRect, Qt, QTimer, Property
    from PySide6.QtGui import QColor, QPainter, QPen
    from PySide6.QtWidgets import (
        QFrame,
        QGridLayout,
        QLabel,
        QPushButton,
        QScrollArea,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    from PySide6.QtCore import QPropertyAnimation, QRect, Qt, QTimer, Property
    from PySide6.QtGui import QColor, QPainter, QPen
    from PySide6.QtWidgets import (
        QFrame,
        QGridLayout,
        QLabel,
        QPushButton,
        QScrollArea,
        QVBoxLayout,
        QWidget,
    )

from services.system_diagnostics import ComponentDiagnostic, DiagnosticStatus, SystemDiagnostics


class AnimatedStatusIndicator(QWidget):
    """Animated status indicator with pulsing animation."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.status = DiagnosticStatus.UNKNOWN
        self._pulse_opacity = 1.0
        self.setFixedSize(24, 24)

        # Pulse animation
        self.pulse_animation = QPropertyAnimation(self, b"pulseOpacity")
        self.pulse_animation.setDuration(1000)
        self.pulse_animation.setLoopCount(-1)  # Infinite loop
        self.pulse_animation.setStartValue(1.0)
        self.pulse_animation.setEndValue(0.3)

    def set_status(self, status: DiagnosticStatus) -> None:
        """Set status and start/stop animation."""
        self.status = status
        if status in (DiagnosticStatus.OK, DiagnosticStatus.ERROR):
            self.pulse_animation.start()
        else:
            self.pulse_animation.stop()
            self._pulse_opacity = 1.0
        self.update()

    def get_pulse_opacity(self) -> float:
        """Get pulse opacity for animation."""
        return self._pulse_opacity

    def set_pulse_opacity(self, value: float) -> None:
        """Set pulse opacity for animation."""
        self._pulse_opacity = value
        self.update()

    pulseOpacity = Property(float, get_pulse_opacity, set_pulse_opacity)

    def paintEvent(self, event) -> None:
        """Paint the status indicator."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Get color based on status
        if self.status == DiagnosticStatus.OK:
            color = QColor(0, 255, 0)  # Green
        elif self.status == DiagnosticStatus.ERROR:
            color = QColor(255, 0, 0)  # Red
        elif self.status == DiagnosticStatus.WARNING:
            color = QColor(255, 165, 0)  # Orange
        elif self.status == DiagnosticStatus.CHECKING:
            color = QColor(0, 150, 255)  # Blue
        else:
            color = QColor(128, 128, 128)  # Gray

        # Apply pulse opacity
        color.setAlphaF(self._pulse_opacity)

        # Draw outer circle (pulse effect)
        if self.status in (DiagnosticStatus.OK, DiagnosticStatus.ERROR):
            pulse_pen = QPen(color)
            pulse_pen.setWidth(2)
            painter.setPen(pulse_pen)
            painter.setBrush(QColor(0, 0, 0, 0))  # Transparent fill
            pulse_radius = 12 * (1.0 + (1.0 - self._pulse_opacity) * 0.3)
            painter.drawEllipse(
                int(self.width() / 2 - pulse_radius),
                int(self.height() / 2 - pulse_radius),
                int(pulse_radius * 2),
                int(pulse_radius * 2),
            )

        # Draw main indicator circle
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setBrush(color)
        radius = 8
        painter.drawEllipse(
            int(self.width() / 2 - radius),
            int(self.height() / 2 - radius),
            radius * 2,
            radius * 2,
        )

        # Draw checkmark for OK, X for error
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        if self.status == DiagnosticStatus.OK:
            # Draw checkmark
            painter.drawLine(6, 12, 10, 16)
            painter.drawLine(10, 16, 18, 8)
        elif self.status == DiagnosticStatus.ERROR:
            # Draw X
            painter.drawLine(8, 8, 16, 16)
            painter.drawLine(16, 8, 8, 16)


class ComponentStatusRow(QFrame):
    """Row showing component status."""

    def __init__(self, component: ComponentDiagnostic, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.component = component
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("background-color: rgba(30, 30, 30, 200); border-radius: 4px;")

        layout = QGridLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        # Status indicator
        self.indicator = AnimatedStatusIndicator()
        self.indicator.set_status(component.status)
        layout.addWidget(self.indicator, 0, 0)

        # Component name
        self.name_label = QLabel(component.name)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 12px; color: white;")
        layout.addWidget(self.name_label, 0, 1)

        # Status message
        self.message_label = QLabel(component.message)
        self.message_label.setStyleSheet("font-size: 11px; color: #cccccc;")
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label, 0, 2)

        # Check duration
        if component.check_duration > 0:
            duration_label = QLabel(f"{component.check_duration*1000:.0f}ms")
            duration_label.setStyleSheet("font-size: 10px; color: #888888;")
            layout.addWidget(duration_label, 0, 3)

    def update_status(self, component: ComponentDiagnostic) -> None:
        """Update component status."""
        self.component = component
        self.indicator.set_status(component.status)
        self.message_label.setText(component.message)

        # Update colors based on status
        if component.status == DiagnosticStatus.OK:
            self.setStyleSheet("background-color: rgba(0, 100, 0, 150); border-radius: 4px;")
        elif component.status == DiagnosticStatus.ERROR:
            self.setStyleSheet("background-color: rgba(100, 0, 0, 150); border-radius: 4px;")
        elif component.status == DiagnosticStatus.WARNING:
            self.setStyleSheet("background-color: rgba(100, 60, 0, 150); border-radius: 4px;")
        else:
            self.setStyleSheet("background-color: rgba(30, 30, 30, 200); border-radius: 4px;")


class DiagnosticsWidget(QWidget):
    """Main diagnostics widget with animated indicators."""

    def __init__(self, diagnostics: Optional[SystemDiagnostics] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.diagnostics = diagnostics or SystemDiagnostics()
        self.component_rows: dict[str, ComponentStatusRow] = {}

        self.setWindowTitle("System Diagnostics")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header_layout = QVBoxLayout()
        title = QLabel("System Diagnostics")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        header_layout.addWidget(title)

        # Summary
        self.summary_label = QLabel("Status: Checking...")
        self.summary_label.setStyleSheet("font-size: 12px; color: #cccccc;")
        header_layout.addWidget(self.summary_label)

        # Run button
        self.run_button = QPushButton("Run Diagnostics")
        self.run_button.setStyleSheet(
            """
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0052a3;
            }
            QPushButton:pressed {
                background-color: #003d7a;
            }
        """
        )
        self.run_button.clicked.connect(self.run_diagnostics)
        header_layout.addWidget(self.run_button)

        layout.addLayout(header_layout)

        # Scroll area for component list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: transparent; border: none;")

        self.components_widget = QWidget()
        self.components_layout = QVBoxLayout(self.components_widget)
        self.components_layout.setSpacing(4)
        self.components_layout.addStretch()

        scroll.setWidget(self.components_widget)
        layout.addWidget(scroll)

        # Auto-refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh_status)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds

    def run_diagnostics(self) -> None:
        """Run diagnostics check."""
        self.run_button.setEnabled(False)
        self.run_button.setText("Checking...")
        self.summary_label.setText("Status: Checking components...")

        # Run in background thread to avoid blocking UI
        try:
            from PySide6.QtCore import QThread
        except ImportError:
            from PySide6.QtCore import QThread

        class DiagnosticsThread(QThread):
            def __init__(self, diagnostics):
                super().__init__()
                self.diagnostics = diagnostics
                self.results = None

            def run(self):
                self.results = self.diagnostics.check_all()

        self.check_thread = DiagnosticsThread(self.diagnostics)
        self.check_thread.finished.connect(self._on_diagnostics_complete)
        self.check_thread.start()

    def _on_diagnostics_complete(self) -> None:
        """Handle diagnostics completion."""
        results = self.check_thread.results
        if results:
            self._update_components(results)

        summary = self.diagnostics.get_summary()
        status_text = f"Status: {summary['ok']}/{summary['total']} OK"
        if summary["error"] > 0:
            status_text += f", {summary['error']} Error(s)"
        if summary["warning"] > 0:
            status_text += f", {summary['warning']} Warning(s)"

        self.summary_label.setText(status_text)
        self.run_button.setEnabled(True)
        self.run_button.setText("Run Diagnostics")

    def _update_components(self, results: dict[str, ComponentDiagnostic]) -> None:
        """Update component status rows."""
        for name, component in results.items():
            if name in self.component_rows:
                self.component_rows[name].update_status(component)
            else:
                # Create new row
                row = ComponentStatusRow(component)
                self.component_rows[name] = row
                # Insert before stretch
                self.components_layout.insertWidget(self.components_layout.count() - 1, row)

    def _refresh_status(self) -> None:
        """Refresh status indicators (lightweight check)."""
        # Just update visual indicators without full check
        for name, row in self.component_rows.items():
            component = self.diagnostics.components.get(name)
            if component:
                row.update_status(component)

    def register_default_checks(self) -> None:
        """Register default diagnostic checks."""
        from services.system_diagnostics import (
            check_cameras,
            check_can_bus,
            check_gps,
            check_network,
            check_obd_interface,
            check_usb_storage,
            check_voice_output,
        )

        self.diagnostics.register_component("CAN Bus", check_can_bus)
        self.diagnostics.register_component("GPS", check_gps)
        self.diagnostics.register_component("Cameras", check_cameras)
        self.diagnostics.register_component("USB Storage", check_usb_storage)
        self.diagnostics.register_component("Network", check_network)
        self.diagnostics.register_component("OBD Interface", check_obd_interface)
        self.diagnostics.register_component("Voice Output", check_voice_output)

    def run_startup_check(self) -> None:
        """Run diagnostics at startup."""
        self.register_default_checks()
        # Set all to checking state
        for name in self.diagnostics.check_callbacks.keys():
            self.diagnostics.components[name] = ComponentDiagnostic(
                name=name,
                status=DiagnosticStatus.CHECKING,
                message="Checking...",
            )
            row = ComponentStatusRow(self.diagnostics.components[name])
            self.component_rows[name] = row
            self.components_layout.insertWidget(self.components_layout.count() - 1, row)

        # Run diagnostics
        self.run_diagnostics()


__all__ = ["DiagnosticsWidget", "AnimatedStatusIndicator", "ComponentStatusRow"]

