"""
Rendering mode enumeration for 3D viewer.

Defines available rendering modes for 3D model visualization.
"""

from enum import Enum


class RenderMode(Enum):
    """Rendering modes for the 3D viewer."""
    SOLID = "solid"
    WIREFRAME = "wireframe"
    POINTS = "points"

