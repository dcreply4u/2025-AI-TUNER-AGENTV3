"""
Conversational Response Manager
Provides natural, varied, and context-aware responses for the AI advisor.
"""

from __future__ import annotations

import json
import logging
import random
import time
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

LOGGER = logging.getLogger(__name__)

# Try to import NLTK for better text processing (optional)
try:
    import nltk
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
    # Download required NLTK data (only once)
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        try:
            nltk.download('punkt', quiet=True)
        except Exception:
            pass
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        try:
            nltk.download('stopwords', quiet=True)
        except Exception:
            pass
except ImportError:
    NLTK_AVAILABLE = False
    word_tokenize = None  # type: ignore
    stopwords = None  # type: ignore

class ConversationMood(Enum):
    """Conversation mood/tone."""
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    TECHNICAL = "technical"
    ENCOURAGING = "encouraging"
    CAUTIOUS = "cautious"


@dataclass
class ConversationContext:
    """Tracks conversation context."""
    first_interaction: bool = True
    last_topic: Optional[str] = None
    interaction_count: int = 0
    user_name: Optional[str] = None
    preferred_detail_level: str = "normal"  # simple, normal, detailed
    last_interaction_time: float = field(default_factory=time.time)
    topics_discussed: List[str] = field(default_factory=list)
    mood: ConversationMood = ConversationMood.FRIENDLY


