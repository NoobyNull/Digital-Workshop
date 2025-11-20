"""
Compatibility wrapper for the library model manager.

The implementation lives in ``src.gui.model_library.library_model_manager``; this
module simply re-exports the class to avoid maintaining duplicated code.
"""

from src.gui.model_library.library_model_manager import LibraryModelManager

__all__ = ["LibraryModelManager"]
