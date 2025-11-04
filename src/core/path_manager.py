"""
Path management for Digital Workshop.

Provides installation-type aware path resolution for cross-platform support.
Supports development mode with --mem-only flag that redirects all writes to temp.
"""

import os
import sys
import platform
import tempfile
from pathlib import Path
from typing import Dict, Optional
from .installation_detector import InstallationType, get_installation_type


class PathManager:
    """Manages paths for different installation types across platforms.

    In memory-only mode (--mem-only), all paths are redirected to a temporary
    directory to avoid any disk persistence.
    """

    def __init__(self):
        """Initialize the path manager."""
        self._paths_cache: Dict[str, Path] = {}
        self._installation_type = get_installation_type()
        self._system = platform.system()
        self._is_memory_only = os.getenv("USE_MEMORY_DB", "false").lower() == "true"
        self._temp_base: Optional[Path] = None

        # Create temp directory for memory-only mode
        if self._is_memory_only:
            self._temp_base = Path(tempfile.gettempdir()) / "digital_workshop_dev"
            self._temp_base.mkdir(parents=True, exist_ok=True)

    def get_cache_directory(self) -> Path:
        """
        Get the cache directory for the current installation.

        Returns:
            Path: The cache directory path
        """
        if "cache" not in self._paths_cache:
            self._paths_cache["cache"] = self._resolve_cache_path()

        return self._paths_cache["cache"]

    def get_log_directory(self) -> Path:
        """
        Get the log directory for the current installation.

        Returns:
            Path: The log directory path
        """
        if "log" not in self._paths_cache:
            self._paths_cache["log"] = self._resolve_log_path()

        return self._paths_cache["log"]

    def get_data_directory(self) -> Path:
        """
        Get the data directory for the current installation.

        Returns:
            Path: The data directory path
        """
        if "data" not in self._paths_cache:
            self._paths_cache["data"] = self._resolve_data_path()

        return self._paths_cache["data"]

    def get_resource_directory(self) -> Path:
        """
        Get the resource directory for the current installation.

        Returns:
            Path: The resource directory path
        """
        if "resource" not in self._paths_cache:
            self._paths_cache["resource"] = self._resolve_resource_path()

        return self._paths_cache["resource"]

    def get_config_directory(self) -> Path:
        """
        Get the config directory for the current installation.

        Returns:
            Path: The config directory path
        """
        if "config" not in self._paths_cache:
            self._paths_cache["config"] = self._resolve_config_path()

        return self._paths_cache["config"]

    def get_database_file(self, db_name: str = None) -> Path:
        """
        Get the database file path for the current installation.

        Args:
            db_name: The database file name (defaults to app name + .db)

        Returns:
            Path: The database file path
        """
        if db_name is None:
            from .version_manager import get_app_name

            db_name = f"{get_app_name()}.db"
        return self.get_data_directory() / db_name

    def _resolve_cache_path(self) -> Path:
        """
        Resolve the cache directory path based on installation type and platform.

        In memory-only mode, redirects to temp directory.

        Returns:
            Path: The cache directory path
        """
        # Memory-only mode: use temp directory
        if self._is_memory_only:
            return self._temp_base / "cache"

        if self._installation_type == InstallationType.RAW:
            # Development: use local cache directory
            return Path.cwd() / "cache"
        elif self._installation_type == InstallationType.PORTABLE:
            # Portable: use directory relative to executable
            executable_dir = (
                Path(sys.executable).parent if hasattr(sys, "executable") else Path.cwd()
            )
            return executable_dir / "cache"
        else:  # USER or SYSTEM
            # Installed: use appropriate app data directory
            return self._get_app_data_base_path() / "cache"

    def _resolve_log_path(self) -> Path:
        """
        Resolve the log directory path based on installation type and platform.

        Returns:
            Path: The log directory path
        """
        cache_dir = self.get_cache_directory()
        return cache_dir / "logs"

    def _resolve_data_path(self) -> Path:
        """
        Resolve the data directory path based on installation type and platform.

        Returns:
            Path: The data directory path
        """
        cache_dir = self.get_cache_directory()
        return cache_dir / "data"

    def _resolve_resource_path(self) -> Path:
        """
        Resolve the resource directory path based on installation type and platform.

        Note: Resources are always read from source, not redirected in memory-only mode.

        Returns:
            Path: The resource directory path
        """
        if self._installation_type == InstallationType.RAW:
            # Development: use local resources directory
            return Path.cwd() / "resources"
        if self._installation_type == InstallationType.PORTABLE:
            # Portable: use directory relative to executable
            executable_dir = (
                Path(sys.executable).parent if hasattr(sys, "executable") else Path.cwd()
            )
            return executable_dir / "resources"
        # USER or SYSTEM
        # Installed: use appropriate app data directory
        return self.get_data_directory() / "resources"

    def _resolve_config_path(self) -> Path:
        """
        Resolve the config directory path based on installation type and platform.

        In memory-only mode, redirects to temp directory.

        Returns:
            Path: The config directory path
        """
        # Memory-only mode: use temp directory
        if self._is_memory_only:
            return self._temp_base / "config"

        if self._installation_type == InstallationType.RAW:
            # Development: use local config directory
            return Path.cwd() / "config"
        if self._installation_type == InstallationType.PORTABLE:
            # Portable: use directory relative to executable
            executable_dir = (
                Path(sys.executable).parent if hasattr(sys, "executable") else Path.cwd()
            )
            return executable_dir / "config"
        # USER or SYSTEM
        # Installed: use appropriate app data directory
        return self._get_app_data_base_path() / "config"

    def _get_app_data_base_path(self) -> Path:
        """
        Get the base application data path for installed versions.

        Returns:
            Path: The base application data path
        """
        from .version_manager import get_app_name

        app_name = get_app_name()

        if self._system == "Windows":
            if self._installation_type == InstallationType.SYSTEM:
                # System installation might use shared data
                try:
                    program_data = os.environ.get("PROGRAMDATA", "")
                    if program_data:
                        return Path(program_data) / app_name
                except (KeyError, OSError):
                    pass  # Fall back to user data
                return (
                    Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
                    / app_name
                )
            else:  # USER
                return (
                    Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
                    / app_name
                )

        elif self._system == "Darwin":  # macOS
            if self._installation_type == InstallationType.SYSTEM:
                return Path("/Library") / "Application Support" / app_name
            else:  # USER
                return Path.home() / "Library" / "Application Support" / app_name

        else:  # Linux and other Unix-like systems
            if self._installation_type == InstallationType.SYSTEM:
                return Path("/opt") / app_name
            else:  # USER
                return Path.home() / ".local" / "share" / app_name

    def ensure_directories_exist(self) -> None:
        """
        Ensure all required directories exist.
        """
        directories = [
            self.get_cache_directory(),
            self.get_log_directory(),
            self.get_data_directory(),
            self.get_resource_directory(),
            self.get_config_directory(),
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# Global path manager instance
_path_manager = PathManager()


def get_cache_directory() -> Path:
    """
    Get the cache directory for the current installation.

    Returns:
        Path: The cache directory path
    """
    return _path_manager.get_cache_directory()


def get_log_directory() -> Path:
    """
    Get the log directory for the current installation.

    Returns:
        Path: The log directory path
    """
    return _path_manager.get_log_directory()


def get_data_directory() -> Path:
    """
    Get the data directory for the current installation.

    Returns:
        Path: The data directory path
    """
    return _path_manager.get_data_directory()


def get_resource_directory() -> Path:
    """
    Get the resource directory for the current installation.

    Returns:
        Path: The resource directory path
    """
    return _path_manager.get_resource_directory()


def get_config_directory() -> Path:
    """
    Get the config directory for the current installation.

    Returns:
        Path: The config directory path
    """
    return _path_manager.get_config_directory()


def get_database_file(db_name: str = None) -> Path:
    """
    Get the database file path for the current installation.

    Args:
        db_name: The database file name (defaults to app name + .db)

    Returns:
        Path: The database file path
    """
    return _path_manager.get_database_file(db_name)


def ensure_directories_exist() -> None:
    """
    Ensure all required directories exist.
    """
    _path_manager.ensure_directories_exist()
