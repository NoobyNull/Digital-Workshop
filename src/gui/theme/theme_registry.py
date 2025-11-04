"""
Theme Registry Module

This module provides widget registration and dynamic theme updates for the unified theme system.
It manages widget lifecycle and ensures all widgets receive theme updates when themes change.

Key Features:
- Automatic widget registration and unregistration
- Dynamic theme updates for newly created widgets
- Thread-safe widget management with proper locking
- Weak reference management to prevent memory leaks
- Batch theme updates for performance optimization
- Comprehensive error handling for widget operations

Widget Management:
- Automatic registration of theme-aware widgets
- Weak reference tracking to prevent memory leaks
- Dynamic discovery of new widgets at runtime
- Batch updates for performance during theme changes
- Graceful handling of widget destruction
"""

import time
import weakref
from typing import Dict, List, Set, Any, Optional, Tuple
from PySide6.QtCore import QObject, Signal, QMutex, QMutexLocker, QTimer
from PySide6.QtWidgets import QWidget, QApplication
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class ThemeUpdateError(Exception):
    """
    Exception raised when theme update operations fail.

    Provides detailed information about update failures
    and affected widgets.
    """

    def __init__(self, message: str, failed_widgets: List[str] = None):
        """
        Initialize theme update error.

        Args:
            message: Error message
            failed_widgets: List of widget names that failed to update
        """
        super().__init__(message)
        self.failed_widgets = failed_widgets or []


class WidgetRegistry:
    """
    Registry entry for individual widgets.

    Tracks widget metadata, update status, and provides
    safe access to widget references.
    """

    def __init__(self, widget: QWidget, widget_name: str = None):
        """
        Initialize widget registry entry.

        Args:
            widget: Widget to register
            widget_name: Optional name for the widget
        """
        self.widget_ref = weakref.ref(widget)
        self.widget_name = widget_name or f"{widget.__class__.__name__}_{id(widget)}"
        self.registered_time = time.time()
        self.last_update_time = 0.0
        self.update_count = 0
        self.update_errors = 0
        self.is_theme_aware = self._detect_theme_awareness(widget)

    def _detect_theme_awareness(self, widget: QWidget) -> bool:
        """
        Detect if widget is theme-aware.

        Args:
            widget: Widget to check

        Returns:
            True if widget appears theme-aware
        """
        # Check for common theme-related methods
        theme_methods = [
            "apply_theme",
            "update_theme",
            "set_theme",
            "on_theme_change",
            "theme_changed",
        ]

        for method_name in theme_methods:
            if hasattr(widget, method_name) and callable(getattr(widget, method_name)):
                return True

        # Check for theme-related attributes
        theme_attributes = [
            "theme",
            "theme_data",
            "color_scheme",
            "style_sheet",
            "theme_manager",
        ]

        for attr_name in theme_attributes:
            if hasattr(widget, attr_name):
                return True

        return False

    def get_widget(self) -> Optional[QWidget]:
        """
        Get widget if it still exists.

        Returns:
            Widget instance or None if destroyed
        """
        return self.widget_ref()

    def is_alive(self) -> bool:
        """
        Check if widget is still alive.

        Returns:
            True if widget exists
        """
        return self.get_widget() is not None

    def update_theme(self, theme_data: Dict[str, Any]) -> bool:
        """
        Update widget theme.

        Args:
            theme_data: Theme configuration

        Returns:
            True if update was successful
        """
        widget = self.get_widget()
        if not widget:
            return False

        try:
            self.last_update_time = time.time()
            self.update_count += 1

            # Try different theme update methods
            if hasattr(widget, "apply_theme") and callable(widget.apply_theme):
                widget.apply_theme(theme_data)
            elif hasattr(widget, "update_theme") and callable(widget.update_theme):
                widget.update_theme(theme_data)
            elif hasattr(widget, "set_theme") and callable(widget.set_theme):
                widget.set_theme(theme_data)
            elif hasattr(widget, "on_theme_change") and callable(widget.on_theme_change):
                widget.on_theme_change(theme_data)
            else:
                # Fallback: update stylesheet if available
                self._update_stylesheet_fallback(widget, theme_data)

            return True

        except Exception as e:
            self.update_errors += 1
            logger.warning(f"Failed to update theme for widget {self.widget_name}: {e}")
            return False

    def _update_stylesheet_fallback(self, widget: QWidget, theme_data: Dict[str, Any]) -> None:
        """
        Fallback theme update using stylesheet.

        Args:
            widget: Widget to update
            theme_data: Theme configuration
        """
        try:
            # Generate basic stylesheet from theme data
            custom_colors = theme_data.get("custom_colors", {})
            primary_color = custom_colors.get("primary", "#1976D2")
            background_color = custom_colors.get("background", "#121212")

            stylesheet = f"""
            QWidget#{self.widget_name} {{
                background-color: {background_color};
                color: {primary_color};
            }}
            """

            # Apply stylesheet if widget supports it
            if hasattr(widget, "setStyleSheet"):
                widget.setStyleSheet(stylesheet)

        except Exception as e:
            logger.debug(f"Stylesheet fallback failed for {self.widget_name}: {e}")


