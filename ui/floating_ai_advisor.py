"""
Floating AI Advisor
Persistent floating icon with chat overlay that can be accessed from any screen.
"""

from __future__ import annotations

import logging
from typing import Optional, Callable

from PySide6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, Signal, QSize
from PySide6.QtGui import QColor, QFont, QPainter, QBrush, QPen, QMouseEvent
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QLineEdit,
    QFrame,
    QScrollArea,
)

from ui.ui_scaling import get_scaled_size, get_scaled_font_size
from ui.ai_advisor_widget import AIAdvisorWidget

LOGGER = logging.getLogger(__name__)


class FloatingAIIcon(QWidget):
    """Floating AI icon that's always accessible."""
    
    clicked = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(60, 60)
        
        # Make it draggable
        self._drag_position = QPoint()
        self._is_dragging = False
    
    def paintEvent(self, event) -> None:
        """Paint the floating AI icon."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw circular background with glow
        center = self.rect().center()
        radius = min(self.width(), self.height()) // 2 - 5
        
        # Outer glow
        gradient = QBrush(QColor(0, 224, 255, 100))
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, radius + 5, radius + 5)
        
        # Main circle
        painter.setBrush(QBrush(QColor(0, 224, 255)))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawEllipse(center, radius, radius)
        
        # "Q" text
        font = QFont("Arial", 24, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Q")
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press for dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move for dragging."""
        if self._is_dragging and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release."""
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._is_dragging:
                # Single click - open chat
                self.clicked.emit()
            self._is_dragging = False
            event.accept()
    
    def enterEvent(self, event) -> None:
        """Handle mouse enter for hover effect."""
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        super().enterEvent(event)
    
    def leaveEvent(self, event) -> None:
        """Handle mouse leave."""
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().leaveEvent(event)


class ActionableSuggestionButton(QPushButton):
    """Button for actionable AI suggestions that navigate to specific screens."""
    
    def __init__(self, text: str, action_type: str, action_data: dict, parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.action_type = action_type  # "navigate", "highlight_cell", "load_tune", etc.
        self.action_data = action_data
        
        font_size = get_scaled_font_size(11)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #00e0ff;
                color: #000000;
                font-size: {font_size}px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: #33e8ff;
            }}
        """)


