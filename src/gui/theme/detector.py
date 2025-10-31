"""
System theme detection for 3D-MM application.

Detects OS dark mode preference and applies appropriate theme.
Supports Windows, macOS, and Linux.

Single Responsibility: Detect and report system theme preference.
"""

import logging
import platform
from typing import Literal

logger = logging.getLogger(__name__)


class SystemThemeDetector:
    """
    Detects the system's theme preference (light or dark mode).

    Supports:
    - Windows: Registry-based detection
    - macOS: Defaults-based detection
    - Linux: Environment variable detection
    """

    def __init__(self):
        """Initialize the detector."""
        self._current_mode: Literal["light", "dark"] = "light"
        self._enabled = False
        self._detect_system_theme()

    def detect(self) -> Literal["light", "dark"]:
        """
        Detect current system theme preference.

        Returns:
            "light" or "dark"
        """
        system = platform.system()

        try:
            if system == "Windows":
                return self._detect_windows()
            elif system == "Darwin":
                return self._detect_macos()
            elif system == "Linux":
                return self._detect_linux()
        except Exception as e:
            logger.warning(f"Failed to detect system theme: {e}")

        return "light"  # Default fallback

    def _detect_windows(self) -> Literal["light", "dark"]:
        r"""
        Detect Windows dark mode via registry.

        Checks: HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize
        Value: AppsUseLightTheme (0 = dark, 1 = light)
        """
        try:
            import winreg

            registry_path = (
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            )
            registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path)
            value, _ = winreg.QueryValueEx(registry_key, "AppsUseLightTheme")
            winreg.CloseKey(registry_key)

            # value == 1 means light theme, value == 0 means dark theme
            return "light" if value == 1 else "dark"
        except Exception as e:
            logger.debug(f"Windows theme detection failed: {e}")
            return "light"

    def _detect_macos(self) -> Literal["light", "dark"]:
        """
        Detect macOS dark mode via defaults.

        Checks: defaults read -g AppleInterfaceStyle
        Returns "dark" if set, "light" otherwise.
        """
        try:
            import subprocess

            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True,
                text=True,
                timeout=2,
            )

            # If command succeeds and output contains "Dark", it's dark mode
            if result.returncode == 0 and "Dark" in result.stdout:
                return "dark"
            return "light"
        except Exception as e:
            logger.debug(f"macOS theme detection failed: {e}")
            return "light"

    def _detect_linux(self) -> Literal["light", "dark"]:
        """
        Detect Linux dark mode via environment variables and GTK settings.

        Checks:
        - GTK_THEME environment variable
        - dconf settings (GNOME)
        - Qt style hints
        """
        try:
            import os

            # Check GTK_THEME environment variable
            gtk_theme = os.environ.get("GTK_THEME", "").lower()
            if "dark" in gtk_theme:
                return "dark"

            # Check GNOME dconf settings
            try:
                import subprocess

                result = subprocess.run(
                    [
                        "dconf",
                        "read",
                        "/org/gnome/desktop/interface/gtk-application-prefer-dark-theme",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                if result.returncode == 0 and "true" in result.stdout.lower():
                    return "dark"
            except Exception:
                pass

            # Check QT_STYLE_OVERRIDE
            qt_style = os.environ.get("QT_STYLE_OVERRIDE", "").lower()
            if "dark" in qt_style:
                return "dark"

            return "light"
        except Exception as e:
            logger.debug(f"Linux theme detection failed: {e}")
            return "light"

    def _detect_system_theme(self) -> None:
        """Detect and cache current system theme."""
        self._current_mode = self.detect()
        logger.info(f"System theme detected: {self._current_mode}")

    def get_current_mode(self) -> Literal["light", "dark"]:
        """Get the currently detected system theme mode."""
        return self._current_mode

    def enable(self) -> None:
        """Enable system theme detection."""
        self._enabled = True
        self._detect_system_theme()
        logger.info("System theme detection enabled")

    def disable(self) -> None:
        """Disable system theme detection."""
        self._enabled = False
        logger.info("System theme detection disabled")

    def is_enabled(self) -> bool:
        """Check if system theme detection is enabled."""
        return self._enabled

    def refresh(self) -> Literal["light", "dark"]:
        """
        Refresh the detected system theme.

        Returns:
            The newly detected theme mode
        """
        old_mode = self._current_mode
        self._detect_system_theme()

        if old_mode != self._current_mode:
            logger.info(f"System theme changed: {old_mode} -> {self._current_mode}")

        return self._current_mode
