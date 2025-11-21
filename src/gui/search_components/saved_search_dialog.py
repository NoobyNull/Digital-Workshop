"""
Saved search dialog for saving searches with custom names.
"""

from typing import Any, Dict, Optional

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QGroupBox,
    QLabel,
    QDialogButtonBox,
)


class SavedSearchDialog(QDialog):
    """
    Dialog for saving a search with a custom name.
    """

    def __init__(
        self, query: str, filters: Optional[Dict[str, Any]] = None, parent=None
    ) -> None:
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

    def setup_ui(self) -> None:
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
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
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

        if "category" in self.filters and self.filters["category"]:
            categories = self.filters["category"]
            if isinstance(categories, list):
                summary_parts.append(f"Categories: {', '.join(categories)}")
            else:
                summary_parts.append(f"Category: {categories}")

        if "format" in self.filters and self.filters["format"]:
            formats = self.filters["format"]
            if isinstance(formats, list):
                summary_parts.append(f"Formats: {', '.join(formats)}")
            else:
                summary_parts.append(f"Format: {formats}")

        if "min_rating" in self.filters and self.filters["min_rating"]:
            summary_parts.append(f"Min Rating: {self.filters['min_rating']}")

        if "date_added_start" in self.filters and self.filters["date_added_start"]:
            summary_parts.append(f"Date From: {self.filters['date_added_start']}")

        if "date_added_end" in self.filters and self.filters["date_added_end"]:
            summary_parts.append(f"Date To: {self.filters['date_added_end']}")

        return "; ".join(summary_parts)

    def get_search_name(self) -> str:
        """
        Get the entered search name.

        Returns:
            Search name
        """
        return self.name_edit.text().strip()
