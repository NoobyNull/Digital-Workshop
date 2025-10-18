"""
Facade for model library components.

Provides unified interface to all library functionality.
"""

from .library_ui_manager import LibraryUIManager
from .library_model_manager import LibraryModelManager
from .library_file_browser import LibraryFileBrowser
from .library_event_handler import LibraryEventHandler


class ModelLibraryFacade:
    """Facade pattern for model library components."""

    def __init__(self, library_widget):
        """
        Initialize facade.

        Args:
            library_widget: The model library widget
        """
        self.library_widget = library_widget
        self.ui_manager = LibraryUIManager(library_widget)
        self.model_manager = LibraryModelManager(library_widget)
        self.file_browser = LibraryFileBrowser(library_widget)
        self.event_handler = LibraryEventHandler(library_widget)

    def initialize(self) -> None:
        """Initialize all components."""
        self.ui_manager.init_ui()
        self.event_handler.setup_connections()
        self.model_manager.load_models_from_database()
        self.file_browser.validate_root_folders()

    # UI Manager delegation
    def init_ui(self) -> None:
        """Initialize UI."""
        self.ui_manager.init_ui()

    def apply_styling(self) -> None:
        """Apply styling."""
        self.ui_manager.apply_styling()

    # Model Manager delegation
    def load_models_from_database(self) -> None:
        """Load models from database."""
        self.model_manager.load_models_from_database()

    def update_model_view(self) -> None:
        """Update model view."""
        self.model_manager.update_model_view()

    def get_selected_model_id(self):
        """Get selected model ID."""
        return self.model_manager.get_selected_model_id()

    def get_selected_models(self):
        """Get selected model IDs."""
        return self.model_manager.get_selected_models()

    def load_models(self, file_paths):
        """Load models from file paths."""
        self.model_manager.load_models(file_paths)

    # File Browser delegation
    def import_from_context_menu(self, path: str) -> None:
        """Import from context menu."""
        self.file_browser.import_from_context_menu(path)

    def open_in_native_app(self, file_path: str) -> None:
        """Open in native app."""
        self.file_browser.open_in_native_app(file_path)

    def remove_model(self, model_id: int) -> None:
        """Remove model."""
        self.file_browser.remove_model(model_id)

    def refresh_models(self) -> None:
        """Refresh models."""
        self.file_browser.refresh_models()

    def refresh_file_browser(self) -> None:
        """Refresh file browser."""
        self.file_browser.refresh_file_browser()

    def validate_root_folders(self) -> None:
        """Validate root folders."""
        self.file_browser.validate_root_folders()

    def import_models(self) -> None:
        """Import models."""
        self.file_browser.import_models()

    def import_selected_files(self) -> None:
        """Import selected files."""
        self.file_browser.import_selected_files()

    def import_selected_folder(self) -> None:
        """Import selected folder."""
        self.file_browser.import_selected_folder()

    # Event Handler delegation
    def setup_connections(self) -> None:
        """Setup connections."""
        self.event_handler.setup_connections()

    def apply_filters(self) -> None:
        """Apply filters."""
        self.event_handler.apply_filters()

