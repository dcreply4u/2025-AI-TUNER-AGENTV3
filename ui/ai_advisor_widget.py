"""
AI Advisor Widget - "Q"
Chat widget for AI advisor that answers questions about the software
"""

from __future__ import annotations

from typing import Optional, Dict, Any

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
    QSizePolicy,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size
from ui.racing_ui_theme import get_racing_stylesheet, RacingColor

try:
    # Try RAG advisor first (modern, production-ready)
    from services.ai_advisor_rag import RAGAIAdvisor, RAGResponse
    RAG_ADVISOR_AVAILABLE = True
    ADVISOR_TYPE = "rag"
except ImportError as e:
    RAG_ADVISOR_AVAILABLE = False
    RAGAIAdvisor = None  # type: ignore
    RAGResponse = None  # type: ignore
    import logging
    logging.getLogger(__name__).debug(f"RAG advisor not available: {e}")

try:
    # Fallback to ultra-enhanced advisor
    from services.ai_advisor_ultra_enhanced import UltraEnhancedAIAdvisor as AIAdvisorQ
    ADVISOR_AVAILABLE = True
    if not RAG_ADVISOR_AVAILABLE:
        ADVISOR_TYPE = "ultra_enhanced"
except ImportError:
    try:
        # Fallback to enhanced advisor
        from services.ai_advisor_q_enhanced import EnhancedAIAdvisorQ as AIAdvisorQ
        ADVISOR_AVAILABLE = True
        if not RAG_ADVISOR_AVAILABLE:
            ADVISOR_TYPE = "enhanced"
    except ImportError:
        try:
            # Fallback to basic advisor
            from services.ai_advisor_q import AIAdvisorQ
            ADVISOR_AVAILABLE = True
            if not RAG_ADVISOR_AVAILABLE:
                ADVISOR_TYPE = "basic"
        except ImportError:
            ADVISOR_AVAILABLE = False
            if not RAG_ADVISOR_AVAILABLE:
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
        self.advisor = None
        self.advisor_type = None
        
        # Track last interaction for feedback
        self.last_question: Optional[str] = None
        self.last_answer: Optional[str] = None
        self.last_confidence: float = 0.0
        self.last_sources: List[str] = []
        
        try:
            # Try to initialize config monitor (optional)
            try:
                from services.intelligent_config_monitor import IntelligentConfigMonitor
                from services.config_version_control import ConfigVersionControl
                
                config_vc = ConfigVersionControl()
                self.config_monitor = IntelligentConfigMonitor(config_vc=config_vc)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Config monitor not available: {e}")
                self.config_monitor = None
            
            # Create telemetry provider function
            def get_telemetry():
                # Try to get telemetry from parent window if available
                parent = self.parent()
                while parent:
                    if hasattr(parent, '_telemetry_data'):
                        return parent._telemetry_data
                    parent = parent.parent()
                return None
            
            # Try RAG advisor first (modern, production-ready)
            if RAG_ADVISOR_AVAILABLE and RAGAIAdvisor:
                try:
                    # Initialize vector store and migrate knowledge if needed
                    from services.vector_knowledge_store import VectorKnowledgeStore
                    from services.migrate_knowledge_to_rag import migrate_from_enhanced_advisor
                    
                    vector_store = VectorKnowledgeStore()
                    
                    # Migrate knowledge if store is empty
                    if vector_store.count() == 0:
                        import logging
                        logging.getLogger(__name__).info("Vector store is empty, migrating knowledge...")
                        migrate_from_enhanced_advisor(vector_store)
                    
                    # Initialize RAG advisor
                    self.advisor = RAGAIAdvisor(
                        use_local_llm=True,  # Use Ollama if available
                        llm_model="llama3.2:3b",  # Lightweight model for Raspberry Pi
                        enable_web_search=True,
                        telemetry_provider=get_telemetry,
                        vector_store=vector_store
                    )
                    self.advisor_type = "rag"
                    
                    import logging
                    logging.getLogger(__name__).info("RAG AI Advisor initialized (production-ready)")
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Failed to initialize RAG advisor: {e}", exc_info=True)
                    self.advisor = None
            
            # Fallback to legacy advisors if RAG failed
            if not self.advisor and ADVISOR_AVAILABLE and AIAdvisorQ:
                try:
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
                            user_id=None,
                            use_local_llm=False,
                        )
                        self.advisor_type = "ultra_enhanced"
                    elif ADVISOR_TYPE == "enhanced":
                        self.advisor = AIAdvisorQ(
                            use_llm=False,
                            config_monitor=self.config_monitor,
                            telemetry_provider=get_telemetry,
                        )
                        self.advisor_type = "enhanced"
                    else:
                        self.advisor = AIAdvisorQ()
                        self.advisor_type = "basic"
                    
                    import logging
                    logging.getLogger(__name__).info(f"AI Advisor initialized: {self.advisor_type} (legacy)")
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Failed to initialize {ADVISOR_TYPE} advisor: {e}", exc_info=True)
                    # Try fallback to basic advisor
                    try:
                        from services.ai_advisor_q import AIAdvisorQ as BasicAdvisor
                        self.advisor = BasicAdvisor()
                        self.advisor_type = "basic"
                        logging.getLogger(__name__).info("Fell back to basic AI advisor")
                    except Exception as e2:
                        logging.getLogger(__name__).error(f"Failed to initialize basic advisor: {e2}", exc_info=True)
                        self.advisor = None
            elif not self.advisor:
                import logging
                logging.getLogger(__name__).warning("AI Advisor not available - no advisor service found")
                self.advisor = None
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to initialize AI advisor system: {e}", exc_info=True)
            self.advisor = None
        
        self.setup_ui()
        self._show_welcome_message()
    
    def setup_ui(self) -> None:
        """Setup AI advisor widget with light theme."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(4)  # Reduced spacing to prevent overlap
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("🤖 Q - AI Advisor")
        title.setStyleSheet("""
            font-size: 12px;
            font-weight: bold;
            color: #2c3e50;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                color: #2c3e50;
                padding: 4px 10px;
                font-size: 10px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
            }
        """)
        clear_btn.clicked.connect(self._clear_chat)
        header_layout.addWidget(clear_btn)
        
        main_layout.addLayout(header_layout)
        
        # Chat display - light theme (positioned first to ensure it has space)
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                color: #2c3e50;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding: 4px;
            }
            QScrollBar:vertical {
                background-color: #e0e0e0;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #3498db;
                border-radius: 4px;
                min-height: 20px;
            }
        """)
        # Chat display - make it expandable but with reasonable limits
        # Use size policy to ensure it takes available space
        self.chat_display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.chat_display.setMinimumHeight(180)
        self.chat_display.setMaximumHeight(350)  # Increased to give more room
        main_layout.addWidget(self.chat_display, stretch=10)  # Give chat very high stretch priority
        
        # Suggestions - light theme (positioned BELOW chat window, above input)
        self.suggestions_list = QListWidget()
        self.suggestions_list.setMaximumHeight(40)  # Further reduced height
        self.suggestions_list.setFixedHeight(0)  # Start with 0 height when hidden
        self.suggestions_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # Fixed height, don't expand
        self.suggestions_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 10px;
            }
            QListWidget::item {
                padding: 3px;
            }
            QListWidget::item:hover {
                background-color: #ecf0f1;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        self.suggestions_list.itemClicked.connect(self._on_suggestion_clicked)
        self.suggestions_list.hide()
        # Add with stretch=0 so it doesn't take space when hidden - BELOW chat, above input
        main_layout.addWidget(self.suggestions_list, stretch=0)
        
        # Input area
        input_layout = QHBoxLayout()
        input_layout.setSpacing(6)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask Q anything...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding: 6px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """)
        self.input_field.returnPressed.connect(self._send_message)
        self.input_field.textChanged.connect(self._on_input_changed)
        input_layout.addWidget(self.input_field, stretch=1)
        
        send_btn = QPushButton("Send")
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(send_btn)
        
        main_layout.addLayout(input_layout)
        
        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #27ae60; font-size: 9px;")
        main_layout.addWidget(self.status_label)
    
    def _show_welcome_message(self) -> None:
        """Show welcome message from Q."""
        welcome = """<b style="color: #3498db;">Q:</b> <span style="color: #2c3e50;">Hello! I'm Q, your AI advisor. I can help with:
<br>• Software features
<br>• Troubleshooting
<br>• Tips & best practices
<br><br>What would you like to know?</span>"""
        
        self.chat_display.setHtml(welcome)
    
    def _on_input_changed(self, text: str) -> None:
        """Handle input text changes for suggestions."""
        if not self.advisor:
            return
        
        try:
            if not text.strip():
                # Show suggestions when input is empty
                if hasattr(self.advisor, 'get_suggestions'):
                    suggestions = self.advisor.get_suggestions("")
                    self.suggestions_list.clear()
                    for suggestion in suggestions:
                        item = QListWidgetItem(suggestion)
                        self.suggestions_list.addItem(item)
                    if self.suggestions_list.count() > 0:
                        self.suggestions_list.setFixedHeight(40)
                        self.suggestions_list.show()
                    else:
                        self.suggestions_list.setFixedHeight(0)
                        self.suggestions_list.hide()
                else:
                    self.suggestions_list.setFixedHeight(0)
                    self.suggestions_list.hide()
            else:
                # Show filtered suggestions
                if hasattr(self.advisor, 'get_suggestions'):
                    suggestions = self.advisor.get_suggestions(text)
                    self.suggestions_list.clear()
                    for suggestion in suggestions:
                        if text.lower() in suggestion.lower():
                            item = QListWidgetItem(suggestion)
                            self.suggestions_list.addItem(item)
                    
                    if self.suggestions_list.count() > 0:
                        self.suggestions_list.setFixedHeight(40)
                        self.suggestions_list.show()
                    else:
                        self.suggestions_list.setFixedHeight(0)
                        self.suggestions_list.hide()
                else:
                    self.suggestions_list.setFixedHeight(0)
                    self.suggestions_list.hide()
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"Error getting suggestions: {e}")
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
        
        # Hide suggestions and reset height
        self.suggestions_list.setFixedHeight(0)
        self.suggestions_list.hide()
        
        # Add user message
        self._add_message("You", question, is_user=True)
        
        # Clear input
        self.input_field.clear()
        
        # Update status
        self.status_label.setText("Q is thinking...")
        self.status_label.setStyleSheet("color: #f39c12; font-size: 9px;")
        
        # Get response (with slight delay for better UX)
        QTimer.singleShot(100, lambda: self._get_response(question))
    
    def _get_response(self, question: str) -> None:
        """Get response from Q."""
        if not self.advisor:
            error_msg = "Sorry, AI advisor is not available. Please check the logs for initialization errors."
            self._add_message("Q", error_msg, is_user=False)
            self.status_label.setText("Advisor unavailable")
            self.status_label.setStyleSheet("color: #e74c3c; font-size: 9px;")
            return
        
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            # Get context (could include current tab, etc.)
            context = {}
            
            # Try to get telemetry for context
            parent = self.parent()
            while parent:
                if hasattr(parent, '_telemetry_data'):
                    context['telemetry'] = parent._telemetry_data
                    break
                parent = parent.parent()
            
            # Ask Q - try RAG advisor first, then legacy advisors
            result = None
            telemetry = context.get('telemetry')
            
            try:
                # Check if RAG advisor
                if self.advisor_type == "rag" and hasattr(self.advisor, 'answer'):
                    logger.debug(f"Calling RAG advisor.answer() with question: {question[:50]}...")
                    result = self.advisor.answer(question, telemetry=telemetry, context=context)
                elif hasattr(self.advisor, 'answer'):
                    # Ultra-enhanced advisor
                    logger.debug(f"Calling ultra-enhanced advisor.answer() with question: {question[:50]}...")
                    result = self.advisor.answer(question, telemetry=telemetry, context=context)
                elif hasattr(self.advisor, 'ask'):
                    # Enhanced advisor
                    logger.debug(f"Calling enhanced advisor.ask() with question: {question[:50]}...")
                    result = self.advisor.ask(question, context=context)
                else:
                    # Fallback - try to call directly
                    logger.warning("Advisor has no 'answer' or 'ask' method, trying direct call")
                    if callable(self.advisor):
                        result = self.advisor(question)
                    else:
                        result = "Advisor not properly initialized"
            except AttributeError as e:
                logger.error(f"Advisor method call failed: {e}", exc_info=True)
                raise
            except Exception as e:
                logger.error(f"Error calling advisor: {e}", exc_info=True)
                raise
            
            # Handle RAGResponse, ResponseResult, and string responses
            sources = []  # Initialize sources variable
            confidence = 0.0  # Initialize confidence variable
            
            if result is None:
                response = "I received your question but couldn't generate a response. Please try rephrasing."
                follow_ups = []
                warnings = []
            elif isinstance(result, RAGResponse):
                # RAGResponse object (new RAG advisor)
                response = result.answer
                confidence = result.confidence
                follow_ups = result.follow_up_questions
                warnings = result.warnings
                sources = result.sources  # Extract sources from RAGResponse
                
                # Add sources info if available
                if result.sources:
                    source_count = len(result.sources)
                    if result.used_web_search:
                        response += f"\n\n📚 Sources: {source_count} knowledge entries + web research"
                    else:
                        response += f"\n\n📚 Sources: {source_count} knowledge entries"
                
                # Add warnings if any
                if warnings:
                    response += "\n\n" + "\n".join(warnings)
            elif hasattr(result, 'answer'):
                # ResponseResult object (legacy enhanced advisor)
                response = result.answer
                confidence = getattr(result, 'confidence', 1.0)
                follow_ups = getattr(result, 'follow_up_questions', [])
                warnings = getattr(result, 'warnings', [])
                # Try to get sources if available
                if hasattr(result, 'sources'):
                    sources = result.sources
            else:
                # String response
                response = str(result)
                follow_ups = []
                warnings = []
            
            # Show follow-up questions in suggestions list
            if follow_ups:
                self.suggestions_list.clear()
                for follow_up in follow_ups[:3]:  # Limit to 3
                    item = QListWidgetItem(f"💡 {follow_up}")
                    self.suggestions_list.addItem(item)
                if self.suggestions_list.count() > 0:
                    self.suggestions_list.setFixedHeight(40)
                    self.suggestions_list.show()
            
            # Ensure we have a valid response
            if not response or response.strip() == "":
                response = "I'm not sure how to answer that. Could you try rephrasing your question?"
            
            # Store last interaction for feedback
            self.last_question = question
            self.last_answer = response
            self.last_confidence = confidence
            self.last_sources = [s.get("title", s.get("text", ""))[:50] if isinstance(s, dict) else str(s)[:50] for s in sources] if sources else []
            
            # Add response
            self._add_message("Q", response, is_user=False)
            
            # Emit signal
            self.advisor_responded.emit(response)
            
            # Update status
            self.status_label.setText("Ready")
            self.status_label.setStyleSheet("color: #27ae60; font-size: 9px;")
            
        except Exception as e:
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"Error in AI advisor response: {e}", exc_info=True)
            
            error_msg = f"Sorry, I encountered an error: {str(e)}\n\nPlease check the logs for more details."
            self._add_message("Q", error_msg, is_user=False)
            self.status_label.setText("Error")
            self.status_label.setStyleSheet("color: #e74c3c; font-size: 9px;")
    
    def _add_message(self, sender: str, message: str, is_user: bool = False) -> None:
        """Add message to chat display."""
        sender_color = "#3498db" if not is_user else "#27ae60"  # Blue for Q, Green for user
        
        html = f"""
        <div style="margin-bottom: 8px;">
            <b style="color: {sender_color};">{sender}:</b>
            <span style="color: #2c3e50; white-space: pre-wrap;">{self._escape_html(message)}</span>
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
    
    def record_feedback(self, helpful: bool, rating: Optional[int] = None, comment: Optional[str] = None) -> None:
        """
        Record user feedback for the last interaction.
        
        Args:
            helpful: Whether the answer was helpful
            rating: Optional rating (1-5)
            comment: Optional comment
        """
        if not self.last_question or not self.last_answer:
            return
        
        if self.advisor and hasattr(self.advisor, 'record_feedback'):
            try:
                # Get session/vehicle context if available
                session_id = None
                vehicle_id = None
                parent = self.parent()
                while parent:
                    if hasattr(parent, '_session_id'):
                        session_id = parent._session_id
                    if hasattr(parent, '_vehicle_id'):
                        vehicle_id = parent._vehicle_id
                    parent = parent.parent()
                
                self.advisor.record_feedback(
                    question=self.last_question,
                    answer=self.last_answer,
                    helpful=helpful,
                    rating=rating,
                    comment=comment,
                    session_id=session_id,
                    vehicle_id=vehicle_id,
                    confidence=self.last_confidence,
                    sources=self.last_sources
                )
                
                # Show confirmation
                self.status_label.setText("Feedback recorded - thank you!")
                self.status_label.setStyleSheet("color: #27ae60; font-size: 9px;")
                QTimer.singleShot(3000, lambda: self.status_label.setText("Ready"))
                
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Failed to record feedback: {e}")
    
    def _clear_chat(self) -> None:
        """Clear chat history."""
        # Clear feedback tracking
        self.last_question = None
        self.last_answer = None
        self.last_confidence = 0.0
        self.last_sources = []
        
        if self.advisor:
            if hasattr(self.advisor, 'clear_history'):
                try:
                    self.advisor.clear_history()
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).debug(f"Error clearing history: {e}")
            elif hasattr(self.advisor, 'conversation_history'):
                # RAG advisor uses conversation_history
                try:
                    self.advisor.conversation_history.clear()
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).debug(f"Error clearing RAG history: {e}")
        self.chat_display.clear()
        self._show_welcome_message()
    
    def ask_question(self, question: str) -> None:
        """Programmatically ask a question."""
        self.input_field.setText(question)
        self._send_message()
    
    def update_context(self, context: Dict[str, Any]) -> None:
        """Update advisor context (current tab, etc.)."""
        # Could be used to provide context-aware responses
        pass

