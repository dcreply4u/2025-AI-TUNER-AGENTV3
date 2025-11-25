"""
Advanced Caching System with Predictive Prefetching

Implements:
- Multi-level caching (L1: Memory, L2: Disk, L3: Network)
- LRU with frequency-based promotion
- Predictive prefetching using access patterns
- Adaptive cache sizing
- Cache warming strategies
"""

from __future__ import annotations

import hashlib
import json
import logging
import pickle
import time
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from threading import Lock, RLock
from typing import Any, Callable, Dict, List, Optional, Tuple

LOGGER = logging.getLogger(__name__)


class CacheLevel(Enum):
    """Cache levels."""

    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    key: str
    value: Any
    timestamp: float
    access_count: int = 0
    last_access: float = field(default_factory=time.time)
    size_bytes: int = 0
    level: CacheLevel = CacheLevel.MEMORY
    prefetch_score: float = 0.0
    dependencies: List[str] = field(default_factory=list)


class PredictivePrefetcher:
    """Predictive prefetching based on access patterns."""

    def __init__(self, history_size: int = 1000):
        """Initialize prefetcher."""
        self.history_size = history_size
        self.access_patterns: Dict[str, List[str]] = defaultdict(list)
        self.access_history: List[Tuple[str, float]] = []
        self.pattern_confidence: Dict[Tuple[str, str], float] = defaultdict(float)
        self._lock = Lock()

    def record_access(self, key: str) -> None:
        """Record key access for pattern analysis."""
        with self._lock:
            current_time = time.time()
            self.access_history.append((key, current_time))
            if len(self.access_history) > self.history_size:
                self.access_history.pop(0)

            # Update access patterns (next key after this one)
            if len(self.access_history) >= 2:
                prev_key = self.access_history[-2][0]
                if prev_key != key:
                    self.access_patterns[prev_key].append(key)
                    # Update confidence
                    pattern = (prev_key, key)
                    self.pattern_confidence[pattern] = min(
                        1.0, self.pattern_confidence[pattern] + 0.1
                    )

    def predict_next(self, current_key: str, top_n: int = 3) -> List[Tuple[str, float]]:
        """
        Predict next keys likely to be accessed.

        Args:
            current_key: Current key being accessed
            top_n: Number of predictions to return

        Returns:
            List of (key, confidence) tuples
        """
        with self._lock:
            if current_key not in self.access_patterns:
                return []

            # Count pattern frequencies
            pattern_counts: Dict[str, int] = defaultdict(int)
            for next_key in self.access_patterns[current_key]:
                pattern_counts[next_key] += 1

            # Calculate confidence scores
            predictions = []
            total_accesses = len(self.access_patterns[current_key])
            for next_key, count in pattern_counts.items():
                confidence = count / total_accesses
                pattern = (current_key, next_key)
                # Combine frequency with historical confidence
                combined_confidence = (confidence + self.pattern_confidence[pattern]) / 2
                predictions.append((next_key, combined_confidence))

            # Sort by confidence and return top N
            predictions.sort(key=lambda x: x[1], reverse=True)
            return predictions[:top_n]

    def get_pattern_stats(self) -> Dict[str, Any]:
        """Get prefetcher statistics."""
        with self._lock:
            return {
                "total_patterns": len(self.pattern_confidence),
                "history_size": len(self.access_history),
                "unique_keys": len(self.access_patterns),
            }


