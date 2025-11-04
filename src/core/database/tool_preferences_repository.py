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

    def __init__(self, db_path: str) -> None:
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
                self.logger.debug("Set preference: %s", key)
                return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to set preference %s: {e}", key)
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

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to get preference %s: {e}", key)
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

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to get external DB paths: %s", e)

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
                    self.logger.debug("Deleted preference: %s", key)
                return success

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to delete preference %s: {e}", key)
            return False
