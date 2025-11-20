"""
Event handling for model library.

Handles user interactions, filtering, and drag-and-drop.
"""

from enum import Enum
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, QModelIndex, QRegularExpression
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QMenu, QMessageBox, QFileDialog, QInputDialog, QDialog

from src.core.logging_config import get_logger
from src.core.root_folder_manager import RootFolderManager
from src.core.import_thumbnail_service import ImportThumbnailService
from src.core.fast_hasher import FastHasher
from src.core.database_manager import get_database_manager

logger = get_logger(__name__)


class ViewMode(Enum):
    """View mode enumeration."""

    LIST = "list"
    GRID = "grid"


class LibraryEventHandler:
    """Handles events and user interactions in the library."""

    def __init__(self, library_widget) -> None:
        """
        Initialize event handler.

        Args:
            library_widget: The model library widget
        """
        self.library_widget = library_widget
        self.logger = get_logger(__name__)

    def setup_connections(self) -> None:
        """Setup signal connections."""
        self.logger.info("Setting up connections in LibraryEventHandler")

        self.library_widget.view_tabs.currentChanged.connect(self.on_tab_changed)

        self.library_widget.file_tree.clicked.connect(self.on_file_tree_clicked)

        self.library_widget.import_selected_button.clicked.connect(
            self.library_widget._import_selected_files
        )
        self.library_widget.import_folder_button.clicked.connect(
            self.library_widget._import_selected_folder
        )

        self.library_widget.list_view.clicked.connect(self.on_model_clicked)
        self.library_widget.list_view.doubleClicked.connect(self.on_model_double_clicked)
        self.library_widget.grid_view.clicked.connect(self.on_model_clicked)
        self.library_widget.grid_view.doubleClicked.connect(self.on_model_double_clicked)

        # Search and filter controls
        self.library_widget.search_box.textChanged.connect(self.apply_filters)
        if hasattr(self.library_widget, "category_filter"):
            self.library_widget.category_filter.currentIndexChanged.connect(self.apply_filters)
        if hasattr(self.library_widget, "dirty_filter"):
            self.library_widget.dirty_filter.currentIndexChanged.connect(self.apply_filters)

        self.library_widget.setAcceptDrops(True)
        self.library_widget.list_view.setAcceptDrops(True)
        self.library_widget.grid_view.setAcceptDrops(True)

        self.library_widget.list_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.library_widget.list_view.customContextMenuRequested.connect(self.show_context_menu)
        self.library_widget.grid_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.library_widget.grid_view.customContextMenuRequested.connect(self.show_context_menu)

        # Set up file tree context menu
        self.logger.info(
            f"Setting up file_tree context menu. Widget exists: {hasattr(self.library_widget, 'file_tree')}"
        )
        if hasattr(self.library_widget, "file_tree"):
            self.library_widget.file_tree.setContextMenuPolicy(Qt.CustomContextMenu)
            self.library_widget.file_tree.customContextMenuRequested.connect(
                self.show_file_tree_context_menu
            )
            self.logger.info("File tree context menu connection established")
        else:
            self.logger.error("file_tree widget not found!")

    def on_tab_changed(self, index: int) -> None:
        """Handle tab change to update view mode."""
        if index == 0:
            self.library_widget.view_mode = ViewMode.LIST
        else:
            self.library_widget.view_mode = ViewMode.GRID

    def on_file_tree_clicked(self, index: QModelIndex) -> None:
        """Handle file tree click."""
        try:
            source_index = self.library_widget.file_proxy_model.mapToSource(index)
            path = self.library_widget.file_model.get_file_path(source_index)
            if hasattr(self.library_widget, "path_display") and path:
                self.library_widget.path_display.setText(path)
        except Exception:
            pass

    def apply_filters(self) -> None:
        """Apply search, category, and dirty/clean filters."""
        if self.library_widget._disposed or not hasattr(self.library_widget, "proxy_model"):
            return

        text = (
            self.library_widget.search_box.text()
            if hasattr(self.library_widget, "search_box")
            else ""
        )
        advanced = text  # unified: the main search box accepts boolean syntax too

        # Treat the main search box as the advanced query; fall back to regex if parsing fails
        try:
            self.library_widget.proxy_model.set_advanced_query(advanced)
            # Clear regex so advanced boolean search drives filtering
            self.library_widget.proxy_model.setFilterRegularExpression(QRegularExpression())
        except Exception:
            try:
                self.library_widget.proxy_model.set_advanced_query("")
                self.library_widget.proxy_model.setFilterRegularExpression(
                    QRegularExpression(text, QRegularExpression.CaseInsensitiveOption)
                )
            except Exception:
                self.library_widget.proxy_model.setFilterFixedString(text or "")

        # Apply category filter via the proxy model
        category_value = None
        if hasattr(self.library_widget, "category_filter"):
            category_value = self.library_widget.category_filter.currentData()

        # Apply dirty/clean filter via the proxy model
        dirty_filter_value = None
        if hasattr(self.library_widget, "dirty_filter"):
            dirty_filter_value = self.library_widget.dirty_filter.currentData()

        proxy_model = self.library_widget.proxy_model
        if hasattr(proxy_model, "set_category_filter"):
            proxy_model.set_category_filter(category_value)
        if hasattr(proxy_model, "set_dirty_filter"):
            proxy_model.set_dirty_filter(dirty_filter_value)

    def on_model_clicked(self, index: QModelIndex) -> None:
        """Handle model click."""
        try:
            src_index = self.library_widget.proxy_model.mapToSource(index)
            item = self.library_widget.list_model.item(src_index.row(), 0)
            if item:
                model_id = item.data(Qt.UserRole)
                if model_id:
                    self.library_widget.model_selected.emit(model_id)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning("Failed to handle model click: %s", e)

    def on_model_double_clicked(self, index: QModelIndex) -> None:
        """Handle model double-click."""
        try:
            src_index = self.library_widget.proxy_model.mapToSource(index)
            item = self.library_widget.list_model.item(src_index.row(), 0)
            if item:
                model_id = item.data(Qt.UserRole)
                if model_id:
                    self.library_widget.model_double_clicked.emit(model_id)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning("Failed to handle model double-click: %s", e)

    def show_context_menu(self, position) -> None:
        """Show context menu for models.

        Provides model-specific actions when a row is clicked and always
        offers an option to open the unified Import wizard.
        """
        try:
            sender_view = self.library_widget.sender()
            view = (
                sender_view
                if sender_view in (self.library_widget.list_view, self.library_widget.grid_view)
                else self.library_widget.list_view
            )
            index = view.indexAt(position)
            menu = QMenu(self.library_widget)

            model_id = None
            model_data = None

            if index.isValid():
                src_index = self.library_widget.proxy_model.mapToSource(index)
                item = self.library_widget.list_model.item(src_index.row(), 0)
                if item:
                    model_id = item.data(Qt.UserRole)

            if model_id:
                # Get model data for file path
                from src.core.database_manager import get_database_manager

                db_manager = get_database_manager()
                model_data = db_manager.get_model(model_id)

            analyze_action = open_native_action = generate_preview_action = remove_action = None

            if model_id and model_data:
                # Model operations
                analyze_action = menu.addAction("🔍 Analyze & Fix Errors")
                open_native_action = menu.addAction("📂 Open in Native App")
                menu.addSeparator()
                generate_preview_action = menu.addAction("🖼️ Generate Preview")
                menu.addSeparator()
                remove_action = menu.addAction("🗑️ Remove from Library")

            # Import wizard entry (available even when no model row is clicked)
            if menu.actions():
                menu.addSeparator()
            import_action = menu.addAction("📥 Import Models…")

            action = menu.exec(self.library_widget.list_view.mapToGlobal(position))

            if action == analyze_action:
                self._analyze_model(model_id, model_data)
            elif action == open_native_action:
                self._open_model_in_native_app(model_data)
            elif action == generate_preview_action:
                self._generate_preview(model_id)
            elif action == remove_action:
                self.library_widget._remove_model(model_id)
            elif action == import_action:
                # Trigger the unified Import wizard via the main window pipeline
                try:
                    if hasattr(self.library_widget, "import_requested"):
                        # No initial files; the dialog will handle file selection
                        self.library_widget.import_requested.emit([])
                    else:
                        parent = self.library_widget.parent()
                        if parent is not None and hasattr(parent, "_open_import_dialog"):
                            parent._open_import_dialog()
                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
                    self.logger.warning("Failed to open Import dialog from context menu: %s", exc)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning("Failed to show context menu: %s", e)

    def show_file_tree_context_menu(self, position) -> None:
        """Show context menu for file tree."""
        self.logger.info("show_file_tree_context_menu called at position: %s", position)
        try:
            index = self.library_widget.file_tree.indexAt(position)
            self.logger.info("Index valid: %s", index.isValid())

            menu = QMenu(self.library_widget)

            # Check if clicking on a valid file/folder
            if index.isValid():
                source_index = self.library_widget.file_proxy_model.mapToSource(index)
                file_path = self.library_widget.file_model.get_file_path(source_index)

                if file_path and Path(file_path).exists():
                    # Add separator before file-specific actions
                    menu.addSeparator()

                    # Differentiate between files and folders
                    path_obj = Path(file_path)
                    if path_obj.is_file():
                        # Check if it's a supported model file
                        if path_obj.suffix.lower() in [".stl", ".obj", ".3mf", ".step", ".stp"]:
                            import_action = menu.addAction("Import File")
                        else:
                            import_action = None
                    elif path_obj.is_dir():
                        import_action = menu.addAction("Import Folder")
                    else:
                        import_action = None

                    open_action = menu.addAction("Open in Explorer")

                    # Execute menu
                    action = menu.exec(self.library_widget.file_tree.mapToGlobal(position))

                    if import_action and action == import_action:
                        self.library_widget._import_from_context_menu(file_path)
                    elif action == open_action:
                        self.library_widget._open_in_native_app(file_path)
                    return

            # If no valid file/folder, don't show a context menu
            return

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to show file tree context menu: %s", e, exc_info=True)

    def _add_root_folder(self) -> None:
        """Add a new root folder via dialog."""
        try:
            # Get RootFolderManager instance
            root_folder_manager = RootFolderManager.get_instance()

            # Open folder selection dialog
            folder_path = QFileDialog.getExistingDirectory(
                self.library_widget,
                "Select Root Folder",
                str(Path.home()),
                QFileDialog.ShowDirsOnly,
            )

            if not folder_path:
                return

            # Get display name
            folder_name = Path(folder_path).name
            display_name, ok = QInputDialog.getText(
                self.library_widget,
                "Folder Display Name",
                "Enter a display name for this folder:",
                text=folder_name,
            )

            if not ok or not display_name.strip():
                return

            # Add to manager
            if root_folder_manager.add_folder(folder_path, display_name.strip()):
                QMessageBox.information(
                    self.library_widget, "Success", f"Added folder '{display_name}'"
                )
                # Refresh the file browser to show the new root folder
                if hasattr(self.library_widget, "_refresh_file_browser"):
                    self.library_widget._refresh_file_browser()
            else:
                QMessageBox.warning(
                    self.library_widget,
                    "Error",
                    "Failed to add folder. It may already exist or be inaccessible.",
                )
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to add root folder: %s", e)
            QMessageBox.critical(self.library_widget, "Error", f"Failed to add root folder: {e}")

    def drag_enter_event(self, event: QDragEnterEvent) -> None:
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    suffix = Path(url.toLocalFile()).suffix.lower()
                    if suffix in [".stl", ".obj", ".3mf", ".step", ".stp"]:
                        event.acceptProposedAction()
                        return

    def drop_event(self, event: QDropEvent) -> None:
        """Handle drop event."""
        if event.mimeData().hasUrls():
            files: List[str] = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    p = url.toLocalFile()
                    if Path(p).is_file() and Path(p).suffix.lower() in [
                        ".stl",
                        ".obj",
                        ".3mf",
                        ".step",
                        ".stp",
                    ]:
                        files.append(p)
            if files:
                if hasattr(self.library_widget, "import_requested"):
                    self.library_widget.import_requested.emit(files)
                else:
                    self.library_widget.facade.model_manager.load_models(files)

    def _generate_preview(self, model_id: int) -> None:
        """Generate preview image for a model."""
        try:
            self.logger.info("Generating preview for model ID: %s", model_id)

            # Get model information from database
            db_manager = get_database_manager()
            model = db_manager.get_model(model_id)

            if not model:
                QMessageBox.warning(self.library_widget, "Error", "Model not found in database")
                return

            model_path = model.get("file_path")
            if not model_path or not Path(model_path).exists():
                QMessageBox.warning(self.library_widget, "Error", "Model file not found on disk")
                return

            # Get file hash
            hasher = FastHasher()
            hash_result = hasher.hash_file(model_path)
            file_hash = hash_result.hash_value if hash_result.success else None

            if not file_hash:
                QMessageBox.warning(self.library_widget, "Error", "Failed to compute file hash")
                return

            # Load thumbnail settings from preferences
            from src.core.application_config import ApplicationConfig
            from PySide6.QtCore import QSettings

            config = ApplicationConfig.get_default()
            settings = QSettings()

            # Get current thumbnail preferences
            bg_image = settings.value(
                "thumbnail/background_image", config.thumbnail_bg_image, type=str
            )
            material = settings.value("thumbnail/material", config.thumbnail_material, type=str)
            bg_color = settings.value(
                "thumbnail/background_color", config.thumbnail_bg_color, type=str
            )

            # Use background image if set, otherwise use background color
            background = bg_image if bg_image else bg_color

            # Generate thumbnail with current preferences
            thumbnail_service = ImportThumbnailService()
            result = thumbnail_service.generate_thumbnail(
                model_path=model_path,
                file_hash=file_hash,
                material=material,
                background=background,
                force_regenerate=True,
            )

            if result.success:
                QMessageBox.information(
                    self.library_widget,
                    "Success",
                    f"Preview generated successfully!\nSaved to: {result.thumbnail_path}",
                )
                self.logger.info(
                    "Preview generated for model %s: {result.thumbnail_path}", model_id
                )

                # Refresh the library view to show updated thumbnail
                if hasattr(self.library_widget, "_refresh_model_display"):
                    self.library_widget._refresh_model_display(model_id)
            else:
                error_msg = result.error or "Unknown error"
                QMessageBox.warning(
                    self.library_widget,
                    "Error",
                    f"Failed to generate preview: {error_msg}",
                )
                self.logger.error("Preview generation failed for model %s: {error_msg}", model_id)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            error_msg = f"Exception during preview generation: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            QMessageBox.critical(self.library_widget, "Error", error_msg)

    def _analyze_model(self, model_id: int, model_data: dict) -> None:
        """
        Analyze model for errors and offer fixing.

        Args:
            model_id: ID of the model to analyze
            model_data: Model data dictionary from database
        """
        try:
            if not model_data:
                self.logger.warning("Analyze requested but model data was missing for id=%s", model_id)
                QMessageBox.warning(
                    self.library_widget,
                    "No Model Data",
                    "Model details are unavailable; please refresh the library and try again.",
                )
                return

            file_path = model_data.get("file_path")
            if not file_path or not Path(file_path).exists():
                QMessageBox.warning(
                    self.library_widget,
                    "File Not Found",
                    f"Model file not found: {file_path}",
                )
                return

            # Load the model
            from src.parsers.stl_parser import STLParser

            self.logger.info("Loading model for analysis: %s", file_path)
            parser = STLParser()
            model = parser.parse(file_path)

            # Normalize triangles to a list to avoid numpy truth-value ambiguity
            try:
                import numpy as np  # type: ignore

                if hasattr(model, "triangles") and isinstance(model.triangles, np.ndarray):
                    model.triangles = model.triangles.tolist()
            except Exception:
                pass

            if not model or not model.triangles or len(model.triangles) == 0:
                QMessageBox.warning(
                    self.library_widget,
                    "Invalid Model",
                    "Model has no triangles to analyze.",
                )
                return

            # Open analyzer dialog
            from src.gui.model_editor.model_analyzer_dialog import ModelAnalyzerDialog

            dialog = ModelAnalyzerDialog(model, file_path, self.library_widget)

            if dialog.exec() == QDialog.Accepted:
                # Model was fixed and saved, refresh the library
                self.logger.info("Model analyzed and fixed: %s", model_id)
                self.library_widget._refresh_model_display(model_id)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            error_msg = f"Failed to analyze model: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            QMessageBox.critical(self.library_widget, "Error", error_msg)

    def _open_model_in_native_app(self, model_data: dict) -> None:
        """
        Open model file in the system's default application.

        Args:
            model_data: Model data dictionary from database
        """
        try:
            file_path = model_data.get("file_path")
            if not file_path or not Path(file_path).exists():
                QMessageBox.warning(
                    self.library_widget,
                    "File Not Found",
                    f"Model file not found: {file_path}",
                )
                return

            # Use Qt's QDesktopServices to open the file
            from PySide6.QtCore import QUrl
            from PySide6.QtGui import QDesktopServices

            url = QUrl.fromLocalFile(file_path)
            if not QDesktopServices.openUrl(url):
                QMessageBox.warning(
                    self.library_widget,
                    "Open File",
                    f"Could not open file in native application:\n{file_path}",
                )
            else:
                self.logger.info("Opened model in native app: %s", file_path)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            error_msg = f"Failed to open file in native app: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            QMessageBox.critical(self.library_widget, "Error", error_msg)
