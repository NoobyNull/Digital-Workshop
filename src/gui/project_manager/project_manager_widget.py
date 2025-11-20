"""
Project Manager Widget for managing projects in the GUI.

Provides UI for creating, opening, and managing projects.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QInputDialog,
    QMessageBox,
    QFileDialog,
)
from PySide6.QtCore import Qt, Signal

from ..layout.flow_layout import FlowLayout
from ...core.services.project_manager import ProjectManager
from ...core.services.project_importer import ProjectImporter
from ...core.services.dry_run_analyzer import DryRunAnalyzer
from ...core.database.database_manager import DatabaseManager
from ...core.logging_config import get_logger

logger = get_logger(__name__)


class ProjectManagerWidget(QWidget):
    """Widget for managing projects."""

    project_opened = Signal(str)  # project_id
    project_created = Signal(str)  # project_id
    project_deleted = Signal(str)  # project_id

    def __init__(self, db_manager: DatabaseManager, parent=None) -> None:
        """
        Initialize project manager widget.

        Args:
            db_manager: DatabaseManager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_manager = db_manager
        self.project_manager = ProjectManager(db_manager)
        self.project_importer = ProjectImporter(db_manager)
        self.dry_run_analyzer = DryRunAnalyzer()
        self._setup_ui()
        self._refresh_project_list()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        layout = QVBoxLayout()

        # Project list
        self.project_list = QListWidget()
        self.project_list.itemDoubleClicked.connect(self._on_project_double_clicked)
        layout.addWidget(self.project_list)

        # Buttons
        button_layout = FlowLayout()

        new_btn = QPushButton("New Project")
        new_btn.clicked.connect(self._create_new_project)
        button_layout.addWidget(new_btn)

        import_btn = QPushButton("Import Library")
        import_btn.clicked.connect(self._import_library)
        button_layout.addWidget(import_btn)

        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self._open_selected_project)
        button_layout.addWidget(open_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_selected_project)
        button_layout.addWidget(delete_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_project_list)
        button_layout.addWidget(refresh_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _refresh_project_list(self) -> None:
        """Refresh project list."""
        try:
            self.project_list.clear()
            projects = self.project_manager.list_projects()

            for project in projects:
                item_text = f"{project['name']}"
                if project.get("import_tag") == "imported_project":
                    item_text += " [Imported]"

                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, project["id"])
                self.project_list.addItem(item)

            logger.info("Refreshed project list: %s projects", len(projects))

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to refresh project list: %s", str(e))
            QMessageBox.critical(self, "Error", f"Failed to refresh projects: {str(e)}")

    def _create_new_project(self) -> None:
        """Create new project."""
        try:
            name, ok = QInputDialog.getText(self, "New Project", "Project name:")

            if ok and name:
                # Check for duplicate
                if self.project_manager.check_duplicate(name):
                    QMessageBox.warning(
                        self, "Duplicate Project", f"Project '{name}' already exists."
                    )
                    return

                project_id = self.project_manager.create_project(name)
                self.project_created.emit(project_id)
                self._refresh_project_list()
                logger.info("Created project: %s", name)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to create project: %s", str(e))
            QMessageBox.critical(self, "Error", f"Failed to create project: {str(e)}")

    def _import_library(self) -> None:
        """Import existing library."""
        try:
            from .import_helpers import import_existing_library

            import_existing_library(
                parent=self,
                project_manager=self.project_manager,
                dry_run_analyzer=self.dry_run_analyzer,
                project_importer=self.project_importer,
                on_created=self.project_created.emit,
                refresh_ui=self._refresh_project_list,
                logger=logger,
            )
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to import library: %s", str(e))
            QMessageBox.critical(self, "Error", f"Failed to import library: {str(e)}")

    def _open_selected_project(self) -> None:
        """Open selected project."""
        try:
            item = self.project_list.currentItem()
            if not item:
                QMessageBox.warning(self, "No Selection", "Please select a project.")
                return

            project_id = item.data(Qt.UserRole)
            if self.project_manager.open_project(project_id):
                self.project_opened.emit(project_id)
                logger.info("Opened project: %s", project_id)
            else:
                QMessageBox.critical(self, "Error", "Failed to open project.")

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to open project: %s", str(e))
            QMessageBox.critical(self, "Error", f"Failed to open project: {str(e)}")

    def _delete_selected_project(self) -> None:
        """Delete selected project."""
        try:
            item = self.project_list.currentItem()
            if not item:
                QMessageBox.warning(self, "No Selection", "Please select a project.")
                return

            project_id = item.data(Qt.UserRole)
            project_name = item.text()

            reply = QMessageBox.question(
                self,
                "Delete Project",
                f"Delete project '{project_name}'?",
                QMessageBox.Yes | QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                if self.project_manager.delete_project(project_id):
                    self.project_deleted.emit(project_id)
                    self._refresh_project_list()
                    logger.info("Deleted project: %s", project_name)
                else:
                    QMessageBox.critical(self, "Error", "Failed to delete project.")

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to delete project: %s", str(e))
            QMessageBox.critical(self, "Error", f"Failed to delete project: {str(e)}")

    def _on_project_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle project double-click."""
        self._open_selected_project()
