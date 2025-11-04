"""
Enhanced Metadata Repository with complete interface compliance.

This module provides a fully compliant implementation of IMetadataRepository
with improved performance, transaction management, and error handling.
"""

import sqlite3
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

from ..logging_config import get_logger, log_function_call
from ..interfaces.repository_interfaces import IMetadataRepository

logger = get_logger(__name__)


class EnhancedMetadataRepository(IMetadataRepository):
    """
    Enhanced repository for metadata operations.

    Fully implements IMetadataRepository interface with improved performance,
    transaction management, and comprehensive error handling.
    """

    def __init__(self, get_connection_func):
        """
        Initialize enhanced metadata repository.

        Args:
            get_connection_func: Function to get database connection
        """
        self._get_connection = get_connection_func

    @log_function_call(logger)
    def add_metadata(self, model_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Add metadata for a model.

        Args:
            model_id: Unique identifier of the model
            metadata: Dictionary containing metadata

        Returns:
            True if metadata was added successfully, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Extract metadata fields
                title = metadata.get("title")
                description = metadata.get("description")
                keywords = metadata.get("keywords")
                category = metadata.get("category")
                source = metadata.get("source")
                rating = metadata.get("rating", 0)

                # Handle camera data if present
                camera_data = metadata.get("camera_data", {})

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO model_metadata (
                        model_id, title, description, keywords, category, source, rating,
                        camera_position_x, camera_position_y, camera_position_z,
                        camera_focal_x, camera_focal_y, camera_focal_z,
                        camera_view_up_x, camera_view_up_y, camera_view_up_z
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        model_id,
                        title,
                        description,
                        keywords,
                        category,
                        source,
                        rating,
                        camera_data.get("position_x"),
                        camera_data.get("position_y"),
                        camera_data.get("position_z"),
                        camera_data.get("focal_x"),
                        camera_data.get("focal_y"),
                        camera_data.get("focal_z"),
                        camera_data.get("view_up_x"),
                        camera_data.get("view_up_y"),
                        camera_data.get("view_up_z"),
                    ),
                )

                success = cursor.rowcount > 0
                conn.commit()

                if success:
                    logger.info(f"Added metadata for model {model_id}")
                else:
                    logger.warning(f"No metadata added for model {model_id}")

                return success

        except sqlite3.Error as e:
            logger.error(f"Failed to add metadata for model {model_id}: {str(e)}")
            return False

    @log_function_call(logger)
    def get_metadata(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a model.

        Args:
            model_id: Unique identifier of the model

        Returns:
            Dictionary containing metadata, None if not found
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT * FROM model_metadata WHERE model_id = ?
                """,
                    (model_id,),
                )

                row = cursor.fetchone()
                if row:
                    metadata = dict(row)

                    # Extract camera data
                    camera_data = {
                        "position_x": metadata.pop("camera_position_x", None),
                        "position_y": metadata.pop("camera_position_y", None),
                        "position_z": metadata.pop("camera_position_z", None),
                        "focal_x": metadata.pop("camera_focal_x", None),
                        "focal_y": metadata.pop("camera_focal_y", None),
                        "focal_z": metadata.pop("camera_focal_z", None),
                        "view_up_x": metadata.pop("camera_view_up_x", None),
                        "view_up_y": metadata.pop("camera_view_up_y", None),
                        "view_up_z": metadata.pop("camera_view_up_z", None),
                    }

                    # Only include camera data if any values are set
                    if any(v is not None for v in camera_data.values()):
                        metadata["camera_data"] = camera_data

                    return metadata
                return None

        except sqlite3.Error as e:
            logger.error(f"Failed to get metadata for model {model_id}: {str(e)}")
            return None

    @log_function_call(logger)
    def update_metadata(self, model_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update metadata for a model.

        Args:
            model_id: Unique identifier of the model
            metadata: Dictionary containing updated metadata

        Returns:
            True if metadata was updated successfully, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Extract regular metadata fields
                regular_fields = {
                    "title",
                    "description",
                    "keywords",
                    "category",
                    "source",
                    "rating",
                }
                updates = {k: v for k, v in metadata.items() if k in regular_fields}

                if updates:
                    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
                    values = list(updates.values())
                    values.append(model_id)

                    cursor.execute(
                        f"""
                        UPDATE model_metadata
                        SET {set_clause}
                        WHERE model_id = ?
                    """,
                        values,
                    )

                # Handle camera data separately
                if "camera_data" in metadata:
                    camera_data = metadata["camera_data"]
                    camera_updates = []
                    camera_values = []

                    for key, value in camera_data.items():
                        if value is not None:
                            camera_updates.append(f"camera_{key} = ?")
                            camera_values.append(value)

                    if camera_updates:
                        camera_values.append(model_id)
                        set_clause = ", ".join(camera_updates)
                        cursor.execute(
                            f"""
                            UPDATE model_metadata
                            SET {set_clause}
                            WHERE model_id = ?
                        """,
                            camera_values,
                        )

                success = cursor.rowcount > 0
                conn.commit()

                if success:
                    logger.info(f"Updated metadata for model {model_id}")
                else:
                    logger.warning(f"No metadata found to update for model {model_id}")

                return success

        except sqlite3.Error as e:
            logger.error(f"Failed to update metadata for model {model_id}: {str(e)}")
            return False

    @log_function_call(logger)
    def delete_metadata(self, model_id: str) -> bool:
        """
        Delete metadata for a model.

        Args:
            model_id: Unique identifier of the model

        Returns:
            True if metadata was deleted successfully, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM model_metadata WHERE model_id = ?", (model_id,)
                )

                success = cursor.rowcount > 0
                conn.commit()

                if success:
                    logger.info(f"Deleted metadata for model {model_id}")
                else:
                    logger.warning(f"No metadata found to delete for model {model_id}")

                return success

        except sqlite3.Error as e:
            logger.error(f"Failed to delete metadata for model {model_id}: {str(e)}")
            return False

    @log_function_call(logger)
    def search_by_metadata(self, criteria: Dict[str, Any]) -> List[str]:
        """
        Search models by metadata criteria.

        Args:
            criteria: Dictionary containing metadata search criteria

        Returns:
            List of model IDs matching the criteria
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                sql = """
                    SELECT DISTINCT model_id
                    FROM model_metadata
                    WHERE 1=1
                """
                params = []

                # Handle different search criteria
                if "title" in criteria:
                    sql += " AND title LIKE ?"
                    params.append(f"%{criteria['title']}%")

                if "description" in criteria:
                    sql += " AND description LIKE ?"
                    params.append(f"%{criteria['description']}%")

                if "keywords" in criteria:
                    sql += " AND keywords LIKE ?"
                    params.append(f"%{criteria['keywords']}%")

                if "category" in criteria:
                    sql += " AND category = ?"
                    params.append(criteria["category"])

                if "source" in criteria:
                    sql += " AND source LIKE ?"
                    params.append(f"%{criteria['source']}%")

                if "min_rating" in criteria:
                    sql += " AND rating >= ?"
                    params.append(criteria["min_rating"])

                if "max_rating" in criteria:
                    sql += " AND rating <= ?"
                    params.append(criteria["max_rating"])

                sql += " ORDER BY model_id"

                cursor.execute(sql, params)
                rows = cursor.fetchall()

                model_ids = [str(row[0]) for row in rows]
                logger.debug(f"Metadata search returned {len(model_ids)} results")
                return model_ids

        except sqlite3.Error as e:
            logger.error(f"Failed to search by metadata: {str(e)}")
            return []

    @log_function_call(logger)
    def get_metadata_keys(self, model_id: str) -> List[str]:
        """
        Get all metadata keys for a model.

        Args:
            model_id: Unique identifier of the model

        Returns:
            List of metadata key names
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("PRAGMA table_info(model_metadata)")
                columns = cursor.fetchall()

                # Filter out system columns and return only data columns
                exclude_columns = {"id", "model_id", "last_viewed"}
                keys = [col[1] for col in columns if col[1] not in exclude_columns]

                return keys

        except sqlite3.Error as e:
            logger.error(f"Failed to get metadata keys for model {model_id}: {str(e)}")
            return []

    @log_function_call(logger)
    def get_metadata_value(self, model_id: str, key: str) -> Optional[Any]:
        """
        Get a specific metadata value.

        Args:
            model_id: Unique identifier of the model
            key: Metadata key name

        Returns:
            Metadata value if found, None otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Handle camera data keys
                if key.startswith("camera_"):
                    camera_key = key[7:]  # Remove 'camera_' prefix
                    cursor.execute(
                        f"SELECT camera_{camera_key} FROM model_metadata WHERE model_id = ?",
                        (model_id,),
                    )
                else:
                    cursor.execute(
                        f"SELECT {key} FROM model_metadata WHERE model_id = ?",
                        (model_id,),
                    )

                row = cursor.fetchone()
                return row[0] if row and row[0] is not None else None

        except sqlite3.Error as e:
            logger.error(
                f"Failed to get metadata value {key} for model {model_id}: {str(e)}"
            )
            return None

    @log_function_call(logger)
    def set_metadata_value(self, model_id: str, key: str, value: Any) -> bool:
        """
        Set a specific metadata value.

        Args:
            model_id: Unique identifier of the model
            key: Metadata key name
            value: Metadata value

        Returns:
            True if value was set successfully, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Handle camera data keys
                if key.startswith("camera_"):
                    camera_key = key[7:]  # Remove 'camera_' prefix
                    column_name = f"camera_{camera_key}"
                else:
                    column_name = key

                cursor.execute(
                    f"""
                    UPDATE model_metadata
                    SET {column_name} = ?
                    WHERE model_id = ?
                """,
                    (value, model_id),
                )

                success = cursor.rowcount > 0
                conn.commit()

                if success:
                    logger.debug(
                        f"Set metadata value {key} = {value} for model {model_id}"
                    )
                else:
                    logger.warning(
                        f"No metadata record found to update for model {model_id}"
                    )

                return success

        except sqlite3.Error as e:
            logger.error(
                f"Failed to set metadata value {key} for model {model_id}: {str(e)}"
            )
            return False

    # Additional enhanced methods for better functionality

    @log_function_call(logger)
    def increment_view_count(self, model_id: str) -> bool:
        """
        Increment the view count for a model.

        Args:
            model_id: Unique identifier of the model

        Returns:
            True if increment was successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE model_metadata
                    SET view_count = view_count + 1, last_viewed = CURRENT_TIMESTAMP
                    WHERE model_id = ?
                """,
                    (model_id,),
                )

                success = cursor.rowcount > 0
                conn.commit()

                if success:
                    logger.debug(f"Incremented view count for model {model_id}")
                else:
                    logger.warning(
                        f"No metadata found to increment view count for model {model_id}"
                    )

                return success

        except sqlite3.Error as e:
            logger.error(
                f"Failed to increment view count for model {model_id}: {str(e)}"
            )
            return False

    @log_function_call(logger)
    def get_categories(self) -> List[Dict[str, Any]]:
        """
        Get all categories from the database.

        Returns:
            List of category dictionaries
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT * FROM categories
                    ORDER BY sort_order ASC, name ASC
                """
                )

                rows = cursor.fetchall()
                categories = [dict(row) for row in rows]

                logger.debug(f"Retrieved {len(categories)} categories")
                return categories

        except sqlite3.Error as e:
            logger.error(f"Failed to get categories: {str(e)}")
            return []

    @log_function_call(logger)
    def add_category(
        self, name: str, color: Optional[str] = None, sort_order: int = 0
    ) -> str:
        """
        Add a new category.

        Args:
            name: Category name
            color: Category color hex code (uses theme color if None)
            sort_order: Sort order for display

        Returns:
            Category ID if successful, None otherwise
        """
        try:
            # Use theme color if none provided
            if color is None:
                try:
                    from ...gui.theme import COLORS

                    color = COLORS.category_default
                except (ImportError, AttributeError):
                    color = "#CCCCCC"  # Fallback to original default

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO categories (name, color, sort_order)
                    VALUES (?, ?, ?)
                """,
                    (name, color, sort_order),
                )

                category_id = str(cursor.lastrowid)
                conn.commit()

                logger.info(f"Added category '{name}' with ID: {category_id}")
                return category_id

        except sqlite3.Error as e:
            logger.error(f"Failed to add category '{name}': {str(e)}")
            return None

    @log_function_call(logger)
    def delete_category(self, category_id: str) -> bool:
        """
        Delete a category.

        Args:
            category_id: Unique identifier of the category

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))

                success = cursor.rowcount > 0
                conn.commit()

                if success:
                    logger.info(f"Deleted category {category_id}")
                else:
                    logger.warning(f"Category {category_id} not found for deletion")

                return success

        except sqlite3.Error as e:
            logger.error(f"Failed to delete category {category_id}: {str(e)}")
            return False

    @log_function_call(logger)
    def get_popular_categories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get categories ordered by usage count.

        Args:
            limit: Maximum number of categories to return

        Returns:
            List of category dictionaries with usage counts
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT c.*, COUNT(mm.model_id) as usage_count
                    FROM categories c
                    LEFT JOIN model_metadata mm ON c.name = mm.category
                    GROUP BY c.id
                    ORDER BY usage_count DESC, c.sort_order ASC
                    LIMIT ?
                """,
                    (limit,),
                )

                rows = cursor.fetchall()
                categories = [dict(row) for row in rows]

                logger.debug(f"Retrieved {len(categories)} popular categories")
                return categories

        except sqlite3.Error as e:
            logger.error(f"Failed to get popular categories: {str(e)}")
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
