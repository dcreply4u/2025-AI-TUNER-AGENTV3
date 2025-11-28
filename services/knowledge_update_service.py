"""
Unified Knowledge Update Service
Manages all AI Advisor knowledge and content updates in a single service.

This service:
- Runs automatically on startup
- Manages auto-knowledge ingestion
- Handles auto-population when confidence is low
- Coordinates between ingestion and population services
- Provides unified statistics and control
"""

from __future__ import annotations

import logging
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

LOGGER = logging.getLogger(__name__)

# Import dependencies
try:
    from services.auto_knowledge_ingestion_service import (
        AutoKnowledgeIngestionService,
        get_auto_ingestion_service,
        start_auto_ingestion,
    )
    from services.auto_knowledge_populator import AutoKnowledgePopulator
    from services.ai_advisor_learning_system import AILearningSystem
    from services.website_ingestion_service import WebsiteIngestionService
    from services.knowledge_base_manager import KnowledgeBaseManager
    from services.web_search_service import WebSearchService
    from services.knowledge_base_file_manager import KnowledgeBaseFileManager
    SERVICES_AVAILABLE = True
except ImportError as e:
    LOGGER.warning(f"Some knowledge update services not available: {e}")
    SERVICES_AVAILABLE = False
    AutoKnowledgeIngestionService = None
    AutoKnowledgePopulator = None
    AILearningSystem = None
    WebsiteIngestionService = None
    KnowledgeBaseManager = None
    WebSearchService = None
    KnowledgeBaseFileManager = None


