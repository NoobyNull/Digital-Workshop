"""
Tool database schema definition and initialization.
"""

import sqlite3
from pathlib import Path

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class ToolDatabaseSchema:
    """Manages the tool database schema initialization and migrations."""

    def __init__(self, db_path: str) -> None:
        """Initialize schema manager with database path."""
        self.db_path = Path(db_path)
        self.logger = logger

    def initialize_schema(self) -> bool:
        """Create all database tables if they don't exist. Alias for initialize_database."""
        return self.initialize_database()

    def initialize_database(self) -> bool:
        """Create all database tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Create Providers table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS providers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        description TEXT,
                        file_path TEXT,
                        format_type TEXT CHECK(format_type IN ('CSV', 'JSON', 'VTDB', 'TDB')),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create Tools table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tools (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        provider_id INTEGER NOT NULL,
                        guid TEXT,
                        description TEXT NOT NULL,
                        tool_type TEXT,
                        diameter REAL,
                        vendor TEXT,
                        product_id TEXT,
                        unit TEXT DEFAULT 'inches',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (provider_id) REFERENCES providers (id) ON DELETE CASCADE
                    )
                """
                )

                # Create ToolProperties table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tool_properties (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tool_id INTEGER NOT NULL,
                        property_name TEXT NOT NULL,
                        property_value TEXT,
                        property_type TEXT CHECK(property_type IN ('geometry', 'start_values', 'custom')),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (tool_id) REFERENCES tools (id) ON DELETE CASCADE
                    )
                """
                )

                # Create Preferences table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS preferences (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key TEXT UNIQUE NOT NULL,
                        value TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create indexes for performance
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_tools_provider_id ON tools(provider_id)"
                )
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_tools_guid ON tools(guid)")
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_tool_properties_tool_id ON tool_properties(tool_id)"
                )
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_preferences_key ON preferences(key)")

                conn.commit()
                self.logger.info("Database schema initialized successfully")
                return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to initialize database schema: %s", e)
            return False

    def get_version(self) -> int:
        """Get current database schema version."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA user_version")
                return cursor.fetchone()[0]
        except Exception:
            return 0

    def set_version(self, version: int) -> None:
        """Set database schema version."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA user_version = {version}")
                conn.commit()
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to set database version: %s", e)
