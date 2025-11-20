"""
Import Coordinator for 3D Model Import Process.

Central orchestrator that coordinates the entire import workflow by integrating:
- FastHasher for file hashing
- ImportFileManager for file management
- ImportThumbnailService for thumbnail generation
- ImportAnalysisService for model analysis
- Database integration for storing import results

Provides:
- Workflow orchestration across all import stages
- Progress aggregation from all components
- Cancellation management across all services
- Error handling and recovery coordination
- Database integration for storing import results

Performance targets:
- Handle multiple files concurrently
- Non-blocking UI during import
- Efficient resource utilization
- Comprehensive error recovery

Example:
    >>> coordinator = ImportCoordinator()
    >>> coordinator.start_import(
    ...     file_paths=["model1.stl", "model2.stl"],
    ...     mode=FileManagementMode.KEEP_ORGANIZED,
    ...     root_directory="/path/to/root",
    ...     progress_callback=lambda stage, pct, msg: print(f"{stage}: {pct}% - {msg}")
    ... )
"""

import time
import gc
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import QThread, Signal, QObject

from src.core.logging_config import get_logger, get_activity_logger
from src.core.cancellation_token import CancellationToken
from src.core.import_file_manager import (
    ImportFileManager,
    FileManagementMode,
    DuplicateAction,
    ImportSession,
    ImportResult,
    ImportFileInfo,
)
from src.core.import_thumbnail_service import (
    ImportThumbnailService,
    ThumbnailBatchResult,
)
from src.core.import_analysis_service import (
    ImportAnalysisService,
    BatchAnalysisResult,
)
from src.core.database_manager import get_database_manager
from src.core.services.image_pairing_service import get_image_pairing_service


class ImportWorkflowStage(Enum):
    """Stages of the import workflow."""

    IDLE = "idle"
    VALIDATION = "validation"
    FILE_DISCOVERY = "file_discovery"
    HASHING = "hashing"
    FILE_MANAGEMENT = "file_management"
    THUMBNAIL_GENERATION = "thumbnail_generation"
    DATABASE_STORAGE = "database_storage"
    BACKGROUND_ANALYSIS = "background_analysis"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ImportProgress:
    """Consolidated progress information from all import stages."""

    stage: ImportWorkflowStage
    overall_percent: float
    current_file_index: int
    total_files: int
    current_file_name: str
    stage_message: str
    stage_percent: float

    # Detailed stage progress
    files_hashed: int = 0
    files_copied: int = 0
    thumbnails_generated: int = 0
    analyses_completed: int = 0

    # Performance metrics
    elapsed_time_seconds: float = 0.0
    estimated_time_remaining_seconds: Optional[float] = None


@dataclass
class ImportCoordinatorResult:
    """Final result from the import coordinator."""

    success: bool
    import_result: Optional[ImportResult]
    thumbnail_result: Optional[ThumbnailBatchResult]
    analysis_result: Optional[BatchAnalysisResult]
    total_duration_seconds: float
    error_message: Optional[str] = None

    # Statistics
    models_imported: int = 0
    models_failed: int = 0
    models_skipped: int = 0
    duplicates_detected: int = 0


