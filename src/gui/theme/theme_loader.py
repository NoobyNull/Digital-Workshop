"""
Theme Loader Module

This module provides functionality to load themes from JSON configuration files,
making the theme system extensible and configurable without code changes.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class ThemeLoader:
    """
    Loads and manages themes from JSON configuration files.

    This class provides an extensible way to manage themes by loading them
    from JSON files instead of hardcoding them in Python.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the theme loader.

        Args:
            config_path: Path to the themes JSON file. If None, uses default path.
        """
        if config_path is None:
            # Default path relative to this module
            current_dir = Path(__file__).parent
            config_path = current_dir / "themes.json"

        self.config_path = Path(config_path)
        self._themes_data = None
        self._load_themes()

    def _load_themes(self) -> None:
        """Load themes from the JSON configuration file."""
        try:
            if not self.config_path.exists():
                logger.error(f"Theme configuration file not found: {self.config_path}")
                self._themes_data = {"themes": {"light": {}, "dark": {}}}
                return

            with open(self.config_path, "r", encoding="utf-8") as f:
                self._themes_data = json.load(f)

            logger.info(f"Successfully loaded themes from {self.config_path}")
            self._validate_themes()

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in theme configuration file: {e}")
            self._themes_data = {"themes": {"light": {}, "dark": {}}}
        except Exception as e:
            logger.error(f"Error loading theme configuration: {e}")
            self._themes_data = {"themes": {"light": {}, "dark": {}}}

    def _validate_themes(self) -> None:
        """Validate the loaded theme data structure."""
        if not self._themes_data or "themes" not in self._themes_data:
            logger.warning("Invalid theme data structure")
            self._themes_data = {"themes": {"light": {}, "dark": {}}}
            return

        themes = self._themes_data["themes"]
        for theme_type in ["light", "dark"]:
            if theme_type not in themes:
                themes[theme_type] = {}
                logger.warning(f"Missing {theme_type} themes section")
                continue

            # Validate each theme has required color properties
            for theme_name, theme_data in themes[theme_type].items():
                if "colors" not in theme_data:
                    logger.warning(f"Theme {theme_name} missing colors section")
                    themes[theme_type][theme_name] = self._create_default_theme(theme_name)

    def _create_default_theme(self, theme_name: str) -> Dict[str, Any]:
        """Create a default theme structure for missing themes."""
        return {
            "name": theme_name.replace("_", " ").title(),
            "description": f"Default theme for {theme_name}",
            "colors": {
                "primary": "#1976D2",
                "primaryLight": "#42A5F5",
                "primaryDark": "#1565C0",
                "secondary": "#424242",
                "secondaryLight": "#6D6D6D",
                "secondaryDark": "#1B1B1B",
                "primaryTextColor": "#212121",
                "secondaryTextColor": "#757575",
                "primaryText": "#000000",
                "secondaryText": "#000000",
                "primaryColor": "#1976D2",
                "secondaryColor": "#424242",
                "primaryLightColor": "#42A5F5",
                "secondaryLightColor": "#6D6D6D",
                "primaryDarkColor": "#1565C0",
                "secondaryDarkColor": "#1B1B1B",
                "successColor": "#4CAF50",
                "warningColor": "#FF9800",
                "errorColor": "#F44336",
                "infoColor": "#2196F3",
            },
        }

    def get_available_themes(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Get all available themes.

        Returns:
            Dictionary containing all themes organized by type (light/dark)
        """
        return self._themes_data.get("themes", {"light": {}, "dark": {}})

    def get_theme_variants(self, theme_type: str) -> Dict[str, Dict[str, Any]]:
        """
        Get all variants for a specific theme type.

        Args:
            theme_type: Either "light" or "dark"

        Returns:
            Dictionary of theme variants for the specified type
        """
        themes = self.get_available_themes()
        return themes.get(theme_type, {})

    def get_theme_info(self, theme_type: str, variant: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific theme variant.

        Args:
            theme_type: Either "light" or "dark"
            variant: The theme variant name

        Returns:
            Theme information dictionary or None if not found
        """
        variants = self.get_theme_variants(theme_type)
        return variants.get(variant)

    def get_theme_colors(self, theme_type: str, variant: str) -> Optional[Dict[str, str]]:
        """
        Get color definitions for a specific theme variant.

        Args:
            theme_type: Either "light" or "dark"
            variant: The theme variant name

        Returns:
            Dictionary of color definitions or None if not found
        """
        theme_info = self.get_theme_info(theme_type, variant)
        if theme_info:
            return theme_info.get("colors")
        return None

    def get_all_variant_names(self) -> Dict[str, list]:
        """
        Get all variant names organized by theme type.

        Returns:
            Dictionary with "light" and "dark" keys containing lists of variant names
        """
        result = {"light": [], "dark": []}
        themes = self.get_available_themes()

        for theme_type in ["light", "dark"]:
            variants = themes.get(theme_type, {})
            result[theme_type] = list(variants.keys())

        return result

    def reload_themes(self) -> None:
        """Reload themes from the configuration file."""
        logger.info("Reloading themes from configuration file")
        self._load_themes()

    def add_theme(self, theme_type: str, variant: str, theme_data: Dict[str, Any]) -> bool:
        """
        Add a new theme variant.

        Args:
            theme_type: Either "light" or "dark"
            variant: The theme variant name
            theme_data: Theme data dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            if theme_type not in ["light", "dark"]:
                logger.error(f"Invalid theme type: {theme_type}")
                return False

            if "colors" not in theme_data:
                logger.error("Theme data must contain 'colors' section")
                return False

            self._themes_data["themes"][theme_type][variant] = theme_data
            logger.info(f"Added new theme: {theme_type}/{variant}")
            return True

        except Exception as e:
            logger.error(f"Error adding theme {theme_type}/{variant}: {e}")
            return False

    def remove_theme(self, theme_type: str, variant: str) -> bool:
        """
        Remove a theme variant.

        Args:
            theme_type: Either "light" or "dark"
            variant: The theme variant name

        Returns:
            True if successful, False otherwise
        """
        try:
            if theme_type in self._themes_data["themes"]:
                if variant in self._themes_data["themes"][theme_type]:
                    del self._themes_data["themes"][theme_type][variant]
                    logger.info(f"Removed theme: {theme_type}/{variant}")
                    return True
                else:
                    logger.warning(f"Theme variant not found: {theme_type}/{variant}")
                    return False
            else:
                logger.warning(f"Theme type not found: {theme_type}")
                return False

        except Exception as e:
            logger.error(f"Error removing theme {theme_type}/{variant}: {e}")
            return False

    def export_themes(self) -> Dict[str, Any]:
        """
        Export all themes data.

        Returns:
            Complete themes configuration dictionary
        """
        return self._themes_data.copy()

    def get_theme_names(self, theme_type: str, variant: str) -> tuple:
        """
        Get display name and description for a theme.

        Args:
            theme_type: Either "light" or "dark"
            variant: The theme variant name

        Returns:
            Tuple of (display_name, description) or defaults if not found
        """
        theme_info = self.get_theme_info(theme_type, variant)
        if theme_info:
            return (
                theme_info.get("name", variant.replace("_", " ").title()),
                theme_info.get("description", f"Theme for {variant}"),
            )

        # Return defaults
        display_name = variant.replace("_", " ").title()
        return (display_name, f"Default theme for {variant}")


# Global theme loader instance
_theme_loader = None


def get_theme_loader() -> ThemeLoader:
    """
    Get the global theme loader instance.

    Returns:
        ThemeLoader instance
    """
    global _theme_loader
    if _theme_loader is None:
        _theme_loader = ThemeLoader()
    return _theme_loader


def reload_global_theme_loader() -> None:
    """Reload the global theme loader."""
    global _theme_loader
    _theme_loader = None
    get_theme_loader()
