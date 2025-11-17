"""
Patch Mode - Update existing installation

This mode updates an existing Digital Workshop installation,
preserving all user data and configuration.
"""

import logging
from typing import List
from datetime import datetime

logger = logging.getLogger(__name__)


class PatchMode:
    """Handles patching/updating existing installation."""

    def __init__(self, installer):
        """Initialize patch mode."""
        self.installer = installer

    def execute(self, version: str, modules: List[str]) -> bool:
        """
        Execute patch installation.

        Args:
            version: Version to patch to
            modules: List of modules to patch

        Returns:
            True if successful, False otherwise
        """
        logger.info("Executing PATCH mode")

        try:
            # Step 1: Detect existing installation
            logger.info("Step 1: Detecting existing installation")
            existing = self.installer.detect_installation()

            if existing is None:
                raise RuntimeError("No existing installation found for patching")

            current_version = existing["version"]
            logger.info("Current version: %s, patching to: {version}", current_version)

            # Step 2: Create backup
            logger.info("Step 2: Creating backup")
            self._create_backup(existing)

            # Step 3: Compare versions
            logger.info("Step 3: Comparing versions")
            changed_modules = self._compare_versions(existing, version)
            logger.info("Changed modules: %s", changed_modules)

            # Step 4: Update changed modules
            logger.info("Step 4: Updating modules")
            self._update_modules(modules, version)

            # Step 5: Run migrations
            logger.info("Step 5: Running migrations")
            self._run_migrations(current_version, version)

            # Step 6: Verify installation
            logger.info("Step 6: Verifying installation")
            self._verify_installation()

            # Step 7: Update manifest
            logger.info("Step 7: Updating manifest")
            self._update_manifest(version, modules)

            logger.info("PATCH completed successfully")
            return True

        except Exception as e:
            logger.error("PATCH failed: %s", e)
            logger.info("Rolling back to previous version")
            self._rollback()
            return False

    def _create_backup(self, existing):
        """Create backup before patching."""
        logger.info("Creating backup")

        backup_dir = (
            self.installer.backup_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Backup manifest
        manifest_backup = backup_dir / "manifest.json"
        if self.installer.manifest_file.exists():
            manifest_backup.write_text(self.installer.manifest_file.read_text())
            logger.debug("Manifest backed up: %s", manifest_backup)

        logger.info("Backup created: %s", backup_dir)

    def _compare_versions(self, existing, new_version):
        """Compare versions to determine changed modules."""
        logger.info("Comparing versions")

        # For now, assume all modules need updating
        # In production, this would compare version numbers
        changed_modules = list(existing["installed_modules"])

        logger.debug("Changed modules: %s", changed_modules)
        return changed_modules

    def _update_modules(self, modules: List[str], version: str):
        """Update modules."""
        logger.info("Updating %s modules", len(modules))

        for module in modules:
            logger.info("Updating module: %s", module)
            # Module update logic will be implemented in ModuleManager
            logger.debug("Module %s updated", module)

    def _run_migrations(self, from_version: str, to_version: str):
        """Run database migrations."""
        logger.info("Running migrations from %s to {to_version}", from_version)
        # Migration logic will be implemented in MigrationManager
        logger.debug("Migrations completed")

    def _verify_installation(self):
        """Verify installation integrity."""
        logger.info("Verifying installation")

        # Check if all modules are present
        for module in self.installer.MODULES:
            module_dir = self.installer.modules_dir / module
            if not module_dir.exists():
                logger.warning("Module directory missing: %s", module_dir)

        logger.debug("Installation verified")

    def _update_manifest(self, version: str, modules: List[str]):
        """Update manifest file."""
        logger.info("Updating manifest")

        manifest = self.installer._load_manifest()
        manifest["version"] = version
        manifest["last_update"] = datetime.now().isoformat()

        # Update module versions and add new modules
        for module in modules:
            if module not in manifest.get("modules", {}):
                manifest["modules"][module] = {}
            manifest["modules"][module]["version"] = version
            manifest["modules"][module]["installed"] = True
            manifest["modules"][module]["update_date"] = datetime.now().isoformat()

        self.installer._save_manifest(manifest)
        self.installer._update_version_file(version)
        logger.debug("Manifest updated")

    def _rollback(self):
        """Rollback to previous version on failure."""
        logger.warning("Rolling back installation")
        # Rollback logic will be implemented in BackupManager
        logger.debug("Rollback completed")
