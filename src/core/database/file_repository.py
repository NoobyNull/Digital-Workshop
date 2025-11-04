"""
File Repository for managing file tracking and status updates.

Handles file CRUD operations, status tracking, and project association.
"""

import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


class FileRepository:
    """Repository for file management operations."""

    def __init__(self, get_connection_func):
        """
        Initialize file repository.

        Args:
            get_connection_func: Callable that returns a database connection
        """
        self.get_connection = get_connection_func

    @log_function_call(logger)
    def add_file(
        self,
        project_id: str,
        file_path: str,
        file_name: str,
        file_size: Optional[int] = None,
        file_hash: Optional[str] = None,
        status: str = "pending",
        link_type: Optional[str] = None,
        original_path: Optional[str] = None,
    ) -> int:
        """
        Add a file to a project.

        Args:
            project_id: Project UUID
            file_path: Full file path
            file_name: File name
            file_size: File size in bytes
            file_hash: File hash for duplicate detection
            status: File status (pending, importing, imported, failed, linked, copied)
            link_type: Link type (hard, symbolic, copy, original)
            original_path: Original path before linking/copying

        Returns:
            File ID

        Raises:
            sqlite3.Error: If database operation fails
        """
        try:
            now = datetime.now().isoformat()

            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO files (
                        project_id, file_path, file_name, file_size, file_hash,
                        status, link_type, original_path, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        project_id,
                        file_path,
                        file_name,
                        file_size,
                        file_hash,
                        status,
                        link_type,
                        original_path,
                        now,
                        now,
                    ),
                )
                conn.commit()

            logger.info("File added to project %s: {file_name}", project_id)
            return cursor.lastrowid

        except sqlite3.Error as e:
            logger.error("Database error adding file: %s", str(e))
            raise

    @log_function_call(logger)
    def get_file(self, file_id: int) -> Optional[Dict[str, Any]]:
        """
        Get file by ID.

        Args:
            file_id: File ID

        Returns:
            File data or None if not found
        """
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
                row = cursor.fetchone()
                return dict(row) if row else None

        except sqlite3.Error as e:
            logger.error("Database error retrieving file: %s", str(e))
            return None

    @log_function_call(logger)
    def get_files_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get all files in a project.

        Args:
            project_id: Project UUID

        Returns:
            List of file data
        """
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM files WHERE project_id = ? ORDER BY created_at DESC",
                    (project_id,),
                )
                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except sqlite3.Error as e:
            logger.error("Database error retrieving files: %s", str(e))
            return []

    @log_function_call(logger)
    def get_files_by_status(self, project_id: str, status: str) -> List[Dict[str, Any]]:
        """
        Get files by status in a project.

        Args:
            project_id: Project UUID
            status: File status

        Returns:
            List of file data
        """
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM files WHERE project_id = ? AND status = ? ORDER BY created_at DESC",
                    (project_id, status),
                )
                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except sqlite3.Error as e:
            logger.error("Database error retrieving files by status: %s", str(e))
            return []

    @log_function_call(logger)
    def update_file_status(self, file_id: int, status: str) -> bool:
        """
        Update file status.

        Args:
            file_id: File ID
            status: New status

        Returns:
            True if successful, False otherwise
        """
        try:
            now = datetime.now().isoformat()

            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE files SET status = ?, updated_at = ? WHERE id = ?",
                    (status, now, file_id),
                )
                conn.commit()

            logger.info("File status updated: %s -> {status}", file_id)
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error("Database error updating file status: %s", str(e))
            return False

    @log_function_call(logger)
    def update_file(self, file_id: int, **kwargs) -> bool:
        """
        Update file fields.

        Args:
            file_id: File ID
            **kwargs: Fields to update

        Returns:
            True if successful, False otherwise
        """
        try:
            allowed_fields = {
                "file_path",
                "file_name",
                "file_size",
                "file_hash",
                "status",
                "link_type",
                "original_path",
            }

            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            if not update_fields:
                return False

            update_fields["updated_at"] = datetime.now().isoformat()

            set_clause = ", ".join([f"{k} = ?" for k in update_fields.keys()])
            values = list(update_fields.values()) + [file_id]

            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"UPDATE files SET {set_clause} WHERE id = ?", values)
                conn.commit()

            logger.info("File updated: %s", file_id)
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error("Database error updating file: %s", str(e))
            return False

    @log_function_call(logger)
    def delete_file(self, file_id: int) -> bool:
        """
        Delete a file record.

        Args:
            file_id: File ID

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
                conn.commit()

            logger.info("File deleted: %s", file_id)
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error("Database error deleting file: %s", str(e))
            return False

    @log_function_call(logger)
    def get_file_count_by_project(self, project_id: str) -> int:
        """
        Get total number of files in a project.

        Args:
            project_id: Project UUID

        Returns:
            Number of files
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM files WHERE project_id = ?", (project_id,))
                result = cursor.fetchone()
                return result[0] if result else 0

        except sqlite3.Error as e:
            logger.error("Database error counting files: %s", str(e))
            return 0

    @log_function_call(logger)
    def find_duplicate_by_hash(self, project_id: str, file_hash: str) -> Optional[Dict[str, Any]]:
        """
        Find duplicate file by hash in a project.

        Args:
            project_id: Project UUID
            file_hash: File hash

        Returns:
            File data if found, None otherwise
        """
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM files WHERE project_id = ? AND file_hash = ? LIMIT 1",
                    (project_id, file_hash),
                )
                row = cursor.fetchone()
                return dict(row) if row else None

        except sqlite3.Error as e:
            logger.error("Database error finding duplicate: %s", str(e))
            return None
