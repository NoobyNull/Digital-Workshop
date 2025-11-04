"""
Query Optimization and Indexing System.

This module provides comprehensive query optimization, indexing strategies,
and performance monitoring for the database layer.
"""

import sqlite3
import time
import threading
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass
from contextlib import contextmanager

from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


@dataclass
class QueryPlan:
    """Query execution plan information."""

    query: str
    plan: str
    cost: float
    rows_examined: int
    cache_hits: int
    cache_misses: int
    execution_time: float


@dataclass
class IndexInfo:
    """Database index information."""

    name: str
    table: str
    columns: List[str]
    unique: bool
    size_kb: float
    usage_count: int
    last_used: Optional[str]


@dataclass
class QueryStats:
    """Query execution statistics."""

    query_pattern: str
    total_executions: int
    average_time: float
    min_time: float
    max_time: float
    cache_hit_rate: float
    last_executed: Optional[str]


class QueryCache:
    """LRU cache for query results with TTL support."""

    def __init__(self, max_size: int = 1000, ttl: float = 300.0):
        """
        Initialize query cache.

        Args:
            max_size: Maximum number of cached queries
            ttl: Time to live for cached results in seconds
        """
        self.max_size = max_size
        self.ttl = ttl
        self._cache = {}
        self._access_order = []
        self._lock = threading.Lock()

    def get(self, query: str, params: tuple = None) -> Optional[Any]:
        """
        Get cached result for query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Cached result or None if not found/expired
        """
        cache_key = (query, params)
        current_time = time.time()

        with self._lock:
            if cache_key in self._cache:
                result, timestamp = self._cache[cache_key]

                # Check if result is still valid
                if current_time - timestamp <= self.ttl:
                    # Move to end of access order
                    self._access_order.remove(cache_key)
                    self._access_order.append(cache_key)
                    return result
                else:
                    # Remove expired entry
                    del self._cache[cache_key]
                    self._access_order.remove(cache_key)

            return None

    def put(self, query: str, params: tuple, result: Any) -> None:
        """
        Cache query result.

        Args:
            query: SQL query string
            params: Query parameters
            result: Result to cache
        """
        cache_key = (query, params)
        current_time = time.time()

        with self._lock:
            # Remove existing entry if present
            if cache_key in self._cache:
                self._access_order.remove(cache_key)
            elif len(self._cache) >= self.max_size:
                # Remove least recently used item
                oldest_key = self._access_order.pop(0)
                del self._cache[oldest_key]

            # Add new entry
            self._cache[cache_key] = (result, current_time)
            self._access_order.append(cache_key)

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_entries = len(self._cache)
            total_size = sum(len(str(v[0])) for v in self._cache.values())

            return {
                "total_entries": total_entries,
                "total_size_bytes": total_size,
                "max_size": self.max_size,
                "ttl_seconds": self.ttl,
                "usage_rate": total_entries / self.max_size if self.max_size > 0 else 0,
            }


