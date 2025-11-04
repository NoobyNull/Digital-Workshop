"""
Deduplication service for managing duplicate detection and resolution.

Integrates with background hasher and provides UI coordination.
"""

from typing import Dict, List, Optional

from PySide6.QtCore import QObject, Signal

from src.core.logging_config import get_logger
from src.core.deduplication_manager import DeduplicationManager
from src.gui.deduplication_dialog import DeduplicationDialog

logger = get_logger(__name__)


class DeduplicationService(QObject):
    """Service for coordinating deduplication operations."""

    # Signals
    hashing_started = Signal()
    hashing_progress = Signal(str, float)  # filename, progress_percent
    hashing_complete = Signal()
    duplicates_found = Signal(int)  # duplicate_count
    deduplication_complete = Signal()

    def __init__(self, db_manager, parent=None) -> None:
        """
        Initialize deduplication service.

        Args:
            db_manager: Database manager instance
            parent: Parent QObject
        """
        super().__init__(parent)
        self.db_manager = db_manager
        self.dedup_manager = DeduplicationManager(db_manager)
        self.logger = get_logger(__name__)
        self.pending_duplicates = {}  # Hash -> list of models

    def start_hashing(self) -> None:
        """Start background hashing process."""
        self.hashing_started.emit()
        self.logger.info("Hashing started")

    def on_hash_progress(self, filename: str, progress: float) -> None:
        """
        Handle hash progress update.

        Args:
            filename: Current file being hashed
            progress: Progress percentage (0-100)
        """
        self.hashing_progress.emit(filename, progress)

    def on_hashing_complete(self) -> None:
        """Handle hashing completion."""
        self.hashing_complete.emit()

        # Check for duplicates
        duplicates = self.dedup_manager.find_all_duplicates()
        duplicate_count = self.dedup_manager.get_duplicate_count()

        if duplicate_count > 0:
            self.pending_duplicates = duplicates
            self.duplicates_found.emit(duplicate_count)
            self.logger.info("Found %s duplicate models", duplicate_count)
        else:
            self.logger.info("No duplicates found")

    def show_deduplication_dialog(self, file_hash: str, parent=None) -> Optional[str]:
        """
        Show deduplication dialog for a duplicate group.

        Args:
            file_hash: Hash of duplicate group
            parent: Parent widget

        Returns:
            Selected keep strategy or None if cancelled
        """
        if file_hash not in self.pending_duplicates:
            return None

        models = self.pending_duplicates[file_hash]
        dialog = DeduplicationDialog(models, parent)

        if dialog.exec() == DeduplicationDialog.Accepted:
            return dialog.get_keep_strategy()

        return None

    def deduplicate_group(self, file_hash: str, keep_strategy: str) -> bool:
        """
        Deduplicate a group of duplicate models.

        Args:
            file_hash: Hash of duplicate group
            keep_strategy: 'largest', 'smallest', 'newest', or 'oldest'

        Returns:
            True if successful
        """
        if file_hash not in self.pending_duplicates:
            return False

        models = self.pending_duplicates[file_hash]

        try:
            keep_id, delete_ids = self.dedup_manager.deduplicate_group(models, keep_strategy)

            if keep_id is None:
                return False

            # Delete the duplicate models
            for delete_id in delete_ids:
                self.db_manager.delete_model(delete_id)
                self.logger.info("Deleted duplicate model %s", delete_id)

            # Remove from pending
            del self.pending_duplicates[file_hash]

            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to deduplicate group: %s", e)
            return False

    def deduplicate_all(self, keep_strategy: str) -> int:
        """
        Deduplicate all pending duplicates with same strategy.

        Args:
            keep_strategy: 'largest', 'smallest', 'newest', or 'oldest'

        Returns:
            Number of models deleted
        """
        deleted_count = 0

        for file_hash in list(self.pending_duplicates.keys()):
            if self.deduplicate_group(file_hash, keep_strategy):
                deleted_count += len(self.pending_duplicates.get(file_hash, [])) - 1

        self.deduplication_complete.emit()
        return deleted_count

    def get_pending_duplicate_count(self) -> int:
        """Get count of pending duplicates."""
        total = 0
        for models in self.pending_duplicates.values():
            total += len(models) - 1
        return total

    def get_pending_duplicate_groups(self) -> Dict[str, List[Dict]]:
        """Get all pending duplicate groups."""
        return self.pending_duplicates.copy()
