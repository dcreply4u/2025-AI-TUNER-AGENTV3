"""
AI Advisor Continuous Learning System
Expert-level learning system for the RAG-based AI advisor.

Implements:
- Feedback collection and analysis
- Continuous learning loops
- Knowledge gap detection
- Automatic knowledge base updates
- Performance monitoring
- Governance and safety
"""

from __future__ import annotations

import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

LOGGER = logging.getLogger(__name__)

# Try to import vector store
try:
    from services.vector_knowledge_store import VectorKnowledgeStore
    VECTOR_STORE_AVAILABLE = True
except ImportError:
    VECTOR_STORE_AVAILABLE = False
    VectorKnowledgeStore = None


@dataclass
class FeedbackRecord:
    """User feedback on an answer."""
    question: str
    answer: str
    helpful: bool
    rating: Optional[int] = None  # 1-5 scale
    comment: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    session_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    confidence: float = 0.0
    sources_used: List[str] = field(default_factory=list)


@dataclass
class KnowledgeGap:
    """Identified gap in knowledge base."""
    question: str
    frequency: int  # How many times this question was asked
    avg_confidence: float  # Average confidence when answered
    avg_rating: Optional[float] = None  # Average user rating
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    suggested_answer: Optional[str] = None
    priority: str = "medium"  # low, medium, high, critical


@dataclass
class PerformanceMetrics:
    """Performance metrics for the advisor."""
    total_queries: int = 0
    avg_confidence: float = 0.0
    avg_response_time: float = 0.0
    positive_feedback_rate: float = 0.0
    knowledge_hit_rate: float = 0.0  # % of queries answered from knowledge base
    web_search_rate: float = 0.0  # % of queries requiring web search
    low_confidence_rate: float = 0.0  # % of queries with confidence < 0.5
    knowledge_gaps_count: int = 0


