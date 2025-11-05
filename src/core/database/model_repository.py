"""
Model repository module for model CRUD and query operations.

Handles all model-related database operations including add, get, update, delete,
and search functionality.
"""

import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


class ModelRepository:
    """Repository for model data access operations."""

    def __init__(self, get_connection_func) -> None:
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
        file_hash: Optional[str] = None,
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
                cursor.execute(
                    """
                    INSERT INTO models (filename, format, file_path, file_size, file_hash, last_modified)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                    (filename, format, file_path, file_size, file_hash),
                )

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
                cursor.execute(
                    """
                    SELECT m.*, mm.title, mm.description, mm.keywords, mm.category,
                           mm.source, mm.rating, mm.view_count, mm.last_viewed
                    FROM models m
                    LEFT JOIN model_metadata mm ON m.id = mm.model_id
                    WHERE m.file_hash = ?
                """,
                    (file_hash,),
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error("Failed to find model by hash: %s", e)
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
                cursor.execute(
                    """
                    UPDATE models SET file_hash = ?, last_modified = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (file_hash, model_id),
                )
                success = cursor.rowcount > 0
                conn.commit()
                if success:
                    logger.info("Updated file hash for model %s", model_id)
                return success
        except sqlite3.Error as e:
            logger.error("Failed to update file hash for model %s: {e}", model_id)
            return False

    @log_function_call(logger)
    def link_duplicate_model(self, duplicate_id: int, keep_id: int) -> bool:
        """
        Link a duplicate model to the model being kept.

        Args:
            duplicate_id: ID of duplicate model to link
            keep_id: ID of model to keep

        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE models SET linked_model_id = ?
                    WHERE id = ?
                """,
                    (keep_id, duplicate_id),
                )
                success = cursor.rowcount > 0
                conn.commit()
                if success:
                    logger.info("Linked duplicate model %s to {keep_id}", duplicate_id)
                return success
        except sqlite3.Error as e:
            logger.error("Failed to link duplicate model: %s", e)
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

                cursor.execute(
                    """
                    SELECT m.*, mm.title, mm.description, mm.keywords, mm.category,
                           mm.source, mm.rating, mm.view_count, mm.last_viewed
                    FROM models m
                    LEFT JOIN model_metadata mm ON m.id = mm.model_id
                    WHERE m.id = ?
                """,
                    (model_id,),
                )

                row = cursor.fetchone()
                return dict(row) if row else None

        except sqlite3.Error as e:
            logger.error("Failed to get model %s: {str(e)}", model_id)
            return None

    @log_function_call(logger)
    def get_all_models(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        exclude_duplicates: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get all models from the database.

        Args:
            limit: Maximum number of models to return
            offset: Number of models to skip
            exclude_duplicates: If True, exclude models with linked_model_id (duplicates)

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
                """

                if exclude_duplicates:
                    query += " WHERE m.linked_model_id IS NULL"

                query += " ORDER BY m.date_added DESC"

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
                logger.debug("Retrieved %s models", len(models))
                return models

        except sqlite3.Error as e:
            logger.error("Failed to get all models: %s", str(e))
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
                cursor.execute(
                    """
                    UPDATE models SET thumbnail_path = ?, last_modified = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (thumbnail_path, model_id),
                )
                success = cursor.rowcount > 0
                conn.commit()
                if success:
                    logger.info("Updated thumbnail for model %s", model_id)
                return success
        except sqlite3.Error as e:
            logger.error("Failed to update thumbnail for model %s: {e}", model_id)
            return False

    @log_function_call(logger)
    def update_model_camera_view(
        self,
        model_id: int,
        camera_position: Tuple[float, float, float],
        camera_focal_point: Tuple[float, float, float],
        camera_view_up: Tuple[float, float, float],
        camera_view_name: str,
    ) -> bool:
        """
        Update optimal camera view parameters for a model.

        Args:
            model_id: Model ID
            camera_position: Camera position (x, y, z)
            camera_focal_point: Camera focal point (x, y, z)
            camera_view_up: Camera view up vector (x, y, z)
            camera_view_name: Name of the view (front, right, back, left, top)

        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE models
                    SET camera_position_x = ?, camera_position_y = ?, camera_position_z = ?,
                        camera_focal_point_x = ?, camera_focal_point_y = ?, camera_focal_point_z = ?,
                        camera_view_up_x = ?, camera_view_up_y = ?, camera_view_up_z = ?,
                        camera_view_name = ?,
                        last_modified = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (
                        camera_position[0],
                        camera_position[1],
                        camera_position[2],
                        camera_focal_point[0],
                        camera_focal_point[1],
                        camera_focal_point[2],
                        camera_view_up[0],
                        camera_view_up[1],
                        camera_view_up[2],
                        camera_view_name,
                        model_id,
                    ),
                )
                success = cursor.rowcount > 0
                conn.commit()
                if success:
                    logger.info("Updated camera view for model %s to '%s'", model_id, camera_view_name)
                return success
        except sqlite3.Error as e:
            logger.error("Failed to update camera view for model %s: {e}", model_id)
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
                    logger.info("Deleted model %s", model_id)
                return success
        except sqlite3.Error as e:
            logger.error("Failed to delete model %s: {e}", model_id)
            return False