class AIChatOverlay(QWidget):
    """Chat overlay that appears over the current screen."""
    
    navigate_to_screen = Signal(str, dict)  # screen_name, action_data
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.ai_widget: Optional[AIAdvisorWidget] = None
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Setup chat overlay UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main frame with rounded corners
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(10, 14, 39, 240);
                border: 2px solid #00e0ff;
                border-radius: 12px;
            }
        """)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(15, 15, 15, 15)
        frame_layout.setSpacing(10)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("AI Advisor - Q")
        font_size = get_scaled_font_size(16)
        title.setStyleSheet(f"""
            font-size: {font_size}px;
            font-weight: bold;
            color: #00e0ff;
        """)
        header.addWidget(title)
        
        header.addStretch()
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                color: #ffffff;
                font-size: 20px;
                font-weight: bold;
                border: none;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: #ff6666;
            }
        """)
        close_btn.clicked.connect(self.hide)
        header.addWidget(close_btn)
        
        frame_layout.addLayout(header)
        
        # AI Advisor widget
        try:
            self.ai_widget = AIAdvisorWidget()
            self.ai_widget.advisor_responded.connect(self._handle_advisor_response)
            frame_layout.addWidget(self.ai_widget, stretch=1)
        except Exception as e:
            LOGGER.error("Failed to create AI advisor widget: %s", e)
            error_label = QLabel("AI Advisor unavailable")
            error_label.setStyleSheet("color: #ff4444;")
            frame_layout.addWidget(error_label)
        
        # Actionable suggestions area
        self.suggestions_area = QWidget()
        suggestions_layout = QVBoxLayout(self.suggestions_area)
        suggestions_layout.setContentsMargins(0, 0, 0, 0)
        
        suggestions_label = QLabel("Quick Actions:")
        suggestions_label.setStyleSheet(f"""
            font-size: {get_scaled_font_size(12)}px;
            font-weight: bold;
            color: #ffffff;
        """)
        suggestions_layout.addWidget(suggestions_label)
        
        self.suggestions_container = QWidget()
        self.suggestions_layout = QVBoxLayout(self.suggestions_container)
        self.suggestions_layout.setContentsMargins(0, 0, 0, 0)
        self.suggestions_layout.setSpacing(5)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.suggestions_container)
        scroll.setMaximumHeight(100)
        scroll.setStyleSheet("border: none; background: transparent;")
        suggestions_layout.addWidget(scroll)
        
        frame_layout.addWidget(self.suggestions_area)
        
        layout.addWidget(frame)
    
    def _handle_advisor_response(self, response: str) -> None:
        """Handle AI advisor response and extract actionable suggestions."""
        # Parse response for actionable suggestions
        # This would parse the ResponseResult for recommendations
        # For now, just clear old suggestions
        self._clear_suggestions()
    
    def _clear_suggestions(self) -> None:
        """Clear actionable suggestions."""
        # Store widget references to ensure proper cleanup
        widgets_to_delete = []
        while self.suggestions_layout.count():
            item = self.suggestions_layout.takeAt(0)
            if item.widget():
                widgets_to_delete.append(item.widget())
        
        # Delete all widgets
        for widget in widgets_to_delete:
            widget.setParent(None)
            widget.deleteLater()
    
    def add_actionable_suggestion(self, text: str, action_type: str, action_data: dict) -> None:
        """Add an actionable suggestion button."""
        btn = ActionableSuggestionButton(text, action_type, action_data)
        btn.clicked.connect(lambda: self._handle_action(action_type, action_data))
        self.suggestions_layout.addWidget(btn)
    
    def _handle_action(self, action_type: str, action_data: dict) -> None:
        """Handle actionable suggestion click."""
        if action_type == "navigate":
            screen_name = action_data.get("screen")
            self.navigate_to_screen.emit(screen_name, action_data)
        elif action_type == "highlight_cell":
            # Navigate to tuning screen and highlight specific cell
            self.navigate_to_screen.emit("ecu_tuning", action_data)
        elif action_type == "load_tune":
            # Load a specific tune
            tune_name = action_data.get("tune_name")
            self.navigate_to_screen.emit("tune_database", {"action": "load", "tune": tune_name})
        
        self.hide()
    
    def show_overlay(self, parent_widget: Optional[QWidget] = None) -> None:
        """Show overlay positioned relative to parent."""
        if parent_widget:
            # Position overlay near parent
            parent_rect = parent_widget.geometry()
            self.setFixedSize(500, 600)
            self.move(
                parent_rect.x() + (parent_rect.width() - 500) // 2,
                parent_rect.y() + (parent_rect.height() - 600) // 2
            )
        self.show()
        self.raise_()
        self.activateWindow()


class FloatingAIAdvisorManager:
    """Manages floating AI advisor icon and chat overlay."""
    
    def __init__(self, parent_window: QWidget):
        self.parent_window = parent_window
        self.floating_icon: Optional[FloatingAIIcon] = None
        self.chat_overlay: Optional[AIChatOverlay] = None
        
        self._setup_floating_icon()
        self._setup_chat_overlay()
    
    def _setup_floating_icon(self) -> None:
        """Setup floating AI icon."""
        self.floating_icon = FloatingAIIcon(self.parent_window)
        self.floating_icon.clicked.connect(self._show_chat)
        
        # Position in bottom-right corner
        if self.parent_window:
            parent_rect = self.parent_window.geometry()
            self.floating_icon.move(
                parent_rect.width() - 80,
                parent_rect.height() - 80
            )
        
        self.floating_icon.show()
    
    def _setup_chat_overlay(self) -> None:
        """Setup chat overlay."""
        self.chat_overlay = AIChatOverlay(self.parent_window)
        self.chat_overlay.hide()
    
    def _show_chat(self) -> None:
        """Show chat overlay."""
        if self.chat_overlay:
            self.chat_overlay.show_overlay(self.parent_window)
    
    def hide_all(self) -> None:
        """Hide floating icon and chat overlay."""
        if self.floating_icon:
            self.floating_icon.hide()
        if self.chat_overlay:
            self.chat_overlay.hide()
    
    def show_all(self) -> None:
        """Show floating icon."""
        if self.floating_icon:
            self.floating_icon.show()

