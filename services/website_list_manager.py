"""
Website List Manager
Manages a list of websites for the AI advisor to ingest or reference.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

LOGGER = logging.getLogger(__name__)


@dataclass
class WebsiteEntry:
    """Entry in the website list."""
    url: str
    name: str
    description: str = ""
    category: str = "forum"  # forum, documentation, blog, etc.
    enabled: bool = True
    last_ingested: Optional[float] = None
    ingest_count: int = 0
    chunks_added: int = 0
    added_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class WebsiteListManager:
    """
    Manages a list of websites for ingestion.
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize website list manager.
        
        Args:
            storage_path: Path to store website list
        """
        self.storage_path = storage_path or Path.home() / ".aituner" / "website_list.json"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.websites: Dict[str, WebsiteEntry] = {}
        self._load_list()
        
        # Add default websites if list is empty
        if not self.websites:
            self._add_default_websites()
        
        LOGGER.info(f"Website List Manager initialized with {len(self.websites)} websites")
    
    def _add_default_websites(self) -> None:
        """Add default websites to the list."""
        default_websites = [
            {
                "url": "https://www.xtremeracingtuning.com/forum/",
                "name": "Xtreme Racing Tuning Forum",
                "description": "Racing and tuning forum",
                "category": "forum"
            },
            {
                "url": "https://www.hpacademy.com/forum/",
                "name": "HP Academy Forum",
                "description": "High Performance Academy tuning forum",
                "category": "forum"
            },
            {
                "url": "https://forum.hptuners.com/",
                "name": "HP Tuners Forum",
                "description": "HP Tuners official forum",
                "category": "forum"
            },
            {
                "url": "https://www.jb4tech.com/",
                "name": "JB4 Tech",
                "description": "JB4 tuning and technical information",
                "category": "documentation"
            },
            {
                "url": "https://www.rctech.net/forum/",
                "name": "RC Tech Forum",
                "description": "RC Tech tuning and racing forum",
                "category": "forum"
            },
            {
                "url": "https://www.gtplanet.net/forum/board/gt5-tuning.236/",
                "name": "GTPlanet GT5 Tuning Forum",
                "description": "Gran Turismo 5 tuning forum",
                "category": "forum"
            },
            {
                "url": "https://www.dragstuff.com/forum/",
                "name": "Drag Stuff Forum",
                "description": "Drag racing and tuning forum",
                "category": "forum"
            },
            {
                "url": "https://www.bimmerforums.com/forum/forumdisplay.php?352-Engine-Tuning",
                "name": "BimmerForums Engine Tuning",
                "description": "BMW engine tuning forum",
                "category": "forum"
            },
            {
                "url": "https://www.torquecars.com/forums/",
                "name": "TorqueCars Forums",
                "description": "Car tuning and modification forums",
                "category": "forum"
            }
        ]
        
        for site in default_websites:
            entry = WebsiteEntry(
                url=site["url"],
                name=site["name"],
                description=site["description"],
                category=site["category"]
            )
            self.websites[site["url"]] = entry
        
        self._save_list()
        LOGGER.info("Added default websites to list")
    
    def add_website(
        self,
        url: str,
        name: str,
        description: str = "",
        category: str = "forum",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a website to the list.
        
        Args:
            url: Website URL
            name: Display name
            description: Description
            category: Category (forum, documentation, blog, etc.)
            metadata: Optional metadata
            
        Returns:
            True if added, False if already exists
        """
        if url in self.websites:
            LOGGER.warning(f"Website already in list: {url}")
            return False
        
        entry = WebsiteEntry(
            url=url,
            name=name,
            description=description,
            category=category,
            metadata=metadata or {}
        )
        
        self.websites[url] = entry
        self._save_list()
        LOGGER.info(f"Added website: {name} ({url})")
        return True
    
    def remove_website(self, url: str) -> bool:
        """
        Remove a website from the list.
        
        Args:
            url: Website URL to remove
            
        Returns:
            True if removed, False if not found
        """
        if url not in self.websites:
            LOGGER.warning(f"Website not in list: {url}")
            return False
        
        name = self.websites[url].name
        del self.websites[url]
        self._save_list()
        LOGGER.info(f"Removed website: {name} ({url})")
        return True
    
    def update_website(
        self,
        url: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        enabled: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a website entry.
        
        Args:
            url: Website URL
            name: New name (optional)
            description: New description (optional)
            category: New category (optional)
            enabled: Enable/disable (optional)
            metadata: New metadata (optional)
            
        Returns:
            True if updated, False if not found
        """
        if url not in self.websites:
            return False
        
        entry = self.websites[url]
        
        if name is not None:
            entry.name = name
        if description is not None:
            entry.description = description
        if category is not None:
            entry.category = category
        if enabled is not None:
            entry.enabled = enabled
        if metadata is not None:
            entry.metadata.update(metadata)
        
        self._save_list()
        LOGGER.info(f"Updated website: {url}")
        return True
    
    def get_websites(self, enabled_only: bool = False, category: Optional[str] = None) -> List[WebsiteEntry]:
        """
        Get list of websites.
        
        Args:
            enabled_only: Only return enabled websites
            category: Filter by category
            
        Returns:
            List of website entries
        """
        websites = list(self.websites.values())
        
        if enabled_only:
            websites = [w for w in websites if w.enabled]
        
        if category:
            websites = [w for w in websites if w.category == category]
        
        return websites
    
    def get_website(self, url: str) -> Optional[WebsiteEntry]:
        """
        Get a specific website entry.
        
        Args:
            url: Website URL
            
        Returns:
            Website entry or None
        """
        return self.websites.get(url)
    
    def mark_ingested(self, url: str, chunks_added: int = 0) -> None:
        """
        Mark a website as ingested.
        
        Args:
            url: Website URL
            chunks_added: Number of chunks added
        """
        if url in self.websites:
            entry = self.websites[url]
            entry.last_ingested = time.time()
            entry.ingest_count += 1
            entry.chunks_added += chunks_added
            self._save_list()
    
    def _save_list(self) -> None:
        """Save website list to disk."""
        try:
            data = {
                url: asdict(entry)
                for url, entry in self.websites.items()
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
        except Exception as e:
            LOGGER.error(f"Failed to save website list: {e}")
    
    def _load_list(self) -> None:
        """Load website list from disk."""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                self.websites = {
                    url: WebsiteEntry(**entry_data)
                    for url, entry_data in data.items()
                }
                
                LOGGER.info(f"Loaded {len(self.websites)} websites from disk")
        except Exception as e:
            LOGGER.warning(f"Failed to load website list: {e}")
            self.websites = {}
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the website list.
        
        Returns:
            Statistics dictionary
        """
        total = len(self.websites)
        enabled = sum(1 for w in self.websites.values() if w.enabled)
        categories = {}
        total_chunks = sum(w.chunks_added for w in self.websites.values())
        
        for entry in self.websites.values():
            categories[entry.category] = categories.get(entry.category, 0) + 1
        
        return {
            "total_websites": total,
            "enabled_websites": enabled,
            "categories": categories,
            "total_chunks_added": total_chunks,
            "websites_ingested": sum(1 for w in self.websites.values() if w.ingest_count > 0)
        }

