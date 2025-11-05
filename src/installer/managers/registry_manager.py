"""
Registry Manager - Tracks installed modules and versions

Manages the registry of installed modules including:
- Recording module installation
- Tracking module versions
- Recording installation dates
- Querying installation status
"""

import logging
import json
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class RegistryManager:
    """Manages registry of installed modules and versions."""
    
    def __init__(self, installer):
        """Initialize registry manager."""
        self.installer = installer
    
    def register_module(self, module_name: str, version: str) -> bool:
        """
        Register a module in the registry.
        
        Args:
            module_name: Name of the module
            version: Version of the module
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Registering module: {module_name} v{version}")
        
        try:
            manifest = self.installer._load_manifest()
            
            manifest['modules'][module_name] = {
                "installed": True,
                "version": version,
                "install_date": datetime.now().isoformat(),
            }
            
            self.installer._save_manifest(manifest)
            logger.info(f"Module registered: {module_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to register module: {e}")
            return False
    
    def unregister_module(self, module_name: str) -> bool:
        """
        Unregister a module from the registry.
        
        Args:
            module_name: Name of the module
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Unregistering module: {module_name}")
        
        try:
            manifest = self.installer._load_manifest()
            
            if module_name in manifest['modules']:
                del manifest['modules'][module_name]
                self.installer._save_manifest(manifest)
                logger.info(f"Module unregistered: {module_name}")
            else:
                logger.warning(f"Module not found in registry: {module_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister module: {e}")
            return False
    
    def get_module_version(self, module_name: str) -> Optional[str]:
        """
        Get the installed version of a module.
        
        Args:
            module_name: Name of the module
            
        Returns:
            Version string or None if not found
        """
        logger.debug(f"Getting module version: {module_name}")
        
        try:
            manifest = self.installer._load_manifest()
            modules = manifest.get('modules', {})
            
            if module_name not in modules:
                logger.warning(f"Module not found in registry: {module_name}")
                return None
            
            version = modules[module_name].get('version')
            logger.debug(f"Module version: {module_name} v{version}")
            
            return version
            
        except Exception as e:
            logger.error(f"Failed to get module version: {e}")
            return None
    
    def is_module_installed(self, module_name: str) -> bool:
        """
        Check if a module is installed.
        
        Args:
            module_name: Name of the module
            
        Returns:
            True if installed, False otherwise
        """
        logger.debug(f"Checking if module is installed: {module_name}")
        
        try:
            manifest = self.installer._load_manifest()
            modules = manifest.get('modules', {})
            
            is_installed = module_name in modules and modules[module_name].get('installed', False)
            logger.debug(f"Module installed: {module_name} = {is_installed}")
            
            return is_installed
            
        except Exception as e:
            logger.error(f"Failed to check module installation: {e}")
            return False
    
    def get_all_modules(self) -> Dict[str, Dict]:
        """
        Get all registered modules.
        
        Returns:
            Dict of all modules with their info
        """
        logger.debug("Getting all modules")
        
        try:
            manifest = self.installer._load_manifest()
            modules = manifest.get('modules', {})
            logger.debug(f"Found {len(modules)} modules")
            
            return modules
            
        except Exception as e:
            logger.error(f"Failed to get all modules: {e}")
            return {}
    
    def get_installed_modules(self) -> List[str]:
        """
        Get list of installed modules.
        
        Returns:
            List of installed module names
        """
        logger.debug("Getting installed modules")
        
        try:
            modules = self.get_all_modules()
            installed = [name for name, info in modules.items() if info.get('installed', False)]
            logger.debug(f"Found {len(installed)} installed modules: {installed}")
            
            return installed
            
        except Exception as e:
            logger.error(f"Failed to get installed modules: {e}")
            return []
    
    def update_module_version(self, module_name: str, version: str) -> bool:
        """
        Update the version of an installed module.
        
        Args:
            module_name: Name of the module
            version: New version
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Updating module version: {module_name} -> v{version}")
        
        try:
            manifest = self.installer._load_manifest()
            
            if module_name not in manifest['modules']:
                logger.error(f"Module not found in registry: {module_name}")
                return False
            
            manifest['modules'][module_name]['version'] = version
            manifest['modules'][module_name]['update_date'] = datetime.now().isoformat()
            
            self.installer._save_manifest(manifest)
            logger.info(f"Module version updated: {module_name} v{version}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update module version: {e}")
            return False
    
    def get_registry_info(self) -> Dict:
        """
        Get complete registry information.
        
        Returns:
            Dict with registry info
        """
        logger.debug("Getting registry info")
        
        try:
            manifest = self.installer._load_manifest()
            
            registry_info = {
                "app_version": manifest.get('version'),
                "install_date": manifest.get('install_date'),
                "last_update": manifest.get('last_update'),
                "total_modules": len(manifest.get('modules', {})),
                "installed_modules": len(self.get_installed_modules()),
                "modules": manifest.get('modules', {}),
            }
            
            logger.debug(f"Registry info: {registry_info}")
            return registry_info
            
        except Exception as e:
            logger.error(f"Failed to get registry info: {e}")
            return {}

