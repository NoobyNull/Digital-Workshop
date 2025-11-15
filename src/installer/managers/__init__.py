"""
Manager classes for Digital Workshop installer

Provides specialized managers for:
- Module management (installation, verification, removal)
- Backup management (creation, restoration, verification)
- Registry management (tracking installed modules and versions)
- Migration management (database schema updates)
"""

from .module_manager import ModuleManager
from .backup_manager import BackupManager
from .registry_manager import RegistryManager
from .migration_manager import MigrationManager

__all__ = [
    "ModuleManager",
    "BackupManager",
    "RegistryManager",
    "MigrationManager",
]
