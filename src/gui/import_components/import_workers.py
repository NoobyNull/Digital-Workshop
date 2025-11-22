"""
Import workers extracted from import_dialog for modularity.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, List, Tuple
from dataclasses import dataclass

from PySide6.QtCore import Signal, QSettings

from src.core.logging_config import get_logger
from src.core.cancellation_token import CancellationToken
from src.core.application_config import ApplicationConfig
from src.core.services.import_settings import ImportSettings
from src.core.import_file_manager import (
    ImportFileManager,
    FileManagementMode,
    DuplicateAction,
)
from src.core.import_thumbnail_service import ImportThumbnailService
from src.core.import_analysis_service import ImportAnalysisService
from src.gui.thumbnail_generation_coordinator import ThumbnailGenerationCoordinator
from src.gui.workers.base_worker import BaseWorker
from src.core.import_pipeline import (
    create_pipeline,
    ImportStage,
    ImportTask,
    PipelineProgress,
    PipelineResult,
)
from src.core.database_manager import get_database_manager
from src.core.thumbnail_generator import ThumbnailGenerator


@dataclass
class ImportJobConfig:
    """Simple container for import job options."""

    generate_thumbnails: bool = True
    run_analysis: bool = False
    concurrency_mode: str = "serial"
    prep_workers: int = 1
    pipeline_workers: int = 1


class ImportWorker(BaseWorker):
    """
    Background worker thread for import process.

    Handles all import operations without blocking the UI thread.
    """

    # Signals for progress communication
    stage_changed = Signal(str, str)  # stage, message
    file_progress = Signal(str, int, str)  # filename, percent, message
    overall_progress = Signal(int, int, int)  # current, total, percent
    thumbnail_progress = Signal(int, int, str)  # current, total, current_file
    import_completed = Signal(object)  # ImportResult
    import_failed = Signal(str)  # error_message

    def __init__(
        self,
        file_paths: List[str],
        mode: FileManagementMode,
        root_directory: Optional[str],
        config: Optional[ImportJobConfig] = None,
    ):
        super().__init__()
        self.file_paths = file_paths
        self.mode = mode
        self.root_directory = root_directory
        self.config = config or ImportJobConfig()
        self.generate_thumbnails = self.config.generate_thumbnails
        self.run_analysis = self.config.run_analysis

        self.logger = get_logger(__name__)
        self.cancellation_token = CancellationToken()
        self.generated_thumbnails: List[Tuple[str, str]] = []

        # Initialize services
        self.file_manager = ImportFileManager()
        self.import_settings = ImportSettings()
        self.thumbnail_service = (
            ImportThumbnailService() if self.generate_thumbnails else None
        )
        self.analysis_service = (
            ImportAnalysisService() if self.run_analysis else None
        )

    def run(self) -> None:
        """Execute the import process."""
        try:
            self.stage_changed.emit("validation", "Validating files and settings...")

            # Start import session
            success, error, session = self.file_manager.start_import_session(
                self.file_paths, self.mode, self.root_directory, DuplicateAction.SKIP
            )

            if not success:
                self.import_failed.emit(error)
                return

            total_files = len(session.files)
            files_to_process = []

            # Process each file
            for idx, file_info in enumerate(session.files):
                if self.cancellation_token.is_cancelled():
                    break

                file_name = Path(file_info.original_path).name

                # Report overall progress
                self.overall_progress.emit(
                    idx, total_files, int((idx / total_files) * 100)
                )

                # Process file (hashing + copying if needed)
                self.stage_changed.emit("hashing", f"Processing {file_name}...")

                def file_progress_callback(
                    message, percent, current_name=file_name
                ) -> None:
                    self.file_progress.emit(current_name, percent, message)

                success, error = self.file_manager.process_file(
                    file_info, session, file_progress_callback, self.cancellation_token
                )

                if not success:
                    self.logger.warning("Failed to process %s: {error}", file_name)
                    continue

                # Collect files for thumbnail generation (don't generate here - it blocks!)
                if self.generate_thumbnails and file_info.file_hash:
                    files_to_process.append(
                        (
                            file_info.managed_path or file_info.original_path,
                            file_info.file_hash,
                        )
                    )

            # Generate thumbnails in separate worker (truly non-blocking)
            if files_to_process:
                self.stage_changed.emit(
                    "thumbnails",
                    f"Generating thumbnails for {len(files_to_process)} files...",
                )
                self._generate_thumbnails_with_window(files_to_process)

            # Complete import session
            result = self.file_manager.complete_import_session(
                session, not self.cancellation_token.is_cancelled()
            )

            # Start background analysis if enabled
            if self.run_analysis and result.processed_files > 0:
                self.stage_changed.emit("analysis", "Queueing background analysis...")
                # Analysis runs in background, doesn't block completion
                file_model_pairs = [
                    (f.managed_path or f.original_path, idx + 1)
                    for idx, f in enumerate(session.files)
                    if f.import_status == "completed"
                ]
                if file_model_pairs:
                    self.analysis_service.start_batch_analysis(
                        file_model_pairs, cancellation_token=self.cancellation_token
                    )

            self.import_completed.emit(result)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Import worker failed: %s", e, exc_info=True)
            self.import_failed.emit(str(e))

    def cancel(self) -> None:
        """Cancel the import operation."""
        self.cancellation_token.cancel()

    def _generate_thumbnails_with_window(
        self, files_to_process: List[Tuple[str, str]]
    ) -> None:
        """
        Generate thumbnails using dedicated window.

        Args:
            files_to_process: List of (model_path, file_hash) tuples
        """
        try:
            config = ApplicationConfig.get_default()
            settings = QSettings()

            # Get current thumbnail preferences
            bg_image = settings.value(
                "thumbnail/background_image",
                config.thumbnail_bg_image,
                type=str,
            )
            material = settings.value(
                "thumbnail/material", config.thumbnail_material, type=str
            )
            bg_color = settings.value(
                "thumbnail/background_color",
                config.thumbnail_bg_color,
                type=str,
            )

            # Prefer tuple(image, color) when both are set so the renderer can apply both.
            background = (
                (bg_image, bg_color)
                if bg_image and bg_color
                else (bg_image or bg_color)
            )

            self.logger.debug(
                "Thumbnail preferences: bg_image=%s, bg_color=%s, material=%s",
                bg_image,
                bg_color,
                material,
            )

            # Create coordinator and generate thumbnails
            coordinator = ThumbnailGenerationCoordinator()
            # Capture generated thumbnail paths for downstream tagging.
            captured: List[Tuple[str, str]] = []
            coordinator.thumbnail_generated.connect(
                lambda file_path, thumb_path: captured.append((file_path, thumb_path))
            )
            coordinator.generate_thumbnails(
                file_info_list=files_to_process,
                background=background,
                material=material,
            )

            # Wait for completion
            coordinator.wait_for_completion()
            self.generated_thumbnails = captured

            self.logger.info("Thumbnail generation completed")

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning("Failed to generate thumbnails: %s", e)


class PipelineImportWorker(BaseWorker):
    """
    Pipeline-based import worker using the modular import pipeline.
    """

    # Signals for progress communication
    stage_changed = Signal(str, str)  # stage, message
    file_progress = Signal(str, int, str)  # filename, percent, message
    overall_progress = Signal(int, int, int)  # current, total, percent
    thumbnail_progress = Signal(int, int, str)  # current, total, current_file
    model_imported = Signal(dict)
    import_completed = Signal(object)  # ImportResult or None when cancelled
    import_cancelled = Signal()
    import_failed = Signal(str)  # error_message

    def __init__(
        self,
        file_paths: List[str],
        mode: FileManagementMode,
        root_directory: Optional[str],
        config: Optional[ImportJobConfig] = None,
    ):
        super().__init__()
        self.file_paths = file_paths
        self.mode = mode
        self.root_directory = root_directory
        self.config = config or ImportJobConfig()
        self.generate_thumbnails = self.config.generate_thumbnails
        self.run_analysis = self.config.run_analysis
        self.concurrency_mode = self.config.concurrency_mode
        self.prep_workers = max(1, int(self.config.prep_workers))
        self.pipeline_workers = max(1, int(self.config.pipeline_workers))

        self.logger = get_logger(__name__)
        self.cancellation_token = CancellationToken()
        self._pipeline = None
        self._last_result: Optional[PipelineResult] = None
        self._last_error: Optional[str] = None
        self._tasks: List[ImportTask] = []

    def run(self) -> None:
        """Run the import pipeline."""
        try:
            db_manager = get_database_manager()
            thumbnail_generator = ThumbnailGenerator()
            pipeline = create_pipeline(
                db_manager, thumbnail_generator, max_workers=self.pipeline_workers
            )
            self._pipeline = pipeline
            self._connect_pipeline_signals(pipeline)

            self._tasks = [self._build_task(Path(path)) for path in self.file_paths]

            if not self._tasks:
                self.import_failed.emit("No import tasks to process")
                return

            self.stage_changed.emit(
                ImportStage.PENDING.value, "Starting pipeline import..."
            )
            pipeline.execute(self._tasks)

            if self._last_error:
                self.import_failed.emit(self._last_error)
            elif self.cancellation_token.is_cancelled():
                self.import_cancelled.emit()
            elif self._last_result:
                self.import_completed.emit(self._last_result)
            else:
                # Fallback result when signals were not emitted as expected
                self.import_completed.emit(
                    PipelineResult(
                        total_tasks=len(self._tasks),
                        successful_tasks=len(self._tasks),
                        failed_tasks=0,
                        skipped_tasks=0,
                        total_duration_seconds=0.0,
                    )
                )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Pipeline import worker failed: %s", e, exc_info=True)
            self.import_failed.emit(str(e))

    def cancel(self) -> None:
        """Cancel the import pipeline."""
        self.cancellation_token.cancel()
        if self._pipeline:
            self._pipeline.cancel()
        self.import_cancelled.emit()

    def _build_task(self, file_path: Path) -> ImportTask:
        """Create an ImportTask with minimal required metadata."""
        file_size = file_path.stat().st_size if file_path.exists() else 0
        fmt = file_path.suffix.lstrip(".").lower() or "unknown"
        return ImportTask(
            file_path=str(file_path),
            filename=file_path.name,
            format=fmt,
            file_size=file_size,
        )

    def _connect_pipeline_signals(self, pipeline) -> None:
        """Bridge pipeline signals to dialog-friendly signals."""
        pipeline.signals.progress_updated.connect(self._on_pipeline_progress)
        pipeline.signals.stage_started.connect(self._on_stage_started)
        pipeline.signals.stage_completed.connect(self._on_stage_completed)
        pipeline.signals.task_completed.connect(self._on_task_completed)
        pipeline.signals.task_failed.connect(self._on_task_failed)
        pipeline.signals.pipeline_completed.connect(self._on_pipeline_completed)
        pipeline.signals.pipeline_failed.connect(self._on_pipeline_failed)
        pipeline.signals.pipeline_cancelled.connect(self._on_pipeline_cancelled)

    def _on_pipeline_progress(self, progress: PipelineProgress) -> None:
        percent = int(progress.progress_percentage)
        self.overall_progress.emit(
            progress.completed_tasks, progress.total_tasks, percent
        )

    def _on_stage_started(self, task: ImportTask, stage_name: str) -> None:
        self.stage_changed.emit(stage_name, f"{task.filename}: {stage_name}")
        self.file_progress.emit(task.filename, 0, stage_name)

    def _on_stage_completed(self, result) -> None:
        stage_enum = getattr(result, "stage", None)
        if stage_enum:
            stage_name = (
                stage_enum.value if hasattr(stage_enum, "value") else str(stage_enum)
            )
            self.stage_changed.emit(stage_name, f"Completed {stage_name}")

    def _on_task_completed(self, task: ImportTask) -> None:
        self.file_progress.emit(task.filename, 100, "completed")
        self.model_imported.emit(task.to_dict())

    def _on_task_failed(self, task: ImportTask, error: str) -> None:
        self.file_progress.emit(task.filename, 100, f"failed: {error}")
        self._last_error = error

    def _on_pipeline_completed(self, result: PipelineResult) -> None:
        self._last_result = result

    def _on_pipeline_failed(self, error: str) -> None:
        self._last_error = error
        self.import_failed.emit(error)

    def _on_pipeline_cancelled(self) -> None:
        self.import_cancelled.emit()
