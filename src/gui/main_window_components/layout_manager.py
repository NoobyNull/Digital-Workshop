"""
Layout management for main window.

Handles dock layout persistence, snapping, and restoration.
"""

import base64
import json
from pathlib import Path
from typing import Optional, List

from PySide6.QtCore import QTimer, QStandardPaths
from PySide6.QtWidgets import QMainWindow, QDockWidget, QSplitter, QTabWidget

from src.core.logging_config import get_logger, log_function_call


logger = get_logger(__name__)


class LayoutManager:
    """Manages window layout persistence and dock snapping."""

    def __init__(self, main_window: QMainWindow):
        """
        Initialize layout manager.

        Args:
            main_window: The main window instance
        """
        self.main_window = main_window
        self.layout_save_timer = None
        self._init_layout_persistence()

    def _settings_json_path(self) -> Path:
        """Get settings.json path."""
        app_data = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
        app_data.mkdir(parents=True, exist_ok=True)
        return app_data / "settings.json"

    def _read_settings_json(self) -> dict:
        """Read settings from JSON file."""
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
        """Write settings to JSON file."""
        try:
            p = self._settings_json_path()
            with p.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _init_layout_persistence(self) -> None:
        """Initialize debounced autosave timer."""
        try:
            self.layout_save_timer = QTimer(self.main_window)
            self.layout_save_timer.setSingleShot(True)
            self.layout_save_timer.setInterval(700)  # ms debounce
            self.layout_save_timer.timeout.connect(self.save_current_layout)
        except Exception:
            pass

    def schedule_layout_save(self) -> None:
        """Request a debounced layout save."""
        try:
            if self.layout_save_timer:
                self.layout_save_timer.start()
        except Exception:
            pass

    @log_function_call(logger)
    def save_current_layout(self) -> None:
        """Persist current window geometry, dock layout, and navigation state."""
        try:
            geom = bytes(self.main_window.saveGeometry())
            state = bytes(self.main_window.saveState())

            payload = {
                "window_geometry": base64.b64encode(geom).decode("ascii"),
                "window_state": base64.b64encode(state).decode("ascii"),
                "layout_version": 1,
            }

            # Persist central splitter sizes
            try:
                cw = self.main_window.centralWidget()
                if isinstance(cw, QSplitter):
                    sizes = cw.sizes()
                    if sizes:
                        payload["central_splitter_sizes"] = [int(s) for s in sizes]
            except Exception:
                pass

            # Persist active main tab index
            try:
                if hasattr(self.main_window, "main_tabs") and isinstance(
                    self.main_window.main_tabs, QTabWidget
                ):
                    payload["active_main_tab_index"] = int(
                        self.main_window.main_tabs.currentIndex()
                    )
            except Exception:
                pass

            # Persist active center tab index
            try:
                if hasattr(self.main_window, "center_tabs") and isinstance(
                    self.main_window.center_tabs, QTabWidget
                ):
                    payload["active_center_tab_index"] = int(
                        self.main_window.center_tabs.currentIndex()
                    )
            except Exception:
                pass

            # Persist active hero tab index
            try:
                if hasattr(self.main_window, "hero_tabs") and isinstance(
                    self.main_window.hero_tabs, QTabWidget
                ):
                    payload["active_hero_tab_index"] = int(
                        self.main_window.hero_tabs.currentIndex()
                    )
            except Exception:
                pass

            settings = self._read_settings_json()
            settings.update(payload)
            self._write_settings_json(settings)
            logger.debug("Layout autosaved")

        except Exception as e:
            logger.warning(f"Failed to save current layout: {e}")

    @log_function_call(logger)
    def load_saved_layout(self) -> bool:
        """Restore previously saved layout from settings.json."""
        try:
            settings = self._read_settings_json()

            # Restore window geometry
            if "window_geometry" in settings:
                geom_b64 = settings["window_geometry"]
                geom = base64.b64decode(geom_b64.encode("ascii"))
                self.main_window.restoreGeometry(geom)

            # Restore window state
            if "window_state" in settings:
                state_b64 = settings["window_state"]
                state = base64.b64decode(state_b64.encode("ascii"))
                self.main_window.restoreState(state)

            # Restore central splitter sizes
            try:
                if "central_splitter_sizes" in settings:
                    cw = self.main_window.centralWidget()
                    if isinstance(cw, QSplitter):
                        sizes = settings["central_splitter_sizes"]
                        cw.setSizes(sizes)
            except Exception:
                pass

            # Restore active main tab index
            try:
                if "active_main_tab_index" in settings:
                    if hasattr(self.main_window, "main_tabs"):
                        idx = settings["active_main_tab_index"]
                        self.main_window.main_tabs.setCurrentIndex(idx)
            except Exception:
                pass

            # Restore active center tab index
            try:
                if "active_center_tab_index" in settings:
                    if hasattr(self.main_window, "center_tabs"):
                        idx = settings["active_center_tab_index"]
                        self.main_window.center_tabs.setCurrentIndex(idx)
            except Exception:
                pass

            # Restore active hero tab index
            try:
                if "active_hero_tab_index" in settings:
                    if hasattr(self.main_window, "hero_tabs"):
                        idx = settings["active_hero_tab_index"]
                        self.main_window.hero_tabs.setCurrentIndex(idx)
            except Exception:
                pass

            logger.debug("Layout restored from settings")
            return True

        except Exception as e:
            logger.warning(f"Failed to load saved layout: {e}")
            return False

    def connect_layout_autosave(self, dock: QDockWidget) -> None:
        """Connect dock changes to autosave."""
        try:
            dock.topLevelChanged.connect(self.schedule_layout_save)
            dock.visibilityChanged.connect(self.schedule_layout_save)
        except Exception as e:
            logger.warning(f"Failed to connect layout autosave: {e}")

    def iter_docks(self) -> List[QDockWidget]:
        """Iterate over all dock widgets."""
        return self.main_window.findChildren(QDockWidget)

    def reset_dock_layout_and_save(self) -> None:
        """Reset dock layout to default and save."""
        try:
            # Reset all docks to default positions
            for dock in self.iter_docks():
                dock.setFloating(False)
                self.main_window.addDockWidget(dock.allowedAreas(), dock)
                dock.show()

            self.save_current_layout()
            logger.debug("Dock layout reset to default")

        except Exception as e:
            logger.error(f"Failed to reset dock layout: {e}")

