"""
PyQt3D viewer widget for Digital Workshop (Facade).

This module provides backward-compatible access to the refactored 3D viewer.
All functionality has been moved to src/gui/viewer_components/ package.

Run standalone for testing:
    python -m src.gui.viewer_widget
"""

from src.gui.viewer_components import (
    Viewer3DWidget,
    ProgressiveLoadWorker,
    RenderMode,
)

__all__ = [
    "Viewer3DWidget",
    "ProgressiveLoadWorker",
    "RenderMode",
]
