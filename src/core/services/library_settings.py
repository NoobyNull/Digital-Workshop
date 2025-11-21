"""Helpers for persistent library configuration.

This module centralizes how the application stores and retrieves
library-related settings such as the global library mode, the
consolidated library root path, and markers for offline databases
when a removable library drive goes missing.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QSettings

from src.core.logging_config import get_logger
from src.core.path_manager import get_cache_directory

logger = get_logger(__name__)


RECENT_MAX_ENTRIES_DEFAULT = 20
DEFAULT_PROJECTS_DIRNAME = "Digital Workshop Projects"
WATCH_FOLDER_NAME = "_Inbox"
DOWNLOADS_FOLDER_NAME = "Downloads"


class LibraryMode(str, Enum):
    """Global behavior for how imported files are handled.

    LEAVE_IN_PLACE:
        The application tracks files where they currently live on disk.
    CONSOLIDATED:
        Imports are expected to live under a single managed library root.
    """

    LEAVE_IN_PLACE = "leave_in_place"
    CONSOLIDATED = "consolidated"


class LibrarySettings:
    """Thin wrapper around :class:`QSettings` for library configuration.

    All keys are stored under a single ``"library"`` group so that other
    parts of the application can continue to use QSettings without
    colliding with these values.
    """

    GROUP = "library"

    def __init__(self) -> None:
        self._settings = QSettings()

    # ------------------------------------------------------------------
    # Setup flag
    # ------------------------------------------------------------------
    def is_setup_completed(self) -> bool:
        """Return whether the first-launch library setup has run."""

        self._settings.beginGroup(self.GROUP)
        try:
            return bool(self._settings.value("setup_completed", False, type=bool))
        finally:
            self._settings.endGroup()

    def set_setup_completed(self, completed: bool) -> None:
        """Persist the first-launch setup completion flag."""

        self._settings.beginGroup(self.GROUP)
        try:
            self._settings.setValue("setup_completed", bool(completed))
        finally:
            self._settings.endGroup()

    # ------------------------------------------------------------------
    # Mode + base root
    # ------------------------------------------------------------------
    def get_mode(self) -> LibraryMode:
        """Return the configured :class:`LibraryMode`.

        Defaults to :attr:`LibraryMode.LEAVE_IN_PLACE` if unset or
        if an invalid value is found in settings.
        """

        self._settings.beginGroup(self.GROUP)
        try:
            raw = self._settings.value(
                "mode", LibraryMode.LEAVE_IN_PLACE.value, type=str
            )
        finally:
            self._settings.endGroup()

        try:
            return LibraryMode(raw)
        except ValueError:
            logger.warning("Unknown library mode in settings: %s", raw)
            return LibraryMode.LEAVE_IN_PLACE

    def set_mode(self, mode: LibraryMode) -> None:
        """Persist the global library mode."""

        self._settings.beginGroup(self.GROUP)
        try:
            self._settings.setValue("mode", mode.value)
        finally:
            self._settings.endGroup()

    def get_base_root(self) -> Optional[Path]:
        """Return the configured consolidated library root, if any."""

        self._settings.beginGroup(self.GROUP)
        try:
            raw = self._settings.value("base_root", "", type=str)
        finally:
            self._settings.endGroup()

        if not raw:
            return None
        return Path(raw)

    def set_base_root(self, root: Optional[Path]) -> None:
        """Persist the consolidated library root path.

        Passing ``None`` clears the stored value.
        """

        self._settings.beginGroup(self.GROUP)
        try:
            if root is None:
                self._settings.remove("base_root")
            else:
                self._settings.setValue("base_root", str(root))
        finally:
            self._settings.endGroup()

    def get_default_projects_root(self) -> Path:
        """Return the default projects folder under Documents."""

        documents_dir = Path.home() / "Documents"
        if not documents_dir.exists():
            documents_dir = Path.home()
        return documents_dir / DEFAULT_PROJECTS_DIRNAME

    def ensure_projects_root(self) -> Path:
        """Ensure the managed projects root exists and return it."""

        root = self.get_base_root()
        if root is None:
            root = self.get_default_projects_root()
            self.set_base_root(root)

        try:
            root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.error("Failed to create projects root %s: %s", root, exc)
            raise

        return root

    def get_watch_folder(self) -> Path:
        """Return the managed import watch folder path, creating it if needed."""

        root = self.ensure_projects_root()
        watch = root / WATCH_FOLDER_NAME
        watch.mkdir(parents=True, exist_ok=True)
        return watch

    def get_downloads_cache(self) -> Path:
        """Return the application downloads cache directory."""

        cache_root = get_cache_directory()
        downloads = cache_root / DOWNLOADS_FOLDER_NAME
        downloads.mkdir(parents=True, exist_ok=True)
        return downloads

    # ------------------------------------------------------------------
    # Offline database markers
    # ------------------------------------------------------------------
    def get_offline_db_path(self) -> Optional[Path]:
        """Return the path of the offline/original database, if recorded."""

        self._settings.beginGroup(self.GROUP)
        try:
            raw = self._settings.value("offline_db_path", "", type=str)
        finally:
            self._settings.endGroup()

        if not raw:
            return None
        return Path(raw)

    def set_offline_db_path(self, path: Optional[Path]) -> None:
        """Persist or clear the offline/original database path marker."""

        self._settings.beginGroup(self.GROUP)
        try:
            if path is None:
                self._settings.remove("offline_db_path")
            else:
                self._settings.setValue("offline_db_path", str(path))
        finally:
            self._settings.endGroup()

    def get_temp_db_path(self) -> Optional[Path]:
        """Return the path of the temporary database, if recorded."""

        self._settings.beginGroup(self.GROUP)
        try:
            raw = self._settings.value("temp_db_path", "", type=str)
        finally:
            self._settings.endGroup()

        if not raw:
            return None
        return Path(raw)

    def set_temp_db_path(self, path: Optional[Path]) -> None:
        """Persist or clear the temporary database path marker."""

        self._settings.beginGroup(self.GROUP)
        try:
            if path is None:
                self._settings.remove("temp_db_path")
            else:
                self._settings.setValue("temp_db_path", str(path))
        finally:
            self._settings.endGroup()

    # ------------------------------------------------------------------
    # Recent models (MRU) preferences
    # ------------------------------------------------------------------
    def get_recent_max_entries(self) -> int:
        """Return the configured MRU length for recent models."""

        self._settings.beginGroup(self.GROUP)
        try:
            raw = self._settings.value(
                "recent_max_entries", RECENT_MAX_ENTRIES_DEFAULT, type=int
            )
        finally:
            self._settings.endGroup()

        try:
            value = int(raw)
        except (TypeError, ValueError):
            value = RECENT_MAX_ENTRIES_DEFAULT

        return max(1, value)

    def set_recent_max_entries(self, limit: int) -> None:
        """Persist the MRU length for recent models."""

        limit = max(1, int(limit))

        self._settings.beginGroup(self.GROUP)
        try:
            self._settings.setValue("recent_max_entries", limit)
        finally:
            self._settings.endGroup()