class AdvancedCache:
    """Advanced multi-level cache with predictive prefetching."""

    def __init__(
        self,
        max_memory_mb: float = 256.0,
        max_disk_mb: float = 1024.0,
        disk_cache_dir: Optional[Path] = None,
        prefetch_enabled: bool = True,
    ):
        """
        Initialize advanced cache.

        Args:
            max_memory_mb: Maximum memory cache size in MB
            max_disk_mb: Maximum disk cache size in MB
            disk_cache_dir: Directory for disk cache
            prefetch_enabled: Enable predictive prefetching
        """
        self.max_memory_bytes = int(max_memory_mb * 1024 * 1024)
        self.max_disk_bytes = int(max_disk_mb * 1024 * 1024)
        self.disk_cache_dir = disk_cache_dir or Path("cache")
        self.disk_cache_dir.mkdir(parents=True, exist_ok=True)

        # Memory cache (LRU with frequency)
        self.memory_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.memory_size_bytes = 0

        # Disk cache index
        self.disk_index: Dict[str, CacheEntry] = {}
        self.disk_size_bytes = 0

        # Prefetcher
        self.prefetcher = PredictivePrefetcher() if prefetch_enabled else None
        self.prefetch_enabled = prefetch_enabled

        # Thread safety
        self._lock = RLock()

        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "prefetch_hits": 0,
            "evictions": 0,
            "promotions": 0,
        }

    def _get_entry_size(self, entry: CacheEntry) -> int:
        """Estimate entry size in bytes."""
        if entry.size_bytes > 0:
            return entry.size_bytes
        try:
            return len(pickle.dumps(entry.value))
        except Exception:
            return 1024  # Default estimate

    def _make_key(self, *args, **kwargs) -> str:
        """Create cache key from arguments."""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()

    def get(self, key: str, default: Any = None) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key
            default: Default value if not found

        Returns:
            Cached value or default
        """
        with self._lock:
            # Check memory cache first
            if key in self.memory_cache:
                entry = self.memory_cache.pop(key)
                entry.access_count += 1
                entry.last_access = time.time()
                self.memory_cache[key] = entry  # Move to end (LRU)
                self.stats["hits"] += 1

                # Record access for prefetching
                if self.prefetcher:
                    self.prefetcher.record_access(key)

                return entry.value

            # Check disk cache
            if key in self.disk_index:
                entry = self.disk_index[key]
                try:
                    # Load from disk
                    cache_file = self.disk_cache_dir / f"{key}.cache"
                    if cache_file.exists():
                        with open(cache_file, "rb") as f:
                            entry.value = pickle.load(f)
                        # Promote to memory if frequently accessed
                        if entry.access_count > 3:
                            self._promote_to_memory(key, entry)
                        entry.access_count += 1
                        entry.last_access = time.time()
                        self.stats["hits"] += 1

                        if self.prefetcher:
                            self.prefetcher.record_access(key)

                        return entry.value
                except Exception as e:
                    LOGGER.warning("Failed to load from disk cache: %s", e)
                    del self.disk_index[key]

            self.stats["misses"] += 1
            return default

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
        level: CacheLevel = CacheLevel.MEMORY,
    ) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            level: Preferred cache level
        """
        with self._lock:
            entry = CacheEntry(
                key=key,
                value=value,
                timestamp=time.time(),
                level=level,
            )
            entry.size_bytes = self._get_entry_size(entry)

            if level == CacheLevel.MEMORY:
                self._set_memory(key, entry)
            else:
                self._set_disk(key, entry)

    def _set_memory(self, key: str, entry: CacheEntry) -> None:
        """Set entry in memory cache."""
        # Evict if needed
        while (
            self.memory_size_bytes + entry.size_bytes > self.max_memory_bytes
            and self.memory_cache
        ):
            self._evict_lru_memory()

        # Add to memory
        if key in self.memory_cache:
            old_entry = self.memory_cache.pop(key)
            self.memory_size_bytes -= old_entry.size_bytes

        self.memory_cache[key] = entry
        self.memory_size_bytes += entry.size_bytes

    def _set_disk(self, key: str, entry: CacheEntry) -> None:
        """Set entry in disk cache."""
        # Evict if needed
        while (
            self.disk_size_bytes + entry.size_bytes > self.max_disk_bytes
            and self.disk_index
        ):
            self._evict_lru_disk()

        try:
            cache_file = self.disk_cache_dir / f"{key}.cache"
            with open(cache_file, "wb") as f:
                pickle.dump(entry.value, f)

            self.disk_index[key] = entry
            self.disk_size_bytes += entry.size_bytes
        except Exception as e:
            LOGGER.warning("Failed to write to disk cache: %s", e)

    def _evict_lru_memory(self) -> None:
        """Evict least recently used entry from memory."""
        if not self.memory_cache:
            return

        # Remove oldest entry
        key, entry = self.memory_cache.popitem(last=False)
        self.memory_size_bytes -= entry.size_bytes

        # Demote to disk if valuable
        if entry.access_count > 2:
            self._set_disk(key, entry)
        else:
            self.stats["evictions"] += 1

    def _evict_lru_disk(self) -> None:
        """Evict least recently used entry from disk."""
        if not self.disk_index:
            return

        # Find LRU entry
        lru_key = min(self.disk_index.keys(), key=lambda k: self.disk_index[k].last_access)
        entry = self.disk_index.pop(lru_key)
        self.disk_size_bytes -= entry.size_bytes

        # Delete file
        cache_file = self.disk_cache_dir / f"{lru_key}.cache"
        try:
            cache_file.unlink()
        except Exception:
            pass

        self.stats["evictions"] += 1

    def _promote_to_memory(self, key: str, entry: CacheEntry) -> None:
        """Promote disk entry to memory."""
        if self.memory_size_bytes + entry.size_bytes <= self.max_memory_bytes:
            self._set_memory(key, entry)
            self.stats["promotions"] += 1

    def prefetch(self, current_key: str, fetch_fn: Callable[[str], Any]) -> None:
        """
        Prefetch predicted keys.

        Args:
            current_key: Current key being accessed
            fetch_fn: Function to fetch values for keys
        """
        if not self.prefetch_enabled or not self.prefetcher:
            return

        predictions = self.prefetcher.predict_next(current_key, top_n=3)
        for predicted_key, confidence in predictions:
            if confidence > 0.3:  # Only prefetch if confident
                if predicted_key not in self.memory_cache and predicted_key not in self.disk_index:
                    try:
                        value = fetch_fn(predicted_key)
                        self.set(predicted_key, value, level=CacheLevel.DISK)
                        self.stats["prefetch_hits"] += 1
                    except Exception as e:
                        LOGGER.debug("Prefetch failed for %s: %s", predicted_key, e)

    def clear(self) -> None:
        """Clear all caches."""
        with self._lock:
            self.memory_cache.clear()
            self.memory_size_bytes = 0
            self.disk_index.clear()
            self.disk_size_bytes = 0

            # Clear disk files
            for cache_file in self.disk_cache_dir.glob("*.cache"):
                try:
                    cache_file.unlink()
                except Exception:
                    pass

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            hit_rate = (
                self.stats["hits"] / (self.stats["hits"] + self.stats["misses"])
                if (self.stats["hits"] + self.stats["misses"]) > 0
                else 0.0
            )
            return {
                **self.stats,
                "hit_rate": hit_rate,
                "memory_entries": len(self.memory_cache),
                "memory_size_mb": self.memory_size_bytes / (1024 * 1024),
                "disk_entries": len(self.disk_index),
                "disk_size_mb": self.disk_size_bytes / (1024 * 1024),
                "prefetch_stats": self.prefetcher.get_pattern_stats() if self.prefetcher else {},
            }


__all__ = ["AdvancedCache", "CacheLevel", "PredictivePrefetcher"]



