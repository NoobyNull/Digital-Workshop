"""Service interfaces for core application services.

This module defines the abstract base classes for all core services
in the Candy-Cadence application architecture.
"""

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


class RenderMode(Enum):
    """Enumeration of available render modes."""

    SOLID = "solid"
    WIREFRAME = "wireframe"
    POINTS = "points"


class IThemeService(ABC):
    """Interface for theme management services."""

    @abstractmethod
    def apply_theme(self, theme_name: str) -> bool:
        """Apply a theme by name.

        Args:
            theme_name: Name of the theme to apply

        Returns:
            True if theme was applied successfully, False otherwise
        """

    @abstractmethod
    def get_current_theme(self) -> str:
        """Get the name of the currently applied theme.

        Returns:
            Name of the current theme
        """

    @abstractmethod
    def get_available_themes(self) -> List[str]:
        """Get list of available theme names.

        Returns:
            List of available theme names
        """

    @abstractmethod
    def get_color(self, color_name: str, default: Optional[str] = None) -> str:
        """Get a color value by name.

        Args:
            color_name: Name of the color to retrieve
            default: Default value if color is not found

        Returns:
            Color value as hex string
        """

    @abstractmethod
    def set_color(self, color_name: str, value: str) -> None:
        """Set a color value.

        Args:
            color_name: Name of the color to set
            value: Color value as hex string
        """

    @abstractmethod
    def export_theme(self, file_path: Path) -> bool:
        """Export current theme to file.

        Args:
            file_path: Path to export the theme file

        Returns:
            True if export was successful, False otherwise
        """

    @abstractmethod
    def import_theme(self, file_path: Path) -> bool:
        """Import theme from file.

        Args:
            file_path: Path to the theme file to import

        Returns:
            True if import was successful, False otherwise
        """


