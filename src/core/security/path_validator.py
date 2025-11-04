"""
Path validation utilities for secure file operations.

Prevents directory traversal attacks and validates file paths.
"""

import os
from pathlib import Path
from typing import Optional
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class PathValidator:
    """Validates file paths to prevent directory traversal attacks."""

    def __init__(self, base_directory: Optional[str] = None):
        """Initialize path validator with optional base directory.
        
        Args:
            base_directory: Base directory for path validation
        """
        self.base_directory = Path(base_directory) if base_directory else Path.cwd()
        self.base_directory = self.base_directory.resolve()

    def validate_path(self, file_path: str) -> bool:
        """Validate that a file path is safe and doesn't escape base directory.
        
        Args:
            file_path: Path to validate
            
        Returns:
            True if path is valid and safe, False otherwise
        """
        try:
            # Resolve the path to absolute form
            target_path = (self.base_directory / file_path).resolve()
            
            # Check if resolved path is within base directory
            target_path.relative_to(self.base_directory)
            
            logger.debug("Path validation passed: %s", file_path)
            return True
            
        except (ValueError, OSError) as e:
            logger.warning("Path validation failed for %s: %s", file_path, e)
            return False

    def get_safe_path(self, file_path: str) -> Optional[Path]:
        """Get a validated safe path.
        
        Args:
            file_path: Path to validate and return
            
        Returns:
            Resolved Path object if valid, None otherwise
        """
        if self.validate_path(file_path):
            return (self.base_directory / file_path).resolve()
        return None

    def is_file_allowed(self, file_path: str, allowed_extensions: Optional[list] = None) -> bool:
        """Check if file is allowed based on extension.
        
        Args:
            file_path: Path to check
            allowed_extensions: List of allowed file extensions (e.g., ['.stl', '.obj'])
            
        Returns:
            True if file is allowed, False otherwise
        """
        if not self.validate_path(file_path):
            return False
        
        if allowed_extensions is None:
            return True
        
        file_ext = Path(file_path).suffix.lower()
        is_allowed = file_ext in allowed_extensions
        
        if not is_allowed:
            logger.warning("File extension not allowed: %s", file_ext)
        
        return is_allowed

    @staticmethod
    def is_system_file(file_path: str) -> bool:
        """Check if file is a system file that should be blocked.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file is a system file, False otherwise
        """
        blocked_extensions = {
            '.exe', '.sys', '.ini', '.inf', '.com', '.bat', '.ps1',
            '.dll', '.msi', '.scr', '.vbs', '.js', '.cmd'
        }
        
        file_ext = Path(file_path).suffix.lower()
        return file_ext in blocked_extensions

