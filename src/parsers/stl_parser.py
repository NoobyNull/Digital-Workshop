"""
STL file parser for 3D-MM application (Facade).

This module provides backward-compatible access to the refactored STL parser.
Core parsing logic remains in stl_parser_original.py for complex interdependencies.
Modular components are available in src/parsers/stl_components/.

This module provides parsing functionality for both binary and ASCII STL file formats.
It includes memory-efficient processing, progress reporting, and comprehensive error handling.
"""

# Re-export all public API from the original implementation
from src.parsers.stl_parser_original import (
    STLParser,
    STLFormat,
    STLModel,
    STLParseError,
    STLProgressCallback,
)

__all__ = [
    "STLParser",
    "STLFormat",
    "STLModel",
    "STLParseError",
    "STLProgressCallback",
]
