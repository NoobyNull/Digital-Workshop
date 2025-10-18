"""
Search Components - Modular search widget system.

This package provides a comprehensive search interface with advanced filtering,
search history, and saved searches functionality.

Public API:
- SearchWidget: Main search widget
- AdvancedSearchWidget: Advanced filter widget
- SavedSearchDialog: Save search dialog
- SearchWorker: Background search thread
- SearchSuggestionWorker: Background suggestion thread
"""

from .search_workers import SearchWorker, SearchSuggestionWorker
from .saved_search_dialog import SavedSearchDialog
from .advanced_search_widget import AdvancedSearchWidget
from .search_widget_main import SearchWidget

__all__ = [
    "SearchWidget",
    "AdvancedSearchWidget",
    "SavedSearchDialog",
    "SearchWorker",
    "SearchSuggestionWorker",
]

