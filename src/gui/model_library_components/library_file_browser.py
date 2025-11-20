"""
Compatibility wrapper for the library file browser.

The implementation lives in ``src.gui.model_library.library_file_browser``; this
module re-exports the class to eliminate duplicated code paths.
"""

from src.gui.model_library.library_file_browser import LibraryFileBrowser

__all__ = ["LibraryFileBrowser"]
