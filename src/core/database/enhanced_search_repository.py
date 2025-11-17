"""
Enhanced Search Repository with complete interface compliance.

This module provides a fully compliant implementation of ISearchRepository
with improved performance, transaction management, and error handling.
"""

import sqlite3
import re
import ast
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

from ..logging_config import get_logger, log_function_call
from ..interfaces.repository_interfaces import ISearchRepository

logger = get_logger(__name__)


class EnhancedSearchRepository(ISearchRepository):
    """
    Enhanced repository for search operations.

    Fully implements ISearchRepository interface with improved performance,
    transaction management, and comprehensive error handling.
    """

    def __init__(self, get_connection_func) -> None:
        """
        Initialize enhanced search repository.

        Args:
            get_connection_func: Function to get database connection
        """
        self._get_connection = get_connection_func

    @log_function_call(logger)
    def search_models(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Search for models using text query and filters.

        Args:
            query: Text search query
            filters: Optional additional filters

        Returns:
            List of model IDs matching the search criteria
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                sql = """
                    SELECT DISTINCT m.id
                    FROM models m
                    LEFT JOIN model_metadata mm ON m.id = mm.model_id
                    WHERE 1=1
                """
                params = []

                # Handle text search
                if query:
                    # Split query into words for better matching
                    search_terms = query.strip().split()
                    for term in search_terms:
                        sql += """
                            AND (
                                m.filename LIKE ? OR
                                mm.title LIKE ? OR
                                mm.description LIKE ? OR
                                mm.keywords LIKE ? OR
                                mm.category LIKE ?
                            )
                        """
                        search_pattern = f"%{term}%"
                        params.extend([search_pattern] * 5)

                # Handle filters
                if filters:
                    if "format" in filters:
                        sql += " AND m.format = ?"
                        params.append(filters["format"])

                    if "category" in filters:
                        sql += " AND mm.category = ?"
                        params.append(filters["category"])

                    if "min_file_size" in filters:
                        sql += " AND m.file_size >= ?"
                        params.append(filters["min_file_size"])

                    if "max_file_size" in filters:
                        sql += " AND m.file_size <= ?"
                        params.append(filters["max_file_size"])

                    if "min_rating" in filters:
                        sql += " AND mm.rating >= ?"
                        params.append(filters["min_rating"])

                    if "date_from" in filters:
                        sql += " AND m.date_added >= ?"
                        params.append(filters["date_from"])

                    if "date_to" in filters:
                        sql += " AND m.date_added <= ?"
                        params.append(filters["date_to"])

                sql += " ORDER BY m.date_added DESC"

                cursor.execute(sql, params)
                rows = cursor.fetchall()

                model_ids = [str(row[0]) for row in rows]
                logger.debug(f"Search returned {len(model_ids)} results for query: '{query}'")
                return model_ids

        except sqlite3.Error as e:
            logger.error("Failed to search models: %s", str(e))
            return []

    @log_function_call(logger)
    def search_by_tags(self, tags: List[str]) -> List[str]:
        """
        Search models by tags.

        Args:
            tags: List of tag names to search for

        Returns:
            List of model IDs containing any of the specified tags
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                sql = """
                    SELECT DISTINCT m.id
                    FROM models m
                    LEFT JOIN model_metadata mm ON m.id = mm.model_id
                    WHERE 1=0
                """
                params = []

                # Add OR conditions for each tag
                for tag in tags:
                    sql += " OR mm.keywords LIKE ?"
                    params.append(f"%{tag}%")

                sql += " ORDER BY m.date_added DESC"

                cursor.execute(sql, params)
                rows = cursor.fetchall()

                model_ids = [str(row[0]) for row in rows]
                logger.debug("Tag search returned %s results for tags: {tags}", len(model_ids))
                return model_ids

        except sqlite3.Error as e:
            logger.error("Failed to search by tags: %s", str(e))
            return []

    @log_function_call(logger)
    def search_by_date_range(self, start_date: str, end_date: str) -> List[str]:
        """
        Search models by date range.

        Args:
            start_date: Start date in ISO format
            end_date: End date in ISO format

        Returns:
            List of model IDs created within the date range
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT DISTINCT m.id
                    FROM models m
                    WHERE m.date_added BETWEEN ? AND ?
                    ORDER BY m.date_added DESC
                """,
                    (start_date, end_date),
                )

                rows = cursor.fetchall()
                model_ids = [str(row[0]) for row in rows]

                logger.debug("Date range search returned %s results", len(model_ids))
                return model_ids

        except sqlite3.Error as e:
            logger.error("Failed to search by date range: %s", str(e))
            return []

    @log_function_call(logger)
    def search_by_file_type(self, file_types: List[str]) -> List[str]:
        """
        Search models by file type.

        Args:
            file_types: List of file extensions (e.g., ['.stl', '.obj'])

        Returns:
            List of model IDs with matching file types
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                sql = """
                    SELECT DISTINCT m.id
                    FROM models m
                    WHERE 1=0
                """
                params = []

                # Add OR conditions for each file type
                for file_type in file_types:
                    sql += " OR m.format = ?"
                    params.append(file_type.lower().replace(".", ""))

                sql += " ORDER BY m.date_added DESC"

                cursor.execute(sql, params)
                rows = cursor.fetchall()

                model_ids = [str(row[0]) for row in rows]
                logger.debug(
                    f"File type search returned {len(model_ids)} results for types: {file_types}"
                )
                return model_ids

        except sqlite3.Error as e:
            logger.error("Failed to search by file type: %s", str(e))
            return []

    @log_function_call(logger)
    def get_search_suggestions(self, partial_query: str) -> List[str]:
        """
        Get search suggestions for partial query.

        Args:
            partial_query: Partial search query

        Returns:
            List of suggested search terms
        """
        try:
            suggestions = set()

            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Get suggestions from filenames
                cursor.execute(
                    """
                    SELECT DISTINCT filename
                    FROM models
                    WHERE filename LIKE ?
                    LIMIT 5
                """,
                    (f"%{partial_query}%",),
                )

                for row in cursor.fetchall():
                    filename = row[0]
                    # Extract words from filename
                    words = re.findall(r"\w+", filename.lower())
                    for word in words:
                        if partial_query.lower() in word and len(word) > 2:
                            suggestions.add(word)

                # Get suggestions from titles
                cursor.execute(
                    """
                    SELECT DISTINCT title
                    FROM model_metadata
                    WHERE title LIKE ? AND title IS NOT NULL
                    LIMIT 5
                """,
                    (f"%{partial_query}%",),
                )

                for row in cursor.fetchall():
                    title = row[0]
                    if title:
                        words = re.findall(r"\w+", title.lower())
                        for word in words:
                            if partial_query.lower() in word and len(word) > 2:
                                suggestions.add(word)

                # Get suggestions from categories
                cursor.execute(
                    """
                    SELECT DISTINCT category
                    FROM model_metadata
                    WHERE category LIKE ? AND category IS NOT NULL
                    LIMIT 5
                """,
                    (f"%{partial_query}%",),
                )

                for row in cursor.fetchall():
                    category = row[0]
                    if category:
                        words = re.findall(r"\w+", category.lower())
                        for word in words:
                            if partial_query.lower() in word and len(word) > 2:
                                suggestions.add(word)

            # Sort suggestions by relevance (shorter matches first)
            sorted_suggestions = sorted(list(suggestions), key=len)

            logger.debug(
                f"Generated {len(sorted_suggestions)} search suggestions for: '{partial_query}'"
            )
            return sorted_suggestions[:10]  # Limit to 10 suggestions

        except sqlite3.Error as e:
            logger.error("Failed to get search suggestions: %s", str(e))
            return []

    @log_function_call(logger)
    def save_search(self, name: str, query: str, filters: Dict[str, Any]) -> bool:
        """
        Save a search query for future use.

        Args:
            name: Name for the saved search
            query: Search query string
            filters: Search filters

        Returns:
            True if search was saved successfully, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Create saved_searches table if it doesn't exist
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS saved_searches (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        query TEXT NOT NULL,
                        filters TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Save the search
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO saved_searches (name, query, filters)
                    VALUES (?, ?, ?)
                """,
                    (name, query, str(filters)),
                )

                success = cursor.rowcount > 0
                conn.commit()

                if success:
                    logger.info(f"Saved search '{name}'")
                else:
                    logger.warning(f"Failed to save search '{name}'")

                return success

        except sqlite3.Error as e:
            logger.error(f"Failed to save search '{name}': {str(e)}")
            return False

    @log_function_call(logger)
    def get_saved_searches(self) -> List[Dict[str, Any]]:
        """
        Get all saved searches.

        Returns:
            List of dictionaries containing saved search information
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT * FROM saved_searches
                    ORDER BY created_at DESC
                """
                )

                rows = cursor.fetchall()
                searches = []

                for row in rows:
                    search = dict(row)
                    # Parse filters string back to dict (safe alternative to eval)
                    filters_str = search.get("filters")
                    if filters_str:
                        try:
                            search["filters"] = ast.literal_eval(filters_str)
                        except (ValueError, SyntaxError):
                            search["filters"] = {}
                    else:
                        search["filters"] = {}
                    searches.append(search)

                logger.debug("Retrieved %s saved searches", len(searches))
                return searches

        except sqlite3.Error as e:
            logger.error("Failed to get saved searches: %s", str(e))
            return []

    @log_function_call(logger)
    def delete_saved_search(self, search_id: str) -> bool:
        """
        Delete a saved search.

        Args:
            search_id: Unique identifier of the saved search

        Returns:
            True if search was deleted successfully, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM saved_searches WHERE id = ?", (search_id,))

                success = cursor.rowcount > 0
                conn.commit()

                if success:
                    logger.info("Deleted saved search %s", search_id)
                else:
                    logger.warning("Saved search %s not found for deletion", search_id)

                return success

        except sqlite3.Error as e:
            logger.error("Failed to delete saved search %s: {str(e)}", search_id)
            return False

    # Additional enhanced search methods for better functionality

    @log_function_call(logger)
    def advanced_search(self, search_config: Dict[str, Any]) -> List[str]:
        """
        Perform advanced search with complex criteria.

        Args:
            search_config: Dictionary containing advanced search configuration

        Returns:
            List of model IDs matching the search criteria
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                sql = """
                    SELECT DISTINCT m.id
                    FROM models m
                    LEFT JOIN model_metadata mm ON m.id = mm.model_id
                    WHERE 1=1
                """
                params = []

                # Handle text search with multiple fields
                if "text_query" in search_config:
                    text_query = search_config["text_query"]
                    search_terms = text_query.strip().split()

                    for term in search_terms:
                        sql += """
                            AND (
                                m.filename LIKE ? OR
                                m.file_path LIKE ? OR
                                mm.title LIKE ? OR
                                mm.description LIKE ? OR
                                mm.keywords LIKE ?
                            )
                        """
                        search_pattern = f"%{term}%"
                        params.extend([search_pattern] * 5)

                # Handle file size range
                if "min_file_size" in search_config:
                    sql += " AND m.file_size >= ?"
                    params.append(search_config["min_file_size"])

                if "max_file_size" in search_config:
                    sql += " AND m.file_size <= ?"
                    params.append(search_config["max_file_size"])

                # Handle rating range
                if "min_rating" in search_config:
                    sql += " AND mm.rating >= ?"
                    params.append(search_config["min_rating"])

                if "max_rating" in search_config:
                    sql += " AND mm.rating <= ?"
                    params.append(search_config["max_rating"])

                # Handle view count range
                if "min_views" in search_config:
                    sql += " AND mm.view_count >= ?"
                    params.append(search_config["min_views"])

                if "max_views" in search_config:
                    sql += " AND mm.view_count <= ?"
                    params.append(search_config["max_views"])

                # Handle date ranges
                if "date_added_from" in search_config:
                    sql += " AND m.date_added >= ?"
                    params.append(search_config["date_added_from"])

                if "date_added_to" in search_config:
                    sql += " AND m.date_added <= ?"
                    params.append(search_config["date_added_to"])

                # Handle categories (OR condition)
                if "categories" in search_config and search_config["categories"]:
                    sql += " AND ("
                    category_conditions = []
                    for category in search_config["categories"]:
                        category_conditions.append("mm.category = ?")
                        params.append(category)
                    sql += " OR ".join(category_conditions) + ")"

                # Handle file formats (OR condition)
                if "file_formats" in search_config and search_config["file_formats"]:
                    sql += " AND ("
                    format_conditions = []
                    for format_type in search_config["file_formats"]:
                        format_conditions.append("m.format = ?")
                        params.append(format_type)
                    sql += " OR ".join(format_conditions) + ")"

                # Handle keywords (OR condition)
                if "keywords" in search_config and search_config["keywords"]:
                    sql += " AND ("
                    keyword_conditions = []
                    for keyword in search_config["keywords"]:
                        keyword_conditions.append("mm.keywords LIKE ?")
                        params.append(f"%{keyword}%")
                    sql += " OR ".join(keyword_conditions) + ")"

                # Add ordering
                order_by = search_config.get("order_by", "date_added")
                order_direction = search_config.get("order_direction", "DESC")

                if order_by == "date_added":
                    sql += f" ORDER BY m.date_added {order_direction}"
                elif order_by == "filename":
                    sql += f" ORDER BY m.filename {order_direction}"
                elif order_by == "file_size":
                    sql += f" ORDER BY m.file_size {order_direction}"
                elif order_by == "rating":
                    sql += f" ORDER BY mm.rating {order_direction}"
                elif order_by == "view_count":
                    sql += f" ORDER BY mm.view_count {order_direction}"

                # Add pagination
                if "limit" in search_config:
                    sql += " LIMIT ?"
                    params.append(search_config["limit"])

                if "offset" in search_config:
                    sql += " OFFSET ?"
                    params.append(search_config["offset"])

                cursor.execute(sql, params)
                rows = cursor.fetchall()

                model_ids = [str(row[0]) for row in rows]
                logger.debug("Advanced search returned %s results", len(model_ids))
                return model_ids

        except sqlite3.Error as e:
            logger.error("Failed to perform advanced search: %s", str(e))
            return []

    @log_function_call(logger)
    def get_search_statistics(self) -> Dict[str, Any]:
        """
        Get search-related statistics.

        Returns:
            Dictionary containing search statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                stats = {}

                # Get total saved searches
                cursor.execute("SELECT COUNT(*) FROM saved_searches")
                stats["saved_searches_count"] = cursor.fetchone()[0]

                # Get most popular search terms (from keywords)
                cursor.execute(
                    """
                    SELECT keywords, COUNT(*) as usage_count
                    FROM model_metadata
                    WHERE keywords IS NOT NULL AND keywords != ''
                    GROUP BY keywords
                    ORDER BY usage_count DESC
                    LIMIT 10
                """
                )
                stats["popular_keywords"] = cursor.fetchall()

                # Get most searched categories
                cursor.execute(
                    """
                    SELECT category, COUNT(*) as usage_count
                    FROM model_metadata
                    WHERE category IS NOT NULL
                    GROUP BY category
                    ORDER BY usage_count DESC
                    LIMIT 10
                """
                )
                stats["popular_categories"] = cursor.fetchall()

                # Get file format distribution
                cursor.execute(
                    """
                    SELECT format, COUNT(*) as count
                    FROM models
                    GROUP BY format
                    ORDER BY count DESC
                """
                )
                stats["format_distribution"] = cursor.fetchall()

                logger.debug("Retrieved search statistics")
                return stats

        except sqlite3.Error as e:
            logger.error("Failed to get search statistics: %s", str(e))
            return {}

    @contextmanager
    def transaction(self) -> None:
        """
        Context manager for database transactions.

        Yields:
            Database connection with transaction support
        """
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
