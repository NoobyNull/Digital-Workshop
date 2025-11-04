"""
CSV tool database parser for IDC-Woodcraft-Carbide-Create-Database-5-2-2025.csv format.
"""

import csv
from typing import List, Optional
from pathlib import Path

from .base_tool_parser import BaseToolParser, ToolData, ProgressCallback


class CSVToolParser(BaseToolParser):
    """Parser for CSV tool databases."""

    def get_format_name(self) -> str:
        """Get the format name."""
        return "CSV"

    def validate_file(self, file_path: str) -> tuple:
        """Validate CSV file format with flexible header matching."""
        try:
            path = Path(file_path)
            if not path.exists():
                return False, "File does not exist"

            if path.suffix.lower() != ".csv":
                return False, "Not a CSV file"

            # Check if file has expected headers with flexible matching
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                headers = next(reader, [])
                headers_lower = [h.lower().strip() for h in headers]

                # Required field variations (matching _normalize_headers logic)
                required_checks = {
                    "description": ["description", "name", "tool_name", "tool name"],
                    "tool_type": ["tool_type", "type", "tool type", "category"],
                    "diameter": [
                        "diameter",
                        "dia",
                        "dc",
                        "diameter (mm)",
                        "diameter (in)",
                    ],
                }

                missing = []
                for field, variations in required_checks.items():
                    # Check if any variation matches any header
                    found = False
                    for header in headers_lower:
                        for var in variations:
                            # Match if variation is in header or vice versa
                            if var.lower() in header or header in var.lower():
                                found = True
                                break
                        if found:
                            break
                    if not found:
                        missing.append(field)

                if missing:
                    return False, f"Missing required headers: {missing}"

            return True, ""

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def _normalize_headers(self, row: dict) -> dict:
        """Normalize CSV headers to handle case variations and common field name differences."""
        # Header mapping for common variations
        header_map = {
            "guid": ["guid", "GUID", "id", "ID", "tool_id"],
            "description": [
                "description",
                "Description",
                "DESCRIPTION",
                "name",
                "Name",
                "tool_name",
            ],
            "tool_type": ["tool_type", "Type", "TYPE", "type", "tool type"],
            "diameter": [
                "diameter",
                "Diameter",
                "DIAMETER",
                "Diameter (mm)",
                "Diameter (in)",
                "DC",
            ],
            "vendor": ["vendor", "Vendor", "VENDOR", "manufacturer", "Manufacturer"],
            "product_id": ["product_id", "Product ID", "PRODUCT_ID", "sku", "SKU"],
            "unit": ["unit", "Unit", "UNIT", "units", "Units"],
            "flute_length": ["flute_length", "Flute Length", "Flute Length (mm)", "FL"],
            "overall_length": [
                "overall_length",
                "Overall Length",
                "Overall Length (mm)",
                "OAL",
            ],
        }

        normalized = {}
        # Create a lowercase version of the row for case-insensitive matching
        row_lower = {k.lower(): v for k, v in row.items()}

        for standard_key, variations in header_map.items():
            for variation in variations:
                if variation.lower() in row_lower:
                    normalized[standard_key] = row_lower[variation.lower()]
                    break
            if standard_key not in normalized:
                normalized[standard_key] = ""

        # Keep all original keys that weren't normalized
        for key, value in row.items():
            if key not in normalized:
                normalized[key] = value

        return normalized

    def parse(
        self, file_path: str, progress_callback: Optional[ProgressCallback] = None
    ) -> List[ToolData]:
        """Parse CSV tool database."""
        tools = []

        try:
            path = Path(file_path)

            # Check if file exists
            if not path.exists():
                self.logger.warning(f"File does not exist: {file_path}")
                return []

            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                # Convert to list to get total rows
                rows = list(reader)
                total_rows = len(rows)

                for row_num, row in enumerate(rows, 1):
                    if self._check_cancelled():
                        break

                    # Normalize headers to handle case variations
                    normalized_row = self._normalize_headers(row)

                    # Parse tool data
                    tool = ToolData(
                        guid=normalized_row.get("guid", ""),
                        description=normalized_row.get("description", ""),
                        tool_type=normalized_row.get("tool_type", ""),
                        diameter=self._parse_float(normalized_row.get("diameter", 0)),
                        vendor=normalized_row.get("vendor", "IDC Woodcraft"),
                        product_id=normalized_row.get("product_id", ""),
                        unit=normalized_row.get("unit", "inches"),
                        geometry=self._parse_geometry(normalized_row),
                        start_values=self._parse_start_values(normalized_row),
                    )

                    tools.append(tool)

                    # Report progress
                    if progress_callback and total_rows > 0:
                        progress = min(row_num / total_rows, 1.0)
                        progress_callback.report(progress, f"Parsing tool {row_num}/{total_rows}")

            self.logger.info(f"Parsed {len(tools)} tools from CSV file")
            return tools

        except FileNotFoundError:
            self.logger.warning(f"File not found: {file_path}")
            return []
        except Exception as e:
            self.logger.error(f"Failed to parse CSV file: {e}")
            return []

    def _parse_float(self, value: str) -> float:
        """Parse float value from string."""
        try:
            return float(str(value).replace(",", ""))
        except (ValueError, AttributeError):
            return 0.0

    def _parse_geometry(self, row: dict) -> dict:
        """Parse geometry properties from row."""
        geometry = {}

        # Common geometry fields
        geometry_fields = {
            "DC": "diameter",
            "LB": "length",
            "NOF": "number_of_flutes",
            "OAL": "overall_length",
            "SHK": "shank_diameter",
        }

        for csv_field, prop_name in geometry_fields.items():
            if csv_field in row and row[csv_field]:
                geometry[prop_name] = self._parse_float(row[csv_field])

        return geometry

    def _parse_start_values(self, row: dict) -> dict:
        """Parse start values from row."""
        start_values = {}

        # Common start value fields
        start_fields = {
            "n": "rpm",
            "v_f": "feed_rate",
            "stepdown": "stepdown",
            "stepover": "stepover",
        }

        for csv_field, prop_name in start_fields.items():
            if csv_field in row and row[csv_field]:
                start_values[prop_name] = self._parse_float(row[csv_field])

        return start_values
