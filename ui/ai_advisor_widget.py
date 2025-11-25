"""
AI Advisor Widget - "Q"
Chat widget for AI advisor that answers questions about the software
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QTextCharFormat, QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size
from ui.racing_ui_theme import get_racing_stylesheet, RacingColor

try:
    # Try ultra-enhanced advisor first
    from services.ai_advisor_ultra_enhanced import UltraEnhancedAIAdvisor as AIAdvisorQ
    ADVISOR_AVAILABLE = True
    ADVISOR_TYPE = "ultra_enhanced"
except ImportError:
    try:
        # Fallback to enhanced advisor
        from services.ai_advisor_q_enhanced import EnhancedAIAdvisorQ as AIAdvisorQ
        ADVISOR_AVAILABLE = True
        ADVISOR_TYPE = "enhanced"
    except ImportError:
        try:
            # Fallback to basic advisor
            from services.ai_advisor_q import AIAdvisorQ
            ADVISOR_AVAILABLE = True
            ADVISOR_TYPE = "basic"
        except ImportError:
            ADVISOR_AVAILABLE = False
            ADVISOR_TYPE = "none"
            AIAdvisorQ = None  # type: ignore


class AIAdvisorWidget(QWidget):
    """
    AI Advisor Widget - "Q"
    Chat interface for software help and assistance
    """
    
    # Signal emitted when advisor responds
    advisor_responded = Signal(str)
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        
        # Initialize configuration monitor and AI advisor
        self.config_monitor = None
        self.advisor: Optional[AIAdvisorQ] = None
        
        try:
            from services.intelligent_config_monitor import IntelligentConfigMonitor
            from services.config_version_control import ConfigVersionControl
            
            config_vc = ConfigVersionControl()
            self.config_monitor = IntelligentConfigMonitor(config_vc=config_vc)
            
            if ADVISOR_AVAILABLE and AIAdvisorQ:
                # Create telemetry provider function
                def get_telemetry():
                    # Try to get telemetry from parent window if available
                    parent = self.parent()
                    while parent:
                        if hasattr(parent, '_telemetry_data'):
                            return parent._telemetry_data
                        parent = parent.parent()
                    return None
                
                # Initialize advisor based on type
                if ADVISOR_TYPE == "ultra_enhanced":
                    # Get vehicle ID from context if available
                    vehicle_id = None
                    parent = self.parent()
                    while parent:
                        if hasattr(parent, 'vehicle_id'):
                            vehicle_id = parent.vehicle_id
                            break
                        parent = parent.parent()
                    
                    self.advisor = AIAdvisorQ(
                        vehicle_id=vehicle_id,
                        user_id=None,  # Could get from user context
                        use_local_llm=False,  # Can enable if Ollama/etc available
                    )
                elif ADVISOR_TYPE == "enhanced":
                    self.advisor = AIAdvisorQ(
                        use_llm=False,
                        config_monitor=self.config_monitor,
                        telemetry_provider=get_telemetry,
                    )
                else:
                    self.advisor = AIAdvisorQ()
        except Exception as e:
            print(f"Failed to initialize AI advisor: {e}")
        
        self.setup_ui()
        self._show_welcome_message()
    
    def setup_ui(self) -> None:
        """Setup AI advisor widget."""
        main_layout = QVBoxLayout(self)
        margin = self.scaler.get_scaled_size(5)
        spacing = self.scaler.get_scaled_size(5)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Q - AI Advisor")
        title_font = self.scaler.get_scaled_font_size(14)
        title.setStyleSheet(f"""
            font-size: {title_font}px;
            font-weight: bold;
            color: {RacingColor.ACCENT_NEON_BLUE.value};
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #404040;
                color: #ffffff;
                padding: {self.scaler.get_scaled_size(3)}px {self.scaler.get_scaled_size(8)}px;
                font-size: {self.scaler.get_scaled_font_size(9)}px;
                border: 1px solid #606060;
            }}
            QPushButton:hover {{
                background-color: #505050;
            }}
        """)
        clear_btn.clicked.connect(self._clear_chat)
        header_layout.addWidget(clear_btn)
        
        main_layout.addLayout(header_layout)
        
        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        chat_font = self.scaler.get_scaled_font_size(10)
        self.chat_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: #0a0a0a;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: {chat_font}px;
                border: 1px solid #404040;
                border-radius: {self.scaler.get_scaled_size(3)}px;
            }}
        """)
        self.chat_display.setMinimumHeight(self.scaler.get_scaled_size(300))
        main_layout.addWidget(self.chat_display, stretch=1)
        
        # Suggestions (hidden by default, shown when input is empty)
        self.suggestions_list = QListWidget()
        self.suggestions_list.setMaximumHeight(self.scaler.get_scaled_size(100))
        self.suggestions_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #404040;
                font-size: 10px;
            }
            QListWidget::item {
                padding: 4px;
            }
            QListWidget::item:hover {
                background-color: #2a2a2a;
            }
            QListWidget::item:selected {
                background-color: #0080ff;
            }
        """)
        self.suggestions_list.itemClicked.connect(self._on_suggestion_clicked)
        self.suggestions_list.hide()
        main_layout.addWidget(self.suggestions_list)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask Q anything about the software...")
        input_font = self.scaler.get_scaled_font_size(10)
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: {self.scaler.get_scaled_size(3)}px;
                padding: {self.scaler.get_scaled_size(5)}px;
                font-size: {input_font}px;
            }}
            QLineEdit:focus {{
                border: 2px solid {RacingColor.ACCENT_NEON_BLUE.value};
            }}
        """)
        self.input_field.returnPressed.connect(self._send_message)
        self.input_field.textChanged.connect(self._on_input_changed)
        input_layout.addWidget(self.input_field, stretch=1)
        
        send_btn = QPushButton("Send")
        btn_padding_v = self.scaler.get_scaled_size(5)
        btn_padding_h = self.scaler.get_scaled_size(12)
        send_btn.setStyleSheet(get_racing_stylesheet("button_primary"))
        send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(send_btn)
        
        main_layout.addLayout(input_layout)
        
        # Status
        self.status_label = QLabel("Ready")
        status_font = self.scaler.get_scaled_font_size(9)
        self.status_label.setStyleSheet(f"color: #00ff00; font-size: {status_font}px;")
        main_layout.addWidget(self.status_label)
    
    def _show_welcome_message(self) -> None:
        """Show welcome message from Q."""
        welcome = """<b style="color: #00e0ff;">Q:</b> Hello! I'm Q, your TelemetryIQ AI advisor. I can help you with:
<br>• Software features and configuration
<br>• Troubleshooting issues
<br>• Tips and best practices
<br>• Keyboard shortcuts
<br>• Hardware setup
<br><br>What would you like to know?"""
        
        self.chat_display.setHtml(welcome)
    
    def _on_input_changed(self, text: str) -> None:
        """Handle input text changes for suggestions."""
        if not self.advisor:
            return
        
        if not text.strip():
            # Show suggestions when input is empty
            suggestions = self.advisor.get_suggestions("")
            self.suggestions_list.clear()
            for suggestion in suggestions:
                item = QListWidgetItem(suggestion)
                self.suggestions_list.addItem(item)
            self.suggestions_list.show()
        else:
            # Show filtered suggestions
            suggestions = self.advisor.get_suggestions(text)
            self.suggestions_list.clear()
            for suggestion in suggestions:
                if text.lower() in suggestion.lower():
                    item = QListWidgetItem(suggestion)
                    self.suggestions_list.addItem(item)
            
            if self.suggestions_list.count() > 0:
                self.suggestions_list.show()
            else:
                self.suggestions_list.hide()
    
    def _on_suggestion_clicked(self, item: QListWidgetItem) -> None:
        """Handle suggestion click."""
        self.input_field.setText(item.text())
        self.suggestions_list.hide()
        self.input_field.setFocus()
    
    def _send_message(self) -> None:
        """Send message to Q."""
        question = self.input_field.text().strip()
        if not question:
            return
        
        if not self.advisor:
            self._add_message("Q", "Sorry, AI advisor is not available.", is_user=False)
            return
        
        # Hide suggestions
        self.suggestions_list.hide()
        
        # Add user message
        self._add_message("You", question, is_user=True)
        
        # Clear input
        self.input_field.clear()
        
        # Update status
        self.status_label.setText("Q is thinking...")
        self.status_label.setStyleSheet("color: #ff8000; font-size: 9px;")
        
        # Get response (with slight delay for better UX)
        QTimer.singleShot(100, lambda: self._get_response(question))
    
    def _get_response(self, question: str) -> None:
        """Get response from Q."""
        if not self.advisor:
            return
        
        try:
            # Get context (could include current tab, etc.)
            context = {}
            
            # Try to get telemetry for context
            parent = self.parent()
            while parent:
                if hasattr(parent, '_telemetry_data'):
                    context['telemetry'] = parent._telemetry_data
                    break
                parent = parent.parent()
            
            # Ask Q - try answer() method first (ultra-enhanced), then ask() (enhanced), then direct call
            result = None
            if hasattr(self.advisor, 'answer'):
                # Ultra-enhanced advisor
                telemetry = context.get('telemetry')
                result = self.advisor.answer(question, telemetry=telemetry, context=context)
            elif hasattr(self.advisor, 'ask'):
                # Enhanced advisor
                result = self.advisor.ask(question, context=context)
            else:
                # Fallback
                result = str(self.advisor) if self.advisor else "Advisor not available"
            
            # Handle both ResponseResult and string responses
            if hasattr(result, 'answer'):
                # ResponseResult object
                response = result.answer
                confidence = result.confidence
                
                # Add follow-up questions if available
                if result.follow_up_questions:
                    response += "\n\n💡 Related questions you might ask:\n"
                    for follow_up in result.follow_up_questions:
                        response += f"• {follow_up}\n"
            else:
                # String response
                response = str(result)
            
            # Add response
            self._add_message("Q", response, is_user=False)
            
            # Emit signal
            self.advisor_responded.emit(response)
            
            # Update status
            self.status_label.setText("Ready")
            self.status_label.setStyleSheet("color: #00ff00; font-size: 9px;")
            
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            self._add_message("Q", error_msg, is_user=False)
            self.status_label.setText("Error")
            self.status_label.setStyleSheet("color: #ff0000; font-size: 9px;")
    
    def _add_message(self, sender: str, message: str, is_user: bool = False) -> None:
        """Add message to chat display."""
        color = RacingColor.ACCENT_NEON_BLUE.value if not is_user else RacingColor.ACCENT_NEON_GREEN.value
        sender_color = "#00e0ff" if not is_user else "#00ff00"
        
        html = f"""
        <div style="margin-bottom: 10px;">
            <b style="color: {sender_color};">{sender}:</b>
            <span style="color: #ffffff; white-space: pre-wrap;">{self._escape_html(message)}</span>
        </div>
        """
        
        self.chat_display.append(html)
        
        # Scroll to bottom
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\n", "<br>"))
    
    def _clear_chat(self) -> None:
        """Clear chat history."""
        if self.advisor:
            self.advisor.clear_history()
        self.chat_display.clear()
        self._show_welcome_message()
    
    def ask_question(self, question: str) -> None:
        """Programmatically ask a question."""
        self.input_field.setText(question)
        self._send_message()
    
    def update_context(self, context: Dict[str, any]) -> None:
        """Update advisor context (current tab, etc.)."""
        # Could be used to provide context-aware responses
        pass

