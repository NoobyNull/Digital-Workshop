"""
Digital Workshop - Settings Migration Module

This module handles settings and database migration between different versions
of Digital Workshop, ensuring smooth upgrades without data loss.
"""

import json
import sqlite3
import shutil
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SettingsMigrator:
    """Handles migration of settings and data between application versions."""

    def __init__(self, app_name: str = "Digital Workshop") -> None:
        """Initialize the settings migrator.

        Args:
            app_name: The name of the application
        """
        from .path_manager import get_data_directory

        self.app_name = app_name
        self.current_version = "1.0.0"

        # Get application data directories using new path manager
        self.app_data_path = get_data_directory()
        self.old_app_data_path = self.app_data_path.parent / f"{app_name}_old"

        # Database paths
        self.current_db_path = self.app_data_path / "3dmm.db"
        self.old_db_path = self.old_app_data_path / "3dmm.db"

        # Settings paths
        self.settings_path = self.app_data_path / "settings.json"
        self.old_settings_path = self.old_app_data_path / "settings.json"

        logger.info("Settings migrator initialized for %s v{self.current_version}", app_name)

    def check_migration_needed(self) -> bool:
        """Check if migration is needed from a previous version.

        Returns:
            True if migration is needed, False otherwise
        """
        # Check if old data exists
        if not self.old_app_data_path.exists():
            logger.info("No previous installation found")
            return False

        # Check if current installation is new (no settings)
        if not self.settings_path.exists():
            logger.info("New installation detected, migration may be needed")
            return True

        # Check versions
        old_version = self._get_old_version()
        if old_version and old_version != self.current_version:
            logger.info("Version change detected: %s -> {self.current_version}", old_version)
            return True

        return False

    def _get_old_version(self) -> Optional[str]:
        """Get the version of the previous installation.

        Returns:
            The old version string or None if not found
        """
        try:
            if self.old_settings_path.exists():
                with open(self.old_settings_path, "r") as f:
                    settings = json.load(f)
                    return settings.get("version", "1.0.0")

            # Try to get version from database
            if self.old_db_path.exists():
                conn = sqlite3.connect(str(self.old_db_path))
                cursor = conn.cursor()
                cursor.execute("PRAGMA user_version")
                version = cursor.fetchone()[0]
                conn.close()
                return f"1.0.{version}"
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.warning("Failed to get old version: %s", e)

        return None

    def migrate_settings(self) -> bool:
        """Migrate settings from previous version.

        Returns:
            True if migration was successful, False otherwise
        """
        try:
            logger.info("Starting settings migration...")

            # Ensure app data directory exists
            self.app_data_path.mkdir(parents=True, exist_ok=True)

            # Migrate settings file
            if self.old_settings_path.exists():
                self._migrate_settings_file()

            # Migrate database
            if self.old_db_path.exists():
                self._migrate_database()

            # Migrate user data
            self._migrate_user_data()

            # Update version in settings
            self._update_version_info()

            logger.info("Settings migration completed successfully")
            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Settings migration failed: %s", e)
            return False

    def _migrate_settings_file(self) -> None:
        """Migrate the settings.json file."""
        logger.info("Migrating settings file...")

        try:
            with open(self.old_settings_path, "r") as f:
                old_settings = json.load(f)

            # Load current settings if they exist
            current_settings = {}
            if self.settings_path.exists():
                with open(self.settings_path, "r") as f:
                    current_settings = json.load(f)

            # Merge settings, preferring new defaults but keeping user customizations
            merged_settings = self._merge_settings(old_settings, current_settings)

            # Write merged settings
            with open(self.settings_path, "w") as f:
                json.dump(merged_settings, f, indent=2)

            logger.info("Settings file migrated successfully")

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to migrate settings file: %s", e)
            raise

    def _merge_settings(self, old_settings: Dict, current_settings: Dict) -> Dict:
        """Merge old settings with current defaults.

        Args:
            old_settings: Settings from previous version
            current_settings: Current default settings

        Returns:
            Merged settings dictionary
        """
        # Start with current defaults
        merged = current_settings.copy()

        # Preserve user customizations from old settings
        user_customizable_keys = [
            "window_geometry",
            "window_state",
            "recent_files",
            "viewer_settings",
            "library_settings",
            "theme",
            "language",
        ]

        for key in user_customizable_keys:
            if key in old_settings:
                merged[key] = old_settings[key]

        # Handle special cases for version-specific settings
        if "viewer_settings" in old_settings:
            # Migrate old viewer settings to new format if needed
            old_viewer = old_settings["viewer_settings"]
            if "render_mode" in old_viewer and "render_mode" not in merged.get(
                "viewer_settings", {}
            ):
                merged.setdefault("viewer_settings", {})["render_mode"] = old_viewer["render_mode"]

        return merged

    def _migrate_database(self) -> None:
        """Migrate the database from previous version."""
        logger.info("Migrating database...")

        try:
            # Check if we need to copy or upgrade the database
            if not self.current_db_path.exists():
                # Copy the entire database
                shutil.copy2(self.old_db_path, self.current_db_path)
                logger.info("Database copied successfully")
            else:
                # Upgrade existing database
                self._upgrade_database()

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to migrate database: %s", e)
            raise

    def _upgrade_database(self) -> None:
        """Upgrade the database schema if needed."""
        logger.info("Upgrading database schema...")

        try:
            conn = sqlite3.connect(str(self.current_db_path))
            cursor = conn.cursor()

            # Get current database version
            cursor.execute("PRAGMA user_version")
            current_db_version = cursor.fetchone()[0]

            # Perform version-specific upgrades
            if current_db_version < 1:
                # Upgrade to version 1: Add new columns
                cursor.execute(
                    """
                    ALTER TABLE models ADD COLUMN created_date TEXT
                """
                )
                cursor.execute(
                    """
                    ALTER TABLE models ADD COLUMN modified_date TEXT
                """
                )
                cursor.execute("PRAGMA user_version = 1")
                logger.info("Database upgraded to version 1")

            if current_db_version < 2:
                # Upgrade to version 2: Add new indexes
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_models_format ON models(format)
                """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_models_created_date ON models(created_date)
                """
                )
                cursor.execute("PRAGMA user_version = 2")
                logger.info("Database upgraded to version 2")

            conn.commit()
            conn.close()

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to upgrade database: %s", e)
            raise

    def _migrate_user_data(self) -> None:
        """Migrate user data files."""
        logger.info("Migrating user data...")

        try:
            # Migrate model files
            old_models_dir = self.old_app_data_path / "models"
            new_models_dir = self.app_data_path / "models"

            if old_models_dir.exists():
                new_models_dir.mkdir(parents=True, exist_ok=True)

                # Copy model files
                for file_path in old_models_dir.rglob("*"):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(old_models_dir)
                        dest_path = new_models_dir / relative_path
                        dest_path.parent.mkdir(parents=True, exist_ok=True)

                        # Only copy if destination doesn't exist
                        if not dest_path.exists():
                            shutil.copy2(file_path, dest_path)

            # Migrate other user data directories
            user_dirs = ["temp", "cache", "exports"]

            for dir_name in user_dirs:
                old_dir = self.old_app_data_path / dir_name
                new_dir = self.app_data_path / dir_name

                if old_dir.exists():
                    new_dir.mkdir(parents=True, exist_ok=True)

                    # Copy directory contents
                    for file_path in old_dir.rglob("*"):
                        if file_path.is_file():
                            relative_path = file_path.relative_to(old_dir)
                            dest_path = new_dir / relative_path
                            dest_path.parent.mkdir(parents=True, exist_ok=True)

                            if not dest_path.exists():
                                shutil.copy2(file_path, dest_path)

            logger.info("User data migrated successfully")

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to migrate user data: %s", e)
            raise

    def _update_version_info(self) -> None:
        """Update version information in settings."""
        try:
            # Load current settings
            settings = {}
            if self.settings_path.exists():
                with open(self.settings_path, "r") as f:
                    settings = json.load(f)

            # Update version information
            settings["version"] = self.current_version
            settings["migration_date"] = datetime.now().isoformat()
            settings["migration_successful"] = True

            # Save updated settings
            with open(self.settings_path, "w") as f:
                json.dump(settings, f, indent=2)

            logger.info("Version information updated")

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to update version info: %s", e)
            raise

    def cleanup_old_data(self) -> bool:
        """Clean up old installation data after successful migration.

        Returns:
            True if cleanup was successful, False otherwise
        """
        try:
            if self.old_app_data_path.exists():
                # Rename old directory with timestamp for backup
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.old_app_data_path.parent / f"{self.app_name}_backup_{timestamp}"

                shutil.move(str(self.old_app_data_path), str(backup_path))
                logger.info("Old data backed up to: %s", backup_path)

                # Optionally delete backup after confirmation
                # For now, we'll keep it for safety
                return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to cleanup old data: %s", e)
            return False

        return True

    def create_backup(self) -> bool:
        """Create a backup of current settings and data.

        Returns:
            True if backup was successful, False otherwise
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.app_data_path.parent / f"{self.app_name}_backup_{timestamp}"

            if self.app_data_path.exists():
                shutil.copytree(self.app_data_path, backup_path)
                logger.info("Backup created at: %s", backup_path)
                return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to create backup: %s", e)
            return False

        return False


def migrate_on_startup() -> bool:
    """Perform migration check and execution on application startup.

    Returns:
        True if migration was successful or not needed, False if it failed
    """
    try:
        migrator = SettingsMigrator()

        if migrator.check_migration_needed():
            logger.info("Migration required, starting process...")

            # Create backup before migration
            if not migrator.create_backup():
                logger.warning("Failed to create backup before migration")

            # Perform migration
            if migrator.migrate_settings():
                logger.info("Migration completed successfully")
                return True
            else:
                logger.error("Migration failed")
                return False
        else:
            logger.info("No migration needed")
            return True

    except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
        logger.error("Migration process failed: %s", e)
        return False
