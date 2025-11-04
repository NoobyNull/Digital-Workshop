"""
Base class for all tool parsers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field

from src.core.logging_config import get_logger


@dataclass
class ToolData:
    """Data structure for a parsed tool."""

    guid: str
    description: str
    tool_type: str
    diameter: float
    vendor: str
    product_id: str = ""
    unit: str = "inches"
    geometry: Dict[str, Any] = field(default_factory=dict)
    geometry_data: Dict[str, Any] = field(default_factory=dict)
    start_values: Dict[str, Any] = field(default_factory=dict)
    properties: Dict[str, Any] = field(default_factory=dict)
    custom_properties: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Post-initialization to handle geometry_data alias."""
        if self.geometry_data and not self.geometry:
            self.geometry = self.geometry_data
        if self.custom_properties and not self.properties:
            self.properties = self.custom_properties


class ProgressCallback:
    """Callback for progress reporting during parsing."""

    def __init__(self, callback: Optional[Callable[[float, str], None]] = None):
        """Initialize progress callback."""
        self.callback = callback
        self.last_report = 0.0

    def report(self, progress: float, message: str = "") -> None:
        """Report progress if callback is set."""
        if self.callback and progress - self.last_report >= 0.1:  # Report every 10%
            self.callback(progress, message)
            self.last_report = progress


class BaseToolParser(ABC):
    """Abstract base class for tool parsers."""

    def __init__(self):
        """Initialize parser."""
        self.logger = get_logger(self.__class__.__name__)
        self._cancelled = False

    @abstractmethod
    def parse(
        self, file_path: str, progress_callback: Optional[ProgressCallback] = None
    ) -> List[ToolData]:
        """
        Parse a tool database file.

        Args:
            file_path: Path to the tool database file
            progress_callback: Optional progress callback

        Returns:
            List of parsed tools
        """

    @abstractmethod
    def validate_file(self, file_path: str) -> tuple:
        """
        Validate if file is supported format.

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (is_valid, error_message)
        """

    @abstractmethod
    def get_format_name(self) -> str:
        """Get the format name this parser handles."""

    def cancel(self) -> None:
        """Cancel the parsing operation."""
        self._cancelled = True
        self.logger.info("Parsing cancelled")

    def reset_cancel(self) -> None:
        """Reset cancellation state."""
        self._cancelled = False

    def _check_cancelled(self) -> bool:
        """Check if parsing was cancelled."""
        return self._cancelled
