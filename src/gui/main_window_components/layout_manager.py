"""
Compatibility wrapper for layout management.

Delegates to ``src.gui.window.layout_persistence.LayoutPersistenceManager`` to avoid
duplicated persistence logic while keeping the historical class name.
"""

from src.gui.window.layout_persistence import LayoutPersistenceManager

# Preserve legacy API name.
LayoutManager = LayoutPersistenceManager

__all__ = ["LayoutManager", "LayoutPersistenceManager"]
