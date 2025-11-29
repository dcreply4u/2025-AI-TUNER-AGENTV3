from __future__ import annotations

"""
Startup Splash Screen
---------------------

Shows a simple fade‑in / fade‑out splash image when the application starts.
The image path can be configured via the AITUNER_SPLASH_IMAGE environment
variable. On Windows, the default is:

    C:\\Users\\DC\\Pictures\\TelemetryIQgood9.jpg

On other platforms, set AITUNER_SPLASH_IMAGE to a valid image path.
"""

import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QEasingCurve, QObject, QPoint, QPropertyAnimation, Qt, QTimer, Signal
from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QGraphicsOpacityEffect


DEFAULT_WINDOWS_SPLASH = Path(r"C:\Users\DC\Pictures\TelemetryIQgood9.jpg")


class StartupSplash(QWidget):
    """A frameless, centered splash screen with slow fade‑in / fade‑out."""

    finished = Signal()

    def __init__(self, image_path: Optional[Path] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.SplashScreen)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        # Resolve image path
        env_path = os.environ.get("AITUNER_SPLASH_IMAGE")
        if image_path is None and env_path:
            image_path = Path(env_path)
        if image_path is None and os.name == "nt":
        # prefer the user-provided default on Windows
            image_path = DEFAULT_WINDOWS_SPLASH

        self._pixmap = None
        if image_path is not None and image_path.exists():
            self._pixmap = QPixmap(str(image_path))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if self._pixmap is not None and not self._pixmap.isNull():
            self._label.setPixmap(self._pixmap)
        layout.addWidget(self._label)

        # Center the splash on the primary screen
        screen = QGuiApplication.primaryScreen()
        if screen and self._pixmap is not None and not self._pixmap.isNull():
            size = self._pixmap.size()
            self.resize(size)
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - size.width()) // 2
            y = geo.y() + (geo.height() - size.height()) // 2
            self.move(QPoint(x, y))
        else:
            # Fallback size/position
            self.resize(600, 300)
            if screen:
                geo = screen.availableGeometry()
                x = geo.x() + (geo.width() - self.width()) // 2
                y = geo.y() + (geo.height() - self.height()) // 2
                self.move(QPoint(x, y))

        # Opacity effect for fade in/out
        self._effect = QGraphicsOpacityEffect(self)
        self._effect.setOpacity(0.0)
        self.setGraphicsEffect(self._effect)

        self._fade_in = QPropertyAnimation(self._effect, b"opacity", self)
        self._fade_in.setDuration(2000)  # 2 seconds fade in
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self._fade_out = QPropertyAnimation(self._effect, b"opacity", self)
        self._fade_out.setDuration(2000)  # 2 seconds fade out
        self._fade_out.setStartValue(1.0)
        self._fade_out.setEndValue(0.0)
        self._fade_out.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self._fade_in.finished.connect(self._on_fade_in_finished)
        self._fade_out.finished.connect(self._on_fade_out_finished)

    def show_slow(self) -> None:
        """Show the splash and start the fade sequence."""
        if self._pixmap is None or self._pixmap.isNull():
            # Nothing to show, emit finished immediately
            QTimer.singleShot(10, self._emit_finished)
            return
        self.show()
        self._fade_in.start()

    def _on_fade_in_finished(self) -> None:
        # Hold the image for a brief moment before fading out
        QTimer.singleShot(1000, self._start_fade_out)  # 1 second hold

    def _start_fade_out(self) -> None:
        self._fade_out.start()

    def _on_fade_out_finished(self) -> None:
        self.hide()
        self._emit_finished()

    def _emit_finished(self) -> None:
        self.finished.emit()
        self.deleteLater()


def show_startup_splash_if_available() -> None:
    """
    Convenience helper to be called after QApplication is created.
    Safe to call on all platforms; it will no‑op if the image is missing.
    """
    app = QApplication.instance()
    if app is None:
        return

    splash = StartupSplash()
    # If there is no valid pixmap, it will emit finished immediately
    splash.show_slow()