class ImportCoordinatorWorker(QThread):
    """
    Background worker thread for coordinated import process.

    Orchestrates all import stages without blocking the UI thread.
    """

    # Signals for progress communication
    stage_changed = Signal(object, str)  # ImportWorkflowStage, message
    progress_updated = Signal(object)  # ImportProgress
    import_completed = Signal(object)  # ImportCoordinatorResult
    import_failed = Signal(str)  # error_message

    def __init__(
        self,
        file_paths: List[str],
        mode: FileManagementMode,
        root_directory: Optional[str],
        generate_thumbnails: bool,
        run_analysis: bool,
        duplicate_action: DuplicateAction,
        cancellation_token: Optional[CancellationToken] = None,
    ):
        """
        Initialize the import coordinator worker.

        Args:
            file_paths: List of file paths to import
            mode: File management mode
            root_directory: Root directory for organized mode
            generate_thumbnails: Whether to generate thumbnails
            run_analysis: Whether to run background analysis
            duplicate_action: How to handle duplicates
            cancellation_token: Optional cancellation token
        """
        super().__init__()
        self.file_paths = file_paths
        self.mode = mode
        self.root_directory = root_directory
        self.generate_thumbnails = generate_thumbnails
        self.run_analysis = run_analysis
        self.duplicate_action = duplicate_action
        self.cancellation_token = cancellation_token or CancellationToken()

        self.logger = get_logger(__name__)
        self.activity_logger = get_activity_logger(__name__)
        self.start_time: Optional[float] = None

        # Initialize services
        self.file_manager = ImportFileManager()
        self.thumbnail_service = ImportThumbnailService() if generate_thumbnails else None
        self.analysis_service = ImportAnalysisService() if run_analysis else None
        self.db_manager = get_database_manager()
        self._batches: List[List[str]] = []
        try:
            cap = ImportFileManager.MAX_IMPORT_FILES
            if cap and isinstance(cap, int) and cap > 0:
                paths = list(file_paths)
                self._batches = [paths[i : i + cap] for i in range(0, len(paths), cap)]
            else:
                self._batches = [list(file_paths)]
        except Exception:
            self._batches = [list(file_paths)]

    def run(self) -> None:
        """Execute the coordinated import process."""
        self.start_time = time.time()

        try:
            # Stage 1: Validation
            self._update_stage(ImportWorkflowStage.VALIDATION, "Validating import settings...")
            if not self._validate_settings():
                return

            overall_imports = 0
            overall_failed = 0
            overall_skipped = 0
            overall_duplicates = 0
            final_import_result = None
            final_thumbnail_result = None
            final_analysis_result = None

            total_files_all = len(self.file_paths)
            processed_global_index = 0

            for batch_index, batch_paths in enumerate(self._batches):
                if self.cancellation_token.is_cancelled():
                    break

                self._update_stage(
                    ImportWorkflowStage.FILE_DISCOVERY,
                    f"Starting batch {batch_index + 1}/{len(self._batches)} "
                    f"({len(batch_paths)} files)...",
                )

                session = self._start_import_session(batch_paths)
                if not session:
                    break

                total_files = len(session.files)
                self.logger.info(
                    "Starting coordinated import batch %s/%s of %s files",
                    batch_index + 1,
                    len(self._batches),
                    total_files,
                )

                processed_files = self._process_files(
                    session, processed_global_index, total_files_all
                )
                processed_global_index += len(session.files)

                if self.cancellation_token.is_cancelled():
                    self._handle_cancellation(session)
                    break

                thumbnail_result = None
                if self.generate_thumbnails and processed_files:
                    thumbnail_result = self._generate_thumbnails(processed_files)
                    final_thumbnail_result = thumbnail_result

                self._update_stage(
                    ImportWorkflowStage.DATABASE_STORAGE, "Storing import results..."
                )
                stored_models = self._store_in_database(session, processed_files)

                analysis_result = None
                if self.run_analysis and stored_models:
                    analysis_result = self._queue_analysis(stored_models)
                    final_analysis_result = analysis_result

                import_result = self.file_manager.complete_import_session(session, True)
                final_import_result = import_result

                overall_imports += import_result.processed_files
                overall_failed += import_result.failed_files
                overall_skipped += import_result.skipped_files
                overall_duplicates += import_result.duplicate_count

            total_duration = time.time() - self.start_time

            final_result = ImportCoordinatorResult(
                success=not self.cancellation_token.is_cancelled(),
                import_result=final_import_result,
                thumbnail_result=final_thumbnail_result,
                analysis_result=final_analysis_result,
                total_duration_seconds=total_duration,
                models_imported=overall_imports,
                models_failed=overall_failed,
                models_skipped=overall_skipped,
                duplicates_detected=overall_duplicates,
            )

            if self.cancellation_token.is_cancelled():
                self._update_stage(ImportWorkflowStage.CANCELLED, "Import cancelled")
                self.import_failed.emit("Import cancelled")
            else:
                self._update_stage(ImportWorkflowStage.COMPLETED, "Import completed successfully")
                self.import_completed.emit(final_result)

            gc.collect()

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Import coordinator failed: %s", e, exc_info=True)
            self.import_failed.emit(str(e))

    def _validate_settings(self) -> bool:
        """Validate import settings."""
        try:
            # Validate file management mode and root directory
            is_valid, error = self.file_manager.validate_root_directory(
                self.root_directory, self.mode
            )

            if not is_valid:
                self.import_failed.emit(f"Validation failed: {error}")
                return False

            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Settings validation failed: %s", e, exc_info=True)
            self.import_failed.emit(f"Validation error: {e}")
            return False

    def _start_import_session(self, batch_paths: Optional[List[str]] = None) -> Optional[ImportSession]:
        """Start a new import session."""
        try:
            success, error, session = self.file_manager.start_import_session(
                batch_paths or self.file_paths, self.mode, self.root_directory, self.duplicate_action
            )

            if not success:
                self.import_failed.emit(f"Failed to start import session: {error}")
                return None

            return session

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to start import session: %s", e, exc_info=True)
            self.import_failed.emit(f"Session start error: {e}")
            return None

    def _process_files(
        self, session: ImportSession, processed_global_index: int, total_files_all: int
    ) -> List[ImportFileInfo]:
        """Process all files in the session."""
        self._update_stage(ImportWorkflowStage.HASHING, "Processing files...")

        processed_files = []
        total_files = len(session.files)

        for idx, file_info in enumerate(session.files):
            if self.cancellation_token.is_cancelled():
                break

            file_name = Path(file_info.original_path).name

            # Create progress callback
            def file_progress(message: str, percent: int) -> None:
                overall_idx = processed_global_index + idx
                progress = ImportProgress(
                    stage=ImportWorkflowStage.HASHING,
                    overall_percent=((overall_idx) / max(total_files_all, 1)) * 100,
                    current_file_index=overall_idx + 1,
                    total_files=total_files_all,
                    current_file_name=file_name,
                    stage_message=message,
                    stage_percent=percent,
                    files_hashed=len(processed_files),
                    elapsed_time_seconds=time.time() - self.start_time,
                )
                self.progress_updated.emit(progress)

            # Process file
            success, error = self.file_manager.process_file(
                file_info, session, file_progress, self.cancellation_token
            )

            if success:
                processed_files.append(file_info)
            else:
                self.logger.warning("Failed to process %s: {error}", file_name)

        return processed_files

    def _generate_thumbnails(
        self, processed_files: List[ImportFileInfo]
    ) -> Optional[ThumbnailBatchResult]:
        """
        Generate thumbnails for processed files with image pairing support.

        Checks for matching image files (e.g., model1.stl + model1.jpg) and uses
        them as thumbnails instead of generating via VTK rendering.
        """
        self._update_stage(ImportWorkflowStage.THUMBNAIL_GENERATION, "Generating thumbnails...")

        try:
            # Load thumbnail settings from preferences
            from src.core.application_config import ApplicationConfig
            from PySide6.QtCore import QSettings
            import shutil

            config = ApplicationConfig.get_default()
            settings = QSettings()

            # Get current thumbnail preferences
            bg_image = settings.value(
                "thumbnail/background_image", config.thumbnail_bg_image, type=str
            )
            material = settings.value("thumbnail/material", config.thumbnail_material, type=str)
            bg_color = settings.value(
                "thumbnail/background_color", config.thumbnail_bg_color, type=str
            )

            # Use background image if set, otherwise use background color
            background = bg_image if bg_image else bg_color

            # Get image pairing service
            pairing_service = get_image_pairing_service()

            # Collect all file paths for pairing detection
            all_file_paths = [f.managed_path or f.original_path for f in processed_files]

            # Find image-model pairs
            pairs, unpaired_models, unpaired_images = pairing_service.find_pairs(all_file_paths)

            # Track paired thumbnails
            paired_count = 0
            thumbnail_dir = Path(config.thumbnail_directory)
            thumbnail_dir.mkdir(parents=True, exist_ok=True)

            # Process paired images first
            for pair in pairs:
                # Find the corresponding file info
                file_info = next(
                    (
                        f
                        for f in processed_files
                        if (f.managed_path or f.original_path) == pair.model_path
                    ),
                    None,
                )

                if not file_info or not file_info.file_hash:
                    continue

                # Validate the paired image
                if not pairing_service.validate_image(pair.image_path):
                    self.logger.warning(
                        "Paired image invalid, will generate thumbnail: %s",
                        pair.image_path,
                    )
                    continue

                # Copy paired image as thumbnail
                try:
                    thumbnail_path = thumbnail_dir / f"{file_info.file_hash}.png"
                    shutil.copy2(pair.image_path, thumbnail_path)
                    paired_count += 1
                    self.logger.info(
                        "Used paired image as thumbnail: %s -> %s",
                        Path(pair.image_path).name,
                        thumbnail_path.name,
                    )
                except (OSError, IOError) as e:
                    self.logger.error("Failed to copy paired image: %s", e)

            # Prepare file list for VTK thumbnail generation (unpaired models only)
            file_info_list = [
                (f.managed_path or f.original_path, f.file_hash)
                for f in processed_files
                if f.file_hash
                and f.import_status == "completed"
                and (f.managed_path or f.original_path) in unpaired_models
            ]

            total_files = len(file_info_list) + paired_count

            if not file_info_list and paired_count == 0:
                return None

            # Generate thumbnails for unpaired models
            result = None
            if file_info_list:

                def progress_callback(completed: int, total: int, current_file: str) -> None:
                    """Progress callback for thumbnail generation."""
                    total_completed = paired_count + completed
                    progress = ImportProgress(
                        stage=ImportWorkflowStage.THUMBNAIL_GENERATION,
                        overall_percent=70 + (total_completed / total_files) * 20,  # 70-90%
                        current_file_index=total_completed,
                        total_files=total_files,
                        current_file_name=current_file,
                        stage_message=f"Generating thumbnail for {current_file}",
                        stage_percent=(total_completed / total_files) * 100,
                        thumbnails_generated=total_completed,
                        elapsed_time_seconds=time.time() - self.start_time,
                    )
                    self.progress_updated.emit(progress)

                result = self.thumbnail_service.generate_thumbnails_batch(
                    file_info_list,
                    progress_callback,
                    self.cancellation_token,
                    background=background,
                    material=material,
                )

            self.logger.info(
                "Thumbnail generation complete: %d paired, %d generated",
                paired_count,
                len(file_info_list) if file_info_list else 0,
            )

            return result

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Thumbnail generation failed: %s", e, exc_info=True)
            return None

    def _store_in_database(
        self, session: ImportSession, processed_files: List[ImportFileInfo]
    ) -> List[Dict[str, Any]]:
        """Store import results in the database."""
        stored_models = []

        try:
            # For now, just prepare the data structure
            for file_info in processed_files:
                if file_info.import_status == "completed":
                    model_data = {
                        "file_path": file_info.managed_path or file_info.original_path,
                        "file_hash": file_info.file_hash,
                        "file_size": file_info.file_size,
                        "file_management_mode": session.mode.value,
                        "import_session_id": session.session_id,
                        "original_path": file_info.original_path,
                        "managed_path": file_info.managed_path,
                    }
                    stored_models.append(model_data)

            self.logger.info("Prepared %s models for database storage", len(stored_models))

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Database storage failed: %s", e, exc_info=True)

        return stored_models

    def _queue_analysis(self, stored_models: List[Dict[str, Any]]) -> Optional[BatchAnalysisResult]:
        """Queue background analysis for imported models."""
        self._update_stage(
            ImportWorkflowStage.BACKGROUND_ANALYSIS, "Queueing background analysis..."
        )

        try:
            # Prepare file-model pairs for analysis
            file_model_pairs = [
                (model["file_path"], idx + 1) for idx, model in enumerate(stored_models)
            ]

            if not file_model_pairs:
                return None

            # Note: Analysis runs in background, so we don't wait for completion
            self.analysis_service.start_batch_analysis(
                file_model_pairs, cancellation_token=self.cancellation_token
            )

            self.logger.info("Queued %s models for background analysis", len(file_model_pairs))
            return None  # Analysis result will come later via signals

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to queue analysis: %s", e, exc_info=True)
            return None

    def _handle_cancellation(self, session: ImportSession) -> None:
        """Handle import cancellation."""
        self.logger.info("Import cancelled, performing rollback...")

        try:
            # Rollback any file operations
            self.file_manager.rollback_session(session)

            # Complete session as cancelled
            result = self.file_manager.complete_import_session(session, False)
            total_duration = time.time() - self.start_time

            final_result = ImportCoordinatorResult(
                success=False,
                import_result=result,
                thumbnail_result=None,
                analysis_result=None,
                total_duration_seconds=total_duration,
                error_message="Import cancelled by user",
            )

            self._update_stage(ImportWorkflowStage.CANCELLED, "Import cancelled")
            self.import_completed.emit(final_result)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Cancellation handling failed: %s", e, exc_info=True)

    def _update_stage(self, stage: ImportWorkflowStage, message: str) -> None:
        """Update current stage and emit signal."""
        self.stage_changed.emit(stage, message)
        self.logger.info("Import stage: %s - {message}", stage.value)


