"""
Thin controller wrapper for the import dialog to separate UI wiring from worker orchestration.
"""

from __future__ import annotations

from typing import Optional, List

from src.core.import_file_manager import FileManagementMode, ImportResult
from src.gui.import_components.import_workers import (
    ImportJobConfig,
    ImportWorker,
    PipelineImportWorker,
)


class ImportDialogController:
    """Controller that manages the import dialog workers and state."""

    def __init__(self) -> None:
        self.import_worker: Optional[PipelineImportWorker] = None
        self.selected_files: List[str] = []
        self.start_time: Optional[float] = None

    def start_import(
        self,
        file_paths: List[str],
        mode: FileManagementMode,
        root_directory: Optional[str],
        generate_thumbnails: bool,
        run_analysis: bool,
        use_pipeline: bool = True,
    ) -> ImportWorker | PipelineImportWorker:
        """Create and return the appropriate worker for the import job."""
        config = ImportJobConfig(
            generate_thumbnails=generate_thumbnails, run_analysis=run_analysis
        )
        if use_pipeline:
            self.import_worker = PipelineImportWorker(
                file_paths, mode, root_directory, config=config
            )
            return self.import_worker

        worker = ImportWorker(file_paths, mode, root_directory, config=config)
        return worker

    def cancel(self) -> None:
        """Cancel any running import worker."""
        if self.import_worker and self.import_worker.isRunning():
            self.import_worker.cancel()

    def clear(self) -> None:
        """Reset controller state."""
        self.import_worker = None
        self.selected_files = []
        self.start_time = None
