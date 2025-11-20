"""G-code Previewer controller for MainWindow.

Owns creation of the G-code previewer hero tab, its detachable tools dock,
project-context wiring, and file-loading integration so that MainWindow
remains a thin orchestrator.
"""

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QLabel

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from src.gui.main_window import MainWindow


class GcodePreviewController:
    """Controller responsible for G-code Previewer integration."""

    def __init__(self, main_window: "MainWindow") -> None:
        self.main_window = main_window
        self.logger = main_window.logger

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    def setup_gcode_previewer(self) -> None:
        """Create the G-code Previewer tab and its tools dock."""
        try:
            self.logger.info("Attempting to create G-code Previewer widget...")
            from src.gui.gcode_previewer_components import GcodePreviewerWidget

            # Use external tools mode so the right-hand tools live in their own
            # detachable dock widget rather than inside the splitter.
            self.main_window.gcode_previewer_widget = GcodePreviewerWidget(
                self.main_window, use_external_tools=True
            )
            self.main_window.hero_tabs.addTab(
                self.main_window.gcode_previewer_widget, "G Code Previewer"
            )
            self.logger.info("G-code Previewer widget created successfully")

            # Once the previewer exists, set up the detachable G-code tools dock.
            try:
                self._setup_gcode_tools_dock()
            except Exception as dock_error:  # pragma: no cover - defensive
                self.logger.warning("Failed to initialize G-code tools dock: %s", dock_error)

            try:
                self._setup_camera_controls_dock()
            except Exception as dock_error:  # pragma: no cover - defensive
                self.logger.warning("Failed to initialize camera controls dock: %s", dock_error)
        except Exception as e:  # pragma: no cover - defensive
            self.logger.error("Failed to create G-code Previewer widget: %s", e, exc_info=True)
            placeholder = self._create_placeholder(
                "G Code Previewer",
                "G-code Previewer\n\nComponent unavailable.",
            )
            self.main_window.hero_tabs.addTab(placeholder, "G Code Previewer")

    def _create_placeholder(self, title: str, content: str) -> QLabel:
        """Create a simple placeholder widget for the G-code tab.

        This mirrors the behavior of the generic placeholder used in
        MainWindow._add_placeholder_tabs without depending on its
        nested helper.
        """

        label = QLabel(content)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignCenter)
        label.setMinimumSize(320, 240)
        return label

    def _setup_gcode_tools_dock(self) -> None:
        """Set up the detachable G-code tools dock using the native dock system."""
        from src.gui.gcode_previewer_components.gcode_tools_widget import (
            GcodeToolsWidget,
        )

        try:
            self.main_window.gcode_tools_dock = QDockWidget("G-code Tools", self.main_window)
            self.main_window.gcode_tools_dock.setObjectName("GcodeToolsDock")

            # Configure with native Qt dock features
            self.main_window.gcode_tools_dock.setAllowedAreas(
                Qt.LeftDockWidgetArea
                | Qt.RightDockWidgetArea
                | Qt.TopDockWidgetArea
                | Qt.BottomDockWidgetArea
            )
            # Start with layout locked (only closable, not movable)
            self.main_window.gcode_tools_dock.setFeatures(QDockWidget.DockWidgetClosable)

            # Use the renderer from the G-code previewer widget if available.
            renderer = None
            if (
                hasattr(self.main_window, "gcode_previewer_widget")
                and self.main_window.gcode_previewer_widget is not None
            ):
                renderer = getattr(self.main_window.gcode_previewer_widget, "renderer", None)

            self.main_window.gcode_tools_widget = GcodeToolsWidget(renderer, self.main_window)
            self.main_window.gcode_tools_dock.setWidget(self.main_window.gcode_tools_widget)

            # Add to main window using native Qt dock system
            self.main_window.addDockWidget(
                Qt.RightDockWidgetArea, self.main_window.gcode_tools_dock
            )

            # Register for snapping functionality
            try:
                self.main_window._register_dock_for_snapping(  # noqa: SLF001 - intentional
                    self.main_window.gcode_tools_dock
                )
            except Exception as e:  # pragma: no cover - defensive
                self.logger.debug("Failed to register G-code tools dock for snapping: %s", e)

            # Attach this tools widget to the previewer so its signals are wired
            # up when the docked configuration is in use.
            if (
                hasattr(self.main_window, "gcode_previewer_widget")
                and self.main_window.gcode_previewer_widget is not None
            ):
                try:
                    self.main_window.gcode_previewer_widget.attach_tools_widget(
                        self.main_window.gcode_tools_widget
                    )
                except Exception as e:  # pragma: no cover - defensive
                    self.logger.warning("Failed to attach G-code tools widget to previewer: %s", e)

        except Exception as e:  # pragma: no cover - defensive
            self.logger.error("Failed to setup G-code tools dock: %s", e)

    def _setup_camera_controls_dock(self) -> None:
        """Create a dockable camera toolbar for the VTK viewer."""
        if (
            not hasattr(self.main_window, "gcode_previewer_widget")
            or self.main_window.gcode_previewer_widget is None
        ):
            return

        vtk_widget = getattr(self.main_window.gcode_previewer_widget, "vtk_widget", None)
        if vtk_widget is None:
            return

        toolbar = vtk_widget.create_camera_toolbar(self.main_window)
        dock = QDockWidget("Camera Controls", self.main_window)
        dock.setObjectName("CameraControlsDock")
        dock.setAllowedAreas(
            Qt.LeftDockWidgetArea
            | Qt.RightDockWidgetArea
            | Qt.TopDockWidgetArea
            | Qt.BottomDockWidgetArea
        )
        dock.setFeatures(
            QDockWidget.DockWidgetMovable
            | QDockWidget.DockWidgetFloatable
            | QDockWidget.DockWidgetClosable
        )
        dock.setWidget(toolbar)
        # Prefer bottom docking by default so it can sit under the main viewport
        self.main_window._place_camera_controls_bottom(dock)

        try:
            if hasattr(self.main_window, "_register_dock_for_snapping"):
                self.main_window._register_dock_for_snapping(dock)  # noqa: SLF001
        except Exception:
            self.logger.debug("Failed to register camera controls dock for snapping context")

        if hasattr(self.main_window, "_register_dock_for_snapping"):
            try:
                self.main_window._register_dock_for_snapping(dock)  # noqa: SLF001
            except Exception as e:  # pragma: no cover - defensive
                self.logger.debug("Failed to register camera controls dock for snapping: %s", e)

        self.main_window.camera_controls_dock = dock
        dock.visibilityChanged.connect(self._on_camera_dock_visibility_changed)

    def _on_camera_dock_visibility_changed(self, visible: bool) -> None:
        previewer = getattr(self.main_window, "gcode_previewer_widget", None)
        if previewer is None:
            return
        try:
            previewer.sync_camera_controls_checkbox(visible)
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.debug("Failed to sync camera controls checkbox: %s", exc)

    # ------------------------------------------------------------------
    # Project and file integration
    # ------------------------------------------------------------------
    def set_current_project(self, project_id: int) -> None:
        """Attach the current project to the G-code previewer."""
        if not hasattr(self.main_window, "gcode_previewer_widget"):
            return

        if self.main_window.gcode_previewer_widget:
            try:
                self.main_window.gcode_previewer_widget.set_current_project(project_id)
                self.logger.debug("Set current project for G-code Previewer: %s", project_id)
            except Exception as e:  # pragma: no cover - defensive
                self.logger.warning("Failed to set project for G-code Previewer: %s", e)

    def open_gcode_file(self, file_path: str) -> None:
        """Load a G-code file into the previewer."""
        if not hasattr(self.main_window, "gcode_previewer_widget"):
            return

        if self.main_window.gcode_previewer_widget:
            try:
                self.main_window.gcode_previewer_widget.load_gcode_file(file_path)
            except Exception as e:  # pragma: no cover - defensive
                self.logger.error("Failed to load G-code file %s in previewer: %s", file_path, e)
