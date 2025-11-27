"""
AI Advisor Widget - "Q"
Chat widget for AI advisor that answers questions about the software
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List

from PySide6.QtCore import Qt, QTimer, Signal, QUrl, QSize
from PySide6.QtGui import QFont, QTextCharFormat, QColor, QAction, QKeySequence, QPixmap, QImage, QIcon
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
    QToolBar,
    QFileDialog,
    QMessageBox,
    QMenu,
)
from pathlib import Path
import logging

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
                    
                    # CRITICAL: Ensure racing/tuning knowledge is loaded
                    try:
                        from services.ensure_racing_knowledge_loaded import ensure_racing_knowledge_loaded
                        added = ensure_racing_knowledge_loaded(vector_store)
                        if added > 0:
                            import logging
                            logging.getLogger(__name__).info(f"Loaded {added} racing/tuning knowledge entries into advisor")
                    except Exception as e:
                        import logging
                        logging.getLogger(__name__).warning(f"Could not load racing knowledge: {e}", exc_info=True)
                    
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
        """Setup AI advisor widget with Cursor-style compact layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(4)
        
        # Compact header - Cursor style
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        
        title = QLabel("Q")
        title.setStyleSheet("""
            font-size: 13px;
            font-weight: 600;
            color: #1a1a1a;
            padding: 0px;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Clear button with colorful icon
        clear_btn = QPushButton("✕")
        clear_btn.setToolTip("Clear chat")
        clear_btn.setFixedSize(24, 24)
        # Try multiple icon sources for better color support
        icon = None
        try:
            # Try Qt standard icons first (more colorful)
            from PySide6.QtWidgets import QStyle
            style = clear_btn.style()
            icon = style.standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)
            if icon.isNull():
                # Fallback to theme icons
                icon = QIcon.fromTheme("edit-clear")
                if icon.isNull():
                    icon = QIcon.fromTheme("clear")
                if icon.isNull():
                    icon = QIcon.fromTheme("edit-delete")
        except Exception:
            pass
        
        if icon and not icon.isNull():
            clear_btn.setIcon(icon)
            clear_btn.setText("")  # Remove text if icon works
            clear_btn.setIconSize(QSize(16, 16))
        
        # Colorful styling for clear button
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #e74c3c;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #fee;
                color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #fcc;
            }
        """)
        clear_btn.clicked.connect(self._clear_chat)
        header_layout.addWidget(clear_btn)
        
        main_layout.addLayout(header_layout)
        
        # Chat display - Cursor style: fixed size, clean background with better styling
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.chat_display.customContextMenuRequested.connect(self._show_context_menu)
        
        # Fixed height but expandable width
        self.chat_display.setFixedHeight(300)  # Slightly taller for better visibility
        self.chat_display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #fafafa;
                color: #1a1a1a;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif;
                font-size: 13px;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
                line-height: 1.5;
            }
            QScrollBar:vertical {
                background-color: #f5f5f5;
                width: 12px;
                border: none;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background-color: #c0c0c0;
                border-radius: 6px;
                min-height: 30px;
                margin: 1px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        main_layout.addWidget(self.chat_display)
        
        # Suggestions - compact, appears above input when available
        self.suggestions_list = QListWidget()
        self.suggestions_list.setFixedHeight(0)
        self.suggestions_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.suggestions_list.setStyleSheet("""
            QListWidget {
                background-color: #f8f8f8;
                color: #1a1a1a;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 4px 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:hover {
                background-color: #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #e8e8e8;
                color: #1a1a1a;
            }
        """)
        self.suggestions_list.itemClicked.connect(self._on_suggestion_clicked)
        self.suggestions_list.hide()
        main_layout.addWidget(self.suggestions_list)
        
        # Input area - Cursor style: clean, minimal
        input_layout = QHBoxLayout()
        input_layout.setSpacing(6)
        input_layout.setContentsMargins(0, 0, 0, 0)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask Q anything about tuning, racing, or the software...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #1a1a1a;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            }
            QLineEdit:focus {
                border: 2px solid #007acc;
                outline: none;
                background-color: #fafafa;
            }
            QLineEdit:hover {
                border: 1px solid #b0b0b0;
            }
        """)
        self.input_field.returnPressed.connect(self._send_message)
        self.input_field.textChanged.connect(self._on_input_changed)
        input_layout.addWidget(self.input_field, stretch=1)
        
        # Send button with colorful icon
        send_btn = QPushButton("→")
        send_btn.setToolTip("Send message (Enter)")
        send_btn.setFixedSize(40, 40)
        # Try multiple icon sources for better color support
        icon = None
        try:
            # Try Qt standard icons first (more colorful)
            from PySide6.QtWidgets import QStyle
            style = send_btn.style()
            icon = style.standardIcon(QStyle.StandardPixmap.SP_ArrowForward)
            if icon.isNull():
                # Fallback to theme icons
                icon = QIcon.fromTheme("mail-send")
                if icon.isNull():
                    icon = QIcon.fromTheme("document-send")
                if icon.isNull():
                    icon = QIcon.fromTheme("go-next")
        except Exception:
            pass
        
        if icon and not icon.isNull():
            send_btn.setIcon(icon)
            send_btn.setText("")  # Remove text if icon works
            send_btn.setIconSize(QSize(20, 20))
        
        # Set stylesheet
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                padding: 8px;
                font-size: 18px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
        """)
        send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(send_btn)
        
        main_layout.addLayout(input_layout)
        
        # Toolbar with feature buttons (copy, paste, file upload, voice, image)
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 4, 0, 0)
        toolbar_layout.setSpacing(3)
        
        # Neutral, compact button style - more visible
        button_style = """
            QPushButton {
                background-color: #e8e8e8;
                color: #333;
                border: 1px solid #bbb;
                border-radius: 4px;
                padding: 3px;
                min-width: 24px;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
                border-color: #999;
            }
            QPushButton:pressed {
                background-color: #bbb;
            }
        """
        
        # Copy button
        copy_btn = QPushButton()
        copy_btn.setToolTip("Copy")
        copy_btn.setFixedSize(24, 24)
        copy_icon = None
        try:
            from PySide6.QtWidgets import QStyle
            style = copy_btn.style()
            copy_icon = style.standardIcon(QStyle.StandardPixmap.SP_DialogCopyButton)
            if copy_icon.isNull():
                copy_icon = QIcon.fromTheme("edit-copy")
        except Exception:
            pass
        if copy_icon and not copy_icon.isNull():
            copy_btn.setIcon(copy_icon)
            copy_btn.setIconSize(QSize(12, 12))
        else:
            copy_btn.setText("📋")
            copy_btn.setStyleSheet(button_style + "font-size: 10px;")
        if copy_icon and not copy_icon.isNull():
            copy_btn.setStyleSheet(button_style)
        copy_btn.clicked.connect(self._copy_text)
        toolbar_layout.addWidget(copy_btn)
        
        # Paste button
        paste_btn = QPushButton()
        paste_btn.setToolTip("Paste")
        paste_btn.setFixedSize(24, 24)
        paste_icon = None
        try:
            from PySide6.QtWidgets import QStyle
            style = paste_btn.style()
            paste_icon = style.standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
            if paste_icon.isNull():
                paste_icon = QIcon.fromTheme("edit-paste")
        except Exception:
            pass
        if paste_icon and not paste_icon.isNull():
            paste_btn.setIcon(paste_icon)
            paste_btn.setIconSize(QSize(12, 12))
        else:
            paste_btn.setText("📄")
            paste_btn.setStyleSheet(button_style + "font-size: 10px;")
        if paste_icon and not paste_icon.isNull():
            paste_btn.setStyleSheet(button_style)
        paste_btn.clicked.connect(self._paste_text)
        toolbar_layout.addWidget(paste_btn)
        
        # File upload button
        upload_btn = QPushButton()
        upload_btn.setToolTip("Upload File")
        upload_btn.setFixedSize(24, 24)
        upload_icon = None
        try:
            from PySide6.QtWidgets import QStyle
            style = upload_btn.style()
            upload_icon = style.standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder)
            if upload_icon.isNull():
                upload_icon = QIcon.fromTheme("document-open")
        except Exception:
            pass
        if upload_icon and not upload_icon.isNull():
            upload_btn.setIcon(upload_icon)
            upload_btn.setIconSize(QSize(12, 12))
        else:
            upload_btn.setText("📁")
            upload_btn.setStyleSheet(button_style + "font-size: 10px;")
        if upload_icon and not upload_icon.isNull():
            upload_btn.setStyleSheet(button_style)
        upload_btn.clicked.connect(self._upload_file)
        toolbar_layout.addWidget(upload_btn)
        
        # Image upload button
        image_btn = QPushButton()
        image_btn.setToolTip("Insert Image")
        image_btn.setFixedSize(24, 24)
        image_icon = None
        try:
            from PySide6.QtWidgets import QStyle
            style = image_btn.style()
            image_icon = style.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
            if image_icon.isNull():
                image_icon = QIcon.fromTheme("image-x-generic")
        except Exception:
            pass
        if image_icon and not image_icon.isNull():
            image_btn.setIcon(image_icon)
            image_btn.setIconSize(QSize(12, 12))
        else:
            image_btn.setText("🖼️")
            image_btn.setStyleSheet(button_style + "font-size: 10px;")
        if image_icon and not image_icon.isNull():
            image_btn.setStyleSheet(button_style)
        image_btn.clicked.connect(self._insert_image)
        toolbar_layout.addWidget(image_btn)
        
        # Voice button
        self.voice_btn = QPushButton()
        self.voice_btn.setToolTip("Voice Input")
        self.voice_btn.setFixedSize(24, 24)
        self.voice_recording = False
        voice_icon = None
        try:
            from PySide6.QtWidgets import QStyle
            style = self.voice_btn.style()
            voice_icon = style.standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
            if voice_icon.isNull():
                voice_icon = QIcon.fromTheme("audio-input-microphone")
        except Exception:
            pass
        if voice_icon and not voice_icon.isNull():
            self.voice_btn.setIcon(voice_icon)
            self.voice_btn.setIconSize(QSize(12, 12))
        else:
            self.voice_btn.setText("🎤")
            self.voice_btn.setStyleSheet(button_style + "font-size: 10px;")
        if voice_icon and not voice_icon.isNull():
            self.voice_btn.setStyleSheet(button_style)
        self.voice_btn.clicked.connect(self._toggle_voice)
        toolbar_layout.addWidget(self.voice_btn)
        
        toolbar_layout.addStretch()
        main_layout.addLayout(toolbar_layout)
        
        # Status - minimal, at bottom
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888; font-size: 11px; padding: 2px 0px;")
        self.status_label.setFixedHeight(16)
        main_layout.addWidget(self.status_label)
        
        # Allow horizontal expansion to match other panels
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumHeight(350)
        self.setMaximumHeight(400)
    
    def _show_welcome_message(self) -> None:
        """Show welcome message from Q - Cursor style."""
        welcome = self._format_message("Q", "Hello! I'm Q, your AI advisor. I can help with software features, troubleshooting, and best practices. What would you like to know?", is_user=False)
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
                        self.suggestions_list.setFixedHeight(min(80, self.suggestions_list.count() * 28))
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
                        self.suggestions_list.setFixedHeight(min(80, self.suggestions_list.count() * 28))
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
        
        # Validate and sanitize input
        try:
            from core.input_validator import InputValidator
            is_valid, error_msg = InputValidator.validate_chat_input(question)
            if not is_valid:
                QMessageBox.warning(self, "Invalid Input", error_msg or "Invalid input detected")
                return
            # Sanitize the input
            question = InputValidator.sanitize_text(question, max_length=5000, allow_html=False)
        except ImportError:
            # Input validator not available, use basic validation
            if len(question) > 5000:
                QMessageBox.warning(self, "Input Too Long", "Input exceeds maximum length of 5000 characters")
                return
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Input validation failed: {e}")
            # Continue with unsanitized input if validation fails (graceful degradation)
        
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
        self.status_label.setText("Thinking...")
        self.status_label.setStyleSheet("color: #007acc; font-size: 11px;")
        
        # Get response (with slight delay for better UX)
        QTimer.singleShot(100, lambda: self._get_response(question))
    
    def _get_response(self, question: str) -> None:
        """Get response from Q."""
        if not self.advisor:
            error_msg = "Sorry, AI advisor is not available. Please check the logs for initialization errors."
            self._add_message("Q", error_msg, is_user=False)
            self.status_label.setText("Unavailable")
            self.status_label.setStyleSheet("color: #d32f2f; font-size: 11px;")
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
                    self.suggestions_list.setFixedHeight(min(80, self.suggestions_list.count() * 28))
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
            self.status_label.setText("")
            self.status_label.setStyleSheet("color: #888; font-size: 11px;")
            
        except Exception as e:
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"Error in AI advisor response: {e}", exc_info=True)
            
            error_msg = f"Sorry, I encountered an error: {str(e)}\n\nPlease check the logs for more details."
            self._add_message("Q", error_msg, is_user=False)
            self.status_label.setText("Error")
            self.status_label.setStyleSheet("color: #d32f2f; font-size: 11px;")
    
    def _add_message(self, sender: str, message: str, is_user: bool = False) -> None:
        """Add message to chat display - Cursor style with message bubbles."""
        html = self._format_message(sender, message, is_user)
        self.chat_display.append(html)
        
        # Scroll to bottom
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _format_message(self, sender: str, message: str, is_user: bool = False) -> str:
        """Format message in Cursor style - message bubbles with better styling."""
        escaped_message = self._escape_html(message)
        if is_user:
            # User message - right aligned, blue background bubble
            return f"""
            <div style="margin: 10px 0px; text-align: right; padding-right: 8px;">
                <div style="display: inline-block; max-width: 75%; background-color: #007acc; color: white; padding: 10px 14px; border-radius: 18px 18px 4px 18px; text-align: left; word-wrap: break-word; box-shadow: 0 1px 2px rgba(0,0,0,0.1);">
                    <span style="white-space: pre-wrap; font-size: 13px; line-height: 1.4;">{escaped_message}</span>
                </div>
            </div>
            """
        else:
            # AI message - left aligned, light gray background bubble with sender label
            return f"""
            <div style="margin: 10px 0px; padding-left: 8px;">
                <div style="font-weight: 600; color: #666; margin-bottom: 6px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">{sender}</div>
                <div style="display: inline-block; max-width: 80%; background-color: #f5f5f5; color: #1a1a1a; padding: 10px 14px; border-radius: 18px 18px 18px 4px; word-wrap: break-word; box-shadow: 0 1px 2px rgba(0,0,0,0.05); border: 1px solid #e8e8e8;">
                    <span style="white-space: pre-wrap; font-size: 13px; line-height: 1.5;">{escaped_message}</span>
                </div>
            </div>
            """
    
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
    
    def _get_toolbar_button_style(self) -> str:
        """Get style for toolbar buttons."""
        return """
            QPushButton {
                background-color: #ecf0f1;
                color: #2c3e50;
                padding: 3px 8px;
                font-size: 9px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
            }
            QPushButton:pressed {
                background-color: #bdc3c7;
            }
        """
    
    def _cut_text(self) -> None:
        """Cut selected text."""
        if self.input_field.hasFocus():
            self.input_field.cut()
        # Chat display is read-only, so cut doesn't apply
    
    def _copy_text(self) -> None:
        """Copy selected text."""
        if self.chat_display.hasFocus():
            self.chat_display.copy()
        elif self.input_field.hasFocus():
            self.input_field.copy()
        else:
            # Copy from chat display by default
            self.chat_display.copy()
    
    def _paste_text(self) -> None:
        """Paste text."""
        if self.input_field.hasFocus():
            self.input_field.paste()
        else:
            # Focus input field and paste
            self.input_field.setFocus()
            self.input_field.paste()
    
    def _show_context_menu(self, position) -> None:
        """Show context menu for text operations."""
        menu = QMenu(self)
        
        # Only show cut if input field has focus
        if self.input_field.hasFocus():
            cut_action = QAction("Cut", self)
            cut_action.setShortcut(QKeySequence.StandardKey.Cut)
            cut_action.triggered.connect(self._cut_text)
            menu.addAction(cut_action)
        
        copy_action = QAction("Copy", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_icon = None
        try:
            from PySide6.QtWidgets import QStyle
            style = self.style()
            copy_icon = style.standardIcon(QStyle.StandardPixmap.SP_DialogCopyButton)
            if copy_icon.isNull():
                copy_icon = QIcon.fromTheme("edit-copy")
        except Exception:
            pass
        if copy_icon and not copy_icon.isNull():
            copy_action.setIcon(copy_icon)
        copy_action.triggered.connect(self._copy_text)
        menu.addAction(copy_action)
        
        paste_action = QAction("Paste", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_icon = None
        try:
            from PySide6.QtWidgets import QStyle
            style = self.style()
            paste_icon = style.standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
            if paste_icon.isNull():
                paste_icon = QIcon.fromTheme("edit-paste")
        except Exception:
            pass
        if paste_icon and not paste_icon.isNull():
            paste_action.setIcon(paste_icon)
        paste_action.triggered.connect(self._paste_text)
        menu.addAction(paste_action)
        
        menu.addSeparator()
        
        select_all_action = QAction("Select All", self)
        select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        select_all_action.triggered.connect(self._select_all)
        menu.addAction(select_all_action)
        
        menu.exec(self.chat_display.mapToGlobal(position))
    
    def _select_all(self) -> None:
        """Select all text."""
        if self.chat_display.hasFocus():
            self.chat_display.selectAll()
        elif self.input_field.hasFocus():
            self.input_field.selectAll()
    
    def _insert_image(self) -> None:
        """Insert image into chat."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            str(Path.home()),
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp *.svg);;All Files (*)"
        )
        
        if file_path:
            try:
                # Read image
                pixmap = QPixmap(file_path)
                if pixmap.isNull():
                    QMessageBox.warning(self, "Error", "Could not load image file.")
                    return
                
                # Resize if too large
                if pixmap.width() > 800 or pixmap.height() > 600:
                    pixmap = pixmap.scaled(800, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                
                # Insert into chat
                cursor = self.chat_display.textCursor()
                cursor.insertHtml(f'<img src="{file_path}" width="{pixmap.width()}" height="{pixmap.height()}" /><br>')
                self.chat_display.setTextCursor(cursor)
                
                # Also add as message
                self._add_message("You", f"[Image: {Path(file_path).name}]", is_user=True)
                
                # Ask AI about the image if advisor supports it
                if self.advisor and hasattr(self.advisor, 'analyze_image'):
                    try:
                        response = self.advisor.analyze_image(file_path)
                        self._add_message("Q", response, is_user=False)
                    except Exception as e:
                        logging.getLogger(__name__).debug(f"Image analysis not supported: {e}")
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to insert image: {str(e)}")
                logging.getLogger(__name__).error(f"Error inserting image: {e}")
    
    def _toggle_voice(self) -> None:
        """Toggle voice input."""
        if not self.voice_recording:
            self._start_voice_input()
        else:
            self._stop_voice_input()
    
    def _start_voice_input(self) -> None:
        """Start voice input."""
        try:
            import speech_recognition as sr
            
            self.voice_recording = True
            self.voice_btn.setText("⏹️ Stop")
            self.voice_btn.setStyleSheet(self._get_toolbar_button_style().replace("#ecf0f1", "#e74c3c").replace("#2c3e50", "white"))
            self.status_label.setText("Listening...")
            self.status_label.setStyleSheet("color: #f39c12; font-size: 9px;")
            
            # Start recognition in background
            QTimer.singleShot(100, self._process_voice_input)
            
        except ImportError:
            QMessageBox.information(
                self,
                "Voice Input",
                "Voice input requires 'speech_recognition' library.\n\n"
                "Install with: pip install SpeechRecognition\n"
                "Also install PyAudio for microphone support."
            )
            self.voice_recording = False
            self.voice_btn.setText("🎤 Voice")
        except Exception as e:
            logging.getLogger(__name__).error(f"Error starting voice input: {e}")
            QMessageBox.warning(self, "Error", f"Failed to start voice input: {str(e)}")
            self.voice_recording = False
            self.voice_btn.setText("🎤 Voice")
    
    def _process_voice_input(self) -> None:
        """Process voice input."""
        try:
            import speech_recognition as sr
            
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            # Recognize speech
            try:
                text = recognizer.recognize_google(audio)
                self.input_field.setText(text)
                self._add_message("You", f"[Voice: {text}]", is_user=True)
                # Auto-send if text is recognized
                QTimer.singleShot(500, lambda: self._send_message())
            except sr.UnknownValueError:
                self.status_label.setText("Could not understand audio")
                self.status_label.setStyleSheet("color: #e74c3c; font-size: 9px;")
                QTimer.singleShot(2000, lambda: self.status_label.setText("Ready"))
            except sr.RequestError as e:
                self.status_label.setText(f"Voice recognition error: {e}")
                self.status_label.setStyleSheet("color: #e74c3c; font-size: 9px;")
                QTimer.singleShot(2000, lambda: self.status_label.setText("Ready"))
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error processing voice: {e}")
            self.status_label.setText(f"Voice error: {str(e)}")
            self.status_label.setStyleSheet("color: #e74c3c; font-size: 9px;")
        
        finally:
            self.voice_recording = False
            self.voice_btn.setText("🎤 Voice")
            self.voice_btn.setStyleSheet(self._get_toolbar_button_style())
            if self.status_label.text() == "Listening...":
                self.status_label.setText("Ready")
                self.status_label.setStyleSheet("color: #27ae60; font-size: 9px;")
    
    def _stop_voice_input(self) -> None:
        """Stop voice input."""
        self.voice_recording = False
        self.voice_btn.setText("🎤 Voice")
        self.voice_btn.setStyleSheet(self._get_toolbar_button_style())
        self.status_label.setText("Ready")
        self.status_label.setStyleSheet("color: #27ae60; font-size: 9px;")
    
    def _upload_file(self) -> None:
        """Upload file and process it."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Upload File",
            str(Path.home()),
            "All Files (*);;Text Files (*.txt);;PDF Files (*.pdf);;Image Files (*.png *.jpg *.jpeg);;Data Files (*.csv *.json *.log)"
        )
        
        if file_path:
            try:
                file_name = Path(file_path).name
                file_size = Path(file_path).stat().st_size
                
                # Add file info to chat
                self._add_message("You", f"[Uploaded: {file_name} ({file_size} bytes)]", is_user=True)
                
                # Process file based on type
                ext = Path(file_path).suffix.lower()
                
                if ext in ['.txt', '.log', '.csv']:
                    # Read text file
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()[:1000]  # First 1000 chars
                    self._add_message("Q", f"File content preview:\n{content}...", is_user=False)
                    
                    # Ask AI to analyze if advisor supports it
                    if self.advisor:
                        question = f"Please analyze this file: {file_name}"
                        QTimer.singleShot(500, lambda: self._get_response(question))
                
                elif ext in ['.png', '.jpg', '.jpeg', '.gif']:
                    # Handle as image
                    self._insert_image_from_path(file_path)
                
                elif ext == '.pdf':
                    self._add_message("Q", f"PDF file uploaded. I can help analyze it if you ask specific questions about it.", is_user=False)
                
                else:
                    self._add_message("Q", f"File uploaded. How can I help you with {file_name}?", is_user=False)
                
                self.status_label.setText(f"File uploaded: {file_name}")
                QTimer.singleShot(3000, lambda: self.status_label.setText("Ready"))
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to upload file: {str(e)}")
                logging.getLogger(__name__).error(f"Error uploading file: {e}")
    
    def _insert_image_from_path(self, file_path: str) -> None:
        """Insert image from file path."""
        try:
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                return
            
            if pixmap.width() > 800 or pixmap.height() > 600:
                pixmap = pixmap.scaled(800, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            cursor = self.chat_display.textCursor()
            cursor.insertHtml(f'<img src="{file_path}" width="{pixmap.width()}" height="{pixmap.height()}" /><br>')
            self.chat_display.setTextCursor(cursor)
        except Exception as e:
            logging.getLogger(__name__).error(f"Error inserting image: {e}")
    
    def _show_search(self) -> None:
        """Show/hide search bar."""
        if self.search_bar.isVisible():
            self.search_bar.hide()
            self.search_bar.clear()
        else:
            self.search_bar.show()
            self.search_bar.setFocus()
    
    def _search_in_chat(self, text: str) -> None:
        """Search for text in chat."""
        if not text:
            # Clear highlighting
            self.chat_display.setExtraSelections([])
            return
        
        # Find text in chat
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        self.chat_display.setTextCursor(cursor)
        
        extra_selections = []
        search_text = text
        while self.chat_display.find(search_text):
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor("#fff9c4"))
            selection.cursor = self.chat_display.textCursor()
            extra_selections.append(selection)
        
        self.chat_display.setExtraSelections(extra_selections)
    
    def _search_next(self) -> None:
        """Move to next search result."""
        if not self.search_bar.text():
            return
        
        if not self.chat_display.find(self.search_bar.text()):
            # Wrap around
            cursor = self.chat_display.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self.chat_display.setTextCursor(cursor)
            self.chat_display.find(self.search_bar.text())

