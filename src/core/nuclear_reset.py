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

import logging
import os
import platform
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from PySide6.QtCore import QSettings

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
                targets["directories"].append(
                    {
                        "path": str(directory),
                        "size_mb": size_mb,
                        "file_count": file_count,
                        "type": "AppData",
                    }
                )
                targets["total_size_mb"] += size_mb
                targets["file_count"] += file_count

        # 2. Thumbnail storage (might be in different location)
        thumbnail_dirs = self._get_thumbnail_directories()
        for directory in thumbnail_dirs:
            if directory.exists():
                size_mb, file_count = self._calculate_directory_size(directory)
                targets["directories"].append(
                    {
                        "path": str(directory),
                        "size_mb": size_mb,
                        "file_count": file_count,
                        "type": "Thumbnails",
                    }
                )
                targets["total_size_mb"] += size_mb
                targets["file_count"] += file_count

        # 3. Temp directories
        temp_dirs = self._get_temp_directories()
        for directory in temp_dirs:
            if directory.exists():
                size_mb, file_count = self._calculate_directory_size(directory)
                targets["directories"].append(
                    {
                        "path": str(directory),
                        "size_mb": size_mb,
                        "file_count": file_count,
                        "type": "Temp",
                    }
                )
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
                    self.logger.info("Backup created: %s", backup_path)

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
            self.logger.error("Nuclear reset failed: %s", e, exc_info=True)
            results["errors"].append(str(e))
            results["success"] = False

        return results

    def _get_all_appdata_directories(self) -> List[Path]:
        """Get all AppData directories used by the application.

        This is intentionally aggressive: it returns every directory tree that
        is known to contain *application-owned* data, including migration
        backups under AppData. User content (model files, project folders,
        etc.) is *not* included here.
        """
        directories: List[Path] = []

        # Use PathManager to get the correct paths based on installation type
        # PathManager automatically detects RAW (source) vs installed and uses:
        # - RAW: %LOCALAPPDATA%\DigitalWorkshop-Dev\
        # - Installed: %LOCALAPPDATA%\DigitalWorkshop\
        try:
            # Base application directory (parent of cache/data/log/config)
            base_dir = self.path_manager.get_cache_directory().parent
            directories.append(base_dir)

            # Explicit well-known subdirectories
            directories.extend(
                [
                    self.path_manager.get_cache_directory(),
                    self.path_manager.get_log_directory(),
                    self.path_manager.get_data_directory(),
                    self.path_manager.get_config_directory(),
                ]
            )
        except Exception as exc:
            self.logger.warning("Failed to get directories from PathManager: %s", exc)

        # Also check for alternate names and backup directories (in case of migration)
        if self.system == "Windows":
            local_appdata = Path(
                os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
            )
            roaming_appdata = Path(
                os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")
            )

            # Check both LOCALAPPDATA and APPDATA
            for base_dir in (local_appdata, roaming_appdata):
                # Check for both regular and -Dev versions
                for suffix in ("", "-Dev"):
                    app_dir = base_dir / f"{self.app_name}{suffix}"
                    if app_dir.exists():
                        directories.append(app_dir)

                    # Migration/installer backups created by SettingsMigrator and installers
                    # e.g. DigitalWorkshop_backup_YYYYMMDD_HHMMSS
                    for backup_dir in base_dir.glob(f"{self.app_name}{suffix}_backup_*"):
                        if backup_dir.is_dir():
                            directories.append(backup_dir)

                # Also check for plain "DigitalWorkshop" root (defensive)
                dw_dir = base_dir / "DigitalWorkshop"
                if dw_dir.exists():
                    directories.append(dw_dir)

        elif self.system == "Darwin":  # macOS
            app_support = Path.home() / "Library" / "Application Support" / self.app_name
            if app_support.exists():
                directories.append(app_support)

        else:  # Linux and other Unix-like systems
            local_share = Path.home() / ".local" / "share" / self.app_name
            if local_share.exists():
                directories.append(local_share)

        # Remove duplicates while preserving order
        unique_dirs: List[Path] = []
        for path in directories:
            if path not in unique_dirs:
                unique_dirs.append(path)

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
        directories: List[Path] = []

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
        """Calculate total size and file count of a directory.

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
        except Exception as exc:  # pragma: no cover - best-effort diagnostics
            self.logger.warning(
                "Failed to calculate size for %s: %s", directory, exc
            )

        size_mb = total_size / (1024 * 1024)
        return size_mb, file_count

    def _create_final_backup(self) -> Path:
        """Create a final backup before nuclear reset.

        Returns:
            Path to backup directory
        """
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
                        self.logger.info("Backed up: %s -> %s", source_dir, dest_dir)
                    except Exception as exc:  # pragma: no cover - best-effort diagnostics
                        self.logger.warning("Failed to backup %s: %s", source_dir, exc)

            self.logger.info("Final backup created: %s", backup_dir)
            return backup_dir

        except Exception as exc:  # pragma: no cover - best-effort diagnostics
            self.logger.error("Failed to create backup: %s", exc, exc_info=True)
            return None

    def _clear_qsettings(self) -> bool:
        """Clear ALL QSettings / Registry entries.

        Returns:
            True if successful.
        """
        try:
            settings = QSettings()

            # Clear ALL keys for the current org/app pair.
            settings.clear()
            settings.sync()

            self.logger.info("QSettings cleared")

            # On Windows, also delete the backing registry tree explicitly.
            # QSettings.clear() in the background NUKE process may point at
            # a default Qt org/app instead of our real keys, so we remove
            # HKCU\Software\<org_name> recursively as a safety net.
            if self.system == "Windows":
                try:
                    import winreg

                    def _delete_tree(root_key, sub_key: str) -> None:
                        """Recursively delete a registry key tree."""
                        try:
                            handle = winreg.OpenKey(
                                root_key,
                                sub_key,
                                0,
                                winreg.KEY_READ | winreg.KEY_WRITE,
                            )
                        except FileNotFoundError:
                            return

                        try:
                            while True:
                                try:
                                    child = winreg.EnumKey(handle, 0)
                                except OSError:
                                    break
                                _delete_tree(root_key, f"{sub_key}\\{child}")
                        finally:
                            winreg.CloseKey(handle)

                        winreg.DeleteKey(root_key, sub_key)
                        self.logger.info("Deleted registry key tree: %s", sub_key)

                    org_subkey = f"Software\\{self.org_name}"
                    _delete_tree(winreg.HKEY_CURRENT_USER, org_subkey)
                except ImportError:
                    self.logger.warning(
                        "winreg not available, skipping direct registry deletion",
                    )
                except Exception as e:  # pragma: no cover - defensive logging
                    self.logger.warning("Failed to delete registry key tree: %s", e)

            return True

        except Exception as e:  # pragma: no cover - best-effort diagnostics
            self.logger.error("Failed to clear QSettings: %s", e, exc_info=True)
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
                    self.logger.info("Deleted: %s ({file_count} files)", directory)

                except Exception as e:
                    error_msg = f"Failed to delete {directory}: {e}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)

        return dirs_deleted, files_deleted, errors

    def _clean_temp_files(self) -> None:
        """Clean any remaining temp files."""
        try:
            temp_base = Path(tempfile.gettempdir())

            # Clean VTK temp files
            for vtk_temp in temp_base.glob("vtk*"):
                try:
                    if vtk_temp.is_file():
                        vtk_temp.unlink()
                    elif vtk_temp.is_dir():
                        shutil.rmtree(vtk_temp)
                except Exception as exc:  # pragma: no cover - best-effort diagnostics
                    self.logger.debug("Failed to clean %%s: %%s", vtk_temp, exc)

            self.logger.info("Temp files cleaned")

        except Exception as exc:  # pragma: no cover - best-effort diagnostics
            self.logger.warning("Failed to clean temp files: %s", exc)

    def _close_log_handlers(self) -> None:
        """Close all log handlers to release file locks."""
        try:
            # Get the root logger
            root_logger = logging.getLogger()

            # Close all handlers
            for handler in root_logger.handlers[:]:
                try:
                    handler.close()
                    root_logger.removeHandler(handler)
                except Exception:
                    # Can't reliably log handler-close failures here
                    pass

            # Also close handlers for our logger
            for handler in self.logger.handlers[:]:
                try:
                    handler.close()
                    self.logger.removeHandler(handler)
                except Exception:
                    pass

        except Exception:
            # Can't log this since we're closing loggers
            pass


def create_nuclear_reset_handler() -> NuclearReset:
    """
    Factory function to create a nuclear reset handler.

    Returns:
        NuclearReset instance
    """
    return NuclearReset()
