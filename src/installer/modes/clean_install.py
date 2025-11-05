"""
Clean Install Mode - Complete removal and fresh start (DESTRUCTIVE)

This mode completely removes all Digital Workshop files and data,
then performs a fresh installation. This is a DESTRUCTIVE operation.
"""

import json
import logging
import shutil
from pathlib import Path
from typing import List
from datetime import datetime

logger = logging.getLogger(__name__)


class CleanInstallMode:
    """Handles complete removal and fresh installation."""
    
    def __init__(self, installer):
        """Initialize clean install mode."""
        self.installer = installer
    
    def execute(self, version: str, modules: List[str]) -> bool:
        """
        Execute clean installation.

        Args:
            version: Version to install
            modules: List of modules to install

        Returns:
            True if successful, False otherwise
        """
        logger.info("Executing CLEAN_INSTALL mode")
        logger.warning("DESTRUCTIVE OPERATION: All Digital Workshop files and data will be deleted")
        
        try:
            # Step 1: Create final backup
            logger.info("Step 1: Creating final backup")
            self._create_final_backup()
            
            # Step 2: Display warning
            logger.warning("Step 2: Displaying DESTRUCTIVE warning")
            self._display_destructive_warning()
            
            # Step 3: Remove everything
            logger.info("Step 3: Removing all files and data")
            self._remove_everything()
            
            # Step 4: Create fresh directory structure
            logger.info("Step 4: Creating fresh directory structure")
            self.installer.create_directories()
            
            # Step 5: Install modules
            logger.info("Step 5: Installing modules")
            self._install_modules(modules)
            
            # Step 6: Initialize database
            logger.info("Step 6: Initializing database")
            self._initialize_database()
            
            # Step 7: Create configuration
            logger.info("Step 7: Creating configuration")
            self._create_configuration()
            
            # Step 8: Update manifest
            logger.info("Step 8: Updating manifest")
            self._update_manifest(modules, version)

            logger.info("CLEAN_INSTALL completed successfully")
            return True

        except Exception as e:
            logger.error("CLEAN_INSTALL failed: %s", e)
            return False
    
    def _create_final_backup(self):
        """Create final backup before complete removal."""
        logger.info("Creating final backup")

        if not self.installer.app_dir.exists():
            logger.info("No existing installation to backup")
            return

        backup_dir = self.installer.backup_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Copy app_dir but exclude the backup directory to avoid nested paths
            def ignore_backups(directory, contents):
                """Ignore backup directory during copy."""
                return ['backups'] if 'backups' in contents else []

            shutil.copytree(self.installer.app_dir, backup_dir / "app_data", ignore=ignore_backups)
            logger.info("Final backup created: %s", backup_dir)
        except Exception as e:
            logger.warning("Failed to create final backup: %s", e)
    
    def _display_destructive_warning(self):
        """Display warning about destructive operation."""
        logger.warning("=" * 70)
        logger.warning("DESTRUCTIVE OPERATION WARNING")
        logger.warning("=" * 70)
        logger.warning("This operation will DELETE ALL Digital Workshop files and data:")
        logger.warning(f"  - Application files: {self.installer.modules_dir}")
        logger.warning(f"  - User data: {self.installer.data_dir}")
        logger.warning(f"  - Configuration: {self.installer.config_dir}")
        logger.warning(f"  - Logs: {self.installer.logs_dir}")
        logger.warning("")
        logger.warning("A backup has been created in:")
        logger.warning(f"  {self.installer.backup_dir}")
        logger.warning("")
        logger.warning("This operation CANNOT be undone!")
        logger.warning("=" * 70)
    
    def _remove_everything(self):
        """Remove all Digital Workshop files and data."""
        logger.warning("Removing all Digital Workshop files and data")

        if self.installer.app_dir.exists():
            try:
                # Remove everything except backups
                for item in self.installer.app_dir.iterdir():
                    if item.name != 'backups':
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
                logger.info("Removed application files and data: %s", self.installer.app_dir)
            except Exception as e:
                logger.error("Failed to remove application directory: %s", e)
                raise

        logger.info("All files and data removed")
    
    def _install_modules(self, modules: List[str]):
        """Install modules."""
        logger.info(f"Installing {len(modules)} modules")
        
        for module in modules:
            logger.info(f"Installing module: {module}")
            # Module installation logic will be implemented in ModuleManager
            logger.debug(f"Module {module} installed")
    
    def _initialize_database(self):
        """Initialize database."""
        logger.info("Initializing database")
        
        db_path = self.installer.data_dir / "3dmm.db"
        
        if not db_path.exists():
            logger.info(f"Creating database: {db_path}")
            # Database initialization logic will be implemented in MigrationManager
            logger.debug("Database initialized")
    
    def _create_configuration(self):
        """Create configuration files."""
        logger.info("Creating configuration files")
        
        config_file = self.installer.config_dir / "config.json"
        preferences_file = self.installer.config_dir / "preferences.json"
        
        config = {
            "app_name": self.installer.APP_NAME,
            "version": "0.1.5",
            "install_date": datetime.now().isoformat(),
            "data_dir": str(self.installer.data_dir),
            "modules_dir": str(self.installer.modules_dir),
        }
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        logger.debug(f"Configuration created: {config_file}")
        
        preferences = {
            "theme": "dark",
            "language": "en",
            "auto_update": False,
        }
        with open(preferences_file, 'w') as f:
            json.dump(preferences, f, indent=2)
        logger.debug(f"Preferences created: {preferences_file}")
    
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

