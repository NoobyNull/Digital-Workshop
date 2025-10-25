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
    Qt, QSize, QTimer, Signal, QStandardPaths, QSettings, QEvent, QObject,
    QPoint, QRect
)
from PySide6.QtGui import QAction, QIcon, QKeySequence, QPalette, QCursor
from PySide6.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QToolBar, QStatusBar, QDockWidget, QLabel, QTextEdit, QPushButton,
    QFrame, QSplitter, QFileDialog, QMessageBox, QProgressBar, QTabWidget,
    QSizePolicy
)

from src.core.logging_config import get_logger
from src.core.database_manager import get_database_manager
from src.core.data_structures import ModelFormat
from src.parsers.stl_parser import STLParser, STLProgressCallback
from src.gui.preferences import PreferencesDialog
from src.gui.window.dock_snapping import SnapOverlayLayer, DockDragHandler



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
        super().__init__(parent)

        # Initialize logger
        self.logger = get_logger(__name__)
        self.logger.info("Initializing main window")

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
            default_width = config.default_window_width
            default_height = config.default_window_height
            self.maximize_on_startup = config.maximize_on_startup
            self.remember_window_size = config.remember_window_size
        except Exception as e:
            self.logger.warning(f"Failed to load window settings from config: {e}")
            min_width = 800
            min_height = 600
            default_width = 1200
            default_height = 800
            self.maximize_on_startup = False
            self.remember_window_size = True

        self.setMinimumSize(min_width, min_height)
        self.resize(default_width, default_height)

        # Initialize UI components
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize basic UI properties and styling."""
        # Set application style for Windows desktop
        QApplication.setStyle("Fusion")  # Modern look and feel

        # Use native title bar (removed frameless window flag)
        # This allows the OS to handle the title bar and window controls

        # Enable dock widget features for better layout management
        options = (
            QMainWindow.AllowNestedDocks |
            QMainWindow.AllowTabbedDocks |
            QMainWindow.AnimatedDocks
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

        # Set up native central widget with Qt's built-in layout management
        self._setup_native_central_widget()

        # Let PySide6 handle all window management naturally
        # Removed all custom layout management and snapping systems
        # Default to locked layout mode
        try:
            settings = QSettings()
            default_locked = not bool(settings.value("ui/layout_edit_mode", False, type=bool))
            # When saved value is True, enable edit mode; otherwise lock
            self._set_layout_edit_mode(bool(settings.value("ui/layout_edit_mode", False, type=bool)))
            if hasattr(self, "toggle_layout_edit_action"):
                self.toggle_layout_edit_action.setChecked(bool(settings.value("ui/layout_edit_mode", False, type=bool)))
        except Exception:
            # If settings fail, lock layout
            try:
                self._set_layout_edit_mode(False)
            except Exception:
                pass

        # Set up status update timer
        self.status_bar_manager.setup_status_timer()

        # Let PySide6 handle all layout management naturally
        # Removed custom layout timers and forced layout updates

        # Log window initialization
        self.logger.info("Main window initialized successfully - PySide6 handling all layout management")

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
            QMainWindow.AllowNestedDocks |
            QMainWindow.AllowTabbedDocks |
            QMainWindow.AnimatedDocks
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

        # Set up individual dock widgets using native Qt
        self._setup_model_library_dock()
        self._setup_properties_dock()
        self._setup_metadata_dock()

        # Load saved dock layout using native Qt methods
        self._load_native_dock_layout()

        # Connect native dock signals for layout persistence
        self._connect_native_dock_signals()

        self.logger.info("Native dock widgets setup completed - Qt handling all dock management")

    def _setup_model_library_dock(self) -> None:
        """Set up model library dock using native Qt."""
        try:
            self.model_library_dock = QDockWidget("Model Library", self)
            self.model_library_dock.setObjectName("ModelLibraryDock")

            # Configure with native Qt dock features
            self.model_library_dock.setAllowedAreas(
                Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea |
                Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea
            )
            self.model_library_dock.setFeatures(
                QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable
            )

            # Create model library widget
            try:
                from src.gui.model_library import ModelLibraryWidget
                self.model_library_widget = ModelLibraryWidget(self)

                # Connect native Qt signals
                self.model_library_widget.model_selected.connect(self._on_model_selected)
                self.model_library_widget.model_double_clicked.connect(self._on_model_double_clicked)
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

            # Connect visibility signal for menu synchronization
            self.model_library_dock.visibilityChanged.connect(
                lambda visible: self._update_library_action_state()
            )
            # Qt handles layout persistence automatically

        except Exception as e:
            self.logger.error(f"Failed to setup model library dock: {e}")

    def _setup_properties_dock(self) -> None:
        """Set up properties dock using native Qt."""
        try:
            self.properties_dock = QDockWidget("Model Properties", self)
            self.properties_dock.setObjectName("PropertiesDock")

            # Configure with native Qt dock features
            self.properties_dock.setAllowedAreas(
                Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea |
                Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea
            )
            self.properties_dock.setFeatures(
                QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable
            )

            # Create properties widget using native Qt
            properties_widget = QLabel(
                "Model Properties\n\n"
                "This panel will display properties and metadata\n"
                "for the selected 3D model.\n\n"
                "Features will include:\n"
                "- Model information\n"
                "- Metadata editing\n"
                "- Tag management\n"
                "- Export settings"
            )
            properties_widget.setAlignment(Qt.AlignCenter)
            properties_widget.setWordWrap(True)

            self.properties_dock.setWidget(properties_widget)

            # Add to main window using native Qt dock system
            self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)

            # Set minimum width for proper native layout
            self.properties_dock.setMinimumWidth(200)
            self.properties_dock.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        except Exception as e:
            self.logger.error(f"Failed to setup properties dock: {e}")

    def _setup_metadata_dock(self) -> None:
        """Set up metadata dock using native Qt."""
        try:
            self.metadata_dock = QDockWidget("Metadata Editor", self)
            self.metadata_dock.setObjectName("MetadataDock")

            # Configure with native Qt dock features
            self.metadata_dock.setAllowedAreas(
                Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea |
                Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea
            )
            self.metadata_dock.setFeatures(
                QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable
            )

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

            # Tabify with properties dock using native Qt
            try:
                self.tabifyDockWidget(self.properties_dock, self.metadata_dock)
                self.logger.info("Properties and Metadata docks tabified using native Qt")
            except Exception as e:
                self.logger.debug(f"Could not tabify docks: {e}")

            # Set size constraints for native layout
            self.metadata_dock.setMinimumWidth(300)
            self.metadata_dock.setMaximumWidth(500)
            self.metadata_dock.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

            # Connect visibility signal for menu synchronization
            self.metadata_dock.visibilityChanged.connect(
                lambda visible: self._update_metadata_action_state()
            )
            # Qt handles layout persistence automatically

        except Exception as e:
            self.logger.error(f"Failed to setup metadata dock: {e}")

    def _load_native_dock_layout(self) -> None:
        """Load saved dock layout using native Qt methods."""
        try:
            settings = QSettings()
            if settings.contains("window_geometry") and settings.contains("window_state"):
                # Use native Qt methods to restore layout
                geometry_data = settings.value("window_geometry")
                state_data = settings.value("window_state")

                if geometry_data and state_data:
                    self.restoreGeometry(geometry_data)
                    self.restoreState(state_data)
                    self.logger.info("Native dock layout restored successfully")
                else:
                    self.logger.debug("No saved dock layout found, using defaults")
            else:
                self.logger.debug("No dock layout settings found")
        except Exception as e:
            self.logger.warning(f"Failed to load native dock layout: {e}")

    def _connect_native_dock_signals(self) -> None:
        """Connect native Qt dock signals for layout persistence."""
        # Qt handles dock layout persistence automatically through QSettings
        self.logger.debug("Native Qt dock system handles layout persistence automatically")

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
                self.logger.warning("Viewer3DWidget not available, using native Qt placeholder")

            # Connect viewer signals
            if hasattr(self.viewer_widget, 'model_loaded'):
                self.viewer_widget.model_loaded.connect(self._on_model_loaded)
            if hasattr(self.viewer_widget, 'performance_updated'):
                self.viewer_widget.performance_updated.connect(self._on_performance_updated)

            # Set up managers
            self._setup_viewer_managers()

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
            self.logger.error(f"Failed to create G-code Previewer widget: {e}", exc_info=True)
            self.hero_tabs.addTab(create_placeholder("G Code Previewer", "G-code Previewer\n\nComponent unavailable."), "G Code Previewer")

        # Try to add Cut List Optimizer widget
        try:
            self.logger.info("Attempting to create Cut List Optimizer widget...")
            from src.gui.CLO import CutListOptimizerWidget
            self.clo_widget = CutListOptimizerWidget()
            self.hero_tabs.addTab(self.clo_widget, "Cut List Optimizer")
            self.logger.info("Cut List Optimizer widget created successfully")
        except Exception as e:
            self.logger.warning(f"Failed to create Cut List Optimizer widget: {e}")
            self.hero_tabs.addTab(create_placeholder("Cut List Optimizer", "Cut List Optimizer\n\nComponent unavailable."), "Cut List Optimizer")

        # Try to add Feeds & Speeds widget
        try:
            self.logger.info("Attempting to create Feeds & Speeds widget...")
            from src.gui.feeds_and_speeds import FeedsAndSpeedsWidget
            self.feeds_and_speeds_widget = FeedsAndSpeedsWidget(self)
            self.hero_tabs.addTab(self.feeds_and_speeds_widget, "Feed and Speed")
            self.logger.info("Feeds & Speeds widget created successfully")
        except Exception as e:
            self.logger.warning(f"Failed to create Feeds & Speeds widget: {e}")
            self.hero_tabs.addTab(create_placeholder("Feed and Speed", "Feeds & Speeds Calculator\n\nComponent unavailable."), "Feed and Speed")

        # Add Project Cost Estimator placeholder
        try:
            self.hero_tabs.addTab(create_placeholder("Project Cost Estimator", "Cost Calculator\n\nEstimate material, machine, and labor costs."), "Project Cost Estimator")
        except Exception as e:
            self.logger.warning(f"Failed to add Project Cost Estimator tab: {e}")

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

    def _set_layout_edit_mode(self, enabled: bool) -> None:
        """Toggle Layout Edit Mode: when off, docks are locked; when on, docks movable/floatable."""
        try:
            self.layout_edit_mode = bool(enabled)
            # Use native Qt dock features for layout edit mode
            for dock in self.findChildren(QDockWidget):
                if self.layout_edit_mode:
                    # Enable full dock features for editing
                    dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
                else:
                    # Lock docks but keep closable for hiding
                    dock.setFeatures(QDockWidget.DockWidgetClosable)

            # Persist state for next launch
            settings = QSettings()
            settings.setValue("ui/layout_edit_mode", self.layout_edit_mode)

            # Update status bar indicator
            try:
                self.status_bar_manager.update_layout_edit_mode(self.layout_edit_mode)
            except Exception:
                pass

            # Status feedback
            try:
                self.statusBar().showMessage("Layout Edit Mode ON" if self.layout_edit_mode else "Layout locked", 2000)
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
            if hasattr(self, 'lighting_manager') and self.lighting_manager:
                props = self.lighting_manager.get_properties()
                settings.setValue('lighting/position_x', float(props['position'][0]))
                settings.setValue('lighting/position_y', float(props['position'][1]))
                settings.setValue('lighting/position_z', float(props['position'][2]))
                settings.setValue('lighting/color_r', float(props['color'][0]))
                settings.setValue('lighting/color_g', float(props['color'][1]))
                settings.setValue('lighting/color_b', float(props['color'][2]))
                settings.setValue('lighting/intensity', float(props['intensity']))
                settings.setValue('lighting/cone_angle', float(props.get('cone_angle', 30.0)))
                self.logger.debug("Lighting settings saved to QSettings")
        except Exception as e:
            self.logger.warning(f"Failed to save lighting settings: {e}")

    def _load_lighting_settings(self) -> None:
        """Load lighting settings from QSettings and apply to manager and panel."""
        try:
            settings = QSettings()
            if settings.contains('lighting/position_x'):
                pos_x = settings.value('lighting/position_x', 100.0, type=float)
                pos_y = settings.value('lighting/position_y', 100.0, type=float)
                pos_z = settings.value('lighting/position_z', 100.0, type=float)
                col_r = settings.value('lighting/color_r', 1.0, type=float)
                col_g = settings.value('lighting/color_g', 1.0, type=float)
                col_b = settings.value('lighting/color_b', 1.0, type=float)
                intensity = settings.value('lighting/intensity', 0.8, type=float)
                cone_angle = settings.value('lighting/cone_angle', 30.0, type=float)
                props = {
                    "position": (float(pos_x), float(pos_y), float(pos_z)),
                    "color": (float(col_r), float(col_g), float(col_b)),
                    "intensity": float(intensity),
                    "cone_angle": float(cone_angle),
                }
                if hasattr(self, 'lighting_manager') and self.lighting_manager:
                    self.lighting_manager.apply_properties(props)
                # Sync to lighting_panel without re-emitting
                try:
                    if hasattr(self, 'lighting_panel') and self.lighting_panel:
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
            if hasattr(self, 'lighting_panel') and self.lighting_panel:
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
            if hasattr(self, 'lighting_manager') and self.lighting_manager:
                self.lighting_manager.update_position(x, y, z)
                self._save_lighting_settings()
        except Exception as e:
            self.logger.warning(f"Failed to update light position: {e}")

    def _update_light_color(self, r: float, g: float, b: float) -> None:
        """Update light color from lighting panel."""
        try:
            if hasattr(self, 'lighting_manager') and self.lighting_manager:
                self.lighting_manager.update_color(r, g, b)
                self._save_lighting_settings()
        except Exception as e:
            self.logger.warning(f"Failed to update light color: {e}")

    def _update_light_intensity(self, value: float) -> None:
        """Update light intensity from lighting panel."""
        try:
            if hasattr(self, 'lighting_manager') and self.lighting_manager:
                self.lighting_manager.update_intensity(value)
                self._save_lighting_settings()
        except Exception as e:
            self.logger.warning(f"Failed to update light intensity: {e}")

    def _update_light_cone_angle(self, angle: float) -> None:
        """Update light cone angle from lighting panel."""
        try:
            if hasattr(self, 'lighting_manager') and self.lighting_manager:
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
            if hasattr(self, 'material_lighting_integrator') and self.material_lighting_integrator:
                self.material_lighting_integrator.apply_material_species(species_name)
            else:
                self.logger.warning("MaterialLightingIntegrator not available for applying material")
        except Exception as e:
            self.logger.error(f"Failed to apply material species '{species_name}': {e}")

    def _reset_dock_layout_and_save(self) -> None:
        """Reset dock layout to default positions and save settings."""
        try:
            self.logger.info("Resetting dock layout to defaults")

            # Reset dock layout using native Qt methods
            # Clear any saved layout state
            from PySide6.QtCore import QSettings
            settings = QSettings()

            # Remove saved geometry and state
            if settings.contains("window_geometry"):
                settings.remove("window_geometry")
            if settings.contains("window_state"):
                settings.remove("window_state")

            # Restore default dock positions
            # Model library to left
            if hasattr(self, 'model_library_dock') and self.model_library_dock:
                self.removeDockWidget(self.model_library_dock)
                self.addDockWidget(Qt.LeftDockWidgetArea, self.model_library_dock)

            # Properties and metadata to right, tabified
            if hasattr(self, 'properties_dock') and self.properties_dock:
                self.removeDockWidget(self.properties_dock)
                self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)

            if hasattr(self, 'metadata_dock') and self.metadata_dock:
                self.removeDockWidget(self.metadata_dock)
                self.addDockWidget(Qt.RightDockWidgetArea, self.metadata_dock)
                # Tabify with properties dock
                try:
                    self.tabifyDockWidget(self.properties_dock, self.metadata_dock)
                except Exception as e:
                    self.logger.debug(f"Could not tabify docks: {e}")

            # Make sure all docks are visible
            if hasattr(self, 'model_library_dock') and self.model_library_dock:
                self.model_library_dock.setVisible(True)
            if hasattr(self, 'properties_dock') and self.properties_dock:
                self.properties_dock.setVisible(True)
            if hasattr(self, 'metadata_dock') and self.metadata_dock:
                self.metadata_dock.setVisible(True)

            # Save the new layout state
            self._save_window_settings()

            self.logger.info("Dock layout reset to defaults and saved")
            self.statusBar().showMessage("Layout reset to defaults", 3000)

        except Exception as e:
            self.logger.error(f"Failed to reset dock layout: {e}")
            self.statusBar().showMessage("Failed to reset layout", 3000)

    def _save_window_settings(self) -> None:
        """Save current window geometry and dock state."""
        try:
            from PySide6.QtCore import QSettings
            settings = QSettings()

            # Save window geometry and state
            settings.setValue("window_geometry", self.saveGeometry())
            settings.setValue("window_state", self.saveState())

            # Save current tab index
            if hasattr(self, 'hero_tabs') and self.hero_tabs:
                settings.setValue("ui/active_hero_tab_index", self.hero_tabs.currentIndex())

            self.logger.debug("Window settings saved")
        except Exception as e:
            self.logger.error(f"Failed to save window settings: {e}")

    def _on_model_loaded(self, info: str) -> None:
        """Handle model loaded signal from viewer."""
        try:
            self.logger.info(f"Model loaded: {info}")
            self.status_label.setText(f"Model loaded: {info}")
            self.progress_bar.setVisible(False)

            # Clear status after a delay
            QTimer.singleShot(3000, lambda: self.status_label.setText("Ready"))
        except Exception as e:
            self.logger.error(f"Failed to handle model loaded signal: {e}")

    def _on_performance_updated(self, fps: float) -> None:
        """Handle performance update signal from viewer."""
        try:
            self.logger.debug(f"Performance updated: {fps:.1f} FPS")
            # Update status bar if performance is low
            if fps < 30:
                self.status_label.setText(f"Low FPS: {fps:.1f}")
            elif fps < 60:
                self.status_label.setText(f"FPS: {fps:.1f}")
        except Exception as e:
            self.logger.error(f"Failed to handle performance update signal: {e}")

    def closeEvent(self, event) -> None:
        """Handle window close event - save settings before closing."""
        try:
            self._save_lighting_settings()
            self.logger.info("Lighting settings saved on app close")
        except Exception as e:
            self.logger.warning(f"Failed to save lighting settings on close: {e}")

        # Save viewer and window settings
        try:
            from src.gui.main_window_components.settings_manager import SettingsManager
            settings_mgr = SettingsManager(self)
            settings_mgr.save_viewer_settings()
            settings_mgr.save_window_settings()
            self.logger.info("Viewer and window settings saved on app close")
        except Exception as e:
            self.logger.warning(f"Failed to save viewer/window settings on close: {e}")

        # Clean up viewer widget and VTK resources before closing
        try:
            if hasattr(self, 'viewer_widget') and self.viewer_widget:
                if hasattr(self.viewer_widget, 'cleanup'):
                    self.viewer_widget.cleanup()
                    self.logger.info("Viewer widget cleaned up on app close")
        except Exception as e:
            self.logger.warning(f"Failed to cleanup viewer widget: {e}")

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
            if hasattr(self, 'metadata_dock') and self.metadata_dock:
                settings = QSettings()
                vis = bool(self.metadata_dock.isVisible())
                settings.setValue('metadata_panel/visible', vis)
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
            if hasattr(self, "show_model_library_action") and self.show_model_library_action:
                self.show_model_library_action.setEnabled(not visible)
        except Exception:
            pass

        # TODO: Add material roughness/metallic sliders in picker
        # TODO: Add export material presets feature

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
                file_path = model['file_path']
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

        Args:
            model_id: ID of the selected model
        """
        try:
            # Store the current model ID
            self.current_model_id = model_id

            # Enable the Edit Model action
            if hasattr(self.menu_manager, 'edit_model_action'):
                self.menu_manager.edit_model_action.setEnabled(True)
            if hasattr(self.toolbar_manager, 'edit_model_action'):
                self.toolbar_manager.edit_model_action.setEnabled(True)

            self.logger.debug(f"Model selected: {model_id}")

        except Exception as e:
            self.logger.error(f"Failed to handle model selection: {e}")

    def _edit_model(self) -> None:
        """Analyze the currently selected model for errors."""
        try:
            # Check if a model is currently selected
            if not hasattr(self, 'current_model_id') or self.current_model_id is None:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "No Model Selected",
                                      "Please select a model from the library first.")
                return

            # Get the model from database
            db_manager = get_database_manager()
            model_data = db_manager.get_model(self.current_model_id)

            if not model_data:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Error", "Model not found in database")
                return

            # Load the model file
            file_path = model_data.get('file_path')
            if not file_path:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Error", "Model file path not found")
                return

            parser = STLParser()
            model = parser.parse_file(file_path)

            if not model:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Error", f"Failed to load model: {file_path}")
                return

            # Open model analyzer dialog
            from src.gui.model_editor.model_analyzer_dialog import ModelAnalyzerDialog
            dialog = ModelAnalyzerDialog(model, file_path, self)

            if dialog.exec() == 1:  # QDialog.Accepted
                # Model was fixed and saved, reload it
                self.logger.info(f"Model analyzed and fixed")
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
            if hasattr(self.status_bar_manager, 'start_background_hasher'):
                self.status_bar_manager.start_background_hasher()
                self.logger.info("Background hasher started via status bar manager")
            else:
                self.logger.warning("Status bar manager does not have start_background_hasher method")
        except Exception as e:
            self.logger.error(f"Failed to start background hasher: {e}")

    def _connect_model_library_status_updates(self) -> None:
        """Connect model library progress updates to main window status bar."""
        try:
            if not hasattr(self.model_library_widget, 'model_loader'):
                return

            # We need to monitor the model loader when it's created
            # Store reference to original _load_models method
            original_load_models = self.model_library_widget._load_models

            def _load_models_with_status_update(file_paths):
                """Wrapper to connect status updates when loading starts."""
                # Call original method
                original_load_models(file_paths)

                # Connect progress signals if model_loader exists
                if hasattr(self.model_library_widget, 'model_loader') and self.model_library_widget.model_loader:
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
            if hasattr(self, 'status_label'):
                # Get total files from model loader if available
                if (hasattr(self.model_library_widget, 'model_loader') and
                    self.model_library_widget.model_loader):
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
            if hasattr(self, 'progress_bar'):
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
        dlg = PreferencesDialog(self, on_reset_layout=self._reset_dock_layout_and_save)
        # Connect theme change signal to update main window stylesheet
        dlg.theme_changed.connect(self._on_theme_changed)
        # Connect viewer settings change signal to update VTK scene
        dlg.viewer_settings_changed.connect(self._on_viewer_settings_changed)
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
            
            if not hasattr(self, 'viewer_widget'):
                self.logger.error("ERROR: Main window has no viewer_widget attribute")
                return
                
            if not self.viewer_widget:
                self.logger.error("ERROR: viewer_widget is None")
                return
            
            self.logger.info(f"viewer_widget type: {type(self.viewer_widget).__name__}")
            self.logger.info(f"viewer_widget has scene_manager: {hasattr(self.viewer_widget, 'scene_manager')}")

            # Reload settings from QSettings and apply them
            if hasattr(self.viewer_widget, 'scene_manager'):
                try:
                    scene_manager = self.viewer_widget.scene_manager
                    self.logger.info(f"scene_manager type: {type(scene_manager).__name__}")
                    
                    # Reload all settings from QSettings
                    if hasattr(scene_manager, 'reload_settings_from_qsettings'):
                        self.logger.info("Calling scene_manager.reload_settings_from_qsettings()")
                        scene_manager.reload_settings_from_qsettings()
                        self.logger.info("✓ Viewer settings reloaded and applied successfully")
                    else:
                        self.logger.warning("WARNING: scene_manager has no reload_settings_from_qsettings method")
                        # Fallback to just rendering
                        if hasattr(scene_manager, 'render'):
                            scene_manager.render()
                            self.logger.info("Fallback: Scene re-rendered")
                            
                except Exception as e:
                    self.logger.error(f"ERROR in scene_manager path: {e}", exc_info=True)
            else:
                self.logger.warning("WARNING: viewer_widget has no scene_manager attribute")
                
                # Also try direct render if available
                if hasattr(self.viewer_widget, 'render'):
                    try:
                        self.viewer_widget.render()
                        self.logger.info("Fallback: Viewer re-rendered directly")
                    except Exception as e:
                        self.logger.error(f"ERROR in direct render: {e}")
           
            self.logger.info("=== VIEWER SETTINGS CHANGE HANDLING COMPLETE ===")
        except Exception as e:
            self.logger.error(f"FATAL ERROR applying viewer settings: {e}", exc_info=True)

    def _show_theme_manager(self) -> None:
        """Show the Theme Manager dialog and hook apply signal."""
        try:
            from src.gui.theme import ThemeDialog
            dlg = ThemeDialog(self)
            dlg.theme_applied.connect(self._on_theme_applied)
            dlg.exec()
        except Exception as e:
            self.logger.error(f"Failed to open Theme Manager: {e}")
            QMessageBox.warning(self, "Theme Manager", f"Failed to open Theme Manager:\n{e}")

    def _on_theme_applied(self, preset_name: str) -> None:
        """Handle theme change notification."""
        # Theme is managed by ThemeService and applied globally
        self.logger.info(f"Theme changed: {preset_name}")

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
            # Reset save view button when view is reset
            try:
                if hasattr(self.viewer_widget, 'reset_save_view_button'):
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
            current_index = themes.index(current_theme) if current_theme in themes else 0
            next_index = (current_index + 1) % len(themes)
            next_theme = themes[next_index]

            # Apply next theme
            service.apply_theme(next_theme, "qt-material")

            # Update status
            theme_names = {"light": "Light", "dark": "Dark", "auto": "System"}
            self.status_label.setText(f"Theme: {theme_names.get(next_theme, next_theme)}")
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
            if not hasattr(self.viewer_widget, 'current_model') or not self.viewer_widget.current_model:
                QMessageBox.information(self, "Save View", "No model is currently loaded.")
                return

            # Get the model ID from the current model
            model = self.viewer_widget.current_model
            if not hasattr(model, 'file_path') or not model.file_path:
                QMessageBox.warning(self, "Save View", "Cannot save view: model file path not found.")
                return

            # Find the model ID in the database by file path
            db_manager = get_database_manager()
            models = db_manager.get_all_models()
            model_id = None
            for m in models:
                if m.get('file_path') == model.file_path:
                    model_id = m.get('id')
                    break

            if not model_id:
                QMessageBox.warning(self, "Save View", "Model not found in database.")
                return

            # Get camera state from viewer
            if hasattr(self.viewer_widget, 'renderer'):
                camera = self.viewer_widget.renderer.GetActiveCamera()
                if camera:
                    pos = camera.GetPosition()
                    focal = camera.GetFocalPoint()
                    view_up = camera.GetViewUp()

                    camera_data = {
                        'position_x': pos[0], 'position_y': pos[1], 'position_z': pos[2],
                        'focal_x': focal[0], 'focal_y': focal[1], 'focal_z': focal[2],
                        'view_up_x': view_up[0], 'view_up_y': view_up[1], 'view_up_z': view_up[2]
                    }

                    # Save to database
                    success = db_manager.save_camera_orientation(model_id, camera_data)

                    if success:
                        self.status_label.setText("View saved for this model")
                        self.logger.info(f"Saved camera view for model ID {model_id}")
                        # Reset save view button after successful save
                        try:
                            if hasattr(self.viewer_widget, 'reset_save_view_button'):
                                self.viewer_widget.reset_save_view_button()
                        except Exception as e:
                            self.logger.warning(f"Failed to reset save view button: {e}")
                        QTimer.singleShot(3000, lambda: self.status_label.setText("Ready"))
                    else:
                        QMessageBox.warning(self, "Save View", "Failed to save view to database.")
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

            if camera_data and hasattr(self.viewer_widget, 'renderer'):
                camera = self.viewer_widget.renderer.GetActiveCamera()
                if camera:
                    # Restore camera position, focal point, and view up
                    camera.SetPosition(
                        camera_data['camera_position_x'],
                        camera_data['camera_position_y'],
                        camera_data['camera_position_z']
                    )
                    camera.SetFocalPoint(
                        camera_data['camera_focal_x'],
                        camera_data['camera_focal_y'],
                        camera_data['camera_focal_z']
                    )
                    camera.SetViewUp(
                        camera_data['camera_view_up_x'],
                        camera_data['camera_view_up_y'],
                        camera_data['camera_view_up_z']
                    )

                    # Update clipping range and render
                    self.viewer_widget.renderer.ResetCameraClippingRange()
                    self.viewer_widget.vtk_widget.GetRenderWindow().Render()

                    self.logger.info(f"Restored saved camera view for model ID {model_id}")
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
            QMessageBox.warning(
                self,
                "Help Error",
                f"Could not open help system: {e}"
            )

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
        """Generate screenshots for all models in the library with applied materials."""
        try:
            from src.gui.batch_screenshot_worker import BatchScreenshotWorker
            from src.core.application_config import ApplicationConfig

            # Check if material manager is available
            if not hasattr(self, 'material_manager') or self.material_manager is None:
                QMessageBox.warning(
                    self,
                    "Screenshot Generation",
                    "Material manager not available. Cannot generate screenshots."
                )
                return

            # Load thumbnail settings
            config = ApplicationConfig.get_default()
            bg_image = config.thumbnail_bg_image
            material = config.thumbnail_material

            # Create and start the batch screenshot worker
            self.screenshot_worker = BatchScreenshotWorker(
                material_manager=self.material_manager,
                screenshot_size=256,
                background_image=bg_image,
                material_name=material
            )

            # Connect signals
            self.screenshot_worker.progress_updated.connect(self._on_screenshot_progress)
            self.screenshot_worker.screenshot_generated.connect(self._on_screenshot_generated)
            self.screenshot_worker.error_occurred.connect(self._on_screenshot_error)
            self.screenshot_worker.finished_batch.connect(self._on_screenshots_finished)

            # Show progress dialog
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.status_label.setText("Generating screenshots for all models...")

            # Start worker
            self.screenshot_worker.start()
            self.logger.info("Started batch screenshot generation")

        except Exception as e:
            self.logger.error(f"Failed to start screenshot generation: {e}")
            QMessageBox.critical(
                self,
                "Screenshot Generation Error",
                f"Failed to start screenshot generation:\n{e}"
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
            self.logger.debug(f"Screenshot generated for model {model_id}: {screenshot_path}")
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
            if hasattr(self, 'model_library_widget') and self.model_library_widget:
                self.model_library_widget._load_models_from_database()

            QMessageBox.information(
                self,
                "Screenshot Generation Complete",
                "All model screenshots have been generated successfully!"
            )

            self.logger.info("Batch screenshot generation completed")

            # Clear status after a delay
            QTimer.singleShot(3000, lambda: self.status_label.setText("Ready"))

        except Exception as e:
            self.logger.error(f"Failed to handle screenshots finished event: {e}")

    def _toggle_maximize(self) -> None:
        """Toggle window maximize/restore state."""
        try:
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()
        except Exception as e:
            self.logger.warning(f"Failed to toggle maximize: {e}")

    # ===== END_EXTRACT_TO: src/gui/materials/integration.py =====

    # ===== END_EXTRACT_TO: src/gui/materials/integration.py =====

    # ===== END_EXTRACT_TO: src/gui/services/background_processor.py =====

    # ===== END_EXTRACT_TO: src/gui/core/event_coordinator.py =====
