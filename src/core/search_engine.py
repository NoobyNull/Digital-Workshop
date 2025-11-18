"""
Search engine for Digital Workshop using SQLite FTS5.

This module provides advanced search functionality including full-text search,
filtering, search history, and saved searches with proper error handling
and logging integration.
"""

import json
import re
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from .database_manager import get_database_manager
from .logging_config import get_logger, log_function_call

# Initialize logger
logger = get_logger(__name__)


def parse_search_query_language(raw_query: str) -> Tuple[str, Dict[str, Any]]:
    """Parse the mini search language from a raw query string.

    The supported constructs are::

        tag=foo      # include tag "foo"
        tag!=bar     # exclude tag "bar"
        inProject    # only models that belong to at least one project
        !inProject   # only models that are not linked to any project
        LAT>=N       # last accessed at least N days ago (stale models)

    Everything that does not match these constructs is treated as free-text
    and passed unchanged to the FTS layer.

    Args:
        raw_query: Full query string as typed by the user.

    Returns:
        A tuple of (free_text_query, extra_filters_dict).
    """
    if not raw_query or not raw_query.strip():
        return "", {}

    tokens = raw_query.strip().split()
    tags_include: List[str] = []
    tags_exclude: List[str] = []
    in_project: Optional[bool] = None
    lat_days: Optional[int] = None
    filter_indices: Set[int] = set()

    # First pass: identify and extract filter tokens
    for idx, token in enumerate(tokens):
        stripped = token.strip()
        if not stripped:
            continue

        upper = stripped.upper()
        lower = stripped.lower()

        # inProject / !inProject
        if upper == "INPROJECT":
            in_project = True
            filter_indices.add(idx)
            continue
        if upper == "!INPROJECT":
            in_project = False
            filter_indices.add(idx)
            continue

        # LAT comparisons, currently only LAT>=N is supported
        # Accept forms like "LAT>=30" (case-insensitive, no spaces)
        lat_match = re.match(r"(?i)LAT\s*(>=)\s*(\d+)$", stripped)
        if lat_match:
            try:
                lat_days = int(lat_match.group(2))
                filter_indices.add(idx)
                continue
            except ValueError:
                # Fall through and treat as free-text if parsing fails
                pass

        # Tag inclusion / exclusion
        # Check exclusion first so "tag!=foo" does not match the "tag=" prefix
        if lower.startswith("tag!="):
            value = stripped[5:].strip().strip('\"\'')
            if value:
                tags_exclude.append(value)
                filter_indices.add(idx)
                continue

        if lower.startswith("tag="):
            value = stripped[4:].strip().strip('\"\'')
            if value:
                tags_include.append(value)
                filter_indices.add(idx)
                continue

    # Deduplicate while preserving order
    def _dedupe(values: List[str]) -> List[str]:
        seen: Set[str] = set()
        result: List[str] = []
        for v in values:
            key = v.lower()
            if key in seen:
                continue
            seen.add(key)
            result.append(v)
        return result

    tags_include = _dedupe(tags_include)
    tags_exclude = _dedupe(tags_exclude)

    # Second pass: rebuild the free-text part, skipping filter tokens.
    # We only keep boolean connectors (AND/OR/NOT) when they sit between
    # two non-filter, non-connector tokens so that the resulting FTS
    # expression stays well-formed.
    free_text_tokens: List[str] = []

    def _is_connector(tok: str) -> bool:
        return tok.upper() in {"AND", "OR", "NOT"}

    for idx, token in enumerate(tokens):
        if idx in filter_indices:
            continue

        if _is_connector(token):
            left_ok = (
                idx > 0
                and idx - 1 not in filter_indices
                and not _is_connector(tokens[idx - 1])
            )
            right_ok = (
                idx + 1 < len(tokens)
                and idx + 1 not in filter_indices
                and not _is_connector(tokens[idx + 1])
            )
            if left_ok and right_ok:
                free_text_tokens.append(token)
            continue

        free_text_tokens.append(token)

    free_text_query = " ".join(free_text_tokens).strip()

    # If free text consists solely of connectors, drop it entirely
    if free_text_query:
        parts = free_text_query.split()
        if all(_is_connector(p) for p in parts):
            free_text_query = ""

    extra_filters: Dict[str, Any] = {}
    if tags_include:
        extra_filters["tags_include"] = tags_include
    if tags_exclude:
        extra_filters["tags_exclude"] = tags_exclude
    if in_project is not None:
        extra_filters["in_project"] = in_project
    if lat_days is not None:
        extra_filters["lat_days"] = lat_days

    return free_text_query, extra_filters


