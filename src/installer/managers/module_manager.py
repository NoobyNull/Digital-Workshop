"""
Module Manager - Handles module installation, verification, and removal

Manages the lifecycle of individual modules including:
- Installation from compiled packages
- Verification of module integrity
- Removal of modules
- Module dependency tracking
"""

import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ModuleManager:
    """Manages module installation, verification, and removal."""
    
    def __init__(self, installer):
        """Initialize module manager."""
        self.installer = installer
    
    def install_module(self, module_name: str, module_path: Path, version: str) -> bool:
        """
        Install a module.
        
        Args:
            module_name: Name of the module
            module_path: Path to compiled module
            version: Version of the module
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Installing module: {module_name} v{version}")
        
        try:
            # Check if module path exists
            if not module_path.exists():
                logger.error(f"Module path not found: {module_path}")
                return False
            
            # Create module directory
            module_dir = self.installer.modules_dir / module_name
            if module_dir.exists():
                logger.warning(f"Module directory already exists: {module_dir}")
                shutil.rmtree(module_dir)
            
            # Copy module files
            shutil.copytree(module_path, module_dir)
            logger.info(f"Module installed: {module_dir}")
            
            # Update registry
            self._update_registry(module_name, version, "installed")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to install module {module_name}: {e}")
            return False
    
    def verify_module(self, module_name: str) -> bool:
        """
        Verify module integrity.
        
        Args:
            module_name: Name of the module
            
        Returns:
            True if module is valid, False otherwise
        """
        logger.info(f"Verifying module: {module_name}")
        
        try:
            module_dir = self.installer.modules_dir / module_name
            
            # Check if module directory exists
            if not module_dir.exists():
                logger.error(f"Module directory not found: {module_dir}")
                return False
            
            # Check if module has required files
            if not list(module_dir.glob("*")):
                logger.error(f"Module directory is empty: {module_dir}")
                return False
            
            logger.info(f"Module verified: {module_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to verify module {module_name}: {e}")
            return False
    
    def remove_module(self, module_name: str) -> bool:
        """
        Remove a module.
        
        Args:
            module_name: Name of the module
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Removing module: {module_name}")
        
        try:
            module_dir = self.installer.modules_dir / module_name
            
            if not module_dir.exists():
                logger.warning(f"Module directory not found: {module_dir}")
                return True
            
            # Remove module directory
            shutil.rmtree(module_dir)
            logger.info(f"Module removed: {module_dir}")
            
            # Update registry
            self._update_registry(module_name, None, "removed")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove module {module_name}: {e}")
            return False
    
    def get_module_info(self, module_name: str) -> Optional[Dict]:
        """
        Get module information.
        
        Args:
            module_name: Name of the module
            
        Returns:
            Dict with module info or None if not found
        """
        logger.debug(f"Getting module info: {module_name}")
        
        try:
            manifest = self.installer._load_manifest()
            modules = manifest.get('modules', {})
            
            if module_name not in modules:
                logger.warning(f"Module not found in manifest: {module_name}")
                return None
            
            return modules[module_name]
            
        except Exception as e:
            logger.error(f"Failed to get module info: {e}")
            return None
    
    def list_modules(self) -> List[str]:
        """
        List all installed modules.
        
        Returns:
            List of installed module names
        """
        logger.debug("Listing installed modules")
        
        try:
            if not self.installer.modules_dir.exists():
                return []
            
            modules = [d.name for d in self.installer.modules_dir.iterdir() if d.is_dir()]
            logger.debug(f"Found {len(modules)} modules: {modules}")
            
            return modules
            
        except Exception as e:
            logger.error(f"Failed to list modules: {e}")
            return []
    
    def _update_registry(self, module_name: str, version: Optional[str], status: str):
        """Update module registry."""
        logger.debug(f"Updating registry for {module_name}: {status}")
        
        try:
            manifest = self.installer._load_manifest()
            
            if status == "installed":
                manifest['modules'][module_name] = {
                    "installed": True,
                    "version": version,
                    "install_date": datetime.now().isoformat(),
                }
            elif status == "removed":
                if module_name in manifest['modules']:
                    del manifest['modules'][module_name]
            
            self.installer._save_manifest(manifest)
            logger.debug(f"Registry updated for {module_name}")
            
        except Exception as e:
            logger.error(f"Failed to update registry: {e}")

