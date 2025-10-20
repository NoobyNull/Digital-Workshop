"""
Help system module for searchable documentation.

Provides keyword search across all project documentation.
"""

from src.gui.help_system.documentation_indexer import (
    DocumentationIndexer,
    HelpTopic,
)
from src.gui.help_system.help_dialog import HelpDialog

__all__ = [
    "DocumentationIndexer",
    "HelpTopic",
    "HelpDialog",
]

