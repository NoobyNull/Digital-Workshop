"""
SQLite database manager for Digital Workshop - Compatibility Layer.

REFACTORED: This module now acts as a compatibility layer.
The actual implementation has been split into modular components in src/core/database/

This module provides database operations for managing 3D models, metadata,
and categories with proper error handling and logging integration.
"""

import os
import threading
from pathlib import Path
from typing import Optional

from .logging_config import get_logger

# Import from refactored database module
from .database import DatabaseManager

# Initialize logger
logger = get_logger(__name__)

# Singleton instance for application-wide use
_database_manager: Optional[DatabaseManager] = None
_db_lock = threading.Lock()


def _get_default_db_path() -> str:
    """
    Get the default database path using AppData location.

    This ensures the database is always in the same location regardless
    of the current working directory.

    In memory-only mode (--mem-only), paths are automatically redirected to temp
    by the path manager, so no special handling is needed here.

    Returns:
        Absolute path to the database file
    """
    try:
        from .path_manager import get_data_directory

        data_dir = get_data_directory()
        return str(data_dir / "3dmm.db")
    except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
        logger.warning(
            "Failed to get data directory: %s, falling back to user data path", e
        )
        # Fallback to user-specific directory
        app_data = Path(
            os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
        )
        from .version_manager import get_app_name

        app_name = get_app_name()
        db_dir = app_data / app_name / "data"
        db_dir.mkdir(parents=True, exist_ok=True)
        return str(db_dir / "3dmm.db")


def get_database_manager(db_path: Optional[str] = None) -> DatabaseManager:
    """
    Get the singleton database manager instance.

    Args:
        db_path: Path to the SQLite database file. If None, uses AppData location.

    Returns:
        DatabaseManager instance
    """
    global _database_manager

    with _db_lock:
        if _database_manager is None:
            # Use AppData path if no path provided
            if db_path is None:
                db_path = _get_default_db_path()
            _database_manager = DatabaseManager(db_path)

        return _database_manager


def close_database_manager() -> None:
    """
    Close the database manager instance.
    """
    global _database_manager

    with _db_lock:
        if _database_manager:
            _database_manager.close()
            _database_manager = None


__all__ = [
    "DatabaseManager",
    "get_database_manager",
    "close_database_manager",
]
