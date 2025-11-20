"""
Compatibility wrapper for VTK context management.

Provides the legacy helper functions expected throughout the codebase while
delegating to the enhanced context manager implementation.
"""

from typing import Optional

from src.gui.vtk.enhanced_context_manager import (
    EnhancedVTKContextManager as VTKContextManager,
    ContextState,
    ShutdownScenario,
)

_CONTEXT_SINGLETON: Optional[VTKContextManager] = None


def get_vtk_context_manager() -> VTKContextManager:
    """Return the process-wide VTK context manager singleton."""
    global _CONTEXT_SINGLETON
    if _CONTEXT_SINGLETON is None:
        _CONTEXT_SINGLETON = VTKContextManager()
    return _CONTEXT_SINGLETON


def validate_vtk_context(render_window, operation: str = "render"):
    """
    Legacy helper returning (error, state) tuple.

    Falls back to the enhanced manager's internal validation; if the API changes,
    we conservatively return UNKNOWN state.
    """
    manager = get_vtk_context_manager()
    try:
        state = manager._validate_context_internal(render_window, operation)  # type: ignore[attr-defined]
    except Exception:
        state = ContextState.UNKNOWN
    return state not in (ContextState.VALID,), state


def is_context_safe_for_cleanup(render_window) -> bool:
    """
    Legacy helper to gate cleanup routines. Treat LOST/DESTROYING/INVALID as unsafe.
    """
    manager = get_vtk_context_manager()
    try:
        _, state = manager.detect_context_loss_early(render_window)
    except Exception:
        state = ContextState.UNKNOWN
    return state in (ContextState.VALID, ContextState.UNKNOWN)


__all__ = [
    "VTKContextManager",
    "ContextState",
    "ShutdownScenario",
    "get_vtk_context_manager",
    "validate_vtk_context",
    "is_context_safe_for_cleanup",
]