class ConversationalResponseManager:
    """
    Manages natural, varied conversational responses.
    
    Features:
    - Multiple response variations for each intent
    - Context-aware responses
    - Personality and tone variation
    - Conversation memory
    - Natural language patterns
    """
    
    def __init__(self):
        self.context = ConversationContext()
        self.dataset: Optional[Dict] = None
        self._load_dataset()
        self._initialize_response_pools()
    
    def _load_dataset(self):
        """Load conversation dataset from JSON file."""
        try:
            dataset_path = Path(__file__).parent / "conversation_dataset.json"
            if dataset_path.exists():
                with open(dataset_path, 'r', encoding='utf-8') as f:
                    self.dataset = json.load(f)
                LOGGER.info("Loaded conversation dataset")
            else:
                LOGGER.warning("Conversation dataset not found at %s", dataset_path)
                self.dataset = None
        except Exception as e:
            LOGGER.warning("Failed to load conversation dataset: %s", e)
            self.dataset = None
    
    def _initialize_response_pools(self):
        """Initialize pools of varied responses."""
        
        # Load from dataset if available, otherwise use defaults
        if self.dataset and "greetings" in self.dataset:
            self.greeting_responses = self.dataset["greetings"].get("responses", [])
        else:
            # Default greeting responses - varied and natural
            self.greeting_responses = [
            "Hey there! 👋 I'm Q, your AI tuning assistant. What can I help you with today?",
            "Hello! I'm Q, ready to help with your tuning questions. What's on your mind?",
            "Hi! 👋 Q here. Whether it's tuning advice, troubleshooting, or just questions about your setup, I've got you covered. What do you need?",
            "Hey! I'm Q, your TelemetryIQ assistant. Ready to dive into some tuning? What would you like to know?",
            "Hi there! 👋 Q at your service. I can help with tuning, ECU setup, troubleshooting, and more. What can I do for you?",
            "Hello! I'm Q. Think of me as your co-pilot for tuning and ECU work. What are you working on?",
            "Hey! 👋 Q here. I'm here to help make your tuning journey smoother. What questions do you have?",
            "Hi! I'm Q, your AI tuning advisor. Whether you're just starting or fine-tuning, I'm here to help. What's up?",
            ]
        
        # Load other responses from dataset if available
        if self.dataset:
            if "response_variations" in self.dataset:
                variations = self.dataset["response_variations"]
                if "acknowledgments" in variations:
                    self.acknowledgments = variations["acknowledgments"]
                if "transitions" in variations:
                    self.transitions = variations["transitions"]
                if "encouragements" in variations:
                    self.encouragements = variations["encouragements"]
        
        # Follow-up greetings (when user returns)
        self.returning_greetings = [
            "Welcome back! 👋 What can I help you with today?",
            "Hey again! What are we working on?",
            "Good to see you back! What's the question?",
            "Back for more? Let's dive in - what do you need?",
            "Hey! Ready to continue? What's on your mind?",
        ]
        
        # If dataset didn't provide these, use defaults
        if not hasattr(self, 'acknowledgments') or not self.acknowledgments:
            self.acknowledgments = [
                "Got it!",
                "Sure thing!",
                "Absolutely!",
                "No problem!",
                "I can help with that.",
                "Let me help you with that.",
                "I understand.",
                "Right, let's get into it.",
            ]
        
        if not hasattr(self, 'transitions') or not self.transitions:
            self.transitions = [
                "Here's what I found:",
                "Let me break that down:",
                "Here's the deal:",
                "So here's the thing:",
                "Let me explain:",
                "Here's what you need to know:",
                "The short answer is:",
            ]
        
        if not hasattr(self, 'encouragements') or not self.encouragements:
            self.encouragements = [
                "Feel free to ask if you need anything else!",
                "Let me know if you have more questions!",
                "Happy to help with anything else!",
                "Anything else you'd like to know?",
                "Don't hesitate to ask if you need more help!",
                "I'm here if you have more questions!",
            ]
        
        # When no answer found
        self.no_answer_responses = [
            "Hmm, I'm not entirely sure about that one. Let me search for more information.",
            "That's a good question. I don't have that in my knowledge base, but let me look it up for you.",
            "I'm not certain about that specific detail. Let me do some research.",
            "That's outside my immediate knowledge. Give me a moment to find the answer.",
        ]
        
        # Technical but friendly explanations
        self.technical_intros = [
            "Here's the technical breakdown:",
            "From a tuning perspective:",
            "In tuning terms:",
            "The way this works is:",
            "Here's how it breaks down:",
        ]
    
    def get_greeting(self, is_returning: bool = False, user_input: Optional[str] = None) -> str:
        """
        Get a natural greeting response.
        
        Args:
            is_returning: Whether this is a returning user
            user_input: The user's greeting input (for pattern matching)
        """
        # Check dataset for pattern matching
        if user_input and self.dataset and "common_questions" in self.dataset:
            user_lower = user_input.lower().strip()
            
            # Check "what can you do" patterns
            if "what_can_you_do" in self.dataset["common_questions"]:
                patterns = self.dataset["common_questions"]["what_can_you_do"].get("patterns", [])
                if any(pattern in user_lower for pattern in patterns):
                    responses = self.dataset["common_questions"]["what_can_you_do"].get("responses", [])
                    if responses:
                        return random.choice(responses)
            
            # Check "how are you" patterns
            if "how_are_you" in self.dataset["common_questions"]:
                patterns = self.dataset["common_questions"]["how_are_you"].get("patterns", [])
                if any(pattern in user_lower for pattern in patterns):
                    responses = self.dataset["common_questions"]["how_are_you"].get("responses", [])
                    if responses:
                        return random.choice(responses)
        
        # Standard greeting
        if is_returning and self.context.interaction_count > 1:
            return random.choice(self.returning_greetings)
        return random.choice(self.greeting_responses)
    
    def get_acknowledgment(self) -> str:
        """Get a natural acknowledgment."""
        return random.choice(self.acknowledgments)
    
    def get_transition(self) -> str:
        """Get a transition phrase."""
        return random.choice(self.transitions)
    
    def get_encouragement(self) -> str:
        """Get an encouragement/closing phrase."""
        return random.choice(self.encouragements)
    
    def format_response(
        self,
        main_content: str,
        intent: str = "unknown",
        include_acknowledgment: bool = False,
        include_encouragement: bool = True,
        use_transition: bool = False,
    ) -> str:
        """
        Format a response with natural conversational elements.
        
        Args:
            main_content: The main response content
            intent: The detected intent
            include_acknowledgment: Add acknowledgment at start
            include_encouragement: Add encouragement at end
            use_transition: Use transition phrase before content
        """
        parts = []
        
        if include_acknowledgment:
            parts.append(self.get_acknowledgment())
        
        if use_transition:
            parts.append(self.get_transition())
        
        parts.append(main_content)
        
        if include_encouragement and intent not in ["greeting", "unknown"]:
            parts.append("")
            parts.append(self.get_encouragement())
        
        return "\n".join(parts)
    
    def update_context(self, topic: Optional[str] = None, interaction_type: str = "question"):
        """Update conversation context."""
        self.context.interaction_count += 1
        self.context.first_interaction = False
        self.context.last_interaction_time = time.time()
        
        if topic:
            self.context.last_topic = topic
            if topic not in self.context.topics_discussed:
                self.context.topics_discussed.append(topic)
    
    def get_contextual_response(self, question: str, base_response: str, intent: str) -> str:
        """
        Enhance a base response with contextual, conversational elements.
        
        Args:
            question: The user's question
            base_response: The base technical response
            intent: The detected intent
        """
        # For greetings, use natural greeting
        if intent == "greeting":
            return self.get_greeting(is_returning=not self.context.first_interaction)
        
        # For first interaction after greeting, be welcoming
        if self.context.first_interaction and intent != "greeting":
            return self.format_response(
                base_response,
                intent=intent,
                include_acknowledgment=True,
                include_encouragement=True,
                use_transition=True,
            )
        
        # For follow-up questions on same topic
        if self.context.last_topic and any(word in question.lower() for word in self.context.last_topic.lower().split()):
            return self.format_response(
                base_response,
                intent=intent,
                include_acknowledgment=True,
                include_encouragement=True,
            )
        
        # Default: natural formatting
        return self.format_response(
            base_response,
            intent=intent,
            include_acknowledgment=random.choice([True, False]),  # Sometimes, not always
            include_encouragement=True,
            use_transition=len(base_response) > 200,  # Use transition for longer responses
        )
    
    def get_no_answer_response(self) -> str:
        """Get a response when no answer is found."""
        return random.choice(self.no_answer_responses)
    
    def get_technical_intro(self) -> str:
        """Get a technical introduction phrase."""
        return random.choice(self.technical_intros)


# Global instance
_conversation_manager: Optional[ConversationalResponseManager] = None


def get_conversation_manager() -> ConversationalResponseManager:
    """Get or create the global conversation manager."""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationalResponseManager()
    return _conversation_manager

