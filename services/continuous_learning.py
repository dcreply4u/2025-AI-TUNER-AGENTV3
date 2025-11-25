"""
Continuous Learning System
Learns from user interactions and tuning sessions.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

LOGGER = logging.getLogger(__name__)


@dataclass
class LearningEvent:
    """A learning event from user interaction."""
    event_id: str
    event_type: str  # "question", "tune_success", "tune_failure", "feedback"
    timestamp: float
    context: Dict[str, Any] = field(default_factory=dict)
    outcome: Optional[str] = None
    user_feedback: Optional[str] = None


@dataclass
class LearnedPattern:
    """A pattern learned from interactions."""
    pattern_id: str
    pattern_type: str  # "successful_tune", "common_issue", "user_preference"
    description: str
    confidence: float
    occurrences: int
    last_seen: float
    associated_data: Dict[str, Any] = field(default_factory=dict)


class ContinuousLearning:
    """
    Continuous learning system that improves over time.
    
    Features:
    - Learn from successful/unsuccessful tuning sessions
    - Adapt recommendations based on user feedback
    - Identify patterns in user behavior
    - Improve accuracy over time
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize learning system.
        
        Args:
            data_dir: Directory to store learning data
        """
        if data_dir is None:
            data_dir = Path.home() / ".telemetryiq" / "learning"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.learning_events: List[LearningEvent] = []
        self.learned_patterns: Dict[str, LearnedPattern] = {}
        self._load_learning_data()
    
    def record_event(
        self,
        event_type: str,
        context: Dict[str, Any],
        outcome: Optional[str] = None,
        user_feedback: Optional[str] = None
    ) -> None:
        """
        Record a learning event.
        
        Args:
            event_type: Type of event
            context: Event context
            outcome: Event outcome
            user_feedback: User feedback if available
        """
        event = LearningEvent(
            event_id=f"event_{int(time.time() * 1000)}",
            event_type=event_type,
            timestamp=time.time(),
            context=context,
            outcome=outcome,
            user_feedback=user_feedback
        )
        
        self.learning_events.append(event)
        
        # Process event for patterns
        self._process_event_for_patterns(event)
        
        # Save learning data
        self._save_learning_data()
    
    def _process_event_for_patterns(self, event: LearningEvent) -> None:
        """Process event to identify patterns."""
        # Successful tune pattern
        if event.event_type == "tune_success":
            pattern_key = "successful_tune"
            if pattern_key not in self.learned_patterns:
                self.learned_patterns[pattern_key] = LearnedPattern(
                    pattern_id=pattern_key,
                    pattern_type="successful_tune",
                    description="Successful tuning approach",
                    confidence=0.5,
                    occurrences=1,
                    last_seen=event.timestamp,
                    associated_data=event.context
                )
            else:
                pattern = self.learned_patterns[pattern_key]
                pattern.occurrences += 1
                pattern.last_seen = event.timestamp
                pattern.confidence = min(1.0, 0.5 + (pattern.occurrences * 0.05))
                # Update with successful context
                pattern.associated_data.update(event.context)
        
        # Failed tune pattern
        elif event.event_type == "tune_failure":
            pattern_key = "failed_tune"
            if pattern_key not in self.learned_patterns:
                self.learned_patterns[pattern_key] = LearnedPattern(
                    pattern_id=pattern_key,
                    pattern_type="failed_tune",
                    description="Failed tuning approach",
                    confidence=0.5,
                    occurrences=1,
                    last_seen=event.timestamp,
                    associated_data=event.context
                )
            else:
                pattern = self.learned_patterns[pattern_key]
                pattern.occurrences += 1
                pattern.last_seen = event.timestamp
        
        # Common question pattern
        elif event.event_type == "question":
            question = event.context.get("question", "").lower()
            # Extract topic
            topics = ["fuel", "timing", "boost", "knock", "overheat"]
            for topic in topics:
                if topic in question:
                    pattern_key = f"common_question_{topic}"
                    if pattern_key not in self.learned_patterns:
                        self.learned_patterns[pattern_key] = LearnedPattern(
                            pattern_id=pattern_key,
                            pattern_type="common_issue",
                            description=f"Common questions about {topic}",
                            confidence=0.3,
                            occurrences=1,
                            last_seen=event.timestamp
                        )
                    else:
                        pattern = self.learned_patterns[pattern_key]
                        pattern.occurrences += 1
                        pattern.last_seen = event.timestamp
                        pattern.confidence = min(1.0, 0.3 + (pattern.occurrences * 0.1))
    
    def get_learned_recommendations(self, context: Dict[str, Any]) -> List[str]:
        """
        Get recommendations based on learned patterns.
        
        Args:
            context: Current context
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Check for successful patterns
        if "successful_tune" in self.learned_patterns:
            pattern = self.learned_patterns["successful_tune"]
            if pattern.confidence > 0.7:
                # Suggest similar approach
                recommendations.append(
                    f"Based on {pattern.occurrences} successful tunes, consider: {pattern.description}"
                )
        
        # Check for failed patterns to avoid
        if "failed_tune" in self.learned_patterns:
            pattern = self.learned_patterns["failed_tune"]
            if pattern.confidence > 0.6:
                recommendations.append(
                    f"Avoid: {pattern.description} (failed {pattern.occurrences} times)"
                )
        
        return recommendations
    
    def _load_learning_data(self) -> None:
        """Load learning data from disk."""
        data_file = self.data_dir / "learning_data.json"
        if not data_file.exists():
            return
        
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
                
                # Load events
                if "events" in data:
                    for event_data in data["events"]:
                        self.learning_events.append(LearningEvent(**event_data))
                
                # Load patterns
                if "patterns" in data:
                    for pattern_id, pattern_data in data["patterns"].items():
                        self.learned_patterns[pattern_id] = LearnedPattern(**pattern_data)
        except Exception as e:
            LOGGER.warning("Failed to load learning data: %s", e)
    
    def _save_learning_data(self) -> None:
        """Save learning data to disk."""
        data_file = self.data_dir / "learning_data.json"
        
        try:
            data = {
                "events": [
                    {
                        "event_id": e.event_id,
                        "event_type": e.event_type,
                        "timestamp": e.timestamp,
                        "context": e.context,
                        "outcome": e.outcome,
                        "user_feedback": e.user_feedback
                    }
                    for e in self.learning_events[-1000:]  # Keep last 1000 events
                ],
                "patterns": {
                    pid: {
                        "pattern_id": p.pattern_id,
                        "pattern_type": p.pattern_type,
                        "description": p.description,
                        "confidence": p.confidence,
                        "occurrences": p.occurrences,
                        "last_seen": p.last_seen,
                        "associated_data": p.associated_data
                    }
                    for pid, p in self.learned_patterns.items()
                }
            }
            
            with open(data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            LOGGER.warning("Failed to save learning data: %s", e)


__all__ = ["ContinuousLearning", "LearningEvent", "LearnedPattern"]

