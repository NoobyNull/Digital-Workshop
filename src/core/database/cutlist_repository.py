"""Cut list optimizer repository layer."""

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


class CutListRepository:
    """Handles persistence for scenarios, materials, pieces, and sequences."""

    def __init__(self, get_connection_func) -> None:
        self.get_connection = get_connection_func

    # ------------------------------------------------------------------ #
    # Scenarios
    # ------------------------------------------------------------------ #

    @log_function_call(logger)
    def create_scenario(
        self,
        project_id: str,
        name: str,
        stock_strategy: Optional[str] = None,
        status: str = "draft",
        metadata: Optional[Any] = None,
    ) -> int:
        timestamp = _now()
        metadata_json = _serialize(metadata)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO cutlist_scenarios (
                    project_id, name, stock_strategy, status, metadata_json,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    name,
                    stock_strategy,
                    status,
                    metadata_json,
                    timestamp,
                    timestamp,
                ),
            )
            conn.commit()
            scenario_id = cursor.lastrowid

        logger.info(
            "Created cut list scenario %s for project %s", scenario_id, project_id
        )
        return scenario_id

    @log_function_call(logger)
    def get_scenario(self, scenario_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM cutlist_scenarios WHERE id = ?", (scenario_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @log_function_call(logger)
    def list_scenarios(
        self, project_id: str, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM cutlist_scenarios WHERE project_id = ?"
        params: List[Any] = [project_id]

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
    def update_scenario(self, scenario_id: int, **kwargs: Any) -> bool:
        allowed = {"name", "stock_strategy", "status", "metadata"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}

        if not updates:
            return False

        if "metadata" in updates:
            updates["metadata_json"] = _serialize(updates.pop("metadata"))

        updates["updated_at"] = _now()
        set_clause = ", ".join([f"{field} = ?" for field in updates])
        params = list(updates.values()) + [scenario_id]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE cutlist_scenarios SET {set_clause} WHERE id = ?",
                params,
            )
            conn.commit()
            success = cursor.rowcount > 0

        if success:
            logger.info("Updated cut list scenario %s", scenario_id)
        return success

    @log_function_call(logger)
    def delete_scenario(self, scenario_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cutlist_scenarios WHERE id = ?", (scenario_id,))
            conn.commit()
            success = cursor.rowcount > 0

        if success:
            logger.info("Deleted cut list scenario %s", scenario_id)
        return success

    # ------------------------------------------------------------------ #
    # Materials
    # ------------------------------------------------------------------ #

    @log_function_call(logger)
    def add_material(
        self,
        scenario_id: int,
        description: Optional[str],
        width: Optional[float],
        height: Optional[float],
        thickness: Optional[float],
        quantity: int = 1,
        grain: Optional[str] = None,
        material_tag: Optional[str] = None,
        waste_area: Optional[float] = None,
        metadata: Optional[Any] = None,
    ) -> int:
        metadata_json = _serialize(metadata)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO cutlist_materials (
                    scenario_id, description, width, height, thickness,
                    quantity, grain, material_tag, waste_area, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    scenario_id,
                    description,
                    width,
                    height,
                    thickness,
                    quantity,
                    grain,
                    material_tag,
                    waste_area,
                    metadata_json,
                ),
            )
            conn.commit()
            material_id = cursor.lastrowid

        logger.info("Added stock material %s to scenario %s", material_id, scenario_id)
        return material_id

    @log_function_call(logger)
    def list_materials(self, scenario_id: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM cutlist_materials WHERE scenario_id = ? ORDER BY id ASC",
                (scenario_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    @log_function_call(logger)
    def delete_material(self, material_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cutlist_materials WHERE id = ?", (material_id,))
            conn.commit()
            success = cursor.rowcount > 0

        if success:
            logger.info("Deleted material %s", material_id)
        return success

    # ------------------------------------------------------------------ #
    # Pieces
    # ------------------------------------------------------------------ #

    @log_function_call(logger)
    def add_piece(
        self,
        scenario_id: int,
        name: Optional[str],
        width: Optional[float],
        height: Optional[float],
        thickness: Optional[float],
        quantity: int = 1,
        grain: Optional[str] = None,
        orientation: Optional[str] = None,
        project_model_id: Optional[int] = None,
        placement: Optional[Any] = None,
    ) -> int:
        placement_json = _serialize(placement)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO cutlist_pieces (
                    scenario_id, project_model_id, name, width, height, thickness,
                    quantity, grain, orientation, placement_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    scenario_id,
                    project_model_id,
                    name,
                    width,
                    height,
                    thickness,
                    quantity,
                    grain,
                    orientation,
                    placement_json,
                ),
            )
            conn.commit()
            piece_id = cursor.lastrowid

        logger.info("Added piece %s to scenario %s", piece_id, scenario_id)
        return piece_id

    @log_function_call(logger)
    def list_pieces(self, scenario_id: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM cutlist_pieces WHERE scenario_id = ? ORDER BY id ASC",
                (scenario_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    @log_function_call(logger)
    def delete_piece(self, piece_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cutlist_pieces WHERE id = ?", (piece_id,))
            conn.commit()
            success = cursor.rowcount > 0

        if success:
            logger.info("Deleted piece %s", piece_id)
        return success

    # ------------------------------------------------------------------ #
    # Sequencing
    # ------------------------------------------------------------------ #

    @log_function_call(logger)
    def add_sequence_step(
        self,
        scenario_id: int,
        sequence_order: int,
        piece_id: Optional[int] = None,
        board_reference: Optional[str] = None,
        instruction: Optional[str] = None,
        metadata: Optional[Any] = None,
    ) -> int:
        metadata_json = _serialize(metadata)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO cutlist_sequences (
                    scenario_id, sequence_order, piece_id, board_reference, instruction, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    scenario_id,
                    sequence_order,
                    piece_id,
                    board_reference,
                    instruction,
                    metadata_json,
                ),
            )
            conn.commit()
            step_id = cursor.lastrowid

        logger.info("Added cut sequence step %s to scenario %s", step_id, scenario_id)
        return step_id

    @log_function_call(logger)
    def list_sequence(self, scenario_id: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM cutlist_sequences
                WHERE scenario_id = ?
                ORDER BY sequence_order ASC
                """,
                (scenario_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    @log_function_call(logger)
    def delete_sequence(self, scenario_id: int) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM cutlist_sequences WHERE scenario_id = ?", (scenario_id,)
            )
            conn.commit()
            deleted = cursor.rowcount

        if deleted:
            logger.info(
                "Deleted %s sequence steps for scenario %s", deleted, scenario_id
            )
        return deleted
