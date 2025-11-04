"""
Enhanced Legacy ThemeManager Compatibility Layer

This module provides a comprehensive backward compatibility layer for the legacy
ThemeManager system, ensuring smooth migration to qt-material while maintaining
all existing functionality.

Key Features:
- Full backward compatibility with existing ThemeManager API
- Seamless delegation to UnifiedThemeManager
- Enhanced error handling and logging
- Migration warnings and guidance
- Performance monitoring and optimization
- Thread-safe operations

Migration Strategy:
1. This compatibility layer allows existing code to continue working
2. Gradual migration of individual components to UnifiedThemeManager
3. Eventually phase out legacy usage once all components are migrated
"""

import threading
from typing import Dict, Any, Tuple
from PySide6.QtCore import QObject, Signal

from src.core.logging_config import get_logger
from .unified_theme_manager import get_unified_theme_manager

logger = get_logger(__name__)


class LegacyThemeManager(QObject):
    """
    Enhanced legacy ThemeManager compatibility class.

    Provides full backward compatibility for all existing ThemeManager usage
    while delegating to the UnifiedThemeManager for actual implementation.

    This class ensures that existing code continues to work during the migration
    period while providing warnings and guidance for migration.
    """

    # Signals for backward compatibility
    theme_changed = Signal(str, str)  # theme, variant
    colors_updated = Signal(dict)  # color_dict
    error_occurred = Signal(str)  # error_message

    def __init__(self):
        """Initialize legacy theme manager with backward compatibility."""
        super().__init__()

        # Get unified theme manager instance
        self._unified_manager = get_unified_theme_manager()

        # Connect to unified manager signals
        self._connect_signals()

        # Migration tracking
        self._migration_warnings_shown = set()
        self._operation_count = 0
        self._deprecated_operations = 0

        # Thread safety
        self._lock = threading.RLock()

        logger.info("LegacyThemeManager initialized with backward compatibility")

    @classmethod
    def instance(cls) -> "LegacyThemeManager":
        """
        Get singleton instance (backward compatibility method).

        Returns:
            LegacyThemeManager: Singleton instance
        """
        if not hasattr(cls, "_instance") or cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def apply_theme(self, theme_name: str, variant: str = None) -> bool:
        """
        Apply theme with backward compatibility.

        Args:
            theme_name: Theme name ("dark", "light", "auto")
            variant: Theme variant (optional, defaults to "blue")

        Returns:
            True if theme was applied successfully
        """
        with self._lock:
            self._operation_count += 1

            if variant is None:
                variant = "blue"

            self._log_migration_warning("apply_theme", "UnifiedThemeManager.apply_theme")

            try:
                success = self._unified_manager.apply_theme(theme_name, variant)

                if success:
                    # Emit backward compatibility signals
                    self.theme_changed.emit(theme_name, variant)

                    # Get updated colors for compatibility
                    colors = self._unified_manager.get_theme_colors()
                    self.colors_updated.emit(colors)

                return success

            except Exception as e:
                logger.error("Legacy apply_theme failed: %s", e)
                self.error_occurred.emit(str(e))
                return False

    def get_color(self, color_name: str) -> str:
        """
        Get color by name (backward compatibility method).

        Args:
            color_name: Name of the color

        Returns:
            Hex color string or fallback color
        """
        with self._lock:
            self._operation_count += 1

            self._log_migration_warning("get_color", "UnifiedThemeManager.get_color")

            try:
                return self._unified_manager.get_color(color_name)
            except Exception as e:
                logger.error("Legacy get_color failed for %s: {e}", color_name)
                return "#1976D2"  # Fallback color

    def get_theme_colors(self) -> Dict[str, str]:
        """
        Get all theme colors (backward compatibility method).

        Returns:
            Dictionary of color names to hex values
        """
        with self._lock:
            self._operation_count += 1

            self._log_migration_warning("get_theme_colors", "UnifiedThemeManager.get_theme_colors")

            try:
                return self._unified_manager.get_theme_colors()
            except Exception as e:
                logger.error("Legacy get_theme_colors failed: %s", e)
                return {}

    def save_settings(self) -> bool:
        """
        Save current theme settings (backward compatibility method).

        Returns:
            True if save was successful
        """
        with self._lock:
            self._operation_count += 1

            self._log_migration_warning("save_settings", "UnifiedThemeManager.save_settings")

            try:
                return self._unified_manager.save_settings()
            except Exception as e:
                logger.error("Legacy save_settings failed: %s", e)
                return False

    def load_settings(self) -> bool:
        """
        Load theme settings (backward compatibility method).

        Returns:
            True if load was successful
        """
        with self._lock:
            self._operation_count += 1

            self._log_migration_warning("load_settings", "UnifiedThemeManager.load_settings")

            try:
                return self._unified_manager.load_settings()
            except Exception as e:
                logger.error("Legacy load_settings failed: %s", e)
                return False

    def get_current_theme(self) -> Tuple[str, str]:
        """
        Get currently applied theme (backward compatibility method).

        Returns:
            Tuple of (theme, variant)
        """
        with self._lock:
            self._operation_count += 1

            self._log_migration_warning(
                "get_current_theme", "UnifiedThemeManager.get_current_theme"
            )

            try:
                return self._unified_manager.get_current_theme()
            except Exception as e:
                logger.error("Legacy get_current_theme failed: %s", e)
                return "dark", "blue"

    def reset_to_default(self) -> bool:
        """
        Reset theme to default (backward compatibility method).

        Returns:
            True if reset was successful
        """
        with self._lock:
            self._operation_count += 1

            self._log_migration_warning("reset_to_default", "UnifiedThemeManager.reset_to_default")

            try:
                return self._unified_manager.reset_to_default()
            except Exception as e:
                logger.error("Legacy reset_to_default failed: %s", e)
                return False

    def export_theme(self, file_path: str) -> bool:
        """
        Export current theme to file (backward compatibility method).

        Args:
            file_path: Path to export theme

        Returns:
            True if export was successful
        """
        with self._lock:
            self._operation_count += 1

            self._log_migration_warning("export_theme", "UnifiedThemeManager.export_theme")

            try:
                return self._unified_manager.export_theme(file_path)
            except Exception as e:
                logger.error("Legacy export_theme failed: %s", e)
                return False

    def import_theme(self, file_path: str) -> bool:
        """
        Import theme from file (backward compatibility method).

        Args:
            file_path: Path to import theme from

        Returns:
            True if import was successful
        """
        with self._lock:
            self._operation_count += 1

            self._log_migration_warning("import_theme", "UnifiedThemeManager.import_theme")

            try:
                return self._unified_manager.import_theme(file_path)
            except Exception as e:
                logger.error("Legacy import_theme failed: %s", e)
                return False

    def register_widget(self, widget, widget_name: str = None) -> bool:
        """
        Register widget for dynamic theme updates (backward compatibility method).

        Args:
            widget: Widget to register
            widget_name: Optional name for the widget

        Returns:
            True if registration was successful
        """
        with self._lock:
            self._operation_count += 1

            self._log_migration_warning("register_widget", "UnifiedThemeManager.register_widget")

            try:
                return self._unified_manager.register_widget(widget, widget_name)
            except Exception as e:
                logger.error("Legacy register_widget failed: %s", e)
                return False

    def unregister_widget(self, widget_name: str) -> bool:
        """
        Unregister widget from theme updates (backward compatibility method).

        Args:
            widget_name: Name of widget to unregister

        Returns:
            True if unregistration was successful
        """
        with self._lock:
            self._operation_count += 1

            self._log_migration_warning(
                "unregister_widget", "UnifiedThemeManager.unregister_widget"
            )

            try:
                return self._unified_manager.unregister_widget(widget_name)
            except Exception as e:
                logger.error("Legacy unregister_widget failed: %s", e)
                return False

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status (backward compatibility method).

        Returns:
            Dictionary containing system status information
        """
        with self._lock:
            self._operation_count += 1

            self._log_migration_warning(
                "get_system_status", "UnifiedThemeManager.get_system_status"
            )

            try:
                status = self._unified_manager.get_system_status()

                # Add legacy compatibility information
                status["legacy_compatibility"] = {
                    "enabled": True,
                    "operation_count": self._operation_count,
                    "deprecated_operations": self._deprecated_operations,
                    "migration_warnings_shown": len(self._migration_warnings_shown),
                }

                return status

            except Exception as e:
                logger.error("Legacy get_system_status failed: %s", e)
                return {
                    "error": str(e),
                    "legacy_compatibility": {
                        "enabled": True,
                        "operation_count": self._operation_count,
                        "deprecated_operations": self._deprecated_operations,
                    },
                }

    def cleanup_resources(self) -> None:
        """
        Clean up system resources (backward compatibility method).
        """
        with self._lock:
            self._operation_count += 1

            self._log_migration_warning(
                "cleanup_resources", "UnifiedThemeManager.cleanup_resources"
            )

            try:
                self._unified_manager.cleanup_resources()
            except Exception as e:
                logger.error("Legacy cleanup_resources failed: %s", e)

    def _connect_signals(self) -> None:
        """Connect to unified theme manager signals."""
        try:
            # Connect unified manager signals to legacy signals
            self._unified_manager.theme_changed.connect(self.theme_changed.emit)
            self._unified_manager.theme_applied.connect(
                lambda success, msg: None  # Handle success/failure
            )
            self._unified_manager.theme_validation_failed.connect(
                lambda msg, errors: self.error_occurred.emit(f"Validation failed: {msg}")
            )

            logger.debug("Legacy theme manager signals connected")

        except Exception as e:
            logger.error("Failed to connect legacy signals: %s", e)

    def _log_migration_warning(self, method_name: str, new_method: str) -> None:
        """
        Log migration warning for deprecated methods.

        Args:
            method_name: Name of the legacy method being called
            new_method: Name of the new method to use
        """
        warning_key = f"{method_name}_warning"

        if warning_key not in self._migration_warnings_shown:
            logger.warning(
                f"Legacy ThemeManager.{method_name}() called. "
                f"Consider migrating to {new_method}() for better performance and features."
            )
            self._migration_warnings_shown.add(warning_key)
            self._deprecated_operations += 1

    def get_migration_report(self) -> Dict[str, Any]:
        """
        Get migration report showing usage statistics.

        Returns:
            Dictionary containing migration statistics and recommendations
        """
        with self._lock:
            return {
                "legacy_operations": self._operation_count,
                "deprecated_operations": self._deprecated_operations,
                "migration_warnings_shown": len(self._migration_warnings_shown),
                "warnings_list": list(self._migration_warnings_shown),
                "recommendations": [
                    "Migrate to UnifiedThemeManager for better performance",
                    "Use qt-material color variables instead of hardcoded colors",
                    "Consider using theme signals for dynamic updates",
                    "Review setStyleSheet() calls for qt-material compatibility",
                ],
                "compatibility_status": "active",
                "estimated_migration_effort": self._estimate_migration_effort(),
            }

    def _estimate_migration_effort(self) -> str:
        """
        Estimate the effort required for migration.

        Returns:
            String describing migration effort level
        """
        if self._deprecated_operations > 100:
            return "high"
        elif self._deprecated_operations > 20:
            return "medium"
        else:
            return "low"


# Create singleton instance
_legacy_theme_manager_instance = None


def get_legacy_theme_manager() -> LegacyThemeManager:
    """
    Get singleton LegacyThemeManager instance.

    Returns:
        LegacyThemeManager: The singleton instance
    """
    global _legacy_theme_manager_instance
    if _legacy_theme_manager_instance is None:
        _legacy_theme_manager_instance = LegacyThemeManager.instance()
    return _legacy_theme_manager_instance


# Backward compatibility aliases
ThemeManager = LegacyThemeManager
get_theme_manager = get_legacy_theme_manager
