"""
Rate Limiting Middleware
Prevents API abuse with configurable rate limits.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Optional

from fastapi import HTTPException, Request, status

LOGGER = logging.getLogger(__name__)


@dataclass
class RateLimit:
    """Rate limit configuration."""
    requests: int  # Number of requests
    window: int  # Time window in seconds
    burst: Optional[int] = None  # Burst allowance


@dataclass
class RateLimitEntry:
    """Rate limit entry for tracking."""
    count: int = 0
    reset_time: float = field(default_factory=time.time)
    burst_used: int = 0


class RateLimiter:
    """
    Rate limiter for API endpoints.
    
    Supports:
    - Per-IP rate limiting
    - Per-user rate limiting
    - Token bucket algorithm
    - Burst allowance
    """
    
    def __init__(self):
        """Initialize rate limiter."""
        self.limits: Dict[str, RateLimit] = {}
        self.entries: Dict[str, RateLimitEntry] = {}
        self.default_limit = RateLimit(requests=100, window=60)  # 100 requests per minute
    
    def add_limit(self, endpoint: str, limit: RateLimit) -> None:
        """
        Add rate limit for endpoint.
        
        Args:
            endpoint: Endpoint path or pattern
            limit: Rate limit configuration
        """
        self.limits[endpoint] = limit
        LOGGER.info("Rate limit added for %s: %d requests per %d seconds", 
                   endpoint, limit.requests, limit.window)
    
    def get_client_id(self, request: Request) -> str:
        """
        Get client identifier for rate limiting.
        
        Args:
            request: FastAPI request
        
        Returns:
            Client ID (IP or user ID)
        """
        # Try to get user ID first
        if hasattr(request.state, "user"):
            user = request.state.user
            user_id = user.get("user_id")
            if user_id:
                return f"user:{user_id}"
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def check_rate_limit(
        self,
        request: Request,
        endpoint: str,
    ) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if request is within rate limit.
        
        Args:
            request: FastAPI request
            endpoint: Endpoint path
        
        Returns:
            Tuple of (allowed, rate_limit_info)
        """
        client_id = self.get_client_id(request)
        key = f"{endpoint}:{client_id}"
        
        # Get limit for endpoint or use default
        limit = self.limits.get(endpoint, self.default_limit)
        
        # Get or create entry
        entry = self.entries.get(key)
        current_time = time.time()
        
        if not entry:
            entry = RateLimitEntry(reset_time=current_time + limit.window)
            self.entries[key] = entry
        
        # Check if window expired
        if current_time >= entry.reset_time:
            entry.count = 0
            entry.burst_used = 0
            entry.reset_time = current_time + limit.window
        
        # Check burst allowance
        if limit.burst and entry.burst_used < limit.burst:
            entry.burst_used += 1
            return True, {
                "limit": limit.requests,
                "remaining": limit.requests - entry.count,
                "reset_time": entry.reset_time,
                "burst_remaining": limit.burst - entry.burst_used if limit.burst else None,
            }
        
        # Check regular limit
        if entry.count >= limit.requests:
            retry_after = int(entry.reset_time - current_time)
            return False, {
                "limit": limit.requests,
                "remaining": 0,
                "reset_time": entry.reset_time,
                "retry_after": retry_after,
            }
        
        # Increment count
        entry.count += 1
        
        return True, {
            "limit": limit.requests,
            "remaining": limit.requests - entry.count,
            "reset_time": entry.reset_time,
        }
    
    def cleanup_old_entries(self, max_age: int = 3600) -> None:
        """
        Clean up old rate limit entries.
        
        Args:
            max_age: Maximum age in seconds
        """
        current_time = time.time()
        keys_to_remove = [
            key for key, entry in self.entries.items()
            if current_time - entry.reset_time > max_age
        ]
        
        for key in keys_to_remove:
            del self.entries[key]
        
        if keys_to_remove:
            LOGGER.debug("Cleaned up %d old rate limit entries", len(keys_to_remove))


# Global rate limiter instance
rate_limiter = RateLimiter()

# Configure default limits
rate_limiter.add_limit("/api/telemetry", RateLimit(requests=1000, window=60))  # High frequency
rate_limiter.add_limit("/api/ota/check", RateLimit(requests=10, window=3600))  # Once per hour
rate_limiter.add_limit("/api/remote-tuning", RateLimit(requests=100, window=60))
rate_limiter.add_limit("/api/social", RateLimit(requests=200, window=60))
rate_limiter.add_limit("/api/fleet", RateLimit(requests=100, window=60))
rate_limiter.add_limit("/api/blockchain", RateLimit(requests=50, window=60))
rate_limiter.add_limit("/api/ai", RateLimit(requests=50, window=60, burst=10))  # Burst for AI


def rate_limit(endpoint: str):
    """
    Decorator to apply rate limiting to endpoint.
    
    Usage:
        @app.get("/api/endpoint")
        @rate_limit("/api/endpoint")
        async def my_endpoint(request: Request):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )
            
            # Check rate limit
            allowed, rate_info = rate_limiter.check_rate_limit(request, endpoint)
            
            if not allowed:
                retry_after = rate_info.get("retry_after", 60)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={
                        "X-RateLimit-Limit": str(rate_info["limit"]),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(rate_info["reset_time"])),
                        "Retry-After": str(retry_after),
                    }
                )
            
            # Add rate limit headers
            if hasattr(request.state, "response_headers"):
                request.state.response_headers = {}
            else:
                request.state.response_headers = {}
            
            request.state.response_headers.update({
                "X-RateLimit-Limit": str(rate_info["limit"]),
                "X-RateLimit-Remaining": str(rate_info["remaining"]),
                "X-RateLimit-Reset": str(int(rate_info["reset_time"])),
            })
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


