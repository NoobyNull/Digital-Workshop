"""
Run Mode Manager for managing application run modes and preferences.

Handles run mode detection, storage location configuration, and preferences.
"""

from typing import Optional
from pathlib import Path
from PySide6.QtCore import QSettings

from ..logging_config import get_logger, log_function_call
from ..path_manager import PathManager

logger = get_logger(__name__)


class RunModeManager:
    """Manages application run modes and preferences."""

    # Run modes
    RUN_MODE_FIRST_TIME = "first_time"
    RUN_MODE_NORMAL = "normal"
    RUN_MODE_PORTABLE = "portable"

    def __init__(self):
        """Initialize run mode manager."""
        self.logger = logger
        self.settings = QSettings("DigitalWorkshop", "DigitalWorkshop")
        self.path_manager = PathManager()

    @log_function_call(logger)
    def get_run_mode(self) -> str:
        """Get current run mode."""
        try:
            # Check if first run
            if not self.settings.contains("run_mode/initialized"):
                return self.RUN_MODE_FIRST_TIME

            run_mode = self.settings.value("run_mode/mode", self.RUN_MODE_NORMAL)
            logger.info("Run mode: %s", run_mode)
            return run_mode

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to get run mode: %s", str(e))
            return self.RUN_MODE_NORMAL

    @log_function_call(logger)
    def set_run_mode(self, mode: str) -> bool:
        """Set run mode."""
        try:
            if mode not in (
                self.RUN_MODE_FIRST_TIME,
                self.RUN_MODE_NORMAL,
                self.RUN_MODE_PORTABLE,
            ):
                raise ValueError(f"Invalid run mode: {mode}")

            self.settings.setValue("run_mode/mode", mode)
            self.settings.setValue("run_mode/initialized", True)
            logger.info("Set run mode: %s", mode)
            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to set run mode: %s", str(e))
            return False

    @log_function_call(logger)
    def is_first_run(self) -> bool:
        """Check if this is first run."""
        return self.get_run_mode() == self.RUN_MODE_FIRST_TIME

    @log_function_call(logger)
    def mark_first_run_complete(self) -> bool:
        """Mark first run as complete."""
        try:
            self.set_run_mode(self.RUN_MODE_NORMAL)
            self.settings.setValue("run_mode/first_run_date", str(Path.cwd()))
            logger.info("Marked first run as complete")
            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to mark first run complete: %s", str(e))
            return False

    @log_function_call(logger)
    def get_storage_location(self) -> str:
        """Get configured storage location."""
        try:
            location = self.settings.value("storage/location", "")

            if not location:
                # Use default location
                location = str(self.path_manager.get_data_directory())
                self.set_storage_location(location)

            logger.info("Storage location: %s", location)
            return location

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to get storage location: %s", str(e))
            return str(self.path_manager.get_data_directory())

    @log_function_call(logger)
    def set_storage_location(self, location: str) -> bool:
        """Set storage location."""
        try:
            path = Path(location)

            # Create directory if it doesn't exist
            path.mkdir(parents=True, exist_ok=True)

            # Verify it's writable
            test_file = path / ".write_test"
            test_file.touch()
            test_file.unlink()

            self.settings.setValue("storage/location", str(path))
            logger.info("Set storage location: %s", location)
            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to set storage location: %s", str(e))
            return False

    @log_function_call(logger)
    def get_database_path(self) -> str:
        """Get database file path."""
        try:
            storage_location = self.get_storage_location()
            db_path = str(Path(storage_location) / "3dmm.db")
            logger.info("Database path: %s", db_path)
            return db_path

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to get database path: %s", str(e))
            return str(self.path_manager.get_data_directory() / "3dmm.db")

    @log_function_call(logger)
    def get_projects_directory(self) -> str:
        """Get projects directory path."""
        try:
            storage_location = self.get_storage_location()
            projects_dir = str(Path(storage_location) / "projects")
            Path(projects_dir).mkdir(parents=True, exist_ok=True)
            return projects_dir

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to get projects directory: %s", str(e))
            return str(self.path_manager.get_data_dir() / "projects")

    @log_function_call(logger)
    def get_imports_directory(self) -> str:
        """Get imports directory path."""
        try:
            storage_location = self.get_storage_location()
            imports_dir = str(Path(storage_location) / "imports")
            Path(imports_dir).mkdir(parents=True, exist_ok=True)
            return imports_dir

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to get imports directory: %s", str(e))
            return str(self.path_manager.get_data_directory() / "imports")

    def get_preference(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get preference value."""
        try:
            return self.settings.value(f"preferences/{key}", default)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to get preference: %s", str(e))
            return default

    def set_preference(self, key: str, value: str) -> bool:
        """Set preference value."""
        try:
            self.settings.setValue(f"preferences/{key}", value)
            return True
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to set preference: %s", str(e))
            return False

    def get_all_preferences(self) -> dict:
        """Get all preferences."""
        try:
            self.settings.beginGroup("preferences")
            prefs = {key: self.settings.value(key) for key in self.settings.childKeys()}
            self.settings.endGroup()
            return prefs
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to get preferences: %s", str(e))
            return {}
