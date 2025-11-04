"""
Event handling for main window.

Handles user actions, model events, and view management.
"""

from pathlib import Path
from typing import List

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox

from src.core.logging_config import get_logger, get_activity_logger, log_function_call
from src.core.database_manager import get_database_manager
from src.gui.preferences import PreferencesDialog


logger = get_logger(__name__)
activity_logger = get_activity_logger(__name__)


class EventHandler:
    """Handles events and user actions in the main window."""

    def __init__(self, main_window):
        """
        Initialize event handler.

        Args:
            main_window: The main window instance
        """
        self.main_window = main_window

    def reload_stylesheet_action(self) -> None:
        """Reload and re-apply the Material Design theme."""
        logger.info("Theme is managed by Material Design system")
        self.main_window.statusBar().showMessage("Material Design theme active", 2000)

    @log_function_call(logger)
    def on_model_double_clicked(self, model_id: int) -> None:
        """Handle model double-click from the model library."""
        try:
            db_manager = get_database_manager()
            model = db_manager.get_model(model_id)

            if model:
                file_path = model["file_path"]
                logger.info(f"Loading model from library: {file_path}")

                filename = Path(file_path).name
                self.main_window.status_label.setText(f"Loading: {filename}")
                self.main_window.progress_bar.setVisible(True)
                self.main_window.progress_bar.setRange(0, 0)

                self.main_window.current_model_id = model_id
                self.main_window.model_loader_manager.load_stl_model(file_path)

                QTimer.singleShot(500, lambda: self.restore_saved_camera(model_id))
            else:
                logger.warning(f"Model with ID {model_id} not found in database")

        except Exception as e:
            logger.error(f"Failed to handle model double-click: {str(e)}")

    def on_models_added(self, model_ids: List[int]) -> None:
        """Handle models added to the library."""
        activity_logger.info(f"Added {len(model_ids)} models to library")

        if model_ids:
            self.main_window.status_label.setText(f"Added {len(model_ids)} models to library")
            self.main_window._start_background_hasher()
            QTimer.singleShot(3000, lambda: self.main_window.status_label.setText("Ready"))

    @log_function_call(logger)
    def on_metadata_saved(self, model_id: int) -> None:
        """Handle metadata saved event from the metadata editor."""
        try:
            activity_logger.info(f"Metadata saved for model ID: {model_id}")
            self.main_window.status_label.setText("Metadata saved")

            if hasattr(self.main_window, "model_library_widget"):
                self.main_window.model_library_widget._load_models_from_database()

            QTimer.singleShot(3000, lambda: self.main_window.status_label.setText("Ready"))

        except Exception as e:
            logger.error(f"Failed to handle metadata saved event: {str(e)}")

    def on_metadata_changed(self, model_id: int) -> None:
        """Handle metadata changed event from the metadata editor."""
        try:
            logger.debug(f"Metadata changed for model ID: {model_id}")
            self.main_window.status_label.setText("Metadata modified (unsaved changes)")

        except Exception as e:
            logger.error(f"Failed to handle metadata changed event: {str(e)}")

    def show_preferences(self) -> None:
        """Show preferences dialog."""
        logger.info("Opening preferences dialog")
        dlg = PreferencesDialog(
            self.main_window,
            on_reset_layout=self.main_window._reset_dock_layout_and_save,
        )
        dlg.viewer_settings_changed.connect(self._on_viewer_settings_changed)
        dlg.exec_()

    def _on_viewer_settings_changed(self) -> None:
        """Handle viewer settings changed from preferences dialog."""
        try:
            logger.info(
                "Viewer settings changed from preferences, syncing to lighting panel and manager"
            )

            # Reload lighting settings from QSettings and apply to lighting manager
            if hasattr(self.main_window, "_settings_manager"):
                self.main_window._settings_manager.load_lighting_settings()
                logger.info("Lighting settings reloaded and synced to popup and manager")
            elif hasattr(self.main_window, "_load_lighting_settings"):
                # Fallback: call load_lighting_settings directly
                self.main_window._load_lighting_settings()
                logger.info("Lighting settings reloaded directly from main window")

            # Reload viewer settings to scene manager
            if hasattr(self.main_window.viewer_widget, "scene_manager"):
                self.main_window.viewer_widget.scene_manager.reload_viewer_settings()
                logger.info("Viewer settings reloaded to scene manager")

        except Exception as e:
            logger.error(f"Failed to sync viewer settings: {e}")

    def show_theme_manager(self) -> None:
        """Show the Theme Manager dialog."""
        try:
            from src.gui.theme import ThemeDialog

            dlg = ThemeDialog(self.main_window)
            dlg.theme_applied.connect(self.on_theme_applied)
            dlg.exec()
        except Exception as e:
            logger.error(f"Failed to open Theme Manager: {e}")
            QMessageBox.warning(
                self.main_window, "Theme Manager", f"Failed to open Theme Manager:\n{e}"
            )

    def on_theme_applied(self, preset_name: str) -> None:
        """Handle theme change notification."""
        logger.info(f"Theme changed: {preset_name}")

    def zoom_in(self) -> None:
        """Handle zoom in action."""
        logger.debug("Zoom in requested")
        self.main_window.status_label.setText("Zoomed in")

        if hasattr(self.main_window.viewer_widget, "zoom_in"):
            self.main_window.viewer_widget.zoom_in()
        else:
            QTimer.singleShot(2000, lambda: self.main_window.status_label.setText("Ready"))

    def zoom_out(self) -> None:
        """Handle zoom out action."""
        logger.debug("Zoom out requested")
        self.main_window.status_label.setText("Zoomed out")

        if hasattr(self.main_window.viewer_widget, "zoom_out"):
            self.main_window.viewer_widget.zoom_out()
        else:
            QTimer.singleShot(2000, lambda: self.main_window.status_label.setText("Ready"))

    def reset_view(self) -> None:
        """Handle reset view action."""
        logger.debug("Reset view requested")
        self.main_window.status_label.setText("View reset")

        if hasattr(self.main_window.viewer_widget, "reset_view"):
            self.main_window.viewer_widget.reset_view()
            try:
                if hasattr(self.main_window.viewer_widget, "reset_save_view_button"):
                    self.main_window.viewer_widget.reset_save_view_button()
            except Exception as e:
                logger.warning(f"Failed to reset save view button: {e}")
        else:
            QTimer.singleShot(2000, lambda: self.main_window.status_label.setText("Ready"))

    @log_function_call(logger)
    def save_current_view(self) -> None:
        """Save the current camera view for the loaded model."""
        try:
            if (
                not hasattr(self.main_window.viewer_widget, "current_model")
                or not self.main_window.viewer_widget.current_model
            ):
                QMessageBox.information(
                    self.main_window, "Save View", "No model is currently loaded."
                )
                return

            model = self.main_window.viewer_widget.current_model
            if not hasattr(model, "file_path") or not model.file_path:
                QMessageBox.warning(
                    self.main_window,
                    "Save View",
                    "Cannot save view: model file path not found.",
                )
                return

            db_manager = get_database_manager()
            models = db_manager.get_all_models()
            model_id = None
            for m in models:
                if m.get("file_path") == model.file_path:
                    model_id = m.get("id")
                    break

            if not model_id:
                QMessageBox.warning(self.main_window, "Save View", "Model not found in database.")
                return

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

                    success = db_manager.save_camera_orientation(model_id, camera_data)

                    if success:
                        self.main_window.status_label.setText("View saved for this model")
                        logger.info(f"Saved camera view for model ID {model_id}")
                        try:
                            if hasattr(self.main_window.viewer_widget, "reset_save_view_button"):
                                self.main_window.viewer_widget.reset_save_view_button()
                        except Exception as e:
                            logger.warning(f"Failed to reset save view button: {e}")
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
                    QMessageBox.warning(self.main_window, "Save View", "Camera not available.")
            else:
                QMessageBox.warning(self.main_window, "Save View", "Viewer not initialized.")

        except Exception as e:
            logger.error(f"Failed to save current view: {e}")
            QMessageBox.warning(self.main_window, "Save View", f"Failed to save view: {str(e)}")

    @log_function_call(logger)
    def restore_saved_camera(self, model_id: int) -> None:
        """Restore saved camera orientation for a model."""
        try:
            db_manager = get_database_manager()
            camera_data = db_manager.get_camera_orientation(model_id)

            if camera_data and hasattr(self.main_window.viewer_widget, "renderer"):
                camera = self.main_window.viewer_widget.renderer.GetActiveCamera()
                if camera:
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

                    self.main_window.viewer_widget.renderer.ResetCameraClippingRange()
                    self.main_window.viewer_widget.vtk_widget.GetRenderWindow().Render()

                    logger.info(f"Restored saved camera view for model ID {model_id}")
                    self.main_window.status_label.setText("Restored saved view")
                    QTimer.singleShot(2000, lambda: self.main_window.status_label.setText("Ready"))
            else:
                logger.debug(f"No saved camera view for model ID {model_id}")

        except Exception as e:
            logger.warning(f"Failed to restore saved camera: {e}")

    def show_about(self) -> None:
        """Show about dialog."""
        logger.info("Showing about dialog")

        about_text = (
            "<h3>Digital Workshop</h3>"
            "<p>Version 1.0.0</p>"
            "<p>A desktop application for managing and viewing 3D models.</p>"
            "<p><b>Supported formats:</b> STL, OBJ, STEP, MF3</p>"
            "<p><b>Requirements:</b> Windows 7+, Python 3.8+, PySide5</p>"
            "<br>"
            "<p>&copy; 2023 Digital Workshop Development Team</p>"
        )

        QMessageBox.about(self.main_window, "About Digital Workshop", about_text)

    @log_function_call(logger)
    def generate_library_screenshots(self) -> None:
        """Generate screenshots for all models in the library with applied materials."""
        try:
            from src.gui.batch_screenshot_worker import BatchScreenshotWorker
            from src.core.application_config import ApplicationConfig

            if (
                not hasattr(self.main_window, "material_manager")
                or self.main_window.material_manager is None
            ):
                QMessageBox.warning(
                    self.main_window,
                    "Screenshot Generation",
                    "Material manager not available. Cannot generate screenshots.",
                )
                return

            config = ApplicationConfig.get_default()
            bg_image = config.thumbnail_bg_image
            material = config.thumbnail_material

            self.main_window.screenshot_worker = BatchScreenshotWorker(
                material_manager=self.main_window.material_manager,
                screenshot_size=256,
                background_image=bg_image,
                material_name=material,
            )

            self.main_window.screenshot_worker.progress_updated.connect(self.on_screenshot_progress)
            self.main_window.screenshot_worker.screenshot_generated.connect(
                self.on_screenshot_generated
            )
            self.main_window.screenshot_worker.error_occurred.connect(self.on_screenshot_error)
            self.main_window.screenshot_worker.finished_batch.connect(self.on_screenshots_finished)

            self.main_window.progress_bar.setVisible(True)
            self.main_window.progress_bar.setRange(0, 100)
            self.main_window.progress_bar.setValue(0)
            self.main_window.status_label.setText("Generating screenshots for all models...")

            self.main_window.screenshot_worker.start()
            logger.info("Started batch screenshot generation")

        except Exception as e:
            logger.error(f"Failed to start screenshot generation: {e}")
            QMessageBox.critical(
                self.main_window,
                "Screenshot Generation Error",
                f"Failed to start screenshot generation:\n{e}",
            )

    def on_screenshot_progress(self, current: int, total: int) -> None:
        """Handle screenshot generation progress."""
        try:
            if total > 0:
                progress = int((current / total) * 100)
                self.main_window.progress_bar.setValue(progress)
                self.main_window.status_label.setText(f"Generating screenshots: {current}/{total}")
        except Exception as e:
            logger.warning(f"Failed to update progress: {e}")

    def on_screenshot_generated(self, model_id: int, screenshot_path: str) -> None:
        """Handle screenshot generated event."""
        try:
            logger.debug(f"Screenshot generated for model {model_id}: {screenshot_path}")
        except Exception as e:
            logger.warning(f"Failed to handle screenshot generated event: {e}")

    def on_screenshot_error(self, error_message: str) -> None:
        """Handle screenshot generation error."""
        try:
            logger.error(f"Screenshot generation error: {error_message}")
            self.main_window.status_label.setText(f"Error: {error_message}")
        except Exception as e:
            logger.warning(f"Failed to handle screenshot error: {e}")

    def on_screenshots_finished(self) -> None:
        """Handle screenshot generation finished."""
        try:
            self.main_window.progress_bar.setVisible(False)
            self.main_window.status_label.setText("Screenshots generated successfully")
            logger.info("Batch screenshot generation finished")
            QTimer.singleShot(3000, lambda: self.main_window.status_label.setText("Ready"))
        except Exception as e:
            logger.warning(f"Failed to handle screenshots finished: {e}")
