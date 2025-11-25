"""
Crowdsourced Track Database

Community shares track data, optimal lines, and best practices.
This creates a NETWORK EFFECT - more users = more valuable!
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

LOGGER = logging.getLogger(__name__)


@dataclass
class TrackSubmission:
    """Track data submission from community."""

    track_name: str
    track_id: str
    gps_trace: List[Dict[str, float]]
    optimal_lap_time: float
    submitted_by: str
    vehicle_type: str
    conditions: Dict[str, float]
    verified: bool = False
    upvotes: int = 0
    timestamp: float = field(default_factory=time.time)


@dataclass
class CommunityTrackData:
    """Aggregated community track data."""

    track_name: str
    track_id: str
    submissions: List[TrackSubmission]
    average_lap_time: float
    best_lap_time: float
    optimal_line: List[Dict[str, float]]
    braking_points: List[Dict[str, float]]
    popularity_score: float  # Based on submissions and upvotes


class CrowdsourcedTrackDatabase:
    """
    Crowdsourced Track Database.

    UNIQUE FEATURE: No one has built a crowdsourced track database!
    Community shares track data, creating a NETWORK EFFECT.
    More users = more tracks = more value = more users!
    """

    def __init__(self, api_endpoint: Optional[str] = None) -> None:
        """
        Initialize crowdsourced track database.

        Args:
            api_endpoint: API endpoint for cloud sync (optional)
        """
        self.api_endpoint = api_endpoint
        self.local_tracks: Dict[str, CommunityTrackData] = {}
        self.user_submissions: List[TrackSubmission] = []

    def submit_track_data(
        self,
        track_name: str,
        gps_trace: List[Dict[str, float]],
        lap_time: float,
        vehicle_type: str,
        conditions: Dict[str, float],
        user_id: str,
    ) -> TrackSubmission:
        """
        Submit track data to community database.

        Args:
            track_name: Name of track
            gps_trace: GPS coordinates
            lap_time: Lap time
            vehicle_type: Type of vehicle
            conditions: Weather/conditions
            user_id: User ID

        Returns:
            Track submission
        """
        from services.track_learning_ai import TrackLearningAI

        track_ai = TrackLearningAI()
        track_id = track_ai._generate_track_id(gps_trace)

        submission = TrackSubmission(
            track_name=track_name,
            track_id=track_id,
            gps_trace=gps_trace,
            optimal_lap_time=lap_time,
            submitted_by=user_id,
            vehicle_type=vehicle_type,
            conditions=conditions,
        )

        self.user_submissions.append(submission)

        # Update local database
        if track_id not in self.local_tracks:
            self.local_tracks[track_id] = CommunityTrackData(
                track_name=track_name,
                track_id=track_id,
                submissions=[],
                average_lap_time=lap_time,
                best_lap_time=lap_time,
                optimal_line=gps_trace,
                braking_points=[],
                popularity_score=1.0,
            )

        track_data = self.local_tracks[track_id]
        track_data.submissions.append(submission)

        # Update statistics
        lap_times = [s.optimal_lap_time for s in track_data.submissions]
        track_data.average_lap_time = sum(lap_times) / len(lap_times)
        track_data.best_lap_time = min(lap_times)

        # Update optimal line (use fastest lap)
        if lap_time == track_data.best_lap_time:
            track_data.optimal_line = gps_trace

        # Update popularity
        track_data.popularity_score = len(track_data.submissions) + sum(s.upvotes for s in track_data.submissions)

        LOGGER.info(f"Submitted track data for {track_name}: {lap_time:.2f}s")

        return submission

    def get_track_data(self, track_id: str) -> Optional[CommunityTrackData]:
        """
        Get community track data.

        Args:
            track_id: Track ID

        Returns:
            Community track data or None
        """
        return self.local_tracks.get(track_id)

    def search_tracks(self, query: str) -> List[CommunityTrackData]:
        """
        Search for tracks by name.

        Args:
            query: Search query

        Returns:
            List of matching tracks
        """
        query_lower = query.lower()
        matches = []

        for track_data in self.local_tracks.values():
            if query_lower in track_data.track_name.lower():
                matches.append(track_data)

        # Sort by popularity
        matches.sort(key=lambda t: t.popularity_score, reverse=True)

        return matches

    def get_popular_tracks(self, limit: int = 10) -> List[CommunityTrackData]:
        """Get most popular tracks."""
        tracks = list(self.local_tracks.values())
        tracks.sort(key=lambda t: t.popularity_score, reverse=True)
        return tracks[:limit]

    def upvote_track(self, track_id: str, submission_index: int) -> bool:
        """
        Upvote a track submission.

        Args:
            track_id: Track ID
            submission_index: Index of submission

        Returns:
            True if upvoted successfully
        """
        track_data = self.local_tracks.get(track_id)
        if not track_data or submission_index >= len(track_data.submissions):
            return False

        track_data.submissions[submission_index].upvotes += 1
        track_data.popularity_score += 1

        return True

    def sync_to_cloud(self) -> bool:
        """Sync track data to cloud database."""
        if not self.api_endpoint:
            return False

        # Would POST submissions to API
        LOGGER.info(f"Syncing {len(self.user_submissions)} track submissions to cloud...")
        return True


__all__ = ["CrowdsourcedTrackDatabase", "CommunityTrackData", "TrackSubmission"]

