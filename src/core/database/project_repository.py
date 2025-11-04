"""
Project Repository for managing project CRUD operations and duplicate detection.

Handles project creation, retrieval, updates, and case-insensitive duplicate detection.
"""

import sqlite3
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


class ProjectRepository:
    """Repository for project management operations."""

    def __init__(self, get_connection_func):
        """
        Initialize project repository.

        Args:
            get_connection_func: Callable that returns a database connection
        """
        self.get_connection = get_connection_func

    @log_function_call(logger)
    def create_project(
        self,
        name: str,
        base_path: Optional[str] = None,
        import_tag: Optional[str] = None,
        original_path: Optional[str] = None,
        structure_type: Optional[str] = None,
    ) -> str:
        """
        Create a new project.

        Args:
            name: Project name (must be unique, case-insensitive)
            base_path: Base directory path for the project
            import_tag: Tag for imported projects (e.g., "imported_project")
            original_path: Original import path
            structure_type: Structure type ("flat", "nested", "balanced")

        Returns:
            Project ID (UUID)

        Raises:
            ValueError: If project name already exists (case-insensitive)
            sqlite3.Error: If database operation fails
        """
        try:
            # Check for duplicate (case-insensitive)
            if self.get_project_by_name(name):
                raise ValueError(f"Project '{name}' already exists")

            project_id = str(uuid.uuid4())
            now = datetime.now().isoformat()

            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO projects (
                        id, name, base_path, import_tag, original_path,
                        structure_type, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        project_id,
                        name,
                        base_path,
                        import_tag,
                        original_path,
                        structure_type,
                        now,
                        now,
                    ),
                )
                conn.commit()

            logger.info(f"Project created: {name} (ID: {project_id})")
            return project_id

        except ValueError as e:
            logger.warning(f"Failed to create project: {str(e)}")
            raise
        except sqlite3.Error as e:
            logger.error(f"Database error creating project: {str(e)}")
            raise

    @log_function_call(logger)
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get project by ID.

        Args:
            project_id: Project UUID

        Returns:
            Project data or None if not found
        """
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
                row = cursor.fetchone()
                return dict(row) if row else None

        except sqlite3.Error as e:
            logger.error(f"Database error retrieving project: {str(e)}")
            return None

    @log_function_call(logger)
    def get_project_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get project by name (case-insensitive).

        Args:
            name: Project name

        Returns:
            Project data or None if not found
        """
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM projects WHERE LOWER(name) = LOWER(?)", (name,))
                row = cursor.fetchone()
                return dict(row) if row else None

        except sqlite3.Error as e:
            logger.error(f"Database error retrieving project by name: {str(e)}")
            return None

    @log_function_call(logger)
    def list_projects(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List all projects.

        Args:
            limit: Maximum number of projects to return
            offset: Number of projects to skip

        Returns:
            List of project data
        """
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if limit:
                    cursor.execute(
                        "SELECT * FROM projects ORDER BY created_at DESC LIMIT ? OFFSET ?",
                        (limit, offset),
                    )
                else:
                    cursor.execute("SELECT * FROM projects ORDER BY created_at DESC")

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Database error listing projects: {str(e)}")
            return []

    @log_function_call(logger)
    def list_imported_projects(self) -> List[Dict[str, Any]]:
        """
        List all imported projects (tagged with "imported_project").

        Returns:
            List of imported project data
        """
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM projects WHERE import_tag = 'imported_project' ORDER BY import_date DESC"
                )
                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Database error listing imported projects: {str(e)}")
            return []

    @log_function_call(logger)
    def update_project(self, project_id: str, **kwargs) -> bool:
        """
        Update project fields.

        Args:
            project_id: Project UUID
            **kwargs: Fields to update (name, base_path, import_tag, etc.)

        Returns:
            True if successful, False otherwise
        """
        try:
            allowed_fields = {
                "name",
                "base_path",
                "import_tag",
                "original_path",
                "structure_type",
                "import_date",
            }

            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            if not update_fields:
                return False

            update_fields["updated_at"] = datetime.now().isoformat()

            set_clause = ", ".join([f"{k} = ?" for k in update_fields.keys()])
            values = list(update_fields.values()) + [project_id]

            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"UPDATE projects SET {set_clause} WHERE id = ?", values)
                conn.commit()

            logger.info(f"Project updated: {project_id}")
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error(f"Database error updating project: {str(e)}")
            return False

    @log_function_call(logger)
    def delete_project(self, project_id: str) -> bool:
        """
        Delete project and associated files.

        Args:
            project_id: Project UUID

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Delete associated files first (cascade handled by FK)
                cursor.execute("DELETE FROM files WHERE project_id = ?", (project_id,))

                # Delete project
                cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
                conn.commit()

            logger.info(f"Project deleted: {project_id}")
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error(f"Database error deleting project: {str(e)}")
            return False

    @log_function_call(logger)
    def get_project_count(self) -> int:
        """
        Get total number of projects.

        Returns:
            Number of projects
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM projects")
                result = cursor.fetchone()
                return result[0] if result else 0

        except sqlite3.Error as e:
            logger.error(f"Database error counting projects: {str(e)}")
            return 0
