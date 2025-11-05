"""
Path Utilities - Path manipulation and validation

Provides utilities for:
- Path validation
- Safe path operations
- Directory structure verification
- Path normalization
"""

import logging
import os
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)


class PathUtils:
    """Utilities for path manipulation and validation."""
    
    @staticmethod
    def validate_path(path: Path) -> bool:
        """
        Validate that a path is safe and accessible.
        
        Args:
            path: Path to validate
            
        Returns:
            True if path is valid, False otherwise
        """
        logger.debug(f"Validating path: {path}")
        
        try:
            # Check if path is absolute
            if not path.is_absolute():
                logger.warning(f"Path is not absolute: {path}")
                return False
            
            # Check for invalid characters
            invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
            path_str = str(path)
            
            for char in invalid_chars:
                if char in path_str:
                    logger.error(f"Path contains invalid character '{char}': {path}")
                    return False
            
            logger.debug(f"Path validated: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate path: {e}")
            return False
    
    @staticmethod
    def ensure_directory(directory: Path) -> bool:
        """
        Ensure directory exists, creating it if necessary.
        
        Args:
            directory: Path to directory
            
        Returns:
            True if successful, False otherwise
        """
        logger.debug(f"Ensuring directory exists: {directory}")
        
        try:
            if not PathUtils.validate_path(directory):
                logger.error(f"Invalid path: {directory}")
                return False
            
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory ensured: {directory}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to ensure directory: {e}")
            return False
    
    @staticmethod
    def is_directory_empty(directory: Path) -> bool:
        """
        Check if directory is empty.
        
        Args:
            directory: Path to directory
            
        Returns:
            True if empty, False otherwise
        """
        logger.debug(f"Checking if directory is empty: {directory}")
        
        try:
            if not directory.exists():
                logger.warning(f"Directory not found: {directory}")
                return True
            
            is_empty = not any(directory.iterdir())
            logger.debug(f"Directory empty: {directory} = {is_empty}")
            
            return is_empty
            
        except Exception as e:
            logger.error(f"Failed to check if directory is empty: {e}")
            return False
    
    @staticmethod
    def get_directory_size(directory: Path) -> int:
        """
        Get total size of directory in bytes.
        
        Args:
            directory: Path to directory
            
        Returns:
            Total size in bytes
        """
        logger.debug(f"Calculating directory size: {directory}")
        
        try:
            if not directory.exists():
                logger.warning(f"Directory not found: {directory}")
                return 0
            
            total_size = 0
            
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            
            logger.debug(f"Directory size: {directory} = {total_size} bytes")
            return total_size
            
        except Exception as e:
            logger.error(f"Failed to calculate directory size: {e}")
            return 0
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """
        Format bytes to human-readable size.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        
        return f"{size_bytes:.2f} PB"
    
    @staticmethod
    def list_files(directory: Path, pattern: str = "*") -> List[Path]:
        """
        List files in directory matching pattern.
        
        Args:
            directory: Path to directory
            pattern: File pattern (e.g., "*.py")
            
        Returns:
            List of matching file paths
        """
        logger.debug(f"Listing files: {directory} (pattern: {pattern})")
        
        try:
            if not directory.exists():
                logger.warning(f"Directory not found: {directory}")
                return []
            
            files = sorted(directory.glob(pattern))
            logger.debug(f"Found {len(files)} files")
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []
    
    @staticmethod
    def get_relative_path(path: Path, base: Path) -> Optional[Path]:
        """
        Get relative path from base.
        
        Args:
            path: Path to get relative path for
            base: Base path
            
        Returns:
            Relative path or None if not relative to base
        """
        logger.debug(f"Getting relative path: {path} relative to {base}")
        
        try:
            relative = path.relative_to(base)
            logger.debug(f"Relative path: {relative}")
            
            return relative
            
        except ValueError:
            logger.warning(f"Path is not relative to base: {path} vs {base}")
            return None
        except Exception as e:
            logger.error(f"Failed to get relative path: {e}")
            return None
    
    @staticmethod
    def normalize_path(path: Path) -> Path:
        """
        Normalize path (resolve symlinks, remove redundant separators).
        
        Args:
            path: Path to normalize
            
        Returns:
            Normalized path
        """
        logger.debug(f"Normalizing path: {path}")
        
        try:
            normalized = path.resolve()
            logger.debug(f"Normalized path: {normalized}")
            
            return normalized
            
        except Exception as e:
            logger.error(f"Failed to normalize path: {e}")
            return path
    
    @staticmethod
    def is_path_safe(path: Path, base: Path) -> bool:
        """
        Check if path is safe (doesn't escape base directory).
        
        Args:
            path: Path to check
            base: Base directory
            
        Returns:
            True if path is safe, False otherwise
        """
        logger.debug(f"Checking if path is safe: {path} within {base}")
        
        try:
            # Resolve both paths
            resolved_path = path.resolve()
            resolved_base = base.resolve()
            
            # Check if path is within base
            try:
                resolved_path.relative_to(resolved_base)
                logger.debug(f"Path is safe: {path}")
                return True
            except ValueError:
                logger.error(f"Path escapes base directory: {path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to check path safety: {e}")
            return False

