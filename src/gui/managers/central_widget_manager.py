"""
Central Widget Manager for MainWindow.

Handles creation and management of the central widget and tabs.
Extracted from MainWindow to reduce monolithic class size.
"""

import logging

from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QLabel,
    QSizePolicy,
)


class CentralWidgetManager:
    """Manages central widget and tab setup for MainWindow."""

    def __init__(self, main_window: QMainWindow, logger: logging.Logger):
        """
        Initialize the central widget manager.

        Args:
            main_window: The main window instance
            logger: Logger instance
        """
        self.main_window = main_window
        self.logger = logger

    def setup_central_widget(self) -> None:
        """Set up the central widget with tabs."""
        self.logger.debug("Setting up native central widget")

        # Create tab widget
        tabs = QTabWidget(self.main_window)
        tabs.setObjectName("HeroTabs")
        tabs.setDocumentMode(True)
        tabs.setTabsClosable(False)
        tabs.setMovable(True)
        tabs.setUsesScrollButtons(False)
        tabs.setElideMode(Qt.ElideNone)
        tabs.setTabBarAutoHide(False)
        tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        tabs.setContentsMargins(0, 0, 0, 0)

        # Configure tab bar
        tab_bar = tabs.tabBar()
        if tab_bar:
            tab_bar.setExpanding(True)
            tab_bar.setUsesScrollButtons(False)

        # Set up viewer
        self._setup_viewer_widget(tabs)

        # Add feature tabs
        self._add_feature_tabs(tabs)

        # Set as central widget
        self.main_window.setCentralWidget(tabs)
        self.main_window.hero_tabs = tabs

        # Restore active tab
        self._restore_active_tab(tabs)

        # Log summary of created tabs
        self._log_tab_summary(tabs)

        self.logger.info("Central widget setup completed")

    def _setup_viewer_widget(self, tabs: QTabWidget) -> None:
        """Set up the 3D viewer widget."""
        try:
            try:
                from src.gui.viewer_widget_vtk import Viewer3DWidget
            except ImportError:
                try:
                    from src.gui.viewer_widget import Viewer3DWidget
                except ImportError:
                    Viewer3DWidget = None

            if Viewer3DWidget is not None:
                viewer = Viewer3DWidget(self.main_window)
                tabs.addTab(viewer, "3D Viewer")
                self.main_window.viewer_widget = viewer

                # Connect signals
                if hasattr(viewer, "model_loaded"):
                    viewer.model_loaded.connect(self.main_window._on_model_loaded)
                if hasattr(viewer, "lighting_panel_requested"):
                    viewer.lighting_panel_requested.connect(self.main_window._toggle_lighting_panel)

                self.logger.info("3D viewer widget created")
            else:
                fallback = QLabel("3D Viewer not available")
                fallback.setAlignment(Qt.AlignCenter)
                tabs.addTab(fallback, "3D Viewer")
                self.logger.warning("Viewer3DWidget not available")

        except Exception as e:
            self.logger.error("Failed to setup viewer: %s", e, exc_info=True)
            fallback = QLabel("3D Viewer\n\nComponent unavailable.")
            fallback.setAlignment(Qt.AlignCenter)
            tabs.addTab(fallback, "3D Viewer")

    def _add_feature_tabs(self, tabs: QTabWidget) -> None:
        """Add feature tabs to the central widget."""
        # G-code Previewer
        self._add_gcode_previewer_tab(tabs)

        # Cut List Optimizer
        self._add_clo_tab(tabs)

        # Feeds & Speeds
        self._add_feeds_speeds_tab(tabs)

        # Cost Estimator
        self._add_cost_estimator_tab(tabs)

    def _add_gcode_previewer_tab(self, tabs: QTabWidget) -> None:
        """Add G-code Previewer tab."""
        try:
            self.logger.debug("Attempting to import GcodePreviewerWidget...")
            from src.gui.gcode_previewer_components import GcodePreviewerWidget

            self.logger.debug("Creating GcodePreviewerWidget instance...")
            widget = GcodePreviewerWidget(self.main_window)
            tabs.addTab(widget, "G Code Previewer")
            self.main_window.gcode_previewer_widget = widget
            self.logger.info("G-code Previewer tab created successfully")
        except Exception as e:
            self.logger.error("Failed to create G-code Previewer: %s", e, exc_info=True)
            tabs.addTab(
                self._create_placeholder("G Code Previewer", "Component unavailable."),
                "G Code Previewer",
            )

    def _add_clo_tab(self, tabs: QTabWidget) -> None:
        """Add Cut List Optimizer tab."""
        try:
            self.logger.debug("Attempting to import CutListOptimizerWidget...")
            from src.gui.CLO import CutListOptimizerWidget

            self.logger.debug("Creating CutListOptimizerWidget instance...")
            widget = CutListOptimizerWidget()
            tabs.addTab(widget, "Cut List Optimizer")
            self.main_window.clo_widget = widget
            self.logger.info("Cut List Optimizer tab created successfully")
        except Exception as e:
            self.logger.error("Failed to create Cut List Optimizer: %s", e, exc_info=True)
            tabs.addTab(
                self._create_placeholder("Cut List Optimizer", "Component unavailable."),
                "Cut List Optimizer",
            )

    def _add_feeds_speeds_tab(self, tabs: QTabWidget) -> None:
        """Add Feeds & Speeds tab."""
        try:
            self.logger.debug("Attempting to import FeedsAndSpeedsWidget...")
            from src.gui.feeds_and_speeds import FeedsAndSpeedsWidget

            self.logger.debug("Creating FeedsAndSpeedsWidget instance...")
            widget = FeedsAndSpeedsWidget(self.main_window)
            tabs.addTab(widget, "Feed and Speed")
            self.main_window.feeds_and_speeds_widget = widget
            self.logger.info("Feeds & Speeds tab created successfully")
        except Exception as e:
            self.logger.error("Failed to create Feeds & Speeds: %s", e, exc_info=True)
            tabs.addTab(
                self._create_placeholder(
                    "Feed and Speed", "Feeds & Speeds Calculator\n\nComponent unavailable."
                ),
                "Feed and Speed",
            )

    def _add_cost_estimator_tab(self, tabs: QTabWidget) -> None:
        """Add Cost Estimator tab."""
        try:
            self.logger.debug("Attempting to import CostEstimatorWidget...")
            from src.gui.cost_estimator import CostEstimatorWidget

            self.logger.debug("Creating CostEstimatorWidget instance...")
            widget = CostEstimatorWidget(self.main_window)
            tabs.addTab(widget, "Project Cost Estimator")
            self.main_window.cost_estimator_widget = widget
            self.logger.info("Cost Estimator tab created successfully")
        except Exception as e:
            self.logger.error("Failed to create Cost Estimator: %s", e, exc_info=True)
            tabs.addTab(
                self._create_placeholder(
                    "Project Cost Estimator",
                    "Cost Calculator\n\nEstimate material, machine, and labor costs.",
                ),
                "Project Cost Estimator",
            )

    def _restore_active_tab(self, tabs: QTabWidget) -> None:
        """Restore the last active tab."""
        try:
            settings = QSettings()
            active_tab = settings.value("ui/active_hero_tab_index", 0, type=int)
            if isinstance(active_tab, int) and 0 <= active_tab < tabs.count():
                tabs.setCurrentIndex(active_tab)
        except Exception as e:
            self.logger.debug("Failed to restore active tab: %s", e)

    def _log_tab_summary(self, tabs: QTabWidget) -> None:
        """Log a summary of which tabs were successfully created."""
        tab_widget_attrs = [
            ("viewer_widget", "3D Viewer"),
            ("gcode_previewer_widget", "G Code Previewer"),
            ("clo_widget", "Cut List Optimizer"),
            ("feeds_and_speeds_widget", "Feed and Speed"),
            ("cost_estimator_widget", "Project Cost Estimator"),
        ]

        created = []
        missing = []

        for attr, name in tab_widget_attrs:
            if hasattr(self.main_window, attr):
                widget = getattr(self.main_window, attr)
                if widget is not None:
                    created.append(name)
                else:
                    missing.append(name)
            else:
                missing.append(name)

        self.logger.info("Tab creation summary: %s created, {len(missing)} missing", len(created))
        if created:
            self.logger.info("Successfully created tabs: %s", ", ".join(created))
        if missing:
            self.logger.warning("Missing tabs: %s", ", ".join(missing))

        # Also log actual tab count
        self.logger.info("Total tabs in widget: %s", tabs.count())

    @staticmethod
    def _create_placeholder(title: str, content: str) -> QWidget:
        """Create a placeholder widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)

        label = QLabel(content)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        layout.addStretch(1)

        return widget
