"""Tool import tracking repository."""

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


def _serialize(payload: Optional[Any]) -> Optional[str]:
    if payload is None:
        return None
    if isinstance(payload, str):
        return payload
    try:
        return json.dumps(payload)
    except (TypeError, ValueError):
        logger.warning("Failed to serialize payload %s", payload)
        return json.dumps({"value": str(payload)})


def _now() -> str:
    return datetime.now().isoformat()


class ToolImportRepository:
    """Manage tool provider sources and import batch metadata."""

    def __init__(self, get_connection_func) -> None:
        self.get_connection = get_connection_func

    # ------------------------------------------------------------------ #
    # Provider Sources
    # ------------------------------------------------------------------ #

    @log_function_call(logger)
    def create_provider_source(
        self,
        provider_name: str,
        source_path: Optional[str] = None,
        checksum: Optional[str] = None,
        format_type: Optional[str] = None,
        status: Optional[str] = None,
        metadata: Optional[Any] = None,
    ) -> int:
        metadata_json = _serialize(metadata)
        timestamp = _now()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO tool_provider_sources (
                    provider_name, source_path, checksum, format_type,
                    status, imported_at, last_sync_at, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    provider_name,
                    source_path,
                    checksum,
                    format_type,
                    status,
                    timestamp,
                    timestamp,
                    metadata_json,
                ),
            )
            conn.commit()
            source_id = cursor.lastrowid

        logger.info("Registered tool provider source %s (%s)", source_id, provider_name)
        return source_id

    @log_function_call(logger)
    def update_provider_source(self, source_id: int, **kwargs: Any) -> bool:
        allowed = {
            "provider_name",
            "source_path",
            "checksum",
            "format_type",
            "status",
            "imported_at",
            "last_sync_at",
            "metadata",
        }
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False

        if "metadata" in updates:
            updates["metadata_json"] = _serialize(updates.pop("metadata"))

        if "imported_at" in updates and isinstance(updates["imported_at"], datetime):
            updates["imported_at"] = updates["imported_at"].isoformat()
        if "last_sync_at" in updates and isinstance(updates["last_sync_at"], datetime):
            updates["last_sync_at"] = updates["last_sync_at"].isoformat()

        set_clause = ", ".join([f"{field} = ?" for field in updates])
        params = list(updates.values()) + [source_id]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE tool_provider_sources SET {set_clause} WHERE id = ?",
                params,
            )
            conn.commit()
            success = cursor.rowcount > 0

        if success:
            logger.info("Updated tool provider source %s", source_id)
        return success

    @log_function_call(logger)
    def list_provider_sources(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM tool_provider_sources ORDER BY last_sync_at DESC NULLS LAST"
            )
            return [dict(row) for row in cursor.fetchall()]

    @log_function_call(logger)
    def get_provider_source(self, source_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tool_provider_sources WHERE id = ?", (source_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @log_function_call(logger)
    def delete_provider_source(self, source_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tool_provider_sources WHERE id = ?", (source_id,))
            conn.commit()
            success = cursor.rowcount > 0

        if success:
            logger.info("Deleted tool provider source %s", source_id)
        return success

    # ------------------------------------------------------------------ #
    # Import Batches
    # ------------------------------------------------------------------ #

    @log_function_call(logger)
    def create_import_batch(
        self,
        provider_source_id: Optional[int],
        imported_count: int,
        duration_seconds: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO tool_import_batches (
                    provider_source_id, imported_count, duration_seconds, notes, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    provider_source_id,
                    imported_count,
                    duration_seconds,
                    notes,
                    _now(),
                ),
            )
            conn.commit()
            batch_id = cursor.lastrowid

        logger.info("Recorded tool import batch %s", batch_id)
        return batch_id

    @log_function_call(logger)
    def list_import_batches(self, provider_source_id: Optional[int] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM tool_import_batches WHERE 1=1"
        params: List[Any] = []

        if provider_source_id:
            query += " AND provider_source_id = ?"
            params.append(provider_source_id)

        query += " ORDER BY created_at DESC"

        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    @log_function_call(logger)
    def get_import_batch(self, batch_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tool_import_batches WHERE id = ?", (batch_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @log_function_call(logger)
    def delete_import_batch(self, batch_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tool_import_batches WHERE id = ?", (batch_id,))
            conn.commit()
            success = cursor.rowcount > 0

        if success:
            logger.info("Deleted tool import batch %s", batch_id)
        return success
