"""
Path Utilities - Path manipulation and validation

Provides utilities for:
- Path validation
- Safe path operations
- Directory structure verification
- Path normalization
"""

import logging
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
        logger.debug("Validating path: %s", path)

        try:
            # Check if path is absolute
            if not path.is_absolute():
                logger.warning("Path is not absolute: %s", path)
                return False

            # Check for invalid characters
            invalid_chars = ["<", ">", ":", '"', "|", "?", "*"]
            path_str = str(path)

            for char in invalid_chars:
                if char in path_str:
                    logger.error(f"Path contains invalid character '{char}': {path}")
                    return False

            logger.debug("Path validated: %s", path)
            return True

        except Exception as e:
            logger.error("Failed to validate path: %s", e)
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
        logger.debug("Ensuring directory exists: %s", directory)

        try:
            if not PathUtils.validate_path(directory):
                logger.error("Invalid path: %s", directory)
                return False

            directory.mkdir(parents=True, exist_ok=True)
            logger.debug("Directory ensured: %s", directory)

            return True

        except Exception as e:
            logger.error("Failed to ensure directory: %s", e)
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
        logger.debug("Checking if directory is empty: %s", directory)

        try:
            if not directory.exists():
                logger.warning("Directory not found: %s", directory)
                return True

            is_empty = not any(directory.iterdir())
            logger.debug("Directory empty: %s = {is_empty}", directory)

            return is_empty

        except Exception as e:
            logger.error("Failed to check if directory is empty: %s", e)
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
        logger.debug("Calculating directory size: %s", directory)

        try:
            if not directory.exists():
                logger.warning("Directory not found: %s", directory)
                return 0

            total_size = 0

            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size

            logger.debug("Directory size: %s = {total_size} bytes", directory)
            return total_size

        except Exception as e:
            logger.error("Failed to calculate directory size: %s", e)
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
        for unit in ["B", "KB", "MB", "GB", "TB"]:
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
        logger.debug("Listing files: %s (pattern: {pattern})", directory)

        try:
            if not directory.exists():
                logger.warning("Directory not found: %s", directory)
                return []

            files = sorted(directory.glob(pattern))
            logger.debug("Found %s files", len(files))

            return files

        except Exception as e:
            logger.error("Failed to list files: %s", e)
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
        logger.debug("Getting relative path: %s relative to {base}", path)

        try:
            relative = path.relative_to(base)
            logger.debug("Relative path: %s", relative)

            return relative

        except ValueError:
            logger.warning("Path is not relative to base: %s vs {base}", path)
            return None
        except Exception as e:
            logger.error("Failed to get relative path: %s", e)
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
        logger.debug("Normalizing path: %s", path)

        try:
            normalized = path.resolve()
            logger.debug("Normalized path: %s", normalized)

            return normalized

        except Exception as e:
            logger.error("Failed to normalize path: %s", e)
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
        logger.debug("Checking if path is safe: %s within {base}", path)

        try:
            # Resolve both paths
            resolved_path = path.resolve()
            resolved_base = base.resolve()

            # Check if path is within base
            try:
                resolved_path.relative_to(resolved_base)
                logger.debug("Path is safe: %s", path)
                return True
            except ValueError:
                logger.error("Path escapes base directory: %s", path)
                return False

        except Exception as e:
            logger.error("Failed to check path safety: %s", e)
            return False
