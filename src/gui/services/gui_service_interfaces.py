"""GUI-specific service interfaces for enhanced modularity and maintainability.

This module provides service interfaces specifically for GUI components,
extending the core service interfaces with GUI-specific functionality.
"""

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, Union
from PySide6.QtCore import QObject, Signal


class UIState(Enum):
    """Enumeration of UI states."""

    LOADING = "loading"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    PROCESSING = "processing"


class ProgressInfo:
    """Information about operation progress."""

    def __init__(self, current: float, total: float, message: str = ""):
        """
        Initialize progress information.

        Args:
            current: Current progress value (0.0 to total)
            total: Total progress value
            message: Optional progress message
        """
        self.current = current
        self.total = total
        self.message = message

    @property
    def percentage(self) -> float:
        """Get progress as percentage (0.0 to 100.0)."""
        if self.total <= 0:
            return 0.0
        return min(100.0, (self.current / self.total) * 100.0)

    @property
    def is_complete(self) -> bool:
        """Check if progress is complete."""
        return self.current >= self.total


class IViewerUIService(ABC):
    """Interface for viewer UI management services."""

    @abstractmethod
    def set_ui_state(self, state: UIState, message: str = "") -> None:
        """Set the current UI state.

        Args:
            state: New UI state
            message: Optional state message
        """
        pass

    @abstractmethod
    def get_ui_state(self) -> UIState:
        """Get current UI state.

        Returns:
            Current UI state
        """
        pass

    @abstractmethod
    def show_progress(self, progress: ProgressInfo) -> None:
        """Show progress information to user.

        Args:
            progress: Progress information to display
        """
        pass

    @abstractmethod
    def hide_progress(self) -> None:
        """Hide progress indicator."""
        pass

    @abstractmethod
    def enable_cancellation(self, cancellable: bool) -> None:
        """Enable or disable operation cancellation.

        Args:
            cancellable: Whether operations can be cancelled
        """
        pass

    @abstractmethod
    def is_cancellation_requested(self) -> bool:
        """Check if user requested cancellation.

        Returns:
            True if cancellation was requested
        """
        pass

    @abstractmethod
    def reset_cancellation(self) -> None:
        """Reset cancellation request flag."""
        pass

    @abstractmethod
    def show_error(self, title: str, message: str, details: str = "") -> None:
        """Show error dialog to user.

        Args:
            title: Error dialog title
            message: Error message
            details: Optional detailed error information
        """
        pass

    @abstractmethod
    def show_warning(self, title: str, message: str) -> None:
        """Show warning dialog to user.

        Args:
            title: Warning dialog title
            message: Warning message
        """
        pass

    @abstractmethod
    def show_info(self, title: str, message: str) -> None:
        """Show information dialog to user.

        Args:
            title: Information dialog title
            message: Information message
        """
        pass


class IEnhancedViewerService(ABC):
    """Enhanced interface for 3D viewer operations with performance and UX features."""

    @abstractmethod
    def load_model_async(
        self,
        file_path: Path,
        progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
        cancellation_token: Optional[Callable[[], bool]] = None,
    ) -> bool:
        """Load a 3D model asynchronously with progress tracking.

        Args:
            file_path: Path to the model file
            progress_callback: Optional callback for progress updates
            cancellation_token: Optional function to check for cancellation

        Returns:
            True if model loading started successfully, False otherwise
        """
        pass

    @abstractmethod
    def cancel_loading(self) -> None:
        """Cancel current model loading operation."""
        pass

    @abstractmethod
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get viewer performance statistics.

        Returns:
            Dictionary containing performance metrics
        """
        pass

    @abstractmethod
    def set_performance_mode(self, mode: str) -> None:
        """Set performance mode (quality vs speed tradeoff).

        Args:
            mode: Performance mode ('high', 'balanced', 'performance')
        """
        pass

    @abstractmethod
    def enable_vsync(self, enabled: bool) -> None:
        """Enable or disable VSync for tear-free rendering.

        Args:
            enabled: Whether to enable VSync
        """
        pass

    @abstractmethod
    def set_target_fps(self, fps: int) -> None:
        """Set target frame rate.

        Args:
            fps: Target FPS (30, 60, etc.)
        """
        pass

    @abstractmethod
    def optimize_for_model_size(self, triangle_count: int) -> None:
        """Optimize rendering settings based on model complexity.

        Args:
            triangle_count: Number of triangles in the model
        """
        pass


class IEnhancedThemeService(ABC):
    """Enhanced interface for theme management with dynamic switching."""

    @abstractmethod
    def apply_theme_async(self, theme_name: str) -> bool:
        """Apply theme asynchronously without blocking UI.

        Args:
            theme_name: Name of the theme to apply

        Returns:
            True if theme application started successfully
        """
        pass

    @abstractmethod
    def get_theme_preview(self, theme_name: str) -> Optional[str]:
        """Get preview information for a theme.

        Args:
            theme_name: Name of the theme

        Returns:
            Preview information or None if not available
        """
        pass

    @abstractmethod
    def validate_theme(self, theme_name: str) -> Tuple[bool, str]:
        """Validate theme before applying.

        Args:
            theme_name: Name of the theme to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    @abstractmethod
    def preview_theme_temporarily(
        self, theme_name: str, duration_ms: int = 3000
    ) -> bool:
        """Preview a theme temporarily without permanent application.

        Args:
            theme_name: Name of the theme to preview
            duration_ms: Duration to show preview in milliseconds

        Returns:
            True if preview started successfully
        """
        pass

    @abstractmethod
    def revert_to_previous_theme(self) -> bool:
        """Revert to the previously applied theme.

        Returns:
            True if reversion was successful
        """
        pass

    @abstractmethod
    def get_theme_categories(self) -> Dict[str, List[str]]:
        """Get available theme categories and their themes.

        Returns:
            Dictionary mapping categories to theme lists
        """
        pass


