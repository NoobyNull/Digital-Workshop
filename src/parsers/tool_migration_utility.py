"""
Tool database migration utility for converting existing JSON tool library to SQLite.

This module provides functionality to migrate tool data from the existing JSON format
to the new SQLite database format, ensuring backward compatibility and data preservation.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Callable, Tuple

from src.core.logging_config import get_logger
from src.core.database.tool_database_schema import ToolDatabaseSchema
from src.core.database.tool_database_repository import ToolDatabaseRepository
from src.core.database.provider_repository import ProviderRepository
from .tool_parsers.base_tool_parser import ToolData

logger = get_logger(__name__)


class ToolMigrationUtility:
    """Utility for migrating tool data from JSON to SQLite."""

    def __init__(self, sqlite_db_path: str):
        """Initialize migration utility with target SQLite database path."""
        self.db_path = sqlite_db_path
        self.logger = logger

        # Initialize database and repositories
        schema = ToolDatabaseSchema(sqlite_db_path)
        schema.create_tables()

        self.tool_repo = ToolDatabaseRepository(sqlite_db_path)
        self.provider_repo = ProviderRepository(sqlite_db_path)

    def migrate_from_json(
        self,
        json_file_path: str,
        provider_name: str = "IDC Woodcraft",
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> Tuple[int, int, List[str]]:
        """
        Migrate tool data from JSON file to SQLite database.

        Args:
            json_file_path: Path to source JSON file
            provider_name: Name of provider for imported tools
            progress_callback: Optional callback for progress updates (progress_percent, message)

        Returns:
            Tuple of (successfully_migrated_count, failed_count, error_messages)
        """
        try:
            json_path = Path(json_file_path)
            if not json_path.exists():
                raise FileNotFoundError(f"JSON file not found: {json_file_path}")

            if json_path.suffix.lower() != ".json":
                raise ValueError(f"Not a JSON file: {json_file_path}")

            self.logger.info("Starting migration from %s", json_file_path)

            # Load JSON data
            with open(json_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)

            # Ensure provider exists
            provider_id = self.provider_repo.add_provider(
                name=provider_name,
                description="Imported from JSON on migration",
                format_type="JSON",
            )

            # Extract tools from JSON
            tools = self._extract_tools_from_json(json_data)

            # Migrate tools
            success_count = 0
            fail_count = 0
            errors = []

            for idx, tool in enumerate(tools):
                try:
                    # Add tool to database
                    self.tool_repo.add_tool(
                        provider_id=provider_id,
                        guid=tool.guid or f"migrated_{idx}",
                        description=tool.description or "",
                        tool_type=tool.tool_type or "Unknown",
                        diameter=tool.diameter or 0.0,
                        vendor=tool.vendor or "",
                        geometry=tool.geometry or {},
                        start_values=tool.start_values or {},
                        properties=tool.custom_properties or {},
                    )
                    success_count += 1

                except Exception as e:
                    fail_count += 1
                    error_msg = f"Failed to migrate tool {idx}: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)

                # Report progress
                if progress_callback:
                    progress = (idx + 1) / len(tools)
                    progress_callback(progress, f"Migrated {success_count}/{len(tools)}")

            self.logger.info("Migration complete: %s successful, {fail_count} failed", success_count)
            return success_count, fail_count, errors

        except Exception as e:
            self.logger.error("Migration failed: %s", e)
            raise

    def _extract_tools_from_json(self, json_data: dict) -> List[ToolData]:
        """Extract tool data from JSON structure."""
        tools = []

        # Handle different JSON structures
        if isinstance(json_data, dict):
            # Try common keys for tool collections
            tool_lists = [
                json_data.get("tools", []),
                json_data.get("tool_library", []),
                json_data.get("items", []),
            ]

            for tool_list in tool_lists:
                if isinstance(tool_list, list):
                    for item in tool_list:
                        tool = self._parse_json_tool_item(item)
                        if tool:
                            tools.append(tool)

        elif isinstance(json_data, list):
            # JSON is a direct array of tools
            for item in json_data:
                tool = self._parse_json_tool_item(item)
                if tool:
                    tools.append(tool)

        self.logger.info("Extracted %s tools from JSON", len(tools))
        return tools

    def _parse_json_tool_item(self, item: dict) -> Optional[ToolData]:
        """Parse a single tool item from JSON."""
        try:
            if not isinstance(item, dict):
                return None

            # Extract common fields
            guid = item.get("guid") or item.get("id") or item.get("uuid") or ""
            description = item.get("description") or item.get("name") or ""
            tool_type = item.get("type") or item.get("tool_type") or ""
            diameter = float(item.get("diameter") or 0.0)
            vendor = item.get("vendor") or item.get("manufacturer") or ""

            # Extract geometry and start values
            geometry = item.get("geometry") or {}
            start_values = item.get("start_values") or item.get("speeds_feeds") or {}

            # Collect remaining properties as custom properties
            reserved_fields = {
                "guid",
                "id",
                "uuid",
                "description",
                "name",
                "type",
                "tool_type",
                "diameter",
                "vendor",
                "manufacturer",
                "geometry",
                "start_values",
                "speeds_feeds",
            }
            custom_properties = {k: v for k, v in item.items() if k not in reserved_fields}

            return ToolData(
                guid=guid,
                description=description,
                tool_type=tool_type,
                diameter=diameter,
                vendor=vendor,
                geometry=geometry,
                start_values=start_values,
                custom_properties=custom_properties,
            )

        except Exception as e:
            self.logger.warning("Failed to parse JSON tool item: %s", e)
            return None

    def migrate_from_existing_json_library(
        self, progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Tuple[int, int, List[str]]:
        """
        Migrate from the application's existing tool library JSON file.

        Looks for common locations of tool library JSON files.

        Args:
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple of (successfully_migrated_count, failed_count, error_messages)
        """
        # Common locations for tool library JSON
        possible_paths = [
            Path("data/tool_library.json"),
            Path("data/tools.json"),
            Path("resources/tool_library.json"),
            Path("src/resources/tool_library.json"),
        ]

        json_path = None
        for path in possible_paths:
            if path.exists():
                json_path = path
                break

        if not json_path:
            error_msg = "Could not find existing tool library JSON file. " "Checked: " + ", ".join(
                str(p) for p in possible_paths
            )
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        self.logger.info("Found tool library at %s", json_path)
        return self.migrate_from_json(str(json_path), progress_callback=progress_callback)

    def get_migration_status(self) -> Dict[str, any]:
        """Get status of migration (number of providers and tools in database)."""
        try:
            provider_count = self.provider_repo.get_provider_count()
            tool_count = self.tool_repo.get_tool_count()

            return {
                "database_path": self.db_path,
                "provider_count": provider_count,
                "tool_count": tool_count,
                "status": "ready" if tool_count > 0 else "empty",
            }

        except Exception as e:
            self.logger.error("Failed to get migration status: %s", e)
            return {
                "database_path": self.db_path,
                "status": "error",
                "error": str(e),
            }
