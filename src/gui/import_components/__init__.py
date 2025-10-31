"""
Import UI components for 3D model import process.

This package provides user interface components for importing 3D models with:
- File/directory selection with drag-and-drop support
- File management preference selection (keep organized vs leave in place)
- Multi-stage progress tracking (hashing, copying, thumbnails, analysis)
- Real-time progress updates with cancellation support
- Import results summary with statistics
"""

from src.gui.import_components.import_dialog import ImportDialog

__all__ = ['ImportDialog']