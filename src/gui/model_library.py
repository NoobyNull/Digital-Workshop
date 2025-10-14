"""
Model library interface for 3D-MM application.

This module provides a comprehensive model library interface with file browser,
model list/grid views, drag-and-drop support, thumbnail generation, and database
integration for managing 3D model collections.
"""

import gc
import os
import threading
import time
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any

from PySide6.QtCore import (
    Qt, QThread, Signal, QTimer, QFileInfo, QMimeData, QSize, QRectF,
    QObject, QModelIndex, QAbstractListModel, QSortFilterProxyModel
)
from PySide6.QtGui import (
    QIcon, QPixmap, QPainter, QDragEnterEvent, QDropEvent, QMouseEvent,
    QStandardItemModel, QStandardItem, QAction, QKeySequence
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTreeView, QListView,
    QTableView, QPushButton, QLabel, QLineEdit, QComboBox, QProgressBar,
    QGroupBox, QTabWidget, QFrame, QScrollArea, QMenu, QMessageBox,
    QFileDialog, QCheckBox, QSpinBox, QSlider, QToolButton, QHeaderView
)

from core.logging_config import get_logger, log_function_call
from core.database_manager import get_database_manager
from core.performance_monitor import get_performance_monitor, monitor_operation
from core.model_cache import get_model_cache, CacheLevel
from parsers import (
    STLParser, OBJParser, ThreeMFParser, STEPParser,
    FormatDetector, ProgressCallback, ModelFormat
)
from core.data_structures import LoadingState


class ViewMode(Enum):
    """View modes for the model library."""
    LIST = "list"
    GRID = "grid"


class ModelLoadWorker(QThread):
    """
    Worker thread for loading models in the background with performance optimization.
    
    This prevents UI blocking during model parsing and thumbnail generation.
    Uses lazy loading and caching for improved performance.
    """
    
    # Signals
    model_loaded = Signal(dict)  # Emitted when a model is loaded
    progress_updated = Signal(float, str)  # Emitted with progress updates
    error_occurred = Signal(str)  # Emitted when an error occurs
    finished = Signal()  # Emitted when loading is complete
    
    def __init__(self, file_paths: List[str]):
        """
        Initialize the model loader worker.
        
        Args:
            file_paths: List of file paths to load
        """
        super().__init__()
        self.file_paths = file_paths
        self._is_cancelled = False
        self.logger = get_logger(__name__)
        self.performance_monitor = get_performance_monitor()
        self.model_cache = get_model_cache()
    
    def run(self) -> None:
        """Load models in background thread."""
        self.logger.info(f"Starting to load {len(self.file_paths)} models")
        
        for i, file_path in enumerate(self.file_paths):
            if self._is_cancelled:
                self.logger.info("Model loading cancelled")
                break
            
            try:
                # Update progress
                progress = (i / len(self.file_paths)) * 100
                filename = Path(file_path).name
                self.progress_updated.emit(progress, f"Loading {filename}")
                
                # Start performance monitoring
                operation_id = self.performance_monitor.start_operation(
                    "load_model_to_library",
                    {"file_path": file_path, "filename": filename}
                )
                
                # Check cache first
                cached_model = self.model_cache.get(file_path, CacheLevel.METADATA)
                if cached_model:
                    self.logger.debug(f"Using cached model metadata: {file_path}")
                    model = cached_model
                else:
                    # Detect format and get appropriate parser
                    format_detector = FormatDetector()
                    format_type = format_detector.detect_format(Path(file_path))
                    
                    if format_type == ModelFormat.STL:
                        parser = STLParser()
                    elif format_type == ModelFormat.OBJ:
                        parser = OBJParser()
                    elif format_type == ModelFormat.THREE_MF:
                        parser = ThreeMFParser()
                    elif format_type == ModelFormat.STEP:
                        parser = STEPParser()
                    else:
                        raise Exception(f"Unsupported model format: {format_type}")
                    
                    # Parse metadata only for library
                    model = parser.parse_metadata_only(file_path)
                    
                    # Cache metadata
                    self.model_cache.put(file_path, CacheLevel.METADATA, model)
                
                # Create model info dictionary
                model_info = {
                    'file_path': file_path,
                    'filename': filename,
                    'format': model.format_type.value,
                    'file_size': model.stats.file_size_bytes,
                    'triangle_count': model.stats.triangle_count,
                    'vertex_count': model.stats.vertex_count,
                    'dimensions': model.stats.get_dimensions(),
                    'parsing_time': model.stats.parsing_time_seconds,
                    'min_bounds': (model.stats.min_bounds.x, model.stats.min_bounds.y, model.stats.min_bounds.z),
                    'max_bounds': (model.stats.max_bounds.x, model.stats.max_bounds.y, model.stats.max_bounds.z),
                    'loading_state': model.loading_state.value if hasattr(model, 'loading_state') else 'full'
                }
                
                self.model_loaded.emit(model_info)
                
                # End performance monitoring
                self.performance_monitor.end_operation(operation_id, success=True)
                
                # Periodic garbage collection
                if i % 10 == 0:
                    gc.collect()
                    
            except Exception as e:
                error_msg = f"Failed to load {file_path}: {str(e)}"
                self.logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                
                # End performance monitoring with error
                if 'operation_id' in locals():
                    self.performance_monitor.end_operation(operation_id, success=False, error_message=str(e))
        
        self.finished.emit()
        self.logger.info("Model loading completed")
    
    def cancel(self) -> None:
        """Cancel the loading process."""
        self._is_cancelled = True


