"""
Dock Widget Manager for MainWindow.

Handles creation and management of all dock widgets in the application.
Extracted from MainWindow to reduce monolithic class size.
"""

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QDockWidget,
    QLabel,
    QTabWidget,
    QSizePolicy,
)

from src.core.database_manager import get_database_manager
from src.gui.gcode_previewer_components import (
    GcodePropertiesWidget,
    GcodeControlsWidget,
)

# Minimum widget size constant
MIN_WIDGET_SIZE = 200


class DockWidgetManager:
    """Manages dock widget creation and layout for MainWindow."""

    def __init__(self, main_window: QMainWindow, logger: logging.Logger):
        """
        Initialize the dock widget manager.

        Args:
            main_window: The main window instance
            logger: Logger instance
        """
        self.main_window = main_window
        self.logger = logger

    def setup_all_docks(self) -> None:
        """Set up all dock widgets."""
        self.logger.info("=== STARTING DOCK WIDGET SETUP ===")
        self.logger.debug("Setting up native dock widgets")

        # Configure native Qt dock options
        self._configure_dock_options()

        # Set up individual dock widgets
        self.logger.info("Creating Model Library dock...")
        self._setup_model_library_dock()
        self.logger.info("Creating Project Manager dock...")
        self._setup_project_manager_dock()
        self.logger.info("Creating Properties dock...")
        self._setup_properties_dock()
        self.logger.info("Creating Metadata dock...")
        self._setup_metadata_dock()
        self.logger.info("Creating G-code Properties dock...")
        self._setup_gcode_properties_dock()
        self.logger.info("Creating G-code Controls dock...")
        self._setup_gcode_controls_dock()

        # Ensure all docks are visible
        self.logger.info("Ensuring all docks are visible...")
        self._ensure_all_docks_visible()

        # Log summary of created widgets
        self._log_widget_summary()

        self.logger.info("=== DOCK WIDGET SETUP COMPLETED ===")

    def _configure_dock_options(self) -> None:
        """Configure native Qt dock options."""
        dock_options = (
            QMainWindow.AllowNestedDocks | QMainWindow.AllowTabbedDocks | QMainWindow.AnimatedDocks
        )
        if hasattr(QMainWindow, "GroupedDragging"):
            dock_options |= QMainWindow.GroupedDragging
        self.main_window.setDockOptions(dock_options)

        try:
            self.main_window.setDockNestingEnabled(True)
        except RuntimeError:
            pass

    def _ensure_all_docks_visible(self) -> None:
        """Ensure all dock widgets are visible."""
        try:
            dock_attrs = [
                "model_library_dock",
                "project_manager_dock",
                "properties_dock",
                "metadata_dock",
                "gcode_properties_dock",
                "gcode_controls_dock",
            ]
            for attr in dock_attrs:
                if hasattr(self.main_window, attr):
                    dock = getattr(self.main_window, attr)
                    if dock is not None:
                        dock.setVisible(True)
                        self.logger.debug("Ensured %s is visible", attr)
                else:
                    self.logger.warning("Dock attribute %s not found on main window", attr)
        except (RuntimeError, AttributeError) as e:
            self.logger.warning("Failed to ensure dock visibility: %s", e, exc_info=True)

    def _log_widget_summary(self) -> None:
        """Log a summary of which widgets were successfully created."""
        widget_attrs = [
            ("model_library_widget", "Model Library"),
            ("project_manager_widget", "Project Manager"),
            ("project_details_widget", "Project Details"),
            ("metadata_editor", "Metadata Editor"),
            ("gcode_properties_widget", "G-code Properties"),
            ("gcode_controls_widget", "G-code Controls"),
        ]

        created = []
        missing = []

        for attr, name in widget_attrs:
            if hasattr(self.main_window, attr):
                widget = getattr(self.main_window, attr)
                if widget is not None:
                    created.append(name)
                else:
                    missing.append(name)
            else:
                missing.append(name)

        self.logger.info(
            "Widget creation summary: %s created, {len(missing)} missing", len(created)
        )
        if created:
            self.logger.info("Successfully created widgets: %s", ", ".join(created))
        if missing:
            self.logger.warning("Missing widgets: %s", ", ".join(missing))

    def _setup_model_library_dock(self) -> None:
        """Set up model library dock."""
        try:
            dock = QDockWidget("Model Library", self.main_window)
            dock.setObjectName("ModelLibraryDock")
            dock.setAllowedAreas(
                Qt.LeftDockWidgetArea
                | Qt.RightDockWidgetArea
                | Qt.TopDockWidgetArea
                | Qt.BottomDockWidgetArea
            )
            dock.setFeatures(QDockWidget.DockWidgetClosable)

            try:
                self.logger.debug("Attempting to import ModelLibraryWidget...")
                from src.gui.model_library import ModelLibraryWidget

                self.logger.debug("Creating ModelLibraryWidget instance...")
                widget = ModelLibraryWidget(self.main_window)
                widget.model_selected.connect(self.main_window._on_model_selected)
                widget.model_double_clicked.connect(self.main_window._on_model_double_clicked)
                widget.models_added.connect(self.main_window._on_models_added)

                dock.setWidget(widget)
                self.main_window.model_library_widget = widget
                self.logger.info("Model library dock created successfully")

            except Exception as e:
                self.logger.error("Failed to create model library: %s", e, exc_info=True)
                fallback = QLabel("Model Library\n\nComponent unavailable.")
                fallback.setAlignment(Qt.AlignCenter)
                dock.setWidget(fallback)

            self.main_window.addDockWidget(Qt.LeftDockWidgetArea, dock)
            dock.visibilityChanged.connect(lambda: self.main_window._update_library_action_state())
            self.main_window.model_library_dock = dock
            dock.setMinimumWidth(MIN_WIDGET_SIZE)

        except Exception as e:
            self.logger.error("Failed to setup model library dock: %s", e, exc_info=True)

    def _setup_project_manager_dock(self) -> None:
        """Set up project manager dock."""
        try:
            dock = QDockWidget("Project Manager", self.main_window)
            dock.setObjectName("ProjectManagerDock")
            dock.setAllowedAreas(
                Qt.LeftDockWidgetArea
                | Qt.RightDockWidgetArea
                | Qt.TopDockWidgetArea
                | Qt.BottomDockWidgetArea
            )
            dock.setFeatures(QDockWidget.DockWidgetClosable)

            try:
                self.logger.debug("Attempting to import ProjectTreeWidget...")
                from src.gui.project_manager import ProjectTreeWidget

                self.logger.debug("Creating ProjectTreeWidget instance...")
                db_manager = get_database_manager()
                widget = ProjectTreeWidget(db_manager, self.main_window)
                widget.project_opened.connect(self.main_window._on_project_opened)
                widget.project_created.connect(self.main_window._on_project_created)
                widget.project_deleted.connect(self.main_window._on_project_deleted)
                widget.tab_switch_requested.connect(self.main_window._on_tab_switch_requested)

                dock.setWidget(widget)
                self.main_window.project_manager_widget = widget
                self.logger.info("Project manager dock created successfully")

            except Exception as e:
                self.logger.error("Failed to create project manager: %s", e, exc_info=True)
                fallback = QLabel("Project Manager\n\nComponent unavailable.")
                fallback.setAlignment(Qt.AlignCenter)
                dock.setWidget(fallback)

            self.main_window.addDockWidget(Qt.LeftDockWidgetArea, dock)

            # Tabify with model library
            if hasattr(self.main_window, "model_library_dock"):
                try:
                    self.main_window.tabifyDockWidget(self.main_window.model_library_dock, dock)
                except Exception:
                    pass

            dock.visibilityChanged.connect(
                lambda: self.main_window._update_project_manager_action_state()
            )
            self.main_window.project_manager_dock = dock
            dock.setMinimumWidth(MIN_WIDGET_SIZE)

        except Exception as e:
            self.logger.error("Failed to setup project manager dock: %s", e, exc_info=True)

    def _setup_properties_dock(self) -> None:
        """Set up properties dock."""
        try:
            from src.gui.project_details_widget import ProjectDetailsWidget

            dock = QDockWidget("Project Details", self.main_window)
            dock.setObjectName("PropertiesDock")
            dock.setAllowedAreas(
                Qt.LeftDockWidgetArea
                | Qt.RightDockWidgetArea
                | Qt.TopDockWidgetArea
                | Qt.BottomDockWidgetArea
            )
            dock.setFeatures(QDockWidget.DockWidgetClosable)

            widget = ProjectDetailsWidget(self.main_window)
            dock.setWidget(widget)
            self.main_window.addDockWidget(Qt.RightDockWidgetArea, dock)

            self.main_window.project_details_widget = widget
            self.main_window.properties_dock = dock
            dock.setMinimumWidth(MIN_WIDGET_SIZE)
            dock.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        except Exception as e:
            self.logger.error("Failed to setup properties dock: %s", e)

    def _setup_metadata_dock(self) -> None:
        """Set up metadata dock."""
        try:
            dock = QDockWidget("Metadata Editor", self.main_window)
            dock.setObjectName("MetadataDock")
            dock.setAllowedAreas(
                Qt.LeftDockWidgetArea
                | Qt.RightDockWidgetArea
                | Qt.TopDockWidgetArea
                | Qt.BottomDockWidgetArea
            )
            dock.setFeatures(QDockWidget.DockWidgetClosable)

            try:
                self.logger.debug("Attempting to import MetadataEditorWidget...")
                from src.gui.metadata_editor import MetadataEditorWidget

                self.logger.debug("Creating MetadataEditorWidget instance...")
                editor = MetadataEditorWidget(self.main_window)
                editor.metadata_saved.connect(self.main_window._on_metadata_saved)
                editor.metadata_changed.connect(self.main_window._on_metadata_changed)

                tabs = QTabWidget(self.main_window)
                tabs.setObjectName("MetadataTabs")
                tabs.addTab(editor, "Metadata")

                notes = QLabel("Notes\n\nAdd project or model-specific notes here.")
                notes.setAlignment(Qt.AlignCenter)
                notes.setWordWrap(True)
                tabs.addTab(notes, "Notes")

                history = QLabel("History\n\nTimeline of edits will appear here.")
                history.setAlignment(Qt.AlignCenter)
                history.setWordWrap(True)
                tabs.addTab(history, "History")

                dock.setWidget(tabs)
                self.main_window.metadata_editor = editor
                self.main_window.metadata_tabs = tabs
                self.logger.info("Metadata dock created successfully")

            except Exception as e:
                self.logger.error("Failed to create metadata editor: %s", e, exc_info=True)
                fallback = QLabel("Metadata Editor\n\nComponent unavailable.")
                fallback.setAlignment(Qt.AlignCenter)
                fallback.setWordWrap(True)
                dock.setWidget(fallback)

            self.main_window.addDockWidget(Qt.RightDockWidgetArea, dock)

            if hasattr(self.main_window, "properties_dock"):
                try:
                    self.main_window.tabifyDockWidget(self.main_window.properties_dock, dock)
                except Exception:
                    pass

            dock.visibilityChanged.connect(lambda: self.main_window._update_metadata_action_state())
            self.main_window.metadata_dock = dock
            dock.setMinimumWidth(MIN_WIDGET_SIZE)
            dock.setMaximumWidth(500)
            dock.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        except Exception as e:
            self.logger.error("Failed to setup metadata dock: %s", e, exc_info=True)

    def _setup_gcode_properties_dock(self) -> None:
        """Set up G-code properties dock."""
        try:
            dock = QDockWidget("G-code Properties", self.main_window)
            dock.setObjectName("GcodePropertiesDock")
            dock.setAllowedAreas(
                Qt.LeftDockWidgetArea
                | Qt.RightDockWidgetArea
                | Qt.TopDockWidgetArea
                | Qt.BottomDockWidgetArea
            )
            dock.setFeatures(QDockWidget.DockWidgetClosable)

            widget = GcodePropertiesWidget(self.main_window)
            dock.setWidget(widget)
            self.main_window.addDockWidget(Qt.RightDockWidgetArea, dock)

            if hasattr(self.main_window, "metadata_dock"):
                try:
                    self.main_window.tabifyDockWidget(self.main_window.metadata_dock, dock)
                except Exception:
                    pass

            dock.visibilityChanged.connect(
                lambda: self.main_window._update_gcode_properties_action_state()
            )
            self.main_window.gcode_properties_dock = dock
            self.main_window.gcode_properties_widget = widget
            dock.setMinimumWidth(MIN_WIDGET_SIZE)
            dock.setMaximumWidth(500)
            dock.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        except Exception as e:
            self.logger.error("Failed to setup G-code properties dock: %s", e)

    def _setup_gcode_controls_dock(self) -> None:
        """Set up G-code controls dock."""
        try:
            dock = QDockWidget("G-code Controls", self.main_window)
            dock.setObjectName("GcodeControlsDock")
            dock.setAllowedAreas(
                Qt.LeftDockWidgetArea
                | Qt.RightDockWidgetArea
                | Qt.TopDockWidgetArea
                | Qt.BottomDockWidgetArea
            )
            dock.setFeatures(QDockWidget.DockWidgetClosable)

            widget = GcodeControlsWidget(parent=self.main_window)
            dock.setWidget(widget)
            self.main_window.addDockWidget(Qt.RightDockWidgetArea, dock)

            if hasattr(self.main_window, "gcode_properties_dock"):
                try:
                    self.main_window.tabifyDockWidget(self.main_window.gcode_properties_dock, dock)
                except Exception:
                    pass

            dock.visibilityChanged.connect(
                lambda: self.main_window._update_gcode_controls_action_state()
            )
            self.main_window.gcode_controls_dock = dock
            self.main_window.gcode_controls_widget = widget
            dock.setMinimumWidth(MIN_WIDGET_SIZE)
            dock.setMaximumWidth(500)
            dock.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        except Exception as e:
            self.logger.error("Failed to setup G-code controls dock: %s", e)
