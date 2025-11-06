"""
Signal definitions for the import pipeline.

Defines all Qt signals used for communication between pipeline components.
"""

from PySide6.QtCore import QObject, Signal

from src.core.import_pipeline.pipeline_models import (
    ImportTask,
    StageResult,
    PipelineProgress,
    PipelineResult,
)


class PipelineSignals(QObject):
    """
    Signals emitted by the import pipeline coordinator.

    These signals allow GUI components to track pipeline progress and respond
    to events without tight coupling.
    """

    # Pipeline lifecycle signals
    pipeline_started = Signal(int)  # total_tasks
    pipeline_completed = Signal(PipelineResult)
    pipeline_failed = Signal(str)  # error_message
    pipeline_cancelled = Signal()

    # Progress signals
    progress_updated = Signal(PipelineProgress)
    task_started = Signal(ImportTask)
    task_completed = Signal(ImportTask)
    task_failed = Signal(ImportTask, str)  # task, error_message

    # Stage-specific signals
    stage_started = Signal(ImportTask, str)  # task, stage_name
    stage_completed = Signal(StageResult)
    stage_failed = Signal(ImportTask, str, str)  # task, stage_name, error_message


class StageSignals(QObject):
    """
    Signals emitted by individual pipeline stages.

    Each stage emits these signals to communicate with the coordinator.
    """

    started = Signal(ImportTask)
    completed = Signal(StageResult)
    failed = Signal(ImportTask, str)  # task, error_message
    progress = Signal(ImportTask, float)  # task, progress_percentage


class WorkerSignals(QObject):
    """
    Signals emitted by async workers (QRunnable).

    These are used by worker threads to communicate results back to the main thread.
    """

    # Worker lifecycle
    started = Signal(str)  # task_id or file_path
    completed = Signal(object)  # result object (varies by worker type)
    failed = Signal(str, str)  # task_id or file_path, error_message

    # Progress reporting
    progress = Signal(str, float, str)  # task_id, progress_percentage, message

