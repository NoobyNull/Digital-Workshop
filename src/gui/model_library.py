"""
Model library interface for 3D-MM application.

Provides a model library widget with:
- File browser
- List/Grid views
- Drag-and-drop import
- Background loading worker
- Database integration
- Simple search and filters for tests
"""

import gc
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any

from PySide6.QtCore import (
    Qt, QThread, Signal, QSize, QRectF, QModelIndex, QSortFilterProxyModel, QPointF, QDir
)
from PySide6.QtGui import (
    QIcon, QPixmap, QPainter, QDragEnterEvent, QDropEvent,
    QStandardItemModel, QStandardItem, QAction, QKeySequence, QPen, QBrush, QColor
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTreeView, QListView,
    QTableView, QPushButton, QLabel, QLineEdit, QComboBox, QProgressBar,
    QGroupBox, QTabWidget, QFrame, QMenu, QMessageBox, QHeaderView,
    QFileSystemModel, QButtonGroup, QToolButton, QCheckBox
)

from src.core.logging_config import get_logger
from src.core.database_manager import get_database_manager
from src.core.performance_monitor import get_performance_monitor, monitor_operation
from src.core.model_cache import get_model_cache, CacheLevel
from src.utils.file_hash import calculate_file_hash
from src.parsers.stl_parser import STLParser
from src.parsers.obj_parser import OBJParser
from src.parsers.threemf_parser import ThreeMFParser
from src.parsers.step_parser import STEPParser
from src.parsers.format_detector import FormatDetector, ModelFormat
from src.gui.theme import SPACING_4, SPACING_8, SPACING_12, SPACING_16, SPACING_24
from src.gui.theme_core import get_theme_color
from src.gui.multi_root_file_system_model import MultiRootFileSystemModel


