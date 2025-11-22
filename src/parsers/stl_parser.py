"""
Compatibility shim for STL imports.

Many modules import from src.parsers.stl_parser; this module re-exports
the current STL types and parser to avoid breakage when refactoring.
"""

from .stl_components.stl_models import (
    STLModel,
    STLFormat,
    STLParseError,
    STLProgressCallback,
)
from .refactored_stl_parser import RefactoredSTLParser, STLParser

__all__ = [
    "STLModel",
    "STLFormat",
    "STLParseError",
    "STLProgressCallback",
    "STLParser",
    "RefactoredSTLParser",
]
