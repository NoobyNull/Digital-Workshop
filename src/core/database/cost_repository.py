"""Cost estimation repository layer."""

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


class CostRepository:
    """Persists cost templates, snapshots, and detailed entries."""

    def __init__(self, get_connection_func) -> None:
        self.get_connection = get_connection_func

    # ------------------------------------------------------------------ #
    # Templates
    # ------------------------------------------------------------------ #

    @log_function_call(logger)
    def create_template(
        self,
        name: str,
        description: Optional[str] = None,
        data: Optional[Any] = None,
        created_by: Optional[str] = None,
    ) -> int:
        timestamp = _now()
        data_json = _serialize(data)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO cost_templates (
                    name, description, data_json, created_by, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name, description, data_json, created_by, timestamp, timestamp),
            )
            conn.commit()
            template_id = cursor.lastrowid

        logger.info("Created cost template %s (%s)", template_id, name)
        return template_id

    @log_function_call(logger)
    def get_template(self, template_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cost_templates WHERE id = ?", (template_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @log_function_call(logger)
    def list_templates(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cost_templates ORDER BY updated_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    @log_function_call(logger)
    def update_template(self, template_id: int, **kwargs: Any) -> bool:
        allowed = {"name", "description", "data", "created_by"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}

        if not updates:
            return False

        if "data" in updates:
            updates["data_json"] = _serialize(updates.pop("data"))

        updates["updated_at"] = _now()
        set_clause = ", ".join([f"{field} = ?" for field in updates])
        params = list(updates.values()) + [template_id]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE cost_templates SET {set_clause} WHERE id = ?",
                params,
            )
            conn.commit()
            success = cursor.rowcount > 0

        if success:
            logger.info("Updated cost template %s", template_id)
        return success

    @log_function_call(logger)
    def delete_template(self, template_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cost_templates WHERE id = ?", (template_id,))
            conn.commit()
            success = cursor.rowcount > 0

        if success:
            logger.info("Deleted cost template %s", template_id)
        return success

    # ------------------------------------------------------------------ #
    # Snapshots
    # ------------------------------------------------------------------ #

    @log_function_call(logger)
    def create_snapshot(
        self,
        project_id: str,
        name: Optional[str] = None,
        template_id: Optional[int] = None,
        totals: Optional[Dict[str, float]] = None,
        rates: Optional[Dict[str, float]] = None,
        data: Optional[Any] = None,
        quantity: int = 1,
    ) -> int:
        totals = totals or {}
        rates = rates or {}
        data_json = _serialize(data)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO cost_snapshots (
                    project_id, name, template_id,
                    total_material_cost, total_machine_cost, total_labor_cost,
                    total_shop_cost, total_tool_cost, total_expense_cost,
                    overhead_pct, profit_margin_pct, tax_pct,
                    final_quote, quantity, data_json,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    name,
                    template_id,
                    totals.get("materials"),
                    totals.get("machine"),
                    totals.get("labor"),
                    totals.get("shop"),
                    totals.get("tool"),
                    totals.get("expense"),
                    rates.get("overhead"),
                    rates.get("profit"),
                    rates.get("tax"),
                    totals.get("final"),
                    quantity,
                    data_json,
                    _now(),
                    _now(),
                ),
            )
            conn.commit()
            snapshot_id = cursor.lastrowid

        logger.info("Created cost snapshot %s for project %s", snapshot_id, project_id)
        return snapshot_id

    @log_function_call(logger)
    def get_snapshot(self, snapshot_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cost_snapshots WHERE id = ?", (snapshot_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @log_function_call(logger)
    def list_snapshots(self, project_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM cost_snapshots WHERE project_id = ? ORDER BY created_at DESC",
                (project_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    @log_function_call(logger)
    def update_snapshot(self, snapshot_id: int, **kwargs: Any) -> bool:
        allowed_totals = {
            "total_material_cost",
            "total_machine_cost",
            "total_labor_cost",
            "total_shop_cost",
            "total_tool_cost",
            "total_expense_cost",
            "final_quote",
        }
        allowed_rates = {"overhead_pct", "profit_margin_pct", "tax_pct"}

        updates: Dict[str, Any] = {}
        for key, value in kwargs.items():
            if key in allowed_totals or key in allowed_rates:
                updates[key] = value
            elif key == "name":
                updates[key] = value
            elif key == "template_id":
                updates[key] = value
            elif key == "quantity":
                updates[key] = value
            elif key == "data":
                updates["data_json"] = _serialize(value)

        if not updates:
            return False

        updates["updated_at"] = _now()
        set_clause = ", ".join([f"{field} = ?" for field in updates])
        params = list(updates.values()) + [snapshot_id]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE cost_snapshots SET {set_clause} WHERE id = ?",
                params,
            )
            conn.commit()
            success = cursor.rowcount > 0

        if success:
            logger.info("Updated cost snapshot %s", snapshot_id)
        return success

    @log_function_call(logger)
    def delete_snapshot(self, snapshot_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cost_snapshots WHERE id = ?", (snapshot_id,))
            conn.commit()
            success = cursor.rowcount > 0

        if success:
            logger.info("Deleted cost snapshot %s", snapshot_id)
        return success

    # ------------------------------------------------------------------ #
    # Entries
    # ------------------------------------------------------------------ #

    @log_function_call(logger)
    def add_entry(
        self,
        snapshot_id: int,
        category: Optional[str],
        source_type: Optional[str],
        source_reference: Optional[str],
        description: Optional[str],
        quantity: float,
        unit: Optional[str],
        rate: Optional[float],
        cost: Optional[float],
        metadata: Optional[Any] = None,
    ) -> int:
        metadata_json = _serialize(metadata)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO cost_entries (
                    snapshot_id, category, source_type, source_reference, description,
                    quantity, unit, rate, cost, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    category,
                    source_type,
                    source_reference,
                    description,
                    quantity,
                    unit,
                    rate,
                    cost,
                    metadata_json,
                ),
            )
            conn.commit()
            entry_id = cursor.lastrowid

        logger.info("Added cost entry %s to snapshot %s", entry_id, snapshot_id)
        return entry_id

    @log_function_call(logger)
    def list_entries(self, snapshot_id: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM cost_entries WHERE snapshot_id = ? ORDER BY id ASC",
                (snapshot_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    @log_function_call(logger)
    def delete_entries(self, snapshot_id: int) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cost_entries WHERE snapshot_id = ?", (snapshot_id,))
            conn.commit()
            deleted = cursor.rowcount

        if deleted:
            logger.info("Deleted %s cost entries for snapshot %s", deleted, snapshot_id)
        return deleted