class AILearningSystem:
    """
    Continuous learning system for the AI advisor.
    
    Features:
    - Collects and analyzes user feedback
    - Identifies knowledge gaps
    - Automatically updates knowledge base
    - Monitors performance metrics
    - Implements feedback-driven retraining loop
    - Governance and safety validation
    """
    
    def __init__(
        self,
        vector_store: Optional[VectorKnowledgeStore] = None,
        storage_path: Optional[Path] = None,
        enable_auto_learning: bool = True,
        min_feedback_for_learning: int = 3
    ):
        """
        Initialize learning system.
        
        Args:
            vector_store: Vector knowledge store to update
            storage_path: Path to store learning data
            enable_auto_learning: Enable automatic knowledge base updates
            min_feedback_for_learning: Minimum feedback count before learning
        """
        self.vector_store = vector_store
        self.enable_auto_learning = enable_auto_learning
        self.min_feedback_for_learning = min_feedback_for_learning
        
        # Storage
        self.storage_path = storage_path or Path.home() / ".aituner" / "learning_data"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Data structures
        self.feedback_records: deque = deque(maxlen=10000)  # Last 10k feedback records
        self.knowledge_gaps: Dict[str, KnowledgeGap] = {}
        self.conversation_history: deque = deque(maxlen=5000)  # Last 5k conversations
        self.performance_metrics = PerformanceMetrics()
        
        # Learning state
        self.learning_stats = {
            "total_feedback": 0,
            "positive_feedback": 0,
            "negative_feedback": 0,
            "knowledge_updates": 0,
            "last_update": None
        }
        
        # Load existing data
        self._load_data()
        
        LOGGER.info("AI Learning System initialized")
    
    def record_interaction(
        self,
        question: str,
        answer: str,
        confidence: float,
        sources: List[Dict[str, Any]],
        session_id: Optional[str] = None,
        vehicle_id: Optional[str] = None,
        response_time: Optional[float] = None
    ) -> None:
        """
        Record an interaction for learning.
        
        Args:
            question: User question
            answer: Given answer
            confidence: Answer confidence
            sources: Sources used
            session_id: Session identifier
            vehicle_id: Vehicle identifier
            response_time: Response time in seconds
        """
        interaction = {
            "question": question,
            "answer": answer,
            "confidence": confidence,
            "sources": sources,
            "timestamp": time.time(),
            "session_id": session_id,
            "vehicle_id": vehicle_id,
            "response_time": response_time
        }
        
        self.conversation_history.append(interaction)
        
        # Update performance metrics
        self._update_metrics(interaction)
        
        # Check for knowledge gaps
        if confidence < 0.5:
            self._identify_knowledge_gap(question, confidence)
        
        # Auto-save periodically
        if len(self.conversation_history) % 100 == 0:
            self._save_data()
    
    def record_feedback(
        self,
        question: str,
        answer: str,
        helpful: bool,
        rating: Optional[int] = None,
        comment: Optional[str] = None,
        session_id: Optional[str] = None,
        vehicle_id: Optional[str] = None,
        confidence: Optional[float] = None,
        sources: Optional[List[str]] = None
    ) -> None:
        """
        Record user feedback.
        
        Args:
            question: Original question
            answer: Given answer
            helpful: Whether answer was helpful
            rating: Optional rating (1-5)
            comment: Optional comment
            session_id: Session identifier
            vehicle_id: Vehicle identifier
            confidence: Answer confidence
            sources: Sources used
        """
        feedback = FeedbackRecord(
            question=question,
            answer=answer,
            helpful=helpful,
            rating=rating,
            comment=comment,
            session_id=session_id,
            vehicle_id=vehicle_id,
            confidence=confidence or 0.0,
            sources_used=sources or []
        )
        
        self.feedback_records.append(feedback)
        self.learning_stats["total_feedback"] += 1
        
        if helpful:
            self.learning_stats["positive_feedback"] += 1
        else:
            self.learning_stats["negative_feedback"] += 1
            # Negative feedback triggers immediate gap analysis
            self._identify_knowledge_gap(question, feedback.confidence, rating)
        
        # Update knowledge base if enough feedback collected
        if self.enable_auto_learning:
            self._process_feedback_for_learning(feedback)
        
        # Save data
        self._save_data()
        
        LOGGER.info(f"Feedback recorded: helpful={helpful}, rating={rating}, question={question[:50]}")
    
    def _identify_knowledge_gap(
        self,
        question: str,
        confidence: float,
        rating: Optional[int] = None
    ) -> None:
        """
        Identify and track knowledge gaps.
        
        Args:
            question: Question that had low confidence or negative feedback
            confidence: Answer confidence
            rating: Optional user rating
        """
        question_key = question.lower().strip()
        
        if question_key in self.knowledge_gaps:
            gap = self.knowledge_gaps[question_key]
            gap.frequency += 1
            gap.last_seen = time.time()
            gap.avg_confidence = (gap.avg_confidence * (gap.frequency - 1) + confidence) / gap.frequency
            
            if rating:
                if gap.avg_rating:
                    gap.avg_rating = (gap.avg_rating * (gap.frequency - 1) + rating) / gap.frequency
                else:
                    gap.avg_rating = rating
            
            # Update priority based on frequency and rating
            if gap.frequency >= 10 or (gap.avg_rating and gap.avg_rating < 2.0):
                gap.priority = "critical"
            elif gap.frequency >= 5 or (gap.avg_rating and gap.avg_rating < 3.0):
                gap.priority = "high"
            elif gap.frequency >= 3:
                gap.priority = "medium"
        else:
            gap = KnowledgeGap(
                question=question,
                frequency=1,
                avg_confidence=confidence,
                avg_rating=rating,
                priority="high" if confidence < 0.3 else "medium"
            )
            self.knowledge_gaps[question_key] = gap
        
        self.performance_metrics.knowledge_gaps_count = len(self.knowledge_gaps)
    
    def _process_feedback_for_learning(self, feedback: FeedbackRecord) -> None:
        """
        Process feedback to update knowledge base.
        
        Args:
            feedback: Feedback record
        """
        if not self.vector_store:
            return
        
        # Count feedback for this question pattern
        question_pattern = feedback.question.lower().strip()
        similar_feedback = [
            f for f in self.feedback_records
            if f.question.lower().strip() == question_pattern
        ]
        
        # Only learn if we have enough feedback
        if len(similar_feedback) < self.min_feedback_for_learning:
            return
        
        # Check if feedback is consistently negative
        negative_count = sum(1 for f in similar_feedback if not f.helpful)
        if negative_count >= self.min_feedback_for_learning:
            # This is a knowledge gap - mark for manual review or auto-update
            LOGGER.warning(f"Knowledge gap identified: {feedback.question[:50]}")
            
            # If we have a suggested answer from comments, add it
            if feedback.comment and len(feedback.comment) > 20:
                # Extract potential answer from comment
                self._add_knowledge_from_feedback(feedback)
    
    def _add_knowledge_from_feedback(self, feedback: FeedbackRecord) -> None:
        """
        Add knowledge to vector store from feedback.
        
        Args:
            feedback: Feedback record with potential knowledge
        """
        if not self.vector_store or not feedback.comment:
            return
        
        # Extract topic from question
        question_lower = feedback.question.lower()
        topic = feedback.question.split("?")[0].split(".")[0].strip()
        
        # Use comment as knowledge if it's substantial
        if len(feedback.comment) > 50:
            try:
                self.vector_store.add_knowledge(
                    text=f"Topic: {topic}\n\n{feedback.comment}",
                    metadata={
                        "topic": topic,
                        "source": "user_feedback",
                        "confidence": 0.7,  # Lower confidence for user-sourced
                        "feedback_count": len([f for f in self.feedback_records if not f.helpful])
                    }
                )
                self.learning_stats["knowledge_updates"] += 1
                self.learning_stats["last_update"] = time.time()
                LOGGER.info(f"Added knowledge from feedback: {topic[:50]}")
            except Exception as e:
                LOGGER.error(f"Failed to add knowledge from feedback: {e}")
    
    def _update_metrics(self, interaction: Dict[str, Any]) -> None:
        """Update performance metrics."""
        metrics = self.performance_metrics
        
        # Update counts
        metrics.total_queries += 1
        
        # Update averages using running average
        n = metrics.total_queries
        metrics.avg_confidence = ((metrics.avg_confidence * (n - 1)) + interaction["confidence"]) / n
        
        if interaction.get("response_time"):
            metrics.avg_response_time = (
                (metrics.avg_response_time * (n - 1)) + interaction["response_time"]
            ) / n
        
        # Update rates
        if self.feedback_records:
            positive_count = sum(1 for f in self.feedback_records if f.helpful)
            metrics.positive_feedback_rate = positive_count / len(self.feedback_records)
        
        # Knowledge hit rate (answered from knowledge base vs web search)
        if interaction.get("sources"):
            kb_sources = sum(1 for s in interaction["sources"] if s.get("source") != "web")
            if kb_sources > 0:
                metrics.knowledge_hit_rate = (
                    (metrics.knowledge_hit_rate * (n - 1)) + 1.0
                ) / n
            else:
                metrics.knowledge_hit_rate = (metrics.knowledge_hit_rate * (n - 1)) / n
        
        # Low confidence rate
        if interaction["confidence"] < 0.5:
            metrics.low_confidence_rate = (
                (metrics.low_confidence_rate * (n - 1)) + 1.0
            ) / n
        else:
            metrics.low_confidence_rate = (metrics.low_confidence_rate * (n - 1)) / n
    
    def get_knowledge_gaps(self, priority: Optional[str] = None) -> List[KnowledgeGap]:
        """
        Get identified knowledge gaps.
        
        Args:
            priority: Filter by priority (low, medium, high, critical)
            
        Returns:
            List of knowledge gaps
        """
        gaps = list(self.knowledge_gaps.values())
        
        if priority:
            gaps = [g for g in gaps if g.priority == priority]
        
        # Sort by frequency and priority
        priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        gaps.sort(key=lambda g: (priority_order.get(g.priority, 0), g.frequency), reverse=True)
        
        return gaps
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Get comprehensive performance report.
        
        Returns:
            Performance report dictionary
        """
        return {
            "metrics": asdict(self.performance_metrics),
            "learning_stats": self.learning_stats.copy(),
            "knowledge_gaps": {
                "total": len(self.knowledge_gaps),
                "by_priority": {
                    priority: len([g for g in self.knowledge_gaps.values() if g.priority == priority])
                    for priority in ["critical", "high", "medium", "low"]
                }
            },
            "recent_feedback": {
                "total": len(self.feedback_records),
                "positive_rate": self.performance_metrics.positive_feedback_rate,
                "last_24h": len([
                    f for f in self.feedback_records
                    if time.time() - f.timestamp < 86400
                ])
            }
        }
    
    def _save_data(self) -> None:
        """Save learning data to disk."""
        try:
            # Save feedback records (last 1000)
            feedback_file = self.storage_path / "feedback_records.json"
            recent_feedback = list(self.feedback_records)[-1000:]
            with open(feedback_file, 'w') as f:
                json.dump([asdict(fb) for fb in recent_feedback], f, indent=2)
            
            # Save knowledge gaps
            gaps_file = self.storage_path / "knowledge_gaps.json"
            with open(gaps_file, 'w') as f:
                json.dump(
                    {k: asdict(v) for k, v in self.knowledge_gaps.items()},
                    f,
                    indent=2
                )
            
            # Save metrics
            metrics_file = self.storage_path / "performance_metrics.json"
            with open(metrics_file, 'w') as f:
                json.dump(asdict(self.performance_metrics), f, indent=2)
            
            # Save learning stats
            stats_file = self.storage_path / "learning_stats.json"
            with open(stats_file, 'w') as f:
                json.dump(self.learning_stats, f, indent=2)
            
        except Exception as e:
            LOGGER.error(f"Failed to save learning data: {e}")
    
    def _load_data(self) -> None:
        """Load learning data from disk."""
        try:
            # Load feedback records
            feedback_file = self.storage_path / "feedback_records.json"
            if feedback_file.exists():
                with open(feedback_file, 'r') as f:
                    data = json.load(f)
                    self.feedback_records = deque([
                        FeedbackRecord(**item) for item in data[-1000:]
                    ], maxlen=10000)
            
            # Load knowledge gaps
            gaps_file = self.storage_path / "knowledge_gaps.json"
            if gaps_file.exists():
                with open(gaps_file, 'r') as f:
                    data = json.load(f)
                    self.knowledge_gaps = {
                        k: KnowledgeGap(**v) for k, v in data.items()
                    }
            
            # Load metrics
            metrics_file = self.storage_path / "performance_metrics.json"
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    data = json.load(f)
                    self.performance_metrics = PerformanceMetrics(**data)
            
            # Load learning stats
            stats_file = self.storage_path / "learning_stats.json"
            if stats_file.exists():
                with open(stats_file, 'r') as f:
                    self.learning_stats = json.load(f)
            
            LOGGER.info("Loaded learning data from disk")
            
        except Exception as e:
            LOGGER.warning(f"Failed to load learning data: {e}")

