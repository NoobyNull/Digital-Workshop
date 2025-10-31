"""
Qt-Material-Only Core Module

This module provides qt-material-focused core functionality, completely replacing
the legacy static color systems and presets. It contains only qt-material theme
definitions and color mappings with no legacy dependencies.

Key Features:
- qt-material theme definitions
- Color mapping from qt-material to application color names
- No legacy color systems or presets
- No circular dependencies
"""

from typing import Dict, List, Tuple, Any
from PySide6.QtCore import QObject, Signal, QSettings
from PySide6.QtGui import QColor
from src.core.logging_config import get_logger
from .theme_loader import get_theme_loader

logger = get_logger(__name__)


class QtMaterialThemeCore(QObject):
    """
    Qt-material-only theme core functionality.
    
    Provides qt-material theme definitions and color mappings without any
    legacy color system dependencies.
    """
    
    # Signals for theme changes
    theme_changed = Signal(str, str)  # theme, variant
    colors_updated = Signal()
    
    # Singleton instance
    _instance = None
    
    def __init__(self):
        """Initialize qt-material core with default theme."""
        super().__init__()
        
        # Settings storage
        self.settings = QSettings("Candy-Cadence", "3D-MM")
        
        # Current theme state
        self._current_theme = "dark"
        self._current_variant = "blue"
        
        # Qt-material theme definitions
        self._qt_material_themes = self._define_qt_material_themes()
        
        # Color mappings from qt-material to application colors
        self._color_mappings = self._define_color_mappings()
        
        logger.info("QtMaterialCore initialized with qt-material-only architecture")
    
    @classmethod
    def instance(cls) -> 'QtMaterialThemeCore':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _define_qt_material_themes(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        """
        Define qt-material theme configurations.
        
        Returns:
            Dictionary of qt-material themes, variants, and their color definitions
        """
        # Load themes from JSON configuration
        theme_loader = get_theme_loader()
        return theme_loader.get_available_themes()
    
    def _define_color_mappings(self) -> Dict[str, str]:
        """
        Define mappings from application color names to qt-material color names.
        
        Returns:
            Dictionary mapping application color names to qt-material color names
        """
        return {
            # Canvas and background colors
            "canvas_bg": "secondaryDarkColor",
            "canvas_top": "secondaryColor",
            "window_bg": "secondaryDarkColor",
            "surface": "secondaryColor",
            
            # Text colors
            "text": "primaryTextColor",
            "text_secondary": "secondaryTextColor",
            "text_primary": "primaryTextColor",
            "primary_text": "primaryTextColor",
            "secondary_text": "secondaryTextColor",
            
            # Primary colors
            "primary": "primaryColor",
            "primary_light": "primaryLightColor",
            "primary_dark": "primaryDarkColor",
            "primary_hover": "primaryLightColor",
            "primary_pressed": "primaryDarkColor",
            
            # Secondary colors
            "secondary": "secondaryColor",
            "secondary_light": "secondaryLightColor",
            "secondary_dark": "secondaryDarkColor",
            
            # Border and UI element colors
            "border": "secondaryLightColor",
            "border_light": "secondaryColor",
            "hover": "secondaryLightColor",
            "pressed": "primaryDarkColor",
            
            # Selection and focus colors
            "selection_bg": "primaryColor",
            "selection_text": "primaryTextColor",
            "focus": "primaryColor",
            
            # Status colors
            "success": "successColor",
            "warning": "warningColor",
            "error": "errorColor",
            "info": "infoColor",
            
            # Progress and specific UI elements
            "progress_chunk": "primaryColor",
            "tab_selected_border": "primaryColor",
            
            # VTK specific colors
            "light_color": "primaryLightColor",
            "edge_color": "primaryTextColor",
            "grid_color": "secondaryLightColor",
            "ground_color": "secondaryColor",
            "model_surface": "primaryColor"
        }
    
    def get_available_themes(self) -> Dict[str, List[str]]:
        """
        Get available qt-material themes and their variants.
        
        Returns:
            Dictionary of theme names and their available variants
        """
        # Handle both dictionary and list variants from theme loader
        result = {}
        for theme, variants in self._qt_material_themes.items():
            if isinstance(variants, dict):
                result[theme] = list(variants.keys())
            elif isinstance(variants, list):
                result[theme] = variants
            else:
                result[theme] = []
        return result
    
    def get_available_variants(self, theme: str) -> List[str]:
        """
        Get available variants for a specific theme.
        
        Args:
            theme: Theme name (e.g., "dark", "light")
            
        Returns:
            List of available variant names
        """
        return list(self._qt_material_themes.get(theme, {}).keys())
    
    def get_qt_material_colors(self, theme: str, variant: str) -> Dict[str, str]:
        """
        Get qt-material color definitions for a theme/variant.
        
        Args:
            theme: Theme name (e.g., "dark", "light")
            variant: Variant name (e.g., "blue", "amber", "cyan")
            
        Returns:
            Dictionary of qt-material color definitions
        """
        try:
            return self._qt_material_themes[theme][variant].copy()
        except KeyError:
            logger.warning(f"Theme/variant not found: {theme}/{variant}, using dark/blue")
            return self._qt_material_themes["dark"]["blue"].copy()
    
    def get_color(self, color_name: str, theme: str = None, variant: str = None) -> str:
        """
        Get a color value by name using qt-material theme.
        
        Args:
            color_name: Application color name (e.g., "primary", "canvas_bg")
            theme: Theme name (optional, uses current if None)
            variant: Variant name (optional, uses current if None)
            
        Returns:
            Hex color string
        """
        if theme is None:
            theme = self._current_theme
        if variant is None:
            variant = self._current_variant
        
        # Map application color name to qt-material color name
        qt_material_color = self._color_mappings.get(color_name, "primaryColor")
        
        # Get qt-material color definition
        theme_colors = self.get_qt_material_colors(theme, variant)
        
        return theme_colors.get(qt_material_color, "#1976D2")
    
    def get_all_colors(self, theme: str = None, variant: str = None) -> Dict[str, str]:
        """
        Get all application colors mapped from qt-material theme.
        
        Args:
            theme: Theme name (optional, uses current if None)
            variant: Variant name (optional, uses current if None)
            
        Returns:
            Dictionary of all application colors
        """
        if theme is None:
            theme = self._current_theme
        if variant is None:
            variant = self._current_variant
        
        # Get base qt-material colors
        qt_material_colors = self.get_qt_material_colors(theme, variant)
        
        # Map to application colors
        app_colors = {}
        for app_color_name, qt_color_name in self._color_mappings.items():
            app_colors[app_color_name] = qt_material_colors.get(qt_color_name, "#1976D2")
        
        return app_colors
    
    def get_qcolor(self, color_name: str, theme: str = None, variant: str = None) -> QColor:
        """
        Get a QColor for a named color.
        
        Args:
            color_name: Application color name
            theme: Theme name (optional, uses current if None)
            variant: Variant name (optional, uses current if None)
            
        Returns:
            QColor object
        """
        hex_color = self.get_color(color_name, theme, variant)
        return QColor(hex_color)
    
    def get_vtk_color(self, color_name: str, theme: str = None, variant: str = None) -> Tuple[float, float, float]:
        """
        Get a normalized RGB tuple (0..1) for VTK.
        
        Args:
            color_name: Application color name
            theme: Theme name (optional, uses current if None)
            variant: Variant name (optional, uses current if None)
            
        Returns:
            Tuple of normalized RGB values
        """
        hex_color = self.get_color(color_name, theme, variant)
        return self._hex_to_vtk_rgb(hex_color)
    
    @staticmethod
    def _hex_to_vtk_rgb(hex_color: str) -> Tuple[float, float, float]:
        """
        Convert hex color to VTK RGB tuple (0..1).
        
        Args:
            hex_color: Hex color string
            
        Returns:
            Tuple of normalized RGB values
        """
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    
    def set_theme(self, theme: str, variant: str = None) -> None:
        """
        Set the current theme and variant.
        
        Args:
            theme: Theme name (e.g., "dark", "light")
            variant: Variant name (optional, uses current if None)
        """
        if theme not in self._qt_material_themes:
            logger.error(f"Unknown theme: {theme}")
            return
        
        if variant is None:
            variant = self._current_variant
        
        if variant not in self._qt_material_themes[theme]:
            logger.error(f"Unknown variant: {variant} for theme: {theme}")
            return
        
        old_theme = self._current_theme
        old_variant = self._current_variant
        
        self._current_theme = theme
        self._current_variant = variant
        
        logger.info(f"Theme changed from {old_theme}/{old_variant} to {theme}/{variant}")
        
        # Emit signals
        self.theme_changed.emit(theme, variant)
        self.colors_updated.emit()
    
    def get_current_theme(self) -> Tuple[str, str]:
        """
        Get the current theme and variant.
        
        Returns:
            Tuple of (theme, variant)
        """
        return self._current_theme, self._current_variant
    
    def save_settings(self) -> None:
        """Save current theme settings."""
        self.settings.setValue("theme/current_theme", self._current_theme)
        self.settings.setValue("theme/current_variant", self._current_variant)
        logger.debug(f"Theme settings saved: {self._current_theme}/{self._current_variant}")
    
    def load_settings(self) -> None:
        """Load theme settings."""
        self._current_theme = self.settings.value("theme/current_theme", "dark", type=str)
        self._current_variant = self.settings.value("theme/current_variant", "blue", type=str)
        
        # Validate loaded settings
        if self._current_theme not in self._qt_material_themes:
            self._current_theme = "dark"
        if self._current_variant not in self._qt_material_themes.get(self._current_theme, {}):
            self._current_variant = "blue"
        
        logger.debug(f"Theme settings loaded: {self._current_theme}/{self._current_variant}")
    
    def export_theme(self, theme: str = None, variant: str = None) -> Dict[str, Any]:
        """
        Export theme configuration as dictionary.
        
        Args:
            theme: Theme name (optional, uses current if None)
            variant: Variant name (optional, uses current if None)
            
        Returns:
            Dictionary containing theme configuration
        """
        if theme is None:
            theme = self._current_theme
        if variant is None:
            variant = self._current_variant
        
        return {
            "theme": theme,
            "variant": variant,
            "colors": self.get_all_colors(theme, variant),
            "qt_material_colors": self.get_qt_material_colors(theme, variant)
        }
    
    def log_theme_info(self) -> None:
        """Log current theme information for debugging."""
        theme, variant = self.get_current_theme()
        colors = self.get_all_colors(theme, variant)
        
        logger.info(f"Current theme: {theme}/{variant}")
        logger.debug(f"Available themes: {list(self._qt_material_themes.keys())}")
        logger.debug(f"Available variants for {theme}: {list(self._qt_material_themes[theme].keys())}")
        logger.debug(f"Color count: {len(colors)}")