class FileSystemProxyModel(QSortFilterProxyModel):
    """
    Proxy model that filters out hidden folders and handles network paths.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.home_drive = str(Path.home().drive) if hasattr(Path.home(), 'drive') else ''

    def filterAcceptsRow(self, source_row, source_parent):
        """Override to filter out hidden folders and network paths."""
        # Get the source model index
        source_model = self.sourceModel()
        if not source_model:
            return True

        index = source_model.index(source_row, 0, source_parent)
        if not index.isValid():
            return True

        # Get file info
        file_info = source_model.fileInfo(index)

        # Skip hidden files and folders
        if file_info.isHidden():
            return False

        # Skip files/folders starting with '.'
        file_name = file_info.fileName()
        if file_name.startswith('.'):
            return False

        # Skip network paths (UNC paths starting with \\)
        file_path = file_info.absoluteFilePath()
        if file_path.startswith('\\\\'):
            return False

        # Skip R drives that are not in home directory
        if self.home_drive and file_path.startswith('R:') and not file_path.startswith(self.home_drive + '\\'):
            return False

        return True


class ViewMode(Enum):
    LIST = "list"
    GRID = "grid"


class ModelLoadWorker(QThread):
    model_loaded = Signal(dict)
    progress_updated = Signal(float, str)
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(self, file_paths: List[str]):
        super().__init__()
        self.file_paths = file_paths
        self._is_cancelled = False
        self.logger = get_logger(__name__)
        self.performance_monitor = get_performance_monitor()
        self.model_cache = get_model_cache()

    def cancel(self) -> None:
        self._is_cancelled = True

    def run(self) -> None:
        self.logger.info(f"Starting to load {len(self.file_paths)} models")
        for i, file_path in enumerate(self.file_paths):
            if self._is_cancelled:
                self.logger.info("Model loading cancelled")
                break

            try:
                progress = (i / max(1, len(self.file_paths))) * 100.0
                filename = Path(file_path).name
                self.progress_updated.emit(progress, f"Loading {filename}")

                operation_id = self.performance_monitor.start_operation(
                    "load_model_to_library",
                    {"file_path": file_path, "filename": filename}
                )

                cached_model = self.model_cache.get(file_path, CacheLevel.METADATA)
                if cached_model:
                    model = cached_model
                else:
                    fmt = FormatDetector().detect_format(Path(file_path))
                    if fmt == ModelFormat.STL:
                        parser = STLParser()
                    elif fmt == ModelFormat.OBJ:
                        parser = OBJParser()
                    elif fmt == ModelFormat.THREE_MF:
                        parser = ThreeMFParser()
                    elif fmt == ModelFormat.STEP:
                        parser = STEPParser()
                    else:
                        raise Exception(f"Unsupported model format: {fmt}")

                    model = parser.parse_metadata_only(file_path)
                    self.model_cache.put(file_path, CacheLevel.METADATA, model)

                model_info = {
                    "file_path": file_path,
                    "filename": filename,
                    "format": model.format_type.value,
                    "file_size": model.stats.file_size_bytes,
                    "file_hash": None,
                    "triangle_count": model.stats.triangle_count,
                    "vertex_count": model.stats.vertex_count,
                    "dimensions": model.stats.get_dimensions(),
                    "parsing_time": model.stats.parsing_time_seconds,
                    "min_bounds": (model.stats.min_bounds.x, model.stats.min_bounds.y, model.stats.min_bounds.z),
                    "max_bounds": (model.stats.max_bounds.x, model.stats.max_bounds.y, model.stats.max_bounds.z),
                }

                self.model_loaded.emit(model_info)
                self.performance_monitor.end_operation(operation_id, success=True)

                if i % 10 == 0:
                    gc.collect()

            except Exception as e:
                msg = f"Failed to load {file_path}: {e}"
                self.logger.error(msg)
                self.error_occurred.emit(msg)

        self.finished.emit()
        self.logger.info("Model loading completed")


class ThumbnailGenerator:
    def __init__(self, size: QSize = QSize(128, 128)):
        self.size = size
        self.logger = get_logger(__name__)

    def generate_thumbnail(self, model_info: Dict[str, Any]) -> QPixmap:
        try:
            pixmap = QPixmap(self.size)
            pixmap.fill(QColor(0, 0, 0, 0))  # Use QColor for transparent

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            dimensions = model_info.get("dimensions", (1.0, 1.0, 1.0))
            width, height, depth = dimensions
            max_dim = max(width, height, depth) or 1.0
            norm_w = (width / max_dim) * (self.size.width() * 0.8)
            norm_h = (height / max_dim) * (self.size.height() * 0.8)
            cx = self.size.width() / 2
            cy = self.size.height() / 2

            tri_count = model_info.get("triangle_count", 0)
            if tri_count < 1000:
                painter.setPen(QPen(get_theme_color('text_muted'), 1))
                rect = QRectF(cx - norm_w / 2, cy - norm_h / 2, norm_w, norm_h)
                painter.drawRect(rect)
                painter.drawLine(rect.topLeft(), rect.bottomRight())
                painter.drawLine(rect.topRight(), rect.bottomLeft())
            elif tri_count < 10000:
                painter.setPen(QPen(get_theme_color('edge_color'), 1))
                c = get_theme_color('model_surface'); c.setAlpha(180)
                painter.setBrush(QBrush(c))
                rect = QRectF(cx - norm_w / 2, cy - norm_h / 2, norm_w, norm_h)
                painter.drawRect(rect)
                c2 = get_theme_color('text_inverse'); c2.setAlpha(100)
                painter.setBrush(QBrush(c2))
                painter.drawRect(QRectF(cx - norm_w / 2, cy - norm_h / 2, norm_w / 3, norm_h / 3))
            else:
                painter.setPen(QPen(get_theme_color('edge_color'), 1))
                c3 = get_theme_color('primary'); c3.setAlpha(180)
                painter.setBrush(QBrush(c3))
                radius = min(norm_w, norm_h) / 2
                painter.drawEllipse(QPointF(cx, cy), radius, radius)
                painter.setPen(QPen(get_theme_color('primary_text'), 1))
                painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
                painter.drawEllipse(QPointF(cx, cy), radius * 0.7, radius * 0.7)
                painter.drawEllipse(QPointF(cx, cy), radius * 0.4, radius * 0.4)

            painter.setPen(QPen(get_theme_color('primary_text'), 1))
            c4 = get_theme_color('model_ambient'); c4.setAlpha(200)
            painter.setBrush(QBrush(c4))
            indicator_rect = QRectF(self.size.width() - 25, self.size.height() - 15, 20, 12)
            painter.drawRect(indicator_rect)
            font = painter.font()
            font.setPointSize(6)
            painter.setFont(font)
            fmt = (model_info.get("format") or "UNK")[:3].upper()
            painter.drawText(indicator_rect, Qt.AlignCenter, fmt)

            painter.end()
            return pixmap
        except Exception as e:
            self.logger.error(f"Failed to generate thumbnail: {e}")
            px = QPixmap(self.size)
            px.fill(Qt.lightGray)
            p = QPainter(px)
            p.setPen(QPen(Qt.red, 2))
            p.drawLine(10, 10, self.size.width() - 10, self.size.height() - 10)
            p.drawLine(self.size.width() - 10, 10, 10, self.size.height() - 10)
            p.end()
            return px


class ModelLibraryWidget(QWidget):
    model_selected = Signal(int)
    model_double_clicked = Signal(int)
    models_added = Signal(list)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.logger = get_logger(__name__)
        self.db_manager = get_database_manager()
        self.thumbnail_generator = ThumbnailGenerator()
        self.model_loader: Optional[ModelLoadWorker] = None
        self.current_models: List[Dict[str, Any]] = []
        self.view_mode = ViewMode.LIST

        self.performance_monitor = get_performance_monitor()
        self.model_cache = get_model_cache()

        self.loading_in_progress = False
        self._disposed = False

        self._init_ui()
        self._initialize_view_mode()
        self._setup_connections()
        self._load_models_from_database()

    def _init_ui(self) -> None:
        # Top-level layout for the combined widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(SPACING_8, SPACING_8, SPACING_8, SPACING_8)
        main_layout.setSpacing(SPACING_8)

        # Global controls that persist across internal tabs
        self._create_search_bar(main_layout)

        # Internal tabs: Library | Files (combined widget)
        self.internal_tabs = QTabWidget()
        main_layout.addWidget(self.internal_tabs)

        # --- Library tab: Model Library functionality without file browser ---
        library_container = QWidget()
        library_layout = QVBoxLayout(library_container)
        library_layout.setContentsMargins(0, 0, 0, 0)
        library_layout.setSpacing(SPACING_8)

        # Model views only (no file browser)
        self._create_model_view_area(library_layout)

        # Status bar for library operations
        self._create_status_bar(library_layout)

        self.internal_tabs.addTab(library_container, "Library")

        # --- Files tab: Dedicated file browser ---
        files_container = QWidget()
        files_layout = QVBoxLayout(files_container)
        files_layout.setContentsMargins(0, 0, 0, 0)
        files_layout.setSpacing(SPACING_8)

        # File browser in its own tab
        self._create_file_browser(files_layout)

        self.internal_tabs.addTab(files_container, "Files")

        # Validate root folder reachability after UI is set up
        self._validate_root_folders()

        # Set up context menu for file tree
        self._show_file_tree_context_menu = self._show_file_tree_context_menu

    def _initialize_view_mode(self) -> None:
        """Initialize default view mode."""
        self.view_mode = ViewMode.LIST

    def _create_search_bar(self, parent_layout: QVBoxLayout) -> None:
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(SPACING_8)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search models...")
        controls_layout.addWidget(QLabel("Search:"))
        controls_layout.addWidget(self.search_box)

        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        controls_layout.addWidget(QLabel("Category:"))
        controls_layout.addWidget(self.category_filter)

        self.format_filter = QComboBox()
        self.format_filter.addItem("All Formats")
        self.format_filter.addItems(["STL", "OBJ", "3MF", "STEP"])
        controls_layout.addWidget(QLabel("Format:"))
        controls_layout.addWidget(self.format_filter)

        parent_layout.addWidget(controls_frame)

    def _create_file_browser(self, parent_layout: QVBoxLayout) -> None:
        group = QGroupBox("File Browser")
        layout = QVBoxLayout(group)

        # Create multi-root file system model
        self.file_model = MultiRootFileSystemModel()
        self.file_proxy_model = FileSystemProxyModel()
        self.file_proxy_model.setSourceModel(self.file_model)

        # Connect to file model signals for status updates
        self.file_model.indexing_started.connect(self._on_indexing_started)
        self.file_model.indexing_completed.connect(self._on_indexing_completed)

        self.file_tree = QTreeView()
        self.file_tree.setModel(self.file_proxy_model)
        self.file_tree.setColumnHidden(1, True)  # Hide size column
        self.file_tree.setColumnHidden(2, True)  # Hide type column
        self.file_tree.setColumnHidden(3, True)  # Hide modified column

        layout.addWidget(self.file_tree)

        # Import buttons at the bottom of file browser
        import_frame = QFrame()
        import_layout = QHBoxLayout(import_frame)
        import_layout.setContentsMargins(0, SPACING_8, 0, 0)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setToolTip("Refresh directory index")
        self.refresh_button.clicked.connect(self._refresh_file_browser)
        import_layout.addWidget(self.refresh_button)

        import_layout.addStretch()

        self.import_selected_button = QPushButton("Import Selected")
        self.import_selected_button.setToolTip("Import selected file(s)")
        import_layout.addWidget(self.import_selected_button)

        self.import_folder_button = QPushButton("Import Folder")
        self.import_folder_button.setToolTip("Import the selected folder")
        import_layout.addWidget(self.import_folder_button)

        layout.addWidget(import_frame)

        parent_layout.addWidget(group)

    def _create_model_view_area(self, parent_layout: QVBoxLayout) -> None:
        group = QGroupBox("Models")
        layout = QVBoxLayout(group)

        self.view_tabs = QTabWidget()

        self.list_view = QTableView()
        self.list_model = QStandardItemModel()
        self.list_model.setHorizontalHeaderLabels(["Name", "Format", "Size", "Triangles", "Category", "Added Date"])

        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.list_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(-1)

        self.list_view.setModel(self.proxy_model)
        self.list_view.setSortingEnabled(True)
        self.list_view.setSelectionBehavior(QTableView.SelectRows)
        self.list_view.setAlternatingRowColors(True)
        header = self.list_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for col in range(1, 6):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        self.view_tabs.addTab(self.list_view, "List")

        self.grid_view = QListView()
        self.grid_view.setViewMode(QListView.IconMode)
        self.grid_view.setResizeMode(QListView.Adjust)
        self.grid_view.setSpacing(10)
        self.grid_view.setUniformItemSizes(True)
        self.grid_view.setModel(self.proxy_model)
        self.view_tabs.addTab(self.grid_view, "Grid")

        layout.addWidget(self.view_tabs)
        parent_layout.addWidget(group)

    def _create_status_bar(self, parent_layout: QVBoxLayout) -> None:
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(SPACING_8)

        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)

        self.model_count_label = QLabel("Models: 0")
        status_layout.addWidget(self.model_count_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)

        parent_layout.addWidget(status_frame)

    def _apply_styling(self) -> None:
        """Apply styling (no-op - qt-material handles all styling)."""
        pass

    def _setup_connections(self) -> None:
        # View mode connections are handled by the tab widget directly
        # Connect tab changes to update view mode
        self.view_tabs.currentChanged.connect(self._on_tab_changed)

        # File browser click handlers (Files tab)
        self.file_tree.clicked.connect(self._on_file_tree_clicked)

        # Import button handlers (Files tab)
        self.import_selected_button.clicked.connect(self._import_selected_files)
        self.import_folder_button.clicked.connect(self._import_selected_folder)

        # Model list/grid interactions
        self.list_view.clicked.connect(self._on_model_clicked)
        self.list_view.doubleClicked.connect(self._on_model_double_clicked)
        self.grid_view.clicked.connect(self._on_model_clicked)
        self.grid_view.doubleClicked.connect(self._on_model_double_clicked)

        # Filters / search (maintained across views)
        self.search_box.textChanged.connect(self._apply_filters)
        self.category_filter.currentIndexChanged.connect(self._apply_filters)
        self.format_filter.currentIndexChanged.connect(self._apply_filters)

        # Drag-and-drop
        self.setAcceptDrops(True)
        self.list_view.setAcceptDrops(True)
        self.grid_view.setAcceptDrops(True)

        # Context menus
        self.list_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_view.customContextMenuRequested.connect(self._show_context_menu)
        self.grid_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.grid_view.customContextMenuRequested.connect(self._show_context_menu)

        # File tree context menu
        self.file_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self._show_file_tree_context_menu)

    def _on_tab_changed(self, index: int) -> None:
        """Handle tab change to update view mode."""
        if index == 0:
            self.view_mode = ViewMode.LIST
        else:
            self.view_mode = ViewMode.GRID

    def _on_file_tree_clicked(self, index: QModelIndex) -> None:
        # Update the path display when a file is clicked
        try:
            # Map from proxy to source model
            source_index = self.file_proxy_model.mapToSource(index)
            path = self.file_model.get_file_path(source_index)
            if hasattr(self, "path_display") and path:
                self.path_display.setText(path)
        except Exception:
            # Fallback: do not raise in tests
            pass

    def _apply_filters(self) -> None:
        if self._disposed or not hasattr(self, "proxy_model"):
            return
        text = self.search_box.text() if hasattr(self, "search_box") and self.search_box else ""
        try:
            from PySide6.QtCore import QRegularExpression
            self.proxy_model.setFilterRegularExpression(QRegularExpression(text, QRegularExpression.CaseInsensitiveOption))
        except Exception:
            self.proxy_model.setFilterFixedString(text or "")

#这两个方法放在这里是因为要在数据库中载入模型到列表，然后选中的时候，可以当选到的model的mapper
    def _load_models_from_database(self) -> None:
        """Load models from the database into the view."""
        try:
            self.status_label.setText("Loading models...")
            self.current_models = self.db_manager.get_all_models()
            self._update_model_view()
            self.model_count_label.setText(f"Models: {len(self.current_models)}")
            self.status_label.setText("Ready")
        except Exception as e:
            self.logger.error(f"Failed to load models from database: {e}")
            self.status_label.setText("Error loading models")

    def _update_model_view(self) -> None:
        """Populate list/grid views from current_models."""
        self.list_model.clear()
        self.list_model.setHorizontalHeaderLabels(["Name", "Format", "Size", "Triangles", "Category", "Added Date"])
        for model in self.current_models:
            name_item = QStandardItem(model.get("title") or model.get("filename", "Unknown"))
            name_item.setData(model.get("id"), Qt.UserRole)

            # Set icon from thumbnail if available
            thumbnail_path = model.get("thumbnail_path")
            if thumbnail_path and Path(thumbnail_path).exists():
                try:
                    icon = QIcon(thumbnail_path)
                    name_item.setIcon(icon)
                except Exception as e:
                    self.logger.warning(f"Failed to load thumbnail icon: {e}")

            fmt = (model.get("format") or "Unknown").upper()
            format_item = QStandardItem(fmt)

            size_bytes = model.get("file_size", 0) or 0
            if size_bytes > 1024 * 1024:
                size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
            elif size_bytes > 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes} B"
            size_item = QStandardItem(size_str)

            triangles_item = QStandardItem(f"{model.get('triangle_count', 0):,}")
            category_item = QStandardItem(model.get("category", "Uncategorized"))
            date_item = QStandardItem(str(model.get("date_added", "Unknown")))

            self.list_model.appendRow([name_item, format_item, size_item, triangles_item, category_item, date_item])

        # Apply current filter text
        self._apply_filters()

    def get_selected_model_id(self) -> Optional[int]:
        view = self.list_view if self.view_mode == ViewMode.LIST else self.grid_view
        indexes = view.selectedIndexes()
        if not indexes:
            return None
        src_index = self.proxy_model.mapToSource(indexes[0])
        item = self.list_model.item(src_index.row(), 0)
        model_id = item.data(Qt.UserRole) if item else None
        return model_id

    def get_selected_models(self) -> List[int]:
        view = self.list_view if self.view_mode == ViewMode.LIST else self.grid_view
        model_ids: List[int] = []
        for idx in view.selectedIndexes():
            src = self.proxy_model.mapToSource(idx)
            item = self.list_model.item(src.row(), 0)
            if item:
                mid = item.data(Qt.UserRole)
                if mid and mid not in model_ids:
                    model_ids.append(mid)
        return model_ids

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    suffix = Path(url.toLocalFile()).suffix.lower()
                    if suffix in [".stl", ".obj", ".3mf", ".step", ".stp"]:
                        event.acceptProposedAction()
                        return

    def dropEvent(self, event: QDropEvent) -> None:
        if event.mimeData().hasUrls():
            files: List[str] = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    p = url.toLocalFile()
                    if Path(p).is_file() and Path(p).suffix.lower() in [".stl", ".obj", ".3mf", ".step", ".stp"]:
                        files.append(p)
            if files:
                self._load_models(files)

    @monitor_operation("load_models_to_library")
    def _load_models(self, file_paths: List[str]) -> None:
        if self.loading_in_progress or self._disposed:
            QMessageBox.information(self, "Loading", "Models are currently being loaded. Please wait.")
            return

        op_id = self.performance_monitor.start_operation("load_models_batch", {"file_count": len(file_paths)})

        self.loading_in_progress = True
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("Loading models...")

        self.model_loader = ModelLoadWorker(file_paths)
        self.model_loader.model_loaded.connect(self._on_model_loaded)
        self.model_loader.progress_updated.connect(self._on_load_progress)
        self.model_loader.error_occurred.connect(self._on_load_error)
        self.model_loader.finished.connect(self._on_load_finished)
        self.model_loader.start()
        self._load_operation_id = op_id

    def _on_model_loaded(self, model_info: Dict[str, Any]) -> None:
        if self._disposed or self.model_loader is None:
            return
        try:
            # Add to database without hash (will be hashed in background)
            model_id = self.db_manager.add_model(
                filename=model_info["filename"],
                format=model_info["format"],
                file_path=model_info["file_path"],
                file_size=model_info["file_size"],
                file_hash=None
            )
            self.db_manager.add_model_metadata(model_id=model_id, title=model_info["filename"], description="")
            thumb = self.thumbnail_generator.generate_thumbnail(model_info)
            model_info["id"] = model_id
            model_info["thumbnail"] = thumb
            self.current_models.append(model_info)
        except Exception as e:
            self.logger.error(f"Failed to save model to database: {e}")

    def _on_load_progress(self, progress_percent: float, message: str) -> None:
        if self._disposed or self.model_loader is None:
            return
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(int(progress_percent))

        # Calculate current item number from progress
        total_files = len(self.model_loader.file_paths)
        current_item = int((progress_percent / 100.0) * total_files) + 1
        current_item = min(current_item, total_files)  # Don't exceed total

        # Enhanced status message with progress details
        if total_files > 1:
            status_text = f"{message} ({current_item} of {total_files} = {int(progress_percent)}%)"
        else:
            status_text = f"{message} ({int(progress_percent)}%)"

        self.status_label.setText(status_text)

    def _on_load_error(self, error_message: str) -> None:
        if self._disposed or self.model_loader is None:
            return
        self.logger.error(error_message)
        QMessageBox.warning(self, "Loading Error", error_message)

    def _on_load_finished(self) -> None:
        if self._disposed:
            if self.model_loader:
                try:
                    try: self.model_loader.model_loaded.disconnect(self._on_model_loaded)
                    except Exception: pass
                    try: self.model_loader.progress_updated.disconnect(self._on_load_progress)
                    except Exception: pass
                    try: self.model_loader.error_occurred.disconnect(self._on_load_error)
                    except Exception: pass
                    try: self.model_loader.finished.disconnect(self._on_load_finished)
                    except Exception: pass

                    if self.model_loader.isRunning():
                        try:
                            self.model_loader.cancel()
                        except Exception:
                            pass
                    self.model_loader.wait(3000)
                finally:
                    try:
                        self.model_loader.deleteLater()
                    except Exception:
                        pass
                self.model_loader = None

            try:
                self.model_cache.optimize_cache()

                if self.model_loader:
                    try:
                        self.model_loader.deleteLater()
                    except Exception:
                        pass
            except Exception:
                pass
            gc.collect()
            return

        self.loading_in_progress = False
        self.progress_bar.setVisible(False)
        self.status_label.setText("Ready")

        # Reload models from database to ensure all metadata is loaded
        self._load_models_from_database()

        added_ids = [m["id"] for m in self.current_models if "id" in m]
        if added_ids:
            self.models_added.emit(added_ids)

        if hasattr(self, "_load_operation_id"):
            self.performance_monitor.end_operation(self._load_operation_id, success=True)
            delattr(self, "_load_operation_id")

        self.model_cache.optimize_cache()

        if self.model_loader:
            try:
                self.model_loader.deleteLater()
            except Exception:
                pass
            self.model_loader = None

        gc.collect()

    def _on_model_clicked(self, index: QModelIndex) -> None:
        """Emit model_selected when an item is clicked."""
        try:
            src_index = self.proxy_model.mapToSource(index)
            item = self.list_model.item(src_index.row(), 0)
            if item:
                mid = item.data(Qt.UserRole)
                if mid is not None:
                    self.model_selected.emit(int(mid))
        except Exception:
            pass

    def _on_model_double_clicked(self, index: QModelIndex) -> None:
        """Emit model_double_clicked when an item is double-clicked."""
        try:
            src_index = self.proxy_model.mapToSource(index)
            item = self.list_model.item(src_index.row(), 0)
            if item:
                mid = item.data(Qt.UserRole)
                if mid is not None:
                    self.model_double_clicked.emit(int(mid))
        except Exception:
            pass

    def _show_context_menu(self, position) -> None:
        """Show a minimal context menu for the model list/grid."""
        try:
            view = self.sender()
            index = view.indexAt(position)
            if not index.isValid():
                return
            src_index = self.proxy_model.mapToSource(index)
            item = self.list_model.item(src_index.row(), 0)
            if not item:
                return
            model_id = item.data(Qt.UserRole)
            menu = QMenu(self)
            open_action = QAction("Open", self)
            open_action.triggered.connect(lambda: self.model_double_clicked.emit(int(model_id)))
            menu.addAction(open_action)

            # Add separator and remove action
            menu.addSeparator()
            remove_action = QAction("Remove", self)
            remove_action.triggered.connect(lambda: self._remove_model(int(model_id)))
            menu.addAction(remove_action)

            menu.exec_(view.mapToGlobal(position))
        except Exception:
            # Fail silently in tests if something goes wrong with context menu
            pass

    def _show_file_tree_context_menu(self, position) -> None:
        """Show context menu for the file tree with import and open options."""
        try:
            index = self.file_tree.indexAt(position)
            if not index.isValid():
                return

            # Map from proxy to source model
            source_index = self.file_proxy_model.mapToSource(index)
            path = self.file_model.get_file_path(source_index)
            if not path:
                return

            menu = QMenu(self)

            # Import action (for files and folders)
            import_action = QAction("Import", self)
            import_action.triggered.connect(lambda: self._import_from_context_menu(path))
            menu.addAction(import_action)

            # Open in native app action (for files only)
            if Path(path).is_file():
                menu.addSeparator()
                open_action = QAction("Open in Native App", self)
                open_action.triggered.connect(lambda: self._open_in_native_app(path))
                menu.addAction(open_action)

            menu.exec_(self.file_tree.mapToGlobal(position))

        except Exception as e:
            self.logger.error(f"Error showing file tree context menu: {e}")

    def _import_from_context_menu(self, path: str) -> None:
        """Import files/folders from context menu selection."""
        try:
            p = Path(path)
            if p.is_file():
                # Import single file
                if p.suffix.lower() in [".stl", ".obj", ".3mf", ".step", ".stp"]:
                    self._load_models([path])
                else:
                    QMessageBox.warning(self, "Import", f"Unsupported file format: {p.suffix}")
            elif p.is_dir():
                # Import folder recursively
                files_to_import = []
                supported_extensions = [".stl", ".obj", ".3mf", ".step", ".stp"]
                for ext in supported_extensions:
                    files_to_import.extend(p.rglob(f"*{ext}"))

                if files_to_import:
                    files_to_import = [str(f) for f in files_to_import]
                    self._load_models(files_to_import)
                else:
                    QMessageBox.information(self, "Import", f"No supported model files found in {p.name}")

        except Exception as e:
            self.logger.error(f"Error importing from context menu: {e}")
            QMessageBox.critical(self, "Import Error", f"Failed to import: {e}")

    def _open_in_native_app(self, file_path: str) -> None:
        """Open file in its native application."""
        try:
            from PySide6.QtCore import QUrl
            from PySide6.QtGui import QDesktopServices

            url = QUrl.fromLocalFile(file_path)
            if not QDesktopServices.openUrl(url):
                QMessageBox.warning(self, "Open File", f"Could not open file: {file_path}")

        except Exception as e:
            self.logger.error(f"Error opening file in native app: {e}")
            QMessageBox.critical(self, "Open File", f"Failed to open file: {e}")

    def _remove_model(self, model_id: int) -> None:
        """Remove a model from the library after confirmation."""
        try:
            # Get model details for confirmation dialog
            model_info = self.db_manager.get_model(model_id)
            if not model_info:
                self.logger.warning(f"Model with ID {model_id} not found")
                return

            model_name = model_info.get("title") or model_info.get("filename", "Unknown")

            # Show confirmation dialog
            reply = QMessageBox.question(
                self,
                "Confirm Removal",
                f"Are you sure you want to remove '{model_name}' from the library?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # Remove from database
                success = self.db_manager.delete_model(model_id)

                if success:
                    # Remove from cache if present
                    if model_info.get("file_path"):
                        try:
                            self.model_cache.remove(model_info["file_path"])
                        except Exception:
                            # Continue even if cache removal fails
                            pass

                    # Update UI
                    self.status_label.setText(f"Removed '{model_name}' from library")
                    self._load_models_from_database()

                    self.logger.info(f"Successfully removed model '{model_name}' (ID: {model_id})")
                else:
                    self.status_label.setText(f"Failed to remove '{model_name}'")
                    self.logger.error(f"Failed to remove model with ID {model_id}")

        except Exception as e:
            self.logger.error(f"Error removing model: {e}")
            QMessageBox.warning(self, "Error", f"Failed to remove model: {str(e)}")

    def _refresh_models(self) -> None:
        self._load_models_from_database()

    def _refresh_file_browser(self) -> None:
        """Refresh the file browser by re-indexing directories."""
        try:
            self.file_model.refresh_index()
            self.status_label.setText("Indexing directories...")
            self.logger.info("Manual file browser refresh initiated")
        except Exception as e:
            self.logger.error(f"Error refreshing file browser: {e}")
            self.status_label.setText("Error refreshing directories")

    def _on_indexing_started(self) -> None:
        """Handle indexing started signal."""
        self.status_label.setText("Indexing directories...")

    def _on_indexing_completed(self) -> None:
        """Handle indexing completed signal."""
        self.status_label.setText("Ready")

    def _validate_root_folders(self) -> None:
        """Validate that configured root folders are accessible."""
        try:
            enabled_folders = self.root_folder_manager.get_enabled_folders()
            inaccessible_folders = []

            for folder in enabled_folders:
                if not Path(folder.path).exists():
                    inaccessible_folders.append(f"{folder.display_name} ({folder.path})")
                    self.logger.warning(f"Root folder not accessible: {folder.display_name} ({folder.path})")

            if inaccessible_folders:
                folder_list = "\n".join(f"• {folder}" for folder in inaccessible_folders)
                QMessageBox.warning(
                    self,
                    "Inaccessible Root Folders",
                    f"The following configured root folders are not accessible:\n\n{folder_list}\n\n"
                    "Please check that the folders exist and you have permission to access them.\n"
                    "You can update root folder settings in Preferences > Files."
                )
            else:
                self.logger.debug(f"All {len(enabled_folders)} root folders are accessible")

        except Exception as e:
            self.logger.error(f"Error validating root folders: {e}")
            # Don't show error dialog for validation failures to avoid startup blocking

    def _import_models(self) -> None:
        # Tests trigger import via _load_models or DnD, so this can be a stub
        self.status_label.setText("Use drag-and-drop to import models.")

    def _import_selected_files(self) -> None:
        """Import selected files from the file tree."""
        try:
            selected_indexes = self.file_tree.selectedIndexes()
            if not selected_indexes:
                QMessageBox.information(self, "Import", "Please select one or more files to import.")
                return

            files_to_import = []
            for index in selected_indexes:
                if index.column() == 0:  # Only process the first column to avoid duplicates
                    # Map from proxy to source model
                    source_index = self.file_proxy_model.mapToSource(index)
                    path = self.file_model.get_file_path(source_index)
                    if path and Path(path).is_file():
                        suffix = Path(path).suffix.lower()
                        if suffix in [".stl", ".obj", ".3mf", ".step", ".stp"]:
                            files_to_import.append(path)

            if not files_to_import:
                QMessageBox.warning(self, "Import", "No supported model files selected.\nSupported formats: STL, OBJ, 3MF, STEP")
                return

            self._load_models(files_to_import)

        except Exception as e:
            self.logger.error(f"Error importing selected files: {e}")
            QMessageBox.critical(self, "Import Error", f"Failed to import files: {e}")

    def _import_selected_folder(self) -> None:
        """Import selected folder from the file tree with recursive option."""
        try:
            selected_indexes = self.file_tree.selectedIndexes()
            if not selected_indexes:
                QMessageBox.information(self, "Import", "Please select a folder to import.")
                return

            # Get the selected folder path
            selected_index = selected_indexes[0]  # Take the first selection
            if selected_index.column() != 0:  # Make sure we're looking at the name column
                selected_index = selected_indexes[0].sibling(selected_index.row(), 0)

            # Map from proxy to source model
            source_index = self.file_proxy_model.mapToSource(selected_index)
            path = self.file_model.filePath(source_index)
            folder_path = Path(path)

            if not folder_path.is_dir():
                QMessageBox.warning(self, "Import", "Please select a folder, not a file.")
                return

            # Ask about recursive import
            reply = QMessageBox.question(
                self,
                "Recursive Import",
                "Do you want to import files recursively from subfolders?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            # Find all model files in the folder
            files_to_import = []
            supported_extensions = [".stl", ".obj", ".3mf", ".step", ".stp"]

            if reply == QMessageBox.Yes:
                # Recursive search
                for ext in supported_extensions:
                    files_to_import.extend(folder_path.rglob(f"*{ext}"))
            else:
                # Non-recursive search (only immediate folder)
                for ext in supported_extensions:
                    files_to_import.extend(folder_path.glob(f"*{ext}"))

            # Convert Path objects to strings
            files_to_import = [str(f) for f in files_to_import]

            if not files_to_import:
                QMessageBox.information(self, "Import", f"No supported model files found in the selected folder.\nSupported formats: {', '.join(supported_extensions)}")
                return

            self._load_models(files_to_import)

        except Exception as e:
            self.logger.error(f"Error importing selected folder: {e}")
            QMessageBox.critical(self, "Import Error", f"Failed to import folder: {e}")

    def cleanup(self) -> None:
        self._disposed = True
        if self.model_loader:
            try:
                try: self.model_loader.model_loaded.disconnect(self._on_model_loaded)
                except Exception: pass
                try: self.model_loader.progress_updated.disconnect(self._on_load_progress)
                except Exception: pass
                try: self.model_loader.error_occurred.disconnect(self._on_load_error)
                except Exception: pass
                try: self.model_loader.finished.disconnect(self._on_load_finished)
                except Exception: pass

                if self.model_loader.isRunning():
                    try:
                        self.model_loader.cancel()
                    except Exception:
                        pass
                self.model_loader.wait(3000)
            finally:
                try:
                    self.model_loader.deleteLater()
                except Exception:
                    pass
            self.model_loader = None

        try:
            self.model_cache.optimize_cache()
        except Exception:
            pass
        gc.collect()

    def closeEvent(self, event) -> None:
        self.cleanup()
        super().closeEvent(event)
