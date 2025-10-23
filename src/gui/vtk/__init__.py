"""
VTK Error Handling Package.

This package provides comprehensive VTK error handling and context management
to gracefully handle OpenGL context loss and prevent application crashes.

Main Components:
- VTKErrorHandler: Centralized error processing and logging
- VTKContextManager: OpenGL context validation and management
- VTKCleanupCoordinator: Proper cleanup sequence and error handling
- VTKResourceTracker: Track VTK resources for proper cleanup
- VTKFallbackRenderer: Fallback rendering when context is lost
- VTKDiagnosticTools: Tools for diagnosing VTK issues

Usage:
    from src.gui.vtk import (
        get_vtk_error_handler,
        get_vtk_context_manager,
        coordinate_vtk_cleanup,
        register_vtk_resource,
        generate_vtk_diagnostic_report
    )

    # Handle VTK errors gracefully
    error_handler = get_vtk_error_handler()
    success = error_handler.handle_error(exception, "context")

    # Validate context before operations
    context_manager = get_vtk_context_manager()
    is_valid, state = context_manager.validate_context(render_window, "render")

    # Coordinate proper cleanup
    cleanup_success = coordinate_vtk_cleanup(render_window, renderer, interactor)

    # Generate diagnostic report
    report = generate_vtk_diagnostic_report("vtk_diagnostics.txt")
"""

from .error_handler import (
    VTKErrorHandler,
    VTKErrorCode,
    VTKErrorSeverity,
    get_vtk_error_handler,
    handle_vtk_error,
    suppress_vtk_errors_temporarily
)

from .context_manager import (
    VTKContextManager,
    ContextState,
    get_vtk_context_manager,
    validate_vtk_context,
    is_context_safe_for_cleanup
)

from .cleanup_coordinator import (
    VTKCleanupCoordinator,
    CleanupPhase,
    CleanupPriority,
    get_vtk_cleanup_coordinator,
    coordinate_vtk_cleanup
)

from .resource_tracker import (
    VTKResourceTracker,
    ResourceType,
    ResourceState,
    get_vtk_resource_tracker,
    register_vtk_resource,
    cleanup_vtk_resource,
    cleanup_all_vtk_resources
)

from .fallback_renderer import (
    VTKFallbackRenderer,
    FallbackMode,
    get_vtk_fallback_renderer,
    activate_vtk_fallback,
    render_with_vtk_fallback
)

from .diagnostic_tools import (
    VTKDiagnosticTools,
    get_vtk_diagnostic_tools,
    generate_vtk_diagnostic_report,
    run_vtk_health_check
)

__version__ = "1.0.0"
__all__ = [
    # Error Handler
    "VTKErrorHandler",
    "VTKErrorCode",
    "VTKErrorSeverity",
    "get_vtk_error_handler",
    "handle_vtk_error",
    "suppress_vtk_errors_temporarily",

    # Context Manager
    "VTKContextManager",
    "ContextState",
    "get_vtk_context_manager",
    "validate_vtk_context",
    "is_context_safe_for_cleanup",

    # Cleanup Coordinator
    "VTKCleanupCoordinator",
    "CleanupPhase",
    "CleanupPriority",
    "get_vtk_cleanup_coordinator",
    "coordinate_vtk_cleanup",

    # Resource Tracker
    "VTKResourceTracker",
    "ResourceType",
    "ResourceState",
    "get_vtk_resource_tracker",
    "register_vtk_resource",
    "cleanup_vtk_resource",
    "cleanup_all_vtk_resources",

    # Fallback Renderer
    "VTKFallbackRenderer",
    "FallbackMode",
    "get_vtk_fallback_renderer",
    "activate_vtk_fallback",
    "render_with_vtk_fallback",

    # Diagnostic Tools
    "VTKDiagnosticTools",
    "get_vtk_diagnostic_tools",
    "generate_vtk_diagnostic_report",
    "run_vtk_health_check",
]