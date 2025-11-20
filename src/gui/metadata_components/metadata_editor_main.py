"""
Metadata editor widget for 3D models.

Provides a comprehensive metadata editing interface with form fields,
star rating system, category management, and database integration.
"""

import gc
from pathlib import Path
from typing import Dict, Optional, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QPushButton,
    QLabel,
    QFrame,
    QScrollArea,
    QMessageBox,
    QStyle,
)

from src.core.logging_config import get_logger
from src.core.database_manager import get_database_manager
from src.core.import_thumbnail_service import ImportThumbnailService
from src.core.fast_hasher import FastHasher
from src.gui.theme import SPACING_8, SPACING_12, SPACING_16
from .star_rating_widget import StarRatingWidget
from .thumbnail_inspector import ThumbnailInspectorLabel


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

    def __init__(self, parent: Optional[QWidget] = None) -> None:
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

    def _std_icon(self, standard_pixmap) -> QIcon:
        """Return a native Qt icon for the given standard pixmap."""
        try:
            style = self.style()
            return style.standardIcon(standard_pixmap)
        except Exception:
            return QIcon()

    def _init_ui(self) -> None:
        """Initialize the user interface layout."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(SPACING_16, SPACING_16, SPACING_16, SPACING_16)
        main_layout.setSpacing(SPACING_12)

        # Create scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Create content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(SPACING_16)

        # Create model info group
        self._create_model_info_group(content_layout)

        # Create preview image group
        self._create_preview_image_group(content_layout)

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
        group_layout.setContentsMargins(SPACING_12, SPACING_12, SPACING_12, SPACING_12)
        try:
            group_layout.setHorizontalSpacing(SPACING_12)
            group_layout.setVerticalSpacing(SPACING_8)
        except Exception:
            pass

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

    def _create_preview_image_group(self, parent_layout: QVBoxLayout) -> None:
        """Create the preview image group."""
        group = QGroupBox("Preview Image")
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(SPACING_12, SPACING_12, SPACING_12, SPACING_12)
        group_layout.setSpacing(SPACING_8)

        # Preview image label with double-click inspector
        self.preview_image_label = ThumbnailInspectorLabel()
        self.preview_image_label.setAlignment(Qt.AlignCenter)
        self.preview_image_label.setMinimumHeight(200)
        self.preview_image_label.setText(
            "No preview available\n\nClick 'Generate Preview' in the library\ncontext menu to create one\n\n(Double-click to inspect at full resolution)"
        )
        group_layout.addWidget(self.preview_image_label)

        # Preview actions
        preview_button_layout = QHBoxLayout()

        self.generate_preview_button = QPushButton("Generate Preview")
        self.generate_preview_button.setIcon(self._std_icon(QStyle.SP_DesktopIcon))
        self.generate_preview_button.clicked.connect(self._generate_preview_for_current_model)
        preview_button_layout.addWidget(self.generate_preview_button)

        self.run_ai_analysis_button = QPushButton("Run AI Analysis")
        self.run_ai_analysis_button.setIcon(self._std_icon(QStyle.SP_MediaPlay))
        self.run_ai_analysis_button.clicked.connect(self._run_ai_analysis)
        self.run_ai_analysis_button.setToolTip(
            "Analyze the preview image with AI to generate metadata"
        )
        preview_button_layout.addWidget(self.run_ai_analysis_button)

        preview_button_layout.addStretch()
        group_layout.addLayout(preview_button_layout)

        parent_layout.addWidget(group)

    def _create_metadata_form(self, parent_layout: QVBoxLayout) -> None:
        """Create the metadata form fields."""
        group = QGroupBox("Metadata")
        group_layout = QFormLayout(group)
        group_layout.setContentsMargins(SPACING_12, SPACING_12, SPACING_12, SPACING_12)
        try:
            group_layout.setHorizontalSpacing(SPACING_12)
            group_layout.setVerticalSpacing(SPACING_8)
        except Exception:
            pass

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
        group_layout.setContentsMargins(SPACING_12, SPACING_12, SPACING_12, SPACING_12)
        group_layout.setSpacing(SPACING_8)

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
        button_layout.setSpacing(SPACING_8)

        # Save button
        self.save_button = QPushButton("Save")
        self.save_button.setDefault(True)
        self.save_button.setIcon(self._std_icon(QStyle.SP_DialogSaveButton))
        button_layout.addWidget(self.save_button)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setIcon(self._std_icon(QStyle.SP_DialogCancelButton))
        button_layout.addWidget(self.cancel_button)

        # Reset button
        self.reset_button = QPushButton("Reset")
        self.reset_button.setIcon(self._std_icon(QStyle.SP_DialogResetButton))
        button_layout.addWidget(self.reset_button)

        parent_layout.addWidget(button_frame)

    def _apply_styling(self) -> None:
        """Apply styling (no-op - qt-material handles all styling)."""

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
                self.category_field.addItem(category["name"])

            self.logger.debug("Loaded %s categories", len(self.categories))

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to load categories: %s", str(e))

    def _ensure_category_exists(self, name: str) -> bool:
        """Ensure a category exists in the database, adding it if missing.

        Returns True if a new category was added.
        """
        try:
            clean = name.strip()
            if not clean:
                return False
            existing = {c.get("name", "").lower() for c in self.categories or []}
            if clean.lower() in existing:
                return False
            self.db_manager.add_category(clean)
            self.logger.info("Added new category from metadata editor: %s", clean)
            return True
        except Exception as e:
            self.logger.warning("Failed to add category '%s': %s", name, e)
            return False

    def load_model_metadata(self, model_id: int) -> None:
        """
        Load metadata for a specific model.

        Args:
            model_id: ID of the model to load metadata for
        """
        try:
            self.logger.info("Loading metadata for model ID: %s", model_id)

            # Get model information from database
            model = self.db_manager.get_model(model_id)

            if not model:
                self.logger.warning("Model with ID %s not found", model_id)
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
                "title": model.get("title", ""),
                "description": model.get("description", ""),
                "keywords": model.get("keywords", ""),
                "category": model.get("category", ""),
                "source": model.get("source", ""),
                "rating": model.get("rating", 0),
            }

            # Load preview image
            self._load_preview_image(model_id)

            # Reset dirty state
            self._reset_dirty_state()

            self.logger.info("Metadata loaded for model: %s", model["filename"])

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            # Silently ignore unavailable or invalid metadata; clear form and continue
            self.logger.warning("Failed to load metadata for model %s: {str(e)}", model_id)
            try:
                self._clear_form()
            except Exception:
                pass
            return

    def _update_model_info(self, model: Dict[str, Any]) -> None:
        """
        Update the model information display.

        Args:
            model: Model information dictionary
        """
        self.model_filename_label.setText(model.get("filename", "Unknown"))
        fmt = model.get("format") or "Unknown"
        self.model_format_label.setText(str(fmt).upper())

        # Format file size
        file_size = model.get("file_size", 0)
        if file_size > 1024 * 1024:
            size_text = f"{file_size / (1024 * 1024):.1f} MB"
        elif file_size > 1024:
            size_text = f"{file_size / 1024:.1f} KB"
        else:
            size_text = f"{file_size} B"
        self.model_size_label.setText(size_text)

        # Triangle count
        triangle_count = model.get("triangle_count") or 0
        self.model_triangles_label.setText(f"{int(triangle_count):,}")

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
            self.title_field.setText(model.get("title", ""))
            self.description_field.setPlainText(model.get("description", ""))
            self.keywords_field.setText(model.get("keywords", ""))
            self.source_field.setText(model.get("source", ""))

            # Load category
            category = model.get("category", "")
            if category:
                index = self.category_field.findText(category)
                if index >= 0:
                    self.category_field.setCurrentIndex(index)
                else:
                    self.category_field.setCurrentText(category)
            else:
                self.category_field.setCurrentIndex(0)

            # Load rating (coerce None or invalid values to 0 without errors)
            rating_val = model.get("rating", 0)
            try:
                rating_int = int(rating_val) if rating_val is not None else 0
            except Exception:
                rating_int = 0
            if 1 <= rating_int <= 5:
                self.star_rating.set_rating(rating_int)
            else:
                self.star_rating.reset_rating()
            self._update_rating_label(rating_int)

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
            self.logger.info("Saving metadata for model ID: %s", self.current_model_id)

            # Validate input
            if not self._validate_input():
                return

            # Collect metadata
            metadata = {
                "title": self.title_field.text().strip(),
                "description": self.description_field.toPlainText().strip(),
                "keywords": self.keywords_field.text().strip(),
                "category": self.category_field.currentText().strip(),
                "source": self.source_field.text().strip(),
                "rating": self.star_rating.get_rating(),
            }

            # Remove empty category
            if not metadata["category"]:
                metadata["category"] = None
            else:
                # Ensure category exists in DB; add if new
                added = self._ensure_category_exists(metadata["category"])
                if added:
                    # Refresh local list and combo to include the newly added category
                    self._load_categories()
                    idx = self.category_field.findText(metadata["category"])
                    if idx >= 0:
                        self.category_field.setCurrentIndex(idx)

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
                self.logger.info("Metadata saved for model ID: %s", self.current_model_id)
            else:
                QMessageBox.warning(self, "Warning", "Failed to save metadata")

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to save metadata: %s", str(e))
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

            if existing_metadata and existing_metadata.get("title") is not None:
                # Update existing metadata
                success = self.db_manager.update_model_metadata(self.current_model_id, **metadata)
            else:
                # Add new metadata
                self.db_manager.add_model_metadata(self.current_model_id, **metadata)
                success = True

            return success

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Database save failed: %s", str(e))
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
                self,
                "Missing Title",
                "The model title is empty. Do you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return False

        # Validate keywords format (comma-separated)
        keywords = self.keywords_field.text().strip()
        if keywords:
            # Check for valid comma-separated format
            keyword_list = [k.strip() for k in keywords.split(",")]
            if len(keyword_list) > 20:  # Reasonable limit
                QMessageBox.warning(
                    self,
                    "Too Many Keywords",
                    "Please limit the number of keywords to 20 or fewer.",
                )
                return False

        # Validate rating
        rating = self.star_rating.get_rating()
        if not 0 <= rating <= 5:
            QMessageBox.warning(self, "Invalid Rating", "The rating must be between 0 and 5.")
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

        # Clear preview image
        self._clear_preview_image()

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
            "title": self.title_field.text().strip(),
            "description": self.description_field.toPlainText().strip(),
            "keywords": self.keywords_field.text().strip(),
            "category": self.category_field.currentText().strip() or None,
            "source": self.source_field.text().strip(),
            "rating": self.star_rating.get_rating(),
        }

        return current_metadata != self.original_metadata

    def _load_preview_image(self, model_id: int) -> None:
        """Load and display the preview image for the current model."""
        try:
            # Get model information
            model = self.db_manager.get_model(model_id)
            if not model:
                self._clear_preview_image()
                return

            # First try to use thumbnail_path from database (fast path)
            thumbnail_path_str = model.get("thumbnail_path")
            if thumbnail_path_str:
                thumbnail_path = Path(thumbnail_path_str)
                if thumbnail_path.exists():
                    # Load and display the thumbnail
                    pixmap = QPixmap(str(thumbnail_path))
                    if not pixmap.isNull():
                        # Scale the image to fit the label while maintaining aspect ratio
                        scaled_pixmap = pixmap.scaled(
                            self.preview_image_label.size(),
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation,
                        )
                        # Use set_thumbnail to store both scaled and full-resolution versions
                        self.preview_image_label.set_thumbnail(scaled_pixmap, str(thumbnail_path))
                        self.preview_image_label.setText("")  # Clear any placeholder text
                        self.logger.debug("Loaded preview image for model %s", model_id)
                        return

            # Fallback: Try to find thumbnail by hashing the file (slow path)
            model_path = model.get("file_path")
            if not model_path or not Path(model_path).exists():
                self._clear_preview_image()
                return

            # Get file hash from database first, or compute it
            file_hash = model.get("file_hash")
            if not file_hash:
                hasher = FastHasher()
                hash_result = hasher.hash_file(model_path)
                file_hash = hash_result.hash_value if hash_result.success else None

            if not file_hash:
                self._clear_preview_image()
                return

            thumbnail_service = ImportThumbnailService()
            thumbnail_path = thumbnail_service.get_thumbnail_path(file_hash)

            if thumbnail_path and thumbnail_path.exists():
                # Load and display the thumbnail
                pixmap = QPixmap(str(thumbnail_path))
                if not pixmap.isNull():
                    # Scale the image to fit the label while maintaining aspect ratio
                    scaled_pixmap = pixmap.scaled(
                        self.preview_image_label.size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                    # Use set_thumbnail to store both scaled and full-resolution versions
                    self.preview_image_label.set_thumbnail(scaled_pixmap, str(thumbnail_path))
                    self.preview_image_label.setText("")  # Clear any placeholder text
                    self.logger.debug("Loaded preview image for model %s", model_id)
                else:
                    self._clear_preview_image()
            else:
                self._clear_preview_image()

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to load preview image for model %s: %s", model_id, e)
            self._clear_preview_image()

    def _clear_preview_image(self) -> None:
        """Clear the preview image display."""
        self.preview_image_label.clear()
        self.preview_image_label.setText(
            "No preview available\n\nClick 'Generate Preview' in the library\ncontext menu to create one"
        )

    def _generate_preview_for_current_model(self) -> None:
        """Generate preview image for the currently loaded model."""
        if self.current_model_id is None:
            QMessageBox.warning(self, "Warning", "No model selected")
            return

        try:
            self.logger.info("Generating preview for model ID: %s", self.current_model_id)

            # Get model information
            model = self.db_manager.get_model(self.current_model_id)
            if not model:
                QMessageBox.warning(self, "Error", "Model not found in database")
                return

            model_path = model.get("file_path")
            if not model_path or not Path(model_path).exists():
                QMessageBox.warning(self, "Error", "Model file not found on disk")
                return

            # Get file hash
            hasher = FastHasher()
            hash_result = hasher.hash_file(model_path)
            file_hash = hash_result.hash_value if hash_result.success else None

            if not file_hash:
                QMessageBox.warning(self, "Error", "Failed to compute file hash")
                return

            # Load thumbnail settings from preferences
            from src.core.application_config import ApplicationConfig
            from PySide6.QtCore import QSettings
            from src.gui.thumbnail_generation_coordinator import ThumbnailGenerationCoordinator

            config = ApplicationConfig.get_default()
            settings = QSettings()

            # Get current thumbnail preferences
            bg_image = settings.value(
                "thumbnail/background_image", config.thumbnail_bg_image, type=str
            )
            material = settings.value("thumbnail/material", config.thumbnail_material, type=str)
            bg_color = settings.value(
                "thumbnail/background_color", config.thumbnail_bg_color, type=str
            )

            # Use background image if set, otherwise use background color
            background = bg_image if bg_image else bg_color

            # Generate thumbnail using coordinator with dedicated window
            coordinator = ThumbnailGenerationCoordinator(parent=self)

            # Save thumbnail path to database as soon as it is generated
            def on_thumbnail_generated(file_path: str, thumbnail_path: str) -> None:
                model = self.db_manager.get_model(self.current_model_id)
                if not model:
                    return
                if model.get("file_path") != file_path:
                    return
                self.db_manager.update_model_thumbnail(self.current_model_id, thumbnail_path)
                self.logger.info(
                    "Saved thumbnail path to database for model %s: %s",
                    self.current_model_id,
                    thumbnail_path,
                )

            coordinator.thumbnail_generated.connect(on_thumbnail_generated)

            # Connect completion signal to refresh display
            def on_generation_completed() -> None:
                self.logger.info("Preview generated for model %s", self.current_model_id)
                # Reload the preview image (will now use the stored thumbnail path)
                self._load_preview_image(self.current_model_id)
                QMessageBox.information(self, "Success", "Preview generated successfully!")

            coordinator.generation_completed.connect(on_generation_completed)

            # Generate thumbnail
            coordinator.generate_thumbnails(
                file_info_list=[(model_path, file_hash)],
                background=background,
                material=material,
                force_regenerate=True,
            )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            error_msg = f"Exception during preview generation: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            QMessageBox.critical(self, "Error", error_msg)

    def _run_ai_analysis(self) -> None:
        """Run AI analysis on the preview image to generate metadata."""
        if self.current_model_id is None:
            QMessageBox.warning(self, "Warning", "No model selected")
            return

        try:
            # Get the thumbnail path
            model = self.db_manager.get_model(self.current_model_id)
            if not model:
                QMessageBox.warning(self, "Error", "Model not found in database")
                return

            thumbnail_path = model.get("thumbnail_path")

            # If the database does not yet know about the thumbnail, fall back to
            # the hash-based thumbnail location and self-heal the database entry.
            if not thumbnail_path or not Path(thumbnail_path).exists():
                file_path = model.get("file_path")
                file_hash = model.get("file_hash")

                if file_path and not file_hash:
                    hasher = FastHasher()
                    hash_result = hasher.hash_file(file_path)
                    file_hash = hash_result.hash_value if hash_result.success else None

                if file_hash:
                    thumbnail_service = ImportThumbnailService()
                    thumb_path = thumbnail_service.get_thumbnail_path(file_hash)
                    if thumb_path and thumb_path.exists():
                        thumbnail_path = str(thumb_path)
                        self.db_manager.update_model_thumbnail(
                            self.current_model_id, thumbnail_path
                        )

            if not thumbnail_path or not Path(thumbnail_path).exists():
                QMessageBox.warning(
                    self,
                    "No Preview",
                    "Please generate a preview image first before running AI analysis.",
                )
                return

            # Get AI service from parent window
            ai_service = self._get_ai_service()
            if not ai_service:
                QMessageBox.warning(
                    self,
                    "AI Service Unavailable",
                    "AI description service is not available. Please configure an AI provider in settings.",
                )
                return

            # Check if any provider is available and configured
            if not ai_service.providers:
                QMessageBox.warning(
                    self,
                    "No AI Providers Available",
                    "No AI providers are configured. Please set an API key environment variable:\n"
                    "- GOOGLE_API_KEY for Gemini\n"
                    "- OPENAI_API_KEY for OpenAI\n"
                    "- ANTHROPIC_API_KEY for Anthropic",
                )
                return

            # Use the first available provider if current_provider is not set
            if not ai_service.current_provider:
                ai_service.current_provider = next(iter(ai_service.providers.values()))
                self.logger.info(
                    "Set current provider to: %s", list(ai_service.providers.keys())[0]
                )

            # Check if provider is configured
            if not ai_service.current_provider.is_configured():
                QMessageBox.warning(
                    self,
                    "AI Provider Not Configured",
                    "The selected AI provider is not properly configured. Please check your API key settings.",
                )
                return

            # Disable button during analysis
            self.run_ai_analysis_button.setEnabled(False)
            self.run_ai_analysis_button.setText("Analyzing...")

            # Run analysis
            self.logger.info("Running AI analysis on preview for model %s", self.current_model_id)
            result = ai_service.analyze_image(thumbnail_path)

            # Apply results to metadata
            self._apply_ai_results(result)

            self.logger.info("AI analysis completed for model %s", self.current_model_id)
            QMessageBox.information(
                self,
                "Analysis Complete",
                "AI analysis completed successfully. Metadata has been updated.",
            )

        except ValueError as e:
            QMessageBox.warning(self, "Configuration Error", str(e))
            self.logger.warning("AI analysis configuration error: %s", e)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            error_msg = f"AI analysis failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            QMessageBox.critical(self, "Error", error_msg)
        finally:
            # Re-enable button
            self.run_ai_analysis_button.setEnabled(True)
            self.run_ai_analysis_button.setText("Run AI Analysis")

    def _get_ai_service(self) -> None:
        """Get the AI description service from the parent window."""
        try:
            # Try to get from parent window
            parent = self.parent()
            while parent:
                if hasattr(parent, "ai_service"):
                    return parent.ai_service
                parent = parent.parent()

            # If not found in parent hierarchy, try to create one
            from src.gui.services.ai_description_service import AIDescriptionService

            return AIDescriptionService()
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to get AI service: %s", e)
            return None

    def _apply_ai_results(self, result: Dict[str, Any]) -> None:
        """Apply AI analysis results to metadata fields."""
        try:
            # Update title if provided
            if "title" in result and result["title"]:
                self.title_field.setText(result["title"])
                self.logger.info("Updated title: %s", result["title"])

            # Update description if provided
            if "description" in result and result["description"]:
                self.description_field.setPlainText(result["description"])
                self.logger.info("Updated description: %s...", result["description"][:50])

            # Update taxonomy (category + keywords) if provided
            if "metadata_keywords" in result and result["metadata_keywords"]:
                from src.core.taxonomy_utils import split_category_and_keywords

                category, keywords = split_category_and_keywords(result["metadata_keywords"])

                # Update category if we inferred one
                if category:
                    try:
                        self.category_field.setCurrentText(category)
                        self.logger.info("Updated category: %s", category)
                    except Exception:
                        # Category is a user-facing hint; failure here should
                        # not prevent keyword updates.
                        self.logger.warning("Failed to update category field", exc_info=True)

                keywords_str = ", ".join(keywords)
                self.keywords_field.setText(keywords_str)
                self.logger.info("Updated keywords: %s", keywords_str)

            # Mark as changed
            self.metadata_changed.emit(self.current_model_id)
            self.logger.info("Applied AI analysis results to model %s", self.current_model_id)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to apply AI results: %s", e)
            raise

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
                self,
                "Unsaved Changes",
                "There are unsaved changes. Do you want to save them?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Cancel,
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
