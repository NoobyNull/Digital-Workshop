"""
Search widget for 3D-MM application (Facade).

This module provides backward-compatible access to the refactored search widget.
All functionality has been moved to src/gui/search_components/ package.

Run standalone for testing:
    python -m src.gui.search_widget
"""

from src.gui.search_components import (
    SearchWidget,
    AdvancedSearchWidget,
    SavedSearchDialog,
    SearchWorker,
    SearchSuggestionWorker,
)

__all__ = [
    "SearchWidget",
    "AdvancedSearchWidget",
    "SavedSearchDialog",
    "SearchWorker",
    "SearchSuggestionWorker",
]
