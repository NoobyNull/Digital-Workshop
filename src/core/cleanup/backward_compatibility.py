"""
Backward Compatibility Layer for Legacy Cleanup Systems

This module provides compatibility wrappers that allow existing code
to continue working while using the new unified cleanup architecture.
"""

import warnings
from typing import Optional, Any, Dict
from src.core.logging_config import get_logger

from .unified_cleanup_coordinator import (
    get_unified_cleanup_coordinator,
)


class LegacyVTKCleanupCoordinator:
    """
    Backward compatibility wrapper for the old VTKCleanupCoordinator.

    This class provides the same interface as the original VTKCleanupCoordinator
    but delegates to the new unified cleanup system.
    """

    def __init__(self) -> None:
        """Initialize the legacy VTK cleanup coordinator."""
        self.logger = get_logger(__name__)
        self._unified_coordinator = get_unified_cleanup_coordinator()
        self._deprecation_warned = False

        # Warn about deprecation on first use
        if not self._deprecation_warned:
            warnings.warn(
                "VTKCleanupCoordinator is deprecated. Use UnifiedCleanupCoordinator instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            self._deprecation_warned = True

    def coordinate_cleanup(
        self, render_window=None, renderer=None, interactor=None
    ) -> bool:
        """
        Coordinate VTK cleanup (legacy interface).

        Args:
            render_window: VTK render window
            renderer: VTK renderer
            interactor: VTK interactor

        Returns:
            True if cleanup completed successfully
        """
        try:
            self.logger.info("Using legacy VTK cleanup coordinator interface")

            # Delegate to unified coordinator
            stats = self._unified_coordinator.coordinate_cleanup(
                render_window=render_window, renderer=renderer, interactor=interactor
            )

            # Return success based on stats
            return stats.failed_phases == 0

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Legacy VTK cleanup failed: %s", e)
            return False

    def cleanup_all_resources(self) -> Dict[str, Any]:
        """
        Cleanup all resources (legacy interface).

        Returns:
            Dictionary with cleanup statistics
        """
        try:
            self.logger.info("Using legacy cleanup_all_resources interface")

            # Delegate to unified coordinator
            stats = self._unified_coordinator.coordinate_cleanup()

            return {
                "success": stats.completed_phases,
                "errors": stats.failed_phases,
                "total_duration": stats.total_duration,
                "context_lost": stats.context_lost,
                "errors_list": stats.errors,
            }

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Legacy cleanup_all_resources failed: %s", e)
            return {
                "success": 0,
                "errors": 1,
                "total_duration": 0.0,
                "context_lost": False,
                "errors_list": [str(e)],
            }


class LegacyViewerWidgetFacade:
    """
    Backward compatibility wrapper for ViewerWidgetFacade cleanup.

    This class provides the same interface as the original ViewerWidgetFacade
    but delegates to the new unified cleanup system.
    """

    def __init__(self) -> None:
        """Initialize the legacy viewer widget facade."""
        self.logger = get_logger(__name__)
        self._unified_coordinator = get_unified_cleanup_coordinator()
        self._deprecation_warned = False

        # Warn about deprecation on first use
        if not self._deprecation_warned:
            warnings.warn(
                "ViewerWidgetFacade cleanup methods are deprecated. Use UnifiedCleanupCoordinator instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            self._deprecation_warned = True

    def cleanup(self, render_window=None, renderer=None, interactor=None) -> bool:
        """
        Cleanup viewer widget (legacy interface).

        Args:
            render_window: VTK render window
            renderer: VTK renderer
            interactor: VTK interactor

        Returns:
            True if cleanup completed successfully
        """
        try:
            self.logger.info("Using legacy viewer widget cleanup interface")

            # Delegate to unified coordinator
            stats = self._unified_coordinator.coordinate_cleanup(
                render_window=render_window, renderer=renderer, interactor=interactor
            )

            return stats.failed_phases == 0

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Legacy viewer widget cleanup failed: %s", e)
            return False


class LegacyVTKSceneManager:
    """
    Backward compatibility wrapper for VTKSceneManager cleanup.

    This class provides the same interface as the original VTKSceneManager
    but delegates to the new unified cleanup system.
    """

    def __init__(self) -> None:
        """Initialize the legacy VTK scene manager."""
        self.logger = get_logger(__name__)
        self._unified_coordinator = get_unified_cleanup_coordinator()
        self._deprecation_warned = False

        # Warn about deprecation on first use
        if not self._deprecation_warned:
            warnings.warn(
                "VTKSceneManager cleanup methods are deprecated. Use UnifiedCleanupCoordinator instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            self._deprecation_warned = True

    def cleanup(self, render_window=None, renderer=None, interactor=None) -> bool:
        """
        Cleanup VTK scene manager (legacy interface).

        Args:
            render_window: VTK render window
            renderer: VTK renderer
            interactor: VTK interactor

        Returns:
            True if cleanup completed successfully
        """
        try:
            self.logger.info("Using legacy VTK scene manager cleanup interface")

            # Delegate to unified coordinator
            stats = self._unified_coordinator.coordinate_cleanup(
                render_window=render_window, renderer=renderer, interactor=interactor
            )

            return stats.failed_phases == 0

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Legacy VTK scene manager cleanup failed: %s", e)
            return False


# Global compatibility instances
_legacy_vtk_cleanup_coordinator: Optional[LegacyVTKCleanupCoordinator] = None
_legacy_viewer_widget_facade: Optional[LegacyViewerWidgetFacade] = None
_legacy_vtk_scene_manager: Optional[LegacyVTKSceneManager] = None


def get_legacy_vtk_cleanup_coordinator() -> LegacyVTKCleanupCoordinator:
    """Get the legacy VTK cleanup coordinator instance."""
    global _legacy_vtk_cleanup_coordinator
    if _legacy_vtk_cleanup_coordinator is None:
        _legacy_vtk_cleanup_coordinator = LegacyVTKCleanupCoordinator()
    return _legacy_vtk_cleanup_coordinator


def get_legacy_viewer_widget_facade() -> LegacyViewerWidgetFacade:
    """Get the legacy viewer widget facade instance."""
    global _legacy_viewer_widget_facade
    if _legacy_viewer_widget_facade is None:
        _legacy_viewer_widget_facade = LegacyViewerWidgetFacade()
    return _legacy_viewer_widget_facade


def get_legacy_vtk_scene_manager() -> LegacyVTKSceneManager:
    """Get the legacy VTK scene manager instance."""
    global _legacy_vtk_scene_manager
    if _legacy_vtk_scene_manager is None:
        _legacy_vtk_scene_manager = LegacyVTKSceneManager()
    return _legacy_vtk_scene_manager


def coordinate_vtk_cleanup_legacy(
    render_window=None, renderer=None, interactor=None
) -> bool:
    """
    Legacy function for VTK cleanup coordination.

    Args:
        render_window: VTK render window
        renderer: VTK renderer
        interactor: VTK interactor

    Returns:
        True if cleanup completed successfully
    """
    coordinator = get_legacy_vtk_cleanup_coordinator()
    return coordinator.coordinate_cleanup(render_window, renderer, interactor)


# Error handling utilities
class CleanupErrorHandler:
    """Centralized error handling for cleanup operations."""

    def __init__(self) -> None:
        """Initialize the cleanup error handler."""
        self.logger = get_logger(__name__)
        self._error_counts = {}
        self._last_errors = []

    def handle_cleanup_error(self, error: Exception, context: str) -> bool:
        """
        Handle cleanup errors with appropriate logging and recovery.

        Args:
            error: The exception that occurred
            context: Context where the error occurred

        Returns:
            True if error was handled successfully
        """
        try:
            error_type = type(error).__name__
            error_key = f"{context}:{error_type}"

            # Count errors
            self._error_counts[error_key] = self._error_counts.get(error_key, 0) + 1

            # Store last errors
            self._last_errors.append(
                {
                    "context": context,
                    "error_type": error_type,
                    "error_message": str(error),
                    "count": self._error_counts[error_key],
                }
            )

            # Keep only last 10 errors
            if len(self._last_errors) > 10:
                self._last_errors.pop(0)

            # Log error with appropriate level
            if self._error_counts[error_key] == 1:
                self.logger.warning("Cleanup error in %s: {error}", context)
            elif self._error_counts[error_key] <= 3:
                self.logger.warning(
                    f"Repeated cleanup error in {context} ({self._error_counts[error_key]} times): {error}"
                )
            else:
                self.logger.error(
                    f"Frequent cleanup error in {context} ({self._error_counts[error_key]} times): {error}"
                )

            return True

        except (
            OSError,
            IOError,
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
        ) as handling_error:
            self.logger.error("Error in cleanup error handler: %s", handling_error)
            return False

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get cleanup error statistics."""
        return {
            "error_counts": self._error_counts.copy(),
            "last_errors": self._last_errors.copy(),
            "total_errors": sum(self._error_counts.values()),
        }

    def reset_error_counts(self) -> None:
        """Reset error counts."""
        self._error_counts.clear()
        self._last_errors.clear()


# Global error handler instance
_cleanup_error_handler: Optional[CleanupErrorHandler] = None


def get_cleanup_error_handler() -> CleanupErrorHandler:
    """Get the global cleanup error handler instance."""
    global _cleanup_error_handler
    if _cleanup_error_handler is None:
        _cleanup_error_handler = CleanupErrorHandler()
    return _cleanup_error_handler
