"""
Unified Cleanup Coordinator - Central orchestration for all cleanup operations.

This module provides a single, well-architected cleanup system that consolidates
the functionality of 4 overlapping cleanup systems into a unified architecture
with clear boundaries and responsibilities.
"""

import time
import threading
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from dataclasses import dataclass

from src.core.logging_config import get_logger, log_function_call


class CleanupPhase(Enum):
    """Phases of the unified cleanup process."""

    PRE_CLEANUP = "pre_cleanup"
    SERVICE_SHUTDOWN = "service_shutdown"
    WIDGET_CLEANUP = "widget_cleanup"
    VTK_CLEANUP = "vtk_cleanup"
    RESOURCE_CLEANUP = "resource_cleanup"
    VERIFICATION = "verification"


class CleanupContext(Enum):
    """Context state during cleanup operations."""

    VALID = "valid"
    LOST = "lost"
    UNKNOWN = "unknown"


class CleanupError(Exception):
    """Exception raised during cleanup operations."""

    def __init__(self, message: str, phase: CleanupPhase, context: CleanupContext):
        super().__init__(message)
        self.phase = phase
        self.context = context


@dataclass
class PhaseError:
    """Detailed error information for a cleanup phase."""

    phase: str
    handler: str
    error_message: str
    error_type: str
    timestamp: float = 0.0
    is_critical: bool = False
    recovery_attempted: bool = False
    recovery_successful: bool = False

    def __str__(self) -> str:
        """Return a formatted error string."""
        severity = "CRITICAL" if self.is_critical else "ERROR"
        recovery_info = ""
        if self.recovery_attempted:
            recovery_info = (
                f" [Recovery: {'successful' if self.recovery_successful else 'failed'}]"
            )
        return (
            f"{severity} in {self.phase} ({self.handler}): {self.error_message} "
            f"({self.error_type}){recovery_info}"
        )


@dataclass
class CleanupStats:
    """Statistics for cleanup operations."""

    total_phases: int = 0
    completed_phases: int = 0
    failed_phases: int = 0
    skipped_phases: int = 0
    total_duration: float = 0.0
    context_lost: bool = False
    errors: List[str] = None
    phase_errors: Dict[str, List[PhaseError]] = None
    handler_stats: Dict[str, Dict[str, Any]] = None
    verification_report: Optional[Any] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.phase_errors is None:
            self.phase_errors = {}
        if self.handler_stats is None:
            self.handler_stats = {}

    def add_phase_error(self, phase_error: PhaseError) -> None:
        """Add a detailed phase error."""
        phase_name = phase_error.phase
        if phase_name not in self.phase_errors:
            self.phase_errors[phase_name] = []
        self.phase_errors[phase_name].append(phase_error)
        # Also add to simple errors list for backward compatibility
        self.errors.append(str(phase_error))

    def get_error_summary(self) -> str:
        """Get a summary of all errors."""
        if not self.errors:
            return "No errors"

        summary_lines = [f"Cleanup completed with {len(self.errors)} error(s):"]
        for error in self.errors:
            summary_lines.append(f"  - {error}")
        return "\n".join(summary_lines)

    def get_detailed_report(self) -> str:
        """Get a detailed error report."""
        lines = [
            "=== Cleanup Statistics ===",
            f"Total phases: {self.total_phases}",
            f"Completed: {self.completed_phases}",
            f"Failed: {self.failed_phases}",
            f"Skipped: {self.skipped_phases}",
            f"Duration: {self.total_duration:.3f}s",
            f"Context lost: {self.context_lost}",
            "",
        ]

        if self.phase_errors:
            lines.append("=== Phase Errors ===")
            for phase_name, errors in self.phase_errors.items():
                lines.append(f"\n{phase_name}:")
                for error in errors:
                    lines.append(f"  {error}")

        if self.handler_stats:
            lines.append("\n=== Handler Statistics ===")
            for handler_name, stats in self.handler_stats.items():
                lines.append(f"\n{handler_name}:")
                for key, value in stats.items():
                    lines.append(f"  {key}: {value}")

        return "\n".join(lines)


