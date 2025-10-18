"""
SQLite database manager for 3D-MM application - Compatibility Layer.

REFACTORED: This module now acts as a compatibility layer.
The actual implementation has been split into modular components in src/core/database/

This module provides database operations for managing 3D models, metadata,
and categories with proper error handling and logging integration.
"""

import threading
from typing import Optional

from .logging_config import get_logger

# Import from refactored database module
from .database import DatabaseManager

# Initialize logger
logger = get_logger(__name__)

# Singleton instance for application-wide use
_database_manager: Optional[DatabaseManager] = None
_db_lock = threading.Lock()


def get_database_manager(db_path: str = "data/3dmm.db") -> DatabaseManager:
    """
    Get the singleton database manager instance.

    Args:
        db_path: Path to the SQLite database file

    Returns:
        DatabaseManager instance
    """
    global _database_manager

    with _db_lock:
        if _database_manager is None:
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
    'DatabaseManager',
    'get_database_manager',
    'close_database_manager',
]
