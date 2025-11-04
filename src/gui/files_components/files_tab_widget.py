"""
Files tab for preferences dialog.

Provides UI for managing root folders used by the file browser.
"""

from pathlib import Path

from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QCheckBox,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QInputDialog,
    QProgressBar,
    QComboBox,
    QMenu,
)

from src.core.logging_config import get_logger
from src.core.root_folder_manager import RootFolderManager, RootFolder
from src.gui.theme import SPACING_4, SPACING_8, SPACING_12
from src.gui.files_components.file_maintenance_worker import FileMaintenanceWorker
from src.gui.components.auto_close_message_box import show_auto_close_message


class FilesTab(QWidget):
    """
    Files preferences tab for managing root folders.

    Allows users to add, remove, enable/disable root folders
    that are used by the file browser in the model library.
    """

    def __init__(self, parent=None) -> None:
        """TODO: Add docstring."""
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.root_folder_manager = RootFolderManager.get_instance()
        self.maintenance_worker = None  # Initialize maintenance worker attribute
        self._setup_ui()
        self._load_folders()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_12, SPACING_12, SPACING_12, SPACING_12)
        layout.setSpacing(SPACING_12)

        # Header
        header = QLabel("Configure root folders for file browsing")
        header.setWordWrap(True)
        layout.addWidget(header)

        desc = QLabel(
            "Add folders that contain your 3D model files. Only enabled folders "
            "will be shown in the file browser."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Root folders group
        folders_group = QGroupBox("Root Folders")
        folders_layout = QVBoxLayout(folders_group)

        # Folders list
        self.folders_list = QListWidget()
        self.folders_list.setMinimumHeight(200)
        self.folders_list.setContextMenuPolicy(Qt.CustomContextMenu)
        folders_layout.addWidget(self.folders_list)

        # Buttons row
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(SPACING_8)

        self.add_button = QPushButton("Add Folder")
        self.add_button.setToolTip("Add a new root folder")
        buttons_layout.addWidget(self.add_button)

        self.remove_button = QPushButton("Remove")
        self.remove_button.setToolTip("Remove selected folder")
        self.remove_button.setEnabled(False)
        buttons_layout.addWidget(self.remove_button)

        self.edit_button = QPushButton("Edit")
        self.edit_button.setToolTip("Edit selected folder")
        self.edit_button.setEnabled(False)
        buttons_layout.addWidget(self.edit_button)

        buttons_layout.addStretch()
        folders_layout.addLayout(buttons_layout)

        layout.addWidget(folders_group)

        # Validation section
        validation_group = QGroupBox("Folder Validation")
        validation_layout = QVBoxLayout(validation_group)

        self.validate_button = QPushButton("Validate All Folders")
        self.validate_button.setToolTip("Check if all configured folders are accessible")
        validation_layout.addWidget(self.validate_button)

        self.validation_status = QLabel("Ready")
        validation_layout.addWidget(self.validation_status)

        layout.addWidget(validation_group)

        # File matching and regeneration section
        maintenance_group = QGroupBox("File & Model Maintenance")
        maintenance_layout = QVBoxLayout(maintenance_group)

        maintenance_desc = QLabel(
            "Force check and match files to models, or regenerate thumbnails. "
            "Useful if files have been moved or hashes need to be recalculated."
        )
        maintenance_desc.setWordWrap(True)
        maintenance_layout.addWidget(maintenance_desc)

        # Operation selection
        operation_layout = QHBoxLayout()
        operation_layout.addWidget(QLabel("Operation:"))
        self.operation_combo = QComboBox()
        self.operation_combo.addItem("Recalculate File Hashes", "recalculate_hashes")
        self.operation_combo.addItem("Match Files to Models", "match_files")
        self.operation_combo.addItem("Regenerate Thumbnails", "regenerate_thumbnails")
        self.operation_combo.addItem("Full Maintenance (All)", "full_maintenance")
        operation_layout.addWidget(self.operation_combo)
        operation_layout.addStretch()
        maintenance_layout.addLayout(operation_layout)

        # Progress bar
        self.maintenance_progress = QProgressBar()
        self.maintenance_progress.setVisible(False)
        self.maintenance_progress.setMinimum(0)
        self.maintenance_progress.setMaximum(100)
        maintenance_layout.addWidget(self.maintenance_progress)

        # Status label
        self.maintenance_status = QLabel("Ready")
        maintenance_layout.addWidget(self.maintenance_status)

        # Buttons
        maintenance_buttons = QHBoxLayout()
        self.start_maintenance_button = QPushButton("Start Maintenance")
        self.start_maintenance_button.setToolTip("Start the selected maintenance operation")
        maintenance_buttons.addWidget(self.start_maintenance_button)

        self.cancel_maintenance_button = QPushButton("Cancel")
        self.cancel_maintenance_button.setToolTip("Cancel running operation")
        self.cancel_maintenance_button.setEnabled(False)
        maintenance_buttons.addWidget(self.cancel_maintenance_button)

        maintenance_buttons.addStretch()
        maintenance_layout.addLayout(maintenance_buttons)

        layout.addWidget(maintenance_group)

        layout.addStretch()

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        self.add_button.clicked.connect(self._add_folder)
        self.remove_button.clicked.connect(self._remove_folder)
        self.edit_button.clicked.connect(self._edit_folder)
        self.validate_button.clicked.connect(self._validate_folders)
        self.folders_list.itemSelectionChanged.connect(self._update_button_states)
        self.folders_list.itemChanged.connect(self._on_item_changed)
        self.folders_list.customContextMenuRequested.connect(self._show_context_menu)
        self.start_maintenance_button.clicked.connect(self._start_maintenance)
        self.cancel_maintenance_button.clicked.connect(self._cancel_maintenance)

    def _load_folders(self) -> None:
        """Load folders from the manager and populate the list."""
        self.folders_list.clear()

        for folder in self.root_folder_manager.get_folders():
            self._add_folder_item(folder)

    def _add_folder_item(self, folder: RootFolder) -> None:
        """Add a folder item to the list widget."""
        item = QListWidgetItem()
        item.setData(Qt.UserRole, folder.id)

        # Create widget for the item
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(SPACING_4, SPACING_4, SPACING_4, SPACING_4)
        layout.setSpacing(SPACING_8)

        # Checkbox for enabled/disabled
        enabled_cb = QCheckBox()
        enabled_cb.setChecked(folder.enabled)
        enabled_cb.setToolTip("Enable/disable this folder in file browser")
        layout.addWidget(enabled_cb)

        # Folder info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(SPACING_4)

        name_label = QLabel(f"<b>{folder.display_name}</b>")
        path_label = QLabel(f"<small>{folder.path}</small>")
        path_label.setWordWrap(True)

        info_layout.addWidget(name_label)
        info_layout.addWidget(path_label)
        layout.addLayout(info_layout, 1)

        # Status indicator
        status_label = QLabel()
        if self._is_folder_valid(folder):
            status_label.setText("✓")
            # Material Design theme handles colors - no hardcoded colors
            status_label.setToolTip("Folder is accessible")
        else:
            status_label.setText("✗")
            # Material Design theme handles colors - no hardcoded colors
            status_label.setToolTip("Folder is not accessible")
        layout.addWidget(status_label)

        item.setSizeHint(widget.sizeHint())
        self.folders_list.addItem(item)
        self.folders_list.setItemWidget(item, widget)

        # Connect checkbox signal
        enabled_cb.stateChanged.connect(
            lambda state, fid=folder.id: self._toggle_folder_enabled(fid, state)
        )

    def _is_folder_valid(self, folder: RootFolder) -> bool:
        """Check if a folder is valid (exists and accessible)."""
        try:
            path = Path(folder.path)
            return path.exists() and path.is_dir()
        except Exception:
            return False

    def _add_folder(self) -> None:
        """Add a new root folder."""
        # Open folder selection dialog
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select Root Folder", str(Path.home()), QFileDialog.ShowDirsOnly
        )

        if not folder_path:
            return

        # Get display name
        folder_name = Path(folder_path).name
        display_name, ok = QInputDialog.getText(
            self,
            "Folder Display Name",
            "Enter a display name for this folder:",
            text=folder_name,
        )

        if not ok or not display_name.strip():
            return

        # Add to manager
        if self.root_folder_manager.add_folder(folder_path, display_name.strip()):
            self._load_folders()  # Refresh the list
            show_auto_close_message(self, "Success", f"Added folder '{display_name}'", 5000)
        else:
            QMessageBox.warning(
                self,
                "Error",
                "Failed to add folder. It may already exist or be inaccessible.",
            )

    def _remove_folder(self) -> None:
        """Remove the selected folder."""
        current_item = self.folders_list.currentItem()
        if not current_item:
            return

        folder_id = current_item.data(Qt.UserRole)
        folder = self.root_folder_manager.get_folder_by_id(folder_id)
        if not folder:
            return

        # Confirm removal
        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove '{folder.display_name}' from the root folders?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            if self.root_folder_manager.remove_folder(folder_id):
                self._load_folders()  # Refresh the list
                show_auto_close_message(
                    self, "Success", f"Removed folder '{folder.display_name}'", 5000
                )
            else:
                QMessageBox.warning(self, "Error", "Failed to remove folder.")

    def _edit_folder(self) -> None:
        """Edit the selected folder."""
        current_item = self.folders_list.currentItem()
        if not current_item:
            return

        folder_id = current_item.data(Qt.UserRole)
        folder = self.root_folder_manager.get_folder_by_id(folder_id)
        if not folder:
            return

        # Get new display name
        new_name, ok = QInputDialog.getText(
            self,
            "Edit Folder Name",
            "Enter new display name:",
            text=folder.display_name,
        )

        if ok and new_name.strip() and new_name.strip() != folder.display_name:
            if self.root_folder_manager.update_folder(folder_id, display_name=new_name.strip()):
                self._load_folders()  # Refresh the list
                show_auto_close_message(self, "Success", "Folder name updated.", 5000)
            else:
                QMessageBox.warning(self, "Error", "Failed to update folder name.")

    def _toggle_folder_enabled(self, folder_id: int, enabled: bool) -> None:
        """Toggle folder enabled/disabled state."""
        self.root_folder_manager.update_folder(folder_id, enabled=enabled)

    def _update_button_states(self) -> None:
        """Update button enabled states based on selection."""
        has_selection = self.folders_list.currentItem() is not None
        self.remove_button.setEnabled(has_selection)
        self.edit_button.setEnabled(has_selection)

    def _on_item_changed(self, item: QListWidgetItem) -> None:
        """Handle item changes."""
        # Could be used for additional item-specific updates

    def _show_context_menu(self, position: QPoint) -> None:
        """Show context menu for the folders list."""
        menu = QMenu(self)

        # Add Root Folder action - always available
        add_action = menu.addAction("Add Root Folder")
        add_action.triggered.connect(self._add_folder)

        # Get item at position
        item = self.folders_list.itemAt(position)

        if item:
            # Add separator
            menu.addSeparator()

            # Edit action for selected item
            edit_action = menu.addAction("Edit Folder Name")
            edit_action.triggered.connect(self._edit_folder)

            # Remove action for selected item
            remove_action = menu.addAction("Remove Folder")
            remove_action.triggered.connect(self._remove_folder)

        # Show menu at cursor position
        menu.exec(self.folders_list.mapToGlobal(position))

    def _validate_folders(self) -> None:
        """Validate all configured folders."""
        self.validation_status.setText("Validating folders...")

        results = self.root_folder_manager.validate_all_folders()
        valid_count = len(results["valid"])
        invalid_count = len(results["invalid"])

        if invalid_count == 0:
            self.validation_status.setText(f"✓ All {valid_count} folders are accessible.")
            QMessageBox.information(
                self,
                "Validation Complete",
                f"All {valid_count} folders are accessible.",
            )
        else:
            self.validation_status.setText(
                f"✗ {invalid_count} of {valid_count + invalid_count} folders have issues."
            )
            invalid_list = "\n".join(f"• {path}" for path in results["invalid"])
            QMessageBox.warning(
                self,
                "Validation Issues",
                f"The following folders are not accessible:\n\n{invalid_list}\n\n"
                "Consider removing or fixing these folders.",
            )

        # Refresh the list to update status indicators
        self._load_folders()

    def _start_maintenance(self) -> None:
        """Start the selected maintenance operation."""
        operation = self.operation_combo.currentData()

        # Confirm before starting
        operation_name = self.operation_combo.currentText()
        reply = QMessageBox.question(
            self,
            "Confirm Maintenance",
            f"Start '{operation_name}' operation?\n\n"
            "This may take some time depending on the number of models.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        # Disable controls
        self.start_maintenance_button.setEnabled(False)
        self.cancel_maintenance_button.setEnabled(True)
        self.operation_combo.setEnabled(False)
        self.maintenance_progress.setVisible(True)
        self.maintenance_progress.setValue(0)
        self.maintenance_status.setText(f"Starting {operation_name}...")

        # Create and start worker thread
        self.maintenance_worker = FileMaintenanceWorker(operation)
        self.maintenance_worker.progress.connect(self._on_maintenance_progress)
        self.maintenance_worker.finished.connect(self._on_maintenance_finished)
        self.maintenance_worker.error.connect(self._on_maintenance_error)
        self.maintenance_worker.start()

    def _cancel_maintenance(self) -> None:
        """Cancel the running maintenance operation."""
        if hasattr(self, "maintenance_worker") and self.maintenance_worker.isRunning():
            self.maintenance_worker.stop()
            self.maintenance_status.setText("Cancelling operation...")

    def _on_maintenance_progress(self, current: int, total: int, message: str) -> None:
        """Handle maintenance progress update."""
        if total > 0:
            percentage = int((current / total) * 100)
            self.maintenance_progress.setValue(percentage)
        self.maintenance_status.setText(f"{message} ({current}/{total})")

    def _on_maintenance_finished(self, result: dict) -> None:
        """Handle maintenance operation completion."""
        self.maintenance_progress.setVisible(False)
        self.start_maintenance_button.setEnabled(True)
        self.cancel_maintenance_button.setEnabled(False)
        self.operation_combo.setEnabled(True)

        # Show results
        operation_name = self.operation_combo.currentText()
        message = (
            f"{operation_name} completed successfully!\n\n"
            f"Processed: {result.get('processed', 0)}\n"
            f"Updated: {result.get('updated', 0)}\n"
            f"Errors: {result.get('errors', 0)}"
        )
        self.maintenance_status.setText(message)
        QMessageBox.information(self, "Maintenance Complete", message)

    def _on_maintenance_error(self, error_message: str) -> None:
        """Handle maintenance operation error."""
        self.maintenance_progress.setVisible(False)
        self.start_maintenance_button.setEnabled(True)
        self.cancel_maintenance_button.setEnabled(False)
        self.operation_combo.setEnabled(True)
        self.maintenance_status.setText(f"Error: {error_message}")
        QMessageBox.critical(self, "Maintenance Error", error_message)
