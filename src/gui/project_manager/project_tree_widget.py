"""
Project Tree Widget - Hierarchical project and file browser with tab navigation.

Provides a tree view showing projects with expandable file hierarchies,
and auto-switches to appropriate tabs when files are clicked.
"""

from pathlib import Path
from typing import Dict, List
import tempfile
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QMessageBox,
    QFileDialog,
    QInputDialog,
    QMenu,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal

from ...core.services.project_manager import ProjectManager
from ...core.services.project_importer import ProjectImporter
from ...core.services.dry_run_analyzer import DryRunAnalyzer
from ...core.database.database_manager import DatabaseManager
from ...core.export.dww_export_manager import PJCTExportManager
from ...core.export.dww_import_manager import DWWImportManager
from ...core.logging_config import get_logger

logger = get_logger(__name__)

# File type to tab mapping - must match actual tab names in main_window.py
FILE_TYPE_TAB_MAP = {
    ".nc": "G Code Previewer",
    ".gcode": "G Code Previewer",
    ".stl": "Model Previewer",
    ".obj": "Model Previewer",
    ".step": "Model Previewer",
    ".stp": "Model Previewer",
    ".3mf": "Model Previewer",
    ".ply": "Model Previewer",
}

# File type to category mapping for tree organization
FILE_TYPE_CATEGORY_MAP = {
    # Models
    ".stl": "Models",
    ".obj": "Models",
    ".step": "Models",
    ".stp": "Models",
    ".3mf": "Models",
    ".ply": "Models",
    # G-Code
    ".nc": "Gcode",
    ".gcode": "Gcode",
    # Cut Lists
    ".csv": "Cut Lists",
    ".xlsx": "Cut Lists",
    ".xls": "Cut Lists",
    # Cost Sheets
    ".pdf": "Cost Sheets",
    ".docx": "Cost Sheets",
    ".doc": "Cost Sheets",
    # Other documents
    ".txt": "Documents",
    ".md": "Documents",
}


