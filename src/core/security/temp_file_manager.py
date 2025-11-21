"""
Secure temporary file management.

Ensures temporary files are properly cleaned up and securely handled.
"""

import tempfile
import os
from typing import Optional, Generator
from contextlib import contextmanager
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class TempFileManager:
    """Manages temporary files with secure cleanup."""

    def __init__(self, base_temp_dir: Optional[str] = None) -> None:
        """Initialize temp file manager.

        Args:
            base_temp_dir: Base directory for temporary files
        """
        self.base_temp_dir = base_temp_dir or tempfile.gettempdir()
        self.temp_files = []

    @contextmanager
    def temporary_file(
        self, suffix: str = "", prefix: str = "dw_"
    ) -> Generator[str, None, None]:
        """Context manager for temporary file creation.

        Ensures file is cleaned up even if an error occurs.

        Args:
            suffix: File suffix
            prefix: File prefix

        Yields:
            Path to temporary file
        """
        temp_file = None
        try:
            # Create temporary file
            fd, temp_file = tempfile.mkstemp(
                suffix=suffix, prefix=prefix, dir=self.base_temp_dir
            )
            os.close(fd)

            self.temp_files.append(temp_file)
            logger.debug("Created temporary file: %s", temp_file)

            yield temp_file

        except (OSError, IOError) as e:
            logger.error("Error creating temporary file: %s", e)
            raise
        finally:
            # Ensure cleanup
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                    self.temp_files.remove(temp_file)
                    logger.debug("Cleaned up temporary file: %s", temp_file)
                except (OSError, IOError) as e:
                    logger.warning(
                        "Failed to clean up temporary file %s: %s", temp_file, e
                    )

    @contextmanager
    def temporary_directory(self, prefix: str = "dw_") -> Generator[str, None, None]:
        """Context manager for temporary directory creation.

        Ensures directory is cleaned up even if an error occurs.

        Args:
            prefix: Directory prefix

        Yields:
            Path to temporary directory
        """
        temp_dir = None
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(prefix=prefix, dir=self.base_temp_dir)
            logger.debug("Created temporary directory: %s", temp_dir)

            yield temp_dir

        except (OSError, IOError) as e:
            logger.error("Error creating temporary directory: %s", e)
            raise
        finally:
            # Ensure cleanup
            if temp_dir and os.path.exists(temp_dir):
                try:
                    import shutil

                    shutil.rmtree(temp_dir)
                    logger.debug("Cleaned up temporary directory: %s", temp_dir)
                except (OSError, IOError) as e:
                    logger.warning(
                        "Failed to clean up temporary directory %s: %s", temp_dir, e
                    )

    def cleanup_all(self) -> None:
        """Clean up all tracked temporary files."""
        for temp_file in self.temp_files[:]:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    self.temp_files.remove(temp_file)
                    logger.debug("Cleaned up temporary file: %s", temp_file)
            except (OSError, IOError) as e:
                logger.warning("Failed to clean up temporary file %s: %s", temp_file, e)

    def __del__(self) -> None:
        """Ensure cleanup on object destruction."""
        self.cleanup_all()
