"""
Thumbnail Manager for MainWindow.

Handles screenshot and thumbnail generation operations.
Extracted from MainWindow to reduce monolithic class size.
"""

import logging

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMainWindow, QMessageBox


class ThumbnailManager:
    """Manages screenshot and thumbnail generation operations."""

    def __init__(self, main_window: QMainWindow, logger: logging.Logger):
        """
        Initialize the thumbnail manager.

        Args:
            main_window: The main window instance
            logger: Logger instance
        """
        self.main_window = main_window
        self.logger = logger

    def generate_library_screenshots(self) -> None:
        """Generate thumbnails for all models in the library with applied materials."""
        try:
            from src.gui.thumbnail_generation_coordinator import (
                ThumbnailGenerationCoordinator,
            )
            from src.core.application_config import ApplicationConfig
            from src.core.database_manager import get_database_manager

            # Get all models from database
            db_manager = get_database_manager()
            models = db_manager.get_all_models()

            if not models:
                QMessageBox.information(
                    self.main_window,
                    "No Models",
                    "No models found in the library. Import some models first.",
                )
                return

            # Get configuration
            config = ApplicationConfig.get_default()
            background = config.thumbnail_bg_image
            material = config.thumbnail_material

            # Prepare file info list
            file_info_list = []
            for model in models:
                file_info_list.append(
                    {
                        "file_path": model.get("file_path"),
                        "model_id": model.get("id"),
                    }
                )

            # Create coordinator and generate thumbnails
            coordinator = ThumbnailGenerationCoordinator(parent=self.main_window)

            # Connect thumbnail generated signal to save to database
            def on_thumbnail_generated(file_path: str, thumbnail_path: str):
                """Save thumbnail path to database when generated."""
                try:
                    from src.core.database_manager import get_database_manager

                    db_manager = get_database_manager()
                    # Find model by file path
                    for model in models:
                        if model.get("file_path") == file_path:
                            model_id = model.get("id")
                            db_manager.update_model_thumbnail(model_id, thumbnail_path)
                            self.logger.info(
                                "Saved thumbnail path to database for model %d: %s",
                                model_id,
                                thumbnail_path,
                            )
                            break
                except Exception as e:
                    self.logger.error("Failed to save thumbnail path to database: %s", e)

            coordinator.thumbnail_generated.connect(on_thumbnail_generated)
            coordinator.generate_thumbnails(
                file_info_list=file_info_list,
                background=background,
                material=material,
            )

            # Connect completion signal to reload library
            coordinator.generation_completed.connect(self.on_library_thumbnails_completed)

            self.logger.info(f"Started thumbnail generation for {len(file_info_list)} models")

        except Exception as e:
            self.logger.error("Failed to start thumbnail generation: %s", e)
            QMessageBox.critical(
                self.main_window,
                "Thumbnail Generation Error",
                f"Failed to start thumbnail generation:\n{e}",
            )

    def on_screenshot_progress(self, current: int, total: int) -> None:
        """Handle screenshot generation progress."""
        try:
            if total > 0:
                progress = int((current / total) * 100)
                self.main_window.progress_bar.setValue(progress)
                self.main_window.status_label.setText(f"Generating screenshots: {current}/{total}")
        except Exception as e:
            self.logger.warning("Failed to update progress: %s", e)

    def on_screenshot_generated(self, model_id: int, screenshot_path: str) -> None:
        """Handle screenshot generated event."""
        try:
            self.logger.debug(f"Screenshot generated for model {model_id}: {screenshot_path}")
        except Exception as e:
            self.logger.warning("Failed to handle screenshot generated event: %s", e)

    def on_screenshot_error(self, error_message: str) -> None:
        """Handle screenshot generation error."""
        try:
            self.logger.error("Screenshot generation error: %s", error_message)
            self.main_window.status_label.setText(f"Error: {error_message}")
        except Exception as e:
            self.logger.warning("Failed to handle screenshot error: %s", e)

    def on_screenshots_finished(self) -> None:
        """Handle batch screenshot generation completion."""
        try:
            self.main_window.progress_bar.setVisible(False)
            self.main_window.status_label.setText("Screenshots generated successfully")

            # Reload model library to display new thumbnails
            if hasattr(self.main_window, "model_library_widget"):
                if self.main_window.model_library_widget:
                    self.main_window.model_library_widget._load_models_from_database()

            QMessageBox.information(
                self.main_window,
                "Screenshot Generation Complete",
                "All model screenshots have been generated successfully!",
            )

            self.logger.info("Batch screenshot generation completed")

            # Clear status after a delay
            QTimer.singleShot(3000, lambda: self.main_window.status_label.setText("Ready"))

        except Exception as e:
            self.logger.error("Failed to handle screenshots finished event: %s", e)

    def on_library_thumbnails_completed(self) -> None:
        """Handle library thumbnail generation completion."""
        try:
            # Reload model library to display new thumbnails
            if hasattr(self.main_window, "model_library_widget"):
                if self.main_window.model_library_widget:
                    self.main_window.model_library_widget._load_models_from_database()

            self.logger.info("Library thumbnail generation completed")

        except Exception as e:
            self.logger.error("Failed to handle library thumbnails completion: %s", e)
