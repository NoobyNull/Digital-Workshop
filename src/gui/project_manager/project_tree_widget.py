"""
Project Tree Widget - Hierarchical project and file browser with tab navigation.

Provides a tree view showing projects with expandable file hierarchies,
and auto-switches to appropriate tabs when files are clicked.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import tempfile
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QMessageBox,
    QFileDialog,
    QInputDialog,
    QMenu,
    QSizePolicy,
    QAbstractItemView,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent

from ..layout.flow_layout import FlowLayout

from ...core.services.project_manager import ProjectManager
from ...core.services.project_importer import ProjectImporter
from ...core.services.dry_run_analyzer import DryRunAnalyzer
from ...core.database.database_manager import DatabaseManager
from ...core.export.dww_export_manager import PJCTExportManager
from ...core.export.dww_import_manager import PJCTImportManager
from ...core.logging_config import get_logger
from ...core.services.file_type_registry import (
    get_tab_for_extension,
    get_tree_category_for_extension,
)

logger = get_logger(__name__)


class ProjectHierarchyTree(QTreeWidget):
    """QTreeWidget with drag/drop notifications."""

    itemsDropped = Signal(list)
    externalPathsDropped = Signal(list, object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        # Allow internal moves plus external drops (file system).
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.MoveAction)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # type: ignore[override]
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:  # type: ignore[override]
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:  # type: ignore[override]
        # External drop (e.g., from OS) ships URLs.
        if event.mimeData().hasUrls():
            paths = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    paths.append(url.toLocalFile())
            if paths:
                # Pass along drop target so caller can resolve the owning project.
                target_item = self.itemAt(event.position().toPoint())
                self.externalPathsDropped.emit(paths, target_item)
                event.acceptProposedAction()
                return

        dragged = list(self.selectedItems())
        super().dropEvent(event)
        if dragged:
            self.itemsDropped.emit(dragged)


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
        self.group_items: Dict[str, QTreeWidgetItem] = {}
        self.ungrouped_item: QTreeWidgetItem | None = None
        self._setup_ui()
        self._refresh_project_tree()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        layout = QVBoxLayout()

        # Tree widget for hierarchical view
        self.tree_widget = ProjectHierarchyTree()
        self.tree_widget.setHeaderLabels(["Projects & Files"])
        self.tree_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree_widget.itemClicked.connect(self._on_item_clicked)
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self._on_context_menu)
        self.tree_widget.itemsDropped.connect(self._handle_items_dropped)
        self.tree_widget.externalPathsDropped.connect(
            self._handle_external_paths_dropped
        )
        layout.addWidget(self.tree_widget)

        # Buttons
        button_layout = FlowLayout()

        new_btn = QPushButton("New Project")
        new_btn.clicked.connect(self._create_new_project)
        button_layout.addWidget(new_btn)

        import_btn = QPushButton("Import Library")
        import_btn.clicked.connect(self._import_library)
        button_layout.addWidget(import_btn)

        add_files_btn = QPushButton("Add Files")
        add_files_btn.clicked.connect(self._add_files_to_project)
        button_layout.addWidget(add_files_btn)

        new_group_btn = QPushButton("New Group")
        new_group_btn.clicked.connect(self._create_group_via_dialog)
        button_layout.addWidget(new_group_btn)

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
            self.group_items.clear()
            self.ungrouped_item = None

            projects = self.project_manager.list_projects()
            groups = self.project_manager.list_project_groups()

            # Build group hierarchy
            if groups:
                children_map: Dict[Optional[str], List[Dict[str, Any]]] = {}
                for group in groups:
                    children_map.setdefault(group.get("parent_id"), []).append(group)

                for grp_list in children_map.values():
                    grp_list.sort(
                        key=lambda g: (
                            (g.get("sort_order") or 0),
                            g.get("name", "").lower(),
                        )
                    )

                for root_group in children_map.get(None, []):
                    item = self._create_group_item(root_group)
                    self.tree_widget.addTopLevelItem(item)
                    self._populate_group_children(item, children_map)

            # Ungrouped bucket
            self.ungrouped_item = QTreeWidgetItem()
            self.ungrouped_item.setText(0, "Ungrouped Projects")
            self.ungrouped_item.setData(0, Qt.UserRole, None)
            self.ungrouped_item.setData(0, Qt.UserRole + 1, "ungrouped")
            self.ungrouped_item.setFlags(
                Qt.ItemIsEnabled | Qt.ItemIsDropEnabled | Qt.ItemIsSelectable
            )
            self.tree_widget.addTopLevelItem(self.ungrouped_item)

            if not projects:
                placeholder = QTreeWidgetItem()
                placeholder.setText(
                    0, "No projects found. Use 'New Project' or 'Import Project' above."
                )
                placeholder.setFlags(Qt.NoItemFlags)
                self.ungrouped_item.addChild(placeholder)
                self.tree_widget.expandItem(self.ungrouped_item)
                logger.info("Refreshed project tree: no projects found")
                return

            for project in projects:
                project_id = project["id"]
                project_name = project["name"]
                project_item = self._create_project_item(project_name, project_id)
                if project.get("import_tag") == "imported_project":
                    project_item.setText(0, f"{project_name} [Imported]")
                parent_group_id = project.get("group_id")
                parent_item = (
                    self.group_items.get(parent_group_id)
                    if parent_group_id
                    else self.ungrouped_item
                )
                if parent_item is None:
                    parent_item = self.ungrouped_item
                parent_item.addChild(project_item)
                self.project_items[project_id] = project_item
                self._load_project_files(project_id, project_item)

            self.tree_widget.expandItem(self.ungrouped_item)
            logger.info("Refreshed project tree: %s projects", len(projects))

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to refresh project tree: %s", str(e))
            QMessageBox.critical(self, "Error", f"Failed to refresh projects: {str(e)}")

    def _create_group_item(self, group: Dict[str, Any]) -> QTreeWidgetItem:
        item = QTreeWidgetItem()
        item.setText(0, group.get("name", "Group"))
        item.setData(0, Qt.UserRole, group.get("id"))
        item.setData(0, Qt.UserRole + 1, "group")
        item.setFlags(
            Qt.ItemIsEnabled
            | Qt.ItemIsSelectable
            | Qt.ItemIsDragEnabled
            | Qt.ItemIsDropEnabled
        )
        self.group_items[group["id"]] = item
        return item

    def _populate_group_children(
        self,
        parent_item: QTreeWidgetItem,
        children_map: Dict[Optional[str], List[Dict[str, Any]]],
    ) -> None:
        parent_id = parent_item.data(0, Qt.UserRole)
        for child in children_map.get(parent_id, []):
            child_item = self._create_group_item(child)
            parent_item.addChild(child_item)
            self._populate_group_children(child_item, children_map)

    def _create_project_item(self, name: str, project_id: str) -> QTreeWidgetItem:
        project_item = QTreeWidgetItem()
        project_item.setText(0, name)
        project_item.setData(0, Qt.UserRole, project_id)
        project_item.setData(0, Qt.UserRole + 1, "project")
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled
        project_item.setFlags(flags)
        return project_item

    def _load_project_files(
        self, project_id: str, project_item: QTreeWidgetItem
    ) -> None:
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

                # Determine category via central registry
                category = get_tree_category_for_extension(file_ext)

                if category not in categories:
                    categories[category] = []

                categories[category].append(
                    {"name": file_name, "path": file_path, "ext": file_ext}
                )

            # Create category items and add files
            for category in sorted(categories.keys()):
                category_item = QTreeWidgetItem()
                category_item.setText(0, category)
                category_item.setData(0, Qt.UserRole, category)
                category_item.setData(0, Qt.UserRole + 1, "category")
                category_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
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
            global_pos = self.tree_widget.viewport().mapToGlobal(position)
            menu = QMenu(self)

            if not item:
                new_group_action = menu.addAction("New Group…")
                action = menu.exec(global_pos)
                if action == new_group_action:
                    self._create_group_via_dialog()
                return

            item_type = item.data(0, Qt.UserRole + 1)

            if item_type == "project":
                add_files_action = menu.addAction("Add Files")
                open_action = menu.addAction("Open Project")
                export_action = menu.addAction("Export Project")
                move_action = menu.addAction("Move to Group…")
                menu.addSeparator()
                delete_action = menu.addAction("Delete Project")

                action = menu.exec(global_pos)
                if action == add_files_action:
                    self._add_files_to_project()
                elif action == open_action:
                    self._open_project(item.data(0, Qt.UserRole))
                elif action == export_action:
                    self._export_project_as_pjct()
                elif action == move_action:
                    self._move_project_to_group_dialog(item)
                elif action == delete_action:
                    self._delete_selected_project()

            elif item_type == "group":
                add_sub_action = menu.addAction("Add Subgroup…")
                rename_action = menu.addAction("Rename Group…")
                delete_action = menu.addAction("Delete Group…")
                action = menu.exec(global_pos)
                if action == add_sub_action:
                    self._create_group_under_item(item)
                elif action == rename_action:
                    self._rename_group(item)
                elif action == delete_action:
                    self._delete_group(item)

            elif item_type == "ungrouped":
                new_group_action = menu.addAction("New Group…")
                action = menu.exec(global_pos)
                if action == new_group_action:
                    self._create_group_under_item(None)

            elif item_type == "file":
                open_action = menu.addAction("Open File")
                action = menu.exec(global_pos)
                if action == open_action:
                    self._handle_file_selection(
                        item.data(0, Qt.UserRole), open_file=True
                    )

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
            tab_name = get_tab_for_extension(file_ext)

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

                default_group_id = self._group_id_for_item(
                    self.tree_widget.currentItem()
                )
                project_id = self.project_manager.create_project(
                    name, group_id=default_group_id
                )
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
            project_item = self._find_project_item(current_item)
            if not project_item:
                QMessageBox.warning(
                    self,
                    "Invalid Selection",
                    "Please select a project or item within a project.",
                )
                return

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
                except (
                    OSError,
                    IOError,
                    ValueError,
                    TypeError,
                    KeyError,
                    AttributeError,
                ) as e:
                    logger.warning("Failed to add file %s: {str(e)}", file_path)

            if added_count > 0:
                self._refresh_project_tree()
                QMessageBox.information(
                    self,
                    "Files Added",
                    f"Successfully added {added_count} file(s) to project.",
                )
            else:
                QMessageBox.warning(
                    self, "No Files Added", "Failed to add files to project."
                )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to add files to project: %s", str(e))
            QMessageBox.critical(self, "Error", f"Failed to add files: {str(e)}")

    def _create_group_via_dialog(self) -> None:
        # New groups from the toolbar/context should default to top-level unless
        # explicitly invoked via "Add Subgroup".
        self._create_group_under_item(None)

    def _create_group_under_item(self, parent_item: QTreeWidgetItem | None) -> None:
        parent_id = self._group_id_for_item(parent_item) if parent_item else None
        name = self._prompt_group_name(
            "New Group",
            "Group name:",
        )
        if not name:
            return
        try:
            self.project_manager.create_project_group(name, parent_id=parent_id)
            self._refresh_project_tree()
        except ValueError as exc:
            QMessageBox.warning(self, "Create Group", str(exc))

    def _rename_group(self, item: QTreeWidgetItem) -> None:
        group_id = item.data(0, Qt.UserRole)
        if not group_id:
            return
        name = self._prompt_group_name(
            "Rename Group", "New name:", default=item.text(0)
        )
        if not name:
            return
        if self.project_manager.rename_project_group(group_id, name):
            self._refresh_project_tree()

    def _delete_group(self, item: QTreeWidgetItem) -> None:
        group_id = item.data(0, Qt.UserRole)
        if not group_id:
            return
        reply = QMessageBox.question(
            self,
            "Delete Group",
            "Delete this group and move its projects to 'Ungrouped'? This also removes subgroups.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        if self.project_manager.delete_project_group(group_id):
            self._refresh_project_tree()

    def _move_project_to_group_dialog(self, item: QTreeWidgetItem) -> None:
        project_id = item.data(0, Qt.UserRole)
        if not project_id:
            return
        options: List[str] = ["Ungrouped"]
        id_map = {"Ungrouped": None}
        for group_name, group_id in self._group_display_names():
            options.append(group_name)
            id_map[group_name] = group_id

        selection, ok = QInputDialog.getItem(
            self,
            "Move Project",
            "Select destination group:",
            options,
            0,
            False,
        )
        if not ok or selection is None:
            return
        target_group = id_map.get(selection)
        if self.project_manager.assign_project_to_group(project_id, target_group):
            self._refresh_project_tree()

    def _prompt_group_name(
        self, title: str, label: str, default: str = ""
    ) -> Optional[str]:
        text, ok = QInputDialog.getText(self, title, label, text=default)
        if not ok:
            return None
        cleaned = text.strip()
        return cleaned or None

    def _group_display_names(self) -> List[Tuple[str, Optional[str]]]:
        groups = self.project_manager.list_project_groups()
        by_id = {g["id"]: g for g in groups if g.get("id")}

        def full_name(group: Dict[str, Any]) -> str:
            parts = [group.get("name", "Group")]
            parent_id = group.get("parent_id")
            while parent_id:
                parent = by_id.get(parent_id)
                if not parent:
                    break
                parts.insert(0, parent.get("name", "Group"))
                parent_id = parent.get("parent_id")
            return " / ".join(parts)

        return [(full_name(group), group.get("id")) for group in groups]

    def _find_project_item(
        self, item: QTreeWidgetItem | None
    ) -> QTreeWidgetItem | None:
        """Return the project item for a given tree item (or None)."""
        cursor = item
        while cursor and cursor.data(0, Qt.UserRole + 1) != "project":
            cursor = cursor.parent()
        if cursor and cursor.data(0, Qt.UserRole + 1) == "project":
            return cursor
        return None

    def _collect_files_recursively(self, paths: List[str]) -> List[str]:
        """Expand a mix of files/folders into a unique file list."""
        collected: list[str] = []
        seen: set[str] = set()

        for raw in paths:
            try:
                path = Path(raw)
            except (OSError, ValueError):
                logger.warning("Skipping invalid drop path: %s", raw)
                continue

            if not path.exists():
                logger.warning("Dropped path does not exist: %s", path)
                continue

            if path.is_file():
                norm = str(path)
                if norm not in seen:
                    seen.add(norm)
                    collected.append(norm)
                continue

            if path.is_dir():
                for child in path.rglob("*"):
                    if child.is_file():
                        norm = str(child)
                        if norm not in seen:
                            seen.add(norm)
                            collected.append(norm)

        return collected

    def _handle_external_paths_dropped(
        self, paths: List[str], target_item: QTreeWidgetItem | None
    ) -> None:
        """Handle OS drag-and-drop of files/folders into the Projects pane."""
        try:
            project_item = self._find_project_item(
                target_item or self.tree_widget.currentItem()
            )
            if not project_item:
                QMessageBox.warning(
                    self,
                    "Drop Target Needed",
                    "Drop files or folders onto a project to add them.",
                )
                return

            project_id = project_item.data(0, Qt.UserRole)
            files = self._collect_files_recursively(paths)

            if not files:
                QMessageBox.information(
                    self, "No Files Found", "Nothing to add from the dropped paths."
                )
                return

            existing = {
                f.get("file_path")
                for f in self.db_manager.get_files_by_project(project_id)
                if f.get("file_path")
            }

            added_count = 0
            skipped_duplicates = 0

            for file_path in files:
                if file_path in existing:
                    skipped_duplicates += 1
                    continue

                try:
                    file_name = Path(file_path).name
                    try:
                        file_size = Path(file_path).stat().st_size
                    except (OSError, IOError):
                        file_size = None

                    self.db_manager.add_file(
                        project_id=project_id,
                        file_path=file_path,
                        file_name=file_name,
                        file_size=file_size,
                        status="linked",
                        link_type="original",
                        original_path=file_path,
                    )
                    added_count += 1
                    logger.info(
                        "Added dropped file to project %s: %s", project_id, file_path
                    )
                except (
                    OSError,
                    IOError,
                    ValueError,
                    TypeError,
                    KeyError,
                    AttributeError,
                ) as e:
                    logger.warning("Failed to add dropped file %s: %s", file_path, e)

            if added_count > 0:
                self._refresh_project_tree()
                summary = f"Added {added_count} file(s)"
                if skipped_duplicates:
                    summary += f" ({skipped_duplicates} already linked and skipped)"
                QMessageBox.information(self, "Files Added", summary)
            else:
                QMessageBox.warning(
                    self,
                    "No Files Added",
                    "No new files were added from the dropped paths.",
                )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Error handling dropped paths: %s", str(e))
            QMessageBox.critical(
                self, "Error", f"Failed to handle dropped files: {str(e)}"
            )

    def _handle_items_dropped(self, items: List[QTreeWidgetItem]) -> None:
        changed = False
        for item in items:
            item_type = item.data(0, Qt.UserRole + 1)
            if item_type == "project":
                project_id = item.data(0, Qt.UserRole)
                parent_item = item.parent()
                target_group = self._group_id_for_item(parent_item)
                if self.project_manager.assign_project_to_group(
                    project_id, target_group
                ):
                    changed = True
            elif item_type == "group":
                group_id = item.data(0, Qt.UserRole)
                if not group_id:
                    continue
                parent_item = item.parent()
                new_parent_id = self._group_id_for_item(parent_item)
                if parent_item and self._is_descendant(parent_item, item):
                    QMessageBox.warning(
                        self,
                        "Invalid Move",
                        "Cannot move a group inside one of its descendants.",
                    )
                    self._refresh_project_tree()
                    return
                if self.project_manager.move_project_group(group_id, new_parent_id):
                    changed = True
        if changed:
            self._refresh_project_tree()

    def _group_id_for_item(self, item: QTreeWidgetItem | None) -> Optional[str]:
        if not item:
            return None
        item_type = item.data(0, Qt.UserRole + 1)
        if item_type == "group":
            return item.data(0, Qt.UserRole)
        return None

    def _is_descendant(
        self, parent: QTreeWidgetItem, potential_child: QTreeWidgetItem
    ) -> bool:
        cursor = parent
        while cursor:
            if cursor == potential_child:
                return True
            cursor = cursor.parent()
        return False

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
                refresh_ui=self._refresh_project_tree,
                logger=logger,
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
                QMessageBox.warning(
                    self, "Invalid Selection", "Please select a project to delete."
                )
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
                QMessageBox.warning(
                    self, "Invalid Selection", "Please select a project to export."
                )
                return

            project_id = current_item.data(0, Qt.UserRole)
            project_name = current_item.text(0).replace(" [Imported]", "")

            # Get save location
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Project",
                f"{project_name}.pjt",
                "Project File (*.pjt);;All Files (*)",
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
                "Project File (*.pjt);;All Files (*)",
            )

            if not file_path:
                return

            # Get project info from project file
            import_manager = PJCTImportManager(self.db_manager)
            success, manifest = import_manager.get_pjct_info(file_path)

            if not success or not manifest:
                QMessageBox.critical(
                    self, "Import Failed", "Could not read project file information."
                )
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
                # Import project file
                success, message, _ = import_manager.import_project(
                    file_path, temp_dir, verify_integrity=True, import_thumbnails=True
                )

                if not success:
                    QMessageBox.critical(self, "Import Failed", message)
                    logger.error("Failed to import project file: %s", message)
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
                    logger.info("Imported project: %s", import_name)
                else:
                    QMessageBox.critical(
                        self,
                        "Import Failed",
                        f"Failed to import project files: {import_report.error}",
                    )
                    logger.error(
                        "Failed to import project files: %s", import_report.error
                    )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to import project: %s", str(e))
            QMessageBox.critical(self, "Error", f"Failed to import project: {str(e)}")
