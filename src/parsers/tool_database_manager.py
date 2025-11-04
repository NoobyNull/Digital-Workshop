"""
Unified tool database manager that integrates all parsers.

This module provides a central interface for importing tools from multiple formats,
managing tool databases, and exporting tools to external databases.
"""

import struct
import json
import csv
import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.core.logging_config import get_logger
from src.core.database.tool_database_repository import ToolDatabaseRepository
from src.core.database.provider_repository import ProviderRepository
from src.core.database.tool_preferences_repository import ToolPreferencesRepository
from .tool_parsers import (
    BaseToolParser,
    CSVToolParser,
    JSONToolParser,
    VTDBToolParser,
    TDBToolParser,
    ProgressCallback,
)

logger = get_logger(__name__)


class ToolDatabaseManager:
    """Unified manager for tool database operations."""

    def __init__(self, db_path: str) -> None:
        """Initialize manager with database path."""
        self.db_path = db_path
        self.logger = logger

        # Initialize repositories
        self.tool_repo = ToolDatabaseRepository(db_path)
        self.provider_repo = ProviderRepository(db_path)
        self.preferences_repo = ToolPreferencesRepository(db_path)

        # Initialize parsers
        self.parsers: Dict[str, BaseToolParser] = {
            "CSV": CSVToolParser(),
            "JSON": JSONToolParser(),
            "VTDB": VTDBToolParser(),
            "TDB": TDBToolParser(),
        }

    def import_tools_from_file(
        self,
        file_path: str,
        provider_name: str = "",
        progress_callback: Optional[ProgressCallback] = None,
    ) -> tuple:
        """
        Import tools from a file.

        Args:
            file_path: Path to the tool database file
            provider_name: Optional provider name (defaults to filename)
            progress_callback: Optional progress callback

        Returns:
            Tuple of (success, message)
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return False, "File does not exist"

            # Determine format from file extension
            format_type = path.suffix.upper().lstrip(".")
            if format_type not in self.parsers:
                return False, f"Unsupported file format: {format_type}"

            parser = self.parsers[format_type]

            # Validate file
            is_valid, error_msg = parser.validate_file(file_path)
            if not is_valid:
                return False, f"Invalid file: {error_msg}"

            # Create provider if needed
            if not provider_name:
                provider_name = path.stem

            provider_id = self.provider_repo.add_provider(
                name=provider_name,
                description=f"Imported from {path.name}",
                file_path=str(path),
                format_type=format_type,
            )

            if not provider_id:
                return False, "Failed to create provider"

            # Parse tools
            tools = parser.parse(file_path, progress_callback)

            if not tools:
                return False, "No tools found in file"

            # Import tools to database
            imported_count = 0
            for tool in tools:
                tool_data = {
                    "guid": tool.guid,
                    "description": tool.description,
                    "tool_type": tool.tool_type,
                    "diameter": tool.diameter,
                    "vendor": tool.vendor,
                    "product_id": tool.product_id,
                    "unit": tool.unit,
                    "properties": {**tool.geometry, **tool.start_values},
                    "property_types": {
                        **{k: "geometry" for k in tool.geometry.keys()},
                        **{k: "start_values" for k in tool.start_values.keys()},
                    },
                }

                if self.tool_repo.add_tool(provider_id, tool_data):
                    imported_count += 1

            message = f"Successfully imported {imported_count} tools from {provider_name}"
            self.logger.info(message)
            return True, message

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            error_msg = f"Failed to import tools: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def get_tools_by_provider(self, provider_id: int) -> List[Dict[str, Any]]:
        """Get all tools for a provider."""
        return self.tool_repo.get_tools_by_provider(provider_id)

    def search_tools(self, query: str, provider_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for tools."""
        return self.tool_repo.search_tools(query, provider_id)

    def get_all_providers(self) -> List[Dict[str, Any]]:
        """Get all providers."""
        return self.provider_repo.get_all_providers()

    def export_tools_to_external_db(
        self, provider_id: int, external_db_path: str, format_type: str
    ) -> tuple:
        """
        Export tools to external database.

        Args:
            provider_id: Provider ID to export
            external_db_path: Path to external database
            format_type: Export format ('CSV', 'JSON', 'VTDB', 'TDB')

        Returns:
            Tuple of (success, message)
        """
        try:
            # Get tools
            tools = self.get_tools_by_provider(provider_id)
            if not tools:
                return False, "No tools to export"

            # Export based on format
            if format_type == "CSV":
                return self._export_to_csv(tools, external_db_path)
            elif format_type == "JSON":
                return self._export_to_json(tools, external_db_path)
            elif format_type == "VTDB":
                return self._export_to_vtdb(tools, external_db_path)
            elif format_type == "TDB":
                return self._export_to_tdb(tools, external_db_path)
            else:
                return False, f"Unsupported export format: {format_type}"

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            error_msg = f"Failed to export tools: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def _export_to_csv(self, tools: List[Dict[str, Any]], file_path: str) -> tuple:
        """Export tools to CSV format."""
        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Write header
                writer.writerow(
                    [
                        "guid",
                        "description",
                        "tool_type",
                        "diameter",
                        "vendor",
                        "product_id",
                        "unit",
                        "geometry",
                        "start_values",
                    ]
                )

                # Write tools
                for tool in tools:
                    writer.writerow(
                        [
                            tool.get("guid", ""),
                            tool.get("description", ""),
                            tool.get("tool_type", ""),
                            tool.get("diameter", ""),
                            tool.get("vendor", ""),
                            tool.get("product_id", ""),
                            tool.get("unit", ""),
                            str(tool.get("properties", {}).get("geometry", {})),
                            str(tool.get("properties", {}).get("start_values", {})),
                        ]
                    )

            return True, f"Exported {len(tools)} tools to CSV"

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return False, f"Failed to export to CSV: {str(e)}"

    def _export_to_json(self, tools: List[Dict[str, Any]], file_path: str) -> tuple:
        """Export tools to JSON format."""
        try:
            # Convert tools to expected format
            export_data = {"data": []}

            for tool in tools:
                tool_data = {
                    "guid": tool.get("guid", ""),
                    "description": tool.get("description", ""),
                    "type": tool.get("tool_type", ""),
                    "vendor": tool.get("vendor", ""),
                    "product-id": tool.get("product_id", ""),
                    "unit": tool.get("unit", "inches"),
                    "geometry": tool.get("properties", {}).get("geometry", {}),
                    "start-values": tool.get("properties", {}).get("start_values", {}),
                }
                export_data["data"].append(tool_data)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)

            return True, f"Exported {len(tools)} tools to JSON"

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return False, f"Failed to export to JSON: {str(e)}"

    def _export_to_vtdb(self, tools: List[Dict[str, Any]], file_path: str) -> tuple:
        """Export tools to VTDB (SQLite) format."""
        try:
            # Create new SQLite database
            with sqlite3.connect(file_path) as conn:
                cursor = conn.cursor()

                # Create tables
                cursor.execute(
                    """
                    CREATE TABLE tools (
                        id INTEGER PRIMARY KEY,
                        guid TEXT,
                        description TEXT,
                        tool_type TEXT,
                        diameter REAL,
                        vendor TEXT,
                        product_id TEXT,
                        unit TEXT,
                        properties TEXT
                    )
                """
                )

                # Insert tools
                for tool in tools:
                    properties = {
                        "geometry": tool.get("properties", {}).get("geometry", {}),
                        "start_values": tool.get("properties", {}).get("start_values", {}),
                    }

                    cursor.execute(
                        """
                        INSERT INTO tools (guid, description, tool_type, diameter, vendor,
                                         product_id, unit, properties)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            tool.get("guid", ""),
                            tool.get("description", ""),
                            tool.get("tool_type", ""),
                            tool.get("diameter", 0.0),
                            tool.get("vendor", ""),
                            tool.get("product_id", ""),
                            tool.get("unit", "inches"),
                            str(properties),
                        ),
                    )

                conn.commit()

            return True, f"Exported {len(tools)} tools to VTDB"

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return False, f"Failed to export to VTDB: {str(e)}"

    def _export_to_tdb(self, tools: List[Dict[str, Any]], file_path: str) -> tuple:
        """Export tools to TDB (binary) format."""
        try:
            with open(file_path, "wb") as f:
                # Write header
                f.write(b"TDB\x00")  # Magic bytes
                f.write(struct.pack("<I", 1))  # Version
                f.write(struct.pack("<I", len(tools)))  # Tool count

                # Write tools
                for tool in tools:
                    tool_data = self._format_tool_for_tdb(tool)
                    encoded_data = tool_data.encode("utf-16-le")
                    f.write(struct.pack("<I", len(encoded_data)))
                    f.write(encoded_data)

            return True, f"Exported {len(tools)} tools to TDB"

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return False, f"Failed to export to TDB: {str(e)}"

    def _format_tool_for_tdb(self, tool: Dict[str, Any]) -> str:
        """Format tool data for TDB export."""
        # Format tool as null-separated fields
        fields = [
            tool.get("guid", ""),
            tool.get("description", ""),
            tool.get("tool_type", ""),
            str(tool.get("diameter", 0.0)),
            tool.get("vendor", ""),
            tool.get("product_id", ""),
            tool.get("unit", "inches"),
            str(tool.get("properties", {}).get("geometry", {})),
            str(tool.get("properties", {}).get("start_values", {})),
        ]

        return "\x00".join(fields)
