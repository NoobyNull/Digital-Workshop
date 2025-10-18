"""
3D viewer module for VTK-based visualization.

Provides modular components for 3D model viewing with VTK.
"""

from .vtk_scene_manager import VTKSceneManager
from .model_renderer import ModelRenderer, RenderMode
from .camera_controller import CameraController
from .performance_tracker import PerformanceTracker
from .viewer_ui_manager import ViewerUIManager

__all__ = [
    'VTKSceneManager',
    'ModelRenderer',
    'RenderMode',
    'CameraController',
    'PerformanceTracker',
    'ViewerUIManager',
]

