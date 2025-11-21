"""Monitoring for the consolidated library root and database failover.

This module provides :class:`LibraryRootMonitor`, a small helper that
checks whether the configured library root still exists and, if not,
backs up the current database and switches the application to a fresh
"temporary" database. When the root later becomes available again it
can prompt the user to switch back to the original database.

The design is intentionally conservative: no databases are deleted and
all actions are logged. A future revision can extend this to support
true data merging between the temporary and original databases once the
exact semantics have been agreed.
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QMessageBox, QWidget

from src.core.logging_config import get_logger
from src.core.database_manager import close_database_manager, get_database_manager
from src.core.services.library_settings import LibraryMode, LibrarySettings

logger = get_logger(__name__)


class LibraryRootMonitor:
    """Monitor the consolidated library root and manage DB failover.

    The public entry point is :meth:`check_on_startup`, which should be
    called once during application initialisation *after* the Qt
    application has been created.
    """

    def __init__(self, settings: Optional[LibrarySettings] = None) -> None:
        self._settings = settings or LibrarySettings()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def check_on_startup(self, parent: Optional[QWidget] = None) -> None:
        """Check the library root and handle missing/restored scenarios.

        This method is cheap to call and handles both cases:

        * Consolidated library root missing -> backup + fail over to
          a temporary database.
        * Library root restored while an offline database marker is
          recorded -> prompt to switch back to the original DB.
        """

        mode = self._settings.get_mode()
        base_root = self._settings.get_base_root()

        # If no root is configured we only need to check for a pending
        # offline marker so that the user can be offered a choice.
        if base_root is None or mode != LibraryMode.CONSOLIDATED:
            self._maybe_handle_recovery(parent)
            return

        if not base_root.exists():
            self._handle_missing_root(base_root, parent)
        else:
            self._maybe_handle_recovery(parent)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _handle_missing_root(self, base_root: Path, parent: Optional[QWidget]) -> None:
        """Handle the case where the consolidated library root vanished."""

        box = QMessageBox(parent)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle("Library Drive Missing")
        box.setText(
            "The configured library root folder cannot be found.\n\n"
            f"Expected location:\n{base_root}\n\n"
            "The application will switch to a new, empty library database "
            "so you can keep working. The current database will be backed "
            "up first so it can be restored later."
        )
        box.setStandardButtons(QMessageBox.Ok)
        box.exec()

        db_manager = get_database_manager()
        active_path = Path(db_manager.db_path)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        offline_path = active_path.with_name(
            f"{active_path.stem}-offline-{timestamp}{active_path.suffix}"
        )
        try:
            shutil.copy2(active_path, offline_path)
            logger.info(
                "Backed up database before switching to temporary DB: %s -> %s",
                active_path,
                offline_path,
            )
        except OSError as exc:  # pragma: no cover - filesystem dependent
            logger.error(
                "Failed to backup database %s -> %s: %s", active_path, offline_path, exc
            )

        self._settings.set_offline_db_path(offline_path)

        temp_path = active_path.with_name(
            f"{active_path.stem}-temp-{timestamp}{active_path.suffix}"
        )
        self._settings.set_temp_db_path(temp_path)

        close_database_manager()
        get_database_manager(str(temp_path))
        logger.info("Switched to temporary database at %s", temp_path)

    def _maybe_handle_recovery(self, parent: Optional[QWidget]) -> None:
        """If an offline DB is recorded and the root is back, offer recovery."""

        offline_path = self._settings.get_offline_db_path()
        temp_path = self._settings.get_temp_db_path()
        base_root = self._settings.get_base_root()

        if not offline_path or not base_root or not base_root.exists():
            return

        if not offline_path.exists():
            # Offline record is stale; clean it up.
            logger.warning(
                "Recorded offline database no longer exists: %s", offline_path
            )
            self._settings.set_offline_db_path(None)
            self._settings.set_temp_db_path(None)
            return

        box = QMessageBox(parent)
        box.setIcon(QMessageBox.Question)
        box.setWindowTitle("Library Drive Restored")
        box.setText(
            "The library drive is available again.\n\n"
            f"Original database: {offline_path}\n"
            f"Temporary database: {temp_path or '<in-memory>'}\n\n"
            "How would you like to proceed?"
        )

        restore_button = box.addButton(
            "Restore original library", QMessageBox.AcceptRole
        )
        keep_button = box.addButton(
            "Keep using temporary library", QMessageBox.RejectRole
        )
        box.setDefaultButton(restore_button)

        box.exec()
        clicked = box.clickedButton()

        if clicked is restore_button:
            self._switch_to_database(offline_path, temp_path)
        elif clicked is keep_button:
            self._keep_temporary(temp_path)

    def _switch_to_database(
        self, offline_path: Path, temp_path: Optional[Path]
    ) -> None:
        """Switch the singleton manager back to the original database."""

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        if temp_path and temp_path.exists():
            backup_temp = temp_path.with_name(
                f"{temp_path.stem}-backup-{timestamp}{temp_path.suffix}"
            )
            try:
                shutil.copy2(temp_path, backup_temp)
                logger.info(
                    "Backed up temporary database before switching: %s -> %s",
                    temp_path,
                    backup_temp,
                )
            except OSError as exc:  # pragma: no cover - filesystem dependent
                logger.error(
                    "Failed to backup temporary database %s -> %s: %s",
                    temp_path,
                    backup_temp,
                    exc,
                )

        close_database_manager()
        get_database_manager(str(offline_path))
        logger.info("Switched back to original database at %s", offline_path)

        self._settings.set_offline_db_path(None)
        self._settings.set_temp_db_path(None)

    def _keep_temporary(self, temp_path: Optional[Path]) -> None:
        """Continue using the temporary database and clear markers."""

        # Ensure the singleton is pointing at the temporary DB if one exists.
        if temp_path is not None:
            close_database_manager()
            get_database_manager(str(temp_path))
            logger.info("Continuing to use temporary database at %s", temp_path)

        self._settings.set_offline_db_path(None)
        self._settings.set_temp_db_path(None)
