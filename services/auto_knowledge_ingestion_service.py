#!/usr/bin/env python3
"""
Automatic Knowledge Ingestion Service

Runs continuously in the background to:
1. Monitor knowledge gaps
2. Automatically search and ingest new knowledge
3. Update knowledge base from web searches
4. Run on a schedule without manual intervention
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import json

LOGGER = logging.getLogger(__name__)

try:
    from services.web_search_service import WebSearchService
    from services.vector_knowledge_store import VectorKnowledgeStore
    from services.knowledge_base_file_manager import KnowledgeBaseFileManager
    from services.auto_knowledge_populator import AutoKnowledgePopulator
    IMPORTS_AVAILABLE = True
except ImportError as e:
    LOGGER.warning(f"Some imports not available for auto ingestion: {e}")
    IMPORTS_AVAILABLE = False


class AutoKnowledgeIngestionService:
    """
    Automatic knowledge ingestion service that runs in the background.
    
    Features:
    - Continuous monitoring of knowledge gaps
    - Scheduled web searches for new knowledge
    - Automatic ingestion of relevant documents
    - Background operation without blocking main application
    """
    
    def __init__(
        self,
        vector_store: Optional[VectorKnowledgeStore] = None,
        kb_file_manager: Optional[KnowledgeBaseFileManager] = None,
        web_search: Optional[WebSearchService] = None,
        ingestion_interval_minutes: int = 60,  # Check every hour
        max_ingestions_per_day: int = 50,  # Limit to avoid rate limits
        enable_auto_population: bool = True,
    ):
        """Initialize the auto ingestion service."""
        self.vector_store = vector_store or (VectorKnowledgeStore() if IMPORTS_AVAILABLE else None)
        self.kb_file_manager = kb_file_manager or (KnowledgeBaseFileManager(auto_save=True) if IMPORTS_AVAILABLE else None)
        self.web_search = web_search or (WebSearchService(enable_search=True, prefer_google=True) if IMPORTS_AVAILABLE else None)
        
        self.ingestion_interval = ingestion_interval_minutes * 60  # Convert to seconds
        self.max_ingestions_per_day = max_ingestions_per_day
        self.enable_auto_population = enable_auto_population
        
        # State tracking
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.ingestion_count_today = 0
        self.last_ingestion_date = datetime.now().date()
        self.last_ingestion_time = None
        
        # Statistics
        self.stats = {
            "total_ingestions": 0,
            "total_chunks_added": 0,
            "last_ingestion": None,
            "errors": 0,
            "start_time": None,
        }
        
        # Search queries to automatically ingest
        self.auto_search_queries = [
            # Dyno
            "dyno manual tuning guide",
            "dynamometer calculation formulas",
            "SAE dyno correction factor",
            "virtual dyno calculation",
            "chassis dyno vs engine dyno",
            
            # EFI Tuning
            "EFI tuning guide",
            "electronic fuel injection tuning manual",
            "EFI fuel map tuning",
            "EFI sensor calibration",
            "injector sizing calculation",
            
            # Holley EFI
            "Holley EFI tuning manual",
            "Holley EFI software guide",
            "Holley EFI calibration",
            "Holley EFI Learn feature",
            
            # Nitrous
            "nitrous oxide tuning guide",
            "nitrous system installation",
            "progressive nitrous control",
            "nitrous safety features",
            
            # Turbo
            "turbocharger tuning guide",
            "turbo boost control tuning",
            "turbo sizing calculation",
            "turbo compressor map",
        ]
        
        # Load stats from file if exists
        self._load_stats()
    
    def start(self):
        """Start the auto ingestion service in background thread."""
        if not IMPORTS_AVAILABLE:
            LOGGER.warning("Auto ingestion service cannot start - required imports not available")
            return False
        
        if self.running:
            LOGGER.warning("Auto ingestion service is already running")
            return False
        
        self.running = True
        self.stats["start_time"] = datetime.now().isoformat()
        self.thread = threading.Thread(target=self._run_loop, daemon=True, name="AutoKnowledgeIngestion")
        self.thread.start()
        LOGGER.info("Auto knowledge ingestion service started")
        return True
    
    def stop(self):
        """Stop the auto ingestion service."""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
        self._save_stats()
        LOGGER.info("Auto knowledge ingestion service stopped")
    
    def _run_loop(self):
        """Main loop that runs continuously."""
        LOGGER.info(f"Auto ingestion service running (checking every {self.ingestion_interval/60:.0f} minutes)")
        
        while self.running:
            try:
                # Check if we should ingest today
                today = datetime.now().date()
                if today != self.last_ingestion_date:
                    # New day - reset counter
                    self.ingestion_count_today = 0
                    self.last_ingestion_date = today
                
                # Check if we've hit daily limit
                if self.ingestion_count_today < self.max_ingestions_per_day:
                    # Perform ingestion
                    self._perform_ingestion_cycle()
                else:
                    LOGGER.debug(f"Daily ingestion limit reached ({self.max_ingestions_per_day})")
                
                # Wait for next cycle
                time.sleep(self.ingestion_interval)
                
            except Exception as e:
                LOGGER.error(f"Error in auto ingestion loop: {e}", exc_info=True)
                self.stats["errors"] += 1
                time.sleep(60)  # Wait 1 minute before retrying
    
    def _perform_ingestion_cycle(self):
        """Perform one ingestion cycle - search and ingest knowledge."""
        try:
            LOGGER.info("Starting auto ingestion cycle...")
            
            # Select a query to search (rotate through list)
            query_index = self.stats["total_ingestions"] % len(self.auto_search_queries)
            query = self.auto_search_queries[query_index]
            
            LOGGER.info(f"Auto searching: {query}")
            
            # Search web
            if not self.web_search or not self.web_search.is_available():
                LOGGER.warning("Web search not available - skipping ingestion")
                return
            
            search_results = self.web_search.search(query, max_results=3)
            
            if not search_results or not search_results.results:
                LOGGER.debug(f"No results found for: {query}")
                return
            
            # Ingest results
            chunks_added = 0
            for result in search_results.results[:2]:  # Limit to 2 results per cycle
                try:
                    knowledge_text = f"{result.title}\n\n{result.snippet}\n\nSource: {result.url}"
                    
                    # Add to vector store
                    if self.vector_store:
                        doc_id = self.vector_store.add_knowledge(
                            text=knowledge_text,
                            metadata={
                                "source": "auto_ingestion",
                                "url": result.url,
                                "query": query,
                                "auto_populated": True,
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                    
                    # Add to KB file manager
                    if self.kb_file_manager:
                        self.kb_file_manager.add_entry(
                            question=f"Information about {query}",
                            answer=knowledge_text,
                            source="auto_ingestion",
                            url=result.url,
                            title=result.title,
                            confidence=0.7,
                            topic="Auto-Ingested",
                            keywords=query.split(),
                            verified=False
                        )
                    
                    chunks_added += 1
                    LOGGER.debug(f"  ✓ Ingested: {result.title[:60]}...")
                    
                except Exception as e:
                    LOGGER.error(f"Failed to ingest result: {e}")
            
            # Update statistics
            self.ingestion_count_today += 1
            self.stats["total_ingestions"] += 1
            self.stats["total_chunks_added"] += chunks_added
            self.stats["last_ingestion"] = datetime.now().isoformat()
            self.last_ingestion_time = datetime.now()
            
            LOGGER.info(f"Auto ingestion cycle complete: {chunks_added} chunks added")
            
            # Save stats periodically
            if self.stats["total_ingestions"] % 10 == 0:
                self._save_stats()
            
        except Exception as e:
            LOGGER.error(f"Error in ingestion cycle: {e}", exc_info=True)
            self.stats["errors"] += 1
    
    def _load_stats(self):
        """Load statistics from file."""
        stats_file = Path(__file__).parent.parent / "data" / "auto_ingestion_stats.json"
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    self.stats.update(json.load(f))
            except Exception as e:
                LOGGER.warning(f"Failed to load ingestion stats: {e}")
    
    def _save_stats(self):
        """Save statistics to file."""
        stats_file = Path(__file__).parent.parent / "data" / "auto_ingestion_stats.json"
        stats_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            LOGGER.warning(f"Failed to save ingestion stats: {e}")
    
    def get_stats(self) -> Dict:
        """Get current statistics."""
        return {
            **self.stats,
            "running": self.running,
            "ingestions_today": self.ingestion_count_today,
            "max_per_day": self.max_ingestions_per_day,
            "next_ingestion_in_minutes": (
                (self.ingestion_interval - (time.time() - (self.last_ingestion_time.timestamp() if self.last_ingestion_time else 0))) / 60
                if self.last_ingestion_time else 0
            ),
        }
    
    def trigger_manual_ingestion(self, query: Optional[str] = None):
        """Manually trigger an ingestion cycle (for testing or on-demand)."""
        if not self.running:
            LOGGER.warning("Cannot trigger ingestion - service not running")
            return False
        
        if query:
            # Temporarily add query to list
            self.auto_search_queries.insert(0, query)
        
        # Trigger ingestion in background
        threading.Thread(target=self._perform_ingestion_cycle, daemon=True).start()
        return True


# Global instance (singleton pattern)
_global_service: Optional[AutoKnowledgeIngestionService] = None


def get_auto_ingestion_service() -> Optional[AutoKnowledgeIngestionService]:
    """Get or create the global auto ingestion service instance."""
    global _global_service
    if _global_service is None:
        _global_service = AutoKnowledgeIngestionService()
    return _global_service


def start_auto_ingestion():
    """Start the global auto ingestion service."""
    service = get_auto_ingestion_service()
    if service:
        return service.start()
    return False


def stop_auto_ingestion():
    """Stop the global auto ingestion service."""
    global _global_service
    if _global_service:
        _global_service.stop()


if __name__ == "__main__":
    # Test the service
    logging.basicConfig(level=logging.INFO)
    
    service = AutoKnowledgeIngestionService(ingestion_interval_minutes=5)  # Test with 5 min interval
    service.start()
    
    try:
        # Run for a bit
        time.sleep(300)  # 5 minutes
    except KeyboardInterrupt:
        pass
    finally:
        service.stop()
        print("\nStats:", json.dumps(service.get_stats(), indent=2))

