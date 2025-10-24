"""
Metadata editor widget for Digital Workshop (Facade).

This module provides backward-compatible access to the refactored metadata editor.
All functionality has been moved to src/gui/metadata_components/ package.

Run standalone for testing:
    python -m src.gui.metadata_editor
"""

from src.gui.metadata_components import (
    MetadataEditorWidget,
    StarRatingWidget,
)

__all__ = [
    "MetadataEditorWidget",
    "StarRatingWidget",
]
