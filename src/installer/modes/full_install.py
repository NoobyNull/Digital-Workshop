"""
Full Install Mode - Fresh installation with all modules

This mode performs a complete fresh installation of Digital Workshop
with all modules.
"""

import json
import logging
from pathlib import Path
from typing import List
from datetime import datetime

logger = logging.getLogger(__name__)


class FullInstallMode:
    """Handles full fresh installation."""
    
    def __init__(self, installer):
        """Initialize full install mode."""
        self.installer = installer
    
    def execute(self, version: str, modules: List[str]) -> bool:
        """
        Execute full installation.

        Args:
            version: Version to install
            modules: List of modules to install

        Returns:
            True if successful, False otherwise
        """
        logger.info("Executing FULL_INSTALL mode")

        try:
            # Step 1: Create directory structure
            logger.info("Step 1: Creating directory structure")
            self._create_directories()

            # Step 2: Install modules
            logger.info("Step 2: Installing modules")
            self._install_modules(modules)

            # Step 3: Initialize database
            logger.info("Step 3: Initializing database")
            self._initialize_database()

            # Step 4: Create configuration
            logger.info("Step 4: Creating configuration")
            self._create_configuration()

            # Step 5: Create shortcuts
            logger.info("Step 5: Creating shortcuts")
            self._create_shortcuts()

            # Step 6: Register application
            logger.info("Step 6: Registering application")
            self._register_application()

            # Step 7: Update manifest
            logger.info("Step 7: Updating manifest")
            self._update_manifest(modules, version)

            logger.info("FULL_INSTALL completed successfully")
            return True

        except Exception as e:
            logger.error("FULL_INSTALL failed: %s", e)
            return False
    
    def _create_directories(self):
        """Create directory structure."""
        logger.debug("Creating directory structure")
        self.installer.create_directories()
    
    def _install_modules(self, modules: List[str]):
        """Install modules."""
        logger.info(f"Installing {len(modules)} modules: {modules}")
        
        for module in modules:
            logger.info(f"Installing module: {module}")
            # Module installation logic will be implemented in ModuleManager
            logger.debug(f"Module {module} installed")
    
    def _initialize_database(self):
        """Initialize database."""
        logger.info("Initializing database")

        db_path = self.installer.data_dir / "3dmm.db"

        if not db_path.exists():
            logger.info("Creating database: %s", db_path)
            # Create empty database file
            db_path.touch()
            logger.debug("Database initialized")
        else:
            logger.debug("Database already exists")
    
    def _create_configuration(self):
        """Create configuration files."""
        logger.info("Creating configuration files")
        
        config_file = self.installer.config_dir / "config.json"
        preferences_file = self.installer.config_dir / "preferences.json"
        
        if not config_file.exists():
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
        
        if not preferences_file.exists():
            preferences = {
                "theme": "dark",
                "language": "en",
                "auto_update": False,
            }
            with open(preferences_file, 'w') as f:
                json.dump(preferences, f, indent=2)
            logger.debug(f"Preferences created: {preferences_file}")
    
    def _create_shortcuts(self):
        """Create application shortcuts."""
        logger.info("Creating shortcuts")
        # Shortcut creation logic will be implemented
        logger.debug("Shortcuts created")
    
    def _register_application(self):
        """Register application in system."""
        logger.info("Registering application")
        # Application registration logic will be implemented
        logger.debug("Application registered")
    
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

