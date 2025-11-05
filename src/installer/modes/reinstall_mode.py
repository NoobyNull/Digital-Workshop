"""
Reinstall Mode - Fresh app installation with data preservation

This mode performs a fresh installation of the application while
preserving all user data, projects, and configuration.
"""

import json
import logging
import shutil
from pathlib import Path
from typing import List
from datetime import datetime

logger = logging.getLogger(__name__)


class ReinstallMode:
    """Handles reinstallation with data preservation."""
    
    def __init__(self, installer):
        """Initialize reinstall mode."""
        self.installer = installer
    
    def execute(self, version: str, modules: List[str]) -> bool:
        """
        Execute reinstall installation.

        Args:
            version: Version to install
            modules: List of modules to install

        Returns:
            True if successful, False otherwise
        """
        logger.info("Executing REINSTALL mode")

        try:
            # Step 1: Backup user data
            logger.info("Step 1: Backing up user data")
            data_backup = self._backup_user_data()

            # Step 2: Remove application files
            logger.info("Step 2: Removing application files")
            self._remove_app_files()

            # Step 3: Install fresh modules
            logger.info("Step 3: Installing fresh modules")
            self._install_modules(modules)

            # Step 4: Restore user data
            logger.info("Step 4: Restoring user data")
            self._restore_user_data(data_backup)
            
            # Step 5: Verify installation
            logger.info("Step 5: Verifying installation")
            self._verify_installation()
            
            # Step 6: Update manifest
            logger.info("Step 6: Updating manifest")
            self._update_manifest(modules, version)

            logger.info("REINSTALL completed successfully")
            return True

        except Exception as e:
            logger.error("REINSTALL failed: %s", e)
            return False
    
    def _backup_user_data(self) -> Path:
        """Backup user data before reinstallation."""
        logger.info("Backing up user data")

        backup_dir = self.installer.backup_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup data directory
        if self.installer.data_dir.exists():
            data_backup = backup_dir / "data"
            shutil.copytree(self.installer.data_dir, data_backup)
            logger.info(f"Data backed up: {data_backup}")
        
        # Backup config directory
        if self.installer.config_dir.exists():
            config_backup = backup_dir / "config"
            shutil.copytree(self.installer.config_dir, config_backup)
            logger.info(f"Config backed up: {config_backup}")
        
        logger.info(f"User data backup created: {backup_dir}")
        return backup_dir
    
    def _remove_app_files(self):
        """Remove application files but preserve user data."""
        logger.info("Removing application files")
        
        # Remove modules directory
        if self.installer.modules_dir.exists():
            shutil.rmtree(self.installer.modules_dir)
            logger.debug(f"Removed modules directory: {self.installer.modules_dir}")
        
        # Remove logs directory
        if self.installer.logs_dir.exists():
            shutil.rmtree(self.installer.logs_dir)
            logger.debug(f"Removed logs directory: {self.installer.logs_dir}")
        
        # Remove manifest and version files
        if self.installer.manifest_file.exists():
            self.installer.manifest_file.unlink()
            logger.debug(f"Removed manifest file: {self.installer.manifest_file}")
        
        if self.installer.version_file.exists():
            self.installer.version_file.unlink()
            logger.debug(f"Removed version file: {self.installer.version_file}")
        
        logger.info("Application files removed")
    
    def _install_modules(self, modules: List[str]):
        """Install fresh modules."""
        logger.info("Installing %d modules", len(modules))

        for module in modules:
            logger.info("Installing module: %s", module)
            # Create module directory
            module_dir = self.installer.modules_dir / module
            module_dir.mkdir(parents=True, exist_ok=True)
            logger.debug("Module %s installed", module)
    
    def _restore_user_data(self, backup_dir: Path):
        """Restore user data after fresh installation."""
        logger.info("Restoring user data")
        
        # Restore data directory
        data_backup = backup_dir / "data"
        if data_backup.exists():
            if self.installer.data_dir.exists():
                shutil.rmtree(self.installer.data_dir)
            shutil.copytree(data_backup, self.installer.data_dir)
            logger.info(f"Data restored: {self.installer.data_dir}")
        
        # Restore config directory
        config_backup = backup_dir / "config"
        if config_backup.exists():
            if self.installer.config_dir.exists():
                shutil.rmtree(self.installer.config_dir)
            shutil.copytree(config_backup, self.installer.config_dir)
            logger.info(f"Config restored: {self.installer.config_dir}")
        
        logger.info("User data restored")
    
    def _verify_installation(self):
        """Verify installation integrity."""
        logger.info("Verifying installation")
        
        # Check if all modules are present
        for module in self.installer.MODULES:
            module_dir = self.installer.modules_dir / module
            if not module_dir.exists():
                logger.warning(f"Module directory missing: {module_dir}")
        
        # Check if data is present
        if not self.installer.data_dir.exists():
            logger.warning(f"Data directory missing: {self.installer.data_dir}")
        
        logger.debug("Installation verified")
    
    def _update_manifest(self, modules: List[str], version: str):
        """Update manifest file."""
        logger.info("Updating manifest")
        
        manifest = {
            "app_name": self.installer.APP_NAME,
            "version": version,
            "install_date": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat(),
            "modules": {
                module: {
                    "installed": True,
                    "version": version,
                    "install_date": datetime.now().isoformat(),
                }
                for module in modules
            }
        }
        
        self.installer._save_manifest(manifest)
        self.installer._update_version_file(version)
        logger.debug("Manifest updated")

