"""Tool library management for Feeds & Speeds calculator."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from src.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class Tool:
    """Represents a cutting tool."""

    guid: str
    description: str
    tool_type: str
    diameter: float  # DC - Diameter
    vendor: str
    product_id: str
    geometry: Dict[str, Any]
    start_values: Dict[str, Any]
    unit: str = "inches"

    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary for storage."""
        return {
            "guid": self.guid,
            "description": self.description,
            "tool_type": self.tool_type,
            "diameter": self.diameter,
            "vendor": self.vendor,
            "product_id": self.product_id,
            "geometry": self.geometry,
            "start_values": self.start_values,
            "unit": self.unit,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Tool":
        """Create tool from dictionary."""
        return cls(
            guid=data.get("guid", ""),
            description=data.get("description", ""),
            tool_type=data.get("tool_type", ""),
            diameter=data.get("diameter", 0.0),
            vendor=data.get("vendor", ""),
            product_id=data.get("product_id", ""),
            geometry=data.get("geometry", {}),
            start_values=data.get("start_values", {}),
            unit=data.get("unit", "inches"),
        )


class ToolLibraryManager:
    """Manages tool libraries from JSON files."""

    def __init__(self):
        """Initialize tool library manager."""
        self.libraries: Dict[str, List[Tool]] = {}
        self.logger = logger

    def load_library(self, library_name: str, file_path: str) -> bool:
        """
        Load a tool library from JSON file.

        Args:
            library_name: Name for the library
            file_path: Path to JSON file

        Returns:
            True if successful, False otherwise
        """
        try:
            path = Path(file_path)
            if not path.exists():
                self.logger.warning("Library file not found: %s", file_path)
                return False

            with open(path, "r") as f:
                data = json.load(f)

            tools = []
            for tool_data in data.get("data", []):
                try:
                    tool = Tool(
                        guid=tool_data.get("guid", ""),
                        description=tool_data.get("description", ""),
                        tool_type=tool_data.get("type", ""),
                        diameter=tool_data.get("geometry", {}).get("DC", 0.0),
                        vendor=tool_data.get("vendor", ""),
                        product_id=tool_data.get("product-id", ""),
                        geometry=tool_data.get("geometry", {}),
                        start_values=tool_data.get("start-values", {}),
                        unit=tool_data.get("unit", "inches"),
                    )
                    tools.append(tool)
                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                    self.logger.debug("Failed to parse tool: %s", e)
                    continue

            self.libraries[library_name] = tools
            self.logger.info("Loaded %s tools from {library_name}", len(tools))
            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to load library %s: {e}", library_name)
            return False

    def get_library(self, library_name: str) -> List[Tool]:
        """Get tools from a library."""
        return self.libraries.get(library_name, [])

    def get_all_libraries(self) -> Dict[str, List[Tool]]:
        """Get all loaded libraries."""
        return self.libraries

    def search_tools(self, query: str, library_name: Optional[str] = None) -> List[Tool]:
        """
        Search for tools by description.

        Args:
            query: Search query
            library_name: Optional library to search in

        Returns:
            List of matching tools
        """
        query_lower = query.lower()
        results = []

        if library_name:
            tools = self.get_library(library_name)
            results = [t for t in tools if query_lower in t.description.lower()]
        else:
            for tools in self.libraries.values():
                results.extend([t for t in tools if query_lower in t.description.lower()])

        return results

    def get_tool_by_guid(self, guid: str) -> Optional[Tool]:
        """Get a tool by its GUID."""
        for tools in self.libraries.values():
            for tool in tools:
                if tool.guid == guid:
                    return tool
        return None
