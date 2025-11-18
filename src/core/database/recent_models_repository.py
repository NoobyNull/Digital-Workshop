"""Repository for managing the model_recent_usage table."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


class RecentModelsRepository:
    """Encapsulates MRU persistence for models."""

    def __init__(self, get_connection_func) -> None:
        self._get_connection = get_connection_func

    @log_function_call(logger)
    def record_access(self, model_id: int, limit: Optional[int]) -> List[int]:
        """Insert or update the MRU entry for a model.

        Returns:
            List of model IDs that were trimmed to respect the limit.
        """

        trimmed_ids: List[int] = []
        timestamp = datetime.utcnow().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO model_recent_usage (model_id, last_accessed)
                VALUES (?, ?)
                ON CONFLICT(model_id) DO UPDATE SET last_accessed = excluded.last_accessed
                """,
                (model_id, timestamp),
            )

            if limit and limit > 0:
                trimmed_ids = self._trim_to_limit(cursor, limit)

            conn.commit()

        return trimmed_ids

    @log_function_call(logger)
    def set_favorite(self, model_id: int, is_favorite: bool) -> bool:
        """Toggle the is_favorite flag for an MRU entry."""

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE model_recent_usage
                SET is_favorite = ?
                WHERE model_id = ?
                """,
                (1 if is_favorite else 0, model_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    @log_function_call(logger)
    def get_recent_models(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return recent models ordered by last access (newest first)."""

        with self._get_connection() as conn:
            conn.row_factory = None
            cursor = conn.cursor()

            sql = """
                SELECT
                    mru.model_id,
                    mru.last_accessed,
                    mru.is_favorite,
                    m.filename,
                    m.format,
                    m.file_path,
                    mm.title,
                    mm.category
                FROM model_recent_usage mru
                JOIN models m ON mru.model_id = m.id
                LEFT JOIN model_metadata mm ON mru.model_id = mm.model_id
                ORDER BY mru.last_accessed DESC
            """

            params: List[Any] = []
            if limit and limit > 0:
                sql += " LIMIT ?"
                params.append(limit)

            cursor.execute(sql, params)
            rows = cursor.fetchall()

        results: List[Dict[str, Any]] = []
        for row in rows:
            (
                model_id,
                last_accessed,
                is_favorite,
                filename,
                fmt,
                file_path,
                title,
                category,
            ) = row

            results.append(
                {
                    "model_id": model_id,
                    "last_accessed": last_accessed,
                    "is_favorite": bool(is_favorite),
                    "filename": filename,
                    "format": fmt,
                    "file_path": file_path,
                    "title": title,
                    "category": category,
                }
            )

        return results

    @log_function_call(logger)
    def get_entry(self, model_id: int) -> Optional[Dict[str, Any]]:
        """Return a single MRU entry."""

        with self._get_connection() as conn:
            conn.row_factory = None
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT model_id, last_accessed, is_favorite
                FROM model_recent_usage
                WHERE model_id = ?
                """,
                (model_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        return {
            "model_id": row[0],
            "last_accessed": row[1],
            "is_favorite": bool(row[2]),
        }

    @log_function_call(logger)
    def trim(self, limit: int) -> List[int]:
        """Trim MRU entries down to the requested limit.

        If ``limit`` is less than or equal to zero, all entries are removed.
        """

        with self._get_connection() as conn:
            cursor = conn.cursor()

            if limit <= 0:
                # Clear the entire MRU table and report all removed model IDs.
                cursor.execute(
                    """
                    SELECT model_id
                    FROM model_recent_usage
                    """
                )
                trimmed_ids = [row[0] for row in cursor.fetchall()]
                cursor.execute("DELETE FROM model_recent_usage")
                conn.commit()
                return trimmed_ids

            trimmed = self._trim_to_limit(cursor, limit)
            conn.commit()

        return trimmed

    def _trim_to_limit(self, cursor, limit: int) -> List[int]:
        """Remove entries exceeding the limit."""

        cursor.execute(
            """
            SELECT model_id
            FROM model_recent_usage
            ORDER BY last_accessed DESC
            """
        )
        rows = [row[0] for row in cursor.fetchall()]

        if len(rows) <= limit:
            return []

        trimmed_ids = rows[limit:]

        placeholders = ",".join(["?"] * len(trimmed_ids))
        cursor.execute(
            f"""
            DELETE FROM model_recent_usage
            WHERE model_id IN ({placeholders})
            """,
            trimmed_ids,
        )

        return trimmed_ids