class ThumbnailGenerator:
    """
    Utility class for generating model thumbnails.
    
    Creates simple geometry-based previews for 3D models.
    """
    
    def __init__(self, size: QSize = QSize(128, 128)):
        """
        Initialize the thumbnail generator.
        
        Args:
            size: Thumbnail size in pixels
        """
        self.size = size
        self.logger = get_logger(__name__)
    
    def generate_thumbnail(self, model_info: Dict[str, Any]) -> QPixmap:
        """
        Generate a thumbnail for a model.
        
        Args:
            model_info: Model information dictionary
            
        Returns:
            QPixmap thumbnail image
        """
        try:
            # Create a blank pixmap
            pixmap = QPixmap(self.size)
            pixmap.fill(Qt.transparent)  # Transparent background
            
            # Create painter
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Draw a simple representation based on model dimensions
            dimensions = model_info.get('dimensions', (1.0, 1.0, 1.0))
            width, height, depth = dimensions
            
            # Normalize dimensions to fit thumbnail
            max_dim = max(width, height, depth)
            if max_dim > 0:
                norm_width = (width / max_dim) * (self.size.width() * 0.8)
                norm_height = (height / max_dim) * (self.size.height() * 0.8)
            else:
                norm_width = self.size.width() * 0.8
                norm_height = self.size.height() * 0.8
            
            # Center position
            center_x = self.size.width() / 2
            center_y = self.size.height() / 2
            
            # Draw based on model complexity (triangle count)
            triangle_count = model_info.get('triangle_count', 0)
            
            if triangle_count < 1000:
                # Simple models: draw as wireframe box
                self._draw_wireframe_box(painter, center_x, center_y, norm_width, norm_height)
            elif triangle_count < 10000:
                # Medium models: draw as solid box
                self._draw_solid_box(painter, center_x, center_y, norm_width, norm_height)
            else:
                # Complex models: draw as sphere with detail indicator
                self._draw_complex_model(painter, center_x, center_y, norm_width, norm_height)
            
            # Draw format indicator
            format_type = model_info.get('format', 'unknown')
            self._draw_format_indicator(painter, format_type)
            
            painter.end()
            
            return pixmap
            
        except Exception as e:
            self.logger.error(f"Failed to generate thumbnail: {str(e)}")
            # Return error thumbnail
            return self._create_error_thumbnail()
    
    def _draw_wireframe_box(self, painter: QPainter, cx: float, cy: float, 
                           width: float, height: float) -> None:
        """Draw a wireframe box representation."""
        painter.setPen(QPen(Qt.darkGray, 1))
        
        # Draw rectangle outline
        rect = QRectF(cx - width/2, cy - height/2, width, height)
        painter.drawRect(rect)
        
        # Draw diagonal lines to show 3D effect
        painter.drawLine(rect.topLeft(), rect.bottomRight())
        painter.drawLine(rect.topRight(), rect.bottomLeft())
    
    def _draw_solid_box(self, painter: QPainter, cx: float, cy: float, 
                       width: float, height: float) -> None:
        """Draw a solid box representation."""
        painter.setPen(QPen(Qt.black, 1))
        painter.setBrush(QBrush(QColor(100, 150, 200, 180)))
        
        # Draw rectangle
        rect = QRectF(cx - width/2, cy - height/2, width, height)
        painter.drawRect(rect)
        
        # Add highlight to show 3D effect
        painter.setBrush(QBrush(QColor(255, 255, 255, 100)))
        highlight_rect = QRectF(cx - width/2, cy - height/2, width/3, height/3)
        painter.drawRect(highlight_rect)
    
    def _draw_complex_model(self, painter: QPainter, cx: float, cy: float, 
                           width: float, height: float) -> None:
        """Draw a complex model representation."""
        # Draw as circle with detail indicator
        painter.setPen(QPen(Qt.black, 1))
        painter.setBrush(QBrush(QColor(200, 100, 100, 180)))
        
        radius = min(width, height) / 2
        painter.drawEllipse(QPointF(cx, cy), radius, radius)
        
        # Add detail indicator (concentric circles)
        painter.setPen(QPen(Qt.white, 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), radius * 0.7, radius * 0.7)
        painter.drawEllipse(QPointF(cx, cy), radius * 0.4, radius * 0.4)
    
    def _draw_format_indicator(self, painter: QPainter, format_type: str) -> None:
        """Draw a format indicator in the corner."""
        painter.setPen(QPen(Qt.white, 1))
        painter.setBrush(QBrush(QColor(50, 50, 50, 200)))
        
        # Draw small rectangle in bottom right
        indicator_rect = QRectF(
            self.size.width() - 25, 
            self.size.height() - 15, 
            20, 12
        )
        painter.drawRect(indicator_rect)
        
        # Draw format text
        painter.setPen(QPen(Qt.white, 1))
        font = painter.font()
        font.setPointSize(6)
        painter.setFont(font)
        painter.drawText(indicator_rect, Qt.AlignCenter, format_type.upper()[:3])
    
    def _create_error_thumbnail(self) -> QPixmap:
        """Create an error thumbnail."""
        pixmap = QPixmap(self.size)
        pixmap.fill(Qt.lightGray)
        
        painter = QPainter(pixmap)
        painter.setPen(QPen(Qt.red, 2))
        painter.drawLine(10, 10, self.size.width() - 10, self.size.height() - 10)
        painter.drawLine(self.size.width() - 10, 10, 10, self.size.height() - 10)
        painter.end()
        
        return pixmap


