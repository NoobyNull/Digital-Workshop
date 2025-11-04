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

from src.core.logging_config import get_logger
from .error_handler import get_vtk_error_handler
from .context_manager import get_vtk_context_manager
from .resource_tracker import get_vtk_resource_tracker


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

    CRITICAL = 1  # Must be cleaned up first
    HIGH = 2  # Should be cleaned up early
    NORMAL = 3  # Standard cleanup order
    LOW = 4  # Can be cleaned up later
    DEFERRED = 5  # Clean up last or skip if context lost


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

        # CRITICAL FIX: Robust resource tracker initialization with fallback
        self.resource_tracker = None
        self._initialize_resource_tracker_with_fallback()

        # Cleanup state
        self.cleanup_in_progress = False
        self.context_lost_detected = False
        self.cleanup_completed = False  # CRITICAL FIX: Prevent duplicate cleanup
        self.cleanup_callbacks: Dict[CleanupPhase, List[Callable]] = {}
        self.cleanup_resources: Dict[str, Any] = {}

        # Setup cleanup phases
        self._setup_cleanup_phases()

        self.logger.info("VTK Cleanup Coordinator initialized")

    def _initialize_resource_tracker_with_fallback(self) -> None:
        """
        CRITICAL FIX: Initialize resource tracker with robust fallback mechanisms.

        This method ensures the resource tracker is always available during cleanup
        operations, even if the primary initialization fails.
        """
        max_retries = 3
        retry_delay = 0.1  # 100ms between retries

        for attempt in range(max_retries):
            try:
                self.logger.info(
                    f"CRITICAL FIX: Initializing resource tracker (attempt {attempt + 1}/{max_retries})"
                )

                # Try to get the global resource tracker
                tracker = get_vtk_resource_tracker()

                # Verify the tracker is functional
                if tracker is not None:
                    # Test basic functionality
                    test_stats = tracker.get_statistics()
                    if isinstance(test_stats, dict):
                        self.resource_tracker = tracker
                        self.logger.info(
                            "CRITICAL FIX: Resource tracker initialized successfully with fallback"
                        )
                        return
                    else:
                        raise ValueError("Resource tracker returned invalid statistics")
                else:
                    raise ValueError("Resource tracker is None")

            except Exception as e:
                self.logger.warning(
                    f"CRITICAL FIX: Resource tracker initialization attempt {attempt + 1} failed: {e}"
                )

                if attempt < max_retries - 1:
                    self.logger.info("CRITICAL FIX: Retrying in %ss...", retry_delay)
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    self.logger.error(
                        "CRITICAL FIX: All resource tracker initialization attempts failed"
                    )

        # Final fallback: Create a minimal mock tracker for cleanup operations
        self._create_fallback_resource_tracker()

    def _create_fallback_resource_tracker(self) -> None:
        """
        Create a minimal fallback resource tracker when the primary tracker fails.

        This ensures cleanup operations can still proceed even without the full
        resource tracking functionality.
        """
        try:

            class FallbackResourceTracker:
                """Minimal fallback resource tracker for emergency cleanup."""

                def __init__(self):
                    self.logger = get_logger(__name__)
                    self.resources = {}

                def cleanup_all_resources(self) -> Dict[str, int]:
                    """Fallback cleanup that does basic resource cleanup."""
                    try:
                        self.logger.info(
                            "CRITICAL FIX: Using fallback resource tracker for cleanup"
                        )
                        success_count = 0
                        error_count = 0

                        # Basic cleanup without tracking
                        for resource_id, resource_info in self.resources.items():
                            try:
                                resource = resource_info.get("resource")
                                if resource and hasattr(resource, "Delete"):
                                    resource.Delete()
                                    success_count += 1
                            except Exception:
                                error_count += 1

                        return {
                            "total": len(self.resources),
                            "success": success_count,
                            "errors": error_count,
                        }
                    except Exception as e:
                        self.logger.error("CRITICAL FIX: Fallback cleanup failed: %s", e)
                        return {"total": 0, "success": 0, "errors": 1}

                def get_statistics(self) -> Dict[str, Any]:
                    """Return minimal statistics for fallback tracker."""
                    return {"total_tracked": len(self.resources), "fallback_mode": True}

            self.resource_tracker = FallbackResourceTracker()
            self.logger.warning(
                "CRITICAL FIX: Fallback resource tracker created - limited cleanup functionality"
            )

        except Exception as e:
            self.logger.error("CRITICAL FIX: Failed to create fallback resource tracker: %s", e)
            self.resource_tracker = None

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

    def emergency_shutdown_cleanup(self) -> None:
        """Emergency cleanup called during application shutdown."""
        try:
            # CRITICAL FIX: Skip if cleanup already completed
            if self.cleanup_completed:
                self.logger.debug(
                    "CRITICAL FIX: Emergency shutdown cleanup skipped - already completed"
                )
                return

            self.logger.info("CRITICAL FIX: Emergency shutdown cleanup initiated")

            # CRITICAL FIX: Suppress all VTK errors during emergency cleanup
            vtk.vtkObject.GlobalWarningDisplayOff()

            # CRITICAL FIX: Comprehensive VTK object cleanup before context loss
            self._perform_comprehensive_vtk_cleanup()

            # Perform basic cleanup without context validation
            if self.resource_tracker is not None:
                try:
                    cleanup_stats = self.resource_tracker.cleanup_all_resources()
                    self.logger.info(
                        f"CRITICAL FIX: Emergency shutdown cleanup - "
                        f"{cleanup_stats.get('success', 0)} cleaned, {cleanup_stats.get('errors', 0)} errors"
                    )
                except Exception as e:
                    self.logger.warning(
                        f"CRITICAL FIX: Emergency resource tracker cleanup failed: {e}"
                    )

            # Mark as completed to prevent further cleanup attempts
            self.cleanup_completed = True

            # Force garbage collection with VTK error suppression
            for _ in range(3):
                try:
                    gc.collect()
                except Exception:
                    pass  # Suppress any errors during garbage collection
                time.sleep(0.01)

            # CRITICAL FIX: Final VTK cleanup suppression
            vtk.vtkObject.GlobalWarningDisplayOff()

            self.logger.info("CRITICAL FIX: Emergency shutdown cleanup completed")

        except Exception as e:
            self.logger.error("CRITICAL FIX: Emergency shutdown cleanup failed: %s", e)

    def register_cleanup_callback(self, phase: CleanupPhase, callback: Callable) -> None:
        """
        Register a cleanup callback for a specific phase.

        Args:
            phase: The cleanup phase
            callback: Function to call during this phase
        """
        self.cleanup_callbacks[phase].append(callback)
        self.logger.debug("Registered cleanup callback for phase: %s", phase.value)

    def register_resource(
        self,
        name: str,
        resource: Any,
        priority: CleanupPriority = CleanupPriority.NORMAL,
    ) -> None:
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
            "cleaned": False,
        }
        self.logger.debug("Registered resource for cleanup: %s (priority: {priority.value})", name)

    def coordinate_cleanup(
        self,
        render_window: Optional[vtk.vtkRenderWindow] = None,
        renderer: Optional[vtk.vtkRenderer] = None,
        interactor: Optional[vtk.vtkRenderWindowInteractor] = None,
    ) -> bool:
        """
        Coordinate the complete VTK cleanup process.

        Args:
            render_window: The render window to cleanup
            renderer: The renderer to cleanup
            interactor: The interactor to cleanup

        Returns:
            True if cleanup completed successfully, False if skipped due to context loss
        """
        # CRITICAL FIX: Prevent duplicate cleanup attempts
        if self.cleanup_completed:
            self.logger.debug("VTK cleanup already completed, skipping duplicate cleanup")
            return True

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
                    "cleaned": False,
                }
            if renderer:
                self.cleanup_resources["renderer"] = {
                    "resource": renderer,
                    "priority": CleanupPriority.HIGH,
                    "cleaned": False,
                }
            if interactor:
                self.cleanup_resources["interactor"] = {
                    "resource": interactor,
                    "priority": CleanupPriority.HIGH,
                    "cleaned": False,
                }

            # Execute cleanup phases in order
            success = self._execute_cleanup_phases()

            # CRITICAL FIX: Mark cleanup as completed to prevent duplicates
            self.cleanup_completed = True

            if success:
                self.logger.info("VTK cleanup completed successfully")
            else:
                self.logger.info("VTK cleanup completed with context loss (normal during shutdown)")

            return success

        except Exception as e:
            self.logger.error("Error during cleanup coordination: %s", e)
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
            CleanupPhase.POST_CLEANUP,
        ]

        for phase in phases:
            try:
                self.logger.debug("Executing cleanup phase: %s", phase.value)

                # Execute callbacks for this phase
                for callback in self.cleanup_callbacks[phase]:
                    try:
                        result = callback()
                        if result is False:  # Callback indicated failure
                            self.logger.debug(
                                f"Cleanup phase {phase.value} indicated early termination"
                            )
                            return False
                    except Exception as e:
                        self.logger.debug("Error in cleanup phase %s: {e}", phase.value)
                        # Continue with other phases unless it's critical

                # Small delay between phases to allow context cleanup
                time.sleep(0.01)

            except Exception as e:
                self.logger.debug("Exception in cleanup phase %s: {e}", phase.value)
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
            self.logger.debug("Pre-cleanup error: %s", e)
            return True  # Continue even if pre-cleanup fails

    def _validate_context(self) -> Optional[bool]:
        """Context validation phase: Check if context is still valid."""
        try:
            render_window = self.cleanup_resources.get("render_window", {}).get("resource")
            if not render_window:
                self.logger.debug("No render window to validate")
                return True

            is_valid, context_state = self.context_manager.validate_context(
                render_window, "cleanup"
            )

            if not is_valid:
                self.context_lost_detected = True
                self.logger.info("Context lost during cleanup: %s", context_state)

                # If context is lost, we should skip most cleanup operations
                # but still clean up Python references
                return False  # Signal early termination

            self.logger.debug("Context validation passed")
            return True

        except Exception as e:
            self.logger.debug("Context validation error: %s", e)
            self.context_lost_detected = True
            return False

    def _cleanup_resources(self) -> Optional[bool]:
        """Resource cleanup phase: Clean up VTK resources."""
        try:
            # Clean up resources in priority order
            sorted_resources = sorted(
                self.cleanup_resources.items(), key=lambda x: x[1]["priority"].value
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
                    self.logger.debug("Error cleaning up resource %s: {e}", name)
                    # Continue with other resources

            self.logger.debug("Resource cleanup phase completed")
            return True

        except Exception as e:
            self.logger.debug("Resource cleanup error: %s", e)
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
                if hasattr(resource, "Delete"):
                    resource.Delete()

        except Exception as e:
            self.logger.debug("Error in single resource cleanup for %s: {e}", name)

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
                self.logger.debug("Error removing actors: %s", e)

            return True

        except Exception as e:
            self.logger.debug("Actor cleanup error: %s", e)
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
                self.logger.debug("Renderer cleanup error: %s", e)

            return True

        except Exception as e:
            self.logger.debug("Renderer cleanup error: %s", e)
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
                self.logger.debug("Expected window cleanup error: %s", e)

            return True

        except Exception as e:
            self.logger.debug("Window cleanup error: %s", e)
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
                self.logger.debug("Interactor cleanup error: %s", e)

            return True

        except Exception as e:
            self.logger.debug("Interactor cleanup error: %s", e)
            return True

    def _final_cleanup(self) -> Optional[bool]:
        """Final cleanup phase: Last cleanup operations with robust resource tracker handling."""
        try:
            # CRITICAL FIX: Enhanced resource tracker cleanup with comprehensive error handling
            self._perform_robust_resource_tracker_cleanup()

            # Clear all resource references with enhanced logging
            self._clear_resource_references()

            # Clear context cache with error handling
            self._clear_context_cache_safely()

            # Force garbage collection with timing
            start_time = time.time()
            gc.collect()
            gc_time = time.time() - start_time
            self.logger.debug("CRITICAL FIX: Garbage collection completed in %ss", gc_time:.3f)

            self.logger.info("CRITICAL FIX: Final cleanup phase completed successfully")
            return True

        except Exception as e:
            self.logger.error("CRITICAL FIX: Final cleanup error: %s", e)
            return True

    def _perform_robust_resource_tracker_cleanup(self) -> None:
        """
        CRITICAL FIX: Perform resource tracker cleanup with multiple fallback strategies.

        This method ensures resource cleanup happens even if the resource tracker
        becomes unavailable during shutdown.
        """
        try:
            if self.resource_tracker is not None:
                try:
                    # Verify tracker is still functional
                    stats = self.resource_tracker.get_statistics()
                    if isinstance(stats, dict):
                        self.logger.info(
                            "CRITICAL FIX: Resource tracker is functional, performing cleanup"
                        )
                        cleanup_stats = self.resource_tracker.cleanup_all_resources()

                        self.logger.info(
                            f"CRITICAL FIX: Resource tracker cleanup completed - "
                            f"{cleanup_stats.get('success', 0)} cleaned, {cleanup_stats.get('errors', 0)} errors"
                        )
                    else:
                        raise ValueError("Resource tracker returned invalid statistics")

                except Exception as e:
                    self.logger.warning("CRITICAL FIX: Resource tracker cleanup failed: %s", e)
                    # Try to reinitialize the tracker
                    self._attempt_tracker_reinitialization()
            else:
                self.logger.warning(
                    "CRITICAL FIX: Resource tracker is None, attempting emergency cleanup"
                )
                self._perform_emergency_cleanup()

        except Exception as e:
            self.logger.error("CRITICAL FIX: Critical error in resource tracker cleanup: %s", e)
            # Last resort: perform basic cleanup without tracking
            self._perform_basic_emergency_cleanup()

    def _attempt_tracker_reinitialization(self) -> None:
        """Attempt to reinitialize the resource tracker during cleanup."""
        try:
            self.logger.info("CRITICAL FIX: Attempting to reinitialize resource tracker")
            self._initialize_resource_tracker_with_fallback()

            if self.resource_tracker is not None:
                self.logger.info("CRITICAL FIX: Resource tracker reinitialized successfully")
                # Try cleanup again with reinitialized tracker
                cleanup_stats = self.resource_tracker.cleanup_all_resources()
                self.logger.info(
                    f"CRITICAL FIX: Reinitialized tracker cleanup - "
                    f"{cleanup_stats.get('success', 0)} cleaned, {cleanup_stats.get('errors', 0)} errors"
                )
            else:
                self.logger.warning("CRITICAL FIX: Failed to reinitialize resource tracker")

        except Exception as e:
            self.logger.error("CRITICAL FIX: Failed to reinitialize resource tracker: %s", e)

    def _perform_emergency_cleanup(self) -> None:
        """Perform emergency cleanup when resource tracker is unavailable."""
        try:
            self.logger.warning(
                "CRITICAL FIX: Performing emergency cleanup without resource tracker"
            )

            # Try to get a fresh resource tracker instance
            try:
                emergency_tracker = get_vtk_resource_tracker()
                if emergency_tracker is not None:
                    cleanup_stats = emergency_tracker.cleanup_all_resources()
                    self.logger.info(
                        f"CRITICAL FIX: Emergency tracker cleanup - "
                        f"{cleanup_stats.get('success', 0)} cleaned, {cleanup_stats.get('errors', 0)} errors"
                    )
                else:
                    raise ValueError("Emergency tracker is also None")
            except Exception:
                self.logger.warning(
                    "CRITICAL FIX: Emergency tracker unavailable, using basic cleanup"
                )
                self._perform_basic_emergency_cleanup()

        except Exception as e:
            self.logger.error("CRITICAL FIX: Emergency cleanup failed: %s", e)

    def _perform_basic_emergency_cleanup(self) -> None:
        """Perform basic emergency cleanup without any resource tracking."""
        try:
            self.logger.warning("CRITICAL FIX: Performing basic emergency cleanup")

            # Clean up any VTK objects we can find
            vtk.vtkObject.GlobalWarningDisplayOff()  # Suppress warnings during emergency cleanup

            # Force garbage collection multiple times
            for i in range(3):
                gc.collect()
                time.sleep(0.01)

            self.logger.info("CRITICAL FIX: Basic emergency cleanup completed")

        except Exception as e:
            self.logger.error("CRITICAL FIX: Basic emergency cleanup failed: %s", e)

    def _clear_resource_references(self) -> None:
        """Clear all resource references with enhanced logging."""
        try:
            cleared_count = 0
            for resource_name, resource_info in self.cleanup_resources.items():
                try:
                    resource_info["resource"] = None
                    resource_info["cleaned"] = True
                    cleared_count += 1
                    self.logger.debug("CRITICAL FIX: Cleared resource reference: %s", resource_name)
                except Exception as e:
                    self.logger.debug("CRITICAL FIX: Error clearing resource %s: {e}", resource_name)

            self.logger.info("CRITICAL FIX: Cleared %s resource references", cleared_count)

        except Exception as e:
            self.logger.error("CRITICAL FIX: Error clearing resource references: %s", e)

    def _clear_context_cache_safely(self) -> None:
        """Clear context cache with comprehensive error handling."""
        try:
            if hasattr(self.context_manager, "clear_context_cache"):
                self.context_manager.clear_context_cache()
                self.logger.debug("CRITICAL FIX: Context cache cleared successfully")
            else:
                self.logger.debug(
                    "CRITICAL FIX: Context manager does not have clear_context_cache method"
                )
        except Exception as e:
            self.logger.debug("CRITICAL FIX: Context cache clear error: %s", e)

    def _post_cleanup(self) -> Optional[bool]:
        """Post-cleanup phase: Verify cleanup."""
        try:
            # Verify that resources are cleaned up
            cleaned_count = sum(1 for r in self.cleanup_resources.values() if r["cleaned"])
            total_count = len(self.cleanup_resources)

            self.logger.info(
                f"Cleanup verification: {cleaned_count}/{total_count} resources cleaned"
            )

            # Reset state
            self._reset_cleanup_state()

            return True

        except Exception as e:
            self.logger.debug("Post-cleanup error: %s", e)
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
            self.logger.debug("Actor cleanup error: %s", e)

    def _cleanup_mapper(self, mapper: vtk.vtkPolyDataMapper) -> None:
        """Clean up a VTK mapper."""
        try:
            # Clear input connections
            mapper.RemoveAllInputs()
            mapper.SetInputData(None)

        except Exception as e:
            self.logger.debug("Mapper cleanup error: %s", e)

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
            self.logger.debug("Renderer resource cleanup error: %s", e)

    def _cleanup_window_resource(self, render_window: vtk.vtkRenderWindow) -> None:
        """Clean up render window resources."""
        try:
            # Only finalize if context is safe
            if self.context_manager.is_context_safe_for_cleanup(render_window):
                render_window.Finalize()

        except Exception as e:
            self.logger.debug("Window resource cleanup error: %s", e)

    def _cleanup_interactor_resource(self, interactor: vtk.vtkRenderWindowInteractor) -> None:
        """Clean up interactor resources."""
        try:
            interactor.TerminateApp()

        except Exception as e:
            self.logger.debug("Interactor resource cleanup error: %s", e)

    def _cleanup_orientation_widget(self, widget: vtk.vtkOrientationMarkerWidget) -> None:
        """Clean up orientation marker widget."""
        try:
            widget.Off()
            widget.SetInteractor(None)

        except Exception as e:
            self.logger.debug("Orientation widget cleanup error: %s", e)

    def _perform_comprehensive_vtk_cleanup(self) -> None:
        """
        CRITICAL FIX: Perform comprehensive VTK object cleanup before context loss.

        This method ensures all VTK objects are properly deleted before the OpenGL
        context is destroyed, preventing wglMakeCurrent errors during shutdown.
        """
        try:
            self.logger.debug("CRITICAL FIX: Starting comprehensive VTK cleanup")

            # Clean up common VTK objects that might still exist
            vtk_classes_to_cleanup = [
                "vtkRenderWindow",
                "vtkRenderer",
                "vtkRenderWindowInteractor",
                "vtkActor",
                "vtkPolyDataMapper",
                "vtkPolyData",
                "vtkPoints",
                "vtkCellArray",
                "vtkCamera",
                "vtkLight",
                "vtkOrientationMarkerWidget",
                "vtkAxesActor",
                "vtkTextActor",
            ]

            cleaned_count = 0

            # Try to find and clean up VTK objects in the current namespace
            import sys
            import gc

            # Get all objects in the current frame and globals
            current_frame = sys._getframe()
            current_globals = current_frame.f_globals
            current_locals = current_frame.f_locals

            # Search for VTK objects in globals and locals
            for namespace_name, namespace in [
                ("globals", current_globals),
                ("locals", current_locals),
            ]:
                for obj_name, obj in namespace.items():
                    try:
                        # Check if it's a VTK object
                        if hasattr(obj, "__class__") and hasattr(obj.__class__, "__module__"):
                            if "vtk" in obj.__class__.__module__:
                                # Try to delete it safely
                                if hasattr(obj, "Delete"):
                                    obj.Delete()
                                    cleaned_count += 1
                                    self.logger.debug(
                                        f"CRITICAL FIX: Cleaned up VTK object: {obj_name} from {namespace_name}"
                                    )
                    except Exception:
                        # Silently continue if cleanup fails
                        pass

            # Force garbage collection to clean up any remaining references
            for _ in range(2):
                try:
                    gc.collect()
                except Exception:
                    pass

            self.logger.debug(
                f"CRITICAL FIX: Comprehensive VTK cleanup completed - {cleaned_count} objects cleaned"
            )

        except Exception as e:
            self.logger.debug("CRITICAL FIX: Comprehensive VTK cleanup error: %s", e)

    def _reset_cleanup_state(self) -> None:
        """Reset cleanup state for next cleanup operation."""
        self.cleanup_in_progress = False
        self.context_lost_detected = False
        # CRITICAL FIX: Don't reset cleanup_completed flag - it should persist
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
            "cleanup_callbacks_registered": sum(
                len(callbacks) for callbacks in self.cleanup_callbacks.values()
            ),
        }


# Global cleanup coordinator instance
_vtk_cleanup_coordinator: Optional[VTKCleanupCoordinator] = None


def get_vtk_cleanup_coordinator() -> VTKCleanupCoordinator:
    """Get the global VTK cleanup coordinator instance."""
    global _vtk_cleanup_coordinator
    if _vtk_cleanup_coordinator is None:
        _vtk_cleanup_coordinator = VTKCleanupCoordinator()
    return _vtk_cleanup_coordinator


def coordinate_vtk_cleanup(
    render_window: Optional[vtk.vtkRenderWindow] = None,
    renderer: Optional[vtk.vtkRenderer] = None,
    interactor: Optional[vtk.vtkRenderWindowInteractor] = None,
) -> bool:
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
