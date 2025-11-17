"""Machine repository for handling CNC machine profiles and kinematics.

This module provides CRUD operations for machine definitions used by
cutting-time estimation and costing.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional

from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


class MachineRepository:
    """Repository for managing machine profiles in the database."""

    def __init__(self, get_connection_func) -> None:
        """Initialize the machine repository.

        Args:
            get_connection_func: Callable that returns a SQLite connection.
        """

        self._get_connection = get_connection_func
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info("MachineRepository initialized")

    @log_function_call(logger)
    def add_machine(
        self,
        name: str,
        max_feed_mm_min: float,
        accel_mm_s2: float,
        notes: Optional[str] = None,
        is_default: bool = False,
    ) -> int:
        """Add a new machine profile.

        Returns the ID of the newly created machine.
        """

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO machines (
                        name, max_feed_mm_min, accel_mm_s2, notes, is_default
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (name, max_feed_mm_min, accel_mm_s2, notes, int(is_default)),
                )
                machine_id = cursor.lastrowid
                conn.commit()
                self.logger.info("Added machine '%s' with ID %s", name, machine_id)
                return machine_id

        except sqlite3.IntegrityError as exc:  # duplicate name, etc.
            self.logger.error("Machine with name '%s' already exists: %s", name, exc)
            raise
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
            self.logger.error("Failed to add machine '%s': %s", name, exc)
            raise

    @log_function_call(logger)
    def get_machine(self, machine_id: int) -> Optional[Dict[str, Any]]:
        """Get a machine by ID."""

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM machines WHERE id = ?", (machine_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
            self.logger.error("Failed to get machine %s: %s", machine_id, exc)
            return None

    @log_function_call(logger)
    def get_machine_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a machine by unique name."""

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM machines WHERE name = ?", (name,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
            self.logger.error("Failed to get machine by name '%s': %s", name, exc)
            return None

    @log_function_call(logger)
    def get_all_machines(self) -> List[Dict[str, Any]]:
        """Return all machine profiles sorted by default flag then name."""

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM machines ORDER BY is_default DESC, name ASC"
                )
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
            self.logger.error("Failed to list machines: %s", exc)
            return []

    @log_function_call(logger)
    def get_default_machine(self) -> Optional[Dict[str, Any]]:
        """Return the default machine if one is configured."""

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM machines WHERE is_default = 1 ORDER BY id ASC LIMIT 1"
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
            self.logger.error("Failed to get default machine: %s", exc)
            return None

    @log_function_call(logger)
    def update_machine(
        self,
        machine_id: int,
        *,
        name: Optional[str] = None,
        max_feed_mm_min: Optional[float] = None,
        accel_mm_s2: Optional[float] = None,
        notes: Optional[str] = None,
        is_default: Optional[bool] = None,
    ) -> bool:
        """Update machine fields. Returns True if a row was updated."""

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                updates: List[str] = []
                params: List[Any] = []

                if name is not None:
                    updates.append("name = ?")
                    params.append(name)
                if max_feed_mm_min is not None:
                    updates.append("max_feed_mm_min = ?")
                    params.append(max_feed_mm_min)
                if accel_mm_s2 is not None:
                    updates.append("accel_mm_s2 = ?")
                    params.append(accel_mm_s2)
                if notes is not None:
                    updates.append("notes = ?")
                    params.append(notes)
                if is_default is not None:
                    updates.append("is_default = ?")
                    params.append(int(is_default))

                if not updates:
                    return False

                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(machine_id)

                query = f"UPDATE machines SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, params)
                success = cursor.rowcount > 0
                conn.commit()

                if success:
                    self.logger.info("Updated machine %s", machine_id)
                else:
                    self.logger.warning("Machine %s not found for update", machine_id)

                return success

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
            self.logger.error("Failed to update machine %s: %s", machine_id, exc)
            return False

    @log_function_call(logger)
    def delete_machine(self, machine_id: int) -> bool:
        """Delete a machine profile if it is not marked as default."""

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT is_default FROM machines WHERE id = ?",
                    (machine_id,),
                )
                row = cursor.fetchone()
                if not row:
                    self.logger.warning("Machine %s not found for deletion", machine_id)
                    return False
                if row[0]:
                    self.logger.error("Cannot delete default machine %s", machine_id)
                    return False

                cursor.execute("DELETE FROM machines WHERE id = ?", (machine_id,))
                success = cursor.rowcount > 0
                conn.commit()

                if success:
                    self.logger.info("Deleted machine %s", machine_id)
                else:
                    self.logger.warning("Machine %s not found for deletion after check", machine_id)

                return success

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
            self.logger.error("Failed to delete machine %s: %s", machine_id, exc)
            return False

    @log_function_call(logger)
    def initialize_default_machine(self) -> None:
        """Ensure at least one generic machine exists in the database."""

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM machines")
                count_row = cursor.fetchone()
                if count_row and count_row[0] > 0:
                    return

            # No machines defined yet; create a generic metric default.
            self.add_machine(
                name="Generic CNC (metric)",
                max_feed_mm_min=600.0,
                accel_mm_s2=100.0,
                notes="Default generic machine profile for timing calculations.",
                is_default=True,
            )
            self.logger.info("Initialized default generic machine profile")

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
            self.logger.error("Failed to initialize default machine: %s", exc)
            raise

