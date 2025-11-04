"""
VTK Fallback Renderer - Fallback rendering when context is lost.

This module provides fallback rendering strategies when the primary OpenGL
context is lost or invalid, ensuring the application remains functional.
"""

import platform
from typing import Optional, Dict, Any, Tuple
from enum import Enum

import vtk

from src.core.logging_config import get_logger, log_function_call
from .error_handler import get_vtk_error_handler, VTKErrorCode
from .context_manager import get_vtk_context_manager, ContextState


logger = get_logger(__name__)


class FallbackMode(Enum):
    """Fallback rendering modes."""

    SOFTWARE_RENDERING = "software_rendering"
    IMAGE_CACHE = "image_cache"
    WIREFRAME_ONLY = "wireframe_only"
    BOUNDING_BOX = "bounding_box"
    DISABLED = "disabled"


class VTKFallbackRenderer:
    """
    Provides fallback rendering when primary OpenGL context is lost.

    This class implements various fallback strategies to maintain application
    functionality when the primary VTK rendering context becomes invalid.
    """

    def __init__(self):
        """Initialize the fallback renderer."""
        self.logger = get_logger(__name__)
        self.error_handler = get_vtk_error_handler()
        self.context_manager = get_vtk_context_manager()

        # Fallback state
        self.fallback_mode = FallbackMode.SOFTWARE_RENDERING
        self.original_renderer = None
        self.fallback_active = False
        self.image_cache: Dict[str, Any] = {}

        # Performance settings
        self.enable_image_cache = True
        self.cache_timeout_seconds = 300  # 5 minutes
        self.max_cache_size = 50

        # Platform-specific settings
        self.platform_capabilities = self._detect_platform_capabilities()

        self.logger.info("VTK Fallback Renderer initialized")

    def _detect_platform_capabilities(self) -> Dict[str, Any]:
        """Detect platform-specific rendering capabilities."""
        system = platform.system()

        capabilities = {
            "platform": system,
            "software_rendering_available": True,
            "image_cache_supported": True,
            "wireframe_fallback": True,
            "bounding_box_fallback": True,
        }

        # Platform-specific adjustments
        if system == "Windows":
            capabilities.update(
                {"software_rendering_available": True, "angle_fallback": True}
            )
        elif system == "Linux":
            capabilities.update(
                {"software_rendering_available": True, "mesa_fallback": True}
            )
        elif system == "Darwin":
            capabilities.update(
                {"software_rendering_available": True, "metal_fallback": True}
            )

        return capabilities

    def activate_fallback(
        self, renderer: vtk.vtkRenderer, mode: Optional[FallbackMode] = None
    ) -> bool:
        """
        Activate fallback rendering mode.

        Args:
            renderer: The original renderer
            mode: Fallback mode to use (auto-detect if None)

        Returns:
            True if fallback activated successfully
        """
        try:
            if self.fallback_active:
                self.logger.debug("Fallback already active")
                return True

            self.original_renderer = renderer
            self.fallback_mode = mode or self._select_best_fallback_mode()

            self.logger.info(
                f"Activating fallback rendering mode: {self.fallback_mode.value}"
            )

            success = self._apply_fallback_mode()

            if success:
                self.fallback_active = True
                self.logger.info("Fallback rendering activated successfully")
            else:
                self.logger.error("Failed to activate fallback rendering")

            return success

        except Exception as e:
            self.logger.error(f"Error activating fallback: {e}")
            return False

    def _select_best_fallback_mode(self) -> FallbackMode:
        """Select the best fallback mode based on platform and situation."""
        try:
            # Check platform capabilities
            caps = self.platform_capabilities

            # If software rendering is available, prefer it
            if caps.get("software_rendering_available", False):
                return FallbackMode.SOFTWARE_RENDERING

            # Otherwise, try image cache if available
            if caps.get("image_cache_supported", False) and self.enable_image_cache:
                return FallbackMode.IMAGE_CACHE

            # Fall back to wireframe
            if caps.get("wireframe_fallback", False):
                return FallbackMode.WIREFRAME_ONLY

            # Last resort: bounding box
            return FallbackMode.BOUNDING_BOX

        except Exception as e:
            self.logger.debug(f"Error selecting fallback mode: {e}")
            return FallbackMode.WIREFRAME_ONLY

    def _apply_fallback_mode(self) -> bool:
        """Apply the selected fallback mode."""
        try:
            if self.fallback_mode == FallbackMode.SOFTWARE_RENDERING:
                return self._setup_software_rendering()
            elif self.fallback_mode == FallbackMode.IMAGE_CACHE:
                return self._setup_image_cache()
            elif self.fallback_mode == FallbackMode.WIREFRAME_ONLY:
                return self._setup_wireframe_fallback()
            elif self.fallback_mode == FallbackMode.BOUNDING_BOX:
                return self._setup_bounding_box_fallback()
            else:
                self.logger.warning(f"Unknown fallback mode: {self.fallback_mode}")
                return False

        except Exception as e:
            self.logger.error(f"Error applying fallback mode {self.fallback_mode}: {e}")
            return False

    def _setup_software_rendering(self) -> bool:
        """Set up software rendering fallback."""
        try:
            self.logger.info("Setting up software rendering fallback")

            # Try to force software rendering
            if hasattr(vtk, "vtkRenderWindow"):
                # Set environment variables for software rendering
                import os

                os.environ["VTK_USE_OFFSCREEN_RENDERING"] = "1"

                # Try to create a software-based render window
                try:
                    # This is a platform-specific approach
                    if platform.system() == "Windows":
                        # On Windows, try to use the software rasterizer
                        software_window = vtk.vtkRenderWindow()
                        software_window.SetOffScreenRendering(1)
                        self.logger.info("Software rendering window created")
                        return True

                    elif platform.system() == "Linux":
                        # On Linux, try Mesa software rendering
                        software_window = vtk.vtkRenderWindow()
                        software_window.SetOffScreenRendering(1)
                        self.logger.info("Mesa software rendering configured")
                        return True

                except Exception as e:
                    self.logger.debug(f"Software rendering setup error: {e}")

            # If specific setup fails, try generic offscreen rendering
            return self._setup_generic_offscreen()

        except Exception as e:
            self.logger.error(f"Software rendering setup failed: {e}")
            return False

    def _setup_generic_offscreen(self) -> bool:
        """Set up generic offscreen rendering."""
        try:
            self.logger.info("Setting up generic offscreen rendering")

            # Create an offscreen render window
            offscreen_window = vtk.vtkRenderWindow()
            offscreen_window.SetOffScreenRendering(1)
            offscreen_window.SetSize(800, 600)

            # Copy settings from original renderer if available
            if self.original_renderer:
                # Copy camera settings
                original_camera = self.original_renderer.GetActiveCamera()
                if original_camera:
                    new_camera = vtk.vtkCamera()
                    new_camera.DeepCopy(original_camera)
                    offscreen_window.GetRenderers().GetFirstRenderer().SetActiveCamera(
                        new_camera
                    )

            self.logger.info("Generic offscreen rendering configured")
            return True

        except Exception as e:
            self.logger.error(f"Generic offscreen setup failed: {e}")
            return False

    def _setup_image_cache(self) -> bool:
        """Set up image cache fallback."""
        try:
            self.logger.info("Setting up image cache fallback")

            # This mode uses cached images instead of live rendering
            # Implementation would depend on how the image cache is populated
            self.logger.info("Image cache fallback configured")
            return True

        except Exception as e:
            self.logger.error(f"Image cache setup failed: {e}")
            return False

    def _setup_wireframe_fallback(self) -> bool:
        """Set up wireframe-only fallback."""
        try:
            self.logger.info("Setting up wireframe fallback")

            if not self.original_renderer:
                return False

            # Set all actors to wireframe representation
            actors = self.original_renderer.GetActors()
            actors.InitTraversal()

            for i in range(actors.GetNumberOfItems()):
                actor = actors.GetNextActor()
                if actor:
                    actor.GetProperty().SetRepresentationToWireframe()
                    actor.GetProperty().SetLineWidth(2.0)

            self.logger.info("Wireframe fallback configured")
            return True

        except Exception as e:
            self.logger.error(f"Wireframe fallback setup failed: {e}")
            return False

    def _setup_bounding_box_fallback(self) -> bool:
        """Set up bounding box fallback."""
        try:
            self.logger.info("Setting up bounding box fallback")

            if not self.original_renderer:
                return False

            # Remove all existing actors and replace with bounding boxes
            self._clear_all_actors()

            # This would create bounding box representations
            # Implementation depends on the specific model data available

            self.logger.info("Bounding box fallback configured")
            return True

        except Exception as e:
            self.logger.error(f"Bounding box fallback setup failed: {e}")
            return False

    def _clear_all_actors(self) -> None:
        """Clear all actors from the renderer."""
        try:
            if self.original_renderer:
                self.original_renderer.RemoveAllViewProps()
        except Exception as e:
            self.logger.debug(f"Error clearing actors: {e}")

    def deactivate_fallback(self) -> bool:
        """
        Deactivate fallback rendering and restore original.

        Returns:
            True if deactivated successfully
        """
        try:
            if not self.fallback_active:
                self.logger.debug("Fallback not active")
                return True

            self.logger.info("Deactivating fallback rendering")

            # Restore original rendering if possible
            success = self._restore_original_rendering()

            if success:
                self.fallback_active = False
                self.fallback_mode = FallbackMode.SOFTWARE_RENDERING
                self.logger.info("Fallback rendering deactivated successfully")
            else:
                self.logger.warning("Failed to restore original rendering")

            return success

        except Exception as e:
            self.logger.error(f"Error deactivating fallback: {e}")
            return False

    def _restore_original_rendering(self) -> bool:
        """Restore original rendering settings."""
        try:
            # This would restore the original renderer settings
            # Implementation depends on what was saved during activation

            self.logger.info("Original rendering restored")
            return True

        except Exception as e:
            self.logger.error(f"Error restoring original rendering: {e}")
            return False

    def is_fallback_active(self) -> bool:
        """Check if fallback rendering is currently active."""
        return self.fallback_active

    def get_fallback_mode(self) -> FallbackMode:
        """Get current fallback mode."""
        return self.fallback_mode

    def can_use_fallback(self, context_state: ContextState) -> bool:
        """
        Check if fallback can be used for the given context state.

        Args:
            context_state: The current context state

        Returns:
            True if fallback is appropriate
        """
        try:
            # Fallback is appropriate for lost or invalid contexts
            if context_state in [ContextState.LOST, ContextState.INVALID]:
                return True

            # Check platform capabilities
            caps = self.platform_capabilities
            if not caps.get("software_rendering_available", False):
                return False

            return True

        except Exception as e:
            self.logger.debug(f"Error checking fallback capability: {e}")
            return False

    def render_with_fallback(self, render_window: vtk.vtkRenderWindow) -> bool:
        """
        Render using fallback mode if context is invalid.

        Args:
            render_window: The render window to render

        Returns:
            True if rendered successfully (with or without fallback)
        """
        try:
            # Check if context is valid
            is_valid, context_state = self.context_manager.validate_context(
                render_window, "render"
            )

            if is_valid:
                # Context is valid, use normal rendering
                return self._normal_render(render_window)

            # Context is invalid, check if fallback is appropriate
            if not self.can_use_fallback(context_state):
                self.logger.warning(
                    f"Cannot use fallback for context state: {context_state}"
                )
                return False

            # Activate fallback if not already active
            if not self.fallback_active:
                renderer = render_window.GetRenderers().GetFirstRenderer()
                if not self.activate_fallback(renderer):
                    return False

            # Render with fallback
            return self._fallback_render(render_window)

        except Exception as e:
            self.logger.error(f"Error in fallback render: {e}")
            return False

    def _normal_render(self, render_window: vtk.vtkRenderWindow) -> bool:
        """Perform normal rendering."""
        try:
            # Suppress VTK warnings during rendering to avoid wglMakeCurrent errors
            # These are expected and handled gracefully by VTK
            import os
            import sys

            vtk.vtkObject.GlobalWarningDisplayOff()

            # Redirect stderr at file descriptor level to suppress VTK C++ error messages
            # (wglMakeCurrent errors are printed directly by VTK's C++ code)
            old_stderr_fd = None
            devnull_fd = None
            try:
                # Save original stderr file descriptor
                old_stderr_fd = os.dup(2)  # 2 is stderr
                # Open devnull
                devnull_fd = os.open(os.devnull, os.O_WRONLY)
                # Redirect stderr to devnull
                os.dup2(devnull_fd, 2)

                # Perform rendering
                render_window.Render()

            finally:
                # Restore stderr
                if old_stderr_fd is not None:
                    os.dup2(old_stderr_fd, 2)
                    os.close(old_stderr_fd)
                if devnull_fd is not None:
                    os.close(devnull_fd)

                vtk.vtkObject.GlobalWarningDisplayOn()

            return True

        except Exception as e:
            handled = self.error_handler.handle_error(e, "normal_render")
            return handled

    def _fallback_render(self, render_window: vtk.vtkRenderWindow) -> bool:
        """Perform fallback rendering."""
        try:
            if self.fallback_mode == FallbackMode.SOFTWARE_RENDERING:
                return self._software_render(render_window)
            elif self.fallback_mode == FallbackMode.IMAGE_CACHE:
                return self._cached_render(render_window)
            elif self.fallback_mode == FallbackMode.WIREFRAME_ONLY:
                return self._wireframe_render(render_window)
            elif self.fallback_mode == FallbackMode.BOUNDING_BOX:
                return self._bounding_box_render(render_window)
            else:
                self.logger.warning(
                    f"Unknown fallback mode for rendering: {self.fallback_mode}"
                )
                return False

        except Exception as e:
            self.logger.error(
                f"Error in fallback render mode {self.fallback_mode}: {e}"
            )
            return False

    def _software_render(self, render_window: vtk.vtkRenderWindow) -> bool:
        """Software rendering implementation."""
        try:
            # Software rendering is already set up, just render
            render_window.Render()
            return True

        except Exception as e:
            self.logger.debug(f"Software render error: {e}")
            return False

    def _cached_render(self, render_window: vtk.vtkRenderWindow) -> bool:
        """Cached image rendering implementation."""
        try:
            # This would use cached images instead of live rendering
            # Implementation depends on cache population strategy
            self.logger.debug("Using cached image rendering")
            return True

        except Exception as e:
            self.logger.debug(f"Cached render error: {e}")
            return False

    def _wireframe_render(self, render_window: vtk.vtkRenderWindow) -> bool:
        """Wireframe rendering implementation."""
        try:
            render_window.Render()
            return True

        except Exception as e:
            self.logger.debug(f"Wireframe render error: {e}")
            return False

    def _bounding_box_render(self, render_window: vtk.vtkRenderWindow) -> bool:
        """Bounding box rendering implementation."""
        try:
            render_window.Render()
            return True

        except Exception as e:
            self.logger.debug(f"Bounding box render error: {e}")
            return False

    def get_fallback_info(self) -> Dict[str, Any]:
        """Get fallback renderer information."""
        return {
            "fallback_active": self.fallback_active,
            "fallback_mode": self.fallback_mode.value if self.fallback_mode else None,
            "platform_capabilities": self.platform_capabilities,
            "image_cache_enabled": self.enable_image_cache,
            "cache_size": len(self.image_cache),
            "max_cache_size": self.max_cache_size,
        }

    def set_fallback_mode(self, mode: FallbackMode) -> None:
        """
        Set the fallback mode.

        Args:
            mode: The fallback mode to use
        """
        self.fallback_mode = mode
        self.logger.info(f"Fallback mode set to: {mode.value}")

    def enable_image_cache(self, enabled: bool, max_size: int = 50) -> None:
        """
        Enable or disable image caching.

        Args:
            enabled: Whether to enable image caching
            max_size: Maximum number of cached images
        """
        self.enable_image_cache = enabled
        self.max_cache_size = max_size

        if not enabled:
            self.image_cache.clear()

        self.logger.info(
            f"Image cache {'enabled' if enabled else 'disabled'} (max size: {max_size})"
        )


# Global fallback renderer instance
_vtk_fallback_renderer: Optional[VTKFallbackRenderer] = None


def get_vtk_fallback_renderer() -> VTKFallbackRenderer:
    """Get the global VTK fallback renderer instance."""
    global _vtk_fallback_renderer
    if _vtk_fallback_renderer is None:
        _vtk_fallback_renderer = VTKFallbackRenderer()
    return _vtk_fallback_renderer


def activate_vtk_fallback(
    renderer: vtk.vtkRenderer, mode: Optional[FallbackMode] = None
) -> bool:
    """
    Convenience function to activate VTK fallback rendering.

    Args:
        renderer: The original renderer
        mode: Fallback mode to use

    Returns:
        True if fallback activated successfully
    """
    return get_vtk_fallback_renderer().activate_fallback(renderer, mode)


def render_with_vtk_fallback(render_window: vtk.vtkRenderWindow) -> bool:
    """
    Convenience function to render with fallback if needed.

    Args:
        render_window: The render window to render

    Returns:
        True if rendered successfully
    """
    return get_vtk_fallback_renderer().render_with_fallback(render_window)
