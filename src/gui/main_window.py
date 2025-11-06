"""
Main window implementation for Digital Workshop.

This module provides the main application window with menu bar, toolbar,
status bar, and dockable widgets for 3D model management.
"""

import logging
import sys
import json
import base64
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import (
    Qt,
    QSize,
    QTimer,
    Signal,
    QStandardPaths,
    QSettings,
    QEvent,
    QObject,
    QPoint,
    QRect,
)
from PySide6.QtGui import QAction, QIcon, QKeySequence, QPalette, QCursor
from PySide6.QtWidgets import (
    QMainWindow,
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QMenuBar,
    QToolBar,
    QStatusBar,
    QDockWidget,
    QLabel,
    QTextEdit,
    QPushButton,
    QFrame,
    QSplitter,
    QFileDialog,
    QMessageBox,
    QProgressBar,
    QTabWidget,
    QSizePolicy,
)

from src.core.logging_config import get_logger, get_activity_logger
from src.core.database_manager import get_database_manager
from src.core.data_structures import ModelFormat
from src.core.model_cache import get_model_cache, CacheLevel
from src.parsers.stl_parser import STLParser, STLProgressCallback
from src.parsers.obj_parser import OBJParser
from src.parsers.threemf_parser import ThreeMFParser
from src.parsers.step_parser import STEPParser
from src.parsers.format_detector import FormatDetector
from src.gui.preferences import PreferencesDialog
from src.gui.window.dock_snapping import SnapOverlayLayer, DockDragHandler
from src.gui.project_details_widget import ProjectDetailsWidget
from src.gui.theme import MIN_WIDGET_SIZE


