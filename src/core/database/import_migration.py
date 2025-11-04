"""
Database migration utility for the Import System.

Provides functions to:
- Create import-related tables
- Extend models table with import columns
- Handle migration versioning

Usage:
    from src.core.database.import_migration import migrate_import_schema

    db_manager = get_database_manager()
    success = migrate_import_schema(db_manager)
"""

import re
import sqlite3
from typing import Optional, Tuple

from src.core.logging_config import get_logger
from src.core.database.import_schema import (
    get_all_schema_statements,
    get_models_table_extensions,
)


logger = get_logger(__name__)


def check_table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    """
    Check if a table exists in the database.

    Args:
        connection: Database connection
        table_name: Name of the table to check

    Returns:
        True if table exists, False otherwise
    """
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None


def check_column_exists(connection: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    """
    Check if a column exists in a table.

    Args:
        connection: Database connection
        table_name: Name of the table
        column_name: Name of the column

    Returns:
        True if column exists, False otherwise
    """
    # Validate table_name to prevent SQL injection (PRAGMA doesn't support parameters)
    if not table_name.isidentifier():
        raise ValueError(f"Invalid table name: {table_name}")

    cursor = connection.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def create_import_tables(connection: sqlite3.Connection) -> Tuple[bool, Optional[str]]:
    """
    Create import-related tables if they don't exist.

    Args:
        connection: Database connection

    Returns:
        Tuple of (success, error_message)
    """
    try:
        cursor = connection.cursor()

        # Get all schema statements
        statements = get_all_schema_statements()

        logger.info(f"Executing {len(statements)} schema statements...")

        for statement in statements:
            try:
                cursor.execute(statement)
                logger.debug(f"Executed: {statement[:50]}...")
            except sqlite3.OperationalError as e:
                # Expected error: table/index might already exist
                if "already exists" in str(e).lower():
                    logger.debug(f"Schema object already exists: {e}")
                else:
                    logger.warning(f"Operational error during schema creation: {e}")
            except sqlite3.Error as e:
                # Unexpected database error
                logger.error(f"Unexpected database error during schema creation: {e}")

        connection.commit()
        logger.info("Import tables created successfully")

        return True, None

    except Exception as e:
        error_msg = f"Failed to create import tables: {e}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg


def extend_models_table(connection: sqlite3.Connection) -> Tuple[bool, Optional[str]]:
    """
    Extend models table with import-related columns.

    Args:
        connection: Database connection

    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Check if models table exists
        if not check_table_exists(connection, "models"):
            logger.warning("Models table does not exist, skipping extension")
            return True, None

        cursor = connection.cursor()
        extensions = get_models_table_extensions()

        logger.info(f"Extending models table with {len(extensions)} columns...")

        added_columns = 0
        for statement in extensions:
            try:
                # Extract column name from ALTER TABLE statement using regex
                # Format: ALTER TABLE models ADD COLUMN column_name ...
                match = re.search(r"ADD\s+COLUMN\s+(\w+)", statement, re.IGNORECASE)
                if match:
                    column_name = match.group(1)

                    # Check if column already exists
                    if not check_column_exists(connection, "models", column_name):
                        cursor.execute(statement)
                        added_columns += 1
                        logger.debug(f"Added column: {column_name}")
                    else:
                        logger.debug(f"Column already exists: {column_name}")
                else:
                    logger.warning(f"Could not extract column name from: {statement}")

            except sqlite3.OperationalError as e:
                # Expected error: column might already exist
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    logger.debug(f"Column already exists: {e}")
                else:
                    logger.warning(f"Operational error adding column: {e}")
            except sqlite3.Error as e:
                # Unexpected database error
                logger.error(f"Unexpected database error adding column: {e}")

        connection.commit()
        logger.info(f"Models table extended successfully ({added_columns} columns added)")

        return True, None

    except Exception as e:
        error_msg = f"Failed to extend models table: {e}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg


def get_migration_version(connection: sqlite3.Connection) -> int:
    """
    Get current migration version from database.

    Args:
        connection: Database connection

    Returns:
        Current migration version (0 if no migrations table exists)
    """
    try:
        cursor = connection.cursor()

        # Check if migrations table exists
        if not check_table_exists(connection, "schema_migrations"):
            return 0

        cursor.execute("SELECT MAX(version) FROM schema_migrations WHERE component='import'")
        result = cursor.fetchone()
        return result[0] if result and result[0] else 0

    except Exception as e:
        logger.warning(f"Failed to get migration version: {e}")
        return 0


def set_migration_version(connection: sqlite3.Connection, version: int) -> bool:
    """
    Set migration version in database.

    Args:
        connection: Database connection
        version: Migration version to set

    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = connection.cursor()

        # Create migrations table if it doesn't exist
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component TEXT NOT NULL,
                version INTEGER NOT NULL,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        """
        )

        # Insert or update migration record (avoid duplicates)
        cursor.execute(
            """
            INSERT OR REPLACE INTO schema_migrations (component, version, description, applied_at)
            VALUES ('import', ?, 'Import system schema migration', CURRENT_TIMESTAMP)
        """,
            (version,),
        )

        connection.commit()
        return True

    except Exception as e:
        logger.error(f"Failed to set migration version: {e}", exc_info=True)
        return False


def migrate_import_schema(db_manager) -> Tuple[bool, Optional[str]]:
    """
    Migrate database schema for the import system.

    This is the main entry point for import schema migration.
    It will:
    1. Create import tables if they don't exist
    2. Extend models table with import columns
    3. Update migration version

    Args:
        db_manager: DatabaseManager instance

    Returns:
        Tuple of (success, error_message)
    """
    logger.info("Starting import schema migration...")
    connection = db_manager.conn

    # Check current migration version
    current_version = get_migration_version(connection)
    target_version = 1  # Current import schema version

    if current_version >= target_version:
        logger.info(f"Import schema already at version {current_version}")
        return True, None

    # Wrap all migration steps in a transaction
    try:
        # Step 1: Create import tables
        success, error = create_import_tables(connection)
        if not success:
            connection.rollback()
            return False, error

        # Step 2: Extend models table
        success, error = extend_models_table(connection)
        if not success:
            connection.rollback()
            return False, error

        # Step 3: Update migration version
        if not set_migration_version(connection, target_version):
            connection.rollback()
            return False, "Failed to update migration version"

        logger.info(f"Import schema migration completed successfully (v{target_version})")
        return True, None

    except Exception as e:
        connection.rollback()
        error_msg = f"Migration transaction failed: {e}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg


def verify_import_schema(db_manager) -> Tuple[bool, list]:
    """
    Verify that import schema is properly installed.

    Args:
        db_manager: DatabaseManager instance

    Returns:
        Tuple of (all_present, missing_tables)
    """
    try:
        connection = db_manager.conn

        required_tables = ["import_sessions", "import_files", "model_analysis"]

        missing_tables = []
        for table in required_tables:
            if not check_table_exists(connection, table):
                missing_tables.append(table)

        if missing_tables:
            logger.warning(f"Missing import tables: {missing_tables}")
            return False, missing_tables

        logger.info("Import schema verification passed")
        return True, []

    except Exception as e:
        logger.error(f"Schema verification failed: {e}", exc_info=True)
        return False, []


__all__ = [
    "migrate_import_schema",
    "verify_import_schema",
    "check_table_exists",
    "check_column_exists",
]
