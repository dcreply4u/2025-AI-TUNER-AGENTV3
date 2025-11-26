"""
Website Ingestion Service
Ingests websites from the website list into the knowledge base.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any

LOGGER = logging.getLogger(__name__)

# Import dependencies
try:
    from services.website_list_manager import WebsiteListManager
    from services.knowledge_base_manager import KnowledgeBaseManager
    from services.vector_knowledge_store import VectorKnowledgeStore
    SERVICES_AVAILABLE = True
except ImportError as e:
    SERVICES_AVAILABLE = False
    LOGGER.warning(f"Services not available: {e}")


class WebsiteIngestionService:
    """
    Service to ingest websites from the website list.
    """
    
    def __init__(
        self,
        website_list_manager: Optional[WebsiteListManager] = None,
        knowledge_base_manager: Optional[KnowledgeBaseManager] = None
    ):
        """
        Initialize website ingestion service.
        
        Args:
            website_list_manager: Website list manager
            knowledge_base_manager: Knowledge base manager
        """
        if not SERVICES_AVAILABLE:
            raise ImportError("Required services not available")
        
        self.website_list_manager = website_list_manager or WebsiteListManager()
        
        if not knowledge_base_manager:
            vector_store = VectorKnowledgeStore()
            knowledge_base_manager = KnowledgeBaseManager(vector_store)
        
        self.knowledge_base_manager = knowledge_base_manager
        
        LOGGER.info("Website Ingestion Service initialized")
    
    def ingest_all(self, enabled_only: bool = True, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Ingest all websites from the list.
        
        Args:
            enabled_only: Only ingest enabled websites
            category: Filter by category
            
        Returns:
            Summary dictionary
        """
        websites = self.website_list_manager.get_websites(
            enabled_only=enabled_only,
            category=category
        )
        
        results = {
            "total": len(websites),
            "successful": 0,
            "failed": 0,
            "total_chunks": 0,
            "details": []
        }
        
        LOGGER.info(f"Starting ingestion of {len(websites)} websites...")
        
        for website in websites:
            try:
                LOGGER.info(f"Ingesting: {website.name} ({website.url})")
                
                # Ingest website
                result = self.knowledge_base_manager.add_website(
                    website.url,
                    metadata={
                        "name": website.name,
                        "description": website.description,
                        "category": website.category,
                        **website.metadata
                    }
                )
                
                if result.get("success"):
                    chunks_added = result.get("chunks_added", 0)
                    self.website_list_manager.mark_ingested(website.url, chunks_added)
                    results["successful"] += 1
                    results["total_chunks"] += chunks_added
                    results["details"].append({
                        "url": website.url,
                        "name": website.name,
                        "status": "success",
                        "chunks": chunks_added
                    })
                    LOGGER.info(f"✓ Ingested {website.name}: {chunks_added} chunks")
                else:
                    results["failed"] += 1
                    errors = result.get("errors", [])
                    results["details"].append({
                        "url": website.url,
                        "name": website.name,
                        "status": "failed",
                        "errors": errors
                    })
                    LOGGER.warning(f"✗ Failed to ingest {website.name}: {errors}")
                
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "url": website.url,
                    "name": website.name,
                    "status": "error",
                    "error": str(e)
                })
                LOGGER.error(f"Error ingesting {website.name}: {e}")
        
        LOGGER.info(f"Ingestion complete: {results['successful']} successful, {results['failed']} failed")
        
        return results
    
    def ingest_website(self, url: str) -> Dict[str, Any]:
        """
        Ingest a specific website.
        
        Args:
            url: Website URL
            
        Returns:
            Result dictionary
        """
        website = self.website_list_manager.get_website(url)
        if not website:
            return {
                "success": False,
                "error": f"Website not in list: {url}"
            }
        
        if not website.enabled:
            return {
                "success": False,
                "error": f"Website is disabled: {url}"
            }
        
        try:
            result = self.knowledge_base_manager.add_website(
                url,
                metadata={
                    "name": website.name,
                    "description": website.description,
                    "category": website.category,
                    **website.metadata
                }
            )
            
            if result.get("success"):
                chunks_added = result.get("chunks_added", 0)
                self.website_list_manager.mark_ingested(url, chunks_added)
            
            return result
            
        except Exception as e:
            LOGGER.error(f"Error ingesting website: {e}")
            return {
                "success": False,
                "error": str(e)
            }

