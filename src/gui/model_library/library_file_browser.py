"""
File browser functionality for model library.

Handles file browsing, importing, and file operations.
"""

from pathlib import Path

from PySide6.QtWidgets import QMessageBox

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class LibraryFileBrowser:
    """Manages file browser functionality."""

    def __init__(self, library_widget) -> None:
        """
        Initialize file browser.

        Args:
            library_widget: The model library widget
        """
        self.library_widget = library_widget
        self.logger = get_logger(__name__)

    def import_from_context_menu(self, path: str) -> None:
        """Import files/folders from context menu selection."""
        try:
            p = Path(path)
            if p.is_file():
                if p.suffix.lower() in [".stl", ".obj", ".3mf", ".step", ".stp"]:
                    self.library_widget.model_manager.load_models([path])
                else:
                    QMessageBox.warning(
                        self.library_widget,
                        "Import",
                        f"Unsupported file format: {p.suffix}",
                    )
            elif p.is_dir():
                files_to_import = []
                supported_extensions = [".stl", ".obj", ".3mf", ".step", ".stp"]
                for ext in supported_extensions:
                    files_to_import.extend(p.rglob(f"*{ext}"))

                if files_to_import:
                    files_to_import = [str(f) for f in files_to_import]
                    self.library_widget.facade.model_manager.load_models(files_to_import)
                else:
                    QMessageBox.information(
                        self.library_widget,
                        "Import",
                        f"No supported model files found in {p.name}",
                    )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error importing from context menu: %s", e)
            QMessageBox.critical(self.library_widget, "Import Error", f"Failed to import: {e}")

    def open_in_native_app(self, file_path: str) -> None:
        """Open file in its native application."""
        try:
            from PySide6.QtCore import QUrl
            from PySide6.QtGui import QDesktopServices

            url = QUrl.fromLocalFile(file_path)
            if not QDesktopServices.openUrl(url):
                QMessageBox.warning(
                    self.library_widget,
                    "Open File",
                    f"Could not open file: {file_path}",
                )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error opening file in native app: %s", e)
            QMessageBox.critical(self.library_widget, "Open File", f"Failed to open file: {e}")

    def remove_model(self, model_id: int) -> None:
        """Remove a model from the library after confirmation."""
        try:
            model_info = self.library_widget.db_manager.get_model(model_id)
            if not model_info:
                self.logger.warning("Model with ID %s not found", model_id)
                return

            model_name = model_info.get("title") or model_info.get("filename", "Unknown")

            reply = QMessageBox.question(
                self.library_widget,
                "Confirm Removal",
                f"Are you sure you want to remove '{model_name}' from the library?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                success = self.library_widget.db_manager.delete_model(model_id)

                if success:
                    if model_info.get("file_path"):
                        try:
                            self.library_widget.model_cache.remove(model_info["file_path"])
                        except Exception:
                            pass

                    self.library_widget.status_label.setText(f"Removed '{model_name}' from library")
                    self.library_widget.model_manager.load_models_from_database()

                    self.logger.info(f"Successfully removed model '{model_name}' (ID: {model_id})")
                else:
                    self.library_widget.status_label.setText(f"Failed to remove '{model_name}'")
                    self.logger.error("Failed to remove model with ID %s", model_id)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error removing model: %s", e)
            QMessageBox.warning(self.library_widget, "Error", f"Failed to remove model: {str(e)}")

    def refresh_models(self) -> None:
        """Refresh models from database."""
        self.library_widget.facade.model_manager.load_models_from_database()

    def refresh_file_browser(self) -> None:
        """Refresh the file browser by re-indexing directories."""
        try:
            self.library_widget.file_model.refresh_index()
            self.library_widget.status_label.setText("Indexing directories...")
            self.logger.info("Manual file browser refresh initiated")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error refreshing file browser: %s", e)
            self.library_widget.status_label.setText("Error refreshing directories")

    def on_indexing_started(self) -> None:
        """Handle indexing started signal."""
        self.library_widget.status_label.setText("Indexing directories...")

    def on_indexing_completed(self) -> None:
        """Handle indexing completed signal."""
        self.library_widget.status_label.setText("Ready")

    def validate_root_folders(self) -> None:
        """Validate that configured root folders are accessible."""
        try:
            enabled_folders = self.library_widget.root_folder_manager.get_enabled_folders()
            inaccessible_folders = []

            for folder in enabled_folders:
                if not Path(folder.path).exists():
                    inaccessible_folders.append(f"{folder.display_name} ({folder.path})")
                    self.logger.warning(
                        f"Root folder not accessible: {folder.display_name} ({folder.path})"
                    )

            if inaccessible_folders:
                folder_list = "\n".join(f"• {folder}" for folder in inaccessible_folders)
                QMessageBox.warning(
                    self.library_widget,
                    "Inaccessible Root Folders",
                    f"The following configured root folders are not accessible:\n\n{folder_list}\n\n"
                    "Please check that the folders exist and you have permission to access them.\n"
                    "You can update root folder settings in Preferences > Files.",
                )
            else:
                self.logger.debug("All %s root folders are accessible", len(enabled_folders))

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error validating root folders: %s", e)

    def import_models(self) -> None:
        """Import models (stub for tests)."""
        self.library_widget.status_label.setText("Use drag-and-drop to import models.")

    def import_selected_files(self) -> None:
        """Import selected files from the file tree."""
        try:
            selected_indexes = self.library_widget.file_tree.selectedIndexes()
            if not selected_indexes:
                QMessageBox.information(
                    self.library_widget, "Import", "Please select files to import."
                )
                return

            files_to_import = []
            for index in selected_indexes:
                source_index = self.library_widget.file_proxy_model.mapToSource(index)
                file_path = self.library_widget.file_model.get_file_path(source_index)
                if file_path and Path(file_path).is_file():
                    if Path(file_path).suffix.lower() in [
                        ".stl",
                        ".obj",
                        ".3mf",
                        ".step",
                        ".stp",
                    ]:
                        files_to_import.append(file_path)

            if files_to_import:
                self.library_widget.facade.model_manager.load_models(files_to_import)
            else:
                QMessageBox.warning(
                    self.library_widget, "Import", "No supported model files selected."
                )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error importing selected files: %s", e)
            QMessageBox.critical(
                self.library_widget, "Import Error", f"Failed to import files: {e}"
            )

    def import_selected_folder(self) -> None:
        """Import all models from selected folder."""
        try:
            selected_indexes = self.library_widget.file_tree.selectedIndexes()
            if not selected_indexes:
                QMessageBox.information(
                    self.library_widget, "Import", "Please select a folder to import."
                )
                return

            source_index = self.library_widget.file_proxy_model.mapToSource(selected_indexes[0])
            folder_path = self.library_widget.file_model.get_file_path(source_index)

            if not folder_path or not Path(folder_path).is_dir():
                QMessageBox.warning(self.library_widget, "Import", "Please select a folder.")
                return

            files_to_import = []
            supported_extensions = [".stl", ".obj", ".3mf", ".step", ".stp"]
            for ext in supported_extensions:
                files_to_import.extend(Path(folder_path).rglob(f"*{ext}"))
                files_to_import.extend(Path(folder_path).rglob(f"*{ext.upper()}"))

            if files_to_import:
                # Remove duplicates and convert to strings
                files_to_import = list(set(str(f) for f in files_to_import))
                self.library_widget.facade.model_manager.load_models(files_to_import)
            else:
                QMessageBox.information(
                    self.library_widget,
                    "Import",
                    f"No supported model files found in folder.",
                )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error importing folder: %s", e)
            QMessageBox.critical(
                self.library_widget, "Import Error", f"Failed to import folder: {e}"
            )
