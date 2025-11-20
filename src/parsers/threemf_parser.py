"""
Compatibility wrapper for 3MF parsing.

Delegates to the refactored 3MF parser to avoid duplicated implementations.
"""

from src.parsers.refactored_threemf_parser import (
    RefactoredThreeMFParser,
    ThreeMFParseError,
    ThreeMFComponent,
    ThreeMFObject,
    ThreeMFBuildItem,
)

# Preserve legacy name expected by callers.
ThreeMFParser = RefactoredThreeMFParser

__all__ = [
    "ThreeMFParser",
    "RefactoredThreeMFParser",
    "ThreeMFParseError",
    "ThreeMFComponent",
    "ThreeMFObject",
    "ThreeMFBuildItem",
]
