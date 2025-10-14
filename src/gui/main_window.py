"""
Main window implementation for 3D-MM application.

This module provides the main application window with menu bar, toolbar,
status bar, and dockable widgets for 3D model management.
"""

import logging
import sys
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, QSize, QTimer, Signal
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QToolBar, QStatusBar, QDockWidget, QLabel, QTextEdit,
    QFrame, QSplitter, QFileDialog, QMessageBox, QProgressBar
)

from core.logging_config import get_logger
from core.database_manager import get_database_manager
from parsers.stl_parser import STLParser, STLProgressCallback


class MainWindow(QMainWindow):
    """
    Main application window for 3D Model Manager.
    
    Provides the primary interface with menu bar, toolbar, status bar,
    and dockable widgets for model management and 3D visualization.
    """
    
    # Custom signals for application events
    model_loaded = Signal(str)  # Emitted when a model is loaded
    model_selected = Signal(int)  # Emitted when a model is selected
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the main window.
        
        Args:
            parent: Parent widget (typically None for main window)
        """
        super().__init__(parent)
        
        # Initialize logger
        self.logger = get_logger(__name__)
        self.logger.info("Initializing main window")
        
        # Window properties
        self.setWindowTitle("3D-MM - 3D Model Manager")
        self.setMinimumSize(1200, 800)
        self.resize(1600, 1000)  # Default size for desktop
        
        # Initialize UI components
        self._init_ui()
        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_status_bar()
        self._setup_dock_widgets()
        self._setup_central_widget()
        
        # Set up status update timer
        self._setup_status_timer()
        
        # Log window initialization
        self.logger.info("Main window initialized successfully")
    
    def _init_ui(self) -> None:
        """Initialize basic UI properties and styling."""
        # Set window icon if available
        # self.setWindowIcon(QIcon(":/icons/app_icon.png"))
        
        # Set application style for Windows desktop
        QApplication.setStyle("Fusion")  # Modern look and feel
        
        # Enable dock widget features for better layout management
        self.setDockOptions(
            QMainWindow.AllowNestedDocks |
            QMainWindow.AllowTabbedDocks |
            QMainWindow.AnimatedDocks
        )
        
        # Set central widget background with standard Windows colors
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
                color: #000000;
            }
            QDockWidget {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
            QDockWidget::title {
                background-color: #f5f5f5;
                padding: 5px;
                border-bottom: 1px solid #d0d0d0;
            }
            QToolBar {
                background-color: #f5f5f5;
                border: 1px solid #d0d0d0;
                spacing: 3px;
                color: #000000;
            }
            QMenuBar {
                background-color: #f5f5f5;
                color: #000000;
                border-bottom: 1px solid #d0d0d0;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
            }
            QMenuBar::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QStatusBar {
                background-color: #f5f5f5;
                color: #000000;
                border-top: 1px solid #d0d0d0;
            }
            QLabel {
                color: #000000;
            }
            QPushButton {
                background-color: #f5f5f5;
                color: #000000;
                border: 1px solid #d0d0d0;
                padding: 4px 12px;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #e1e1e1;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
    
    def _setup_menu_bar(self) -> None:
        """Set up the application menu bar."""
        self.logger.debug("Setting up menu bar")
        
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Open action
        open_action = QAction("&Open Model...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.setStatusTip("Open a 3D model file")
        open_action.triggered.connect(self._open_model)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        # Preferences action
        prefs_action = QAction("&Preferences...", self)
        prefs_action.setStatusTip("Open application preferences")
        prefs_action.triggered.connect(self._show_preferences)
        edit_menu.addAction(prefs_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Zoom actions
        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut(QKeySequence.ZoomIn)
        zoom_in_action.setStatusTip("Zoom in on the 3D view")
        zoom_in_action.triggered.connect(self._zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut(QKeySequence.ZoomOut)
        zoom_out_action.setStatusTip("Zoom out from the 3D view")
        zoom_out_action.triggered.connect(self._zoom_out)
        view_menu.addAction(zoom_out_action)
        
        view_menu.addSeparator()
        
        # Reset view action
        reset_view_action = QAction("&Reset View", self)
        reset_view_action.setStatusTip("Reset the 3D view to default")
        reset_view_action.triggered.connect(self._reset_view)
        view_menu.addAction(reset_view_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        # About action
        about_action = QAction("&About 3D-MM", self)
        about_action.setStatusTip("Show information about 3D-MM")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
        self.logger.debug("Menu bar setup completed")
    
    def _setup_toolbar(self) -> None:
        """Set up the main application toolbar."""
        self.logger.debug("Setting up toolbar")
        
        toolbar = self.addToolBar("Main")
        toolbar.setObjectName("MainToolBar")
        
        # Open button
        open_action = QAction("Open", self)
        open_action.setStatusTip("Open a 3D model file")
        open_action.triggered.connect(self._open_model)
        toolbar.addAction(open_action)
        
        toolbar.addSeparator()
        
        # View controls
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setStatusTip("Zoom in on the 3D view")
        zoom_in_action.triggered.connect(self._zoom_in)
        toolbar.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setStatusTip("Zoom out from the 3D view")
        zoom_out_action.triggered.connect(self._zoom_out)
        toolbar.addAction(zoom_out_action)
        
        reset_action = QAction("Reset View", self)
        reset_action.setStatusTip("Reset the 3D view to default")
        reset_action.triggered.connect(self._reset_view)
        toolbar.addAction(reset_action)
        
        self.logger.debug("Toolbar setup completed")
    
    def _setup_status_bar(self) -> None:
        """Set up the application status bar."""
        self.logger.debug("Setting up status bar")
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Permanent status message
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Progress bar for long operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Memory usage indicator
        self.memory_label = QLabel("Memory: N/A")
        self.status_bar.addPermanentWidget(self.memory_label)
        
        self.logger.debug("Status bar setup completed")
    
    def _setup_dock_widgets(self) -> None:
        """Set up dockable widgets for the application."""
        self.logger.debug("Setting up dock widgets")
        
        # Model library dock (left side)
        self.model_library_dock = QDockWidget("Model Library", self)
        self.model_library_dock.setObjectName("ModelLibraryDock")
        self.model_library_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea
        )
        
        # Create model library widget
        try:
            from gui.model_library import ModelLibraryWidget
            self.model_library_widget = ModelLibraryWidget(self)
            
            # Connect signals
            self.model_library_widget.model_selected.connect(self._on_model_selected)
            self.model_library_widget.model_double_clicked.connect(self._on_model_double_clicked)
            self.model_library_widget.models_added.connect(self._on_models_added)
            
            self.model_library_dock.setWidget(self.model_library_widget)
            self.logger.info("Model library widget created successfully")
            
        except ImportError as e:
            self.logger.warning(f"Failed to import model library widget: {str(e)}")
            
            # Fallback to placeholder
            model_library_widget = QTextEdit()
            model_library_widget.setReadOnly(True)
            model_library_widget.setPlainText(
                "Model Library\n\n"
                "Failed to load model library component.\n"
                "Please ensure all dependencies are properly installed.\n\n"
                "Features will include:\n"
                "- Model list with thumbnails\n"
                "- Category filtering\n"
                "- Search functionality\n"
                "- Import/export options"
            )
            self.model_library_dock.setWidget(model_library_widget)
        
        self.addDockWidget(Qt.LeftDockWidgetArea, self.model_library_dock)
        
        # Properties dock (right side)
        self.properties_dock = QDockWidget("Model Properties", self)
        self.properties_dock.setObjectName("PropertiesDock")
        self.properties_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea
        )
        
        # Placeholder for model properties
        properties_widget = QTextEdit()
        properties_widget.setReadOnly(True)
        properties_widget.setPlainText(
            "Model Properties\n\n"
            "This panel will display properties and metadata\n"
            "for the selected 3D model.\n"
            "Features will include:\n"
            "- Model information\n"
            "- Metadata editing\n"
            "- Tag management\n"
            "- Export settings"
        )
        self.properties_dock.setWidget(properties_widget)
        
        self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)
        
        # Metadata dock (bottom)
        self.metadata_dock = QDockWidget("Metadata Editor", self)
        self.metadata_dock.setObjectName("MetadataDock")
        self.metadata_dock.setAllowedAreas(
            Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea
        )
        
        # Create metadata editor widget
        try:
            from gui.metadata_editor import MetadataEditorWidget
            self.metadata_editor = MetadataEditorWidget(self)
            
            # Connect signals
            self.metadata_editor.metadata_saved.connect(self._on_metadata_saved)
            self.metadata_editor.metadata_changed.connect(self._on_metadata_changed)
            
            self.metadata_dock.setWidget(self.metadata_editor)
            self.logger.info("Metadata editor widget created successfully")
            
        except ImportError as e:
            self.logger.warning(f"Failed to import metadata editor widget: {str(e)}")
            
            # Fallback to placeholder
            metadata_widget = QTextEdit()
            metadata_widget.setReadOnly(True)
            metadata_widget.setPlainText(
                "Metadata Editor\n\n"
                "Failed to load metadata editor component.\n"
                "Please ensure all dependencies are properly installed.\n\n"
                "Features will include:\n"
                "- Title and description editing\n"
                "- Category assignment\n"
                "- Keyword tagging\n"
                "- Custom properties"
            )
            self.metadata_dock.setWidget(metadata_widget)
        
        self.addDockWidget(Qt.BottomDockWidgetArea, self.metadata_dock)
        
        self.logger.debug("Dock widgets setup completed")
    
    def _setup_central_widget(self) -> None:
        """Set up the central widget for the 3D viewer."""
        self.logger.debug("Setting up central widget")
        
        # Import the viewer widget
        try:
            # Try to import VTK-based viewer first
            try:
                from gui.viewer_widget_vtk import Viewer3DWidget
            except ImportError:
                # Fallback to original viewer if VTK is not available
                try:
                    from gui.viewer_widget import Viewer3DWidget
                except ImportError:
                    Viewer3DWidget = None
            
            # Create the 3D viewer widget
            self.viewer_widget = Viewer3DWidget(self)
            
            # Connect signals
            self.viewer_widget.model_loaded.connect(self._on_model_loaded)
            self.viewer_widget.performance_updated.connect(self._on_performance_updated)
            
            self.logger.info("3D viewer widget created successfully")
            
        except ImportError as e:
            self.logger.warning(f"Failed to import 3D viewer widget: {str(e)}")
            
            # Create fallback widget
            self.viewer_widget = QTextEdit()
            self.viewer_widget.setReadOnly(True)
            self.viewer_widget.setPlainText(
                "3D Model Viewer\n\n"
                "Failed to load 3D viewer component.\n"
                "Please ensure VTK or PyQt3D is properly installed.\n\n"
                "Features will include:\n"
                "- Interactive 3D model rendering\n"
                "- Multiple view modes (wireframe, solid, textured)\n"
                "- Camera controls (orbit, pan, zoom)\n"
                "- Lighting controls\n"
                "- Measurement tools\n"
                "- Animation playback\n"
                "- Screenshot capture"
            )
            self.viewer_widget.setAlignment(Qt.AlignCenter)
        
        # Set as central widget
        self.setCentralWidget(self.viewer_widget)
        
        self.logger.debug("Central widget setup completed")
    
    def _setup_status_timer(self) -> None:
        """Set up timer for periodic status updates."""
        # Update memory usage every 5 seconds
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(5000)  # 5 seconds
        
        # Initial update
        self._update_status()
    
    def _update_status(self) -> None:
        """Update status bar information."""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_label.setText(f"Memory: {memory_mb:.1f} MB")
        except ImportError:
            self.memory_label.setText("Memory: N/A (psutil not available)")
        except Exception as e:
            self.logger.warning(f"Failed to update memory status: {str(e)}")
            self.memory_label.setText("Memory: Error")
    
    # Menu action handlers
    
    def _open_model(self) -> None:
        """Handle open model action."""
        self.logger.info("Opening model file dialog")
        
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter(
            "3D Model Files (*.stl *.obj *.step *.stp *.mf3);;All Files (*)"
        )
        
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            self.logger.info(f"Selected model file: {file_path}")
            
            # Update status
            self.status_label.setText(f"Loading: {Path(file_path).name}")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            
            # Load the model using STL parser
            self._load_stl_model(file_path)
    
    def _finish_model_loading(self, file_path: str, success: bool = True, error_message: str = "") -> None:
        """Finish model loading process."""
        filename = Path(file_path).name
        
        if success:
            self.status_label.setText(f"Loaded: {filename}")
            self.logger.info(f"Model loaded successfully: {filename}")
        else:
            self.status_label.setText(f"Failed to load: {filename}")
            self.logger.error(f"Failed to load model: {filename} - {error_message}")
            QMessageBox.warning(
                self,
                "Load Error",
                f"Failed to load model {filename}:\n{error_message}"
            )
        
        self.progress_bar.setVisible(False)
        
        # Emit signal
        self.model_loaded.emit(file_path)
    
    def _load_stl_model(self, file_path: str) -> None:
        """
        Load an STL model using the STL parser and display it in the viewer.
        
        Args:
            file_path: Path to the STL file to load
        """
        try:
            # Create STL parser
            parser = STLParser()
            
            # Create progress callback
            progress_callback = STLProgressCallback(
                callback_func=lambda progress, message: self._update_loading_progress(progress, message)
            )
            
            # Parse the file
            model = parser.parse_file(file_path, progress_callback)
            
            # Load model into viewer if available
            if hasattr(self.viewer_widget, 'load_model'):
                success = self.viewer_widget.load_model(model)
                self._finish_model_loading(file_path, success, "" if success else "Failed to load model into viewer")
            else:
                self._finish_model_loading(file_path, False, "3D viewer not available")
                
        except Exception as e:
            self._finish_model_loading(file_path, False, str(e))
    
    def _update_loading_progress(self, progress_percent: float, message: str) -> None:
        """
        Update loading progress in the UI.
        
        Args:
            progress_percent: Progress percentage (0-100)
            message: Progress message
        """
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(int(progress_percent))
        if message:
            self.status_label.setText(f"Loading: {message}")
    
    def _on_model_loaded(self, info: str) -> None:
        """
        Handle model loaded signal from viewer widget.
        
        Args:
            info: Information about the loaded model
        """
        self.logger.info(f"Viewer model loaded: {info}")
        
        # Update model properties dock if it exists
        if hasattr(self, 'properties_dock'):
            properties_widget = self.properties_dock.widget()
            if isinstance(properties_widget, QTextEdit):
                if hasattr(self.viewer_widget, 'get_model_info'):
                    model_info = self.viewer_widget.get_model_info()
                    if model_info:
                        info_text = (
                            f"Model Properties\n\n"
                            f"Triangles: {model_info['triangle_count']:,}\n"
                            f"Vertices: {model_info['vertex_count']:,}\n"
                            f"Dimensions: {model_info['dimensions'][0]:.2f} x "
                            f"{model_info['dimensions'][1]:.2f} x "
                            f"{model_info['dimensions'][2]:.2f}\n"
                            f"File size: {model_info['file_size'] / 1024:.1f} KB\n"
                            f"Format: {model_info['format']}\n"
                            f"Parse time: {model_info['parsing_time']:.3f} s\n"
                            f"FPS: {model_info['current_fps']:.1f}"
                        )
                        properties_widget.setPlainText(info_text)
    
    def _on_performance_updated(self, fps: float) -> None:
        """
        Handle performance update signal from viewer widget.
        
        Args:
            fps: Current frames per second
        """
        # Update status with FPS if it's below threshold
        if fps < 30.0:
            self.status_label.setText(f"Performance: {fps:.1f} FPS (low)")
    
    def _on_model_selected(self, model_id: int) -> None:
        """
        Handle model selection from the model library.
        
        Args:
            model_id: ID of the selected model
        """
        try:
            # Get model information from database
            db_manager = get_database_manager()
            model = db_manager.get_model(model_id)
            
            if model:
                self.logger.info(f"Model selected from library: {model['filename']} (ID: {model_id})")
                self.model_selected.emit(model_id)
                
                # Load metadata in the metadata editor
                if hasattr(self, 'metadata_editor'):
                    self.metadata_editor.load_model_metadata(model_id)
                
                # Update view count
                db_manager.increment_view_count(model_id)
            else:
                self.logger.warning(f"Model with ID {model_id} not found in database")
                
        except Exception as e:
            self.logger.error(f"Failed to handle model selection: {str(e)}")
    
    def _on_model_double_clicked(self, model_id: int) -> None:
        """
        Handle model double-click from the model library.
        
        Args:
            model_id: ID of the double-clicked model
        """
        try:
            # Get model information from database
            db_manager = get_database_manager()
            model = db_manager.get_model(model_id)
            
            if model:
                file_path = model['file_path']
                self.logger.info(f"Loading model from library: {file_path}")
                
                # Update status
                from pathlib import Path
                filename = Path(file_path).name
                self.status_label.setText(f"Loading: {filename}")
                self.progress_bar.setVisible(True)
                self.progress_bar.setRange(0, 0)  # Indeterminate progress
                
                # Load the model using STL parser
                self._load_stl_model(file_path)
            else:
                self.logger.warning(f"Model with ID {model_id} not found in database")
                
        except Exception as e:
            self.logger.error(f"Failed to handle model double-click: {str(e)}")
    
    def _on_models_added(self, model_ids: List[int]) -> None:
        """
        Handle models added to the library.
        
        Args:
            model_ids: List of IDs of added models
        """
        self.logger.info(f"Added {len(model_ids)} models to library")
        
        # Update status
        if model_ids:
            self.status_label.setText(f"Added {len(model_ids)} models to library")
            
            # Clear status after a delay
            QTimer.singleShot(3000, lambda: self.status_label.setText("Ready"))
    
    def _on_metadata_saved(self, model_id: int) -> None:
        """
        Handle metadata saved event from the metadata editor.
        
        Args:
            model_id: ID of the model whose metadata was saved
        """
        try:
            self.logger.info(f"Metadata saved for model ID: {model_id}")
            self.status_label.setText("Metadata saved")
            
            # Update the model library to reflect changes
            if hasattr(self, 'model_library_widget'):
                self.model_library_widget._load_models_from_database()
            
            # Clear status after a delay
            QTimer.singleShot(3000, lambda: self.status_label.setText("Ready"))
            
        except Exception as e:
            self.logger.error(f"Failed to handle metadata saved event: {str(e)}")
    
    def _on_metadata_changed(self, model_id: int) -> None:
        """
        Handle metadata changed event from the metadata editor.
        
        Args:
            model_id: ID of the model whose metadata changed
        """
        try:
            self.logger.debug(f"Metadata changed for model ID: {model_id}")
            # Update status to indicate unsaved changes
            self.status_label.setText("Metadata modified (unsaved changes)")
            
        except Exception as e:
            self.logger.error(f"Failed to handle metadata changed event: {str(e)}")
    
    def _show_preferences(self) -> None:
        """Show preferences dialog."""
        self.logger.info("Opening preferences dialog")
        QMessageBox.information(
            self,
            "Preferences",
            "Preferences dialog will be implemented in a future version.\n\n"
            "Planned features:\n"
            "- Display settings\n"
            "- File paths and directories\n"
            "- Performance options\n"
            "- Theme customization"
        )
    
    def _zoom_in(self) -> None:
        """Handle zoom in action."""
        self.logger.debug("Zoom in requested")
        self.status_label.setText("Zoomed in")
        
        # Forward to viewer widget if available
        if hasattr(self.viewer_widget, 'zoom_in'):
            self.viewer_widget.zoom_in()
        else:
            QTimer.singleShot(2000, lambda: self.status_label.setText("Ready"))
    
    def _zoom_out(self) -> None:
        """Handle zoom out action."""
        self.logger.debug("Zoom out requested")
        self.status_label.setText("Zoomed out")
        
        # Forward to viewer widget if available
        if hasattr(self.viewer_widget, 'zoom_out'):
            self.viewer_widget.zoom_out()
        else:
            QTimer.singleShot(2000, lambda: self.status_label.setText("Ready"))
    
    def _reset_view(self) -> None:
        """Handle reset view action."""
        self.logger.debug("Reset view requested")
        self.status_label.setText("View reset")
        
        # Forward to viewer widget if available
        if hasattr(self.viewer_widget, 'reset_view'):
            self.viewer_widget.reset_view()
        else:
            QTimer.singleShot(2000, lambda: self.status_label.setText("Ready"))
    
    def _show_about(self) -> None:
        """Show about dialog."""
        self.logger.info("Showing about dialog")
        
        about_text = (
            "<h3>3D-MM - 3D Model Manager</h3>"
            "<p>Version 1.0.0</p>"
            "<p>A desktop application for managing and viewing 3D models.</p>"
            "<p><b>Supported formats:</b> STL, OBJ, STEP, MF3</p>"
            "<p><b>Requirements:</b> Windows 7+, Python 3.8+, PySide5</p>"
            "<br>"
            "<p>&copy; 2023 3D-MM Development Team</p>"
        )
        
        QMessageBox.about(self, "About 3D-MM", about_text)
    
    # Event handlers
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        self.logger.info("Application closing")
        
        # Clean up resources
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        
        # Clean up widgets
        if hasattr(self, 'metadata_editor'):
            self.metadata_editor.cleanup()
        
        if hasattr(self, 'model_library_widget'):
            self.model_library_widget.cleanup()
        
        # Accept the close event
        event.accept()
        
        self.logger.info("Application closed")