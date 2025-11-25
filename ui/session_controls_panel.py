"""
Session Controls Panel - Modern styled control buttons.

Matches the light theme design of other panels (Wheel Slip Monitor, Streaming Panel).

Features:
- Categorized button groups
- Modern styling with icons
- Consistent visual design
- Hover effects and animations
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class StyledButton(QPushButton):
    """Modern styled button with icon and hover effects."""
    
    def __init__(
        self,
        text: str,
        icon: str = "",
        color: str = "default",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        
        self.base_text = text
        self.icon = icon
        self.color_scheme = color
        
        self.setText(f"{icon}  {text}" if icon else text)
        self.setMinimumHeight(36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._apply_style()
    
    def _apply_style(self) -> None:
        """Apply color-coded styling."""
        styles = {
            "default": {
                "bg": "#3498db",
                "bg_hover": "#2980b9",
                "text": "white",
            },
            "success": {
                "bg": "#27ae60",
                "bg_hover": "#229954",
                "text": "white",
            },
            "warning": {
                "bg": "#f39c12",
                "bg_hover": "#d68910",
                "text": "white",
            },
            "danger": {
                "bg": "#e74c3c",
                "bg_hover": "#c0392b",
                "text": "white",
            },
            "info": {
                "bg": "#9b59b6",
                "bg_hover": "#8e44ad",
                "text": "white",
            },
            "dark": {
                "bg": "#34495e",
                "bg_hover": "#2c3e50",
                "text": "white",
            },
            "light": {
                "bg": "#ecf0f1",
                "bg_hover": "#bdc3c7",
                "text": "#2c3e50",
            },
            "cyan": {
                "bg": "#00bcd4",
                "bg_hover": "#00acc1",
                "text": "white",
            },
        }
        
        s = styles.get(self.color_scheme, styles["default"])
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {s['bg']};
                color: {s['text']};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 11px;
                font-weight: bold;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {s['bg_hover']};
            }}
            QPushButton:pressed {{
                background-color: {s['bg_hover']};
                padding-left: 18px;
            }}
            QPushButton:disabled {{
                background-color: #bdc3c7;
                color: #7f8c8d;
            }}
        """)


class ButtonGroup(QFrame):
    """Group of related buttons with a label."""
    
    def __init__(
        self,
        title: str,
        icon: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("background: transparent;")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(6)
        
        # Header
        header = QLabel(f"{icon} {title}" if icon else title)
        header.setStyleSheet("""
            color: #7f8c8d;
            font-size: 10px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 4px 0;
        """)
        self.layout.addWidget(header)
        
        # Buttons container
        self.buttons_layout = QVBoxLayout()
        self.buttons_layout.setSpacing(4)
        self.layout.addLayout(self.buttons_layout)
    
    def add_button(self, button: QPushButton) -> None:
        """Add a button to the group."""
        self.buttons_layout.addWidget(button)


class SessionControlsPanel(QFrame):
    """
    Modern session controls panel with categorized buttons.
    
    Matches the visual style of other panels.
    """
    
    # Signals for button clicks
    start_session_clicked = Signal()
    voice_control_clicked = Signal()
    replay_log_clicked = Signal()
    settings_clicked = Signal()
    theme_clicked = Signal()
    diagnostics_clicked = Signal()
    email_logs_clicked = Signal()
    export_data_clicked = Signal()
    configure_cameras_clicked = Signal()
    video_overlay_clicked = Signal()
    external_display_clicked = Signal()
    
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
            }
        """)
        
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Header
        header = QLabel("🎮 Session Controls")
        header.setStyleSheet("font-size: 14px; font-weight: 700; color: #2c3e50;")
        layout.addWidget(header)
        
        # Session Group
        session_group = ButtonGroup("Session", "🏁")
        
        self.start_btn = StyledButton("Start Session", "▶️", "success")
        self.start_btn.clicked.connect(self.start_session_clicked.emit)
        session_group.add_button(self.start_btn)
        
        self.voice_btn = StyledButton("Voice Control", "🎤", "cyan")
        self.voice_btn.clicked.connect(self.voice_control_clicked.emit)
        session_group.add_button(self.voice_btn)
        
        self.replay_btn = StyledButton("Replay Log", "⏪", "default")
        self.replay_btn.clicked.connect(self.replay_log_clicked.emit)
        session_group.add_button(self.replay_btn)
        
        layout.addWidget(session_group)
        
        # Camera Group
        camera_group = ButtonGroup("Camera & Display", "📹")
        
        self.camera_btn = StyledButton("Configure Cameras", "📷", "dark")
        self.camera_btn.clicked.connect(self.configure_cameras_clicked.emit)
        camera_group.add_button(self.camera_btn)
        
        self.overlay_btn = StyledButton("Video Overlay", "🎬", "dark")
        self.overlay_btn.clicked.connect(self.video_overlay_clicked.emit)
        camera_group.add_button(self.overlay_btn)
        
        self.display_btn = StyledButton("External Display", "🖥️", "info")
        self.display_btn.clicked.connect(self.external_display_clicked.emit)
        camera_group.add_button(self.display_btn)
        
        layout.addWidget(camera_group)
        
        # Tools Group
        tools_group = ButtonGroup("Tools & Settings", "🔧")
        
        self.settings_btn = StyledButton("Settings", "⚙️", "light")
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
        tools_group.add_button(self.settings_btn)
        
        self.theme_btn = StyledButton("Theme", "🎨", "light")
        self.theme_btn.clicked.connect(self.theme_clicked.emit)
        tools_group.add_button(self.theme_btn)
        
        self.diagnostics_btn = StyledButton("Diagnostics", "🔍", "warning")
        self.diagnostics_btn.clicked.connect(self.diagnostics_clicked.emit)
        tools_group.add_button(self.diagnostics_btn)
        
        layout.addWidget(tools_group)
        
        # Data Group
        data_group = ButtonGroup("Data & Export", "📊")
        
        self.email_btn = StyledButton("Email Logs", "📧", "default")
        self.email_btn.clicked.connect(self.email_logs_clicked.emit)
        data_group.add_button(self.email_btn)
        
        self.export_btn = StyledButton("Export Data", "💾", "default")
        self.export_btn.clicked.connect(self.export_data_clicked.emit)
        data_group.add_button(self.export_btn)
        
        layout.addWidget(data_group)
        
        layout.addStretch()
    
    def set_session_active(self, active: bool) -> None:
        """Update session button state."""
        if active:
            self.start_btn.setText("⏹️  Stop Session")
            self.start_btn.color_scheme = "danger"
        else:
            self.start_btn.setText("▶️  Start Session")
            self.start_btn.color_scheme = "success"
        self.start_btn._apply_style()
    
    def set_voice_active(self, active: bool) -> None:
        """Update voice control button state."""
        if active:
            self.voice_btn.setText("🎤  Voice Active")
            self.voice_btn.color_scheme = "success"
        else:
            self.voice_btn.setText("🎤  Voice Control")
            self.voice_btn.color_scheme = "cyan"
        self.voice_btn._apply_style()
    
    def enable_camera_buttons(self, enabled: bool) -> None:
        """Enable/disable camera-related buttons."""
        self.camera_btn.setEnabled(enabled)
        self.overlay_btn.setEnabled(enabled)


__all__ = [
    "SessionControlsPanel",
    "StyledButton",
    "ButtonGroup",
]




