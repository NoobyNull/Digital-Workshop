"""
Deduplication manager for handling duplicate model detection and resolution.

Provides functionality to:
- Find duplicate models by hash
- Get file statistics (size, date modified)
- Handle deduplication based on user preferences
- Track linked/deduplicated models
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .logging_config import get_logger

logger = get_logger(__name__)


class DeduplicationManager:
    """Manages duplicate detection and resolution."""

    def __init__(self, db_manager) -> None:
        """
        Initialize deduplication manager.

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.logger = get_logger(__name__)

    def find_all_duplicates(self) -> Dict[str, List[Dict]]:
        """
        Find all duplicate models grouped by hash.

        Returns:
            Dict mapping file_hash to list of model dicts with that hash
        """
        try:
            all_models = self.db_manager.get_all_models()
            duplicates_by_hash = {}

            for model in all_models:
                file_hash = model.get("file_hash")
                if not file_hash or file_hash == "":
                    continue

                if file_hash not in duplicates_by_hash:
                    duplicates_by_hash[file_hash] = []

                duplicates_by_hash[file_hash].append(model)

            # Filter to only hashes with multiple models
            return {
                hash_val: models
                for hash_val, models in duplicates_by_hash.items()
                if len(models) > 1
            }

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to find duplicates: %s", e)
            return {}

    def get_file_stats(self, file_path: str) -> Optional[Dict]:
        """
        Get file statistics (size, modification time).

        Args:
            file_path: Path to file

        Returns:
            Dict with 'size' and 'modified' keys, or None if file not found
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return None

            stat = path.stat()
            return {
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime),
            }

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to get file stats for %s: {e}", file_path)
            return None

    def deduplicate_group(
        self, models: List[Dict], keep_strategy: str
    ) -> Tuple[int, List[int]]:
        """
        Deduplicate a group of duplicate models.

        Args:
            models: List of duplicate model dicts
            keep_strategy: 'largest', 'smallest', 'newest', or 'oldest'

        Returns:
            Tuple of (model_id_to_keep, list_of_model_ids_to_delete)
        """
        try:
            if not models:
                return None, []

            # Determine which model to keep
            if keep_strategy == "largest":
                keep_model = max(
                    models,
                    key=lambda m: (
                        self.get_file_stats(m["file_path"]).get("size", 0)
                        if self.get_file_stats(m["file_path"])
                        else 0
                    ),
                )
            elif keep_strategy == "smallest":
                keep_model = min(
                    models,
                    key=lambda m: (
                        self.get_file_stats(m["file_path"]).get("size", float("inf"))
                        if self.get_file_stats(m["file_path"])
                        else float("inf")
                    ),
                )
            elif keep_strategy == "newest":
                keep_model = max(
                    models,
                    key=lambda m: (
                        self.get_file_stats(m["file_path"]).get(
                            "modified", datetime.min
                        )
                        if self.get_file_stats(m["file_path"])
                        else datetime.min
                    ),
                )
            elif keep_strategy == "oldest":
                keep_model = min(
                    models,
                    key=lambda m: (
                        self.get_file_stats(m["file_path"]).get(
                            "modified", datetime.max
                        )
                        if self.get_file_stats(m["file_path"])
                        else datetime.max
                    ),
                )
            else:
                self.logger.error("Unknown keep strategy: %s", keep_strategy)
                return None, []

            keep_id = keep_model["id"]
            delete_ids = [m["id"] for m in models if m["id"] != keep_id]

            # Link deleted models to the kept model
            for delete_id in delete_ids:
                self.db_manager.link_duplicate_model(delete_id, keep_id)
                self.logger.info("Linked duplicate model %s to {keep_id}", delete_id)

            return keep_id, delete_ids

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to deduplicate group: %s", e)
            return None, []

    def get_duplicate_count(self) -> int:
        """
        Get total count of duplicate models.

        Returns:
            Number of models that are duplicates
        """
        try:
            duplicates = self.find_all_duplicates()
            total = 0
            for models in duplicates.values():
                # Count all but the first (kept) model
                total += len(models) - 1
            return total
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to get duplicate count: %s", e)
            return 0