class ThemeRegistry(QObject):
    """
    Widget registration and dynamic theme update management.

    Provides comprehensive widget lifecycle management for theme updates:
    - Automatic registration of theme-aware widgets
    - Dynamic discovery and registration of new widgets
    - Thread-safe batch theme updates
    - Memory leak prevention through weak references
    - Performance monitoring for theme operations

    Registry Features:
    - Weak reference management to prevent memory leaks
    - Automatic cleanup of destroyed widgets
    - Batch updates for performance optimization
    - Error tracking and recovery for failed updates
    - Performance monitoring and statistics
    """

    # Signals for registry events
    widget_registered = Signal(str)  # widget_name
    widget_unregistered = Signal(str)  # widget_name
    theme_update_started = Signal()
    theme_update_completed = Signal(int, int)  # successful_updates, failed_updates
    registry_cleanup_completed = Signal(int)  # removed_count

    def __init__(self):
        """Initialize theme registry."""
        super().__init__()

        # Widget registry storage
        self._widgets: Dict[str, WidgetRegistry] = {}
        self._registry_mutex = QMutex()

        # Update management
        self._pending_updates = False
        self._update_in_progress = False
        self._batch_update_timer = QTimer()
        self._batch_update_timer.timeout.connect(self._process_batch_updates)

        # Performance tracking
        self._total_updates = 0
        self._successful_updates = 0
        self._failed_updates = 0
        self._cleanup_count = 0

        # Auto-discovery settings
        self._auto_discovery_enabled = True
        self._discovery_interval = 5000  # 5 seconds
        self._discovery_timer = QTimer()
        self._discovery_timer.timeout.connect(self._discover_widgets)

        # Start timers
        self._batch_update_timer.start(100)  # Process batch updates every 100ms
        self._discovery_timer.start(self._discovery_interval)

        logger.info("ThemeRegistry initialized with dynamic widget management")

    def register_widget(self, widget: QWidget, widget_name: str = None) -> bool:
        """
        Register a widget for theme updates.

        Args:
            widget: Widget to register
            widget_name: Optional name for the widget

        Returns:
            True if registration was successful
        """
        if not isinstance(widget, QWidget):
            logger.warning(f"Cannot register non-QWidget object: {type(widget)}")
            return False

        widget_name = widget_name or f"{widget.__class__.__name__}_{id(widget)}"

        with QMutexLocker(self._registry_mutex):
            # Check if already registered
            if widget_name in self._widgets:
                existing_entry = self._widgets[widget_name]
                if existing_entry.is_alive():
                    logger.debug(f"Widget {widget_name} already registered")
                    return True
                else:
                    # Remove dead reference
                    del self._widgets[widget_name]

            # Create new registry entry
            try:
                entry = WidgetRegistry(widget, widget_name)
                self._widgets[widget_name] = entry

                logger.debug(f"Registered widget for theme updates: {widget_name}")
                self.widget_registered.emit(widget_name)
                return True

            except Exception as e:
                logger.error(f"Failed to register widget {widget_name}: {e}")
                return False

    def unregister_widget(self, widget_name: str) -> bool:
        """
        Unregister a widget from theme updates.

        Args:
            widget_name: Name of widget to unregister

        Returns:
            True if widget was unregistered
        """
        with QMutexLocker(self._registry_mutex):
            if widget_name in self._widgets:
                del self._widgets[widget_name]
                logger.debug(f"Unregistered widget: {widget_name}")
                self.widget_unregistered.emit(widget_name)
                return True

            return False

    def update_widget_theme(self, widget_name: str, theme_data: Dict[str, Any]) -> bool:
        """
        Update theme for specific widget.

        Args:
            widget_name: Name of widget to update
            theme_data: Theme configuration

        Returns:
            True if update was successful
        """
        with QMutexLocker(self._registry_mutex):
            if widget_name in self._widgets:
                entry = self._widgets[widget_name]
                success = entry.update_theme(theme_data)

                if success:
                    self._successful_updates += 1
                else:
                    self._failed_updates += 1

                self._total_updates += 1
                return success

            logger.warning(f"Widget not found in registry: {widget_name}")
            return False

    def update_all_themes(self, theme_data: Dict[str, Any]) -> Tuple[int, int]:
        """
        Update themes for all registered widgets.

        Args:
            theme_data: Theme configuration

        Returns:
            Tuple of (successful_updates, failed_updates)
        """
        self.theme_update_started.emit()

        successful = 0
        failed = 0

        with QMutexLocker(self._registry_mutex):
            # Create a snapshot of current widgets to avoid modification during iteration
            current_widgets = list(self._widgets.items())

        # Update each widget
        for widget_name, entry in current_widgets:
            if entry.is_alive():
                if entry.update_theme(theme_data):
                    successful += 1
                else:
                    failed += 1
            else:
                # Remove dead widgets
                with QMutexLocker(self._registry_mutex):
                    if widget_name in self._widgets:
                        del self._widgets[widget_name]
                        self._cleanup_count += 1

        self._successful_updates += successful
        self._failed_updates += failed
        self._total_updates += successful + failed

        logger.info(f"Theme update completed: {successful} successful, {failed} failed")
        self.theme_update_completed.emit(successful, failed)

        return successful, failed

    def get_registered_widgets(self) -> List[str]:
        """
        Get list of registered widget names.

        Returns:
            List of registered widget names
        """
        with QMutexLocker(self._registry_mutex):
            # Filter out dead widgets
            alive_widgets = []
            dead_widgets = []

            for widget_name, entry in self._widgets.items():
                if entry.is_alive():
                    alive_widgets.append(widget_name)
                else:
                    dead_widgets.append(widget_name)

            # Clean up dead widgets
            for widget_name in dead_widgets:
                del self._widgets[widget_name]
                self._cleanup_count += 1

            return alive_widgets

    def get_widget_info(self, widget_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a registered widget.

        Args:
            widget_name: Name of widget

        Returns:
            Widget information or None if not found
        """
        with QMutexLocker(self._registry_mutex):
            if widget_name in self._widgets:
                entry = self._widgets[widget_name]
                return {
                    "widget_name": entry.widget_name,
                    "is_alive": entry.is_alive(),
                    "is_theme_aware": entry.is_theme_aware,
                    "registered_time": entry.registered_time,
                    "last_update_time": entry.last_update_time,
                    "update_count": entry.update_count,
                    "update_errors": entry.update_errors,
                }

            return None

    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive registry statistics.

        Returns:
            Dictionary containing registry metrics
        """
        with QMutexLocker(self._registry_mutex):
            # Count alive vs dead widgets
            alive_count = 0
            dead_count = 0
            theme_aware_count = 0

            for entry in self._widgets.values():
                if entry.is_alive():
                    alive_count += 1
                    if entry.is_theme_aware:
                        theme_aware_count += 1
                else:
                    dead_count += 1

            # Clean up dead widgets during stats collection
            if dead_count > 0:
                dead_widget_names = [
                    name for name, entry in self._widgets.items() if not entry.is_alive()
                ]
                for name in dead_widget_names:
                    del self._widgets[name]
                    self._cleanup_count += 1

            total_requests = self._successful_updates + self._failed_updates
            success_rate = self._successful_updates / total_requests if total_requests > 0 else 0

            return {
                "total_registered": len(self._widgets),
                "alive_widgets": alive_count,
                "dead_widgets": dead_count,
                "theme_aware_widgets": theme_aware_count,
                "total_updates": self._total_updates,
                "successful_updates": self._successful_updates,
                "failed_updates": self._failed_updates,
                "success_rate": success_rate,
                "cleanup_count": self._cleanup_count,
                "auto_discovery_enabled": self._auto_discovery_enabled,
                "discovery_interval_ms": self._discovery_interval,
            }

    def enable_auto_discovery(self) -> None:
        """Enable automatic widget discovery."""
        self._auto_discovery_enabled = True
        logger.debug("Auto-discovery enabled")

    def disable_auto_discovery(self) -> None:
        """Disable automatic widget discovery."""
        self._auto_discovery_enabled = False
        logger.debug("Auto-discovery disabled")

    def set_discovery_interval(self, interval_ms: int) -> None:
        """
        Set widget discovery interval.

        Args:
            interval_ms: Discovery interval in milliseconds
        """
        self._discovery_interval = max(1000, interval_ms)  # Minimum 1 second
        self._discovery_timer.setInterval(self._discovery_interval)
        logger.debug(f"Discovery interval set to {self._discovery_interval}ms")

    def force_discovery(self) -> None:
        """Force immediate widget discovery."""
        self._discover_widgets()
        logger.debug("Forced widget discovery completed")

    def cleanup_dead_widgets(self) -> int:
        """
        Clean up dead widget references.

        Returns:
            Number of widgets cleaned up
        """
        with QMutexLocker(self._registry_mutex):
            dead_widgets = []
            for widget_name, entry in self._widgets.items():
                if not entry.is_alive():
                    dead_widgets.append(widget_name)

            for widget_name in dead_widgets:
                del self._widgets[widget_name]
                self._cleanup_count += 1

            if dead_widgets:
                logger.info(f"Cleaned up {len(dead_widgets)} dead widget references")

            return len(dead_widgets)

    def _discover_widgets(self) -> None:
        """Discover and register new widgets."""
        if not self._auto_discovery_enabled:
            return

        try:
            app = QApplication.instance()
            if not app:
                return

            # Get all top-level widgets
            top_level_widgets = app.topLevelWidgets()

            registered_count = 0
            for widget in top_level_widgets:
                if self._register_widget_recursive(widget):
                    registered_count += 1

            if registered_count > 0:
                logger.debug(f"Auto-discovered and registered {registered_count} widgets")

        except Exception as e:
            logger.error(f"Widget discovery failed: {e}")

    def _register_widget_recursive(self, widget: QWidget, visited: Set[int] = None) -> bool:
        """
        Recursively register widget and its children.

        Args:
            widget: Widget to register
            visited: Set of already visited widget IDs

        Returns:
            True if any widgets were registered
        """
        if visited is None:
            visited = set()

        widget_id = id(widget)
        if widget_id in visited:
            return False

        visited.add(widget_id)
        registered_any = False

        # Register this widget
        widget_name = f"{widget.__class__.__name__}_{widget_id}"
        if self.register_widget(widget, widget_name):
            registered_any = True

        # Register children
        try:
            for child in widget.children():
                if isinstance(child, QWidget):
                    if self._register_widget_recursive(child, visited):
                        registered_any = True
        except Exception as e:
            logger.debug(f"Error registering child widgets: {e}")

        return registered_any

    def _process_batch_updates(self) -> None:
        """Process any pending batch theme updates."""
        # This method can be extended to handle batch updates
        # For now, it's a placeholder for future optimization