class QueryOptimizer:
    """Advanced query optimizer with indexing strategies."""

    def __init__(self, get_connection_func):
        """
        Initialize query optimizer.

        Args:
            get_connection_func: Function to get database connection
        """
        self._get_connection = get_connection_func
        self.query_cache = QueryCache()
        self._query_stats = defaultdict(QueryStats)
        self._index_usage = defaultdict(int)
        self._lock = threading.Lock()

    @log_function_call(logger)
    def analyze_query(self, query: str, params: tuple = None) -> QueryPlan:
        """
        Analyze query execution plan.

        Args:
            query: SQL query to analyze
            params: Query parameters

        Returns:
            QueryPlan object with execution details
        """
        start_time = time.time()

        try:
            with self._get_connection() as conn:
                # Enable query planning output
                cursor = conn.cursor()
                cursor.execute("EXPLAIN QUERY PLAN " + query, params or ())
                plan_rows = cursor.fetchall()

                # Execute query to get actual metrics
                cursor.execute(query, params or ())
                rows_examined = len(cursor.fetchall())

                # Calculate execution time
                execution_time = time.time() - start_time

                # Build plan description
                plan = " | ".join([f"{row[0]}.{row[1]}({row[2]})" for row in plan_rows])

                # Estimate cost (simplified)
                cost = self._estimate_query_cost(query, plan_rows)

                # Get cache statistics
                cache_result = self.query_cache.get(query, params)
                cache_hits = 1 if cache_result else 0
                cache_misses = 0 if cache_result else 1

                query_plan = QueryPlan(
                    query=query,
                    plan=plan,
                    cost=cost,
                    rows_examined=rows_examined,
                    cache_hits=cache_hits,
                    cache_misses=cache_misses,
                    execution_time=execution_time,
                )

                # Update statistics
                self._update_query_stats(
                    query, execution_time, cache_result is not None
                )

                logger.debug(
                    f"Query analyzed: {execution_time:.3f}s, cost: {cost:.2f}, rows: {rows_examined}"
                )
                return query_plan

        except sqlite3.Error as e:
            logger.error(f"Failed to analyze query: {str(e)}")
            raise

    def _estimate_query_cost(self, query: str, plan_rows: List[tuple]) -> float:
        """
        Estimate query execution cost.

        Args:
            query: SQL query
            plan_rows: Query plan rows

        Returns:
            Estimated cost value
        """
        cost = 0.0

        # Base cost components
        for row in plan_rows:
            detail = row[3] if len(row) > 3 else ""

            if "SCAN" in detail:
                cost += 1000  # Full table scan
            elif "SEARCH" in detail:
                cost += 10  # Index search
            elif "USE TEMP B-TREE" in detail:
                cost += 100  # Temporary index
            elif "USING INDEX" in detail:
                cost += 1  # Using existing index

        # Query type adjustments
        query_upper = query.upper().strip()
        if query_upper.startswith("SELECT"):
            cost *= 1.0
        elif query_upper.startswith("UPDATE") or query_upper.startswith("DELETE"):
            cost *= 2.0
        elif query_upper.startswith("INSERT"):
            cost *= 1.5

        return cost

    def _update_query_stats(
        self, query: str, execution_time: float, cache_hit: bool
    ) -> None:
        """
        Update query execution statistics.

        Args:
            query: SQL query
            execution_time: Execution time in seconds
            cache_hit: Whether result was from cache
        """
        with self._lock:
            # Extract query pattern (simplified)
            pattern = self._extract_query_pattern(query)

            stats = self._query_stats[pattern]
            stats.total_executions += 1
            stats.average_time = (
                stats.average_time * (stats.total_executions - 1) + execution_time
            ) / stats.total_executions
            stats.min_time = min(stats.min_time, execution_time)
            stats.max_time = max(stats.max_time, execution_time)
            stats.last_executed = time.strftime("%Y-%m-%d %H:%M:%S")

            # Update cache hit rate
            if cache_hit:
                # In a real implementation, we'd track hits separately
                stats.cache_hit_rate = min(1.0, stats.cache_hit_rate + 0.01)

    def _extract_query_pattern(self, query: str) -> str:
        """
        Extract query pattern for statistics.

        Args:
            query: SQL query

        Returns:
            Simplified query pattern
        """
        # Remove parameters and normalize whitespace
        pattern = " ".join(query.split()).upper()

        # Remove specific values but keep structure
        import re

        pattern = re.sub(r"'[^']*'", "?", pattern)  # String literals
        pattern = re.sub(r"\b\d+\b", "?", pattern)  # Numbers
        pattern = re.sub(r"\?", "?", pattern)  # Keep placeholders

        return pattern

    @log_function_call(logger)
    def execute_optimal_query(
        self, query: str, params: tuple = None, use_cache: bool = True
    ) -> List[tuple]:
        """
        Execute query with optimization and caching.

        Args:
            query: SQL query to execute
            params: Query parameters
            use_cache: Whether to use query cache

        Returns:
            Query results
        """
        # Check cache first
        if use_cache:
            cached_result = self.query_cache.get(query, params)
            if cached_result is not None:
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return cached_result

        start_time = time.time()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                results = cursor.fetchall()

                # Cache the result
                if use_cache:
                    self.query_cache.put(query, params, results)

                execution_time = time.time() - start_time
                logger.debug(
                    f"Query executed in {execution_time:.3f}s: {query[:50]}..."
                )

                return results

        except sqlite3.Error as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise

    def get_optimized_indexes(self) -> List[IndexInfo]:
        """
        Get recommended database indexes.

        Returns:
            List of recommended index information
        """
        recommended_indexes = []

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Analyze query patterns for index recommendations
                for pattern, stats in self._query_stats.items():
                    if (
                        stats.total_executions >= 10
                    ):  # Only for frequently executed queries
                        indexes = self._recommend_indexes_for_query(pattern)
                        recommended_indexes.extend(indexes)

                # Remove duplicates and get existing indexes
                existing_indexes = self._get_existing_indexes()
                existing_names = {idx.name for idx in existing_indexes}

                # Filter out existing indexes
                new_indexes = [
                    idx for idx in recommended_indexes if idx.name not in existing_names
                ]

                logger.info(f"Found {len(new_indexes)} new recommended indexes")
                return new_indexes

        except sqlite3.Error as e:
            logger.error(f"Failed to get recommended indexes: {str(e)}")
            return []

    def _recommend_indexes_for_query(self, query_pattern: str) -> List[IndexInfo]:
        """
        Recommend indexes for a query pattern.

        Args:
            query_pattern: Query pattern to analyze

        Returns:
            List of recommended IndexInfo objects
        """
        recommendations = []

        # Simple pattern-based recommendations
        if "WHERE" in query_pattern:
            # Look for equality conditions in WHERE clauses
            if "filename = ?" in query_pattern:
                recommendations.append(
                    IndexInfo(
                        name="idx_models_filename_optimal",
                        table="models",
                        columns=["filename"],
                        unique=False,
                        size_kb=0.0,
                        usage_count=0,
                        last_used=None,
                    )
                )

            if "format = ?" in query_pattern:
                recommendations.append(
                    IndexInfo(
                        name="idx_models_format_optimal",
                        table="models",
                        columns=["format"],
                        unique=False,
                        size_kb=0.0,
                        usage_count=0,
                        last_used=None,
                    )
                )

            if "category = ?" in query_pattern:
                recommendations.append(
                    IndexInfo(
                        name="idx_metadata_category_optimal",
                        table="model_metadata",
                        columns=["category"],
                        unique=False,
                        size_kb=0.0,
                        usage_count=0,
                        last_used=None,
                    )
                )

        # Composite indexes for common multi-column queries
        if "WHERE" in query_pattern and "ORDER BY" in query_pattern:
            if "filename" in query_pattern and "format" in query_pattern:
                recommendations.append(
                    IndexInfo(
                        name="idx_models_filename_format_optimal",
                        table="models",
                        columns=["filename", "format"],
                        unique=False,
                        size_kb=0.0,
                        usage_count=0,
                        last_used=None,
                    )
                )

        return recommendations

    def _get_existing_indexes(self) -> List[IndexInfo]:
        """
        Get information about existing database indexes.

        Returns:
            List of existing IndexInfo objects
        """
        indexes = []

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Get index information
                cursor.execute(
                    """
                    SELECT name, tbl_name, sql
                    FROM sqlite_master
                    WHERE type = 'index' AND sql IS NOT NULL
                """
                )

                for row in cursor.fetchall():
                    name, table, sql = row

                    # Extract columns from CREATE INDEX statement
                    columns = []
                    if sql:
                        import re

                        column_match = re.search(r"\(([^)]+)\)", sql)
                        if column_match:
                            columns = [
                                col.strip() for col in column_match.group(1).split(",")
                            ]

                    indexes.append(
                        IndexInfo(
                            name=name,
                            table=table,
                            columns=columns,
                            unique="UNIQUE" in sql.upper(),
                            size_kb=0.0,
                            usage_count=0,
                            last_used=None,
                        )
                    )

        except sqlite3.Error as e:
            logger.error(f"Failed to get existing indexes: {str(e)}")

        return indexes

    def create_recommended_indexes(self) -> List[str]:
        """
        Create all recommended indexes.

        Returns:
            List of created index names
        """
        created_indexes = []
        recommended = self.get_optimized_indexes()

        for idx in recommended:
            try:
                self._create_index(idx)
                created_indexes.append(idx.name)
                logger.info(f"Created index: {idx.name}")
            except Exception as e:
                logger.error(f"Failed to create index {idx.name}: {str(e)}")

        return created_indexes

    def _create_index(self, index_info: IndexInfo) -> None:
        """
        Create a database index.

        Args:
            index_info: Index information
        """
        columns_str = ", ".join(index_info.columns)

        create_sql = f"""
            CREATE INDEX IF NOT EXISTS {index_info.name}
            ON {index_info.table} ({columns_str})
        """

        with self._get_connection() as conn:
            conn.execute(create_sql)
            conn.commit()

    def analyze_and_optimize(self) -> Dict[str, Any]:
        """
        Perform comprehensive query optimization analysis.

        Returns:
            Dictionary with optimization results
        """
        results = {
            "query_stats": dict(self._query_stats),
            "recommended_indexes": [],
            "cache_stats": self.query_cache.get_stats(),
            "optimization_suggestions": [],
        }

        try:
            # Get recommended indexes
            results["recommended_indexes"] = [
                {
                    "name": idx.name,
                    "table": idx.table,
                    "columns": idx.columns,
                    "reason": "Based on query pattern analysis",
                }
                for idx in self.get_optimized_indexes()
            ]

            # Generate optimization suggestions
            slow_queries = [
                pattern
                for pattern, stats in self._query_stats.items()
                if stats.average_time > 0.1  # Queries taking more than 100ms
            ]

            if slow_queries:
                results["optimization_suggestions"].append(
                    f"Found {len(slow_queries)} slow queries that may benefit from optimization"
                )

            low_cache_hit_rate = [
                pattern
                for pattern, stats in self._query_stats.items()
                if stats.cache_hit_rate < 0.5 and stats.total_executions > 10
            ]

            if low_cache_hit_rate:
                results["optimization_suggestions"].append(
                    f"Found {len(low_cache_hit_rate)} queries with low cache hit rates"
                )

            logger.info("Query optimization analysis completed")

        except Exception as e:
            logger.error(f"Optimization analysis failed: {str(e)}")

        return results

    def get_slow_queries(self, threshold: float = 0.1) -> List[Tuple[str, QueryStats]]:
        """
        Get queries that are slower than threshold.

        Args:
            threshold: Time threshold in seconds

        Returns:
            List of (query_pattern, QueryStats) tuples
        """
        with self._lock:
            return [
                (pattern, stats)
                for pattern, stats in self._query_stats.items()
                if stats.average_time > threshold and stats.total_executions >= 5
            ]

    def clear_cache(self) -> None:
        """Clear the query cache."""
        self.query_cache.clear()
        logger.info("Query cache cleared")

    def reset_statistics(self) -> None:
        """Reset all query statistics."""
        with self._lock:
            self._query_stats.clear()
            self._index_usage.clear()
        logger.info("Query statistics reset")


