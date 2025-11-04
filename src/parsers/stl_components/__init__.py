"""
STL Parser Components - Modular STL file parsing.

This package provides a comprehensive STL file parser with support for both
binary and ASCII formats, hardware acceleration, and progress reporting.

Public API:
- STLParser: Main parser class
- STLFormat: Format type enum
- STLModel: Model data structure
- STLParseError: Custom exception
"""

from .stl_models import STLFormat, STLModel, STLParseError, STLProgressCallback
from .stl_parser_main import STLParser

__all__ = [
    "STLParser",
    "STLFormat",
    "STLModel",
    "STLParseError",
    "STLProgressCallback",
]
