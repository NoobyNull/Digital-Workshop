"""
Thumbnail generator for 3D model files (Facade).

This module provides backward-compatible access to the refactored thumbnail generator.
All functionality has been moved to src/core/thumbnail_components/ package.

Run standalone for testing:
    python -m src.core.thumbnail_generator
"""

from src.core.thumbnail_components import ThumbnailGenerator

__all__ = [
    "ThumbnailGenerator",
]