class IndexManager:
    """Manager for database indexes with usage tracking."""

    def __init__(self, get_connection_func):
        """
        Initialize index manager.

        Args:
            get_connection_func: Function to get database connection
        """
        self._get_connection = get_connection_func
        self._index_usage = defaultdict(int)
        self._lock = threading.Lock()

    @log_function_call(logger)
    def create_performance_indexes(self) -> List[str]:
        """
        Create indexes optimized for performance.

        Returns:
            List of created index names
        """
        created_indexes = []

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Model table indexes
                indexes_to_create = [
                    # Primary search indexes
                    ("idx_models_filename_search", "models", "filename"),
                    ("idx_models_format_search", "models", "format"),
                    ("idx_models_file_hash_unique", "models", "file_hash"),
                    ("idx_models_date_added", "models", "date_added"),
                    ("idx_models_file_size", "models", "file_size"),
                    # Composite indexes for common queries
                    ("idx_models_format_date", "models", "format, date_added"),
                    ("idx_models_filename_format", "models", "filename, format"),
                    # Metadata table indexes
                    ("idx_metadata_model_id", "model_metadata", "model_id"),
                    ("idx_metadata_category", "model_metadata", "category"),
                    ("idx_metadata_title_search", "model_metadata", "title"),
                    ("idx_metadata_rating", "model_metadata", "rating"),
                    ("idx_metadata_view_count", "model_metadata", "view_count"),
                    ("idx_metadata_last_viewed", "model_metadata", "last_viewed"),
                    # Composite metadata indexes
                    (
                        "idx_metadata_category_rating",
                        "model_metadata",
                        "category, rating",
                    ),
                    (
                        "idx_metadata_category_view_count",
                        "model_metadata",
                        "category, view_count",
                    ),
                    # Full-text search support (if needed)
                    ("idx_metadata_keywords_search", "model_metadata", "keywords"),
                ]

                for idx_name, table, columns in indexes_to_create:
                    try:
                        create_sql = f"""
                            CREATE INDEX IF NOT EXISTS {idx_name}
                            ON {table} ({columns})
                        """
                        cursor.execute(create_sql)
                        created_indexes.append(idx_name)
                        logger.debug(f"Created index: {idx_name}")

                    except sqlite3.Error as e:
                        logger.warning(f"Failed to create index {idx_name}: {str(e)}")

                conn.commit()
                logger.info(f"Created {len(created_indexes)} performance indexes")

        except sqlite3.Error as e:
            logger.error(f"Failed to create performance indexes: {str(e)}")

        return created_indexes

    @log_function_call(logger)
    def analyze_index_usage(self) -> Dict[str, Any]:
        """
        Analyze index usage and performance.

        Returns:
            Dictionary with index analysis results
        """
        analysis = {
            "total_indexes": 0,
            "indexes_by_table": defaultdict(list),
            "index_usage_stats": {},
            "recommendations": [],
        }

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Get all indexes
                cursor.execute(
                    """
                    SELECT name, tbl_name, sql
                    FROM sqlite_master
                    WHERE type = 'index' AND sql IS NOT NULL
                """
                )

                for row in cursor.fetchall():
                    name, table, sql = row
                    analysis["total_indexes"] += 1
                    analysis["indexes_by_table"][table].append(name)

                # Analyze index effectiveness (simplified)
                for table, indexes in analysis["indexes_by_table"].items():
                    table_stats = {}
                    for idx_name in indexes:
                        # In a real implementation, this would query sqlite_stat1
                        # For now, just return basic info
                        table_stats[idx_name] = {
                            "usage_count": self._index_usage.get(idx_name, 0),
                            "effectiveness": "unknown",  # Would be calculated from query plans
                        }
                    analysis["index_usage_stats"][table] = table_stats

                # Generate recommendations
                if analysis["total_indexes"] == 0:
                    analysis["recommendations"].append(
                        "No indexes found - consider creating performance indexes"
                    )
                elif analysis["total_indexes"] < 5:
                    analysis["recommendations"].append(
                        "Consider adding more indexes for common query patterns"
                    )

        except sqlite3.Error as e:
            logger.error(f"Failed to analyze index usage: {str(e)}")

        return analysis

    def track_index_usage(self, index_name: str) -> None:
        """
        Track usage of an index.

        Args:
            index_name: Name of the index
        """
        with self._lock:
            self._index_usage[index_name] += 1

    def get_unused_indexes(self, min_usage: int = 10) -> List[str]:
        """
        Get indexes that haven't been used much.

        Args:
            min_usage: Minimum usage count to consider as "used"

        Returns:
            List of unused index names
        """
        with self._lock:
            all_indexes = set(self._index_usage.keys())
            used_indexes = {
                name for name, count in self._index_usage.items() if count >= min_usage
            }
            return list(all_indexes - used_indexes)

    def drop_unused_indexes(self, min_usage: int = 10) -> List[str]:
        """
        Drop indexes that haven't been used.

        Args:
            min_usage: Minimum usage count to keep index

        Returns:
            List of dropped index names
        """
        dropped_indexes = []
        unused_indexes = self.get_unused_indexes(min_usage)

        for idx_name in unused_indexes:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"DROP INDEX IF EXISTS {idx_name}")
                    conn.commit()

                    dropped_indexes.append(idx_name)
                    logger.info(f"Dropped unused index: {idx_name}")

            except sqlite3.Error as e:
                logger.error(f"Failed to drop index {idx_name}: {str(e)}")

        return dropped_indexes


@contextmanager
def query_performance_monitor(optimizer: QueryOptimizer, query: str):
    """
    Context manager to monitor query performance.

    Args:
        optimizer: QueryOptimizer instance
        query: SQL query being executed
    """
    start_time = time.time()
    try:
        yield
    finally:
        execution_time = time.time() - start_time
        if execution_time > 0.1:  # Log slow queries
            logger.warning(
                f"Slow query detected: {execution_time:.3f}s - {query[:100]}..."
            )
