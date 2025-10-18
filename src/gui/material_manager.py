"""
Material manager for procedural wood textures and VTK actor application (Facade).

This module provides backward-compatible access to the refactored material manager.
All functionality has been moved to src/gui/material_components/ package.

Run standalone for testing:
    python -m src.gui.material_manager
"""

from src.gui.material_components import MaterialManager

__all__ = [
    "MaterialManager",
]
