"""
Project event handling for the main window.

Moves project open/create/delete/file-selected and related sync logic out of main_window.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox

from src.core.database_manager import get_database_manager


class ProjectEventsController:
    """Encapsulates project-related event handling for MainWindow."""

    def __init__(self, main_window) -> None:
        self.main = main_window
        self.logger = getattr(main_window, "logger", None)

    def on_project_opened(self, project_id: str) -> None:
        """Handle project opened event."""
        try:
            if self.logger:
                self.logger.info("Project opened: %s", project_id)
            if hasattr(self.main, "status_label"):
                self.main.status_label.setText(f"Project opened: {project_id}")

            self._push_project_to_widgets(project_id)

            if hasattr(self.main, "gcode_previewer_controller"):
                self.main.gcode_previewer_controller.set_current_project(project_id)

            QTimer.singleShot(3000, lambda: self._set_status("Ready"))
        except Exception as exc:
            if self.logger:
                self.logger.error("Failed to handle project opened event: %s", exc)

    def on_project_created(self, project_id: str) -> None:
        """Handle project created event."""
        try:
            if self.logger:
                self.logger.info("Project created: %s", project_id)
            self._set_status(f"Project created: {project_id}")
            QTimer.singleShot(3000, lambda: self._set_status("Ready"))
        except Exception as exc:
            if self.logger:
                self.logger.error("Failed to handle project created event: %s", exc)

    def on_project_deleted(self, project_id: str) -> None:
        """Handle project deleted event."""
        try:
            if self.logger:
                self.logger.info("Project deleted: %s", project_id)
            self._set_status(f"Project deleted: {project_id}")
            QTimer.singleShot(3000, lambda: self._set_status("Ready"))
        except Exception as exc:
            if self.logger:
                self.logger.error("Failed to handle project deleted event: %s", exc)

    def on_project_file_selected(self, file_path: str, tab_name: str) -> None:
        """Handle file selection from the project tree."""
        try:
            if not file_path:
                return

            path_obj = Path(file_path)
            if not path_obj.exists():
                self._warn_file_missing(file_path)
                return

            if tab_name == "Model Previewer":
                self._load_model_file(path_obj)
            elif tab_name == "G Code Previewer":
                self._load_gcode_file(path_obj)
        except Exception as exc:
            if self.logger:
                self.logger.error("Failed to handle project file selection: %s", exc)

    # ---- helpers ---------------------------------------------------------
    def _set_status(self, text: str) -> None:
        if hasattr(self.main, "status_label") and self.main.status_label:
            self.main.status_label.setText(text)

    def _push_project_to_widgets(self, project_id: str) -> None:
        """Propagate current project to dependent widgets."""
        targets = [
            ("clo_widget", "set_current_project"),
            ("feeds_and_speeds_widget", "set_current_project"),
            ("cost_estimator_widget", "set_current_project"),
            ("viewer_widget", "set_current_project"),
        ]
        for attr, method in targets:
            widget = getattr(self.main, attr, None)
            if not widget:
                continue
            try:
                if hasattr(widget, method):
                    getattr(widget, method)(project_id)
                    if self.logger:
                        self.logger.debug(
                            "Set current project for %s: %s", attr, project_id
                        )
            except Exception as exc:
                if self.logger:
                    self.logger.warning("Failed to set project for %s: %s", attr, exc)

    def _warn_file_missing(self, file_path: str) -> None:
        if self.logger:
            self.logger.warning("Selected project file does not exist: %s", file_path)
        QMessageBox.warning(
            self.main,
            "File Not Found",
            f"The selected file no longer exists on disk:\n{file_path}",
        )

    def _load_model_file(self, path_obj: Path) -> None:
        filename = path_obj.name
        self._set_status(f"Loading: {filename}")
        if hasattr(self.main, "progress_bar"):
            self.main.progress_bar.setVisible(True)
            self.main.progress_bar.setRange(0, 0)

        if hasattr(self.main, "project_details_widget"):
            db_manager = get_database_manager()
            model_data = db_manager.get_model_by_path(str(path_obj))
            if model_data:
                self.main.project_details_widget.set_model(model_data)
            else:
                self.main.project_details_widget.show_file(str(path_obj))

        # Clear library model context and load directly from path
        self.main.current_model_id = None
        if (
            hasattr(self.main, "model_loader_manager")
            and self.main.model_loader_manager
        ):
            self.main.model_loader_manager.load_stl_model(str(path_obj))

    def _load_gcode_file(self, path_obj: Path) -> None:
        if hasattr(self.main, "project_details_widget"):
            self.main.project_details_widget.show_file(str(path_obj))
        if hasattr(self.main, "gcode_previewer_controller"):
            self.main.gcode_previewer_controller.open_gcode_file(str(path_obj))
