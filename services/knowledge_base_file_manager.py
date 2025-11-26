"""
Knowledge Base File Manager
Manages human-readable KB files for learned knowledge.

Allows users to review, edit, and train the AI advisor by managing KB files.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

LOGGER = logging.getLogger(__name__)


@dataclass
class KBEntry:
    """A knowledge base entry."""
    question: str
    answer: str
    source: str  # "web", "forum", "user", "auto_populate"
    url: Optional[str] = None
    title: Optional[str] = None
    confidence: float = 0.0
    keywords: List[str] = None
    topic: str = "General"
    created_at: str = None
    updated_at: str = None
    verified: bool = False  # User verified this is correct
    user_edited: bool = False  # User manually edited this
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()


class KnowledgeBaseFileManager:
    """
    Manages human-readable KB files for learned knowledge.
    
    Features:
    - Save learned knowledge to JSON files
    - Load knowledge from KB files
    - User can review/edit KB files
    - Automatic organization by topic
    - Merge with vector store
    """
    
    def __init__(
        self,
        kb_directory: Optional[str] = None,
        auto_save: bool = True
    ):
        """
        Initialize KB file manager.
        
        Args:
            kb_directory: Directory to store KB files (default: ~/.aituner/kb)
            auto_save: Automatically save when entries are added
        """
        self.kb_directory = Path(kb_directory) if kb_directory else Path.home() / ".aituner" / "kb"
        self.kb_directory.mkdir(parents=True, exist_ok=True)
        self.auto_save = auto_save
        
        # In-memory cache
        self.entries: Dict[str, KBEntry] = {}  # key: question (normalized)
        self.entries_by_topic: Dict[str, List[str]] = {}  # topic -> [question keys]
        
        # Load existing KB files
        self._load_all_kb_files()
        
        LOGGER.info(f"KB File Manager initialized with {len(self.entries)} entries")
    
    def _normalize_question(self, question: str) -> str:
        """Normalize question for use as key."""
        return question.lower().strip()
    
    def _get_kb_file_path(self, topic: str) -> Path:
        """Get KB file path for a topic."""
        # Sanitize topic name for filename
        safe_topic = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in topic)
        safe_topic = safe_topic.replace(' ', '_').lower()
        return self.kb_directory / f"{safe_topic}.json"
    
    def add_entry(
        self,
        question: str,
        answer: str,
        source: str = "auto_populate",
        url: Optional[str] = None,
        title: Optional[str] = None,
        confidence: float = 0.0,
        keywords: Optional[List[str]] = None,
        topic: str = "General",
        verified: bool = False
    ) -> str:
        """
        Add or update a KB entry.
        
        Args:
            question: User question
            answer: Answer text
            source: Source of knowledge ("web", "forum", "user", "auto_populate")
            url: Source URL (if from web/forum)
            title: Source title
            confidence: Confidence score
            keywords: Keywords for search
            topic: Topic category
            verified: User verified this is correct
            
        Returns:
            Entry key (normalized question)
        """
        key = self._normalize_question(question)
        
        # Check if entry exists
        if key in self.entries:
            # Update existing entry
            entry = self.entries[key]
            entry.answer = answer
            entry.source = source
            entry.url = url or entry.url
            entry.title = title or entry.title
            entry.confidence = max(confidence, entry.confidence)
            entry.keywords = keywords or entry.keywords
            entry.topic = topic
            entry.updated_at = datetime.now().isoformat()
            entry.verified = verified or entry.verified
            
            # Move to new topic if changed
            if entry.topic != topic:
                self._remove_from_topic(entry.topic, key)
                self._add_to_topic(topic, key)
                entry.topic = topic
        else:
            # Create new entry
            entry = KBEntry(
                question=question,
                answer=answer,
                source=source,
                url=url,
                title=title,
                confidence=confidence,
                keywords=keywords or [],
                topic=topic,
                verified=verified
            )
            self.entries[key] = entry
            self._add_to_topic(topic, key)
        
        # Auto-save if enabled
        if self.auto_save:
            self._save_topic_file(topic)
        
        LOGGER.info(f"Added KB entry: {question[:50]}... (topic: {topic})")
        return key
    
    def _add_to_topic(self, topic: str, key: str) -> None:
        """Add entry key to topic index."""
        if topic not in self.entries_by_topic:
            self.entries_by_topic[topic] = []
        if key not in self.entries_by_topic[topic]:
            self.entries_by_topic[topic].append(key)
    
    def _remove_from_topic(self, topic: str, key: str) -> None:
        """Remove entry key from topic index."""
        if topic in self.entries_by_topic:
            if key in self.entries_by_topic[topic]:
                self.entries_by_topic[topic].remove(key)
            if not self.entries_by_topic[topic]:
                del self.entries_by_topic[topic]
    
    def get_entry(self, question: str) -> Optional[KBEntry]:
        """Get KB entry by question."""
        key = self._normalize_question(question)
        return self.entries.get(key)
    
    def search_entries(
        self,
        query: str,
        topic: Optional[str] = None,
        min_confidence: float = 0.0
    ) -> List[KBEntry]:
        """
        Search KB entries.
        
        Args:
            query: Search query
            topic: Filter by topic (optional)
            min_confidence: Minimum confidence
            
        Returns:
            List of matching entries
        """
        query_lower = query.lower()
        results = []
        
        # Get entries to search
        if topic:
            keys = self.entries_by_topic.get(topic, [])
        else:
            keys = list(self.entries.keys())
        
        # Search
        for key in keys:
            entry = self.entries[key]
            
            # Skip if confidence too low
            if entry.confidence < min_confidence:
                continue
            
            # Check if query matches
            if (query_lower in entry.question.lower() or
                query_lower in entry.answer.lower() or
                any(query_lower in kw.lower() for kw in entry.keywords)):
                results.append(entry)
        
        # Sort by confidence (highest first)
        results.sort(key=lambda e: e.confidence, reverse=True)
        return results
    
    def get_entries_by_topic(self, topic: str) -> List[KBEntry]:
        """Get all entries for a topic."""
        keys = self.entries_by_topic.get(topic, [])
        return [self.entries[key] for key in keys]
    
    def get_all_topics(self) -> List[str]:
        """Get all topics."""
        return sorted(self.entries_by_topic.keys())
    
    def verify_entry(self, question: str, verified: bool = True) -> bool:
        """
        Mark entry as verified by user.
        
        Args:
            question: Question
            verified: Verification status
            
        Returns:
            True if entry found and updated
        """
        entry = self.get_entry(question)
        if entry:
            entry.verified = verified
            entry.updated_at = datetime.now().isoformat()
            if self.auto_save:
                self._save_topic_file(entry.topic)
            return True
        return False
    
    def edit_entry(
        self,
        question: str,
        answer: Optional[str] = None,
        topic: Optional[str] = None,
        keywords: Optional[List[str]] = None
    ) -> bool:
        """
        Manually edit an entry (marks as user_edited).
        
        Args:
            question: Question
            answer: New answer (optional)
            topic: New topic (optional)
            keywords: New keywords (optional)
            
        Returns:
            True if entry found and updated
        """
        entry = self.get_entry(question)
        if not entry:
            return False
        
        if answer:
            entry.answer = answer
        if topic and topic != entry.topic:
            self._remove_from_topic(entry.topic, self._normalize_question(question))
            self._add_to_topic(topic, self._normalize_question(question))
            entry.topic = topic
        if keywords:
            entry.keywords = keywords
        
        entry.user_edited = True
        entry.verified = True
        entry.updated_at = datetime.now().isoformat()
        
        if self.auto_save:
            self._save_topic_file(entry.topic)
        
        LOGGER.info(f"User edited KB entry: {question[:50]}...")
        return True
    
    def delete_entry(self, question: str) -> bool:
        """
        Delete an entry.
        
        Args:
            question: Question to delete
            
        Returns:
            True if entry found and deleted
        """
        key = self._normalize_question(question)
        if key not in self.entries:
            return False
        
        entry = self.entries[key]
        topic = entry.topic
        
        # Remove from indexes
        del self.entries[key]
        self._remove_from_topic(topic, key)
        
        # Save updated topic file
        if self.auto_save:
            self._save_topic_file(topic)
        
        LOGGER.info(f"Deleted KB entry: {question[:50]}...")
        return True
    
    def _save_topic_file(self, topic: str) -> None:
        """Save all entries for a topic to file."""
        kb_file = self._get_kb_file_path(topic)
        entries = self.get_entries_by_topic(topic)
        
        # Convert to dict for JSON
        data = {
            "topic": topic,
            "updated_at": datetime.now().isoformat(),
            "entries": [asdict(entry) for entry in entries]
        }
        
        try:
            with open(kb_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            LOGGER.debug(f"Saved KB file: {kb_file}")
        except Exception as e:
            LOGGER.error(f"Failed to save KB file {kb_file}: {e}")
    
    def _load_all_kb_files(self) -> None:
        """Load all KB files from directory."""
        if not self.kb_directory.exists():
            return
        
        for kb_file in self.kb_directory.glob("*.json"):
            try:
                with open(kb_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                topic = data.get("topic", "General")
                entries_data = data.get("entries", [])
                
                for entry_data in entries_data:
                    entry = KBEntry(**entry_data)
                    key = self._normalize_question(entry.question)
                    self.entries[key] = entry
                    self._add_to_topic(topic, key)
                
                LOGGER.debug(f"Loaded {len(entries_data)} entries from {kb_file.name}")
            except Exception as e:
                LOGGER.warning(f"Failed to load KB file {kb_file}: {e}")
    
    def save_all(self) -> None:
        """Save all KB files."""
        for topic in self.entries_by_topic.keys():
            self._save_topic_file(topic)
        LOGGER.info("Saved all KB files")
    
    def export_to_vector_store(self, vector_store) -> int:
        """
        Export KB entries to vector store.
        
        Args:
            vector_store: VectorKnowledgeStore instance
            
        Returns:
            Number of entries exported
        """
        exported = 0
        for entry in self.entries.values():
            try:
                # Combine question and answer for better search
                text = f"Q: {entry.question}\nA: {entry.answer}"
                
                metadata = {
                    "source": "kb_file",
                    "topic": entry.topic,
                    "question": entry.question,
                    "url": entry.url or "",
                    "title": entry.title or "",
                    "verified": entry.verified,
                    "user_edited": entry.user_edited,
                    "confidence": entry.confidence,
                    "keywords": ",".join(entry.keywords)
                }
                
                vector_store.add_knowledge(text, metadata=metadata)
                exported += 1
            except Exception as e:
                LOGGER.warning(f"Failed to export entry to vector store: {e}")
        
        LOGGER.info(f"Exported {exported} KB entries to vector store")
        return exported
    
    def get_stats(self) -> Dict[str, Any]:
        """Get KB statistics."""
        total = len(self.entries)
        verified = sum(1 for e in self.entries.values() if e.verified)
        user_edited = sum(1 for e in self.entries.values() if e.user_edited)
        
        by_source = {}
        for entry in self.entries.values():
            source = entry.source
            by_source[source] = by_source.get(source, 0) + 1
        
        return {
            "total_entries": total,
            "topics": len(self.entries_by_topic),
            "verified_entries": verified,
            "user_edited_entries": user_edited,
            "entries_by_source": by_source,
            "entries_by_topic": {
                topic: len(keys) for topic, keys in self.entries_by_topic.items()
            }
        }


__all__ = ["KnowledgeBaseFileManager", "KBEntry"]

