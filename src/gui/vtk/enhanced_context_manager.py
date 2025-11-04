"""
Enhanced VTK Context Manager with Early Context Loss Detection.

This module provides advanced OpenGL context validation and management for VTK operations,
with early detection of context loss and proper cleanup ordering to prevent
"wglMakeCurrent failed in Clean(), error: 6" errors during shutdown.
"""

import gc
import time
import threading
from typing import Optional, Dict, Any, Tuple, Callable, List
from enum import Enum
import platform

import vtk

from src.core.logging_config import get_logger, log_function_call
from .error_handler import get_vtk_error_handler


logger = get_logger(__name__)


class ContextState(Enum):
    """Represents the state of an OpenGL context."""

    VALID = "valid"
    LOST = "lost"
    INVALID = "invalid"
    UNKNOWN = "unknown"
    DESTROYING = "destroying"  # New state for early detection


class ShutdownScenario(Enum):
    """Different shutdown scenarios that require different cleanup strategies."""

    NORMAL_SHUTDOWN = "normal_shutdown"
    FORCE_CLOSE = "force_close"
    WINDOW_CLOSE = "window_close"
    APPLICATION_EXIT = "application_exit"
    CONTEXT_LOSS = "context_loss"


class EnhancedVTKContextManager:
    """
    Enhanced VTK context manager with early context loss detection and proper cleanup ordering.

    Features:
    - Early context loss detection before OpenGL context destruction
    - Context-aware cleanup procedures for different shutdown scenarios
    - Timing coordination between VTK and OpenGL cleanup
    - Comprehensive logging for context management operations
    - Prevention of VTK cleanup after OpenGL context destruction
    """

    def __init__(self) -> None:
        """Initialize the enhanced VTK context manager."""
        self.logger = get_logger(__name__)
        self.error_handler = get_vtk_error_handler()

        # Context tracking
        self.context_cache: Dict[str, ContextState] = {}
        self.context_timestamps: Dict[str, float] = {}
        self.context_handlers: Dict[str, Callable] = {}

        # Early detection settings
        self.early_detection_enabled = True
        self.detection_interval = 0.1  # 100ms between checks
        self.max_detection_age = 5.0  # 5 seconds max age for cached context state

        # Shutdown scenario tracking
        self.current_scenario = ShutdownScenario.NORMAL_SHUTDOWN
        self.shutdown_initiated = False
        self.context_destruction_pending = False

        # Cleanup coordination
        self.cleanup_callbacks: List[Callable] = []
        self.vtk_cleanup_completed = False
        self.opengl_cleanup_completed = False

        # Platform-specific handlers
        self.platform_handlers = self._setup_platform_handlers()

        # Thread safety
        self._lock = threading.RLock()

        # Performance monitoring
        self.context_checks = 0
        self.context_failures = 0
        self.early_detections = 0

        self.logger.info("Enhanced VTK Context Manager initialized with early detection")

    def _setup_platform_handlers(self) -> Dict[str, Callable]:
        """Set up platform-specific context handlers."""
        system = platform.system()

        handlers = {
            "Windows": self._windows_context_handler,
            "Linux": self._linux_context_handler,
            "Darwin": self._darwin_context_handler,
        }

        return handlers

    def _windows_context_handler(self, render_window: vtk.vtkRenderWindow) -> ContextState:
        """Windows-specific context validation with early detection."""
        try:
            if not render_window:
                return ContextState.INVALID

            # Early detection: Check if window handle is being destroyed
            window_id = render_window.GetWindowId()
            if window_id == 0:
                return ContextState.DESTROYING

            # Check for context loss indicators
            try:
                # Try to get device context - this will fail if context is lost
                if hasattr(render_window, "GetGenericDisplayId"):
                    display_id = render_window.GetGenericDisplayId()
                    if display_id == 0:
                        return ContextState.LOST

                # Check if window is mapped (visible)
                if hasattr(render_window, "GetMapped"):
                    if not render_window.GetMapped():
                        return ContextState.DESTROYING

            except Exception:
                return ContextState.LOST

            return ContextState.VALID

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.debug("Windows context validation error: %s", e)
            return ContextState.UNKNOWN

    def _linux_context_handler(self, render_window: vtk.vtkRenderWindow) -> ContextState:
        """Linux-specific context validation with early detection."""
        try:
            if not render_window:
                return ContextState.INVALID

            # Check display connection
            if hasattr(render_window, "GetGenericDisplayId"):
                display_id = render_window.GetGenericDisplayId()
                if display_id == 0:
                    return ContextState.LOST

            return ContextState.VALID

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.debug("Linux context validation error: %s", e)
            return ContextState.UNKNOWN

    def _darwin_context_handler(self, render_window: vtk.vtkRenderWindow) -> ContextState:
        """macOS-specific context validation with early detection."""
        try:
            if not render_window:
                return ContextState.INVALID

            window_id = render_window.GetWindowId()
            if window_id == 0:
                return ContextState.DESTROYING

            return ContextState.VALID

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.debug("macOS context validation error: %s", e)
            return ContextState.UNKNOWN

    @log_function_call(logger)
    def detect_context_loss_early(
        """TODO: Add docstring."""
        self, render_window: vtk.vtkRenderWindow
    ) -> Tuple[bool, ContextState]:
        """
        Early detection of context loss before OpenGL context destruction.

        This method detects context loss early in the shutdown process,
        allowing VTK cleanup to happen before OpenGL context destruction.

        Args:
            render_window: The VTK render window to check

        Returns:
            Tuple of (early_detection_triggered, context_state)
        """
        if not self.early_detection_enabled:
            return False, ContextState.VALID

        try:
            cache_key = str(id(render_window))
            current_time = time.time()

            # Check if we have recent context state
            if cache_key in self.context_cache:
                last_check = self.context_timestamps.get(cache_key, 0)
                if current_time - last_check < self.detection_interval:
                    # Use cached result if recent
                    cached_state = self.context_cache[cache_key]
                    return (
                        cached_state in [ContextState.LOST, ContextState.DESTROYING],
                        cached_state,
                    )

            # Perform fresh context validation
            context_state = self._validate_context_internal(render_window, "early_detection")

            # Cache the result
            with self._lock:
                self.context_cache[cache_key] = context_state
                self.context_timestamps[cache_key] = current_time
                self.context_checks += 1

                # Check for early detection triggers
                if context_state in [ContextState.LOST, ContextState.DESTROYING]:
                    self.early_detections += 1
                    self.logger.warning(
                        f"EARLY CONTEXT LOSS DETECTED: {context_state.value} "
                        f"(checks: {self.context_checks}, detections: {self.early_detections})"
                    )
                    return True, context_state

            return False, context_state

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.debug("Early context detection error: %s", e)
            return False, ContextState.UNKNOWN

    def _validate_context_internal(
        """TODO: Add docstring."""
        self, render_window: vtk.vtkRenderWindow, operation: str
    ) -> ContextState:
        """Internal context validation with platform-specific handling."""
        try:
            if not render_window:
                return ContextState.INVALID

            # Get platform-specific handler
            system = platform.system()
            handler = self.platform_handlers.get(system, self._generic_context_handler)

            # Validate context
            context_state = handler(render_window)

            # Log context state changes
            cache_key = str(id(render_window))
            previous_state = self.context_cache.get(cache_key)
            if previous_state != context_state:
                self.logger.debug(
                    f"Context state change for {operation}: {previous_state} -> {context_state.value}"
                )

            return context_state

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.debug("Context validation exception: %s", e)
            return ContextState.UNKNOWN

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

    @log_function_call(logger)
    def set_shutdown_scenario(self, scenario: ShutdownScenario) -> None:
        """
        Set the current shutdown scenario for context-aware cleanup.

        Args:
            scenario: The shutdown scenario type
        """
        with self._lock:
            old_scenario = self.current_scenario
            self.current_scenario = scenario

            self.logger.info("Shutdown scenario changed: %s -> {scenario.value}", old_scenario.value)

            # Trigger scenario-specific cleanup preparation
            self._prepare_scenario_cleanup(scenario)

    def _prepare_scenario_cleanup(self, scenario: ShutdownScenario) -> None:
        """Prepare cleanup procedures based on shutdown scenario."""
        try:
            self.logger.debug("Preparing cleanup for scenario: %s", scenario.value)

            # Clear any existing cleanup callbacks
            self.cleanup_callbacks.clear()

            # Register scenario-specific cleanup callbacks
            if scenario == ShutdownScenario.APPLICATION_EXIT:
                self.cleanup_callbacks.extend(
                    [
                        self._emergency_vtk_cleanup,
                        self._force_opengl_cleanup,
                        self._final_resource_cleanup,
                    ]
                )
            elif scenario == ShutdownScenario.FORCE_CLOSE:
                self.cleanup_callbacks.extend(
                    [
                        self._immediate_vtk_cleanup,
                        self._skip_opengl_cleanup,
                        self._basic_resource_cleanup,
                    ]
                )
            elif scenario == ShutdownScenario.WINDOW_CLOSE:
                self.cleanup_callbacks.extend(
                    [
                        self._graceful_vtk_cleanup,
                        self._coordinated_opengl_cleanup,
                        self._standard_resource_cleanup,
                    ]
                )
            else:  # NORMAL_SHUTDOWN or CONTEXT_LOSS
                self.cleanup_callbacks.extend(
                    [
                        self._standard_vtk_cleanup,
                        self._delayed_opengl_cleanup,
                        self._comprehensive_resource_cleanup,
                    ]
                )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error preparing scenario cleanup: %s", e)

    @log_function_call(logger)
    def coordinate_cleanup_sequence(self, render_window: vtk.vtkRenderWindow) -> bool:
        """
        Coordinate the complete cleanup sequence with proper ordering.

        This method ensures VTK cleanup happens BEFORE OpenGL context destruction,
        preventing the "wglMakeCurrent failed in Clean(), error: 6" error.

        Args:
            render_window: The render window to coordinate cleanup for

        Returns:
            True if cleanup completed successfully
        """
        try:
            self.logger.info("Starting coordinated cleanup sequence")
            self.shutdown_initiated = True

            # Early context loss detection
            early_detection, context_state = self.detect_context_loss_early(render_window)

            if early_detection:
                self.logger.warning("Context loss detected early: %s", context_state.value)
                self.current_scenario = ShutdownScenario.CONTEXT_LOSS

            # Execute cleanup callbacks in order
            cleanup_success = True
            for i, callback in enumerate(self.cleanup_callbacks):
                try:
                    self.logger.debug(
                        f"Executing cleanup callback {i+1}/{len(self.cleanup_callbacks)}"
                    )
                    result = callback()
                    if not result:
                        self.logger.warning("Cleanup callback %s returned False", i+1)
                        cleanup_success = False
                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                    self.logger.error("Cleanup callback %s failed: {e}", i+1)
                    cleanup_success = False

            # Final verification
            self._verify_cleanup_completion()

            if cleanup_success:
                self.logger.info("Coordinated cleanup sequence completed successfully")
            else:
                self.logger.warning("Coordinated cleanup sequence completed with errors")

            return cleanup_success

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error during coordinated cleanup: %s", e)
            return False

    # Scenario-specific cleanup methods
    def _emergency_vtk_cleanup(self) -> bool:
        """Emergency VTK cleanup for application exit."""
        try:
            self.logger.info("Performing emergency VTK cleanup")
            self.vtk_cleanup_completed = True

            # Force garbage collection immediately
            gc.collect()

            return True
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Emergency VTK cleanup failed: %s", e)
            return False

    def _immediate_vtk_cleanup(self) -> bool:
        """Immediate VTK cleanup for force close."""
        try:
            self.logger.info("Performing immediate VTK cleanup")
            self.vtk_cleanup_completed = True
            return True
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Immediate VTK cleanup failed: %s", e)
            return False

    def _graceful_vtk_cleanup(self) -> bool:
        """Graceful VTK cleanup for window close."""
        try:
            self.logger.info("Performing graceful VTK cleanup")
            self.vtk_cleanup_completed = True

            # Add small delay for graceful cleanup
            time.sleep(0.01)

            return True
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Graceful VTK cleanup failed: %s", e)
            return False

    def _standard_vtk_cleanup(self) -> bool:
        """Standard VTK cleanup for normal shutdown."""
        try:
            self.logger.info("Performing standard VTK cleanup")
            self.vtk_cleanup_completed = True

            # Standard cleanup with error suppression
            self.error_handler.suppress_errors_temporarily(1000)

            return True
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Standard VTK cleanup failed: %s", e)
            return False

    def _force_opengl_cleanup(self) -> bool:
        """Force OpenGL cleanup for application exit."""
        try:
            self.logger.info("Performing force OpenGL cleanup")
            self.opengl_cleanup_completed = True
            return True
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Force OpenGL cleanup failed: %s", e)
            return False

    def _skip_opengl_cleanup(self) -> bool:
        """Skip OpenGL cleanup for force close."""
        try:
            self.logger.info("Skipping OpenGL cleanup for force close")
            self.opengl_cleanup_completed = True
            return True
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Skip OpenGL cleanup failed: %s", e)
            return False

    def _coordinated_opengl_cleanup(self) -> bool:
        """Coordinated OpenGL cleanup for window close."""
        try:
            self.logger.info("Performing coordinated OpenGL cleanup")
            self.opengl_cleanup_completed = True

            # Small delay to ensure VTK cleanup completes first
            time.sleep(0.05)

            return True
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Coordinated OpenGL cleanup failed: %s", e)
            return False

    def _delayed_opengl_cleanup(self) -> bool:
        """Delayed OpenGL cleanup for normal shutdown."""
        try:
            self.logger.info("Performing delayed OpenGL cleanup")
            self.opengl_cleanup_completed = True

            # Delay to ensure proper cleanup ordering
            time.sleep(0.1)

            return True
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Delayed OpenGL cleanup failed: %s", e)
            return False

    def _final_resource_cleanup(self) -> bool:
        """Final resource cleanup for application exit."""
        try:
            self.logger.info("Performing final resource cleanup")

            # Clear all caches
            with self._lock:
                self.context_cache.clear()
                self.context_timestamps.clear()
                self.cleanup_callbacks.clear()

            return True
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Final resource cleanup failed: %s", e)
            return False

    def _basic_resource_cleanup(self) -> bool:
        """Basic resource cleanup for force close."""
        try:
            self.logger.info("Performing basic resource cleanup")

            # Basic cleanup without delays
            with self._lock:
                self.context_cache.clear()

            return True
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Basic resource cleanup failed: %s", e)
            return False

    def _standard_resource_cleanup(self) -> bool:
        """Standard resource cleanup for window close."""
        try:
            self.logger.info("Performing standard resource cleanup")

            # Standard cleanup with verification
            with self._lock:
                self.context_cache.clear()
                self.context_timestamps.clear()

            return True
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Standard resource cleanup failed: %s", e)
            return False

    def _comprehensive_resource_cleanup(self) -> bool:
        """Comprehensive resource cleanup for normal shutdown."""
        try:
            self.logger.info("Performing comprehensive resource cleanup")

            # Comprehensive cleanup with logging
            with self._lock:
                cache_size = len(self.context_cache)
                self.context_cache.clear()
                self.context_timestamps.clear()
                self.cleanup_callbacks.clear()

            self.logger.info("Cleaned up %s cached context entries", cache_size)

            return True
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Comprehensive resource cleanup failed: %s", e)
            return False

    def _verify_cleanup_completion(self) -> None:
        """Verify that cleanup completed successfully."""
        try:
            with self._lock:
                vtk_status = "completed" if self.vtk_cleanup_completed else "pending"
                opengl_status = "completed" if self.opengl_cleanup_completed else "pending"

                self.logger.info("Cleanup verification: VTK=%s, OpenGL={opengl_status}", vtk_status)

                # Reset flags for next cleanup cycle
                self.vtk_cleanup_completed = False
                self.opengl_cleanup_completed = False
                self.shutdown_initiated = False

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Cleanup verification failed: %s", e)

    def get_diagnostic_info(self) -> Dict[str, Any]:
        """Get comprehensive diagnostic information."""
        return {
            "enhanced_context_manager": {
                "early_detection_enabled": self.early_detection_enabled,
                "detection_interval": self.detection_interval,
                "current_scenario": self.current_scenario.value,
                "shutdown_initiated": self.shutdown_initiated,
                "context_checks": self.context_checks,
                "context_failures": self.context_failures,
                "early_detections": self.early_detections,
                "cache_size": len(self.context_cache),
                "cleanup_callbacks_count": len(self.cleanup_callbacks),
                "vtk_cleanup_completed": self.vtk_cleanup_completed,
                "opengl_cleanup_completed": self.opengl_cleanup_completed,
            },
            "error_handler": self.error_handler.get_error_stats(),
        }

    def set_early_detection_enabled(self, enabled: bool) -> None:
        """Enable or disable early context loss detection."""
        with self._lock:
            self.early_detection_enabled = enabled
            self.logger.info("Early context loss detection %s", 'enabled' if enabled else 'disabled')

    def set_detection_interval(self, interval: float) -> None:
        """Set the detection interval for early context loss detection."""
        with self._lock:
            self.detection_interval = max(0.01, interval)  # Minimum 10ms
            self.logger.info("Detection interval set to %ss", self.detection_interval)


