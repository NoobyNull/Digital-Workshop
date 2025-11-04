"""
Enhanced Model Repository with complete interface compliance.

This module provides a fully compliant implementation of IModelRepository
with improved performance, transaction management, and error handling.
"""

import sqlite3
import threading
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

from ..logging_config import get_logger, log_function_call
from ..interfaces.repository_interfaces import IModelRepository

logger = get_logger(__name__)


class EnhancedModelRepository(IModelRepository):
    """
    Enhanced repository for model data access operations.

    Fully implements IModelRepository interface with improved performance,
    transaction management, and comprehensive error handling.
    """

    def __init__(self, get_connection_func):
        """
        Initialize enhanced model repository.

        Args:
            get_connection_func: Function to get database connection
        """
        self._get_connection = get_connection_func
        self._lock = threading.Lock()

    @log_function_call(logger)
    def create(self, model_data: Dict[str, Any]) -> str:
        """
        Create a new model record.

        Args:
            model_data: Dictionary containing model data

        Returns:
            Unique model ID if successful, None otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Validate required fields
                required_fields = ["filename", "format", "file_path"]
                for field in required_fields:
                    if field not in model_data:
                        raise ValueError(f"Required field '{field}' missing from model_data")

                cursor.execute(
                    """
                    INSERT INTO models (filename, format, file_path, file_size, file_hash, 
                                      thumbnail_path, last_modified)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                    (
                        model_data["filename"],
                        model_data["format"],
                        model_data["file_path"],
                        model_data.get("file_size"),
                        model_data.get("file_hash"),
                        model_data.get("thumbnail_path"),
                    ),
                )

                model_id = str(cursor.lastrowid)
                conn.commit()

                logger.info(f"Created model with ID: {model_id}")
                return model_id

        except sqlite3.Error as e:
            logger.error(f"Failed to create model: {str(e)}")
            return None
        except ValueError as e:
            logger.error(f"Invalid model data: {str(e)}")
            return None

    @log_function_call(logger)
    def read(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Read a model record by ID.

        Args:
            model_id: Unique identifier of the model

        Returns:
            Dictionary containing model data, None if not found
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
                if row:
                    return dict(row)
                return None

        except sqlite3.Error as e:
            logger.error(f"Failed to read model {model_id}: {str(e)}")
            return None

    @log_function_call(logger)
    def update(self, model_id: str, model_data: Dict[str, Any]) -> bool:
        """
        Update an existing model record.

        Args:
            model_id: Unique identifier of the model
            model_data: Dictionary containing updated model data

        Returns:
            True if update was successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Filter valid fields
                valid_fields = {
                    "filename",
                    "format",
                    "file_path",
                    "file_size",
                    "file_hash",
                    "thumbnail_path",
                }
                updates = {k: v for k, v in model_data.items() if k in valid_fields}

                if not updates:
                    logger.warning("No valid fields provided for model update")
                    return False

                # Build update query
                set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
                values = list(updates.values())
                values.extend([model_id])

                cursor.execute(
                    f"""
                    UPDATE models
                    SET {set_clause}, last_modified = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    values,
                )

                success = cursor.rowcount > 0
                conn.commit()

                if success:
                    logger.info(f"Updated model {model_id}")
                else:
                    logger.warning(f"Model {model_id} not found for update")

                return success

        except sqlite3.Error as e:
            logger.error(f"Failed to update model {model_id}: {str(e)}")
            return False

    @log_function_call(logger)
    def delete(self, model_id: str) -> bool:
        """
        Delete a model record.

        Args:
            model_id: Unique identifier of the model to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Delete related metadata first (due to foreign key constraints)
                cursor.execute("DELETE FROM model_metadata WHERE model_id = ?", (model_id,))

                # Delete the model
                cursor.execute("DELETE FROM models WHERE id = ?", (model_id,))

                success = cursor.rowcount > 0
                conn.commit()

                if success:
                    logger.info(f"Deleted model {model_id}")
                else:
                    logger.warning(f"Model {model_id} not found for deletion")

                return success

        except sqlite3.Error as e:
            logger.error(f"Failed to delete model {model_id}: {str(e)}")
            return False

    @log_function_call(logger)
    def list_all(self) -> List[Dict[str, Any]]:
        """
        List all model records.

        Returns:
            List of dictionaries containing all model data
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
                    ORDER BY m.date_added DESC
                """
                )

                rows = cursor.fetchall()
                models = [dict(row) for row in rows]

                logger.debug(f"Retrieved {len(models)} models")
                return models

        except sqlite3.Error as e:
            logger.error(f"Failed to list all models: {str(e)}")
            return []

    @log_function_call(logger)
    def search(self, criteria: Dict[str, Any]) -> List[str]:
        """
        Search for models matching criteria.

        Args:
            criteria: Dictionary containing search criteria

        Returns:
            List of model IDs matching the criteria
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                sql = """
                    SELECT DISTINCT m.id
                    FROM models m
                    LEFT JOIN model_metadata mm ON m.id = mm.model_id
                    WHERE 1=1
                """
                params = []

                # Handle different search criteria
                if "filename" in criteria:
                    sql += " AND m.filename LIKE ?"
                    params.append(f"%{criteria['filename']}%")

                if "format" in criteria:
                    sql += " AND m.format = ?"
                    params.append(criteria["format"])

                if "category" in criteria:
                    sql += " AND mm.category = ?"
                    params.append(criteria["category"])

                if "title" in criteria:
                    sql += " AND mm.title LIKE ?"
                    params.append(f"%{criteria['title']}%")

                if "keywords" in criteria:
                    sql += " AND mm.keywords LIKE ?"
                    params.append(f"%{criteria['keywords']}%")

                if "min_file_size" in criteria:
                    sql += " AND m.file_size >= ?"
                    params.append(criteria["min_file_size"])

                if "max_file_size" in criteria:
                    sql += " AND m.file_size <= ?"
                    params.append(criteria["max_file_size"])

                sql += " ORDER BY m.date_added DESC"

                cursor.execute(sql, params)
                rows = cursor.fetchall()

                model_ids = [str(row[0]) for row in rows]
                logger.debug(f"Search returned {len(model_ids)} results for criteria: {criteria}")
                return model_ids

        except sqlite3.Error as e:
            logger.error(f"Failed to search models: {str(e)}")
            return []

    @log_function_call(logger)
    def exists(self, model_id: str) -> bool:
        """
        Check if a model exists.

        Args:
            model_id: Unique identifier of the model

        Returns:
            True if model exists, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM models WHERE id = ?", (model_id,))
                count = cursor.fetchone()[0]
                return count > 0

        except sqlite3.Error as e:
            logger.error(f"Failed to check model existence {model_id}: {str(e)}")
            return False

    @log_function_call(logger)
    def count(self) -> int:
        """
        Get total count of models.

        Returns:
            Total number of models in the repository
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM models")
                count = cursor.fetchone()[0]
                return count

        except sqlite3.Error as e:
            logger.error(f"Failed to get model count: {str(e)}")
            return 0

    # Additional enhanced methods for better performance and functionality

    @log_function_call(logger)
    def get_models_paginated(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get models with pagination support.

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

                cursor.execute(
                    """
                    SELECT m.*, mm.title, mm.description, mm.keywords, mm.category,
                           mm.source, mm.rating, mm.view_count, mm.last_viewed
                    FROM models m
                    LEFT JOIN model_metadata mm ON m.id = mm.model_id
                    ORDER BY m.date_added DESC
                    LIMIT ? OFFSET ?
                """,
                    (limit, offset),
                )

                rows = cursor.fetchall()
                models = [dict(row) for row in rows]

                logger.debug(f"Retrieved {len(models)} models (limit: {limit}, offset: {offset})")
                return models

        except sqlite3.Error as e:
            logger.error(f"Failed to get paginated models: {str(e)}")
            return []

    @log_function_call(logger)
    def find_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """
        Find a model by its file hash.

        Args:
            file_hash: File hash to search for

        Returns:
            Model dictionary if found, None otherwise
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
            logger.error(f"Failed to find model by hash: {str(e)}")
            return None

    @log_function_call(logger)
    def bulk_create(self, models_data: List[Dict[str, Any]]) -> List[str]:
        """
        Create multiple models in a single transaction.

        Args:
            models_data: List of model data dictionaries

        Returns:
            List of created model IDs
        """
        created_ids = []
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                for model_data in models_data:
                    cursor.execute(
                        """
                        INSERT INTO models (filename, format, file_path, file_size, file_hash, 
                                          thumbnail_path, last_modified)
                        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                        (
                            model_data["filename"],
                            model_data["format"],
                            model_data["file_path"],
                            model_data.get("file_size"),
                            model_data.get("file_hash"),
                            model_data.get("thumbnail_path"),
                        ),
                    )
                    created_ids.append(str(cursor.lastrowid))

                conn.commit()
                logger.info(f"Bulk created {len(created_ids)} models")
                return created_ids

        except sqlite3.Error as e:
            logger.error(f"Failed to bulk create models: {str(e)}")
            return []

    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.

        Yields:
            Database connection with transaction support
        """
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
