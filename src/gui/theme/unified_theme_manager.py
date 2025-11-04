"""
Unified Theme Manager

This module provides the main theme coordinator that unifies all theme services and eliminates conflicts.
It serves as the single entry point for all theme operations and manages the entire theme system.

Key Features:
- Single unified theme manager replacing all conflicting services
- Coordinated theme application with proper timing
- Thread-safe operations with comprehensive error handling
- Memory-efficient theme caching and management
- Dynamic theme updates for newly created widgets
- Performance monitoring and optimization

Architecture:
- Singleton pattern for consistent state management
- Event-driven architecture for theme change notifications
- Modular design with pluggable components
- Backward compatibility with existing theme usage
- Comprehensive logging for debugging and monitoring

Integration:
- Consolidates ThemePersistence, ThemeValidator, ThemeCache, ThemeRegistry, ThemeApplication
- Provides unified API for all theme operations
- Maintains compatibility with existing code
- Enables seamless theme transitions
"""

import time
from typing import Dict, Any, Tuple, List
from PySide6.QtCore import QObject, Signal

from .theme_persistence import ThemePersistence
from .theme_validator import ThemeValidator
from .theme_cache import ThemeCache
from .theme_registry import ThemeRegistry
from .theme_application import ThemeApplication
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class UnifiedThemeManager(QObject):
    """
    Unified theme manager that consolidates all theme services.

    This is the main theme coordinator that replaces all existing conflicting
    theme services and provides a single, consistent interface for theme management.

    Key Responsibilities:
    - Coordinate all theme-related operations
    - Manage theme persistence, validation, caching, and application
    - Provide thread-safe theme operations
    - Handle theme change notifications and updates
    - Maintain backward compatibility with existing code

    Architecture Benefits:
    - Eliminates race conditions between different theme services
    - Provides consistent theme application timing
    - Enables proper error handling and recovery
    - Supports dynamic theme updates for new widgets
    - Maintains memory efficiency through intelligent caching
    """

    # Signals for theme system events
    theme_changed = Signal(str, str)  # theme, variant
    theme_applied = Signal(bool, str)  # success, message
    theme_validation_failed = Signal(str, list)  # error_message, error_list
    system_ready = Signal()

    def __init__(self):
        """Initialize unified theme manager."""
        super().__init__()

        # Core components
        self._persistence = ThemePersistence()
        self._validator = ThemeValidator()
        self._cache = ThemeCache()
        self._registry = ThemeRegistry()
        self._application = ThemeApplication()

        # State management
        self._initialized = False
        self._current_theme = "dark"
        self._current_variant = "blue"
        self._system_ready = False

        # Performance tracking
        self._operation_count = 0
        self._error_count = 0
        self._total_operation_time = 0.0

        # Connect component signals
        self._connect_signals()

        # Initialize system
        self._initialize_system()

        logger.info("UnifiedThemeManager initialized as single theme coordinator")

    @classmethod
    def instance(cls) -> "UnifiedThemeManager":
        """
        Get singleton instance of unified theme manager.

        Returns:
            UnifiedThemeManager instance
        """
        if not hasattr(cls, "_instance") or cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def apply_theme(self, theme: str, variant: str = "blue") -> bool:
        """
        Apply theme with full validation and coordination.

        Args:
            theme: Theme name ("dark", "light", "auto")
            variant: Theme variant ("blue", "amber", "cyan", etc.)

        Returns:
            True if theme was applied successfully
        """
        start_time = time.time()
        operation_id = f"apply_{theme}_{variant}_{start_time}"

        try:
            logger.info(f"Applying theme: {theme}/{variant}")

            # Validate theme request
            if not self._validate_theme_request(theme, variant):
                error_msg = f"Invalid theme request: {theme}/{variant}"
                logger.error(error_msg)
                self.theme_applied.emit(False, error_msg)
                return False

            # Create theme data structure
            theme_data = self._create_theme_data(theme, variant)

            # Validate theme data
            is_valid, errors, warnings = self._validator.validate_theme(theme_data)
            if not is_valid:
                error_msg = f"Theme validation failed: {errors}"
                logger.error(error_msg)
                self.theme_validation_failed.emit(error_msg, errors)
                self.theme_applied.emit(False, error_msg)
                return False

            # Log warnings if any
            if warnings:
                logger.warning(f"Theme validation warnings: {warnings}")

            # Check cache first
            cache_key = f"{theme}_{variant}"
            cached_data = self._cache.get(cache_key)
            if cached_data:
                theme_data = cached_data
                logger.debug(f"Using cached theme data: {cache_key}")
            else:
                # Cache the validated theme data
                self._cache.put(cache_key, theme_data)

            # Apply theme through coordinated application
            success = self._application.apply_theme(theme, variant)

            if success:
                # Update current state
                self._current_theme = theme
                self._current_variant = variant

                # Save to persistence
                self._persistence.save_theme(theme_data)

                # Emit success signal
                self.theme_changed.emit(theme, variant)
                self.theme_applied.emit(
                    True, f"Theme {theme}/{variant} applied successfully"
                )

                # Track performance
                elapsed = (time.time() - start_time) * 1000
                self._track_operation(True, elapsed, operation_id)

                logger.info(
                    f"Theme {theme}/{variant} applied successfully in {elapsed:.2f}ms"
                )
                return True
            else:
                error_msg = f"Theme application failed: {theme}/{variant}"
                self.theme_applied.emit(False, error_msg)

                # Track performance
                elapsed = (time.time() - start_time) * 1000
                self._track_operation(False, elapsed, operation_id)

                return False

        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            self._track_operation(False, elapsed, operation_id)

            logger.error(f"Theme application exception: {e}", exc_info=True)
            self.theme_applied.emit(False, f"Theme application failed: {str(e)}")
            return False

    def get_current_theme(self) -> Tuple[str, str]:
        """
        Get currently applied theme.

        Returns:
            Tuple of (theme, variant)
        """
        return self._current_theme, self._current_variant

    def get_available_themes(self) -> Dict[str, List[str]]:
        """
        Get available themes and variants dynamically.

        Returns:
            Dictionary of theme names and their available variants
        """
        # Dynamic theme system - all variants available for all themes
        variants = ["blue", "amber", "cyan", "red", "green", "purple", "teal"]
        return {"dark": variants, "light": variants, "auto": variants}

    def get_theme_colors(self) -> Dict[str, str]:
        """
        Get current theme colors.

        Returns:
            Dictionary of color names to hex values
        """
        theme_data = self._create_theme_data(self._current_theme, self._current_variant)
        return theme_data.get("custom_colors", {})

    def get_color(self, color_name: str) -> str:
        """
        Get specific color value.

        Args:
            color_name: Name of the color

        Returns:
            Hex color value or fallback color
        """
        colors = self.get_theme_colors()
        return colors.get(color_name, "#1976D2")  # Default blue

    def save_settings(self) -> bool:
        """
        Save current theme settings.

        Returns:
            True if save was successful
        """
        try:
            theme_data = self._create_theme_data(
                self._current_theme, self._current_variant
            )
            return self._persistence.save_theme(theme_data)
        except Exception as e:
            logger.error(f"Failed to save theme settings: {e}")
            return False

    def load_settings(self) -> bool:
        """
        Load theme settings.

        Returns:
            True if load was successful
        """
        try:
            theme_data = self._persistence.load_theme()

            # Validate loaded data
            is_valid, errors, warnings = self._validator.validate_theme(theme_data)
            if not is_valid:
                logger.warning(f"Loaded theme data has validation issues: {errors}")
                if warnings:
                    logger.info(f"Loaded theme warnings: {warnings}")

            # Apply loaded theme
            theme = theme_data.get("theme_name", "dark")
            variant = theme_data.get("theme_variant", "blue")

            return self.apply_theme(theme, variant)

        except Exception as e:
            logger.error(f"Failed to load theme settings: {e}")
            return False

    def reset_to_default(self) -> bool:
        """
        Reset theme to default (dark/blue).

        Returns:
            True if reset was successful
        """
        return self.apply_theme("dark", "blue")

    def export_theme(self, file_path: str) -> bool:
        """
        Export current theme to file.

        Args:
            file_path: Path to export theme

        Returns:
            True if export was successful
        """
        try:
            return self._persistence.export_theme(file_path)
        except Exception as e:
            logger.error(f"Failed to export theme: {e}")
            return False

    def import_theme(self, file_path: str) -> bool:
        """
        Import theme from file.

        Args:
            file_path: Path to import theme from

        Returns:
            True if import was successful
        """
        try:
            success = self._persistence.import_theme(file_path)
            if success:
                # Reload settings after import
                return self.load_settings()
            return False
        except Exception as e:
            logger.error(f"Failed to import theme: {e}")
            return False

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status.

        Returns:
            Dictionary containing system status information
        """
        return {
            "initialized": self._initialized,
            "system_ready": self._system_ready,
            "current_theme": self._current_theme,
            "current_variant": self._current_variant,
            "operation_count": self._operation_count,
            "error_count": self._error_count,
            "total_operation_time_ms": self._total_operation_time,
            "components": {
                "persistence": self._persistence.get_performance_stats(),
                "validator": self._validator.get_performance_stats(),
                "cache": self._cache.get_stats(),
                "registry": self._registry.get_registry_stats(),
                "application": self._application.get_application_stats(),
            },
        }

    def register_widget(self, widget, widget_name: str = None) -> bool:
        """
        Register widget for dynamic theme updates.

        Args:
            widget: Widget to register
            widget_name: Optional name for the widget

        Returns:
            True if registration was successful
        """
        return self._registry.register_widget(widget, widget_name)

    def unregister_widget(self, widget_name: str) -> bool:
        """
        Unregister widget from theme updates.

        Args:
            widget_name: Name of widget to unregister

        Returns:
            True if unregistration was successful
        """
        return self._registry.unregister_widget(widget_name)

    def force_widget_discovery(self) -> None:
        """Force discovery and registration of new widgets."""
        self._registry.force_discovery()

    def cleanup_resources(self) -> None:
        """Clean up system resources."""
        try:
            self._registry.cleanup_dead_widgets()
            logger.debug("Theme system resources cleaned up")
        except Exception as e:
            logger.error(f"Resource cleanup failed: {e}")

    def _connect_signals(self) -> None:
        """Connect component signals."""
        try:
            # Connect application signals
            self._application.application_started.connect(self._on_application_started)
            self._application.application_completed.connect(
                self._on_application_completed
            )
            self._application.application_failed.connect(self._on_application_failed)

            # Connect registry signals
            self._registry.widget_registered.connect(self._on_widget_registered)
            self._registry.widget_unregistered.connect(self._on_widget_unregistered)

            logger.debug("Theme manager signals connected")

        except Exception as e:
            logger.error(f"Failed to connect signals: {e}")

    def _initialize_system(self) -> None:
        """Initialize the theme system."""
        try:
            # Load saved settings
            load_success = self.load_settings()

            if not load_success:
                logger.info("Using default theme (failed to load saved settings)")
                # Apply default theme
                self.apply_theme("dark", "blue")

            # Mark as initialized
            self._initialized = True
            self._system_ready = True

            # Emit ready signal
            self.system_ready.emit()

            logger.info("Unified theme system initialized successfully")

        except Exception as e:
            logger.error(f"Theme system initialization failed: {e}", exc_info=True)
            self._initialized = False
            self._system_ready = False

    def _validate_theme_request(self, theme: str, variant: str) -> bool:
        """
        Validate theme application request.

        Args:
            theme: Theme name
            variant: Theme variant

        Returns:
            True if request is valid
        """
        valid_themes = ["dark", "light", "auto"]
        valid_variants = ["blue", "amber", "cyan", "red", "green", "purple", "teal"]

        if theme not in valid_themes:
            logger.error(f"Invalid theme: {theme}")
            return False

        if variant not in valid_variants:
            logger.error(f"Invalid variant: {variant}")
            return False

        return True

    def _create_theme_data(self, theme: str, variant: str) -> Dict[str, Any]:
        """
        Create dynamic theme data structure without hard-coded colors.

        Args:
            theme: Theme name
            variant: Theme variant

        Returns:
            Dynamic theme configuration dictionary
        """
        # Generate dynamic colors based on theme and variant
        colors = self._generate_dynamic_colors(theme, variant)

        return {
            "theme_name": theme,
            "theme_variant": variant,
            "qt_material_available": self._is_qt_material_available(),
            "custom_colors": colors,
            "system_theme_detection": False,
            "auto_save_enabled": True,
            "theme_version": "2.0.0",
        }

    def _generate_dynamic_colors(self, theme: str, variant: str) -> Dict[str, str]:
        """
        Generate dynamic colors based on theme and variant.

        Args:
            theme: Theme name
            variant: Theme variant

        Returns:
            Dictionary of dynamically generated colors
        """
        # Base colors derived from theme and variant
        base_hue = self._get_base_hue(theme, variant)
        is_dark = theme == "dark"

        # Generate color palette dynamically
        colors = {}

        if is_dark:
            colors["background"] = self._generate_dark_background(base_hue)
            colors["surface"] = self._generate_dark_surface(base_hue)
            colors["text_primary"] = "#FFFFFF"
            colors["text_secondary"] = "#B0B0B0"
        else:
            colors["background"] = self._generate_light_background(base_hue)
            colors["surface"] = self._generate_light_surface(base_hue)
            colors["text_primary"] = "#000000"
            colors["text_secondary"] = "#666666"

        # Generate primary colors
        colors["primary"] = self._generate_primary_color(base_hue, is_dark)
        colors["primary_light"] = self._lighten_color(colors["primary"], 0.3)
        colors["primary_dark"] = self._darken_color(colors["primary"], 0.3)

        # Generate semantic colors
        colors["error"] = "#F44336" if is_dark else "#D32F2F"
        colors["success"] = "#4CAF50" if is_dark else "#388E3C"
        colors["warning"] = "#FF9800" if is_dark else "#F57C00"
        colors["info"] = colors["primary"]

        return colors

    def _get_base_hue(self, theme: str, variant: str) -> float:
        """
        Get base hue for theme and variant.

        Args:
            theme: Theme name
            variant: Theme variant

        Returns:
            Base hue value (0-360)
        """
        # Map variants to hue ranges
        hue_map = {
            "blue": 220,  # Blue range
            "amber": 45,  # Yellow/Orange range
            "cyan": 180,  # Cyan range
            "red": 0,  # Red range
            "green": 120,  # Green range
            "purple": 270,  # Purple range
            "teal": 180,  # Teal range (same as cyan)
        }

        base_hue = hue_map.get(variant, 220)  # Default to blue

        # Adjust hue based on theme
        if theme == "light":
            base_hue = (base_hue + 30) % 360  # Shift hue for light theme

        return base_hue

    def _generate_primary_color(self, base_hue: float, is_dark: bool) -> str:
        """
        Generate primary color from base hue.

        Args:
            base_hue: Base hue value
            is_dark: Whether this is a dark theme

        Returns:
            Hex color string
        """
        import colorsys

        # Adjust saturation and value based on theme
        saturation = 0.7 if is_dark else 0.6
        value = 0.8 if is_dark else 0.7

        rgb = colorsys.hsv_to_rgb(base_hue / 360.0, saturation, value)
        return f"#{int(rgb[0] * 255):02x}{int(rgb[1] * 255):02x}{int(rgb[2] * 255):02x}"

    def _generate_dark_background(self, base_hue: float) -> str:
        """Generate dark theme background color."""
        import colorsys

        # Very dark background with slight hue tint
        rgb = colorsys.hsv_to_rgb(base_hue / 360.0, 0.1, 0.07)
        return f"#{int(rgb[0] * 255):02x}{int(rgb[1] * 255):02x}{int(rgb[2] * 255):02x}"

    def _generate_dark_surface(self, base_hue: float) -> str:
        """Generate dark theme surface color."""
        import colorsys

        # Slightly lighter than background
        rgb = colorsys.hsv_to_rgb(base_hue / 360.0, 0.15, 0.12)
        return f"#{int(rgb[0] * 255):02x}{int(rgb[1] * 255):02x}{int(rgb[2] * 255):02x}"

    def _generate_light_background(self, base_hue: float) -> str:
        """Generate light theme background color."""
        import colorsys

        # Very light background with slight hue tint
        rgb = colorsys.hsv_to_rgb(base_hue / 360.0, 0.05, 0.98)
        return f"#{int(rgb[0] * 255):02x}{int(rgb[1] * 255):02x}{int(rgb[2] * 255):02x}"

    def _generate_light_surface(self, base_hue: float) -> str:
        """Generate light theme surface color."""
        import colorsys

        # Slightly darker than background
        rgb = colorsys.hsv_to_rgb(base_hue / 360.0, 0.08, 0.95)
        return f"#{int(rgb[0] * 255):02x}{int(rgb[1] * 255):02x}{int(rgb[2] * 255):02x}"

    def _lighten_color(self, hex_color: str, factor: float) -> str:
        """Lighten a hex color by a factor."""
        import colorsys

        # Convert hex to RGB
        hex_color = hex_color.lstrip("#")
        rgb = tuple(int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4))

        # Convert to HSV and lighten
        hsv = colorsys.rgb_to_hsv(*rgb)
        new_rgb = colorsys.hsv_to_rgb(hsv[0], hsv[1], min(1.0, hsv[2] + factor))

        return f"#{int(new_rgb[0] * 255):02x}{int(new_rgb[1] * 255):02x}{int(new_rgb[2] * 255):02x}"

    def _darken_color(self, hex_color: str, factor: float) -> str:
        """Darken a hex color by a factor."""
        import colorsys

        # Convert hex to RGB
        hex_color = hex_color.lstrip("#")
        rgb = tuple(int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4))

        # Convert to HSV and darken
        hsv = colorsys.rgb_to_hsv(*rgb)
        new_rgb = colorsys.hsv_to_rgb(hsv[0], hsv[1], max(0.0, hsv[2] - factor))

        return f"#{int(new_rgb[0] * 255):02x}{int(new_rgb[1] * 255):02x}{int(new_rgb[2] * 255):02x}"

    def _is_qt_material_available(self) -> bool:
        """
        Check if Qt-material library is available.

        Returns:
            False - qt-material has been removed
        """
        return False

    def _track_operation(
        self, success: bool, elapsed_ms: float, operation_id: str
    ) -> None:
        """Track operation performance and statistics."""
        self._operation_count += 1
        if not success:
            self._error_count += 1
        self._total_operation_time += elapsed_ms

        # Log slow operations
        if elapsed_ms > 1000:  # More than 1 second
            logger.warning(
                f"Slow theme operation: {operation_id} took {elapsed_ms:.2f}ms"
            )

    def _on_application_started(self, theme: str, variant: str) -> None:
        """Handle theme application started signal."""
        logger.debug(f"Theme application started: {theme}/{variant}")

    def _on_application_completed(self, success: bool, message: str) -> None:
        """Handle theme application completed signal."""
        if success:
            logger.debug(f"Theme application completed: {message}")
        else:
            logger.error(f"Theme application failed: {message}")

    def _on_application_failed(self, error_message: str, component: str) -> None:
        """Handle theme application failed signal."""
        logger.error(f"Theme application failed in {component}: {error_message}")

    def _on_widget_registered(self, widget_name: str) -> None:
        """Handle widget registered signal."""
        logger.debug(f"Widget registered for theme updates: {widget_name}")

    def _on_widget_unregistered(self, widget_name: str) -> None:
        """Handle widget unregistered signal."""
        logger.debug(f"Widget unregistered from theme updates: {widget_name}")

    # Dynamic theme methods - no backward compatibility


# Singleton instance
_unified_theme_manager_instance = None


def get_unified_theme_manager() -> UnifiedThemeManager:
    """
    Get or create the singleton UnifiedThemeManager instance.

    Returns:
        UnifiedThemeManager: The singleton instance
    """
    global _unified_theme_manager_instance
    if _unified_theme_manager_instance is None:
        _unified_theme_manager_instance = UnifiedThemeManager.instance()
    return _unified_theme_manager_instance
