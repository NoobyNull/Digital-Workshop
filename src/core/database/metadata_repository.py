"""
Metadata repository module for metadata and category operations.

Handles model metadata, camera orientation, and category management.
"""

import sqlite3
from typing import Any, Dict, List, Optional

from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


class MetadataRepository:
    """Repository for metadata and category data access operations."""

    def __init__(self, get_connection_func):
        """
        Initialize metadata repository.

        Args:
            get_connection_func: Function to get database connection
        """
        self._get_connection = get_connection_func

    @log_function_call(logger)
    def add_metadata(self, model_id: int, **kwargs) -> int:
        """
        Add metadata for a model.

        Args:
            model_id: Model ID
            **kwargs: Metadata fields (title, description, keywords, category, source, rating)

        Returns:
            ID of the inserted metadata
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO model_metadata (model_id, title, description, keywords, category, source, rating)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    model_id,
                    kwargs.get('title'),
                    kwargs.get('description'),
                    kwargs.get('keywords'),
                    kwargs.get('category'),
                    kwargs.get('source'),
                    kwargs.get('rating', 0)
                ))

                metadata_id = cursor.lastrowid
                conn.commit()

                logger.info(f"Added metadata for model {model_id}")
                return metadata_id

        except sqlite3.Error as e:
            logger.error(f"Failed to add metadata for model {model_id}: {str(e)}")
            raise

    @log_function_call(logger)
    def update_model_metadata(self, model_id: int, **kwargs) -> bool:
        """
        Update model metadata.

        Args:
            model_id: Model ID
            **kwargs: Fields to update

        Returns:
            True if update was successful
        """
        if not kwargs:
            logger.warning("No fields provided for metadata update")
            return False

        # Filter valid fields
        valid_fields = {'title', 'description', 'keywords', 'category', 'source', 'rating'}
        metadata_updates = {k: v for k, v in kwargs.items() if k in valid_fields}

        if not metadata_updates:
            logger.warning("No valid metadata fields provided")
            return False

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Build update query
                set_clause = ", ".join([f"{k} = ?" for k in metadata_updates.keys()])
                values = list(metadata_updates.values())
                values.append(model_id)

                cursor.execute(f"""
                    UPDATE model_metadata
                    SET {set_clause}
                    WHERE model_id = ?
                """, values)

                success = cursor.rowcount > 0
                conn.commit()

                if success:
                    logger.info(f"Updated metadata for model {model_id}")

                return success

        except sqlite3.Error as e:
            logger.error(f"Failed to update metadata for model {model_id}: {str(e)}")
            raise

    @log_function_call(logger)
    def save_camera_orientation(self, model_id: int, camera_data: Dict[str, float]) -> bool:
        """
        Save camera orientation for a model.

        Args:
            model_id: Model ID
            camera_data: Dict with keys: position_x/y/z, focal_x/y/z, view_up_x/y/z

        Returns:
            True if save was successful
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE model_metadata
                    SET camera_position_x = ?, camera_position_y = ?, camera_position_z = ?,
                        camera_focal_x = ?, camera_focal_y = ?, camera_focal_z = ?,
                        camera_view_up_x = ?, camera_view_up_y = ?, camera_view_up_z = ?
                    WHERE model_id = ?
                """, (
                    camera_data.get('position_x'), camera_data.get('position_y'), camera_data.get('position_z'),
                    camera_data.get('focal_x'), camera_data.get('focal_y'), camera_data.get('focal_z'),
                    camera_data.get('view_up_x'), camera_data.get('view_up_y'), camera_data.get('view_up_z'),
                    model_id
                ))
                success = cursor.rowcount > 0
                conn.commit()
                if success:
                    logger.info(f"Saved camera orientation for model {model_id}")
                return success
        except sqlite3.Error as e:
            logger.error(f"Failed to save camera orientation: {e}")
            return False

    @log_function_call(logger)
    def get_camera_orientation(self, model_id: int) -> Optional[Dict[str, float]]:
        """
        Get saved camera orientation for a model.

        Args:
            model_id: Model ID

        Returns:
            Dict with camera data or None if not saved
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT camera_position_x, camera_position_y, camera_position_z,
                           camera_focal_x, camera_focal_y, camera_focal_z,
                           camera_view_up_x, camera_view_up_y, camera_view_up_z
                    FROM model_metadata WHERE model_id = ?
                """, (model_id,))
                row = cursor.fetchone()
                if row and row['camera_position_x'] is not None:
                    return dict(row)
                return None
        except sqlite3.Error as e:
            logger.error(f"Failed to get camera orientation: {e}")
            return None

    @log_function_call(logger)
    def increment_view_count(self, model_id: int) -> bool:
        """
        Increment the view count for a model.

        Args:
            model_id: Model ID

        Returns:
            True if update was successful
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE model_metadata
                    SET view_count = view_count + 1, last_viewed = CURRENT_TIMESTAMP
                    WHERE model_id = ?
                """, (model_id,))

                success = cursor.rowcount > 0
                conn.commit()

                if success:
                    logger.debug(f"Incremented view count for model {model_id}")

                return success

        except sqlite3.Error as e:
            logger.error(f"Failed to increment view count for model {model_id}: {str(e)}")
            raise

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

                cursor.execute("""
                    SELECT * FROM categories
                    ORDER BY name ASC
                """)

                rows = cursor.fetchall()
                categories = [dict(row) for row in rows]

                logger.debug(f"Retrieved {len(categories)} categories")
                return categories

        except sqlite3.Error as e:
            logger.error(f"Failed to get categories: {str(e)}")
            raise

    @log_function_call(logger)
    def add_category(
        self,
        name: str,
        color: str = "#CCCCCC",
        sort_order: int = 0
    ) -> int:
        """
        Add a new category.

        Args:
            name: Category name
            color: Category color hex code
            sort_order: Sort order for display

        Returns:
            ID of the inserted category
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO categories (name, color, sort_order)
                    VALUES (?, ?, ?)
                """, (name, color, sort_order))

                category_id = cursor.lastrowid
                conn.commit()

                logger.info(f"Added category '{name}' with ID: {category_id}")
                return category_id

        except sqlite3.Error as e:
            logger.error(f"Failed to add category '{name}': {str(e)}")
            raise

    @log_function_call(logger)
    def delete_category(self, category_id: int) -> bool:
        """
        Delete a category.

        Args:
            category_id: Category ID

        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
                success = cursor.rowcount > 0
                conn.commit()
                if success:
                    logger.info(f"Deleted category {category_id}")
                return success
        except sqlite3.Error as e:
            logger.error(f"Failed to delete category {category_id}: {e}")
            return False

