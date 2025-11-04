"""
VTDB tool database parser for IDC Woodcraft Vectric Tool Database Library Update rev 25-5.vtdb format.
VTDB files are SQLite databases with a specific structure.
"""

import sqlite3
from typing import List
from pathlib import Path

from .base_tool_parser import BaseToolParser, ToolData, ProgressCallback


class VTDBToolParser(BaseToolParser):
    """Parser for VTDB (SQLite) tool databases."""

    def get_format_name(self) -> str:
        """Get the format name."""
        return "VTDB"

    def validate_file(self, file_path: str) -> tuple:
        """Validate VTDB file format."""
        try:
            path = Path(file_path)
            if not path.exists():
                return False, "File does not exist"

            if path.suffix.lower() != ".vtdb":
                return False, "Not a VTDB file"

            # Try to connect to SQLite database
            with sqlite3.connect(file_path) as conn:
                cursor = conn.cursor()

                # Check if it has expected tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]

                if "tools" not in tables:
                    return False, "Missing 'tools' table"

                # Check tools table structure
                cursor.execute("PRAGMA table_info(tools)")
                columns = [row[1] for row in cursor.fetchall()]

                required_columns = ["description", "tool_type"]
                missing = [c for c in required_columns if c not in columns]

                if missing:
                    return False, f"Missing required columns: {missing}"

            return True, ""

        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def parse(self, file_path: str, progress_callback: ProgressCallback = None) -> List[ToolData]:
        """Parse VTDB tool database."""
        tools = []

        try:
            with sqlite3.connect(file_path) as conn:
                cursor = conn.cursor()

                # Get total tool count
                cursor.execute("SELECT COUNT(*) FROM tools")
                total_tools = cursor.fetchone()[0]

                # Query tools
                cursor.execute(
                    """
                    SELECT * FROM tools
                    ORDER BY description
                """
                )

                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]

                for i, row in enumerate(rows):
                    if self._check_cancelled():
                        break

                    tool_dict = dict(zip(columns, row))

                    # Parse tool properties if they exist
                    geometry = {}
                    start_values = {}

                    if "properties" in tool_dict and tool_dict["properties"]:
                        try:
                            import json

                            properties = json.loads(tool_dict["properties"])
                            geometry = properties.get("geometry", {})
                            start_values = properties.get("start_values", {})
                        except Exception:
                            self.logger.warning(
                                f"Failed to parse properties for tool {tool_dict.get('description', '')}"
                            )

                    # Create tool
                    tool = ToolData(
                        guid=tool_dict.get("guid", ""),
                        description=tool_dict.get("description", ""),
                        tool_type=tool_dict.get("tool_type", ""),
                        diameter=tool_dict.get("diameter", 0.0),
                        vendor=tool_dict.get("vendor", "IDC Woodcraft"),
                        product_id=tool_dict.get("product_id", ""),
                        unit=tool_dict.get("unit", "inches"),
                        geometry=geometry,
                        start_values=start_values,
                    )

                    tools.append(tool)

                    # Report progress
                    if progress_callback and total_tools > 0:
                        progress = min((i + 1) / total_tools, 1.0)
                        progress_callback.report(progress, f"Parsing tool {i + 1}/{total_tools}")

            self.logger.info(f"Parsed {len(tools)} tools from VTDB file")
            return tools

        except Exception as e:
            self.logger.error(f"Failed to parse VTDB file: {e}")
            raise
