"""
Nuclear Reset - Complete application data destruction.

This module provides a NUCLEAR RESET that destroys ALL application data:
- Database files
- QSettings (Windows Registry)
- Cache directories
- Config directories
- Log directories
- Thumbnail storage
- Temp files
- All AppData directories
- Everything related to Digital Workshop

WARNING: This is IRREVERSIBLE. All data will be permanently deleted.
"""

import os
import shutil
import platform
from pathlib import Path
from typing import List, Dict, Any
from PySide6.QtCore import QSettings, QStandardPaths

from src.core.logging_config import get_logger
from src.core.path_manager import PathManager
from src.core.version_manager import get_app_name, get_organization_name

logger = get_logger(__name__)


class NuclearReset:
    """Handles complete destruction of all application data."""

    def __init__(self):
        """Initialize nuclear reset handler."""
        self.logger = get_logger(__name__)
        self.path_manager = PathManager()
        self.system = platform.system()
        self.app_name = get_app_name()
        self.org_name = get_organization_name()
        
        # Track what will be deleted
        self.deletion_targets: List[Path] = []
        self.registry_targets: List[str] = []
        
    def scan_all_targets(self) -> Dict[str, Any]:
        """
        Scan and identify ALL targets for deletion.
        
        Returns:
            Dictionary with all targets and their sizes
        """
        self.logger.info("Scanning for all application data...")
        
        targets = {
            "directories": [],
            "registry_keys": [],
            "total_size_mb": 0.0,
            "file_count": 0,
        }
        
        # 1. Main AppData directories
        app_data_dirs = self._get_all_appdata_directories()
        for directory in app_data_dirs:
            if directory.exists():
                size_mb, file_count = self._calculate_directory_size(directory)
                targets["directories"].append({
                    "path": str(directory),
                    "size_mb": size_mb,
                    "file_count": file_count,
                    "type": "AppData"
                })
                targets["total_size_mb"] += size_mb
                targets["file_count"] += file_count
        
        # 2. Thumbnail storage (might be in different location)
        thumbnail_dirs = self._get_thumbnail_directories()
        for directory in thumbnail_dirs:
            if directory.exists():
                size_mb, file_count = self._calculate_directory_size(directory)
                targets["directories"].append({
                    "path": str(directory),
                    "size_mb": size_mb,
                    "file_count": file_count,
                    "type": "Thumbnails"
                })
                targets["total_size_mb"] += size_mb
                targets["file_count"] += file_count
        
        # 3. Temp directories
        temp_dirs = self._get_temp_directories()
        for directory in temp_dirs:
            if directory.exists():
                size_mb, file_count = self._calculate_directory_size(directory)
                targets["directories"].append({
                    "path": str(directory),
                    "size_mb": size_mb,
                    "file_count": file_count,
                    "type": "Temp"
                })
                targets["total_size_mb"] += size_mb
                targets["file_count"] += file_count
        
        # 4. QSettings / Registry keys
        if self.system == "Windows":
            targets["registry_keys"] = [
                f"HKEY_CURRENT_USER\\Software\\{self.org_name}",
                f"HKEY_CURRENT_USER\\Software\\{self.org_name}\\{self.app_name}",
            ]
        
        self.logger.info(
            f"Scan complete: {len(targets['directories'])} directories, "
            f"{targets['file_count']} files, {targets['total_size_mb']:.2f} MB"
        )
        
        return targets
    
    def execute_nuclear_reset(self, create_backup: bool = True) -> Dict[str, Any]:
        """
        Execute the NUCLEAR RESET - destroy everything.

        Args:
            create_backup: If True, create a final backup before destruction

        Returns:
            Dictionary with results of the operation
        """
        self.logger.warning("=" * 80)
        self.logger.warning("NUCLEAR RESET INITIATED")
        self.logger.warning("=" * 80)

        results = {
            "success": False,
            "backup_created": False,
            "backup_path": None,
            "directories_deleted": 0,
            "files_deleted": 0,
            "registry_cleared": False,
            "errors": [],
        }

        try:
            # Step 1: Create backup if requested
            if create_backup:
                backup_path = self._create_final_backup()
                if backup_path:
                    results["backup_created"] = True
                    results["backup_path"] = str(backup_path)
                    self.logger.info(f"Backup created: {backup_path}")

            # Step 2: Close all log handlers to release file locks
            self.logger.warning("Closing log handlers...")
            self._close_log_handlers()

            # Step 3: Clear QSettings / Registry
            self.logger.warning("Clearing QSettings / Registry...")
            if self._clear_qsettings():
                results["registry_cleared"] = True
                self.logger.info("QSettings / Registry cleared")

            # Step 4: Delete all directories
            self.logger.warning("Deleting all application directories...")
            dirs_deleted, files_deleted, errors = self._delete_all_directories()
            results["directories_deleted"] = dirs_deleted
            results["files_deleted"] = files_deleted
            results["errors"].extend(errors)

            # Step 5: Clean temp files
            self.logger.warning("Cleaning temporary files...")
            self._clean_temp_files()

            results["success"] = True
            self.logger.warning("=" * 80)
            self.logger.warning("NUCLEAR RESET COMPLETE")
            self.logger.warning("=" * 80)

        except Exception as e:
            self.logger.error(f"Nuclear reset failed: {e}", exc_info=True)
            results["errors"].append(str(e))
            results["success"] = False

        return results
    
    def _get_all_appdata_directories(self) -> List[Path]:
        """Get all AppData directories used by the application."""
        directories = []

        # Use PathManager to get the correct paths based on installation type
        # PathManager automatically detects RAW (source) vs installed and uses:
        # - RAW: %LOCALAPPDATA%\DigitalWorkshop-Dev\
        # - Installed: %LOCALAPPDATA%\DigitalWorkshop\
        try:
            directories.extend([
                self.path_manager.get_cache_directory().parent,  # Get base app directory
                self.path_manager.get_log_directory(),
                self.path_manager.get_data_directory(),
                self.path_manager.get_config_directory(),
            ])
        except Exception as e:
            self.logger.warning(f"Failed to get directories from PathManager: {e}")

        # Also check for alternate names (in case of migration)
        if self.system == "Windows":
            local_appdata = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
            roaming_appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))

            # Check both LOCALAPPDATA and APPDATA
            for base_dir in [local_appdata, roaming_appdata]:
                # Check for both regular and -Dev versions
                for suffix in ["", "-Dev"]:
                    app_dir = base_dir / f"{self.app_name}{suffix}"
                    if app_dir.exists() and app_dir not in directories:
                        directories.append(app_dir)

                # Also check for "DigitalWorkshop" (in case app_name is different)
                dw_dir = base_dir / "DigitalWorkshop"
                if dw_dir.exists() and dw_dir not in directories:
                    directories.append(dw_dir)
        
        elif self.system == "Darwin":  # macOS
            app_support = Path.home() / "Library" / "Application Support" / self.app_name
            if app_support.exists():
                directories.append(app_support)
        
        else:  # Linux
            local_share = Path.home() / ".local" / "share" / self.app_name
            if local_share.exists():
                directories.append(local_share)
        
        # Add directories from PathManager
        try:
            directories.extend([
                self.path_manager.get_cache_directory(),
                self.path_manager.get_log_directory(),
                self.path_manager.get_data_directory(),
                self.path_manager.get_config_directory(),
            ])
        except Exception as e:
            self.logger.warning(f"Failed to get some directories from PathManager: {e}")
        
        # Remove duplicates
        unique_dirs = []
        for d in directories:
            if d not in unique_dirs:
                unique_dirs.append(d)
        
        return unique_dirs
    
    def _get_thumbnail_directories(self) -> List[Path]:
        """Get thumbnail storage directories."""
        directories = []
        
        if self.system == "Windows":
            appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
            thumb_dir = appdata / "3DModelManager" / "thumbnails"
            if thumb_dir.exists():
                directories.append(thumb_dir)
        
        return directories
    
    def _get_temp_directories(self) -> List[Path]:
        """Get temporary directories used by the application."""
        directories = []
        
        import tempfile
        temp_base = Path(tempfile.gettempdir())
        
        # Check for various temp directory patterns
        patterns = [
            "digital_workshop_*",
            "dw_*",
            "DigitalWorkshop_*",
        ]
        
        for pattern in patterns:
            for temp_dir in temp_base.glob(pattern):
                if temp_dir.is_dir():
                    directories.append(temp_dir)

        return directories

    def _calculate_directory_size(self, directory: Path) -> tuple[float, int]:
        """
        Calculate total size and file count of a directory.

        Args:
            directory: Directory to calculate

        Returns:
            Tuple of (size_in_mb, file_count)
        """
        total_size = 0
        file_count = 0

        try:
            for item in directory.rglob("*"):
                if item.is_file():
                    total_size += item.stat().st_size
                    file_count += 1
        except Exception as e:
            self.logger.warning(f"Failed to calculate size for {directory}: {e}")

        size_mb = total_size / (1024 * 1024)
        return size_mb, file_count

    def _create_final_backup(self) -> Path:
        """
        Create a final backup before nuclear reset.

        Returns:
            Path to backup directory
        """
        from datetime import datetime

        try:
            # Create backup in user's Documents folder (safer than AppData)
            if self.system == "Windows":
                docs_path = Path(os.environ.get("USERPROFILE", Path.home())) / "Documents"
            else:
                docs_path = Path.home() / "Documents"

            backup_base = docs_path / "DigitalWorkshop_Backups"
            backup_base.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = backup_base / f"nuclear_reset_backup_{timestamp}"
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Copy all AppData directories to backup
            app_data_dirs = self._get_all_appdata_directories()
            for source_dir in app_data_dirs:
                if source_dir.exists():
                    dest_dir = backup_dir / source_dir.name
                    try:
                        shutil.copytree(source_dir, dest_dir, ignore_dangling_symlinks=True)
                        self.logger.info(f"Backed up: {source_dir} -> {dest_dir}")
                    except Exception as e:
                        self.logger.warning(f"Failed to backup {source_dir}: {e}")

            self.logger.info(f"Final backup created: {backup_dir}")
            return backup_dir

        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}", exc_info=True)
            return None

    def _clear_qsettings(self) -> bool:
        """
        Clear ALL QSettings / Registry entries.

        Returns:
            True if successful
        """
        try:
            settings = QSettings()

            # Clear ALL keys
            settings.clear()
            settings.sync()

            self.logger.info("QSettings cleared")

            # On Windows, also try to delete registry keys directly
            if self.system == "Windows":
                try:
                    import winreg

                    # Try to delete organization key (this deletes all app keys under it)
                    try:
                        winreg.DeleteKey(
                            winreg.HKEY_CURRENT_USER,
                            f"Software\\{self.org_name}"
                        )
                        self.logger.info(f"Deleted registry key: Software\\{self.org_name}")
                    except FileNotFoundError:
                        pass  # Key doesn't exist
                    except Exception as e:
                        self.logger.warning(f"Failed to delete registry key: {e}")

                except ImportError:
                    self.logger.warning("winreg not available, skipping direct registry deletion")

            return True

        except Exception as e:
            self.logger.error(f"Failed to clear QSettings: {e}", exc_info=True)
            return False

    def _delete_all_directories(self) -> tuple[int, int, List[str]]:
        """
        Delete all application directories.

        Returns:
            Tuple of (directories_deleted, files_deleted, errors)
        """
        dirs_deleted = 0
        files_deleted = 0
        errors = []

        # Get all directories to delete
        all_dirs = []
        all_dirs.extend(self._get_all_appdata_directories())
        all_dirs.extend(self._get_thumbnail_directories())
        all_dirs.extend(self._get_temp_directories())

        # Remove duplicates
        unique_dirs = list(set(all_dirs))

        for directory in unique_dirs:
            if directory.exists():
                try:
                    # Count files before deletion
                    _, file_count = self._calculate_directory_size(directory)

                    # Delete the directory
                    shutil.rmtree(directory)

                    dirs_deleted += 1
                    files_deleted += file_count
                    self.logger.info(f"Deleted: {directory} ({file_count} files)")

                except Exception as e:
                    error_msg = f"Failed to delete {directory}: {e}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)

        return dirs_deleted, files_deleted, errors

    def _clean_temp_files(self) -> None:
        """Clean any remaining temp files."""
        try:
            import tempfile
            temp_base = Path(tempfile.gettempdir())

            # Clean VTK temp files
            for vtk_temp in temp_base.glob("vtk*"):
                try:
                    if vtk_temp.is_file():
                        vtk_temp.unlink()
                    elif vtk_temp.is_dir():
                        shutil.rmtree(vtk_temp)
                except Exception as e:
                    self.logger.debug(f"Failed to clean {vtk_temp}: {e}")

            self.logger.info("Temp files cleaned")

        except Exception as e:
            self.logger.warning(f"Failed to clean temp files: {e}")

    def _close_log_handlers(self) -> None:
        """Close all log handlers to release file locks."""
        try:
            import logging

            # Get the root logger
            root_logger = logging.getLogger()

            # Close all handlers
            for handler in root_logger.handlers[:]:
                try:
                    handler.close()
                    root_logger.removeHandler(handler)
                except Exception as e:
                    # Can't log this since we're closing loggers
                    pass

            # Also close handlers for our logger
            for handler in self.logger.handlers[:]:
                try:
                    handler.close()
                    self.logger.removeHandler(handler)
                except Exception as e:
                    pass

        except Exception as e:
            # Can't log this since we're closing loggers
            pass


def create_nuclear_reset_handler() -> NuclearReset:
    """
    Factory function to create a nuclear reset handler.

    Returns:
        NuclearReset instance
    """
    return NuclearReset()
