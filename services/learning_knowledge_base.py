"""
Learning Knowledge Base

Learns from user interactions, successful tunings, and feedback
to improve responses over time.
"""

from __future__ import annotations

import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

LOGGER = logging.getLogger(__name__)

from services.ai_advisor_q_enhanced import KnowledgeEntry


@dataclass
class TuningSession:
    """Record of a tuning session."""
    session_id: str
    vehicle_id: str
    timestamp: float
    changes_made: Dict[str, any]
    results: Dict[str, float]  # Performance metrics
    success: bool
    user_feedback: Optional[str] = None


@dataclass
class InteractionRecord:
    """Record of user interaction with advisor."""
    question: str
    answer: str
    timestamp: float
    helpful: Optional[bool] = None
    vehicle_id: Optional[str] = None
    context: Dict[str, any] = field(default_factory=dict)


@dataclass
class LearnedPattern:
    """Pattern learned from interactions."""
    pattern_id: str
    condition: str  # When this pattern applies
    advice: str  # Advice to give
    success_rate: float  # How often this advice worked
    usage_count: int
    last_used: float


class LearningKnowledgeBase:
    """
    Learning knowledge base that improves from user interactions.
    
    Features:
    - Learns from successful tunings
    - Tracks user feedback
    - Builds vehicle-specific patterns
    - Improves recommendations over time
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize learning knowledge base.
        
        Args:
            storage_path: Path to store learned data
        """
        self.storage_path = storage_path or Path("data/learned_knowledge.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Learned data
        self.tuning_sessions: List[TuningSession] = []
        self.interactions: List[InteractionRecord] = []
        self.learned_patterns: Dict[str, LearnedPattern] = {}
        self.vehicle_patterns: Dict[str, Dict[str, any]] = defaultdict(dict)
        
        # Statistics
        self.successful_tunings: int = 0
        self.total_interactions: int = 0
        self.positive_feedback: int = 0
        
        # Load existing data
        self._load_learned_data()
    
    def learn_from_tuning(
        self,
        vehicle_id: str,
        changes_made: Dict[str, any],
        results: Dict[str, float],
        success: bool,
        user_feedback: Optional[str] = None
    ) -> None:
        """
        Learn from a tuning session.
        
        Args:
            vehicle_id: Vehicle identifier
            changes_made: What changes were made
            results: Performance results
            success: Whether tuning was successful
            user_feedback: Optional user feedback
        """
        session = TuningSession(
            session_id=f"session_{int(time.time())}",
            vehicle_id=vehicle_id,
            timestamp=time.time(),
            changes_made=changes_made,
            results=results,
            success=success,
            user_feedback=user_feedback,
        )
        
        self.tuning_sessions.append(session)
        
        if success:
            self.successful_tunings += 1
            self._extract_success_patterns(session)
        
        # Update vehicle-specific patterns
        self._update_vehicle_patterns(vehicle_id, session)
        
        # Save learned data
        self._save_learned_data()
        
        LOGGER.info("Learned from tuning session: %s (success: %s)", session.session_id, success)
    
    def learn_from_interaction(
        self,
        question: str,
        answer: str,
        helpful: Optional[bool] = None,
        vehicle_id: Optional[str] = None,
        context: Optional[Dict[str, any]] = None
    ) -> None:
        """
        Learn from user interaction.
        
        Args:
            question: User question
            answer: Given answer
            helpful: Whether answer was helpful (None = unknown)
            vehicle_id: Vehicle identifier
            context: Additional context
        """
        interaction = InteractionRecord(
            question=question,
            answer=answer,
            timestamp=time.time(),
            helpful=helpful,
            vehicle_id=vehicle_id,
            context=context or {},
        )
        
        self.interactions.append(interaction)
        self.total_interactions += 1
        
        if helpful is True:
            self.positive_feedback += 1
            self._reinforce_answer(question, answer)
        elif helpful is False:
            self._improve_answer(question, answer)
        
        # Keep only recent interactions (last 1000)
        if len(self.interactions) > 1000:
            self.interactions = self.interactions[-1000:]
        
        # Save learned data
        self._save_learned_data()
    
    def get_learned_advice(
        self,
        question: str,
        vehicle_id: Optional[str] = None,
        context: Optional[Dict[str, any]] = None
    ) -> Optional[Tuple[str, float]]:
        """
        Get learned advice for question.
        
        Args:
            question: User question
            vehicle_id: Vehicle identifier
            context: Additional context
        
        Returns:
            Tuple of (advice, confidence) or None
        """
        # Check vehicle-specific patterns first
        if vehicle_id and vehicle_id in self.vehicle_patterns:
            vehicle_patterns = self.vehicle_patterns[vehicle_id]
            # Simple pattern matching (can be enhanced)
            question_lower = question.lower()
            for pattern_key, pattern_data in vehicle_patterns.items():
                if pattern_key in question_lower:
                    advice = pattern_data.get("advice")
                    success_rate = pattern_data.get("success_rate", 0.5)
                    if advice and success_rate > 0.6:
                        return (advice, success_rate)
        
        # Check general learned patterns
        for pattern in self.learned_patterns.values():
            if pattern.condition.lower() in question.lower():
                if pattern.success_rate > 0.6 and pattern.usage_count > 3:
                    return (pattern.advice, pattern.success_rate)
        
        return None
    
    def _extract_success_patterns(self, session: TuningSession) -> None:
        """Extract patterns from successful tuning."""
        # Extract what worked
        for change_type, change_value in session.changes_made.items():
            pattern_id = f"{change_type}_{change_value}"
            
            if pattern_id not in self.learned_patterns:
                self.learned_patterns[pattern_id] = LearnedPattern(
                    pattern_id=pattern_id,
                    condition=change_type,
                    advice=f"Consider {change_type} = {change_value}",
                    success_rate=1.0,
                    usage_count=1,
                    last_used=time.time(),
                )
            else:
                # Update success rate
                pattern = self.learned_patterns[pattern_id]
                pattern.usage_count += 1
                pattern.success_rate = (
                    (pattern.success_rate * (pattern.usage_count - 1) + 1.0) / pattern.usage_count
                )
                pattern.last_used = time.time()
    
    def _update_vehicle_patterns(self, vehicle_id: str, session: TuningSession) -> None:
        """Update vehicle-specific patterns."""
        if session.success:
            # Store successful settings for this vehicle
            for change_type, change_value in session.changes_made.items():
                if change_type not in self.vehicle_patterns[vehicle_id]:
                    self.vehicle_patterns[vehicle_id][change_type] = {
                        "advice": f"For this vehicle, {change_type} = {change_value} worked well",
                        "success_rate": 1.0,
                        "count": 1,
                    }
                else:
                    pattern = self.vehicle_patterns[vehicle_id][change_type]
                    pattern["count"] += 1
                    pattern["success_rate"] = (
                        (pattern["success_rate"] * (pattern["count"] - 1) + 1.0) / pattern["count"]
                    )
    
    def _reinforce_answer(self, question: str, answer: str) -> None:
        """Reinforce successful answer."""
        # Could create pattern from successful Q&A pair
        question_key = question.lower()[:50]  # Use first 50 chars as key
        
        if question_key not in self.learned_patterns:
            self.learned_patterns[question_key] = LearnedPattern(
                pattern_id=question_key,
                condition=question,
                advice=answer,
                success_rate=1.0,
                usage_count=1,
                last_used=time.time(),
            )
        else:
            pattern = self.learned_patterns[question_key]
            pattern.usage_count += 1
            pattern.success_rate = (
                (pattern.success_rate * (pattern.usage_count - 1) + 1.0) / pattern.usage_count
            )
            pattern.last_used = time.time()
    
    def _improve_answer(self, question: str, answer: str) -> None:
        """Mark answer for improvement."""
        # Could flag for manual review or automatic improvement
        LOGGER.info("Answer marked as unhelpful, will improve: %s", question[:50])
    
    def get_statistics(self) -> Dict[str, any]:
        """Get learning statistics."""
        return {
            "total_tuning_sessions": len(self.tuning_sessions),
            "successful_tunings": self.successful_tunings,
            "success_rate": (
                self.successful_tunings / len(self.tuning_sessions)
                if self.tuning_sessions else 0.0
            ),
            "total_interactions": self.total_interactions,
            "positive_feedback": self.positive_feedback,
            "feedback_rate": (
                self.positive_feedback / self.total_interactions
                if self.total_interactions > 0 else 0.0
            ),
            "learned_patterns": len(self.learned_patterns),
            "vehicle_profiles": len(self.vehicle_patterns),
        }
    
    def _save_learned_data(self) -> None:
        """Save learned data to disk."""
        try:
            data = {
                "tuning_sessions": [asdict(s) for s in self.tuning_sessions[-100:]],  # Keep last 100
                "interactions": [asdict(i) for i in self.interactions[-500:]],  # Keep last 500
                "learned_patterns": {
                    k: asdict(v) for k, v in self.learned_patterns.items()
                },
                "vehicle_patterns": dict(self.vehicle_patterns),
                "statistics": {
                    "successful_tunings": self.successful_tunings,
                    "total_interactions": self.total_interactions,
                    "positive_feedback": self.positive_feedback,
                },
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            LOGGER.error("Failed to save learned data: %s", e)
    
    def _load_learned_data(self) -> None:
        """Load learned data from disk."""
        if not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            # Load tuning sessions
            self.tuning_sessions = [
                TuningSession(**s) for s in data.get("tuning_sessions", [])
            ]
            
            # Load interactions
            self.interactions = [
                InteractionRecord(**i) for i in data.get("interactions", [])
            ]
            
            # Load learned patterns
            self.learned_patterns = {
                k: LearnedPattern(**v)
                for k, v in data.get("learned_patterns", {}).items()
            }
            
            # Load vehicle patterns
            self.vehicle_patterns = defaultdict(dict, data.get("vehicle_patterns", {}))
            
            # Load statistics
            stats = data.get("statistics", {})
            self.successful_tunings = stats.get("successful_tunings", 0)
            self.total_interactions = stats.get("total_interactions", 0)
            self.positive_feedback = stats.get("positive_feedback", 0)
            
            LOGGER.info("Loaded learned data: %d sessions, %d interactions, %d patterns",
                       len(self.tuning_sessions), len(self.interactions), len(self.learned_patterns))
        except Exception as e:
            LOGGER.error("Failed to load learned data: %s", e)


__all__ = [
    "LearningKnowledgeBase",
    "TuningSession",
    "InteractionRecord",
    "LearnedPattern",
]









