"""
Model repository module for model CRUD and query operations.

Handles all model-related database operations including add, get, update, delete,
and search functionality.
"""

import sqlite3
from typing import Any, Dict, List, Optional

from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


class ModelRepository:
    """Repository for model data access operations."""

    def __init__(self, get_connection_func):
        """
        Initialize model repository.

        Args:
            get_connection_func: Function to get database connection
        """
        self._get_connection = get_connection_func

    @log_function_call(logger)
    def add_model(
        self,
        filename: str,
        format: str,
        file_path: str,
        file_size: Optional[int] = None,
        file_hash: Optional[str] = None
    ) -> int:
        """
        Add a new model to the database.

        Args:
            filename: Model filename
            format: Model format ('stl', 'mf3', 'obj', 'step')
            file_path: Full path to the model file
            file_size: File size in bytes
            file_hash: xxHash128 hash of file content

        Returns:
            ID of the inserted model
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO models (filename, format, file_path, file_size, file_hash, last_modified)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (filename, format, file_path, file_size, file_hash))

                model_id = cursor.lastrowid
                conn.commit()

                logger.info(f"Added model '{filename}' with ID: {model_id}")
                return model_id

        except sqlite3.Error as e:
            logger.error(f"Failed to add model '{filename}': {str(e)}")
            raise

    @log_function_call(logger)
    def find_model_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """
        Find a model by its file hash.

        Args:
            file_hash: xxHash128 hash to search for

        Returns:
            Model dict if found, None otherwise
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT m.*, mm.title, mm.description, mm.keywords, mm.category,
                           mm.source, mm.rating, mm.view_count, mm.last_viewed
                    FROM models m
                    LEFT JOIN model_metadata mm ON m.id = mm.model_id
                    WHERE m.file_hash = ?
                """, (file_hash,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Failed to find model by hash: {e}")
            return None

    @log_function_call(logger)
    def update_file_hash(self, model_id: int, file_hash: str) -> bool:
        """
        Update file hash for a model.

        Args:
            model_id: Model ID
            file_hash: xxHash128 hash to set (32 hex characters)

        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE models SET file_hash = ?, last_modified = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (file_hash, model_id))
                success = cursor.rowcount > 0
                conn.commit()
                if success:
                    logger.info(f"Updated file hash for model {model_id}")
                return success
        except sqlite3.Error as e:
            logger.error(f"Failed to update file hash for model {model_id}: {e}")
            return False

    @log_function_call(logger)
    def get_model(self, model_id: int) -> Optional[Dict[str, Any]]:
        """
        Get model information by ID.

        Args:
            model_id: Model ID

        Returns:
            Model information dictionary or None if not found
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT m.*, mm.title, mm.description, mm.keywords, mm.category,
                           mm.source, mm.rating, mm.view_count, mm.last_viewed
                    FROM models m
                    LEFT JOIN model_metadata mm ON m.id = mm.model_id
                    WHERE m.id = ?
                """, (model_id,))

                row = cursor.fetchone()
                return dict(row) if row else None

        except sqlite3.Error as e:
            logger.error(f"Failed to get model {model_id}: {str(e)}")
            return None

    @log_function_call(logger)
    def get_all_models(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all models from the database.

        Args:
            limit: Maximum number of models to return
            offset: Number of models to skip

        Returns:
            List of model dictionaries
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                query = """
                    SELECT m.*, mm.title, mm.description, mm.keywords, mm.category,
                           mm.source, mm.rating, mm.view_count, mm.last_viewed
                    FROM models m
                    LEFT JOIN model_metadata mm ON m.id = mm.model_id
                    ORDER BY m.date_added DESC
                """

                params = []
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                if offset:
                    query += " OFFSET ?"
                    params.append(offset)

                cursor.execute(query, params)
                rows = cursor.fetchall()

                models = [dict(row) for row in rows]
                logger.debug(f"Retrieved {len(models)} models")
                return models

        except sqlite3.Error as e:
            logger.error(f"Failed to get all models: {str(e)}")
            raise

    @log_function_call(logger)
    def update_model_thumbnail(self, model_id: int, thumbnail_path: str) -> bool:
        """
        Update thumbnail path for a model.

        Args:
            model_id: Model ID
            thumbnail_path: Path to thumbnail image

        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE models SET thumbnail_path = ?, last_modified = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (thumbnail_path, model_id))
                success = cursor.rowcount > 0
                conn.commit()
                if success:
                    logger.info(f"Updated thumbnail for model {model_id}")
                return success
        except sqlite3.Error as e:
            logger.error(f"Failed to update thumbnail for model {model_id}: {e}")
            return False

    @log_function_call(logger)
    def delete_model(self, model_id: int) -> bool:
        """
        Delete a model from the database.

        Args:
            model_id: Model ID

        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM models WHERE id = ?", (model_id,))
                success = cursor.rowcount > 0
                conn.commit()
                if success:
                    logger.info(f"Deleted model {model_id}")
                return success
        except sqlite3.Error as e:
            logger.error(f"Failed to delete model {model_id}: {e}")
            return False

