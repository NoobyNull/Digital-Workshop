"""
Installation type detection for Digital Workshop.

Determines which installation variant is running to enable
installation-type specific behavior and paths.
"""

import os
import sys
import platform
from pathlib import Path
from enum import Enum
from typing import Optional


class InstallationType(Enum):
    """Enumeration of installation types."""

    RAW = "raw"
    PORTABLE = "portable"
    USER = "user"
    SYSTEM = "system"


class InstallationDetector:
    """Detects the current installation type."""

    def __init__(self):
        """Initialize the installation detector."""
        self._installation_type: Optional[InstallationType] = None
        self._detection_performed = False

    def detect_installation_type(self) -> InstallationType:
        """
        Detect the current installation type.

        Returns:
            InstallationType: The detected installation type
        """
        if not self._detection_performed:
            self._installation_type = self._perform_detection()
            self._detection_performed = True

        return self._installation_type

    def _perform_detection(self) -> InstallationType:
        """
        Perform the actual installation type detection.

        Returns:
            InstallationType: The detected installation type
        """
        # Check for RAW (development) installation
        if self._is_raw_installation():
            return InstallationType.RAW

        # Check for PORTABLE installation
        if self._is_portable_installation():
            return InstallationType.PORTABLE

        # Check for SYSTEM vs USER installation
        if self._is_system_installation():
            return InstallationType.SYSTEM

        # Default to USER installation
        return InstallationType.USER

    def _is_raw_installation(self) -> bool:
        """
        Check if this is a raw development installation.

        Returns:
            bool: True if raw development installation
        """
        # Check if we're running from source directory
        current_script = Path(sys.argv[0])
        src_dir = Path(__file__).parent.parent.parent

        # If we're in development mode (running from src/)
        if current_script.name in ["run.py", "main.py"] or current_script.parent == src_dir:
            return True

        # Check for development environment indicators
        if os.path.exists(src_dir / "run.py") and os.path.exists(src_dir / "requirements.txt"):
            return True

        return False

    def _is_portable_installation(self) -> bool:
        """
        Check if this is a portable installation.

        Returns:
            bool: True if portable installation
        """
        # Portable installations typically run from a specific directory
        # and have DigitalWorkshop-Portable.exe or similar

        current_script = Path(sys.argv[0])
        executable_name = current_script.name.lower()

        # Check for portable executable name
        if "portable" in executable_name:
            return True

        # Check for common portable installation patterns
        if platform.system() == "Windows":
            app_data = Path(os.environ.get("LOCALAPPDATA", ""))
            from .version_manager import get_app_name

            app_name = get_app_name()
            if not (app_data / app_name).exists():
                # If no app data directory, might be portable
                return True
        else:
            # On Linux/macOS, check for portable patterns
            home_dir = Path.home()
            from .version_manager import get_app_name

            app_name = get_app_name()
            if not (home_dir / ".local" / "share" / app_name).exists():
                return True

        return False

    def _is_system_installation(self) -> bool:
        """
        Check if this is a system-wide installation.

        Returns:
            bool: True if system installation
        """
        # First, check the registry for explicit installation type marker
        if platform.system() == "Windows":
            try:
                import winreg

                try:
                    # Check HKEY_LOCAL_MACHINE for system installation marker
                    with winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE, r"Software\Digital Workshop"
                    ) as key:
                        install_type, _ = winreg.QueryValueEx(key, "InstallationType")
                        if install_type == "system":
                            return True
                except (OSError, FileNotFoundError):
                    # Registry key doesn't exist in HKLM
                    pass
            except ImportError:
                pass

        # Fallback: Check if running with elevated privileges (admin)
        try:
            if platform.system() == "Windows":
                import ctypes

                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.getuid() == 0
        except (AttributeError, ImportError):
            return False

    def get_installation_type(self) -> InstallationType:
        """
        Get the current installation type (cached).

        Returns:
            InstallationType: The installation type
        """
        return self._installation_type or self.detect_installation_type()

    def is_development(self) -> bool:
        """
        Check if this is a development installation.

        Returns:
            bool: True if development/raw installation
        """
        return self.get_installation_type() == InstallationType.RAW

    def is_portable(self) -> bool:
        """
        Check if this is a portable installation.

        Returns:
            bool: True if portable installation
        """
        return self.get_installation_type() == InstallationType.PORTABLE

    def is_user_install(self) -> bool:
        """
        Check if this is a user installation.

        Returns:
            bool: True if user installation
        """
        return self.get_installation_type() == InstallationType.USER

    def is_system_install(self) -> bool:
        """
        Check if this is a system installation.

        Returns:
            bool: True if system installation
        """
        return self.get_installation_type() == InstallationType.SYSTEM


# Global installation detector instance
_installation_detector = InstallationDetector()


def get_installation_type() -> InstallationType:
    """
    Get the current installation type.

    Returns:
        InstallationType: The installation type
    """
    return _installation_detector.get_installation_type()


def is_development() -> bool:
    """
    Check if this is a development installation.

    Returns:
        bool: True if development installation
    """
    return _installation_detector.is_development()


def is_portable() -> bool:
    """
    Check if this is a portable installation.

    Returns:
        bool: True if portable installation
    """
    return _installation_detector.is_portable()


def is_user_install() -> bool:
    """
    Check if this is a user installation.

    Returns:
        bool: True if user installation
    """
    return _installation_detector.is_user_install()


def is_system_install() -> bool:
    """
    Check if this is a system installation.

    Returns:
        bool: True if system installation
    """
    return _installation_detector.is_system_install()
