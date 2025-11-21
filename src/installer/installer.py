"""
Main Installer class for Digital Workshop

Handles installation detection, mode selection, and execution.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class Installer:
    """Main installer class for Digital Workshop."""

    # Installation directory structure
    APP_NAME = "Digital Workshop"
    MODULES = ["core", "pyside6", "vtk", "opencv", "numpy"]

    def __init__(self):
        """Initialize the installer."""
        self.app_dir = Path.home() / "AppData" / "Local" / "DigitalWorkshop"
        self.modules_dir = self.app_dir / "modules"
        self.data_dir = self.app_dir / "data"
        self.config_dir = self.app_dir / "config"
        self.backup_dir = self.app_dir / "backups"
        self.logs_dir = self.app_dir / "logs"
        self.manifest_file = self.app_dir / "manifest.json"
        self.version_file = self.app_dir / "version.txt"

        logger.info(f"Installer initialized")
        logger.info("App directory: %s", self.app_dir)

    def detect_installation(self) -> Optional[Dict]:
        """
        Detect existing installation.

        Returns:
            Dict with installation info if exists, None otherwise
        """
        logger.info("Detecting existing installation...")

        if not self.version_file.exists():
            logger.info("No existing installation found")
            return None

        try:
            version = self.version_file.read_text().strip()
            manifest = self._load_manifest()

            installation_info = {
                "exists": True,
                "version": version,
                "manifest": manifest,
                "installed_modules": list(manifest.get("modules", {}).keys()),
                "install_date": manifest.get("install_date"),
                "last_update": manifest.get("last_update"),
            }

            logger.info("Existing installation found: v%s", version)
            logger.info("Installed modules: %s", installation_info["installed_modules"])

            return installation_info

        except Exception as e:
            logger.error("Error detecting installation: %s", e)
            return None

    def select_mode(self, existing_installation: Optional[Dict]) -> str:
        """
        Select installation mode based on existing installation.

        Args:
            existing_installation: Result from detect_installation()

        Returns:
            Installation mode: 'full_install', 'patch', 'reinstall', or 'clean_install'
        """
        if existing_installation is None:
            logger.info("No existing installation - selecting FULL_INSTALL mode")
            return "full_install"

        logger.info("Existing installation found - selecting PATCH mode")
        return "patch"

    def create_directories(self):
        """Create installation directory structure."""
        logger.info("Creating installation directories...")

        directories = [
            self.app_dir,
            self.modules_dir,
            self.data_dir,
            self.config_dir,
            self.backup_dir,
            self.logs_dir,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug("Created/verified directory: %s", directory)

        logger.info("Directory structure created")

    def _load_manifest(self) -> Dict:
        """Load manifest file."""
        if not self.manifest_file.exists():
            return {"modules": {}}

        try:
            with open(self.manifest_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Error loading manifest: %s", e)
            return {"modules": {}}

    def _save_manifest(self, manifest: Dict):
        """Save manifest file."""
        try:
            with open(self.manifest_file, "w") as f:
                json.dump(manifest, f, indent=2)
            logger.debug("Manifest saved")
        except Exception as e:
            logger.error("Error saving manifest: %s", e)
            raise

    def _update_version_file(self, version: str):
        """Update version file."""
        try:
            self.version_file.write_text(version)
            logger.debug("Version file updated: %s", version)
        except Exception as e:
            logger.error("Error updating version file: %s", e)
            raise

    def install(self, mode: str, version: str, modules: List[str] = None):
        """
        Execute installation.

        Args:
            mode: Installation mode ('full_install', 'patch', 'reinstall', 'clean_install')
            version: Version to install
            modules: List of modules to install (defaults to all)
        """
        if modules is None:
            modules = self.MODULES

        logger.info("Starting %s installation (v{version})", mode)
        logger.info("Modules to install: %s", modules)

        try:
            # Create directories
            self.create_directories()

            # Import and execute mode-specific installer
            if mode == "full_install":
                from .modes.full_install import FullInstallMode

                installer = FullInstallMode(self)
                installer.execute(modules, version)

            elif mode == "patch":
                from .modes.patch_mode import PatchMode

                installer = PatchMode(self)
                installer.execute(version, modules or [])

            elif mode == "reinstall":
                from .modes.reinstall_mode import ReinstallMode

                installer = ReinstallMode(self)
                installer.execute(modules, version)

            elif mode == "clean_install":
                from .modes.clean_install import CleanInstallMode

                installer = CleanInstallMode(self)
                installer.execute(modules, version)

            else:
                raise ValueError(f"Unknown installation mode: {mode}")

            logger.info("%s installation completed successfully", mode)

        except Exception as e:
            logger.error("Installation failed: %s", e)
            raise

    def get_installation_info(self) -> Dict:
        """Get current installation information."""
        existing = self.detect_installation()

        if existing is None:
            return {
                "installed": False,
                "version": None,
                "modules": [],
            }

        return {
            "installed": True,
            "version": existing["version"],
            "modules": existing["installed_modules"],
            "install_date": existing.get("install_date"),
            "last_update": existing.get("last_update"),
        }
