"""
Google Custom Search API Service

Provides high-quality, reliable web search using Google's official Custom Search API.
Falls back to DuckDuckGo if quota exceeded or unavailable.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

LOGGER = logging.getLogger(__name__)

# Try to import Google API client
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    build = None  # type: ignore
    HttpError = None  # type: ignore

# Fallback to requests if googleapiclient not available
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None  # type: ignore


@dataclass
class GoogleSearchResult:
    """Google search result."""
    title: str
    url: str
    snippet: str
    display_url: Optional[str] = None
    source: str = "Google"


class GoogleSearchService:
    """
    Google Custom Search API service.
    
    Features:
    - Official Google API (reliable, won't break)
    - Custom search engine support (focus on specific sites)
    - Rate limiting and quota management
    - Automatic fallback to DuckDuckGo
    - Result caching
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        search_engine_id: Optional[str] = None,
        enable_custom_search: bool = True
    ):
        """
        Initialize Google Search service.
        
        Args:
            api_key: Google API key (from environment or parameter)
            search_engine_id: Custom search engine ID (CX) for domain-specific search
            enable_custom_search: Enable custom search engine (if CX provided)
        """
        # Get API key from environment or parameter
        self.api_key = api_key or os.getenv("GOOGLE_SEARCH_API_KEY")
        self.search_engine_id = search_engine_id or os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        self.enable_custom_search = enable_custom_search and self.search_engine_id is not None
        
        self.service = None
        self.is_available = False
        self.quota_exceeded = False
        self.daily_quota_used = 0
        self.daily_quota_limit = 100  # Free tier limit
        
        # Result cache
        self._cache: Dict[str, List[GoogleSearchResult]] = {}
        self._cache_ttl = 3600  # 1 hour
        
        # Initialize if API key available
        if self.api_key:
            self._initialize()
        else:
            LOGGER.warning("Google Search API key not found. Set GOOGLE_SEARCH_API_KEY environment variable.")
    
    def _initialize(self) -> None:
        """Initialize Google API client."""
        if not GOOGLE_API_AVAILABLE:
            LOGGER.warning("googleapiclient not installed. Install: pip install google-api-python-client")
            return
        
        try:
            # Build the service
            self.service = build("customsearch", "v1", developerKey=self.api_key)
            self.is_available = True
            LOGGER.info("Google Search API initialized")
            
            if self.enable_custom_search:
                LOGGER.info(f"Custom search engine enabled: {self.search_engine_id[:10]}...")
            else:
                LOGGER.info("Using general web search")
        except Exception as e:
            LOGGER.error(f"Failed to initialize Google Search API: {e}")
            self.is_available = False
    
    def search(
        self,
        query: str,
        max_results: int = 10,
        use_custom_search: Optional[bool] = None,
        site_restrict: Optional[str] = None
    ) -> Optional[List[GoogleSearchResult]]:
        """
        Perform Google search.
        
        Args:
            query: Search query
            max_results: Maximum number of results (max 10 per request, will paginate if needed)
            use_custom_search: Force use of custom search engine (if available)
            site_restrict: Restrict search to specific site (e.g., "bimmerforums.com")
            
        Returns:
            List of GoogleSearchResult, or None if unavailable
        """
        if not self.is_available or self.quota_exceeded:
            return None
        
        # Check cache
        cache_key = f"{query}:{max_results}:{use_custom_search}:{site_restrict}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            # Cache is valid (simplified - in production, add timestamp checking)
            LOGGER.debug(f"Using cached Google search results for: {query}")
            return cached
        
        # Check daily quota
        if self.daily_quota_used >= self.daily_quota_limit:
            LOGGER.warning("Google Search API daily quota exceeded. Use DuckDuckGo as fallback.")
            self.quota_exceeded = True
            return None
        
        try:
            results = self._perform_search(query, max_results, use_custom_search, site_restrict)
            if results:
                # Cache results
                self._cache[cache_key] = results
                self.daily_quota_used += 1
                LOGGER.info(f"Google search successful: {len(results)} results for '{query}'")
                return results
        except HttpError as e:
            if e.resp.status == 429:  # Quota exceeded
                LOGGER.warning("Google Search API quota exceeded")
                self.quota_exceeded = True
            else:
                LOGGER.error(f"Google Search API error: {e}")
        except Exception as e:
            LOGGER.error(f"Google search failed: {e}")
        
        return None
    
    def _perform_search(
        self,
        query: str,
        max_results: int,
        use_custom_search: Optional[bool],
        site_restrict: Optional[str]
    ) -> List[GoogleSearchResult]:
        """Perform actual Google search."""
        if not self.service:
            return []
        
        # Determine which search engine to use
        cx = None
        if use_custom_search is True and self.enable_custom_search:
            cx = self.search_engine_id
        elif use_custom_search is False:
            cx = None  # Use general web search
        elif self.enable_custom_search:
            cx = self.search_engine_id  # Default to custom if available
        
        # Build query with site restriction if specified
        search_query = query
        if site_restrict:
            search_query = f"site:{site_restrict} {query}"
        
        # Google API returns max 10 results per request
        results = []
        num_requests = (max_results + 9) // 10  # Ceiling division
        
        for request_num in range(num_requests):
            start_index = request_num * 10 + 1
            
            try:
                # Execute search
                response = self.service.cse().list(
                    q=search_query,
                    cx=cx,  # None for general search, CX for custom
                    num=min(10, max_results - len(results)),
                    start=start_index
                ).execute()
                
                # Parse results
                items = response.get("items", [])
                for item in items:
                    results.append(GoogleSearchResult(
                        title=item.get("title", ""),
                        url=item.get("link", ""),
                        snippet=item.get("snippet", ""),
                        display_url=item.get("displayLink", ""),
                        source="Google Custom" if cx else "Google"
                    ))
                
                # Check if we have enough results
                if len(results) >= max_results:
                    break
                
                # Check if there are more results
                if "queries" in response:
                    queries = response["queries"]
                    if "nextPage" not in queries:
                        break  # No more pages
            except Exception as e:
                LOGGER.error(f"Error in Google search request {request_num + 1}: {e}")
                break
        
        return results
    
    def search_with_requests(
        self,
        query: str,
        max_results: int = 10,
        use_custom_search: Optional[bool] = None
    ) -> Optional[List[GoogleSearchResult]]:
        """
        Alternative implementation using direct HTTP requests (if googleapiclient not available).
        
        This is a fallback method that uses requests library directly.
        """
        if not REQUESTS_AVAILABLE or not self.api_key:
            return None
        
        # Determine CX
        cx = None
        if use_custom_search is True and self.enable_custom_search:
            cx = self.search_engine_id
        elif use_custom_search is False:
            cx = None
        elif self.enable_custom_search:
            cx = self.search_engine_id
        
        # Build URL
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.api_key,
            "q": query,
            "num": min(max_results, 10)  # Max 10 per request
        }
        
        if cx:
            params["cx"] = cx
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get("items", []):
                results.append(GoogleSearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    display_url=item.get("displayLink", ""),
                    source="Google Custom" if cx else "Google"
                ))
            
            self.daily_quota_used += 1
            return results
            
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Google search HTTP request failed: {e}")
            return None
        except Exception as e:
            LOGGER.error(f"Google search parsing failed: {e}")
            return None
    
    def search_forum(self, query: str, forum_domain: str, max_results: int = 5) -> Optional[List[GoogleSearchResult]]:
        """
        Search a specific forum/website.
        
        Args:
            query: Search query
            forum_domain: Domain to search (e.g., "bimmerforums.com")
            max_results: Maximum results
            
        Returns:
            List of search results from that domain
        """
        return self.search(
            query=query,
            max_results=max_results,
            site_restrict=forum_domain,
            use_custom_search=False  # Use general search with site restriction
        )
    
    def reset_quota(self) -> None:
        """Reset daily quota (call this daily)."""
        self.daily_quota_used = 0
        self.quota_exceeded = False
        LOGGER.info("Google Search API quota reset")
    
    def clear_cache(self) -> None:
        """Clear search result cache."""
        self._cache.clear()
        LOGGER.info("Google Search cache cleared")
    
    def get_quota_status(self) -> Dict[str, Any]:
        """Get current quota status."""
        return {
            "available": self.is_available,
            "quota_exceeded": self.quota_exceeded,
            "daily_used": self.daily_quota_used,
            "daily_limit": self.daily_quota_limit,
            "remaining": max(0, self.daily_quota_limit - self.daily_quota_used),
            "custom_search_enabled": self.enable_custom_search
        }


__all__ = ["GoogleSearchService", "GoogleSearchResult"]

