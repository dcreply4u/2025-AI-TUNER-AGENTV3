"""
Session Management Service

Manages named sessions with metadata, comparison tools, and export/import.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger(__name__)


@dataclass
class SessionMetadata:
    """Session metadata and tags."""

    session_id: str
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None  # seconds
    track_name: Optional[str] = None
    weather: Optional[str] = None  # "sunny", "cloudy", "rain", etc.
    temperature: Optional[float] = None  # Fahrenheit
    humidity: Optional[float] = None  # Percent
    vehicle_config: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    lap_count: int = 0
    best_lap_time: Optional[float] = None
    total_distance: float = 0.0  # miles
    max_speed: float = 0.0  # mph
    avg_speed: float = 0.0  # mph
    telemetry_file: Optional[str] = None
    video_files: List[str] = field(default_factory=list)
    gps_file: Optional[str] = None
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionComparison:
    """Comparison between two sessions."""

    session1: SessionMetadata
    session2: SessionMetadata
    lap_time_diff: Optional[float] = None  # session2 - session1
    speed_diff: Optional[float] = None  # session2 - session1
    distance_diff: Optional[float] = None  # session2 - session1
    differences: Dict[str, Any] = field(default_factory=dict)


class SessionManager:
    """Manages named sessions with metadata, comparison, and export/import."""

    def __init__(self, sessions_dir: str | Path = "sessions") -> None:
        """
        Initialize session manager.

        Args:
            sessions_dir: Directory to store session data
        """
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.sessions_dir / "sessions.json"

        self.sessions: Dict[str, SessionMetadata] = {}
        self.current_session: Optional[SessionMetadata] = None

        # Load existing sessions
        self._load_sessions()

    def create_session(
        self,
        name: str,
        track_name: Optional[str] = None,
        weather: Optional[str] = None,
        temperature: Optional[float] = None,
        humidity: Optional[float] = None,
        vehicle_config: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> SessionMetadata:
        """
        Create a new session.

        Args:
            name: Session name
            track_name: Track name
            weather: Weather conditions
            temperature: Temperature (Fahrenheit)
            humidity: Humidity (percent)
            vehicle_config: Vehicle configuration dict
            notes: Session notes
            tags: List of tags

        Returns:
            Created session metadata
        """
        session_id = f"session_{int(time.time())}"
        session = SessionMetadata(
            session_id=session_id,
            name=name,
            start_time=time.time(),
            track_name=track_name,
            weather=weather,
            temperature=temperature,
            humidity=humidity,
            vehicle_config=vehicle_config,
            notes=notes,
            tags=tags or [],
        )

        self.sessions[session_id] = session
        self.current_session = session
        self._save_sessions()

        LOGGER.info("Created session: %s (ID: %s)", name, session_id)
        return session

    def end_session(self, session_id: Optional[str] = None) -> Optional[SessionMetadata]:
        """
        End a session.

        Args:
            session_id: Session ID (None = current session)

        Returns:
            Ended session metadata
        """
        if session_id is None:
            session = self.current_session
        else:
            session = self.sessions.get(session_id)

        if not session:
            LOGGER.warning("Session not found: %s", session_id)
            return None

        session.end_time = time.time()
        session.duration = session.end_time - session.start_time

        self._save_sessions()
        LOGGER.info("Ended session: %s (duration: %.2f seconds)", session.name, session.duration)

        if session == self.current_session:
            self.current_session = None

        return session

    def update_session(
        self,
        session_id: str,
        **updates: Any,
    ) -> Optional[SessionMetadata]:
        """
        Update session metadata.

        Args:
            session_id: Session ID
            **updates: Fields to update

        Returns:
            Updated session metadata
        """
        session = self.sessions.get(session_id)
        if not session:
            LOGGER.warning("Session not found: %s", session_id)
            return None

        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)

        self._save_sessions()
        return session

    def get_session(self, session_id: str) -> Optional[SessionMetadata]:
        """Get session by ID."""
        return self.sessions.get(session_id)

    def get_current_session(self) -> Optional[SessionMetadata]:
        """Get current active session."""
        return self.current_session

    def list_sessions(
        self,
        track_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        start_date: Optional[float] = None,
        end_date: Optional[float] = None,
    ) -> List[SessionMetadata]:
        """
        List sessions with optional filters.

        Args:
            track_name: Filter by track name
            tags: Filter by tags (any match)
            start_date: Filter by start date (timestamp)
            end_date: Filter by end date (timestamp)

        Returns:
            List of matching sessions
        """
        sessions = list(self.sessions.values())

        if track_name:
            sessions = [s for s in sessions if s.track_name == track_name]

        if tags:
            sessions = [s for s in sessions if any(tag in s.tags for tag in tags)]

        if start_date:
            sessions = [s for s in sessions if s.start_time >= start_date]

        if end_date:
            sessions = [s for s in sessions if s.start_time <= end_date]

        # Sort by start time (newest first)
        sessions.sort(key=lambda s: s.start_time, reverse=True)

        return sessions

    def compare_sessions(self, session_id1: str, session_id2: str) -> Optional[SessionComparison]:
        """
        Compare two sessions.

        Args:
            session_id1: First session ID
            session_id2: Second session ID

        Returns:
            Session comparison
        """
        session1 = self.sessions.get(session_id1)
        session2 = self.sessions.get(session_id2)

        if not session1 or not session2:
            LOGGER.warning("One or both sessions not found")
            return None

        comparison = SessionComparison(session1=session1, session2=session2)

        # Compare lap times
        if session1.best_lap_time and session2.best_lap_time:
            comparison.lap_time_diff = session2.best_lap_time - session1.best_lap_time

        # Compare speeds
        if session1.max_speed and session2.max_speed:
            comparison.speed_diff = session2.max_speed - session1.max_speed

        # Compare distances
        if session1.total_distance and session2.total_distance:
            comparison.distance_diff = session2.total_distance - session1.total_distance

        # Find all differences
        comparison.differences = {}
        for key in ["lap_count", "best_lap_time", "max_speed", "avg_speed", "total_distance"]:
            val1 = getattr(session1, key)
            val2 = getattr(session2, key)
            if val1 is not None and val2 is not None:
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    comparison.differences[key] = val2 - val1

        return comparison

    def export_session(self, session_id: str, output_path: Optional[Path] = None) -> Path:
        """
        Export session to JSON file.

        Args:
            session_id: Session ID
            output_path: Output file path (auto-generated if None)

        Returns:
            Path to exported file
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if output_path is None:
            safe_name = "".join(c for c in session.name if c.isalnum() or c in (" ", "-", "_"))
            output_path = self.sessions_dir / f"{safe_name}_{session_id}.json"

        export_data = {
            "session": asdict(session),
            "export_date": datetime.now().isoformat(),
            "version": "1.0",
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, default=str)

        LOGGER.info("Exported session %s to %s", session_id, output_path)
        return output_path

    def import_session(self, file_path: Path | str) -> SessionMetadata:
        """
        Import session from JSON file.

        Args:
            file_path: Path to session JSON file

        Returns:
            Imported session metadata
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Session file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        session_data = data.get("session", data)
        session = SessionMetadata(**session_data)

        # Use existing ID or generate new one
        if session.session_id in self.sessions:
            session.session_id = f"session_{int(time.time())}"

        self.sessions[session.session_id] = session
        self._save_sessions()

        LOGGER.info("Imported session: %s (ID: %s)", session.name, session.session_id)
        return session

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session ID

        Returns:
            True if deleted successfully
        """
        if session_id not in self.sessions:
            return False

        del self.sessions[session_id]
        self._save_sessions()

        LOGGER.info("Deleted session: %s", session_id)
        return True

    def _load_sessions(self) -> None:
        """Load sessions from disk."""
        if not self.metadata_file.exists():
            return

        try:
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for session_data in data.get("sessions", []):
                session = SessionMetadata(**session_data)
                self.sessions[session.session_id] = session

            LOGGER.info("Loaded %d sessions", len(self.sessions))
        except Exception as e:
            LOGGER.error("Error loading sessions: %s", e)

    def _save_sessions(self) -> None:
        """Save sessions to disk."""
        try:
            data = {
                "sessions": [asdict(session) for session in self.sessions.values()],
                "last_updated": datetime.now().isoformat(),
            }

            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            LOGGER.error("Error saving sessions: %s", e)


__all__ = ["SessionManager", "SessionMetadata", "SessionComparison"]









