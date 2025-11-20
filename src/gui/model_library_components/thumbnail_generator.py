"""
Compatibility wrapper for thumbnail generation.

Re-exports the thumbnail generator from ``src.gui.model_library.thumbnail_generator`` to
avoid maintaining duplicate implementations.
"""

from src.gui.model_library.thumbnail_generator import ThumbnailGenerator

__all__ = ["ThumbnailGenerator"]
