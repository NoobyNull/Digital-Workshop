from pathlib import Path

from PySide6.QtCore import Signal, Slot

from src.core.database_manager import get_database_manager
from src.core.fast_hasher import FastHasher
from src.core.import_thumbnail_service import ImportThumbnailService
from src.gui.workers.base_worker import BaseWorker


class ThumbnailBackfillWorker(BaseWorker):
    """
    Background worker to regenerate thumbnails for models missing them.

    Now uses BaseWorker for consistent cancellation and progress signalling.
    """

    progress = Signal(int, int)  # processed, total
    finished = Signal(int, int)  # completed, total
    failed = Signal(str)

    def __init__(self, logger) -> None:
        super().__init__()
        self._logger = logger

    def cancel(self) -> None:
        """Request cancellation."""
        self.request_cancel()

    @Slot()
    def run(self) -> None:
        """Execute the backfill in a background thread."""
        try:
            db_manager = get_database_manager()
            models = db_manager.get_all_models()
            missing = [m for m in models if not m.get("thumbnail_path")]
            total = len(missing)

            if total == 0:
                self.finished.emit(0, 0)
                return

            thumbnail_service = ImportThumbnailService()
            hasher = FastHasher()
            completed = 0

            for idx, model in enumerate(missing, 1):
                if self.is_cancel_requested():
                    self._logger.info("Thumbnail backfill cancelled")
                    break

                file_path = model.get("file_path")
                if not file_path or not Path(file_path).exists():
                    continue
                try:
                    hash_result = hasher.hash_file(file_path)
                    file_hash = hash_result.hash_value if hash_result.success else None
                    if not file_hash:
                        continue
                    thumbnail_service.generate_thumbnail(
                        model_path=file_path,
                        file_hash=file_hash,
                        material="default",
                        background=None,
                        force_regenerate=False,
                    )
                    completed += 1
                except Exception as exc:  # pragma: no cover - best effort
                    self._logger.debug(
                        "Thumbnail backfill failed for %s: %s", file_path, exc
                    )
                self.progress.emit(idx, total)

            self.finished.emit(completed, total)
        except Exception as exc:  # pragma: no cover - best effort
            self.failed.emit(str(exc))
