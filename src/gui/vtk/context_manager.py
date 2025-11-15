"""
VTK Context Manager - OpenGL context validation and management.

This module provides OpenGL context validation and management for VTK operations,
preventing errors when the context is lost or invalid during cleanup.
"""

import platform
from typing import Optional, Dict, Any, Tuple
from contextlib import contextmanager

import vtk

from src.core.logging_config import get_logger
from .error_handler import get_vtk_error_handler


logger = get_logger(__name__)


class ContextState:
    """Represents the state of an OpenGL context."""

    VALID = "valid"
    LOST = "lost"
    INVALID = "invalid"
    UNKNOWN = "unknown"


class VTKContextManager:
    """
    Manages OpenGL context validation and lifecycle for VTK operations.

    Provides context validation before VTK operations and handles context loss
    gracefully, especially during application shutdown when the wglMakeCurrent
    error occurs.
    """

    def __init__(self) -> None:
        """Initialize the VTK context manager."""
        self.logger = get_logger(__name__)
        self.error_handler = get_vtk_error_handler()
        self.context_cache: Dict[str, ContextState] = {}
        self.platform_handlers = self._setup_platform_handlers()

        # Context validation settings
        self.validation_enabled = True
        self.strict_mode = False  # If True, throw exceptions on invalid context

        self.logger.info("VTK Context Manager initialized")

    def _setup_platform_handlers(self) -> Dict[str, Any]:
        """Set up platform-specific context handlers."""
        system = platform.system()

        handlers = {
            "Windows": self._windows_context_handler,
            "Linux": self._linux_context_handler,
            "Darwin": self._darwin_context_handler,
        }

        return handlers

    def _windows_context_handler(self, render_window: vtk.vtkRenderWindow) -> ContextState:
        """Windows-specific context validation."""
        try:
            # On Windows, check if the render window handle is valid
            if not render_window:
                return ContextState.INVALID

            # Check if window is mapped and has a valid device context
            window_id = render_window.GetWindowId()
            if window_id == 0:
                return ContextState.LOST

            # Try to get the device context - this will fail if context is lost
            try:
                # This is a safe way to check if the context is still valid
                # without triggering the wglMakeCurrent error
                if hasattr(render_window, "GetGenericDisplayId"):
                    display_id = render_window.GetGenericDisplayId()
                    if display_id == 0:
                        return ContextState.LOST
            except Exception:
                return ContextState.LOST

            return ContextState.VALID

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.debug("Windows context validation error: %s", e)
            return ContextState.UNKNOWN

    def _linux_context_handler(self, render_window: vtk.vtkRenderWindow) -> ContextState:
        """Linux-specific context validation."""
        try:
            if not render_window:
                return ContextState.INVALID

            # On Linux, check display connection
            if hasattr(render_window, "GetGenericDisplayId"):
                display_id = render_window.GetGenericDisplayId()
                if display_id == 0:
                    return ContextState.LOST

            return ContextState.VALID

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.debug("Linux context validation error: %s", e)
            return ContextState.UNKNOWN

    def _darwin_context_handler(self, render_window: vtk.vtkRenderWindow) -> ContextState:
        """macOS-specific context validation."""
        try:
            if not render_window:
                return ContextState.INVALID

            # On macOS, check if window is valid
            window_id = render_window.GetWindowId()
            if window_id == 0:
                return ContextState.LOST

            return ContextState.VALID

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.debug("macOS context validation error: %s", e)
            return ContextState.UNKNOWN

    def validate_context(
        self, render_window: vtk.vtkRenderWindow, operation: str = "unknown"
    ) -> Tuple[bool, ContextState]:
        """
        Validate OpenGL context before VTK operations.

        Args:
            render_window: The VTK render window to validate
            operation: Description of the operation being attempted

        Returns:
            Tuple of (is_valid, context_state)
        """
        if not self.validation_enabled:
            return True, ContextState.VALID

        try:
            # Check if render window exists
            if not render_window:
                self.logger.debug(
                    f"Context validation failed: render window is None for {operation}"
                )
                return False, ContextState.INVALID

            # Get platform-specific handler
            system = platform.system()
            handler = self.platform_handlers.get(system, self._generic_context_handler)

            # Validate context
            context_state = handler(render_window)

            # Cache the result
            cache_key = str(id(render_window))
            self.context_cache[cache_key] = context_state

            is_valid = context_state == ContextState.VALID

            if not is_valid:
                self.logger.debug("Context validation failed for %s: {context_state}", operation)
                if self.strict_mode:
                    self.error_handler.handle_error(
                        RuntimeError(f"Invalid context for {operation}: {context_state}"),
                        f"context_validation_{operation}",
                    )

            return is_valid, context_state

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.debug("Context validation exception: %s", e)
            return False, ContextState.UNKNOWN

    def _generic_context_handler(self, render_window: vtk.vtkRenderWindow) -> ContextState:
        """Generic context validation fallback."""
        try:
            if not render_window:
                return ContextState.INVALID

            # Basic validation - check if render window methods work
            try:
                render_window.GetSize()
                return ContextState.VALID
            except Exception:
                return ContextState.LOST

        except Exception:
            return ContextState.UNKNOWN

    def is_context_safe_for_cleanup(self, render_window: vtk.vtkRenderWindow) -> bool:
        """
        Check if context is safe for cleanup operations.

        During application shutdown, the OpenGL context may be destroyed
        but VTK still tries to cleanup resources, causing wglMakeCurrent errors.

        Args:
            render_window: The render window to check

        Returns:
            True if safe for cleanup, False if context is lost
        """
        try:
            is_valid, context_state = self.validate_context(render_window, "cleanup")

            if not is_valid:
                # Check if this is a context loss scenario (common during shutdown)
                if context_state in [ContextState.LOST, ContextState.INVALID]:
                    self.logger.debug(
                        "Context lost during cleanup, skipping VTK cleanup operations"
                    )
                    return False

            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.debug("Error checking cleanup safety: %s", e)
            return False

    @contextmanager
    def safe_vtk_operation(self, render_window: vtk.vtkRenderWindow, operation: str) -> None:
        """
        Context manager for safe VTK operations with context validation.

        Args:
            render_window: The render window to validate
            operation: Description of the operation
        """
        is_valid, context_state = self.validate_context(render_window, operation)

        if not is_valid:
            self.logger.debug("Skipping %s due to invalid context: {context_state}", operation)
            yield False  # Operation should be skipped
            return

        try:
            yield True  # Operation can proceed
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            # Handle errors during the operation
            handled = self.error_handler.handle_error(e, operation)
            if not handled and self.strict_mode:
                raise
            yield False

    def invalidate_context(self, render_window: vtk.vtkRenderWindow) -> None:
        """
        Mark a context as invalid (e.g., when window is destroyed).

        Args:
            render_window: The render window whose context should be invalidated
        """
        cache_key = str(id(render_window))
        self.context_cache[cache_key] = ContextState.INVALID
        self.logger.debug("Context invalidated for render window %s", cache_key)

    def clear_context_cache(self) -> None:
        """Clear the context validation cache."""
        self.context_cache.clear()
        self.logger.debug("Context cache cleared")

    def get_context_info(self, render_window: vtk.vtkRenderWindow) -> Dict[str, Any]:
        """
        Get detailed context information for debugging.

        Args:
            render_window: The render window to analyze

        Returns:
            Dictionary with context information
        """
        info = {
            "platform": platform.system(),
            "validation_enabled": self.validation_enabled,
            "strict_mode": self.strict_mode,
            "cache_size": len(self.context_cache),
        }

        try:
            if render_window:
                info.update(
                    {
                        "window_id": render_window.GetWindowId(),
                        "size": render_window.GetSize(),
                        "position": render_window.GetPosition(),
                        "is_current": False,  # Would need platform-specific check
                        "is_mapped": False,  # Would need platform-specific check
                    }
                )

                # Try to get more detailed info
                try:
                    if hasattr(render_window, "GetGenericDisplayId"):
                        info["display_id"] = render_window.GetGenericDisplayId()
                except Exception:
                    pass

                # Check cached state
                cache_key = str(id(render_window))
                if cache_key in self.context_cache:
                    info["cached_state"] = self.context_cache[cache_key]

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            info["error"] = str(e)

        return info

    def set_validation_enabled(self, enabled: bool) -> None:
        """
        Enable or disable context validation.

        Args:
            enabled: Whether to enable validation
        """
        self.validation_enabled = enabled
        self.logger.info("Context validation %s", "enabled" if enabled else "disabled")

    def set_strict_mode(self, strict: bool) -> None:
        """
        Enable or disable strict mode.

        In strict mode, invalid contexts will raise exceptions.
        In non-strict mode, operations are skipped gracefully.

        Args:
            strict: Whether to enable strict mode
        """
        self.strict_mode = strict
        self.logger.info("Strict mode %s", "enabled" if strict else "disabled")

    def safe_render(self, render_window: vtk.vtkRenderWindow) -> bool:
        """
        Safely perform a render operation with context validation.

        Args:
            render_window: The render window to render

        Returns:
            True if render succeeded, False if skipped or failed
        """
        with self.safe_vtk_operation(render_window, "render") as can_proceed:
            if not can_proceed:
                return False

            try:
                render_window.Render()
                return True
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                handled = self.error_handler.handle_error(e, "render")
                return handled

    def safe_cleanup(self, render_window: vtk.vtkRenderWindow) -> bool:
        """
        Safely perform cleanup operations with context validation.

        This is specifically designed to handle the wglMakeCurrent error
        that occurs during application shutdown.

        Args:
            render_window: The render window to cleanup

        Returns:
            True if cleanup succeeded, False if skipped
        """
        # Check if context is safe for cleanup
        if not self.is_context_safe_for_cleanup(render_window):
            self.logger.debug("Skipping VTK cleanup due to lost context")
            return False

        try:
            # Temporarily suppress errors during cleanup
            self.error_handler.suppress_errors_temporarily(2000)

            # Perform cleanup operations that don't require a valid context
            try:
                if render_window:
                    # These operations are safe even with lost context
                    render_window.Finalize()
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                # This is expected during shutdown
                self.logger.debug("Expected cleanup error: %s", e)

            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.debug("Cleanup error: %s", e)
            return False

    def get_diagnostic_info(self) -> Dict[str, Any]:
        """Get diagnostic information for troubleshooting."""
        return {
            "context_manager": {
                "validation_enabled": self.validation_enabled,
                "strict_mode": self.strict_mode,
                "platform": platform.system(),
                "cache_size": len(self.context_cache),
                "cached_states": dict(self.context_cache),
            },
            "error_handler": self.error_handler.get_error_stats(),
        }


# Global context manager instance
_vtk_context_manager: Optional[VTKContextManager] = None


def get_vtk_context_manager() -> VTKContextManager:
    """Get the global VTK context manager instance."""
    global _vtk_context_manager
    if _vtk_context_manager is None:
        _vtk_context_manager = VTKContextManager()
    return _vtk_context_manager


def validate_vtk_context(
    render_window: vtk.vtkRenderWindow, operation: str = "unknown"
) -> Tuple[bool, ContextState]:
    """
    Convenience function to validate VTK context.

    Args:
        render_window: The render window to validate
        operation: Description of the operation

    Returns:
        Tuple of (is_valid, context_state)
    """
    return get_vtk_context_manager().validate_context(render_window, operation)


def is_context_safe_for_cleanup(render_window: vtk.vtkRenderWindow) -> bool:
    """
    Convenience function to check if context is safe for cleanup.

    Args:
        render_window: The render window to check

    Returns:
        True if safe for cleanup
    """
    return get_vtk_context_manager().is_context_safe_for_cleanup(render_window)
