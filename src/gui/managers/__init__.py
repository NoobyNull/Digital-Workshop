"""
GUI Managers Package.

Contains extracted manager classes for MainWindow components.
"""

from .dock_widget_manager import DockWidgetManager
from .central_widget_manager import CentralWidgetManager
from .window_state_manager import WindowStateManager
from .lighting_manager import LightingManager
from .model_operation_manager import ModelOperationManager
from .metadata_manager import MetadataManager
from .project_manager import ProjectManager
from .viewer_manager import ViewerManager
from .thumbnail_manager import ThumbnailManager

__all__ = [
    "DockWidgetManager",
    "CentralWidgetManager",
    "WindowStateManager",
    "LightingManager",
    "ModelOperationManager",
    "MetadataManager",
    "ProjectManager",
    "ViewerManager",
    "ThumbnailManager",
]
