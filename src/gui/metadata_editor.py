"""
Metadata editor widget for 3D-MM application.

This module provides a comprehensive metadata editing interface with form fields,
star rating system, category management, and database integration for managing
3D model metadata.
"""

import gc
from typing import Dict, List, Optional, Any

from PySide6.QtCore import Qt, Signal, QSize, QPointF
from PySide6.QtGui import QPixmap, QPainter, QPen, QBrush, QColor, QFont, QPolygonF
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QTextEdit, QComboBox, QPushButton, QLabel,
    QFrame, QScrollArea, QMessageBox, QSpinBox, QButtonGroup,
    QRadioButton, QCheckBox, QSizePolicy, QGridLayout
)

from core.logging_config import get_logger, log_function_call
from core.database_manager import get_database_manager
from gui.theme import COLORS, qcolor


class StarRatingWidget(QWidget):
    """
    Interactive star rating widget with visual feedback.
    
    Provides a 1-5 star rating system with hover effects and click interaction.
    """
    
    # Signal emitted when rating changes
    rating_changed = Signal(int)
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the star rating widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Initialize logger
        self.logger = get_logger(__name__)
        
        # Rating state
        self.current_rating = 0
        self.hover_rating = 0
        
        # Star properties
        self.star_size = 24
        self.star_spacing = 5
        self.star_count = 5
        
        # Star colors (from theme)
        self.filled_color = qcolor('star_filled')
        self.empty_color = qcolor('star_empty')
        self.hover_color = qcolor('star_hover')
        
        # Set widget size
        self.setFixedSize(
            self.star_count * (self.star_size + self.star_spacing) - self.star_spacing,
            self.star_size
        )
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
        self.logger.debug("Star rating widget initialized")
    
    def set_rating(self, rating: int) -> None:
        """
        Set the current rating.
        
        Args:
            rating: Rating value (1-5)
        """
        if 1 <= rating <= self.star_count:
            self.current_rating = rating
            self.update()
            self.rating_changed.emit(rating)
            self.logger.debug(f"Rating set to: {rating}")
    
    def get_rating(self) -> int:
        """
        Get the current rating.
        
        Returns:
            Current rating value (1-5)
        """
        return self.current_rating
    
    def reset_rating(self) -> None:
        """Reset the rating to 0."""
        self.current_rating = 0
        self.update()
        self.rating_changed.emit(0)
        self.logger.debug("Rating reset")
    
    def paintEvent(self, event) -> None:
        """Paint the star rating widget."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        for i in range(self.star_count):
            # Calculate star position
            x = i * (self.star_size + self.star_spacing)
            y = 0
            
            # Determine star color
            if i < self.current_rating:
                color = self.filled_color
            elif i < self.hover_rating:
                color = self.hover_color
            else:
                color = self.empty_color
            
            # Draw star
            self._draw_star(painter, x, y, self.star_size, color)
        
        painter.end()
    
    def _draw_star(self, painter: QPainter, x: int, y: int, size: int, color: QColor) -> None:
        """
        Draw a star shape.
        
        Args:
            painter: QPainter object
            x: X coordinate
            y: Y coordinate
            size: Star size
            color: Star color
        """
        painter.setPen(QPen(color.darker(120), 1))
        painter.setBrush(QBrush(color))
        
        # Create star path
        center_x = x + size / 2
        center_y = y + size / 2
        outer_radius = size / 2
        inner_radius = outer_radius * 0.4
        
        points = []
        for i in range(10):
            angle = 3.14159 * i / 5 - 3.14159 / 2
            if i % 2 == 0:
                radius = outer_radius
            else:
                radius = inner_radius
            
            px = center_x + radius * (angle if i % 4 < 2 else -angle)
            py = center_y + radius * (1 if i % 4 < 2 else -1)
            points.append(QPointF(px, py))
        
        painter.drawPolygon(QPolygonF(points))
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton:
            rating = self._get_rating_from_position(event.pos().x())
            self.set_rating(rating)
    
    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move events for hover effects."""
        rating = self._get_rating_from_position(event.pos().x())
        if rating != self.hover_rating:
            self.hover_rating = rating
            self.update()
    
    def leaveEvent(self, event) -> None:
        """Handle mouse leave events."""
        self.hover_rating = 0
        self.update()
    
    def _get_rating_from_position(self, x: int) -> int:
        """
        Get rating value from mouse position.
        
        Args:
            x: Mouse X coordinate
            
        Returns:
            Rating value (1-5)
        """
        rating = (x // (self.star_size + self.star_spacing)) + 1
        return max(0, min(rating, self.star_count))


class MetadataEditorWidget(QWidget):
    """
    Comprehensive metadata editor widget for 3D models.
    
    Features:
    - Form fields for title, description, keywords, category, and source
    - Interactive star rating system
    - Category management with predefined categories
    - Save/cancel/reset functionality
    - Validation and error handling
    - Database integration for metadata persistence
    """
    
    # Signals
    metadata_saved = Signal(int)  # Emitted when metadata is saved (model_id)
    metadata_changed = Signal(int)  # Emitted when metadata is changed (model_id)
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the metadata editor widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Initialize logger
        self.logger = get_logger(__name__)
        self.logger.info("Initializing metadata editor widget")
        
        # Initialize components
        self.db_manager = get_database_manager()
        self.current_model_id = None
        self.original_metadata = {}
        self.categories = []
        
        # Initialize UI
        self._init_ui()
        self._setup_connections()
        self._load_categories()
        
        self.logger.info("Metadata editor widget initialized successfully")
    
    def _init_ui(self) -> None:
        """Initialize the user interface layout."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        
        # Create model info group
        self._create_model_info_group(content_layout)
        
        # Create metadata form
        self._create_metadata_form(content_layout)
        
        # Create rating group
        self._create_rating_group(content_layout)
        
        # Create button group
        self._create_button_group(content_layout)
        
        # Add stretch to push content to top
        content_layout.addStretch()
        
        # Set scroll area content
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # Apply styling
        self._apply_styling()
    
    def _create_model_info_group(self, parent_layout: QVBoxLayout) -> None:
        """Create the model information group."""
        group = QGroupBox("Model Information")
        group_layout = QFormLayout(group)
        
        # Model filename
        self.model_filename_label = QLabel("No model selected")
        group_layout.addRow("Filename:", self.model_filename_label)
        
        # Model format
        self.model_format_label = QLabel("-")
        group_layout.addRow("Format:", self.model_format_label)
        
        # Model file size
        self.model_size_label = QLabel("-")
        group_layout.addRow("File Size:", self.model_size_label)
        
        # Model triangle count
        self.model_triangles_label = QLabel("-")
        group_layout.addRow("Triangles:", self.model_triangles_label)
        
        parent_layout.addWidget(group)
    
    def _create_metadata_form(self, parent_layout: QVBoxLayout) -> None:
        """Create the metadata form fields."""
        group = QGroupBox("Metadata")
        group_layout = QFormLayout(group)
        
        # Title field
        self.title_field = QLineEdit()
        self.title_field.setPlaceholderText("Enter model title...")
        group_layout.addRow("Title:", self.title_field)
        
        # Description field
        self.description_field = QTextEdit()
        self.description_field.setPlaceholderText("Enter model description...")
        self.description_field.setMaximumHeight(100)
        group_layout.addRow("Description:", self.description_field)
        
        # Keywords field
        self.keywords_field = QLineEdit()
        self.keywords_field.setPlaceholderText("Enter keywords separated by commas...")
        group_layout.addRow("Keywords:", self.keywords_field)
        
        # Category field
        self.category_field = QComboBox()
        self.category_field.setEditable(True)
        group_layout.addRow("Category:", self.category_field)
        
        # Source field
        self.source_field = QLineEdit()
        self.source_field.setPlaceholderText("Enter source URL or reference...")
        group_layout.addRow("Source:", self.source_field)
        
        parent_layout.addWidget(group)
    
    def _create_rating_group(self, parent_layout: QVBoxLayout) -> None:
        """Create the rating group with star widget."""
        group = QGroupBox("Rating")
        group_layout = QVBoxLayout(group)
        
        # Create star rating widget
        self.star_rating = StarRatingWidget()
        group_layout.addWidget(self.star_rating)
        
        # Rating label
        self.rating_label = QLabel("No rating")
        self.rating_label.setAlignment(Qt.AlignCenter)
        group_layout.addWidget(self.rating_label)
        
        parent_layout.addWidget(group)
    
    def _create_button_group(self, parent_layout: QVBoxLayout) -> None:
        """Create the button group for actions."""
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # Save button
        self.save_button = QPushButton("Save")
        self.save_button.setDefault(True)
        button_layout.addWidget(self.save_button)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        button_layout.addWidget(self.cancel_button)
        
        # Reset button
        self.reset_button = QPushButton("Reset")
        button_layout.addWidget(self.reset_button)
        
        parent_layout.addWidget(button_frame)
    
    def _apply_styling(self) -> None:
        """Apply styling to the widget with Windows standard colors."""
        self.setStyleSheet(f"""
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
            QLineEdit, QTextEdit, QComboBox {{
                border: 1px solid {COLORS.border};
                border-radius: 2px;
                padding: 6px;
                background-color: {COLORS.window_bg};
                color: {COLORS.text};
                selection-background-color: {COLORS.selection_bg};
                selection-color: {COLORS.selection_text};
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
                border: 2px solid {COLORS.primary};
                outline: none;
            }}
            QLineEdit:hover, QTextEdit:hover, QComboBox:hover {{
                border: 1px solid {COLORS.primary};
            }}
            QPushButton {{
                border: 1px solid {COLORS.border};
                border-radius: 2px;
                padding: 8px 16px;
                background-color: {COLORS.surface};
                color: {COLORS.text};
                font-weight: normal;
            }}
            QPushButton:hover {{
                background-color: {COLORS.hover};
                border: 1px solid {COLORS.primary};
            }}
            QPushButton:pressed {{
                background-color: {COLORS.pressed};
            }}
            QPushButton:default {{
                border: 1px solid {COLORS.primary};
                background-color: {COLORS.primary};
                color: {COLORS.primary_text};
                font-weight: bold;
            }}
            QPushButton:default:hover {{
                background-color: {COLORS.primary_hover};
            }}
            QLabel {{
                color: {COLORS.text};
                background-color: transparent;
            }}
            QScrollArea {{
                background-color: {COLORS.window_bg};
                border: none;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {COLORS.text_muted};
                margin-right: 4px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS.window_bg};
                border: 1px solid {COLORS.border};
                selection-background-color: {COLORS.selection_bg};
                selection-color: {COLORS.selection_text};
                color: {COLORS.text};
            }}
        """)
    
    def _setup_connections(self) -> None:
        """Set up signal connections."""
        # Button connections
        self.save_button.clicked.connect(self._save_metadata)
        self.cancel_button.clicked.connect(self._cancel_changes)
        self.reset_button.clicked.connect(self._reset_form)
        
        # Star rating connection
        self.star_rating.rating_changed.connect(self._on_rating_changed)
        
        # Field change connections for dirty state tracking
        self.title_field.textChanged.connect(self._on_field_changed)
        self.description_field.textChanged.connect(self._on_field_changed)
        self.keywords_field.textChanged.connect(self._on_field_changed)
        self.category_field.currentTextChanged.connect(self._on_field_changed)
        self.source_field.textChanged.connect(self._on_field_changed)
    
    def _load_categories(self) -> None:
        """Load categories from the database."""
        try:
            self.categories = self.db_manager.get_categories()
            
            # Clear and repopulate category combo box
            self.category_field.clear()
            self.category_field.addItem("")  # Empty option for no category
            
            for category in self.categories:
                self.category_field.addItem(category['name'])
            
            self.logger.debug(f"Loaded {len(self.categories)} categories")
            
        except Exception as e:
            self.logger.error(f"Failed to load categories: {str(e)}")
    
    def load_model_metadata(self, model_id: int) -> None:
        """
        Load metadata for a specific model.
        
        Args:
            model_id: ID of the model to load metadata for
        """
        try:
            self.logger.info(f"Loading metadata for model ID: {model_id}")
            
            # Get model information from database
            model = self.db_manager.get_model(model_id)
            
            if not model:
                self.logger.warning(f"Model with ID {model_id} not found")
                self._clear_form()
                return
            
            # Store current model ID
            self.current_model_id = model_id
            
            # Update model information
            self._update_model_info(model)
            
            # Load metadata
            self._load_metadata_fields(model)
            
            # Store original metadata for change detection
            self.original_metadata = {
                'title': model.get('title', ''),
                'description': model.get('description', ''),
                'keywords': model.get('keywords', ''),
                'category': model.get('category', ''),
                'source': model.get('source', ''),
                'rating': model.get('rating', 0)
            }
            
            # Reset dirty state
            self._reset_dirty_state()
            
            self.logger.info(f"Metadata loaded for model: {model['filename']}")
            
        except Exception as e:
            self.logger.error(f"Failed to load metadata for model {model_id}: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load metadata: {str(e)}")
    
    def _update_model_info(self, model: Dict[str, Any]) -> None:
        """
        Update the model information display.
        
        Args:
            model: Model information dictionary
        """
        self.model_filename_label.setText(model.get('filename', 'Unknown'))
        self.model_format_label.setText(model.get('format', 'Unknown').upper())
        
        # Format file size
        file_size = model.get('file_size', 0)
        if file_size > 1024 * 1024:
            size_text = f"{file_size / (1024 * 1024):.1f} MB"
        elif file_size > 1024:
            size_text = f"{file_size / 1024:.1f} KB"
        else:
            size_text = f"{file_size} B"
        self.model_size_label.setText(size_text)
        
        # Triangle count
        triangle_count = model.get('triangle_count', 0)
        self.model_triangles_label.setText(f"{triangle_count:,}")
    
    def _load_metadata_fields(self, model: Dict[str, Any]) -> None:
        """
        Load metadata into form fields.
        
        Args:
            model: Model information dictionary
        """
        # Block signals to prevent change detection during loading
        self.title_field.blockSignals(True)
        self.description_field.blockSignals(True)
        self.keywords_field.blockSignals(True)
        self.category_field.blockSignals(True)
        self.source_field.blockSignals(True)
        self.star_rating.blockSignals(True)
        
        try:
            # Load text fields
            self.title_field.setText(model.get('title', ''))
            self.description_field.setPlainText(model.get('description', ''))
            self.keywords_field.setText(model.get('keywords', ''))
            self.source_field.setText(model.get('source', ''))
            
            # Load category
            category = model.get('category', '')
            if category:
                index = self.category_field.findText(category)
                if index >= 0:
                    self.category_field.setCurrentIndex(index)
                else:
                    self.category_field.setCurrentText(category)
            else:
                self.category_field.setCurrentIndex(0)
            
            # Load rating
            rating = model.get('rating', 0)
            self.star_rating.set_rating(rating)
            self._update_rating_label(rating)
            
        finally:
            # Unblock signals
            self.title_field.blockSignals(False)
            self.description_field.blockSignals(False)
            self.keywords_field.blockSignals(False)
            self.category_field.blockSignals(False)
            self.source_field.blockSignals(False)
            self.star_rating.blockSignals(False)
    
    def _update_rating_label(self, rating: int) -> None:
        """
        Update the rating label text.
        
        Args:
            rating: Rating value (1-5)
        """
        if rating == 0:
            self.rating_label.setText("No rating")
        else:
            self.rating_label.setText(f"Rating: {rating}/5 stars")
    
    def _on_rating_changed(self, rating: int) -> None:
        """
        Handle rating change events.
        
        Args:
            rating: New rating value
        """
        self._update_rating_label(rating)
        self._on_field_changed()
    
    def _on_field_changed(self) -> None:
        """Handle field change events for dirty state tracking."""
        if self.current_model_id is not None:
            self.metadata_changed.emit(self.current_model_id)
    
    def _save_metadata(self) -> None:
        """Save the current metadata to the database."""
        if self.current_model_id is None:
            QMessageBox.warning(self, "Warning", "No model selected for editing")
            return
        
        try:
            self.logger.info(f"Saving metadata for model ID: {self.current_model_id}")
            
            # Validate input
            if not self._validate_input():
                return
            
            # Collect metadata
            metadata = {
                'title': self.title_field.text().strip(),
                'description': self.description_field.toPlainText().strip(),
                'keywords': self.keywords_field.text().strip(),
                'category': self.category_field.currentText().strip(),
                'source': self.source_field.text().strip(),
                'rating': self.star_rating.get_rating()
            }
            
            # Remove empty category
            if not metadata['category']:
                metadata['category'] = None
            
            # Save to database
            success = self._save_to_database(metadata)
            
            if success:
                # Update original metadata
                self.original_metadata = metadata.copy()
                
                # Reset dirty state
                self._reset_dirty_state()
                
                # Emit signal
                self.metadata_saved.emit(self.current_model_id)
                
                QMessageBox.information(self, "Success", "Metadata saved successfully")
                self.logger.info(f"Metadata saved for model ID: {self.current_model_id}")
            else:
                QMessageBox.warning(self, "Warning", "Failed to save metadata")
                
        except Exception as e:
            self.logger.error(f"Failed to save metadata: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to save metadata: {str(e)}")
    
    def _save_to_database(self, metadata: Dict[str, Any]) -> bool:
        """
        Save metadata to the database.
        
        Args:
            metadata: Metadata dictionary to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if metadata already exists
            existing_metadata = self.db_manager.get_model(self.current_model_id)
            
            if existing_metadata and existing_metadata.get('title') is not None:
                # Update existing metadata
                success = self.db_manager.update_model_metadata(
                    self.current_model_id,
                    **metadata
                )
            else:
                # Add new metadata
                self.db_manager.add_model_metadata(
                    self.current_model_id,
                    **metadata
                )
                success = True
            
            return success
            
        except Exception as e:
            self.logger.error(f"Database save failed: {str(e)}")
            return False
    
    def _validate_input(self) -> bool:
        """
        Validate the current input.
        
        Returns:
            True if valid, False otherwise
        """
        # Title is recommended but not required
        title = self.title_field.text().strip()
        if not title:
            reply = QMessageBox.question(
                self, "Missing Title",
                "The model title is empty. Do you want to continue?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.No:
                return False
        
        # Validate keywords format (comma-separated)
        keywords = self.keywords_field.text().strip()
        if keywords:
            # Check for valid comma-separated format
            keyword_list = [k.strip() for k in keywords.split(',')]
            if len(keyword_list) > 20:  # Reasonable limit
                QMessageBox.warning(self, "Too Many Keywords", 
                                  "Please limit the number of keywords to 20 or fewer.")
                return False
        
        # Validate rating
        rating = self.star_rating.get_rating()
        if not 0 <= rating <= 5:
            QMessageBox.warning(self, "Invalid Rating", 
                              "The rating must be between 0 and 5.")
            return False
        
        return True
    
    def _cancel_changes(self) -> None:
        """Cancel changes and reset form to original state."""
        if self.current_model_id is not None:
            self._reset_form()
    
    def _reset_form(self) -> None:
        """Reset the form to original metadata values."""
        if self.current_model_id is not None and self.original_metadata:
            self._load_metadata_fields(self.original_metadata)
            self._reset_dirty_state()
    
    def _clear_form(self) -> None:
        """Clear all form fields."""
        self.current_model_id = None
        
        # Clear model info
        self.model_filename_label.setText("No model selected")
        self.model_format_label.setText("-")
        self.model_size_label.setText("-")
        self.model_triangles_label.setText("-")
        
        # Clear metadata fields
        self.title_field.clear()
        self.description_field.clear()
        self.keywords_field.clear()
        self.category_field.setCurrentIndex(0)
        self.source_field.clear()
        self.star_rating.reset_rating()
        self.rating_label.setText("No rating")
        
        # Reset state
        self.original_metadata = {}
        self._reset_dirty_state()
    
    def _reset_dirty_state(self) -> None:
        """Reset the dirty state for form fields."""
        # This would be used to track if the form has been modified
        # For now, we'll just ensure the save button state is consistent
        pass
    
    def has_unsaved_changes(self) -> bool:
        """
        Check if there are unsaved changes.
        
        Returns:
            True if there are unsaved changes, False otherwise
        """
        if self.current_model_id is None or not self.original_metadata:
            return False
        
        # Compare current values with original metadata
        current_metadata = {
            'title': self.title_field.text().strip(),
            'description': self.description_field.toPlainText().strip(),
            'keywords': self.keywords_field.text().strip(),
            'category': self.category_field.currentText().strip() or None,
            'source': self.source_field.text().strip(),
            'rating': self.star_rating.get_rating()
        }
        
        return current_metadata != self.original_metadata
    
    def cleanup(self) -> None:
        """Clean up resources before widget destruction."""
        self.logger.info("Cleaning up metadata editor resources")
        
        # Clear current model
        self._clear_form()
        
        # Force garbage collection
        gc.collect()
        
        self.logger.info("Metadata editor cleanup completed")
    
    def closeEvent(self, event) -> None:
        """Handle widget close event."""
        if self.has_unsaved_changes():
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "There are unsaved changes. Do you want to save them?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Yes:
                self._save_metadata()
                if self.has_unsaved_changes():  # If save failed
                    event.ignore()
                    return
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
        
        self.cleanup()
        super().closeEvent(event)