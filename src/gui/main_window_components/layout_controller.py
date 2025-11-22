"""
Layout controller for the main window.

Moves dock snapping, context menus, and layout reset helpers out of main_window.py.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QSettings, QTimer
from PySide6.QtWidgets import QApplication, QDockWidget, QMenu

from src.gui.window.dock_snapping import SnapOverlayLayer, DockDragHandler


class LayoutController:
    """Encapsulates dock layout behaviors for the main window."""

    def __init__(self, main_window) -> None:
        self.main = main_window
        self.logger = getattr(main_window, "logger", None)
        self._snap_layer: Optional[SnapOverlayLayer] = None
        self._snap_handlers: dict[str, DockDragHandler] = {}

    # ---- Dock snapping / context menus ------------------------------------
    def snap_dock_to_edge(self, dock: QDockWidget, edge: str) -> None:
        try:
            area_map = {
                "left": Qt.LeftDockWidgetArea,
                "right": Qt.RightDockWidgetArea,
                "top": Qt.TopDockWidgetArea,
                "bottom": Qt.BottomDockWidgetArea,
            }
            target_area = area_map.get(edge)
            if target_area is None:
                if self.logger:
                    self.logger.warning("Invalid snap edge: %s", edge)
                return

            if not (dock.allowedAreas() & target_area):
                if self.logger:
                    self.logger.debug(
                        "Dock %s not allowed in %s area", dock.windowTitle(), edge
                    )
                return

            neighbors = [
                d
                for d in self.main.findChildren(QDockWidget)
                if d is not dock and self.main.dockWidgetArea(d) == target_area
            ]
            neighbor = neighbors[0] if neighbors else None

            dock.setFloating(False)
            self.main.addDockWidget(target_area, dock)
            dock.raise_()
            dock.setProperty("_last_dock_edge", edge)

            if neighbor:
                try:
                    if target_area == Qt.BottomDockWidgetArea:
                        self.main.splitDockWidget(neighbor, dock, Qt.Horizontal)
                    else:
                        self.main.tabifyDockWidget(neighbor, dock)
                except Exception as exc:
                    if self.logger:
                        self.logger.debug(
                            "Failed to arrange dock '%s' with '%s': %s",
                            dock.windowTitle(),
                            neighbor.windowTitle(),
                            exc,
                        )

            if self.logger:
                self.logger.info(
                    "Snapped dock '%s' to %s area", dock.windowTitle(), edge
                )
            self.main._save_window_settings()
        except Exception as exc:
            if self.logger:
                self.logger.warning("Failed to snap dock to %s: %s", edge, exc)

    def register_dock_for_snapping(self, dock: QDockWidget) -> None:
        try:
            settings = QSettings()
            snapping_enabled = settings.value("dock_snapping/enabled", True, type=bool)
            if not snapping_enabled and self.logger:
                self.logger.info(
                    "Dock snapping disabled in settings; re-enabling for dock '%s'",
                    dock.windowTitle(),
                )
                settings.setValue("dock_snapping/enabled", True)

            if not dock.objectName():
                dock.setObjectName(
                    dock.windowTitle().replace(" ", "").replace("/", "_")
                )
            else:
                existing_names = {
                    d.objectName() for d in self.main.findChildren(QDockWidget)
                }
                if list(existing_names).count(dock.objectName()) > 1:
                    dock.setObjectName(f"{dock.objectName()}_{id(dock)}")

            dock.setAllowedAreas(
                Qt.LeftDockWidgetArea
                | Qt.RightDockWidgetArea
                | Qt.TopDockWidgetArea
                | Qt.BottomDockWidgetArea
            )
            dock.setContextMenuPolicy(Qt.CustomContextMenu)

            def _show_menu(point):
                self.show_dock_context_menu(dock, point)

            dock.customContextMenuRequested.connect(_show_menu)
            dock.topLevelChanged.connect(
                lambda floating, d=dock: self._on_dock_top_level_changed(d, floating)
            )
            self._on_dock_top_level_changed(dock, dock.isFloating())

            if self._snap_layer is None:
                self._snap_layer = SnapOverlayLayer(self.main)
                self._snap_handlers = {}

            handler = DockDragHandler(self.main, dock, self._snap_layer, self.logger)
            self._snap_handlers[dock.objectName()] = handler
            dock.installEventFilter(handler)

            if self.logger:
                self.logger.debug(
                    "Registered dock '%s' for snapping/context menus",
                    dock.windowTitle(),
                )
        except Exception as exc:
            if self.logger:
                self.logger.warning("Failed to prepare dock context menu: %s", exc)

    def refresh_dock_snapping(self) -> None:
        try:
            if self._snap_layer is None:
                self._snap_layer = SnapOverlayLayer(self.main)
                self._snap_handlers = {}
            for dock in self.main.findChildren(QDockWidget):
                try:
                    if not dock.objectName():
                        dock.setObjectName(
                            dock.windowTitle().replace(" ", "").replace("/", "_")
                        )
                    if dock.objectName() not in self._snap_handlers:
                        self.register_dock_for_snapping(dock)
                except Exception:
                    continue
        except Exception as exc:
            if self.logger:
                self.logger.debug(
                    "Failed to refresh dock snapping registration: %s", exc
                )

    def show_dock_context_menu(self, dock: QDockWidget, point) -> None:
        menu = QMenu(dock)
        edit_enabled = getattr(self.main, "layout_edit_mode", False)

        def add_snap_action(text: str, edge: str) -> None:
            action = menu.addAction(
                text, lambda e=edge: self.snap_dock_to_edge(dock, e)
            )
            action.setEnabled(edit_enabled)

        add_snap_action("Dock Left", "left")
        add_snap_action("Dock Right", "right")
        add_snap_action("Dock Top", "top")
        add_snap_action("Dock Bottom", "bottom")

        menu.addSeparator()
        last_edge = dock.property("_last_dock_edge") or "right"
        re_dock_action = menu.addAction(
            "Re-dock to Previous Edge", lambda: self.snap_dock_to_edge(dock, last_edge)
        )
        re_dock_action.setEnabled(edit_enabled)

        tab_menu = menu.addMenu("Stack With...")
        others = [d for d in self.main.findChildren(QDockWidget) if d is not dock]
        if not others:
            tab_menu.setEnabled(False)
        else:
            for other in others:
                action = tab_menu.addAction(
                    other.windowTitle(), lambda o=other: self._tabify_docks(o, dock)
                )
                action.setEnabled(edit_enabled)

        menu.addSeparator()
        reset_action = menu.addAction(
            "Reset All Docks to Default Layout", self.main._reset_dock_layout_and_save
        )
        reset_action.setEnabled(True)

        menu.exec(dock.mapToGlobal(point))

    def _tabify_docks(self, base: QDockWidget, target: QDockWidget) -> None:
        try:
            if target.isFloating():
                target.setFloating(False)
            self.main.tabifyDockWidget(base, target)
            target.raise_()
        except Exception as exc:
            if self.logger:
                self.logger.warning("Failed to tabify docks: %s", exc)

    def _edge_from_area(self, area: Qt.DockWidgetArea) -> Optional[str]:
        mapping = {
            Qt.LeftDockWidgetArea: "left",
            Qt.RightDockWidgetArea: "right",
            Qt.TopDockWidgetArea: "top",
            Qt.BottomDockWidgetArea: "bottom",
        }
        return mapping.get(area)

    def _on_dock_top_level_changed(self, dock: QDockWidget, floating: bool) -> None:
        if floating:
            return
        area = self.main.dockWidgetArea(dock)
        edge = self._edge_from_area(area)
        if edge:
            dock.setProperty("_last_dock_edge", edge)

    # Public helpers so callers avoid touching protected members
    def edge_from_area(self, area: Qt.DockWidgetArea) -> Optional[str]:
        return self._edge_from_area(area)

    def on_dock_top_level_changed(self, dock: QDockWidget, floating: bool) -> None:
        self._on_dock_top_level_changed(dock, floating)

    def tabify_docks(self, base: QDockWidget, target: QDockWidget) -> None:
        self._tabify_docks(base, target)

    # ---- Layout reset/save helpers ---------------------------------------
    def reset_layout(self) -> None:
        """Clear saved layout data and apply defaults."""
        from PySide6.QtCore import QSettings

        settings = QSettings()
        for key in [
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
        ]:
            if settings.contains(key):
                settings.remove(key)
        # Refresh snapping and restore baseline geometry
        try:
            self.refresh_dock_snapping()
        except Exception:
            pass
        try:
            self.main._restore_window_geometry(default=True)
            self.main._save_window_settings()
        except Exception:
            pass

    def save_current_layout_as_default(self) -> None:
        """Persist the current window/dock layout as the default template."""
        try:
            from PySide6.QtCore import QSettings

            settings = QSettings()
            settings.setValue("ui/default_window_geometry", self.main.saveGeometry())
            settings.setValue("ui/default_window_state", self.main.saveState())
            settings.setValue("ui/default_window_width", self.main.width())
            settings.setValue("ui/default_window_height", self.main.height())
            settings.setValue("ui/default_window_x", self.main.x())
            settings.setValue("ui/default_window_y", self.main.y())
            settings.sync()
            if self.logger:
                self.logger.info("Saved current layout as default reset template")
            try:
                self.main.statusBar().showMessage(
                    "Current layout saved as default", 3000
                )
            except Exception:
                pass
        except Exception as exc:
            if self.logger:
                self.logger.warning("Failed to save current layout as default: %s", exc)
            try:
                self.main.statusBar().showMessage("Failed to save layout", 3000)
            except Exception:
                pass

    def restore_window_geometry_early(self) -> None:
        """Restore saved window geometry/state early in init."""
        from PySide6.QtCore import QSettings

        try:
            settings = QSettings()
            remember_loc = settings.value("window/remember_location", True, type=bool)
            if remember_loc and settings.contains("window_geometry"):
                geometry_data = settings.value("window_geometry")
                if geometry_data and self.main.restoreGeometry(geometry_data):
                    if self.logger:
                        self.logger.info(
                            "Window geometry restored successfully during init"
                        )
                    return

            default_width, default_height = self.main._calculate_centered_default_size()
            self.main._apply_default_window_geometry(default_width, default_height)
            if self.logger:
                self.logger.debug("Applied default centered geometry during init")
        except Exception as exc:
            if self.logger:
                self.logger.warning(
                    "FAILED to apply default window geometry during init: %s", exc
                )

    def restore_window_geometry_from_settings(
        self, default_width: int, default_height: int
    ) -> None:
        """Restore geometry from QSettings if available, else apply defaults."""
        from PySide6.QtCore import QSettings

        settings = QSettings()
        remember_loc = settings.value(
            "window/remember_location",
            getattr(self.main, "remember_window_location", True),
            type=bool,
        )
        remember_size = settings.value(
            "window/remember_window_size",
            getattr(self.main, "remember_window_size", True),
            type=bool,
        )

        if (remember_loc or remember_size) and settings.contains("window_geometry"):
            geometry_data = settings.value("window_geometry")
            if geometry_data and self.main.restoreGeometry(geometry_data):
                if self.logger:
                    self.logger.info("Window geometry restored from saved settings")
                return

        width = settings.value("window/width", default_width, type=int)
        height = settings.value("window/height", default_height, type=int)
        x_pos = settings.value("window/x", -1, type=int)
        y_pos = settings.value("window/y", -1, type=int)

        width = max(800, min(width, 3840))
        height = max(600, min(height, 2160))

        if remember_loc and x_pos >= 0 and y_pos >= 0:
            self.main.move(x_pos, y_pos)
        if remember_size:
            self.main.resize(width, height)
        if self.logger:
            self.logger.info(
                "Window geometry applied from explicit settings: %sx%s at (%s,%s)",
                width,
                height,
                x_pos,
                y_pos,
            )

        if remember_size:
            is_maximized = settings.value("window/maximized", False, type=bool)
            if is_maximized:
                self.main.showMaximized()

    def restore_window_state(self) -> None:
        """Restore dock layout/state from QSettings."""
        from PySide6.QtCore import QSettings

        try:
            settings = QSettings()
            if settings.contains("window_geometry"):
                geometry_data = settings.value("window_geometry")
                if geometry_data:
                    self.main.restoreGeometry(geometry_data)
            if settings.contains("window_state"):
                state_data = settings.value("window_state")
                if state_data:
                    self.main.restoreState(state_data)
        except Exception as exc:
            if self.logger:
                self.logger.warning("Failed to restore window state: %s", exc)

    def save_window_settings(self) -> None:
        """Save dock state and optionally geometry/position."""
        from PySide6.QtCore import QSettings

        try:
            settings = QSettings()
            self.ensure_dock_object_names()
            settings.setValue("window_state", self.main.saveState())

            remember_loc = settings.value(
                "window/remember_location",
                getattr(self.main, "remember_window_location", True),
                type=bool,
            )
            remember_size = settings.value(
                "window/remember_window_size",
                getattr(self.main, "remember_window_size", True),
                type=bool,
            )
            if remember_loc or remember_size:
                settings.setValue("window_geometry", self.main.saveGeometry())
                if remember_size:
                    settings.setValue("window/width", self.main.width())
                    settings.setValue("window/height", self.main.height())
                    settings.setValue("window/maximized", self.main.isMaximized())
                if remember_loc:
                    settings.setValue("window/x", self.main.x())
                    settings.setValue("window/y", self.main.y())

            if hasattr(self.main, "hero_tabs") and self.main.hero_tabs:
                settings.setValue(
                    "ui/active_hero_tab_index", self.main.hero_tabs.currentIndex()
                )

            settings.sync()
            if self.logger:
                self.logger.info(
                    "Window state saved%s",
                    (
                        ""
                        if (remember_loc or remember_size)
                        else " (geometry not persisted)"
                    ),
                )
        except Exception as exc:
            if self.logger:
                self.logger.error("Failed to save window state: %s", exc)

    def setup_periodic_window_state_save(self) -> None:
        """Set up periodic window state saving (every 5 seconds)."""
        from PySide6.QtCore import QTimer

        try:
            self._window_state_save_timer = QTimer(self.main)
            self._window_state_save_timer.timeout.connect(
                self.periodic_save_window_state
            )
            self._window_state_save_timer.start(5000)
            if self.logger:
                self.logger.debug(
                    "Periodic window state save timer started (5 second interval)"
                )
        except Exception as exc:
            if self.logger:
                self.logger.warning(
                    "Failed to set up periodic window state save: %s", exc
                )

    def periodic_save_window_state(self) -> None:
        """Periodically save window state without verbose logging."""
        from PySide6.QtCore import QSettings

        try:
            if self.main.isMinimized():
                if self.logger:
                    self.logger.debug("Periodic save skipped (window minimized)")
                return
            try:
                docks = self.main.findChildren(QDockWidget)
                if any(d.isFloating() for d in docks):
                    if self.logger:
                        self.logger.debug(
                            "Periodic save skipped (floating docks present)"
                        )
                    return
            except Exception:
                pass

            settings = QSettings()
            self.ensure_dock_object_names()
            settings.setValue("window_state", self.main.saveState())

            remember_loc = settings.value(
                "window/remember_location",
                getattr(self.main, "remember_window_location", True),
                type=bool,
            )
            remember_size = settings.value(
                "window/remember_window_size",
                getattr(self.main, "remember_window_size", True),
                type=bool,
            )
            if remember_loc or remember_size:
                settings.setValue("window_geometry", self.main.saveGeometry())
                if remember_size:
                    settings.setValue("window/width", self.main.width())
                    settings.setValue("window/height", self.main.height())
                    settings.setValue("window/maximized", self.main.isMaximized())
                if remember_loc:
                    settings.setValue("window/x", self.main.x())
                    settings.setValue("window/y", self.main.y())

            settings.sync()
            if self.logger:
                self.logger.debug(
                    "Periodic save: dock layout%s",
                    " + geometry" if (remember_loc or remember_size) else " only",
                )
        except Exception as exc:
            if self.logger:
                self.logger.warning("Failed to periodically save window state: %s", exc)

    def ensure_dock_object_names(self) -> None:
        """Ensure every dock has a stable objectName before saving."""
        try:
            for dock in self.main.findChildren(QDockWidget):
                name = dock.objectName().strip()
                if not name:
                    safe = (
                        dock.windowTitle().replace(" ", "").replace("/", "_")
                        or f"Dock{hex(id(dock))}"
                    )
                    dock.setObjectName(safe)
        except Exception:
            pass

    def place_camera_controls_bottom(self, dock: Optional[QDockWidget] = None) -> None:
        """Place the camera controls dock along the bottom edge."""
        try:
            if hasattr(self.main, "_camera_bottom_spacers"):
                try:
                    for spacer in getattr(self.main, "_camera_bottom_spacers") or []:
                        try:
                            self.main.removeDockWidget(spacer)
                        except Exception:
                            pass
                    delattr(self.main, "_camera_bottom_spacers")
                except Exception:
                    pass

            if dock is None:
                dock = getattr(self.main, "camera_controls_dock", None)
                if dock is None:
                    return

            if not dock.objectName():
                dock.setObjectName("CameraControlsDock")

            try:
                dock.setMinimumWidth(1)
                dock.setMaximumWidth(16777215)
                dock.setSizePolicy(dock.sizePolicy().Expanding, dock.sizePolicy().Fixed)
            except Exception:
                pass

            self.main.addDockWidget(Qt.BottomDockWidgetArea, dock)
            dock.setProperty("_last_dock_edge", "bottom")
        except Exception:
            pass

    def ensure_default_window_settings(
        self, default_width: int, default_height: int
    ) -> None:
        """Seed QSettings with a default window position/size if none exist."""
        from PySide6.QtCore import QSettings

        try:
            settings = QSettings()
            missing = not all(
                settings.contains(key)
                for key in ("window/width", "window/height", "window/x", "window/y")
            )
            if missing:
                settings.setValue("window/width", max(800, default_width))
                settings.setValue("window/height", max(600, default_height))
                settings.setValue("window/x", 50)
                settings.setValue("window/y", 50)
                settings.setValue("window/maximized", False)
                settings.sync()
                if self.logger:
                    self.logger.info("Seeded default window position/size in settings")
        except Exception:
            pass

    # ---- Geometry / restore helpers --------------------------------------
    def log_geometry(self, label: str) -> None:
        """Log current window geometry details for diagnostics."""
        try:
            self.logger.info(
                "%s: size=%sx%s pos=(%s,%s) maximized=%s",
                label,
                self.main.width(),
                self.main.height(),
                self.main.x(),
                self.main.y(),
                self.main.isMaximized(),
            )
        except Exception:
            pass

    def calculate_centered_default_size(self) -> tuple[int, int]:
        """Calculate an 80% height 4:3 window size based on the primary screen."""
        try:
            screen = self.main.screen() or QApplication.primaryScreen()
            if screen:
                geom = screen.availableGeometry()
                target_height = int(geom.height() * 0.8)
                target_width = int(target_height * 4 / 3)
                return max(800, target_width), max(600, target_height)
        except Exception:
            pass
        return 1200, 800

    def apply_default_window_geometry(self, width: int, height: int) -> None:
        """Apply default geometry centered on the current screen."""
        try:
            screen = self.main.screen() or QApplication.primaryScreen()
            if screen:
                geom = screen.availableGeometry()
                w = min(width, geom.width())
                h = min(height, geom.height())
                x = geom.x() + (geom.width() - w) // 2
                y = geom.y() + (geom.height() - h) // 2
                self.main.setGeometry(x, y, w, h)
                return
        except Exception:
            pass
        self.main.resize(width, height)

    def deferred_geometry_restoration(self) -> None:
        """Apply default geometry after show when no saved geometry is present."""
        try:
            settings = QSettings()
            has_saved_geometry = settings.contains("window_geometry") or (
                settings.contains("window/width") and settings.contains("window/height")
            )

            remember_loc = settings.value(
                "window/remember_location",
                getattr(self.main, "remember_window_location", True),
                type=bool,
            )
            remember_size = settings.value(
                "window/remember_window_size",
                getattr(self.main, "remember_window_size", True),
                type=bool,
            )

            if has_saved_geometry and (remember_loc or remember_size):
                if self.logger:
                    self.logger.info(
                        "Skipping post-show centering; saved geometry present and respected"
                    )
                return

            if self.logger:
                self.logger.info(
                    "Applying default centered geometry (post-show, no saved geometry)"
                )
            default_width, default_height = self.calculate_centered_default_size()
            self.apply_default_window_geometry(default_width, default_height)
        except Exception as exc:
            if self.logger:
                self.logger.warning("Failed to apply default geometry after show: %s", exc)

    def deferred_dock_layout_restoration(self) -> None:
        """Restore dock layout after the window is shown to avoid repaint issues."""
        from PySide6.QtCore import QSettings

        try:
            if self.logger:
                self.logger.debug("Starting deferred dock layout restoration after show")

            settings = QSettings()
            dock_state = settings.value("window_state", None) or settings.value(
                "window/dock_state", None
            )

            if dock_state:
                self.main.restoreState(dock_state)
                if self.logger:
                    self.logger.debug("Dock layout restored from QSettings")
            else:
                if self.logger:
                    self.logger.debug("No saved dock layout found")
        except Exception as exc:
            if self.logger:
                self.logger.warning("Failed to restore dock layout: %s", exc)
        finally:
            try:
                self.refresh_dock_snapping()
            except Exception:
                pass
