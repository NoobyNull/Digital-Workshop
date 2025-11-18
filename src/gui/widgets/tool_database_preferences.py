"""
Tool database preferences widget for managing external database paths.

Provides UI for setting and managing paths to external tool databases
and other tool database system preferences.
"""

from typing import Dict, Any
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QGroupBox,
    QPushButton,
    QLineEdit,
    QLabel,
    QFileDialog,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
)
from PySide6.QtCore import pyqtSignal

from src.gui.layout.flow_layout import FlowLayout

from src.core.logging_config import get_logger
from src.core.database.tool_preferences_repository import ToolPreferencesRepository

logger = get_logger(__name__)


class ToolDatabasePreferencesDialog(QDialog):
    """Dialog for managing tool database preferences."""

    preferences_changed = pyqtSignal()

    def __init__(self, db_path: str, parent=None) -> None:
        """
        Initialize preferences dialog.

        Args:
            db_path: Path to the tool database
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_path = db_path
        self.preferences_repo = ToolPreferencesRepository(db_path)
        self.logger = logger

        self.setWindowTitle("Tool Database Preferences")
        self.setGeometry(100, 100, 600, 500)

        self._init_ui()
        self._load_preferences()

    def _init_ui(self) -> None:
        """Initialize user interface."""
        layout = QVBoxLayout()

        # External Database Paths Group
        ext_db_group = QGroupBox("External Database Paths")
        ext_db_layout = QVBoxLayout()

        # Path list
        self.paths_list = QListWidget()
        self.paths_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        ext_db_layout.addWidget(QLabel("Registered External Databases:"))
        ext_db_layout.addWidget(self.paths_list)

        # Path management buttons
        path_button_layout = FlowLayout()
        self.add_path_btn = QPushButton("Add Path")
        self.add_path_btn.clicked.connect(self._add_external_path)
        path_button_layout.addWidget(self.add_path_btn)

        self.remove_path_btn = QPushButton("Remove Selected")
        self.remove_path_btn.clicked.connect(self._remove_external_path)
        path_button_layout.addWidget(self.remove_path_btn)

        ext_db_layout.addLayout(path_button_layout)
        ext_db_group.setLayout(ext_db_layout)
        layout.addWidget(ext_db_group)

        # Default Provider Group
        provider_group = QGroupBox("Default Provider")
        provider_layout = QVBoxLayout()

        provider_layout.addWidget(QLabel("Default Provider for New Tools:"))
        self.default_provider = QLineEdit()
        self.default_provider.setPlaceholderText("e.g., IDC Woodcraft")
        provider_layout.addWidget(self.default_provider)

        provider_group.setLayout(provider_layout)
        layout.addWidget(provider_group)

        # Settings Group
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout()

        self.auto_import_cb = QPushButton("Toggle Auto-Import")
        self.auto_import_cb.setCheckable(True)
        settings_layout.addWidget(self.auto_import_cb)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Dialog buttons
        button_layout = FlowLayout()
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self._save_and_close)
        button_layout.addWidget(self.ok_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _load_preferences(self) -> None:
        """Load preferences from repository."""
        try:
            # Load external database paths
            paths = self.preferences_repo.get_preference("external_database_paths", [])
            self.paths_list.clear()
            for path in paths:
                self.paths_list.addItem(QListWidgetItem(path))

            # Load default provider
            default_provider = self.preferences_repo.get_preference(
                "default_provider", "IDC Woodcraft"
            )
            self.default_provider.setText(default_provider)

            # Load auto-import setting
            auto_import = self.preferences_repo.get_preference("auto_import_enabled", False)
            self.auto_import_cb.setChecked(auto_import)

            self.logger.info("Preferences loaded successfully")

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to load preferences: %s", e)
            QMessageBox.critical(self, "Error", f"Failed to load preferences: {str(e)}")

    def _add_external_path(self) -> None:
        """Add external database path."""
        file_path = QFileDialog.getExistingDirectory(self, "Select External Database Directory")

        if file_path:
            if not any(
                self.paths_list.item(i).text() == file_path for i in range(self.paths_list.count())
            ):
                self.paths_list.addItem(QListWidgetItem(file_path))
                self.logger.info("Added external database path: %s", file_path)
            else:
                QMessageBox.information(self, "Info", "Path already added")

    def _remove_external_path(self) -> None:
        """Remove selected external database path."""
        current_item = self.paths_list.currentItem()
        if current_item:
            row = self.paths_list.row(current_item)
            removed_item = self.paths_list.takeItem(row)
            self.logger.info("Removed external database path: %s", removed_item.text())

    def _save_and_close(self) -> None:
        """Save preferences and close dialog."""
        try:
            # Collect paths
            paths = [self.paths_list.item(i).text() for i in range(self.paths_list.count())]

            # Save preferences
            prefs: Dict[str, Any] = {
                "external_database_paths": paths,
                "default_provider": self.default_provider.text(),
                "auto_import_enabled": self.auto_import_cb.isChecked(),
            }

            for key, value in prefs.items():
                self.preferences_repo.set_preference(key, value)

            self.logger.info("Preferences saved successfully")
            self.preferences_changed.emit()
            self.accept()

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to save preferences: %s", e)
            QMessageBox.critical(self, "Error", f"Failed to save preferences: {str(e)}")
