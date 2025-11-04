"""
JSON tool database parser for IDCWoodcraftFusion360Library.json format.
"""

import json
from typing import List, Optional
from pathlib import Path

from .base_tool_parser import BaseToolParser, ToolData, ProgressCallback


class JSONToolParser(BaseToolParser):
    """Parser for JSON tool databases."""

    def get_format_name(self) -> str:
        """Get the format name."""
        return "JSON"

    def validate_file(self, file_path: str) -> tuple[bool, str]:
        """Validate JSON file format."""
        try:
            path = Path(file_path)
            if not path.exists():
                return False, "File does not exist"

            if path.suffix.lower() != ".json":
                return False, "Not a JSON file"

            # Try to parse JSON
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Check if it has expected structure (support both 'data' and 'tools')
            tool_list = None
            if "data" in data and isinstance(data["data"], list):
                tool_list = data["data"]
            elif "tools" in data and isinstance(data["tools"], list):
                tool_list = data["tools"]
            else:
                return False, "Missing 'data' or 'tools' field in JSON"

            # Check first tool structure
            if tool_list:
                tool = tool_list[0]
                required_fields = ["description", "type"]
                missing = [f for f in required_fields if f not in tool]

                if missing:
                    return False, f"Missing required tool fields: {missing}"

            return True, ""

        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}"
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return False, f"Validation error: {str(e)}"

    def parse(
        self, file_path: str, progress_callback: Optional[ProgressCallback] = None
    ) -> List[ToolData]:
        """Parse JSON tool database."""
        tools = []

        try:
            path = Path(file_path)

            # Check if file exists
            if not path.exists():
                self.logger.warning("File does not exist: %s", file_path)
                return []

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Support both 'data' and 'tools' field names
            tool_list = data.get("data", data.get("tools", []))
            total_tools = len(tool_list)

            for i, tool_data in enumerate(tool_list):
                if self._check_cancelled():
                    break

                # Parse tool
                tool = ToolData(
                    guid=tool_data.get("guid", ""),
                    description=tool_data.get("description", ""),
                    tool_type=tool_data.get("type", ""),
                    diameter=tool_data.get("geometry", {}).get("DC", 0.0),
                    vendor=tool_data.get("vendor", "IDC Woodcraft"),
                    product_id=tool_data.get("product-id", ""),
                    unit=tool_data.get("unit", "inches"),
                    geometry=tool_data.get("geometry", {}),
                    start_values=tool_data.get("start-values", {}),
                )

                tools.append(tool)

                # Report progress
                if progress_callback and total_tools > 0:
                    progress = min((i + 1) / total_tools, 1.0)
                    progress_callback.report(progress, f"Parsing tool {i + 1}/{total_tools}")

            self.logger.info("Parsed %s tools from JSON file", len(tools))
            return tools

        except FileNotFoundError:
            self.logger.warning("File not found: %s", file_path)
            return []
        except json.JSONDecodeError as e:
            self.logger.error("Invalid JSON format: %s", e)
            return []
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to parse JSON file: %s", e)
            return []