class ModelLibraryWidget(QWidget):
    """
    Main model library widget with file browser, model views, and database integration.
    
    Features:
    - File browser with tree view for folder navigation
    - Model list and grid views with thumbnails
    - Drag-and-drop support for adding models
    - Search and filter functionality
    - Integration with database manager
    - Progress feedback for long operations
    - Memory-efficient handling of large collections
    """
    
    # Signals
    model_selected = Signal(int)  # Emitted when a model is selected (model_id)
    model_double_clicked = Signal(int)  # Emitted when a model is double-clicked
    models_added = Signal(list)  # Emitted when models are added (list of model_ids)
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the model library widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Initialize logger
        self.logger = get_logger(__name__)
        self.logger.info("Initializing model library widget")
        
        # Initialize components
        self.db_manager = get_database_manager()
        self.thumbnail_generator = ThumbnailGenerator()
        self.model_loader = None
        self.current_models = []
        self.view_mode = ViewMode.LIST
        
        # Performance optimization components
        self.performance_monitor = get_performance_monitor()
        self.model_cache = get_model_cache()
        
        # UI state
        self.loading_in_progress = False
        self.current_filter = ""
        self.current_category_filter = ""
        
        # Initialize UI
        self._init_ui()
        self._setup_connections()
        self._load_models_from_database()
        
        self.logger.info("Model library widget initialized successfully")
    
    def _init_ui(self) -> None:
        """Initialize the user interface layout."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Create toolbar
        self._create_toolbar(main_layout)
        
        # Create search/filter bar
        self._create_search_bar(main_layout)
        
        # Create content area with splitter
        content_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(content_splitter)
        
        # Create file browser (left side)
        self._create_file_browser(content_splitter)
        
        # Create model view area (right side)
        self._create_model_view_area(content_splitter)
        
        # Set splitter sizes
        content_splitter.setSizes([300, 700])
        
        # Create status bar
        self._create_status_bar(main_layout)
        
        # Apply styling
        self._apply_styling()
    
    def _create_toolbar(self, parent_layout: QVBoxLayout) -> None:
        """Create the toolbar with view controls and actions."""
        toolbar_frame = QFrame()
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # View mode buttons
        self.list_view_button = QToolButton()
        self.list_view_button.setText("List View")
        self.list_view_button.setCheckable(True)
        self.list_view_button.setChecked(True)
        self.list_view_button.setToolTip("Show models in list view")
        
        self.grid_view_button = QToolButton()
        self.grid_view_button.setText("Grid View")
        self.grid_view_button.setCheckable(True)
        self.grid_view_button.setToolTip("Show models in grid view")
        
        # Add view mode buttons to button group
        view_mode_group = QButtonGroup(self)
        view_mode_group.addButton(self.list_view_button, 0)
        view_mode_group.addButton(self.grid_view_button, 1)
        
        toolbar_layout.addWidget(QLabel("View:"))
        toolbar_layout.addWidget(self.list_view_button)
        toolbar_layout.addWidget(self.grid_view_button)
        toolbar_layout.addWidget(QFrame())  # Spacer
        
        # Import button
        self.import_button = QPushButton("Import Models...")
        self.import_button.setToolTip("Import models from files or folders")
        toolbar_layout.addWidget(self.import_button)
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setToolTip("Refresh model library")
        toolbar_layout.addWidget(self.refresh_button)
        
        parent_layout.addWidget(toolbar_frame)
    
    def _create_search_bar(self, parent_layout: QVBoxLayout) -> None:
        """Create the search and filter bar."""
        # Import search widget
        from gui.search_widget import SearchWidget
        
        # Create search widget
        self.search_widget = SearchWidget()
        self.search_widget.model_selected.connect(self.model_selected)
        self.search_widget.search_requested.connect(self._on_search_requested)
        
        parent_layout.addWidget(self.search_widget)
    
    def _create_file_browser(self, parent_splitter: QSplitter) -> None:
        """Create the file browser widget."""
        # File browser group
        file_browser_group = QGroupBox("File Browser")
        file_browser_layout = QVBoxLayout(file_browser_group)
        
        # Path display
        path_frame = QFrame()
        path_layout = QHBoxLayout(path_frame)
        path_layout.setContentsMargins(0, 0, 0, 0)
        
        path_layout.addWidget(QLabel("Path:"))
        self.path_display = QLabel()
        self.path_display.setText("C:\\")
        path_layout.addWidget(self.path_display)
        
        file_browser_layout.addWidget(path_frame)
        
        # File tree view
        self.file_tree = QTreeView()
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(QDir.rootPath())
        self.file_tree.setModel(self.file_model)
        
        # Hide unnecessary columns
        self.file_tree.setColumnHidden(1, True)  # Size
        self.file_tree.setColumnHidden(2, True)  # Type
        self.file_tree.setColumnHidden(3, True)  # Date modified
        
        # Set initial path
        initial_path = QDir.homePath()
        index = self.file_model.index(initial_path)
        self.file_tree.setRootIndex(index)
        self.path_display.setText(initial_path)
        
        file_browser_layout.addWidget(self.file_tree)
        
        # Add to splitter
        parent_splitter.addWidget(file_browser_group)
    
    def _create_model_view_area(self, parent_splitter: QSplitter) -> None:
        """Create the model view area with list and grid views."""
        # Model view group
        model_view_group = QGroupBox("Models")
        model_view_layout = QVBoxLayout(model_view_group)
        
        # Create tab widget for different views
        self.view_tabs = QTabWidget()
        
        # List view
        self.list_view = QTableView()
        self.list_model = QStandardItemModel()
        self.list_model.setHorizontalHeaderLabels([
            "Name", "Format", "Size", "Triangles", "Category", "Added Date"
        ])
        
        # Create proxy model for sorting and filtering
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.list_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(-1)  # Search all columns
        
        self.list_view.setModel(self.proxy_model)
        self.list_view.setSortingEnabled(True)
        self.list_view.setSelectionBehavior(QTableView.SelectRows)
        self.list_view.setAlternatingRowColors(True)
        
        # Adjust column widths
        header = self.list_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Name column stretches
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        self.view_tabs.addTab(self.list_view, "List")
        
        # Grid view
        self.grid_view = QListView()
        self.grid_view.setViewMode(QListView.IconMode)
        self.grid_view.setResizeMode(QListView.Adjust)
        self.grid_view.setSpacing(10)
        self.grid_view.setUniformItemSizes(True)
        self.grid_view.setModel(self.proxy_model)
        
        self.view_tabs.addTab(self.grid_view, "Grid")
        
        model_view_layout.addWidget(self.view_tabs)
        
        # Add to splitter
        parent_splitter.addWidget(model_view_group)
    
    def _create_status_bar(self, parent_layout: QVBoxLayout) -> None:
        """Create the status bar with progress indicator."""
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        # Status label
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)
        
        # Model count
        self.model_count_label = QLabel("Models: 0")
        status_layout.addWidget(self.model_count_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        parent_layout.addWidget(status_frame)
    
    def _apply_styling(self) -> None:
        """Apply styling to the widget with Windows standard colors."""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #d0d0d0;
                border-radius: 4px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: #ffffff;
                color: #000000;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #000000;
            }
            QTreeView {
                alternate-background-color: #f5f5f5;
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                color: #000000;
                selection-background-color: #0078d4;
                selection-color: #ffffff;
            }
            QTreeView::item {
                padding: 3px;
            }
            QTreeView::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QTableView {
                alternate-background-color: #f5f5f5;
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                gridline-color: #e0e0e0;
                color: #000000;
                selection-background-color: #0078d4;
                selection-color: #ffffff;
            }
            QTableView::item {
                padding: 3px;
            }
            QTableView::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QListView {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                color: #000000;
                selection-background-color: #0078d4;
                selection-color: #ffffff;
            }
            QListView::item {
                padding: 5px;
            }
            QListView::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background: #f5f5f5;
                padding: 8px;
                margin-right: 2px;
                border: 1px solid #d0d0d0;
                border-bottom: none;
                color: #000000;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border-bottom: 2px solid #0078d4;
                color: #000000;
            }
            QTabBar::tab:hover {
                background: #e1e1e1;
            }
            QPushButton, QToolButton {
                background-color: #f5f5f5;
                color: #000000;
                border: 1px solid #d0d0d0;
                padding: 6px 12px;
                border-radius: 2px;
            }
            QPushButton:hover, QToolButton:hover {
                background-color: #e1e1e1;
                border: 1px solid #0078d4;
            }
            QPushButton:pressed, QToolButton:pressed {
                background-color: #d0d0d0;
            }
            QToolButton:checked {
                background-color: #0078d4;
                color: #ffffff;
                border: 1px solid #0078d4;
            }
            QLabel {
                color: #000000;
                background-color: transparent;
            }
            QLineEdit {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #d0d0d0;
                padding: 4px;
                border-radius: 2px;
            }
            QLineEdit:focus {
                border: 2px solid #0078d4;
            }
        """)
    
    def _setup_connections(self) -> None:
        """Set up signal connections."""
        # View mode buttons
        self.list_view_button.clicked.connect(lambda: self._set_view_mode(ViewMode.LIST))
        self.grid_view_button.clicked.connect(lambda: self._set_view_mode(ViewMode.GRID))
        
        # Import and refresh buttons
        self.import_button.clicked.connect(self._import_models)
        self.refresh_button.clicked.connect(self._refresh_models)
        
        # File browser
        self.file_tree.clicked.connect(self._on_file_tree_clicked)
        
        # Model views
        self.list_view.clicked.connect(self._on_model_clicked)
        self.list_view.doubleClicked.connect(self._on_model_double_clicked)
        self.grid_view.clicked.connect(self._on_model_clicked)
        self.grid_view.doubleClicked.connect(self._on_model_double_clicked)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        self.list_view.setAcceptDrops(True)
        self.grid_view.setAcceptDrops(True)
        
        # Context menu
        self.list_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_view.customContextMenuRequested.connect(self._show_context_menu)
        self.grid_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.grid_view.customContextMenuRequested.connect(self._show_context_menu)
    
    def _set_view_mode(self, mode: ViewMode) -> None:
        """
        Set the current view mode.
        
        Args:
            mode: The view mode to set
        """
        self.view_mode = mode
        
        # Update button states
        self.list_view_button.setChecked(mode == ViewMode.LIST)
        self.grid_view_button.setChecked(mode == ViewMode.GRID)
        
        # Switch tabs
        if mode == ViewMode.LIST:
            self.view_tabs.setCurrentIndex(0)
        else:
            self.view_tabs.setCurrentIndex(1)
        
        self.logger.debug(f"View mode changed to: {mode.value}")
    
    def _populate_category_filter(self) -> None:
        """Populate the category filter with available categories."""
        try:
            categories = self.db_manager.get_categories()
            for category in categories:
                self.category_filter.addItem(category['name'])
        except Exception as e:
            self.logger.error(f"Failed to populate categories: {str(e)}")
    
    def _load_models_from_database(self) -> None:
        """Load models from the database into the view."""
        try:
            self.status_label.setText("Loading models...")
            self.current_models = self.db_manager.get_all_models()
            self._update_model_view()
            self.model_count_label.setText(f"Models: {len(self.current_models)}")
            self.status_label.setText("Ready")
            
            self.logger.info(f"Loaded {len(self.current_models)} models from database")
            
        except Exception as e:
            self.logger.error(f"Failed to load models from database: {str(e)}")
            self.status_label.setText("Error loading models")
    
    def _update_model_view(self) -> None:
        """Update the model view with current models."""
        # Clear existing items
        self.list_model.clear()
        self.list_model.setHorizontalHeaderLabels([
            "Name", "Format", "Size", "Triangles", "Category", "Added Date"
        ])
        
        # Add models to view
        for model in self.current_models:
            # Create items for each column
            name_item = QStandardItem(model.get('title') or model.get('filename', 'Unknown'))
            name_item.setData(model.get('id'), Qt.UserRole)  # Store model ID
            
            format_item = QStandardItem(model.get('format', 'Unknown').upper())
            
            # Format file size
            file_size = model.get('file_size', 0)
            if file_size > 1024 * 1024:
                size_text = f"{file_size / (1024 * 1024):.1f} MB"
            elif file_size > 1024:
                size_text = f"{file_size / 1024:.1f} KB"
            else:
                size_text = f"{file_size} B"
            size_item = QStandardItem(size_text)
            
            triangles_item = QStandardItem(f"{model.get('triangle_count', 0):,}")
            
            category_item = QStandardItem(model.get('category', 'Uncategorized'))
            
            # Format date
            date_added = model.get('date_added', '')
            if date_added:
                # Parse and reformat date
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(date_added.replace('Z', '+00:00'))
                    date_text = dt.strftime('%Y-%m-%d')
                except:
                    date_text = date_added
            else:
                date_text = 'Unknown'
            date_item = QStandardItem(date_text)
            
            # Add row to model
            self.list_model.appendRow([name_item, format_item, size_item, 
                                     triangles_item, category_item, date_item])
        
        # Apply current filters
        self._apply_filters()
    
    def _on_search_requested(self, query: str, filters: Dict[str, Any]) -> None:
        """
        Handle search requests from the search widget.
        
        Args:
            query: Search query string
            filters: Search filters dictionary
        """
        # Update the model view with search results
        # This would typically update the current_models list with search results
        # For now, we'll just log the search request
        self.logger.info(f"Search requested: query='{query}', filters={filters}")
        
        # TODO: Update the model view with search results
        # This would involve:
        # 1. Getting search results from the search engine
        # 2. Updating self.current_models with the results
        # 3. Calling self._update_model_view() to refresh the display
    
    def _on_file_tree_clicked(self, index: QModelIndex) -> None:
        """
        Handle file tree click events.
        
        Args:
            index: Index of the clicked item
        """
        path = self.file_model.filePath(index)
        self.path_display.setText(path)
        
        # Check if this is a directory containing model files
        if self.file_model.isDir(index):
            self._scan_directory_for_models(path)
    
    def _scan_directory_for_models(self, directory_path: str) -> None:
        """
        Scan a directory for model files.
        
        Args:
            directory_path: Path to the directory to scan
        """
        # TODO: Implement directory scanning for model files
        # This would look for STL, OBJ, STEP, MF3 files in the directory
        pass
    
    def _on_model_clicked(self, index: QModelIndex) -> None:
        """
        Handle model click events.
        
        Args:
            index: Index of the clicked model
        """
        # Get the source model index (through proxy)
        source_index = self.proxy_model.mapToSource(index)
        item = self.list_model.item(source_index.row(), 0)
        
        if item:
            model_id = item.data(Qt.UserRole)
            if model_id:
                self.model_selected.emit(model_id)
    
    def _on_model_double_clicked(self, index: QModelIndex) -> None:
        """
        Handle model double-click events.
        
        Args:
            index: Index of the double-clicked model
        """
        # Get the source model index (through proxy)
        source_index = self.proxy_model.mapToSource(index)
        item = self.list_model.item(source_index.row(), 0)
        
        if item:
            model_id = item.data(Qt.UserRole)
            if model_id:
                self.model_double_clicked.emit(model_id)
    
    def _show_context_menu(self, position) -> None:
        """
        Show context menu for model operations.
        
        Args:
            position: Position where the menu should be shown
        """
        # Get the model at the clicked position
        view = self.sender()
        index = view.indexAt(position)
        
        if not index.isValid():
            return
        
        # Get the source model index (through proxy)
        source_index = self.proxy_model.mapToSource(index)
        item = self.list_model.item(source_index.row(), 0)
        
        if not item:
            return
        
        model_id = item.data(Qt.UserRole)
        
        # Create context menu
        menu = QMenu(self)
        
        # Add actions
        open_action = QAction("Open", self)
        open_action.triggered.connect(lambda: self.model_double_clicked.emit(model_id))
        menu.addAction(open_action)
        
        menu.addSeparator()
        
        edit_action = QAction("Edit Properties", self)
        # TODO: Connect to property editor
        menu.addAction(edit_action)
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self._delete_model(model_id))
        menu.addAction(delete_action)
        
        # Show menu
        menu.exec_(view.mapToGlobal(position))
    
    def _delete_model(self, model_id: int) -> None:
        """
        Delete a model from the library.
        
        Args:
            model_id: ID of the model to delete
        """
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Delete Model",
            "Are you sure you want to delete this model from the library?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Delete from database
                success = self.db_manager.delete_model(model_id)
                
                if success:
                    # Reload models
                    self._load_models_from_database()
                    self.logger.info(f"Deleted model with ID: {model_id}")
                else:
                    QMessageBox.warning(self, "Error", "Failed to delete model")
                    
            except Exception as e:
                self.logger.error(f"Failed to delete model {model_id}: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to delete model: {str(e)}")
    
    def _import_models(self) -> None:
        """Handle import models button click."""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter(
            "3D Model Files (*.stl *.obj *.3mf *.step *.stp);;All Files (*)"
        )
        
        if file_dialog.exec_():
            file_paths = file_dialog.selectedFiles()
            self._load_models(file_paths)
    
    @monitor_operation("load_models_to_library")
    def _load_models(self, file_paths: List[str]) -> None:
        """
        Load models from file paths with performance optimization.
        
        Args:
            file_paths: List of file paths to load
        """
        if self.loading_in_progress:
            QMessageBox.information(self, "Loading", "Models are currently being loaded. Please wait.")
            return
        
        # Start performance monitoring
        operation_id = self.performance_monitor.start_operation(
            "load_models_batch",
            {"file_count": len(file_paths)}
        )
        
        self.loading_in_progress = True
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_label.setText("Loading models...")
        
        # Create and start worker thread
        self.model_loader = ModelLoadWorker(file_paths)
        self.model_loader.model_loaded.connect(self._on_model_loaded)
        self.model_loader.progress_updated.connect(self._on_load_progress)
        self.model_loader.error_occurred.connect(self._on_load_error)
        self.model_loader.finished.connect(self._on_load_finished)
        self.model_loader.start()
        
        # Store operation ID for completion
        self._load_operation_id = operation_id
    
    def _on_model_loaded(self, model_info: Dict[str, Any]) -> None:
        """
        Handle model loaded signal from worker thread.
        
        Args:
            model_info: Information about the loaded model
        """
        try:
            # Add to database
            model_id = self.db_manager.add_model(
                filename=model_info['filename'],
                format=model_info['format'],
                file_path=model_info['file_path'],
                file_size=model_info['file_size']
            )
            
            # Add metadata
            self.db_manager.add_model_metadata(
                model_id=model_id,
                title=model_info['filename'],
                description=""
            )
            
            # Generate thumbnail
            thumbnail = self.thumbnail_generator.generate_thumbnail(model_info)
            
            # Store model info for UI update
            model_info['id'] = model_id
            model_info['thumbnail'] = thumbnail
            self.current_models.append(model_info)
            
            self.logger.info(f"Loaded model: {model_info['filename']}")
            
        except Exception as e:
            self.logger.error(f"Failed to save model to database: {str(e)}")
    
    def _on_load_progress(self, progress_percent: float, message: str) -> None:
        """
        Handle loading progress updates.
        
        Args:
            progress_percent: Progress percentage (0-100)
            message: Progress message
        """
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(int(progress_percent))
        self.status_label.setText(message)
    
    def _on_load_error(self, error_message: str) -> None:
        """
        Handle loading errors.
        
        Args:
            error_message: Error message
        """
        self.logger.error(error_message)
        QMessageBox.warning(self, "Loading Error", error_message)
    
    def _on_load_finished(self) -> None:
        """Handle loading completion."""
        self.loading_in_progress = False
        self.progress_bar.setVisible(False)
        self.status_label.setText("Ready")
        
        # Update view
        self._update_model_view()
        
        # Emit signal for added models
        added_ids = [model['id'] for model in self.current_models if 'id' in model]
        if added_ids:
            self.models_added.emit(added_ids)
        
        # End performance monitoring
        if hasattr(self, '_load_operation_id'):
            self.performance_monitor.end_operation(self._load_operation_id, success=True)
            delattr(self, '_load_operation_id')
        
        # Optimize cache
        self.model_cache.optimize_cache()
        
        # Clean up worker thread
        if self.model_loader:
            self.model_loader.deleteLater()
            self.model_loader = None
        
        # Force garbage collection
        gc.collect()
    
    def _refresh_models(self) -> None:
        """Refresh the model library."""
        self._load_models_from_database()
    
    def get_selected_model_id(self) -> Optional[int]:
        """
        Get the ID of the currently selected model.
        
        Returns:
            Model ID or None if no model is selected
        """
        # Get the current view
        if self.view_mode == ViewMode.LIST:
            view = self.list_view
        else:
            view = self.grid_view
        
        # Get selected indexes
        selected_indexes = view.selectedIndexes()
        if not selected_indexes:
            return None
        
        # Get the first selected index
        index = selected_indexes[0]
        source_index = self.proxy_model.mapToSource(index)
        item = self.list_model.item(source_index.row(), 0)
        
        if item:
            return item.data(Qt.UserRole)
        
        return None
    
    def get_selected_models(self) -> List[int]:
        """
        Get the IDs of all selected models.
        
        Returns:
            List of model IDs
        """
        # Get the current view
        if self.view_mode == ViewMode.LIST:
            view = self.list_view
        else:
            view = self.grid_view
        
        # Get selected indexes
        selected_indexes = view.selectedIndexes()
        model_ids = []
        
        for index in selected_indexes:
            source_index = self.proxy_model.mapToSource(index)
            item = self.list_model.item(source_index.row(), 0)
            
            if item:
                model_id = item.data(Qt.UserRole)
                if model_id and model_id not in model_ids:
                    model_ids.append(model_id)
        
        return model_ids
    
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter events."""
        if event.mimeData().hasUrls():
            # Check if any URLs are local files with supported extensions
            has_supported_files = False
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if Path(file_path).suffix.lower() in ['.stl', '.obj', '.3mf', '.step', '.stp']:
                        has_supported_files = True
                        break
            
            if has_supported_files:
                event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop events."""
        if event.mimeData().hasUrls():
            file_paths = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    
                    # Check if it's a directory
                    if Path(file_path).is_dir():
                        # TODO: Add directory scanning
                        pass
                    else:
                        # Check if it's a supported file type
                        if Path(file_path).suffix.lower() in ['.stl', '.obj', '.3mf', '.step', '.stp']:
                            file_paths.append(file_path)
            
            if file_paths:
                self._load_models(file_paths)
    
    def cleanup(self) -> None:
        """Clean up resources before widget destruction."""
        self.logger.info("Cleaning up model library resources")
        
        # Cancel any ongoing loading
        if self.model_loader and self.model_loader.isRunning():
            self.model_loader.cancel()
            self.model_loader.wait(3000)  # Wait up to 3 seconds
        
        # Optimize cache before cleanup
        self.model_cache.optimize_cache()
        
        # Force garbage collection
        gc.collect()
        
        self.logger.info("Model library cleanup completed")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics for the model library.
        
        Returns:
            Dictionary with performance statistics
        """
        cache_stats = self.model_cache.get_stats()
        memory_stats = self.performance_monitor.get_current_memory_stats()
        
        return {
            'cache': {
                'total_entries': cache_stats.total_entries,
                'hit_ratio': self.model_cache.get_hit_ratio(),
                'memory_usage_mb': self.model_cache.get_memory_usage_mb()
            },
            'memory': {
                'used_mb': memory_stats.used_mb,
                'available_mb': memory_stats.available_mb,
                'percent_used': memory_stats.percent_used
            },
            'models_loaded': len(self.current_models)
        }
    
    def closeEvent(self, event) -> None:
        """Handle widget close event."""
        self.cleanup()
        super().closeEvent(event)


# Import required Qt classes
from PySide6.QtCore import QDir, QFileInfo, QRegularExpression
from PySide6.QtGui import QPen, QBrush, QRegularExpressionValidator
from PySide6.QtWidgets import QFileSystemModel, QButtonGroup