"""
Database module - modular database operations for Digital Workshop.

Provides DatabaseManager facade with specialized repositories for models, metadata,
and maintenance operations.
"""

from .database_manager import DatabaseManager
from .db_operations import DatabaseOperations
from .model_repository import ModelRepository
from .metadata_repository import MetadataRepository
from .db_maintenance import DatabaseMaintenance

__all__ = [
    'DatabaseManager',
    'DatabaseOperations',
    'ModelRepository',
    'MetadataRepository',
    'DatabaseMaintenance',
]