class ImportCoordinator(QObject):
    """
    Central coordinator for the 3D model import process.

    Orchestrates the entire import workflow by integrating all import services:
    - FastHasher for file hashing
    - ImportFileManager for file management
    - ImportThumbnailService for thumbnail generation
    - ImportAnalysisService for model analysis
    - Database integration for storing results

    Provides:
    - High-level import API
    - Progress aggregation from all stages
    - Cancellation support across all services
    - Error handling and recovery
    - Comprehensive logging

    Example:
        >>> coordinator = ImportCoordinator()
        >>> coordinator.progress_updated.connect(
        ...     lambda progress: print(f"{progress.stage}: {progress.overall_percent}%")
        ... )
        >>> coordinator.start_import(
        ...     file_paths=["model1.stl", "model2.stl"],
        ...     mode=FileManagementMode.KEEP_ORGANIZED,
        ...     root_directory="/path/to/root"
        ... )
    """

    # Signals
    stage_changed = Signal(object, str)  # ImportWorkflowStage, message
    progress_updated = Signal(object)  # ImportProgress
    import_completed = Signal(object)  # ImportCoordinatorResult
    import_failed = Signal(str)  # error_message

    PENDING_KEY = "import/pending_batches"

    def __init__(self, parent=None) -> None:
        """
        Initialize the import coordinator.

        Args:
            parent: Optional parent QObject
        """
        super().__init__(parent)
        self.logger = get_logger(__name__)

        # Active worker
        self._worker: Optional[ImportCoordinatorWorker] = None
        self._cancellation_token: Optional[CancellationToken] = None

        # Statistics
        self._stats = {
            "total_imports": 0,
            "successful_imports": 0,
            "failed_imports": 0,
            "cancelled_imports": 0,
            "total_files_imported": 0,
            "total_import_time": 0.0,
        }

        self.logger.info("ImportCoordinator initialized")

    @staticmethod
    def _load_pending_batches() -> list[list[str]]:
        try:
            from PySide6.QtCore import QSettings
            import json

            settings = QSettings()
            raw = settings.value(ImportCoordinator.PENDING_KEY, "[]", type=str) or "[]"
            batches = json.loads(raw)
            # Ensure list of lists of strings
            sanitized: list[list[str]] = []
            for batch in batches:
                if isinstance(batch, list):
                    sanitized.append([str(p) for p in batch])
            return sanitized
        except Exception:
            return []

    @staticmethod
    def _save_pending_batches(batches: list[list[str]]) -> None:
        try:
            from PySide6.QtCore import QSettings
            import json

            settings = QSettings()
            settings.setValue(ImportCoordinator.PENDING_KEY, json.dumps(batches))
        except Exception:
            pass

    @staticmethod
    def pending_batch_count() -> int:
        """Helper to expose pending batch count for UI display."""
        return len(ImportCoordinator._load_pending_batches())

    def start_import(
        self,
        file_paths: List[str],
        mode: FileManagementMode,
        root_directory: Optional[str] = None,
        generate_thumbnails: bool = True,
        run_analysis: bool = True,
        duplicate_action: DuplicateAction = DuplicateAction.SKIP,
    ) -> bool:
        """
        Start a coordinated import process.

        Args:
            file_paths: List of file paths to import
            mode: File management mode
            root_directory: Root directory (required for KEEP_ORGANIZED mode)
            generate_thumbnails: Whether to generate thumbnails
            run_analysis: Whether to run background analysis
            duplicate_action: How to handle duplicates

        Returns:
            True if import started successfully, False otherwise
        """
        if self.is_import_running():
            self.logger.warning("Import already running")
            return False

        if not file_paths:
            self.logger.warning("No files provided for import")
            return False

        try:
            # Create cancellation token
            self._cancellation_token = CancellationToken()

            # Split into batches respecting MAX_IMPORT_FILES
            try:
                from src.core.import_file_manager import ImportFileManager

                cap = ImportFileManager.MAX_IMPORT_FILES
            except Exception:
                cap = 500

            paths = list(file_paths)
            batches: list[list[str]] = [paths[i : i + cap] for i in range(0, len(paths), cap)] or [paths]

            # Persist any remaining batches beyond the first
            pending_batches = batches[1:] if len(batches) > 1 else []
            self._save_pending_batches(pending_batches)

            # Create and configure worker for the first/current batch
            self._worker = ImportCoordinatorWorker(
                file_paths=batches[0],
                mode=mode,
                root_directory=root_directory,
                generate_thumbnails=generate_thumbnails,
                run_analysis=run_analysis,
                duplicate_action=duplicate_action,
                cancellation_token=self._cancellation_token,
            )

            # Connect signals
            self._worker.stage_changed.connect(self._on_stage_changed)
            self._worker.progress_updated.connect(self._on_progress_updated)
            self._worker.import_completed.connect(self._on_import_completed)
            self._worker.import_failed.connect(self._on_import_failed)
            self._worker.finished.connect(self._on_worker_finished)

            # Start worker
            self._worker.start()

            self._stats["total_imports"] += 1

            self.logger.info(
                "Started coordinated import of %s files (batch size %s, pending batches: %s)",
                len(file_paths),
                len(batches[0]),
                len(pending_batches),
            )
            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to start import: %s", e, exc_info=True)
            return False

    def cancel_import(self) -> bool:
        """
        Cancel the current import operation.

        Returns:
            True if cancellation was requested, False if no import running
        """
        if not self.is_import_running():
            return False

        if self._cancellation_token:
            self._cancellation_token.cancel()
            self.logger.info("Import cancellation requested")
            return True

        return False

    def is_import_running(self) -> bool:
        """
        Check if an import is currently running.

        Returns:
            True if import is running, False otherwise
        """
        return self._worker is not None and self._worker.isRunning()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get import statistics.

        Returns:
            Dictionary with import statistics
        """
        return {
            **self._stats,
            "avg_import_time": (
                self._stats["total_import_time"] / max(1, self._stats["successful_imports"])
            ),
            "success_rate": (
                (self._stats["successful_imports"] / max(1, self._stats["total_imports"])) * 100
            ),
        }

    def _on_stage_changed(self, stage: ImportWorkflowStage, message: str) -> None:
        """Handle stage change from worker."""
        self.stage_changed.emit(stage, message)

    def _on_progress_updated(self, progress: ImportProgress) -> None:
        """Handle progress update from worker."""
        self.progress_updated.emit(progress)

    def _on_import_completed(self, result: ImportCoordinatorResult) -> None:
        """Handle import completion."""
        if result.success:
            self._stats["successful_imports"] += 1
            self._stats["total_files_imported"] += result.models_imported
        else:
            if result.error_message and "cancel" in result.error_message.lower():
                self._stats["cancelled_imports"] += 1
            else:
                self._stats["failed_imports"] += 1

        self._stats["total_import_time"] += result.total_duration_seconds

        # Log to activity logger so user sees it in console
        self.activity_logger.info(
            f"Import completed: {result.models_imported} models imported "
            f"in {result.total_duration_seconds:.1f} seconds"
        )

        self.import_completed.emit(result)

    def _on_import_failed(self, error_message: str) -> None:
        """Handle import failure."""
        self._stats["failed_imports"] += 1
        self.logger.error("Import failed: %s", error_message)
        self.import_failed.emit(error_message)

    def _on_worker_finished(self) -> None:
        """Handle worker thread completion."""
        self._worker = None
        self._cancellation_token = None


__all__ = [
    "ImportCoordinator",
    "ImportCoordinatorResult",
    "ImportProgress",
    "ImportWorkflowStage",
]