class ProjectTreeWidget(QWidget):
    """Widget for managing projects with hierarchical file tree view."""

    project_opened = Signal(str)  # project_id
    project_created = Signal(str)  # project_id
    project_deleted = Signal(str)  # project_id
    file_selected = Signal(str, str)  # file_path, tab_name
    tab_switch_requested = Signal(str)  # tab_name

    def __init__(self, db_manager: DatabaseManager, parent=None) -> None:
        """
        Initialize project tree widget.

        Args:
            db_manager: DatabaseManager instance
            parent: Parent widget
        """
        super().__init__(parent)

        # Set flexible size policy to allow shrinking when tabbed with other widgets
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # Set minimum size to prevent zero-width/zero-height widgets
        from src.gui.theme import MIN_WIDGET_SIZE

        self.setMinimumSize(MIN_WIDGET_SIZE, MIN_WIDGET_SIZE)

        self.db_manager = db_manager
        self.project_manager = ProjectManager(db_manager)
        self.project_importer = ProjectImporter(db_manager)
        self.dry_run_analyzer = DryRunAnalyzer()
        self.project_items: Dict[str, QTreeWidgetItem] = {}
        self._setup_ui()
        self._refresh_project_tree()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        layout = QVBoxLayout()

        # Tree widget for hierarchical view
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Projects & Files"])
        self.tree_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree_widget.itemClicked.connect(self._on_item_clicked)
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self._on_context_menu)
        layout.addWidget(self.tree_widget)

        # Buttons
        button_layout = QHBoxLayout()

        new_btn = QPushButton("New Project")
        new_btn.clicked.connect(self._create_new_project)
        button_layout.addWidget(new_btn)

        import_btn = QPushButton("Import Library")
        import_btn.clicked.connect(self._import_library)
        button_layout.addWidget(import_btn)

        add_files_btn = QPushButton("Add Files")
        add_files_btn.clicked.connect(self._add_files_to_project)
        button_layout.addWidget(add_files_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_project_tree)
        button_layout.addWidget(refresh_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_selected_project)
        button_layout.addWidget(delete_btn)

        export_btn = QPushButton("Export Project")
        export_btn.clicked.connect(self._export_project_as_pjct)
        button_layout.addWidget(export_btn)

        import_project_btn = QPushButton("Import Project")
        import_project_btn.clicked.connect(self._import_pjct_project)
        button_layout.addWidget(import_project_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _refresh_project_tree(self) -> None:
        """Refresh the project tree."""
        try:
            self.tree_widget.clear()
            self.project_items.clear()
            projects = self.project_manager.list_projects()

            for project in projects:
                project_id = project["id"]
                project_name = project["name"]

                # Create project item
                project_item = QTreeWidgetItem()
                project_item.setText(0, project_name)
                project_item.setData(0, Qt.UserRole, project_id)
                project_item.setData(0, Qt.UserRole + 1, "project")

                if project.get("import_tag") == "imported_project":
                    project_item.setText(0, f"{project_name} [Imported]")

                self.tree_widget.addTopLevelItem(project_item)
                self.project_items[project_id] = project_item

                # Load files for this project
                self._load_project_files(project_id, project_item)

            logger.info("Refreshed project tree: %s projects", len(projects))

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to refresh project tree: %s", str(e))
            QMessageBox.critical(self, "Error", f"Failed to refresh projects: {str(e)}")

    def _load_project_files(self, project_id: str, project_item: QTreeWidgetItem) -> None:
        """Load files for a project into the tree, organized by category."""
        try:
            # Get files from database
            files = self.db_manager.get_files_by_project(project_id)

            # Organize files by category
            categories: Dict[str, List] = {}

            for file_info in files:
                file_path = file_info.get("file_path")
                if not file_path:
                    continue

                file_name = Path(file_path).name
                file_ext = Path(file_path).suffix.lower()

                # Determine category
                category = FILE_TYPE_CATEGORY_MAP.get(file_ext, "Other")

                if category not in categories:
                    categories[category] = []

                categories[category].append({"name": file_name, "path": file_path, "ext": file_ext})

            # Create category items and add files
            for category in sorted(categories.keys()):
                category_item = QTreeWidgetItem()
                category_item.setText(0, category)
                category_item.setData(0, Qt.UserRole, category)
                category_item.setData(0, Qt.UserRole + 1, "category")
                project_item.addChild(category_item)

                # Add files to category
                for file_info in sorted(categories[category], key=lambda x: x["name"]):
                    file_item = QTreeWidgetItem()
                    file_item.setText(0, file_info["name"])
                    file_item.setData(0, Qt.UserRole, file_info["path"])
                    file_item.setData(0, Qt.UserRole + 1, "file")
                    category_item.addChild(file_item)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.warning("Failed to load files for project %s: {str(e)}", project_id)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle item click - single click on file to preview and switch tab."""
        item_type = item.data(0, Qt.UserRole + 1)
        if item_type == "file":
            file_path = item.data(0, Qt.UserRole)
            self._handle_file_selection(file_path)

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle item double-click - expand/collapse categories or open projects."""
        item_type = item.data(0, Qt.UserRole + 1)
        if item_type == "project":
            project_id = item.data(0, Qt.UserRole)
            self._open_project(project_id)
        elif item_type == "category":
            # Toggle category expansion
            if item.isExpanded():
                item.setExpanded(False)
            else:
                item.setExpanded(True)
        elif item_type == "file":
            file_path = item.data(0, Qt.UserRole)
            self._handle_file_selection(file_path, open_file=True)

    def _on_context_menu(self, position) -> None:
        """Handle right-click context menu."""
        try:
            item = self.tree_widget.itemAt(position)
            if not item:
                return

            item_type = item.data(0, Qt.UserRole + 1)

            # Create context menu
            menu = QMenu(self)

            if item_type == "project":
                # Project context menu
                add_files_action = menu.addAction("Add Files")
                add_files_action.triggered.connect(self._add_files_to_project)

                menu.addSeparator()

                open_action = menu.addAction("Open Project")
                open_action.triggered.connect(lambda: self._open_project(item.data(0, Qt.UserRole)))

                export_action = menu.addAction("Export Project")
                export_action.triggered.connect(self._export_project_as_pjct)

                menu.addSeparator()

                delete_action = menu.addAction("Delete Project")
                delete_action.triggered.connect(self._delete_selected_project)

            elif item_type == "file":
                # File context menu
                open_action = menu.addAction("Open File")
                open_action.triggered.connect(
                    lambda: self._handle_file_selection(item.data(0, Qt.UserRole), open_file=True)
                )

            # Show menu at cursor position
            if menu.actions():
                menu.exec(self.tree_widget.mapToGlobal(position))

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Error showing context menu: %s", str(e))

    def _handle_file_selection(self, file_path: str, open_file: bool = False) -> None:
        """Handle file selection and tab switching."""
        try:
            if not file_path or not Path(file_path).exists():
                logger.warning("File not found: %s", file_path)
                return

            # Determine tab based on file extension
            file_ext = Path(file_path).suffix.lower()
            tab_name = FILE_TYPE_TAB_MAP.get(file_ext)

            if tab_name:
                self.file_selected.emit(file_path, tab_name)
                self.tab_switch_requested.emit(tab_name)
                logger.info("File selected: %s, switching to {tab_name}", file_path)
            else:
                logger.debug("No tab mapping for file type: %s", file_ext)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Error handling file selection: %s", str(e))

    def _create_new_project(self) -> None:
        """Create new project."""
        try:
            name, ok = QInputDialog.getText(self, "New Project", "Project name:")

            if ok and name:
                if self.project_manager.check_duplicate(name):
                    QMessageBox.warning(
                        self, "Duplicate Project", f"Project '{name}' already exists."
                    )
                    return

                project_id = self.project_manager.create_project(name)
                self.project_created.emit(project_id)
                self._refresh_project_tree()
                logger.info("Created project: %s", name)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to create project: %s", str(e))
            QMessageBox.critical(self, "Error", f"Failed to create project: {str(e)}")

    def _add_files_to_project(self) -> None:
        """Add files to selected project."""
        try:
            current_item = self.tree_widget.currentItem()
            if not current_item:
                QMessageBox.warning(self, "No Selection", "Please select a project.")
                return

            # Get the project item (could be a file or category, need to find parent project)
            item_type = current_item.data(0, Qt.UserRole + 1)
            project_item = current_item

            # If not a project, find the parent project
            if item_type != "project":
                parent = current_item.parent()
                while parent and parent.data(0, Qt.UserRole + 1) != "project":
                    parent = parent.parent()
                if not parent:
                    QMessageBox.warning(
                        self,
                        "Invalid Selection",
                        "Please select a project or item within a project.",
                    )
                    return
                project_item = parent

            project_id = project_item.data(0, Qt.UserRole)

            # Open file dialog to select files
            files, _ = QFileDialog.getOpenFileNames(
                self, "Add Files to Project", "", "All Files (*)"
            )

            if not files:
                return

            # Add files to project
            added_count = 0
            for file_path in files:
                try:
                    file_name = Path(file_path).name
                    file_size = Path(file_path).stat().st_size

                    # Add file to database
                    self.db_manager.add_file(
                        project_id=project_id,
                        file_path=file_path,
                        file_name=file_name,
                        file_size=file_size,
                        status="linked",
                        link_type="original",
                    )
                    added_count += 1
                    logger.info("Added file to project: %s", file_name)
                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                    logger.warning("Failed to add file %s: {str(e)}", file_path)

            if added_count > 0:
                self._refresh_project_tree()
                QMessageBox.information(
                    self,
                    "Files Added",
                    f"Successfully added {added_count} file(s) to project.",
                )
            else:
                QMessageBox.warning(self, "No Files Added", "Failed to add files to project.")

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to add files to project: %s", str(e))
            QMessageBox.critical(self, "Error", f"Failed to add files: {str(e)}")

    def _import_library(self) -> None:
        """Import existing library."""
        try:
            folder = QFileDialog.getExistingDirectory(
                self, "Select Library Folder", "", QFileDialog.ShowDirsOnly
            )

            if not folder:
                return

            name, ok = QInputDialog.getText(
                self, "Import Library", "Project name:", text=folder.split("/")[-1]
            )

            if not ok or not name:
                return

            if self.project_manager.check_duplicate(name):
                QMessageBox.warning(self, "Duplicate Project", f"Project '{name}' already exists.")
                return

            dry_run = self.dry_run_analyzer.analyze(folder, name)

            if not dry_run.can_proceed:
                QMessageBox.warning(self, "Import Failed", "No files to import.")
                return

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
                import_report = self.project_importer.import_project(
                    folder,
                    name,
                    structure_type=dry_run.structure_analysis.get("structure_type", "nested"),
                )

                if import_report.success:
                    self.project_created.emit(import_report.project_id)
                    self._refresh_project_tree()
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

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to import library: %s", str(e))
            QMessageBox.critical(self, "Error", f"Failed to import library: {str(e)}")

    def _open_project(self, project_id: str) -> None:
        """Open selected project."""
        try:
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
            current_item = self.tree_widget.currentItem()
            if not current_item:
                QMessageBox.warning(self, "No Selection", "Please select a project.")
                return

            item_type = current_item.data(0, Qt.UserRole + 1)
            if item_type != "project":
                QMessageBox.warning(self, "Invalid Selection", "Please select a project to delete.")
                return

            project_id = current_item.data(0, Qt.UserRole)
            project_name = current_item.text(0)

            reply = QMessageBox.question(
                self,
                "Delete Project",
                f"Delete project '{project_name}'?",
                QMessageBox.Yes | QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                if self.project_manager.delete_project(project_id):
                    self.project_deleted.emit(project_id)
                    self._refresh_project_tree()
                    logger.info("Deleted project: %s", project_name)
                else:
                    QMessageBox.critical(self, "Error", "Failed to delete project.")

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to delete project: %s", str(e))
            QMessageBox.critical(self, "Error", f"Failed to delete project: {str(e)}")

    def _export_project_as_pjct(self) -> None:
        """Export selected project as PJCT (project) archive."""
        try:
            current_item = self.tree_widget.currentItem()
            if not current_item:
                QMessageBox.warning(self, "No Selection", "Please select a project.")
                return

            item_type = current_item.data(0, Qt.UserRole + 1)
            if item_type != "project":
                QMessageBox.warning(self, "Invalid Selection", "Please select a project to export.")
                return

            project_id = current_item.data(0, Qt.UserRole)
            project_name = current_item.text(0).replace(" [Imported]", "")

            # Get save location
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Project",
                f"{project_name}.pjct",
                "Project File (*.pjct);;All Files (*)",
            )

            if not file_path:
                return

            # Export project
            export_manager = PJCTExportManager(self.db_manager)
            success, message = export_manager.export_project(project_id, file_path)

            if success:
                QMessageBox.information(self, "Export Successful", message)
                logger.info("Exported project %s to %s", project_name, file_path)
            else:
                QMessageBox.critical(self, "Export Failed", message)
                logger.error("Failed to export project: %s", message)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to export project: %s", str(e))
            QMessageBox.critical(self, "Error", f"Failed to export project: {str(e)}")

    def _import_pjct_project(self) -> None:
        """Import a project from PJCT (project) archive."""
        try:
            # Get PJCT file to import
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Import Project",
                "",
                "Project File (*.pjct);;All Files (*)",
            )

            if not file_path:
                return

            # Get project info from DWW file
            import_manager = DWWImportManager(self.db_manager)
            success, manifest = import_manager.get_dww_info(file_path)

            if not success or not manifest:
                QMessageBox.critical(self, "Import Failed", "Could not read DWW file information.")
                return

            # Show import preview
            project_info = manifest.get("project", {})
            project_name = project_info.get("name", "Unknown")
            file_count = manifest.get("file_count", 0)

            preview_text = (
                f"Import Project\n\n"
                f"Project: {project_name}\n"
                f"Files: {file_count}\n"
                f"Created: {project_info.get('created_at', 'Unknown')}\n\n"
                "Proceed with import?"
            )

            reply = QMessageBox.question(
                self,
                "Import Project",
                preview_text,
                QMessageBox.Yes | QMessageBox.No,
            )

            if reply != QMessageBox.Yes:
                return

            # Ask for project name
            import_name, ok = QInputDialog.getText(
                self, "Import Project", "Project name:", text=project_name
            )

            if not ok or not import_name:
                return

            # Check for duplicate
            if self.project_manager.check_duplicate(import_name):
                QMessageBox.warning(
                    self,
                    "Duplicate Project",
                    f"Project '{import_name}' already exists.",
                )
                return

            # Create temporary directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                # Import DWW file
                success, message, _ = import_manager.import_project(
                    file_path, temp_dir, verify_integrity=True, import_thumbnails=True
                )

                if not success:
                    QMessageBox.critical(self, "Import Failed", message)
                    logger.error("Failed to import DWW: %s", message)
                    return

                # Import extracted files as a new project
                import_report = self.project_importer.import_project(
                    temp_dir, import_name, structure_type="flat"
                )

                if import_report.success:
                    self.project_created.emit(import_report.project_id)
                    self._refresh_project_tree()
                    QMessageBox.information(
                        self,
                        "Import Complete",
                        f"Project '{import_name}' imported successfully with {file_count} files.",
                    )
                    logger.info("Imported DWW project: %s", import_name)
                else:
                    QMessageBox.critical(
                        self,
                        "Import Failed",
                        f"Failed to import project files: {import_report.error}",
                    )
                    logger.error("Failed to import project files: %s", import_report.error)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to import DWW project: %s", str(e))
            QMessageBox.critical(self, "Error", f"Failed to import DWW project: {str(e)}")
