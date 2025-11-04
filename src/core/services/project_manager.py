"""
Project Manager for managing project creation, opening, and lifecycle.

Handles project operations including creation, opening, closing, and duplicate detection.
"""

from typing import Optional, List, Dict, Any

from ..database.database_manager import DatabaseManager
from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


class ProjectManager:
    """Manages project lifecycle and operations."""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize project manager.

        Args:
            db_manager: DatabaseManager instance
        """
        self.logger = logger
        self.db_manager = db_manager
        self.current_project: Optional[Dict[str, Any]] = None

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
            name: Project name
            base_path: Base directory path
            import_tag: Import tag (e.g., "imported_project")
            original_path: Original import path
            structure_type: Structure type (flat, nested, balanced)

        Returns:
            Project ID
        """
        try:
            project_id = self.db_manager.create_project(
                name=name,
                base_path=base_path,
                import_tag=import_tag,
                original_path=original_path,
                structure_type=structure_type,
            )
            logger.info(f"Created project: {name} ({project_id})")
            return project_id

        except ValueError as e:
            logger.error(f"Failed to create project: {str(e)}")
            raise

    @log_function_call(logger)
    def open_project(self, project_id: str) -> bool:
        """
        Open a project.

        Args:
            project_id: Project ID

        Returns:
            True if successful
        """
        try:
            project = self.db_manager.get_project(project_id)

            if not project:
                raise ValueError(f"Project not found: {project_id}")

            self.current_project = project
            logger.info(f"Opened project: {project['name']}")
            return True

        except Exception as e:
            logger.error(f"Failed to open project: {str(e)}")
            return False

    @log_function_call(logger)
    def close_project(self) -> bool:
        """Close current project."""
        try:
            if self.current_project:
                logger.info(f"Closed project: {self.current_project['name']}")
                self.current_project = None
            return True

        except Exception as e:
            logger.error(f"Failed to close project: {str(e)}")
            return False

    def get_current_project(self) -> Optional[Dict[str, Any]]:
        """Get current project."""
        return self.current_project

    @log_function_call(logger)
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID."""
        try:
            return self.db_manager.get_project(project_id)
        except Exception as e:
            logger.error(f"Failed to get project: {str(e)}")
            return None

    @log_function_call(logger)
    def get_project_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get project by name (case-insensitive)."""
        try:
            return self.db_manager.get_project_by_name(name)
        except Exception as e:
            logger.error(f"Failed to get project by name: {str(e)}")
            return None

    @log_function_call(logger)
    def list_projects(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List all projects."""
        try:
            return self.db_manager.list_projects(limit=limit, offset=offset)
        except Exception as e:
            logger.error(f"Failed to list projects: {str(e)}")
            return []

    @log_function_call(logger)
    def list_imported_projects(self) -> List[Dict[str, Any]]:
        """List imported projects."""
        try:
            return self.db_manager.list_imported_projects()
        except Exception as e:
            logger.error(f"Failed to list imported projects: {str(e)}")
            return []

    @log_function_call(logger)
    def update_project(self, project_id: str, **kwargs) -> bool:
        """Update project."""
        try:
            return self.db_manager.update_project(project_id, **kwargs)
        except Exception as e:
            logger.error(f"Failed to update project: {str(e)}")
            return False

    @log_function_call(logger)
    def delete_project(self, project_id: str) -> bool:
        """Delete project."""
        try:
            if self.current_project and self.current_project["id"] == project_id:
                self.close_project()

            return self.db_manager.delete_project(project_id)

        except Exception as e:
            logger.error(f"Failed to delete project: {str(e)}")
            return False

    @log_function_call(logger)
    def check_duplicate(self, name: str) -> bool:
        """Check if project name already exists (case-insensitive)."""
        try:
            project = self.db_manager.get_project_by_name(name)
            return project is not None
        except Exception as e:
            logger.error(f"Failed to check duplicate: {str(e)}")
            return False

    @log_function_call(logger)
    def get_project_count(self) -> int:
        """Get total number of projects."""
        try:
            return self.db_manager.get_project_count()
        except Exception as e:
            logger.error(f"Failed to get project count: {str(e)}")
            return 0

    @log_function_call(logger)
    def get_project_files(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all files in a project."""
        try:
            return self.db_manager.get_files_by_project(project_id)
        except Exception as e:
            logger.error(f"Failed to get project files: {str(e)}")
            return []

    @log_function_call(logger)
    def get_project_file_count(self, project_id: str) -> int:
        """Get number of files in a project."""
        try:
            return self.db_manager.get_file_count_by_project(project_id)
        except Exception as e:
            logger.error(f"Failed to get file count: {str(e)}")
            return 0
