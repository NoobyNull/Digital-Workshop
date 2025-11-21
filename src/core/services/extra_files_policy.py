"""Policy service for handling extra/unknown file types during consolidation.

Stores per-extension decisions (e.g. move_to_misc, leave_in_place) in QSettings
so the consolidation planner and dialogs can behave consistently across runs.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from PySide6.QtCore import QSettings

from src.core.logging_config import get_logger


logger = get_logger(__name__)


class ExtraFileDecision(str, Enum):
    """Possible actions for extra/unknown file types.

    These values are stored in QSettings, so keep them stable.
    """

    MOVE_TO_MISC = "move_to_misc"
    LEAVE_IN_PLACE = "leave_in_place"


@dataclass(frozen=True)
class ExtraFilePolicyEntry:
    """Represents the stored policy for a specific extension."""

    extension: str
    decision: ExtraFileDecision


class ExtraFilesPolicy:
    """Service for persisting user decisions about extra file types.

    The policy is keyed by lowercase file extension (including the leading dot).
    For example: ".mp4" -> MOVE_TO_MISC.
    """

    SETTINGS_GROUP = "extra_files_policy"

    def __init__(self, settings: Optional[QSettings] = None) -> None:
        self._settings = settings or QSettings()

    def _normalize_extension(self, extension: str) -> str:
        """Normalize extension to a canonical form (lowercase, leading dot).

        Args:
            extension: Raw extension, with or without leading dot.
        """

        ext = extension.strip().lower()
        if not ext:
            return ""
        if not ext.startswith("."):
            ext = "." + ext
        return ext

    def get_policy(self, extension: str) -> Optional[ExtraFilePolicyEntry]:
        """Return stored policy for an extension, if any.

        Args:
            extension: File extension (with or without leading dot).
        """

        ext = self._normalize_extension(extension)
        if not ext:
            return None

        self._settings.beginGroup(self.SETTINGS_GROUP)
        try:
            value = self._settings.value(ext, type=str)
        finally:
            self._settings.endGroup()

        if not value:
            return None

        try:
            decision = ExtraFileDecision(value)
        except ValueError:
            logger.warning(
                "Unknown extra file decision '%s' for extension %s", value, ext
            )
            return None

        return ExtraFilePolicyEntry(extension=ext, decision=decision)

    def set_policy(self, extension: str, decision: ExtraFileDecision) -> None:
        """Persist policy for an extension.

        Args:
            extension: File extension (with or without leading dot).
            decision: Decision to store.
        """

        ext = self._normalize_extension(extension)
        if not ext:
            return

        self._settings.beginGroup(self.SETTINGS_GROUP)
        try:
            self._settings.setValue(ext, decision.value)
        finally:
            self._settings.endGroup()

        logger.info("Extra files policy updated: %s -> %s", ext, decision.value)

    def clear_policy(self, extension: str) -> None:
        """Remove stored policy for an extension, if present."""

        ext = self._normalize_extension(extension)
        if not ext:
            return

        self._settings.beginGroup(self.SETTINGS_GROUP)
        try:
            if self._settings.contains(ext):
                self._settings.remove(ext)
        finally:
            self._settings.endGroup()

        logger.info("Extra files policy cleared for %s", ext)

    def clear_all_policies(self) -> None:
        """Remove all stored extra-files policies."""

        self._settings.beginGroup(self.SETTINGS_GROUP)
        try:
            self._settings.remove("")
        finally:
            self._settings.endGroup()

        logger.info("All extra files policies cleared")
