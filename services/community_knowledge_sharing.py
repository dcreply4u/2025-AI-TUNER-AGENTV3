"""
Community-Driven Knowledge Sharing

Allows users to share successful tuning profiles, data logs, and tips
with the community, creating a crowdsourced knowledge base.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any

LOGGER = logging.getLogger(__name__)


@dataclass
class CommunityTuningProfile:
    """Community-shared tuning profile."""
    profile_id: str
    user_id: str
    vehicle_id: str
    vehicle_specs: Dict[str, Any]
    modifications: List[str]
    tuning_settings: Dict[str, Any]
    performance_results: Dict[str, float]  # HP, torque, etc.
    description: str
    tags: List[str] = field(default_factory=list)
    upvotes: int = 0
    downvotes: int = 0
    downloads: int = 0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    verified: bool = False  # Verified by community or admin


@dataclass
class CommunityDataLog:
    """Community-shared data log."""
    log_id: str
    user_id: str
    vehicle_id: str
    log_data: Dict[str, Any]  # Telemetry data
    session_type: str  # "dyno", "track", "street", etc.
    conditions: Dict[str, Any]  # Weather, track, etc.
    description: str
    tags: List[str] = field(default_factory=list)
    upvotes: int = 0
    downloads: int = 0
    created_at: float = field(default_factory=time.time)


@dataclass
class CommunityTip:
    """Community-shared tuning tip."""
    tip_id: str
    user_id: str
    title: str
    content: str
    category: str  # "tuning", "maintenance", "troubleshooting", etc.
    vehicle_applicability: List[str] = field(default_factory=list)  # Vehicle IDs
    upvotes: int = 0
    helpful_count: int = 0
    created_at: float = field(default_factory=time.time)


class CommunityKnowledgeSharing:
    """
    Community-driven knowledge sharing system.
    
    Features:
    - Share tuning profiles
    - Share data logs
    - Share tips and tricks
    - Upvote/downvote system
    - Search and filter
    - Community verification
    """
    
    def __init__(self, storage_path: Optional[Path] = None, api_endpoint: Optional[str] = None):
        """
        Initialize community knowledge sharing.
        
        Args:
            storage_path: Path to store local data
            api_endpoint: API endpoint for cloud sync (optional)
        """
        self.storage_path = storage_path or Path("data/community_knowledge.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.api_endpoint = api_endpoint
        
        # Community data
        self.tuning_profiles: Dict[str, CommunityTuningProfile] = {}
        self.data_logs: Dict[str, CommunityDataLog] = {}
        self.tips: Dict[str, CommunityTip] = {}
        
        # User contributions
        self.user_contributions: Dict[str, List[str]] = {}  # user_id -> [profile_ids, log_ids, tip_ids]
        
        # Load existing data
        self._load_community_data()
    
    def share_tuning_profile(
        self,
        user_id: str,
        vehicle_id: str,
        vehicle_specs: Dict[str, Any],
        modifications: List[str],
        tuning_settings: Dict[str, Any],
        performance_results: Dict[str, float],
        description: str,
        tags: Optional[List[str]] = None
    ) -> CommunityTuningProfile:
        """
        Share a tuning profile with community.
        
        Args:
            user_id: User identifier
            vehicle_id: Vehicle identifier
            vehicle_specs: Vehicle specifications
            modifications: List of modifications
            tuning_settings: Tuning settings/parameters
            performance_results: Performance results (HP, torque, etc.)
            description: Profile description
            tags: Optional tags
        
        Returns:
            Created tuning profile
        """
        profile_id = f"profile_{int(time.time())}_{user_id}"
        
        profile = CommunityTuningProfile(
            profile_id=profile_id,
            user_id=user_id,
            vehicle_id=vehicle_id,
            vehicle_specs=vehicle_specs,
            modifications=modifications,
            tuning_settings=tuning_settings,
            performance_results=performance_results,
            description=description,
            tags=tags or [],
        )
        
        self.tuning_profiles[profile_id] = profile
        
        # Track user contribution
        if user_id not in self.user_contributions:
            self.user_contributions[user_id] = []
        self.user_contributions[user_id].append(profile_id)
        
        self._save_community_data()
        LOGGER.info("User %s shared tuning profile: %s", user_id, profile_id)
        
        return profile
    
    def share_data_log(
        self,
        user_id: str,
        vehicle_id: str,
        log_data: Dict[str, Any],
        session_type: str,
        conditions: Dict[str, Any],
        description: str,
        tags: Optional[List[str]] = None
    ) -> CommunityDataLog:
        """
        Share a data log with community.
        
        Args:
            user_id: User identifier
            vehicle_id: Vehicle identifier
            log_data: Telemetry/log data
            session_type: Type of session
            conditions: Conditions (weather, track, etc.)
            description: Log description
            tags: Optional tags
        
        Returns:
            Created data log
        """
        log_id = f"log_{int(time.time())}_{user_id}"
        
        log = CommunityDataLog(
            log_id=log_id,
            user_id=user_id,
            vehicle_id=vehicle_id,
            log_data=log_data,
            session_type=session_type,
            conditions=conditions,
            description=description,
            tags=tags or [],
        )
        
        self.data_logs[log_id] = log
        
        # Track user contribution
        if user_id not in self.user_contributions:
            self.user_contributions[user_id] = []
        self.user_contributions[user_id].append(log_id)
        
        self._save_community_data()
        LOGGER.info("User %s shared data log: %s", user_id, log_id)
        
        return log
    
    def share_tip(
        self,
        user_id: str,
        title: str,
        content: str,
        category: str,
        vehicle_applicability: Optional[List[str]] = None
    ) -> CommunityTip:
        """
        Share a tip with community.
        
        Args:
            user_id: User identifier
            title: Tip title
            content: Tip content
            category: Tip category
            vehicle_applicability: Applicable vehicle IDs
        
        Returns:
            Created tip
        """
        tip_id = f"tip_{int(time.time())}_{user_id}"
        
        tip = CommunityTip(
            tip_id=tip_id,
            user_id=user_id,
            title=title,
            content=content,
            category=category,
            vehicle_applicability=vehicle_applicability or [],
        )
        
        self.tips[tip_id] = tip
        
        # Track user contribution
        if user_id not in self.user_contributions:
            self.user_contributions[user_id] = []
        self.user_contributions[user_id].append(tip_id)
        
        self._save_community_data()
        LOGGER.info("User %s shared tip: %s", user_id, tip_id)
        
        return tip
    
    def search_profiles(
        self,
        vehicle_id: Optional[str] = None,
        min_hp: Optional[int] = None,
        tags: Optional[List[str]] = None,
        sort_by: str = "upvotes"  # "upvotes", "downloads", "recent"
    ) -> List[CommunityTuningProfile]:
        """
        Search tuning profiles.
        
        Args:
            vehicle_id: Filter by vehicle
            min_hp: Minimum HP gain
            tags: Filter by tags
            sort_by: Sort order
        
        Returns:
            List of matching profiles
        """
        results = []
        
        for profile in self.tuning_profiles.values():
            if vehicle_id and profile.vehicle_id != vehicle_id:
                continue
            if min_hp and profile.performance_results.get("hp_gain", 0) < min_hp:
                continue
            if tags and not any(tag in profile.tags for tag in tags):
                continue
            results.append(profile)
        
        # Sort
        if sort_by == "upvotes":
            results.sort(key=lambda p: p.upvotes - p.downvotes, reverse=True)
        elif sort_by == "downloads":
            results.sort(key=lambda p: p.downloads, reverse=True)
        elif sort_by == "recent":
            results.sort(key=lambda p: p.created_at, reverse=True)
        
        return results
    
    def upvote_profile(self, profile_id: str, user_id: str) -> None:
        """Upvote a tuning profile."""
        if profile_id in self.tuning_profiles:
            self.tuning_profiles[profile_id].upvotes += 1
            self._save_community_data()
    
    def downvote_profile(self, profile_id: str, user_id: str) -> None:
        """Downvote a tuning profile."""
        if profile_id in self.tuning_profiles:
            self.tuning_profiles[profile_id].downvotes += 1
            self._save_community_data()
    
    def download_profile(self, profile_id: str, user_id: str) -> Dict[str, Any]:
        """
        Download a tuning profile.
        
        Args:
            profile_id: Profile ID
            user_id: User downloading
        
        Returns:
            Profile data
        """
        if profile_id in self.tuning_profiles:
            profile = self.tuning_profiles[profile_id]
            profile.downloads += 1
            self._save_community_data()
            
            return {
                "tuning_settings": profile.tuning_settings,
                "vehicle_specs": profile.vehicle_specs,
                "modifications": profile.modifications,
                "performance_results": profile.performance_results,
            }
        return {}
    
    def _save_community_data(self) -> None:
        """Save community data to disk."""
        try:
            data = {
                "tuning_profiles": {
                    k: asdict(v) for k, v in self.tuning_profiles.items()
                },
                "data_logs": {
                    k: asdict(v) for k, v in self.data_logs.items()
                },
                "tips": {
                    k: asdict(v) for k, v in self.tips.items()
                },
                "user_contributions": self.user_contributions,
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            LOGGER.error("Failed to save community data: %s", e)
    
    def _load_community_data(self) -> None:
        """Load community data from disk."""
        if not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            # Load tuning profiles
            self.tuning_profiles = {
                k: CommunityTuningProfile(**v)
                for k, v in data.get("tuning_profiles", {}).items()
            }
            
            # Load data logs
            self.data_logs = {
                k: CommunityDataLog(**v)
                for k, v in data.get("data_logs", {}).items()
            }
            
            # Load tips
            self.tips = {
                k: CommunityTip(**v)
                for k, v in data.get("tips", {}).items()
            }
            
            # Load user contributions
            self.user_contributions = data.get("user_contributions", {})
            
            LOGGER.info("Loaded community data: %d profiles, %d logs, %d tips",
                       len(self.tuning_profiles), len(self.data_logs), len(self.tips))
        except Exception as e:
            LOGGER.error("Failed to load community data: %s", e)


__all__ = [
    "CommunityKnowledgeSharing",
    "CommunityTuningProfile",
    "CommunityDataLog",
    "CommunityTip",
]









