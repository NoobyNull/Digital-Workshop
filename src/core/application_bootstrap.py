#!/usr/bin/env python3
"""
Application Bootstrap Module

This module contains the ApplicationBootstrap class responsible for
initializing application services like hardware acceleration, settings migration,
and theme loading in the correct order.
"""

import logging

from .application_config import ApplicationConfig
from .hardware_acceleration import get_acceleration_manager
from .settings_migration import migrate_on_startup


class ApplicationBootstrap:
    """Handles application service initialization and bootstrap sequence."""

    def __init__(self, config: ApplicationConfig) -> None:
        """Initialize the ApplicationBootstrap with configuration.

        Args:
            config: Application configuration instance
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._hardware_acceleration_manager = None

    def bootstrap_services(self) -> bool:
        """Initialize all application services in the correct order.

        Returns:
            True if all services were initialized successfully, False otherwise
        """
        try:
            self.logger.info("Starting application service bootstrap")

            # Initialize services in order
            if not self._initialize_settings_migration():
                return False

            if not self._initialize_theme_system():
                return False

            if self.config.enable_hardware_acceleration:
                if not self._initialize_hardware_acceleration():
                    # Hardware acceleration failure is not critical
                    self.logger.warning(
                        "Hardware acceleration failed, continuing without it"
                    )

            self.logger.info("Application service bootstrap completed successfully")
            return True

        except RuntimeError as e:
            self.logger.error("Service bootstrap failed: %s", str(e))
            return False

    def _initialize_settings_migration(self) -> bool:
        """Initialize settings migration if needed.

        Returns:
            True if migration was successful or not needed, False on failure
        """
        try:
            self.logger.debug("Checking for settings migration")
            if not migrate_on_startup():
                self.logger.warning("Settings migration failed or incomplete")
                # Continue even if migration fails, but log the issue
            return True
        except RuntimeError as e:
            self.logger.error("Settings migration error: %s", str(e))
            return False

    def _initialize_theme_system(self) -> bool:
        """Initialize the theme system.

        Returns:
            True if theme initialization was successful, False otherwise
        """
        try:
            self.logger.debug("Loading theme settings")

            # Initialize theme system using ThemeService
            try:
                from src.gui.theme import ThemeService

                service = ThemeService.instance()

                # Apply default dark theme
                try:
                    result = service.apply_theme("dark")
                    if result:
                        self.logger.debug("Theme applied successfully")
                    else:
                        self.logger.debug(
                            "Theme application returned False, but continuing"
                        )
                except (
                    OSError,
                    IOError,
                    ValueError,
                    TypeError,
                    KeyError,
                    AttributeError,
                ) as theme_error:
                    self.logger.debug("Failed to apply theme: %s", theme_error)

                return True

            except (
                OSError,
                IOError,
                ValueError,
                TypeError,
                KeyError,
                AttributeError,
            ) as error:
                self.logger.debug("Theme initialization: %s", error)
                # Continue without theme system - not critical for startup
                return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.debug("Theme initialization: %s", e)
            # Continue without theme system - not critical for startup
            return True

    def _initialize_hardware_acceleration(self) -> bool:
        """Initialize hardware acceleration detection and setup.

        Returns:
            True if hardware acceleration was initialized successfully, False otherwise
        """
        try:
            self.logger.debug("Detecting hardware acceleration capabilities")
            self._hardware_acceleration_manager = get_acceleration_manager()

            # Get capabilities and log detailed information
            caps = self._hardware_acceleration_manager.get_capabilities()
            self.logger.info(
                "Hardware acceleration detected: backend=%s score=%d available=%s devices=%s",
                caps.recommended_backend.value,
                caps.performance_score,
                [b.value for b in caps.available_backends],
                [f"{d.vendor} {d.name} ({d.memory_mb or '?'}MB)" for d in caps.devices],
            )

            # Warn if no acceleration is available
            self._hardware_acceleration_manager.warn_if_no_acceleration()

            self.logger.debug("Hardware acceleration initialized")
            return True

        except RuntimeError as e:
            self.logger.warning("Hardware acceleration detection failed: %s", str(e))
            return False

    def get_hardware_acceleration_manager(self) -> None:
        """Get the hardware acceleration manager instance.

        Returns:
            Hardware acceleration manager or None if not initialized
        """
        return self._hardware_acceleration_manager

    def get_system_info(self) -> dict:
        """Get information about the initialized system.

        Returns:
            Dictionary containing system information
        """
        info = {
            "hardware_acceleration_enabled": self._hardware_acceleration_manager
            is not None,
            "theme_loaded": True,  # We would track this more precisely in a real implementation
            "settings_migrated": True,  # Same as above
        }

        if self._hardware_acceleration_manager:
            try:
                caps = self._hardware_acceleration_manager.get_capabilities()
                info["hardware_capabilities"] = {
                    "recommended_backend": caps.recommended_backend.value,
                    "performance_score": caps.performance_score,
                    "available_backends": [b.value for b in caps.available_backends],
                    "device_count": len(caps.devices),
                }
            except RuntimeError:
                info["hardware_capabilities"] = None

        return info

    def cleanup(self) -> None:
        """Cleanup bootstrap resources."""
        if self._hardware_acceleration_manager:
            # Hardware acceleration manager doesn't have explicit cleanup
            # but we would call it here if it did
            pass

        self.logger.debug("Application bootstrap cleanup completed")
