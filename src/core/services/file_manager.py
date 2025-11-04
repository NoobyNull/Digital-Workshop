"""
File Manager for managing file operations including linking, copying, and status tracking.

Handles file operations with fallback logic and status tracking.
"""

import os
import shutil
from typing import Optional, List, Dict, Any
from enum import Enum

from ..database.database_manager import DatabaseManager
from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


class LinkType(Enum):
    """File linking types."""

    HARD = "hard"
    SYMBOLIC = "symbolic"
    COPY = "copy"
    ORIGINAL = "original"


class FileStatus(Enum):
    """File status values."""

    PENDING = "pending"
    IMPORTING = "importing"
    IMPORTED = "imported"
    FAILED = "failed"
    LINKED = "linked"
    COPIED = "copied"


class FileManager:
    """Manages file operations and tracking."""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize file manager.

        Args:
            db_manager: DatabaseManager instance
        """
        self.logger = logger
        self.db_manager = db_manager

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
        Add file to project.

        Args:
            project_id: Project ID
            file_path: File path
            file_name: File name
            file_size: File size in bytes
            file_hash: File hash
            status: File status
            link_type: Link type
            original_path: Original path

        Returns:
            File ID
        """
        try:
            return self.db_manager.add_file(
                project_id=project_id,
                file_path=file_path,
                file_name=file_name,
                file_size=file_size,
                file_hash=file_hash,
                status=status,
                link_type=link_type,
                original_path=original_path,
            )

        except Exception as e:
            logger.error(f"Failed to add file: {str(e)}")
            raise

    @log_function_call(logger)
    def get_file(self, file_id: int) -> Optional[Dict[str, Any]]:
        """Get file by ID."""
        try:
            return self.db_manager.get_file(file_id)
        except Exception as e:
            logger.error(f"Failed to get file: {str(e)}")
            return None

    @log_function_call(logger)
    def get_files_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all files in project."""
        try:
            return self.db_manager.get_files_by_project(project_id)
        except Exception as e:
            logger.error(f"Failed to get files: {str(e)}")
            return []

    @log_function_call(logger)
    def get_files_by_status(self, project_id: str, status: str) -> List[Dict[str, Any]]:
        """Get files by status."""
        try:
            return self.db_manager.get_files_by_status(project_id, status)
        except Exception as e:
            logger.error(f"Failed to get files by status: {str(e)}")
            return []

    @log_function_call(logger)
    def update_file_status(self, file_id: int, status: str) -> bool:
        """Update file status."""
        try:
            return self.db_manager.update_file_status(file_id, status)
        except Exception as e:
            logger.error(f"Failed to update file status: {str(e)}")
            return False

    @log_function_call(logger)
    def update_file(self, file_id: int, **kwargs) -> bool:
        """Update file."""
        try:
            return self.db_manager.update_file(file_id, **kwargs)
        except Exception as e:
            logger.error(f"Failed to update file: {str(e)}")
            return False

    @log_function_call(logger)
    def delete_file(self, file_id: int) -> bool:
        """Delete file record."""
        try:
            return self.db_manager.delete_file(file_id)
        except Exception as e:
            logger.error(f"Failed to delete file: {str(e)}")
            return False

    @log_function_call(logger)
    def link_file(
        self, source_path: str, dest_path: str, link_type: str = "hard"
    ) -> bool:
        """
        Link file with fallback logic.

        Args:
            source_path: Source file path
            dest_path: Destination file path
            link_type: Type of link (hard, symbolic, copy)

        Returns:
            True if successful
        """
        try:
            dest_dir = os.path.dirname(dest_path)
            os.makedirs(dest_dir, exist_ok=True)

            if link_type == "hard":
                try:
                    os.link(source_path, dest_path)
                    logger.info(f"Hard linked: {source_path} -> {dest_path}")
                    return True
                except Exception as e:
                    logger.warning(f"Hard link failed: {str(e)}, trying symbolic link")
                    link_type = "symbolic"

            if link_type == "symbolic":
                try:
                    os.symlink(source_path, dest_path)
                    logger.info(f"Symbolic linked: {source_path} -> {dest_path}")
                    return True
                except Exception as e:
                    logger.warning(f"Symbolic link failed: {str(e)}, trying copy")
                    link_type = "copy"

            if link_type == "copy":
                try:
                    shutil.copy2(source_path, dest_path)
                    logger.info(f"Copied: {source_path} -> {dest_path}")
                    return True
                except Exception as e:
                    logger.error(f"Copy failed: {str(e)}")
                    return False

        except Exception as e:
            logger.error(f"Failed to link file: {str(e)}")
            return False

    @log_function_call(logger)
    def find_duplicate(
        self, project_id: str, file_hash: str
    ) -> Optional[Dict[str, Any]]:
        """Find duplicate file by hash."""
        try:
            return self.db_manager.find_duplicate_by_hash(project_id, file_hash)
        except Exception as e:
            logger.error(f"Failed to find duplicate: {str(e)}")
            return None

    @log_function_call(logger)
    def get_file_count(self, project_id: str) -> int:
        """Get file count for project."""
        try:
            return self.db_manager.get_file_count_by_project(project_id)
        except Exception as e:
            logger.error(f"Failed to get file count: {str(e)}")
            return 0
