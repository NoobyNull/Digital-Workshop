"""
VTK-based 3D viewer widget for Digital Workshop.

This module provides a compatibility layer for the refactored viewer widget.
The actual implementation is in src.gui.viewer_3d.viewer_widget_facade.

This module maintains backward compatibility with existing code.
"""

# Import from refactored modules
from src.gui.viewer_3d.viewer_widget_facade import Viewer3DWidget
from src.gui.viewer_3d.model_renderer import RenderMode

__all__ = [
    'Viewer3DWidget',
    'RenderMode',
]
