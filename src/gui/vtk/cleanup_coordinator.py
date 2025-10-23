"""
VTK Cleanup Coordinator - Proper cleanup sequence and error handling.

This module coordinates VTK resource cleanup in the proper order to prevent
OpenGL context errors during application shutdown, specifically handling
the "wglMakeCurrent failed in Clean(), error: 6" error.
"""

import gc
import time
from typing import List, Dict, Any, Optional, Callable
from enum import Enum

import vtk

from src.core.logging_config import get_logger, log_function_call
from .error_handler import get_vtk_error_handler, VTKErrorCode
from .context_manager import get_vtk_context_manager, ContextState


logger = get_logger(__name__)


class CleanupPhase(Enum):
    """Phases of VTK cleanup process."""

    PRE_CLEANUP = "pre_cleanup"
    CONTEXT_VALIDATION = "context_validation"
    RESOURCE_CLEANUP = "resource_cleanup"
    ACTOR_CLEANUP = "actor_cleanup"
    RENDERER_CLEANUP = "renderer_cleanup"
    WINDOW_CLEANUP = "window_cleanup"
    INTERACTOR_CLEANUP = "interactor_cleanup"
    FINAL_CLEANUP = "final_cleanup"
    POST_CLEANUP = "post_cleanup"


class CleanupPriority(Enum):
    """Priority levels for cleanup operations."""

    CRITICAL = 1    # Must be cleaned up first
    HIGH = 2        # Should be cleaned up early
    NORMAL = 3      # Standard cleanup order
    LOW = 4         # Can be cleaned up later
    DEFERRED = 5    # Clean up last or skip if context lost


