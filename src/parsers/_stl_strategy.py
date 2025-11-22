"""
STL parser strategy selector.

Prefers the refactored STL parser and falls back to the legacy facade if needed.
This keeps a single import point for STL while we finish migrating call sites.
"""

from __future__ import annotations

from typing import Type

from src.core.interfaces.parser_interfaces import IParser

# Refactored implementation (alias defined inside the module)
from src.parsers.refactored_stl_parser import RefactoredSTLParser
from src.parsers.stl_parser_original import STLParser as LegacySTLParser


def get_stl_parser_class() -> Type[IParser]:
    """Return the preferred (refactored) STL parser class."""
    return RefactoredSTLParser


def get_legacy_stl_parser_class() -> Type[IParser]:
    """Return the legacy STL parser class (fallback/compatibility)."""
    return LegacySTLParser