class IMaterialService(ABC):
    """Interface for material management services."""

    @abstractmethod
    def validate_material(self, material_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate material data before application.

        Args:
            material_data: Material data to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    @abstractmethod
    def get_material_preview(self, material_name: str) -> Optional[bytes]:
        """Get preview image for a material.

        Args:
            material_name: Name of the material

        Returns:
            Preview image data or None if not available
        """
        pass

    @abstractmethod
    def create_material_from_template(
        self, template_name: str, custom_params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create a new material from a template.

        Args:
            template_name: Name of the material template
            custom_params: Custom parameters for the material

        Returns:
            Created material data or None if creation failed
        """
        pass

    @abstractmethod
    def get_material_categories(self) -> List[str]:
        """Get list of available material categories.

        Returns:
            List of material category names
        """
        pass

    @abstractmethod
    def search_materials(self, query: str, category: Optional[str] = None) -> List[str]:
        """Search for materials by name and optionally category.

        Args:
            query: Search query string
            category: Optional category filter

        Returns:
            List of matching material names
        """
        pass


class ILayoutManager(ABC):
    """Interface for UI layout management."""

    @abstractmethod
    def save_layout(self, layout_name: str) -> bool:
        """Save current UI layout.

        Args:
            layout_name: Name to save the layout as

        Returns:
            True if layout was saved successfully
        """
        pass

    @abstractmethod
    def load_layout(self, layout_name: str) -> bool:
        """Load a saved UI layout.

        Args:
            layout_name: Name of the layout to load

        Returns:
            True if layout was loaded successfully
        """
        pass

    @abstractmethod
    def get_saved_layouts(self) -> List[str]:
        """Get list of saved layout names.

        Returns:
            List of saved layout names
        """
        pass

    @abstractmethod
    def delete_layout(self, layout_name: str) -> bool:
        """Delete a saved layout.

        Args:
            layout_name: Name of the layout to delete

        Returns:
            True if layout was deleted successfully
        """
        pass

    @abstractmethod
    def reset_to_default_layout(self) -> bool:
        """Reset UI to default layout.

        Returns:
            True if reset was successful
        """
        pass


class INotificationService(ABC):
    """Interface for user notification services."""

    @abstractmethod
    def show_notification(
        self,
        title: str,
        message: str,
        notification_type: str = "info",
        duration_ms: int = 5000,
    ) -> str:
        """Show a notification to the user.

        Args:
            title: Notification title
            message: Notification message
            notification_type: Type ('info', 'warning', 'error', 'success')
            duration_ms: Duration to show notification in milliseconds

        Returns:
            Notification ID for potential cancellation
        """
        pass

    @abstractmethod
    def hide_notification(self, notification_id: str) -> bool:
        """Hide a specific notification.

        Args:
            notification_id: ID of the notification to hide

        Returns:
            True if notification was hidden successfully
        """
        pass

    @abstractmethod
    def clear_all_notifications(self) -> None:
        """Clear all active notifications."""
        pass

    @abstractmethod
    def set_notification_enabled(self, enabled: bool) -> None:
        """Enable or disable notifications globally.

        Args:
            enabled: Whether notifications should be enabled
        """
        pass


class IUIService(QObject):
    """Main UI service combining all GUI service interfaces."""

    # Signals for UI events
    state_changed = Signal(str, str)  # state, message
    progress_updated = Signal(object)  # ProgressInfo
    error_occurred = Signal(str, str, str)  # title, message, details
    notification_shown = Signal(str, str, str, int)  # id, title, message, type

    def __init__(self):
        """Initialize UI service."""
        super().__init__()

    # Viewer UI management
    def set_ui_state(self, state: UIState, message: str = "") -> None:
        """Set the current UI state."""
        self.state_changed.emit(state.value, message)

    def show_progress(self, progress: ProgressInfo) -> None:
        """Show progress information to user."""
        self.progress_updated.emit(progress)

    def show_error(self, title: str, message: str, details: str = "") -> None:
        """Show error dialog to user."""
        self.error_occurred.emit(title, message, details)

    def show_notification(
        self,
        title: str,
        message: str,
        notification_type: str = "info",
        duration_ms: int = 5000,
    ) -> str:
        """Show a notification to the user."""
        notification_id = f"notification_{id(self)}"
        self.notification_shown.emit(notification_id, title, message, notification_type)
        return notification_id