class VTKCleanupCoordinator:
    """
    Coordinates VTK cleanup in proper sequence to prevent OpenGL context errors.

    This class manages the cleanup of VTK resources in the correct order,
    validating context state at each step and gracefully handling context loss
    during application shutdown.
    """

    def __init__(self):
        """Initialize the cleanup coordinator."""
        self.logger = get_logger(__name__)
        self.error_handler = get_vtk_error_handler()
        self.context_manager = get_vtk_context_manager()

        # Cleanup state
        self.cleanup_in_progress = False
        self.context_lost_detected = False
        self.cleanup_callbacks: Dict[CleanupPhase, List[Callable]] = {}
        self.cleanup_resources: Dict[str, Any] = {}

        # Setup cleanup phases
        self._setup_cleanup_phases()

        self.logger.info("VTK Cleanup Coordinator initialized")

    def _setup_cleanup_phases(self) -> None:
        """Set up cleanup phases and their priorities."""
        # Initialize callback lists for each phase
        for phase in CleanupPhase:
            self.cleanup_callbacks[phase] = []

        # Register default cleanup operations
        self._register_default_cleanup_operations()

    def _register_default_cleanup_operations(self) -> None:
        """Register default cleanup operations for each phase."""

        # Pre-cleanup: Prepare for cleanup
        self.register_cleanup_callback(CleanupPhase.PRE_CLEANUP, self._pre_cleanup)

        # Context validation: Check if context is still valid
        self.register_cleanup_callback(CleanupPhase.CONTEXT_VALIDATION, self._validate_context)

        # Resource cleanup: Clean up VTK resources that don't require context
        self.register_cleanup_callback(CleanupPhase.RESOURCE_CLEANUP, self._cleanup_resources)

        # Actor cleanup: Remove actors from renderer
        self.register_cleanup_callback(CleanupPhase.ACTOR_CLEANUP, self._cleanup_actors)

        # Renderer cleanup: Clean up renderer
        self.register_cleanup_callback(CleanupPhase.RENDERER_CLEANUP, self._cleanup_renderer)

        # Window cleanup: Clean up render window
        self.register_cleanup_callback(CleanupPhase.WINDOW_CLEANUP, self._cleanup_window)

        # Interactor cleanup: Clean up interactor
        self.register_cleanup_callback(CleanupPhase.INTERACTOR_CLEANUP, self._cleanup_interactor)

        # Final cleanup: Final resource cleanup
        self.register_cleanup_callback(CleanupPhase.FINAL_CLEANUP, self._final_cleanup)

        # Post-cleanup: Cleanup verification
        self.register_cleanup_callback(CleanupPhase.POST_CLEANUP, self._post_cleanup)

    def register_cleanup_callback(self, phase: CleanupPhase, callback: Callable) -> None:
        """
        Register a cleanup callback for a specific phase.

        Args:
            phase: The cleanup phase
            callback: Function to call during this phase
        """
        self.cleanup_callbacks[phase].append(callback)
        self.logger.debug(f"Registered cleanup callback for phase: {phase.value}")

    def register_resource(self, name: str, resource: Any, priority: CleanupPriority = CleanupPriority.NORMAL) -> None:
        """
        Register a VTK resource for cleanup tracking.

        Args:
            name: Name identifier for the resource
            resource: The VTK resource object
            priority: Cleanup priority for this resource
        """
        self.cleanup_resources[name] = {
            "resource": resource,
            "priority": priority,
            "cleaned": False
        }
        self.logger.debug(f"Registered resource for cleanup: {name} (priority: {priority.value})")

    def coordinate_cleanup(self, render_window: Optional[vtk.vtkRenderWindow] = None,
                          renderer: Optional[vtk.vtkRenderer] = None,
                          interactor: Optional[vtk.vtkRenderWindowInteractor] = None) -> bool:
        """
        Coordinate the complete VTK cleanup process.

        Args:
            render_window: The render window to cleanup
            renderer: The renderer to cleanup
            interactor: The interactor to cleanup

        Returns:
            True if cleanup completed successfully, False if skipped due to context loss
        """
        if self.cleanup_in_progress:
            self.logger.debug("Cleanup already in progress, skipping")
            return True

        try:
            self.cleanup_in_progress = True
            self.logger.info("Starting coordinated VTK cleanup")

            # Store references for cleanup
            if render_window:
                self.cleanup_resources["render_window"] = {
                    "resource": render_window,
                    "priority": CleanupPriority.CRITICAL,
                    "cleaned": False
                }
            if renderer:
                self.cleanup_resources["renderer"] = {
                    "resource": renderer,
                    "priority": CleanupPriority.HIGH,
                    "cleaned": False
                }
            if interactor:
                self.cleanup_resources["interactor"] = {
                    "resource": interactor,
                    "priority": CleanupPriority.HIGH,
                    "cleaned": False
                }

            # Execute cleanup phases in order
            success = self._execute_cleanup_phases()

            if success:
                self.logger.info("VTK cleanup completed successfully")
            else:
                self.logger.info("VTK cleanup completed with context loss (normal during shutdown)")

            return success

        except Exception as e:
            self.logger.error(f"Error during cleanup coordination: {e}")
            return False

        finally:
            self.cleanup_in_progress = False
            self._reset_cleanup_state()

    def _execute_cleanup_phases(self) -> bool:
        """Execute cleanup phases in proper order."""
        phases = [
            CleanupPhase.PRE_CLEANUP,
            CleanupPhase.CONTEXT_VALIDATION,
            CleanupPhase.RESOURCE_CLEANUP,
            CleanupPhase.ACTOR_CLEANUP,
            CleanupPhase.RENDERER_CLEANUP,
            CleanupPhase.WINDOW_CLEANUP,
            CleanupPhase.INTERACTOR_CLEANUP,
            CleanupPhase.FINAL_CLEANUP,
            CleanupPhase.POST_CLEANUP
        ]

        for phase in phases:
            try:
                self.logger.debug(f"Executing cleanup phase: {phase.value}")

                # Execute callbacks for this phase
                for callback in self.cleanup_callbacks[phase]:
                    try:
                        result = callback()
                        if result is False:  # Callback indicated failure
                            self.logger.debug(f"Cleanup phase {phase.value} indicated early termination")
                            return False
                    except Exception as e:
                        self.logger.debug(f"Error in cleanup phase {phase.value}: {e}")
                        # Continue with other phases unless it's critical

                # Small delay between phases to allow context cleanup
                time.sleep(0.01)

            except Exception as e:
                self.logger.debug(f"Exception in cleanup phase {phase.value}: {e}")
                continue

        return True

    def _pre_cleanup(self) -> Optional[bool]:
        """Pre-cleanup phase: Prepare for cleanup."""
        try:
            # Suppress VTK errors during cleanup
            self.error_handler.suppress_errors_temporarily(5000)

            # Force garbage collection to clean up any pending objects
            gc.collect()

            self.logger.debug("Pre-cleanup phase completed")
            return True

        except Exception as e:
            self.logger.debug(f"Pre-cleanup error: {e}")
            return True  # Continue even if pre-cleanup fails

    def _validate_context(self) -> Optional[bool]:
        """Context validation phase: Check if context is still valid."""
        try:
            render_window = self.cleanup_resources.get("render_window", {}).get("resource")
            if not render_window:
                self.logger.debug("No render window to validate")
                return True

            is_valid, context_state = self.context_manager.validate_context(render_window, "cleanup")

            if not is_valid:
                self.context_lost_detected = True
                self.logger.info(f"Context lost during cleanup: {context_state}")

                # If context is lost, we should skip most cleanup operations
                # but still clean up Python references
                return False  # Signal early termination

            self.logger.debug("Context validation passed")
            return True

        except Exception as e:
            self.logger.debug(f"Context validation error: {e}")
            self.context_lost_detected = True
            return False

    def _cleanup_resources(self) -> Optional[bool]:
        """Resource cleanup phase: Clean up VTK resources."""
        try:
            # Clean up resources in priority order
            sorted_resources = sorted(
                self.cleanup_resources.items(),
                key=lambda x: x[1]["priority"].value
            )

            for name, resource_info in sorted_resources:
                if resource_info["cleaned"]:
                    continue

                resource = resource_info["resource"]
                if not resource:
                    continue

                try:
                    self._cleanup_single_resource(name, resource)
                    resource_info["cleaned"] = True

                except Exception as e:
                    self.logger.debug(f"Error cleaning up resource {name}: {e}")
                    # Continue with other resources

            self.logger.debug("Resource cleanup phase completed")
            return True

        except Exception as e:
            self.logger.debug(f"Resource cleanup error: {e}")
            return True

    def _cleanup_single_resource(self, name: str, resource: Any) -> None:
        """Clean up a single resource based on its type."""
        try:
            # Handle different VTK resource types
            if isinstance(resource, vtk.vtkActor):
                self._cleanup_actor(resource)
            elif isinstance(resource, vtk.vtkRenderer):
                self._cleanup_renderer_resource(resource)
            elif isinstance(resource, vtk.vtkRenderWindow):
                self._cleanup_window_resource(resource)
            elif isinstance(resource, vtk.vtkRenderWindowInteractor):
                self._cleanup_interactor_resource(resource)
            elif isinstance(resource, vtk.vtkPolyDataMapper):
                self._cleanup_mapper(resource)
            elif isinstance(resource, vtk.vtkOrientationMarkerWidget):
                self._cleanup_orientation_widget(resource)
            else:
                # Generic cleanup - try to delete if it has a Delete method
                if hasattr(resource, 'Delete'):
                    resource.Delete()

        except Exception as e:
            self.logger.debug(f"Error in single resource cleanup for {name}: {e}")

    def _cleanup_actors(self) -> Optional[bool]:
        """Actor cleanup phase: Remove actors from renderer."""
        try:
            renderer = self.cleanup_resources.get("renderer", {}).get("resource")
            if not renderer:
                return True

            # Remove all actors from renderer
            try:
                renderer.RemoveAllViewProps()
                self.logger.debug("Removed all actors from renderer")
            except Exception as e:
                self.logger.debug(f"Error removing actors: {e}")

            return True

        except Exception as e:
            self.logger.debug(f"Actor cleanup error: {e}")
            return True

    def _cleanup_renderer(self) -> Optional[bool]:
        """Renderer cleanup phase."""
        try:
            renderer = self.cleanup_resources.get("renderer", {}).get("resource")
            if not renderer:
                return True

            # Clear renderer resources
            try:
                # Remove lights
                lights = renderer.GetLights()
                if lights:
                    lights.RemoveAllItems()

                # Clear other renderer resources
                renderer.RemoveAllViewProps()

                self.logger.debug("Renderer cleanup completed")
            except Exception as e:
                self.logger.debug(f"Renderer cleanup error: {e}")

            return True

        except Exception as e:
            self.logger.debug(f"Renderer cleanup error: {e}")
            return True

    def _cleanup_window(self) -> Optional[bool]:
        """Window cleanup phase."""
        try:
            render_window = self.cleanup_resources.get("render_window", {}).get("resource")
            if not render_window:
                return True

            # Check if context is safe for cleanup
            if not self.context_manager.is_context_safe_for_cleanup(render_window):
                self.logger.debug("Skipping window cleanup due to lost context")
                return True

            try:
                # Safe window cleanup operations
                render_window.Finalize()
                self.logger.debug("Render window finalized")
            except Exception as e:
                # This is expected if context is lost
                self.logger.debug(f"Expected window cleanup error: {e}")

            return True

        except Exception as e:
            self.logger.debug(f"Window cleanup error: {e}")
            return True

    def _cleanup_interactor(self) -> Optional[bool]:
        """Interactor cleanup phase."""
        try:
            interactor = self.cleanup_resources.get("interactor", {}).get("resource")
            if not interactor:
                return True

            try:
                # Terminate interactor
                interactor.TerminateApp()
                self.logger.debug("Interactor terminated")
            except Exception as e:
                self.logger.debug(f"Interactor cleanup error: {e}")

            return True

        except Exception as e:
            self.logger.debug(f"Interactor cleanup error: {e}")
            return True

    def _final_cleanup(self) -> Optional[bool]:
        """Final cleanup phase: Last cleanup operations."""
        try:
            # Clear all resource references
            for name, resource_info in self.cleanup_resources.items():
                resource_info["resource"] = None
                resource_info["cleaned"] = True

            # Clear context cache
            self.context_manager.clear_context_cache()

            # Force garbage collection
            gc.collect()

            self.logger.debug("Final cleanup completed")
            return True

        except Exception as e:
            self.logger.debug(f"Final cleanup error: {e}")
            return True

    def _post_cleanup(self) -> Optional[bool]:
        """Post-cleanup phase: Verify cleanup."""
        try:
            # Verify that resources are cleaned up
            cleaned_count = sum(1 for r in self.cleanup_resources.values() if r["cleaned"])
            total_count = len(self.cleanup_resources)

            self.logger.info(f"Cleanup verification: {cleaned_count}/{total_count} resources cleaned")

            # Reset state
            self._reset_cleanup_state()

            return True

        except Exception as e:
            self.logger.debug(f"Post-cleanup error: {e}")
            return True

    def _cleanup_actor(self, actor: vtk.vtkActor) -> None:
        """Clean up a VTK actor."""
        try:
            # Get the mapper and clean it up
            mapper = actor.GetMapper()
            if mapper:
                self._cleanup_mapper(mapper)

            # Clear actor properties
            actor.SetMapper(None)

        except Exception as e:
            self.logger.debug(f"Actor cleanup error: {e}")

    def _cleanup_mapper(self, mapper: vtk.vtkPolyDataMapper) -> None:
        """Clean up a VTK mapper."""
        try:
            # Clear input connections
            mapper.RemoveAllInputs()
            mapper.SetInputData(None)

        except Exception as e:
            self.logger.debug(f"Mapper cleanup error: {e}")

    def _cleanup_renderer_resource(self, renderer: vtk.vtkRenderer) -> None:
        """Clean up renderer resources."""
        try:
            # Remove all view props
            renderer.RemoveAllViewProps()

            # Clear lights
            lights = renderer.GetLights()
            if lights:
                lights.RemoveAllItems()

        except Exception as e:
            self.logger.debug(f"Renderer resource cleanup error: {e}")

    def _cleanup_window_resource(self, render_window: vtk.vtkRenderWindow) -> None:
        """Clean up render window resources."""
        try:
            # Only finalize if context is safe
            if self.context_manager.is_context_safe_for_cleanup(render_window):
                render_window.Finalize()

        except Exception as e:
            self.logger.debug(f"Window resource cleanup error: {e}")

    def _cleanup_interactor_resource(self, interactor: vtk.vtkRenderWindowInteractor) -> None:
        """Clean up interactor resources."""
        try:
            interactor.TerminateApp()

        except Exception as e:
            self.logger.debug(f"Interactor resource cleanup error: {e}")

    def _cleanup_orientation_widget(self, widget: vtk.vtkOrientationMarkerWidget) -> None:
        """Clean up orientation marker widget."""
        try:
            widget.Off()
            widget.SetInteractor(None)

        except Exception as e:
            self.logger.debug(f"Orientation widget cleanup error: {e}")

    def _reset_cleanup_state(self) -> None:
        """Reset cleanup state for next cleanup operation."""
        self.cleanup_in_progress = False
        self.context_lost_detected = False
        self.cleanup_resources.clear()

    def is_cleanup_in_progress(self) -> bool:
        """Check if cleanup is currently in progress."""
        return self.cleanup_in_progress

    def was_context_lost(self) -> bool:
        """Check if context was lost during cleanup."""
        return self.context_lost_detected

    def get_cleanup_stats(self) -> Dict[str, Any]:
        """Get cleanup statistics."""
        cleaned_count = sum(1 for r in self.cleanup_resources.values() if r["cleaned"])
        total_count = len(self.cleanup_resources)

        return {
            "cleanup_in_progress": self.cleanup_in_progress,
            "context_lost_detected": self.context_lost_detected,
            "resources_registered": total_count,
            "resources_cleaned": cleaned_count,
            "cleanup_callbacks_registered": sum(len(callbacks) for callbacks in self.cleanup_callbacks.values())
        }


# Global cleanup coordinator instance
_vtk_cleanup_coordinator: Optional[VTKCleanupCoordinator] = None


def get_vtk_cleanup_coordinator() -> VTKCleanupCoordinator:
    """Get the global VTK cleanup coordinator instance."""
    global _vtk_cleanup_coordinator
    if _vtk_cleanup_coordinator is None:
        _vtk_cleanup_coordinator = VTKCleanupCoordinator()
    return _vtk_cleanup_coordinator


def coordinate_vtk_cleanup(render_window: Optional[vtk.vtkRenderWindow] = None,
                          renderer: Optional[vtk.vtkRenderer] = None,
                          interactor: Optional[vtk.vtkRenderWindowInteractor] = None) -> bool:
    """
    Convenience function to coordinate VTK cleanup.

    Args:
        render_window: The render window to cleanup
        renderer: The renderer to cleanup
        interactor: The interactor to cleanup

    Returns:
        True if cleanup completed successfully
    """
    return get_vtk_cleanup_coordinator().coordinate_cleanup(render_window, renderer, interactor)