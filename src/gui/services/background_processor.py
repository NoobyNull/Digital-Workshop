"""
Background Processing System Module

This module handles background processing tasks such as file hashing,
model processing, and other long-running operations that should not
block the main UI thread.

Classes:
    BackgroundProcessor: Main class for managing background processing tasks
"""

import logging
from typing import Optional

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QMainWindow, QMessageBox

from src.core.database_manager import get_database_manager


class BackgroundHasher(QThread):
    """
    Background thread for hashing model files to detect duplicates.

    This thread runs in the background to process model files and calculate
    their hashes for duplicate detection without blocking the main UI.
    """

    # Signals for communication with main thread
    hash_progress = Signal(str)  # filename
    model_hashed = Signal(int, str)  # model_id, file_hash
    duplicate_found = Signal(int, int, str, str)  # new_id, existing_id, new_path, old_path
    all_complete = Signal()

    def __init__(self, main_window: QMainWindow):
        """
        Initialize the background hasher.

        Args:
            main_window: The main window instance
        """
        super().__init__(main_window)
        self.main_window = main_window
        self._is_paused = False
        self._is_stopped = False

    def run(self):
        """Main thread execution method."""
        try:
            # Get all models that need hashing
            db_manager = get_database_manager()
            models = db_manager.get_models_needing_hash()

            for model in models:
                if self._is_stopped:
                    break

                while self._is_paused and not self._is_stopped:
                    self.msleep(100)  # Sleep for 100ms while paused

                if self._is_stopped:
                    break

                try:
                    # Emit progress signal
                    self.hash_progress.emit(model["filename"])

                    # Calculate file hash
                    file_hash = self._calculate_file_hash(model["file_path"])

                    # Check for duplicates
                    existing_model = db_manager.find_model_by_hash(file_hash)

                    if existing_model:
                        # Duplicate found - emit signal for user decision
                        self.duplicate_found.emit(
                            model["id"],
                            existing_model["id"],
                            model["file_path"],
                            existing_model["file_path"],
                        )
                    else:
                        # No duplicate - update hash
                        db_manager.update_file_hash(model["id"], file_hash)
                        self.model_hashed.emit(model["id"], file_hash)

                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                    self.main_window.logger.warning("Failed to hash model %s: {e}", model['id'])

            # Signal completion
            self.all_complete.emit()

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.main_window.logger.error("Background hasher error: %s", e)

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate xxHash128 for a file."""
        import xxhash

        hasher = xxhash.xxh128()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def pause(self):
        """Pause the background processing."""
        self._is_paused = True

    def resume(self):
        """Resume the background processing."""
        self._is_paused = False

    def stop(self):
        """Stop the background processing."""
        self._is_stopped = True

    def is_paused(self) -> bool:
        """Check if the thread is paused."""
        return self._is_paused


class BackgroundProcessor:
    """
    Manages background processing tasks for the main window.

    This class coordinates background threads and handles the communication
    between background tasks and the main UI thread.
    """

    def __init__(self, main_window: QMainWindow, logger: Optional[logging.Logger] = None):
        """
        Initialize the background processor.

        Args:
            main_window: The main window instance
            logger: Optional logger instance for debugging
        """
        self.main_window = main_window
        self.logger = logger or logging.getLogger(__name__)
        self.background_hasher = None

    def start_background_hasher(self) -> None:
        """Start the background hasher thread."""
        try:
            if self.background_hasher and self.background_hasher.isRunning():
                self.logger.debug("Background hasher already running")
                return

            self.background_hasher = BackgroundHasher(self.main_window)
            self.background_hasher.hash_progress.connect(self._on_hash_progress)
            self.background_hasher.model_hashed.connect(self._on_model_hashed)
            self.background_hasher.duplicate_found.connect(self._on_duplicate_found)
            self.background_hasher.all_complete.connect(self._on_hashing_complete)

            self.background_hasher.start()

            self.logger.info("Background hasher started")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to start background hasher: %s", e)

    def toggle_background_hasher(self) -> None:
        """Toggle pause/resume of background hasher."""
        try:
            if not self.background_hasher or not self.background_hasher.isRunning():
                # Not running, start it
                self.start_background_hasher()
                return

            if self.background_hasher.is_paused():
                # Resume
                self.background_hasher.resume()
                self.main_window.statusBar().showMessage("Background hashing resumed", 2000)
            else:
                # Pause
                self.background_hasher.pause()
                self.main_window.statusBar().showMessage("Background hashing paused", 2000)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to toggle background hasher: %s", e)

    def _on_hash_progress(self, filename: str) -> None:
        """Handle hash progress update."""
        try:
            self.main_window.statusBar().showMessage(f"Hashing: {filename}", 1000)
        except Exception:
            pass

    def _on_model_hashed(self, model_id: int, file_hash: str) -> None:
        """Handle model hashed successfully."""
        try:
            self.logger.debug("Model %s hashed: {file_hash[:16]}...", model_id)
        except Exception:
            pass

    def _on_duplicate_found(
        self, new_model_id: int, existing_id: int, new_path: str, old_path: str
    ) -> None:
        """Handle duplicate file detected - prompt user for action."""
        try:
            reply = QMessageBox.question(
                self.main_window,
                "File Location Changed",
                "This file already exists in the library but has moved:\n\n"
                f"Old: {old_path}\n"
                f"New: {new_path}\n\n"
                "Update to new location?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )

            if reply == QMessageBox.Yes:
                # Update to new path, delete old entry
                db_manager = get_database_manager()
                db_manager.update_model_path(existing_id, new_path)
                db_manager.delete_model(new_model_id)
                self.logger.info(
                    f"Updated file path for model {existing_id}, removed duplicate {new_model_id}"
                )

                # Refresh model library if available
                if hasattr(self.main_window, "model_library_widget"):
                    self.main_window.model_library_widget._load_models_from_database()
            else:
                # Keep duplicate, just mark it as hashed with the same hash
                db_manager = get_database_manager()
                existing = db_manager.get_model(existing_id)
                if existing and existing.get("file_hash"):
                    db_manager.update_file_hash(new_model_id, existing["file_hash"])

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to handle duplicate: %s", e)

    def _on_hashing_complete(self) -> None:
        """Handle all hashing complete."""
        try:
            self.main_window.statusBar().showMessage("Background hashing complete", 2000)
            self.logger.info("Background hashing completed")
        except Exception:
            pass


# Convenience function for easy background processing setup
def setup_background_processing(
    main_window: QMainWindow, logger: Optional[logging.Logger] = None
) -> BackgroundProcessor:
    """
    Convenience function to set up background processing for a main window.

    Args:
        main_window: The main window to set up background processing for
        logger: Optional logger instance

    Returns:
        BackgroundProcessor instance for further background operations
    """
    return BackgroundProcessor(main_window, logger)
