"""Controller for the Project Details dock in the main window.

This controller owns creation of the Project Details dock and its
`ProjectDetailsWidget`, keeping `MainWindow` focused on orchestration.
"""

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QSizePolicy

from src.gui.theme import MIN_WIDGET_SIZE
from src.gui.project_details_widget import ProjectDetailsWidget

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from src.gui.main_window import MainWindow


class ProjectDetailsController:
    """Controller responsible for the Project Details dock."""

    def __init__(self, main_window: "MainWindow") -> None:
        self.main_window = main_window
        self.logger = main_window.logger

    def setup_project_details_dock(self) -> None:
        """Create and register the Project Details dock and widget."""
        try:
            self.main_window.properties_dock = QDockWidget(
                "Project Details", self.main_window
            )
            self.main_window.properties_dock.setObjectName("PropertiesDock")

            # Configure with native Qt dock features
            self.main_window.properties_dock.setAllowedAreas(
                Qt.LeftDockWidgetArea
                | Qt.RightDockWidgetArea
                | Qt.TopDockWidgetArea
                | Qt.BottomDockWidgetArea
            )
            # Start with layout locked (only closable, not movable)
            self.main_window.properties_dock.setFeatures(QDockWidget.DockWidgetClosable)

            # Create project details widget
            self.main_window.project_details_widget = ProjectDetailsWidget(
                self.main_window
            )
            self.main_window.properties_dock.setWidget(
                self.main_window.project_details_widget
            )

            # Add to main window using native Qt dock system
            self.main_window.addDockWidget(
                Qt.RightDockWidgetArea, self.main_window.properties_dock
            )
            try:
                # Ensure the dock starts visible with a sensible width
                self.main_window.properties_dock.show()
                self.main_window.resizeDocks(
                    [self.main_window.properties_dock],
                    [320],
                    Qt.Horizontal,
                )
            except Exception:
                pass

            # Register for snapping functionality
            try:
                self.main_window._register_dock_for_snapping(  # noqa: SLF001 - intentional
                    self.main_window.properties_dock
                )
            except Exception as e:  # pragma: no cover - defensive
                self.logger.debug(
                    "Failed to register Project Details dock for snapping: %s", e
                )

            # Set minimum width to prevent zero-width widgets
            self.main_window.properties_dock.setMinimumWidth(MIN_WIDGET_SIZE)
            self.main_window.properties_dock.setSizePolicy(
                QSizePolicy.Preferred, QSizePolicy.Expanding
            )

        except Exception as e:  # pragma: no cover - defensive
            self.logger.error("Failed to setup Project Details dock: %s", e)
