"""
Qt-Material-Only Theme Service

This module provides a simplified qt-material-only theme service that replaces
the current ThemeService. It focuses ONLY on qt-material operations with no
legacy support, eliminating all circular dependencies.

Key Features:
- Direct qt-material library integration
- No legacy color management
- Built-in VTK color provider
- Settings persistence via QSettings
- No ThemeManager references or circular dependencies
"""

import time
from typing import Dict, List, Tuple, Any
from PySide6.QtCore import QObject, Signal, QSettings
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class QtMaterialThemeService(QObject):
    """
    Qt-material-only theme service.
    
    Provides unified theme management using only qt-material library with
    no legacy dependencies or circular references.
    """
    
    # Signals for theme changes
    theme_changed = Signal(str, str)  # theme, variant
    colors_updated = Signal()
    theme_applied = Signal(bool)  # success
    
    # Singleton instance
    _instance = None
    
    def __init__(self):
        """Initialize qt-material theme service."""
        super().__init__()
        
        # Import qt-material library with graceful fallback
        self.qtmaterial = None
        self.qtmaterial_available = False
        try:
            import qtmaterial
            self.qtmaterial = qtmaterial
            self.qtmaterial_available = True
            logger.info("qt-material library loaded successfully")
        except ImportError as e:
            logger.warning(f"qt-material library not available: {e}")
            logger.info("Application will use fallback theme system")
            self.qtmaterial = None
            self.qtmaterial_available = False
        except Exception as e:
            logger.error(f"Unexpected error importing qt-material: {e}")
            logger.info("Application will use fallback theme system")
            self.qtmaterial = None
            self.qtmaterial_available = False
        
        # Import core module
        from .qt_material_core import QtMaterialThemeCore
        self.core = QtMaterialThemeCore.instance()
        
        # Connect to core signals
        self.core.theme_changed.connect(self._on_theme_changed)
        self.core.colors_updated.connect(self._on_colors_updated)
        
        # Performance tracking
        self._last_theme_change_time = 0
        self._theme_change_count = 0
        
        # Initialize settings
        self.settings = QSettings("Candy-Cadence", "3D-MM")
        
        # Load saved theme
        self.load_settings()
        
        logger.info("QtMaterialThemeService initialized with qt-material-only architecture")
    
    @classmethod
    def instance(cls) -> 'QtMaterialThemeService':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def apply_theme(self, theme: str, variant: str = None) -> bool:
        """
        Apply a qt-material theme to the application.
        
        Args:
            theme: Theme name (e.g., "dark", "light", "auto")
            variant: Variant name (e.g., "blue", "amber", "cyan")
            
        Returns:
            True if theme was applied successfully
        """
        start_time = time.time()
        
        try:
            # Handle auto theme detection
            if theme == "auto":
                theme = self._detect_system_theme()
                logger.info(f"Auto-detected system theme: {theme}")
            
            # Validate theme and variant
            available_themes = self.core.get_available_themes()
            if theme not in available_themes:
                logger.error(f"Unknown theme: {theme}")
                return False
            
            if variant is None:
                variant = self.core.get_current_theme()[1]
            
            if variant not in available_themes[theme]:
                logger.error(f"Unknown variant: {variant} for theme: {theme}")
                return False
            
            # Apply qt-material theme if library is available
            if self.qtmaterial_available and self.qtmaterial:
                try:
                    self._apply_qt_material_theme(theme, variant)
                except Exception as e:
                    logger.warning(f"qt-material theme application failed: {e}")
                    logger.info("Falling back to basic theme system")
                    self._apply_fallback_theme(theme, variant)
            else:
                # Apply fallback theme when qt-material is not available
                self._apply_fallback_theme(theme, variant)
            
            # Update core theme
            self.core.set_theme(theme, variant)
            
            # Track performance
            elapsed = (time.time() - start_time) * 1000
            self._last_theme_change_time = elapsed
            self._theme_change_count += 1
            
            logger.info(f"Theme {theme}/{variant} applied in {elapsed:.2f}ms")
            
            # Emit signals
            self.theme_applied.emit(True)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply theme {theme}/{variant}: {e}", exc_info=True)
            self.theme_applied.emit(False)
            return False
    
    def _apply_qt_material_theme(self, theme: str, variant: str = None) -> None:
        """
        Apply qt-material theme using the qt-material library.
        
        Args:
            theme: Theme name
            variant: Variant name (currently unused, reserved for future use)
        """
        _ = variant  # Mark as used to avoid lint warning
        if not self.qtmaterial or not self.qtmaterial_available:
            logger.warning("qt-material library not available for theme application")
            return
        
        try:
            # Map theme names to qt-material theme names
            qt_theme_mapping = {
                "dark": "dark_teal",
                "light": "light_cyan",
                "auto": "dark_teal"  # Default to dark for auto
            }
            qt_theme = qt_theme_mapping.get(theme, "dark_teal")
            
            # Apply qt-material theme
            app = QApplication.instance()
            if app:
                stylesheet = self.qtmaterial.apply_stylesheet(app, theme=qt_theme)
                app.setStyleSheet(stylesheet)
                logger.debug(f"qt-material theme applied: {qt_theme}")
            else:
                logger.warning("No QApplication instance available for qt-material theme")
            
        except Exception as e:
            logger.warning(f"Failed to apply qt-material theme: {e}")
            raise
    
    def _apply_fallback_theme(self, theme: str, variant: str = None) -> None:
        """
        Apply fallback theme when qt-material library is not available.
        
        Args:
            theme: Theme name
            variant: Variant name
        """
        try:
            app = QApplication.instance()
            if app:
                # Enhanced fallback styling with variant support
                if theme == "dark":
                    if variant == "amber":
                        primary_color = "#FFA000"
                        primary_light = "#FFB74D"
                        primary_dark = "#FF8F00"
                    elif variant == "cyan":
                        primary_color = "#00ACC1"
                        primary_light = "#4DD0E1"
                        primary_dark = "#00838F"
                    else:  # blue default
                        primary_color = "#1976D2"
                        primary_light = "#42A5F5"
                        primary_dark = "#1565C0"
                    
                    stylesheet = f"""
                    QWidget {{
                        background-color: #121212;
                        color: #FFFFFF;
                    }}
                    QPushButton {{
                        background-color: {primary_color};
                        color: white;
                        border: none;
                        padding: 5px;
                        border-radius: 2px;
                    }}
                    QPushButton:hover {{
                        background-color: {primary_light};
                    }}
                    QPushButton:pressed {{
                        background-color: {primary_dark};
                    }}
                    QLineEdit {{
                        background-color: #1E1E1E;
                        color: #FFFFFF;
                        border: 1px solid #333333;
                        padding: 3px;
                        border-radius: 2px;
                    }}
                    QTabWidget::pane {{
                        border: 1px solid #333333;
                        background: #1E1E1E;
                    }}
                    QTabBar::tab {{
                        background: #2E2E2E;
                        color: #FFFFFF;
                        padding: 5px 10px;
                        border: 1px solid #333333;
                    }}
                    QTabBar::tab:selected {{
                        background: {primary_color};
                    }}
                    """
                else:  # light theme
                    if variant == "amber":
                        primary_color = "#FFA000"
                        primary_light = "#FFB74D"
                        primary_dark = "#FF8F00"
                    elif variant == "cyan":
                        primary_color = "#00ACC1"
                        primary_light = "#4DD0E1"
                        primary_dark = "#00838F"
                    else:  # blue default
                        primary_color = "#1976D2"
                        primary_light = "#42A5F5"
                        primary_dark = "#1565C0"
                    
                    stylesheet = f"""
                    QWidget {{
                        background-color: #FFFFFF;
                        color: #000000;
                    }}
                    QPushButton {{
                        background-color: {primary_color};
                        color: white;
                        border: none;
                        padding: 5px;
                        border-radius: 2px;
                    }}
                    QPushButton:hover {{
                        background-color: {primary_light};
                    }}
                    QPushButton:pressed {{
                        background-color: {primary_dark};
                    }}
                    QLineEdit {{
                        background-color: #F5F5F5;
                        color: #000000;
                        border: 1px solid #CCCCCC;
                        padding: 3px;
                        border-radius: 2px;
                    }}
                    QTabWidget::pane {{
                        border: 1px solid #CCCCCC;
                        background: #F5F5F5;
                    }}
                    QTabBar::tab {{
                        background: #E0E0E0;
                        color: #000000;
                        padding: 5px 10px;
                        border: 1px solid #CCCCCC;
                    }}
                    QTabBar::tab:selected {{
                        background: {primary_color};
                        color: white;
                    }}
                    """
                app.setStyleSheet(stylesheet)
                logger.info(f"Applied fallback {theme}/{variant} theme")
            else:
                logger.warning("No QApplication instance available for fallback theme")
        except Exception as e:
            logger.warning(f"Failed to apply fallback theme: {e}")
    
    def _detect_system_theme(self) -> str:
        """
        Detect system theme (light/dark).
        
        Returns:
            "dark" or "light"
        """
        try:
            # Try to detect from system settings
            import sys
            if sys.platform == "win32":
                import winreg
                try:
                    registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                    key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                    value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                    winreg.CloseKey(key)
                    return "light" if value == 1 else "dark"
                except Exception:
                    pass
            elif sys.platform == "darwin":
                # macOS theme detection
                try:
                    import subprocess
                    result = subprocess.run(
                        ["defaults", "read", "-g", "AppleInterfaceStyle"],
                        capture_output=True, text=True, check=False
                    )
                    return "dark" if "Dark" in result.stdout else "light"
                except Exception:
                    pass
            
            # Default to dark theme
            return "dark"
            
        except Exception:
            return "dark"
    
    def get_current_theme(self) -> Tuple[str, str]:
        """
        Get the current theme and variant.
        
        Returns:
            Tuple of (theme, variant)
        """
        return self.core.get_current_theme()
    
    def get_available_themes(self) -> Dict[str, List[str]]:
        """
        Get available qt-material themes and their variants.
        
        Returns:
            Dictionary of theme names and their available variants
        """
        themes = self.core.get_available_themes()
        # Add auto theme option
        themes["auto"] = ["blue", "amber", "cyan"]
        return themes
    
    def get_available_variants(self, theme: str) -> List[str]:
        """
        Get available variants for a specific theme.
        
        Args:
            theme: Theme name
            
        Returns:
            List of available variant names
        """
        if theme == "auto":
            return ["blue", "amber", "cyan"]
        return self.core.get_available_variants(theme)
    
    def get_color(self, color_name: str) -> str:
        """
        Get a color value by name.
        
        Args:
            color_name: Application color name
            
        Returns:
            Hex color string
        """
        return self.core.get_color(color_name)
    
    def get_all_colors(self) -> Dict[str, str]:
        """
        Get all application colors.
        
        Returns:
            Dictionary of all application colors
        """
        return self.core.get_all_colors()
    
    def get_qcolor(self, color_name: str) -> QColor:
        """
        Get a QColor for a named color.
        
        Args:
            color_name: Application color name
            
        Returns:
            QColor object
        """
        return self.core.get_qcolor(color_name)
    
    def get_vtk_color(self, color_name: str) -> Tuple[float, float, float]:
        """
        Get a normalized RGB tuple (0..1) for VTK.
        
        Args:
            color_name: Application color name
            
        Returns:
            Tuple of normalized RGB values
        """
        return self.core.get_vtk_color(color_name)
    
    def set_theme_variant(self, variant: str) -> bool:
        """
        Change only the variant of the current theme.
        
        Args:
            variant: Variant name
            
        Returns:
            True if variant was changed successfully
        """
        current_theme, _ = self.core.get_current_theme()
        return self.apply_theme(current_theme, variant)
    
    def cycle_theme(self) -> bool:
        """
        Cycle through available themes.
        
        Returns:
            True if theme was changed successfully
        """
        themes = list(self.get_available_themes().keys())
        current_theme, current_variant = self.core.get_current_theme()
        
        # Find next theme
        current_index = themes.index(current_theme) if current_theme in themes else 0
        next_index = (current_index + 1) % len(themes)
        next_theme = themes[next_index]
        
        # Use current variant for new theme if available
        variants = self.get_available_variants(next_theme)
        next_variant = current_variant if current_variant in variants else variants[0]
        
        return self.apply_theme(next_theme, next_variant)
    
    def cycle_variant(self) -> bool:
        """
        Cycle through variants of the current theme.
        
        Returns:
            True if variant was changed successfully
        """
        current_theme, current_variant = self.core.get_current_theme()
        variants = self.get_available_variants(current_theme)
        
        # Find next variant
        current_index = variants.index(current_variant) if current_variant in variants else 0
        next_index = (current_index + 1) % len(variants)
        next_variant = variants[next_index]
        
        return self.apply_theme(current_theme, next_variant)
    
    def save_settings(self) -> None:
        """Save current theme settings."""
        self.core.save_settings()
        logger.debug("Theme service settings saved")
    
    def load_settings(self) -> None:
        """Load theme settings."""
        self.core.load_settings()
        
        # Apply loaded theme
        theme, variant = self.core.get_current_theme()
        self.apply_theme(theme, variant)
        
        logger.debug(f"Theme service settings loaded: {theme}/{variant}")
    
    def get_theme_info(self) -> Dict[str, Any]:
        """
        Get comprehensive theme information.
        
        Returns:
            Dictionary containing theme information
        """
        theme, variant = self.core.get_current_theme()
        return {
            "current_theme": theme,
            "current_variant": variant,
            "available_themes": self.get_available_themes(),
            "theme_change_count": self._theme_change_count,
            "last_theme_change_time_ms": self._last_theme_change_time,
            "qt_material_available": self.qtmaterial is not None,
            "all_colors": self.get_all_colors()
        }
    
    def export_theme(self, theme: str = None, variant: str = None) -> Dict[str, Any]:
        """
        Export theme configuration.
        
        Args:
            theme: Theme name (optional, uses current if None)
            variant: Variant name (optional, uses current if None)
            
        Returns:
            Dictionary containing theme configuration
        """
        return self.core.export_theme(theme, variant)
    
    def reset_to_default(self) -> bool:
        """
        Reset theme to default (dark/blue).
        
        Returns:
            True if reset was successful
        """
        return self.apply_theme("dark", "blue")
    
    def _on_theme_changed(self, theme: str, variant: str) -> None:
        """Handle theme change from core."""
        logger.debug(f"Theme changed signal received: {theme}/{variant}")
        self.theme_changed.emit(theme, variant)
    
    def _on_colors_updated(self) -> None:
        """Handle colors updated from core."""
        logger.debug("Colors updated signal received")
        self.colors_updated.emit()
    
    def log_performance_stats(self) -> None:
        """Log performance statistics."""
        logger.info("Theme service performance stats:")
        logger.info(f"  Theme changes: {self._theme_change_count}")
        logger.info(f"  Last change time: {self._last_theme_change_time:.2f}ms")
        logger.info(f"  Current theme: {self.core.get_current_theme()}")
        logger.info(f"  qt-material available: {self.qtmaterial is not None}")


# Backward compatibility alias
ThemeService = QtMaterialThemeService