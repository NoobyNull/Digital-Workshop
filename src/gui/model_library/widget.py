"""
Model Library Widget - Main entry point for model library functionality.

This is a thin coordinator that delegates to specialized components via the facade pattern.
"""

from typing import Optional, List, Dict, Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QCloseEvent

from src.core.logging_config import get_logger
from src.core.database_manager import get_database_manager
from src.core.performance_monitor import get_performance_monitor
from src.core.model_cache import get_model_cache
from src.core.root_folder_manager import RootFolderManager

from .model_library_facade import ModelLibraryFacade
from .library_event_handler import ViewMode
from .thumbnail_generator import ThumbnailGenerator
from .model_load_worker import ModelLoadWorker


class ModelLibraryWidget(QWidget):
    """
    Main model library widget.

    Provides a unified interface for:
    - File browser with multi-root support
    - List/Grid views of models
    - Drag-and-drop import
    - Background loading with progress
    - Database integration
    - Search and filtering
    - Context menus for operations
    - Metadata editing
    - Thumbnail generation

    Signals:
        model_selected: Emitted when a model is selected (model_id: int)
        model_double_clicked: Emitted when a model is double-clicked (model_id: int)
        models_added: Emitted when models are added (model_ids: List[int])
    """

    # Public signals
    model_selected = Signal(int)
    model_double_clicked = Signal(int)
    models_added = Signal(list)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the model library widget.

        Args:
            parent: Parent widget (optional)
        """
        super().__init__(parent)

        # Core services
        self.logger = get_logger(__name__)
        self.db_manager = get_database_manager()
        self.performance_monitor = get_performance_monitor()
        self.model_cache = get_model_cache()
        self.root_folder_manager = RootFolderManager.get_instance()

        # Component instances
        self.thumbnail_generator = ThumbnailGenerator()
        self.model_loader: Optional[ModelLoadWorker] = None

        # State
        self.current_models: List[Dict[str, Any]] = []
        self.view_mode = ViewMode.LIST
        self.loading_in_progress = False
        self._disposed = False

        # Initialize facade (coordinates all components)
        self.facade = ModelLibraryFacade(self)

        # Initialize UI and load data
        self.facade.initialize()

    # ==================== Public API ====================

    def get_selected_model_id(self) -> Optional[int]:
        """
        Get the ID of the currently selected model.

        Returns:
            Model ID if a model is selected, None otherwise
        """
        return self.facade.get_selected_model_id()

    def get_selected_models(self) -> List[int]:
        """
        Get IDs of all currently selected models.

        Returns:
            List of model IDs
        """
        return self.facade.get_selected_models()

    def cleanup(self) -> None:
        """Clean up resources before closing."""
        if self._disposed:
            return

        self.logger.info("Cleaning up ModelLibraryWidget")
        self._disposed = True

        # Cancel any ongoing loading
        if self.model_loader and self.model_loader.isRunning():
            self.logger.info("Cancelling model loader thread")
            self.model_loader.cancel()
            self.model_loader.wait(2000)
            if self.model_loader.isRunning():
                self.logger.warning("Model loader thread did not stop gracefully")
                self.model_loader.terminate()
                self.model_loader.wait()

        # Clear references
        self.current_models.clear()
        self.model_loader = None

        self.logger.info("ModelLibraryWidget cleanup complete")

    # ==================== Internal Methods (Delegation) ====================

    def _on_indexing_started(self) -> None:
        """Handle file system indexing started."""
        self.facade.file_browser.on_indexing_started()

    def _on_indexing_completed(self) -> None:
        """Handle file system indexing completed."""
        self.facade.file_browser.on_indexing_completed()

    def _refresh_file_browser(self) -> None:
        """Refresh the file browser."""
        self.facade.file_browser.refresh_file_browser()

    def _apply_filters(self) -> None:
        """Apply search filters."""
        self.facade.event_handler.apply_filters()

    def _load_models_from_database(self) -> None:
        """Load models from database."""
        self.facade.model_manager.load_models_from_database()

    def _load_models(self, file_paths: List[str]) -> None:
        """Load models from file paths."""
        self.facade.model_manager.load_models(file_paths)

    def _import_selected_files(self) -> None:
        """Import selected files from file browser."""
        self.facade.file_browser.import_selected_files()

    def _import_selected_folder(self) -> None:
        """Import selected folder from file browser."""
        self.facade.file_browser.import_selected_folder()

    def _remove_model(self, model_id: int) -> None:
        """Remove a model."""
        self.facade.event_handler.remove_model(model_id)

    def _import_from_context_menu(self) -> None:
        """Import from context menu."""
        self.facade.file_browser.import_selected_files()

    def _open_in_native_app(self, file_path: str) -> None:
        """Open file in native application."""
        self.facade.file_browser.open_in_native_app(file_path)

    def _refresh_model_display(self) -> None:
        """Refresh model display."""
        self.facade.model_manager.update_model_view()

    # ==================== Event Handlers ====================

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """
        Handle drag enter events.

        Args:
            event: Drag enter event
        """
        self.facade.event_handler.drag_enter_event(event)

    def dropEvent(self, event: QDropEvent) -> None:
        """
        Handle drop events.

        Args:
            event: Drop event
        """
        self.facade.event_handler.drop_event(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Handle widget close event.

        Args:
            event: Close event
        """
        self.cleanup()
        super().closeEvent(event)
