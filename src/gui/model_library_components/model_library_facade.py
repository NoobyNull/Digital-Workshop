"""
Compatibility wrapper for the model library facade.

Delegates to ``src.gui.model_library.model_library_facade`` to keep a single
implementation.
"""

from src.gui.model_library.model_library_facade import ModelLibraryFacade

__all__ = ["ModelLibraryFacade"]