class MainWindow(QMainWindow):
    """
    Main application window for Digital Workshop.

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
        import time

        super().__init__(parent)

        # Initialize logger
        self.logger = get_logger(__name__)
        self.activity_logger = get_activity_logger(__name__)
        self.logger.info("Initializing main window")

        # Initialize AI Description Service
        try:
            from src.gui.services.ai_description_service import AIDescriptionService

            self.ai_service = AIDescriptionService()
            self.logger.info("AI Description Service initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize AI Description Service: {e}")
            self.ai_service = None

        # Hide window during initialization to prevent blinking
        self.hide()

        # Window properties
        self.setWindowTitle("Digital Workshop")

        # Load window settings from config
        try:
            from src.core.application_config import ApplicationConfig

            config = ApplicationConfig.get_default()
            min_width = config.minimum_window_width
            min_height = config.minimum_window_height

            # Calculate default window size based on screen geometry
            # (50% width, 100% height - snapped to middle wide, full height)
            default_width, default_height = (
                ApplicationConfig.calculate_default_window_size()
            )

            self.maximize_on_startup = config.maximize_on_startup
            self.remember_window_size = config.remember_window_size

            self.logger.info(
                f"FIX: Calculated default window size: {default_width}x{default_height} (50% width, 100% height)"
            )
        except Exception as e:
            self.logger.warning(f"Failed to load window settings from config: {e}")
            min_width = 800
            min_height = 600
            default_width = 1200
            default_height = 800
            self.maximize_on_startup = False
            self.remember_window_size = True

        self.setMinimumSize(MIN_WIDGET_SIZE, MIN_WIDGET_SIZE)

        # CRITICAL FIX: Restore window geometry during initialization, not in showEvent
        # This ensures proper timing coordination between window creation and state restoration
        restoration_start = time.time()
        self.logger.info("FIX: Restoring window geometry during initialization phase")

        try:
            self._restore_window_geometry_early()
            restoration_time = time.time() - restoration_start
            self.logger.info(
                f"FIX: Window geometry restoration completed in {restoration_time:.3f}s during init"
            )
        except Exception as e:
            self.logger.warning(
                f"FIX: Failed to restore window geometry during init, using defaults: {e}"
            )
            # Fallback to default size if restoration fails
            self.resize(default_width, default_height)

        # Initialize UI components
        self._init_ui()

        # Window geometry restoration now happens during initialization for proper timing

    def _init_ui(self) -> None:
        """Initialize basic UI properties and styling."""
        # Set application style for Windows desktop
        QApplication.setStyle("Fusion")  # Modern look and feel

        # Use native title bar (removed frameless window flag)
        # This allows the OS to handle the title bar and window controls

        # Enable dock widget features for better layout management
        options = (
            QMainWindow.AllowNestedDocks
            | QMainWindow.AllowTabbedDocks
            | QMainWindow.AnimatedDocks
        )
        # Grouped dragging (if available) improves docking behavior when tabs are involved
        if hasattr(QMainWindow, "GroupedDragging"):
            options |= QMainWindow.GroupedDragging
        self.setDockOptions(options)
        # Explicitly enable nesting (no-op on some styles, harmless)
        try:
            self.setDockNestingEnabled(True)
        except Exception:
            pass

        # Initialize extracted managers
        from src.gui.components.menu_manager import MenuManager
        from src.gui.components.toolbar_manager import ToolbarManager
        from src.gui.components.status_bar_manager import StatusBarManager

        self.menu_manager = MenuManager(self, self.logger)
        self.toolbar_manager = ToolbarManager(self, self.logger)
        self.status_bar_manager = StatusBarManager(self, self.logger)

        self.menu_manager.setup_menu_bar()
        self.toolbar_manager.setup_toolbar()
        self.status_bar_manager.setup_status_bar()

        # Expose theme button for easy access
        self.theme_button = self.status_bar_manager.theme_button

        # Update initial theme icon
        self.status_bar_manager._update_theme_icon()

        # Expose status bar components for easy access
        self.status_label = self.status_bar_manager.status_label
        self.progress_bar = self.status_bar_manager.progress_bar
        self.hash_indicator = self.status_bar_manager.hash_indicator
        self.memory_label = self.status_bar_manager.memory_label

        # Expose menu manager actions for easy access
        self.toggle_layout_edit_action = self.menu_manager.toggle_layout_edit_action
        self.show_metadata_action = self.menu_manager.show_metadata_action
        self.show_model_library_action = self.menu_manager.show_model_library_action

        # Use native Qt dock system instead of custom dock manager
        self._setup_native_dock_widgets()

        # Use native Qt central widget instead of custom manager
        self._setup_native_central_widget()

        # Qt-material handles all styling automatically through the application
        # No need to manually apply stylesheets to main window

        # Initialize model loader
        from src.gui.model.model_loader import ModelLoader

        self.model_loader_manager = ModelLoader(self, self.logger)

        # Let PySide6 handle all window management naturally
        # Removed all custom layout management and snapping systems
        # CRITICAL: Always start with layout locked (edit mode OFF)
        # This ensures the app always opens with layout locked, regardless of saved settings
        try:
            # Force layout edit mode OFF on startup
            self._set_layout_edit_mode(False, show_message=False)
            self.logger.info("FIX: Layout edit mode forced OFF on application startup")

            # Update toggle action to reflect locked state
            if hasattr(self, "toggle_layout_edit_action"):
                self.toggle_layout_edit_action.setChecked(False)
        except Exception:
            # If settings fail, lock layout
            try:
                self._set_layout_edit_mode(False, show_message=False)
            except Exception:
                pass

        # Set up status update timer
        self.status_bar_manager.setup_status_timer()

        # Set up periodic window state save timer (every 5 seconds)
        # This ensures window position/size is saved periodically, not just on close
        # Protects against data loss if the app crashes
        self._setup_periodic_window_state_save()

        # Let PySide6 handle all layout management naturally
        # Removed custom layout timers and forced layout updates

        # Log window initialization
        self.logger.info(
            "Main window initialized successfully - PySide6 handling all layout management"
        )

    def _setup_native_central_widget(self) -> None:
        """Set up native Qt central widget with built-in layout management."""
        self.logger.debug("Setting up native central widget")

        # Create native Qt tab widget for central area
        self.hero_tabs = QTabWidget(self)
        self.hero_tabs.setObjectName("HeroTabs")

        # Configure tab widget with native Qt properties
        self.hero_tabs.setDocumentMode(True)
        self.hero_tabs.setTabsClosable(False)
        self.hero_tabs.setMovable(True)
        self.hero_tabs.setUsesScrollButtons(False)
        self.hero_tabs.setElideMode(Qt.ElideNone)
        self.hero_tabs.setTabBarAutoHide(False)

        # Set expanding policy for native layout management
        self.hero_tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.hero_tabs.setContentsMargins(0, 0, 0, 0)

        # Get tab bar and configure for native behavior
        tab_bar = self.hero_tabs.tabBar()
        if tab_bar:
            tab_bar.setExpanding(True)
            tab_bar.setUsesScrollButtons(False)

        # Set up 3D viewer as the primary tab
        self._setup_viewer_widget()

        # Add placeholder tabs for other features
        self._add_placeholder_tabs()

        # Set as central widget - Qt will handle all layout automatically
        self.setCentralWidget(self.hero_tabs)

        # Qt handles tab persistence automatically through QSettings

        # Restore last active tab
        self._restore_active_tab()

        self.logger.info("Native central widget setup completed - Qt handling layout")

    def _setup_native_dock_widgets(self) -> None:
        """Set up dock widgets using native Qt dock system."""
        self.logger.debug("Setting up native dock widgets")

        # Configure native Qt dock options for optimal performance
        dock_options = (
            QMainWindow.AllowNestedDocks
            | QMainWindow.AllowTabbedDocks
            | QMainWindow.AnimatedDocks
        )
        # Add grouped dragging if available for better UX
        if hasattr(QMainWindow, "GroupedDragging"):
            dock_options |= QMainWindow.GroupedDragging
        self.setDockOptions(dock_options)

        # Enable dock nesting for native layout management
        try:
            self.setDockNestingEnabled(True)
        except Exception:
            pass

        # Apply dock tab positions from settings
        self._apply_dock_tab_positions()

        # Set up individual dock widgets using native Qt
        self._setup_model_library_dock()
        self._setup_project_manager_dock()
        self._setup_properties_dock()
        self._setup_metadata_dock()

        # Load saved dock layout using native Qt methods
        self._load_native_dock_layout()

        # Connect native dock signals for layout persistence
        self._connect_native_dock_signals()

        self.logger.info(
            "Native dock widgets setup completed - Qt handling all dock management"
        )

    def _setup_model_library_dock(self) -> None:
        """Set up model library dock using native Qt."""
        try:
            self.model_library_dock = QDockWidget("Model Library", self)
            self.model_library_dock.setObjectName("ModelLibraryDock")

            # Configure with native Qt dock features
            self.model_library_dock.setAllowedAreas(
                Qt.LeftDockWidgetArea
                | Qt.RightDockWidgetArea
                | Qt.TopDockWidgetArea
                | Qt.BottomDockWidgetArea
            )
            # Start with layout locked (only closable, not movable)
            self.model_library_dock.setFeatures(QDockWidget.DockWidgetClosable)

            # Create model library widget
            try:
                from src.gui.model_library import ModelLibraryWidget

                self.model_library_widget = ModelLibraryWidget(self)

                # Connect native Qt signals
                self.model_library_widget.model_selected.connect(
                    self._on_model_selected
                )
                self.model_library_widget.model_double_clicked.connect(
                    self._on_model_double_clicked
                )
                self.model_library_widget.models_added.connect(self._on_models_added)

                self.model_library_dock.setWidget(self.model_library_widget)
                self.logger.info("Model library dock created successfully")

            except Exception as e:
                self.logger.warning(f"Failed to create model library widget: {e}")
                # Native Qt fallback
                fallback_widget = QLabel("Model Library\n\nComponent unavailable.")
                fallback_widget.setAlignment(Qt.AlignCenter)
                self.model_library_dock.setWidget(fallback_widget)

            # Add to main window using native Qt dock system
            self.addDockWidget(Qt.LeftDockWidgetArea, self.model_library_dock)

            # Register for snapping functionality
            try:
                self._register_dock_for_snapping(self.model_library_dock)
            except Exception as e:
                self.logger.debug(f"Failed to register dock for snapping: {e}")

            # Connect visibility signal for menu synchronization
            self.model_library_dock.visibilityChanged.connect(
                lambda visible: self._update_library_action_state()
            )
            # Qt handles layout persistence automatically

        except Exception as e:
            self.logger.error(f"Failed to setup model library dock: {e}")

    def _setup_project_manager_dock(self) -> None:
        """Set up project manager dock using native Qt."""
        try:
            self.project_manager_dock = QDockWidget("Project Manager", self)
            self.project_manager_dock.setObjectName("ProjectManagerDock")

            # Configure with native Qt dock features
            self.project_manager_dock.setAllowedAreas(
                Qt.LeftDockWidgetArea
                | Qt.RightDockWidgetArea
                | Qt.TopDockWidgetArea
                | Qt.BottomDockWidgetArea
            )
            # Start with layout locked (only closable, not movable)
            self.project_manager_dock.setFeatures(QDockWidget.DockWidgetClosable)

            # Create project manager widget
            try:
                from src.gui.project_manager import ProjectTreeWidget
                from src.core.database.database_manager import DatabaseManager

                db_manager = get_database_manager()
                self.project_manager_widget = ProjectTreeWidget(db_manager, self)

                # Connect signals
                self.project_manager_widget.project_opened.connect(
                    self._on_project_opened
                )
                self.project_manager_widget.project_created.connect(
                    self._on_project_created
                )
                self.project_manager_widget.project_deleted.connect(
                    self._on_project_deleted
                )
                self.project_manager_widget.tab_switch_requested.connect(
                    self._on_tab_switch_requested
                )

                self.project_manager_dock.setWidget(self.project_manager_widget)
                self.logger.info("Project manager dock created successfully")

            except Exception as e:
                self.logger.warning(f"Failed to create project manager widget: {e}")
                # Native Qt fallback
                fallback_widget = QLabel("Project Manager\n\nComponent unavailable.")
                fallback_widget.setAlignment(Qt.AlignCenter)
                self.project_manager_dock.setWidget(fallback_widget)

            # Add to main window using native Qt dock system
            self.addDockWidget(Qt.LeftDockWidgetArea, self.project_manager_dock)

            # Tabify with model library dock using native Qt
            # This ensures they start tabbed together, preventing the "jump" effect
            try:
                if hasattr(self, "model_library_dock") and self.model_library_dock:
                    self.tabifyDockWidget(self.model_library_dock, self.project_manager_dock)
                    self.logger.info(
                        "Model Library and Project Manager docks tabified using native Qt"
                    )
            except Exception as e:
                self.logger.debug(f"Could not tabify docks: {e}")

            # Set minimum width to prevent zero-width widgets
            self.project_manager_dock.setMinimumWidth(MIN_WIDGET_SIZE)

            # Register for snapping functionality
            try:
                self._register_dock_for_snapping(self.project_manager_dock)
            except Exception as e:
                self.logger.debug(f"Failed to register dock for snapping: {e}")

            # Connect visibility signal for menu synchronization
            self.project_manager_dock.visibilityChanged.connect(
                lambda visible: self._update_project_manager_action_state()
            )

        except Exception as e:
            self.logger.error(f"Failed to setup project manager dock: {e}")

    def _setup_properties_dock(self) -> None:
        """Set up properties dock using native Qt."""
        try:
            self.properties_dock = QDockWidget("Project Details", self)
            self.properties_dock.setObjectName("PropertiesDock")

            # Configure with native Qt dock features
            self.properties_dock.setAllowedAreas(
                Qt.LeftDockWidgetArea
                | Qt.RightDockWidgetArea
                | Qt.TopDockWidgetArea
                | Qt.BottomDockWidgetArea
            )
            # Start with layout locked (only closable, not movable)
            self.properties_dock.setFeatures(QDockWidget.DockWidgetClosable)

            # Create project details widget
            self.project_details_widget = ProjectDetailsWidget(self)
            self.properties_dock.setWidget(self.project_details_widget)

            # Add to main window using native Qt dock system
            self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)

            # Register for snapping functionality
            try:
                self._register_dock_for_snapping(self.properties_dock)
            except Exception as e:
                self.logger.debug(f"Failed to register dock for snapping: {e}")

            # Set minimum width to prevent zero-width widgets
            self.properties_dock.setMinimumWidth(MIN_WIDGET_SIZE)
            self.properties_dock.setSizePolicy(
                QSizePolicy.Preferred, QSizePolicy.Expanding
            )

        except Exception as e:
            self.logger.error(f"Failed to setup properties dock: {e}")

    def _setup_metadata_dock(self) -> None:
        """Set up metadata dock using native Qt."""
        try:
            self.metadata_dock = QDockWidget("Metadata Editor", self)
            self.metadata_dock.setObjectName("MetadataDock")

            # Configure with native Qt dock features
            self.metadata_dock.setAllowedAreas(
                Qt.LeftDockWidgetArea
                | Qt.RightDockWidgetArea
                | Qt.TopDockWidgetArea
                | Qt.BottomDockWidgetArea
            )
            # Start with layout locked (only closable, not movable)
            self.metadata_dock.setFeatures(QDockWidget.DockWidgetClosable)

            # Create metadata widget using native Qt
            try:
                from src.gui.metadata_editor import MetadataEditorWidget

                self.metadata_editor = MetadataEditorWidget(self)

                # Connect native Qt signals
                self.metadata_editor.metadata_saved.connect(self._on_metadata_saved)
                self.metadata_editor.metadata_changed.connect(self._on_metadata_changed)

                # Create tab widget for metadata sections
                self.metadata_tabs = QTabWidget(self)
                self.metadata_tabs.setObjectName("MetadataTabs")
                self.metadata_tabs.addTab(self.metadata_editor, "Metadata")

                # Add placeholder tabs using native Qt
                notes_widget = QLabel(
                    "Notes\n\n"
                    "Add project or model-specific notes here.\n"
                    "Future: rich text, timestamps, and attachments."
                )
                notes_widget.setAlignment(Qt.AlignCenter)
                notes_widget.setWordWrap(True)
                self.metadata_tabs.addTab(notes_widget, "Notes")

                history_widget = QLabel(
                    "History\n\n"
                    "Timeline of edits and metadata changes will appear here."
                )
                history_widget.setAlignment(Qt.AlignCenter)
                history_widget.setWordWrap(True)
                self.metadata_tabs.addTab(history_widget, "History")

                self.metadata_dock.setWidget(self.metadata_tabs)
                self.logger.info("Metadata dock created successfully")

            except Exception as e:
                self.logger.warning(f"Failed to create metadata editor: {e}")
                # Native Qt fallback
                fallback_widget = QLabel("Metadata Editor\n\nComponent unavailable.")
                fallback_widget.setAlignment(Qt.AlignCenter)
                fallback_widget.setWordWrap(True)
                self.metadata_dock.setWidget(fallback_widget)

            # Add to main window using native Qt dock system
            self.addDockWidget(Qt.RightDockWidgetArea, self.metadata_dock)

            # Register for snapping functionality
            try:
                self._register_dock_for_snapping(self.metadata_dock)
            except Exception as e:
                self.logger.debug(f"Failed to register dock for snapping: {e}")

            # Tabify with properties dock using native Qt
            try:
                self.tabifyDockWidget(self.properties_dock, self.metadata_dock)
                self.logger.info(
                    "Properties and Metadata docks tabified using native Qt"
                )
            except Exception as e:
                self.logger.debug(f"Could not tabify docks: {e}")

            # Set minimum width to prevent zero-width widgets
            self.metadata_dock.setMinimumWidth(MIN_WIDGET_SIZE)
            self.metadata_dock.setMaximumWidth(500)
            self.metadata_dock.setSizePolicy(
                QSizePolicy.Preferred, QSizePolicy.Expanding
            )

            # Connect visibility signal for menu synchronization
            self.metadata_dock.visibilityChanged.connect(
                lambda visible: self._update_metadata_action_state()
            )
            # Qt handles layout persistence automatically

        except Exception as e:
            self.logger.error(f"Failed to setup metadata dock: {e}")

    def _load_native_dock_layout(self) -> None:
        """Load saved dock layout using native Qt methods.

        Note: This is called during initialization but actual restoration
        is deferred to showEvent() to ensure proper timing.
        """
        # Geometry restoration is now handled in showEvent() for proper timing
        self.logger.debug("Dock layout restoration deferred to showEvent()")

    def _connect_native_dock_signals(self) -> None:
        """Connect native Qt dock signals for layout persistence."""
        # Qt handles dock layout persistence automatically through QSettings
        self.logger.debug(
            "Native Qt dock system handles layout persistence automatically"
        )

    def _setup_viewer_widget(self) -> None:
        """Set up the 3D viewer widget using native Qt integration."""
        try:
            # Try to load the VTK viewer widget
            try:
                from src.gui.viewer_widget_vtk import Viewer3DWidget
            except ImportError:
                try:
                    from src.gui.viewer_widget import Viewer3DWidget
                except ImportError:
                    Viewer3DWidget = None

            if Viewer3DWidget is not None:
                self.viewer_widget = Viewer3DWidget(self)
                self.logger.info("3D viewer widget created successfully")
            else:
                # Native Qt fallback
                self.viewer_widget = QLabel("3D Viewer not available")
                self.viewer_widget.setAlignment(Qt.AlignCenter)
                self.logger.warning(
                    "Viewer3DWidget not available, using native Qt placeholder"
                )

            # Connect viewer signals
            if hasattr(self.viewer_widget, "model_loaded"):
                self.viewer_widget.model_loaded.connect(self._on_model_loaded)
            # FPS counter removed - performance_updated signal no longer connected

            # Set up managers
            self._setup_viewer_managers()

            # Connect lighting panel signal after managers are set up
            if hasattr(self.viewer_widget, "lighting_panel_requested"):
                self.viewer_widget.lighting_panel_requested.connect(
                    self._toggle_lighting_panel
                )
                self.logger.info("Lighting panel signal connected to main window")

        except Exception as e:
            self.logger.warning(f"Failed to setup viewer widget: {e}")
            # Native Qt fallback
            self.viewer_widget = QLabel("3D Model Viewer\n\nComponent unavailable.")
            self.viewer_widget.setAlignment(Qt.AlignCenter)

        # Add to hero tabs
        self.hero_tabs.addTab(self.viewer_widget, "Model Previewer")

    def _setup_viewer_managers(self) -> None:
        """Set up viewer-related managers using native Qt integration."""
        try:
            from src.core.database_manager import get_database_manager
            from src.gui.material_manager import MaterialManager
            from src.gui.lighting_manager import LightingManager

            # Material manager
            try:
                self.material_manager = MaterialManager(get_database_manager())
            except Exception as e:
                self.material_manager = None
                self.logger.warning(f"MaterialManager unavailable: {e}")

            # Lighting manager
            try:
                renderer = getattr(self.viewer_widget, "renderer", None)
                self.lighting_manager = LightingManager(renderer) if renderer else None
                if self.lighting_manager:
                    self.lighting_manager.create_light()
            except Exception as e:
                self.lighting_manager = None
                self.logger.warning(f"LightingManager unavailable: {e}")

            # Create lighting control panel
            try:
                from src.gui.lighting_control_panel import LightingControlPanel

                self.lighting_panel = LightingControlPanel(self)
                self.lighting_panel.setObjectName("LightingDialog")
                self.lighting_panel.hide()
                self.logger.info("Lighting control panel created as floating dialog")

                # Connect lighting panel signals to main window handlers
                if self.lighting_manager:
                    self.lighting_panel.position_changed.connect(
                        self._update_light_position
                    )
                    self.lighting_panel.color_changed.connect(self._update_light_color)
                    self.lighting_panel.intensity_changed.connect(
                        self._update_light_intensity
                    )
                    self.lighting_panel.cone_angle_changed.connect(
                        self._update_light_cone_angle
                    )

                    # Initialize panel with current lighting properties
                    props = self.lighting_manager.get_properties()
                    self.lighting_panel.set_values(
                        position=tuple(props.get("position", (100.0, 100.0, 100.0))),
                        color=tuple(props.get("color", (1.0, 1.0, 1.0))),
                        intensity=float(props.get("intensity", 0.8)),
                        cone_angle=float(props.get("cone_angle", 30.0)),
                        emit_signals=False,
                    )
                    self.logger.info(
                        "Lighting panel signals connected to main window handlers"
                    )
            except Exception as e:
                self.lighting_panel = None
                self.logger.warning(f"Failed to create LightingControlPanel: {e}")

            # Material-Lighting integration
            try:
                from src.gui.materials.integration import MaterialLightingIntegrator

                self.material_lighting_integrator = MaterialLightingIntegrator(self)
                self.logger.info("MaterialLightingIntegrator created successfully")
            except Exception as e:
                self.material_lighting_integrator = None
                self.logger.warning(f"MaterialLightingIntegrator unavailable: {e}")

        except Exception as e:
            self.logger.warning(f"Failed to setup viewer managers: {e}")

    def _add_placeholder_tabs(self) -> None:
        """Add placeholder tabs for other features using native Qt widgets."""

        def create_placeholder(title: str, content: str) -> QWidget:
            """Create a native Qt placeholder widget."""
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(12, 12, 12, 12)

            label = QLabel(content)
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
            layout.addStretch(1)

            return widget

        # Try to add G-code Previewer widget
        try:
            self.logger.info("Attempting to create G-code Previewer widget...")
            from src.gui.gcode_previewer_components import GcodePreviewerWidget

            self.gcode_previewer_widget = GcodePreviewerWidget(self)
            self.hero_tabs.addTab(self.gcode_previewer_widget, "G Code Previewer")
            self.logger.info("G-code Previewer widget created successfully")
        except Exception as e:
            self.logger.error(
                f"Failed to create G-code Previewer widget: {e}", exc_info=True
            )
            self.hero_tabs.addTab(
                create_placeholder(
                    "G Code Previewer", "G-code Previewer\n\nComponent unavailable."
                ),
                "G Code Previewer",
            )

        # Try to add Cut List Optimizer widget
        try:
            self.logger.info("Attempting to create Cut List Optimizer widget...")
            from src.gui.CLO import CutListOptimizerWidget

            self.clo_widget = CutListOptimizerWidget()
            self.hero_tabs.addTab(self.clo_widget, "Cut List Optimizer")
            self.logger.info("Cut List Optimizer widget created successfully")
        except Exception as e:
            self.logger.warning(f"Failed to create Cut List Optimizer widget: {e}")
            self.hero_tabs.addTab(
                create_placeholder(
                    "Cut List Optimizer", "Cut List Optimizer\n\nComponent unavailable."
                ),
                "Cut List Optimizer",
            )

        # Try to add Feeds & Speeds widget
        try:
            self.logger.info("Attempting to create Feeds & Speeds widget...")
            from src.gui.feeds_and_speeds import FeedsAndSpeedsWidget

            self.feeds_and_speeds_widget = FeedsAndSpeedsWidget(self)
            self.hero_tabs.addTab(self.feeds_and_speeds_widget, "Feed and Speed")
            self.logger.info("Feeds & Speeds widget created successfully")
        except Exception as e:
            self.logger.warning(f"Failed to create Feeds & Speeds widget: {e}")
            self.hero_tabs.addTab(
                create_placeholder(
                    "Feed and Speed",
                    "Feeds & Speeds Calculator\n\nComponent unavailable.",
                ),
                "Feed and Speed",
            )

        # Try to add Cost Estimator widget
        try:
            self.logger.info("Attempting to create Cost Estimator widget...")
            from src.gui.cost_estimator import CostEstimatorWidget

            self.cost_estimator_widget = CostEstimatorWidget(self)
            self.hero_tabs.addTab(self.cost_estimator_widget, "Project Cost Estimator")
            self.logger.info("Cost Estimator widget created successfully")
        except Exception as e:
            self.logger.warning(f"Failed to create Cost Estimator widget: {e}")
            self.hero_tabs.addTab(
                create_placeholder(
                    "Project Cost Estimator",
                    "Cost Calculator\n\nEstimate material, machine, and labor costs.",
                ),
                "Project Cost Estimator",
            )

    def _restore_active_tab(self) -> None:
        """Restore the last active tab using native Qt settings."""
        try:
            settings = QSettings()
            active_tab = settings.value("ui/active_hero_tab_index", 0, type=int)
            if isinstance(active_tab, int) and 0 <= active_tab < self.hero_tabs.count():
                self.hero_tabs.setCurrentIndex(active_tab)
        except Exception as e:
            self.logger.debug(f"Failed to restore active tab: {e}")

    # Manual layout management methods removed - Qt handles layout automatically

    # Timer-based layout updates removed for performance optimization
    # Qt's native layout system handles responsive updates automatically

    # ===== END_EXTRACT_TO: src/gui/window/dock_manager.py =====

    # ===== END_EXTRACT_TO: src/gui/window/central_widget_manager.py =====

    # --- Dock layout helpers ---
    # ===== END_EXTRACT_TO: src/gui/window/layout_persistence.py =====

    # Layout autosave connections removed - Qt handles layout persistence automatically

    # ---- Layout persistence (auto-save/auto-load) ----
    # JSON settings methods removed - Qt handles layout persistence automatically

    # Layout persistence initialization removed - Qt handles automatically

    # Layout persistence handled automatically by Qt's native dock system

    # Layout persistence handled automatically by Qt's native dock system

    # Layout loading handled automatically by Qt's native dock system
    # ===== END_EXTRACT_TO: src/gui/window/layout_persistence.py =====

    # Layout autosave connections removed - Qt handles layout persistence automatically

    def _trigger_responsive_layout_update(self) -> None:
        """Trigger responsive layout update with debouncing."""
        try:
            if hasattr(self, "_layout_update_timer"):
                self._layout_update_timer.start()
        except Exception as e:
            self.logger.debug(f"Failed to trigger responsive layout update: {e}")

    # Snapping system removed - Qt handles dock management automatically

    def _set_layout_edit_mode(self, enabled: bool, show_message: bool = False) -> None:
        """Toggle Layout Edit Mode: when off, docks are locked; when on, docks movable/floatable.

        Args:
            enabled: Whether to enable layout edit mode
            show_message: Whether to show a status message (default False to avoid initialization artifacts)
        """
        try:
            self.layout_edit_mode = bool(enabled)
            # Use native Qt dock features for layout edit mode
            for dock in self.findChildren(QDockWidget):
                if self.layout_edit_mode:
                    # Enable full dock features for editing
                    dock.setFeatures(
                        QDockWidget.DockWidgetMovable
                        | QDockWidget.DockWidgetFloatable
                        | QDockWidget.DockWidgetClosable
                    )
                else:
                    # Layout locked - only allow closing, no moving or floating
                    dock.setFeatures(QDockWidget.DockWidgetClosable)

            # Persist state for next launch
            settings = QSettings()
            settings.setValue("ui/layout_edit_mode", self.layout_edit_mode)

            # Update status bar indicator
            try:
                self.status_bar_manager.update_layout_edit_mode(self.layout_edit_mode)
            except Exception:
                pass

            # Status feedback - only show message if explicitly requested
            # This prevents overlay artifacts during initialization
            if show_message:
                try:
                    self.statusBar().showMessage(
                        (
                            "Layout Edit Mode ON"
                            if self.layout_edit_mode
                            else "Layout locked"
                        ),
                        2000,
                    )
                except Exception:
                    pass
        except Exception as e:
            self.logger.warning(f"Failed to toggle Layout Edit Mode: {e}")

    # Manual central widget update methods removed - Qt handles layout automatically

    # Dock snapping methods removed - Qt handles dock management automatically

    # Dock layout reset methods removed - Qt handles layout persistence automatically

    # ---- Settings persistence (QSettings) ----
    def _save_lighting_settings(self) -> None:
        """Save current lighting settings to QSettings."""
        try:
            settings = QSettings()
            if hasattr(self, "lighting_manager") and self.lighting_manager:
                props = self.lighting_manager.get_properties()
                settings.setValue("lighting/position_x", float(props["position"][0]))
                settings.setValue("lighting/position_y", float(props["position"][1]))
                settings.setValue("lighting/position_z", float(props["position"][2]))
                settings.setValue("lighting/color_r", float(props["color"][0]))
                settings.setValue("lighting/color_g", float(props["color"][1]))
                settings.setValue("lighting/color_b", float(props["color"][2]))
                settings.setValue("lighting/intensity", float(props["intensity"]))
                settings.setValue(
                    "lighting/cone_angle", float(props.get("cone_angle", 30.0))
                )
                self.logger.debug("Lighting settings saved to QSettings")
        except Exception as e:
            self.logger.warning(f"Failed to save lighting settings: {e}")

    def _load_lighting_settings(self) -> None:
        """Load lighting settings from QSettings and apply to manager and panel."""
        try:
            settings = QSettings()
            if settings.contains("lighting/position_x"):
                pos_x = settings.value("lighting/position_x", 90.0, type=float)
                pos_y = settings.value("lighting/position_y", 90.0, type=float)
                pos_z = settings.value("lighting/position_z", 180.0, type=float)
                col_r = settings.value("lighting/color_r", 1.0, type=float)
                col_g = settings.value("lighting/color_g", 1.0, type=float)
                col_b = settings.value("lighting/color_b", 1.0, type=float)
                intensity = settings.value("lighting/intensity", 1.2, type=float)
                cone_angle = settings.value("lighting/cone_angle", 90.0, type=float)
                props = {
                    "position": (float(pos_x), float(pos_y), float(pos_z)),
                    "color": (float(col_r), float(col_g), float(col_b)),
                    "intensity": float(intensity),
                    "cone_angle": float(cone_angle),
                }
                if hasattr(self, "lighting_manager") and self.lighting_manager:
                    self.lighting_manager.apply_properties(props)
                # Sync to lighting_panel without re-emitting
                try:
                    if hasattr(self, "lighting_panel") and self.lighting_panel:
                        self.lighting_panel.set_values(
                            position=props["position"],
                            color=props["color"],
                            intensity=props["intensity"],
                            cone_angle=props["cone_angle"],
                            emit_signals=False,
                        )
                except Exception:
                    pass
                self.logger.info("Lighting settings loaded from QSettings")
        except Exception as e:
            self.logger.warning(f"Failed to load lighting settings: {e}")

    def _save_lighting_panel_visibility(self) -> None:
        """Lighting panel is now a floating dialog, visibility is not persisted."""
        pass

    def _toggle_lighting_panel(self) -> None:
        """Toggle the lighting control panel visibility."""
        try:
            if hasattr(self, "lighting_panel") and self.lighting_panel:
                if self.lighting_panel.isVisible():
                    self.lighting_panel.hide()
                else:
                    self.lighting_panel.show()
                    self.lighting_panel.raise_()
                    self.lighting_panel.activateWindow()
            else:
                self.logger.warning("Lighting panel not available")
        except Exception as e:
            self.logger.warning(f"Failed to toggle lighting panel: {e}")

    def _update_light_position(self, x: float, y: float, z: float) -> None:
        """Update light position from lighting panel."""
        try:
            if hasattr(self, "lighting_manager") and self.lighting_manager:
                self.lighting_manager.update_position(x, y, z)
                self._save_lighting_settings()
        except Exception as e:
            self.logger.warning(f"Failed to update light position: {e}")

    def _update_light_color(self, r: float, g: float, b: float) -> None:
        """Update light color from lighting panel."""
        try:
            if hasattr(self, "lighting_manager") and self.lighting_manager:
                self.lighting_manager.update_color(r, g, b)
                self._save_lighting_settings()
        except Exception as e:
            self.logger.warning(f"Failed to update light color: {e}")

    def _update_light_intensity(self, value: float) -> None:
        """Update light intensity from lighting panel."""
        try:
            if hasattr(self, "lighting_manager") and self.lighting_manager:
                self.lighting_manager.update_intensity(value)
                self._save_lighting_settings()
        except Exception as e:
            self.logger.warning(f"Failed to update light intensity: {e}")

    def _update_light_cone_angle(self, angle: float) -> None:
        """Update light cone angle from lighting panel."""
        try:
            if hasattr(self, "lighting_manager") and self.lighting_manager:
                self.lighting_manager.update_cone_angle(angle)
                self._save_lighting_settings()
        except Exception as e:
            self.logger.warning(f"Failed to update light cone angle: {e}")

    def _apply_material_species(self, species_name: str) -> None:
        """Apply selected material species to the current model."""
        try:
            if not species_name:
                return

            # Use MaterialLightingIntegrator if available
            if (
                hasattr(self, "material_lighting_integrator")
                and self.material_lighting_integrator
            ):
                self.material_lighting_integrator.apply_material_species(species_name)
            else:
                self.logger.warning(
                    "MaterialLightingIntegrator not available for applying material"
                )
        except Exception as e:
            self.logger.error(f"Failed to apply material species '{species_name}': {e}")

    def _apply_dock_tab_positions(self) -> None:
        """Apply dock tab positions from settings."""
        try:
            from PySide6.QtCore import QSettings
            from PySide6.QtWidgets import QTabWidget

            settings = QSettings()

            # Get tab position settings
            left_pos = settings.value("dock_tabs/left_position", "bottom", type=str)
            right_pos = settings.value("dock_tabs/right_position", "bottom", type=str)

            # Convert to Qt enum
            left_tab_pos = (
                QTabWidget.TabPosition.North
                if left_pos == "top"
                else QTabWidget.TabPosition.South
            )
            right_tab_pos = (
                QTabWidget.TabPosition.North
                if right_pos == "top"
                else QTabWidget.TabPosition.South
            )

            # Apply tab positions
            self.setTabPosition(Qt.LeftDockWidgetArea, left_tab_pos)
            self.setTabPosition(Qt.RightDockWidgetArea, right_tab_pos)

            self.logger.debug(
                f"Applied dock tab positions: Left={left_pos}, Right={right_pos}"
            )

        except Exception as e:
            self.logger.warning(f"Failed to apply dock tab positions: {e}")

    def _reset_dock_layout_and_save(self) -> None:
        """Reset dock layout to default positions and save settings."""
        try:
            self.logger.info("Resetting dock layout to defaults")

            # Reset dock layout using native Qt methods
            # Clear ALL saved layout state
            from PySide6.QtCore import QSettings

            settings = QSettings()

            # Remove ALL layout-related QSettings keys
            layout_keys = [
                "window_geometry",
                "window_state",
                "window/width",
                "window/height",
                "window/x",
                "window/y",
                "window/maximized",
                "window/default_width",
                "window/default_height",
                "ui/layout_edit_mode",
                "metadata_panel/visible",
                "library_panel/visible",
            ]
            for key in layout_keys:
                if settings.contains(key):
                    settings.remove(key)
                    self.logger.debug(f"Cleared QSettings key: {key}")

            # Restore default window size: 50% width, 100% height (snapped to middle wide, full height)
            try:
                from src.core.application_config import ApplicationConfig

                default_width, default_height = (
                    ApplicationConfig.calculate_default_window_size()
                )
                self.resize(default_width, default_height)
                self.logger.info(
                    f"Reset window size to default: {default_width}x{default_height}"
                )
            except Exception as e:
                self.logger.warning(f"Failed to calculate default window size: {e}")
                self.resize(1200, 800)

            # Restore default dock positions
            # Model library to left
            if hasattr(self, "model_library_dock") and self.model_library_dock:
                self.removeDockWidget(self.model_library_dock)
                self.addDockWidget(Qt.LeftDockWidgetArea, self.model_library_dock)

            # Properties and metadata to right, tabified
            if hasattr(self, "properties_dock") and self.properties_dock:
                self.removeDockWidget(self.properties_dock)
                self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)

            if hasattr(self, "metadata_dock") and self.metadata_dock:
                self.removeDockWidget(self.metadata_dock)
                self.addDockWidget(Qt.RightDockWidgetArea, self.metadata_dock)
                # Tabify with properties dock
                try:
                    self.tabifyDockWidget(self.properties_dock, self.metadata_dock)
                except Exception as e:
                    self.logger.debug(f"Could not tabify docks: {e}")

            # Make sure all docks are visible
            if hasattr(self, "model_library_dock") and self.model_library_dock:
                self.model_library_dock.setVisible(True)
            if hasattr(self, "properties_dock") and self.properties_dock:
                self.properties_dock.setVisible(True)
            if hasattr(self, "metadata_dock") and self.metadata_dock:
                self.metadata_dock.setVisible(True)

            # Save the new layout state
            self._save_window_settings()

            self.logger.info("Dock layout reset to defaults and saved")
            self.statusBar().showMessage("Layout reset to defaults", 3000)

        except Exception as e:
            self.logger.error(f"Failed to reset dock layout: {e}")
            self.statusBar().showMessage("Failed to reset layout", 3000)

    def _restore_window_geometry_early(self) -> None:
        """Restore saved window geometry and state during initialization phase.

        This method is called during __init__ to ensure proper timing coordination
        between window creation and state restoration, eliminating race conditions.
        """
        import time

        try:
            settings = QSettings()
            self.logger.debug(
                "FIX: Starting early window geometry restoration during init"
            )

            # Try to restore window geometry (size and position)
            geometry_restored = False
            if settings.contains("window_geometry"):
                geometry_data = settings.value("window_geometry")
                self.logger.info(
                    f"FIX: Found saved window_geometry key, size: {len(geometry_data) if geometry_data else 0} bytes"
                )
                if geometry_data:
                    if self.restoreGeometry(geometry_data):
                        self.logger.info(
                            "FIX: Window geometry restored successfully during init"
                        )
                        geometry_restored = True
                    else:
                        self.logger.debug(
                            "FIX: Failed to restore window geometry during init, trying explicit size"
                        )
            else:
                self.logger.info("FIX: No window_geometry key found in QSettings")

            # Fallback: Use explicit width/height if geometry restoration failed
            if not geometry_restored and settings.contains("window/width"):
                try:
                    # Get default values from config
                    from src.core.application_config import ApplicationConfig

                    config = ApplicationConfig.get_default()
                    default_width, default_height = (
                        ApplicationConfig.calculate_default_window_size()
                    )

                    width = settings.value("window/width", default_width, type=int)
                    height = settings.value("window/height", default_height, type=int)
                    maximized = settings.value("window/maximized", False, type=bool)

                    self.logger.info(
                        f"FIX: Found explicit window size settings: {width}x{height}, maximized={maximized}"
                    )

                    # Ensure dimensions are within reasonable bounds
                    width = max(800, min(width, 3840))  # Cap at 4K width, min 800
                    height = max(600, min(height, 2160))  # Cap at 4K height, min 600

                    self.resize(width, height)
                    self.logger.info(
                        f"FIX: Window resized to {width}x{height} from saved settings"
                    )

                    if maximized:
                        self.showMaximized()
                        self.logger.info("FIX: Window maximized from saved settings")

                    geometry_restored = True
                except Exception as e:
                    self.logger.debug(f"FIX: Failed to restore explicit size: {e}")
            else:
                if not geometry_restored:
                    self.logger.info(
                        "FIX: No explicit window/width key found in QSettings"
                    )

            if not geometry_restored:
                self.logger.debug("FIX: No saved window geometry found, using defaults")

            # Try to restore window state (maximized/normal, dock layout)
            if settings.contains("window_state"):
                state_data = settings.value("window_state")
                self.logger.info(
                    f"FIX: Found saved window_state key, size: {len(state_data) if state_data else 0} bytes"
                )
                if state_data:
                    if self.restoreState(state_data):
                        self.logger.info(
                            "FIX: Window state restored successfully during init"
                        )
                    else:
                        self.logger.debug(
                            "FIX: Failed to restore window state during init, using defaults"
                        )
            else:
                self.logger.info("FIX: No saved window_state key found in QSettings")

            # Handle maximize_on_startup setting if present
            if hasattr(self, "maximize_on_startup") and self.maximize_on_startup:
                self.showMaximized()
                self.logger.info("FIX: Window maximized on startup as configured")

            self.logger.debug("FIX: Early window geometry restoration completed")

        except Exception as e:
            self.logger.warning(f"FAILED to restore window geometry during init: {e}")
            # Don't re-raise - we want initialization to continue even if restoration fails

    def _restore_window_state(self) -> None:
        """Restore saved window geometry and state from QSettings.

        DEPRECATED: This method is kept for compatibility but window geometry
        restoration now happens during initialization via _restore_window_geometry_early().
        This method is only used for manual restoration requests.
        """
        try:
            settings = QSettings()

            # Try to restore window geometry (size and position)
            if settings.contains("window_geometry"):
                geometry_data = settings.value("window_geometry")
                if geometry_data:
                    if self.restoreGeometry(geometry_data):
                        self.logger.info("Window geometry restored successfully")
                    else:
                        self.logger.debug(
                            "Failed to restore window geometry, using defaults"
                        )

            # Try to restore window state (maximized/normal, dock layout)
            if settings.contains("window_state"):
                state_data = settings.value("window_state")
                if state_data:
                    if self.restoreState(state_data):
                        self.logger.info("Window state restored successfully")
                    else:
                        self.logger.debug(
                            "Failed to restore window state, using defaults"
                        )
        except Exception as e:
            self.logger.warning(f"Failed to restore window state: {e}")

    def _save_window_settings(self) -> None:
        """Save current window geometry and dock state."""
        try:
            import sys

            settings = QSettings()

            # Save window geometry and state
            geometry = self.saveGeometry()
            state = self.saveState()

            settings.setValue("window_geometry", geometry)
            settings.setValue("window_state", state)

            # Save window size and position explicitly for reliability
            settings.setValue("window/width", self.width())
            settings.setValue("window/height", self.height())
            settings.setValue("window/x", self.x())
            settings.setValue("window/y", self.y())
            settings.setValue("window/maximized", self.isMaximized())

            msg = f"FIX: Window settings saved: {self.width()}x{self.height()} at ({self.x()},{self.y()}), maximized={self.isMaximized()}"
            self.logger.info(msg)
            print(msg, file=sys.stdout, flush=True)

            msg2 = f"FIX: Saved window_geometry: {len(geometry)} bytes"
            self.logger.info(msg2)
            print(msg2, file=sys.stdout, flush=True)

            msg3 = f"FIX: Saved window_state (dock layout): {len(state)} bytes"
            self.logger.info(msg3)
            print(msg3, file=sys.stdout, flush=True)

            # Save current tab index
            if hasattr(self, "hero_tabs") and self.hero_tabs:
                settings.setValue(
                    "ui/active_hero_tab_index", self.hero_tabs.currentIndex()
                )

            # CRITICAL: Sync settings to disk immediately
            settings.sync()
            msg4 = "FIX: Window settings synced to disk"
            self.logger.info(msg4)
            print(msg4, file=sys.stdout, flush=True)

            # CRITICAL: Flush logger handlers to ensure logs are written immediately
            for handler in self.logger.handlers:
                handler.flush()
        except Exception as e:
            self.logger.error(f"Failed to save window settings: {e}")

    def _setup_periodic_window_state_save(self) -> None:
        """Set up periodic window state saving (every 5 seconds).

        This ensures window position/size is saved periodically, not just on close.
        Protects against data loss if the app crashes.
        """
        try:
            from PySide6.QtCore import QTimer

            # Create timer for periodic saves
            self._window_state_save_timer = QTimer()
            self._window_state_save_timer.timeout.connect(
                self._periodic_save_window_state
            )

            # Save every 5 seconds
            self._window_state_save_timer.start(5000)

            self.logger.debug(
                "Periodic window state save timer started (5 second interval)"
            )
        except Exception as e:
            self.logger.warning(f"Failed to set up periodic window state save: {e}")

    def _periodic_save_window_state(self) -> None:
        """Periodically save window state without verbose logging.

        This is called every 5 seconds to ensure window position/size is saved.
        Uses silent logging to avoid cluttering the logs.
        """
        try:
            settings = QSettings()

            # Save window geometry and state
            geometry = self.saveGeometry()
            state = self.saveState()

            settings.setValue("window_geometry", geometry)
            settings.setValue("window_state", state)

            # Save window size and position explicitly for reliability
            settings.setValue("window/width", self.width())
            settings.setValue("window/height", self.height())
            settings.setValue("window/x", self.x())
            settings.setValue("window/y", self.y())
            settings.setValue("window/maximized", self.isMaximized())

            # Sync to disk
            settings.sync()

            # Silent logging - only log at debug level to avoid spam
            self.logger.debug(
                f"Periodic save: {self.width()}x{self.height()} at ({self.x()},{self.y()})"
            )
        except Exception as e:
            self.logger.warning(f"Failed to periodically save window state: {e}")

    def _on_model_loaded(self, info: str) -> None:
        """Handle model loaded signal from viewer."""
        try:
            self.activity_logger.info(f"Model loaded: {info}")
            self.status_label.setText(f"Model loaded: {info}")
            self.progress_bar.setVisible(False)

            # Clear status after a delay
            QTimer.singleShot(3000, lambda: self.status_label.setText("Ready"))
        except Exception as e:
            self.logger.error(f"Failed to handle model loaded signal: {e}")

    def showEvent(self, event) -> None:
        """Handle window show event - restore geometry and dock layout after window is shown.

        CRITICAL FIX: Window geometry and position restoration must happen AFTER the window
        is shown, not during initialization. Qt's restoreGeometry() doesn't work properly
        until the window is visible on screen.

        CRITICAL FIX: Defer dock layout restoration to prevent recursive repaint errors
        when multiple widgets are being repainted simultaneously during window show.
        """
        import time

        start_time = time.time()

        try:
            # Mark that we've been shown (for any show-specific logic)
            if not hasattr(self, "_window_shown"):
                self._window_shown = True
                self.logger.debug(
                    "FIX: First window show event - deferring geometry and dock restoration"
                )

                # CRITICAL FIX: Defer BOTH geometry and dock layout restoration to next event loop
                # This ensures the window is fully visible before we try to restore its state
                # Use 0ms delay to minimize visible flash while still deferring to event loop
                from PySide6.QtCore import QTimer

                QTimer.singleShot(0, self._deferred_geometry_restoration)
                QTimer.singleShot(0, self._deferred_dock_layout_restoration)
            else:
                self.logger.debug("FIX: Window show event (not first show)")

        except Exception as e:
            self.logger.warning(f"Failed to handle window show event: {e}")

        total_time = time.time() - start_time
        self.logger.debug("showEvent completed in %.3fs", total_time)

        super().showEvent(event)

    def _deferred_geometry_restoration(self) -> None:
        """
        Deferred window geometry restoration after window is shown.

        CRITICAL FIX: This method is called via QTimer.singleShot after the window
        is fully visible. Qt's restoreGeometry() only works properly after the window
        is shown on screen, not during initialization.
        """
        try:
            self.logger.info(
                "FIX: Starting deferred window geometry restoration (after window is shown)"
            )
            settings = QSettings()

            # Try to restore window geometry (size and position)
            geometry_restored = False
            if settings.contains("window_geometry"):
                geometry_data = settings.value("window_geometry")
                self.logger.info(
                    f"FIX: Found saved window_geometry, size: {len(geometry_data) if geometry_data else 0} bytes"
                )
                if geometry_data:
                    if self.restoreGeometry(geometry_data):
                        self.logger.info(
                            "FIX: Window geometry restored successfully (position and size)"
                        )
                        geometry_restored = True
                    else:
                        self.logger.debug(
                            "FIX: Failed to restore window geometry, trying explicit size"
                        )

            # Fallback: Use explicit width/height if geometry restoration failed
            if not geometry_restored and settings.contains("window/width"):
                try:
                    # Get default values from config
                    from src.core.application_config import ApplicationConfig

                    default_width, default_height = (
                        ApplicationConfig.calculate_default_window_size()
                    )

                    width = settings.value("window/width", default_width, type=int)
                    height = settings.value("window/height", default_height, type=int)
                    x_pos = settings.value("window/x", -1, type=int)
                    y_pos = settings.value("window/y", -1, type=int)
                    maximized = settings.value("window/maximized", False, type=bool)

                    self.logger.info(
                        f"FIX: Found explicit window settings: {width}x{height} at ({x_pos},{y_pos}), maximized={maximized}"
                    )

                    # Ensure dimensions are within reasonable bounds
                    width = max(800, min(width, 3840))
                    height = max(600, min(height, 2160))

                    # Move window to saved position if valid
                    if x_pos >= 0 and y_pos >= 0:
                        self.move(x_pos, y_pos)
                        self.logger.info(f"FIX: Window moved to ({x_pos},{y_pos})")

                    # Resize window
                    self.resize(width, height)
                    self.logger.info(f"FIX: Window resized to {width}x{height}")

                    if maximized:
                        self.showMaximized()
                        self.logger.info("FIX: Window maximized from saved settings")

                    geometry_restored = True
                except Exception as e:
                    self.logger.debug(f"FIX: Failed to restore explicit size: {e}")

            if not geometry_restored:
                self.logger.info(
                    "FIX: No saved window geometry found, using current size"
                )

        except Exception as e:
            self.logger.warning(f"FIX: Failed to restore window geometry: {e}")

    def _deferred_dock_layout_restoration(self) -> None:
        """
        Deferred dock layout restoration to prevent recursive repaint errors.

        CRITICAL FIX: This method is called via QTimer.singleShot after the window
        is fully shown to prevent recursive repaint errors when multiple widgets
        are being repainted simultaneously during dock layout restoration.
        """
        try:
            self.logger.debug("CRITICAL FIX: Starting deferred dock layout restoration")

            # Restore dock layout from QSettings
            settings = QSettings()

            # Try window_state first (the actual saved state), then window/dock_state as fallback
            dock_state = settings.value("window_state", None)
            if not dock_state:
                dock_state = settings.value("window/dock_state", None)

            if dock_state:
                # Restore the dock layout
                self.restoreState(dock_state)
                self.logger.debug("CRITICAL FIX: Dock layout restored from QSettings")
            else:
                self.logger.debug("CRITICAL FIX: No saved dock layout found")

        except Exception as e:
            self.logger.warning(f"CRITICAL FIX: Failed to restore dock layout: {e}")

    def closeEvent(self, event) -> None:
        """Handle window close event - save settings before closing.

        FIX: Enhanced to ensure comprehensive window state persistence
        with detailed logging for troubleshooting.
        """
        import time

        start_time = time.time()
        self.logger.info(
            "FIX: Starting enhanced window close sequence with comprehensive state saving"
        )

        # CRITICAL: Stop periodic save timer FIRST
        try:
            if (
                hasattr(self, "_window_state_save_timer")
                and self._window_state_save_timer
            ):
                self._window_state_save_timer.stop()
                self.logger.debug("Periodic window state save timer stopped")
        except Exception as e:
            self.logger.warning(f"Failed to stop periodic save timer: {e}")

        # CRITICAL: Force layout edit mode OFF before closing
        # This ensures the app always closes with layout locked
        try:
            if self.layout_edit_mode:
                self._set_layout_edit_mode(False, show_message=False)
                self.logger.info(
                    "FIX: Layout edit mode forced OFF on application close"
                )
        except Exception as e:
            self.logger.warning(f"Failed to force layout edit mode OFF on close: {e}")

        # CRITICAL: Clean up VTK resources FIRST (before any window destruction)
        # This prevents OpenGL context errors during shutdown
        try:
            vtk_cleanup_start = time.time()
            self.logger.info(
                "FIX: Cleaning up VTK resources early to prevent OpenGL context errors"
            )
            if hasattr(self, "viewer_widget") and self.viewer_widget:
                if hasattr(self.viewer_widget, "cleanup"):
                    self.viewer_widget.cleanup()
                    vtk_cleanup_time = time.time() - vtk_cleanup_start
                    self.logger.info(
                        f"SUCCESS: VTK resources cleaned up early in {vtk_cleanup_time:.3f}s"
                    )
                else:
                    self.logger.debug("No cleanup method found on viewer widget")
            else:
                self.logger.debug("No viewer widget found for VTK cleanup")
        except Exception as e:
            self.logger.warning(f"Failed to cleanup VTK resources early: {e}")

        # Save lighting settings
        try:
            lighting_start = time.time()
            self.logger.info("FIX: Saving lighting settings")
            self._save_lighting_settings()
            lighting_time = time.time() - lighting_start
            self.logger.info(
                f"SUCCESS: Lighting settings saved in {lighting_time:.3f}s"
            )
        except Exception as e:
            self.logger.warning(f"Failed to save lighting settings on close: {e}")

        # Save viewer and window settings (config defaults, not current size)
        try:
            viewer_start = time.time()
            self.logger.info("FIX: Saving viewer and window settings")
            from src.gui.main_window_components.settings_manager import SettingsManager

            settings_mgr = SettingsManager(self)
            settings_mgr.save_viewer_settings()
            settings_mgr.save_window_settings()
            viewer_time = time.time() - viewer_start
            self.logger.info(
                f"SUCCESS: Viewer/window settings saved in {viewer_time:.3f}s"
            )
        except Exception as e:
            self.logger.warning(f"Failed to save viewer/window settings on close: {e}")

        # CRITICAL: Save window geometry and state LAST (most important - must be after SettingsManager)
        try:
            settings_start = time.time()
            self.logger.info(
                "FIX: Saving window geometry and state (size, position, maximized state, dock layout)"
            )
            self._save_window_settings()
            settings_time = time.time() - settings_start
            self.logger.info(
                f"SUCCESS: Window geometry/state saved in {settings_time:.3f}s"
            )
        except Exception as e:
            self.logger.error(
                f"CRITICAL FAILURE: Failed to save window geometry/state on close: {e}"
            )
            # Don't let this prevent closing, but log it as critical

        # Log final window state for debugging
        try:
            final_geometry = self.saveGeometry()
            final_state = self.saveState()
            self.logger.info(
                f"FINAL STATE: Window geometry size: {len(final_geometry)} bytes, state size: {len(final_state)} bytes"
            )
            self.logger.info(
                f"FINAL STATE: Window size: {self.size().width()}x{self.size().height()}, position: {self.pos().x()},{self.pos().y()}"
            )
            self.logger.info(
                f"FINAL STATE: Window maximized: {self.isMaximized()}, minimized: {self.isMinimized()}"
            )
        except Exception as e:
            self.logger.warning(f"Failed to log final window state: {e}")

        total_time = time.time() - start_time
        self.logger.info(
            f"COMPLETE: Window close sequence completed in {total_time:.3f}s - all state saved"
        )

        super().closeEvent(event)

    def _update_metadata_action_state(self) -> None:
        """Enable/disable 'Show Metadata Manager' based on panel visibility."""
        try:
            visible = False
            if hasattr(self, "metadata_dock") and self.metadata_dock:
                visible = bool(self.metadata_dock.isVisible())
            if hasattr(self, "show_metadata_action") and self.show_metadata_action:
                self.show_metadata_action.setEnabled(not visible)
        except Exception:
            pass

    def _save_metadata_panel_visibility(self) -> None:
        """Persist the metadata panel visibility state."""
        try:
            if hasattr(self, "metadata_dock") and self.metadata_dock:
                settings = QSettings()
                vis = bool(self.metadata_dock.isVisible())
                settings.setValue("metadata_panel/visible", vis)
                self.logger.debug(f"Saved metadata panel visibility: {vis}")
        except Exception as e:
            self.logger.warning(f"Failed to save metadata panel visibility: {e}")

    # Old dock creation methods removed - using native Qt dock system

    def _restore_metadata_manager(self) -> None:
        """Restore and show the Metadata Manager panel if it was closed or missing."""
        try:
            # Native Qt dock system handles restoration automatically
            if hasattr(self, "metadata_dock") and self.metadata_dock:
                self.metadata_dock.show()
                self.metadata_dock.raise_()
                self.statusBar().showMessage("Metadata Manager restored", 2000)
            else:
                self.logger.warning("Metadata dock not available")
        except Exception as e:
            self.logger.error(f"Failed to restore Metadata Manager: {e}")

    # Old dock creation methods removed - using native Qt dock system

    def _restore_model_library(self) -> None:
        """Restore and show the Model Library panel if it was closed or missing."""
        try:
            # Native Qt dock system handles restoration automatically
            if hasattr(self, "model_library_dock") and self.model_library_dock:
                self.model_library_dock.show()
                self.model_library_dock.raise_()
                self.statusBar().showMessage("Model Library restored", 2000)
            else:
                self.logger.warning("Model Library dock not available")
        except Exception as e:
            self.logger.error(f"Failed to restore Model Library: {e}")

    def _update_library_action_state(self) -> None:
        """Enable/disable 'Show Model Library' based on panel visibility."""
        try:
            visible = False
            if hasattr(self, "model_library_dock") and self.model_library_dock:
                visible = bool(self.model_library_dock.isVisible())
            if (
                hasattr(self, "show_model_library_action")
                and self.show_model_library_action
            ):
                self.show_model_library_action.setEnabled(not visible)
        except Exception:
            pass

        # TODO: Add material roughness/metallic sliders in picker
        # TODO: Add export material presets feature

    def _on_model_imported_during_import(self, model_id: int) -> None:
        """
        Handle individual model import completion during batch import.

        This is called after each model is successfully imported, allowing
        the model library to update in real-time instead of waiting for all imports.

        Args:
            model_id: Database ID of the imported model
        """
        try:
            # Refresh model library to show the newly imported model
            if hasattr(self, "model_library_widget") and self.model_library_widget:
                self.model_library_widget._load_models_from_database()
                self.logger.debug(f"Model library refreshed for model ID: {model_id}")
        except Exception as e:
            self.logger.error(f"Failed to refresh model library for model {model_id}: {e}")

    def _import_models(self) -> None:
        """Show the import models dialog."""
        try:
            from src.gui.import_components.import_dialog import ImportDialog
            from src.core.root_folder_manager import RootFolderManager
            from src.core.database.import_migration import migrate_import_schema

            # Ensure database schema is migrated
            db_manager = get_database_manager()
            success, error = migrate_import_schema(db_manager)
            if not success:
                self.logger.warning(f"Database migration warning: {error}")

            # Create and show import dialog
            root_folder_mgr = RootFolderManager.get_instance()
            dialog = ImportDialog(self, root_folder_mgr)

            if dialog.exec():
                # Import completed successfully
                import_result = dialog.get_import_result()
                if import_result:
                    self.activity_logger.info(
                        f"Import completed: {import_result.processed_files} files imported"
                    )
                    self.status_label.setText(
                        f"Import complete: {import_result.processed_files} file(s) imported"
                    )

                    # Final refresh to ensure everything is up to date
                    # (Individual models were already added during import via _on_model_imported_during_import)
                    if (
                        hasattr(self, "model_library_widget")
                        and self.model_library_widget
                    ):
                        self.model_library_widget._load_models_from_database()

                    # Clear status after delay
                    QTimer.singleShot(5000, lambda: self.status_label.setText("Ready"))

        except Exception as e:
            self.logger.error(f"Failed to show import dialog: {e}", exc_info=True)
            QMessageBox.critical(
                self, "Import Error", f"Failed to open import dialog:\n\n{str(e)}"
            )

    # Menu action handlers

    def _reload_stylesheet_action(self) -> None:
        """Reload and re-apply the Material Design theme."""
        # Theme is managed by ThemeService and applied globally
        self.logger.info("Theme is managed by Material Design system")
        self.statusBar().showMessage("Material Design theme active", 2000)

    # ===== END_EXTRACT_TO: src/gui/model/model_loader.py =====

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
                file_path = model["file_path"]
                self.logger.info(f"Loading model from library: {file_path}")

                # Update status
                from pathlib import Path

                filename = Path(file_path).name
                self.status_label.setText(f"Loading: {filename}")
                self.progress_bar.setVisible(True)
                self.progress_bar.setRange(0, 0)  # Indeterminate progress

                # Store model ID for save view functionality
                self.current_model_id = model_id

                # Load the model using the model loader
                self.model_loader_manager.load_stl_model(file_path)

                # After model loads, restore saved camera orientation if available
                QTimer.singleShot(500, lambda: self._restore_saved_camera(model_id))
            else:
                self.logger.warning(f"Model with ID {model_id} not found in database")

        except Exception as e:
            self.logger.error(f"Failed to handle model double-click: {str(e)}")

    # ===== END_EXTRACT_TO: src/gui/model/model_loader.py =====

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

            # Start background hasher to process new models
            self._start_background_hasher()

            # Clear status after a delay
            QTimer.singleShot(3000, lambda: self.status_label.setText("Ready"))

    def _on_model_selected(self, model_id: int) -> None:
        """
        Handle model selection from the model library.

        Synchronizes the metadata tab to display the selected model's metadata.
        Also updates the project details widget.

        Args:
            model_id: ID of the selected model
        """
        try:
            # Store the current model ID
            self.current_model_id = model_id

            # Enable the Edit Model action
            if hasattr(self.menu_manager, "edit_model_action"):
                self.menu_manager.edit_model_action.setEnabled(True)
            if hasattr(self.toolbar_manager, "edit_model_action"):
                self.toolbar_manager.edit_model_action.setEnabled(True)

            # Update project details widget
            if hasattr(self, "project_details_widget"):
                db_manager = get_database_manager()
                model_data = db_manager.get_model(model_id)
                if model_data:
                    self.project_details_widget.set_model(model_data)

            # Synchronize metadata tab to selected model
            self._sync_metadata_to_selected_model(model_id)

            self.logger.debug(f"Model selected: {model_id}")

        except Exception as e:
            self.logger.error(f"Failed to handle model selection: {e}")

    def _sync_metadata_to_selected_model(self, model_id: int) -> None:
        """
        Synchronize the metadata tab to display the selected model's metadata.

        This method ensures that when a model is selected in the library,
        the metadata editor widget is updated to show that model's metadata.

        Args:
            model_id: ID of the selected model
        """
        try:
            # Check if metadata editor exists
            if not hasattr(self, "metadata_editor") or self.metadata_editor is None:
                self.logger.debug(f"Metadata editor not available for model {model_id}")
                return

            # Load metadata for the selected model
            self.metadata_editor.load_model_metadata(model_id)
            self.logger.debug(f"Metadata synchronized for model {model_id}")

            # Switch to metadata tab to show the loaded metadata
            if hasattr(self, "metadata_tabs") and self.metadata_tabs:
                self.metadata_tabs.setCurrentIndex(0)  # Switch to Metadata tab
                self.logger.debug(f"Switched to Metadata tab for model {model_id}")

        except Exception as e:
            self.logger.warning(
                f"Failed to synchronize metadata for model {model_id}: {e}"
            )

    def _edit_model(self) -> None:
        """Analyze the currently selected model for errors."""
        try:
            # Check if a model is currently selected
            if not hasattr(self, "current_model_id") or self.current_model_id is None:
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.information(
                    self,
                    "No Model Selected",
                    "Please select a model from the library first.",
                )
                return

            # Get the model from database
            db_manager = get_database_manager()
            model_data = db_manager.get_model(self.current_model_id)

            if not model_data:
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.warning(self, "Error", "Model not found in database")
                return

            # Load the model file
            file_path = model_data.get("file_path")
            if not file_path:
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.warning(self, "Error", "Model file path not found")
                return

            # Load full geometry (not just metadata) for analysis
            model_cache = get_model_cache()
            cached_model = model_cache.get(file_path, CacheLevel.GEOMETRY_FULL)
            if cached_model and cached_model.triangles:
                model = cached_model
            else:
                # Load full geometry from file
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
                    from PySide6.QtWidgets import QMessageBox

                    QMessageBox.critical(
                        self, "Error", f"Unsupported model format: {fmt}"
                    )
                    return

                model = parser.parse_file(file_path)
                if model:
                    # Cache the full geometry for future use
                    model_cache.put(file_path, CacheLevel.GEOMETRY_FULL, model)

            # Validate model has geometry (either triangles or array-based)
            if not model or (not model.triangles and not model.vertex_array):
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.critical(
                    self, "Error", f"Failed to load model geometry: {file_path}"
                )
                return

            # Open model analyzer dialog
            from src.gui.model_editor.model_analyzer_dialog import ModelAnalyzerDialog

            dialog = ModelAnalyzerDialog(model, file_path, self)

            if dialog.exec() == 1:  # QDialog.Accepted
                # Model was fixed and saved, reload it
                self.activity_logger.info(f"Model analyzed and fixed")
                # Reload the model in the viewer
                self._on_model_double_clicked(self.current_model_id)

        except Exception as e:
            self.logger.error(f"Failed to analyze model: {e}")
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Error", f"Failed to analyze model: {str(e)}")

    def _start_background_hasher(self) -> None:
        """Start the background hasher thread to process unhashed models."""
        try:
            # Use the status bar manager's background hasher if available
            if hasattr(self.status_bar_manager, "start_background_hasher"):
                self.status_bar_manager.start_background_hasher()
                self.logger.info("Background hasher started via status bar manager")
            else:
                self.logger.warning(
                    "Status bar manager does not have start_background_hasher method"
                )
        except Exception as e:
            self.logger.error(f"Failed to start background hasher: {e}")

    def _connect_model_library_status_updates(self) -> None:
        """Connect model library progress updates to main window status bar."""
        try:
            if not hasattr(self.model_library_widget, "model_loader"):
                return

            # We need to monitor the model loader when it's created
            # Store reference to original _load_models method
            original_load_models = self.model_library_widget._load_models

            def _load_models_with_status_update(file_paths):
                """Wrapper to connect status updates when loading starts."""
                # Call original method
                original_load_models(file_paths)

                # Connect progress signals if model_loader exists
                if (
                    hasattr(self.model_library_widget, "model_loader")
                    and self.model_library_widget.model_loader
                ):
                    try:
                        self.model_library_widget.model_loader.progress_updated.connect(
                            self._on_model_library_progress
                        )
                    except Exception as e:
                        self.logger.debug(f"Could not connect progress signal: {e}")

            # Replace the method
            self.model_library_widget._load_models = _load_models_with_status_update

            self.logger.debug("Model library status updates connected")
        except Exception as e:
            self.logger.warning(f"Failed to connect model library status updates: {e}")

    def _on_model_library_progress(self, progress_percent: float, message: str) -> None:
        """Handle progress updates from model library."""
        try:
            # Update main window status bar
            if hasattr(self, "status_label"):
                # Get total files from model loader if available
                if (
                    hasattr(self.model_library_widget, "model_loader")
                    and self.model_library_widget.model_loader
                ):
                    total_files = len(self.model_library_widget.model_loader.file_paths)
                    current_item = int((progress_percent / 100.0) * total_files) + 1
                    current_item = min(current_item, total_files)

                    if total_files > 1:
                        status_text = f"{message} ({current_item} of {total_files} = {int(progress_percent)}%)"
                    else:
                        status_text = f"{message} ({int(progress_percent)}%)"
                else:
                    status_text = f"{message} ({int(progress_percent)}%)"

                self.status_label.setText(status_text)

            # Update progress bar
            if hasattr(self, "progress_bar"):
                self.progress_bar.setVisible(True)
                self.progress_bar.setRange(0, 100)
                self.progress_bar.setValue(int(progress_percent))
        except Exception as e:
            self.logger.debug(f"Failed to update status from model library: {e}")

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
            if hasattr(self, "model_library_widget"):
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

    def _on_project_opened(self, project_id: str) -> None:
        """
        Handle project opened event from project manager.

        Args:
            project_id: ID of the opened project
        """
        try:
            self.logger.info(f"Project opened: {project_id}")
            self.status_label.setText(f"Project opened: {project_id}")

            # Set current project for all tabs that support tab data save/load
            if hasattr(self, "clo_widget") and self.clo_widget:
                try:
                    self.clo_widget.set_current_project(project_id)
                    self.logger.debug(
                        f"Set current project for Cut List Optimizer: {project_id}"
                    )
                except Exception as e:
                    self.logger.warning(
                        f"Failed to set project for Cut List Optimizer: {e}"
                    )

            if (
                hasattr(self, "feeds_and_speeds_widget")
                and self.feeds_and_speeds_widget
            ):
                try:
                    self.feeds_and_speeds_widget.set_current_project(project_id)
                    self.logger.debug(
                        f"Set current project for Feed and Speed: {project_id}"
                    )
                except Exception as e:
                    self.logger.warning(
                        f"Failed to set project for Feed and Speed: {e}"
                    )

            if hasattr(self, "cost_estimator_widget") and self.cost_estimator_widget:
                try:
                    self.cost_estimator_widget.set_current_project(project_id)
                    self.logger.debug(
                        f"Set current project for Cost Estimator: {project_id}"
                    )
                except Exception as e:
                    self.logger.warning(
                        f"Failed to set project for Cost Estimator: {e}"
                    )

            QTimer.singleShot(3000, lambda: self.status_label.setText("Ready"))

        except Exception as e:
            self.logger.error(f"Failed to handle project opened event: {str(e)}")

    def _on_project_created(self, project_id: str) -> None:
        """
        Handle project created event from project manager.

        Args:
            project_id: ID of the created project
        """
        try:
            self.logger.info(f"Project created: {project_id}")
            self.status_label.setText(f"Project created: {project_id}")
            QTimer.singleShot(3000, lambda: self.status_label.setText("Ready"))

        except Exception as e:
            self.logger.error(f"Failed to handle project created event: {str(e)}")

    def _on_project_deleted(self, project_id: str) -> None:
        """
        Handle project deleted event from project manager.

        Args:
            project_id: ID of the deleted project
        """
        try:
            self.logger.info(f"Project deleted: {project_id}")
            self.status_label.setText(f"Project deleted: {project_id}")
            QTimer.singleShot(3000, lambda: self.status_label.setText("Ready"))

        except Exception as e:
            self.logger.error(f"Failed to handle project deleted event: {str(e)}")

    def _update_project_manager_action_state(self) -> None:
        """Update project manager action state based on dock visibility."""
        try:
            if hasattr(self, "project_manager_dock"):
                # Update menu action if it exists
                if hasattr(self, "toggle_project_manager_action"):
                    self.toggle_project_manager_action.setChecked(
                        self.project_manager_dock.isVisible()
                    )

        except Exception as e:
            self.logger.debug(f"Failed to update project manager action state: {e}")

    def _show_preferences(self) -> None:
        """Show preferences dialog."""
        self.logger.info("Opening preferences dialog")
        dlg = PreferencesDialog(self, on_reset_layout=self._reset_dock_layout_and_save)
        # Connect theme change signal to update main window stylesheet
        dlg.theme_changed.connect(self._on_theme_changed)
        # Connect viewer settings change signal to update VTK scene
        dlg.viewer_settings_changed.connect(self._on_viewer_settings_changed)
        # Connect AI settings change signal to reload AI service
        dlg.ai_settings_changed.connect(self._on_ai_settings_changed)
        dlg.exec_()

    def _on_theme_changed(self) -> None:
        """Handle theme change from preferences dialog."""
        # Qt-material handles theme changes automatically through the application
        # No need to manually update main window stylesheet
        self.logger.debug("Theme changed - qt-material handling automatically")

        # Update theme button icon
        self.status_bar_manager._update_theme_icon()

    def _on_viewer_settings_changed(self) -> None:
        """Handle viewer settings change from preferences dialog."""
        try:
            self.logger.info("=== VIEWER SETTINGS CHANGED SIGNAL RECEIVED ===")

            if not hasattr(self, "viewer_widget"):
                self.logger.error("ERROR: Main window has no viewer_widget attribute")
                return

            if not self.viewer_widget:
                self.logger.error("ERROR: viewer_widget is None")
                return

            self.logger.info(f"viewer_widget type: {type(self.viewer_widget).__name__}")
            self.logger.info(
                f"viewer_widget has scene_manager: {hasattr(self.viewer_widget, 'scene_manager')}"
            )

            # Reload settings from QSettings and apply them
            if hasattr(self.viewer_widget, "scene_manager"):
                try:
                    scene_manager = self.viewer_widget.scene_manager
                    self.logger.info(
                        f"scene_manager type: {type(scene_manager).__name__}"
                    )

                    # Reload all settings from QSettings
                    if hasattr(scene_manager, "reload_settings_from_qsettings"):
                        self.logger.info(
                            "Calling scene_manager.reload_settings_from_qsettings()"
                        )
                        scene_manager.reload_settings_from_qsettings()
                        self.logger.info(
                            "✓ Viewer settings reloaded and applied successfully"
                        )
                    else:
                        self.logger.warning(
                            "WARNING: scene_manager has no reload_settings_from_qsettings method"
                        )
                        # Fallback to just rendering
                        if hasattr(scene_manager, "render"):
                            scene_manager.render()
                            self.logger.info("Fallback: Scene re-rendered")

                except Exception as e:
                    self.logger.error(
                        f"ERROR in scene_manager path: {e}", exc_info=True
                    )
            else:
                self.logger.warning(
                    "WARNING: viewer_widget has no scene_manager attribute"
                )

                # Also try direct render if available
                if hasattr(self.viewer_widget, "render"):
                    try:
                        self.viewer_widget.render()
                        self.logger.info("Fallback: Viewer re-rendered directly")
                    except Exception as e:
                        self.logger.error(f"ERROR in direct render: {e}")

            self.logger.info("=== VIEWER SETTINGS CHANGE HANDLING COMPLETE ===")
        except Exception as e:
            self.logger.error(
                f"FATAL ERROR applying viewer settings: {e}", exc_info=True
            )

    def _on_ai_settings_changed(self) -> None:
        """Handle AI settings change from preferences dialog."""
        try:
            self.logger.info("=== AI SETTINGS CHANGED SIGNAL RECEIVED ===")

            # Reload AI service with new settings
            if self.ai_service:
                self.logger.info("Reloading AI service configuration...")
                # Reload config from QSettings
                self.ai_service.config = self.ai_service._load_config()
                # Re-initialize providers with new config
                self.ai_service._initialize_providers()
                self.logger.info(
                    f"✓ AI service reloaded. Available providers: {list(self.ai_service.providers.keys())}"
                )
            else:
                self.logger.warning("AI service not available, skipping reload")

            self.logger.info("=== AI SETTINGS CHANGE HANDLING COMPLETE ===")
        except Exception as e:
            self.logger.error(f"ERROR reloading AI service: {e}", exc_info=True)

    def _show_theme_manager(self) -> None:
        """Show the Theme Manager dialog and hook apply signal."""
        try:
            from src.gui.theme import ThemeDialog

            dlg = ThemeDialog(self)
            dlg.theme_applied.connect(self._on_theme_applied)
            dlg.exec()
        except Exception as e:
            self.logger.error(f"Failed to open Theme Manager: {e}")
            QMessageBox.warning(
                self, "Theme Manager", f"Failed to open Theme Manager:\n{e}"
            )

    def _on_theme_applied(self, preset_name: str) -> None:
        """Handle theme change notification."""
        # Theme is managed by ThemeService and applied globally
        self.logger.info(f"Theme changed: {preset_name}")

    def _zoom_in(self) -> None:
        """Handle zoom in action."""
        self.logger.debug("Zoom in requested")
        self.status_label.setText("Zoomed in")

        # Forward to viewer widget if available
        if hasattr(self.viewer_widget, "zoom_in"):
            self.viewer_widget.zoom_in()
        else:
            QTimer.singleShot(2000, lambda: self.status_label.setText("Ready"))

    def _zoom_out(self) -> None:
        """Handle zoom out action."""
        self.logger.debug("Zoom out requested")
        self.status_label.setText("Zoomed out")

        # Forward to viewer widget if available
        if hasattr(self.viewer_widget, "zoom_out"):
            self.viewer_widget.zoom_out()
        else:
            QTimer.singleShot(2000, lambda: self.status_label.setText("Ready"))

    def _reset_view(self) -> None:
        """Handle reset view action."""
        self.logger.debug("Reset view requested")
        self.status_label.setText("View reset")

        # Forward to viewer widget if available
        if hasattr(self.viewer_widget, "reset_view"):
            self.viewer_widget.reset_view()
            # Reset save view button when view is reset
            try:
                if hasattr(self.viewer_widget, "reset_save_view_button"):
                    self.viewer_widget.reset_save_view_button()
            except Exception as e:
                self.logger.warning(f"Failed to reset save view button: {e}")
        else:
            QTimer.singleShot(2000, lambda: self.status_label.setText("Ready"))

    def _cycle_theme(self) -> None:
        """Cycle through Light, Dark, and System themes."""
        try:
            from src.gui.theme.simple_service import ThemeService

            service = ThemeService.instance()

            # Get current theme
            current_theme, _ = service.get_current_theme()

            # Define theme cycle
            themes = ["light", "dark", "auto"]
            current_index = (
                themes.index(current_theme) if current_theme in themes else 0
            )
            next_index = (current_index + 1) % len(themes)
            next_theme = themes[next_index]

            # Apply next theme
            service.apply_theme(next_theme, "qt-material")

            # Update status
            theme_names = {"light": "Light", "dark": "Dark", "auto": "System"}
            self.status_label.setText(
                f"Theme: {theme_names.get(next_theme, next_theme)}"
            )
            QTimer.singleShot(2000, lambda: self.status_label.setText("Ready"))

            # Update theme button icon
            self.status_bar_manager._update_theme_icon()

            self.logger.info(f"Cycled theme from {current_theme} to {next_theme}")

        except Exception as e:
            self.logger.error(f"Failed to cycle theme: {e}")
            self.status_label.setText("Theme cycle failed")
            QTimer.singleShot(2000, lambda: self.status_label.setText("Ready"))

    def _save_current_view(self) -> None:
        """Save the current camera view for the loaded model."""
        try:
            # Check if a model is currently loaded
            if (
                not hasattr(self.viewer_widget, "current_model")
                or not self.viewer_widget.current_model
            ):
                QMessageBox.information(
                    self, "Save View", "No model is currently loaded."
                )
                return

            # Get the model ID from the current model
            model = self.viewer_widget.current_model
            if not hasattr(model, "file_path") or not model.file_path:
                QMessageBox.warning(
                    self, "Save View", "Cannot save view: model file path not found."
                )
                return

            # Find the model ID in the database by file path
            db_manager = get_database_manager()
            models = db_manager.get_all_models()
            model_id = None
            for m in models:
                if m.get("file_path") == model.file_path:
                    model_id = m.get("id")
                    break

            if not model_id:
                QMessageBox.warning(self, "Save View", "Model not found in database.")
                return

            # Get camera state from viewer
            if hasattr(self.viewer_widget, "renderer"):
                camera = self.viewer_widget.renderer.GetActiveCamera()
                if camera:
                    pos = camera.GetPosition()
                    focal = camera.GetFocalPoint()
                    view_up = camera.GetViewUp()

                    camera_data = {
                        "position_x": pos[0],
                        "position_y": pos[1],
                        "position_z": pos[2],
                        "focal_x": focal[0],
                        "focal_y": focal[1],
                        "focal_z": focal[2],
                        "view_up_x": view_up[0],
                        "view_up_y": view_up[1],
                        "view_up_z": view_up[2],
                    }

                    # Save to database
                    success = db_manager.save_camera_orientation(model_id, camera_data)

                    if success:
                        self.status_label.setText("View saved for this model")
                        self.logger.info(f"Saved camera view for model ID {model_id}")
                        # Reset save view button after successful save
                        try:
                            if hasattr(self.viewer_widget, "reset_save_view_button"):
                                self.viewer_widget.reset_save_view_button()
                        except Exception as e:
                            self.logger.warning(
                                f"Failed to reset save view button: {e}"
                            )
                        QTimer.singleShot(
                            3000, lambda: self.status_label.setText("Ready")
                        )
                    else:
                        QMessageBox.warning(
                            self, "Save View", "Failed to save view to database."
                        )
                else:
                    QMessageBox.warning(self, "Save View", "Camera not available.")
            else:
                QMessageBox.warning(self, "Save View", "Viewer not initialized.")

        except Exception as e:
            self.logger.error(f"Failed to save current view: {e}")
            QMessageBox.warning(self, "Save View", f"Failed to save view: {str(e)}")

    def _restore_saved_camera(self, model_id: int) -> None:
        """Restore saved camera orientation for a model."""
        try:
            db_manager = get_database_manager()
            camera_data = db_manager.get_camera_orientation(model_id)

            if camera_data and hasattr(self.viewer_widget, "renderer"):
                camera = self.viewer_widget.renderer.GetActiveCamera()
                if camera:
                    # Restore camera position, focal point, and view up
                    camera.SetPosition(
                        camera_data["camera_position_x"],
                        camera_data["camera_position_y"],
                        camera_data["camera_position_z"],
                    )
                    camera.SetFocalPoint(
                        camera_data["camera_focal_x"],
                        camera_data["camera_focal_y"],
                        camera_data["camera_focal_z"],
                    )
                    camera.SetViewUp(
                        camera_data["camera_view_up_x"],
                        camera_data["camera_view_up_y"],
                        camera_data["camera_view_up_z"],
                    )

                    # Update clipping range and render
                    self.viewer_widget.renderer.ResetCameraClippingRange()
                    self.viewer_widget.vtk_widget.GetRenderWindow().Render()

                    self.logger.info(
                        f"Restored saved camera view for model ID {model_id}"
                    )
                    self.status_label.setText("Restored saved view")
                    QTimer.singleShot(2000, lambda: self.status_label.setText("Ready"))
            else:
                self.logger.debug(f"No saved camera view for model ID {model_id}")

        except Exception as e:
            self.logger.warning(f"Failed to restore saved camera: {e}")

    def _show_help(self) -> None:
        """Show searchable help dialog."""
        try:
            from src.gui.help_system import HelpDialog

            help_dialog = HelpDialog(self)
            help_dialog.exec()
        except Exception as e:
            self.logger.error(f"Error showing help dialog: {e}")
            QMessageBox.warning(self, "Help Error", f"Could not open help system: {e}")

    def _show_about(self) -> None:
        """Show about dialog."""
        self.logger.info("Showing about dialog")

        about_text = (
            "<h3>Digital Workshop</h3>"
            "<p>Version 1.0.0</p>"
            "<p>A desktop application for managing and viewing 3D models.</p>"
            "<p><b>Supported formats:</b> STL, OBJ, STEP, MF3</p>"
            "<p><b>Requirements:</b> Windows 7+, Python 3.8+, PySide5</p>"
            "<br>"
            "<p>&copy; 2023 Digital Workshop Development Team</p>"
        )

        QMessageBox.about(self, "About Digital Workshop", about_text)

    def _generate_library_screenshots(self) -> None:
        """Generate thumbnails for all models in the library with applied materials."""
        try:
            from src.gui.thumbnail_generation_coordinator import ThumbnailGenerationCoordinator
            from src.core.application_config import ApplicationConfig
            from src.core.database_manager import get_database_manager

            # Get all models from database
            db_manager = get_database_manager()
            models = db_manager.get_all_models()

            if not models:
                QMessageBox.information(
                    self,
                    "No Models",
                    "No models found in the library. Import some models first.",
                )
                return

            # Load thumbnail settings
            config = ApplicationConfig.get_default()
            bg_image = config.thumbnail_bg_image
            material = config.thumbnail_material

            # Build file info list: (file_path, file_hash)
            file_info_list = []
            for model in models:
                file_path = model.get("file_path")
                file_hash = model.get("file_hash")
                if file_path and file_hash and Path(file_path).exists():
                    file_info_list.append((file_path, file_hash))

            if not file_info_list:
                QMessageBox.warning(
                    self,
                    "No Valid Models",
                    "No valid model files found. Check that model files still exist.",
                )
                return

            # Create coordinator and generate thumbnails
            coordinator = ThumbnailGenerationCoordinator(parent=self)
            coordinator.generate_thumbnails(
                file_info_list=file_info_list,
                background=bg_image,
                material=material,
            )

            # Connect completion signal to reload library
            coordinator.generation_completed.connect(self._on_library_thumbnails_completed)

            self.logger.info(f"Started thumbnail generation for {len(file_info_list)} models")

        except Exception as e:
            self.logger.error(f"Failed to start thumbnail generation: {e}")
            QMessageBox.critical(
                self,
                "Thumbnail Generation Error",
                f"Failed to start thumbnail generation:\n{e}",
            )

    def _on_screenshot_progress(self, current: int, total: int) -> None:
        """Handle screenshot generation progress."""
        try:
            if total > 0:
                progress = int((current / total) * 100)
                self.progress_bar.setValue(progress)
                self.status_label.setText(f"Generating screenshots: {current}/{total}")
        except Exception as e:
            self.logger.warning(f"Failed to update progress: {e}")

    def _on_screenshot_generated(self, model_id: int, screenshot_path: str) -> None:
        """Handle screenshot generated event."""
        try:
            self.logger.debug(
                f"Screenshot generated for model {model_id}: {screenshot_path}"
            )
        except Exception as e:
            self.logger.warning(f"Failed to handle screenshot generated event: {e}")

    def _on_screenshot_error(self, error_message: str) -> None:
        """Handle screenshot generation error."""
        try:
            self.logger.error(f"Screenshot generation error: {error_message}")
            self.status_label.setText(f"Error: {error_message}")
        except Exception as e:
            self.logger.warning(f"Failed to handle screenshot error: {e}")

    def _on_screenshots_finished(self) -> None:
        """Handle batch screenshot generation completion."""
        try:
            self.progress_bar.setVisible(False)
            self.status_label.setText("Screenshots generated successfully")

            # Reload model library to display new thumbnails
            if hasattr(self, "model_library_widget") and self.model_library_widget:
                self.model_library_widget._load_models_from_database()

            QMessageBox.information(
                self,
                "Screenshot Generation Complete",
                "All model screenshots have been generated successfully!",
            )

            self.logger.info("Batch screenshot generation completed")

            # Clear status after a delay
            QTimer.singleShot(3000, lambda: self.status_label.setText("Ready"))

        except Exception as e:
            self.logger.error(f"Failed to handle screenshots finished event: {e}")

    def _on_library_thumbnails_completed(self) -> None:
        """Handle library thumbnail generation completion."""
        try:
            # Reload model library to display new thumbnails
            if hasattr(self, "model_library_widget") and self.model_library_widget:
                self.model_library_widget._load_models_from_database()

            self.logger.info("Library thumbnail generation completed")

        except Exception as e:
            self.logger.error(f"Failed to handle library thumbnails completion: {e}")

    def _toggle_maximize(self) -> None:
        """Toggle window maximize/restore state."""
        try:
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()
        except Exception as e:
            self.logger.warning(f"Failed to toggle maximize: {e}")

    def _on_tab_switch_requested(self, tab_name: str) -> None:
        """Handle tab switch request from project manager."""
        try:
            # Map tab names to indices - must match actual tab names added in _add_placeholder_tabs
            tab_map = {
                "Model Previewer": 0,
                "G Code Previewer": 1,
                "Cut List Optimizer": 2,
                "Feed and Speed": 3,  # Note: actual tab name is "Feed and Speed" not "Feeds & Speeds"
                "Project Cost Estimator": 4,
            }

            tab_index = tab_map.get(tab_name)
            if tab_index is not None and hasattr(self, "hero_tabs"):
                self.hero_tabs.setCurrentIndex(tab_index)
                self.logger.info(f"Switched to tab: {tab_name}")
            else:
                self.logger.warning(f"Unknown tab name: {tab_name}")

        except Exception as e:
            self.logger.error(f"Failed to switch tab: {e}")

    def _snap_dock_to_edge(self, dock: QDockWidget, edge: str) -> None:
        """Snap a floating dock widget to the specified edge of the main window.

        Args:
            dock: The dock widget to snap
            edge: The edge to snap to ('left', 'right', 'top', 'bottom')
        """
        try:
            area_map = {
                "left": Qt.LeftDockWidgetArea,
                "right": Qt.RightDockWidgetArea,
                "top": Qt.TopDockWidgetArea,
                "bottom": Qt.BottomDockWidgetArea,
            }
            target_area = area_map.get(edge)
            if target_area is None:
                self.logger.warning(f"Invalid snap edge: {edge}")
                return

            # Check if this dock is allowed to dock to the target area
            allowed = dock.allowedAreas()
            if not (allowed & target_area):
                self.logger.debug(
                    f"Dock {dock.windowTitle()} not allowed in {edge} area"
                )
                return

            # Perform the snap operation
            dock.setFloating(False)
            self.addDockWidget(target_area, dock)
            dock.raise_()

            self.logger.info(f"Snapped dock '{dock.windowTitle()}' to {edge} area")

            # Save the new layout
            self._save_window_settings()

        except Exception as e:
            self.logger.warning(f"Failed to snap dock to {edge}: {e}")

    def _register_dock_for_snapping(self, dock: QDockWidget) -> None:
        """Register a dock widget for snapping functionality.

        This sets up the visual feedback and snapping behavior when dragging
        floating dock widgets near the main window edges.

        Args:
            dock: The dock widget to register for snapping
        """
        try:
            # Initialize snap system if not already done
            if not hasattr(self, "_snap_layer"):
                self._snap_layer, self._snap_handlers = setup_dock_snapping(
                    self, self.logger
                )
                self.logger.debug("Initialized dock snapping system")

            # Create and register the drag handler for this dock
            handler = DockDragHandler(self, dock, self._snap_layer, self.logger)

            # Store handler reference
            if not hasattr(self, "_snap_handlers"):
                self._snap_handlers = {}
            self._snap_handlers[dock.objectName() or id(dock)] = handler

            # Install the event filter on the dock widget
            dock.installEventFilter(handler)

            self.logger.debug(f"Registered dock '{dock.windowTitle()}' for snapping")

        except Exception as e:
            self.logger.warning(f"Failed to register dock for snapping: {e}")

    # ===== END_EXTRACT_TO: src/gui/materials/integration.py =====

    # ===== END_EXTRACT_TO: src/gui/materials/integration.py =====

    # ===== END_EXTRACT_TO: src/gui/services/background_processor.py =====

    # ===== END_EXTRACT_TO: src/gui/core/event_coordinator.py =====
