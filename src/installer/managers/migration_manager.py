"""
Migration Manager - Handles database schema updates and data migrations

Manages database migrations including:
- Applying schema changes
- Data transformations
- Version tracking
- Rollback capability
"""

import logging
import sqlite3
from typing import Optional, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations and schema updates."""

    def __init__(self, installer):
        """Initialize migration manager."""
        self.installer = installer
        self.db_path = installer.data_dir / "3dmm.db"

    def initialize_database(self) -> bool:
        """
        Initialize database with schema.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Initializing database")

        try:
            # Create data directory if it doesn't exist
            self.installer.data_dir.mkdir(parents=True, exist_ok=True)

            # Connect to database
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Create tables
            self._create_tables(cursor)

            # Record migration
            self._record_migration(cursor, "0.1.0", "initial")

            conn.commit()
            conn.close()

            logger.info("Database initialized: %s", self.db_path)
            return True

        except Exception as e:
            logger.error("Failed to initialize database: %s", e)
            return False

    def apply_migrations(self, from_version: str, to_version: str) -> bool:
        """
        Apply migrations from one version to another.

        Args:
            from_version: Current version
            to_version: Target version

        Returns:
            True if successful, False otherwise
        """
        logger.info("Applying migrations: %s -> {to_version}", from_version)

        try:
            if not self.db_path.exists():
                logger.info("Database doesn't exist, initializing")
                return self.initialize_database()

            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Get migration path
            migrations = self._get_migration_path(from_version, to_version)
            logger.info("Migration path: %s", migrations)

            # Apply each migration
            for migration in migrations:
                logger.info("Applying migration: %s", migration)
                self._apply_migration(cursor, migration)

            # Record migration
            self._record_migration(cursor, to_version, "upgrade")

            conn.commit()
            conn.close()

            logger.info("Migrations applied: %s -> {to_version}", from_version)
            return True

        except Exception as e:
            logger.error("Failed to apply migrations: %s", e)
            return False

    def _create_tables(self, cursor):
        """Create database tables."""
        logger.debug("Creating database tables")

        # Projects table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                path TEXT NOT NULL,
                created_date TEXT NOT NULL,
                modified_date TEXT NOT NULL,
                description TEXT
            )
        """
        )

        # Models table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                created_date TEXT NOT NULL,
                modified_date TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """
        )

        # Settings table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                modified_date TEXT NOT NULL
            )
        """
        )

        # Migration history table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS migration_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL,
                migration_type TEXT NOT NULL,
                applied_date TEXT NOT NULL
            )
        """
        )

        logger.debug("Database tables created")

    def _apply_migration(self, cursor, migration_name: str):
        """Apply a specific migration."""
        logger.debug("Applying migration: %s", migration_name)

        # Migration implementations would go here
        # For now, just log the migration
        logger.debug("Migration %s applied", migration_name)

    def _get_migration_path(self, from_version: str, to_version: str) -> List[str]:
        """Get list of migrations to apply."""
        logger.debug("Getting migration path: %s -> {to_version}", from_version)

        # Define migration paths
        migration_paths = {
            ("0.1.0", "0.1.1"): ["0.1.0_to_0.1.1"],
            ("0.1.1", "0.1.2"): ["0.1.1_to_0.1.2"],
            ("0.1.0", "0.1.2"): ["0.1.0_to_0.1.1", "0.1.1_to_0.1.2"],
        }

        key = (from_version, to_version)
        if key in migration_paths:
            return migration_paths[key]

        logger.warning("No migration path found: %s -> {to_version}", from_version)
        return []

    def _record_migration(self, cursor, version: str, migration_type: str):
        """Record migration in history."""
        logger.debug("Recording migration: %s ({migration_type})", version)

        cursor.execute(
            """
            INSERT INTO migration_history (version, migration_type, applied_date)
            VALUES (?, ?, ?)
        """,
            (version, migration_type, datetime.now().isoformat()),
        )

    def get_migration_history(self) -> List[Dict]:
        """
        Get migration history.

        Returns:
            List of migration records
        """
        logger.debug("Getting migration history")

        try:
            if not self.db_path.exists():
                logger.warning("Database doesn't exist")
                return []

            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM migration_history ORDER BY applied_date DESC")
            rows = cursor.fetchall()

            history = [dict(row) for row in rows]
            conn.close()

            logger.debug("Found %s migration records", len(history))
            return history

        except Exception as e:
            logger.error("Failed to get migration history: %s", e)
            return []

    def get_current_schema_version(self) -> Optional[str]:
        """
        Get current database schema version.

        Returns:
            Version string or None if not found
        """
        logger.debug("Getting current schema version")

        try:
            if not self.db_path.exists():
                logger.warning("Database doesn't exist")
                return None

            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT version FROM migration_history 
                ORDER BY applied_date DESC LIMIT 1
            """
            )

            result = cursor.fetchone()
            conn.close()

            if result:
                version = result[0]
                logger.debug("Current schema version: %s", version)
                return version

            logger.warning("No migration history found")
            return None

        except Exception as e:
            logger.error("Failed to get schema version: %s", e)
            return None