class KnowledgeUpdateService:
    """
    Unified service for managing AI Advisor knowledge updates.
    
    Features:
    - Automatic knowledge ingestion on schedule
    - Auto-population when confidence is low
    - Unified statistics and monitoring
    - Background operation without blocking
    """
    
    def __init__(
        self,
        enable_auto_ingestion: bool = True,
        enable_auto_population: bool = True,
        ingestion_interval_minutes: int = 60,
        auto_start: bool = True,
    ):
        """
        Initialize the knowledge update service.
        
        Args:
            enable_auto_ingestion: Enable automatic knowledge ingestion
            enable_auto_population: Enable auto-population on low confidence
            ingestion_interval_minutes: Minutes between ingestion cycles
            auto_start: Automatically start service on initialization
        """
        if not SERVICES_AVAILABLE:
            LOGGER.warning("Knowledge update services not fully available")
            self.available = False
            return
            
        self.available = True
        self.enable_auto_ingestion = enable_auto_ingestion
        self.enable_auto_population = enable_auto_population
        
        # Initialize ingestion service
        self.ingestion_service: Optional[AutoKnowledgeIngestionService] = None
        if enable_auto_ingestion:
            try:
                self.ingestion_service = get_auto_ingestion_service()
                if self.ingestion_service:
                    # Update interval if needed
                    self.ingestion_service.ingestion_interval = ingestion_interval_minutes * 60
            except Exception as e:
                LOGGER.warning(f"Failed to initialize ingestion service: {e}")
                self.ingestion_service = None
        
        # Initialize auto-populator
        self.auto_populator: Optional[AutoKnowledgePopulator] = None
        if enable_auto_population:
            try:
                # Get dependencies for auto-populator
                learning_system = AILearningSystem() if AILearningSystem else None
                website_ingestion = WebsiteIngestionService() if WebsiteIngestionService else None
                kb_manager = KnowledgeBaseManager() if KnowledgeBaseManager else None
                web_search = WebSearchService(enable_search=True, prefer_google=True) if WebSearchService else None
                kb_file_manager = KnowledgeBaseFileManager(auto_save=True) if KnowledgeBaseFileManager else None
                
                self.auto_populator = AutoKnowledgePopulator(
                    learning_system=learning_system,
                    website_ingestion_service=website_ingestion,
                    knowledge_base_manager=kb_manager,
                    web_search_service=web_search,
                    kb_file_manager=kb_file_manager,
                    auto_populate_enabled=True,
                    confidence_threshold=0.5,
                )
            except Exception as e:
                LOGGER.warning(f"Failed to initialize auto-populator: {e}")
                self.auto_populator = None
        
        # Service state
        self.running = False
        self.start_time: Optional[datetime] = None
        
        # Statistics
        self.stats = {
            "service_started": None,
            "ingestion_enabled": enable_auto_ingestion,
            "auto_population_enabled": enable_auto_population,
            "ingestion_stats": {},
            "auto_population_stats": {},
            "total_updates": 0,
        }
        
        # Auto-start if requested
        if auto_start:
            self.start()
    
    def start(self) -> bool:
        """Start the knowledge update service."""
        if not self.available:
            LOGGER.warning("Knowledge update service not available")
            return False
            
        if self.running:
            LOGGER.info("Knowledge update service already running")
            return True
        
        try:
            # Start ingestion service
            if self.enable_auto_ingestion and self.ingestion_service:
                if start_auto_ingestion():
                    LOGGER.info("✅ Auto knowledge ingestion service started")
                else:
                    LOGGER.warning("Failed to start auto ingestion service")
            
            self.running = True
            self.start_time = datetime.now()
            self.stats["service_started"] = self.start_time.isoformat()
            
            LOGGER.info("🚀 Knowledge Update Service started successfully")
            return True
            
        except Exception as e:
            LOGGER.error(f"Failed to start knowledge update service: {e}", exc_info=True)
            return False
    
    def stop(self) -> None:
        """Stop the knowledge update service."""
        if not self.running:
            return
            
        try:
            # Stop ingestion service
            if self.ingestion_service:
                try:
                    from services.auto_knowledge_ingestion_service import stop_auto_ingestion
                    stop_auto_ingestion()
                except Exception as e:
                    LOGGER.warning(f"Error stopping ingestion service: {e}")
            
            self.running = False
            LOGGER.info("Knowledge Update Service stopped")
            
        except Exception as e:
            LOGGER.error(f"Error stopping knowledge update service: {e}")
    
    def check_and_populate(self, question: str, confidence: float, answer: str) -> Dict[str, Any]:
        """
        Check if knowledge gap exists and auto-populate if needed.
        
        This is called by the AI Advisor when confidence is low.
        
        Args:
            question: User question
            confidence: Answer confidence score
            answer: Given answer
            
        Returns:
            Result dictionary with population status
        """
        if not self.available or not self.enable_auto_population or not self.auto_populator:
            return {"populated": False, "reason": "service_not_available"}
        
        try:
            result = self.auto_populator.check_and_populate(question, confidence, answer)
            if result.get("populated"):
                self.stats["total_updates"] += 1
            return result
        except Exception as e:
            LOGGER.error(f"Error in auto-population: {e}")
            return {"populated": False, "error": str(e)}
    
    def trigger_manual_ingestion(self, query: Optional[str] = None) -> bool:
        """
        Manually trigger a knowledge ingestion cycle.
        
        Args:
            query: Optional specific query to ingest
            
        Returns:
            True if triggered successfully
        """
        if not self.available or not self.ingestion_service:
            return False
        
        try:
            return self.ingestion_service.trigger_manual_ingestion(query)
        except Exception as e:
            LOGGER.error(f"Error triggering manual ingestion: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the service."""
        stats = {
            **self.stats,
            "running": self.running,
            "available": self.available,
            "uptime_seconds": (
                (datetime.now() - self.start_time).total_seconds()
                if self.start_time else 0
            ),
        }
        
        # Add ingestion stats
        if self.ingestion_service:
            try:
                ingestion_stats = self.ingestion_service.get_stats()
                stats["ingestion_stats"] = ingestion_stats
            except Exception as e:
                LOGGER.debug(f"Could not get ingestion stats: {e}")
        
        # Add auto-population stats
        if self.auto_populator:
            try:
                stats["auto_population_stats"] = {
                    "successful_populations": self.auto_populator.successful_populations,
                    "failed_populations": self.auto_populator.failed_populations,
                    "total_attempts": len(self.auto_populator.auto_population_history),
                }
            except Exception as e:
                LOGGER.debug(f"Could not get auto-population stats: {e}")
        
        return stats
    
    def get_status_message(self) -> str:
        """Get a human-readable status message."""
        if not self.available:
            return "❌ Service not available"
        
        if not self.running:
            return "⏸️ Service stopped"
        
        status_parts = []
        
        if self.enable_auto_ingestion:
            if self.ingestion_service and self.ingestion_service.running:
                status_parts.append("✅ Ingestion active")
            else:
                status_parts.append("⚠️ Ingestion inactive")
        
        if self.enable_auto_population:
            if self.auto_populator:
                status_parts.append("✅ Auto-population active")
            else:
                status_parts.append("⚠️ Auto-population inactive")
        
        return " | ".join(status_parts) if status_parts else "✅ Service running"


# Global instance (singleton)
_global_knowledge_service: Optional[KnowledgeUpdateService] = None


def get_knowledge_update_service() -> Optional[KnowledgeUpdateService]:
    """Get or create the global knowledge update service instance."""
    global _global_knowledge_service
    if _global_knowledge_service is None:
        _global_knowledge_service = KnowledgeUpdateService()
    return _global_knowledge_service


def start_knowledge_update_service() -> bool:
    """Start the global knowledge update service."""
    service = get_knowledge_update_service()
    if service:
        return service.start()
    return False


def stop_knowledge_update_service() -> None:
    """Stop the global knowledge update service."""
    global _global_knowledge_service
    if _global_knowledge_service:
        _global_knowledge_service.stop()


if __name__ == "__main__":
    # Test the service
    logging.basicConfig(level=logging.INFO)
    
    service = KnowledgeUpdateService()
    print(f"Service status: {service.get_status_message()}")
    print(f"Stats: {service.get_stats()}")
    
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        service.stop()

