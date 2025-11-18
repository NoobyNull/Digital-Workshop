"""
Model management for library.

Handles model loading, database integration, and view updates.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import threading

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtGui import QIcon, QStandardItem
from PySide6.QtWidgets import QMessageBox

from src.core.logging_config import get_logger, log_function_call
from src.core.model_tags import TAG_DIRTY
from src.core.performance_monitor import monitor_operation
from .async_tasks import CombinedModelProcessingTask
from .progress_throttler import BatchProgressTracker

logger = get_logger(__name__)


class LibraryModelManager:
    """Manages model loading and database integration."""

    def __init__(self, library_widget) -> None:
        """
        Initialize model manager.

        Args:
            library_widget: The model library widget
        """
        self.library_widget = library_widget
        self.logger = get_logger(__name__)

        # Thread pool for async operations
        self.thread_pool = QThreadPool.globalInstance()
        self.logger.info(
            "Using global thread pool with %d threads", self.thread_pool.maxThreadCount()
        )

        # Progress tracking
        self.progress_tracker: Optional[BatchProgressTracker] = None

        # Pending models waiting for async processing to complete
        self._pending_models: List[Dict[str, Any]] = []
        self._pending_lock = threading.Lock()
        self._completed_count = 0
        self._total_expected = 0

    @log_function_call(logger)
    def load_models_from_database(self) -> None:
        """Load models from the database into the view."""
        try:
            self.library_widget.status_label.setText("Loading models...")
            self.library_widget.current_models = self.library_widget.db_manager.get_all_models()
            self.update_model_view()
            self.library_widget.model_count_label.setText(
                f"Models: {len(self.library_widget.current_models)}"
            )
            self.library_widget.status_label.setText("Ready")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to load models from database: %s", e)
            self.library_widget.status_label.setText("Error loading models")

    def update_model_view(self) -> None:
        """Populate list/grid views from current_models."""
        self.library_widget.list_model.clear()
        self.library_widget.list_model.setHorizontalHeaderLabels(
            [
                "Thumbnail",
                "Name",
                "Format",
                "Size",
                "Triangles",
                "Category",
                "Added Date",
                "Dirty",
            ]
        )

        for model in self.library_widget.current_models:
            # Create thumbnail item (first column)
            thumbnail_item = QStandardItem()
            thumbnail_item.setData(model.get("id"), Qt.UserRole)

            # Set icon from thumbnail if available
            thumbnail_path = model.get("thumbnail_path")
            if thumbnail_path and Path(thumbnail_path).exists():
                try:
                    icon = QIcon(thumbnail_path)
                    thumbnail_item.setIcon(icon)
                except (
                    OSError,
                    IOError,
                    ValueError,
                    TypeError,
                    KeyError,
                    AttributeError,
                ) as e:
                    self.logger.warning("Failed to load thumbnail icon: %s", e)

            # Thumbnail item should not be editable
            thumbnail_item.setEditable(False)

            # Create name item (second column)
            name_item = QStandardItem(model.get("title") or model.get("filename", "Unknown"))
            name_item.setData(model.get("id"), Qt.UserRole)
            name_item.setEditable(False)  # Not editable - use metadata editor to change name

            fmt = (model.get("format") or "Unknown").upper()
            format_item = QStandardItem(fmt)
            format_item.setEditable(False)

            # Size column - store numeric value for proper sorting
            size_bytes = model.get("file_size", 0) or 0
            if size_bytes > 1024 * 1024:
                size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
            elif size_bytes > 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes} B"
            size_item = QStandardItem(size_str)
            size_item.setData(size_bytes, Qt.UserRole)  # Store numeric value for sorting
            size_item.setEditable(False)

            # Triangles column - store numeric value for proper sorting
            triangle_count = model.get("triangle_count", 0) or 0
            triangles_item = QStandardItem(f"{triangle_count:,}")
            triangles_item.setData(triangle_count, Qt.UserRole)  # Store numeric value for sorting
            triangles_item.setEditable(False)

            category_item = QStandardItem(model.get("category", "Uncategorized"))
            category_item.setEditable(False)

            date_item = QStandardItem(str(model.get("date_added", "Unknown")))
            date_item.setEditable(False)

            # Dirty status column - based on TAG_DIRTY presence in keywords
            keywords_value = model.get("keywords") or ""
            keyword_tags = [
                tag.strip() for tag in str(keywords_value).split(",") if tag and tag.strip()
            ]
            is_dirty = TAG_DIRTY in keyword_tags

            dirty_item = QStandardItem("Dirty" if is_dirty else "")
            dirty_item.setEditable(False)
            dirty_item.setData(is_dirty, Qt.UserRole)

            self.library_widget.list_model.appendRow(
                [
                    thumbnail_item,
                    name_item,
                    format_item,
                    size_item,
                    triangles_item,
                    category_item,
                    date_item,
                    dirty_item,
                ]
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
            QMessageBox.information(
                self.library_widget,
                "Loading",
                "Models are currently being loaded. Please wait.",
            )
            return

        op_id = self.library_widget.performance_monitor.start_operation(
            "load_models_batch", {"file_count": len(file_paths)}
        )

        self.library_widget.loading_in_progress = True
        self.library_widget.progress_bar.setVisible(True)
        self.library_widget.progress_bar.setRange(0, 0)
        self.library_widget.status_label.setText("Loading models...")

        # Initialize async processing state
        with self._pending_lock:
            self._completed_count = 0
            self._total_expected = len(file_paths)
            self._pending_models.clear()

        # Initialize progress tracker with throttling
        self.progress_tracker = BatchProgressTracker(
            total_items=len(file_paths),
            progress_callback=self._on_progress_update,
            throttle_ms=100.0,  # Update UI at most every 100ms
        )

        self.logger.info("Starting batch load of %d models with async processing", len(file_paths))

        from .model_load_worker import ModelLoadWorker

        self.library_widget.model_loader = ModelLoadWorker(file_paths)
        self.library_widget.model_loader.model_loaded.connect(self.on_model_loaded)
        self.library_widget.model_loader.progress_updated.connect(self.on_load_progress)
        self.library_widget.model_loader.error_occurred.connect(self.on_load_error)
        self.library_widget.model_loader.finished.connect(self.on_load_finished)
        self.library_widget.model_loader.start()
        self.library_widget._load_operation_id = op_id

    def on_model_loaded(self, model_info: Dict[str, Any]) -> None:
        """
        Handle model loaded event - dispatch async processing task.

        This method now runs on the main thread but immediately dispatches
        the database and thumbnail operations to a thread pool worker,
        preventing UI blocking.
        """
        if self.library_widget._disposed or self.library_widget.model_loader is None:
            return

        try:
            # Create async task for database insert and thumbnail generation
            task = CombinedModelProcessingTask(
                model_info=model_info,
                db_manager=self.library_widget.db_manager,
                thumbnail_generator=self.library_widget.thumbnail_generator,
                task_index=self._completed_count,
                total_tasks=self._total_expected,
            )

            # Connect signals
            task.signals.database_completed.connect(self._on_async_task_completed)
            task.signals.database_failed.connect(self._on_async_task_failed)

            # Dispatch to thread pool (non-blocking)
            self.thread_pool.start(task)

            self.logger.debug(
                "Dispatched async task for %s (active threads: %d)",
                model_info.get("filename", "unknown"),
                self.thread_pool.activeThreadCount(),
            )

        except Exception as e:
            self.logger.error(
                "Failed to dispatch async task for %s: %s",
                model_info.get("filename", "unknown"),
                e,
                exc_info=True,
            )

    def _on_async_task_completed(self, model_info: Dict[str, Any]) -> None:
        """
        Handle completion of async processing task.

        This runs on the main thread (via Qt signal/slot) but only performs
        lightweight UI updates.
        """
        try:
            with self._pending_lock:
                # Add to current models list
                self.library_widget.current_models.append(model_info)
                self._completed_count += 1

                # Update progress
                if self.progress_tracker:
                    self.progress_tracker.increment(
                        f"Processed {model_info.get('filename', 'unknown')}"
                    )

                self.logger.debug(
                    "Async task completed for %s (ID: %d) - %d/%d complete",
                    model_info.get("filename", "unknown"),
                    model_info.get("id", -1),
                    self._completed_count,
                    self._total_expected,
                )

                # Check if all tasks are complete
                if self._completed_count >= self._total_expected:
                    self.logger.info(
                        "All async tasks completed (%d/%d)",
                        self._completed_count,
                        self._total_expected,
                    )
                    # Trigger final UI update
                    self._finalize_batch_load()

        except Exception as e:
            self.logger.error("Error handling async task completion: %s", e, exc_info=True)

    def _on_async_task_failed(self, file_path: str, error_message: str) -> None:
        """Handle failure of async processing task."""
        self.logger.error("Async task failed for %s: %s", file_path, error_message)

        with self._pending_lock:
            self._completed_count += 1

            if self.progress_tracker:
                self.progress_tracker.increment_failed(error_message)

            # Check if all tasks are complete (including failures)
            if self._completed_count >= self._total_expected:
                self._finalize_batch_load()

    def _finalize_batch_load(self) -> None:
        """Finalize batch loading - update UI with all loaded models."""
        try:
            # Finish progress tracking
            if self.progress_tracker:
                self.progress_tracker.finish("All models processed")
                self.progress_tracker = None

            # Refresh the view with all models
            self.update_model_view()

            self.logger.info(
                "Batch load finalized: %d models loaded", len(self.library_widget.current_models)
            )

        except Exception as e:
            self.logger.error("Error finalizing batch load: %s", e, exc_info=True)

    def _on_progress_update(self, current: int, total: int, message: str) -> None:
        """
        Handle throttled progress updates.

        This is called by the progress tracker at most every 100ms.
        """
        try:
            if self.library_widget._disposed:
                return

            # Update progress bar
            if total > 0:
                progress_percent = int((current / total) * 100)
                self.library_widget.progress_bar.setRange(0, 100)
                self.library_widget.progress_bar.setValue(progress_percent)

            # Update status label
            status_text = f"Processing models: {current}/{total} ({message})"
            self.library_widget.status_label.setText(status_text)

        except Exception as e:
            self.logger.error("Error updating progress: %s", e, exc_info=True)

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
                        self.library_widget.model_loader.model_loaded.disconnect(
                            self.on_model_loaded
                        )
                    except Exception:
                        pass
                    try:
                        self.library_widget.model_loader.progress_updated.disconnect(
                            self.on_load_progress
                        )
                    except Exception:
                        pass
                    try:
                        self.library_widget.model_loader.error_occurred.disconnect(
                            self.on_load_error
                        )
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
        self.library_widget.performance_monitor.end_operation(
            self.library_widget._load_operation_id, success=True
        )

        # Trigger post-import deduplication
        self._trigger_post_import_deduplication()

    def _trigger_post_import_deduplication(self) -> None:
        """Trigger deduplication after models are imported."""
        try:
            # Get main window reference
            main_window = self.library_widget.window()
            if not main_window or not hasattr(main_window, "dedup_service"):
                self.logger.debug("Main window or dedup_service not available")
                return

            # Start hashing for newly imported models
            if hasattr(main_window, "dedup_service") and main_window.dedup_service:
                self.logger.info("Starting post-import deduplication")
                main_window.dedup_service.start_hashing()

                # Find duplicates
                duplicates = main_window.dedup_service.dedup_manager.find_all_duplicates()
                duplicate_count = main_window.dedup_service.dedup_manager.get_duplicate_count()

                if duplicate_count > 0:
                    main_window.dedup_service.pending_duplicates = duplicates
                    main_window.dedup_service.duplicates_found.emit(duplicate_count)
                    self.logger.info("Found %s duplicate models after import", duplicate_count)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to trigger post-import deduplication: %s", e)
