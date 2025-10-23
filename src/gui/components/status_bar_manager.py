"""
Status Bar Management Module

This module handles the creation and management of the application's status bar,
including progress indicators, memory usage display, and background process status.

Classes:
    StatusBarManager: Main class for managing status bar functionality
"""

import logging
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QMainWindow, QStatusBar, QLabel, QProgressBar, QPushButton, QMessageBox

from src.core.database_manager import get_database_manager
from src.gui.components.deduplication_status_widget import DeduplicationStatusWidget


class StatusBarManager:
    """
    Manages the application's status bar and all associated status indicators.

    This class handles the creation of status bar widgets, progress indicators,
    memory usage display, and background process status updates.
    """

    def __init__(self, main_window: QMainWindow, logger: Optional[logging.Logger] = None):
        """
        Initialize the status bar manager.

        Args:
            main_window: The main window instance
            logger: Optional logger instance for debugging
        """
        self.main_window = main_window
        self.logger = logger or logging.getLogger(__name__)
        self.status_bar = None
        self.status_label = None
        self.progress_bar = None
        self.hash_indicator = None
        self.memory_label = None
        self.status_timer = None
        self.background_hasher = None

    def setup_status_bar(self) -> None:
        """Set up the application status bar."""
        self.logger.debug("Setting up status bar")

        self.status_bar = QStatusBar()
        # Give the bar a stable objectName so we can target it precisely in QSS
        try:
            self.status_bar.setObjectName("AppStatusBar")
        except Exception:
            pass

        self.main_window.setStatusBar(self.status_bar)
        # Make sure the bar paints its background, some styles require this for QSS background-color to take effect
        try:
            self.status_bar.setAutoFillBackground(True)
            self.status_bar.setAttribute(Qt.WA_StyledBackground, True)
        except Exception:
            pass

        # qt-material handles statusbar styling automatically

        # Main status message - larger and takes up available space
        self.status_label = QLabel("Ready")
        self.status_label.setMinimumWidth(300)  # Give it more space
        # Qt-material handles font styling automatically
        self.status_bar.addWidget(self.status_label, 1)  # Stretch factor 1 to take available space

        # Progress bar for long operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.status_bar.addPermanentWidget(self.progress_bar)

        # Hash indicator button
        self.hash_indicator = QPushButton("#")
        self.hash_indicator.setFixedSize(20, 20)
        self.hash_indicator.setToolTip("Background hashing idle - Click to start/pause")
        self.hash_indicator.setVisible(False)
        self.hash_indicator.clicked.connect(self._toggle_background_hasher)
        self.status_bar.addPermanentWidget(self.hash_indicator)

        # Memory usage indicator
        self.memory_label = QLabel("Memory: N/A")
        self.memory_label.setMinimumWidth(120)
        self.memory_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.status_bar.addPermanentWidget(self.memory_label)

        # Layout Edit Mode indicator
        self.layout_edit_indicator = QLabel("Layout Edit Mode: OFF")
        self.layout_edit_indicator.setMinimumWidth(150)
        self.layout_edit_indicator.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.status_bar.addPermanentWidget(self.layout_edit_indicator)

        # Deduplication status widget (add last to be on the far right)
        self.dedup_status_widget = DeduplicationStatusWidget()
        # Add with 0 stretch to ensure it's positioned on the far right
        self.status_bar.addPermanentWidget(self.dedup_status_widget, 0)

        # Initialize background hasher
        self.background_hasher = None

        self.logger.debug("Status bar setup completed")

    def setup_status_timer(self) -> None:
        """Set up timer for periodic status updates."""
        # Update memory usage every 5 seconds
        self.status_timer = QTimer(self.main_window)
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(5000)  # 5 seconds

        # Initial update
        self._update_status()

    def _update_status(self) -> None:
        """Update status bar information."""
        try:
            # Check if current status message is an important UI feedback message
            current_message = self.status_label.text()
            important_messages = [
                "Applied main_window.css",
                "Modern UI styling applied",
                "Stylesheet reloaded",
                "Toolbar icons active",
                "Loading:",
                "Metadata saved",
                "Added"
            ]

            # Don't override important UI feedback messages
            is_important = any(msg in current_message for msg in important_messages)
            if not is_important:
                import psutil
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                self.memory_label.setText(f"Memory: {memory_mb:.1f} MB")
        except ImportError:
            if self.status_label.text() not in ["Applied main_window.css", "Modern UI styling applied", "Stylesheet reloaded", "Toolbar icons active"]:
                self.memory_label.setText("Memory: N/A (psutil not available)")
        except Exception as e:
            self.logger.warning(f"Failed to update memory status: {str(e)}")
            if self.status_label.text() not in ["Applied main_window.css", "Modern UI styling applied", "Stylesheet reloaded", "Toolbar icons active"]:
                self.memory_label.setText("Memory: Error")

    def _toggle_background_hasher(self) -> None:
        """Toggle pause/resume of background hasher."""
        try:
            if not self.background_hasher or not self.background_hasher.isRunning():
                # Not running, start it
                self._start_background_hasher()
                return

            if self.background_hasher.is_paused():
                # Resume
                self.background_hasher.resume()
                self.hash_indicator.setToolTip("Background hashing active - Click to pause")
                self.main_window.statusBar().showMessage("Background hashing resumed", 2000)
            else:
                # Pause
                self.background_hasher.pause()
                self.hash_indicator.setToolTip("Background hashing paused - Click to resume")
                self.main_window.statusBar().showMessage("Background hashing paused", 2000)
        except Exception as e:
            self.logger.error(f"Failed to toggle background hasher: {e}")

    def _start_background_hasher(self) -> None:
        """Start the background hasher thread."""
        try:
            if self.background_hasher and self.background_hasher.isRunning():
                self.logger.debug("Background hasher already running")
                return

            from src.gui.background_hasher import BackgroundHasher

            self.background_hasher = BackgroundHasher(self.main_window)
            self.background_hasher.hash_progress.connect(self._on_hash_progress)
            self.background_hasher.model_hashed.connect(self._on_model_hashed)
            self.background_hasher.duplicate_found.connect(self._on_duplicate_found)
            self.background_hasher.all_complete.connect(self._on_hashing_complete)

            self.background_hasher.start()

            # Update indicator - solid when hashing
            self.hash_indicator.setVisible(True)
            self.hash_indicator.setToolTip("Background hashing active - Click to pause")

            self.logger.info("Background hasher started")
        except Exception as e:
            self.logger.error(f"Failed to start background hasher: {e}")

    def _on_hash_progress(self, filename: str) -> None:
        """Handle hash progress update."""
        try:
            self.main_window.statusBar().showMessage(f"Hashing: {filename}", 1000)
        except Exception:
            pass

    def _on_model_hashed(self, model_id: int, file_hash: str) -> None:
        """Handle model hashed successfully."""
        try:
            self.logger.debug(f"Model {model_id} hashed: {file_hash[:16]}...")
        except Exception:
            pass

    def _on_duplicate_found(self, new_model_id: int, existing_id: int, new_path: str, old_path: str) -> None:
        """Handle duplicate file detected - prompt user for action."""
        try:
            reply = QMessageBox.question(
                self.main_window,
                "File Location Changed",
                f"This file already exists in the library but has moved:\n\n"
                f"Old: {old_path}\n"
                f"New: {new_path}\n\n"
                f"Update to new location?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if reply == QMessageBox.Yes:
                # Update to new path, delete old entry
                db_manager = get_database_manager()
                db_manager.update_model_path(existing_id, new_path)
                db_manager.delete_model(new_model_id)
                self.logger.info(f"Updated file path for model {existing_id}, removed duplicate {new_model_id}")

                # Refresh model library if available
                if hasattr(self.main_window, 'model_library_widget'):
                    self.main_window.model_library_widget._load_models_from_database()
            else:
                # Keep duplicate, just mark it as hashed with the same hash
                db_manager = get_database_manager()
                existing = db_manager.get_model(existing_id)
                if existing and existing.get('file_hash'):
                    db_manager.update_file_hash(new_model_id, existing['file_hash'])

        except Exception as e:
            self.logger.error(f"Failed to handle duplicate: {e}")

    def _on_hashing_complete(self) -> None:
        """Handle all hashing complete."""
        try:
            self.hash_indicator.setToolTip("Background hashing idle - Click to start")
            self.main_window.statusBar().showMessage("Background hashing complete", 2000)
            self.logger.info("Background hashing completed")
        except Exception:
            pass

    def update_layout_edit_mode(self, is_enabled: bool) -> None:
        """
        Update the layout edit mode indicator.

        Args:
            is_enabled: Whether layout edit mode is enabled
        """
        try:
            if is_enabled:
                self.layout_edit_indicator.setText("Layout Edit Mode: ON")
            else:
                self.layout_edit_indicator.setText("Layout Edit Mode: OFF")
        except Exception as e:
            self.logger.warning(f"Failed to update layout edit mode indicator: {e}")


# Convenience function for easy status bar setup
def setup_main_window_status_bar(main_window: QMainWindow, logger: Optional[logging.Logger] = None) -> StatusBarManager:
    """
    Convenience function to set up status bar for a main window.

    Args:
        main_window: The main window to set up status bar for
        logger: Optional logger instance

    Returns:
        StatusBarManager instance for further status bar operations
    """
    manager = StatusBarManager(main_window, logger)
    manager.setup_status_bar()
    manager.setup_status_timer()
    return manager
