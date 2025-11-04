"""
Main window facade for modular component integration.

Integrates layout, settings, dock, and event management components.
"""


from PySide6.QtWidgets import QMainWindow

from src.core.logging_config import get_logger

from .layout_manager import LayoutManager
from .settings_manager import SettingsManager
from .dock_manager import DockManager
from .event_handler import EventHandler


logger = get_logger(__name__)


class MainWindowFacade:
    """Facade for integrating main window components."""

    def __init__(self, main_window: QMainWindow):
        """
        Initialize the facade.

        Args:
            main_window: The main window instance
        """
        self.main_window = main_window
        self.layout_manager = LayoutManager(main_window)
        self.settings_manager = SettingsManager(main_window)
        self.dock_manager = DockManager(main_window)
        self.event_handler = EventHandler(main_window)

        logger.info("Main window facade initialized")

    def initialize_components(self) -> None:
        """Initialize all components."""
        logger.info("Initializing main window components")

        # Initialize layout persistence
        self.layout_manager._init_layout_persistence()

        # Load saved settings
        self.settings_manager.load_lighting_settings()
        self.settings_manager.load_metadata_panel_visibility()
        self.settings_manager.load_library_panel_visibility()

        # Connect layout autosave
        self.layout_manager.connect_layout_autosave()

        logger.info("Main window components initialized")

    def create_docks(self) -> None:
        """Create dock widgets."""
        logger.info("Creating dock widgets")
        self.dock_manager.create_metadata_dock()
        self.dock_manager.create_model_library_dock()

    def save_layout(self) -> None:
        """Save current layout."""
        self.layout_manager.save_current_layout()

    def load_layout(self) -> None:
        """Load saved layout."""
        self.layout_manager.load_saved_layout()

    def reset_layout(self) -> None:
        """Reset layout to default."""
        self.layout_manager.reset_dock_layout_and_save()

    def save_settings(self) -> None:
        """Save current settings."""
        self.settings_manager.save_lighting_settings()
        self.settings_manager.save_metadata_panel_visibility()
        self.settings_manager.save_library_panel_visibility()

    def cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Cleaning up main window components")
        self.save_layout()
        self.save_settings()
