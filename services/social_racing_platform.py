"""
Social Racing Platform
Gamified racing with leaderboards, challenges, and achievements.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class AchievementType(Enum):
    """Achievement types."""
    FIRST_RUN = "first_run"
    SPEED_DEMON = "speed_demon"
    CONSISTENCY_KING = "consistency_king"
    POWER_MONSTER = "power_monster"
    TRACK_MASTER = "track_master"
    STREET_LEGEND = "street_legend"
    TUNING_GURU = "tuning_guru"
    DATA_ANALYST = "data_analyst"


@dataclass
class Achievement:
    """User achievement."""
    achievement_id: str
    achievement_type: AchievementType
    name: str
    description: str
    unlocked_at: float
    progress: float = 100.0  # 0-100
    icon: str = ""


@dataclass
class LeaderboardEntry:
    """Leaderboard entry."""
    rank: int
    user_id: str
    username: str
    vehicle: str
    value: float  # Time, speed, power, etc.
    unit: str
    timestamp: float
    verified: bool = False


@dataclass
class Challenge:
    """Racing challenge."""
    challenge_id: str
    name: str
    description: str
    category: str  # speed, consistency, power, etc.
    target_value: float
    unit: str
    start_date: float
    end_date: float
    participants: List[str] = field(default_factory=list)
    winners: List[str] = field(default_factory=list)
    prize: str = ""


@dataclass
class UserProfile:
    """User profile for social platform."""
    user_id: str
    username: str
    vehicle: str
    achievements: List[Achievement] = field(default_factory=list)
    best_times: Dict[str, float] = field(default_factory=dict)  # Track -> time
    best_speeds: Dict[str, float] = field(default_factory=dict)  # Category -> speed
    total_runs: int = 0
    total_distance: float = 0.0  # miles
    rating: float = 0.0
    level: int = 1
    xp: int = 0
    joined_at: float = field(default_factory=time.time)


class SocialRacingPlatform:
    """
    Social racing platform service.
    
    Features:
    - Leaderboards
    - Achievements
    - Challenges
    - User profiles
    - Community sharing
    """
    
    def __init__(
        self,
        server_url: Optional[str] = None,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
    ):
        """
        Initialize social racing platform.
        
        Args:
            server_url: Platform server URL (optional, can work offline)
            user_id: Current user ID
            username: Current username
        """
        self.server_url = server_url.rstrip('/') if server_url else None
        self.user_id = user_id
        self.username = username
        
        self.current_profile: Optional[UserProfile] = None
        self.leaderboards: Dict[str, List[LeaderboardEntry]] = {}
        self.challenges: List[Challenge] = []
        
        # Local storage
        self.data_dir = Path("data/social_platform")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        if user_id:
            self._load_profile()
    
    def create_profile(
        self,
        username: str,
        vehicle: str,
        user_id: Optional[str] = None,
    ) -> UserProfile:
        """
        Create user profile.
        
        Args:
            username: Username
            vehicle: Vehicle name
            user_id: User ID (generated if None)
        
        Returns:
            Created UserProfile
        """
        if user_id is None:
            import uuid
            user_id = str(uuid.uuid4())
        
        profile = UserProfile(
            user_id=user_id,
            username=username,
            vehicle=vehicle,
            joined_at=time.time(),
        )
        
        self.current_profile = profile
        self.user_id = user_id
        self.username = username
        
        self._save_profile()
        
        # Register with server if available
        if self.server_url and REQUESTS_AVAILABLE:
            try:
                requests.post(
                    f"{self.server_url}/api/profiles",
                    json={
                        "user_id": user_id,
                        "username": username,
                        "vehicle": vehicle,
                    },
                    timeout=10,
                )
            except requests.RequestException as e:
                LOGGER.warning("Failed to register profile with server: %s", e)
        
        LOGGER.info("Profile created: %s", username)
        return profile
    
    def submit_run(
        self,
        track_name: str,
        time_seconds: float,
        telemetry_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Submit a run for leaderboards.
        
        Args:
            track_name: Track or category name
            time_seconds: Run time in seconds
            telemetry_data: Optional telemetry data
        
        Returns:
            True if submitted successfully
        """
        if not self.current_profile:
            LOGGER.error("No profile found")
            return False
        
        # Update profile
        if track_name not in self.current_profile.best_times or \
           time_seconds < self.current_profile.best_times[track_name]:
            self.current_profile.best_times[track_name] = time_seconds
        
        self.current_profile.total_runs += 1
        if telemetry_data:
            distance = telemetry_data.get("distance_miles", 0.0)
            self.current_profile.total_distance += distance
        
        # Award XP
        self._award_xp(100)  # Base XP for run
        
        # Check for achievements
        self._check_achievements()
        
        self._save_profile()
        
        # Submit to server
        if self.server_url and REQUESTS_AVAILABLE:
            try:
                requests.post(
                    f"{self.server_url}/api/runs",
                    json={
                        "user_id": self.user_id,
                        "track_name": track_name,
                        "time_seconds": time_seconds,
                        "telemetry_data": telemetry_data,
                    },
                    timeout=10,
                )
            except requests.RequestException as e:
                LOGGER.warning("Failed to submit run to server: %s", e)
        
        LOGGER.info("Run submitted: %s - %.2fs", track_name, time_seconds)
        return True
    
    def get_leaderboard(
        self,
        category: str,
        limit: int = 100,
    ) -> List[LeaderboardEntry]:
        """
        Get leaderboard for category.
        
        Args:
            category: Leaderboard category (e.g., "0-60", "quarter_mile", "track_name")
            limit: Number of entries to return
        
        Returns:
            List of leaderboard entries
        """
        # Try to fetch from server
        if self.server_url and REQUESTS_AVAILABLE:
            try:
                response = requests.get(
                    f"{self.server_url}/api/leaderboards/{category}",
                    params={"limit": limit},
                    timeout=10,
                )
                response.raise_for_status()
                
                data = response.json()
                entries = []
                for entry_data in data.get("entries", []):
                    entry = LeaderboardEntry(
                        rank=entry_data["rank"],
                        user_id=entry_data["user_id"],
                        username=entry_data["username"],
                        vehicle=entry_data.get("vehicle", ""),
                        value=entry_data["value"],
                        unit=entry_data.get("unit", ""),
                        timestamp=entry_data.get("timestamp", time.time()),
                        verified=entry_data.get("verified", False),
                    )
                    entries.append(entry)
                
                self.leaderboards[category] = entries
                return entries
            except requests.RequestException as e:
                LOGGER.warning("Failed to fetch leaderboard from server: %s", e)
        
        # Return cached leaderboard
        return self.leaderboards.get(category, [])
    
    def get_achievements(self) -> List[Achievement]:
        """Get user achievements."""
        if not self.current_profile:
            return []
        return self.current_profile.achievements
    
    def get_challenges(self, active_only: bool = True) -> List[Challenge]:
        """
        Get available challenges.
        
        Args:
            active_only: Only return active challenges
        
        Returns:
            List of challenges
        """
        # Try to fetch from server
        if self.server_url and REQUESTS_AVAILABLE:
            try:
                response = requests.get(
                    f"{self.server_url}/api/challenges",
                    params={"active_only": active_only},
                    timeout=10,
                )
                response.raise_for_status()
                
                data = response.json()
                challenges = []
                for challenge_data in data.get("challenges", []):
                    challenge = Challenge(
                        challenge_id=challenge_data["challenge_id"],
                        name=challenge_data["name"],
                        description=challenge_data["description"],
                        category=challenge_data["category"],
                        target_value=challenge_data["target_value"],
                        unit=challenge_data.get("unit", ""),
                        start_date=challenge_data["start_date"],
                        end_date=challenge_data["end_date"],
                        participants=challenge_data.get("participants", []),
                        winners=challenge_data.get("winners", []),
                        prize=challenge_data.get("prize", ""),
                    )
                    challenges.append(challenge)
                
                self.challenges = challenges
                return challenges
            except requests.RequestException as e:
                LOGGER.warning("Failed to fetch challenges from server: %s", e)
        
        # Return cached challenges
        current_time = time.time()
        if active_only:
            return [c for c in self.challenges 
                   if c.start_date <= current_time <= c.end_date]
        return self.challenges
    
    def join_challenge(self, challenge_id: str) -> bool:
        """
        Join a challenge.
        
        Args:
            challenge_id: Challenge ID
        
        Returns:
            True if joined successfully
        """
        if not self.user_id:
            return False
        
        # Submit to server
        if self.server_url and REQUESTS_AVAILABLE:
            try:
                response = requests.post(
                    f"{self.server_url}/api/challenges/{challenge_id}/join",
                    json={"user_id": self.user_id},
                    timeout=10,
                )
                response.raise_for_status()
                return True
            except requests.RequestException as e:
                LOGGER.warning("Failed to join challenge: %s", e)
                return False
        
        return False
    
    def share_map(self, map_id: str, description: str = "") -> bool:
        """
        Share a tuning map with community.
        
        Args:
            map_id: Map ID to share
            description: Map description
        
        Returns:
            True if shared successfully
        """
        if self.server_url and REQUESTS_AVAILABLE:
            try:
                response = requests.post(
                    f"{self.server_url}/api/maps/share",
                    json={
                        "user_id": self.user_id,
                        "map_id": map_id,
                        "description": description,
                    },
                    timeout=10,
                )
                response.raise_for_status()
                LOGGER.info("Map shared: %s", map_id)
                return True
            except requests.RequestException as e:
                LOGGER.warning("Failed to share map: %s", e)
                return False
        
        return False
    
    def _check_achievements(self) -> None:
        """Check and award achievements."""
        if not self.current_profile:
            return
        
        # First run achievement
        if self.current_profile.total_runs == 1:
            self._award_achievement(AchievementType.FIRST_RUN, "First Run", 
                                  "Completed your first run!")
        
        # Speed demon (high speed)
        if any(speed >= 150 for speed in self.current_profile.best_speeds.values()):
            self._award_achievement(AchievementType.SPEED_DEMON, "Speed Demon",
                                  "Reached 150+ MPH!")
        
        # Consistency (multiple runs)
        if self.current_profile.total_runs >= 50:
            self._award_achievement(AchievementType.CONSISTENCY_KING, "Consistency King",
                                  "Completed 50+ runs!")
        
        # Power monster (high power)
        # Would need power data from telemetry
    
    def _award_achievement(
        self,
        achievement_type: AchievementType,
        name: str,
        description: str,
    ) -> None:
        """Award an achievement."""
        if not self.current_profile:
            return
        
        # Check if already unlocked
        if any(a.achievement_type == achievement_type 
               for a in self.current_profile.achievements):
            return
        
        achievement = Achievement(
            achievement_id=str(int(time.time())),
            achievement_type=achievement_type,
            name=name,
            description=description,
            unlocked_at=time.time(),
        )
        
        self.current_profile.achievements.append(achievement)
        self._award_xp(500)  # XP for achievement
        
        LOGGER.info("Achievement unlocked: %s", name)
    
    def _award_xp(self, amount: int) -> None:
        """Award experience points."""
        if not self.current_profile:
            return
        
        self.current_profile.xp += amount
        
        # Level up (1000 XP per level)
        new_level = (self.current_profile.xp // 1000) + 1
        if new_level > self.current_profile.level:
            old_level = self.current_profile.level
            self.current_profile.level = new_level
            LOGGER.info("Level up! %d -> %d", old_level, new_level)
    
    def _save_profile(self) -> None:
        """Save user profile."""
        if not self.current_profile:
            return
        
        try:
            profile_file = self.data_dir / f"{self.user_id}_profile.json"
            with open(profile_file, 'w') as f:
                json.dump({
                    "user_id": self.current_profile.user_id,
                    "username": self.current_profile.username,
                    "vehicle": self.current_profile.vehicle,
                    "achievements": [
                        {
                            "achievement_id": a.achievement_id,
                            "achievement_type": a.achievement_type.value,
                            "name": a.name,
                            "description": a.description,
                            "unlocked_at": a.unlocked_at,
                            "progress": a.progress,
                        }
                        for a in self.current_profile.achievements
                    ],
                    "best_times": self.current_profile.best_times,
                    "best_speeds": self.current_profile.best_speeds,
                    "total_runs": self.current_profile.total_runs,
                    "total_distance": self.current_profile.total_distance,
                    "rating": self.current_profile.rating,
                    "level": self.current_profile.level,
                    "xp": self.current_profile.xp,
                    "joined_at": self.current_profile.joined_at,
                }, f, indent=2)
        except Exception as e:
            LOGGER.error("Failed to save profile: %s", e)
    
    def _load_profile(self) -> None:
        """Load user profile."""
        if not self.user_id:
            return
        
        try:
            profile_file = self.data_dir / f"{self.user_id}_profile.json"
            if not profile_file.exists():
                return
            
            with open(profile_file, 'r') as f:
                data = json.load(f)
            
            achievements = [
                Achievement(
                    achievement_id=a["achievement_id"],
                    achievement_type=AchievementType(a["achievement_type"]),
                    name=a["name"],
                    description=a["description"],
                    unlocked_at=a["unlocked_at"],
                    progress=a.get("progress", 100.0),
                )
                for a in data.get("achievements", [])
            ]
            
            self.current_profile = UserProfile(
                user_id=data["user_id"],
                username=data["username"],
                vehicle=data["vehicle"],
                achievements=achievements,
                best_times=data.get("best_times", {}),
                best_speeds=data.get("best_speeds", {}),
                total_runs=data.get("total_runs", 0),
                total_distance=data.get("total_distance", 0.0),
                rating=data.get("rating", 0.0),
                level=data.get("level", 1),
                xp=data.get("xp", 0),
                joined_at=data.get("joined_at", time.time()),
            )
        except Exception as e:
            LOGGER.error("Failed to load profile: %s", e)
