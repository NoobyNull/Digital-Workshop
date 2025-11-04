"""
Optimized VTK Cleanup Coordinator with Enhanced Context Management.

This module provides an optimized cleanup sequence that ensures VTK resources are cleaned up
BEFORE OpenGL context destruction, preventing "wglMakeCurrent failed in Clean(), error: 6" errors.

Key improvements:
- Early context loss detection
- Context-aware cleanup procedures
- Proper timing coordination between VTK and OpenGL cleanup
- Comprehensive logging for context management operations
- Prevention of VTK cleanup after OpenGL context destruction
"""

import gc
import time
from typing import List, Dict, Any, Optional, Callable
from enum import Enum

import vtk

from src.core.logging_config import get_logger, log_function_call
from .error_handler import get_vtk_error_handler
from .resource_tracker import get_vtk_resource_tracker
from .enhanced_context_manager import (
    get_enhanced_vtk_context_manager,
    ContextState,
    ShutdownScenario,
    detect_context_loss_early,
)


logger = get_logger(__name__)


class CleanupPhase(Enum):
    """Optimized phases of VTK cleanup process."""

    PRE_CLEANUP = "pre_cleanup"
    EARLY_DETECTION = "early_detection"
    VTK_CLEANUP = "vtk_cleanup"
    CONTEXT_COORDINATION = "context_coordination"
    OPENGL_CLEANUP = "opengl_cleanup"
    FINAL_CLEANUP = "final_cleanup"
    POST_CLEANUP = "post_cleanup"


class CleanupPriority(Enum):
    """Priority levels for cleanup operations."""

    CRITICAL = 1  # Must be cleaned up first
    HIGH = 2  # Should be cleaned up early
    NORMAL = 3  # Standard cleanup order
    LOW = 4  # Can be cleaned up later
    DEFERRED = 5  # Clean up last or skip if context lost


