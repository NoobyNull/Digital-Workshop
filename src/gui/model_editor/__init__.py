"""
Model Editor Module - VTK-based model editing and transformation.

Provides functionality for:
- Model rotation (90-degree increments)
- Z-up orientation detection and correction
- Hollow model detection and solid plane generation
- Model verification (manual and automatic)
- Model saving without other modifications
"""

from .model_editor_core import ModelEditor, RotationAxis
from .model_geometry_analyzer import ModelGeometryAnalyzer

__all__ = [
    "ModelEditor",
    "RotationAxis",
    "ModelGeometryAnalyzer",
]
