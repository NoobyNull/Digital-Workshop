"""
Theme persistence for Digital Workshop.

Handles saving, loading, importing, and exporting themes to/from JSON files.

Single Responsibility: Persist theme data to disk.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import QStandardPaths

logger = logging.getLogger(__name__)


class ThemePersistence:
    """
    Handles theme persistence operations:
    - Save theme to AppData
    - Load theme from AppData
    - Export theme to JSON file
    - Import theme from JSON file
    """

    THEME_FILENAME = "theme.json"

    def __init__(self):
        """Initialize persistence handler."""
        self._app_data_path = self._get_app_data_path()

    def _get_app_data_path(self) -> Path:
        """Get the application data directory path."""
        app_data = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        path = Path(app_data)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _get_theme_file_path(self) -> Path:
        """Get the path to the theme.json file in AppData."""
        return self._app_data_path / self.THEME_FILENAME

    def save_theme(self, colors: Dict[str, str]) -> None:
        """
        Save theme colors to AppData/theme.json.

        Args:
            colors: Dictionary of color variable names to hex values

        Raises:
            IOError: If file cannot be written
        """
        try:
            path = self._get_theme_file_path()

            # Ensure directory exists
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write JSON file
            with open(path, "w", encoding="utf-8") as f:
                json.dump(colors, f, indent=2)

            logger.info("Theme saved to %s", path)
        except Exception as e:
            logger.error("Failed to save theme: %s", e)
            raise

    def load_theme(self) -> Optional[Dict[str, str]]:
        """
        Load theme colors from AppData/theme.json.

        Returns:
            Dictionary of colors, or None if file doesn't exist or is invalid
        """
        try:
            path = self._get_theme_file_path()

            if not path.exists():
                logger.debug("Theme file not found: %s", path)
                return None

            with open(path, "r", encoding="utf-8") as f:
                colors = json.load(f)

            if not isinstance(colors, dict):
                logger.warning("Theme file contains invalid data: %s", path)
                return None

            logger.info("Theme loaded from %s", path)
            return colors
        except json.JSONDecodeError as e:
            logger.error("Failed to parse theme file: %s", e)
            return None
        except Exception as e:
            logger.error("Failed to load theme: %s", e)
            return None

    def export_theme(self, path: Path, colors: Dict[str, str]) -> None:
        """
        Export theme colors to a JSON file.

        Args:
            path: Path to export to
            colors: Dictionary of color variable names to hex values

        Raises:
            IOError: If file cannot be written
        """
        try:
            # Ensure .json extension
            if path.suffix.lower() != ".json":
                path = path.with_suffix(".json")

            # Ensure directory exists
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write JSON file
            with open(path, "w", encoding="utf-8") as f:
                json.dump(colors, f, indent=2)

            logger.info("Theme exported to %s", path)
        except Exception as e:
            logger.error("Failed to export theme: %s", e)
            raise

    def import_theme(self, path: Path) -> Optional[Dict[str, str]]:
        """
        Import theme colors from a JSON file.

        Args:
            path: Path to import from

        Returns:
            Dictionary of colors, or None if file is invalid

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        try:
            if not path.exists():
                raise FileNotFoundError(f"Theme file not found: {path}")

            with open(path, "r", encoding="utf-8") as f:
                colors = json.load(f)

            if not isinstance(colors, dict):
                logger.warning("Theme file contains invalid data: %s", path)
                return None

            logger.info("Theme imported from %s", path)
            return colors
        except json.JSONDecodeError as e:
            logger.error("Failed to parse theme file: %s", e)
            raise
        except Exception as e:
            logger.error("Failed to import theme: %s", e)
            raise

    def theme_exists(self) -> bool:
        """Check if a saved theme exists in AppData."""
        return self._get_theme_file_path().exists()

    def get_app_data_path(self) -> Path:
        """Get the application data directory path."""
        return self._app_data_path
