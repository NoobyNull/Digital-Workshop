"""
Metadata Components - Modular metadata editing system.

This package provides a comprehensive metadata editing interface with form fields,
star rating system, category management, and database integration for managing
3D model metadata.

Public API:
- MetadataEditorWidget: Main metadata editor widget
- StarRatingWidget: Interactive star rating component
"""

from .star_rating_widget import StarRatingWidget
from .metadata_editor_main import MetadataEditorWidget

__all__ = [
    "MetadataEditorWidget",
    "StarRatingWidget",
]

