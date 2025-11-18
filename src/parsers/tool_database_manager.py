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
    ToolData,
    ProgressCallback,
    CSVToolParser,
    JSONToolParser,
    VTDBToolParser,
    TDBToolParser,
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

    def _build_existing_tool_key(self, tool_row: Dict[str, Any]) -> str:
        """Build a stable key for an existing tool row for duplicate detection."""
        guid = (tool_row.get("guid") or "").strip()
        if guid:
            return f"guid:{guid}"

        desc = (tool_row.get("description") or "").strip().lower()
        tool_type = (tool_row.get("tool_type") or "").strip().lower()
        vendor = (tool_row.get("vendor") or "").strip().lower()
        product_id = (tool_row.get("product_id") or "").strip().lower()
        try:
            diameter = float(tool_row.get("diameter") or 0.0)
        except (TypeError, ValueError):
            diameter = 0.0

        return f"meta:{desc}|{tool_type}|{vendor}|{product_id}|{diameter:.5f}"

    def _build_parsed_tool_key(self, tool: ToolData) -> str:
        """Build a stable key for a parsed ToolData object for duplicate detection."""
        guid = (tool.guid or "").strip()
        if guid:
            return f"guid:{guid}"

        desc = (tool.description or "").strip().lower()
        tool_type = (tool.tool_type or "").strip().lower()
        vendor = (tool.vendor or "").strip().lower()
        product_id = (tool.product_id or "").strip().lower()
        try:
            diameter = float(tool.diameter or 0.0)
        except (TypeError, ValueError):
            diameter = 0.0

        return f"meta:{desc}|{tool_type}|{vendor}|{product_id}|{diameter:.5f}"

    def _select_parser_for_file(
        self, path: Path
    ) -> tuple[Optional[BaseToolParser], Optional[str], Optional[str]]:
        """Select an appropriate parser for the given file.

        This uses a hybrid strategy:
        1) Prefer the parser implied by the file extension if it validates.
        2) If the extension is unknown or validation fails, fall back to
           content-based detection (sniff the file structure).

        Returns:
            (parser, format_type, error_message)
            parser/format_type are None if detection fails.
        """
        # Give a clear message for known-but-unsupported formats.
        if path.suffix.lower() == ".tool":
            msg = (
                "The selected file is a Vectric/Amana '.tool' library. "
                "This uses a proprietary binary format that Digital Workshop "
                "cannot reliably parse yet.\n\n"
                "Please export the library from Vectric as a VTDB, TDB, CSV, or JSON "
                "file and import that file instead."
            )
            return None, None, msg

        format_type = path.suffix.upper().lstrip(".")
        ext_error: Optional[str] = None

        # Fast path: extension-based detection
        if format_type in self.parsers:
            parser = self.parsers[format_type]
            is_valid, error_msg = parser.validate_file(str(path))
            if is_valid:
                return parser, format_type, None

            # Remember why the extension-based parser failed, but still
            # allow content-based detection to try to recover.
            ext_error = f"{format_type}: {error_msg}" if error_msg else None

        # Fallback: content-based detection (ignore extension)
        parser, detected_type = self._detect_parser_by_content(path)
        if parser is not None and detected_type:
            return parser, detected_type, None

        # Nothing matched; surface the extension error if we have one
        if ext_error:
            return None, None, ext_error

        return None, None, "Unsupported or unrecognized tool database format"

    def _detect_parser_by_content(
        self, path: Path
    ) -> tuple[Optional[BaseToolParser], Optional[str]]:
        """Detect parser based on file contents instead of extension.

        This is intentionally conservative and only recognizes formats that
        clearly match our expected structures.
        """
        # VTDB / Vectric-style SQLite database: look for a 'tools' table with
        # at least description + tool_type columns.
        try:
            with sqlite3.connect(str(path)) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]

                if "tools" in tables:
                    cursor.execute("PRAGMA table_info(tools)")
                    columns = [row[1] for row in cursor.fetchall()]
                    if "description" in columns and "tool_type" in columns:
                        parser = self.parsers.get("VTDB")
                        if parser is not None:
                            return parser, "VTDB"
        except sqlite3.Error:
            # Not a valid SQLite DB in the expected VTDB shape
            pass

        # TDB: binary file with magic bytes 'TDB\0'
        try:
            with open(path, "rb") as f:
                header = f.read(4)
                if header == b"TDB\x00":
                    parser = self.parsers.get("TDB")
                    if parser is not None:
                        return parser, "TDB"
        except (OSError, IOError):
            pass

        # JSON: must parse as JSON and contain a 'data' or 'tools' list
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                tool_list = None
                if "data" in data and isinstance(data["data"], list):
                    tool_list = data["data"]
                elif "tools" in data and isinstance(data["tools"], list):
                    tool_list = data["tools"]

                if tool_list is not None:
                    parser = self.parsers.get("JSON")
                    if parser is not None:
                        return parser, "JSON"
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError):
            pass

        # CSV: require at least a header row and basic required header checks
        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                headers = next(reader, [])

            headers_lower = [h.lower().strip() for h in headers]
            required_checks = {
                "description": ["description", "name", "tool_name", "tool name"],
                "tool_type": ["tool_type", "type", "tool type", "category"],
            }

            missing = []
            for field, variations in required_checks.items():
                found = False
                for header in headers_lower:
                    for var in variations:
                        if var in header or header in var:
                            found = True
                            break
                    if found:
                        break
                if not found:
                    missing.append(field)

            if not missing:
                parser = self.parsers.get("CSV")
                if parser is not None:
                    return parser, "CSV"
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError):
            pass

        return None, None

    def import_tools_from_file(
        self,
        file_path: str,
        provider_name: str = "",
        progress_callback: Optional[ProgressCallback] = None,
        mode: str = "auto",
    ) -> tuple:
        """Import tools from a file into the unified database.

        Args:
            file_path: Path to the tool database file.
            provider_name: Optional provider name (defaults to filename).
            progress_callback: Optional progress callback.
            mode: How to handle existing providers:
                - "auto": create provider if needed, merge new tools otherwise.
                - "merge": always merge, skipping duplicates.
                - "overwrite": replace all tools for this provider with the new contents.

        Returns:
            Tuple of (success, message).
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return False, "File does not exist"

            # Select parser using hybrid extension + content-based detection
            parser, format_type, error_msg = self._select_parser_for_file(path)
            if parser is None or not format_type:
                if error_msg:
                    return False, f"Invalid file: {error_msg}"
                return False, "Unsupported or unrecognized tool database format"

            # Normalize mode
            normalized_mode = (mode or "auto").lower()
            if normalized_mode not in {"auto", "merge", "overwrite"}:
                normalized_mode = "auto"

            # Determine provider
            if not provider_name:
                provider_name = path.stem

            existing_provider = self.provider_repo.get_provider_by_name(provider_name)

            if existing_provider:
                provider_id = existing_provider.get("id")
                # Keep metadata in sync with latest import location/format
                self.provider_repo.update_provider(
                    provider_id,
                    file_path=str(path),
                    format_type=format_type,
                )
            else:
                provider_id = self.provider_repo.add_provider(
                    name=provider_name,
                    description=f"Imported from {path.name}",
                    file_path=str(path),
                    format_type=format_type,
                )

            if not provider_id:
                return False, "Failed to create or locate provider"

            # Parse tools from the source file
            tools = parser.parse(file_path, progress_callback)

            if not tools:
                return False, "No tools found in file"

            # If overwriting, clear existing tools first
            if existing_provider and normalized_mode == "overwrite":
                deleted = self.tool_repo.delete_tools_by_provider(provider_id)
                self.logger.info(
                    "Cleared %s existing tools before overwriting provider %s",
                    deleted,
                    provider_name,
                )

            # For merge/auto, build a set of existing tool keys to avoid duplicates
            existing_keys = set()
            if existing_provider and normalized_mode in {"auto", "merge"}:
                existing_tools = self.tool_repo.get_tools_by_provider(provider_id)
                for tool_row in existing_tools:
                    key = self._build_existing_tool_key(tool_row)
                    existing_keys.add(key)

            # Import tools to database
            imported_count = 0
            for tool in tools:
                if existing_keys:
                    key = self._build_parsed_tool_key(tool)
                    if key in existing_keys:
                        continue

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

            # Build user-facing message
            if existing_provider:
                if normalized_mode == "overwrite":
                    message = (
                        f"Successfully updated {provider_name}: imported {imported_count} tools"
                    )
                else:
                    message = f"Successfully merged {imported_count} new tools into {provider_name}"
            else:
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
