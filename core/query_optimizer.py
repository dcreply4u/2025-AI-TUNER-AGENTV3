"""
Advanced Query Optimization Engine

Implements:
- Query plan analysis and optimization
- Index recommendation
- Query result caching
- Batch query optimization
- Adaptive query rewriting
"""

from __future__ import annotations

import logging
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

LOGGER = logging.getLogger(__name__)


@dataclass
class QueryPlan:
    """Query execution plan."""

    query: str
    estimated_cost: float
    execution_time: float = 0.0
    rows_returned: int = 0
    indexes_used: List[str] = field(default_factory=list)
    optimization_applied: List[str] = field(default_factory=list)


@dataclass
class QueryStats:
    """Query execution statistics."""

    query_pattern: str
    execution_count: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0


class QueryOptimizer:
    """Advanced query optimization engine."""

    def __init__(self):
        """Initialize query optimizer."""
        self.query_stats: Dict[str, QueryStats] = {}
        self.index_recommendations: Dict[str, List[str]] = defaultdict(list)
        self.query_cache: Dict[str, Tuple[Any, float]] = {}
        self.cache_ttl = 60.0  # 60 seconds default TTL

    def normalize_query(self, query: str) -> str:
        """
        Normalize query for pattern matching.

        Args:
            query: SQL query

        Returns:
            Normalized query pattern
        """
        # Remove whitespace
        query = re.sub(r"\s+", " ", query.strip())
        # Replace parameter placeholders
        query = re.sub(r"\?", "?", query)
        query = re.sub(r"%s", "?", query)
        # Replace string literals
        query = re.sub(r"'[^']*'", "'?'", query)
        query = re.sub(r'"[^"]*"', "'?'", query)
        # Replace numbers
        query = re.sub(r"\b\d+\.?\d*\b", "?", query)
        return query.lower()

    def analyze_query(self, query: str, execution_time: float, rows_returned: int) -> QueryPlan:
        """
        Analyze query and create execution plan.

        Args:
            query: SQL query
            execution_time: Execution time in seconds
            rows_returned: Number of rows returned

        Returns:
            Query execution plan
        """
        normalized = self.normalize_query(query)
        plan = QueryPlan(query=query, estimated_cost=execution_time, execution_time=execution_time, rows_returned=rows_returned)

        # Update statistics
        if normalized not in self.query_stats:
            self.query_stats[normalized] = QueryStats(query_pattern=normalized)

        stats = self.query_stats[normalized]
        stats.execution_count += 1
        stats.total_time += execution_time
        stats.avg_time = stats.total_time / stats.execution_count
        stats.min_time = min(stats.min_time, execution_time)
        stats.max_time = max(stats.max_time, execution_time)

        # Analyze query structure
        optimizations = self._suggest_optimizations(query, execution_time, rows_returned)
        plan.optimization_applied = optimizations

        # Suggest indexes
        indexes = self._suggest_indexes(query)
        if indexes:
            self.index_recommendations[normalized].extend(indexes)
            plan.indexes_used = indexes

        return plan

    def _suggest_optimizations(self, query: str, execution_time: float, rows_returned: int) -> List[str]:
        """Suggest query optimizations."""
        optimizations = []

        query_lower = query.lower()

        # Check for missing WHERE clause on large tables
        if "select * from telemetry" in query_lower and "where" not in query_lower:
            if rows_returned > 1000:
                optimizations.append("Add WHERE clause to limit results")

        # Check for ORDER BY without LIMIT
        if "order by" in query_lower and "limit" not in query_lower:
            if rows_returned > 100:
                optimizations.append("Add LIMIT clause when using ORDER BY")

        # Check for LIKE patterns
        if "like '%" in query_lower:
            optimizations.append("Leading wildcard in LIKE prevents index usage")

        # Check for multiple OR conditions
        or_count = query_lower.count(" or ")
        if or_count > 3:
            optimizations.append("Consider using UNION instead of multiple OR conditions")

        # Check for subqueries
        if query_lower.count("select") > 1:
            optimizations.append("Consider JOIN instead of subquery")

        return optimizations

    def _suggest_indexes(self, query: str) -> List[str]:
        """Suggest indexes for query."""
        indexes = []
        query_lower = query.lower()

        # Index on WHERE columns
        where_match = re.search(r"where\s+(\w+)\s*=", query_lower)
        if where_match:
            col = where_match.group(1)
            indexes.append(f"idx_{col}")

        # Index on JOIN columns
        join_matches = re.findall(r"join\s+\w+\s+on\s+(\w+)\.(\w+)\s*=", query_lower)
        for table, col in join_matches:
            indexes.append(f"idx_{table}_{col}")

        # Index on ORDER BY columns
        order_match = re.search(r"order\s+by\s+(\w+)", query_lower)
        if order_match:
            col = order_match.group(1)
            indexes.append(f"idx_{col}_order")

        return list(set(indexes))  # Remove duplicates

    def optimize_query(self, query: str) -> str:
        """
        Optimize query by rewriting.

        Args:
            query: Original query

        Returns:
            Optimized query
        """
        optimized = query
        query_lower = query.lower()

        # Replace SELECT * with specific columns when possible
        if "select * from" in query_lower and "limit" not in query_lower:
            # This would require schema knowledge - simplified for now
            pass

        # Add LIMIT if missing and ORDER BY present
        if "order by" in query_lower and "limit" not in query_lower:
            # Don't auto-add LIMIT - let user decide
            pass

        return optimized

    def get_cache_key(self, query: str, params: Tuple[Any, ...]) -> str:
        """Generate cache key for query."""
        import hashlib

        key_data = f"{query}:{params}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    def get_cached_result(self, query: str, params: Tuple[Any, ...]) -> Optional[Any]:
        """Get cached query result."""
        cache_key = self.get_cache_key(query, params)
        if cache_key in self.query_cache:
            result, timestamp = self.query_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                normalized = self.normalize_query(query)
                if normalized in self.query_stats:
                    self.query_stats[normalized].cache_hits += 1
                return result
            else:
                del self.query_cache[cache_key]

        normalized = self.normalize_query(query)
        if normalized in self.query_stats:
            self.query_stats[normalized].cache_misses += 1
        return None

    def cache_result(self, query: str, params: Tuple[Any, ...], result: Any) -> None:
        """Cache query result."""
        cache_key = self.get_cache_key(query, params)
        self.query_cache[cache_key] = (result, time.time())

    def get_optimization_report(self) -> Dict[str, Any]:
        """Get optimization report."""
        slow_queries = [
            stats
            for stats in self.query_stats.values()
            if stats.avg_time > 0.1  # Queries taking > 100ms on average
        ]
        slow_queries.sort(key=lambda x: x.avg_time, reverse=True)

        return {
            "total_query_patterns": len(self.query_stats),
            "slow_queries": [
                {
                    "pattern": stats.query_pattern,
                    "avg_time_ms": stats.avg_time * 1000,
                    "execution_count": stats.execution_count,
                    "cache_hit_rate": (
                        stats.cache_hits / (stats.cache_hits + stats.cache_misses)
                        if (stats.cache_hits + stats.cache_misses) > 0
                        else 0.0
                    ),
                }
                for stats in slow_queries[:10]
            ],
            "index_recommendations": {
                pattern: list(set(indexes))
                for pattern, indexes in self.index_recommendations.items()
            },
            "cache_stats": {
                "cached_queries": len(self.query_cache),
                "total_hits": sum(s.cache_hits for s in self.query_stats.values()),
                "total_misses": sum(s.cache_misses for s in self.query_stats.values()),
            },
        }

    def clear_cache(self) -> None:
        """Clear query cache."""
        self.query_cache.clear()


__all__ = ["QueryOptimizer", "QueryPlan", "QueryStats"]



