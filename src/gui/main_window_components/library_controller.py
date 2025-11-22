"""
Model library interactions for the main window.

Handles library signals, metadata sync, and model analysis outside main_window.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PySide6.QtWidgets import QMessageBox

from src.core.database_manager import get_database_manager
from src.core.data_structures import ModelFormat
from src.core.model_cache import CacheLevel, get_model_cache
from src.parsers.format_detector import FormatDetector
from src.parsers.obj_parser import OBJParser
from src.parsers.refactored_stl_parser import RefactoredSTLParser as STLParser
from src.parsers.step_parser import STEPParser
from src.parsers.threemf_parser import ThreeMFParser


class LibraryController:
    """Encapsulates model library UI interactions."""

    def __init__(self, main_window) -> None:
        self.main = main_window
        self.logger = getattr(main_window, "logger", None)
        self.activity_logger = getattr(main_window, "activity_logger", None)

    def on_model_imported_during_import(self, model_id: int) -> None:
        """Refresh the library when a single model finishes importing."""
        try:
            library = getattr(self.main, "model_library_widget", None)
            if library:
                if hasattr(library, "facade"):
                    library.facade.load_models_from_database()
                else:
                    library.refresh_models_from_database()
                if self.logger:
                    self.logger.debug("Model library refreshed for model ID: %d", model_id)
        except Exception as exc:
            if self.logger:
                self.logger.error(
                    "Failed to refresh model library for model %d: %s", model_id, exc
                )

    def on_models_added(self, model_ids: List[int]) -> None:
        """Handle models added to the library."""
        if self.logger:
            self.logger.info("Added %s models to library", len(model_ids))

        if model_ids:
            if hasattr(self.main, "status_label"):
                self.main.status_label.setText(
                    f"Added {len(model_ids)} models to library"
                )

            if hasattr(self.main, "_start_background_hasher"):
                self.main._start_background_hasher()

            # Clear status after a short delay
            from PySide6.QtCore import QTimer

            QTimer.singleShot(3000, lambda: self.main.status_label.setText("Ready"))

    def on_model_selected(self, model_id: int) -> None:
        """Handle model selection from the library."""
        try:
            self.main.current_model_id = model_id

            if hasattr(self.main, "menu_manager"):
                edit_action = getattr(self.main.menu_manager, "edit_model_action", None)
                if edit_action:
                    edit_action.setEnabled(True)
            if hasattr(self.main, "toolbar_manager"):
                edit_action = getattr(
                    self.main.toolbar_manager, "edit_model_action", None
                )
                if edit_action:
                    edit_action.setEnabled(True)

            if hasattr(self.main, "project_details_widget"):
                db_manager = get_database_manager()
                model_data = db_manager.get_model(model_id)
                if model_data:
                    self.main.project_details_widget.set_model(model_data)

            self.sync_metadata_to_selected_model(model_id)

            if self.logger:
                self.logger.debug("Model selected: %s", model_id)
        except Exception as exc:
            if self.logger:
                self.logger.error("Failed to handle model selection: %s", exc)

    def sync_metadata_to_selected_model(self, model_id: int) -> None:
        """Update metadata editor to show the selected model."""
        try:
            editor = getattr(self.main, "metadata_editor", None)
            if not editor:
                if self.logger:
                    self.logger.debug("Metadata editor not available for model %s", model_id)
                return

            editor.load_model_metadata(model_id)
            if self.logger:
                self.logger.debug("Metadata synchronized for model %s", model_id)

            tabs = getattr(self.main, "metadata_tabs", None)
            if tabs:
                tabs.setCurrentIndex(0)
                if self.logger:
                    self.logger.debug("Switched to Metadata tab for model %s", model_id)
        except Exception as exc:
            if self.logger:
                self.logger.warning(
                    "Failed to synchronize metadata for model %s: %s", model_id, exc
                )

    def edit_model(self) -> None:
        """Analyze the currently selected model for errors."""
        try:
            if not getattr(self.main, "current_model_id", None):
                QMessageBox.information(
                    self.main,
                    "No Model Selected",
                    "Please select a model from the library first.",
                )
                return

            db_manager = get_database_manager()
            model_data = db_manager.get_model(self.main.current_model_id)
            if not model_data:
                QMessageBox.warning(self.main, "Error", "Model not found in database")
                return

            file_path = model_data.get("file_path")
            if not file_path:
                QMessageBox.warning(self.main, "Error", "Model file path not found")
                return

            fmt = FormatDetector().detect_format(Path(file_path))
            if fmt == ModelFormat.STL:
                parser = STLParser()
            elif fmt == ModelFormat.OBJ:
                parser = OBJParser()
            elif fmt == ModelFormat.THREE_MF:
                parser = ThreeMFParser()
            elif fmt == ModelFormat.STEP:
                parser = STEPParser()
            else:
                QMessageBox.warning(self.main, "Error", f"Unsupported model format: {fmt}")
                return

            model_cache = get_model_cache()
            cached_model = model_cache.get(file_path, CacheLevel.GEOMETRY_FULL)
            model = cached_model if cached_model and cached_model.triangles else None
            if not model:
                model = parser.parse_file(file_path)
                if model:
                    model_cache.put(file_path, CacheLevel.GEOMETRY_FULL, model)

            if not model or (not model.triangles and not model.vertex_array):
                QMessageBox.critical(
                    self.main, "Error", f"Failed to load model geometry: {file_path}"
                )
                return

            from src.gui.model_editor.model_analyzer_dialog import ModelAnalyzerDialog

            dialog = ModelAnalyzerDialog(model, file_path, self.main)

            if dialog.exec() == 1 and self.activity_logger:
                self.activity_logger.info("Model analyzed and fixed")
                if hasattr(self.main, "model_viewer_controller"):
                    self.main.model_viewer_controller.on_model_double_clicked(
                        self.main.current_model_id
                    )
        except Exception as exc:
            if self.logger:
                self.logger.error("Failed to analyze model: %s", exc)
            QMessageBox.critical(
                self.main, "Error", f"Failed to analyze model: {str(exc)}"
            )
