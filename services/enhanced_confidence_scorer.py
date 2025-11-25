"""
Enhanced Confidence Scorer

Improved confidence scoring with multiple factors and uncertainty handling.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple, Any

LOGGER = logging.getLogger(__name__)

from services.ai_advisor_q_enhanced import KnowledgeEntry, IntentType


class EnhancedConfidenceScorer:
    """
    Enhanced confidence scoring system.
    
    Considers multiple factors:
    - Knowledge base match quality
    - Intent classification confidence
    - Telemetry data availability
    - Historical success rate
    - Question clarity
    - Context relevance
    """
    
    def __init__(self):
        """Initialize confidence scorer."""
        self.historical_success: Dict[str, float] = {}  # question_pattern -> success_rate
    
    def calculate_confidence(
        self,
        intent_confidence: float,
        knowledge_matches: List[Tuple[KnowledgeEntry, float]],
        telemetry_available: bool,
        telemetry_relevant: bool,
        question_clarity: float,
        context_relevance: float,
        historical_success_rate: Optional[float] = None
    ) -> Tuple[float, str]:
        """
        Calculate overall confidence score.
        
        Args:
            intent_confidence: Intent classification confidence (0-1)
            knowledge_matches: Knowledge base matches with scores
            telemetry_available: Whether telemetry is available
            telemetry_relevant: Whether telemetry is relevant to question
            question_clarity: Question clarity score (0-1)
            context_relevance: Context relevance score (0-1)
            historical_success_rate: Historical success rate for similar questions
        
        Returns:
            Tuple of (confidence_score, confidence_level)
        """
        # Base confidence from knowledge match
        if knowledge_matches:
            best_match_score = knowledge_matches[0][1]
            knowledge_confidence = min(1.0, best_match_score)
        else:
            knowledge_confidence = 0.3  # Low if no matches
        
        # Weighted combination
        weights = {
            "intent": 0.15,
            "knowledge": 0.40,
            "telemetry": 0.10,
            "clarity": 0.15,
            "context": 0.10,
            "history": 0.10,
        }
        
        # Intent confidence
        intent_score = intent_confidence * weights["intent"]
        
        # Knowledge confidence
        knowledge_score = knowledge_confidence * weights["knowledge"]
        
        # Telemetry boost (if available and relevant)
        telemetry_score = 0.0
        if telemetry_available and telemetry_relevant:
            telemetry_score = 0.1 * weights["telemetry"]
        
        # Question clarity
        clarity_score = question_clarity * weights["clarity"]
        
        # Context relevance
        context_score = context_relevance * weights["context"]
        
        # Historical success
        history_score = 0.0
        if historical_success_rate is not None:
            history_score = historical_success_rate * weights["history"]
        
        # Total confidence
        total_confidence = (
            intent_score +
            knowledge_score +
            telemetry_score +
            clarity_score +
            context_score +
            history_score
        )
        
        # Normalize to 0-1 range
        total_confidence = min(1.0, max(0.0, total_confidence))
        
        # Determine confidence level
        if total_confidence >= 0.8:
            level = "high"
        elif total_confidence >= 0.6:
            level = "medium"
        elif total_confidence >= 0.4:
            level = "low"
        else:
            level = "very_low"
        
        return total_confidence, level
    
    def format_response_with_confidence(
        self,
        answer: str,
        confidence: float,
        confidence_level: str,
        sources: Optional[List[str]] = None
    ) -> str:
        """
        Format response with confidence indicator.
        
        Args:
            answer: Answer text
            confidence: Confidence score (0-1)
            confidence_level: Confidence level string
            sources: List of knowledge sources used
        
        Returns:
            Formatted response with confidence indicator
        """
        # Confidence indicator
        if confidence_level == "very_low":
            indicator = "[⚠️ Low Confidence]"
            note = "This answer may not be accurate. Please verify with other sources."
        elif confidence_level == "low":
            indicator = "[⚠️ Moderate Confidence]"
            note = "Please verify this information."
        elif confidence_level == "medium":
            indicator = "[✓ Good Confidence]"
            note = None
        else:  # high
            indicator = "[✓✓ High Confidence]"
            note = None
        
        # Build response
        response_parts = [answer]
        
        if indicator:
            response_parts.append(f"\n\n{indicator}")
        
        if note:
            response_parts.append(f"\n{note}")
        
        if sources:
            response_parts.append(f"\n\nSources: {', '.join(sources[:3])}")
        
        return "\n".join(response_parts)
    
    def calculate_question_clarity(self, question: str) -> float:
        """
        Calculate question clarity score.
        
        Args:
            question: User question
        
        Returns:
            Clarity score (0-1)
        """
        # Simple heuristics
        clarity = 0.5  # Base
        
        # Longer questions are usually clearer
        if len(question.split()) > 5:
            clarity += 0.2
        
        # Questions with specific terms are clearer
        specific_terms = ["how", "what", "why", "when", "where", "which"]
        if any(term in question.lower() for term in specific_terms):
            clarity += 0.2
        
        # Questions with numbers/values are clearer
        import re
        if re.search(r'\d+', question):
            clarity += 0.1
        
        return min(1.0, clarity)
    
    def calculate_context_relevance(
        self,
        question: str,
        context: Dict[str, Any]
    ) -> float:
        """
        Calculate how relevant context is to question.
        
        Args:
            question: User question
            context: Conversation context
        
        Returns:
            Relevance score (0-1)
        """
        relevance = 0.3  # Base
        
        # Check if question relates to active topics
        active_topics = context.get("active_topics", [])
        question_lower = question.lower()
        
        topic_keywords = {
            "fuel": ["fuel", "afr", "lambda"],
            "timing": ["timing", "spark", "ignition"],
            "boost": ["boost", "turbo", "wastegate"],
        }
        
        for topic in active_topics:
            if topic in topic_keywords:
                keywords = topic_keywords[topic]
                if any(kw in question_lower for kw in keywords):
                    relevance += 0.3
        
        # Check if vehicle context is relevant
        if context.get("current_vehicle_id"):
            if "vehicle" in question_lower or "car" in question_lower:
                relevance += 0.2
        
        # Check if current tab is relevant
        current_tab = context.get("current_tab", "")
        if current_tab and current_tab.lower() in question_lower:
            relevance += 0.2
        
        return min(1.0, relevance)
    
    def record_feedback(
        self,
        question_pattern: str,
        helpful: bool
    ) -> None:
        """
        Record user feedback for learning.
        
        Args:
            question_pattern: Question pattern/keywords
            helpful: Whether answer was helpful
        """
        if question_pattern not in self.historical_success:
            self.historical_success[question_pattern] = 0.5  # Start neutral
        
        current_rate = self.historical_success[question_pattern]
        
        # Update with exponential moving average
        alpha = 0.1  # Learning rate
        new_rate = alpha * (1.0 if helpful else 0.0) + (1 - alpha) * current_rate
        
        self.historical_success[question_pattern] = new_rate
    
    def get_historical_success_rate(self, question: str) -> Optional[float]:
        """
        Get historical success rate for similar questions.
        
        Args:
            question: User question
        
        Returns:
            Success rate (0-1) or None
        """
        # Simple pattern matching (could be enhanced)
        question_lower = question.lower()
        
        # Check for matching patterns
        for pattern, rate in self.historical_success.items():
            if pattern in question_lower:
                return rate
        
        return None


__all__ = ["EnhancedConfidenceScorer"]









