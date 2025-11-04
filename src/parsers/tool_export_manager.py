"""
Tool database export manager for exporting tools to external database formats.

This module provides functionality to export tools from the main SQLite database
to external databases in various formats (CSV, JSON, VTDB, TDB).
"""

import csv
import json
import sqlite3
from typing import Optional
from pathlib import Path

from src.core.logging_config import get_logger
from src.core.database.tool_database_repository import ToolDatabaseRepository
from src.core.database.provider_repository import ProviderRepository
from .tool_parsers import ProgressCallback

logger = get_logger(__name__)


class ToolExportManager:
    """Manager for exporting tools to external database formats."""

    def __init__(self, db_path: str):
        """Initialize export manager with database path."""
        self.db_path = db_path
        self.logger = logger
        self.tool_repo = ToolDatabaseRepository(db_path)
        self.provider_repo = ProviderRepository(db_path)

    def export_to_csv(
        self,
        output_path: str,
        provider_id: Optional[int] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> tuple:
        """
        Export tools to CSV format.

        Args:
            output_path: Path to save CSV file
            provider_id: Optional provider ID to filter exports
            progress_callback: Optional progress callback

        Returns:
            Tuple of (success, message, count)
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            if provider_id:
                tools = self.tool_repo.search_by_provider(provider_id)
            else:
                tools = self.tool_repo.get_all()

            with open(output_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                writer.writerow(
                    [
                        "GUID",
                        "Description",
                        "Type",
                        "Diameter",
                        "Vendor",
                        "Geometry",
                        "Start Values",
                        "Custom Properties",
                    ]
                )

                for i, tool in enumerate(tools):
                    writer.writerow(
                        [
                            tool["guid"],
                            tool["description"],
                            tool["tool_type"],
                            tool["diameter"],
                            tool["vendor"],
                            tool["geometry"],
                            tool["start_values"],
                            tool["custom_properties"],
                        ]
                    )

                    if progress_callback and tools:
                        progress = min((i + 1) / len(tools), 1.0)
                        progress_callback.report(progress, f"Exported {i + 1}/{len(tools)} tools")

            self.logger.info("Exported %s tools to CSV: {output_path}", len(tools))
            return True, f"Successfully exported {len(tools)} tools to CSV", len(tools)

        except Exception as e:
            error_msg = f"Failed to export tools to CSV: {e}"
            self.logger.error(error_msg)
            return False, error_msg, 0

    def export_to_json(
        self,
        output_path: str,
        provider_id: Optional[int] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> tuple:
        """
        Export tools to JSON format.

        Args:
            output_path: Path to save JSON file
            provider_id: Optional provider ID to filter exports
            progress_callback: Optional progress callback

        Returns:
            Tuple of (success, message, count)
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            if provider_id:
                tools = self.tool_repo.search_by_provider(provider_id)
            else:
                tools = self.tool_repo.get_all()

            export_data = {
                "version": "1.0",
                "format": "IDC Woodcraft Fusion360 Library",
                "tools": [],
            }

            for i, tool in enumerate(tools):
                tool_entry = {
                    "guid": tool["guid"],
                    "description": tool["description"],
                    "type": tool["tool_type"],
                    "diameter": tool["diameter"],
                    "vendor": tool["vendor"],
                    "geometry": tool["geometry"],
                    "start_values": tool["start_values"],
                    "custom_properties": json.loads(tool["custom_properties"] or "{}"),
                }
                export_data["tools"].append(tool_entry)

                if progress_callback and tools:
                    progress = min((i + 1) / len(tools), 1.0)
                    progress_callback.report(progress, f"Exported {i + 1}/{len(tools)} tools")

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)

            self.logger.info("Exported %s tools to JSON: {output_path}", len(tools))
            return True, f"Successfully exported {len(tools)} tools to JSON", len(tools)

        except Exception as e:
            error_msg = f"Failed to export tools to JSON: {e}"
            self.logger.error(error_msg)
            return False, error_msg, 0

    def export_to_external_database(
        self,
        output_path: str,
        provider_id: Optional[int] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> tuple:
        """
        Export tools to external SQLite database.

        Args:
            output_path: Path to save external database
            provider_id: Optional provider ID to filter exports
            progress_callback: Optional progress callback

        Returns:
            Tuple of (success, message, count)
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            if provider_id:
                tools = self.tool_repo.search_by_provider(provider_id)
            else:
                tools = self.tool_repo.get_all()

            conn = sqlite3.connect(output_file)
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tools (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guid TEXT UNIQUE NOT NULL,
                    description TEXT NOT NULL,
                    tool_type TEXT NOT NULL,
                    diameter REAL,
                    vendor TEXT,
                    geometry TEXT,
                    start_values TEXT,
                    custom_properties TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            for i, tool in enumerate(tools):
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO tools
                    (guid, description, tool_type, diameter, vendor, geometry,
                     start_values, custom_properties)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        tool["guid"],
                        tool["description"],
                        tool["tool_type"],
                        tool["diameter"],
                        tool["vendor"],
                        tool["geometry"],
                        tool["start_values"],
                        tool["custom_properties"],
                    ),
                )

                if progress_callback and tools:
                    progress = min((i + 1) / len(tools), 1.0)
                    progress_callback.report(progress, f"Exported {i + 1}/{len(tools)} tools")

            conn.commit()
            conn.close()

            self.logger.info("Exported %s tools to external database: {output_path}", len(tools))
            return (
                True,
                f"Successfully exported {len(tools)} tools to external database",
                len(tools),
            )

        except Exception as e:
            error_msg = f"Failed to export tools to external database: {e}"
            self.logger.error(error_msg)
            return False, error_msg, 0

    def get_export_statistics(self, provider_id: Optional[int] = None) -> dict:
        """
        Get statistics about available tools for export.

        Args:
            provider_id: Optional provider ID for statistics

        Returns:
            Dictionary with export statistics
        """
        try:
            if provider_id:
                tools = self.tool_repo.search_by_provider(provider_id)
                provider = self.provider_repo.get_by_id(provider_id)
                provider_name = provider["name"] if provider else "Unknown"
            else:
                tools = self.tool_repo.get_all()
                provider_name = "All Providers"

            tool_types = set()
            vendors = set()

            for tool in tools:
                if tool.get("tool_type"):
                    tool_types.add(tool["tool_type"])
                if tool.get("vendor"):
                    vendors.add(tool["vendor"])

            return {
                "total_tools": len(tools),
                "provider": provider_name,
                "unique_types": len(tool_types),
                "unique_vendors": len(vendors),
                "tool_types": sorted(list(tool_types)),
                "vendors": sorted(list(vendors)),
            }

        except Exception as e:
            self.logger.error("Failed to get export statistics: %s", e)
            return {"total_tools": 0, "error": str(e)}
