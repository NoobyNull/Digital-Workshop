"""
Model Library Widget - Main entry point for model library functionality.

This is a thin coordinator that delegates to specialized components via the facade pattern.
"""

from typing import Optional, List, Dict, Any

from PySide6.QtCore import Signal, Qt, QEvent
from PySide6.QtWidgets import QWidget, QSizePolicy, QMenu
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QCloseEvent, QWheelEvent

from src.core.logging_config import get_logger
from src.core.database_manager import get_database_manager
from src.core.performance_monitor import get_performance_monitor
from src.core.model_cache import get_model_cache
from src.core.root_folder_manager import RootFolderManager
from src.core.model_recent_service import get_recent_models, set_recent_favorite
from src.gui.theme import MIN_WIDGET_SIZE

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
    import_requested = Signal(list)
    import_url_requested = Signal()
    progress_updated = Signal(float, str)
    load_finished = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the model library widget.

        Args:
            parent: Parent widget (optional)
        """
        super().__init__(parent)

        # Set flexible size policy to allow shrinking when tabbed with other widgets
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # Set minimum size to prevent zero-width/zero-height widgets
        self.setMinimumSize(MIN_WIDGET_SIZE, MIN_WIDGET_SIZE)

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
        self.recent_models_panel = None

        # Initialize facade (coordinates all components)
        self.facade = ModelLibraryFacade(self)

        # Initialize UI and load data
        self.facade.initialize()
        self._connect_recent_panel_signals()
        self.refresh_recent_models()

        # Schedule column visibility restoration after a delay to ensure dock layout is restored first
        from PySide6.QtCore import QTimer

        QTimer.singleShot(200, self.restore_column_visibility)
        # Provide a fallback context menu on empty space to access import actions even when the view doesn't fire its own menu.
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_fallback_context_menu)

        # Provide a fallback context menu on the widget itself so users can always reach Import.
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_fallback_context_menu)

    # ==================== Public API ====================

    def restore_column_visibility(self) -> None:
        """Restore column visibility and order from settings (called after dock layout restoration)."""
        from PySide6.QtCore import QSettings

        settings = QSettings("DigitalWorkshop", "ModelLibrary")

        self.logger.debug("[DELAYED] Restoring column visibility from settings...")
        for col in range(8):  # Now 8 columns (Thumbnail + 7 others)
            # Get visibility setting - default to True (visible)
            visible_value = settings.value(f"column_{col}_visible", True)
            # Convert to bool explicitly (QSettings may return string "true"/"false")
            if isinstance(visible_value, str):
                visible = visible_value.lower() in ("true", "1", "yes")
            else:
                visible = bool(visible_value)
            self.logger.debug(
                "[DELAYED] Restoring column %s visibility: raw=%r, converted=%s",
                col,
                visible_value,
                visible,
            )
            self.list_view.setColumnHidden(col, not visible)

        # Restore column order
        column_order = settings.value("column_order")
        if column_order:
            self.logger.debug("[DELAYED] Restoring column order: %s", column_order)
            header = self.list_view.horizontalHeader()
            # Convert to list of ints if needed
            if isinstance(column_order, str):
                # QSettings might return as string, try to parse
                try:
                    import ast

                    column_order = ast.literal_eval(column_order)
                except:
                    column_order = None

            if column_order and isinstance(column_order, list):
                # Restore the visual order
                for logical_index, visual_index in enumerate(column_order):
                    if isinstance(visual_index, int):
                        header.moveSection(
                            header.visualIndex(logical_index), visual_index
                        )
                self.logger.debug("[DELAYED] Column order restored successfully")
            else:
                self.logger.debug(
                    "[DELAYED] Invalid column order format: %r", column_order
                )
        else:
            self.logger.debug("[DELAYED] No saved column order found")

    def _show_fallback_context_menu(self, pos) -> None:
        """Show a minimal import menu when right-clicking empty space."""
        try:
            menu = QMenu(self)
            import_action = menu.addAction("Import Models…")
            import_url_action = menu.addAction("Import from URL…")
            # Map the widget-local position to global so the menu appears where the user clicked.
            global_pos = self.mapToGlobal(pos)
            action = menu.exec(global_pos)
            if action == import_action:
                self.import_requested.emit([])
            elif action == import_url_action:
                self.import_url_requested.emit()
        except Exception as exc:
            self.logger.warning("Failed to show fallback context menu: %s", exc)

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

    def refresh_models_from_database(self) -> None:
        """Public wrapper to reload models from the database."""
        self._load_models_from_database()

    def load_models(self, file_paths: List[str]) -> None:
        """Public wrapper to load models from provided file paths."""
        self._load_models(file_paths)

    def refresh_recent_models(self) -> None:
        """Refresh the MRU panel with the latest database entries."""

        panel = getattr(self, "recent_models_panel", None)
        if not panel:
            return

        try:
            entries = get_recent_models()
            panel.set_entries(entries)
        except Exception as exc:
            self.logger.debug("Failed to refresh recent models panel: %s", exc)
            panel.set_entries([])

    def _connect_recent_panel_signals(self) -> None:
        """Wire MRU panel interactions to library signals."""

        panel = getattr(self, "recent_models_panel", None)
        if not panel:
            return

        try:
            panel.entry_activated.connect(self._handle_recent_entry_activated)
            panel.favorite_toggled.connect(self._handle_recent_favorite_toggled)
        except Exception as exc:
            self.logger.debug("Recent models panel unavailable: %s", exc)

    def _handle_recent_entry_activated(self, model_id: int) -> None:
        """Forward MRU double-clicks to the same signal as the main list."""

        self.model_double_clicked.emit(model_id)

    def _handle_recent_favorite_toggled(self, model_id: int, is_favorite: bool) -> None:
        """Persist favorite changes from the MRU panel."""

        try:
            if set_recent_favorite(model_id, is_favorite):
                self.refresh_recent_models()
        except Exception as exc:
            self.logger.warning(
                "Failed to update favorite state for model %s: %s", model_id, exc
            )

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

    def _import_from_context_menu(self, file_path: str) -> None:
        """Import a specific file path from the file tree context menu.

        This delegates to the file browser's unified import request helper,
        which in turn raises the ``import_requested`` signal so the main
        window can open the Import wizard.
        """
        try:
            # Reuse the file browser's request mechanism to preserve the
            # unified import pipeline and avoid duplicating logic here.
            self.facade.file_browser._request_import([file_path])
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.warning("Failed to request import from context menu: %s", exc)

    def _request_import_from_url(self) -> None:
        """Forward a request to import via URL to the main window."""

        try:
            self.import_url_requested.emit()
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.warning("Failed to emit import_url_requested: %s", exc)

    def _open_in_native_app(self, file_path: str) -> None:
        """Open file in native application."""
        self.facade.file_browser.open_in_native_app(file_path)

    def _refresh_model_display(self, model_id: Optional[int] = None) -> None:
        """Refresh model display.

        Args:
            model_id: Optional model ID to refresh specifically, or None to refresh all
        """
        if model_id is not None:
            # Refresh specific model - find and update its thumbnail
            from PySide6.QtGui import QPixmapCache, QIcon
            from pathlib import Path

            # Clear Qt's pixmap cache to force reload
            QPixmapCache.clear()

            # Find the model in current_models
            for i, model in enumerate(self.current_models):
                if model.get("id") == model_id:
                    # Get the thumbnail path from database (it might have been updated)
                    updated_model = self.db_manager.get_model(model_id)
                    if updated_model:
                        thumbnail_path = updated_model.get("thumbnail_path")
                        if thumbnail_path and Path(thumbnail_path).exists():
                            # Find the item in the list model
                            for row in range(self.list_model.rowCount()):
                                item = self.list_model.item(row, 0)
                                if item and item.data(Qt.UserRole) == model_id:
                                    # Update the icon with the new thumbnail
                                    icon = QIcon(thumbnail_path)
                                    item.setIcon(icon)
                                    # Update the model in current_models
                                    self.current_models[i] = updated_model
                                    break
                    break
        else:
            # Refresh all models
            self.facade.model_manager.update_model_view()

    # ==================== Event Handlers ====================

    def eventFilter(self, obj, event: QEvent) -> bool:
        """
        Event filter to catch wheel events on list/grid view viewports.

        Args:
            obj: Object that received the event
            event: Event to filter

        Returns:
            True if event was handled, False otherwise
        """
        if event.type() == QEvent.Wheel and isinstance(event, QWheelEvent):
            # Check if Ctrl is pressed
            if event.modifiers() & Qt.ControlModifier:
                # Handle the wheel event for zoom
                delta = event.angleDelta().y()

                # Determine which view is active
                is_grid_view = obj == self.grid_view.viewport()

                if is_grid_view:
                    # Grid view zoom
                    self.logger.debug(
                        "EventFilter wheel (grid): delta=%s, current_size={self.current_grid_icon_size}",
                        delta,
                    )

                    # Calculate new icon size (larger steps for grid)
                    if delta > 0:
                        step = 16  # Scroll up = zoom in
                    else:
                        step = -16  # Scroll down = zoom out

                    new_size = self.current_grid_icon_size + step
                    self.logger.debug("EventFilter new grid size: %s", new_size)

                    # Update grid icon size
                    self.facade.ui_manager.set_grid_icon_size(new_size)
                else:
                    # List view zoom
                    self.logger.debug(
                        "EventFilter wheel (list): delta=%s, current_height={self.current_row_height}",
                        delta,
                    )

                    # Calculate new row height
                    if delta > 0:
                        step = 8  # Scroll up = zoom in
                    else:
                        step = -8  # Scroll down = zoom out

                    new_height = self.current_row_height + step
                    self.logger.debug("EventFilter new row height: %s", new_height)

                    # Update row height
                    self.facade.ui_manager.set_row_height(new_height)

                # Event handled
                return True

        # Pass event to parent
        return super().eventFilter(obj, event)

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

    def wheelEvent(self, event: QWheelEvent) -> None:
        """
        Handle mouse wheel events for row height zoom (Ctrl+Scroll).

        Args:
            event: Wheel event
        """
        # Only handle if Ctrl is pressed
        if event.modifiers() & Qt.ControlModifier:
            # Get scroll delta (positive = scroll up, negative = scroll down)
            delta = event.angleDelta().y()

            # Debug logging
            self.logger.debug(
                "Wheel event: delta=%s, current_height={self.current_row_height}", delta
            )

            # Calculate new row height (scroll up = increase, scroll down = decrease)
            # Use step size of 8 pixels per scroll notch
            if delta > 0:
                step = 8  # Scroll up = zoom in
            else:
                step = -8  # Scroll down = zoom out

            new_height = self.current_row_height + step
            self.logger.debug("New height: %s", new_height)

            # Update row height through UI manager
            self.facade.ui_manager.set_row_height(new_height)

            # Accept event to prevent propagation
            event.accept()
        else:
            # Pass to parent for normal scrolling
            super().wheelEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Handle widget close event.

        Args:
            event: Close event
        """
        self.cleanup()
        super().closeEvent(event)
