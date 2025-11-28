"""
Auto Knowledge Populator
Automatically populates knowledge base when confidence is low or gaps are detected.
"""

from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional, Any

LOGGER = logging.getLogger(__name__)

# Import dependencies
try:
    from services.ai_advisor_learning_system import AILearningSystem
    from services.website_list_manager import WebsiteListManager
    from services.website_ingestion_service import WebsiteIngestionService
    from services.knowledge_base_manager import KnowledgeBaseManager
    from services.web_search_service import WebSearchService
    from services.knowledge_base_file_manager import KnowledgeBaseFileManager
    SERVICES_AVAILABLE = True
except ImportError as e:
    SERVICES_AVAILABLE = False
    LOGGER.warning(f"Services not available: {e}")
    KnowledgeBaseFileManager = None


class AutoKnowledgePopulator:
    """
    Automatically populates knowledge base when gaps are detected.
    
    Features:
    - Detects low confidence answers
    - Automatically searches web/forums for missing information
    - Adds found information to knowledge base
    - Learns from successful auto-population
    """
    
    def __init__(
        self,
        learning_system: Optional[AILearningSystem] = None,
        website_ingestion_service: Optional[WebsiteIngestionService] = None,
        knowledge_base_manager: Optional[KnowledgeBaseManager] = None,
        web_search_service: Optional[WebSearchService] = None,
        kb_file_manager: Optional[KnowledgeBaseFileManager] = None,
        auto_populate_enabled: bool = True,
        confidence_threshold: float = 0.5,
        min_gap_frequency: int = 2
    ):
        """
        Initialize auto knowledge populator.
        
        Args:
            learning_system: Learning system for gap detection
            website_ingestion_service: Service for forum search
            knowledge_base_manager: Knowledge base manager
            web_search_service: Web search service
            kb_file_manager: KB file manager for saving learned knowledge
            auto_populate_enabled: Enable automatic population
            confidence_threshold: Minimum confidence to trigger auto-population
            min_gap_frequency: Minimum gap frequency before auto-populating
        """
        if not SERVICES_AVAILABLE:
            raise ImportError("Required services not available")
        
        self.learning_system = learning_system
        self.website_ingestion_service = website_ingestion_service
        self.knowledge_base_manager = knowledge_base_manager
        self.web_search_service = web_search_service
        self.kb_file_manager = kb_file_manager or (KnowledgeBaseFileManager() if KnowledgeBaseFileManager else None)
        self.auto_populate_enabled = auto_populate_enabled
        self.confidence_threshold = confidence_threshold
        self.min_gap_frequency = min_gap_frequency
        
        # Track auto-population attempts
        self.auto_population_history: List[Dict[str, Any]] = []
        self.successful_populations = 0
        self.failed_populations = 0
        
        LOGGER.info("Auto Knowledge Populator initialized")
    
    def check_and_populate(
        self,
        question: str,
        confidence: float,
        answer: str
    ) -> Dict[str, Any]:
        """
        Check if knowledge gap exists and auto-populate if needed.
        
        Args:
            question: User question
            confidence: Answer confidence
            answer: Given answer
            
        Returns:
            Result dictionary
        """
        if not self.auto_populate_enabled:
            return {"action": "skipped", "reason": "auto-populate disabled"}
        
        # Check if confidence is too low
        if confidence >= self.confidence_threshold:
            return {"action": "skipped", "reason": "confidence sufficient"}
        
        # Check if this is a recurring gap
        if self.learning_system:
            gaps = self.learning_system.get_knowledge_gaps()
            question_key = question.lower().strip()
            
            # Find matching gap
            matching_gap = None
            for gap in gaps:
                if gap.question.lower().strip() == question_key:
                    matching_gap = gap
                    break
            
            # Only auto-populate if gap has occurred multiple times
            if matching_gap and matching_gap.frequency < self.min_gap_frequency:
                return {
                    "action": "skipped",
                    "reason": f"gap frequency ({matching_gap.frequency}) below threshold ({self.min_gap_frequency})"
                }
        
        # Attempt auto-population
        LOGGER.info(f"Auto-populating knowledge for: {question[:50]}")
        
        result = self._populate_knowledge(question)
        
        # Track result
        self.auto_population_history.append({
            "question": question,
            "confidence": confidence,
            "timestamp": time.time(),
            "result": result
        })
        
        if result.get("success"):
            self.successful_populations += 1
        else:
            self.failed_populations += 1
        
        return result
    
    def _populate_knowledge(self, question: str) -> Dict[str, Any]:
        """
        Populate knowledge base for a question.
        
        Args:
            question: Question to find knowledge for
            
        Returns:
            Result dictionary
        """
        results = {
            "success": False,
            "sources_tried": [],
            "chunks_added": 0,
            "errors": []
        }
        
        # Strategy 1: Web search (Google/DuckDuckGo) - FASTEST and most reliable
        if self.web_search_service and self.web_search_service.is_available():
            try:
                LOGGER.info("="*60)
                LOGGER.info(f"🌐 SEARCHING WEB (Google/DuckDuckGo) for: {question}")
                LOGGER.info("="*60)
                search_start = time.time()
                search_results = self.web_search_service.search(question, max_results=5)
                search_elapsed = time.time() - search_start
                LOGGER.info(f"⏱️  Web search completed in {search_elapsed:.2f}s")
                
                if search_results and search_results.results:
                    LOGGER.info(f"✅ Found {len(search_results.results)} search results!")
                    for i, result in enumerate(search_results.results[:3], 1):
                        LOGGER.info(f"  [{i}] {result.title[:60]}...")
                        LOGGER.info(f"      URL: {result.url[:60]}...")
                    
                    # Add search results to knowledge base
                    chunks_added = 0
                    LOGGER.info("📝 Adding search results to knowledge base...")
                    for result in search_results.results[:3]:  # Top 3 results
                        try:
                            # Add as knowledge entry via knowledge base manager
                            if self.knowledge_base_manager:
                                # Use the knowledge base manager's add method
                                knowledge_text = f"{result.title}\n\n{result.snippet}"
                                
                                # Try direct vector store access if available
                                if hasattr(self.knowledge_base_manager, 'vector_store') and self.knowledge_base_manager.vector_store:
                                    LOGGER.info(f"  ➕ Adding: {result.title[:50]}...")
                                    doc_id = self.knowledge_base_manager.vector_store.add_knowledge(
                                        text=knowledge_text,
                                        metadata={
                                            "source": "web_search",
                                            "url": result.url,
                                            "topic": question,
                                            "auto_populated": True
                                        }
                                    )
                                    chunks_added += 1
                                    LOGGER.info(f"     ✓ Added (ID: {doc_id[:20]}...)")
                                # Fallback: use knowledge base manager's add method
                                elif hasattr(self.knowledge_base_manager, 'add_knowledge'):
                                    self.knowledge_base_manager.add_knowledge(
                                        text=knowledge_text,
                                        metadata={
                                            "source": "web_search",
                                            "url": result.url,
                                            "topic": question,
                                            "auto_populated": True
                                        }
                                    )
                                    chunks_added += 1
                        except Exception as e:
                            error_msg = f"Failed to add search result: {e}"
                            results["errors"].append(error_msg)
                            LOGGER.warning(f"Failed to add search result: {e}")
                            import traceback
                            LOGGER.debug(f"Traceback: {traceback.format_exc()}")
                    
                    if chunks_added > 0:
                        results["chunks_added"] += chunks_added
                        results["sources_tried"].append("web_search")
                        results["success"] = True
                        LOGGER.info(f"✓ Added {chunks_added} knowledge chunks from web search for: {question[:50]}")
                        
                        # Save to KB file if available
                        if self.kb_file_manager:
                            try:
                                top_result = search_results.results[0]
                                self.kb_file_manager.add_entry(
                                    question=question,
                                    answer=top_result.snippet,
                                    source="web_search",
                                    url=top_result.url,
                                    title=top_result.title,
                                    confidence=0.7,
                                    topic=self._extract_topic(question),
                                    keywords=self._extract_keywords(question),
                                    verified=False
                                )
                                LOGGER.info(f"Saved to KB file: {question[:50]}...")
                            except Exception as e:
                                LOGGER.warning(f"Failed to save to KB file: {e}")
                                results["errors"].append(f"KB file save error: {e}")
                    else:
                        LOGGER.warning(f"No chunks added from web search (search returned {len(search_results.results)} results but add_knowledge failed)")
                        if not results["errors"]:
                            results["errors"].append("Web search returned results but failed to add to knowledge base - check vector store")
            except Exception as e:
                results["errors"].append(f"Web search error: {e}")
                LOGGER.warning(f"Web search failed: {e}")
        
        # Strategy 2: Search forums from website list (fallback, slower)
        if not results["success"] and self.website_ingestion_service:
            try:
                websites = self.website_ingestion_service.website_list_manager.get_websites(
                    enabled_only=True,
                    category="forum"
                )
                
                # Try top 3 forums
                for website in websites[:3]:
                    try:
                        LOGGER.info(f"Searching forum: {website.name}")
                        result = self.website_ingestion_service.knowledge_base_manager.web_scraper.search_forum(
                            website.url,
                            question,
                            max_posts=3
                        )
                        
                        posts_added = result.get("posts_added", 0)
                        if posts_added > 0:
                            results["chunks_added"] += posts_added
                            results["sources_tried"].append(f"forum:{website.name}")
                            results["success"] = True
                            LOGGER.info(f"✓ Found {posts_added} posts in {website.name}")
                    except Exception as e:
                        results["errors"].append(f"Forum {website.name}: {e}")
                        LOGGER.debug(f"Forum search failed: {e}")
                        
            except Exception as e:
                results["errors"].append(f"Forum search error: {e}")
                LOGGER.warning(f"Forum search failed: {e}")
        
        # Strategy 2: Web search
        if not results["success"] and self.web_search_service:
            try:
                LOGGER.info("Trying web search...")
                search_results = self.web_search_service.search(question, max_results=3)
                
                if search_results and search_results.results:
                    # Extract answer from top result
                    top_result = search_results.results[0]
                    answer_text = ""
                    
                    if top_result:
                        # Combine title and snippet for answer
                        answer_text = f"{top_result.title}\n\n{top_result.snippet}"
                        
                        # Save to KB file for user review
                        if self.kb_file_manager:
                            try:
                                # Extract topic from question
                                topic = self._extract_topic(question)
                                
                                # Extract keywords
                                keywords = self._extract_keywords(question)
                                
                                self.kb_file_manager.add_entry(
                                    question=question,
                                    answer=answer_text,
                                    source="auto_populate",
                                    url=top_result.url,
                                    title=top_result.title,
                                    confidence=0.7,  # Medium confidence for auto-populated
                                    keywords=keywords,
                                    topic=topic,
                                    verified=False  # User should verify
                                )
                                LOGGER.info(f"Saved learned knowledge to KB file: {question[:50]}...")
                            except Exception as e:
                                LOGGER.warning(f"Failed to save to KB file: {e}")
                    
                    # Add top results to knowledge base (vector store) - already done above
                    # This section is redundant but kept for compatibility
                    if self.knowledge_base_manager and not results["success"]:
                        for result in search_results.results[:2]:
                            try:
                                chunks = self.knowledge_base_manager.add_website(
                                    result.url,
                                    metadata={
                                        "source": "auto_populate",
                                        "search_query": question,
                                        "title": result.title
                                    }
                                )
                                chunks_added = chunks.get("chunks_added", 0)
                                if chunks_added > 0:
                                    results["chunks_added"] += chunks_added
                                    results["sources_tried"].append(f"web:{result.url[:50]}")
                                    results["success"] = True
                            except Exception as e:
                                results["errors"].append(f"Web add error: {e}")
                                
            except Exception as e:
                results["errors"].append(f"Web search error: {e}")
                LOGGER.warning(f"Web search failed: {e}")
        
        if results["success"]:
            LOGGER.info(f"✓ Auto-populated {results['chunks_added']} chunks for: {question[:50]}")
        else:
            error_summary = "; ".join(results["errors"][:3]) if results["errors"] else "Unknown error"
            LOGGER.warning(f"✗ Auto-population failed for: {question[:50]} - {error_summary}")
            if results["errors"]:
                for error in results["errors"]:
                    LOGGER.debug(f"  Error detail: {error}")
        
        return results
    
    def _extract_topic(self, question: str) -> str:
        """Extract topic category from question."""
        question_lower = question.lower()
        
        # Topic keywords
        topics = {
            "ECU Tuning": ["ecu", "tune", "tuning", "map", "calibration"],
            "Fuel System": ["fuel", "pressure", "injector", "pump", "afr"],
            "Boost Control": ["boost", "turbo", "supercharger", "psi", "bar"],
            "Ignition": ["spark", "timing", "ignition", "coil"],
            "Engine": ["engine", "rpm", "hp", "torque", "power"],
            "Diagnostics": ["error", "code", "fault", "diagnostic", "problem"],
            "Hardware": ["sensor", "ecu", "module", "hardware", "component"],
            "General": []  # Default
        }
        
        for topic, keywords in topics.items():
            if any(kw in question_lower for kw in keywords):
                return topic
        
        return "General"
    
    def _extract_keywords(self, question: str) -> List[str]:
        """Extract keywords from question."""
        # Simple keyword extraction (can be enhanced)
        words = question.lower().split()
        # Remove common words
        stop_words = {"what", "is", "the", "a", "an", "how", "do", "does", "can", "should", "when", "where", "why"}
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        return keywords[:10]  # Top 10 keywords
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get auto-population statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "enabled": self.auto_populate_enabled,
            "successful": self.successful_populations,
            "failed": self.failed_populations,
            "total_attempts": len(self.auto_population_history),
            "success_rate": (
                self.successful_populations / len(self.auto_population_history)
                if self.auto_population_history else 0.0
            )
        }

