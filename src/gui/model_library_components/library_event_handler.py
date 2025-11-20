"""
Compatibility wrapper for the library event handler.

The primary implementation resides in ``src.gui.model_library.library_event_handler``.
This module re-exports it to remove duplicated code.
"""

from src.gui.model_library.library_event_handler import LibraryEventHandler

__all__ = ["LibraryEventHandler"]
