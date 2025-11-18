"""Project-model association repository for CNC workflow."""

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


class ProjectModelRepository:
    """Repository for project_models table."""

    def __init__(self, get_connection_func) -> None:
        """
        Initialize repository.

        Args:
            get_connection_func: Callable returning sqlite3.Connection
        """
        self.get_connection = get_connection_func

    @staticmethod
    def _serialize_metadata(metadata: Optional[Dict[str, Any]]) -> Optional[str]:
        if metadata is None:
            return None
        try:
            return json.dumps(metadata)
        except (TypeError, ValueError):
            logger.warning("Failed to serialize project model metadata; storing as string fallback")
            return json.dumps({"value": str(metadata)})

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat()

    @log_function_call(logger)
    def create_project_model(
        self,
        project_id: str,
        model_id: Optional[int] = None,
        role: Optional[str] = None,
        version: Optional[str] = None,
        material_tag: Optional[str] = None,
        orientation_hint: Optional[str] = None,
        derived_from_model_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Link a model (or derived asset) to a project.

        Returns:
            Row ID for the project_models record.
        """
        payload = (
            project_id,
            model_id,
            role,
            version,
            material_tag,
            orientation_hint,
            derived_from_model_id,
            self._serialize_metadata(metadata),
            self._now(),
            self._now(),
        )

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO project_models (
                    project_id, model_id, role, version, material_tag,
                    orientation_hint, derived_from_model_id, metadata_json,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                payload,
            )
            conn.commit()
            record_id = cursor.lastrowid
            logger.info(
                "Linked model %s to project %s (record %s)", model_id, project_id, record_id
            )
            return record_id

    @log_function_call(logger)
    def get_project_model(self, record_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a single project_models row."""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM project_models WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @log_function_call(logger)
    def list_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """Return all project_models rows for a project."""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM project_models WHERE project_id = ? ORDER BY created_at DESC",
                (project_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    @log_function_call(logger)
    def list_by_model(self, model_id: int) -> List[Dict[str, Any]]:
        """Return all project_models rows referencing a model."""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM project_models WHERE model_id = ? ORDER BY created_at DESC",
                (model_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    @log_function_call(logger)
    def list_by_role(self, project_id: str, role: str) -> List[Dict[str, Any]]:
        """Return associations filtered by role."""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM project_models
                WHERE project_id = ? AND role = ?
                ORDER BY created_at DESC
                """,
                (project_id, role),
            )
            return [dict(row) for row in cursor.fetchall()]

    @log_function_call(logger)
    def update_project_model(self, record_id: int, **kwargs) -> bool:
        """
        Update fields on a project_models entry.

        Allowed keys: role, version, material_tag, orientation_hint,
        derived_from_model_id, metadata.
        """
        allowed_fields = {
            "role",
            "version",
            "material_tag",
            "orientation_hint",
            "derived_from_model_id",
            "metadata",
        }
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return False

        if "metadata" in updates:
            metadata_json = self._serialize_metadata(updates.pop("metadata"))
            updates["metadata_json"] = metadata_json

        updates["updated_at"] = self._now()
        set_clause = ", ".join([f"{field} = ?" for field in updates.keys()])
        values = list(updates.values())
        values.append(record_id)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE project_models
                SET {set_clause}
                WHERE id = ?
                """,
                values,
            )
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info("Updated project model link %s", record_id)
            return success

    @log_function_call(logger)
    def delete_project_model(self, record_id: int) -> bool:
        """Remove a project-model association."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM project_models WHERE id = ?", (record_id,))
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info("Deleted project model link %s", record_id)
            return success
