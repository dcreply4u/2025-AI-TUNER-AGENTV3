"""
Log Notes and Logbook Manager
Contextual notes and logbook for data logs.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger(__name__)


@dataclass
class LogNote:
    """Note attached to a log file."""
    note_id: str
    log_file: str
    timestamp: float
    position: Optional[float] = None  # Time or distance position
    note_text: str = ""
    category: str = "general"  # tune, weather, track, issue, etc.
    tags: List[str] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)  # File paths


@dataclass
class LogbookEntry:
    """Logbook entry for a session."""
    entry_id: str
    session_date: float
    vehicle: str
    track: Optional[str] = None
    weather: Dict[str, Any] = field(default_factory=dict)
    tune_changes: List[str] = field(default_factory=list)
    results: Dict[str, float] = field(default_factory=dict)
    notes: str = ""
    log_files: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


class LogNotesManager:
    """
    Manager for log notes and logbook.
    
    Features:
    - Attach notes to log files
    - Position-specific notes
    - Categorization and tagging
    - Logbook entries
    - Search and filter
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize log notes manager."""
        self.data_dir = data_dir or Path("data/log_notes")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.notes: Dict[str, LogNote] = {}
        self.logbook: List[LogbookEntry] = []
        
        self._load_data()
    
    def add_note(
        self,
        log_file: str,
        note_text: str,
        position: Optional[float] = None,
        category: str = "general",
        tags: Optional[List[str]] = None,
    ) -> LogNote:
        """
        Add note to log file.
        
        Args:
            log_file: Log file path
            note_text: Note text
            position: Optional position (time/distance)
            category: Note category
            tags: Optional tags
        
        Returns:
            Created LogNote
        """
        note_id = f"note_{int(time.time())}"
        
        note = LogNote(
            note_id=note_id,
            log_file=log_file,
            timestamp=time.time(),
            position=position,
            note_text=note_text,
            category=category,
            tags=tags or [],
        )
        
        self.notes[note_id] = note
        self._save_notes()
        
        LOGGER.info("Added note to log: %s", log_file)
        return note
    
    def get_notes(self, log_file: Optional[str] = None) -> List[LogNote]:
        """
        Get notes.
        
        Args:
            log_file: Optional log file filter
        
        Returns:
            List of notes
        """
        if log_file:
            return [n for n in self.notes.values() if n.log_file == log_file]
        return list(self.notes.values())
    
    def get_notes_at_position(
        self,
        log_file: str,
        position: float,
        tolerance: float = 1.0,
    ) -> List[LogNote]:
        """
        Get notes at specific position.
        
        Args:
            log_file: Log file path
            position: Position (time/distance)
            tolerance: Position tolerance
        
        Returns:
            List of notes at position
        """
        return [
            n for n in self.notes.values()
            if n.log_file == log_file and
            n.position is not None and
            abs(n.position - position) <= tolerance
        ]
    
    def add_logbook_entry(
        self,
        vehicle: str,
        track: Optional[str] = None,
        weather: Optional[Dict[str, Any]] = None,
        tune_changes: Optional[List[str]] = None,
        results: Optional[Dict[str, float]] = None,
        notes: str = "",
        log_files: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> LogbookEntry:
        """
        Add logbook entry.
        
        Args:
            vehicle: Vehicle name
            track: Track name
            weather: Weather conditions
            tune_changes: List of tune changes
            results: Performance results
            notes: Session notes
            log_files: Associated log files
            tags: Tags
        
        Returns:
            Created LogbookEntry
        """
        entry_id = f"entry_{int(time.time())}"
        
        entry = LogbookEntry(
            entry_id=entry_id,
            session_date=time.time(),
            vehicle=vehicle,
            track=track,
            weather=weather or {},
            tune_changes=tune_changes or [],
            results=results or {},
            notes=notes,
            log_files=log_files or [],
            tags=tags or [],
        )
        
        self.logbook.append(entry)
        self._save_logbook()
        
        LOGGER.info("Added logbook entry: %s", vehicle)
        return entry
    
    def search_logbook(
        self,
        vehicle: Optional[str] = None,
        track: Optional[str] = None,
        date_from: Optional[float] = None,
        date_to: Optional[float] = None,
        tags: Optional[List[str]] = None,
    ) -> List[LogbookEntry]:
        """
        Search logbook.
        
        Args:
            vehicle: Vehicle filter
            track: Track filter
            date_from: Start date
            date_to: End date
            tags: Tag filters
        
        Returns:
            List of matching entries
        """
        results = self.logbook.copy()
        
        if vehicle:
            results = [e for e in results if e.vehicle == vehicle]
        
        if track:
            results = [e for e in results if e.track == track]
        
        if date_from:
            results = [e for e in results if e.session_date >= date_from]
        
        if date_to:
            results = [e for e in results if e.session_date <= date_to]
        
        if tags:
            results = [
                e for e in results
                if any(tag in e.tags for tag in tags)
            ]
        
        return sorted(results, key=lambda e: e.session_date, reverse=True)
    
    def _save_notes(self) -> None:
        """Save notes to disk."""
        try:
            notes_file = self.data_dir / "notes.json"
            with open(notes_file, 'w') as f:
                json.dump({
                    note_id: {
                        "note_id": n.note_id,
                        "log_file": n.log_file,
                        "timestamp": n.timestamp,
                        "position": n.position,
                        "note_text": n.note_text,
                        "category": n.category,
                        "tags": n.tags,
                        "attachments": n.attachments,
                    }
                    for note_id, n in self.notes.items()
                }, f, indent=2)
        except Exception as e:
            LOGGER.error("Failed to save notes: %s", e)
    
    def _save_logbook(self) -> None:
        """Save logbook to disk."""
        try:
            logbook_file = self.data_dir / "logbook.json"
            with open(logbook_file, 'w') as f:
                json.dump([
                    {
                        "entry_id": e.entry_id,
                        "session_date": e.session_date,
                        "vehicle": e.vehicle,
                        "track": e.track,
                        "weather": e.weather,
                        "tune_changes": e.tune_changes,
                        "results": e.results,
                        "notes": e.notes,
                        "log_files": e.log_files,
                        "tags": e.tags,
                    }
                    for e in self.logbook
                ], f, indent=2)
        except Exception as e:
            LOGGER.error("Failed to save logbook: %s", e)
    
    def _load_data(self) -> None:
        """Load notes and logbook from disk."""
        try:
            # Load notes
            notes_file = self.data_dir / "notes.json"
            if notes_file.exists():
                with open(notes_file, 'r') as f:
                    data = json.load(f)
                    for note_id, note_data in data.items():
                        self.notes[note_id] = LogNote(
                            note_id=note_data["note_id"],
                            log_file=note_data["log_file"],
                            timestamp=note_data["timestamp"],
                            position=note_data.get("position"),
                            note_text=note_data["note_text"],
                            category=note_data.get("category", "general"),
                            tags=note_data.get("tags", []),
                            attachments=note_data.get("attachments", []),
                        )
            
            # Load logbook
            logbook_file = self.data_dir / "logbook.json"
            if logbook_file.exists():
                with open(logbook_file, 'r') as f:
                    data = json.load(f)
                    for entry_data in data:
                        self.logbook.append(LogbookEntry(
                            entry_id=entry_data["entry_id"],
                            session_date=entry_data["session_date"],
                            vehicle=entry_data["vehicle"],
                            track=entry_data.get("track"),
                            weather=entry_data.get("weather", {}),
                            tune_changes=entry_data.get("tune_changes", []),
                            results=entry_data.get("results", {}),
                            notes=entry_data.get("notes", ""),
                            log_files=entry_data.get("log_files", []),
                            tags=entry_data.get("tags", []),
                        ))
        except Exception as e:
            LOGGER.error("Failed to load data: %s", e)


