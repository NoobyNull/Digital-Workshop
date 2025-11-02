"""
Viewer Components - Modular 3D viewer system.

This package provides a 3D visualization widget using VTK with interactive
camera controls, configurable lighting, and multiple rendering modes.

Public API:
- Viewer3DWidget: Main 3D viewer widget
- ProgressiveLoadWorker: Background model loading thread
- RenderMode: Rendering mode enum
"""

from .render_mode import RenderMode
from .progressive_load_worker import ProgressiveLoadWorker
from .viewer_3d_widget_main import Viewer3DWidget

__all__ = [
    "Viewer3DWidget",
    "ProgressiveLoadWorker",
    "RenderMode",
]

