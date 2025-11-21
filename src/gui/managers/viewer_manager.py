"""
Viewer Manager for MainWindow.

Handles viewer and camera operations.
Extracted from MainWindow to reduce monolithic class size.
"""

import logging

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMainWindow, QMessageBox


class ViewerManager:
    """Manages viewer and camera operations."""

    def __init__(self, main_window: QMainWindow, logger: logging.Logger):
        """
        Initialize the viewer manager.

        Args:
            main_window: The main window instance
            logger: Logger instance
        """
        self.main_window = main_window
        self.logger = logger

    def setup_viewer_managers(self) -> None:
        """Set up viewer-related managers using native Qt integration."""
        try:
            from src.core.database_manager import get_database_manager
            from src.gui.material_manager import MaterialManager
            from src.gui.lighting_manager import LightingManager

            # Material manager
            try:
                self.main_window.material_manager = MaterialManager(
                    get_database_manager()
                )
            except Exception as e:
                self.main_window.material_manager = None
                self.logger.warning("MaterialManager unavailable: %s", e)

            # Lighting manager
            try:
                self.main_window.lighting_manager = LightingManager(
                    self.main_window.viewer_widget
                )
            except Exception as e:
                self.main_window.lighting_manager = None
                self.logger.warning("LightingManager unavailable: %s", e)

            self.logger.info("Viewer managers initialized")
        except Exception as e:
            self.logger.warning("Failed to setup viewer managers: %s", e)

    def zoom_in(self) -> None:
        """Handle zoom in action."""
        self.logger.debug("Zoom in requested")
        self.main_window.status_label.setText("Zoomed in")

        # Forward to viewer widget if available
        if hasattr(self.main_window.viewer_widget, "zoom_in"):
            self.main_window.viewer_widget.zoom_in()
        else:
            QTimer.singleShot(
                2000, lambda: self.main_window.status_label.setText("Ready")
            )

    def zoom_out(self) -> None:
        """Handle zoom out action."""
        self.logger.debug("Zoom out requested")
        self.main_window.status_label.setText("Zoomed out")

        # Forward to viewer widget if available
        if hasattr(self.main_window.viewer_widget, "zoom_out"):
            self.main_window.viewer_widget.zoom_out()
        else:
            QTimer.singleShot(
                2000, lambda: self.main_window.status_label.setText("Ready")
            )

    def reset_view(self) -> None:
        """Handle reset view action."""
        self.logger.debug("Reset view requested")
        self.main_window.status_label.setText("View reset")

        # Forward to viewer widget if available
        if hasattr(self.main_window.viewer_widget, "reset_view"):
            self.main_window.viewer_widget.reset_view()
            # Reset save view button when view is reset
            try:
                if hasattr(self.main_window.viewer_widget, "reset_save_view_button"):
                    self.main_window.viewer_widget.reset_save_view_button()
            except Exception as e:
                self.logger.warning("Failed to reset save view button: %s", e)
        else:
            QTimer.singleShot(
                2000, lambda: self.main_window.status_label.setText("Ready")
            )

    def save_current_view(self) -> None:
        """Save the current camera view for the loaded model."""
        try:
            # Check if a model is currently loaded
            if (
                not hasattr(self.main_window.viewer_widget, "current_model")
                or not self.main_window.viewer_widget.current_model
            ):
                QMessageBox.information(
                    self.main_window, "Save View", "No model is currently loaded."
                )
                return

            # Get the model ID from the current model
            model = self.main_window.viewer_widget.current_model
            if not hasattr(model, "file_path") or not model.file_path:
                QMessageBox.warning(
                    self.main_window,
                    "Save View",
                    "Cannot save view: model file path not found.",
                )
                return

            from src.core.database_manager import get_database_manager

            db_manager = get_database_manager()
            model_id = db_manager.get_model_id_by_file_path(model.file_path)

            if not model_id:
                QMessageBox.warning(
                    self.main_window, "Save View", "Model not found in database."
                )
                return

            # Get camera state from viewer
            if hasattr(self.main_window.viewer_widget, "renderer"):
                camera = self.main_window.viewer_widget.renderer.GetActiveCamera()
                if camera:
                    pos = camera.GetPosition()
                    focal = camera.GetFocalPoint()
                    view_up = camera.GetViewUp()

                    camera_data = {
                        "position_x": pos[0],
                        "position_y": pos[1],
                        "position_z": pos[2],
                        "focal_x": focal[0],
                        "focal_y": focal[1],
                        "focal_z": focal[2],
                        "view_up_x": view_up[0],
                        "view_up_y": view_up[1],
                        "view_up_z": view_up[2],
                    }

                    # Save to database
                    success = db_manager.save_camera_orientation(model_id, camera_data)

                    if success:
                        self.main_window.status_label.setText(
                            "View saved for this model"
                        )
                        self.logger.info("Saved camera view for model ID %s", model_id)
                        # Reset save view button after successful save
                        try:
                            if hasattr(
                                self.main_window.viewer_widget, "reset_save_view_button"
                            ):
                                self.main_window.viewer_widget.reset_save_view_button()
                        except Exception as e:
                            self.logger.warning(
                                "Failed to reset save view button: %s", e
                            )
                        QTimer.singleShot(
                            3000, lambda: self.main_window.status_label.setText("Ready")
                        )
                    else:
                        QMessageBox.warning(
                            self.main_window,
                            "Save View",
                            "Failed to save view to database.",
                        )
                else:
                    QMessageBox.warning(
                        self.main_window, "Save View", "Camera not available."
                    )
            else:
                QMessageBox.warning(
                    self.main_window, "Save View", "Viewer not initialized."
                )

        except Exception as e:
            self.logger.error("Failed to save current view: %s", e)
            QMessageBox.critical(
                self.main_window, "Error", f"Failed to save view:\n{str(e)}"
            )

    def restore_saved_camera(self, model_id: int) -> None:
        """Restore saved camera view for a model."""
        try:
            from src.core.database_manager import get_database_manager

            db_manager = get_database_manager()
            camera_data = db_manager.get_camera_orientation(model_id)

            if camera_data and hasattr(self.main_window.viewer_widget, "renderer"):
                camera = self.main_window.viewer_widget.renderer.GetActiveCamera()
                if camera:
                    # Restore camera position, focal point, and view up
                    camera.SetPosition(
                        camera_data["camera_position_x"],
                        camera_data["camera_position_y"],
                        camera_data["camera_position_z"],
                    )
                    camera.SetFocalPoint(
                        camera_data["camera_focal_x"],
                        camera_data["camera_focal_y"],
                        camera_data["camera_focal_z"],
                    )
                    camera.SetViewUp(
                        camera_data["camera_view_up_x"],
                        camera_data["camera_view_up_y"],
                        camera_data["camera_view_up_z"],
                    )

                    # Update clipping range and render
                    self.main_window.viewer_widget.renderer.ResetCameraClippingRange()
                    self.main_window.viewer_widget.vtk_widget.GetRenderWindow().Render()

                    self.logger.info(
                        "Restored saved camera view for model ID %s", model_id
                    )
                    self.main_window.status_label.setText("Restored saved view")
                    QTimer.singleShot(
                        2000, lambda: self.main_window.status_label.setText("Ready")
                    )
            else:
                self.logger.debug("No saved camera view for model ID %s", model_id)

        except Exception as e:
            self.logger.warning("Failed to restore saved camera: %s", e)
