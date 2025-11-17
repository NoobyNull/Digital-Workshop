"""
Unified Progress Window System.

This package provides a unified progress window that adapts to different
operation modes (import, thumbnail generation, analysis, etc.).

Main Components:
- UnifiedProgressWindow: Main window class
- ProgressWindowMode: Operation mode definitions
- StageProgress: Progress tracking for individual stages
- ThumbnailProgress: Specialized progress for thumbnail generation
"""

from .progress_window_mode import (
    ProgressWindowMode,
    StageStatus,
    StageProgress,
    ThumbnailProgress,
    OverallProgress,
    StageConfiguration,
    ProgressWeights,
)

__all__ = [
    "ProgressWindowMode",
    "StageStatus",
    "StageProgress",
    "ThumbnailProgress",
    "OverallProgress",
    "StageConfiguration",
    "ProgressWeights",
]
