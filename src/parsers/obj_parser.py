"""
Compatibility wrapper for OBJ parsing.

Delegates to the refactored OBJ parser to prevent duplicated logic while keeping
the legacy import surface intact.
"""

from src.parsers.refactored_obj_parser import (
    RefactoredOBJParser,
    OBJParseError,
    OBJMaterial,
    OBJFace,
    OBJVertex,
)

# Preserve the historical name expected by callers.
OBJParser = RefactoredOBJParser

__all__ = [
    "OBJParser",
    "RefactoredOBJParser",
    "OBJParseError",
    "OBJMaterial",
    "OBJFace",
    "OBJVertex",
]
