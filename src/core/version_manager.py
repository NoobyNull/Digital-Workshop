"""
Version management for Digital Workshop.

Provides installation-type aware version information.
"""

from typing import Optional
from dataclasses import dataclass
from .installation_detector import InstallationType, get_installation_type


@dataclass
class VersionInfo:
    """Version information container."""

    base_version: str
    installation_type: str
    display_version: str
    logger_name: str
    organization_name: str


class VersionManager:
    """Manages version information for different installation types."""

    def __init__(self) -> None:
        """Initialize the version manager."""
        self._base_name = "DigitalWorkshop"
        self._base_version = "0.1.5"
        self._version_cache: Optional[VersionInfo] = None

    def get_version_info(self) -> VersionInfo:
        """
        Get version information for the current installation.

        Returns:
            VersionInfo: Version information for current installation
        """
        if self._version_cache is None:
            self._version_cache = self._create_version_info()

        return self._version_cache

    def _create_version_info(self) -> VersionInfo:
        """
        Create version information for the current installation.

        Returns:
            VersionInfo: Version information
        """
        installation_type = get_installation_type()

        # Determine display version based on installation type
        if installation_type == InstallationType.RAW:
            display_version = f"{self._base_version}-Raw"
            logger_name = f"{self._base_name}-Raw"
            organization_name = self._base_name
        elif installation_type == InstallationType.PORTABLE:
            display_version = f"{self._base_version}-Portable"
            logger_name = f"{self._base_name}-Portable"
            organization_name = self._base_name
        else:  # USER or SYSTEM
            display_version = self._base_version
            logger_name = self._base_name
            organization_name = self._base_name

        return VersionInfo(
            base_version=self._base_version,
            installation_type=installation_type.value,
            display_version=display_version,
            logger_name=logger_name,
            organization_name=organization_name,
        )

    def get_display_version(self) -> str:
        """
        Get the display version for the current installation.

        Returns:
            str: The display version
        """
        return self.get_version_info().display_version

    def get_logger_name(self) -> str:
        """
        Get the logger name for the current installation.

        Returns:
            str: The logger name
        """
        return self.get_version_info().logger_name

    def get_organization_name(self) -> str:
        """
        Get the organization name for the current installation.

        Returns:
            str: The organization name
        """
        return self.get_version_info().organization_name

    def get_base_version(self) -> str:
        """
        Get the base version.

        Returns:
            str: The base version
        """
        return self._base_version

    def get_app_name(self) -> str:
        """
        Get the application name.

        Returns:
            str: The application name
        """
        return self._base_name


# Global version manager instance
_version_manager = VersionManager()


def get_display_version() -> str:
    """
    Get the display version for the current installation.

    Returns:
        str: The display version
    """
    return _version_manager.get_display_version()


def get_logger_name() -> str:
    """
    Get the logger name for the current installation.

    Returns:
        str: The logger name
    """
    return _version_manager.get_logger_name()


def get_organization_name() -> str:
    """
    Get the organization name for the current installation.

    Returns:
        str: The organization name
    """
    return _version_manager.get_organization_name()


def get_app_name() -> str:
    """
    Get the application name.

    Returns:
        str: The application name
    """
    return _version_manager.get_app_name()
