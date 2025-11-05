"""
Model library package for Digital Workshop.

Provides a modular, component-based model library widget with:
- File browser with multi-root support
- List/Grid views
- Drag-and-drop import
- Background loading
- Database integration
- Search and filtering
- Context menus
- Metadata editing
- Thumbnail generation

Main entry point: ModelLibraryWidget
"""

from .widget import ModelLibraryWidget
from .file_system_proxy import FileSystemProxyModel
from .model_load_worker import ModelLoadWorker
from .thumbnail_generator import ThumbnailGenerator
from .library_ui_manager import LibraryUIManager
from .library_model_manager import LibraryModelManager
from .library_file_browser import LibraryFileBrowser
from .library_event_handler import LibraryEventHandler, ViewMode
from .model_library_facade import ModelLibraryFacade

__all__ = [
    # Main widget (primary export)
    "ModelLibraryWidget",
    # Components (for advanced usage)
    "FileSystemProxyModel",
    "ModelLoadWorker",
    "ThumbnailGenerator",
    "LibraryUIManager",
    "LibraryModelManager",
    "LibraryFileBrowser",
    "LibraryEventHandler",
    "ViewMode",
    "ModelLibraryFacade",
]