class SearchEngine:
    """
    Search engine for Digital Workshop.

    Provides full-text search using SQLite FTS5, filtering options,
    search history, and saved searches functionality.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        """
        Initialize the search engine.

        Args:
            db_path: Path to the SQLite database file. If None, uses AppData location.
        """
        self.db_manager = get_database_manager(db_path)
        self._lock = threading.Lock()

        logger.info("Initializing search engine")

        # Initialize FTS5 tables
        self._initialize_fts_tables()

    @log_function_call(logger)
    def _initialize_fts_tables(self) -> None:
        """
        Initialize FTS5 virtual tables for full-text search.

        Creates virtual tables for models and metadata with proper
        triggers to keep them synchronized with the main tables.
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Create FTS5 virtual table for models
                cursor.execute(
                    """
                    CREATE VIRTUAL TABLE IF NOT EXISTS models_fts USING fts5(
                        filename,
                        format,
                        file_path,
                        content='models',
                        content_rowid='id'
                    )
                """
                )

                # Create FTS5 virtual table for model metadata
                cursor.execute(
                    """
                    CREATE VIRTUAL TABLE IF NOT EXISTS model_metadata_fts USING fts5(
                        title,
                        description,
                        keywords,
                        category,
                        source,
                        content='model_metadata',
                        content_rowid='model_id'
                    )
                """
                )

                # Create triggers to keep FTS tables synchronized
                self._create_fts_triggers(cursor)

                # Populate FTS tables with existing data
                self._populate_fts_tables(cursor)

                conn.commit()
                logger.info("FTS5 tables initialized successfully")

        except sqlite3.Error as e:
            logger.error("Failed to initialize FTS5 tables: %s", str(e))
            raise

    @log_function_call(logger)
    def _create_fts_triggers(self, cursor: sqlite3.Cursor) -> None:
        """
        Create triggers to keep FTS tables synchronized with main tables.

        Args:
            cursor: SQLite cursor object
        """
        # Triggers for models table
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS models_ai AFTER INSERT ON models BEGIN
                INSERT INTO models_fts(rowid, filename, format, file_path)
                VALUES (new.id, new.filename, new.format, new.file_path);
            END
        """
        )

        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS models_ad AFTER DELETE ON models BEGIN
                INSERT INTO models_fts(models_fts, rowid, filename, format, file_path)
                VALUES ('delete', old.id, old.filename, old.format, old.file_path);
            END
        """
        )

        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS models_au AFTER UPDATE ON models BEGIN
                INSERT INTO models_fts(models_fts, rowid, filename, format, file_path)
                VALUES ('delete', old.id, old.filename, old.format, old.file_path);
                INSERT INTO models_fts(rowid, filename, format, file_path)
                VALUES (new.id, new.filename, new.format, new.file_path);
            END
        """
        )

        # Triggers for model_metadata table
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS model_metadata_ai AFTER INSERT ON model_metadata BEGIN
                INSERT INTO model_metadata_fts(rowid, title, description, keywords, category, source)
                VALUES (new.model_id, new.title, new.description, new.keywords, new.category, new.source);
            END
        """
        )

        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS model_metadata_ad AFTER DELETE ON model_metadata BEGIN
                INSERT INTO model_metadata_fts(model_metadata_fts, rowid, title, description, keywords, category, source)
                VALUES ('delete', old.model_id, old.title, old.description, old.keywords, old.category, old.source);
            END
        """
        )

        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS model_metadata_au AFTER UPDATE ON model_metadata BEGIN
                INSERT INTO model_metadata_fts(model_metadata_fts, rowid, title, description, keywords, category, source)
                VALUES ('delete', old.model_id, old.title, old.description, old.keywords, old.category, old.source);
                INSERT INTO model_metadata_fts(rowid, title, description, keywords, category, source)
                VALUES (new.model_id, new.title, new.description, new.keywords, new.category, new.source);
            END
        """
        )

    @log_function_call(logger)
    def _populate_fts_tables(self, cursor: sqlite3.Cursor) -> None:
        """
        Populate FTS tables with existing data from main tables.

        Args:
            cursor: SQLite cursor object
        """
        # Populate models_fts
        cursor.execute(
            """
            INSERT OR IGNORE INTO models_fts(rowid, filename, format, file_path)
            SELECT id, filename, format, file_path FROM models
        """
        )

        # Populate model_metadata_fts
        cursor.execute(
            """
            INSERT OR IGNORE INTO model_metadata_fts(rowid, title, description, keywords, category, source)
            SELECT model_id, title, description, keywords, category, source FROM model_metadata
        """
        )

        logger.info("FTS tables populated with existing data")

    @log_function_call(logger)
    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Perform a full-text search with optional filters.

        Args:
            query: Search query string
            filters: Dictionary of filters (category, format, rating, date_range)
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Dictionary with search results and metadata
        """
        if not query.strip() and not filters:
            logger.warning("Empty search query and no filters provided")
            return {"results": [], "total_count": 0, "query": query, "filters": filters}

        start_time = datetime.now()

        try:
            with self.db_manager.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Build the search query
                search_query, params = self._build_search_query(query, filters)

                # Get total count
                count_query = f"SELECT COUNT(*) FROM ({search_query})"
                cursor.execute(count_query, params)
                total_count = cursor.fetchone()[0]

                # Add pagination
                search_query += " ORDER BY rank DESC, last_viewed DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])

                # Execute search
                cursor.execute(search_query, params)
                rows = cursor.fetchall()

                # Process results
                results = []
                for row in rows:
                    result = dict(row)
                    # Add highlighted snippets
                    result["highlights"] = self._generate_highlights(query, result)
                    results.append(result)

                # Record search in history
                self._record_search(query, filters, len(results))

                # Calculate execution time
                execution_time = (datetime.now() - start_time).total_seconds()

                logger.info("Search completed in %.3fs: %d results", execution_time, len(results))

                return {
                    "results": results,
                    "total_count": total_count,
                    "query": query,
                    "filters": filters,
                    "execution_time": execution_time,
                }

        except sqlite3.Error as e:
            logger.error("Search failed: %s", str(e))
            raise

    @log_function_call(logger)
    def _build_search_query(
        self, query: str, filters: Optional[Dict[str, Any]]
    ) -> Tuple[str, List]:
        """
        Build the SQL search query with FTS5 and filters.

        Args:
            query: Search query string
            filters: Dictionary of filters

        Returns:
            Tuple of (SQL query, parameter list)
        """
        # Base query with FTS5
        sql = """
            SELECT
                m.*, mm.title, mm.description, mm.keywords, mm.category,
                mm.source, mm.rating, mm.view_count, mm.last_viewed,
                bm25(models_fts) + bm25(model_metadata_fts) as rank
            FROM models m
            LEFT JOIN model_metadata mm ON m.id = mm.model_id
            LEFT JOIN models_fts ON m.id = models_fts.rowid
            LEFT JOIN model_metadata_fts ON mm.model_id = model_metadata_fts.rowid
            WHERE 1=1
        """

        params = []

        # Add FTS5 match condition if query is provided
        if query and query.strip():
            # Process query for FTS5 (handle boolean operators)
            fts_query = self._process_fts_query(query)
            sql += f" AND (models_fts MATCH ? OR model_metadata_fts MATCH ?)"
            params.extend([fts_query, fts_query])

        # Add filters
        if filters:
            # Category filter
            if "category" in filters and filters["category"]:
                if isinstance(filters["category"], list):
                    placeholders = ",".join(["?" for _ in filters["category"]])
                    sql += f" AND mm.category IN ({placeholders})"
                    params.extend(filters["category"])
                else:
                    sql += " AND mm.category = ?"
                    params.append(filters["category"])

            # Format filter
            if "format" in filters and filters["format"]:
                if isinstance(filters["format"], list):
                    placeholders = ",".join(["?" for _ in filters["format"]])
                    sql += f" AND m.format IN ({placeholders})"
                    params.extend(filters["format"])
                else:
                    sql += " AND m.format = ?"
                    params.append(filters["format"])

            # Rating filter
            if "min_rating" in filters and filters["min_rating"]:
                sql += " AND mm.rating >= ?"
                params.append(filters["min_rating"])

            # Date range filter
            if "date_added_start" in filters and filters["date_added_start"]:
                sql += " AND m.date_added >= ?"
                params.append(filters["date_added_start"])

            if "date_added_end" in filters and filters["date_added_end"]:
                sql += " AND m.date_added <= ?"
                params.append(filters["date_added_end"])

            if "last_viewed_start" in filters and filters["last_viewed_start"]:
                sql += " AND mm.last_viewed >= ?"
                params.append(filters["last_viewed_start"])

            if "last_viewed_end" in filters and filters["last_viewed_end"]:
                sql += " AND mm.last_viewed <= ?"
                params.append(filters["last_viewed_end"])

            # File size filter
            if "min_file_size" in filters and filters["min_file_size"]:
                sql += " AND m.file_size >= ?"
                params.append(filters["min_file_size"])

            if "max_file_size" in filters and filters["max_file_size"]:
                sql += " AND m.file_size <= ?"
                params.append(filters["max_file_size"])

            # Tag filters (from mini-language or other callers)
            tags_include = filters.get("tags_include") or []
            tags_exclude = filters.get("tags_exclude") or []

            if isinstance(tags_include, str):
                tags_include = [tags_include]
            if isinstance(tags_exclude, str):
                tags_exclude = [tags_exclude]

            for tag in tags_include:
                tag_value = str(tag).strip()
                if not tag_value:
                    continue
                sql += (
                    " AND mm.keywords IS NOT NULL"
                    " AND (',' || LOWER(REPLACE(mm.keywords, ' ', '')) || ',') LIKE ?"
                )
                params.append(f"%,{tag_value.lower().replace(' ', '')},%")

            for tag in tags_exclude:
                tag_value = str(tag).strip()
                if not tag_value:
                    continue
                sql += (
                    " AND (mm.keywords IS NULL"
                    " OR (',' || LOWER(REPLACE(mm.keywords, ' ', '')) || ',') NOT LIKE ?)"
                )
                params.append(f"%,{tag_value.lower().replace(' ', '')},%")

            # Project membership filter (inProject / !inProject)
            in_project = filters.get("in_project")
            if in_project is True:
                sql += """
                    AND EXISTS (
                        SELECT 1
                        FROM project_models pm
                        WHERE pm.model_id = m.id
                    )
                """
            elif in_project is False:
                sql += """
                    AND NOT EXISTS (
                        SELECT 1
                        FROM project_models pm
                        WHERE pm.model_id = m.id
                    )
                """

            # LAT filter: LAT>=N means last accessed at least N days ago
            lat_days = filters.get("lat_days")
            if isinstance(lat_days, (int, float)) and lat_days > 0:
                cutoff = datetime.now() - timedelta(days=int(lat_days))
                cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")
                sql += " AND (mm.last_viewed IS NULL OR mm.last_viewed <= ?)"
                params.append(cutoff_str)

        return sql, params

    @log_function_call(logger)
    def _process_fts_query(self, query: str) -> str:
        """
        Process search query for FTS5 with boolean operators.

        Args:
            query: Raw search query

        Returns:
            Processed FTS5 query
        """
        # Handle boolean operators
        processed = query.strip()

        # Convert common boolean operators to FTS5 syntax
        processed = re.sub(r"\bAND\b", "AND", processed, flags=re.IGNORECASE)
        processed = re.sub(r"\bOR\b", "OR", processed, flags=re.IGNORECASE)
        processed = re.sub(r"\bNOT\b", "NOT", processed, flags=re.IGNORECASE)

        # Handle exact phrases in quotes
        phrase_matches = re.findall(r'"([^"]*)"', processed)
        for phrase in phrase_matches:
            # Keep phrases as-is for FTS5
            processed = processed.replace(f'"{phrase}"', f'"{phrase}"')

        # Handle parentheses for grouping
        processed = processed.replace("(", " ( ").replace(")", " ) ")

        # Clean up extra spaces
        processed = re.sub(r"\s+", " ", processed).strip()

        # If no boolean operators, add implicit AND between terms
        if not re.search(r"\b(AND|OR|NOT)\b", processed, re.IGNORECASE):
            terms = processed.split()
            if len(terms) > 1:
                processed = " AND ".join(terms)

        return processed

    @log_function_call(logger)
    def _generate_highlights(self, query: str, result: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate highlighted snippets for search results.

        Args:
            query: Search query
            result: Search result dictionary

        Returns:
            Dictionary with highlighted fields
        """
        highlights = {}
        query_terms = re.findall(r"\b\w+\b", query.lower())

        # Highlight title
        if result.get("title"):
            highlights["title"] = self._highlight_text(result["title"], query_terms)

        # Highlight description
        if result.get("description"):
            highlights["description"] = self._highlight_text(result["description"], query_terms)

        # Highlight keywords
        if result.get("keywords"):
            highlights["keywords"] = self._highlight_text(result["keywords"], query_terms)

        # Highlight filename
        if result.get("filename"):
            highlights["filename"] = self._highlight_text(result["filename"], query_terms)

        return highlights

    @log_function_call(logger)
    def _highlight_text(self, text: str, query_terms: List[str]) -> str:
        """
        Highlight query terms in text.

        Args:
            text: Text to highlight
            query_terms: List of query terms

        Returns:
            Text with highlighted terms
        """
        if not text:
            return ""

        highlighted = text
        for term in query_terms:
            # Case-insensitive highlighting
            pattern = re.compile(f"({re.escape(term)})", re.IGNORECASE)
            highlighted = pattern.sub(r"<mark>\1</mark>", highlighted)

        return highlighted

    @log_function_call(logger)
    def _record_search(
        self, query: str, filters: Optional[Dict[str, Any]], result_count: int
    ) -> None:
        """
        Record search in search history.

        Args:
            query: Search query
            filters: Search filters
            result_count: Number of results
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Create search_history table if it doesn't exist
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS search_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query TEXT NOT NULL,
                        filters TEXT,
                        result_count INTEGER,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Insert search record
                filters_json = json.dumps(filters) if filters else None
                cursor.execute(
                    """
                    INSERT INTO search_history (query, filters, result_count)
                    VALUES (?, ?, ?)
                """,
                    (query, filters_json, result_count),
                )

                conn.commit()

        except sqlite3.Error as e:
            logger.warning("Failed to record search: %s", str(e))

    @log_function_call(logger)
    def get_search_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get search history.

        Args:
            limit: Maximum number of history items

        Returns:
            List of search history items
        """
        try:
            with self.db_manager.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT * FROM search_history
                    ORDER BY timestamp DESC
                    LIMIT ?
                """,
                    (limit,),
                )

                rows = cursor.fetchall()
                history = []

                for row in rows:
                    item = dict(row)
                    if item["filters"]:
                        item["filters"] = json.loads(item["filters"])
                    history.append(item)

                return history

        except sqlite3.Error as e:
            logger.error("Failed to get search history: %s", str(e))
            return []

    @log_function_call(logger)
    def save_search(self, name: str, query: str, filters: Optional[Dict[str, Any]]) -> int:
        """
        Save a search for later use.

        Args:
            name: Name for the saved search
            query: Search query
            filters: Search filters

        Returns:
            ID of the saved search
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Create saved_searches table if it doesn't exist
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS saved_searches (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        query TEXT NOT NULL,
                        filters TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Insert saved search
                filters_json = json.dumps(filters) if filters else None
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO saved_searches (name, query, filters)
                    VALUES (?, ?, ?)
                """,
                    (name, query, filters_json),
                )

                search_id = cursor.lastrowid
                conn.commit()

                logger.info(f"Saved search '{name}' with ID: {search_id}")
                return search_id

        except sqlite3.Error as e:
            logger.error("Failed to save search: %s", str(e))
            raise

    @log_function_call(logger)
    def get_saved_searches(self) -> List[Dict[str, Any]]:
        """
        Get all saved searches.

        Returns:
            List of saved searches
        """
        try:
            with self.db_manager.get_connection() as conn:
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
                    if search["filters"]:
                        search["filters"] = json.loads(search["filters"])
                    searches.append(search)

                return searches

        except sqlite3.Error as e:
            logger.error("Failed to get saved searches: %s", str(e))
            return []

    @log_function_call(logger)
    def delete_saved_search(self, search_id: int) -> bool:
        """
        Delete a saved search.

        Args:
            search_id: ID of the saved search

        Returns:
            True if deletion was successful
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("DELETE FROM saved_searches WHERE id = ?", (search_id,))
                success = cursor.rowcount > 0
                conn.commit()

                if success:
                    logger.info("Deleted saved search with ID: %s", search_id)

                return success

        except sqlite3.Error as e:
            logger.error("Failed to delete saved search: %s", str(e))
            return False

    @log_function_call(logger)
    def get_search_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """
        Get search suggestions based on partial query.

        Args:
            query: Partial search query
            limit: Maximum number of suggestions

        Returns:
            List of search suggestions
        """
        if not query or len(query) < 2:
            return []

        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                suggestions = set()

                # Get suggestions from titles
                cursor.execute(
                    """
                    SELECT DISTINCT title FROM model_metadata_fts
                    WHERE title MATCH ?
                    LIMIT ?
                """,
                    (f"{query}*", limit),
                )

                for row in cursor.fetchall():
                    if row[0]:
                        suggestions.add(row[0])

                # Get suggestions from keywords
                cursor.execute(
                    """
                    SELECT DISTINCT keywords FROM model_metadata_fts
                    WHERE keywords MATCH ?
                    LIMIT ?
                """,
                    (f"{query}*", limit),
                )

                for row in cursor.fetchall():
                    if row[0]:
                        # Split keywords and add individual ones
                        for keyword in row[0].split(","):
                            keyword = keyword.strip()
                            if keyword.lower().startswith(query.lower()):
                                suggestions.add(keyword)

                # Get suggestions from filenames
                cursor.execute(
                    """
                    SELECT DISTINCT filename FROM models_fts
                    WHERE filename MATCH ?
                    LIMIT ?
                """,
                    (f"{query}*", limit),
                )

                for row in cursor.fetchall():
                    if row[0]:
                        suggestions.add(row[0])

                # Sort by relevance (exact matches first, then alphabetical)
                sorted_suggestions = sorted(
                    suggestions,
                    key=lambda x: (not x.lower().startswith(query.lower()), x.lower()),
                )

                return sorted_suggestions[:limit]

        except sqlite3.Error as e:
            logger.error("Failed to get search suggestions: %s", str(e))
            return []

    @log_function_call(logger)
    def clear_search_history(self, older_than_days: int = 30) -> int:
        """
        Clear search history older than specified days.

        Args:
            older_than_days: Clear history older than this many days

        Returns:
            Number of records deleted
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                cutoff_date = datetime.now() - timedelta(days=older_than_days)

                cursor.execute(
                    """
                    DELETE FROM search_history
                    WHERE timestamp < ?
                """,
                    (cutoff_date,),
                )

                deleted_count = cursor.rowcount
                conn.commit()

                logger.info("Cleared %s old search history records", deleted_count)
                return deleted_count

        except sqlite3.Error as e:
            logger.error("Failed to clear search history: %s", str(e))
            return 0

    @log_function_call(logger)
    def rebuild_fts_indexes(self) -> None:
        """
        Rebuild FTS5 indexes from scratch.

        This operation can be time-consuming for large databases.
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Drop existing FTS tables
                cursor.execute("DROP TABLE IF EXISTS models_fts")
                cursor.execute("DROP TABLE IF EXISTS model_metadata_fts")

                # Recreate FTS tables
                self._initialize_fts_tables()

                logger.info("FTS5 indexes rebuilt successfully")

        except sqlite3.Error as e:
            logger.error("Failed to rebuild FTS indexes: %s", str(e))
            raise


# Singleton instance for application-wide use
_search_engine: Optional[SearchEngine] = None
_search_lock = threading.Lock()


def get_search_engine(db_path: Optional[str] = None) -> SearchEngine:
    """
    Get the singleton search engine instance.

    Args:
        db_path: Path to the SQLite database file. If None, uses AppData location.

    Returns:
        SearchEngine instance
    """
    global _search_engine

    with _search_lock:
        if _search_engine is None:
            _search_engine = SearchEngine(db_path)

        return _search_engine
