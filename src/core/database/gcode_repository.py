"""Data access helpers for G-code operations, tool snapshots, and machining metrics."""

import json
import sqlite3
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


def _serialize_json(payload: Optional[Any]) -> Optional[str]:
    """Serialize arbitrary payloads to JSON strings."""
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


class GcodeRepository:
    """Repository for G-code operations, versions, metrics, and tool snapshots."""

    def __init__(self, get_connection_func) -> None:
        """
        Args:
            get_connection_func: Callable returning sqlite3.Connection
        """
        self.get_connection = get_connection_func

    # ------------------------------------------------------------------ #
    # Operations
    # ------------------------------------------------------------------ #

    @log_function_call(logger)
    def create_operation(
        self,
        project_id: str,
        name: str,
        model_id: Optional[int] = None,
        status: str = "draft",
        strategy: Optional[str] = None,
        notes: Optional[str] = None,
        operation_id: Optional[str] = None,
    ) -> str:
        """Insert a new G-code operation record."""
        op_id = operation_id or str(uuid.uuid4())
        timestamp = _now()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO gcode_operations (
                    id, project_id, model_id, name, status, strategy, notes,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (op_id, project_id, model_id, name, status, strategy, notes, timestamp, timestamp),
            )
            conn.commit()

        logger.info("Created G-code operation %s for project %s", op_id, project_id)
        return op_id

    @log_function_call(logger)
    def get_operation(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single operation."""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM gcode_operations WHERE id = ?", (operation_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @log_function_call(logger)
    def list_operations(
        self,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List operations, optionally filtered by project and status."""
        query = "SELECT * FROM gcode_operations WHERE 1=1"
        params: List[Any] = []

        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC"

        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    @log_function_call(logger)
    def update_operation(self, operation_id: str, **kwargs: Any) -> bool:
        """Update mutable fields on an operation."""
        allowed = {"name", "status", "strategy", "notes", "model_id"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}

        if not updates:
            return False

        updates["updated_at"] = _now()
        set_clause = ", ".join([f"{field} = ?" for field in updates])
        params = list(updates.values()) + [operation_id]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE gcode_operations SET {set_clause} WHERE id = ?",
                params,
            )
            conn.commit()
            success = cursor.rowcount > 0

        if success:
            logger.info("Updated G-code operation %s", operation_id)
        return success

    @log_function_call(logger)
    def delete_operation(self, operation_id: str) -> bool:
        """Remove an operation and its dependent entities (versions cascade)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM gcode_operations WHERE id = ?", (operation_id,))
            conn.commit()
            success = cursor.rowcount > 0

        if success:
            logger.info("Deleted G-code operation %s", operation_id)
        return success

    # ------------------------------------------------------------------ #
    # Versions
    # ------------------------------------------------------------------ #

    @log_function_call(logger)
    def create_version(
        self,
        operation_id: str,
        file_path: str,
        file_hash: Optional[str] = None,
        version_label: Optional[str] = None,
        revision: int = 1,
        status: str = "draft",
        feed_snapshot: Optional[Any] = None,
        tool_list: Optional[Any] = None,
        checksum: Optional[str] = None,
    ) -> int:
        """Insert a version row for an operation."""
        timestamp = _now()
        feed_json = _serialize_json(feed_snapshot)
        tool_json = _serialize_json(tool_list)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO gcode_versions (
                    operation_id, version_label, file_path, file_hash,
                    revision, status, feed_snapshot_json, tool_list_json,
                    checksum, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    operation_id,
                    version_label,
                    file_path,
                    file_hash,
                    revision,
                    status,
                    feed_json,
                    tool_json,
                    checksum,
                    timestamp,
                ),
            )
            conn.commit()
            version_id = cursor.lastrowid

        logger.info("Created G-code version %s for operation %s", version_id, operation_id)
        return version_id

    @log_function_call(logger)
    def get_version(self, version_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM gcode_versions WHERE id = ?", (version_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @log_function_call(logger)
    def list_versions(self, operation_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM gcode_versions WHERE operation_id = ? ORDER BY created_at DESC",
                (operation_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    @log_function_call(logger)
    def update_version(self, version_id: int, **kwargs: Any) -> bool:
        allowed = {
            "version_label",
            "file_path",
            "file_hash",
            "revision",
            "status",
            "feed_snapshot",
            "tool_list",
            "checksum",
        }
        updates: Dict[str, Any] = {}

        for key, value in kwargs.items():
            if key not in allowed:
                continue
            if key == "feed_snapshot":
                updates["feed_snapshot_json"] = _serialize_json(value)
            elif key == "tool_list":
                updates["tool_list_json"] = _serialize_json(value)
            else:
                updates[key] = value

        if not updates:
            return False

        set_clause = ", ".join([f"{field} = ?" for field in updates])
        params = list(updates.values()) + [version_id]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE gcode_versions SET {set_clause} WHERE id = ?", params)
            conn.commit()
            success = cursor.rowcount > 0

        if success:
            logger.info("Updated G-code version %s", version_id)
        return success

    @log_function_call(logger)
    def delete_version(self, version_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM gcode_versions WHERE id = ?", (version_id,))
            conn.commit()
            success = cursor.rowcount > 0

        if success:
            logger.info("Deleted G-code version %s", version_id)
        return success

    # ------------------------------------------------------------------ #
    # Metrics
    # ------------------------------------------------------------------ #

    @log_function_call(logger)
    def upsert_metrics(self, version_id: int, **metrics: Any) -> bool:
        """Insert or update machining metrics for a version."""
        if not metrics:
            return False

        fields = {
            "total_time_seconds",
            "cutting_time_seconds",
            "rapid_time_seconds",
            "tool_changes",
            "distance_cut",
            "distance_rapid",
            "material_removed",
            "warnings",
            "best_case_time_seconds",
            "time_correction_factor",
            "machine_id",
            "feed_override_pct",
        }
        payload = {k: v for k, v in metrics.items() if k in fields}

        if not payload:
            return False

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM gcode_metrics WHERE version_id = ?",
                (version_id,),
            )
            existing = cursor.fetchone()

            if existing:
                set_clause = ", ".join([f"{field} = ?" for field in payload])
                params = list(payload.values()) + [version_id]
                cursor.execute(
                    f"UPDATE gcode_metrics SET {set_clause} WHERE version_id = ?",
                    params,
                )
            else:
                columns = ", ".join(["version_id"] + list(payload.keys()))
                placeholders = ", ".join(["?"] * (1 + len(payload)))
                params = [version_id] + list(payload.values())
                cursor.execute(
                    f"INSERT INTO gcode_metrics ({columns}) VALUES ({placeholders})",
                    params,
                )

            conn.commit()
            success = cursor.rowcount > 0

        if success:
            logger.info("Recorded metrics for version %s", version_id)
        return success

    @log_function_call(logger)
    def get_metrics(self, version_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM gcode_metrics WHERE version_id = ?", (version_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # ------------------------------------------------------------------ #
    # Tool snapshots
    # ------------------------------------------------------------------ #

    @log_function_call(logger)
    def add_tool_snapshot(
        self,
        version_id: int,
        tool_number: Optional[str] = None,
        tool_id: Optional[int] = None,
        provider_name: Optional[str] = None,
        tool_db_source: Optional[str] = None,
        feed_rate: Optional[float] = None,
        plunge_rate: Optional[float] = None,
        spindle_speed: Optional[float] = None,
        stepdown: Optional[float] = None,
        stepover: Optional[float] = None,
        notes: Optional[str] = None,
        metadata: Optional[Any] = None,
    ) -> int:
        """Persist a snapshot of the tool parameters used in a version."""
        metadata_json = _serialize_json(metadata)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO gcode_tool_snapshots (
                    version_id, tool_number, tool_id, provider_name, tool_db_source,
                    feed_rate, plunge_rate, spindle_speed, stepdown, stepover,
                    notes, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id,
                    tool_number,
                    tool_id,
                    provider_name,
                    tool_db_source,
                    feed_rate,
                    plunge_rate,
                    spindle_speed,
                    stepdown,
                    stepover,
                    notes,
                    metadata_json,
                ),
            )
            conn.commit()
            snapshot_id = cursor.lastrowid

        logger.info("Added tool snapshot %s for version %s", snapshot_id, version_id)
        return snapshot_id

    @log_function_call(logger)
    def list_tool_snapshots(self, version_id: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM gcode_tool_snapshots WHERE version_id = ? ORDER BY id ASC",
                (version_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    @log_function_call(logger)
    def delete_tool_snapshots(self, version_id: int) -> int:
        """Remove every snapshot tied to a version."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM gcode_tool_snapshots WHERE version_id = ?", (version_id,))
            conn.commit()
            deleted = cursor.rowcount

        if deleted:
            logger.info("Deleted %s tool snapshots for version %s", deleted, version_id)
        return deleted
