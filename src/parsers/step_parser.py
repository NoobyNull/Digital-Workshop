"""
Compatibility wrapper for STEP parsing.

This module now delegates to the refactored STEP parser to avoid maintaining
duplicated implementations in two places. The public API remains the same via
the aliased classes exported below.
"""

from src.parsers.refactored_step_parser import (
    RefactoredSTEPParser,
    STEPParseError,
    STEPEntity,
    STEPCartesianPoint,
    STEPDirection,
    STEPVector,
    STEPAxis2Placement3D,
    STEPAdvancedFace,
    STEPFaceBound,
    STEPEdgeLoop,
    STEPOrientedEdge,
    STEPEdgeCurve,
    STEPVertexPoint,
)

# Preserve the historical name expected by callers.
STEPParser = RefactoredSTEPParser

__all__ = [
    "STEPParser",
    "RefactoredSTEPParser",
    "STEPParseError",
    "STEPEntity",
    "STEPCartesianPoint",
    "STEPDirection",
    "STEPVector",
    "STEPAxis2Placement3D",
    "STEPAdvancedFace",
    "STEPFaceBound",
    "STEPEdgeLoop",
    "STEPOrientedEdge",
    "STEPEdgeCurve",
    "STEPVertexPoint",
]
