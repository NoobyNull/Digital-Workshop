"""Persistent settings for import concurrency and background processing."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Tuple

from PySide6.QtCore import QSettings

from src.core.logging_config import get_logger

logger = get_logger(__name__)


def _cpu_count() -> int:
    """Return detected CPU count with safe fallback."""

    try:
        count = os.cpu_count() or 1
    except (ValueError, OSError):
        count = 1
    return max(1, count)


def _default_prep_threads() -> int:
    """Choose a conservative default for disk/hash workers."""

    count = _cpu_count()
    # Keep I/O friendly: half the cores but at least 1, at most 6.
    return max(1, min(6, max(1, count // 2)))


def _default_thumbnail_workers() -> int:
    """Default number of concurrent thumbnail jobs."""

    # Favor GPU availability heuristics later; for now limit to 2-4.
    count = _cpu_count()
    if count >= 8:
        return 3
    if count >= 4:
        return 2
    return 1


def _default_queue_limit() -> int:
    """Max queued prepared files awaiting downstream stages."""

    return 8


@dataclass
class ImportConcurrencySettings:
    """Simple container describing concurrency preferences."""

    prep_workers: int
    thumbnail_workers: int
    queue_limit: int


class ImportSettings:
    """Manage persistent import behavior settings using QSettings."""

    GROUP = "import"

    def __init__(self, qsettings: Optional[QSettings] = None) -> None:
        self._settings = qsettings or QSettings()

    def get_concurrency(self) -> ImportConcurrencySettings:
        """Return the current concurrency configuration."""

        self._settings.beginGroup(self.GROUP)
        try:
            prep = int(
                self._settings.value("prep_workers", _default_prep_threads(), type=int)
            )
            thumbs = int(
                self._settings.value(
                    "thumbnail_workers", _default_thumbnail_workers(), type=int
                )
            )
            queue = int(
                self._settings.value("queue_limit", _default_queue_limit(), type=int)
            )
        finally:
            self._settings.endGroup()

        return ImportConcurrencySettings(
            prep_workers=max(1, prep),
            thumbnail_workers=max(1, thumbs),
            queue_limit=max(2, queue),
        )

    def set_concurrency(
        self, prep_workers: int, thumbnail_workers: int, queue_limit: int
    ) -> None:
        """Persist new concurrency values."""

        prep_workers = max(1, int(prep_workers))
        thumbnail_workers = max(1, int(thumbnail_workers))
        queue_limit = max(2, int(queue_limit))

        self._settings.beginGroup(self.GROUP)
        try:
            self._settings.setValue("prep_workers", prep_workers)
            self._settings.setValue("thumbnail_workers", thumbnail_workers)
            self._settings.setValue("queue_limit", queue_limit)
        finally:
            self._settings.endGroup()

        logger.info(
            "Updated import concurrency: prep=%s, thumbnails=%s, queue=%s",
            prep_workers,
            thumbnail_workers,
            queue_limit,
        )

    def reset_defaults(self) -> None:
        """Reset to detected defaults."""

        self.set_concurrency(
            _default_prep_threads(), _default_thumbnail_workers(), _default_queue_limit()
        )


def get_import_settings() -> ImportSettings:
    """Factory to mirror other settings helpers."""

    return ImportSettings()
