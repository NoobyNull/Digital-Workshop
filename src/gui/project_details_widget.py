"""
Project Details Widget for displaying model information and attached resources.

Shows:
- Model information (name, format, size, dimensions, geometry stats)
- Attached resources/files (list of files associated with the model)
"""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtCore import Qt, QFileInfo
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFileIconProvider,
    QStyle,
    QMenu,
    QMessageBox,
    QFileDialog,
)

from src.core.database_manager import get_database_manager
from src.core.logging_config import get_logger
from src.core.services.file_type_registry import get_tab_for_extension
from src.utils.file_hash import calculate_file_hash


logger = get_logger(__name__)


class ProjectDetailsWidget(QWidget):
    """
    Widget for displaying project/model details and attached resources.

    Displays:
    - Model Information: name, format, size, dimensions, geometry stats
    - Attached Resources: list of files associated with the model
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.current_model_id: Optional[int] = None
        self.current_model_data: Optional[Dict[str, Any]] = None
        self.current_project_id: Optional[str] = None
        self.db_manager = get_database_manager()

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(12)

        # Model Information Section
        self.model_info_group = self._create_model_info_section()
        scroll_layout.addWidget(self.model_info_group)

        # Resources/Files Section
        self.resources_group = self._create_resources_section()
        scroll_layout.addWidget(self.resources_group)

        # Stretch to fill remaining space
        scroll_layout.addStretch()

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

    def _create_model_info_section(self) -> QGroupBox:
        """Create the model information section."""
        group = QGroupBox("Model Information")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)

        # Create info labels (will be populated when model is selected)
        self.info_labels = {}

        info_fields = [
            ("Name", "name"),
            ("Format", "format"),
            ("File Size", "file_size"),
            ("Dimensions", "dimensions"),
            ("Triangles", "triangles"),
            ("Vertices", "vertices"),
            ("Date Added", "date_added"),
        ]

        for label_text, field_key in info_fields:
            h_layout = QHBoxLayout()

            label = QLabel(f"{label_text}:")

            value = QLabel("-")
            value.setWordWrap(True)

            self.info_labels[field_key] = value

            h_layout.addWidget(label)
            h_layout.addWidget(value, 1)
            layout.addLayout(h_layout)

        return group

    def _create_resources_section(self) -> QGroupBox:
        """Create the resources/files section."""
        group = QGroupBox("Attached Resources")
        layout = QVBoxLayout(group)

        # Resources table
        self.resources_table = QTableWidget()
        self.resources_table.setColumnCount(3)
        self.resources_table.setHorizontalHeaderLabels(["File Name", "Size", "Type"])
        self.resources_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )
        self.resources_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )
        self.resources_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents
        )
        self.resources_table.setMaximumHeight(200)
        self.resources_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.resources_table.setSelectionMode(QTableWidget.SingleSelection)
        self.resources_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.resources_table.customContextMenuRequested.connect(
            self._on_resources_context_menu
        )
        self.resources_table.itemDoubleClicked.connect(self._on_resource_activated)

        layout.addWidget(self.resources_table)

        return group

    def set_model(self, model_data: Dict[str, Any]) -> None:
        """
        Set the model to display.

        Args:
            model_data: Dictionary containing model information
        """
        try:
            self.current_model_data = model_data
            self.current_model_id = model_data.get("id")

            self._update_model_info(model_data)
            self._update_resources(model_data)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to set model: %s", e)
            self.clear()
        # Ensure widget is visible in its dock when data arrives
        try:
            parent_dock = self.parentWidget()
            if parent_dock and hasattr(parent_dock, "show"):
                parent_dock.show()
        except Exception:
            pass

    def show_file(self, file_path: str) -> None:
        """Populate the panel with basic metadata for a project file (non-model)."""
        try:
            path = Path(file_path)
            if not path.exists():
                self.clear()
                return

            try:
                stat = path.stat()
                file_size = stat.st_size
                date_added = datetime.fromtimestamp(stat.st_mtime).isoformat()
            except (OSError, ValueError):
                file_size = 0
                date_added = "-"

            model_like = {
                "id": None,
                "filename": path.name,
                "format": (path.suffix.lstrip(".") or "file").upper(),
                "file_size": file_size,
                "dimensions": None,
                "triangle_count": 0,
                "vertex_count": 0,
                "date_added": date_added,
                "file_path": str(path),
            }
            self.set_model(model_like)
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Failed to show file in Project Details: %s", exc)
            self.clear()

    def _update_model_info(self, model_data: Dict[str, Any]) -> None:
        """Update model information display."""
        try:
            # Format file size
            file_size = model_data.get("file_size", 0) or 0
            if file_size > 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024):.2f} MB"
            elif file_size > 1024:
                size_str = f"{file_size / 1024:.2f} KB"
            else:
                size_str = f"{file_size} B"

            # Format dimensions
            dimensions = model_data.get("dimensions", (0, 0, 0))
            if isinstance(dimensions, (list, tuple)) and len(dimensions) >= 3:
                dim_str = (
                    f"{dimensions[0]:.2f} × {dimensions[1]:.2f} × {dimensions[2]:.2f}"
                )
            else:
                dim_str = "-"

            # Update labels
            self.info_labels["name"].setText(model_data.get("filename", "-"))
            self.info_labels["format"].setText(model_data.get("format", "-").upper())
            self.info_labels["file_size"].setText(size_str)
            self.info_labels["dimensions"].setText(dim_str)
            self.info_labels["triangles"].setText(
                f"{model_data.get('triangle_count', 0):,}"
            )
            self.info_labels["vertices"].setText(
                f"{model_data.get('vertex_count', 0):,}"
            )
            self.info_labels["date_added"].setText(
                str(model_data.get("date_added", "-"))
            )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to update model info: %s", e)

    def _update_resources(self, model_data: Dict[str, Any]) -> None:
        """Update resources/files display."""
        try:
            self.resources_table.setRowCount(0)

            # Get file path from model
            file_path = model_data.get("file_path")
            if not file_path:
                return

            file_path = Path(file_path)

            # Add the main model file
            if file_path.exists():
                self._add_resource_row(file_path)

            # This would require additional database schema to track related files

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to update resources: %s", e)

    def _add_resource_row(self, file_path: Path) -> None:
        """Add a resource file to the table."""
        try:
            row = self.resources_table.rowCount()
            self.resources_table.insertRow(row)

            # File name
            name_item = QTableWidgetItem(file_path.name)
            name_item.setIcon(self._get_file_icon(file_path))
            name_item.setData(Qt.UserRole, str(file_path))
            self.resources_table.setItem(row, 0, name_item)

            # File size
            try:
                size = file_path.stat().st_size
                if size > 1024 * 1024:
                    size_str = f"{size / (1024 * 1024):.2f} MB"
                elif size > 1024:
                    size_str = f"{size / 1024:.2f} KB"
                else:
                    size_str = f"{size} B"
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError):
                size_str = "-"

            size_item = QTableWidgetItem(size_str)
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.resources_table.setItem(row, 1, size_item)

            # File type
            type_item = QTableWidgetItem(file_path.suffix.upper() or "FILE")
            self.resources_table.setItem(row, 2, type_item)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to add resource row: %s", e)

    def set_project_context(self, project_id: Optional[str]) -> None:
        """Set the active project context (no-op for material info)."""
        self.current_project_id = project_id

    def _on_resource_activated(self, item: QTableWidgetItem) -> None:
        """Handle double-click on a resource row to open it in the appropriate tab."""
        if item is None:
            return

        try:
            row = item.row()
            name_item = self.resources_table.item(row, 0)
            if name_item is None:
                return

            file_path_str = name_item.data(Qt.UserRole)
            if not file_path_str:
                return

            file_path = Path(file_path_str)
            if not file_path.exists():
                QMessageBox.warning(
                    self,
                    "File Not Found",
                    f"The selected file no longer exists on disk:\n{file_path_str}",
                )
                return

            file_ext = file_path.suffix.lower()
            tab_name = get_tab_for_extension(file_ext)

            main_window = self.window()

            # Switch hero tab first if we know where this file should open
            if (
                tab_name
                and main_window is not None
                and hasattr(main_window, "_on_tab_switch_requested")
            ):
                try:
                    main_window._on_tab_switch_requested(tab_name)
                except Exception:  # noqa: BLE001
                    self.logger.warning(
                        "Failed to switch tab for resource %s", file_path_str
                    )

            if main_window is None:
                return

            if tab_name == "Model Previewer":
                self._open_model_resource(main_window, file_path)
            elif tab_name == "G Code Previewer":
                self._open_gcode_resource(main_window, file_path)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to open resource from Project Details: %s", e)

    def _open_model_resource(self, main_window, file_path: Path) -> None:
        """Open a model-type resource in the main viewer.

        Prefer using the current model ID so we get consistent behaviour with
        the model library (camera restore, status messages, etc.).
        """
        try:
            controller = getattr(main_window, "model_viewer_controller", None)

            # If we know which model this is, delegate to the model viewer
            # controller so we reuse the same pipeline (camera restore, status
            # messages, etc.) as the model library.
            if (
                getattr(self, "current_model_id", None) is not None
                and controller is not None
            ):
                try:
                    controller.on_model_double_clicked(self.current_model_id)  # type: ignore[arg-type]
                    return
                except Exception:  # noqa: BLE001
                    self.logger.warning(
                        "Failed to delegate model resource open to controller; "
                        "falling back to direct file load.",
                    )

            # Fallback: load directly from the file path
            model_loader = getattr(main_window, "model_loader_manager", None)
            if model_loader is not None:
                model_loader.load_stl_model(str(file_path))

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to open model resource %s: %s", file_path, e)

    def _open_gcode_resource(self, main_window, file_path: Path) -> None:
        """Open a G-code resource in the G Code Previewer tab."""
        try:
            gcode_widget = getattr(main_window, "gcode_previewer_widget", None)
            if gcode_widget is None:
                return

            gcode_widget.load_gcode_file(str(file_path))

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to open G-code resource %s: %s", file_path, e)

    def _get_file_icon(self, file_path: Path) -> QIcon:
        """Get an appropriate native icon for the given file path."""
        try:
            provider = QFileIconProvider()
            file_info = QFileInfo(str(file_path))
            icon = provider.icon(file_info)
            if not icon.isNull():
                return icon
        except Exception as e:  # noqa: BLE001
            self.logger.debug(
                "Falling back to default file icon for %s: %s", file_path, e
            )
        # Fallback: generic file icon from the current style
        try:
            return self.style().standardIcon(QStyle.SP_FileIcon)
        except Exception:  # noqa: BLE001
            return QIcon()

    def _on_resources_context_menu(self, pos) -> None:
        """Show context menu for the resources table."""
        if not self.current_model_data:
            return

        index = self.resources_table.indexAt(pos)
        if not index.isValid():
            return

        # Currently we only support operations on the primary model file.
        file_path_str = self.resources_table.item(index.row(), 0).data(Qt.UserRole)
        if not file_path_str:
            return

        menu = QMenu(self)

        replace_action = menu.addAction("Replace File...")
        put_back_action = menu.addAction("Put Back to Original Location")

        # Only enable "Put Back" if we have an original path recorded.
        original_path = self.current_model_data.get("original_path")
        put_back_action.setEnabled(bool(original_path))

        chosen_action = menu.exec(self.resources_table.viewport().mapToGlobal(pos))
        if chosen_action is replace_action:
            self._replace_model_file(Path(file_path_str))
        elif chosen_action is put_back_action:
            self._restore_model_file()

    def _replace_model_file(self, current_path: Path) -> None:
        """Replace the current model file with a new one.

        This updates the underlying model record in the database and refreshes the UI.
        """
        db = get_database_manager()

        if not self.current_model_data or self.current_model_id is None:
            return

        # Ask user for replacement file
        dialog_caption = "Select Replacement File"
        start_dir = (
            str(current_path.parent) if current_path and current_path.exists() else ""
        )
        new_path_str, _ = QFileDialog.getOpenFileName(
            self,
            dialog_caption,
            start_dir,
            "All Files (*.*)",
        )
        if not new_path_str:
            return

        new_path = Path(new_path_str)
        if not new_path.exists():
            QMessageBox.warning(self, "Replace File", "Selected file does not exist.")
            return

        # Confirm replacement
        confirm = QMessageBox.question(
            self,
            "Replace File",
            "Replace the current model file with the selected file?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            # Preserve the original path if we have not recorded it yet.
            updates = {}
            if not self.current_model_data.get("original_path"):
                updates["original_path"] = str(current_path)

            # For now, we treat the selected file as the new path directly.
            # If a managed storage scheme is introduced, this is the place to
            # copy into that area.
            updates["file_path"] = str(new_path)
            updates["file_size"] = new_path.stat().st_size

            file_hash = calculate_file_hash(str(new_path))
            if file_hash:
                updates["file_hash"] = file_hash

            # Apply updates to the model record
            if updates:
                if not db.update_model(self.current_model_id, **updates):
                    QMessageBox.warning(
                        self,
                        "Replace File",
                        "Failed to update model record in the database.",
                    )
                    return

            # Refresh cached model data and UI
            model_data = db.get_model(self.current_model_id)
            if model_data:
                self.set_model(model_data)

            QMessageBox.information(
                self, "Replace File", "Model file replaced successfully."
            )

        except Exception as exc:  # noqa: BLE001
            self.logger.error("Failed to replace model file: %s", exc)
            QMessageBox.critical(
                self,
                "Replace File",
                "An unexpected error occurred while replacing the model file.",
            )

    def _restore_model_file(self) -> None:
        """Restore the model's file_path from its original_path if available."""
        db = get_database_manager()

        if not self.current_model_data or self.current_model_id is None:
            return

        original_path = self.current_model_data.get("original_path")
        current_path_str = self.current_model_data.get("file_path")

        if not original_path:
            QMessageBox.information(
                self,
                "Put Back to Original Location",
                "No original location is recorded for this model.",
            )
            return

        current_path = Path(current_path_str) if current_path_str else None
        original_path_obj = Path(original_path)

        if not original_path_obj.parent.exists():
            QMessageBox.warning(
                self,
                "Put Back to Original Location",
                "The original directory no longer exists.",
            )
            return

        # Confirm restoration
        confirm = QMessageBox.question(
            self,
            "Put Back to Original Location",
            "Move the model file back to its original location?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            # Ensure destination directory exists
            original_path_obj.parent.mkdir(parents=True, exist_ok=True)

            if current_path and current_path.exists():
                # If a file already exists at the original path, back it up to a
                # uniquely named temporary file in the same directory.
                if (
                    original_path_obj.exists()
                    and original_path_obj.resolve() != current_path.resolve()
                ):
                    backup_dir = tempfile.gettempdir()
                    backup_path = (
                        Path(backup_dir) / f"dww_backup_{original_path_obj.name}"
                    )
                    shutil.move(str(original_path_obj), str(backup_path))

                shutil.move(str(current_path), str(original_path_obj))

            updates = {
                "file_path": str(original_path_obj),
            }

            # Once we have restored to the original location, clear original_path
            # so that subsequent operations treat this as the canonical path.
            updates["original_path"] = None

            if not db.update_model(self.current_model_id, **updates):
                QMessageBox.warning(
                    self,
                    "Put Back to Original Location",
                    "Failed to update model record in the database.",
                )
                return

            model_data = db.get_model(self.current_model_id)
            if model_data:
                self.set_model(model_data)

            QMessageBox.information(
                self,
                "Put Back to Original Location",
                "Model file restored to its original location.",
            )

        except Exception as exc:  # noqa: BLE001
            self.logger.error("Failed to restore model file: %s", exc)
            QMessageBox.critical(
                self,
                "Put Back to Original Location",
                "An unexpected error occurred while restoring the model file.",
            )

    def clear(self) -> None:
        """Clear all displayed information."""
        self.current_model_id = None
        self.current_model_data = None

        # Clear info labels
        for label in self.info_labels.values():
            label.setText("-")

        # Clear resources table
        self.resources_table.setRowCount(0)
