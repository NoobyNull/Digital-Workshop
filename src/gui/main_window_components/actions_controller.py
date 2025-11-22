"""
Actions controller for the main window.

Moves menu/toolbar handlers out of ``main_window.py`` to keep the shell lighter.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox

from src.core.database_manager import get_database_manager


class ActionsController:
    """Encapsulates menu/toolbar actions for the main window."""

    def __init__(self, main_window) -> None:
        self.main = main_window
        self.logger = getattr(main_window, "logger", None)
        self.activity_logger = getattr(main_window, "activity_logger", None)

    # ---- Import / library -------------------------------------------------
    def import_models(self) -> None:
        self.open_import_dialog()

    def start_library_rebuild(self) -> None:
        if hasattr(self.main, "_start_library_rebuild"):
            self.main._start_library_rebuild()

    def on_model_library_import_requested(self, file_paths: List[str]) -> None:
        cleaned_paths: List[str] = []
        for path in file_paths or []:
            if not path:
                continue
            p = Path(path)
            if p.exists() and p.is_file():
                cleaned_paths.append(str(p))

        if cleaned_paths:
            self.open_import_dialog(cleaned_paths)
        else:
            self.open_import_dialog()

    def open_import_dialog(self, initial_files: Optional[List[str]] = None) -> None:
        try:
            from src.gui.import_components.import_dialog import ImportDialog
            from src.core.root_folder_manager import RootFolderManager

            root_manager = RootFolderManager()
            dialog = ImportDialog(parent=self.main, root_folder_manager=root_manager)

            if initial_files:
                try:
                    dialog.add_files(initial_files)
                except Exception:
                    pass

            dialog.model_imported.connect(self.main._on_model_imported_during_import)
            dialog.fragment_imported.connect(self.main._on_import_completed)

            if dialog.exec() == dialog.Accepted:
                import_result = dialog.get_import_result()
                if import_result and self.activity_logger:
                    self.activity_logger.info(
                        "Import completed: %s files imported",
                        import_result.processed_files,
                    )
                self.main.status_label.setText(
                    f"Import complete: {import_result.processed_files} file(s) imported"
                )

                if getattr(self.main, "model_library_widget", None):
                    self.main.model_library_widget._load_models_from_database()

                QTimer.singleShot(5000, lambda: self.main.status_label.setText("Ready"))

        except Exception as exc:
            if self.logger:
                self.logger.error(
                    "Failed to show import dialog: %s", exc, exc_info=True
                )
            QMessageBox.critical(
                self.main,
                "Import Error",
                f"Failed to open import dialog:\n\n{exc}",
            )

    def open_import_from_url_dialog(self) -> None:
        try:
            from src.gui.import_components.url_import_dialog import UrlImportDialog

            dialog = UrlImportDialog(self.main)
            dialog.exec()
        except Exception as exc:
            if self.logger:
                self.logger.error(
                    "Failed to open Import from URL dialog: %s", exc, exc_info=True
                )
            QMessageBox.critical(
                self.main,
                "Import Error",
                f"Failed to open Import from URL dialog:\n\n{exc}",
            )

    def restore_metadata_manager(self) -> None:
        try:
            if getattr(self.main, "metadata_dock", None):
                self.main.metadata_dock.show()
                self.main.metadata_dock.raise_()
                self.main.statusBar().showMessage("Metadata Manager restored", 2000)
            else:
                if self.logger:
                    self.logger.warning("Metadata dock not available")
        except Exception as exc:
            if self.logger:
                self.logger.error("Failed to restore Metadata Manager: %s", exc)

    def restore_model_library(self) -> None:
        try:
            if getattr(self.main, "model_library_dock", None):
                self.main.model_library_dock.show()
                self.main.model_library_dock.raise_()
                self.main.statusBar().showMessage("Model Library restored", 2000)
            else:
                if self.logger:
                    self.logger.warning("Model Library dock not available")
        except Exception as exc:
            if self.logger:
                self.logger.error("Failed to restore Model Library: %s", exc)

    def reload_stylesheet_action(self) -> None:
        if self.logger:
            self.logger.info("Theme is managed by Material Design system")
        try:
            self.main.statusBar().showMessage("Material Design theme active", 2000)
        except Exception:
            pass

    def reset_dock_layout(self) -> None:
        if hasattr(self.main, "_reset_dock_layout_and_save"):
            self.main._reset_dock_layout_and_save()

    # ---- View controls ----------------------------------------------------
    def zoom_in(self) -> None:
        if self.logger:
            self.logger.debug("Zoom in requested")
        self.main.status_label.setText("Zoomed in")
        if hasattr(self.main, "viewer_widget") and hasattr(
            self.main.viewer_widget, "zoom_in"
        ):
            self.main.viewer_widget.zoom_in()
        else:
            QTimer.singleShot(2000, lambda: self.main.status_label.setText("Ready"))

    def zoom_out(self) -> None:
        if self.logger:
            self.logger.debug("Zoom out requested")
        self.main.status_label.setText("Zoomed out")
        if hasattr(self.main, "viewer_widget") and hasattr(
            self.main.viewer_widget, "zoom_out"
        ):
            self.main.viewer_widget.zoom_out()
        else:
            QTimer.singleShot(2000, lambda: self.main.status_label.setText("Ready"))

    def reset_view(self) -> None:
        if self.logger:
            self.logger.debug("Reset view requested")
        self.main.status_label.setText("View reset")
        if hasattr(self.main, "viewer_widget") and hasattr(
            self.main.viewer_widget, "reset_view"
        ):
            self.main.viewer_widget.reset_view()
            try:
                if hasattr(self.main.viewer_widget, "reset_save_view_button"):
                    self.main.viewer_widget.reset_save_view_button()
            except Exception:
                pass
        else:
            QTimer.singleShot(2000, lambda: self.main.status_label.setText("Ready"))

    def save_current_view(self) -> None:
        try:
            if (
                not hasattr(self.main.viewer_widget, "current_model")
                or not self.main.viewer_widget.current_model
            ):
                QMessageBox.information(
                    self.main, "Save View", "No model is currently loaded."
                )
                return

            model = self.main.viewer_widget.current_model
            if not hasattr(model, "file_path") or not model.file_path:
                QMessageBox.warning(
                    self.main,
                    "Save View",
                    "Cannot save view: model file path not found.",
                )
                return

            db_manager = get_database_manager()
            model_record = db_manager.get_model_by_path(model.file_path)
            if not model_record:
                QMessageBox.warning(
                    self.main,
                    "Save View",
                    "Model not found in database. Save the model before saving the view.",
                )
                return

            model_id = model_record.get("id")
            if model_id is None:
                QMessageBox.warning(
                    self.main,
                    "Save View",
                    "Model ID missing. Cannot save view without a valid model record.",
                )
                return

            if hasattr(self.main.viewer_widget, "save_current_view"):
                self.main.viewer_widget.save_current_view(model_id)
                self.main.statusBar().showMessage("View saved successfully", 2000)
            else:
                QMessageBox.information(
                    self.main,
                    "Save View",
                    "Current viewer does not support saving views.",
                )
        except Exception as exc:
            if self.logger:
                self.logger.error("Failed to save current view: %s", exc, exc_info=True)
            QMessageBox.critical(
                self.main,
                "Save View Error",
                f"Failed to save current view:\n\n{exc}",
            )

    def edit_model(self) -> None:
        if hasattr(self.main, "_edit_model"):
            self.main._edit_model()

    def show_preferences(self) -> None:
        if hasattr(self.main, "_show_preferences"):
            self.main._show_preferences()

    # ---- About / screenshots ----------------------------------------------
    def show_about(self) -> None:
        if self.logger:
            self.logger.info("Showing about dialog")

        about_text = (
            "<h3>Digital Workshop</h3>"
            "<p>Version 1.0.0</p>"
            "<p>A desktop application for managing and viewing 3D models.</p>"
            "<p><b>Supported formats:</b> STL, OBJ, STEP, MF3</p>"
            "<p>&copy; 2023 Digital Workshop Development Team</p>"
        )
        QMessageBox.about(self.main, "About Digital Workshop", about_text)

    def show_tips(self) -> None:
        try:
            from src.gui.walkthrough import WalkthroughDialog

            dialog = WalkthroughDialog(self.main)
            dialog.exec()
        except Exception as exc:
            if self.logger:
                self.logger.error("Failed to show tips dialog: %s", exc)

    def set_layout_edit_mode(self, enabled: bool) -> None:
        if hasattr(self.main, "_set_layout_edit_mode"):
            self.main._set_layout_edit_mode(enabled, show_message=True)

    def generate_library_screenshots(self) -> None:
        try:
            from src.gui.thumbnail_generation_coordinator import (
                ThumbnailGenerationCoordinator,
            )
            from src.core.application_config import ApplicationConfig

            db_manager = get_database_manager()
            models = db_manager.get_all_models()
            if not models:
                QMessageBox.information(
                    self.main,
                    "No Models",
                    "No models found in the library. Import some models first.",
                )
                return

            config = ApplicationConfig.get_default()
            materials = getattr(config, "available_materials", ["default"])
            background = getattr(config, "default_background", None)

            coordinator = ThumbnailGenerationCoordinator()
            file_info_list = []
            for model in models:
                file_path = model.get("file_path")
                file_hash = model.get("file_hash")
                if file_path and file_hash:
                    file_info_list.append((file_path, file_hash))

            if not file_info_list:
                QMessageBox.information(
                    self.main,
                    "No Models",
                    "No models with hashes available for thumbnail generation.",
                )
                return

            coordinator.generate_thumbnails(
                file_info_list=file_info_list,
                material=materials[0] if materials else "default",
                background=background,
            )
            QMessageBox.information(
                self.main,
                "Screenshots Generated",
                "Library screenshots were generated successfully.",
            )
        except Exception as exc:
            if self.logger:
                self.logger.error("Failed to generate library screenshots: %s", exc)
            QMessageBox.critical(
                self.main,
                "Error",
                f"Failed to generate library screenshots:\n\n{exc}",
            )
