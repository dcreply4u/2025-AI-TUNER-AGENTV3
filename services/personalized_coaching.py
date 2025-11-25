"""
Personalized Coaching and Progression Tracking
Tracks user progress and adapts advice to skill level.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

LOGGER = logging.getLogger(__name__)


class SkillLevel(Enum):
    """User skill levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class UserProgress:
    """User progress tracking data."""
    user_id: str
    skill_level: SkillLevel = SkillLevel.BEGINNER
    total_sessions: int = 0
    total_questions: int = 0
    topics_covered: List[str] = field(default_factory=list)
    recurring_issues: Dict[str, int] = field(default_factory=dict)  # issue -> count
    successful_tunes: int = 0
    failed_tunes: int = 0
    improvement_areas: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    last_session_time: float = 0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class CoachingRecommendation:
    """A personalized coaching recommendation."""
    title: str
    description: str
    skill_level: SkillLevel
    priority: str  # "low", "medium", "high"
    action_items: List[str] = field(default_factory=list)
    expected_improvement: str = ""


class PersonalizedCoaching:
    """
    Personalized coaching system that adapts to user skill level.
    
    Features:
    - Progress tracking
    - Skill level assessment
    - Recurring issue identification
    - Personalized recommendations
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize coaching system.
        
        Args:
            data_dir: Directory to store user progress data
        """
        if data_dir is None:
            data_dir = Path.home() / ".telemetryiq" / "coaching"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.user_progress: Dict[str, UserProgress] = {}
        self._load_progress()
    
    def get_user_progress(self, user_id: str) -> UserProgress:
        """Get or create user progress."""
        if user_id not in self.user_progress:
            self.user_progress[user_id] = UserProgress(user_id=user_id)
        return self.user_progress[user_id]
    
    def record_interaction(
        self,
        user_id: str,
        question: str,
        topic: Optional[str] = None,
        success: Optional[bool] = None
    ) -> None:
        """Record a user interaction."""
        progress = self.get_user_progress(user_id)
        progress.total_questions += 1
        progress.updated_at = time.time()
        
        if topic:
            if topic not in progress.topics_covered:
                progress.topics_covered.append(topic)
        
        # Detect recurring issues
        question_lower = question.lower()
        issue_keywords = {
            "knock": "knock/detonation issues",
            "overheat": "overheating problems",
            "unstable": "stability issues",
            "lean": "lean condition problems",
            "boost": "boost control issues",
        }
        
        for keyword, issue_name in issue_keywords.items():
            if keyword in question_lower:
                progress.recurring_issues[issue_name] = progress.recurring_issues.get(issue_name, 0) + 1
        
        # Update skill level based on interactions
        self._update_skill_level(progress)
        
        self._save_progress(user_id)
    
    def record_tune_result(self, user_id: str, successful: bool) -> None:
        """Record a tuning session result."""
        progress = self.get_user_progress(user_id)
        if successful:
            progress.successful_tunes += 1
        else:
            progress.failed_tunes += 1
        progress.total_sessions += 1
        progress.last_session_time = time.time()
        progress.updated_at = time.time()
        
        self._update_skill_level(progress)
        self._save_progress(user_id)
    
    def _update_skill_level(self, progress: UserProgress) -> None:
        """Update user skill level based on progress."""
        # Simple skill level assessment
        total_interactions = progress.total_questions
        success_rate = progress.successful_tunes / max(1, progress.successful_tunes + progress.failed_tunes)
        topics_count = len(progress.topics_covered)
        
        if total_interactions < 10 or topics_count < 3:
            progress.skill_level = SkillLevel.BEGINNER
        elif total_interactions < 50 or success_rate < 0.7:
            progress.skill_level = SkillLevel.INTERMEDIATE
        elif total_interactions < 200 or success_rate < 0.85:
            progress.skill_level = SkillLevel.ADVANCED
        else:
            progress.skill_level = SkillLevel.EXPERT
    
    def get_coaching_recommendations(self, user_id: str) -> List[CoachingRecommendation]:
        """Get personalized coaching recommendations."""
        progress = self.get_user_progress(user_id)
        recommendations = []
        
        # Identify recurring issues
        if progress.recurring_issues:
            top_issue = max(progress.recurring_issues.items(), key=lambda x: x[1])
            if top_issue[1] >= 3:  # Issue mentioned 3+ times
                recommendations.append(CoachingRecommendation(
                    title=f"Address Recurring Issue: {top_issue[0]}",
                    description=f"You've asked about {top_issue[0]} {top_issue[1]} times. Let's focus on resolving this.",
                    skill_level=progress.skill_level,
                    priority="high",
                    action_items=self._get_action_items_for_issue(top_issue[0], progress.skill_level),
                    expected_improvement="Resolve recurring issue and improve confidence"
                ))
        
        # Skill-level specific recommendations
        if progress.skill_level == SkillLevel.BEGINNER:
            if "fuel" not in progress.topics_covered:
                recommendations.append(CoachingRecommendation(
                    title="Learn Fuel Tuning Basics",
                    description="Start with understanding fuel tuning fundamentals",
                    skill_level=SkillLevel.BEGINNER,
                    priority="medium",
                    action_items=[
                        "Learn about AFR targets (12.5-13.2:1 for WOT)",
                        "Understand VE table basics",
                        "Practice with Local Autotune feature"
                    ],
                    expected_improvement="Foundation for all tuning work"
                ))
        
        elif progress.skill_level == SkillLevel.INTERMEDIATE:
            if progress.successful_tunes < 5:
                recommendations.append(CoachingRecommendation(
                    title="Practice Complete Tuning Sessions",
                    description="Complete more full tuning sessions to build experience",
                    skill_level=SkillLevel.INTERMEDIATE,
                    priority="medium",
                    action_items=[
                        "Complete 3-5 full tuning sessions",
                        "Document what works and what doesn't",
                        "Practice with different vehicles"
                    ],
                    expected_improvement="Build confidence and experience"
                ))
        
        # Identify improvement areas
        if not progress.strengths:
            recommendations.append(CoachingRecommendation(
                title="Build Your Strengths",
                description="Focus on areas you're comfortable with first",
                skill_level=progress.skill_level,
                priority="low",
                action_items=[
                    "Identify topics you understand well",
                    "Practice those areas to build confidence",
                    "Gradually expand to new topics"
                ],
                expected_improvement="Builds confidence and solid foundation"
            ))
        
        return recommendations
    
    def _get_action_items_for_issue(self, issue: str, skill_level: SkillLevel) -> List[str]:
        """Get action items for a specific issue."""
        if "knock" in issue.lower():
            if skill_level == SkillLevel.BEGINNER:
                return [
                    "Learn what causes knock (too much timing, lean AFR, high boost)",
                    "Always monitor knock sensor",
                    "Start with conservative timing (20-22°)"
                ]
            else:
                return [
                    "Reduce timing by 2-3° in affected cells",
                    "Enrich fuel mixture if lean",
                    "Reduce boost if necessary",
                    "Check intake air temperature"
                ]
        elif "overheat" in issue.lower():
            return [
                "Check cooling system",
                "Reduce load or boost",
                "Enrich fuel (lowers EGT)",
                "Check for coolant leaks"
            ]
        elif "unstable" in issue.lower():
            return [
                "Check throttle mapping",
                "Review suspension settings",
                "Consider traction control adjustments",
                "Smooth throttle transitions"
            ]
        return ["Investigate root cause", "Check telemetry data", "Consult tuning guide"]
    
    def get_personalized_advice(self, user_id: str, question: str) -> Optional[str]:
        """Get personalized advice based on user's history."""
        progress = self.get_user_progress(user_id)
        
        # Check for recurring issues
        question_lower = question.lower()
        for issue, count in progress.recurring_issues.items():
            if any(word in question_lower for word in issue.lower().split()):
                if count >= 3:
                    return f"I notice you've asked about {issue} before. Let me help you resolve this once and for all. "
        
        # Skill-level appropriate responses
        if progress.skill_level == SkillLevel.BEGINNER:
            if "how do i" in question_lower or "how to" in question_lower:
                return "Since you're just starting out, let me break this down step-by-step. "
        
        return None
    
    def _load_progress(self) -> None:
        """Load user progress from disk."""
        progress_file = self.data_dir / "user_progress.json"
        if not progress_file.exists():
            return
        
        try:
            with open(progress_file, 'r') as f:
                data = json.load(f)
                for user_id, user_data in data.items():
                    # Convert skill level string to enum
                    skill_level_str = user_data.get("skill_level", "beginner")
                    skill_level = SkillLevel(skill_level_str)
                    self.user_progress[user_id] = UserProgress(
                        user_id=user_id,
                        skill_level=skill_level,
                        total_sessions=user_data.get("total_sessions", 0),
                        total_questions=user_data.get("total_questions", 0),
                        topics_covered=user_data.get("topics_covered", []),
                        recurring_issues=user_data.get("recurring_issues", {}),
                        successful_tunes=user_data.get("successful_tunes", 0),
                        failed_tunes=user_data.get("failed_tunes", 0),
                        improvement_areas=user_data.get("improvement_areas", []),
                        strengths=user_data.get("strengths", []),
                        last_session_time=user_data.get("last_session_time", 0),
                        created_at=user_data.get("created_at", time.time()),
                        updated_at=user_data.get("updated_at", time.time()),
                    )
        except Exception as e:
            LOGGER.warning("Failed to load user progress: %s", e)
    
    def _save_progress(self, user_id: str) -> None:
        """Save user progress to disk."""
        progress_file = self.data_dir / "user_progress.json"
        
        try:
            # Load existing data
            data = {}
            if progress_file.exists():
                with open(progress_file, 'r') as f:
                    data = json.load(f)
            
            # Update user data
            progress = self.user_progress[user_id]
            data[user_id] = {
                "skill_level": progress.skill_level.value,
                "total_sessions": progress.total_sessions,
                "total_questions": progress.total_questions,
                "topics_covered": progress.topics_covered,
                "recurring_issues": progress.recurring_issues,
                "successful_tunes": progress.successful_tunes,
                "failed_tunes": progress.failed_tunes,
                "improvement_areas": progress.improvement_areas,
                "strengths": progress.strengths,
                "last_session_time": progress.last_session_time,
                "created_at": progress.created_at,
                "updated_at": progress.updated_at,
            }
            
            # Save
            with open(progress_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            LOGGER.warning("Failed to save user progress: %s", e)


__all__ = ["PersonalizedCoaching", "UserProgress", "CoachingRecommendation", "SkillLevel"]

