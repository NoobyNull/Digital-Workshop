"""
Main window implementation for 3D-MM application.

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
    QFrame, QSplitter, QFileDialog, QMessageBox, QProgressBar, QTabWidget
)

from src.core.logging_config import get_logger
from src.core.database_manager import get_database_manager
from src.core.data_structures import ModelFormat
from src.parsers.stl_parser import STLParser, STLProgressCallback
from src.gui.preferences import PreferencesDialog
from src.gui.window.dock_snapping import SnapOverlayLayer, DockDragHandler



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

        # Hide window during initialization to prevent blinking
        self.hide()

        # Window properties
        self.setWindowTitle("3D-MM - 3D Model Manager")

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

        # Expose status bar components for easy access
        self.status_label = self.status_bar_manager.status_label
        self.progress_bar = self.status_bar_manager.progress_bar
        self.hash_indicator = self.status_bar_manager.hash_indicator
        self.memory_label = self.status_bar_manager.memory_label

        # Expose menu manager actions for easy access
        self.toggle_layout_edit_action = self.menu_manager.toggle_layout_edit_action
        self.show_metadata_action = self.menu_manager.show_metadata_action
        self.show_model_library_action = self.menu_manager.show_model_library_action

        # Initialize dock manager
        from src.gui.window.dock_manager import DockManager
        self.dock_manager = DockManager(self, self.logger)
        self.dock_manager.setup_dock_widgets()

        # Initialize central widget manager
        from src.gui.window.central_widget_manager import CentralWidgetManager
        self.central_widget_manager = CentralWidgetManager(self, self.logger)

        # Ensure main window gets the application stylesheet
        # This is needed for frameless windows to properly inherit the Material Design theme
        try:
            app = QApplication.instance()
            if app:
                # Get the current stylesheet from the application
                app_stylesheet = app.styleSheet()
                if app_stylesheet:
                    # Apply it to the main window
                    self.setStyleSheet(app_stylesheet)
        except Exception as e:
            self.logger.debug(f"Could not apply app stylesheet to main window: {e}")
        self.central_widget_manager.setup_central_widget()

        # Initialize model loader
        from src.gui.model.model_loader import ModelLoader
        self.model_loader_manager = ModelLoader(self, self.logger)

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

    def _force_initial_layout(self) -> None:
        """Force initial layout after all widgets are created."""
        try:
            # Force central widget layout
            self._force_central_widget_layout()

            # Update all dock widgets
            for dock in self.findChildren(QDockWidget):
                if dock.isVisible():
                    dock.updateGeometry()
                    dock.update()

            # Force main window layout recalculation
            self.updateGeometry()
            self.layout().activate() if self.layout() else None

            self.logger.debug("Initial layout forced after widget creation")
        except Exception as e:
            self.logger.debug(f"Failed to force initial layout: {e}")

    def showEvent(self, event: QEvent) -> None:
        """Handle window show event to apply startup settings."""
        super().showEvent(event)

        # Apply maximize on startup setting if configured
        try:
            if hasattr(self, 'maximize_on_startup') and self.maximize_on_startup:
                self.showMaximized()
                self.logger.debug("Window maximized on startup")
        except Exception as e:
            self.logger.warning(f"Failed to apply maximize on startup: {e}")

        # Ensure central widget fills available space after show
        QTimer.singleShot(100, self._force_central_widget_layout)

    def resizeEvent(self, event) -> None:
        """Handle window resize events to ensure proper layout."""
        super().resizeEvent(event)
        # Let PySide6 handle resize events naturally
        # Removed custom layout management

    def _force_central_widget_layout(self) -> None:
        """Force central widget to fill all available space."""
        try:
            central_widget = self.centralWidget()
            if central_widget:
                # Let Qt handle the layout completely naturally
                # Just ensure proper size policies are set and trigger layout update
                if hasattr(central_widget, 'setSizePolicy'):
                    from PySide6.QtWidgets import QSizePolicy
                    central_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

                # Force layout recalculation without manual geometry setting
                if hasattr(central_widget, 'updateGeometry'):
                    central_widget.updateGeometry()

                # Update the main window layout
                self.updateGeometry()
                if self.layout():
                    self.layout().activate()

                # Force repaint
                central_widget.update()
                self.update()

                # Log the actual geometry for debugging
                actual_geometry = central_widget.geometry()
                self.logger.debug(f"Central widget actual geometry: {actual_geometry}")
        except Exception as e:
            self.logger.debug(f"Failed to force central widget layout: {e}")

    def _get_available_central_geometry(self) -> QRect:
        """Get the available geometry for the central widget (excluding dock widgets)."""
        try:
            # Use Qt's built-in method to get the geometry of the central widget area
            # This is more reliable than manual calculation
            central_area = self.centralWidget().geometry() if self.centralWidget() else self.rect()

            # Ensure minimum dimensions
            min_width = 200
            min_height = 150

            if central_area.width() < min_width or central_area.height() < min_height:
                # If the calculated area is too small, use the full window minus dock space
                full_rect = self.rect()
                dock_widgets = self.findChildren(QDockWidget)

                left_width = 0
                right_width = 0
                top_height = 0
                bottom_height = 0

                for dock in dock_widgets:
                    if dock.isVisible():
                        dock_area = self.dockWidgetArea(dock)
                        dock_geometry = dock.geometry()

                        if dock_area == Qt.LeftDockWidgetArea:
                            left_width = max(left_width, dock_geometry.right())
                        elif dock_area == Qt.RightDockWidgetArea:
                            right_width = max(right_width, dock_geometry.width())
                        elif dock_area == Qt.TopDockWidgetArea:
                            top_height = max(top_height, dock_geometry.bottom())
                        elif dock_area == Qt.BottomDockWidgetArea:
                            bottom_height = max(bottom_height, dock_geometry.height())

                # Calculate available space for central widget
                available_x = left_width
                available_y = top_height
                available_width = max(full_rect.width() - left_width - right_width, min_width)
                available_height = max(full_rect.height() - top_height - bottom_height, min_height)

                central_area = QRect(available_x, available_y, available_width, available_height)

            self.logger.debug(f"Central widget geometry: {central_area}")
            return central_area

        except Exception as e:
            self.logger.debug(f"Failed to calculate available central geometry: {e}")
            return self.rect()  # Fallback to full window

    def _setup_layout_update_timer(self) -> None:
        """Set up timer for real-time layout updates."""
        try:
            self._layout_update_timer = QTimer(self)
            self._layout_update_timer.setSingleShot(True)
            self._layout_update_timer.setInterval(200)  # 200ms for responsive updates (reduced frequency)
            self._layout_update_timer.timeout.connect(self._update_layout_responsive)
        except Exception as e:
            self.logger.debug(f"Failed to setup layout update timer: {e}")

    def _update_layout_responsive(self) -> None:
        """Update layout in response to dock widget movements."""
        try:
            # Force central widget to adjust to current dock layout
            self._force_central_widget_layout()

            # Update all dock widgets to ensure proper sizing
            for dock in self.findChildren(QDockWidget):
                if dock.isVisible():
                    dock.updateGeometry()
                    dock.update()

            self.logger.debug("Responsive layout update completed")
        except Exception as e:
            self.logger.debug(f"Failed responsive layout update: {e}")






    # ===== END_EXTRACT_TO: src/gui/window/dock_manager.py =====

    # ===== END_EXTRACT_TO: src/gui/window/central_widget_manager.py =====

    # --- Dock layout helpers ---
    # ===== END_EXTRACT_TO: src/gui/window/layout_persistence.py =====

    def _connect_layout_autosave(self, dock: QDockWidget) -> None:
        """Restore dock widgets to their default docking layout."""
        try:
            # First try to load saved default layout (for fresh installations)
            settings = self._read_settings_json()
            default_geom = settings.get("default_window_geometry")
            default_state = settings.get("default_window_state")

            if default_geom and default_state:
                try:
                    geom = base64.b64decode(default_geom)
                    state = base64.b64decode(default_state)
                    restored = self.restoreGeometry(geom) and self.restoreState(state)
                    if restored:
                        self.logger.info("Restored default layout from saved defaults")
                        # Restore default hero tab if available
                        try:
                            default_hero_idx = settings.get("default_hero_tab_index")
                            if (isinstance(default_hero_idx, int) and hasattr(self, "hero_tabs") and
                                isinstance(self.hero_tabs, QTabWidget) and
                                0 <= default_hero_idx < self.hero_tabs.count()):
                                self.hero_tabs.setCurrentIndex(default_hero_idx)
                        except Exception:
                            pass
                        self._schedule_layout_save()
                        return
                except Exception:
                    pass
            # ===== END_EXTRACT_TO: src/gui/services/background_processor.py =====

            # Fallback to hardcoded defaults if no saved default
            if getattr(self, "_default_geometry", None):
                self.restoreGeometry(self._default_geometry)
            if getattr(self, "_default_layout_state", None):
                # restoreState returns bool; ignore on failure
                self.restoreState(self._default_layout_state)
        except Exception:
            pass
        # Fallback: programmatically re-dock common widgets
        self._redock_all()
        # Persist the reset layout
        try:
            self._schedule_layout_save()
        except Exception:
            pass

    def _redock_all(self) -> None:
        """Force re-dock of known dock widgets to their default areas."""
        try:
            if hasattr(self, "model_library_dock"):
                self.model_library_dock.setFloating(False)
                self.addDockWidget(Qt.LeftDockWidgetArea, self.model_library_dock)
            if hasattr(self, "properties_dock"):
                self.properties_dock.setFloating(False)
                self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)
            if hasattr(self, "metadata_dock"):
                self.metadata_dock.setFloating(False)
                self.addDockWidget(Qt.RightDockWidgetArea, self.metadata_dock)
        except Exception as e:
            self.logger.warning(f"Failed to re-dock widgets: {str(e)}")

    # ---- Layout persistence (auto-save/auto-load) ----
    def _settings_json_path(self) -> Path:
        """Return AppData settings.json path."""
        app_data = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
        app_data.mkdir(parents=True, exist_ok=True)
        return app_data / "settings.json"

    def _read_settings_json(self) -> dict:
        try:
            p = self._settings_json_path()
            if p.exists():
                with p.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
        except Exception:
            pass
        return {}

    def _write_settings_json(self, data: dict) -> None:
        try:
            p = self._settings_json_path()
            with p.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _init_layout_persistence(self) -> None:
        """Initialize debounced autosave timer."""
        try:
            self._layout_save_timer = QTimer(self)
            self._layout_save_timer.setSingleShot(True)
            self._layout_save_timer.setInterval(700)  # ms debounce
            self._layout_save_timer.timeout.connect(self._save_current_layout)
        except Exception:
            pass

    def _schedule_layout_save(self) -> None:
        """Request a debounced layout save."""
        try:
            if hasattr(self, "_layout_save_timer"):
                self._layout_save_timer.start()
        except Exception:
            pass

    def _save_current_layout(self) -> None:
        """Persist current window geometry, dock layout, and navigation state to settings.json."""
        try:
            geom = bytes(self.saveGeometry())
            state = bytes(self.saveState())

            # Persist base window geometry/state
            payload = {
                "window_geometry": base64.b64encode(geom).decode("ascii"),
                "window_state": base64.b64encode(state).decode("ascii"),
                "layout_version": 1,
            }

            # Persist central splitter sizes if applicable (legacy path)
            try:
                cw = self.centralWidget()
                if isinstance(cw, QSplitter):
                    sizes = cw.sizes()
                    if sizes:
                        payload["central_splitter_sizes"] = [int(s) for s in sizes]
            except Exception:
                pass

            # Persist active main tab index if available
            try:
                if hasattr(self, "main_tabs") and isinstance(self.main_tabs, QTabWidget):
                    payload["active_main_tab_index"] = int(self.main_tabs.currentIndex())
            except Exception:
                pass

            # Persist active center tab index (inside "3d Model") if available
            try:
                if hasattr(self, "center_tabs") and isinstance(self.center_tabs, QTabWidget):
                    payload["active_center_tab_index"] = int(self.center_tabs.currentIndex())
            except Exception:
                pass
            # Persist active hero tab index if available
            try:
                if hasattr(self, "hero_tabs") and isinstance(self.hero_tabs, QTabWidget):
                    payload["active_hero_tab_index"] = int(self.hero_tabs.currentIndex())
            except Exception:
                pass

            settings = self._read_settings_json()
            settings.update(payload)
            self._write_settings_json(settings)
            self.logger.debug("Layout autosaved")
        except Exception as e:
            self.logger.warning(f"Failed to save current layout: {e}")

    def _load_saved_layout(self) -> bool:
        """Restore previously saved layout from settings.json. Returns True if successful."""
        try:
            settings = self._read_settings_json()
            g64 = settings.get("window_geometry")
            s64 = settings.get("window_state")
            ok_any = False
            if g64:
                try:
                    geom = base64.b64decode(g64)
                    ok_any = self.restoreGeometry(geom) or ok_any
                except Exception:
                    pass
            if s64:
                try:
                    state = base64.b64decode(s64)
                    ok_any = self.restoreState(state) or ok_any
                except Exception:
                    pass

            # If central is already a splitter, restore sizes
            try:
                cw = self.centralWidget()
                if isinstance(cw, QSplitter):
                    sizes = settings.get("central_splitter_sizes")
                    if isinstance(sizes, list) and sizes:
                        cw.setSizes([int(s) for s in sizes])
            except Exception:
                pass

            if ok_any:
                self.logger.info("Restored window layout from saved settings")
            return ok_any
        except Exception as e:
            self.logger.warning(f"Failed to load saved layout: {e}")
            return False
    # ===== END_EXTRACT_TO: src/gui/window/layout_persistence.py =====

    def _connect_layout_autosave(self, dock: QDockWidget) -> None:
        """Connect signals from a dock to trigger autosave and central widget updates."""
        try:
            dock.topLevelChanged.connect(lambda _=False: self._schedule_layout_save())
            dock.topLevelChanged.connect(lambda _=False: self._update_central_widget_for_dock_changes())
            dock.topLevelChanged.connect(lambda _=False: self._trigger_responsive_layout_update())
            # Some bindings expose dockLocationChanged(area)
            if hasattr(dock, "dockLocationChanged"):
                dock.dockLocationChanged.connect(lambda _area=None: self._schedule_layout_save())
                dock.dockLocationChanged.connect(lambda _area=None: self._update_central_widget_for_dock_changes())
                dock.dockLocationChanged.connect(lambda _area=None: self._trigger_responsive_layout_update())
            dock.visibilityChanged.connect(lambda _=False: self._schedule_layout_save())
            dock.visibilityChanged.connect(lambda _=False: self._update_central_widget_for_dock_changes())
            dock.visibilityChanged.connect(lambda _=False: self._trigger_responsive_layout_update())
        except Exception:
            pass

    def _trigger_responsive_layout_update(self) -> None:
        """Trigger responsive layout update with debouncing."""
        try:
            if hasattr(self, "_layout_update_timer"):
                self._layout_update_timer.start()
        except Exception as e:
            self.logger.debug(f"Failed to trigger responsive layout update: {e}")

    # ---- Snapping system (overlays + edge snap) ----
    def _init_snapping_system(self) -> None:
        """Create snap overlays and attach drag handlers to all current docks."""
        try:
            if hasattr(self, "_snap_layer"):
                return
            self._snap_layer = SnapOverlayLayer(self)
            self._snap_handlers: dict[str, DockDragHandler] = {}
        except Exception:
            # Ensure attributes exist for later safe checks
            self._snap_handlers = {}
            self._snap_layer = SnapOverlayLayer(self)

        # Register known docks if they exist (lighting_panel is now a dialog, not a dock)
        for name in ("model_library_dock", "properties_dock", "metadata_dock"):
            try:
                dock = getattr(self, name, None)
                if dock is not None:
                    self._register_dock_for_snapping(dock)
            except Exception:
                continue

    def _register_dock_for_snapping(self, dock: QDockWidget) -> None:
        """Install a DockDragHandler on the given dock to enable overlay-guided snapping."""
        if dock is None:
            return
        key = dock.objectName() or str(id(dock))
        if hasattr(self, "_snap_handlers") and key in getattr(self, "_snap_handlers", {}):
            return
        handler = DockDragHandler(self, dock, self._snap_layer, self.logger)
        dock.installEventFilter(handler)
        self._snap_handlers[key] = handler

    def _iter_docks(self) -> list[QDockWidget]:
        """Get all dock widgets in the main window."""
        # Use findChildren to get ALL dock widgets, not just the known ones
        return self.findChildren(QDockWidget)

    def _enable_snap_handlers(self, enable: bool) -> None:
        """Enable or disable snap overlay handlers for all docks."""
        try:
            if enable:
                for d in self._iter_docks():
                    self._register_dock_for_snapping(d)
            else:
                # Remove event filters and clear overlays
                if hasattr(self, "_snap_handlers"):
                    for key, handler in list(self._snap_handlers.items()):
                        try:
                            dock = getattr(handler, "_dock", None)
                            if dock:
                                dock.removeEventFilter(handler)  # type: ignore[arg-type]
                        except Exception:
                            pass
                    self._snap_handlers.clear()
                if hasattr(self, "_snap_layer"):
                    self._snap_layer.hide_overlays()
        except Exception:
            pass

    def _set_layout_edit_mode(self, enabled: bool) -> None:
        """Toggle Layout Edit Mode: when off, docks are locked; when on, docks movable/floatable."""
        try:
            self.layout_edit_mode = bool(enabled)
            for d in self._iter_docks():
                if self.layout_edit_mode:
                    d.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
                else:
                    # Locked: disable moving and floating, keep closable so user can hide/pin panels
                    d.setFeatures(QDockWidget.DockWidgetClosable)
            self._enable_snap_handlers(self.layout_edit_mode)
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

    def _update_central_widget_for_dock_changes(self) -> None:
        """Update central widget layout when dock widgets change position or size."""
        try:
            central_widget = self.centralWidget()
            if central_widget:
                # Force geometry update to ensure proper resizing
                central_widget.updateGeometry()

                # Ensure the central widget maintains its expanding policy
                if hasattr(central_widget, 'setSizePolicy'):
                    central_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

                # Force main window layout recalculation
                self.updateGeometry()
                self.layout().activate()

                self.logger.debug("Central widget updated for dock changes")
        except Exception as e:
            self.logger.debug(f"Failed to update central widget for dock changes: {e}")

    def _snap_dock_to_edge(self, dock: QDockWidget, edge: str) -> bool:
        """Dock the provided QDockWidget to the specified edge if allowed."""
        area_map = {
            "left": Qt.LeftDockWidgetArea,
            "right": Qt.RightDockWidgetArea,
            "top": Qt.TopDockWidgetArea,
            "bottom": Qt.BottomDockWidgetArea,
        }
        target_area = area_map.get(edge)
        if target_area is None:
            return False
        allowed = dock.allowedAreas()
        if not (allowed & target_area):
            # Not permitted by this dock's allowed areas
            return False
        try:
            dock.setFloating(False)
        except Exception:
            pass
        # Perform docking
        self.addDockWidget(target_area, dock)
        try:
            dock.raise_()
        except Exception:
            pass
        try:
            self._schedule_layout_save()
        except Exception:
            pass
        return True

    def _reset_dock_layout(self) -> None:
        """Restore dock widgets to their default docking layout."""
        try:
            if getattr(self, "_default_geometry", None):
                self.restoreGeometry(self._default_geometry)
            if getattr(self, "_default_layout_state", None):
                # restoreState returns bool; ignore on failure
                self.restoreState(self._default_layout_state)
        except Exception:
            pass
        # Fallback: programmatically re-dock common widgets
        self._redock_all()
        # Persist the reset layout
        try:
            self._schedule_layout_save()
        except Exception:
            pass

    def _reset_dock_layout_and_save(self) -> None:
        """Reset layout to defaults and persist immediately."""
        self._reset_dock_layout()
        try:
            self._schedule_layout_save()
        except Exception:
            pass

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

    def _create_metadata_dock(self) -> None:
        """Create the Metadata Manager dock and integrate it into the UI."""
        try:
            # Avoid recreating if it already exists
            if hasattr(self, "metadata_dock") and self.metadata_dock:
                return
        except Exception:
            pass

        self.metadata_dock = QDockWidget("Metadata Editor", self)
        self.metadata_dock.setObjectName("MetadataDock")
        # Allow docking to any area for maximum flexibility
        self.metadata_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea
        )
        self.metadata_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)

        try:
            from src.gui.metadata_editor import MetadataEditorWidget
            self.metadata_editor = MetadataEditorWidget(self)

            # Connect signals
            self.metadata_editor.metadata_saved.connect(self._on_metadata_saved)
            self.metadata_editor.metadata_changed.connect(self._on_metadata_changed)

            # Bottom tabs: Metadata | Notes | History
            self.metadata_tabs = QTabWidget(self)
            self.metadata_tabs.setObjectName("MetadataTabs")
            self.metadata_tabs.addTab(self.metadata_editor, "Metadata")

            # Notes tab (placeholder)
            notes_widget = QTextEdit()
            notes_widget.setReadOnly(True)
            notes_widget.setPlainText(
                "Notes\n\n"
                "Add project or model-specific notes here.\n"
                "Future: rich text, timestamps, and attachments."
            )
            self.metadata_tabs.addTab(notes_widget, "Notes")

            # History tab (placeholder)
            history_widget = QTextEdit()
            history_widget.setReadOnly(True)
            history_widget.setPlainText(
                "History\n\n"
                "Timeline of edits and metadata changes will appear here."
            )
            self.metadata_tabs.addTab(history_widget, "History")

            # Material Design theme is applied globally via ThemeService
            # No need to apply custom stylesheets here

            self.metadata_dock.setWidget(self.metadata_tabs)
            self.logger.info("Metadata editor widget created successfully (restored)")
        except Exception as e:
            self.logger.warning(f"Failed to create MetadataEditorWidget during restore: {e}")

            # Fallback to placeholder
            metadata_widget = QTextEdit()
            metadata_widget.setReadOnly(True)
            metadata_widget.setPlainText(
                "Metadata Editor\n\n"
                "Component unavailable."
            )
            self.metadata_dock.setWidget(metadata_widget)

        # Attach dock - default to right side but user can move anywhere
        self.addDockWidget(Qt.RightDockWidgetArea, self.metadata_dock)
        try:
            self._register_dock_for_snapping(self.metadata_dock)
        except Exception:
            pass
        try:
            self._connect_layout_autosave(self.metadata_dock)
        except Exception:
            pass
        # Persist visibility and keep View menu action state in sync
        try:
            self.metadata_dock.visibilityChanged.connect(lambda _=False: self._save_metadata_panel_visibility())
            self.metadata_dock.visibilityChanged.connect(lambda _=False: self._update_metadata_action_state())
        except Exception:
            pass

    def _restore_metadata_manager(self) -> None:
        """Restore and show the Metadata Manager panel if it was closed or missing."""
        try:
            # Create or recreate the dock as needed
            if not hasattr(self, "metadata_dock") or self.metadata_dock is None:
                self._create_metadata_dock()
            else:
                # Ensure it has a widget; recreate contents if missing
                try:
                    has_widget = self.metadata_dock.widget() is not None
                except Exception:
                    has_widget = False
                if not has_widget:
                    try:
                        self.removeDockWidget(self.metadata_dock)
                    except Exception:
                        pass
                    self.metadata_dock = None  # type: ignore
                    self._create_metadata_dock()

            # Dock to default right side and show (user can move)
            try:
                self._snap_dock_to_edge(self.metadata_dock, "right")
            except Exception:
                pass
            try:
                self.metadata_dock.show()
                self.metadata_dock.raise_()
            except Exception:
                pass

            # Persist visibility and menu state
            try:
                self._save_metadata_panel_visibility()
            except Exception:
                pass
            try:
                self._update_metadata_action_state()
            except Exception:
                pass
            try:
                self._schedule_layout_save()
            except Exception:
                pass

            try:
                self.statusBar().showMessage("Metadata Manager restored", 2000)
            except Exception:
                pass
        except Exception as e:
            self.logger.error(f"Failed to restore Metadata Manager: {e}")

    def _create_model_library_dock(self) -> None:
        """Create the Model Library dock and integrate it into the UI."""
        try:
            if hasattr(self, "model_library_dock") and self.model_library_dock:
                return
        except Exception:
            pass

        self.model_library_dock = QDockWidget("Model Library", self)
        self.model_library_dock.setObjectName("ModelLibraryDock")
        # Allow docking to any area for maximum flexibility
        self.model_library_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea
        )
        self.model_library_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)

        try:
            from src.gui.model_library import ModelLibraryWidget
            self.model_library_widget = ModelLibraryWidget(self)

            # Connect signals
            self.model_library_widget.model_selected.connect(self._on_model_selected)
            self.model_library_widget.model_double_clicked.connect(self._on_model_double_clicked)
            self.model_library_widget.models_added.connect(self._on_models_added)

            # Connect model library progress updates to main window status bar
            self._connect_model_library_status_updates()

            self.model_library_dock.setWidget(self.model_library_widget)
        except Exception as e:
            # Fallback widget
            lib_placeholder = QTextEdit()
            lib_placeholder.setReadOnly(True)
            lib_placeholder.setPlainText(
                "Model Library\n\nComponent unavailable."
            )
            self.model_library_dock.setWidget(lib_placeholder)

        # Attach dock - default to left side but user can move anywhere
        self.addDockWidget(Qt.LeftDockWidgetArea, self.model_library_dock)
        try:
            self._register_dock_for_snapping(self.model_library_dock)
        except Exception:
            pass
        try:
            self._connect_layout_autosave(self.model_library_dock)
        except Exception:
            pass
        try:
            self.model_library_dock.visibilityChanged.connect(lambda _=False: self._update_library_action_state())
        except Exception:
            pass
        try:
            self._update_library_action_state()
        except Exception:
            pass

    def _restore_model_library(self) -> None:
        """Restore and show the Model Library panel if it was closed or missing."""
        try:
            # Create or recreate the dock as needed
            recreate = False
            if not hasattr(self, "model_library_dock") or self.model_library_dock is None:
                recreate = True
            else:
                try:
                    has_widget = self.model_library_dock.widget() is not None
                except Exception:
                    has_widget = False
                if not has_widget:
                    try:
                        self.removeDockWidget(self.model_library_dock)
                    except Exception:
                        pass
                    self.model_library_dock = None  # type: ignore
                    recreate = True

            if recreate:
                self._create_model_library_dock()

            # Dock to default left side and show (user can move)
            try:
                self._snap_dock_to_edge(self.model_library_dock, "left")
            except Exception:
                pass
            try:
                self.model_library_dock.show()
                self.model_library_dock.raise_()
            except Exception:
                pass

            # Persist menu/action state and layout
            try:
                self._update_library_action_state()
            except Exception:
                pass
            try:
                self._schedule_layout_save()
            except Exception:
                pass

            try:
                self.statusBar().showMessage("Model Library restored", 2000)
            except Exception:
                pass
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
        try:
            # Get the updated stylesheet from the application
            app = QApplication.instance()
            if app:
                new_stylesheet = app.styleSheet()
                if new_stylesheet:
                    # Apply the new stylesheet to the main window
                    self.setStyleSheet(new_stylesheet)
                    self.logger.debug("Main window stylesheet updated after theme change")
        except Exception as e:
            self.logger.debug(f"Error updating main window stylesheet: {e}")

    def _on_viewer_settings_changed(self) -> None:
        """Handle viewer settings change from preferences dialog."""
        try:
            if not hasattr(self, 'viewer_widget') or not self.viewer_widget:
                return

            # Try to apply viewer settings changes
            # Settings may include grid visibility, ground plane, rendering mode, etc.
            
            # Attempt to trigger refresh by calling render if available
            if hasattr(self.viewer_widget, 'render'):
                try:
                    self.viewer_widget.render()
                    self.logger.debug("Viewer re-rendered after settings change")
                except Exception as e:
                    self.logger.debug(f"Could not re-render viewer: {e}")
           
            # Try scene manager render if available
            if hasattr(self.viewer_widget, 'scene_manager'):
                try:
                    scene_manager = self.viewer_widget.scene_manager
                    if hasattr(scene_manager, 'render'):
                        scene_manager.render()
                        self.logger.debug("Scene re-rendered after viewer settings change")
                except Exception as e:
                    self.logger.debug(f"Could not re-render scene: {e}")
           
            self.logger.debug("Viewer settings applied after preferences change")
        except Exception as e:
            self.logger.debug(f"Error applying viewer settings: {e}")

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
            "<h3>3D-MM - 3D Model Manager</h3>"
            "<p>Version 1.0.0</p>"
            "<p>A desktop application for managing and viewing 3D models.</p>"
            "<p><b>Supported formats:</b> STL, OBJ, STEP, MF3</p>"
            "<p><b>Requirements:</b> Windows 7+, Python 3.8+, PySide5</p>"
            "<br>"
            "<p>&copy; 2023 3D-MM Development Team</p>"
        )

        QMessageBox.about(self, "About 3D-MM", about_text)

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
