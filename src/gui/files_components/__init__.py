"""
Files Components - Modular file management system.

This package provides file browser and management functionality for the application.

Public API:
- FilesTab: Main file browser tab widget
- FileMaintenanceWorker: Background file maintenance thread
"""

from .files_tab_widget import FilesTab
from .file_maintenance_worker import FileMaintenanceWorker

__all__ = [
    "FilesTab",
    "FileMaintenanceWorker",
]

