"""
UI management for model library.

Handles UI creation, layout, and styling.
"""

from PySide6.QtCore import Qt, QSize, QSettings
from PySide6.QtGui import QStandardItemModel, QAction, QIcon
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
    QMenu,
    QStyle,
)
from src.gui.layout.flow_layout import FlowLayout


from src.core.logging_config import get_logger
from src.gui.theme import SPACING_8
from src.gui.multi_root_file_system_model import MultiRootFileSystemModel

from .file_system_proxy import FileSystemProxyModel
from .grid_icon_delegate import GridIconDelegate
from .numeric_sort_proxy import NumericSortProxyModel
from .recent_models_panel import RecentModelsPanel


logger = get_logger(__name__)


class LibraryUIManager:
    """Manages UI creation and styling for model library."""

    def __init__(self, library_widget) -> None:
        """Initialize UI manager.

        Args:
            library_widget: The model library widget
        """
        self.library_widget = library_widget
        self.logger = get_logger(__name__)

    def _std_icon(self, standard_pixmap) -> QIcon:
        """Return a native Qt icon for a given standard pixmap."""
        try:
            style = self.library_widget.style()
            return style.standardIcon(standard_pixmap)
        except Exception:
            return QIcon()

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

        self.create_recent_models_panel(library_layout)
        self.create_model_view_area(library_layout)
        self.create_status_bar(library_layout)

        self.library_widget.internal_tabs.addTab(
            library_container,
            self._std_icon(QStyle.SP_DirIcon),
            "Library",
        )

        # Files tab (hidden - file browser created for internal use only)
        # Parent the container to the main library widget so the underlying Qt
        # objects (file_tree, models, etc.) stay alive even though the tab is
        # not visible.
        files_container = QWidget(self.library_widget)
        files_layout = QVBoxLayout(files_container)
        files_layout.setContentsMargins(0, 0, 0, 0)
        files_layout.setSpacing(SPACING_8)

        self.create_file_browser(files_layout)

        # Do not add the Files tab to internal_tabs; root-folder configuration now lives
        # in Preferences, and file imports are handled via the main File -> Import flow.
        # self.library_widget.internal_tabs.addTab(
        #     files_container,
        #     self._std_icon(QStyle.SP_DirOpenIcon),
        #     "Files",
        # )

        self.apply_styling()

    def create_search_bar(self, parent_layout: QVBoxLayout) -> None:
        """Create search and filter controls."""
        controls_frame = QFrame()
        controls_frame = QFrame()
        controls_frame.setObjectName("LibraryControls")
        controls_layout = QVBoxLayout(controls_frame)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(SPACING_8)

        # Row 1: Free-text search box (dominant width via stretch)
        search_row = QHBoxLayout()
        search_row.setContentsMargins(0, 0, 0, 0)
        search_row.setSpacing(SPACING_8)
        self.library_widget.search_box = QLineEdit()
        self.library_widget.search_box.setPlaceholderText("Search models...")
        self.library_widget.search_box.setMinimumWidth(300)
        search_row.addWidget(QLabel("Search:"))
        search_row.addWidget(self.library_widget.search_box, 4)
        controls_layout.addLayout(search_row)

        # Row 2: filters under the search bar
        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(SPACING_8)

        # Category filter
        self.library_widget.category_filter = QComboBox()
        self.library_widget.category_filter.setEditable(False)
        self.library_widget.category_filter.addItem("All Categories", userData=None)
        try:
            categories = self.library_widget.db_manager.get_categories()
            for category in categories:
                name = category.get("name")
                if not name:
                    continue
                self.library_widget.category_filter.addItem(name, userData=name)
        except Exception:
            # If categories cannot be loaded, keep the filter with only the default option
            logger.warning(
                "Failed to load categories for model library filter", exc_info=True
            )

        button_row.addWidget(QLabel("Category:"))
        button_row.addWidget(self.library_widget.category_filter)

        # Dirty/clean status filter
        self.library_widget.dirty_filter = QComboBox()
        self.library_widget.dirty_filter.setEditable(False)
        self.library_widget.dirty_filter.addItem("All Models", userData=None)
        self.library_widget.dirty_filter.addItem("Only Dirty", userData="dirty")
        self.library_widget.dirty_filter.addItem("Only Clean", userData="clean")

        button_row.addWidget(QLabel("Status:"))
        button_row.addWidget(self.library_widget.dirty_filter)
        button_row.addStretch(1)

        controls_layout.addLayout(button_row)

        parent_layout.addWidget(controls_frame)

    # Advanced search dialog removed; main search bar now accepts boolean syntax directly

    def create_recent_models_panel(self, parent_layout: QVBoxLayout) -> None:
        """Create the MRU list panel that surfaces recently opened models."""

        # Disable the MRU panel to avoid wasted space / distraction.
        self.library_widget.recent_models_panel = None

    def create_file_browser(self, parent_layout: QVBoxLayout) -> None:
        """Create file browser UI.

        The underlying file tree and controls are kept for internal use, but the
        group box itself is unlabelled so no "File Browser" title bar appears in
        the UI.
        """
        group = QGroupBox("")
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
        import_layout = FlowLayout(import_frame)
        import_layout.setContentsMargins(0, SPACING_8, 0, 0)

        self.library_widget.refresh_button = QPushButton("Refresh")
        self.library_widget.refresh_button.setToolTip("Refresh directory index")
        self.library_widget.refresh_button.setIcon(
            self._std_icon(QStyle.SP_BrowserReload)
        )
        self.library_widget.refresh_button.clicked.connect(
            self.library_widget._refresh_file_browser
        )
        import_layout.addWidget(self.library_widget.refresh_button)

        self.library_widget.import_selected_button = QPushButton("Import Selected")
        self.library_widget.import_selected_button.setToolTip("Import selected file(s)")
        self.library_widget.import_selected_button.setIcon(
            self._std_icon(QStyle.SP_ArrowDown)
        )
        import_layout.addWidget(self.library_widget.import_selected_button)

        self.library_widget.import_folder_button = QPushButton("Import Folder")
        self.library_widget.import_folder_button.setToolTip(
            "Import the selected folder"
        )
        self.library_widget.import_folder_button.setIcon(
            self._std_icon(QStyle.SP_FileDialogNewFolder)
        )
        import_layout.addWidget(self.library_widget.import_folder_button)

        layout.addWidget(import_frame)

        parent_layout.addWidget(group)

    def create_model_view_area(self, parent_layout: QVBoxLayout) -> None:
        """Create model view area with list and grid views."""
        group = QGroupBox("Models")
        layout = QVBoxLayout(group)

        # Row height zoom controlled by Ctrl+Scroll (no slider UI)
        # Initialize row height from settings or default
        settings = QSettings("DigitalWorkshop", "ModelLibrary")
        self.library_widget.current_row_height = settings.value(
            "row_height", 64, type=int
        )
        # Initialize grid icon size from settings or default
        self.library_widget.current_grid_icon_size = settings.value(
            "grid_icon_size", 128, type=int
        )

        self.library_widget.view_tabs = QTabWidget()

        self.library_widget.list_view = QTableView()
        self.library_widget.list_model = QStandardItemModel()
        self.library_widget.list_model.setHorizontalHeaderLabels(
            [
                "Thumbnail",
                "Name",
                "Format",
                "Size",
                "Triangles",
                "Category",
                "Added Date",
                "Dirty",
            ]
        )

        # Use custom numeric sort proxy model for proper sorting and filtering
        self.library_widget.proxy_model = NumericSortProxyModel()
        self.library_widget.proxy_model.setSourceModel(self.library_widget.list_model)
        self.library_widget.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.library_widget.proxy_model.setFilterKeyColumn(-1)

        self.library_widget.list_view.setModel(self.library_widget.proxy_model)
        self.library_widget.list_view.setSortingEnabled(True)
        self.library_widget.list_view.setSelectionBehavior(QTableView.SelectRows)

        # Install event filter on list view to catch Ctrl+Scroll wheel events
        self.library_widget.list_view.viewport().installEventFilter(self.library_widget)

        # Apply initial row height from settings
        initial_height = self.library_widget.current_row_height
        self.library_widget.list_view.setIconSize(QSize(initial_height, initial_height))
        self.library_widget.list_view.verticalHeader().setDefaultSectionSize(
            initial_height
        )

        # Removed setAlternatingRowColors(True) - qt-material handles alternating row colors via theme
        header = self.library_widget.list_view.horizontalHeader()

        # Enable column reordering
        header.setSectionsMovable(True)

        # Set default resize modes BEFORE restoring sizes
        # All columns: interactive (user can resize and sizes persist)
        for col in range(8):
            header.setSectionResizeMode(col, QHeaderView.Interactive)

        # Restore column sizes from settings
        for col in range(8):  # Now 8 columns (Thumbnail + 7 others)
            width = settings.value(f"column_{col}_width", type=int)
            if width:
                header.resizeSection(col, width)
            else:
                # Set default widths if not saved
                if col == 0:  # Thumbnail
                    header.resizeSection(col, 100)
                elif col == 1:  # Name - wider default
                    header.resizeSection(col, 250)
                elif col == 7:  # Dirty status column - narrow
                    header.resizeSection(col, 80)

        # Save column sizes when they change
        header.sectionResized.connect(self._save_column_size)

        # Save column order when it changes
        header.sectionMoved.connect(self._save_column_order)

        # Enable context menu for column visibility
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self._show_column_menu)

        # Column visibility and order will be restored after dock layout restoration (see widget.py)

        self.library_widget.view_tabs.addTab(self.library_widget.list_view, "List")

        self.library_widget.grid_view = QListView()
        self.library_widget.grid_view.setViewMode(QListView.IconMode)
        self.library_widget.grid_view.setResizeMode(QListView.Adjust)
        self.library_widget.grid_view.setSpacing(10)
        self.library_widget.grid_view.setUniformItemSizes(True)
        self.library_widget.grid_view.setModel(self.library_widget.proxy_model)

        # Install event filter on grid view to catch Ctrl+Scroll wheel events
        self.library_widget.grid_view.viewport().installEventFilter(self.library_widget)

        # Apply initial grid icon size from settings
        initial_grid_size = self.library_widget.current_grid_icon_size
        self.library_widget.grid_view.setIconSize(
            QSize(initial_grid_size, initial_grid_size)
        )

        # Use custom delegate to hide filenames in grid view
        self.library_widget.grid_delegate = GridIconDelegate(
            self.library_widget.grid_view
        )
        self.library_widget.grid_delegate.set_icon_size(
            QSize(initial_grid_size, initial_grid_size)
        )
        self.library_widget.grid_view.setItemDelegate(self.library_widget.grid_delegate)

        self.library_widget.view_tabs.addTab(self.library_widget.grid_view, "Grid")

        # Connect tab change to enable/disable thumbnail filtering
        self.library_widget.view_tabs.currentChanged.connect(self._on_view_tab_changed)

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

    def set_row_height(self, value: int) -> None:
        """
        Set the row height for the list view.

        Args:
            value: New row height value (clamped to 32-256 range)
        """
        # Clamp value to valid range
        old_value = value
        value = max(32, min(256, value))

        logger.debug(
            "set_row_height: requested=%s, clamped={value}, current={self.library_widget.current_row_height}",
            old_value,
        )

        # Store current height
        self.library_widget.current_row_height = value

        # Save to settings
        settings = QSettings("DigitalWorkshop", "ModelLibrary")
        settings.setValue("row_height", value)
        logger.debug("Saved row_height to settings: %s", value)

        # Update icon size for list view (thumbnails scale with row height)
        icon_size = QSize(value, value)
        self.library_widget.list_view.setIconSize(icon_size)

        # Update vertical header (row height) for list view
        vertical_header = self.library_widget.list_view.verticalHeader()
        vertical_header.setDefaultSectionSize(value)

        # Force refresh to apply changes
        self.library_widget.list_view.viewport().update()

    def set_grid_icon_size(self, value: int) -> None:
        """
        Set the icon size for the grid view.

        Args:
            value: New icon size value (clamped to 64-512 range)
        """
        # Clamp value to valid range
        old_value = value
        value = max(64, min(512, value))

        logger.debug(
            "set_grid_icon_size: requested=%s, clamped={value}, current={self.library_widget.current_grid_icon_size}",
            old_value,
        )

        # Store current size
        self.library_widget.current_grid_icon_size = value

        # Save to settings
        settings = QSettings("DigitalWorkshop", "ModelLibrary")
        settings.setValue("grid_icon_size", value)
        logger.debug("Saved grid_icon_size to settings: %s", value)

        # Update icon size for grid view
        icon_size = QSize(value, value)
        self.library_widget.grid_view.setIconSize(icon_size)

        # Update delegate icon size
        self.library_widget.grid_delegate.set_icon_size(icon_size)

        # Force refresh to apply changes
        self.library_widget.grid_view.viewport().update()

    def _on_view_tab_changed(self, index: int) -> None:
        """
        Handle view tab change to enable/disable thumbnail filtering.

        Args:
            index: Tab index (0=List, 1=Grid)
        """
        # Enable thumbnail filtering for grid view (index 1), disable for list view (index 0)
        is_grid_view = index == 1
        self.library_widget.proxy_model.filter_no_thumbnails = is_grid_view

        # Invalidate filter to reapply with new settings
        self.library_widget.proxy_model.invalidateFilter()

        logger.debug(
            f"View tab changed to {'Grid' if is_grid_view else 'List'}, thumbnail filtering={'enabled' if is_grid_view else 'disabled'}"
        )

    def _save_column_size(self, column: int, old_size: int, new_size: int) -> None:
        """
        Save column size to settings.

        Args:
            column: Column index
            old_size: Previous size (unused)
            new_size: New size
        """
        settings = QSettings("DigitalWorkshop", "ModelLibrary")
        settings.setValue(f"column_{column}_width", new_size)

    def _save_column_order(
        self, logical_index: int, old_visual_index: int, new_visual_index: int
    ) -> None:
        """
        Save column order to settings when columns are reordered.

        Args:
            logical_index: The logical index of the column being moved
            old_visual_index: The old visual position
            new_visual_index: The new visual position
        """
        settings = QSettings("DigitalWorkshop", "ModelLibrary")
        header = self.library_widget.list_view.horizontalHeader()

        # Save the complete visual order
        visual_order = []
        for logical in range(header.count()):
            visual_order.append(header.visualIndex(logical))

        settings.setValue("column_order", visual_order)
        logger.debug("Saved column order: %s", visual_order)

    def _show_column_menu(self, position):
        """Show context menu for column visibility control."""
        header = self.library_widget.list_view.horizontalHeader()
        menu = QMenu()

        # Get column names
        column_names = []
        for col in range(self.library_widget.list_model.columnCount()):
            column_names.append(
                self.library_widget.list_model.headerData(col, Qt.Horizontal)
            )

        # Create actions for each column
        def make_toggle_handler(column_index):
            """Create a handler that captures the column index."""

            def handler(checked):
                self._toggle_column_visibility(column_index, checked)

            return handler

        for col, name in enumerate(column_names):
            action = QAction(name, menu)
            action.setCheckable(True)
            action.setChecked(not self.library_widget.list_view.isColumnHidden(col))
            # Don't allow hiding Thumbnail (col 0) or Name (col 1) columns
            if col in (0, 1):
                action.setEnabled(False)
            # Connect to handler that properly captures column index and checked state
            action.triggered.connect(make_toggle_handler(col))
            menu.addAction(action)

        # Show menu at cursor position
        menu.exec_(header.mapToGlobal(position))

    def _toggle_column_visibility(self, column: int, checked: bool) -> None:
        """
        Toggle column visibility and save to settings.

        Args:
            column: Column index
            checked: Whether column should be visible
        """
        visibility_label = "visible" if checked else "hidden"
        logger.debug(
            "Toggle column %s visibility: checked=%s (will be %s)",
            column,
            checked,
            visibility_label,
        )
        logger.info(
            "Toggle column %s visibility (will be %s)",
            column,
            visibility_label,
        )
        self.library_widget.list_view.setColumnHidden(column, not checked)
        settings = QSettings("DigitalWorkshop", "ModelLibrary")
        settings.setValue(f"column_{column}_visible", checked)
        settings.sync()  # Force write to disk
        # Verify it was saved
        saved_value = settings.value(f"column_{column}_visible")
        logger.debug(
            "Saved and verified column_%s_visible: saved=%s, read_back=%s",
            column,
            checked,
            saved_value,
        )
        logger.info("Saved and verified column_%s_visible", column)

    def apply_styling(self) -> None:
        """Apply CSS styling (no-op - qt-material handles this)."""
