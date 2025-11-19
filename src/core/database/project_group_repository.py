"""Repository for logical project grouping."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


def _now() -> str:
    return datetime.now().isoformat()


class ProjectGroupRepository:
    """Data access helpers for project grouping."""

    def __init__(self, get_connection_func) -> None:
        self.get_connection = get_connection_func

    @log_function_call(logger)
    def create_group(
        self,
        name: str,
        parent_id: Optional[str] = None,
        sort_order: int = 0,
    ) -> str:
        group_id = str(uuid.uuid4())
        timestamp = _now()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO project_groups (
                    id, name, parent_id, sort_order, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (group_id, name, parent_id, sort_order, timestamp, timestamp),
            )
            conn.commit()

        logger.info("Created project group %s", group_id)
        return group_id

    @log_function_call(logger)
    def list_groups(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT *
                FROM project_groups
                ORDER BY sort_order ASC, name COLLATE NOCASE ASC
                """
            )
            return [dict(row) for row in cursor.fetchall()]

    @log_function_call(logger)
    def update_group(self, group_id: str, **kwargs: Any) -> bool:
        allowed = {"name", "parent_id", "sort_order"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False

        updates["updated_at"] = _now()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        params = list(updates.values()) + [group_id]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE project_groups SET {set_clause} WHERE id = ?",
                params,
            )
            conn.commit()
            success = cursor.rowcount > 0

        if success:
            logger.info("Updated project group %s", group_id)
        return success

    @log_function_call(logger)
    def delete_group(self, group_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM project_groups WHERE id = ?", (group_id,))
            conn.commit()
            success = cursor.rowcount > 0

        if success:
            logger.info("Deleted project group %s", group_id)
        return success
