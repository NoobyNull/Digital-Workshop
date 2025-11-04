"""
Advanced search widget with filtering options.

Provides advanced filtering by category, format, rating, date, and file size.
"""

from typing import Any, Dict

from PySide6.QtCore import Signal, Qt, QDate
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QScrollArea,
    QGroupBox,
    QCheckBox,
    QSlider,
    QDateEdit,
    QSpinBox,
    QPushButton,
    QLabel,
)

from src.core.database_manager import get_database_manager
from src.core.logging_config import get_logger

logger = get_logger(__name__)


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
                checkbox = QCheckBox(category["name"])
                checkbox.toggled.connect(self.on_category_toggled)
                self.category_checkboxes[category["name"]] = checkbox
                category_layout.addWidget(checkbox)

        except Exception as e:
            logger.error("Failed to load categories: %s", str(e))

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
        any_selected = any(checkbox.isChecked() for checkbox in self.category_checkboxes.values())

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
        selected_categories = [
            name for name, checkbox in self.category_checkboxes.items() if checkbox.isChecked()
        ]
        if selected_categories:
            filters["category"] = selected_categories

        # Format filter
        selected_formats = [
            format_name
            for format_name, checkbox in self.format_checkboxes.items()
            if checkbox.isChecked()
        ]
        if selected_formats:
            filters["format"] = selected_formats

        # Rating filter
        min_rating = self.min_rating_slider.value()
        if min_rating > 0:
            filters["min_rating"] = min_rating

        # Date range filter
        if self.date_added_start.date().isValid():
            filters["date_added_start"] = self.date_added_start.date().toString("yyyy-MM-dd")

        if self.date_added_end.date().isValid():
            filters["date_added_end"] = self.date_added_end.date().toString("yyyy-MM-dd")

        # File size filter
        min_size = self.min_size_spin.value()
        if min_size > 0:
            filters["min_file_size"] = min_size * 1024 * 1024  # Convert to bytes

        max_size = self.max_size_spin.value()
        if max_size > 0:
            filters["max_file_size"] = max_size * 1024 * 1024  # Convert to bytes

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
        if "category" in filters:
            categories = filters["category"]
            if isinstance(categories, list):
                for category in categories:
                    if category in self.category_checkboxes:
                        self.category_checkboxes[category].setChecked(True)
            elif categories in self.category_checkboxes:
                self.category_checkboxes[categories].setChecked(True)

        # Format filter
        if "format" in filters:
            formats = filters["format"]
            if isinstance(formats, list):
                for format_name in formats:
                    format_key = format_name.lower()
                    if format_key in self.format_checkboxes:
                        self.format_checkboxes[format_key].setChecked(True)
            elif formats.lower() in self.format_checkboxes:
                self.format_checkboxes[formats.lower()].setChecked(True)

        # Rating filter
        if "min_rating" in filters:
            self.min_rating_slider.setValue(filters["min_rating"])

        # Date range filter
        if "date_added_start" in filters:
            date_str = filters["date_added_start"]
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            if date.isValid():
                self.date_added_start.setDate(date)

        if "date_added_end" in filters:
            date_str = filters["date_added_end"]
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            if date.isValid():
                self.date_added_end.setDate(date)

        # File size filter
        if "min_file_size" in filters:
            size_bytes = filters["min_file_size"]
            size_mb = size_bytes // (1024 * 1024)
            self.min_size_spin.setValue(size_mb)

        if "max_file_size" in filters:
            size_bytes = filters["max_file_size"]
            size_mb = size_bytes // (1024 * 1024)
            self.max_size_spin.setValue(size_mb)
