"""
Layout Persistence System Module

This module handles the persistence and restoration of window layouts,
dock widget positions, and user interface state across application sessions.

Classes:
    LayoutPersistenceManager: Main class for managing layout persistence
"""

import base64
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtCore import Qt, QTimer, QStandardPaths, QSettings, QRect
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QMainWindow, QDockWidget, QTabWidget, QSplitter


class LayoutPersistenceManager:
    """
    Manages layout persistence for the main window and dock widgets.

    This class handles saving and restoring window geometry, dock positions,
    tab states, and other layout-related settings to provide a consistent
    user experience across application sessions.
    """

    def __init__(
        self, main_window: QMainWindow, logger: Optional[logging.Logger] = None
    ) -> None:
        """
        Initialize the layout persistence manager.

        Args:
            main_window: The main window instance
            logger: Optional logger instance for debugging
        """
        self.main_window = main_window
        self.logger = logger or logging.getLogger(__name__)
        self._layout_save_timer = None
        self._default_layout_state = None
        self._default_geometry = None

    # Backwards compatibility helpers
    def _init_layout_persistence(self) -> None:
        """Initialize layout persistence defaults (legacy API)."""
        self.save_default_layout_state()

    def reset_dock_layout_and_save(self) -> None:
        """Reset layout and persist immediately (legacy API)."""
        self.reset_dock_layout()
        try:
            self.schedule_layout_save()
        except Exception:
            pass

    def _validate_geometry_for_screens(self, geom_bytes: bytes) -> bytes:
        """
        Validate and clamp geometry to available screen bounds.

        Fixes multi-monitor issues where saved positions may be outside current screen bounds.
        """
        try:
            # Create a temporary rect to extract geometry info
            temp_window = QMainWindow()
            if not temp_window.restoreGeometry(geom_bytes):
                return geom_bytes

            rect = temp_window.geometry()
            screens = QGuiApplication.screens()

            if not screens:
                return geom_bytes

            # Get combined virtual geometry of all screens
            virtual_rect = QRect()
            for screen in screens:
                virtual_rect = virtual_rect.united(screen.geometry())

            # If geometry is completely outside virtual desktop, clamp it
            if not virtual_rect.intersects(rect):
                # Move to primary screen
                primary_screen = QGuiApplication.primaryScreen()
                if primary_screen:
                    screen_geom = primary_screen.availableGeometry()
                    rect.moveTo(screen_geom.x() + 100, screen_geom.y() + 100)

            # Ensure window is not too large
            if rect.width() > virtual_rect.width():
                rect.setWidth(virtual_rect.width() - 100)
            if rect.height() > virtual_rect.height():
                rect.setHeight(virtual_rect.height() - 100)

            temp_window.setGeometry(rect)
            return temp_window.saveGeometry()
        except Exception:
            return geom_bytes

    def save_default_layout_state(self) -> None:
        """Save the default geometry/state for later restore."""
        try:
            self._default_layout_state = self.main_window.saveState()
            self._default_geometry = self.main_window.saveGeometry()
        except Exception:
            self._default_layout_state = None
            self._default_geometry = None

    def save_current_layout_as_default(self) -> None:
        """Save the current layout as the default for fresh installations."""
        try:
            # Only save as default if no default exists yet (fresh installation)
            settings = QSettings()
            if not settings.contains("layout/default_saved"):
                geom = bytes(self.main_window.saveGeometry())
                state = bytes(self.main_window.saveState())

                # Save as default layout
                default_payload = {
                    "default_window_geometry": base64.b64encode(geom).decode("ascii"),
                    "default_window_state": base64.b64encode(state).decode("ascii"),
                    "default_layout_version": 1,
                    "default_saved": True,
                }

                # Also save active hero tab index as default
                try:
                    if hasattr(self.main_window, "hero_tabs") and isinstance(
                        self.main_window.hero_tabs, QTabWidget
                    ):
                        default_payload["default_hero_tab_index"] = int(
                            self.main_window.hero_tabs.currentIndex()
                        )
                except Exception:
                    pass

                # Merge with existing settings
                current_settings = self.read_settings_json()
                current_settings.update(default_payload)
                self.write_settings_json(current_settings)

                # Mark that default has been saved
                settings.setValue("layout/default_saved", True)
                self.logger.info(
                    "Saved current layout as default for fresh installations"
                )
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning("Failed to save current layout as default: %s", e)

    def reset_dock_layout(self) -> None:
        """Restore dock widgets to their default docking layout."""
        try:
            # First try to load saved default layout (for fresh installations)
            settings = self.read_settings_json()
            default_geom = settings.get("default_window_geometry")
            default_state = settings.get("default_window_state")

            if default_geom and default_state:
                try:
                    geom = base64.b64decode(default_geom)
                    state = base64.b64decode(default_state)
                    # Validate geometry for multi-monitor setups
                    geom = self._validate_geometry_for_screens(geom)
                    restored = self.main_window.restoreGeometry(
                        geom
                    ) and self.main_window.restoreState(state)
                    if restored:
                        self.logger.info("Restored default layout from saved defaults")
                        # Restore default hero tab if available
                        try:
                            default_hero_idx = settings.get("default_hero_tab_index")
                            if (
                                isinstance(default_hero_idx, int)
                                and hasattr(self.main_window, "hero_tabs")
                                and isinstance(self.main_window.hero_tabs, QTabWidget)
                                and 0
                                <= default_hero_idx
                                < self.main_window.hero_tabs.count()
                            ):
                                self.main_window.hero_tabs.setCurrentIndex(
                                    default_hero_idx
                                )
                        except Exception:
                            pass
                        self.schedule_layout_save()
                        return
                except Exception:
                    pass

            # Fallback to hardcoded defaults if no saved default
            if getattr(self, "_default_geometry", None):
                self.main_window.restoreGeometry(self._default_geometry)
            if getattr(self, "_default_layout_state", None):
                # restoreState returns bool; ignore on failure
                self.main_window.restoreState(self._default_layout_state)
        except Exception:
            pass
        # Fallback: programmatically re-dock common widgets
        self.redock_all()
        # Persist the reset layout
        try:
            self.schedule_layout_save()
        except Exception:
            pass

    def redock_all(self) -> None:
        """Force re-dock of known dock widgets to their default areas."""
        try:
            if hasattr(self.main_window, "model_library_dock"):
                self.main_window.model_library_dock.setFloating(False)
                self.main_window.addDockWidget(
                    Qt.LeftDockWidgetArea, self.main_window.model_library_dock
                )
            if hasattr(self.main_window, "properties_dock"):
                self.main_window.properties_dock.setFloating(False)
                self.main_window.addDockWidget(
                    Qt.RightDockWidgetArea, self.main_window.properties_dock
                )
            if hasattr(self.main_window, "metadata_dock"):
                self.main_window.metadata_dock.setFloating(False)
                self.main_window.addDockWidget(
                    Qt.RightDockWidgetArea, self.main_window.metadata_dock
                )
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning("Failed to re-dock widgets: %s", str(e))

    def settings_json_path(self) -> Path:
        """Return AppData settings.json path."""
        app_data = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
        app_data.mkdir(parents=True, exist_ok=True)
        return app_data / "settings.json"

    def read_settings_json(self) -> Dict[str, Any]:
        """Read settings from JSON file."""
        try:
            p = self.settings_json_path()
            if p.exists():
                with p.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
        except Exception:
            pass
        return {}

    def write_settings_json(self, data: Dict[str, Any]) -> None:
        """Write settings to JSON file."""
        try:
            p = self.settings_json_path()
            with p.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def init_layout_persistence(self) -> None:
        """Initialize debounced autosave timer."""
        try:
            self._layout_save_timer = QTimer(self.main_window)
            self._layout_save_timer.setSingleShot(True)
            self._layout_save_timer.setInterval(700)  # ms debounce
            self._layout_save_timer.timeout.connect(self.save_current_layout)
        except Exception:
            pass

    def schedule_layout_save(self) -> None:
        """Request a debounced layout save."""
        try:
            if hasattr(self, "_layout_save_timer"):
                self._layout_save_timer.start()
        except Exception:
            pass

    def save_current_layout(self) -> None:
        """Persist current window geometry, dock layout, and navigation state to settings.json."""
        try:
            geom = bytes(self.main_window.saveGeometry())
            state = bytes(self.main_window.saveState())

            # Persist base window geometry/state
            payload = {
                "window_geometry": base64.b64encode(geom).decode("ascii"),
                "window_state": base64.b64encode(state).decode("ascii"),
                "layout_version": 1,
            }

            # Persist central splitter sizes if applicable (legacy path)
            try:
                cw = self.main_window.centralWidget()
                if isinstance(cw, QSplitter):
                    sizes = cw.sizes()
                    if sizes:
                        payload["central_splitter_sizes"] = [int(s) for s in sizes]
            except Exception:
                pass

            # Persist active main tab index if available
            try:
                if hasattr(self.main_window, "main_tabs") and isinstance(
                    self.main_window.main_tabs, QTabWidget
                ):
                    payload["active_main_tab_index"] = int(
                        self.main_window.main_tabs.currentIndex()
                    )
            except Exception:
                pass

            # Persist active center tab index (inside "3d Model") if available
            try:
                if hasattr(self.main_window, "center_tabs") and isinstance(
                    self.main_window.center_tabs, QTabWidget
                ):
                    payload["active_center_tab_index"] = int(
                        self.main_window.center_tabs.currentIndex()
                    )
            except Exception:
                pass
            # Persist active hero tab index if available
            try:
                if hasattr(self.main_window, "hero_tabs") and isinstance(
                    self.main_window.hero_tabs, QTabWidget
                ):
                    payload["active_hero_tab_index"] = int(
                        self.main_window.hero_tabs.currentIndex()
                    )
            except Exception:
                pass

            settings = self.read_settings_json()
            settings.update(payload)
            self.write_settings_json(settings)
            self.logger.debug("Layout autosaved")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning("Failed to save current layout: %s", e)

    def load_saved_layout(self) -> bool:
        """Restore previously saved layout from settings.json. Returns True if successful."""
        try:
            settings = self.read_settings_json()
            g64 = settings.get("window_geometry")
            s64 = settings.get("window_state")
            ok_any = False
            if g64:
                try:
                    geom = base64.b64decode(g64)
                    # Validate geometry for multi-monitor setups
                    geom = self._validate_geometry_for_screens(geom)
                    ok_any = self.main_window.restoreGeometry(geom) or ok_any
                except Exception:
                    pass
            if s64:
                try:
                    state = base64.b64decode(s64)
                    ok_any = self.main_window.restoreState(state) or ok_any
                except Exception:
                    pass

            # If central is already a splitter, restore sizes
            try:
                cw = self.main_window.centralWidget()
                if isinstance(cw, QSplitter):
                    sizes = settings.get("central_splitter_sizes")
                    if isinstance(sizes, list) and sizes:
                        cw.setSizes([int(s) for s in sizes])
            except Exception:
                pass

            if ok_any:
                self.logger.info("Restored window layout from saved settings")
            return ok_any
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning("Failed to load saved layout: %s", e)
            return False

    def connect_layout_autosave(self, dock: QDockWidget | None = None) -> None:
        """Connect signals from a dock to trigger autosave."""
        if dock is None:
            return
        try:
            dock.topLevelChanged.connect(lambda _=False: self.schedule_layout_save())
            # Some bindings expose dockLocationChanged(area)
            if hasattr(dock, "dockLocationChanged"):
                dock.dockLocationChanged.connect(
                    lambda _area=None: self.schedule_layout_save()
                )
            dock.visibilityChanged.connect(lambda _=False: self.schedule_layout_save())
        except Exception:
            pass


# Convenience function for easy layout persistence setup
def setup_layout_persistence(
    main_window: QMainWindow, logger: Optional[logging.Logger] = None
) -> LayoutPersistenceManager:
    """
    Convenience function to set up layout persistence for a main window.

    Args:
        main_window: The main window to set up layout persistence for
        logger: Optional logger instance

    Returns:
        LayoutPersistenceManager instance for further layout operations
    """
    manager = LayoutPersistenceManager(main_window, logger)
    manager.init_layout_persistence()
    return manager
