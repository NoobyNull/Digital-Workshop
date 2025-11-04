"""
VTK Color Provider

This module provides VTK-compatible colors from qt-material themes, eliminating
VTK's dependency on the legacy color system. It offers real-time theme updates
and direct color mapping for VTK scene manager.

Key Features:
- Maps qt-material colors to VTK color names
- Real-time theme updates for VTK
- Eliminates VTK's legacy color system dependency
- Direct integration with VTK scene manager
"""

from typing import Dict, List, Tuple

from PySide6.QtCore import QObject, Signal
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class VTKColorProvider(QObject):
    """
    Provides VTK-compatible colors from qt-material themes.

    Acts as a bridge between qt-material themes and VTK scene manager,
    eliminating VTK's dependency on the legacy color system.
    """

    # Signals for VTK updates
    colors_changed = Signal()
    vtk_colors_updated = Signal(dict)  # vtk_color_dict

    # Singleton instance
    _instance = None

    def __init__(self) -> None:
        """Initialize VTK color provider."""
        super().__init__()

        # Import theme service
        from .simple_service import ThemeService

        self.theme_service = ThemeService.instance()

        # Connect to theme service signals
        try:
            self.theme_service.theme_changed.connect(self._on_theme_changed)
            self.theme_service.colors_updated.connect(self._on_colors_updated)
        except AttributeError:
            # Signals may not be available in simple service
            pass

        # Registered VTK managers
        self._vtk_managers: List["VTKSceneManager"] = []

        # Color mapping from VTK color names to qt-material color names
        self._vtk_color_mapping = self._define_vtk_color_mapping()

        # Cached VTK colors
        self._cached_vtk_colors: Dict[str, Tuple[float, float, float]] = {}

        # Initialize cache
        self._update_vtk_color_cache()

        logger.info("VTKColorProvider initialized with qt-material integration")

    @classmethod
    def instance(cls) -> "VTKColorProvider":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _define_vtk_color_mapping(self) -> Dict[str, str]:
        """
        Define mapping from VTK color names to qt-material color names.

        Returns:
            Dictionary mapping VTK color names to qt-material color names
        """
        return {
            # Canvas and background colors
            "canvas_bg": "secondaryDarkColor",
            "canvas_top": "secondaryColor",
            "window_bg": "secondaryDarkColor",
            "background": "secondaryDarkColor",
            "background_top": "secondaryColor",
            # Text colors
            "text": "primaryTextColor",
            "text_color": "primaryTextColor",
            "label_color": "primaryTextColor",
            # Primary colors
            "primary": "primaryColor",
            "primary_color": "primaryColor",
            "accent": "primaryColor",
            "highlight": "primaryLightColor",
            # Secondary colors
            "secondary": "secondaryColor",
            "secondary_color": "secondaryColor",
            "surface": "secondaryColor",
            # Border and UI element colors
            "border": "secondaryLightColor",
            "border_color": "secondaryLightColor",
            "outline": "secondaryLightColor",
            "edge": "primaryTextColor",
            "edge_color": "primaryTextColor",
            # Grid and ground colors
            "grid": "secondaryLightColor",
            "grid_color": "secondaryLightColor",
            "ground": "secondaryColor",
            "ground_color": "secondaryColor",
            "floor": "secondaryColor",
            "floor_color": "secondaryColor",
            # Model and object colors
            "model": "primaryColor",
            "model_color": "primaryColor",
            "model_surface": "primaryColor",
            "object": "primaryColor",
            "object_color": "primaryColor",
            # Lighting colors
            "light": "primaryLightColor",
            "light_color": "primaryLightColor",
            "ambient": "secondaryLightColor",
            "ambient_color": "secondaryLightColor",
            "diffuse": "primaryColor",
            "diffuse_color": "primaryColor",
            "specular": "primaryLightColor",
            "specular_color": "primaryLightColor",
            # Selection and focus colors
            "selection": "primaryColor",
            "selection_color": "primaryColor",
            "selected": "primaryColor",
            "selected_color": "primaryColor",
            "focus": "primaryColor",
            "focus_color": "primaryColor",
            # Status colors
            "success": "successColor",
            "success_color": "successColor",
            "warning": "warningColor",
            "warning_color": "warningColor",
            "error": "errorColor",
            "error_color": "errorColor",
            "info": "infoColor",
            "info_color": "infoColor",
            # Axis colors (for orientation widgets)
            "x_axis": "#FF4444",  # Red
            "y_axis": "#44FF44",  # Green
            "z_axis": "#4444FF",  # Blue
            "x_positive": "#FF6666",
            "x_negative": "#CC3333",
            "y_positive": "#66FF66",
            "y_negative": "#33CC33",
            "z_positive": "#6666FF",
            "z_negative": "#3333CC",
            # Default fallback color
            "default": "primaryColor",
            "fallback": "primaryColor",
        }

    def get_vtk_color(self, vtk_color_name: str) -> Tuple[float, float, float]:
        """
        Get a VTK-compatible color by name.

        Args:
            vtk_color_name: VTK color name

        Returns:
            Tuple of normalized RGB values (0..1)
        """
        # Check cache first
        if vtk_color_name in self._cached_vtk_colors:
            return self._cached_vtk_colors[vtk_color_name]

        # Get qt-material color name
        qt_material_color = self._vtk_color_mapping.get(vtk_color_name, "primaryColor")

        # Get color from theme service
        try:
            if qt_material_color.startswith("#"):
                # Direct hex color
                return self._hex_to_vtk_rgb(qt_material_color)
            else:
                # Qt-material color name
                vtk_color = self.theme_service.core.get_vtk_color(qt_material_color)

                # Cache the result
                self._cached_vtk_colors[vtk_color_name] = vtk_color

                return vtk_color
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.warning(f"Failed to get VTK color '{vtk_color_name}': {e}")
            # Return default color
            return (0.2, 0.4, 0.8)  # Default blue

    def get_all_vtk_colors(self) -> Dict[str, Tuple[float, float, float]]:
        """
        Get all VTK colors as a dictionary.

        Returns:
            Dictionary of VTK color names and RGB tuples
        """
        vtk_colors = {}
        for vtk_color_name in self._vtk_color_mapping.keys():
            vtk_colors[vtk_color_name] = self.get_vtk_color(vtk_color_name)
        return vtk_colors

    def register_vtk_manager(self, vtk_manager: "VTKSceneManager") -> None:
        """
        Register a VTK scene manager for automatic color updates.

        Args:
            vtk_manager: VTKSceneManager instance
        """
        if vtk_manager not in self._vtk_managers:
            self._vtk_managers.append(vtk_manager)
            logger.debug("Registered VTK manager: %s", vtk_manager.__class__.__name__)

    def unregister_vtk_manager(self, vtk_manager: "VTKSceneManager") -> None:
        """
        Unregister a VTK scene manager.

        Args:
            vtk_manager: VTKSceneManager instance
        """
        if vtk_manager in self._vtk_managers:
            self._vtk_managers.remove(vtk_manager)
            logger.debug("Unregistered VTK manager: %s", vtk_manager.__class__.__name__)

    def update_vtk_colors(self) -> None:
        """Update all registered VTK managers with new colors."""
        try:
            # Update cache
            self._update_vtk_color_cache()

            # Update all registered VTK managers
            for vtk_manager in self._vtk_managers:
                try:
                    if hasattr(vtk_manager, "update_theme_colors"):
                        vtk_manager.update_theme_colors()
                    elif hasattr(vtk_manager, "render"):
                        vtk_manager.render()
                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                    logger.warning(
                        f"Failed to update VTK manager {vtk_manager.__class__.__name__}: {e}"
                    )

            # Emit signals
            self.colors_changed.emit()
            self.vtk_colors_updated.emit(self.get_all_vtk_colors())

            logger.debug("Updated %s VTK managers", len(self._vtk_managers))

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to update VTK colors: %s", e, exc_info=True)

    def _update_vtk_color_cache(self) -> None:
        """Update the cached VTK colors."""
        self._cached_vtk_colors.clear()

        # Pre-cache all common colors
        common_colors = [
            "canvas_bg",
            "canvas_top",
            "primary",
            "secondary",
            "edge_color",
            "grid_color",
            "ground_color",
            "model_surface",
            "light_color",
            "text",
            "border",
            "selection",
            "success",
            "warning",
            "error",
        ]

        for color_name in common_colors:
            self.get_vtk_color(color_name)

        logger.debug("Updated VTK color cache with %s colors", len(self._cached_vtk_colors))

    @staticmethod
    def _hex_to_vtk_rgb(hex_color: str) -> Tuple[float, float, float]:
        """
        Convert hex color to VTK RGB tuple (0..1).

        Args:
            hex_color: Hex color string

        Returns:
            Tuple of normalized RGB values
        """
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4))

    def get_color_mapping_info(self) -> Dict[str, str]:
        """
        Get the color mapping information.

        Returns:
            Dictionary of VTK color names and their qt-material mappings
        """
        return self._vtk_color_mapping.copy()

    def add_custom_mapping(self, vtk_color_name: str, qt_material_color: str) -> None:
        """
        Add a custom color mapping.

        Args:
            vtk_color_name: VTK color name
            qt_material_color: Qt-material color name or hex color
        """
        self._vtk_color_mapping[vtk_color_name] = qt_material_color

        # Clear cache for this color
        if vtk_color_name in self._cached_vtk_colors:
            del self._cached_vtk_colors[vtk_color_name]

        logger.debug("Added custom mapping: %s -> {qt_material_color}", vtk_color_name)

    def remove_custom_mapping(self, vtk_color_name: str) -> bool:
        """
        Remove a custom color mapping.

        Args:
            vtk_color_name: VTK color name

        Returns:
            True if mapping was removed
        """
        if vtk_color_name in self._vtk_color_mapping:
            del self._vtk_color_mapping[vtk_color_name]

            # Clear cache for this color
            if vtk_color_name in self._cached_vtk_colors:
                del self._cached_vtk_colors[vtk_color_name]

            logger.debug("Removed custom mapping: %s", vtk_color_name)
            return True

        return False

    def get_vtk_manager_count(self) -> int:
        """
        Get the number of registered VTK managers.

        Returns:
            Number of registered VTK managers
        """
        return len(self._vtk_managers)

    def _on_theme_changed(self, theme: str, variant: str) -> None:
        """Handle theme change from theme service."""
        logger.debug("VTK provider handling theme change: %s/{variant}", theme)
        self.update_vtk_colors()

    def _on_colors_updated(self) -> None:
        """Handle colors updated from theme service."""
        logger.debug("VTK provider handling colors updated")
        self.update_vtk_colors()

    def log_vtk_color_info(self) -> None:
        """Log VTK color information for debugging."""
        theme, variant = self.theme_service.get_current_theme()
        vtk_colors = self.get_all_vtk_colors()

        logger.info("VTK Color Provider Info:")
        logger.info("  Current theme: %s/{variant}", theme)
        logger.info("  Registered VTK managers: %s", len(self._vtk_managers))
        logger.info("  Color mappings: %s", len(self._vtk_color_mapping))
        logger.info("  Cached colors: %s", len(self._cached_vtk_colors))
        logger.debug("  Available VTK colors: %s", list(vtk_colors.keys()))


# Global instance for easy access
_vtk_color_provider_instance = None


def get_vtk_color_provider() -> VTKColorProvider:
    """
    Get the global VTK color provider instance.

    Returns:
        VTKColorProvider instance
    """
    return VTKColorProvider.instance()


# Convenience function for backward compatibility
def vtk_rgb(color_name: str) -> Tuple[float, float, float]:
    """
    Get VTK RGB color by name (backward compatibility function).

    Args:
        color_name: VTK color name

    Returns:
        Tuple of normalized RGB values
    """
    return get_vtk_color_provider().get_vtk_color(color_name)
