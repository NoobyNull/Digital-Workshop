"""
Background hashing worker for Digital Workshop.

Processes unhashed models in the background without blocking the UI.
Provides duplicate detection and file recovery functionality.

Enhanced to use the new FastHasher for optimal performance.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, Signal

from src.core.logging_config import get_logger
from src.core.database_manager import get_database_manager
from src.core.fast_hasher import FastHasher
from src.core.cancellation_token import CancellationToken


class BackgroundHasher(QThread):
    """
    Background worker thread that processes unhashed models.

    Signals:
        hash_progress: Emitted with (filename) when hashing a file
        model_hashed: Emitted with (model_id, file_hash) when hash is calculated
        duplicate_found: Emitted with (model_id, existing_id, new_path, old_path) when duplicate detected
        all_complete: Emitted when all unhashed models are processed
    """

    hash_progress = Signal(str)  # filename being hashed
    model_hashed = Signal(int, str)  # model_id, file_hash
    duplicate_found = Signal(int, int, str, str)  # new_model_id, existing_id, new_path, old_path
    all_complete = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.db_manager = get_database_manager()
        self.fast_hasher = FastHasher()
        self.cancellation_token = CancellationToken()
        self._paused = False
        self._running = True

    def pause(self) -> None:
        """Pause background hashing."""
        self._paused = True
        self.logger.info("Background hashing paused")

    def resume(self) -> None:
        """Resume background hashing."""
        self._paused = False
        self.logger.info("Background hashing resumed")

    def stop(self) -> None:
        """Stop background hashing completely."""
        self._running = False
        self._paused = False
        self.cancellation_token.cancel()
        self.logger.info("Background hashing stopped")

    def is_paused(self) -> bool:
        """Check if hasher is paused."""
        return self._paused

    def run(self) -> None:
        """Main thread loop - processes unhashed models one by one."""
        self.logger.info("Background hasher started")

        while self._running:
            # Wait if paused
            if self._paused:
                self.msleep(100)
                continue

            # Get next unhashed model
            unhashed_models = self.db_manager.get_unhashed_models(limit=1)

            if not unhashed_models:
                # No more models to hash
                self.all_complete.emit()
                self.logger.info("Background hashing complete - no more unhashed models")
                break

            model = unhashed_models[0]
            model_id = model.get('id')
            file_path = model.get('file_path')
            filename = Path(file_path).name if file_path else "Unknown"

            if not file_path or not Path(file_path).exists():
                self.logger.warning(f"File not found for model {model_id}: {file_path}")
                # Mark with empty hash so we don't try again
                self.db_manager.update_file_hash(model_id, "")
                continue

            try:
                # Emit progress
                self.hash_progress.emit(filename)

                # Calculate hash using FastHasher
                result = self.fast_hasher.hash_file(
                    file_path,
                    cancellation_token=self.cancellation_token
                )

                if not result.success:
                    self.logger.error(f"Failed to calculate hash for {filename}: {result.error}")
                    # Mark with empty hash so we don't try again
                    self.db_manager.update_file_hash(model_id, "")
                    continue
                
                file_hash = result.hash_value

                # Check for duplicates before updating
                existing = self.db_manager.find_model_by_hash(file_hash)

                if existing and existing.get('id') != model_id:
                    existing_id = existing.get('id')
                    existing_path = existing.get('file_path')

                    self.logger.info(f"Duplicate hash detected: {filename} matches existing model {existing_id}")

                    # Check if file moved (hash match but path different)
                    if existing_path != file_path:
                        # Emit signal for UI to handle
                        self.duplicate_found.emit(model_id, existing_id, file_path, existing_path)
                    else:
                        # Same file, same path - just update hash on current model
                        self.db_manager.update_file_hash(model_id, file_hash)
                        self.model_hashed.emit(model_id, file_hash)
                else:
                    # No duplicate, update hash
                    self.db_manager.update_file_hash(model_id, file_hash)
                    self.model_hashed.emit(model_id, file_hash)
                    self.logger.info(f"Hashed model {model_id}: {filename}")

            except Exception as e:
                self.logger.error(f"Error hashing model {model_id} ({filename}): {e}")
                # Mark with empty hash so we don't try again
                self.db_manager.update_file_hash(model_id, "")

            # Small delay between models to avoid blocking
            self.msleep(50)

        self.logger.info("Background hasher thread finished")