class CleanupHandler:
    """Base class for specialized cleanup handlers."""

    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"{__name__}.{name}")
        self.enabled = True
        self.dependencies: Set[str] = set()

    def can_handle(self, phase: CleanupPhase) -> bool:
        """Check if this handler can handle the given phase."""
        raise NotImplementedError

    def execute(self, phase: CleanupPhase, context: CleanupContext) -> bool:
        """Execute cleanup for the given phase."""
        raise NotImplementedError

    def get_dependencies(self) -> Set[str]:
        """Get handler dependencies."""
        return self.dependencies.copy()

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable this handler."""
        self.enabled = enabled
        self.logger.debug(f"Handler {self.name} {'enabled' if enabled else 'disabled'}")


class UnifiedCleanupCoordinator:
    """
    Central coordinator for all cleanup operations.

    This class orchestrates cleanup across all application components using
    specialized handlers with clear responsibility boundaries.
    """

    def __init__(self):
        """Initialize the unified cleanup coordinator."""
        self.logger = get_logger(__name__)
        self._handlers: Dict[str, CleanupHandler] = {}
        self._cleanup_in_progress = False
        self._context_state = CleanupContext.UNKNOWN
        self._stats = CleanupStats()
        self._lock = threading.RLock()

        # Register default handlers
        self._register_default_handlers()

        self.logger.info("Unified Cleanup Coordinator initialized")

    def _register_default_handlers(self) -> None:
        """Register the default cleanup handlers."""
        try:
            # Import handlers to avoid circular imports
            from .vtk_cleanup_handler import VTKCleanupHandler
            from .widget_cleanup_handler import WidgetCleanupHandler
            from .service_cleanup_handler import ServiceCleanupHandler
            from .resource_cleanup_handler import ResourceCleanupHandler

            # Register handlers
            self.register_handler(VTKCleanupHandler())
            self.register_handler(WidgetCleanupHandler())
            self.register_handler(ServiceCleanupHandler())
            self.register_handler(ResourceCleanupHandler())

            self.logger.info("Default cleanup handlers registered")

        except ImportError as e:
            self.logger.warning(f"Could not import default handlers: {e}")

    def register_handler(self, handler: CleanupHandler) -> None:
        """
        Register a cleanup handler.

        Args:
            handler: The cleanup handler to register
        """
        with self._lock:
            self._handlers[handler.name] = handler
            self.logger.debug(f"Registered cleanup handler: {handler.name}")

    def unregister_handler(self, handler_name: str) -> bool:
        """
        Unregister a cleanup handler.

        Args:
            handler_name: Name of the handler to unregister

        Returns:
            True if handler was unregistered, False if not found
        """
        with self._lock:
            if handler_name in self._handlers:
                del self._handlers[handler_name]
                self.logger.debug(f"Unregistered cleanup handler: {handler_name}")
                return True
            return False

    def coordinate_cleanup(
        self,
        render_window=None,
        renderer=None,
        interactor=None,
        main_window=None,
        application=None,
    ) -> CleanupStats:
        """
        Coordinate the complete cleanup process.

        Args:
            render_window: VTK render window (optional)
            renderer: VTK renderer (optional)
            interactor: VTK interactor (optional)
            main_window: Main application window (optional)
            application: Application instance (optional)

        Returns:
            CleanupStats with cleanup results
        """
        if self._cleanup_in_progress:
            self.logger.warning("Cleanup already in progress, skipping")
            return self._stats

        start_time = time.time()

        try:
            self._cleanup_in_progress = True
            self._stats = CleanupStats()
            self.logger.info("=" * 60)
            self.logger.info("Starting unified cleanup process")
            self.logger.info(
                f"Resources: render_window={render_window is not None}, "
                f"renderer={renderer is not None}, "
                f"interactor={interactor is not None}, "
                f"main_window={main_window is not None}"
            )
            self.logger.info("=" * 60)

            # Initialize context and validate
            self._initialize_cleanup_context(render_window, renderer, interactor)

            # Execute cleanup phases in dependency order
            success = self._execute_cleanup_phases(
                render_window, renderer, interactor, main_window, application
            )

            # Update statistics
            self._stats.total_duration = time.time() - start_time

            # Log detailed report
            self.logger.info("=" * 60)
            self.logger.info("Cleanup Summary:")
            self.logger.info(f"  Total phases: {self._stats.total_phases}")
            self.logger.info(f"  Completed: {self._stats.completed_phases}")
            self.logger.info(f"  Failed: {self._stats.failed_phases}")
            self.logger.info(f"  Skipped: {self._stats.skipped_phases}")
            self.logger.info(f"  Duration: {self._stats.total_duration:.3f}s")

            if self._stats.handler_stats:
                self.logger.info("\nHandler Statistics:")
                for handler_name, stats in self._stats.handler_stats.items():
                    self.logger.info(
                        f"  {handler_name}: "
                        f"executed={stats['phases_executed']}, "
                        f"succeeded={stats['phases_succeeded']}, "
                        f"failed={stats['phases_failed']}, "
                        f"duration={stats['total_duration']:.3f}s"
                    )

            if success:
                self.logger.info("Status: CLEANUP SUCCESSFUL ✓")
            else:
                self.logger.warning("Status: CLEANUP COMPLETED WITH ERRORS")
                if self._stats.phase_errors:
                    self.logger.warning("\nPhase Errors:")
                    for phase_name, errors in self._stats.phase_errors.items():
                        for error in errors:
                            self.logger.warning(f"  {error}")

            self.logger.info("=" * 60)

            # Run verification
            self.logger.info("Running cleanup verification...")
            verification_report = self._run_verification()
            self._stats.verification_report = verification_report

            # Log verification results
            self.logger.info(verification_report.get_summary())

            return self._stats

        except Exception as e:
            self.logger.error(f"Error during unified cleanup: {e}", exc_info=True)
            self._stats.errors.append(str(e))
            self._stats.total_duration = time.time() - start_time
            return self._stats

        finally:
            self._cleanup_in_progress = False

    def _initialize_cleanup_context(self, render_window, renderer, interactor) -> None:
        """Initialize and validate cleanup context."""
        try:
            # Check if we have VTK resources that need context validation
            if render_window or renderer or interactor:
                self._validate_vtk_context(render_window)
            else:
                self._context_state = CleanupContext.VALID

            self.logger.debug(
                f"Cleanup context initialized: {self._context_state.value}"
            )

        except Exception as e:
            self.logger.warning(f"Context validation failed: {e}")
            self._context_state = CleanupContext.UNKNOWN

    def _validate_vtk_context(self, render_window) -> None:
        """Validate VTK OpenGL context."""
        try:
            if render_window and hasattr(render_window, "GetGenericWindowId"):
                # Try to validate context using VTK context manager
                from src.gui.vtk.context_manager import get_vtk_context_manager

                context_manager = get_vtk_context_manager()

                is_valid, _ = context_manager.validate_context(render_window, "cleanup")

                if is_valid:
                    self._context_state = CleanupContext.VALID
                else:
                    self._context_state = CleanupContext.LOST
                    self._stats.context_lost = True
                    self.logger.info(
                        "OpenGL context lost during cleanup (normal during shutdown)"
                    )

            else:
                self._context_state = CleanupContext.VALID

        except Exception as e:
            self.logger.debug(f"VTK context validation error: {e}")
            self._context_state = CleanupContext.UNKNOWN

    def _execute_cleanup_phases(
        self, render_window, renderer, interactor, main_window, application
    ) -> bool:
        """
        Execute cleanup phases in dependency order.

        Returns:
            True if all phases completed successfully
        """
        phases = [
            CleanupPhase.PRE_CLEANUP,
            CleanupPhase.SERVICE_SHUTDOWN,
            CleanupPhase.WIDGET_CLEANUP,
            CleanupPhase.VTK_CLEANUP,
            CleanupPhase.RESOURCE_CLEANUP,
            CleanupPhase.VERIFICATION,
        ]

        self._stats.total_phases = len(phases)
        overall_success = True
        phase_start_time = 0.0

        for phase in phases:
            phase_start_time = time.time()
            try:
                self.logger.info(f"Starting cleanup phase: {phase.value}")
                phase_success = self._execute_phase(
                    phase, render_window, renderer, interactor, main_window, application
                )

                phase_duration = time.time() - phase_start_time

                if phase_success:
                    self._stats.completed_phases += 1
                    self.logger.info(
                        f"Phase {phase.value} completed successfully ({phase_duration:.3f}s)"
                    )
                else:
                    self._stats.skipped_phases += 1
                    self.logger.info(
                        f"Phase {phase.value} skipped (context lost or other reason) ({phase_duration:.3f}s)"
                    )

            except Exception as e:
                phase_duration = time.time() - phase_start_time
                self._stats.failed_phases += 1

                # Create detailed error record
                phase_error = PhaseError(
                    phase=phase.value,
                    handler="UnifiedCoordinator",
                    error_message=str(e),
                    error_type=type(e).__name__,
                    timestamp=time.time(),
                    is_critical=(phase == CleanupPhase.PRE_CLEANUP),
                )
                self._stats.add_phase_error(phase_error)

                overall_success = False
                self.logger.error(
                    f"Phase {phase.value} failed after {phase_duration:.3f}s: {e}",
                    exc_info=True,
                )

                # Continue with other phases unless it's a critical error
                if phase == CleanupPhase.PRE_CLEANUP:
                    self.logger.error("Pre-cleanup failed, aborting remaining phases")
                    break

        return overall_success

    def _execute_phase(
        self,
        phase: CleanupPhase,
        render_window,
        renderer,
        interactor,
        main_window,
        application,
    ) -> bool:
        """
        Execute a specific cleanup phase.

        Returns:
            True if phase completed successfully
        """
        # Find handlers that can handle this phase
        capable_handlers = [
            handler
            for handler in self._handlers.values()
            if handler.enabled and handler.can_handle(phase)
        ]

        if not capable_handlers:
            self.logger.debug(f"No handlers available for phase {phase.value}")
            return True

        # Sort handlers by dependencies
        sorted_handlers = self._sort_handlers_by_dependencies(capable_handlers)

        phase_success = True
        handler_count = len(sorted_handlers)

        for idx, handler in enumerate(sorted_handlers, 1):
            handler_start_time = time.time()
            try:
                self.logger.info(
                    f"Handler {idx}/{handler_count}: {handler.name} executing phase {phase.value}"
                )

                # Set context-specific data for handlers
                self._get_phase_context_data(
                    phase, render_window, renderer, interactor, main_window, application
                )

                handler_success = handler.execute(phase, self._context_state)
                handler_duration = time.time() - handler_start_time

                # Track handler statistics
                if handler.name not in self._stats.handler_stats:
                    self._stats.handler_stats[handler.name] = {
                        "phases_executed": 0,
                        "phases_succeeded": 0,
                        "phases_failed": 0,
                        "total_duration": 0.0,
                    }

                self._stats.handler_stats[handler.name]["phases_executed"] += 1
                self._stats.handler_stats[handler.name][
                    "total_duration"
                ] += handler_duration

                if handler_success:
                    self._stats.handler_stats[handler.name]["phases_succeeded"] += 1
                    self.logger.info(
                        f"Handler {handler.name} completed phase {phase.value} ({handler_duration:.3f}s)"
                    )
                else:
                    self._stats.handler_stats[handler.name]["phases_failed"] += 1
                    self.logger.warning(
                        f"Handler {handler.name} failed phase {phase.value} ({handler_duration:.3f}s)"
                    )
                    phase_success = False

            except Exception as e:
                handler_duration = time.time() - handler_start_time

                # Create detailed error record
                phase_error = PhaseError(
                    phase=phase.value,
                    handler=handler.name,
                    error_message=str(e),
                    error_type=type(e).__name__,
                    timestamp=time.time(),
                    is_critical=False,
                )
                self._stats.add_phase_error(phase_error)

                # Track handler statistics
                if handler.name not in self._stats.handler_stats:
                    self._stats.handler_stats[handler.name] = {
                        "phases_executed": 0,
                        "phases_succeeded": 0,
                        "phases_failed": 0,
                        "total_duration": 0.0,
                    }

                self._stats.handler_stats[handler.name]["phases_executed"] += 1
                self._stats.handler_stats[handler.name]["phases_failed"] += 1
                self._stats.handler_stats[handler.name][
                    "total_duration"
                ] += handler_duration

                self.logger.error(
                    f"Handler {handler.name} error in phase {phase.value} ({handler_duration:.3f}s): {e}",
                    exc_info=True,
                )
                phase_success = False

        return phase_success

    def _sort_handlers_by_dependencies(
        self, handlers: List[CleanupHandler]
    ) -> List[CleanupHandler]:
        """Sort handlers by their dependencies."""
        # Simple dependency sorting - handlers with no dependencies first
        sorted_handlers = []
        remaining_handlers = handlers.copy()

        while remaining_handlers:
            # Find handlers whose dependencies are all satisfied
            ready_handlers = [
                h
                for h in remaining_handlers
                if all(
                    dep in [h.name for h in sorted_handlers]
                    for dep in h.get_dependencies()
                )
            ]

            if not ready_handlers:
                # No handlers ready, add remaining handlers without sorting
                ready_handlers = remaining_handlers

            # Add ready handlers to sorted list
            for handler in ready_handlers:
                sorted_handlers.append(handler)
                remaining_handlers.remove(handler)

        return sorted_handlers

    def _get_phase_context_data(
        self,
        phase: CleanupPhase,
        render_window,
        renderer,
        interactor,
        main_window,
        application,
    ) -> Dict[str, Any]:
        """Get context-specific data for a cleanup phase."""
        context_data = {}

        if phase == CleanupPhase.VTK_CLEANUP:
            context_data.update(
                {
                    "render_window": render_window,
                    "renderer": renderer,
                    "interactor": interactor,
                }
            )
        elif phase == CleanupPhase.WIDGET_CLEANUP:
            context_data.update({"main_window": main_window})
        elif phase == CleanupPhase.SERVICE_SHUTDOWN:
            context_data.update({"application": application})

        return context_data

    def is_cleanup_in_progress(self) -> bool:
        """Check if cleanup is currently in progress."""
        return self._cleanup_in_progress

    def get_context_state(self) -> CleanupContext:
        """Get the current cleanup context state."""
        return self._context_state

    def _run_verification(self) -> Any:
        """
        Run cleanup verification and resource leak detection.

        Returns:
            CleanupVerificationReport with verification results
        """
        try:
            from .cleanup_verification import get_cleanup_verifier

            verifier = get_cleanup_verifier()
            report = verifier.verify_cleanup(self._stats)

            return report

        except Exception as e:
            self.logger.error(f"Verification failed: {e}", exc_info=True)
            return None

    def get_stats(self) -> CleanupStats:
        """Get cleanup statistics."""
        return self._stats

    def enable_handler(self, handler_name: str) -> bool:
        """Enable a specific handler."""
        if handler_name in self._handlers:
            self._handlers[handler_name].set_enabled(True)
            return True
        return False

    def disable_handler(self, handler_name: str) -> bool:
        """Disable a specific handler."""
        if handler_name in self._handlers:
            self._handlers[handler_name].set_enabled(False)
            return True
        return False

    def get_registered_handlers(self) -> List[str]:
        """Get list of registered handler names."""
        return list(self._handlers.keys())


# Global coordinator instance
_unified_cleanup_coordinator: Optional[UnifiedCleanupCoordinator] = None


def get_unified_cleanup_coordinator() -> UnifiedCleanupCoordinator:
    """Get the global unified cleanup coordinator instance."""
    global _unified_cleanup_coordinator
    if _unified_cleanup_coordinator is None:
        _unified_cleanup_coordinator = UnifiedCleanupCoordinator()
    return _unified_cleanup_coordinator


def coordinate_unified_cleanup(
    render_window=None,
    renderer=None,
    interactor=None,
    main_window=None,
    application=None,
) -> CleanupStats:
    """
    Convenience function to coordinate unified cleanup.

    Args:
        render_window: VTK render window (optional)
        renderer: VTK renderer (optional)
        interactor: VTK interactor (optional)
        main_window: Main application window (optional)
        application: Application instance (optional)

    Returns:
        CleanupStats with cleanup results
    """
    return get_unified_cleanup_coordinator().coordinate_cleanup(
        render_window, renderer, interactor, main_window, application
    )
