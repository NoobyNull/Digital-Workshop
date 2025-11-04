"""
Project Manager Widget for managing projects in the GUI.

Provides UI for creating, opening, and managing projects.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QInputDialog,
    QMessageBox,
    QFileDialog,
)
from PySide6.QtCore import Qt, Signal

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

    def __init__(self, db_manager: DatabaseManager, parent=None):
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
        button_layout = QHBoxLayout()

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

        except Exception as e:
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

        except Exception as e:
            logger.error("Failed to create project: %s", str(e))
            QMessageBox.critical(self, "Error", f"Failed to create project: {str(e)}")

    def _import_library(self) -> None:
        """Import existing library."""
        try:
            folder = QFileDialog.getExistingDirectory(
                self, "Select Library Folder", "", QFileDialog.ShowDirsOnly
            )

            if not folder:
                return

            # Get project name
            name, ok = QInputDialog.getText(
                self, "Import Library", "Project name:", text=folder.split("/")[-1]
            )

            if not ok or not name:
                return

            # Check for duplicate
            if self.project_manager.check_duplicate(name):
                QMessageBox.warning(self, "Duplicate Project", f"Project '{name}' already exists.")
                return

            # Dry run
            dry_run = self.dry_run_analyzer.analyze(folder, name)

            if not dry_run.can_proceed:
                QMessageBox.warning(self, "Import Failed", "No files to import.")
                return

            # Show dry run report
            report_text = (
                f"Import Preview: {name}\n"
                f"Files: {dry_run.allowed_files}\n"
                f"Blocked: {dry_run.blocked_files}\n"
                f"Size: {dry_run.total_size_mb:.2f} MB\n\n"
                "Proceed with import?"
            )

            reply = QMessageBox.question(
                self, "Import Library", report_text, QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # Execute import
                import_report = self.project_importer.import_project(
                    folder,
                    name,
                    structure_type=dry_run.structure_analysis.get("structure_type", "nested"),
                )

                if import_report.success:
                    self.project_created.emit(import_report.project_id)
                    self._refresh_project_list()
                    QMessageBox.information(
                        self,
                        "Import Complete",
                        f"Imported {import_report.files_imported} files.",
                    )
                    logger.info("Imported library: %s", name)
                else:
                    QMessageBox.critical(
                        self,
                        "Import Failed",
                        f"Failed to import library: {import_report.errors[0] if import_report.errors else 'Unknown error'}",
                    )

        except Exception as e:
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

        except Exception as e:
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

        except Exception as e:
            logger.error("Failed to delete project: %s", str(e))
            QMessageBox.critical(self, "Error", f"Failed to delete project: {str(e)}")

    def _on_project_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle project double-click."""
        self._open_selected_project()
