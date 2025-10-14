"""
Core business logic for 3D-MM application.

This package contains the core functionality including model management,
database operations, search engine, and logging configuration.
"""

from .logging_config import setup_logging

# Try to import other modules, but don't fail if they don't exist yet
try:
    from .database_manager import DatabaseManager
    _database_manager_available = True
except ImportError:
    _database_manager_available = False
    DatabaseManager = None

try:
    from .search_engine import ModelSearchEngine
    _search_engine_available = True
except ImportError:
    _search_engine_available = False
    ModelSearchEngine = None

try:
    from .model_manager import ModelManager
    _model_manager_available = True
except ImportError:
    _model_manager_available = False
    ModelManager = None

# Build the __all__ list based on available modules
__all__ = ['setup_logging']
if _database_manager_available:
    __all__.append('DatabaseManager')
if _search_engine_available:
    __all__.append('ModelSearchEngine')
if _model_manager_available:
    __all__.append('ModelManager')