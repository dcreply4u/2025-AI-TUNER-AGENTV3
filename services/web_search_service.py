"""
Web Search Service for AI Advisor

Provides internet research capabilities when internet connection is available.
Falls back gracefully when offline.
"""

from __future__ import annotations

import logging
import socket
import time
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

LOGGER = logging.getLogger(__name__)

# Try to import web search libraries
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None  # type: ignore

try:
    from duckduckgo_search import DDGS
    DUCKDUCKGO_AVAILABLE = True
except ImportError:
    DUCKDUCKGO_AVAILABLE = False
    DDGS = None  # type: ignore

try:
    import googlesearch
    GOOGLESEARCH_AVAILABLE = True
except ImportError:
    GOOGLESEARCH_AVAILABLE = False
    googlesearch = None  # type: ignore


@dataclass
class SearchResult:
    """Web search result."""
    title: str
    url: str
    snippet: str
    source: str = "web"


@dataclass
class ResearchResult:
    """Complete research result with multiple sources."""
    query: str
    results: List[SearchResult]
    summary: Optional[str] = None
    sources: List[str] = None  # type: ignore
    timestamp: float = None  # type: ignore
    
    def __post_init__(self):
        if self.sources is None:
            self.sources = [r.url for r in self.results]
        if self.timestamp is None:
            self.timestamp = time.time()


class WebSearchService:
    """
    Web search service for AI advisor research capabilities.
    
    Features:
    - Internet connectivity checking
    - Multiple search engine support (DuckDuckGo, Google)
    - Result caching
    - Graceful offline fallback
    """
    
    def __init__(self, enable_search: bool = True):
        """
        Initialize web search service.
        
        Args:
            enable_search: Enable web search (can be disabled for offline mode)
        """
        self.enable_search = enable_search
        self.has_internet = False
        self.search_available = False
        self._check_availability()
        
        # Result cache (simple in-memory cache)
        self._cache: Dict[str, ResearchResult] = {}
        self._cache_ttl = 3600  # 1 hour cache TTL
    
    def _check_availability(self) -> None:
        """Check if internet and search are available."""
        # Check internet connectivity
        self.has_internet = self._check_internet()
        
        # Check search engine availability
        if self.has_internet:
            if DUCKDUCKGO_AVAILABLE:
                self.search_available = True
                LOGGER.info("Web search available via DuckDuckGo")
            elif GOOGLESEARCH_AVAILABLE:
                self.search_available = True
                LOGGER.info("Web search available via Google")
            elif REQUESTS_AVAILABLE:
                # Can use direct API calls if needed
                self.search_available = True
                LOGGER.info("Web search available via direct API")
            else:
                self.search_available = False
                LOGGER.warning("Web search libraries not installed. Install: pip install duckduckgo-search")
        else:
            self.search_available = False
            LOGGER.info("No internet connection - web search unavailable")
    
    def _check_internet(self) -> bool:
        """Check if internet connection is available."""
        try:
            # Quick connectivity check
            socket.create_connection(("8.8.8.8", 53), timeout=2).close()
            return True
        except (OSError, socket.timeout):
            return False
    
    def is_available(self) -> bool:
        """Check if web search is currently available."""
        # Re-check connectivity periodically
        if not self.has_internet:
            self.has_internet = self._check_internet()
            if self.has_internet:
                self._check_availability()
        
        return self.enable_search and self.has_internet and self.search_available
    
    def search(self, query: str, max_results: int = 5) -> Optional[ResearchResult]:
        """
        Perform web search.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            ResearchResult with search results, or None if unavailable
        """
        if not self.is_available():
            LOGGER.debug("Web search not available for query: %s", query)
            return None
        
        # Check cache
        cache_key = f"{query}:{max_results}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            # Check if cache is still valid
            if time.time() - cached.timestamp < self._cache_ttl:
                LOGGER.debug("Using cached search results for: %s", query)
                return cached
        
        try:
            results = self._perform_search(query, max_results)
            if results:
                research_result = ResearchResult(
                    query=query,
                    results=results,
                )
                # Cache the result
                self._cache[cache_key] = research_result
                return research_result
        except Exception as e:
            LOGGER.warning("Web search failed for query '%s': %s", query, e)
        
        return None
    
    def _perform_search(self, query: str, max_results: int) -> List[SearchResult]:
        """Perform actual web search using available search engine."""
        results = []
        
        # Try DuckDuckGo first (no API key required)
        if DUCKDUCKGO_AVAILABLE:
            try:
                with DDGS() as ddgs:
                    search_results = ddgs.text(query, max_results=max_results)
                    for result in search_results:
                        results.append(SearchResult(
                            title=result.get("title", ""),
                            url=result.get("href", ""),
                            snippet=result.get("body", ""),
                            source="DuckDuckGo",
                        ))
                    if results:
                        LOGGER.info("Found %d results via DuckDuckGo for: %s", len(results), query)
                        return results
            except Exception as e:
                LOGGER.debug("DuckDuckGo search failed: %s", e)
        
        # Fallback to Google search
        if GOOGLESEARCH_AVAILABLE and not results:
            try:
                google_results = googlesearch.search(query, num_results=max_results)
                for url in google_results:
                    # Google search returns URLs, need to fetch titles/snippets
                    results.append(SearchResult(
                        title=url,
                        url=url,
                        snippet="",
                        source="Google",
                    ))
                if results:
                    LOGGER.info("Found %d results via Google for: %s", len(results), query)
                    return results
            except Exception as e:
                LOGGER.debug("Google search failed: %s", e)
        
        # Fallback: Direct API call (if requests available)
        if REQUESTS_AVAILABLE and not results:
            # Could implement direct API calls here
            pass
        
        return results
    
    def research_topic(self, topic: str, context: Optional[str] = None) -> Optional[ResearchResult]:
        """
        Research a topic with context-aware query generation.
        
        Args:
            topic: Topic to research
            context: Additional context for better query
            
        Returns:
            ResearchResult with research findings
        """
        if not self.is_available():
            return None
        
        # Build search query with context
        if context:
            query = f"{topic} {context} racing tuning automotive"
        else:
            query = f"{topic} racing tuning automotive ECU"
        
        return self.search(query, max_results=5)
    
    def lookup_specification(self, item: str, item_type: str = "component") -> Optional[ResearchResult]:
        """
        Look up specifications for a component, part, or vehicle.
        
        Args:
            item: Item to look up (e.g., "Holley EFI", "MCP2515", "Honda Civic Type R")
            item_type: Type of item (component, vehicle, ECU, etc.)
            
        Returns:
            ResearchResult with specifications
        """
        if not self.is_available():
            return None
        
        query = f"{item} {item_type} specifications technical details"
        return self.search(query, max_results=3)
    
    def find_troubleshooting_info(self, issue: str) -> Optional[ResearchResult]:
        """
        Find troubleshooting information for an issue.
        
        Args:
            issue: Issue description
            
        Returns:
            ResearchResult with troubleshooting information
        """
        if not self.is_available():
            return None
        
        query = f"{issue} troubleshooting fix solution ECU tuning"
        return self.search(query, max_results=5)
    
    def clear_cache(self) -> None:
        """Clear the search result cache."""
        self._cache.clear()
        LOGGER.info("Web search cache cleared")


__all__ = ["WebSearchService", "SearchResult", "ResearchResult"]



