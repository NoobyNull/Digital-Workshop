"""
TDB tool database parser for IDC-Woodcraft-Carveco-Tool-Database.tdb format.
TDB files are binary files with UTF-16 encoding.
"""

# pylint: disable=unused-variable

import struct
from typing import List, Optional
from pathlib import Path

from .base_tool_parser import BaseToolParser, ToolData, ProgressCallback


class TDBToolParser(BaseToolParser):
    """Parser for TDB (binary) tool databases."""

    def get_format_name(self) -> str:
        """Get the format name."""
        return "TDB"

    def validate_file(self, file_path: str) -> tuple[bool, str]:
        """Validate TDB file format."""
        try:
            path = Path(file_path)
            if not path.exists():
                return False, "File does not exist"

            if path.suffix.lower() != ".tdb":
                return False, "Not a TDB file"

            # Check file header
            with open(path, "rb") as f:
                header = f.read(4)

                # TDB files start with magic bytes 'TDB\0'
                if header != b"TDB\x00":
                    return False, "Invalid TDB file signature"

            return True, ""

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def parse(
        self, file_path: str, progress_callback: Optional[ProgressCallback] = None
    ) -> List[ToolData]:
        """Parse TDB tool database."""
        tools = []

        try:
            path = Path(file_path)

            with open(path, "rb") as f:
                # Read header
                header = f.read(4)
                if header != b"TDB\x00":
                    raise ValueError("Invalid TDB file signature")

                # Read version
                version = struct.unpack("<I", f.read(4))[0]

                # Read tool count
                tool_count = struct.unpack("<I", f.read(4))[0]

                # Parse each tool
                for i in range(tool_count):
                    if self._check_cancelled():
                        break

                    # Read tool header
                    tool_header_size = struct.unpack("<I", f.read(4))[0]
                    tool_data = f.read(tool_header_size)

                    # Parse tool data (UTF-16 encoded)
                    tool = self._parse_tdb_tool(tool_data)
                    tools.append(tool)

                    # Report progress
                    if progress_callback and tool_count > 0:
                        progress = min((i + 1) / tool_count, 1.0)
                        progress_callback.report(progress, f"Parsing tool {i + 1}/{tool_count}")

            self.logger.info(f"Parsed {len(tools)} tools from TDB file")
            return tools

        except Exception as e:
            self.logger.error(f"Failed to parse TDB file: {e}")
            raise

    def _parse_tdb_tool(self, data: bytes) -> ToolData:
        """Parse a single tool from TDB data."""
        # Decode UTF-16 data
        text = data.decode("utf-16-le")

        # Split into fields
        fields = text.split("\x00")

        # Parse tool data (example structure - adjust based on actual format)
        tool = ToolData(
            guid=fields[0] if len(fields) > 0 else "",
            description=fields[1] if len(fields) > 1 else "",
            tool_type=fields[2] if len(fields) > 2 else "",
            diameter=float(fields[3]) if len(fields) > 3 and fields[3] else 0.0,
            vendor=fields[4] if len(fields) > 4 else "IDC Woodcraft",
            product_id=fields[5] if len(fields) > 5 else "",
            unit=fields[6] if len(fields) > 6 else "inches",
        )

        # Parse additional properties if available
        if len(fields) > 7:
            tool.geometry = self._parse_tdb_properties(fields[7])

        if len(fields) > 8:
            tool.start_values = self._parse_tdb_properties(fields[8])

        return tool

    def _parse_tdb_properties(self, prop_string: str) -> dict:
        """Parse property string from TDB format."""
        properties = {}

        if not prop_string:
            return properties

        # Example property parsing - adjust based on actual format
        pairs = prop_string.split(";")
        for pair in pairs:
            if "=" in pair:
                key, value = pair.split("=", 1)
                try:
                    # Try to parse as float
                    properties[key] = float(value)
                except ValueError:
                    # Keep as string
                    properties[key] = value

        return properties
