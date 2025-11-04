"""
Search worker threads for background operations.

Provides worker threads for search and suggestion operations
without blocking the UI.
"""

from typing import Any, Dict, Optional

from PySide6.QtCore import QThread, Signal

from src.core.search_engine import get_search_engine
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class SearchWorker(QThread):
    """
    Worker thread for performing search operations without blocking the UI.
    """

    search_completed = Signal(dict)
    search_failed = Signal(str)

    def __init__(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ):
        """
        Initialize the search worker.

        Args:
            query: Search query string
            filters: Dictionary of filters
            limit: Maximum number of results
            offset: Number of results to skip
        """
        super().__init__()
        self.query = query
        self.filters = filters or {}
        self.limit = limit
        self.offset = offset
        self.search_engine = get_search_engine()

    def run(self):
        """
        Execute the search operation.
        """
        try:
            results = self.search_engine.search(
                self.query, self.filters, self.limit, self.offset
            )
            self.search_completed.emit(results)
        except Exception as e:
            error_msg = f"Search failed: {str(e)}"
            logger.error(error_msg)
            self.search_failed.emit(error_msg)


class SearchSuggestionWorker(QThread):
    """
    Worker thread for getting search suggestions.
    """

    suggestions_ready = Signal(list)

    def __init__(self, query: str, limit: int = 10):
        """
        Initialize the suggestion worker.

        Args:
            query: Partial search query
            limit: Maximum number of suggestions
        """
        super().__init__()
        self.query = query
        self.limit = limit
        self.search_engine = get_search_engine()

    def run(self):
        """
        Get search suggestions.
        """
        try:
            suggestions = self.search_engine.get_search_suggestions(
                self.query, self.limit
            )
            self.suggestions_ready.emit(suggestions)
        except Exception as e:
            logger.error(f"Failed to get suggestions: {str(e)}")
            self.suggestions_ready.emit([])
