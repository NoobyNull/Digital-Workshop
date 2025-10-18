"""
Files tab widget for 3D-MM application (Facade).

This module provides backward-compatible access to the refactored files tab.
All functionality has been moved to src/gui/files_components/ package.

Run standalone for testing:
    python -m src.gui.files_tab
"""

from src.gui.files_components import (
    FilesTab,
    FileMaintenanceWorker,
)

__all__ = [
    "FilesTab",
    "FileMaintenanceWorker",
]
