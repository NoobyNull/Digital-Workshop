"""
Search repository module for model search and filtering operations.

Handles all search-related database operations including text search, filtering,
and specialized queries like recent and popular models.
"""

import sqlite3
from typing import Any, Dict, List, Optional

from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


class SearchRepository:
    """Repository for model search and filtering operations."""

    def __init__(self, get_connection_func) -> None:
        """
        Initialize search repository.

        Args:
            get_connection_func: Function to get database connection
        """
        self._get_connection = get_connection_func

    @log_function_call(logger)
    def search_models(
        self,
        query: str = "",
        category: Optional[str] = None,
        file_format: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for models by query and filters.

        Args:
            query: Search query string (searches filename, title, description, keywords)
            category: Filter by category
            file_format: Filter by file format
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of model dictionaries with metadata

        Raises:
            DatabaseError: If search operation fails
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                sql = """
                    SELECT m.*, mm.title, mm.description, mm.keywords, mm.category,
                           mm.source, mm.rating, mm.view_count, mm.last_viewed
                    FROM models m
                    LEFT JOIN model_metadata mm ON m.id = mm.model_id
                    WHERE 1=1
                """
                params = []

                if query:
                    sql += """ AND (
                        m.filename LIKE ? OR
                        mm.title LIKE ? OR
                        mm.description LIKE ? OR
                        mm.keywords LIKE ?
                    )"""
                    query_param = f"%{query}%"
                    params.extend([query_param] * 4)

                if category:
                    sql += " AND mm.category = ?"
                    params.append(category)

                if file_format:
                    sql += " AND m.format = ?"
                    params.append(file_format)

                # Add ordering and pagination
                sql += " ORDER BY m.date_added DESC"

                if limit:
                    sql += " LIMIT ?"
                    params.append(limit)
                if offset:
                    sql += " OFFSET ?"
                    params.append(offset)

                cursor.execute(sql, params)
                rows = cursor.fetchall()

                results = [dict(row) for row in rows]
                logger.debug(f"Search returned {len(results)} results for query: '{query}'")
                return results

        except sqlite3.Error as e:
            logger.error("Failed to search models: %s", e)
            raise

    @log_function_call(logger)
    def search_by_filename(self, filename: str) -> List[Dict[str, Any]]:
        """
        Search models by filename pattern.

        Args:
            filename: Filename pattern to search for

        Returns:
            List of matching model dictionaries
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT m.*, mm.title, mm.description, mm.keywords, mm.category,
                           mm.source, mm.rating, mm.view_count, mm.last_viewed
                    FROM models m
                    LEFT JOIN model_metadata mm ON m.id = mm.model_id
                    WHERE m.filename LIKE ?
                    ORDER BY m.filename ASC
                """,
                    (f"%{filename}%",),
                )

                rows = cursor.fetchall()
                results = [dict(row) for row in rows]
                logger.debug(f"Filename search returned {len(results)} results for: '{filename}'")
                return results

        except sqlite3.Error as e:
            logger.error("Failed to search by filename: %s", e)
            raise

    @log_function_call(logger)
    def search_by_metadata(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        keywords: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search models by metadata fields.

        Args:
            title: Title to search for
            description: Description to search for
            keywords: Keywords to search for

        Returns:
            List of matching model dictionaries
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                sql = """
                    SELECT m.*, mm.title, mm.description, mm.keywords, mm.category,
                           mm.source, mm.rating, mm.view_count, mm.last_viewed
                    FROM models m
                    LEFT JOIN model_metadata mm ON m.id = mm.model_id
                    WHERE 1=1
                """
                params = []

                if title:
                    sql += " AND mm.title LIKE ?"
                    params.append(f"%{title}%")

                if description:
                    sql += " AND mm.description LIKE ?"
                    params.append(f"%{description}%")

                if keywords:
                    sql += " AND mm.keywords LIKE ?"
                    params.append(f"%{keywords}%")

                sql += " ORDER BY m.date_added DESC"

                cursor.execute(sql, params)
                rows = cursor.fetchall()

                results = [dict(row) for row in rows]
                logger.debug("Metadata search returned %s results", len(results))
                return results

        except sqlite3.Error as e:
            logger.error("Failed to search by metadata: %s", e)
            raise

    @log_function_call(logger)
    def get_recent_models(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recently added models.

        Args:
            days: Number of days to look back
            limit: Maximum number of results

        Returns:
            List of recent model dictionaries
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT m.*, mm.title, mm.description, mm.keywords, mm.category,
                           mm.source, mm.rating, mm.view_count, mm.last_viewed
                    FROM models m
                    LEFT JOIN model_metadata mm ON m.id = mm.model_id
                    WHERE m.date_added >= datetime('now', '-{} days')
                    ORDER BY m.date_added DESC
                    LIMIT ?
                """.format(
                        days
                    ),
                    (limit,),
                )

                rows = cursor.fetchall()
                results = [dict(row) for row in rows]
                logger.debug("Found %s models from last {days} days", len(results))
                return results

        except sqlite3.Error as e:
            logger.error("Failed to get recent models: %s", e)
            raise

    @log_function_call(logger)
    def get_popular_models(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get models by view count.

        Args:
            limit: Maximum number of results

        Returns:
            List of popular model dictionaries
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT m.*, mm.title, mm.description, mm.keywords, mm.category,
                           mm.source, mm.rating, mm.view_count, mm.last_viewed
                    FROM models m
                    LEFT JOIN model_metadata mm ON m.id = mm.model_id
                    WHERE mm.view_count > 0
                    ORDER BY mm.view_count DESC, mm.last_viewed DESC
                    LIMIT ?
                """,
                    (limit,),
                )

                rows = cursor.fetchall()
                results = [dict(row) for row in rows]
                logger.debug("Found %s popular models", len(results))
                return results

        except sqlite3.Error as e:
            logger.error("Failed to get popular models: %s", e)
            raise
