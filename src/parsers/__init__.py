"""
3D format parsers for Digital Workshop.

This package contains parsers for various 3D model formats including STL, OBJ, 3MF, and STEP.
Each parser handles format-specific loading and validation.
"""

from .base_parser import (
    BaseParser,
    Model,
    ModelFormat,
    Triangle,
    Vector3D,
    ModelStats,
    ParseError,
    ProgressCallback,
)
from .stl_parser import STLParser, RefactoredSTLParser
from .stl_components.stl_models import (
    STLFormat,
    STLModel,
    STLParseError,
    STLProgressCallback,
)
from .obj_parser import OBJParser, OBJMaterial, OBJFace
from .threemf_parser import (
    ThreeMFParser,
    ThreeMFObject,
    ThreeMFComponent,
    ThreeMFBuildItem,
)
from .step_parser import STEPParser, STEPEntity, STEPCartesianPoint, STEPDirection
from .format_detector import FormatDetector

__all__ = [
    # Base classes and utilities
    "BaseParser",
    "Model",
    "ModelFormat",
    "Triangle",
    "Vector3D",
    "ModelStats",
    "ParseError",
    "ProgressCallback",
    # STL parser
    "STLParser",
    "RefactoredSTLParser",
    "STLFormat",
    "STLModel",
    "STLParseError",
    "STLProgressCallback",
    # OBJ parser
    "OBJParser",
    "OBJMaterial",
    "OBJFace",
    # 3MF parser
    "ThreeMFParser",
    "ThreeMFObject",
    "ThreeMFComponent",
    "ThreeMFBuildItem",
    # STEP parser
    "STEPParser",
    "STEPEntity",
    "STEPCartesianPoint",
    "STEPDirection",
    # Format detection
    "FormatDetector",
]
