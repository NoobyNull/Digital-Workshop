"""
Provider repository for managing tool providers.
"""

import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class ProviderRepository:
    """Repository for provider operations."""

    def __init__(self, db_path: str):
        """Initialize repository with database path."""
        self.db_path = Path(db_path)
        self.logger = logger
        self._conn = None

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with proper management."""
        return sqlite3.connect(self.db_path)

    def _close_connection(self, conn: sqlite3.Connection):
        """Explicitly close database connection."""
        if conn:
            try:
                conn.close()
            except Exception as e:
                self.logger.warning(f"Error closing connection: {e}")

    def add_provider(
        self,
        name: str,
        description: str = "",
        file_path: str = "",
        format_type: str = "",
    ) -> Optional[int]:
        """Add a new provider to the database."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO providers (name, description, file_path, format_type)
                VALUES (?, ?, ?, ?)
            """,
                (name, description, file_path, format_type),
            )

            provider_id = cursor.lastrowid
            conn.commit()

            self.logger.info(f"Added provider: {name} (ID: {provider_id})")
            return provider_id

        except sqlite3.IntegrityError:
            self.logger.warning(f"Provider already exists: {name}")
            existing = self.get_provider_by_name(name)
            return existing.get("id") if existing else None
        except Exception as e:
            self.logger.error(f"Failed to add provider: {e}")
            return None
        finally:
            self._close_connection(conn)

    def get_provider_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a provider by name."""
        conn = None
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM providers WHERE name = ?", (name,))
            row = cursor.fetchone()

            return dict(row) if row else None

        except Exception as e:
            self.logger.error(f"Failed to get provider {name}: {e}")
            return None
        finally:
            self._close_connection(conn)

    def get_provider(self, provider_id: int) -> Optional[Dict[str, Any]]:
        """Get a provider by ID."""
        conn = None
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM providers WHERE id = ?", (provider_id,))
            row = cursor.fetchone()

            return dict(row) if row else None

        except Exception as e:
            self.logger.error(f"Failed to get provider {provider_id}: {e}")
            return None
        finally:
            self._close_connection(conn)

    def list_providers(self) -> List[Dict[str, Any]]:
        """List all providers. Alias for get_all_providers."""
        return self.get_all_providers()

    def get_all_providers(self) -> List[Dict[str, Any]]:
        """Get all providers."""
        conn = None
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM providers ORDER BY name")

            return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            self.logger.error(f"Failed to get providers: {e}")
            return []
        finally:
            self._close_connection(conn)

    def update_provider(self, provider_id: int, **kwargs) -> bool:
        """Update provider fields."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            allowed_fields = ["name", "description", "file_path", "format_type"]
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}

            if not update_fields:
                return False

            set_clause = ", ".join([f"{k} = ?" for k in update_fields.keys()])
            values = list(update_fields.values()) + [provider_id]

            cursor.execute(
                f"UPDATE providers SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                values,
            )
            conn.commit()
            self.logger.info(f"Updated provider {provider_id}")
            return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Failed to update provider {provider_id}: {e}")
            return False
        finally:
            self._close_connection(conn)

    def delete_provider(self, provider_id: int) -> bool:
        """Delete a provider and all associated tools."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM providers WHERE id = ?", (provider_id,))
            conn.commit()

            success = cursor.rowcount > 0
            if success:
                self.logger.info(f"Deleted provider ID: {provider_id}")
            return success

        except Exception as e:
            self.logger.error(f"Failed to delete provider {provider_id}: {e}")
            return False
        finally:
            self._close_connection(conn)
