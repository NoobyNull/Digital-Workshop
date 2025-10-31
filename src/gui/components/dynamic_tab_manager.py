"""Dynamic tab naming system that shortens tab names when they don't fit."""

from typing import Dict
from PySide6.QtWidgets import QTabWidget
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFontMetrics

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class TabNameConfig:
    """Configuration for a tab with long and short names."""

    def __init__(self, long_name: str, short_name: str):
        """
        Initialize tab name configuration.

        Args:
            long_name: Full tab name
            short_name: Abbreviated tab name
        """
        self.long_name = long_name
        self.short_name = short_name
        self.current_name = long_name

    def should_shorten(self, available_width: int, font_metrics: QFontMetrics) -> bool:
        """
        Determine if tab should use short name.

        Args:
            available_width: Available width for tab text
            font_metrics: Font metrics for measurement

        Returns:
            True if short name should be used
        """
        long_width = font_metrics.horizontalAdvance(self.long_name)
        return long_width > available_width


class DynamicTabManager:
    """Manages dynamic tab naming based on available space."""

    # Padding for tab text (left + right margins)
    TAB_PADDING = 30

    # Minimum width to show long names
    MIN_WIDTH_FOR_LONG_NAMES = 800

    def __init__(self, tab_widget: QTabWidget):
        """
        Initialize dynamic tab manager.

        Args:
            tab_widget: QTabWidget to manage
        """
        self.tab_widget = tab_widget
        self.tab_configs: Dict[int, TabNameConfig] = {}
        self.logger = logger

        # Timer for debouncing resize events
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self._update_tab_names)

        # Connect to resize events
        self.tab_widget.resizeEvent = self._on_resize

    def register_tab(self, index: int, long_name: str, short_name: str) -> None:
        """
        Register a tab with long and short names.

        Args:
            index: Tab index
            long_name: Full tab name
            short_name: Abbreviated tab name
        """
        self.tab_configs[index] = TabNameConfig(long_name, short_name)
        self.logger.debug(f"Registered tab {index}: '{long_name}' / '{short_name}'")

    def _on_resize(self, event) -> None:
        """Handle resize event with debouncing."""
        # Call original resize event
        if hasattr(super(QTabWidget, self.tab_widget), "resizeEvent"):
            super(QTabWidget, self.tab_widget).resizeEvent(event)

        # Debounce tab name updates
        self.resize_timer.stop()
        self.resize_timer.start(100)

    def _update_tab_names(self) -> None:
        """Update tab names based on available space."""
        try:
            tab_bar = self.tab_widget.tabBar()
            if not tab_bar:
                self.logger.debug("Tab bar not available")
                return

            # Calculate available width per tab
            total_width = tab_bar.width()
            actual_tab_count = self.tab_widget.count()

            if actual_tab_count == 0:
                self.logger.debug("No tabs in widget")
                return

            # Use actual tab count for calculations, not registered configs
            # This handles cases where tabs have been added/removed
            num_tabs = min(len(self.tab_configs), actual_tab_count)

            if num_tabs == 0:
                return

            # Account for tab bar margins and spacing
            available_width = (total_width - (self.TAB_PADDING * num_tabs)) // num_tabs

            # Update each tab
            for index, config in self.tab_configs.items():
                # Check if tab still exists
                if index >= actual_tab_count:
                    self.logger.debug(
                        f"Tab {index} no longer exists (only {actual_tab_count} tabs present)"
                    )
                    continue

                try:
                    # Determine if we should use short name
                    should_use_short = (
                        available_width < 100
                        or total_width < self.MIN_WIDTH_FOR_LONG_NAMES
                    )

                    new_name = (
                        config.short_name if should_use_short else config.long_name
                    )

                    # Only update if name changed
                    if new_name != config.current_name:
                        self.tab_widget.setTabText(index, new_name)
                        config.current_name = new_name
                        self.logger.debug(f"Tab {index}: '{config.current_name}'")
                except Exception as e:
                    self.logger.debug(f"Error updating tab {index}: {e}")

        except Exception as e:
            self.logger.debug(f"Error updating tab names: {e}")

    def force_update(self) -> None:
        """Force immediate update of tab names."""
        self.resize_timer.stop()
        self._update_tab_names()


def setup_dynamic_tabs(tab_widget: QTabWidget) -> DynamicTabManager:
    """
    Setup dynamic tab naming for a tab widget.

    Args:
        tab_widget: QTabWidget to manage

    Returns:
        DynamicTabManager instance
    """
    manager = DynamicTabManager(tab_widget)

    # Register standard tabs
    manager.register_tab(0, "Model Previewer", "MV")
    manager.register_tab(1, "G Code Previewer", "GCP")
    manager.register_tab(2, "Cut List Optimizer", "CLO")
    manager.register_tab(3, "Feed and Speed", "F&S")
    manager.register_tab(4, "Project Cost Estimator", "PCO")

    # Initial update
    manager.force_update()

    return manager
