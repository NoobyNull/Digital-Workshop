"""
Background Provider for Thumbnail Generation

This module manages thumbnail background preferences, supporting both
solid colors and custom images from the resources folder or user-specified locations.
"""

from pathlib import Path
from typing import Union, Tuple, List

from src.core.logging_config import get_logger


class BackgroundProvider:
    """
    Manage thumbnail background preferences.

    Supports:
    - Solid colors (hex strings or RGB tuples)
    - Default background images from resources
    - User-specified custom image paths
    """

    # Default backgrounds directory
    DEFAULT_BACKGROUNDS_DIR = Path(__file__).parent.parent / "resources" / "backgrounds"

    # Default background color (light gray)
    DEFAULT_COLOR = "#F5F5F5"

    def __init__(self, settings_manager=None) -> None:
        """
        Initialize the background provider.

        Args:
            settings_manager: Optional settings manager for preferences
        """
        self.logger = get_logger(__name__)
        self.settings = settings_manager
        self.logger.info("BackgroundProvider initialized")

    def get_background(self) -> Union[str, Tuple[float, float, float]]:
        """
        Get the current background preference from settings.

        Returns:
            Background as hex color string, RGB tuple (0-1), or image path
        """
        try:
            # Try to get preference from settings
            if self.settings:
                # Check for image preference
                bg_image = getattr(self.settings, "thumbnail_bg_image", None)
                if bg_image and self._validate_image_path(bg_image):
                    self.logger.debug(
                        "Using background image from settings: %s", bg_image
                    )
                    return bg_image

                # Check for color preference
                bg_color = getattr(self.settings, "thumbnail_bg_color", None)
                if bg_color:
                    self.logger.debug(
                        "Using background color from settings: %s", bg_color
                    )
                    return self._parse_color(bg_color)

            # Fall back to default
            self.logger.debug("Using default background color: %s", self.DEFAULT_COLOR)
            return self._parse_color(self.DEFAULT_COLOR)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error getting background: %s", e, exc_info=True)
            return self._parse_color(self.DEFAULT_COLOR)

    def get_default_backgrounds(self) -> List[Path]:
        """
        Get list of default background images from resources folder.

        Returns:
            List of Path objects for available background images
        """
        try:
            if not self.DEFAULT_BACKGROUNDS_DIR.exists():
                self.logger.warning(
                    f"Default backgrounds directory not found: {self.DEFAULT_BACKGROUNDS_DIR}"
                )
                return []

            # Supported image formats
            image_extensions = {".png", ".jpg", ".jpeg", ".bmp"}

            backgrounds = [
                f
                for f in self.DEFAULT_BACKGROUNDS_DIR.iterdir()
                if f.is_file() and f.suffix.lower() in image_extensions
            ]

            self.logger.debug("Found %s default background images", len(backgrounds))
            return sorted(backgrounds)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error listing default backgrounds: %s", e, exc_info=True)
            return []

    def get_background_by_name(self, name: str) -> Path:
        """
        Get background path by name (without extension).

        Args:
            name: Background name (e.g., "Brick", "Blue", "Gray")

        Returns:
            Path to background image

        Raises:
            FileNotFoundError: If background not found
        """
        try:
            self.logger.debug("Looking for background: '%s'", name)

            # Check in default backgrounds directory
            if self.DEFAULT_BACKGROUNDS_DIR.exists():
                # Try PNG first
                png_path = self.DEFAULT_BACKGROUNDS_DIR / f"{name}.png"
                if png_path.exists():
                    self.logger.info("Found background '%s' at: %s", name, png_path)
                    return png_path

                # Try JPG
                jpg_path = self.DEFAULT_BACKGROUNDS_DIR / f"{name}.jpg"
                if jpg_path.exists():
                    self.logger.info("Found background '%s' at: %s", name, jpg_path)
                    return jpg_path

                # Try JPEG
                jpeg_path = self.DEFAULT_BACKGROUNDS_DIR / f"{name}.jpeg"
                if jpeg_path.exists():
                    self.logger.info("Found background '%s' at: %s", name, jpeg_path)
                    return jpeg_path

            # Not found
            error_msg = (
                f"Background '{name}' not found in {self.DEFAULT_BACKGROUNDS_DIR}"
            )
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        except FileNotFoundError:
            raise
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error(
                "Error getting background '%s': %s", name, e, exc_info=True
            )
            raise FileNotFoundError(
                f"Failed to get background '{name}': {e}"
            ) from e

    def resolve_background(self, background: Union[str, Path]) -> Union[str, Path]:
        """
        Resolve a background reference to an absolute path.

        If the input is an absolute path that exists, return it as-is.
        If the input is a name (no path separators), look it up in resources.

        Args:
            background: Background name or path

        Returns:
            Resolved absolute path or original value if it's a color
        """
        try:
            # If it's a hex color, return as-is
            if isinstance(background, str) and background.startswith("#"):
                return background

            # Convert to Path for easier handling
            bg_path = Path(background) if isinstance(background, str) else background

            # If it's an absolute path that exists, return it
            if bg_path.is_absolute() and bg_path.exists():
                self.logger.debug("Background is absolute path: %s", bg_path)
                resolved = bg_path
            # If it contains path separators, treat it as a path (might be invalid)
            elif "/" in str(background) or "\\" in str(background):
                if bg_path.exists():
                    resolved = bg_path
                else:
                    self.logger.warning(
                        "Background path does not exist: %s", background
                    )
                    resolved = background
            else:
                # Otherwise, treat it as a name and look it up
                self.logger.debug(
                    "Treating '%s' as background name, looking up...", background
                )
                resolved = self.get_background_by_name(str(background))

            return resolved

        except FileNotFoundError:
            # Return original value if lookup fails
            self.logger.warning(
                "Could not resolve background '%s', returning as-is", background
            )
            return background
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error resolving background: %s", e, exc_info=True)
            return background

    def _validate_image_path(self, path: Union[str, Path]) -> bool:
        """
        Validate that an image path exists and is a supported format.

        Args:
            path: Path to image file

        Returns:
            True if valid, False otherwise
        """
        try:
            path = Path(path)

            if not path.exists():
                self.logger.warning("Background image not found: %s", path)
                return False

            if not path.is_file():
                self.logger.warning("Background path is not a file: %s", path)
                return False

            # Check extension
            supported_extensions = {".png", ".jpg", ".jpeg", ".bmp"}
            if path.suffix.lower() not in supported_extensions:
                self.logger.warning(
                    "Unsupported background image format: %s", path.suffix
                )
                return False

            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error validating image path: %s", e, exc_info=True)
            return False

    def _parse_color(
        self, color: Union[str, Tuple, List]
    ) -> Tuple[float, float, float]:
        """
        Parse color from various formats to RGB tuple (0-1 range).

        Args:
            color: Color as hex string, RGB tuple (0-1 or 0-255), or list

        Returns:
            RGB tuple with values 0-1
        """
        try:
            if isinstance(color, str):
                # Hex color string
                return self._hex_to_rgb(color)

            if isinstance(color, (tuple, list)) and len(color) == 3:
                # Check if values are 0-1 or 0-255
                r, g, b = color
                if all(0 <= v <= 1 for v in color):
                    # Already 0-1 range
                    return (float(r), float(g), float(b))
                if all(0 <= v <= 255 for v in color):
                    # 0-255 range, convert to 0-1
                    return (r / 255.0, g / 255.0, b / 255.0)
                raise ValueError(f"RGB values out of range: {color}")

            raise ValueError(f"Unsupported color format: {color}")

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error parsing color %s: %s", color, e, exc_info=True)
            # Return default gray
            return (0.96, 0.96, 0.96)

    def _hex_to_rgb(self, hex_color: str) -> Tuple[float, float, float]:
        """
        Convert hex color string to RGB tuple (0-1 range).

        Args:
            hex_color: Hex color string (e.g., '#FF0000' or 'FF0000')

        Returns:
            RGB tuple with values 0-1
        """
        # Remove '#' if present
        hex_color = hex_color.lstrip("#")

        # Handle 3-digit hex colors (expand to 6-digit)
        if len(hex_color) == 3:
            hex_color = "".join([c * 2 for c in hex_color])

        # Convert to RGB
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0

        return (r, g, b)

    def set_background_color(self, color: Union[str, Tuple[int, int, int]]) -> bool:
        """
        Set background color preference.

        Args:
            color: Color as hex string or RGB tuple (0-255)

        Returns:
            True if successfully set
        """
        try:
            if not self.settings:
                self.logger.warning("No settings manager available")
                return False

            # Parse and validate color
            rgb = self._parse_color(color)

            # Convert back to hex for storage
            hex_color = self._rgb_to_hex(rgb)

            # Update settings
            self.settings.thumbnail_bg_color = hex_color
            self.settings.thumbnail_bg_image = None  # Clear image when setting color

            self.logger.info("Background color set to: %s", hex_color)
            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error setting background color: %s", e, exc_info=True)
            return False

    def set_background_image(self, image_path: Union[str, Path]) -> bool:
        """
        Set background image preference.

        Args:
            image_path: Path to background image

        Returns:
            True if successfully set
        """
        try:
            if not self.settings:
                self.logger.warning("No settings manager available")
                return False

            # Validate image
            if not self._validate_image_path(image_path):
                return False

            # Update settings
            self.settings.thumbnail_bg_image = str(Path(image_path).resolve())

            self.logger.info("Background image set to: %s", image_path)
            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error setting background image: %s", e, exc_info=True)
            return False

    def clear_background_image(self) -> bool:
        """
        Clear background image preference (revert to color).

        Returns:
            True if successfully cleared
        """
        try:
            if not self.settings:
                self.logger.warning("No settings manager available")
                return False

            self.settings.thumbnail_bg_image = None
            self.logger.info("Background image preference cleared")
            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error clearing background image: %s", e, exc_info=True)
            return False

    def _rgb_to_hex(self, rgb: Tuple[float, float, float]) -> str:
        """
        Convert RGB tuple (0-1) to hex color string.

        Args:
            rgb: RGB tuple with values 0-1

        Returns:
            Hex color string with '#' prefix
        """
        r = int(rgb[0] * 255)
        g = int(rgb[1] * 255)
        b = int(rgb[2] * 255)
        return f"#{r:02X}{g:02X}{b:02X}"
