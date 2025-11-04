"""
STL Parser - Main parser class.

This module re-exports the STLParser from the parent module for backward compatibility.
The actual implementation remains in src/parsers/stl_parser.py due to complex interdependencies.
"""

# Import the actual STLParser from the parent module
# This is a temporary re-export to maintain the modular structure
# while keeping the complex parsing logic intact
from src.parsers.stl_parser import STLParser as _OriginalSTLParser


class STLParser(_OriginalSTLParser):
    """
    STL file parser supporting both binary and ASCII formats.

    Features:
    - Memory-efficient parsing for large files
    - Progress reporting for long operations
    - Comprehensive error handling and validation
    - Integration with JSON logging system
    - Performance optimization for different file sizes
    """
