"""
Multi-root file system model for Digital Workshop.

Provides a unified tree view of files from multiple root folders,
with filtering and navigation capabilities.
"""

from pathlib import Path
from typing import List, Optional, Any
from dataclasses import dataclass

from PySide6.QtCore import (
    Qt,
    QAbstractItemModel,
    QModelIndex,
    QFileInfo,
    QMimeData,
    QThread,
    Signal,
)
from PySide6.QtWidgets import QApplication, QStyle

from src.core.logging_config import get_logger
from src.core.root_folder_manager import RootFolderManager, RootFolder


@dataclass
class TreeNode:
    """Represents a node in the multi-root file tree."""

    name: str
    path: Optional[str] = None  # None for root nodes
    is_dir: bool = True
    parent: Optional["TreeNode"] = None
    children: List["TreeNode"] = None
    root_folder: Optional[RootFolder] = None  # Reference to root folder for root nodes

    def __post_init__(self) -> None:
        """TODO: Add docstring."""
        if self.children is None:
            self.children = []

    def add_child(self, child: "TreeNode") -> None:
        """Add a child node."""
        child.parent = self
        self.children.append(child)

    def get_child(self, name: str) -> Optional["TreeNode"]:
        """Get child by name."""
        for child in self.children:
            if child.name == name:
                return child
        return None

    def remove_child(self, name: str) -> bool:
        """Remove child by name."""
        for i, child in enumerate(self.children):
            if child.name == name:
                self.children.pop(i)
                return True
        return False

    def row(self) -> int:
        """Get row index within parent."""
        if self.parent:
            return self.parent.children.index(self)
        return 0


class DirectoryIndexer(QThread):
    """
    Background thread for indexing directory contents to prevent UI freezing.
    """

    indexing_complete = Signal(dict)  # {node_path: [child_nodes]}

    def __init__(self, directories_to_index: List[str]) -> None:
        """TODO: Add docstring."""
        super().__init__()
        self.directories_to_index = directories_to_index
        self.logger = get_logger(__name__)
        self._is_cancelled = False

    def cancel(self) -> None:
        """TODO: Add docstring."""
        self._is_cancelled = True

    def run(self) -> None:
        """Index directory contents in background."""
        indexed_data = {}

        for dir_path in self.directories_to_index:
            if self._is_cancelled:
                break

            try:
                path = Path(dir_path)
                if path.exists() and path.is_dir():
                    children = []
                    try:
                        for item in path.iterdir():
                            if self._is_cancelled:
                                break
                            # Skip hidden files
                            if not item.name.startswith("."):
                                children.append(
                                    {
                                        "name": item.name,
                                        "path": str(item),
                                        "is_dir": item.is_dir(),
                                    }
                                )
                    except PermissionError:
                        self.logger.warning("Permission denied accessing: %s", path)
                        continue

                    # Sort: directories first, then files
                    children.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
                    indexed_data[dir_path] = children

            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                self.logger.error("Error indexing directory %s: {e}", dir_path)

        if not self._is_cancelled:
            self.indexing_complete.emit(indexed_data)