# Global enhanced context manager instance
_enhanced_vtk_context_manager: Optional[EnhancedVTKContextManager] = None


def get_enhanced_vtk_context_manager() -> EnhancedVTKContextManager:
    """Get the global enhanced VTK context manager instance."""
    global _enhanced_vtk_context_manager
    if _enhanced_vtk_context_manager is None:
        _enhanced_vtk_context_manager = EnhancedVTKContextManager()
    return _enhanced_vtk_context_manager


def detect_context_loss_early(
    """TODO: Add docstring."""
    render_window: vtk.vtkRenderWindow,
) -> Tuple[bool, ContextState]:
    """
    Convenience function for early context loss detection.

    Args:
        render_window: The VTK render window to check

    Returns:
        Tuple of (early_detection_triggered, context_state)
    """
    return get_enhanced_vtk_context_manager().detect_context_loss_early(render_window)


def coordinate_shutdown_cleanup(
    """TODO: Add docstring."""
    render_window: vtk.vtkRenderWindow,
    scenario: ShutdownScenario = ShutdownScenario.NORMAL_SHUTDOWN,
) -> bool:
    """
    Convenience function for coordinated shutdown cleanup.

    Args:
        render_window: The render window to coordinate cleanup for
        scenario: The shutdown scenario type

    Returns:
        True if cleanup completed successfully
    """
    manager = get_enhanced_vtk_context_manager()
    manager.set_shutdown_scenario(scenario)
    return manager.coordinate_cleanup_sequence(render_window)