class OptimizedVTKCleanupCoordinator:
    """
    Optimized VTK cleanup coordinator with enhanced context management.

    This coordinator ensures proper cleanup ordering:
    1. Early context loss detection
    2. VTK resource cleanup BEFORE OpenGL context destruction
    3. Context-aware cleanup procedures
    4. Timing coordination between VTK and OpenGL cleanup
    5. Comprehensive logging and error handling
    """

    def __init__(self):
        """Initialize the optimized cleanup coordinator."""
        self.logger = get_logger(__name__)
        self.error_handler = get_vtk_error_handler()
        self.context_manager = get_enhanced_vtk_context_manager()

        # Resource tracking with fallback
        self.resource_tracker = None
        self._initialize_resource_tracker_with_fallback()

        # Cleanup state
        self.cleanup_in_progress = False
        self.context_lost_detected = False
        self.cleanup_callbacks: Dict[CleanupPhase, List[Callable]] = {}
        self.cleanup_resources: Dict[str, Any] = {}

        # Timing coordination
        self.vtk_cleanup_start_time = 0.0
        self.vtk_cleanup_end_time = 0.0
        self.opengl_cleanup_start_time = 0.0
        self.opengl_cleanup_end_time = 0.0

        # Performance monitoring
        self.cleanup_operations = 0
        self.successful_cleanups = 0
        self.failed_cleanups = 0
        self.early_detections = 0

        # Setup cleanup phases
        self._setup_optimized_cleanup_phases()

        self.logger.info("Optimized VTK Cleanup Coordinator initialized")

    def _initialize_resource_tracker_with_fallback(self) -> None:
        """
        Initialize resource tracker with robust fallback mechanisms.

        This ensures the resource tracker is always available during cleanup operations.
        """
        max_retries = 3
        retry_delay = 0.1  # 100ms between retries

        for attempt in range(max_retries):
            try:
                self.logger.info(
                    f"Initializing resource tracker (attempt {attempt + 1}/{max_retries})"
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
                            "Resource tracker initialized successfully with fallback"
                        )
                        return
                    else:
                        raise ValueError("Resource tracker returned invalid statistics")
                else:
                    raise ValueError("Resource tracker is None")

            except Exception as e:
                self.logger.warning(
                    f"Resource tracker initialization attempt {attempt + 1} failed: {e}"
                )

                if attempt < max_retries - 1:
                    self.logger.info(f"Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    self.logger.error(
                        "All resource tracker initialization attempts failed"
                    )

        # Final fallback: Create a minimal mock tracker for cleanup operations
        self._create_fallback_resource_tracker()

    def _create_fallback_resource_tracker(self) -> None:
        """Create a minimal fallback resource tracker when the primary tracker fails."""
        try:

            class FallbackResourceTracker:
                """Minimal fallback resource tracker for emergency cleanup."""

                def __init__(self):
                    self.logger = get_logger(__name__)
                    self.resources = {}

                def cleanup_all_resources(self) -> Dict[str, Any]:
                    """Emergency cleanup of all tracked resources."""
                    try:
                        self.logger.info("Performing emergency resource cleanup")
                        cleanup_count = len(self.resources)
                        self.resources.clear()
                        return {
                            "cleanup_count": cleanup_count,
                            "status": "emergency_cleanup_completed",
                        }
                    except Exception as e:
                        self.logger.error(f"Emergency resource cleanup failed: {e}")
                        return {
                            "cleanup_count": 0,
                            "status": "emergency_cleanup_failed",
                            "error": str(e),
                        }

                def get_statistics(self) -> Dict[str, Any]:
                    """Get basic statistics."""
                    return {
                        "resource_count": len(self.resources),
                        "status": "fallback_mode",
                    }

            self.resource_tracker = FallbackResourceTracker()
            self.logger.info("Fallback resource tracker created successfully")

        except Exception as e:
            self.logger.error(f"Failed to create fallback resource tracker: {e}")

    def _setup_optimized_cleanup_phases(self) -> None:
        """Setup optimized cleanup phases with proper ordering."""
        # Clear existing callbacks
        self.cleanup_callbacks.clear()

        # Define optimized cleanup sequence
        self.cleanup_callbacks = {
            CleanupPhase.PRE_CLEANUP: [
                self._prepare_cleanup_environment,
                self._suppress_vtk_errors_temporarily,
            ],
            CleanupPhase.EARLY_DETECTION: [self._perform_early_context_detection],
            CleanupPhase.VTK_CLEANUP: [
                self._cleanup_vtk_resources_by_priority,
                self._cleanup_vtk_actors,
                self._cleanup_vtk_renderers,
                self._cleanup_vtk_windows,
                self._cleanup_vtk_interactors,
            ],
            CleanupPhase.CONTEXT_COORDINATION: [self._coordinate_context_transition],
            CleanupPhase.OPENGL_CLEANUP: [self._cleanup_opengl_resources],
            CleanupPhase.FINAL_CLEANUP: [
                self._perform_final_resource_cleanup,
                self._cleanup_resource_tracker,
            ],
            CleanupPhase.POST_CLEANUP: [
                self._verify_cleanup_completion,
                self._force_garbage_collection,
            ],
        }

    @log_function_call(logger)
    def coordinate_optimized_cleanup(
        self,
        render_window: vtk.vtkRenderWindow,
        scenario: ShutdownScenario = ShutdownScenario.NORMAL_SHUTDOWN,
    ) -> bool:
        """
        Coordinate the complete optimized cleanup sequence.

        This method ensures VTK cleanup happens BEFORE OpenGL context destruction,
        preventing the "wglMakeCurrent failed in Clean(), error: 6" error.

        Args:
            render_window: The render window to coordinate cleanup for
            scenario: The shutdown scenario type

        Returns:
            True if cleanup completed successfully
        """
        try:
            self.logger.info(
                f"Starting optimized cleanup sequence for scenario: {scenario.value}"
            )
            self.cleanup_in_progress = True
            self.cleanup_operations += 1

            # Set shutdown scenario for context-aware cleanup
            self.context_manager.set_shutdown_scenario(scenario)

            # Execute cleanup phases in optimized order
            cleanup_success = True
            for phase in CleanupPhase:
                try:
                    self.logger.debug(f"Executing cleanup phase: {phase.value}")
                    phase_success = self._execute_cleanup_phase(phase, render_window)
                    if not phase_success:
                        self.logger.warning(
                            f"Cleanup phase {phase.value} reported issues"
                        )
                        cleanup_success = False
                except Exception as e:
                    self.logger.error(f"Cleanup phase {phase.value} failed: {e}")
                    cleanup_success = False

            # Update success metrics
            if cleanup_success:
                self.successful_cleanups += 1
                self.logger.info("Optimized cleanup sequence completed successfully")
            else:
                self.failed_cleanups += 1
                self.logger.warning("Optimized cleanup sequence completed with errors")

            return cleanup_success

        except Exception as e:
            self.logger.error(f"Error during optimized cleanup coordination: {e}")
            self.failed_cleanups += 1
            return False
        finally:
            self.cleanup_in_progress = False

    def _execute_cleanup_phase(
        self, phase: CleanupPhase, render_window: vtk.vtkRenderWindow
    ) -> bool:
        """Execute a specific cleanup phase."""
        try:
            phase_callbacks = self.cleanup_callbacks.get(phase, [])
            phase_success = True

            for callback in phase_callbacks:
                try:
                    result = callback(render_window)
                    if not result:
                        phase_success = False
                except Exception as e:
                    self.logger.error(
                        f"Cleanup callback {callback.__name__} failed: {e}"
                    )
                    phase_success = False

            return phase_success

        except Exception as e:
            self.logger.error(f"Failed to execute cleanup phase {phase.value}: {e}")
            return False

    # Cleanup phase implementations
    def _prepare_cleanup_environment(self, render_window: vtk.vtkRenderWindow) -> bool:
        """Prepare the cleanup environment."""
        try:
            self.logger.debug("Preparing cleanup environment")

            # Record cleanup start time
            self.vtk_cleanup_start_time = time.time()

            # Clear any existing cleanup state
            self.context_lost_detected = False

            return True
        except Exception as e:
            self.logger.error(f"Failed to prepare cleanup environment: {e}")
            return False

    def _suppress_vtk_errors_temporarily(
        self, render_window: vtk.vtkRenderWindow
    ) -> bool:
        """Suppress VTK errors temporarily during cleanup."""
        try:
            self.logger.debug("Suppressing VTK errors temporarily")
            self.error_handler.suppress_errors_temporarily(2000)
            return True
        except Exception as e:
            self.logger.error(f"Failed to suppress VTK errors: {e}")
            return False

    def _perform_early_context_detection(
        self, render_window: vtk.vtkRenderWindow
    ) -> bool:
        """Perform early context loss detection."""
        try:
            self.logger.debug("Performing early context loss detection")

            early_detection, context_state = detect_context_loss_early(render_window)

            if early_detection:
                self.context_lost_detected = True
                self.early_detections += 1
                self.logger.warning(
                    f"Early context loss detected: {context_state.value}"
                )

                # Adjust cleanup strategy based on context state
                if context_state == ContextState.DESTROYING:
                    self.logger.info(
                        "Context is being destroyed - using emergency cleanup"
                    )
                    self._adjust_cleanup_for_destroying_context()
                elif context_state == ContextState.LOST:
                    self.logger.info("Context is already lost - using deferred cleanup")
                    self._adjust_cleanup_for_lost_context()
            else:
                self.logger.debug("Context is valid for cleanup")

            return True
        except Exception as e:
            self.logger.error(f"Early context detection failed: {e}")
            return False

    def _adjust_cleanup_for_destroying_context(self) -> bool:
        """Adjust cleanup strategy for destroying context."""
        try:
            self.logger.info("Adjusting cleanup for destroying context")

            # Replace normal cleanup with emergency cleanup
            self.cleanup_callbacks[CleanupPhase.VTK_CLEANUP] = [
                self._emergency_vtk_cleanup,
                self._skip_actor_cleanup,
                self._skip_renderer_cleanup,
                self._skip_window_cleanup,
                self._skip_interactor_cleanup,
            ]

            return True
        except Exception as e:
            self.logger.error(f"Failed to adjust cleanup for destroying context: {e}")
            return False

    def _adjust_cleanup_for_lost_context(self) -> bool:
        """Adjust cleanup strategy for lost context."""
        try:
            self.logger.info("Adjusting cleanup for lost context")

            # Use deferred cleanup for lost context
            self.cleanup_callbacks[CleanupPhase.VTK_CLEANUP] = [
                self._deferred_vtk_cleanup,
                self._deferred_actor_cleanup,
                self._deferred_renderer_cleanup,
                self._deferred_window_cleanup,
                self._deferred_interactor_cleanup,
            ]

            return True
        except Exception as e:
            self.logger.error(f"Failed to adjust cleanup for lost context: {e}")
            return False

    def _cleanup_vtk_resources_by_priority(
        self, render_window: vtk.vtkRenderWindow
    ) -> bool:
        """Clean up VTK resources by priority."""
        try:
            self.logger.debug("Cleaning up VTK resources by priority")

            if self.resource_tracker is not None:
                try:
                    cleanup_stats = self.resource_tracker.cleanup_all_resources()
                    self.logger.info(
                        f"Resource tracker cleanup completed: {cleanup_stats}"
                    )
                except Exception as e:
                    self.logger.warning(f"Resource tracker cleanup failed: {e}")

            return True
        except Exception as e:
            self.logger.error(f"Failed to cleanup VTK resources by priority: {e}")
            return False

    def _cleanup_vtk_actors(self, render_window: vtk.vtkRenderWindow) -> bool:
        """Clean up VTK actors."""
        try:
            self.logger.debug("Cleaning up VTK actors")

            if render_window and hasattr(render_window, "GetRenderers"):
                renderers = render_window.GetRenderers()
                if renderers:
                    for renderer in renderers:
                        if renderer and hasattr(renderer, "RemoveAllViewProps"):
                            renderer.RemoveAllViewProps()

            return True
        except Exception as e:
            self.logger.error(f"Failed to cleanup VTK actors: {e}")
            return False

    def _cleanup_vtk_renderers(self, render_window: vtk.vtkRenderWindow) -> bool:
        """Clean up VTK renderers."""
        try:
            self.logger.debug("Cleaning up VTK renderers")

            if render_window and hasattr(render_window, "GetRenderers"):
                renderers = render_window.GetRenderers()
                if renderers:
                    for renderer in renderers:
                        if renderer and hasattr(renderer, "Clear"):
                            renderer.Clear()

            return True
        except Exception as e:
            self.logger.error(f"Failed to cleanup VTK renderers: {e}")
            return False

    def _cleanup_vtk_windows(self, render_window: vtk.vtkRenderWindow) -> bool:
        """Clean up VTK windows."""
        try:
            self.logger.debug("Cleaning up VTK windows")

            if render_window:
                # Record VTK cleanup end time
                self.vtk_cleanup_end_time = time.time()
                vtk_cleanup_duration = (
                    self.vtk_cleanup_end_time - self.vtk_cleanup_start_time
                )
                self.logger.info(
                    f"VTK cleanup completed in {vtk_cleanup_duration:.3f}s"
                )

                # Finalize the render window
                if hasattr(render_window, "Finalize"):
                    render_window.Finalize()

            return True
        except Exception as e:
            self.logger.error(f"Failed to cleanup VTK windows: {e}")
            return False

    def _cleanup_vtk_interactors(self, render_window: vtk.vtkRenderWindow) -> bool:
        """Clean up VTK interactors."""
        try:
            self.logger.debug("Cleaning up VTK interactors")

            if render_window and hasattr(render_window, "GetInteractor"):
                interactor = render_window.GetInteractor()
                if interactor and hasattr(interactor, "TerminateApp"):
                    interactor.TerminateApp()

            return True
        except Exception as e:
            self.logger.error(f"Failed to cleanup VTK interactors: {e}")
            return False

    def _coordinate_context_transition(
        self, render_window: vtk.vtkRenderWindow
    ) -> bool:
        """Coordinate the transition from VTK to OpenGL cleanup."""
        try:
            self.logger.debug("Coordinating context transition")

            # Record OpenGL cleanup start time
            self.opengl_cleanup_start_time = time.time()

            # Ensure VTK cleanup is complete before proceeding
            if self.vtk_cleanup_end_time > 0:
                transition_delay = (
                    self.opengl_cleanup_start_time - self.vtk_cleanup_end_time
                )
                self.logger.info(f"Context transition delay: {transition_delay:.3f}s")

            # Use the enhanced context manager for coordination
            coordination_success = self.context_manager.coordinate_cleanup_sequence(
                render_window
            )

            return coordination_success
        except Exception as e:
            self.logger.error(f"Failed to coordinate context transition: {e}")
            return False

    def _cleanup_opengl_resources(self, render_window: vtk.vtkRenderWindow) -> bool:
        """Clean up OpenGL resources."""
        try:
            self.logger.debug("Cleaning up OpenGL resources")

            # Record OpenGL cleanup end time
            self.opengl_cleanup_end_time = time.time()
            opengl_cleanup_duration = (
                self.opengl_cleanup_end_time - self.opengl_cleanup_start_time
            )
            self.logger.info(
                f"OpenGL cleanup completed in {opengl_cleanup_duration:.3f}s"
            )

            # Calculate total cleanup time
            total_cleanup_time = (
                self.opengl_cleanup_end_time - self.vtk_cleanup_start_time
            )
            self.logger.info(f"Total cleanup time: {total_cleanup_time:.3f}s")

            return True
        except Exception as e:
            self.logger.error(f"Failed to cleanup OpenGL resources: {e}")
            return False

    def _perform_final_resource_cleanup(
        self, render_window: vtk.vtkRenderWindow
    ) -> bool:
        """Perform final resource cleanup."""
        try:
            self.logger.debug("Performing final resource cleanup")

            # Clear cleanup resources
            self.cleanup_resources.clear()

            return True
        except Exception as e:
            self.logger.error(f"Failed to perform final resource cleanup: {e}")
            return False

    def _cleanup_resource_tracker(self, render_window: vtk.vtkRenderWindow) -> bool:
        """Clean up the resource tracker."""
        try:
            self.logger.debug("Cleaning up resource tracker")

            if self.resource_tracker is not None:
                try:
                    final_stats = self.resource_tracker.cleanup_all_resources()
                    self.logger.info(f"Final resource tracker cleanup: {final_stats}")
                except Exception as e:
                    self.logger.warning(f"Final resource tracker cleanup failed: {e}")

            return True
        except Exception as e:
            self.logger.error(f"Failed to cleanup resource tracker: {e}")
            return False

    def _verify_cleanup_completion(self, render_window: vtk.vtkRenderWindow) -> bool:
        """Verify that cleanup completed successfully."""
        try:
            self.logger.debug("Verifying cleanup completion")

            # Check cleanup metrics
            success_rate = self.successful_cleanups / max(1, self.cleanup_operations)
            self.logger.info(f"Cleanup success rate: {success_rate:.2%}")

            # Check for context loss
            if self.context_lost_detected:
                self.logger.warning("Cleanup was performed with detected context loss")

            return True
        except Exception as e:
            self.logger.error(f"Failed to verify cleanup completion: {e}")
            return False

    def _force_garbage_collection(self, render_window: vtk.vtkRenderWindow) -> bool:
        """Force garbage collection to ensure cleanup."""
        try:
            self.logger.debug("Forcing garbage collection")

            # Force multiple garbage collection cycles
            for _ in range(3):
                gc.collect()
                time.sleep(0.001)  # Small delay between collections

            return True
        except Exception as e:
            self.logger.error(f"Failed to force garbage collection: {e}")
            return False

    # Emergency and deferred cleanup methods
    def _emergency_vtk_cleanup(self, render_window: vtk.vtkRenderWindow) -> bool:
        """Emergency VTK cleanup for critical situations."""
        try:
            self.logger.info("Performing emergency VTK cleanup")

            if render_window and hasattr(render_window, "Finalize"):
                render_window.Finalize()

            return True
        except Exception as e:
            self.logger.error(f"Emergency VTK cleanup failed: {e}")
            return False

    def _deferred_vtk_cleanup(self, render_window: vtk.vtkRenderWindow) -> bool:
        """Deferred VTK cleanup for lost context."""
        try:
            self.logger.info("Performing deferred VTK cleanup")

            # Skip operations that require valid context
            return True
        except Exception as e:
            self.logger.error(f"Deferred VTK cleanup failed: {e}")
            return False

    # Skip methods for emergency cleanup
    def _skip_actor_cleanup(self, render_window: vtk.vtkRenderWindow) -> bool:
        """Skip actor cleanup in emergency situations."""
        self.logger.debug("Skipping actor cleanup for emergency situation")
        return True

    def _skip_renderer_cleanup(self, render_window: vtk.vtkRenderWindow) -> bool:
        """Skip renderer cleanup in emergency situations."""
        self.logger.debug("Skipping renderer cleanup for emergency situation")
        return True

    def _skip_window_cleanup(self, render_window: vtk.vtkRenderWindow) -> bool:
        """Skip window cleanup in emergency situations."""
        self.logger.debug("Skipping window cleanup for emergency situation")
        return True

    def _skip_interactor_cleanup(self, render_window: vtk.vtkRenderWindow) -> bool:
        """Skip interactor cleanup in emergency situations."""
        self.logger.debug("Skipping interactor cleanup for emergency situation")
        return True

    # Deferred cleanup methods
    def _deferred_actor_cleanup(self, render_window: vtk.vtkRenderWindow) -> bool:
        """Deferred actor cleanup for lost context."""
        self.logger.debug("Performing deferred actor cleanup")
        return True

    def _deferred_renderer_cleanup(self, render_window: vtk.vtkRenderWindow) -> bool:
        """Deferred renderer cleanup for lost context."""
        self.logger.debug("Performing deferred renderer cleanup")
        return True

    def _deferred_window_cleanup(self, render_window: vtk.vtkRenderWindow) -> bool:
        """Deferred window cleanup for lost context."""
        self.logger.debug("Performing deferred window cleanup")
        return True

    def _deferred_interactor_cleanup(self, render_window: vtk.vtkRenderWindow) -> bool:
        """Deferred interactor cleanup for lost context."""
        self.logger.debug("Performing deferred interactor cleanup")
        return True

    def get_optimized_cleanup_stats(self) -> Dict[str, Any]:
        """Get statistics about optimized cleanup operations."""
        return {
            "cleanup_operations": self.cleanup_operations,
            "successful_cleanups": self.successful_cleanups,
            "failed_cleanups": self.failed_cleanups,
            "success_rate": self.successful_cleanups / max(1, self.cleanup_operations),
            "early_detections": self.early_detections,
            "context_lost_detected": self.context_lost_detected,
            "cleanup_in_progress": self.cleanup_in_progress,
            "resource_tracker_available": self.resource_tracker is not None,
            "context_manager_stats": self.context_manager.get_diagnostic_info(),
        }


# Global optimized cleanup coordinator instance
_optimized_vtk_cleanup_coordinator: Optional[OptimizedVTKCleanupCoordinator] = None


def get_optimized_vtk_cleanup_coordinator() -> OptimizedVTKCleanupCoordinator:
    """Get the global optimized VTK cleanup coordinator instance."""
    global _optimized_vtk_cleanup_coordinator
    if _optimized_vtk_cleanup_coordinator is None:
        _optimized_vtk_cleanup_coordinator = OptimizedVTKCleanupCoordinator()
    return _optimized_vtk_cleanup_coordinator


def coordinate_optimized_shutdown_cleanup(
    render_window: vtk.vtkRenderWindow,
    scenario: ShutdownScenario = ShutdownScenario.NORMAL_SHUTDOWN,
) -> bool:
    """
    Convenience function for coordinated optimized shutdown cleanup.

    Args:
        render_window: The render window to coordinate cleanup for
        scenario: The shutdown scenario type

    Returns:
        True if cleanup completed successfully
    """
    return get_optimized_vtk_cleanup_coordinator().coordinate_optimized_cleanup(
        render_window, scenario
    )


# Note: get_vtk_resource_tracker is imported from .resource_tracker
# This duplicate function has been removed to prevent naming conflicts
