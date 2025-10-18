"""
Model Loading and Management Module

This module handles the loading, parsing, and management of 3D model files,
including STL parsing, progress tracking, and model library integration.

Classes:
    ModelLoader: Main class for managing model loading operations
"""

import logging
from pathlib import Path
from typing import Optional, List

from PySide6.QtCore import QTimer, QSettings
from PySide6.QtWidgets import QMainWindow, QMessageBox

from src.core.logging_config import get_logger
from src.core.database_manager import get_database_manager
from src.parsers.stl_parser import STLParser, STLProgressCallback


class ModelLoader:
    """
    Manages model loading operations for the main window.

    This class handles file selection, model parsing, progress tracking,
    and integration with the model library and viewer components.
    """

    def __init__(self, main_window: QMainWindow, logger: Optional[logging.Logger] = None):
        """
        Initialize the model loader.

        Args:
            main_window: The main window instance
            logger: Optional logger instance for debugging
        """
        self.main_window = main_window
        self.logger = logger or get_logger(__name__)
        self.current_model_id = None

    def open_model(self) -> None:
        """Handle open model action."""
        self.logger.info("Opening model file dialog")

        # This would typically use QFileDialog, but for now we'll use a simplified approach
        # file_dialog = QFileDialog(self.main_window)
        # file_dialog.setFileMode(QFileDialog.ExistingFile)
        # file_dialog.setNameFilter(
        #     "3D Model Files (*.stl *.obj *.step *.stp *.mf3);;All Files (*)"
        # )

        # if file_dialog.exec_():
        #     file_path = file_dialog.selectedFiles()[0]
        #     self.logger.info(f"Selected model file: {file_path}")

        #     # Update status
        #     self.main_window.status_label.setText(f"Loading: {Path(file_path).name}")
        #     self.main_window.progress_bar.setVisible(True)
        #     self.main_window.progress_bar.setRange(0, 0)  # Indeterminate progress

        #     # Load the model using STL parser
        #     self._load_stl_model(file_path)

    def finish_model_loading(self, file_path: str, success: bool = True, error_message: str = "") -> None:
        """Finish model loading process."""
        filename = Path(file_path).name

        if success:
            if hasattr(self.main_window, 'status_label'):
                self.main_window.status_label.setText(f"Loaded: {filename}")
            self.logger.info(f"Model loaded successfully: {filename}")
        else:
            if hasattr(self.main_window, 'status_label'):
                self.main_window.status_label.setText(f"Failed to load: {filename}")
            self.logger.error(f"Failed to load model: {filename} - {error_message}")
            QMessageBox.warning(
                self.main_window,
                "Load Error",
                f"Failed to load model {filename}:\n{error_message}"
            )

        if hasattr(self.main_window, 'progress_bar'):
            self.main_window.progress_bar.setVisible(False)

        # Emit signal
        if hasattr(self.main_window, 'model_loaded'):
            self.main_window.model_loaded.emit(file_path)

    def load_stl_model(self, file_path: str) -> None:
        """
        Load an STL model using the STL parser and display it in the viewer.

        Args:
            file_path: Path to the STL file to load
        """
        try:
            # Create STL parser
            parser = STLParser()

            # Create progress callback
            progress_callback = STLProgressCallback(
                callback_func=lambda progress, message: self.update_loading_progress(progress, message)
            )

            # Parse the file
            model = parser.parse_file(file_path, progress_callback)

            # Load model into viewer if available
            if hasattr(self.main_window, 'viewer_widget') and hasattr(self.main_window.viewer_widget, 'load_model'):
                success = self.main_window.viewer_widget.load_model(model)
                self.finish_model_loading(file_path, success, "" if success else "Failed to load model into viewer")
            else:
                self.finish_model_loading(file_path, False, "3D viewer not available")

        except Exception as e:
            self.finish_model_loading(file_path, False, str(e))

    def update_loading_progress(self, progress_percent: float, message: str) -> None:
        """
        Update loading progress in the UI.

        Args:
            progress_percent: Progress percentage (0-100)
            message: Progress message
        """
        if hasattr(self.main_window, 'progress_bar'):
            self.main_window.progress_bar.setRange(0, 100)
            self.main_window.progress_bar.setValue(int(progress_percent))
        if message and hasattr(self.main_window, 'status_label'):
            self.main_window.status_label.setText(f"Loading: {message}")

    def on_model_loaded(self, info: str) -> None:
        """
        Handle model loaded signal from viewer widget.

        Args:
            info: Information about the loaded model
        """
        self.logger.info(f"Viewer model loaded: {info}")
        # Reset save view button when new model is loaded
        try:
            if hasattr(self.main_window, 'viewer_widget') and hasattr(self.main_window.viewer_widget, 'reset_save_view_button'):
                self.main_window.viewer_widget.reset_save_view_button()
        except Exception as e:
            self.logger.warning(f"Failed to reset save view button: {e}")

        # Attempt to apply last-used material species
        try:
            settings = QSettings()
            last_species = settings.value('material/last_species', '', type=str)
            if last_species:
                if hasattr(self.main_window, "material_manager") and self.main_window.material_manager:
                    species_list = self.main_window.material_manager.get_species_list()
                    if last_species in species_list:
                        self.logger.info(f"Applying last material species on load: {last_species}")
                        self._apply_material_species(last_species)
                    else:
                        self.logger.warning(f"Last material '{last_species}' not found; skipping reapply")
        except Exception as e:
            self.logger.warning(f"Failed to reapply last material species: {e}")

        # Update model properties dock if it exists
        if hasattr(self.main_window, 'properties_dock'):
            properties_widget = self.main_window.properties_dock.widget()
            if isinstance(properties_widget, QTextEdit):
                if hasattr(self.main_window, 'viewer_widget') and hasattr(self.main_window.viewer_widget, 'get_model_info'):
                    model_info = self.main_window.viewer_widget.get_model_info()
                    if model_info:
                        info_text = (
                            "Model Properties\n\n"
                            f"Triangles: {model_info['triangle_count']:,}\n"
                            f"Vertices: {model_info['vertex_count']:,}\n"
                            f"Dimensions: {model_info['dimensions'][0]:.2f} x "
                            f"{model_info['dimensions'][1]:.2f} x "
                            f"{model_info['dimensions'][2]:.2f}\n"
                            f"File size: {model_info['file_size'] / 1024:.1f} KB\n"
                            f"Format: {model_info['format']}\n"
                            f"Parse time: {model_info['parsing_time']:.3f} s"
                        )
                        properties_widget.setPlainText(info_text)

    def on_performance_updated(self, fps: float) -> None:
        """
        Handle performance update signal from viewer widget.

        Args:
            fps: Current frames per second
        """
        # Performance updates are no longer displayed in the status bar
        pass

    def on_model_selected(self, model_id: int) -> None:
        """
        Handle model selection from the model library.

        Args:
            model_id: ID of the selected model
        """
        try:
            # Get model information from database
            db_manager = get_database_manager()
            model = db_manager.get_model(model_id)

            if model:
                self.logger.info(f"Model selected from library: {model['filename']} (ID: {model_id})")
                if hasattr(self.main_window, 'model_selected'):
                    self.main_window.model_selected.emit(model_id)

                # Load metadata in the metadata editor
                if hasattr(self.main_window, 'metadata_editor'):
                    self.main_window.metadata_editor.load_model_metadata(model_id)

                # Update view count
                db_manager.increment_view_count(model_id)
            else:
                self.logger.warning(f"Model with ID {model_id} not found in database")

        except Exception as e:
            self.logger.error(f"Failed to handle model selection: {str(e)}")

    def on_model_double_clicked(self, model_id: int) -> None:
        """
        Handle model double-click from the model library.

        Args:
            model_id: ID of the double-clicked model
        """
        try:
            # Get model information from database
            db_manager = get_database_manager()
            model = db_manager.get_model(model_id)

            if model:
                file_path = model['file_path']
                self.logger.info(f"Loading model from library: {file_path}")

                # Update status
                filename = Path(file_path).name
                if hasattr(self.main_window, 'status_label'):
                    self.main_window.status_label.setText(f"Loading: {filename}")
                if hasattr(self.main_window, 'progress_bar'):
                    self.main_window.progress_bar.setVisible(True)
                    self.main_window.progress_bar.setRange(0, 0)  # Indeterminate progress

                # Store model ID for save view functionality
                self.current_model_id = model_id

                # Load the model using STL parser
                self.load_stl_model(file_path)

                # After model loads, restore saved camera orientation if available
                QTimer.singleShot(500, lambda: self._restore_saved_camera(model_id))
            else:
                self.logger.warning(f"Model with ID {model_id} not found in database")

        except Exception as e:
            self.logger.error(f"Failed to handle model double-click: {str(e)}")

    def on_models_added(self, model_ids: List[int]) -> None:
        """
        Handle models added to the library.

        Args:
            model_ids: List of IDs of added models
        """
        self.logger.info(f"Added {len(model_ids)} models to library")

        # Update status
        if model_ids and hasattr(self.main_window, 'status_label'):
            self.main_window.status_label.setText(f"Added {len(model_ids)} models to library")

            # Start background hasher to process new models
            self._start_background_hasher()

            # Clear status after a delay
            QTimer.singleShot(3000, lambda: self.main_window.status_label.setText("Ready"))

    def _apply_material_species(self, species_name: str) -> None:
        """Apply selected material species to the current viewer actor."""
        # This method would need to be implemented or connected to the main window's method
        if hasattr(self.main_window, '_apply_material_species'):
            self.main_window._apply_material_species(species_name)

    def _restore_saved_camera(self, model_id: int) -> None:
        """Restore saved camera orientation for a model."""
        try:
            db_manager = get_database_manager()
            camera_data = db_manager.get_camera_orientation(model_id)

            if camera_data and hasattr(self.main_window, 'viewer_widget') and hasattr(self.main_window.viewer_widget, 'renderer'):
                camera = self.main_window.viewer_widget.renderer.GetActiveCamera()
                if camera:
                    # Restore camera position, focal point, and view up
                    camera.SetPosition(
                        camera_data['camera_position_x'],
                        camera_data['camera_position_y'],
                        camera_data['camera_position_z']
                    )
                    camera.SetFocalPoint(
                        camera_data['camera_focal_x'],
                        camera_data['camera_focal_y'],
                        camera_data['camera_focal_z']
                    )
                    camera.SetViewUp(
                        camera_data['camera_view_up_x'],
                        camera_data['camera_view_up_y'],
                        camera_data['camera_view_up_z']
                    )

                    # Update clipping range and render
                    self.main_window.viewer_widget.renderer.ResetCameraClippingRange()
                    self.main_window.viewer_widget.vtk_widget.GetRenderWindow().Render()

                    self.logger.info(f"Restored saved camera view for model ID {model_id}")
                    if hasattr(self.main_window, 'status_label'):
                        self.main_window.status_label.setText("Restored saved view")
                        QTimer.singleShot(2000, lambda: self.main_window.status_label.setText("Ready"))
            else:
                self.logger.debug(f"No saved camera view for model ID {model_id}")

        except Exception as e:
            self.logger.warning(f"Failed to restore saved camera: {e}")

    def _start_background_hasher(self) -> None:
        """Start background hasher to process new models."""
        # This would need to be connected to the main window's background hasher
        if hasattr(self.main_window, '_start_background_hasher'):
            self.main_window._start_background_hasher()


# Convenience function for easy model loading setup
def setup_model_loading(main_window: QMainWindow, logger: Optional[logging.Logger] = None) -> ModelLoader:
    """
    Convenience function to set up model loading for a main window.

    Args:
        main_window: The main window to set up model loading for
        logger: Optional logger instance

    Returns:
        ModelLoader instance for further model loading operations
    """
    return ModelLoader(main_window, logger)
