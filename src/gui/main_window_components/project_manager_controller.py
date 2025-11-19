"""Controller for Project Manager dock integration.

Encapsulates creation and wiring of the Project Manager dock so that
``MainWindow`` can delegate this responsibility instead of embedding
all logic directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QLabel

from src.core.database_manager import get_database_manager
from src.core.logging_config import get_logger, log_function_call

if TYPE_CHECKING:  # pragma: no cover - import only for type hints
    from PySide6.QtWidgets import QMainWindow


logger = get_logger(__name__)


class ProjectManagerController:
    """Manage the Project Manager dock for the main window."""

    def __init__(self, main_window: "QMainWindow") -> None:
        """Store a reference to the main window.

        Args:
            main_window: The application's main window instance.
        """
        self.main_window = main_window

    @log_function_call(logger)
    def setup_project_manager_dock(self) -> None:
        """Create and integrate the Project Manager dock.

        This mirrors the previous inline implementation in ``MainWindow``,
        but keeps all logic in a dedicated controller for clarity.
        """
        mw = self.main_window

        try:
            mw.project_manager_dock = QDockWidget("Project Manager", mw)
            mw.project_manager_dock.setObjectName("ProjectManagerDock")

            # Configure with native Qt dock features
            mw.project_manager_dock.setAllowedAreas(
                Qt.LeftDockWidgetArea
                | Qt.RightDockWidgetArea
                | Qt.TopDockWidgetArea
                | Qt.BottomDockWidgetArea
            )
            # Start with layout locked (only closable, not movable)
            mw.project_manager_dock.setFeatures(QDockWidget.DockWidgetClosable)

            # Create project manager widget
            try:
                from src.gui.project_manager import ProjectTreeWidget

                db_manager = get_database_manager()
                mw.project_manager_widget = ProjectTreeWidget(db_manager, mw)

                # Connect signals
                mw.project_manager_widget.project_opened.connect(mw._on_project_opened)
                mw.project_manager_widget.project_created.connect(mw._on_project_created)
                mw.project_manager_widget.project_deleted.connect(mw._on_project_deleted)
                mw.project_manager_widget.file_selected.connect(mw._on_project_file_selected)
                mw.project_manager_widget.tab_switch_requested.connect(mw._on_tab_switch_requested)

                mw.project_manager_dock.setWidget(mw.project_manager_widget)
                logger.info("Project manager dock created successfully")

            except Exception as e:  # noqa: BLE001
                logger.warning("Failed to create project manager widget: %s", e)
                # Native Qt fallback
                fallback_widget = QLabel("Project Manager\n\nComponent unavailable.")
                fallback_widget.setAlignment(Qt.AlignCenter)
                mw.project_manager_dock.setWidget(fallback_widget)

            # Add to main window using native Qt dock system
            mw.addDockWidget(Qt.LeftDockWidgetArea, mw.project_manager_dock)

            try:
                if hasattr(mw, "_register_dock_for_snapping"):
                    mw._register_dock_for_snapping(mw.project_manager_dock)  # noqa: SLF001
            except Exception:
                logger.debug("Failed to register Project Manager dock for snapping")

            # Tabify with model library dock using native Qt. This ensures they
            # start tabbed together, preventing the "jump" effect.
            try:
                if hasattr(mw, "model_library_dock") and mw.model_library_dock:
                    mw.tabifyDockWidget(mw.model_library_dock, mw.project_manager_dock)
                    logger.info("Model Library and Project Manager docks tabified using native Qt")
            except Exception:  # noqa: BLE001
                # Dock layout persistence is handled elsewhere; failure to tabify
                # is not fatal.
                logger.debug("Failed to tabify Project Manager dock with Model Library dock")

        except Exception as e:  # noqa: BLE001
            logger.error("Failed to setup project manager dock: %s", e)
