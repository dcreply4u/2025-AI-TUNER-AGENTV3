"""
Enhanced Conversation Memory

Improved conversation memory with better context tracking,
entity extraction, and long-term memory.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any

LOGGER = logging.getLogger(__name__)

from services.ai_advisor_q_enhanced import ChatMessage, IntentType


@dataclass
class ConversationContext:
    """Enhanced conversation context."""
    # Current conversation
    messages: deque = field(default_factory=lambda: deque(maxlen=50))  # Last 50 messages
    
    # Extracted entities
    entities: Dict[str, Any] = field(default_factory=dict)  # vehicle_id, current_tab, etc.
    
    # User profile
    user_profile: Dict[str, Any] = field(default_factory=dict)
    
    # Session information
    session_start: float = field(default_factory=time.time)
    current_vehicle_id: Optional[str] = None
    current_tab: Optional[str] = None
    
    # Long-term memory
    important_facts: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    # Conversation state
    active_topics: Set[str] = field(default_factory=set)
    pending_questions: List[str] = field(default_factory=list)


class EnhancedConversationMemory:
    """
    Enhanced conversation memory with better context tracking.
    
    Features:
    - Message history with sliding window
    - Entity extraction and tracking
    - Long-term memory for important facts
    - User preference learning
    - Context-aware responses
    """
    
    def __init__(self, max_history: int = 50):
        """
        Initialize conversation memory.
        
        Args:
            max_history: Maximum number of messages to remember
        """
        self.max_history = max_history
        self.context = ConversationContext()
        self.vehicle_contexts: Dict[str, ConversationContext] = {}
    
    def add_message(
        self,
        role: str,
        content: str,
        intent: Optional[IntentType] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add message to conversation history.
        
        Args:
            role: "user" or "assistant"
            content: Message content
            intent: Detected intent
            metadata: Additional metadata
        """
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=time.time(),
            intent=intent,
            confidence=1.0,
        )
        
        self.context.messages.append(message)
        
        # Extract entities from user messages
        if role == "user":
            self._extract_entities(content, metadata)
            self._update_active_topics(content, intent)
    
    def remember(self, key: str, value: Any, persistent: bool = False) -> None:
        """
        Store important information.
        
        Args:
            key: Information key
            value: Information value
            persistent: Whether to store in long-term memory
        """
        if persistent:
            self.context.important_facts[key] = value
        else:
            self.context.entities[key] = value
        
        # Also store in vehicle context if vehicle_id is known
        if self.context.current_vehicle_id:
            if self.context.current_vehicle_id not in self.vehicle_contexts:
                self.vehicle_contexts[self.context.current_vehicle_id] = ConversationContext()
            vehicle_context = self.vehicle_contexts[self.context.current_vehicle_id]
            if persistent:
                vehicle_context.important_facts[key] = value
            else:
                vehicle_context.entities[key] = value
    
    def recall(self, key: str, vehicle_id: Optional[str] = None) -> Optional[Any]:
        """
        Retrieve stored information.
        
        Args:
            key: Information key
            vehicle_id: Optional vehicle ID for vehicle-specific recall
        
        Returns:
            Stored value or None
        """
        # Check vehicle-specific context first
        if vehicle_id and vehicle_id in self.vehicle_contexts:
            vehicle_context = self.vehicle_contexts[vehicle_id]
            if key in vehicle_context.important_facts:
                return vehicle_context.important_facts[key]
            if key in vehicle_context.entities:
                return vehicle_context.entities[key]
        
        # Check general context
        if key in self.context.important_facts:
            return self.context.important_facts[key]
        if key in self.context.entities:
            return self.context.entities[key]
        
        return None
    
    def get_relevant_context(
        self,
        question: str,
        include_history: bool = True,
        max_history_messages: int = 5
    ) -> Dict[str, Any]:
        """
        Get relevant context for question.
        
        Args:
            question: Current question
            include_history: Whether to include message history
            max_history_messages: Maximum history messages to include
        
        Returns:
            Context dictionary
        """
        context = {
            "entities": dict(self.context.entities),
            "important_facts": dict(self.context.important_facts),
            "preferences": dict(self.context.preferences),
            "current_vehicle_id": self.context.current_vehicle_id,
            "current_tab": self.context.current_tab,
            "active_topics": list(self.context.active_topics),
        }
        
        if include_history:
            # Get recent messages
            recent_messages = list(self.context.messages)[-max_history_messages:]
            context["recent_messages"] = [
                {"role": msg.role, "content": msg.content, "intent": msg.intent.value if msg.intent else None}
                for msg in recent_messages
            ]
        
        # Add vehicle-specific context
        if self.context.current_vehicle_id and self.context.current_vehicle_id in self.vehicle_contexts:
            vehicle_context = self.vehicle_contexts[self.context.current_vehicle_id]
            context["vehicle_entities"] = dict(vehicle_context.entities)
            context["vehicle_facts"] = dict(vehicle_context.important_facts)
        
        return context
    
    def set_vehicle_context(self, vehicle_id: str) -> None:
        """
        Set current vehicle context.
        
        Args:
            vehicle_id: Vehicle identifier
        """
        self.context.current_vehicle_id = vehicle_id
        if vehicle_id not in self.vehicle_contexts:
            self.vehicle_contexts[vehicle_id] = ConversationContext()
            self.vehicle_contexts[vehicle_id].current_vehicle_id = vehicle_id
    
    def set_current_tab(self, tab_name: str) -> None:
        """
        Set current tab context.
        
        Args:
            tab_name: Current tab name
        """
        self.context.current_tab = tab_name
        self.remember("current_tab", tab_name)
    
    def update_preference(self, key: str, value: Any) -> None:
        """
        Update user preference.
        
        Args:
            key: Preference key
            value: Preference value
        """
        self.context.preferences[key] = value
    
    def _extract_entities(self, content: str, metadata: Optional[Dict[str, Any]]) -> None:
        """Extract entities from message content."""
        content_lower = content.lower()
        
        # Extract vehicle mentions
        vehicle_keywords = ["vehicle", "car", "truck", "engine", "motor"]
        if any(keyword in content_lower for keyword in vehicle_keywords):
            # Could extract vehicle ID or specs
            pass
        
        # Extract numeric values
        import re
        numbers = re.findall(r'\d+\.?\d*', content)
        if numbers:
            # Store relevant numbers (RPM, boost, etc.)
            pass
        
        # Extract from metadata
        if metadata:
            if "vehicle_id" in metadata:
                self.set_vehicle_context(metadata["vehicle_id"])
            if "current_tab" in metadata:
                self.set_current_tab(metadata["current_tab"])
    
    def _update_active_topics(self, content: str, intent: Optional[IntentType]) -> None:
        """Update active conversation topics."""
        content_lower = content.lower()
        
        # Topic keywords
        topics = {
            "fuel": ["fuel", "afr", "lambda", "ve table"],
            "timing": ["timing", "spark", "ignition", "knock"],
            "boost": ["boost", "turbo", "wastegate", "psi"],
            "nitrous": ["nitrous", "n2o", "bottle"],
            "methanol": ["methanol", "meth", "injection"],
            "troubleshooting": ["problem", "issue", "error", "not working"],
        }
        
        for topic, keywords in topics.items():
            if any(keyword in content_lower for keyword in keywords):
                self.context.active_topics.add(topic)


__all__ = [
    "EnhancedConversationMemory",
    "ConversationContext",
]
