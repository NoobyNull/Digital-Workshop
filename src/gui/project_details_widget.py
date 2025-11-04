"""
Project Details Widget for displaying model information and attached resources.

Shows:
- Model information (name, format, size, dimensions, geometry stats)
- Attached resources/files (list of files associated with the model)
"""

from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)

from src.core.logging_config import get_logger


logger = get_logger(__name__)


class ProjectDetailsWidget(QWidget):
    """
    Widget for displaying project/model details and attached resources.

    Displays:
    - Model Information: name, format, size, dimensions, geometry stats
    - Attached Resources: list of files associated with the model
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.current_model_id: Optional[int] = None
        self.current_model_data: Optional[Dict[str, Any]] = None

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(12)

        # Model Information Section
        self.model_info_group = self._create_model_info_section()
        scroll_layout.addWidget(self.model_info_group)

        # Resources/Files Section
        self.resources_group = self._create_resources_section()
        scroll_layout.addWidget(self.resources_group)

        # Stretch to fill remaining space
        scroll_layout.addStretch()

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

    def _create_model_info_section(self) -> QGroupBox:
        """Create the model information section."""
        group = QGroupBox("Model Information")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)

        # Create info labels (will be populated when model is selected)
        self.info_labels = {}

        info_fields = [
            ("Name", "name"),
            ("Format", "format"),
            ("File Size", "file_size"),
            ("Dimensions", "dimensions"),
            ("Triangles", "triangles"),
            ("Vertices", "vertices"),
            ("Date Added", "date_added"),
        ]

        for label_text, field_key in info_fields:
            h_layout = QHBoxLayout()

            label = QLabel(f"{label_text}:")
            label.setStyleSheet("font-weight: bold; min-width: 100px;")

            value = QLabel("-")
            value.setWordWrap(True)
            value.setStyleSheet("color: #666666;")

            self.info_labels[field_key] = value

            h_layout.addWidget(label)
            h_layout.addWidget(value, 1)
            layout.addLayout(h_layout)

        return group

    def _create_resources_section(self) -> QGroupBox:
        """Create the resources/files section."""
        group = QGroupBox("Attached Resources")
        layout = QVBoxLayout(group)

        # Resources table
        self.resources_table = QTableWidget()
        self.resources_table.setColumnCount(3)
        self.resources_table.setHorizontalHeaderLabels(["File Name", "Size", "Type"])
        self.resources_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )
        self.resources_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )
        self.resources_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents
        )
        self.resources_table.setMaximumHeight(200)
        self.resources_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.resources_table.setSelectionMode(QTableWidget.SingleSelection)

        layout.addWidget(self.resources_table)

        return group

    def set_model(self, model_data: Dict[str, Any]) -> None:
        """
        Set the model to display.

        Args:
            model_data: Dictionary containing model information
        """
        try:
            self.current_model_data = model_data
            self.current_model_id = model_data.get("id")

            self._update_model_info(model_data)
            self._update_resources(model_data)

        except Exception as e:
            self.logger.error(f"Failed to set model: {e}")
            self.clear()

    def _update_model_info(self, model_data: Dict[str, Any]) -> None:
        """Update model information display."""
        try:
            # Format file size
            file_size = model_data.get("file_size", 0) or 0
            if file_size > 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024):.2f} MB"
            elif file_size > 1024:
                size_str = f"{file_size / 1024:.2f} KB"
            else:
                size_str = f"{file_size} B"

            # Format dimensions
            dimensions = model_data.get("dimensions", (0, 0, 0))
            if isinstance(dimensions, (list, tuple)) and len(dimensions) >= 3:
                dim_str = (
                    f"{dimensions[0]:.2f} × {dimensions[1]:.2f} × {dimensions[2]:.2f}"
                )
            else:
                dim_str = "-"

            # Update labels
            self.info_labels["name"].setText(model_data.get("filename", "-"))
            self.info_labels["format"].setText(model_data.get("format", "-").upper())
            self.info_labels["file_size"].setText(size_str)
            self.info_labels["dimensions"].setText(dim_str)
            self.info_labels["triangles"].setText(
                f"{model_data.get('triangle_count', 0):,}"
            )
            self.info_labels["vertices"].setText(
                f"{model_data.get('vertex_count', 0):,}"
            )
            self.info_labels["date_added"].setText(
                str(model_data.get("date_added", "-"))
            )

        except Exception as e:
            self.logger.error(f"Failed to update model info: {e}")

    def _update_resources(self, model_data: Dict[str, Any]) -> None:
        """Update resources/files display."""
        try:
            self.resources_table.setRowCount(0)

            # Get file path from model
            file_path = model_data.get("file_path")
            if not file_path:
                return

            file_path = Path(file_path)

            # Add the main model file
            if file_path.exists():
                self._add_resource_row(file_path)

            # TODO: Add support for related files (textures, materials, etc.)
            # This would require additional database schema to track related files

        except Exception as e:
            self.logger.error(f"Failed to update resources: {e}")

    def _add_resource_row(self, file_path: Path) -> None:
        """Add a resource file to the table."""
        try:
            row = self.resources_table.rowCount()
            self.resources_table.insertRow(row)

            # File name
            name_item = QTableWidgetItem(file_path.name)
            name_item.setIcon(self._get_file_icon(file_path))
            self.resources_table.setItem(row, 0, name_item)

            # File size
            try:
                size = file_path.stat().st_size
                if size > 1024 * 1024:
                    size_str = f"{size / (1024 * 1024):.2f} MB"
                elif size > 1024:
                    size_str = f"{size / 1024:.2f} KB"
                else:
                    size_str = f"{size} B"
            except:
                size_str = "-"

            size_item = QTableWidgetItem(size_str)
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.resources_table.setItem(row, 1, size_item)

            # File type
            type_item = QTableWidgetItem(file_path.suffix.upper() or "FILE")
            self.resources_table.setItem(row, 2, type_item)

        except Exception as e:
            self.logger.error(f"Failed to add resource row: {e}")

    def _get_file_icon(self, file_path: Path) -> QIcon:
        """Get appropriate icon for file type."""
        # Return empty icon for now - can be enhanced with file type icons
        return QIcon()

    def clear(self) -> None:
        """Clear all displayed information."""
        self.current_model_id = None
        self.current_model_data = None

        # Clear info labels
        for label in self.info_labels.values():
            label.setText("-")

        # Clear resources table
        self.resources_table.setRowCount(0)
