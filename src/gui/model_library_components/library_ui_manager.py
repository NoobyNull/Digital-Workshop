"""
UI management for model library.

Handles UI creation, layout, and styling.
"""

from PySide6.QtCore import Qt, QSortFilterProxyModel, QModelIndex, QSize
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGroupBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListView,
    QProgressBar,
    QPushButton,
    QTableView,
    QTabWidget,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QTreeView,
)

from src.core.logging_config import get_logger
from src.gui.theme import SPACING_4, SPACING_8, SPACING_12, SPACING_16, SPACING_24
from src.gui.multi_root_file_system_model import MultiRootFileSystemModel

from .file_system_proxy import FileSystemProxyModel
from .grid_icon_delegate import GridIconDelegate


logger = get_logger(__name__)


class LibraryUIManager:
    """Manages UI creation and styling for model library."""

    def __init__(self, library_widget):
        """
        Initialize UI manager.

        Args:
            library_widget: The model library widget
        """
        self.library_widget = library_widget
        self.logger = get_logger(__name__)

    def init_ui(self) -> None:
        """Initialize the UI."""
        main_layout = QVBoxLayout(self.library_widget)
        main_layout.setContentsMargins(SPACING_8, SPACING_8, SPACING_8, SPACING_8)
        main_layout.setSpacing(SPACING_8)

        self.create_search_bar(main_layout)

        self.library_widget.internal_tabs = QTabWidget()
        main_layout.addWidget(self.library_widget.internal_tabs)

        # Library tab
        library_container = QWidget()
        library_layout = QVBoxLayout(library_container)
        library_layout.setContentsMargins(0, 0, 0, 0)
        library_layout.setSpacing(SPACING_8)

        self.create_model_view_area(library_layout)
        self.create_status_bar(library_layout)

        self.library_widget.internal_tabs.addTab(library_container, "Library")

        # Files tab
        files_container = QWidget()
        files_layout = QVBoxLayout(files_container)
        files_layout.setContentsMargins(0, 0, 0, 0)
        files_layout.setSpacing(SPACING_8)

        self.create_file_browser(files_layout)

        self.library_widget.internal_tabs.addTab(files_container, "Files")

        self.apply_styling()

    def create_search_bar(self, parent_layout: QVBoxLayout) -> None:
        """Create search and filter controls."""
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(SPACING_8)

        self.library_widget.search_box = QLineEdit()
        self.library_widget.search_box.setPlaceholderText("Search models...")
        controls_layout.addWidget(QLabel("Search:"))
        controls_layout.addWidget(self.library_widget.search_box)

        parent_layout.addWidget(controls_frame)

    def create_file_browser(self, parent_layout: QVBoxLayout) -> None:
        """Create file browser UI."""
        group = QGroupBox("File Browser")
        layout = QVBoxLayout(group)

        self.library_widget.file_model = MultiRootFileSystemModel()
        self.library_widget.file_proxy_model = FileSystemProxyModel()
        self.library_widget.file_proxy_model.setSourceModel(
            self.library_widget.file_model
        )

        self.library_widget.file_model.indexing_started.connect(
            self.library_widget._on_indexing_started
        )
        self.library_widget.file_model.indexing_completed.connect(
            self.library_widget._on_indexing_completed
        )

        self.library_widget.file_tree = QTreeView()
        self.library_widget.file_tree.setModel(self.library_widget.file_proxy_model)
        self.library_widget.file_tree.setColumnHidden(1, True)
        self.library_widget.file_tree.setColumnHidden(2, True)
        self.library_widget.file_tree.setColumnHidden(3, True)

        layout.addWidget(self.library_widget.file_tree)

        import_frame = QFrame()
        import_layout = QHBoxLayout(import_frame)
        import_layout.setContentsMargins(0, SPACING_8, 0, 0)

        self.library_widget.refresh_button = QPushButton("Refresh")
        self.library_widget.refresh_button.setToolTip("Refresh directory index")
        self.library_widget.refresh_button.clicked.connect(
            self.library_widget._refresh_file_browser
        )
        import_layout.addWidget(self.library_widget.refresh_button)

        import_layout.addStretch()

        self.library_widget.import_selected_button = QPushButton("Import Selected")
        self.library_widget.import_selected_button.setToolTip("Import selected file(s)")
        import_layout.addWidget(self.library_widget.import_selected_button)

        self.library_widget.import_folder_button = QPushButton("Import Folder")
        self.library_widget.import_folder_button.setToolTip(
            "Import the selected folder"
        )
        import_layout.addWidget(self.library_widget.import_folder_button)

        layout.addWidget(import_frame)

        parent_layout.addWidget(group)

    def create_model_view_area(self, parent_layout: QVBoxLayout) -> None:
        """Create model view area with list and grid views."""
        group = QGroupBox("Models")
        layout = QVBoxLayout(group)

        self.library_widget.view_tabs = QTabWidget()

        self.library_widget.list_view = QTableView()
        self.library_widget.list_model = QStandardItemModel()
        self.library_widget.list_model.setHorizontalHeaderLabels(
            ["Name", "Format", "Size", "Triangles", "Category", "Added Date"]
        )

        self.library_widget.proxy_model = QSortFilterProxyModel()
        self.library_widget.proxy_model.setSourceModel(self.library_widget.list_model)
        self.library_widget.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.library_widget.proxy_model.setFilterKeyColumn(-1)

        self.library_widget.list_view.setModel(self.library_widget.proxy_model)
        self.library_widget.list_view.setSortingEnabled(True)
        self.library_widget.list_view.setSelectionBehavior(QTableView.SelectRows)
        # Removed setAlternatingRowColors(True) - qt-material handles alternating row colors via theme
        header = self.library_widget.list_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for col in range(1, 6):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        self.library_widget.view_tabs.addTab(self.library_widget.list_view, "List")

        self.library_widget.grid_view = QListView()
        self.library_widget.grid_view.setViewMode(QListView.IconMode)
        self.library_widget.grid_view.setResizeMode(QListView.Adjust)
        self.library_widget.grid_view.setSpacing(10)
        self.library_widget.grid_view.setUniformItemSizes(True)
        self.library_widget.grid_view.setModel(self.library_widget.proxy_model)

        # Use custom delegate to hide filenames in grid view
        grid_delegate = GridIconDelegate(self.library_widget.grid_view)
        grid_delegate.set_icon_size(QSize(128, 128))
        self.library_widget.grid_view.setItemDelegate(grid_delegate)

        self.library_widget.view_tabs.addTab(self.library_widget.grid_view, "Grid")

        layout.addWidget(self.library_widget.view_tabs)
        parent_layout.addWidget(group)

    def create_status_bar(self, parent_layout: QVBoxLayout) -> None:
        """Create status bar."""
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(SPACING_8)

        self.library_widget.status_label = QLabel("Ready")
        status_layout.addWidget(self.library_widget.status_label)

        self.library_widget.model_count_label = QLabel("Models: 0")
        status_layout.addWidget(self.library_widget.model_count_label)

        self.library_widget.progress_bar = QProgressBar()
        self.library_widget.progress_bar.setVisible(False)
        status_layout.addWidget(self.library_widget.progress_bar)

        parent_layout.addWidget(status_frame)

    def apply_styling(self) -> None:
        """Apply CSS styling (no-op - qt-material handles this)."""
        pass
