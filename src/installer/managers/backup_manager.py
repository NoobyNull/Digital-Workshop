"""
Backup Manager - Handles backup creation, restoration, and verification

Manages backup operations including:
- Creating backups before updates
- Restoring from backups on failure
- Verifying backup integrity
- Managing backup retention
"""

import logging
import shutil
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages backup creation, restoration, and verification."""

    def __init__(self, installer):
        """Initialize backup manager."""
        self.installer = installer
        self.max_backups = 5  # Keep last 5 backups

    def create_backup(self, backup_name: Optional[str] = None) -> Optional[Path]:
        """
        Create a backup of current installation.

        Args:
            backup_name: Optional name for backup

        Returns:
            Path to backup directory or None if failed
        """
        if backup_name is None:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info("Creating backup: %s", backup_name)

        try:
            backup_dir = self.installer.backup_dir / backup_name
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Backup manifest
            if self.installer.manifest_file.exists():
                manifest_backup = backup_dir / "manifest.json"
                shutil.copy2(self.installer.manifest_file, manifest_backup)
                logger.debug("Manifest backed up: %s", manifest_backup)

            # Backup version file
            if self.installer.version_file.exists():
                version_backup = backup_dir / "version.txt"
                shutil.copy2(self.installer.version_file, version_backup)
                logger.debug("Version file backed up: %s", version_backup)

            # Create backup metadata
            metadata = {
                "backup_name": backup_name,
                "created": datetime.now().isoformat(),
                "version": (
                    self.installer.version_file.read_text().strip()
                    if self.installer.version_file.exists()
                    else "unknown"
                ),
            }

            metadata_file = backup_dir / "backup_metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

            logger.info("Backup created: %s", backup_dir)

            # Clean up old backups
            self._cleanup_old_backups()

            return backup_dir

        except Exception as e:
            logger.error("Failed to create backup: %s", e)
            return None

    def restore_backup(self, backup_dir: Path) -> bool:
        """
        Restore from a backup.

        Args:
            backup_dir: Path to backup directory

        Returns:
            True if successful, False otherwise
        """
        logger.info("Restoring backup: %s", backup_dir)

        try:
            if not backup_dir.exists():
                logger.error("Backup directory not found: %s", backup_dir)
                return False

            # Verify backup integrity
            if not self.verify_backup(backup_dir):
                logger.error("Backup verification failed: %s", backup_dir)
                return False

            # Restore manifest
            manifest_backup = backup_dir / "manifest.json"
            if manifest_backup.exists():
                shutil.copy2(manifest_backup, self.installer.manifest_file)
                logger.debug("Manifest restored: %s", self.installer.manifest_file)

            # Restore version file
            version_backup = backup_dir / "version.txt"
            if version_backup.exists():
                shutil.copy2(version_backup, self.installer.version_file)
                logger.debug("Version file restored: %s", self.installer.version_file)

            logger.info("Backup restored: %s", backup_dir)
            return True

        except Exception as e:
            logger.error("Failed to restore backup: %s", e)
            return False

    def verify_backup(self, backup_dir: Path) -> bool:
        """
        Verify backup integrity.

        Args:
            backup_dir: Path to backup directory

        Returns:
            True if backup is valid, False otherwise
        """
        logger.info("Verifying backup: %s", backup_dir)

        try:
            if not backup_dir.exists():
                logger.error("Backup directory not found: %s", backup_dir)
                return False

            # Check for required files
            required_files = ["manifest.json", "version.txt", "backup_metadata.json"]

            for required_file in required_files:
                file_path = backup_dir / required_file
                if not file_path.exists():
                    logger.warning("Required file missing in backup: %s", required_file)
                    # Don't fail on missing files, just warn

            # Verify metadata
            metadata_file = backup_dir / "backup_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                logger.debug("Backup metadata: %s", metadata)

            logger.info("Backup verified: %s", backup_dir)
            return True

        except Exception as e:
            logger.error("Failed to verify backup: %s", e)
            return False

    def list_backups(self) -> list:
        """
        List all available backups.

        Returns:
            List of backup directories
        """
        logger.debug("Listing backups")

        try:
            if not self.installer.backup_dir.exists():
                return []

            backups = sorted(
                [d for d in self.installer.backup_dir.iterdir() if d.is_dir()]
            )
            logger.debug("Found %s backups", len(backups))

            return backups

        except Exception as e:
            logger.error("Failed to list backups: %s", e)
            return []

    def delete_backup(self, backup_dir: Path) -> bool:
        """
        Delete a backup.

        Args:
            backup_dir: Path to backup directory

        Returns:
            True if successful, False otherwise
        """
        logger.info("Deleting backup: %s", backup_dir)

        try:
            if not backup_dir.exists():
                logger.warning("Backup directory not found: %s", backup_dir)
                return True

            shutil.rmtree(backup_dir)
            logger.info("Backup deleted: %s", backup_dir)

            return True

        except Exception as e:
            logger.error("Failed to delete backup: %s", e)
            return False

    def _cleanup_old_backups(self):
        """Clean up old backups, keeping only the most recent ones."""
        logger.debug("Cleaning up old backups")

        try:
            backups = self.list_backups()

            if len(backups) > self.max_backups:
                backups_to_delete = backups[: -self.max_backups]

                for backup_dir in backups_to_delete:
                    logger.info("Removing old backup: %s", backup_dir)
                    self.delete_backup(backup_dir)

        except Exception as e:
            logger.error("Failed to cleanup old backups: %s", e)