class IModelService(ABC):
    """Interface for model management services."""

    @abstractmethod
    def load_model(
        self,
        file_path: Path,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> bool:
        """Load a 3D model from file.

        Args:
            file_path: Path to the model file
            progress_callback: Optional callback for progress updates (0.0 to 1.0)

        Returns:
            True if model was loaded successfully, False otherwise
        """

    @abstractmethod
    def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory.

        Args:
            model_id: Unique identifier of the model to unload

        Returns:
            True if model was unloaded successfully, False otherwise
        """

    @abstractmethod
    def get_model(self, model_id: str) -> Optional[Any]:
        """Get a loaded model by ID.

        Args:
            model_id: Unique identifier of the model

        Returns:
            Model object if found, None otherwise
        """

    @abstractmethod
    def get_loaded_models(self) -> List[str]:
        """Get list of loaded model IDs.

        Returns:
            List of currently loaded model IDs
        """

    @abstractmethod
    def get_model_metadata(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a model.

        Args:
            model_id: Unique identifier of the model

        Returns:
            Dictionary containing model metadata, None if not found
        """

    @abstractmethod
    def update_model_metadata(self, model_id: str, metadata: Dict[str, Any]) -> bool:
        """Update model metadata.

        Args:
            model_id: Unique identifier of the model
            metadata: Dictionary containing updated metadata

        Returns:
            True if metadata was updated successfully, False otherwise
        """

    @abstractmethod
    def search_models(self, query: str) -> List[str]:
        """Search for models by query.

        Args:
            query: Search query string

        Returns:
            List of model IDs matching the search criteria
        """


class IDatabaseService(ABC):
    """Interface for database operations."""

    @abstractmethod
    def add_model(self, model_data: Dict[str, Any]) -> str:
        """Add a model to the database.

        Args:
            model_data: Dictionary containing model data

        Returns:
            Unique model ID if successful, None otherwise
        """

    @abstractmethod
    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get model data by ID.

        Args:
            model_id: Unique identifier of the model

        Returns:
            Dictionary containing model data, None if not found
        """

    @abstractmethod
    def update_model(self, model_id: str, model_data: Dict[str, Any]) -> bool:
        """Update model data.

        Args:
            model_id: Unique identifier of the model
            model_data: Dictionary containing updated model data

        Returns:
            True if update was successful, False otherwise
        """

    @abstractmethod
    def delete_model(self, model_id: str) -> bool:
        """Delete model from database.

        Args:
            model_id: Unique identifier of the model to delete

        Returns:
            True if deletion was successful, False otherwise
        """

    @abstractmethod
    def search_models(self, criteria: Dict[str, Any]) -> List[str]:
        """Search models by criteria.

        Args:
            criteria: Dictionary containing search criteria

        Returns:
            List of model IDs matching the criteria
        """

    @abstractmethod
    def get_all_models(self) -> List[Dict[str, Any]]:
        """Get all models from database.

        Returns:
            List of dictionaries containing all model data
        """

    @abstractmethod
    def add_metadata(self, model_id: str, metadata: Dict[str, Any]) -> bool:
        """Add metadata for a model.

        Args:
            model_id: Unique identifier of the model
            metadata: Dictionary containing metadata

        Returns:
            True if metadata was added successfully, False otherwise
        """

    @abstractmethod
    def get_metadata(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a model.

        Args:
            model_id: Unique identifier of the model

        Returns:
            Dictionary containing metadata, None if not found
        """

    @abstractmethod
    def backup_database(self, backup_path: Path) -> bool:
        """Create database backup.

        Args:
            backup_path: Path to save the backup file

        Returns:
            True if backup was successful, False otherwise
        """

    @abstractmethod
    def restore_database(self, backup_path: Path) -> bool:
        """Restore database from backup.

        Args:
            backup_path: Path to the backup file

        Returns:
            True if restore was successful, False otherwise
        """


class IViewerService(ABC):
    """Interface for 3D viewer operations."""

    @abstractmethod
    def set_model(self, model_id: str) -> bool:
        """Set the model to display in the viewer.

        Args:
            model_id: Unique identifier of the model to display

        Returns:
            True if model was set successfully, False otherwise
        """

    @abstractmethod
    def clear_model(self) -> None:
        """Clear the current model from viewer."""

    @abstractmethod
    def set_render_mode(self, mode: RenderMode) -> None:
        """Set the render mode.

        Args:
            mode: Render mode to apply
        """

    @abstractmethod
    def get_render_mode(self) -> RenderMode:
        """Get current render mode.

        Returns:
            Current render mode
        """

    @abstractmethod
    def reset_camera(self) -> None:
        """Reset camera to default position."""

    @abstractmethod
    def take_screenshot(
        self, file_path: Path, width: int = 1920, height: int = 1080
    ) -> bool:
        """Take a screenshot of the viewer.

        Args:
            file_path: Path to save the screenshot
            width: Screenshot width in pixels
            height: Screenshot height in pixels

        Returns:
            True if screenshot was taken successfully, False otherwise
        """

    @abstractmethod
    def set_camera_position(self, x: float, y: float, z: float) -> None:
        """Set camera position.

        Args:
            x: X coordinate
            y: Y coordinate
            z: Z coordinate
        """

    @abstractmethod
    def get_camera_position(self) -> Tuple[float, float, float]:
        """Get current camera position.

        Returns:
            Tuple of (x, y, z) coordinates
        """


class IConfigurationService(ABC):
    """Interface for configuration management."""

    @abstractmethod
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key is not found

        Returns:
            Configuration value
        """

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """

    @abstractmethod
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get all configuration values for a section.

        Args:
            section: Configuration section name

        Returns:
            Dictionary containing all values in the section
        """

    @abstractmethod
    def save(self) -> bool:
        """Save configuration to persistent storage.

        Returns:
            True if save was successful, False otherwise
        """

    @abstractmethod
    def load(self) -> bool:
        """Load configuration from persistent storage.

        Returns:
            True if load was successful, False otherwise
        """


class IErrorHandler(ABC):
    """Interface for error handling."""

    @abstractmethod
    def handle_error(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Handle an error.

        Args:
            error: Exception to handle
            context: Optional context information

        Returns:
            True if error was handled successfully, False otherwise
        """

    @abstractmethod
    def log_error(self, error: Exception, level: str = "ERROR") -> None:
        """Log an error.

        Args:
            error: Exception to log
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """

    @abstractmethod
    def should_retry(self, error: Exception) -> bool:
        """Determine if operation should be retried.

        Args:
            error: Exception to evaluate

        Returns:
            True if operation should be retried, False otherwise
        """


class IEventPublisher(ABC):
    """Interface for event publishing."""

    @abstractmethod
    def subscribe(self, event_type: str, callback: Callable) -> str:
        """Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            callback: Callback function to invoke when event occurs

        Returns:
            Subscription ID for unsubscribing
        """

    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from an event.

        Args:
            subscription_id: ID returned from subscribe

        Returns:
            True if unsubscription was successful, False otherwise
        """

    @abstractmethod
    def publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """Publish an event.

        Args:
            event_type: Type of event to publish
            data: Event data
        """


class IEventSubscriber(ABC):
    """Interface for event subscribers."""

    @abstractmethod
    def handle_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Handle an event.

        Args:
            event_type: Type of event
            data: Event data
        """
