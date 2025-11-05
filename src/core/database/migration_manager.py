"""
Database Versioning and Migration Management System.

This module provides comprehensive database versioning, migration management,
automatic schema updates, and rollback capabilities.
"""

import sqlite3
import os
import shutil
import json
import hashlib
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


class MigrationStatus(Enum):
    """Migration status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class Migration:
    """Database migration definition."""

    version: str
    name: str
    description: str
    up_sql: str
    down_sql: str
    checksum: str
    dependencies: List[str]
    created_at: str
    estimated_duration: float = 0.0


@dataclass
class MigrationResult:
    """Result of migration execution."""

    migration: Migration
    status: MigrationStatus
    start_time: float
    end_time: Optional[float]
    error_message: Optional[str]
    rows_affected: int
    backup_path: Optional[str]


class DatabaseVersion:
    """Database version information."""

    def __init__(self, major: int, minor: int, patch: int = 0) -> None:
        """
        Initialize database version.

        Args:
            major: Major version number
            minor: Minor version number
            patch: Patch version number
        """
        self.major = major
        self.minor = minor
        self.patch = patch

    def __str__(self) -> str:
        """Return version string."""
        return f"{self.major}.{self.minor}.{self.patch}"

    def __lt__(self, other) -> bool:
        """Compare versions."""
        if not isinstance(other, DatabaseVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch) < (
            other.major,
            other.minor,
            other.patch,
        )

    def __eq__(self, other) -> bool:
        """Compare versions for equality."""
        if not isinstance(other, DatabaseVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch) == (
            other.major,
            other.minor,
            other.patch,
        )

    def __le__(self, other) -> bool:
        """Compare versions for less than or equal."""
        return self < other or self == other

    def __gt__(self, other) -> bool:
        """Compare versions for greater than."""
        return not self <= other

    def __ge__(self, other) -> bool:
        """Compare versions for greater than or equal."""
        return not self < other

    @classmethod
    def from_string(cls, version_str: str) -> "DatabaseVersion":
        """
        Create version from string.

        Args:
            version_str: Version string in format "major.minor.patch"

        Returns:
            DatabaseVersion instance
        """
        parts = version_str.split(".")
        major = int(parts[0])
        minor = int(parts[1])
        patch = int(parts[2]) if len(parts) > 2 else 0
        return cls(major, minor, patch)


class MigrationManager:
    """Comprehensive database migration management system."""

    def __init__(self, db_path: str, migrations_dir: str = None, backup_dir: str = None) -> None:
        """
        Initialize migration manager.

        Args:
            db_path: Path to the SQLite database file
            migrations_dir: Directory containing migration scripts
            backup_dir: Directory for backup files
        """
        self.db_path = db_path
        self.migrations_dir = migrations_dir or os.path.join(os.path.dirname(db_path), "migrations")
        self.backup_dir = backup_dir or os.path.join(os.path.dirname(db_path), "backups")

        # Ensure directories exist
        os.makedirs(self.migrations_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

        # Migration registry
        self._migrations: Dict[str, Migration] = {}
        self._migration_results: List[MigrationResult] = []

        # Initialize database version tracking
        self._initialize_version_tracking()

    def _initialize_version_tracking(self) -> None:
        """Initialize database version tracking tables."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Create schema_migrations table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version TEXT NOT NULL UNIQUE,
                        name TEXT NOT NULL,
                        description TEXT,
                        checksum TEXT NOT NULL,
                        applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        execution_time REAL,
                        status TEXT NOT NULL DEFAULT 'completed',
                        error_message TEXT,
                        backup_path TEXT
                    )
                """
                )

                # Create migration_history table for detailed tracking
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS migration_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        migration_version TEXT NOT NULL,
                        operation TEXT NOT NULL, -- 'up' or 'down'
                        start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                        end_time DATETIME,
                        status TEXT NOT NULL,
                        error_message TEXT,
                        rows_affected INTEGER DEFAULT 0,
                        FOREIGN KEY (migration_version) REFERENCES schema_migrations (version)
                    )
                """
                )

                conn.commit()
                logger.debug("Database version tracking initialized")

        except sqlite3.Error as e:
            logger.error("Failed to initialize version tracking: %s", str(e))
            raise

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with migration-optimized settings."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)

        # Disable foreign key constraints during migrations
        conn.execute("PRAGMA foreign_keys = OFF")

        # Optimize for bulk operations
        conn.execute("PRAGMA synchronous = OFF")
        conn.execute("PRAGMA journal_mode = MEMORY")
        conn.execute("PRAGMA temp_store = MEMORY")

        return conn

    @log_function_call(logger)
    def discover_migrations(self) -> List[Migration]:
        """
        Discover and load migration scripts from the migrations directory.

        Returns:
            List of discovered migrations
        """
        migrations = []

        try:
            if not os.path.exists(self.migrations_dir):
                logger.info("Migrations directory %s does not exist", self.migrations_dir)
                return migrations

            for filename in os.listdir(self.migrations_dir):
                if filename.endswith(".sql") and filename.startswith("migration_"):
                    migration = self._load_migration_file(filename)
                    if migration:
                        migrations.append(migration)
                        self._migrations[migration.version] = migration

            # Sort migrations by version
            migrations.sort(key=lambda m: DatabaseVersion.from_string(m.version))

            logger.info("Discovered %s migrations", len(migrations))

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to discover migrations: %s", str(e))

        return migrations

    def _load_migration_file(self, filename: str) -> Optional[Migration]:
        """
        Load migration from file.

        Args:
            filename: Migration filename

        Returns:
            Migration object or None if loading failed
        """
        try:
            filepath = os.path.join(self.migrations_dir, filename)

            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse migration metadata and SQL
            parts = content.split("---")
            if len(parts) < 3:
                logger.error("Invalid migration format in %s", filename)
                return None

            # Parse metadata
            metadata = json.loads(parts[1].strip())

            # Extract SQL
            sql_parts = parts[2].split("---")
            up_sql = sql_parts[0].strip()
            down_sql = sql_parts[1].strip() if len(sql_parts) > 1 else ""

            # Calculate checksum
            checksum = hashlib.sha256(content.encode()).hexdigest()

            migration = Migration(
                version=metadata["version"],
                name=metadata["name"],
                description=metadata["description"],
                up_sql=up_sql,
                down_sql=down_sql,
                checksum=checksum,
                dependencies=metadata.get("dependencies", []),
                created_at=metadata.get("created_at", datetime.now().isoformat()),
                estimated_duration=metadata.get("estimated_duration", 0.0),
            )

            logger.debug("Loaded migration %s: {migration.name}", migration.version)
            return migration

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to load migration %s: {str(e)}", filename)
            return None

    @log_function_call(logger)
    def get_current_version(self) -> DatabaseVersion:
        """
        Get current database version.

        Returns:
            Current database version
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT version FROM schema_migrations
                    WHERE status = 'completed'
                    ORDER BY version DESC
                    LIMIT 1
                """
                )

                row = cursor.fetchone()
                if row:
                    return DatabaseVersion.from_string(row[0])
                else:
                    # No migrations applied, return initial version
                    return DatabaseVersion(0, 0, 0)

        except sqlite3.Error as e:
            logger.error("Failed to get current version: %s", str(e))
            return DatabaseVersion(0, 0, 0)

    @log_function_call(logger)
    def get_applied_migrations(self) -> List[Dict[str, Any]]:
        """
        Get list of applied migrations.

        Returns:
            List of applied migration information
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT * FROM schema_migrations
                    ORDER BY version ASC
                """
                )

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except sqlite3.Error as e:
            logger.error("Failed to get applied migrations: %s", str(e))
            return []

    @log_function_call(logger)
    def create_backup(self, backup_name: str = None) -> str:
        """
        Create database backup.

        Args:
            backup_name: Optional backup name

        Returns:
            Path to backup file
        """
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.db"

        backup_path = os.path.join(self.backup_dir, backup_name)

        try:
            shutil.copy2(self.db_path, backup_path)
            logger.info("Database backup created: %s", backup_path)
            return backup_path

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to create backup: %s", str(e))
            raise

    @log_function_call(logger)
    def migrate_to_version(
        self, target_version: str, create_backup: bool = True
    ) -> List[MigrationResult]:
        """
        Migrate database to target version.

        Args:
            target_version: Target database version
            create_backup: Whether to create backup before migration

        Returns:
            List of migration results
        """
        current_version = self.get_current_version()
        target_ver = DatabaseVersion.from_string(target_version)

        if current_version == target_ver:
            logger.info("Database already at version %s", target_version)
            return []

        # Discover migrations
        migrations = self.discover_migrations()

        # Determine migration direction and required migrations
        if target_ver > current_version:
            # Upgrade
            required_migrations = [
                m
                for m in migrations
                if DatabaseVersion.from_string(m.version) > current_version
                and DatabaseVersion.from_string(m.version) <= target_ver
            ]
            operation = "upgrade"
        else:
            # Downgrade
            required_migrations = [
                m
                for m in migrations
                if DatabaseVersion.from_string(m.version) <= current_version
                and DatabaseVersion.from_string(m.version) > target_ver
            ]
            required_migrations.reverse()  # Reverse order for downgrades
            operation = "downgrade"

        if not required_migrations:
            logger.warning("No migrations found for %s to version {target_version}", operation)
            return []

        # Create backup if requested
        backup_path = None
        if create_backup:
            backup_path = self.create_backup(f"{operation}_{target_version}_{int(time.time())}")

        results = []

        try:
            logger.info("Starting %s from {current_version} to {target_version}", operation)

            for migration in required_migrations:
                if operation == "upgrade":
                    result = self._execute_migration_up(migration)
                else:
                    result = self._execute_migration_down(migration)

                results.append(result)

                if result.status == MigrationStatus.FAILED:
                    logger.error("Migration %s failed: {result.error_message}", migration.version)
                    break
                else:
                    logger.info("Migration %s completed successfully", migration.version)

            if all(r.status == MigrationStatus.COMPLETED for r in results):
                logger.info("Successfully %sd to version {target_version}", operation)
            else:
                logger.error("%s to {target_version} failed", operation.capitalize())

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Migration process failed: %s", str(e))
            raise

        return results

    def _execute_migration_up(self, migration: Migration) -> MigrationResult:
        """
        Execute migration up operation.

        Args:
            migration: Migration to execute

        Returns:
            MigrationResult object
        """
        result = MigrationResult(
            migration=migration,
            status=MigrationStatus.RUNNING,
            start_time=time.time(),
            end_time=None,
            error_message=None,
            rows_affected=0,
            backup_path=None,
        )

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Record migration start
                cursor.execute(
                    """
                    INSERT INTO migration_history 
                    (migration_version, operation, status)
                    VALUES (?, ?, ?)
                """,
                    (migration.version, "up", MigrationStatus.RUNNING.value),
                )

                history_id = cursor.lastrowid

                # Execute migration SQL
                cursor.executescript(migration.up_sql)
                rows_affected = cursor.rowcount

                # Record successful migration
                cursor.execute(
                    """
                    UPDATE migration_history
                    SET end_time = CURRENT_TIMESTAMP, status = ?, rows_affected = ?
                    WHERE id = ?
                """,
                    (MigrationStatus.COMPLETED.value, rows_affected, history_id),
                )

                # Record in schema_migrations
                cursor.execute(
                    """
                    INSERT INTO schema_migrations 
                    (version, name, description, checksum, status, backup_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        migration.version,
                        migration.name,
                        migration.description,
                        migration.checksum,
                        MigrationStatus.COMPLETED.value,
                        result.backup_path,
                    ),
                )

                conn.commit()

                result.status = MigrationStatus.COMPLETED
                result.rows_affected = rows_affected

        except sqlite3.Error as e:
            result.status = MigrationStatus.FAILED
            result.error_message = str(e)
            logger.error("Migration up failed for %s: {str(e)}", migration.version)

        result.end_time = time.time()
        self._migration_results.append(result)

        return result

    def _execute_migration_down(self, migration: Migration) -> MigrationResult:
        """
        Execute migration down operation.

        Args:
            migration: Migration to rollback

        Returns:
            MigrationResult object
        """
        result = MigrationResult(
            migration=migration,
            status=MigrationStatus.RUNNING,
            start_time=time.time(),
            end_time=None,
            error_message=None,
            rows_affected=0,
            backup_path=None,
        )

        if not migration.down_sql:
            result.status = MigrationStatus.FAILED
            result.error_message = "No rollback SQL defined for this migration"
            return result

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Record migration start
                cursor.execute(
                    """
                    INSERT INTO migration_history 
                    (migration_version, operation, status)
                    VALUES (?, ?, ?)
                """,
                    (migration.version, "down", MigrationStatus.RUNNING.value),
                )

                history_id = cursor.lastrowid

                # Execute rollback SQL
                cursor.executescript(migration.down_sql)
                rows_affected = cursor.rowcount

                # Record successful rollback
                cursor.execute(
                    """
                    UPDATE migration_history
                    SET end_time = CURRENT_TIMESTAMP, status = ?, rows_affected = ?
                    WHERE id = ?
                """,
                    (MigrationStatus.ROLLED_BACK.value, rows_affected, history_id),
                )

                # Remove from schema_migrations
                cursor.execute(
                    """
                    DELETE FROM schema_migrations WHERE version = ?
                """,
                    (migration.version,),
                )

                conn.commit()

                result.status = MigrationStatus.ROLLED_BACK
                result.rows_affected = rows_affected

        except sqlite3.Error as e:
            result.status = MigrationStatus.FAILED
            result.error_message = str(e)
            logger.error("Migration down failed for %s: {str(e)}", migration.version)

        result.end_time = time.time()
        self._migration_results.append(result)

        return result

    @log_function_call(logger)
    def create_migration(
        self,
        version: str,
        name: str,
        description: str,
        up_sql: str,
        down_sql: str = "",
        dependencies: List[str] = None,
    ) -> str:
        """
        Create a new migration file.

        Args:
            version: Migration version (e.g., "1.2.3")
            name: Migration name
            description: Migration description
            up_sql: SQL to apply migration
            down_sql: SQL to rollback migration
            dependencies: List of dependency versions

        Returns:
            Path to created migration file
        """
        if dependencies is None:
            dependencies = []

        # Validate version format
        try:
            DatabaseVersion.from_string(version)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            raise ValueError(f"Invalid version format: {version}")

        # Check if migration already exists
        if version in self._migrations:
            raise ValueError(f"Migration version {version} already exists")

        # Create migration content
        metadata = {
            "version": version,
            "name": name,
            "description": description,
            "dependencies": dependencies,
            "created_at": datetime.now().isoformat(),
            "estimated_duration": 0.0,
        }

        content = f"""-- Migration: {name}
-- Version: {version}
-- Description: {description}
-- Created: {metadata['created_at']}

---METADATA---
{json.dumps(metadata, indent=2)}
---END_METADATA---

---UP---
{up_sql}
---END_UP---

---DOWN---
{down_sql}
---END_DOWN---
"""

        # Calculate checksum
        checksum = hashlib.sha256(content.encode()).hexdigest()
        metadata["checksum"] = checksum

        # Update content with checksum
        content = f"""-- Migration: {name}
-- Version: {version}
-- Description: {description}
-- Created: {metadata['created_at']}

---METADATA---
{json.dumps(metadata, indent=2)}
---END_METADATA---

---UP---
{up_sql}
---END_UP---

---DOWN---
{down_sql}
---END_DOWN---
"""

        # Write migration file
        filename = f"migration_{version}_{name.lower().replace(' ', '_')}.sql"
        filepath = os.path.join(self.migrations_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        # Create Migration object
        migration = Migration(
            version=version,
            name=name,
            description=description,
            up_sql=up_sql,
            down_sql=down_sql,
            checksum=checksum,
            dependencies=dependencies,
            created_at=metadata["created_at"],
        )

        self._migrations[version] = migration

        logger.info("Created migration %s: {name}", version)
        return filepath

    @log_function_call(logger)
    def validate_migrations(self) -> Dict[str, Any]:
        """
        Validate all migrations for consistency and integrity.

        Returns:
            Validation results dictionary
        """
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "migration_count": 0,
            "applied_count": 0,
            "pending_count": 0,
        }

        try:
            # Discover migrations
            migrations = self.discover_migrations()
            validation_results["migration_count"] = len(migrations)

            # Get applied migrations
            applied = self.get_applied_migrations()
            applied_versions = {m["version"] for m in applied}
            validation_results["applied_count"] = len(applied)
            validation_results["pending_count"] = len(migrations) - len(applied_versions)

            # Validate each migration
            for migration in migrations:
                # Check for duplicate versions
                version_count = sum(1 for m in migrations if m.version == migration.version)
                if version_count > 1:
                    validation_results["errors"].append(
                        f"Duplicate migration version: {migration.version}"
                    )
                    validation_results["valid"] = False

                # Check dependencies
                for dep in migration.dependencies:
                    if dep not in self._migrations:
                        validation_results["errors"].append(
                            f"Missing dependency {dep} for migration {migration.version}"
                        )
                        validation_results["valid"] = False

                # Check if applied migration has been modified
                if migration.version in applied_versions:
                    applied_migration = next(
                        m for m in applied if m["version"] == migration.version
                    )
                    if applied_migration["checksum"] != migration.checksum:
                        validation_results["errors"].append(
                            f"Applied migration {migration.version} has been modified"
                        )
                        validation_results["valid"] = False

            # Check for gaps in applied migrations
            applied_versions_sorted = sorted(
                applied_versions, key=lambda v: DatabaseVersion.from_string(v)
            )
            for i in range(len(applied_versions_sorted) - 1):
                current = DatabaseVersion.from_string(applied_versions_sorted[i])
                next_ver = DatabaseVersion.from_string(applied_versions_sorted[i + 1])

                # Check if there's a gap (more than patch increment)
                if next_ver.major == current.major and next_ver.minor == current.minor:
                    if next_ver.patch > current.patch + 1:
                        validation_results["warnings"].append(
                            f"Gap in applied migrations: {current} -> {next_ver}"
                        )
                elif next_ver.major == current.major:
                    if next_ver.minor > current.minor + 1:
                        validation_results["warnings"].append(
                            f"Gap in applied migrations: {current} -> {next_ver}"
                        )

            logger.info(
                f"Migration validation completed: {len(validation_results['errors'])} errors, "
                f"{len(validation_results['warnings'])} warnings"
            )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            validation_results["valid"] = False
            validation_results["errors"].append(f"Validation failed: {str(e)}")
            logger.error("Migration validation failed: %s", str(e))

        return validation_results

    @log_function_call(logger)
    def get_migration_status(self) -> Dict[str, Any]:
        """
        Get comprehensive migration status.

        Returns:
            Migration status dictionary
        """
        current_version = self.get_current_version()
        applied_migrations = self.get_applied_migrations()
        validation = self.validate_migrations()

        return {
            "current_version": str(current_version),
            "total_migrations": len(self._migrations),
            "applied_migrations": len(applied_migrations),
            "pending_migrations": len(self._migrations) - len(applied_migrations),
            "validation": validation,
            "last_migration": applied_migrations[-1] if applied_migrations else None,
            "migration_results": [asdict(result) for result in self._migration_results],
        }

    @log_function_call(logger)
    def restore_from_backup(self, backup_path: str) -> bool:
        """
        Restore database from backup.

        Args:
            backup_path: Path to backup file

        Returns:
            True if restore was successful
        """
        try:
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Backup file not found: {backup_path}")

            # Create backup of current state
            current_backup = self.create_backup(f"pre_restore_{int(time.time())}")

            # Restore from backup
            shutil.copy2(backup_path, self.db_path)

            # Reinitialize version tracking
            self._initialize_version_tracking()

            logger.info("Database restored from backup: %s", backup_path)
            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to restore from backup: %s", str(e))
            return False

    def cleanup_old_backups(self, keep_count: int = 10) -> int:
        """
        Clean up old backup files.

        Args:
            keep_count: Number of recent backups to keep

        Returns:
            Number of backups removed
        """
        try:
            backup_files = []
            for filename in os.listdir(self.backup_dir):
                if filename.endswith(".db"):
                    filepath = os.path.join(self.backup_dir, filename)
                    backup_files.append((filepath, os.path.getctime(filepath)))

            # Sort by creation time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)

            # Remove old backups
            removed_count = 0
            for filepath, _ in backup_files[keep_count:]:
                try:
                    os.remove(filepath)
                    removed_count += 1
                    logger.debug("Removed old backup: %s", filepath)
                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                    logger.warning("Failed to remove backup %s: {str(e)}", filepath)

            logger.info("Cleaned up %s old backups", removed_count)
            return removed_count

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to cleanup old backups: %s", str(e))
            return 0


# Migration template generator
def create_migration_template(version: str, name: str, description: str) -> str:
    """
    Create a migration template.

    Args:
        version: Migration version
        name: Migration name
        description: Migration description

    Returns:
        Migration template content
    """
    template = f"""-- Migration: {name}
-- Version: {version}
-- Description: {description}
-- Created: {datetime.now().isoformat()}

---METADATA---
{{
    "version": "{version}",
    "name": "{name}",
    "description": "{description}",
    "dependencies": [],
    "created_at": "{datetime.now().isoformat()}",
    "estimated_duration": 0.0,
    "checksum": ""
}}
---END_METADATA---

---UP---
-- Add your UP migration SQL here
-- Example:
-- CREATE TABLE example_table (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     name TEXT NOT NULL,
--     created_at DATETIME DEFAULT CURRENT_TIMESTAMP
-- );

-- CREATE INDEX idx_example_name ON example_table(name);
---END_UP---

---DOWN---
-- Add your DOWN migration SQL here (rollback)
-- Example:
-- DROP INDEX IF EXISTS idx_example_name;
-- DROP TABLE IF EXISTS example_table;
---END_DOWN---
"""
    return template
