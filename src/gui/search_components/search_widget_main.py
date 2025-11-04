"""
Main search widget with search input, filters, and results display.

Provides the primary search interface with history and saved searches.
"""

from datetime import datetime
from typing import Any, Dict, List

from PySide6.QtCore import Signal, Qt, QTimer, QStringListModel
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QProgressBar,
    QSplitter,
    QTabWidget,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QCompleter,
    QDialog,
)
from PySide6.QtGui import QFont

from src.core.search_engine import get_search_engine
from src.core.logging_config import get_logger
from .search_workers import SearchWorker, SearchSuggestionWorker
from .saved_search_dialog import SavedSearchDialog
from .advanced_search_widget import AdvancedSearchWidget

logger = get_logger(__name__)


class SearchWidget(QWidget):
    """
    Main search widget with search input, filters, and results.
    """

    search_requested = Signal(str, dict)
    model_selected = Signal(int)

    def __init__(self, parent=None):
        """
        Initialize the search widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.search_engine = get_search_engine()
        self.current_results = []
        self.search_worker = None
        self.suggestion_worker = None
        self.setup_ui()
        self.setup_search_history()
        self.apply_styling()

    def setup_ui(self):
        """Set up the search widget UI."""
        layout = QVBoxLayout(self)

        # Search input section
        search_layout = QHBoxLayout()

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search models...")
        self.search_edit.returnPressed.connect(self.perform_search)

        # Set up completer for search suggestions
        self.completer = QCompleter()
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.search_edit.setCompleter(self.completer)

        # Connect text changed for suggestions
        self.suggestion_timer = QTimer()
        self.suggestion_timer.setSingleShot(True)
        self.suggestion_timer.timeout.connect(self.get_suggestions)
        self.search_edit.textChanged.connect(self.on_search_text_changed)

        search_layout.addWidget(self.search_edit)

        # Search button
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_button)

        # Advanced search toggle
        self.advanced_button = QPushButton("Advanced")
        self.advanced_button.setCheckable(True)
        self.advanced_button.toggled.connect(self.toggle_advanced_search)
        search_layout.addWidget(self.advanced_button)

        # Save search button
        self.save_search_button = QPushButton("Save Search")
        self.save_search_button.clicked.connect(self.save_current_search)
        search_layout.addWidget(self.save_search_button)

        layout.addLayout(search_layout)

        # Progress bar for search
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Main content area with splitter
        self.main_splitter = QSplitter(Qt.Horizontal)

        # Left panel with filters and history
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Tab widget for filters and history
        self.tab_widget = QTabWidget()

        # Advanced search tab
        self.advanced_search = AdvancedSearchWidget()
        self.advanced_search.filters_changed.connect(self.on_filters_changed)
        self.tab_widget.addTab(self.advanced_search, "Filters")

        # Search history tab
        self.history_widget = QListWidget()
        self.history_widget.itemDoubleClicked.connect(self.load_history_search)
        self.tab_widget.addTab(self.history_widget, "History")

        # Saved searches tab
        self.saved_searches_widget = QListWidget()
        self.saved_searches_widget.itemDoubleClicked.connect(self.load_saved_search)
        self.tab_widget.addTab(self.saved_searches_widget, "Saved")

        left_layout.addWidget(self.tab_widget)

        # Add left panel to splitter
        self.main_splitter.addWidget(left_panel)

        # Right panel with search results
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)

        # Results header
        self.results_header = QLabel("Enter a search query to find models")
        self.results_header.setFont(QFont("Arial", 10, QFont.Bold))
        self.results_layout.addWidget(self.results_header)

        # Results list
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self.on_result_selected)
        self.results_layout.addWidget(self.results_list)

        # Add right panel to splitter
        self.main_splitter.addWidget(self.results_widget)

        # Set splitter sizes
        self.main_splitter.setSizes([300, 700])

        layout.addWidget(self.main_splitter)

        # Initially hide advanced search
        self.advanced_search.setVisible(False)

    def apply_styling(self):
        """Apply Material Design theme to the search widget."""
        # Material Design theme is applied globally via ThemeService
        # No need to apply hardcoded stylesheets here

    def setup_search_history(self):
        """Set up search history."""
        self.refresh_search_history()
        self.refresh_saved_searches()

    def on_search_text_changed(self, text: str):
        """
        Handle search text change for suggestions.

        Args:
            text: New search text
        """
        # Start timer for delayed suggestions
        self.suggestion_timer.start(300)  # 300ms delay

    def get_suggestions(self):
        """Get search suggestions for current text."""
        query = self.search_edit.text().strip()

        if len(query) < 2:
            return

        # Cancel any existing suggestion worker
        if self.suggestion_worker and self.suggestion_worker.isRunning():
            self.suggestion_worker.terminate()

        # Start new suggestion worker
        self.suggestion_worker = SearchSuggestionWorker(query)
        self.suggestion_worker.suggestions_ready.connect(self.display_suggestions)
        self.suggestion_worker.start()

    def display_suggestions(self, suggestions: List[str]):
        """
        Display search suggestions.

        Args:
            suggestions: List of suggestions
        """
        if not suggestions:
            return

        # Update completer
        model = QStringListModel(suggestions)
        self.completer.setModel(model)

    def toggle_advanced_search(self, checked: bool):
        """
        Toggle advanced search visibility.

        Args:
            checked: Whether advanced search should be visible
        """
        self.advanced_search.setVisible(checked)

    def perform_search(self):
        """Perform the current search."""
        query = self.search_edit.text().strip()
        filters = self.advanced_search.get_current_filters()

        if not query and not filters:
            return

        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress

        # Cancel any existing search worker
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.terminate()

        # Start new search worker
        self.search_worker = SearchWorker(query, filters)
        self.search_worker.search_completed.connect(self.display_results)
        self.search_worker.search_failed.connect(self.search_failed)
        self.search_worker.start()

    def display_results(self, results: Dict[str, Any]):
        """
        Display search results.

        Args:
            results: Search results dictionary
        """
        self.progress_bar.setVisible(False)
        self.current_results = results["results"]

        # Update results header
        total_count = results["total_count"]
        execution_time = results["execution_time"]
        self.results_header.setText(f"Found {total_count} results in {execution_time:.3f} seconds")

        # Clear and populate results list
        self.results_list.clear()

        for result in self.current_results:
            item = self.create_result_item(result)
            self.results_list.addItem(item)

        # Emit search requested signal
        self.search_requested.emit(results["query"], results["filters"])

    def create_result_item(self, result: Dict[str, Any]) -> QListWidgetItem:
        """
        Create a list widget item for a search result.

        Args:
            result: Search result dictionary

        Returns:
            QListWidgetItem with formatted result
        """
        # Get model information
        title = result.get("title") or result.get("filename", "Unknown")
        description = result.get("description", "")
        category = result.get("category", "Uncategorized")
        format_type = result.get("format", "").upper()
        rating = result.get("rating", 0)

        # Create item text
        item_text = f"<b>{title}</b>"

        if description:
            # Truncate long descriptions
            desc_text = description[:100] + "..." if len(description) > 100 else description
            item_text += f"<br><i>{desc_text}</i>"

        # Add metadata
        metadata_parts = [f"Category: {category}", f"Format: {format_type}"]

        if rating > 0:
            stars = "★" * rating + "☆" * (5 - rating)
            metadata_parts.append(f"Rating: {stars}")

        item_text += f"<br><small>{' | '.join(metadata_parts)}</small>"

        # Create item
        item = QListWidgetItem()
        item.setText(item_text)
        item.setData(Qt.UserRole, result["id"])  # Store model ID

        # Enable rich text
        item.setTextFormat(Qt.RichText)

        return item

    def search_failed(self, error_msg: str):
        """
        Handle search failure.

        Args:
            error_msg: Error message
        """
        self.progress_bar.setVisible(False)
        self.results_header.setText(f"Search failed: {error_msg}")
        logger.error(error_msg)

    def on_filters_changed(self, filters: Dict[str, Any]):
        """
        Handle filter changes.

        Args:
            filters: Updated filters
        """
        # Auto-search if there's already a query
        if self.search_edit.text().strip():
            self.perform_search()

    def on_result_selected(self, item: QListWidgetItem):
        """
        Handle result selection.

        Args:
            item: Selected list item
        """
        model_id = item.data(Qt.UserRole)
        if model_id:
            self.model_selected.emit(model_id)

    def save_current_search(self):
        """Save the current search."""
        query = self.search_edit.text().strip()
        filters = self.advanced_search.get_current_filters()

        if not query and not filters:
            return

        # Show save dialog
        dialog = SavedSearchDialog(query, filters, self)
        if dialog.exec_() == QDialog.Accepted:
            name = dialog.get_search_name()
            if name:
                try:
                    self.search_engine.save_search(name, query, filters)
                    self.refresh_saved_searches()
                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                    logger.error("Failed to save search: %s", str(e))

    def refresh_search_history(self):
        """Refresh the search history list."""
        try:
            history = self.search_engine.get_search_history()

            self.history_widget.clear()

            for item in history:
                # Format history item
                query = item["query"]
                timestamp = item["timestamp"]

                # Parse timestamp
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%Y-%m-%d %H:%M")

                # Create item text
                if query:
                    item_text = f"{query} - {time_str}"
                else:
                    item_text = f"[Filters only] - {time_str}"

                list_item = QListWidgetItem(item_text)
                list_item.setData(Qt.UserRole, item)
                self.history_widget.addItem(list_item)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to refresh search history: %s", str(e))

    def refresh_saved_searches(self):
        """Refresh the saved searches list."""
        try:
            saved = self.search_engine.get_saved_searches()

            self.saved_searches_widget.clear()

            for item in saved:
                # Format saved search item
                name = item["name"]
                query = item["query"]
                created_at = item["created_at"]

                # Parse timestamp
                dt = datetime.fromisoformat(created_at)
                time_str = dt.strftime("%Y-%m-%d %H:%M")

                # Create item text
                if query:
                    item_text = f"{name} - {query} ({time_str})"
                else:
                    item_text = f"{name} - [Filters only] ({time_str})"

                list_item = QListWidgetItem(item_text)
                list_item.setData(Qt.UserRole, item)
                self.saved_searches_widget.addItem(list_item)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to refresh saved searches: %s", str(e))

    def load_history_search(self, item: QListWidgetItem):
        """
        Load a search from history.

        Args:
            item: Selected history item
        """
        search_data = item.data(Qt.UserRole)
        if not search_data:
            return

        # Set query
        self.search_edit.setText(search_data["query"])

        # Set filters
        filters = search_data.get("filters", {})
        if filters:
            # Apply filters to advanced search widget
            self.advanced_search.set_filters(filters)

        # Perform search
        self.perform_search()

    def load_saved_search(self, item: QListWidgetItem):
        """
        Load a saved search.

        Args:
            item: Selected saved search item
        """
        search_data = item.data(Qt.UserRole)
        if not search_data:
            return

        # Set query
        self.search_edit.setText(search_data["query"])

        # Set filters
        filters = search_data.get("filters", {})
        if filters:
            # Apply filters to advanced search widget
            self.advanced_search.set_filters(filters)

        # Perform search
        self.perform_search()

    def clear_search(self):
        """Clear the current search."""
        self.search_edit.clear()
        self.results_list.clear()
        self.results_header.setText("Enter a search query to find models")
        self.current_results = []

    def set_search_query(self, query: str):
        """
        Set the search query.

        Args:
            query: Search query to set
        """
        self.search_edit.setText(query)
        if query:
            self.perform_search()
