"""
Background repository for handling default backgrounds in the database.

This module provides CRUD operations for backgrounds that can be associated with models.
"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


class BackgroundRepository:
    """Repository for managing backgrounds in the database."""

    def __init__(self, get_connection_func):
        """
        Initialize the background repository.

        Args:
            get_connection_func: Function to get database connection
        """
        self._get_connection = get_connection_func
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info("BackgroundRepository initialized")

    @log_function_call(logger)
    def add_background(
        self,
        name: str,
        file_path: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        file_size: Optional[int] = None,
        is_default: bool = True,
        is_deletable: bool = False,
    ) -> int:
        """
        Add a new background to the database.

        Args:
            name: Background name (unique identifier)
            file_path: Path to background file
            display_name: Human-readable display name
            description: Background description
            file_size: Size of the file in bytes
            is_default: Whether this is a default background (cannot be deleted)
            is_deletable: Whether this background can be deleted

        Returns:
            ID of the newly created background
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Calculate file hash and size if file exists
                file_hash = None
                if Path(file_path).exists():
                    from src.utils.file_hash import calculate_file_hash

                    file_hash = calculate_file_hash(file_path)
                    if file_size is None:
                        file_size = Path(file_path).stat().st_size

                cursor.execute(
                    """
                    INSERT INTO backgrounds (
                        name, display_name, description, file_path, file_hash,
                        file_size, is_default, is_deletable
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        name,
                        display_name or name,
                        description,
                        file_path,
                        file_hash,
                        file_size,
                        is_default,
                        is_deletable,
                    ),
                )

                background_id = cursor.lastrowid
                conn.commit()
                self.logger.info(
                    "Added background '%s' with ID %s", name, background_id
                )
                return background_id

        except sqlite3.IntegrityError:
            self.logger.error("Background with name '%s' already exists", name)
            raise
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to add background '%s': %s", name, e)
            raise

    @log_function_call(logger)
    def get_background(self, background_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a background by ID.

        Args:
            background_id: Background ID

        Returns:
            Background dictionary or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM backgrounds WHERE id = ?",
                    (background_id,),
                )
                row = cursor.fetchone()
                return dict(row) if row else None

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to get background %s: %s", background_id, e)
            return None

    @log_function_call(logger)
    def get_background_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a background by name.

        Args:
            name: Background name

        Returns:
            Background dictionary or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM backgrounds WHERE name = ?",
                    (name,),
                )
                row = cursor.fetchone()
                return dict(row) if row else None

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to get background by name '%s': %s", name, e)
            return None

    @log_function_call(logger)
    def get_all_backgrounds(
        self, include_deletable: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all backgrounds from the database.

        Args:
            include_deletable: Whether to include deletable backgrounds

        Returns:
            List of background dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if include_deletable:
                    cursor.execute(
                        "SELECT * FROM backgrounds ORDER BY is_default DESC, name ASC"
                    )
                else:
                    cursor.execute(
                        "SELECT * FROM backgrounds WHERE is_default = 1 ORDER BY name ASC"
                    )

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to get all backgrounds: %s", e)
            return []

    @log_function_call(logger)
    def get_default_backgrounds(self) -> List[Dict[str, Any]]:
        """
        Get all default backgrounds (cannot be deleted).

        Returns:
            List of default background dictionaries
        """
        return self.get_all_backgrounds(include_deletable=False)

    @log_function_call(logger)
    def update_background(
        self,
        background_id: int,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> bool:
        """
        Update background information.

        Args:
            background_id: Background ID
            display_name: New display name
            description: New description

        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Build update query dynamically
                updates = []
                params = []

                if display_name is not None:
                    updates.append("display_name = ?")
                    params.append(display_name)

                if description is not None:
                    updates.append("description = ?")
                    params.append(description)

                if not updates:
                    return False

                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(background_id)

                query = f"UPDATE backgrounds SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, params)

                success = cursor.rowcount > 0
                conn.commit()

                if success:
                    self.logger.info("Updated background %s", background_id)
                else:
                    self.logger.warning(
                        "Background %s not found for update", background_id
                    )

                return success

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to update background %s: %s", background_id, e)
            return False

    @log_function_call(logger)
    def delete_background(self, background_id: int) -> bool:
        """
        Delete a background from the database.

        Args:
            background_id: Background ID

        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Check if background is deletable
                cursor.execute(
                    "SELECT is_default FROM backgrounds WHERE id = ?", (background_id,)
                )
                row = cursor.fetchone()

                if not row:
                    self.logger.warning(
                        "Background %s not found for deletion", background_id
                    )
                    return False

                if row[0]:  # is_default is True
                    self.logger.error(
                        "Cannot delete default background %s", background_id
                    )
                    return False

                # Delete the background
                cursor.execute("DELETE FROM backgrounds WHERE id = ?", (background_id,))

                success = cursor.rowcount > 0
                conn.commit()

                if success:
                    self.logger.info("Deleted background %s", background_id)
                else:
                    self.logger.warning(
                        "Background %s not found for deletion", background_id
                    )

                return success

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to delete background %s: %s", background_id, e)
            return False

    @log_function_call(logger)
    def initialize_default_backgrounds(self) -> None:
        """
        Initialize the database with default backgrounds from the filesystem.

        This method scans the backgrounds directory and adds all found backgrounds to the database
        as default, non-deletable resources.
        """
        try:
            backgrounds_dir = (
                Path(__file__).parent.parent.parent / "resources" / "backgrounds"
            )

            if not backgrounds_dir.exists():
                self.logger.warning(
                    "Backgrounds directory not found: %s", backgrounds_dir
                )
                return

            # Find all image files
            image_extensions = {".png", ".jpg", ".jpeg", ".bmp"}
            background_files = [
                f
                for f in backgrounds_dir.iterdir()
                if f.is_file() and f.suffix.lower() in image_extensions
            ]

            added_count = 0

            for background_file in background_files:
                background_name = background_file.stem

                # Check if background already exists
                if self.get_background_by_name(background_name):
                    continue

                # Get file size
                file_size = background_file.stat().st_size

                # Add background to database
                self.add_background(
                    name=background_name,
                    file_path=str(background_file),
                    display_name=background_name.title(),
                    description=f"Default {background_name} background",
                    file_size=file_size,
                    is_default=True,
                    is_deletable=False,
                )
                added_count += 1

            self.logger.info(
                "Initialized %s default backgrounds from filesystem", added_count
            )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to initialize default backgrounds: %s", e)
            raise
