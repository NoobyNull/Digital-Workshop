"""
Theme Color Helper - Centralized theme color access for all UI components.

This module provides a singleton helper class for accessing theme colors
with proper fallback handling, eliminating code duplication across the UI.
"""

from typing import Dict, Optional


class ThemeColorHelper:
    """
    Centralized theme color access with automatic fallback.
    
    This singleton class provides a consistent interface for accessing
    theme colors across all UI components, with proper error handling
    and fallback colors when the theme system is unavailable.
    
    Usage:
        from src.gui.theme.color_helper import ThemeColorHelper
        
        helper = ThemeColorHelper.instance()
        border_color = helper.get_color('border')
    """
    
    _instance: Optional['ThemeColorHelper'] = None
    _theme_manager = None
    
    # Fallback colors when theme system is unavailable
    FALLBACK_COLORS: Dict[str, str] = {
        'border': '#cccccc',
        'warning': '#ffa500',
        'error': '#ff6b6b',
        'success': '#4caf50',
        'info': '#2196f3',
        'text_primary': '#000000',
        'text_secondary': '#666666',
        'background': '#ffffff',
        'primary': '#1976D2',
        'secondary': '#424242',
        'accent': '#ff4081'
    }
    
    def __init__(self):
        """Private constructor - use instance() instead."""
        if ThemeColorHelper._instance is not None:
            raise RuntimeError("Use ThemeColorHelper.instance() instead")
    
    @classmethod
    def instance(cls) -> 'ThemeColorHelper':
        """
        Get the singleton instance of ThemeColorHelper.
        
        Returns:
            ThemeColorHelper: The singleton instance
        """
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls._instance.initialize()
        return cls._instance
    
    def initialize(self) -> None:
        """Initialize the theme manager connection."""
        self._theme_manager = None
        self._try_connect_theme_manager()
    
    def _try_connect_theme_manager(self) -> None:
        """Attempt to connect to the theme service."""
        if self._theme_manager is not None:
            return
        
        try:
            from src.gui.theme.simple_service import ThemeService
            self._theme_manager = ThemeService.instance()
        except Exception:
            # Theme service not available, will use fallbacks
            pass
    
    def get_color(self, color_name: str) -> str:
        """
        Get a theme color by name with automatic fallback.
        
        Args:
            color_name: The name of the color to retrieve
            
        Returns:
            str: Hex color code (e.g., '#1976D2')
            
        Examples:
            >>> helper = ThemeColorHelper.instance()
            >>> helper.get_color('border')
            '#cccccc'
            >>> helper.get_color('primary')
            '#1976D2'
        """
        # Try to get from theme manager first
        if self._theme_manager:
            try:
                color = self._theme_manager.get_color(color_name)
                if color:
                    return color
            except Exception:
                # Theme manager failed, continue to fallback
                pass
        
        # Use fallback color
        return self.FALLBACK_COLORS.get(color_name, '#1976D2')
    
    def get_colors(self, *color_names: str) -> Dict[str, str]:
        """
        Get multiple theme colors at once.
        
        Args:
            *color_names: Variable number of color names to retrieve
            
        Returns:
            Dict[str, str]: Dictionary mapping color names to hex codes
            
        Example:
            >>> helper = ThemeColorHelper.instance()
            >>> colors = helper.get_colors('border', 'warning', 'error')
            >>> colors['border']
            '#cccccc'
        """
        return {name: self.get_color(name) for name in color_names}
    
    def reset(self) -> None:
        """Reset the theme manager connection (useful for testing)."""
        self._theme_manager = None
        self._try_connect_theme_manager()


# Convenience function for quick access
def get_theme_color(color_name: str) -> str:
    """
    Convenience function to get a theme color.
    
    Args:
        color_name: The name of the color to retrieve
        
    Returns:
        str: Hex color code
        
    Example:
        >>> from src.gui.theme.color_helper import get_theme_color
        >>> border = get_theme_color('border')
    """
    return ThemeColorHelper.instance().get_color(color_name)