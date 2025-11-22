"""
Canonical parser registry.

Central place to decide which parser class backs each ModelFormat. New code should
request parsers from here so we can swap legacy implementations with refactored
ones without changing every consumer.
"""

from __future__ import annotations

from typing import Dict, Type

from src.core.data_structures import ModelFormat
from src.core.interfaces.parser_interfaces import IParser
from src.parsers.obj_parser import OBJParser
from src.parsers.step_parser import STEPParser
from src.parsers.threemf_parser import ThreeMFParser
from src.parsers._stl_strategy import get_stl_parser_class, get_legacy_stl_parser_class

_PARSER_MAPPING: Dict[ModelFormat, Type[IParser]] = {
    ModelFormat.STL: get_stl_parser_class(),
    ModelFormat.OBJ: OBJParser,
    ModelFormat.THREE_MF: ThreeMFParser,
    ModelFormat.STEP: STEPParser,
}


class ParserNotFoundError(LookupError):
    """Raised when no parser is registered for a format."""


def get_parser_for_format(model_format: ModelFormat) -> IParser:
    """Return an instance of the canonical parser for the given format."""
    parser_cls = _PARSER_MAPPING.get(model_format)
    if parser_cls is None:
        raise ParserNotFoundError(f"No parser registered for format: {model_format}")
    return parser_cls()


def get_legacy_parser_for_format(model_format: ModelFormat) -> IParser:
    """Return an instance of the legacy parser for the given format, if available."""
    if model_format == ModelFormat.STL:
        return get_legacy_stl_parser_class()()
    raise ParserNotFoundError(f"No legacy parser registered for format: {model_format}")
