"""
Preferences repository for tool database settings.
"""

import sqlite3
import json
from typing import Any, Dict
from pathlib import Path

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class ToolPreferencesRepository:
    """Repository for tool database preferences."""

    def __init__(self, db_path: str):
        """Initialize repository with database path."""
        self.db_path = Path(db_path)
        self.logger = logger

    def set_preference(self, key: str, value: Any) -> bool:
        """Set a preference value."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Convert value to JSON if it's not a string
                if not isinstance(value, str):
                    value = json.dumps(value)

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO preferences (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                    (key, value),
                )

                conn.commit()
                self.logger.debug(f"Set preference: {key}")
                return True

        except Exception as e:
            self.logger.error(f"Failed to set preference {key}: {e}")
            return False

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a preference value."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT value FROM preferences WHERE key = ?", (key,))
                row = cursor.fetchone()

                if row:
                    value = row[0]
                    # Try to parse as JSON
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value

                return default

        except Exception as e:
            self.logger.error(f"Failed to get preference {key}: {e}")
            return default

    def get_external_db_paths(self) -> Dict[str, str]:
        """Get all external database paths."""
        paths = {}
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT key, value FROM preferences
                    WHERE key LIKE 'external_db_%'
                """
                )

                for row in cursor.fetchall():
                    # Extract format type from key (e.g., 'external_db_csv' -> 'CSV')
                    format_type = row[0].split("_")[-1].upper()
                    paths[format_type] = row[1]

        except Exception as e:
            self.logger.error(f"Failed to get external DB paths: {e}")

        return paths

    def delete_preference(self, key: str) -> bool:
        """Delete a preference."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("DELETE FROM preferences WHERE key = ?", (key,))
                conn.commit()

                success = cursor.rowcount > 0
                if success:
                    self.logger.debug(f"Deleted preference: {key}")
                return success

        except Exception as e:
            self.logger.error(f"Failed to delete preference {key}: {e}")
            return False