class MultiRootFileSystemModel(QAbstractItemModel):
    """
    File system model that displays multiple root folders as a unified tree.

    Presents configured root folders as top-level items, with their contents
    displayed as subtrees. Supports lazy loading and filtering.
    """

    indexing_started = Signal()
    indexing_completed = Signal()

    def __init__(self, parent=None) -> None:
        """TODO: Add docstring."""
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.root_folder_manager = RootFolderManager.get_instance()
        self.root_node = TreeNode("Root", is_dir=True)

        # Background indexing
        self.indexer = None
        self.indexed_data = {}  # Cache for indexed directory contents

        # Connect to folder manager changes
        self.root_folder_manager.folders_changed.connect(self._on_folders_changed)

        self._build_tree()
        self._start_background_indexing()
        self.logger.info("MultiRootFileSystemModel initialized")

    def refresh_index(self) -> None:
        """Manually trigger re-indexing of all directories."""
        self.logger.info("Manual refresh requested - clearing index cache")
        self.indexed_data.clear()
        self._start_background_indexing()

    def _on_folders_changed(self) -> None:
        """Handle changes to root folder configuration."""
        self.logger.debug("Root folders changed, rebuilding tree")
        self.beginResetModel()
        self._build_tree()
        self.endResetModel()

        # Start background indexing for all root folders
        self._start_background_indexing()

    def _build_tree(self) -> None:
        """Build the tree structure from configured root folders."""
        self.root_node.children.clear()

        for folder in self.root_folder_manager.get_enabled_folders():
            root_node = TreeNode(
                name=folder.display_name,
                path=folder.path,
                is_dir=True,
                root_folder=folder,
            )
            self.root_node.add_child(root_node)
            self.logger.debug("Added root folder: %s ({folder.path})", folder.display_name)

    def _get_node(self, index: QModelIndex) -> Optional[TreeNode]:
        """Get the TreeNode for a given model index."""
        if not index.isValid():
            return self.root_node
        return index.internalPointer()

    def _ensure_children_loaded(self, node: TreeNode) -> None:
        """Ensure children are loaded for a directory node."""
        if not node.is_dir or node.children:
            return

        # Check if we have indexed data for this directory
        if node.path in self.indexed_data:
            # Use pre-indexed data
            for child_data in self.indexed_data[node.path]:
                child_node = TreeNode(
                    name=child_data["name"],
                    path=child_data["path"],
                    is_dir=child_data["is_dir"],
                )
                node.add_child(child_node)
            return

        # Fallback: Load children from filesystem (for directories not yet indexed)
        try:
            path = Path(node.path)
            if path.exists() and path.is_dir():
                # Get directory contents
                items = []
                try:
                    for item in path.iterdir():
                        if not item.name.startswith("."):  # Skip hidden files
                            items.append(item)
                except PermissionError:
                    self.logger.warning("Permission denied accessing: %s", path)
                    return

                # Sort: directories first, then files
                items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))

                for item in items:
                    child_node = TreeNode(name=item.name, path=str(item), is_dir=item.is_dir())
                    node.add_child(child_node)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error loading children for %s: {e}", node.path)

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        """Create a model index for the given row, column, and parent."""
        parent_node = self._get_node(parent)
        if not parent_node or row < 0 or row >= len(parent_node.children):
            return QModelIndex()

        child_node = parent_node.children[row]
        return self.createIndex(row, column, child_node)

    def parent(self, index: QModelIndex) -> QModelIndex:
        """Get the parent index for a given index."""
        if not index.isValid():
            return QModelIndex()

        node = self._get_node(index)
        if not node or not node.parent or node.parent == self.root_node:
            return QModelIndex()

        return self.createIndex(node.parent.row(), 0, node.parent)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Get the number of rows (children) for a given parent."""
        parent_node = self._get_node(parent)
        if not parent_node:
            return 0

        # Lazy load children for directories
        if parent_node.is_dir and not parent_node.children:
            self._ensure_children_loaded(parent_node)

        return len(parent_node.children)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Get the number of columns."""
        return 4  # Name, Size, Type, Modified

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """Get data for a given index and role."""
        if not index.isValid():
            return None

        node = self._get_node(index)
        if not node:
            return None

        column = index.column()

        if role == Qt.DisplayRole:
            if column == 0:  # Name
                return node.name
            elif column == 1:  # Size
                if not node.is_dir and node.path:
                    try:
                        return QFileInfo(node.path).size()
                    except Exception:
                        return 0
                return ""
            elif column == 2:  # Type
                if node.is_dir:
                    return "Folder"
                elif node.path:
                    suffix = Path(node.path).suffix.lower()
                    return suffix[1:].upper() if suffix else "File"
                return "File"
            elif column == 3:  # Modified
                if node.path:
                    try:
                        return QFileInfo(node.path).lastModified()
                    except Exception:
                        return None
                return None

        elif role == Qt.DecorationRole and column == 0:
            # Icon for files/folders
            if node.is_dir:
                return QApplication.style().standardIcon(QStyle.SP_DirIcon)
            else:
                return QApplication.style().standardIcon(QStyle.SP_FileIcon)

        elif role == Qt.ToolTipRole:
            if node.path:
                return node.path
            return node.name

        return None

    def headerData(self, section: int, orientation: int, role: int = Qt.DisplayRole) -> Any:
        """Get header data."""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            headers = ["Name", "Size", "Type", "Modified"]
            if section < len(headers):
                return headers[section]
        return None

    def hasChildren(self, parent: QModelIndex = QModelIndex()) -> bool:
        """Check if a parent has children."""
        parent_node = self._get_node(parent)
        if not parent_node:
            return False

        # Root always has children (root folders)
        if parent_node == self.root_node:
            return True

        # For directories, check if they have children (lazy load)
        if parent_node.is_dir:
            if not parent_node.children:
                self._ensure_children_loaded(parent_node)
            return len(parent_node.children) > 0

        return False

    def canFetchMore(self, parent: QModelIndex) -> bool:
        """Check if more data can be fetched for lazy loading."""
        parent_node = self._get_node(parent)
        if not parent_node or not parent_node.is_dir:
            return False
        return len(parent_node.children) == 0

    def fetchMore(self, parent: QModelIndex) -> None:
        """Fetch more data for lazy loading."""
        parent_node = self._get_node(parent)
        if not parent_node or not parent_node.is_dir or parent_node.children:
            return

        # Load children
        self._ensure_children_loaded(parent_node)

        if parent_node.children:
            self.beginInsertRows(parent, 0, len(parent_node.children) - 1)
            # Children already added in _ensure_children_loaded
            self.endInsertRows()

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """Get item flags."""
        if not index.isValid():
            return Qt.NoItemFlags

        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable

        node = self._get_node(index)
        if node and not node.is_dir:
            flags |= Qt.ItemIsDragEnabled

        return flags

    def mimeData(self, indexes: List[QModelIndex]) -> Optional[QMimeData]:
        """Create MIME data for drag operations."""
        if not indexes:
            return None

        mime_data = QMimeData()
        urls = []

        for index in indexes:
            if index.isValid():
                node = self._get_node(index)
                if node and node.path and not node.is_dir:
                    from PySide6.QtCore import QUrl

                    urls.append(QUrl.fromLocalFile(node.path))

        if urls:
            mime_data.setUrls(urls)

        return mime_data

    def supportedDragActions(self) -> Qt.DropActions:
        """Get supported drag actions."""
        return Qt.CopyAction

    def get_file_path(self, index: QModelIndex) -> Optional[str]:
        """Get the full file path for a given index."""
        node = self._get_node(index)
        return node.path if node else None

    def filePath(self, index: QModelIndex) -> str:
        """Compatibility method for QFileSystemModel interface."""
        path = self.get_file_path(index)
        return path if path else ""

    def get_file_info(self, index: QModelIndex) -> Optional[QFileInfo]:
        """Get QFileInfo for a given index."""
        path = self.get_file_path(index)
        return QFileInfo(path) if path else None

    def is_dir(self, index: QModelIndex) -> bool:
        """Check if the item at index is a directory."""
        node = self._get_node(index)
        return node.is_dir if node else False

    def _start_background_indexing(self) -> None:
        """Start background indexing of all root folder directories."""
        # Cancel any existing indexing
        if self.indexer and self.indexer.isRunning():
            self.indexer.cancel()
            self.indexer.wait(1000)

        # Get all root folder paths
        root_paths = []
        for folder in self.root_folder_manager.get_enabled_folders():
            root_paths.append(folder.path)

        if not root_paths:
            return

        # Start new indexing
        self.indexer = DirectoryIndexer(root_paths)
        self.indexer.indexing_complete.connect(self._on_indexing_complete)
        self.indexer.start()
        self.logger.debug("Started background indexing for %s root directories", len(root_paths))

        # Emit signal for status update
        self.indexing_started.emit()

    def _on_indexing_complete(self, indexed_data: dict) -> None:
        """Handle completion of background indexing."""
        self.indexed_data.update(indexed_data)
        self.logger.debug("Background indexing completed for %s directories", len(indexed_data))

        # Clean up indexer
        if self.indexer:
            self.indexer.deleteLater()
            self.indexer = None

        # Emit completion signal
        self.indexing_completed.emit()

    def refresh(self) -> None:
        """Refresh the entire model."""
        self.logger.debug("Refreshing multi-root file system model")
        self.beginResetModel()
        self._build_tree()
        self.endResetModel()

    def fileInfo(self, index: QModelIndex) -> QFileInfo:
        """Get QFileInfo for the item at the given index (for compatibility with QFileSystemModel)."""
        if not index.isValid():
            return QFileInfo()

        node = self._get_node(index)
        if node and node.path:
            return QFileInfo(node.path)

        return QFileInfo()
