"""
Root folder manager for 3D-MM application.

Manages configuration of multiple root folders for the file browser,
with persistence to application settings.
"""

from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict

from PySide6.QtCore import QObject, Signal

from src.core.logging_config import get_logger
from PySide6.QtCore import QSettings


@dataclass
class RootFolder:
    """Represents a configured root folder."""
    path: str
    display_name: str
    enabled: bool = True
    id: Optional[int] = None

    def __post_init__(self):
        if self.id is None:
            # Generate a simple ID based on path hash for uniqueness
            self.id = hash(self.path) & 0xFFFFFFFF


class RootFolderManager(QObject):
    """
    Manages the list of configured root folders for the file browser.

    Provides functionality to add, remove, enable/disable root folders,
    with automatic persistence to application settings.

    This is a singleton class - use get_instance() to get the shared instance.
    """

    folders_changed = Signal()  # Emitted when the folder list changes

    _instance = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.settings = QSettings()
        self._folders: List[RootFolder] = []
        self._load_folders()

    @classmethod
    def get_instance(cls) -> "RootFolderManager":
        """Get the singleton instance of RootFolderManager."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_folders(self) -> None:
        """Load root folders from application settings."""
        try:
            folders_data_str = self.settings.value("root_folders", "")
            if folders_data_str:
                import json
                folders_data = json.loads(folders_data_str)
            else:
                folders_data = []

            self._folders = []

            for folder_data in folders_data:
                if isinstance(folder_data, dict):
                    folder = RootFolder(
                        path=folder_data.get("path", ""),
                        display_name=folder_data.get("display_name", ""),
                        enabled=folder_data.get("enabled", True),
                        id=folder_data.get("id")
                    )
                    if self._validate_folder(folder):
                        self._folders.append(folder)
                    else:
                        self.logger.warning(f"Skipping invalid root folder: {folder.path}")

            # If no folders configured, add default user home
            if not self._folders:
                self._add_default_folders()

            self.logger.info(f"Loaded {len(self._folders)} root folders")

        except Exception as e:
            self.logger.error(f"Failed to load root folders: {e}")
            self._add_default_folders()

    def _add_default_folders(self) -> None:
        """Add default root folders when none are configured."""
        home_path = str(Path.home())
        home_folder = RootFolder(
            path=home_path,
            display_name="Home",
            enabled=True
        )
        self._folders = [home_folder]
        self._save_folders()

    def _save_folders(self) -> None:
        """Save root folders to application settings."""
        try:
            import json
            folders_data = [asdict(folder) for folder in self._folders]
            folders_data_str = json.dumps(folders_data)
            self.settings.setValue("root_folders", folders_data_str)
            self.logger.debug(f"Saved {len(self._folders)} root folders")
        except Exception as e:
            self.logger.error(f"Failed to save root folders: {e}")

    def _validate_folder(self, folder: RootFolder) -> bool:
        """Validate that a root folder is accessible and valid."""
        try:
            path = Path(folder.path)
            if not path.exists():
                self.logger.warning(f"Root folder path does not exist: {folder.path}")
                return False
            if not path.is_dir():
                self.logger.warning(f"Root folder path is not a directory: {folder.path}")
                return False
            # Check if we can list the directory (basic permission check)
            try:
                list(path.iterdir())
            except PermissionError:
                self.logger.warning(f"No permission to access root folder: {folder.path}")
                return False
            return True
        except Exception as e:
            self.logger.error(f"Error validating root folder {folder.path}: {e}")
            return False

    def get_folders(self, enabled_only: bool = False) -> List[RootFolder]:
        """Get the list of configured root folders."""
        if enabled_only:
            return [f for f in self._folders if f.enabled]
        return self._folders.copy()

    def get_enabled_folders(self) -> List[RootFolder]:
        """Get only the enabled root folders."""
        return self.get_folders(enabled_only=True)

    def add_folder(self, path: str, display_name: Optional[str] = None) -> bool:
        """Add a new root folder."""
        try:
            path_obj = Path(path).resolve()
            path_str = str(path_obj)

            # Check if folder already exists
            for folder in self._folders:
                if Path(folder.path).resolve() == path_obj:
                    self.logger.warning(f"Root folder already exists: {path_str}")
                    return False

            # Generate display name if not provided
            if not display_name:
                display_name = path_obj.name or path_str

            folder = RootFolder(
                path=path_str,
                display_name=display_name,
                enabled=True
            )

            if not self._validate_folder(folder):
                return False

            self._folders.append(folder)
            self._save_folders()
            self.folders_changed.emit()
            self.logger.info(f"Added root folder: {display_name} ({path_str})")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add root folder {path}: {e}")
            return False

    def remove_folder(self, folder_id: int) -> bool:
        """Remove a root folder by ID."""
        try:
            for i, folder in enumerate(self._folders):
                if folder.id == folder_id:
                    removed_folder = self._folders.pop(i)
                    self._save_folders()
                    self.folders_changed.emit()
                    self.logger.info(f"Removed root folder: {removed_folder.display_name}")
                    return True

            self.logger.warning(f"Root folder with ID {folder_id} not found")
            return False

        except Exception as e:
            self.logger.error(f"Failed to remove root folder {folder_id}: {e}")
            return False

    def update_folder(self, folder_id: int, path: Optional[str] = None,
                     display_name: Optional[str] = None, enabled: Optional[bool] = None) -> bool:
        """Update properties of a root folder."""
        try:
            for folder in self._folders:
                if folder.id == folder_id:
                    if path is not None:
                        folder.path = path
                    if display_name is not None:
                        folder.display_name = display_name
                    if enabled is not None:
                        folder.enabled = enabled

                    if not self._validate_folder(folder):
                        return False

                    self._save_folders()
                    self.folders_changed.emit()
                    self.logger.info(f"Updated root folder: {folder.display_name}")
                    return True

            self.logger.warning(f"Root folder with ID {folder_id} not found")
            return False

        except Exception as e:
            self.logger.error(f"Failed to update root folder {folder_id}: {e}")
            return False

    def get_folder_by_id(self, folder_id: int) -> Optional[RootFolder]:
        """Get a root folder by its ID."""
        for folder in self._folders:
            if folder.id == folder_id:
                return folder
        return None

    def get_folder_paths(self, enabled_only: bool = True) -> List[str]:
        """Get just the paths of configured folders."""
        folders = self.get_folders(enabled_only=enabled_only)
        return [f.path for f in folders]

    def validate_all_folders(self) -> Dict[str, List[str]]:
        """Validate all configured folders and return results."""
        results = {
            "valid": [],
            "invalid": []
        }

        for folder in self._folders:
            if self._validate_folder(folder):
                results["valid"].append(folder.path)
            else:
                results["invalid"].append(folder.path)

        return results

    def cleanup_invalid_folders(self) -> int:
        """Remove all invalid folders and return count of removed folders."""
        valid_folders = []
        removed_count = 0

        for folder in self._folders:
            if self._validate_folder(folder):
                valid_folders.append(folder)
            else:
                removed_count += 1
                self.logger.info(f"Removing invalid root folder: {folder.display_name} ({folder.path})")

        if removed_count > 0:
            self._folders = valid_folders
            self._save_folders()
            self.folders_changed.emit()

        return removed_count
