"""
Tool database repository for CRUD operations.
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.core.logging_config import get_logger
from .tool_database_schema import ToolDatabaseSchema

logger = get_logger(__name__)


class ToolDatabaseRepository:
    """Repository for tool database operations."""

    def __init__(self, db_path: str):
        """Initialize repository with database path."""
        self.db_path = Path(db_path)
        self.schema = ToolDatabaseSchema(str(self.db_path))
        self.logger = logger
        self.schema.initialize_database()

    def add_tool(
        self,
        provider_id: int,
        guid: str = "",
        description: str = "",
        tool_type: str = "",
        diameter: float = 0.0,
        vendor: str = "",
        product_id: str = "",
        unit: str = "inches",
        geometry_data: Dict[str, Any] = None,
        start_values: Dict[str, Any] = None,
        tool_data: Dict[str, Any] = None,
    ) -> Optional[int]:
        """Add a new tool to the database."""
        try:
            # Support both old dictionary style and new parameter style
            if tool_data is None:
                tool_data = {
                    "guid": guid,
                    "description": description,
                    "tool_type": tool_type,
                    "diameter": diameter,
                    "vendor": vendor,
                    "product_id": product_id,
                    "unit": unit,
                    "geometry": geometry_data or {},
                    "start_values": start_values or {},
                }

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Insert tool
                cursor.execute(
                    """
                    INSERT INTO tools (provider_id, guid, description, tool_type, diameter, vendor, product_id, unit)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        provider_id,
                        tool_data.get("guid"),
                        tool_data.get("description"),
                        tool_data.get("tool_type"),
                        tool_data.get("diameter"),
                        tool_data.get("vendor"),
                        tool_data.get("product_id"),
                        tool_data.get("unit", "inches"),
                    ),
                )

                tool_id = cursor.lastrowid

                # Insert tool properties
                for prop_name, prop_value in tool_data.get("properties", {}).items():
                    cursor.execute(
                        """
                        INSERT INTO tool_properties (tool_id, property_name, property_value, property_type)
                        VALUES (?, ?, ?, ?)
                    """,
                        (
                            tool_id,
                            prop_name,
                            str(prop_value),
                            tool_data.get("property_types", {}).get(
                                prop_name, "custom"
                            ),
                        ),
                    )

                conn.commit()
                self.logger.info(
                    f"Added tool: {tool_data.get('description')} (ID: {tool_id})"
                )
                return tool_id

        except Exception as e:
            self.logger.error(f"Failed to add tool: {e}")
            return None

    def get_tools_by_provider(self, provider_id: int) -> List[Dict[str, Any]]:
        """Get all tools for a specific provider."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT t.*, p.name as provider_name
                    FROM tools t
                    JOIN providers p ON t.provider_id = p.id
                    WHERE t.provider_id = ?
                    ORDER BY t.description
                """,
                    (provider_id,),
                )

                tools = []
                for row in cursor.fetchall():
                    tool = dict(row)

                    # Get tool properties
                    cursor.execute(
                        """
                        SELECT property_name, property_value, property_type
                        FROM tool_properties
                        WHERE tool_id = ?
                    """,
                        (tool["id"],),
                    )

                    properties = {}
                    for prop_row in cursor.fetchall():
                        if prop_row["property_type"] == "geometry":
                            if "geometry" not in properties:
                                properties["geometry"] = {}
                            properties["geometry"][prop_row["property_name"]] = (
                                prop_row["property_value"]
                            )
                        elif prop_row["property_type"] == "start_values":
                            if "start_values" not in properties:
                                properties["start_values"] = {}
                            properties["start_values"][prop_row["property_name"]] = (
                                prop_row["property_value"]
                            )
                        else:
                            properties[prop_row["property_name"]] = prop_row[
                                "property_value"
                            ]

                    tool["properties"] = properties
                    tools.append(tool)

                return tools

        except Exception as e:
            self.logger.error(f"Failed to get tools for provider {provider_id}: {e}")
            return []

    def search_tools(
        self, query: str, provider_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Search for tools by description."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                sql = """
                    SELECT t.*, p.name as provider_name
                    FROM tools t
                    JOIN providers p ON t.provider_id = p.id
                    WHERE t.description LIKE ?
                """
                params = [f"%{query}%"]

                if provider_id:
                    sql += " AND t.provider_id = ?"
                    params.append(provider_id)

                sql += " ORDER BY t.description"

                cursor.execute(sql, params)

                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            self.logger.error(f"Failed to search tools: {e}")
            return []

    def delete_tool(self, tool_id: int) -> bool:
        """Delete a tool from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tools WHERE id = ?", (tool_id,))
                conn.commit()

                success = cursor.rowcount > 0
                if success:
                    self.logger.info(f"Deleted tool ID: {tool_id}")
                return success

        except Exception as e:
            self.logger.error(f"Failed to delete tool {tool_id}: {e}")
            return False

    def list_tools(self) -> List[Dict[str, Any]]:
        """Get all tools from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tools ORDER BY description")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to list tools: {e}")
            return []

    def get_tool(self, tool_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific tool by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tools WHERE id = ?", (tool_id,))
                result = cursor.fetchone()
                return dict(result) if result else None
        except Exception as e:
            self.logger.error(f"Failed to get tool {tool_id}: {e}")
            return None

    def get_tool_by_id(self, tool_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific tool by ID. Alias for get_tool."""
        return self.get_tool(tool_id)

    def update_tool(self, tool_id: int, **kwargs) -> bool:
        """Update tool fields."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                allowed_fields = [
                    "guid",
                    "description",
                    "tool_type",
                    "diameter",
                    "vendor",
                    "product_id",
                    "unit",
                ]
                update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}

                if not update_fields:
                    return False

                set_clause = ", ".join([f"{k} = ?" for k in update_fields.keys()])
                values = list(update_fields.values()) + [tool_id]

                cursor.execute(f"UPDATE tools SET {set_clause} WHERE id = ?", values)
                conn.commit()
                self.logger.info(f"Updated tool {tool_id}")
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Failed to update tool {tool_id}: {e}")
            return False

    def list_tools_for_provider(self, provider_id: int) -> List[Dict[str, Any]]:
        """Get all tools for a specific provider."""
        return self.get_tools_by_provider(provider_id)

    def search_tools(
        self, tool_type: str = None, vendor: str = None, **kwargs
    ) -> List[Dict[str, Any]]:
        """Search tools by type or vendor."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                sql = "SELECT * FROM tools WHERE 1=1"
                params = []

                if tool_type:
                    sql += " AND tool_type = ?"
                    params.append(tool_type)
                if vendor:
                    sql += " AND vendor = ?"
                    params.append(vendor)

                sql += " ORDER BY description"
                cursor.execute(sql, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to search tools: {e}")
            return []

    def search_tools_by_description(self, description: str) -> List[Dict[str, Any]]:
        """Search tools by description."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM tools WHERE description LIKE ? ORDER BY description",
                    (f"%{description}%",),
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to search tools by description: {e}")
            return []

    def filter_by_diameter(
        self, min_diameter: float = 0.0, max_diameter: float = float("inf")
    ) -> List[Dict[str, Any]]:
        """Filter tools by diameter range."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM tools WHERE diameter >= ? AND diameter <= ? ORDER BY diameter",
                    (min_diameter, max_diameter),
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to filter tools by diameter: {e}")
            return []

    def add_tool_properties(self, tool_id: int, properties: Dict[str, Any]) -> bool:
        """Add custom properties to a tool with proper type preservation."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for prop_name, prop_value in properties.items():
                    # Serialize property value as JSON to preserve type information
                    property_value_json = json.dumps(prop_value)
                    cursor.execute(
                        """
                        INSERT INTO tool_properties (tool_id, property_name, property_value, property_type)
                        VALUES (?, ?, ?, ?)
                    """,
                        (tool_id, prop_name, property_value_json, "custom"),
                    )
                conn.commit()
                self.logger.info(f"Added properties to tool {tool_id}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to add tool properties: {e}")
            return False

    def get_tool_properties(self, tool_id: int) -> Optional[Dict[str, Any]]:
        """Get all properties for a tool with proper type deserialization."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT property_name, property_value FROM tool_properties WHERE tool_id = ?",
                    (tool_id,),
                )
                properties = {}
                for row in cursor.fetchall():
                    try:
                        # Deserialize JSON to restore original type
                        properties[row["property_name"]] = json.loads(
                            row["property_value"]
                        )
                    except (json.JSONDecodeError, TypeError):
                        # If not valid JSON, keep as string
                        properties[row["property_name"]] = row["property_value"]
                return properties if properties else None
        except Exception as e:
            self.logger.error(f"Failed to get tool properties: {e}")
            return None

    def get_tool_count_by_provider(self, provider_id: int) -> int:
        """Get count of tools for a provider."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM tools WHERE provider_id = ?", (provider_id,)
                )
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            self.logger.error(f"Failed to get tool count: {e}")
            return 0
