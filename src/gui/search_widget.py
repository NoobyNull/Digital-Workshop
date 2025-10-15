"""
Search widget for 3D-MM application.

This module provides the search interface with advanced filtering,
search history, and saved searches functionality.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QThread, Signal, QTimer, Qt, QDate, QStringListModel
from PySide6.QtWidgets import (
    QComboBox, QCompleter, QDateEdit, QDialog, QDialogButtonBox,
    QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPushButton, QScrollArea,
    QSpinBox, QSplitter, QTabWidget, QTextEdit, QVBoxLayout,
    QWidget, QCheckBox, QGroupBox, QSlider, QProgressBar
)
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QTextDocument

from core.search_engine import get_search_engine
from core.database_manager import get_database_manager
from core.logging_config import get_logger
from gui.theme import COLORS

# Initialize logger
logger = get_logger(__name__)


class SearchWorker(QThread):
    """
    Worker thread for performing search operations without blocking the UI.
    """
    search_completed = Signal(dict)
    search_failed = Signal(str)
    
    def __init__(self, query: str, filters: Optional[Dict[str, Any]] = None,
                 limit: int = 100, offset: int = 0):
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
            suggestions = self.search_engine.get_search_suggestions(self.query, self.limit)
            self.suggestions_ready.emit(suggestions)
        except Exception as e:
            logger.error(f"Failed to get suggestions: {str(e)}")
            self.suggestions_ready.emit([])


class SavedSearchDialog(QDialog):
    """
    Dialog for saving a search with a custom name.
    """
    
    def __init__(self, query: str, filters: Optional[Dict[str, Any]] = None,
                 parent=None):
        """
        Initialize the saved search dialog.
        
        Args:
            query: Search query
            filters: Search filters
            parent: Parent widget
        """
        super().__init__(parent)
        self.query = query
        self.filters = filters or {}
        self.setWindowTitle("Save Search")
        self.setMinimumWidth(400)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Form layout for input fields
        form_layout = QFormLayout()
        
        # Name input
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter a name for this search")
        form_layout.addRow("Search Name:", self.name_edit)
        
        # Display current search criteria
        summary_group = QGroupBox("Search Summary")
        summary_layout = QVBoxLayout()
        
        # Query summary
        query_label = QLabel(f"Query: {self.query}")
        query_label.setWordWrap(True)
        summary_layout.addWidget(query_label)
        
        # Filters summary
        if self.filters:
            filters_text = self._format_filters_summary()
            filters_label = QLabel(f"Filters: {filters_text}")
            filters_label.setWordWrap(True)
            summary_layout.addWidget(filters_label)
        else:
            summary_layout.addWidget(QLabel("Filters: None"))
        
        summary_group.setLayout(summary_layout)
        form_layout.addRow(summary_group)
        
        layout.addLayout(form_layout)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Set initial focus
        self.name_edit.setFocus()
    
    def _format_filters_summary(self) -> str:
        """
        Format filters for display.
        
        Returns:
            Formatted filter summary string
        """
        summary_parts = []
        
        if 'category' in self.filters and self.filters['category']:
            categories = self.filters['category']
            if isinstance(categories, list):
                summary_parts.append(f"Categories: {', '.join(categories)}")
            else:
                summary_parts.append(f"Category: {categories}")
        
        if 'format' in self.filters and self.filters['format']:
            formats = self.filters['format']
            if isinstance(formats, list):
                summary_parts.append(f"Formats: {', '.join(formats)}")
            else:
                summary_parts.append(f"Format: {formats}")
        
        if 'min_rating' in self.filters and self.filters['min_rating']:
            summary_parts.append(f"Min Rating: {self.filters['min_rating']}")
        
        if 'date_added_start' in self.filters and self.filters['date_added_start']:
            summary_parts.append(f"Date From: {self.filters['date_added_start']}")
        
        if 'date_added_end' in self.filters and self.filters['date_added_end']:
            summary_parts.append(f"Date To: {self.filters['date_added_end']}")
        
        return "; ".join(summary_parts)
    
    def get_search_name(self) -> str:
        """
        Get the entered search name.
        
        Returns:
            Search name
        """
        return self.name_edit.text().strip()


class AdvancedSearchWidget(QWidget):
    """
    Widget for advanced search filters.
    """
    
    filters_changed = Signal(dict)
    
    def __init__(self, parent=None):
        """
        Initialize the advanced search widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_manager = get_database_manager()
        self.setup_ui()
        self.load_categories()
    
    def setup_ui(self):
        """Set up the advanced search UI."""
        layout = QVBoxLayout(self)
        
        # Create scroll area for filters
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        filter_widget = QWidget()
        filter_layout = QVBoxLayout(filter_widget)
        
        # Category filter
        category_group = QGroupBox("Category")
        category_layout = QVBoxLayout()
        
        self.category_checkboxes = {}
        self.category_all_checkbox = QCheckBox("All Categories")
        self.category_all_checkbox.setChecked(True)
        self.category_all_checkbox.toggled.connect(self.on_category_all_toggled)
        category_layout.addWidget(self.category_all_checkbox)
        
        category_layout.addSpacing(10)
        
        filter_layout.addWidget(category_group)
        
        # Format filter
        format_group = QGroupBox("File Format")
        format_layout = QVBoxLayout()
        
        self.format_checkboxes = {}
        formats = ["STL", "OBJ", "3MF", "STEP"]
        
        for format_name in formats:
            checkbox = QCheckBox(format_name)
            checkbox.toggled.connect(self.on_filters_changed)
            self.format_checkboxes[format_name.lower()] = checkbox
            format_layout.addWidget(checkbox)
        
        format_group.setLayout(format_layout)
        filter_layout.addWidget(format_group)
        
        # Rating filter
        rating_group = QGroupBox("Rating")
        rating_layout = QVBoxLayout()
        
        self.min_rating_slider = QSlider(Qt.Horizontal)
        self.min_rating_slider.setMinimum(0)
        self.min_rating_slider.setMaximum(5)
        self.min_rating_slider.setValue(0)
        self.min_rating_slider.setTickPosition(QSlider.TicksBelow)
        self.min_rating_slider.setTickInterval(1)
        self.min_rating_slider.valueChanged.connect(self.on_filters_changed)
        
        self.min_rating_label = QLabel("Any Rating")
        rating_layout.addWidget(self.min_rating_label)
        rating_layout.addWidget(self.min_rating_slider)
        
        rating_group.setLayout(rating_layout)
        filter_layout.addWidget(rating_group)
        
        # Date range filter
        date_group = QGroupBox("Date Range")
        date_layout = QFormLayout()
        
        self.date_added_start = QDateEdit()
        self.date_added_start.setCalendarPopup(True)
        self.date_added_start.setDate(QDate.currentDate().addMonths(-1))
        self.date_added_start.dateChanged.connect(self.on_filters_changed)
        date_layout.addRow("Added From:", self.date_added_start)
        
        self.date_added_end = QDateEdit()
        self.date_added_end.setCalendarPopup(True)
        self.date_added_end.setDate(QDate.currentDate())
        self.date_added_end.dateChanged.connect(self.on_filters_changed)
        date_layout.addRow("Added To:", self.date_added_end)
        
        date_group.setLayout(date_layout)
        filter_layout.addWidget(date_group)
        
        # File size filter
        size_group = QGroupBox("File Size (MB)")
        size_layout = QFormLayout()
        
        self.min_size_spin = QSpinBox()
        self.min_size_spin.setMinimum(0)
        self.min_size_spin.setMaximum(10000)
        self.min_size_spin.setSuffix(" MB")
        self.min_size_spin.valueChanged.connect(self.on_filters_changed)
        size_layout.addRow("Minimum:", self.min_size_spin)
        
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setMaximum(10000)
        self.max_size_spin.setSuffix(" MB")
        self.max_size_spin.valueChanged.connect(self.on_filters_changed)
        size_layout.addRow("Maximum:", self.max_size_spin)
        
        size_group.setLayout(size_layout)
        filter_layout.addWidget(size_group)
        
        # Add stretch to push everything to the top
        filter_layout.addStretch()
        
        scroll_area.setWidget(filter_widget)
        layout.addWidget(scroll_area)
        
        # Reset filters button
        reset_button = QPushButton("Reset Filters")
        reset_button.clicked.connect(self.reset_filters)
        layout.addWidget(reset_button)
    
    def load_categories(self):
        """Load categories from the database."""
        try:
            categories = self.db_manager.get_categories()
            
            # Clear existing category checkboxes (except "All")
            for checkbox in self.category_checkboxes.values():
                checkbox.deleteLater()
            self.category_checkboxes.clear()
            
            # Add category checkboxes
            category_layout = self.category_all_checkbox.parent().layout()
            
            for category in categories:
                checkbox = QCheckBox(category['name'])
                checkbox.toggled.connect(self.on_category_toggled)
                self.category_checkboxes[category['name']] = checkbox
                category_layout.addWidget(checkbox)
            
        except Exception as e:
            logger.error(f"Failed to load categories: {str(e)}")
    
    def on_category_all_toggled(self, checked: bool):
        """
        Handle "All Categories" checkbox toggle.
        
        Args:
            checked: Whether the checkbox is checked
        """
        # Uncheck all individual categories when "All" is checked
        for checkbox in self.category_checkboxes.values():
            checkbox.blockSignals(True)
            checkbox.setChecked(not checked)
            checkbox.blockSignals(False)
        
        self.on_filters_changed()
    
    def on_category_toggled(self):
        """Handle individual category checkbox toggle."""
        # Check if any individual categories are selected
        any_selected = any(checkbox.isChecked() 
                          for checkbox in self.category_checkboxes.values())
        
        # Update "All Categories" checkbox
        self.category_all_checkbox.blockSignals(True)
        self.category_all_checkbox.setChecked(not any_selected)
        self.category_all_checkbox.blockSignals(False)
        
        self.on_filters_changed()
    
    def on_filters_changed(self):
        """Handle any filter change."""
        # Update rating label
        rating = self.min_rating_slider.value()
        if rating == 0:
            self.min_rating_label.setText("Any Rating")
        else:
            self.min_rating_label.setText(f"Minimum: {rating} Stars")
        
        # Emit filters changed signal
        filters = self.get_current_filters()
        self.filters_changed.emit(filters)
    
    def get_current_filters(self) -> Dict[str, Any]:
        """
        Get current filter values.
        
        Returns:
            Dictionary of current filters
        """
        filters = {}
        
        # Category filter
        selected_categories = [name for name, checkbox in self.category_checkboxes.items()
                              if checkbox.isChecked()]
        if selected_categories:
            filters['category'] = selected_categories
        
        # Format filter
        selected_formats = [format_name for format_name, checkbox in self.format_checkboxes.items()
                           if checkbox.isChecked()]
        if selected_formats:
            filters['format'] = selected_formats
        
        # Rating filter
        min_rating = self.min_rating_slider.value()
        if min_rating > 0:
            filters['min_rating'] = min_rating
        
        # Date range filter
        if self.date_added_start.date().isValid():
            filters['date_added_start'] = self.date_added_start.date().toString("yyyy-MM-dd")
        
        if self.date_added_end.date().isValid():
            filters['date_added_end'] = self.date_added_end.date().toString("yyyy-MM-dd")
        
        # File size filter
        min_size = self.min_size_spin.value()
        if min_size > 0:
            filters['min_file_size'] = min_size * 1024 * 1024  # Convert to bytes
        
        max_size = self.max_size_spin.value()
        if max_size > 0:
            filters['max_file_size'] = max_size * 1024 * 1024  # Convert to bytes
        
        return filters
    
    def reset_filters(self):
        """Reset all filters to default values."""
        # Reset categories
        self.category_all_checkbox.setChecked(True)
        
        # Reset formats
        for checkbox in self.format_checkboxes.values():
            checkbox.setChecked(False)
        
        # Reset rating
        self.min_rating_slider.setValue(0)
        
        # Reset date range
        self.date_added_start.setDate(QDate.currentDate().addMonths(-1))
        self.date_added_end.setDate(QDate.currentDate())
        
        # Reset file size
        self.min_size_spin.setValue(0)
        self.max_size_spin.setValue(0)
    
    def set_filters(self, filters: Dict[str, Any]):
        """
        Set filter values from a dictionary.
        
        Args:
            filters: Dictionary of filter values
        """
        # Reset first
        self.reset_filters()
        
        # Category filter
        if 'category' in filters:
            categories = filters['category']
            if isinstance(categories, list):
                for category in categories:
                    if category in self.category_checkboxes:
                        self.category_checkboxes[category].setChecked(True)
            elif categories in self.category_checkboxes:
                self.category_checkboxes[categories].setChecked(True)
        
        # Format filter
        if 'format' in filters:
            formats = filters['format']
            if isinstance(formats, list):
                for format_name in formats:
                    format_key = format_name.lower()
                    if format_key in self.format_checkboxes:
                        self.format_checkboxes[format_key].setChecked(True)
            elif formats.lower() in self.format_checkboxes:
                self.format_checkboxes[formats.lower()].setChecked(True)
        
        # Rating filter
        if 'min_rating' in filters:
            self.min_rating_slider.setValue(filters['min_rating'])
        
        # Date range filter
        if 'date_added_start' in filters:
            date_str = filters['date_added_start']
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            if date.isValid():
                self.date_added_start.setDate(date)
        
        if 'date_added_end' in filters:
            date_str = filters['date_added_end']
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            if date.isValid():
                self.date_added_end.setDate(date)
        
        # File size filter
        if 'min_file_size' in filters:
            size_bytes = filters['min_file_size']
            size_mb = size_bytes // (1024 * 1024)
            self.min_size_spin.setValue(size_mb)
        
        if 'max_file_size' in filters:
            size_bytes = filters['max_file_size']
            size_mb = size_bytes // (1024 * 1024)
            self.max_size_spin.setValue(size_mb)


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
        """Apply Windows standard colors to the search widget."""
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS.window_bg};
                color: {COLORS.text};
                border: 1px solid {COLORS.border};
                padding: 6px;
                border-radius: 2px;
                selection-background-color: {COLORS.selection_bg};
                selection-color: {COLORS.selection_text};
            }}
            QLineEdit:focus {{
                border: 2px solid {COLORS.primary};
            }}
            QPushButton {{
                background-color: {COLORS.surface};
                color: {COLORS.text};
                border: 1px solid {COLORS.border};
                padding: 6px 12px;
                border-radius: 2px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.hover};
                border: 1px solid {COLORS.primary};
            }}
            QPushButton:pressed {{
                background-color: {COLORS.pressed};
            }}
            QPushButton:checked {{
                background-color: {COLORS.primary};
                color: {COLORS.primary_text};
                border: 1px solid {COLORS.primary};
            }}
            QProgressBar {{
                border: 1px solid {COLORS.border};
                border-radius: 2px;
                text-align: center;
                background-color: {COLORS.window_bg};
                color: {COLORS.text};
            }}
            QProgressBar::chunk {{
                background-color: {COLORS.progress_chunk};
                border-radius: 1px;
            }}
            QTabWidget::pane {{
                border: 1px solid {COLORS.border};
                background-color: {COLORS.window_bg};
            }}
            QTabBar::tab {{
                background: {COLORS.surface};
                padding: 8px;
                margin-right: 2px;
                border: 1px solid {COLORS.border};
                border-bottom: none;
                color: {COLORS.text};
            }}
            QTabBar::tab:selected {{
                background: {COLORS.window_bg};
                border-bottom: 2px solid {COLORS.tab_selected_border};
                color: {COLORS.text};
            }}
            QTabBar::tab:hover {{
                background: {COLORS.hover};
            }}
            QListWidget {{
                background-color: {COLORS.window_bg};
                color: {COLORS.text};
                border: 1px solid {COLORS.border};
                selection-background-color: {COLORS.selection_bg};
                selection-color: {COLORS.selection_text};
            }}
            QListWidget::item {{
                padding: 5px;
                border-bottom: 1px solid {COLORS.border_light};
            }}
            QListWidget::item:selected {{
                background-color: {COLORS.selection_bg};
                color: {COLORS.selection_text};
            }}
            QLabel {{
                color: {COLORS.text};
                background-color: transparent;
            }}
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLORS.border};
                border-radius: 4px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: {COLORS.window_bg};
                color: {COLORS.text};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {COLORS.text};
            }}
            QCheckBox {{
                color: {COLORS.text};
                background-color: transparent;
            }}
            QSlider::groove:horizontal {{
                border: 1px solid {COLORS.border};
                height: 8px;
                background: {COLORS.surface};
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS.slider_handle};
                border: 1px solid {COLORS.slider_handle};
                width: 18px;
                border-radius: 9px;
                margin: -5px 0;
            }}
            QSpinBox {{
                background-color: {COLORS.window_bg};
                color: {COLORS.text};
                border: 1px solid {COLORS.border};
                padding: 4px;
                border-radius: 2px;
            }}
            QSpinBox:focus {{
                border: 2px solid {COLORS.primary};
            }}
            QDateEdit {{
                background-color: {COLORS.window_bg};
                color: {COLORS.text};
                border: 1px solid {COLORS.border};
                padding: 4px;
                border-radius: 2px;
            }}
            QDateEdit:focus {{
                border: 2px solid {COLORS.primary};
            }}
        """)
    
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
        self.current_results = results['results']
        
        # Update results header
        total_count = results['total_count']
        execution_time = results['execution_time']
        self.results_header.setText(
            f"Found {total_count} results in {execution_time:.3f} seconds"
        )
        
        # Clear and populate results list
        self.results_list.clear()
        
        for result in self.current_results:
            item = self.create_result_item(result)
            self.results_list.addItem(item)
        
        # Emit search requested signal
        self.search_requested.emit(results['query'], results['filters'])
    
    def create_result_item(self, result: Dict[str, Any]) -> QListWidgetItem:
        """
        Create a list widget item for a search result.
        
        Args:
            result: Search result dictionary
            
        Returns:
            QListWidgetItem with formatted result
        """
        # Get model information
        title = result.get('title') or result.get('filename', 'Unknown')
        description = result.get('description', '')
        category = result.get('category', 'Uncategorized')
        format_type = result.get('format', '').upper()
        rating = result.get('rating', 0)
        
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
        item.setData(Qt.UserRole, result['id'])  # Store model ID
        
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
                except Exception as e:
                    logger.error(f"Failed to save search: {str(e)}")
    
    def refresh_search_history(self):
        """Refresh the search history list."""
        try:
            history = self.search_engine.get_search_history()
            
            self.history_widget.clear()
            
            for item in history:
                # Format history item
                query = item['query']
                timestamp = item['timestamp']
                
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
                
        except Exception as e:
            logger.error(f"Failed to refresh search history: {str(e)}")
    
    def refresh_saved_searches(self):
        """Refresh the saved searches list."""
        try:
            saved = self.search_engine.get_saved_searches()
            
            self.saved_searches_widget.clear()
            
            for item in saved:
                # Format saved search item
                name = item['name']
                query = item['query']
                created_at = item['created_at']
                
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
                
        except Exception as e:
            logger.error(f"Failed to refresh saved searches: {str(e)}")
    
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
        self.search_edit.setText(search_data['query'])
        
        # Set filters
        filters = search_data.get('filters', {})
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
        self.search_edit.setText(search_data['query'])
        
        # Set filters
        filters = search_data.get('filters', {})
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