"""
Model management for library.

Handles model loading, database integration, and view updates.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QStandardItem
from PySide6.QtWidgets import QMessageBox

from src.core.logging_config import get_logger, log_function_call
from src.core.performance_monitor import monitor_operation

logger = get_logger(__name__)


class LibraryModelManager:
    """Manages model loading and database integration."""

    def __init__(self, library_widget):
        """
        Initialize model manager.

        Args:
            library_widget: The model library widget
        """
        self.library_widget = library_widget
        self.logger = get_logger(__name__)

    @log_function_call(logger)
    def load_models_from_database(self) -> None:
        """Load models from the database into the view."""
        try:
            self.library_widget.status_label.setText("Loading models...")
            self.library_widget.current_models = self.library_widget.db_manager.get_all_models()
            self.update_model_view()
            self.library_widget.model_count_label.setText(f"Models: {len(self.library_widget.current_models)}")
            self.library_widget.status_label.setText("Ready")
        except Exception as e:
            self.logger.error(f"Failed to load models from database: {e}")
            self.library_widget.status_label.setText("Error loading models")

    def update_model_view(self) -> None:
        """Populate list/grid views from current_models."""
        self.library_widget.list_model.clear()
        self.library_widget.list_model.setHorizontalHeaderLabels(
            ["Name", "Format", "Size", "Triangles", "Category", "Added Date"]
        )
        for model in self.library_widget.current_models:
            name_item = QStandardItem(model.get("title") or model.get("filename", "Unknown"))
            name_item.setData(model.get("id"), Qt.UserRole)

            # Set icon from thumbnail if available
            thumbnail_path = model.get("thumbnail_path")
            if thumbnail_path and Path(thumbnail_path).exists():
                try:
                    icon = QIcon(thumbnail_path)
                    name_item.setIcon(icon)
                except Exception as e:
                    self.logger.warning(f"Failed to load thumbnail icon: {e}")

            fmt = (model.get("format") or "Unknown").upper()
            format_item = QStandardItem(fmt)

            size_bytes = model.get("file_size", 0) or 0
            if size_bytes > 1024 * 1024:
                size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
            elif size_bytes > 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes} B"
            size_item = QStandardItem(size_str)

            triangles_item = QStandardItem(f"{model.get('triangle_count', 0):,}")
            category_item = QStandardItem(model.get("category", "Uncategorized"))
            date_item = QStandardItem(str(model.get("date_added", "Unknown")))

            self.library_widget.list_model.appendRow(
                [name_item, format_item, size_item, triangles_item, category_item, date_item]
            )

        self.library_widget._apply_filters()

    def get_selected_model_id(self) -> Optional[int]:
        """Get the ID of the currently selected model."""
        from .library_event_handler import ViewMode

        view = (
            self.library_widget.list_view
            if self.library_widget.view_mode == ViewMode.LIST
            else self.library_widget.grid_view
        )
        indexes = view.selectedIndexes()
        if not indexes:
            return None
        src_index = self.library_widget.proxy_model.mapToSource(indexes[0])
        item = self.library_widget.list_model.item(src_index.row(), 0)
        model_id = item.data(Qt.UserRole) if item else None
        return model_id

    def get_selected_models(self) -> List[int]:
        """Get IDs of all selected models."""
        from .library_event_handler import ViewMode

        view = (
            self.library_widget.list_view
            if self.library_widget.view_mode == ViewMode.LIST
            else self.library_widget.grid_view
        )
        model_ids: List[int] = []
        for idx in view.selectedIndexes():
            src = self.library_widget.proxy_model.mapToSource(idx)
            item = self.library_widget.list_model.item(src.row(), 0)
            if item:
                mid = item.data(Qt.UserRole)
                if mid and mid not in model_ids:
                    model_ids.append(mid)
        return model_ids

    @monitor_operation("load_models_to_library")
    def load_models(self, file_paths: List[str]) -> None:
        """Load models from file paths."""
        if self.library_widget.loading_in_progress or self.library_widget._disposed:
            QMessageBox.information(self.library_widget, "Loading", "Models are currently being loaded. Please wait.")
            return

        op_id = self.library_widget.performance_monitor.start_operation(
            "load_models_batch", {"file_count": len(file_paths)}
        )

        self.library_widget.loading_in_progress = True
        self.library_widget.progress_bar.setVisible(True)
        self.library_widget.progress_bar.setRange(0, 0)
        self.library_widget.status_label.setText("Loading models...")

        from .model_load_worker import ModelLoadWorker

        self.library_widget.model_loader = ModelLoadWorker(file_paths)
        self.library_widget.model_loader.model_loaded.connect(self.on_model_loaded)
        self.library_widget.model_loader.progress_updated.connect(self.on_load_progress)
        self.library_widget.model_loader.error_occurred.connect(self.on_load_error)
        self.library_widget.model_loader.finished.connect(self.on_load_finished)
        self.library_widget.model_loader.start()
        self.library_widget._load_operation_id = op_id

    def on_model_loaded(self, model_info: Dict[str, Any]) -> None:
        """Handle model loaded event."""
        if self.library_widget._disposed or self.library_widget.model_loader is None:
            return
        try:
            model_id = self.library_widget.db_manager.add_model(
                filename=model_info["filename"],
                format=model_info["format"],
                file_path=model_info["file_path"],
                file_size=model_info["file_size"],
                file_hash=None,
            )
            self.library_widget.db_manager.add_model_metadata(model_id=model_id, title=model_info["filename"], description="")
            thumb = self.library_widget.thumbnail_generator.generate_thumbnail(model_info)
            model_info["id"] = model_id
            model_info["thumbnail"] = thumb
            self.library_widget.current_models.append(model_info)
        except Exception as e:
            self.logger.error(f"Failed to save model to database: {e}")

    def on_load_progress(self, progress_percent: float, message: str) -> None:
        """Handle load progress update."""
        if self.library_widget._disposed or self.library_widget.model_loader is None:
            return
        self.library_widget.progress_bar.setRange(0, 100)
        self.library_widget.progress_bar.setValue(int(progress_percent))

        total_files = len(self.library_widget.model_loader.file_paths)
        current_item = int((progress_percent / 100.0) * total_files) + 1
        current_item = min(current_item, total_files)

        if total_files > 1:
            status_text = f"{message} ({current_item} of {total_files} = {int(progress_percent)}%)"
        else:
            status_text = f"{message} ({int(progress_percent)}%)"

        self.library_widget.status_label.setText(status_text)

    def on_load_error(self, error_message: str) -> None:
        """Handle load error."""
        if self.library_widget._disposed or self.library_widget.model_loader is None:
            return
        self.logger.error(error_message)
        QMessageBox.warning(self.library_widget, "Loading Error", error_message)

    def on_load_finished(self) -> None:
        """Handle load finished."""
        if self.library_widget._disposed:
            if self.library_widget.model_loader:
                try:
                    try:
                        self.library_widget.model_loader.model_loaded.disconnect(self.on_model_loaded)
                    except Exception:
                        pass
                    try:
                        self.library_widget.model_loader.progress_updated.disconnect(self.on_load_progress)
                    except Exception:
                        pass
                    try:
                        self.library_widget.model_loader.error_occurred.disconnect(self.on_load_error)
                    except Exception:
                        pass
                    try:
                        self.library_widget.model_loader.finished.disconnect(self.on_load_finished)
                    except Exception:
                        pass
                except Exception:
                    pass
            return

        self.library_widget.loading_in_progress = False
        self.library_widget.progress_bar.setVisible(False)
        self.library_widget.status_label.setText("Ready")
        self.library_widget.models_added.emit(self.get_selected_models())

        if self.library_widget.model_loader:
            try:
                self.library_widget.model_loader.model_loaded.disconnect(self.on_model_loaded)
                self.library_widget.model_loader.progress_updated.disconnect(self.on_load_progress)
                self.library_widget.model_loader.error_occurred.disconnect(self.on_load_error)
                self.library_widget.model_loader.finished.disconnect(self.on_load_finished)
            except Exception:
                pass

        self.update_model_view()
        self.library_widget.performance_monitor.end_operation(self.library_widget._load_operation_id, success=True)

