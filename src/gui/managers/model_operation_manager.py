"""
Model Operation Manager for MainWindow.

Handles model loading, selection, editing, and import operations.
Extracted from MainWindow to reduce monolithic class size.
"""

import logging
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMainWindow, QMessageBox

from src.core.database_manager import get_database_manager


class ModelOperationManager:
    """Manages model operations and interactions."""

    def __init__(self, main_window: QMainWindow, logger: logging.Logger):
        """
        Initialize the model operation manager.

        Args:
            main_window: The main window instance
            logger: Logger instance
        """
        self.main_window = main_window
        self.logger = logger

    def on_model_loaded(self, info: str) -> None:
        """Handle model loaded signal from viewer."""
        try:
            self.main_window.activity_logger.info(f"Model loaded: {info}")
            self.main_window.status_label.setText(f"Model loaded: {info}")
            self.main_window.progress_bar.setVisible(False)

            # Clear status after a delay
            QTimer.singleShot(3000, lambda: self.main_window.status_label.setText("Ready"))
        except Exception as e:
            self.logger.error(f"Failed to handle model loaded signal: {e}")

    def on_model_double_clicked(self, model_id: int) -> None:
        """Handle model double-click from the model library."""
        try:
            db_manager = get_database_manager()
            model = db_manager.get_model(model_id)

            if model:
                file_path = model["file_path"]
                self.logger.info(f"Loading model from library: {file_path}")

                # Update status
                filename = Path(file_path).name
                self.main_window.status_label.setText(f"Loading: {filename}")
                self.main_window.progress_bar.setVisible(True)
                self.main_window.progress_bar.setRange(0, 0)

                # Store model ID for save view functionality
                self.main_window.current_model_id = model_id

                # Load the model
                if hasattr(self.main_window, "model_loader_manager"):
                    self.main_window.model_loader_manager.load_stl_model(file_path)

                # Restore saved camera orientation if available
                QTimer.singleShot(500, lambda: self._restore_saved_camera(model_id))
            else:
                self.logger.warning(f"Model with ID {model_id} not found in database")

        except Exception as e:
            self.logger.error(f"Failed to handle model double-click: {str(e)}")

    def on_models_added(self, model_ids: List[int]) -> None:
        """Handle models added to the library."""
        try:
            self.logger.info(f"Added {len(model_ids)} models to library")

            if model_ids:
                self.main_window.status_label.setText(
                    f"Added {len(model_ids)} models to library"
                )

                # Start background hasher to process new models
                if hasattr(self.main_window, "_start_background_hasher"):
                    self.main_window._start_background_hasher()

                # Clear status after a delay
                QTimer.singleShot(3000, lambda: self.main_window.status_label.setText("Ready"))

        except Exception as e:
            self.logger.error(f"Failed to handle models added: {e}")

    def on_model_selected(self, model_id: int) -> None:
        """Handle model selection from the model library."""
        try:
            # Store the current model ID
            self.main_window.current_model_id = model_id

            # Enable the Edit Model action
            if hasattr(self.main_window, "menu_manager"):
                if hasattr(self.main_window.menu_manager, "edit_model_action"):
                    self.main_window.menu_manager.edit_model_action.setEnabled(True)

            if hasattr(self.main_window, "toolbar_manager"):
                if hasattr(self.main_window.toolbar_manager, "edit_model_action"):
                    self.main_window.toolbar_manager.edit_model_action.setEnabled(True)

            # Update project details widget
            if hasattr(self.main_window, "project_details_widget"):
                db_manager = get_database_manager()
                model_data = db_manager.get_model(model_id)
                if model_data:
                    self.main_window.project_details_widget.set_model(model_data)

            # Synchronize metadata tab to selected model
            self.sync_metadata_to_selected_model(model_id)

            self.logger.debug(f"Model selected: {model_id}")

        except Exception as e:
            self.logger.error(f"Failed to handle model selection: {e}")

    def sync_metadata_to_selected_model(self, model_id: int) -> None:
        """Synchronize the metadata tab to display the selected model's metadata."""
        try:
            # Check if metadata editor exists
            if not hasattr(self.main_window, "metadata_editor"):
                self.logger.debug(f"Metadata editor not available for model {model_id}")
                return

            if self.main_window.metadata_editor is None:
                return

            # Load metadata for the selected model
            self.main_window.metadata_editor.load_model_metadata(model_id)
            self.logger.debug(f"Metadata synchronized for model {model_id}")

            # Switch to metadata tab to show the loaded metadata
            if hasattr(self.main_window, "metadata_tabs") and self.main_window.metadata_tabs:
                self.main_window.metadata_tabs.setCurrentIndex(0)
                self.logger.debug(f"Switched to Metadata tab for model {model_id}")

        except Exception as e:
            self.logger.warning(
                f"Failed to synchronize metadata for model {model_id}: {e}"
            )

    def edit_model(self, model_id: Optional[int] = None) -> None:
        """Edit the selected model's metadata."""
        try:
            if model_id is None:
                model_id = getattr(self.main_window, "current_model_id", None)

            if model_id is None:
                QMessageBox.warning(self.main_window, "No Model", "Please select a model first")
                return

            db_manager = get_database_manager()
            model = db_manager.get_model(model_id)

            if not model:
                QMessageBox.warning(self.main_window, "Error", "Model not found")
                return

            # Switch to metadata tab
            if hasattr(self.main_window, "metadata_tabs"):
                self.main_window.metadata_tabs.setCurrentIndex(0)

            self.logger.info(f"Editing model {model_id}")

        except Exception as e:
            self.logger.error(f"Failed to edit model: {e}")
            QMessageBox.critical(self.main_window, "Error", f"Failed to edit model: {e}")

    def import_models(self) -> None:
        """Import models from file system."""
        try:
            if hasattr(self.main_window, "model_library_widget"):
                self.main_window.model_library_widget.show_import_dialog()
            else:
                self.logger.warning("Model library widget not available")
        except Exception as e:
            self.logger.error(f"Failed to import models: {e}")

    def _restore_saved_camera(self, model_id: int) -> None:
        """Restore saved camera orientation for a model."""
        try:
            if hasattr(self.main_window, "_restore_saved_camera"):
                self.main_window._restore_saved_camera(model_id)
        except Exception as e:
            self.logger.debug(f"Failed to restore saved camera: {e}")

