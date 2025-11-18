#!/usr/bin/env python3
"""
Application Module

This module contains the Application class that encapsulates
the application lifecycle management and coordinates all components.
"""

import sys
import os
from typing import Optional
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication, QSettings

from .application_config import ApplicationConfig
from .application_bootstrap import ApplicationBootstrap
from .exception_handler import ExceptionHandler
from .logging_config import get_logger
from .system_initializer import SystemInitializer
from src.core.services.library_root_monitor import LibraryRootMonitor
from src.gui.dialogs.library_setup_dialog import run_first_launch_setup
from src.gui.main_window import MainWindow


class Application:
    """Main application class that manages the application lifecycle."""

    def __init__(self, config: Optional[ApplicationConfig] = None) -> None:
        """Initialize the Application with optional configuration.

        Args:
            config: Application configuration, uses default if None
        """
        self.config = config or ApplicationConfig.get_default()
        self.logger: Optional[logging.Logger] = None
        self.qt_app: Optional[QApplication] = None
        self.main_window: Optional[MainWindow] = None
        self.exception_handler: Optional[ExceptionHandler] = None
        self.system_initializer: Optional[SystemInitializer] = None
        self.bootstrap: Optional[ApplicationBootstrap] = None
        self._is_initialized = False
        self._is_running = False

        # Startup splash screen (shown while core systems initialize).
        self._startup_splash = None
        self._startup_progress_bar = None
        self._startup_status_label = None

    def initialize(self, argv: Optional[list] = None) -> bool:
        """Initialize the application and all its components.

        Args:
            argv: Command line arguments, uses sys.argv if None

        Returns:
            True if initialization was successful, False otherwise
        """
        if self._is_initialized:
            if self.logger:
                self.logger.warning("Application already initialized")
            return True

        try:
            # Create QApplication first
            if not self._create_qt_application(argv or sys.argv):
                return False

            # Apply theme EARLY so all widgets created after this get the theme
            self._apply_theme_early()

            # First-launch library setup (runs only once per user)
            run_first_launch_setup()

            # Show a lightweight startup splash while core systems initialize.
            self._show_startup_splash()
            self._update_startup_splash(5, "Initializing system components...")

            # Initialize system components
            if not self._initialize_system():
                self._hide_startup_splash()
                return False

            # System components are up; give this a bigger chunk of the bar.
            self._update_startup_splash(30, "Installing exception handlers...")

            # Install exception handler
            if not self._install_exception_handler():
                self._hide_startup_splash()
                return False

            # Exception handlers are cheap; keep this as a smaller step.
            self._update_startup_splash(45, "Starting application services...")

            # Bootstrap application services (often one of the heavier stages)
            if not self._bootstrap_services():
                self._hide_startup_splash()
                return False

            self._update_startup_splash(70, "Checking project library root...")

            # Monitor consolidated library root and handle DB failover
            monitor = LibraryRootMonitor()
            monitor.check_on_startup()

            self._update_startup_splash(85, "Creating main window...")

            # Create main window (final heavy step before showing UI)
            if not self._create_main_window():
                self._hide_startup_splash()
                return False

            self._update_startup_splash(100, "Ready")

            # Connect signals
            self._connect_signals()

            self._is_initialized = True
            if self.logger:
                self.logger.info("Application initialization completed successfully")
            self._hide_startup_splash()
            return True

        except RuntimeError as e:
            if self.logger:
                self.logger.error("Application initialization failed: %s", str(e))
            else:
                print(f"Application initialization failed: {str(e)}")
            self._hide_startup_splash()
            return False

    def run(self) -> int:
        """Run the application event loop.

        Returns:
            Exit code from the application
        """
        if not self._is_initialized:
            if self.logger:
                self.logger.error("Cannot run uninitialized application")
            else:
                print("Cannot run uninitialized application")
            return 1

        if self._is_running:
            if self.logger:
                self.logger.warning("Application is already running")
            return 0

        try:
            self._is_running = True

            # Show the main window
            if self.main_window:
                self.main_window.show()
                self.logger.info("Main window displayed")

            # Start the event loop
            self.logger.info("Application event loop started")
            exit_code = self.qt_app.exec()

            # Log application shutdown
            self.logger.info("Application exiting with code: %d", exit_code)
            return exit_code

        except RuntimeError as e:
            self.logger.error("Application runtime error: %s", str(e))
            return 1
        finally:
            self._is_running = False
            self.cleanup()

    def shutdown(self, exit_code: int = 0) -> None:
        """Shutdown the application gracefully.

        Args:
            exit_code: Exit code to return
        """
        if self.qt_app:
            self.qt_app.exit(exit_code)

    def cleanup(self) -> None:
        """Cleanup application resources using unified cleanup coordinator."""
        if not self._is_initialized:
            return

        try:
            # Use unified cleanup coordinator for VTK and other resources
            self._perform_unified_cleanup()

            # Cleanup main window
            if self.main_window:
                self.main_window.close()
                self.main_window = None

            # Cleanup bootstrap
            if self.bootstrap:
                self.bootstrap.cleanup()
                self.bootstrap = None

            # Cleanup exception handler
            if self.exception_handler:
                self.exception_handler.cleanup()
                self.exception_handler = None

            # Cleanup system initializer
            if self.system_initializer:
                self.system_initializer.cleanup_temp_files()
                self.system_initializer = None

            self._is_initialized = False
            if self.logger:
                self.logger.info("Application cleanup completed")

        except RuntimeError as e:
            if self.logger:
                self.logger.error("Error during cleanup: %s", str(e))

    def _perform_unified_cleanup(self) -> None:
        """Perform unified cleanup using the cleanup coordinator."""
        try:
            from src.core.cleanup.unified_cleanup_coordinator import (
                UnifiedCleanupCoordinator,
            )

            coordinator = UnifiedCleanupCoordinator()

            # Get VTK resources from main window if available
            render_window = None
            renderer = None
            interactor = None

            if self.main_window and hasattr(self.main_window, "viewer"):
                viewer = self.main_window.viewer
                if viewer and hasattr(viewer, "render_window"):
                    render_window = viewer.render_window
                if viewer and hasattr(viewer, "renderer"):
                    renderer = viewer.renderer
                if viewer and hasattr(viewer, "interactor"):
                    interactor = viewer.interactor

            # Coordinate cleanup with all resources
            stats = coordinator.coordinate_cleanup(
                render_window=render_window,
                renderer=renderer,
                interactor=interactor,
                main_window=self.main_window,
                application=self,
            )

            if self.logger:
                self.logger.info(
                    f"Unified cleanup completed: {stats.completed_phases} phases, "
                    f"{stats.failed_phases} failures, {stats.total_duration:.3f}s"
                )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.warning(
                    f"Unified cleanup failed, continuing with standard cleanup: {e}"
                )

    def _create_qt_application(self, argv: list) -> bool:
        """Create the QApplication instance.

        Args:
            argv: Command line arguments

        Returns:
            True if successful, False otherwise
        """
        try:
            self.qt_app = QApplication(argv)

            # Initialize QSettings with organization and application names
            # This must be done before any QSettings usage to ensure proper persistence
            # Use consistent names that won't be changed later
            org_name = self.config.organization_name
            app_name = self.config.name

            QCoreApplication.setOrganizationName(org_name)
            QCoreApplication.setApplicationName(app_name)

            # Configure QSettings for memory-only mode
            if os.getenv("USE_MEMORY_DB", "false").lower() == "true":
                # In memory-only mode, use file-based INI format in temp directory
                import tempfile

                temp_dir = Path(tempfile.gettempdir()) / "digital_workshop_dev"
                temp_dir.mkdir(parents=True, exist_ok=True)
                settings_file = temp_dir / "settings.ini"

                # Create a file-based QSettings that uses INI format
                QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, str(temp_dir))
                QSettings.setDefaultFormat(QSettings.IniFormat)

            self.logger = get_logger(__name__)
            self.logger.info("QApplication created")
            self.logger.info(
                f"QSettings initialized with organization: '{org_name}', application: '{app_name}'"
            )
            return True
        except RuntimeError as e:
            print(f"Failed to create QApplication: {str(e)}")
            return False

    def _initialize_system(self) -> bool:
        """Initialize system components.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.system_initializer = SystemInitializer(self.config)
            if not self.system_initializer.initialize():
                return False
            self.logger = get_logger(__name__)
            return True
        except RuntimeError as e:
            print(f"System initialization failed: {str(e)}")
            return False

    def _install_exception_handler(self) -> bool:
        """Install the global exception handler.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.exception_handler = ExceptionHandler.create_and_install()
            if self.logger:
                self.logger.info("Exception handler installed")
            return True
        except (
            OSError,
            IOError,
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
        ) as e:  # Catch all exceptions, not just RuntimeError
            if self.logger:
                self.logger.error("Failed to install exception handler: %s", str(e))
            return False

    def _bootstrap_services(self) -> bool:
        """Bootstrap application services.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.bootstrap = ApplicationBootstrap(self.config)
            if not self.bootstrap.bootstrap_services():
                return False
            if self.logger:
                self.logger.info("Application services bootstrapped")
            return True
        except RuntimeError as e:
            if self.logger:
                self.logger.error("Service bootstrap failed: %s", str(e))
            return False

    def _create_main_window(self) -> bool:
        """Create the main application window.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.main_window = MainWindow()
            if self.logger:
                self.logger.info("Main window created")
            return True
        except RuntimeError as e:
            if self.logger:
                self.logger.error("Failed to create main window: %s", str(e))
            return False

    def _show_startup_splash(self) -> None:
        """Show a simple startup splash with a progress indicator.

        The splash uses standard Qt widgets so it respects the active theme.
        """
        if self.qt_app is None:
            return

        # Avoid creating multiple splash screens if initialize() is called twice.
        if getattr(self, "_startup_splash", None) is not None:
            return

        try:
            from PySide6.QtCore import Qt
            from PySide6.QtGui import QFont, QPixmap
            from PySide6.QtWidgets import QLabel, QProgressBar, QSplashScreen, QVBoxLayout
        except Exception:
            return

        pixmap = QPixmap(640, 320)
        pixmap.fill(self.qt_app.palette().window().color())

        splash = QSplashScreen(pixmap, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title_label = QLabel(self.config.display_name or "Digital Workshop")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)

        status_label = QLabel("Starting...")
        status_label.setAlignment(Qt.AlignCenter)

        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setTextVisible(False)
        progress_bar.setMinimumHeight(16)

        layout.addWidget(title_label)
        layout.addWidget(status_label)
        layout.addWidget(progress_bar)

        splash.setLayout(layout)

        screen = self.qt_app.primaryScreen()
        if screen is not None:
            geometry = splash.geometry()
            center = screen.availableGeometry().center()
            geometry.moveCenter(center)
            splash.setGeometry(geometry)

        splash.show()
        self.qt_app.processEvents()

        self._startup_splash = splash
        self._startup_progress_bar = progress_bar
        self._startup_status_label = status_label

    def _update_startup_splash(self, progress: int, message: str) -> None:
        """Update progress and message on the startup splash, if it is visible."""
        if self._startup_splash is None or self.qt_app is None:
            return

        try:
            if self._startup_progress_bar is not None:
                clamped = max(0, min(100, int(progress)))
                self._startup_progress_bar.setValue(clamped)
            if self._startup_status_label is not None:
                self._startup_status_label.setText(message)
            self.qt_app.processEvents()
        except RuntimeError:
            # Splash may have been closed while initializing; ignore.
            self._startup_splash = None
            self._startup_progress_bar = None
            self._startup_status_label = None

    def _hide_startup_splash(self) -> None:
        """Hide and clean up the startup splash if it was created."""
        splash = getattr(self, "_startup_splash", None)
        if splash is None:
            return

        try:
            splash.close()
            splash.deleteLater()
        except RuntimeError:
            pass

        self._startup_splash = None
        self._startup_progress_bar = None
        self._startup_status_label = None

        if self.qt_app is not None:
            try:
                self.qt_app.processEvents()
            except RuntimeError:
                pass


    def _apply_theme_early(self) -> None:
        """Apply theme early, right after QApplication is created."""
        try:
            from src.gui.theme import ThemeService

            service = ThemeService.instance()
            theme, _ = service.get_current_theme()
            service.apply_theme(theme)
            if self.logger:
                self.logger.debug("Theme applied: %s", theme)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.debug("Theme application: %s", e)

    def _connect_signals(self) -> None:
        """Connect application signals."""
        if self.main_window:
            # Connect main window signals for logging
            self.main_window.model_loaded.connect(
                lambda path: self.logger.info("Model loaded: %s", path)
            )
            self.main_window.model_selected.connect(
                lambda model_id: self.logger.info("Model selected: %d", model_id)
            )

            # Store the original closeEvent method
            self._original_close_event = self.main_window.closeEvent

            # Connect window close signal - wrap the original closeEvent
            self.main_window.closeEvent = self._on_main_window_close

    def _on_main_window_close(self, event) -> None:
        """Handle main window close event.

        Args:
            event: Close event
        """
        if self.logger:
            self.logger.info("Main window close event received")

        # CRITICAL: Call the original MainWindow closeEvent FIRST
        # This ensures window settings are saved before cleanup
        try:
            if hasattr(self, "_original_close_event") and self._original_close_event:
                self._original_close_event(event)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.warning("Failed to call original closeEvent: %s", e)

        # Then perform application cleanup
        self.cleanup()
        event.accept()

    def get_system_info(self) -> dict:
        """Get information about the application system.

        Returns:
            Dictionary containing system information
        """
        info = {
            "application_name": self.config.name,
            "application_version": self.config.get_full_version_string(),
            "initialized": self._is_initialized,
            "running": self._is_running,
        }

        if self.bootstrap:
            info.update(self.bootstrap.get_system_info())

        return info
