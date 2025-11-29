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


def _find_default_splash_image() -> Optional[Path]:
    """Find the default splash image on the current platform."""
    # Check environment variable first
    env_path = os.environ.get("AITUNER_SPLASH_IMAGE")
    if env_path:
        path = Path(env_path)
        if path.exists():
            print(f"[SPLASH] Found image from env: {path}")
            return path
        else:
            print(f"[SPLASH] Env path does not exist: {env_path}")
    
    # Platform-specific defaults
    if os.name == "nt":
        # Windows: use user's Pictures folder
        if DEFAULT_WINDOWS_SPLASH.exists():
            print(f"[SPLASH] Found Windows default: {DEFAULT_WINDOWS_SPLASH}")
            return DEFAULT_WINDOWS_SPLASH
    else:
        # Linux/Unix: check project root for common image names
        project_root = Path(__file__).parent.parent
        for name in ["TelemetryIQgood9.jpg", "TelemetryIQgood9.png", "splash.jpg", "splash.png"]:
            candidate = project_root / name
            if candidate.exists():
                print(f"[SPLASH] Found image in project root: {candidate}")
                return candidate
    
    print("[SPLASH] No splash image found")
    return None


class StartupSplash(QWidget):
    """A frameless, centered splash screen with slow fade‑in / fade‑out."""

    finished = Signal()

    def __init__(self, image_path: Optional[Path] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.SplashScreen)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        # Resolve image path
        if image_path is None:
            image_path = _find_default_splash_image()

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

        # Center the splash on the primary screen (defer until show)
        # Don't access screen here as QApplication might not be fully ready
        if self._pixmap is not None and not self._pixmap.isNull():
            size = self._pixmap.size()
            self.resize(size)
        else:
            # Fallback size
            self.resize(600, 300)

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
            print("[SPLASH] No valid pixmap, skipping splash")
            QTimer.singleShot(10, self._emit_finished)
            return
        
        print(f"[SPLASH] Showing splash screen (size: {self._pixmap.width()}x{self._pixmap.height()})")
        
        # Center on screen now that QApplication is ready
        try:
            screen = QGuiApplication.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                screen_w = geo.width()
                screen_h = geo.height()
                pixmap_w = self._pixmap.width()
                pixmap_h = self._pixmap.height()
                
                # Scale down if image is larger than screen (maintain aspect ratio)
                if pixmap_w > screen_w or pixmap_h > screen_h:
                    scale = min(screen_w / pixmap_w, screen_h / pixmap_h, 1.0)
                    scaled_w = int(pixmap_w * scale)
                    scaled_h = int(pixmap_h * scale)
                    scaled_pixmap = self._pixmap.scaled(
                        scaled_w, scaled_h,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self._label.setPixmap(scaled_pixmap)
                    widget_w = scaled_w
                    widget_h = scaled_h
                    print(f"[SPLASH] Scaled image to fit screen: {scaled_w}x{scaled_h} (scale: {scale:.2f})")
                else:
                    widget_w = pixmap_w
                    widget_h = pixmap_h
                
                # Ensure widget has correct size
                self.resize(widget_w, widget_h)
                
                # Calculate center position
                x = geo.x() + (screen_w - widget_w) // 2
                y = geo.y() + (screen_h - widget_h) // 2
                
                # Clamp to ensure it stays on screen (shouldn't be needed after scaling, but safety check)
                x = max(geo.x(), min(x, geo.x() + screen_w - widget_w))
                y = max(geo.y(), min(y, geo.y() + screen_h - widget_h))
                
                self.move(QPoint(x, y))
                print(f"[SPLASH] Screen: {screen_w}x{screen_h}, Widget: {widget_w}x{widget_h}, Positioned at ({x}, {y})")
        except Exception as e:
            # If screen access fails, just show at default position
            print(f"[SPLASH] Screen positioning failed: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: just resize to pixmap size
            self.resize(self._pixmap.width(), self._pixmap.height())
        
        # Ensure window flags are set (in case they were reset)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SplashScreen
        )
        self.show()
        self.raise_()  # Bring to front
        self.activateWindow()  # Activate window
        # Force to front by lowering other windows
        self.setWindowState(self.windowState() | Qt.WindowState.WindowActive)
        self._fade_in.start()
        print("[SPLASH] Fade-in animation started")

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


def show_startup_splash_if_available() -> Optional[StartupSplash]:
    """
    Convenience helper to be called after QApplication is created.
    Safe to call on all platforms; it will no‑op if the image is missing.
    Returns the splash widget so it can be kept alive.
    """
    app = QApplication.instance()
    if app is None:
        return None

    try:
        splash = StartupSplash()
        # If there is no valid pixmap, it will emit finished immediately
        splash.show_slow()
        # Process events immediately to show the splash
        app.processEvents()
        return splash
    except Exception as e:
        print(f"[WARN] Failed to create splash screen: {e}")
        import traceback
        traceback.print_exc()
        return None


