"""
Refactored database manager - facade pattern for modular database operations.

Delegates to specialized repository and maintenance modules for clean separation of concerns.
"""

import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..logging_config import get_logger, log_function_call
from .db_operations import DatabaseOperations
from .model_repository import ModelRepository
from .metadata_repository import MetadataRepository
from .db_maintenance import DatabaseMaintenance

logger = get_logger(__name__)


class DatabaseManager:
    """
    Facade for database operations.

    Delegates to specialized modules for models, metadata, maintenance, and operations.
    """

    def __init__(self, db_path: str = "data/3dmm.db"):
        """
        Initialize the database manager.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self._lock = threading.Lock()

        logger.info(f"Initializing database manager with path: {self.db_path}")

        # Initialize specialized modules
        self._db_ops = DatabaseOperations(str(self.db_path))
        self._model_repo = ModelRepository(self._db_ops.get_connection)
        self._metadata_repo = MetadataRepository(self._db_ops.get_connection)
        self._maintenance = DatabaseMaintenance(self._db_ops.get_connection)

        # Initialize database schema
        self._db_ops.initialize_schema()

    # ===== Model Operations (delegated to ModelRepository) =====

    def add_model(
        self,
        filename: str,
        format: str,
        file_path: str,
        file_size: Optional[int] = None,
        file_hash: Optional[str] = None
    ) -> int:
        """Add a new model to the database."""
        return self._model_repo.add_model(filename, format, file_path, file_size, file_hash)

    def find_model_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Find a model by its file hash."""
        return self._model_repo.find_model_by_hash(file_hash)

    def update_file_hash(self, model_id: int, file_hash: str) -> bool:
        """Update file hash for a model."""
        return self._model_repo.update_file_hash(model_id, file_hash)

    def get_model(self, model_id: int) -> Optional[Dict[str, Any]]:
        """Get model information by ID."""
        return self._model_repo.get_model(model_id)

    def get_all_models(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all models from the database."""
        return self._model_repo.get_all_models(limit, offset)

    def update_model_thumbnail(self, model_id: int, thumbnail_path: str) -> bool:
        """Update thumbnail path for a model."""
        return self._model_repo.update_model_thumbnail(model_id, thumbnail_path)

    def delete_model(self, model_id: int) -> bool:
        """Delete a model from the database."""
        return self._model_repo.delete_model(model_id)

    # ===== Metadata Operations (delegated to MetadataRepository) =====

    def add_metadata(self, model_id: int, **kwargs) -> int:
        """Add metadata for a model."""
        return self._metadata_repo.add_metadata(model_id, **kwargs)

    # Compatibility alias for tests
    def add_model_metadata(self, model_id: int, **kwargs) -> int:
        """Add metadata for a model (compatibility alias)."""
        return self.add_metadata(model_id, **kwargs)

    def update_model_metadata(self, model_id: int, **kwargs) -> bool:
        """Update model metadata."""
        return self._metadata_repo.update_model_metadata(model_id, **kwargs)

    def save_camera_orientation(self, model_id: int, camera_data: Dict[str, float]) -> bool:
        """Save camera orientation for a model."""
        return self._metadata_repo.save_camera_orientation(model_id, camera_data)

    def get_camera_orientation(self, model_id: int) -> Optional[Dict[str, float]]:
        """Get saved camera orientation for a model."""
        return self._metadata_repo.get_camera_orientation(model_id)

    def increment_view_count(self, model_id: int) -> bool:
        """Increment the view count for a model."""
        return self._metadata_repo.increment_view_count(model_id)

    def get_categories(self) -> List[Dict[str, Any]]:
        """Get all categories from the database."""
        return self._metadata_repo.get_categories()

    def add_category(self, name: str, color: str = "#CCCCCC", sort_order: int = 0) -> int:
        """Add a new category."""
        return self._metadata_repo.add_category(name, color, sort_order)

    def delete_category(self, category_id: int) -> bool:
        """Delete a category."""
        return self._metadata_repo.delete_category(category_id)

    # ===== Maintenance Operations (delegated to DatabaseMaintenance) =====

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        return self._maintenance.get_database_stats()

    def vacuum_database(self) -> None:
        """Vacuum the database to reclaim unused space."""
        return self._maintenance.vacuum_database()

    def analyze_database(self) -> None:
        """Analyze the database to update query planner statistics."""
        return self._maintenance.analyze_database()

    # ===== Additional Methods for Compatibility =====

    def update_model(self, model_id: int, **kwargs) -> bool:
        """
        Update model information.

        Args:
            model_id: Model ID
            **kwargs: Fields to update (filename, format, file_path, file_size)

        Returns:
            True if successful
        """
        try:
            with self._db_ops.get_connection() as conn:
                cursor = conn.cursor()

                # Filter valid fields
                valid_fields = {'filename', 'format', 'file_path', 'file_size'}
                updates = {k: v for k, v in kwargs.items() if k in valid_fields}

                if not updates:
                    return False

                # Build update query
                set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
                values = list(updates.values())
                values.append(model_id)

                cursor.execute(f"""
                    UPDATE models
                    SET {set_clause}, last_modified = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, values)

                success = cursor.rowcount > 0
                conn.commit()

                if success:
                    logger.info(f"Updated model {model_id}")

                return success

        except Exception as e:
            logger.error(f"Failed to update model {model_id}: {e}")
            return False

    def search_models(
        self,
        query: str = "",
        category: Optional[str] = None,
        format: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for models by query and filters.

        Args:
            query: Search query string
            category: Filter by category
            format: Filter by format

        Returns:
            List of matching models
        """
        try:
            with self._db_ops.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                sql = """
                    SELECT m.*, mm.title, mm.description, mm.keywords, mm.category,
                           mm.source, mm.rating, mm.view_count, mm.last_viewed
                    FROM models m
                    LEFT JOIN model_metadata mm ON m.id = mm.model_id
                    WHERE 1=1
                """
                params = []

                if query:
                    sql += """ AND (
                        m.filename LIKE ? OR
                        mm.title LIKE ? OR
                        mm.description LIKE ? OR
                        mm.keywords LIKE ?
                    )"""
                    query_param = f"%{query}%"
                    params.extend([query_param] * 4)

                if category:
                    sql += " AND mm.category = ?"
                    params.append(category)

                if format:
                    sql += " AND m.format = ?"
                    params.append(format)

                cursor.execute(sql, params)
                rows = cursor.fetchall()

                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to search models: {e}")
            return []

    def update_category(self, category_id: int, **kwargs) -> bool:
        """
        Update a category.

        Args:
            category_id: Category ID
            **kwargs: Fields to update (name, color)

        Returns:
            True if successful
        """
        try:
            with self._db_ops.get_connection() as conn:
                cursor = conn.cursor()

                # Filter valid fields
                valid_fields = {'name', 'color'}
                updates = {k: v for k, v in kwargs.items() if k in valid_fields}

                if not updates:
                    return False

                # Build update query
                set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
                values = list(updates.values())
                values.append(category_id)

                cursor.execute(f"""
                    UPDATE categories
                    SET {set_clause}
                    WHERE id = ?
                """, values)

                success = cursor.rowcount > 0
                conn.commit()

                if success:
                    logger.info(f"Updated category {category_id}")

                return success

        except Exception as e:
            logger.error(f"Failed to update category {category_id}: {e}")
            return False

    # ===== Connection Management =====

    @log_function_call(logger)
    def close(self) -> None:
        """Close the database connection."""
        logger.info("Database manager closed")

