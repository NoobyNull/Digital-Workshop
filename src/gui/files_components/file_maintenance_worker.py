"""
Files tab for preferences dialog.

Provides UI for managing root folders used by the file browser.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, QDir, QThread
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QCheckBox, QLineEdit, QFileDialog, QMessageBox,
    QGroupBox, QInputDialog, QFrame, QSizePolicy, QProgressBar, QComboBox
)

from src.core.logging_config import get_logger
from src.core.root_folder_manager import RootFolderManager, RootFolder
from src.gui.theme import SPACING_4, SPACING_8, SPACING_12, SPACING_16



class FileMaintenanceWorker(QThread):
    """Worker thread for file maintenance operations."""

    progress = Signal(int, int, str)  # current, total, message
    finished = Signal(dict)  # result dict
    error = Signal(str)  # error message

    def __init__(self, operation: str):
        super().__init__()
        self.operation = operation
        self.logger = get_logger(__name__)
        self._stop_requested = False

    def run(self) -> None:
        """Execute the maintenance operation."""
        try:
            from src.core.database_manager import get_database_manager
            from src.utils.file_hash import calculate_file_hash
            from src.gui.batch_screenshot_worker import BatchScreenshotWorker
            from src.gui.material_manager import MaterialManager

            db_manager = get_database_manager()
            result = {
                "processed": 0,
                "updated": 0,
                "errors": 0
            }

            if self.operation == "recalculate_hashes":
                result = self._recalculate_hashes(db_manager, calculate_file_hash)
            elif self.operation == "match_files":
                result = self._match_files(db_manager, calculate_file_hash)
            elif self.operation == "regenerate_thumbnails":
                result = self._regenerate_thumbnails(db_manager)
            elif self.operation == "full_maintenance":
                result = self._recalculate_hashes(db_manager, calculate_file_hash)
                if not self._stop_requested:
                    result2 = self._match_files(db_manager, calculate_file_hash)
                    result["processed"] += result2["processed"]
                    result["updated"] += result2["updated"]
                    result["errors"] += result2["errors"]
                if not self._stop_requested:
                    result3 = self._regenerate_thumbnails(db_manager)
                    result["processed"] += result3["processed"]
                    result["updated"] += result3["updated"]
                    result["errors"] += result3["errors"]

            if not self._stop_requested:
                self.finished.emit(result)

        except Exception as e:
            self.logger.error(f"Maintenance operation failed: {e}", exc_info=True)
            self.error.emit(f"Maintenance operation failed: {str(e)}")

    def _recalculate_hashes(self, db_manager, calculate_file_hash) -> dict:
        """Recalculate file hashes for all models."""
        result = {"processed": 0, "updated": 0, "errors": 0}

        try:
            models = db_manager.get_all_models()
            total = len(models)

            for idx, model in enumerate(models):
                if self._stop_requested:
                    break

                model_id = model.get('id')
                file_path = model.get('file_path')

                self.progress.emit(idx + 1, total, f"Hashing model {model_id}")

                try:
                    if not Path(file_path).exists():
                        self.logger.warning(f"File not found: {file_path}")
                        result["errors"] += 1
                        continue

                    file_hash = calculate_file_hash(file_path)
                    if file_hash:
                        db_manager.update_file_hash(model_id, file_hash)
                        result["updated"] += 1
                    else:
                        result["errors"] += 1

                except Exception as e:
                    self.logger.error(f"Error hashing model {model_id}: {e}")
                    result["errors"] += 1

                result["processed"] += 1

        except Exception as e:
            self.logger.error(f"Recalculate hashes failed: {e}")
            raise

        return result

    def _match_files(self, db_manager, calculate_file_hash) -> dict:
        """Match files to models by recalculating hashes."""
        result = {"processed": 0, "updated": 0, "errors": 0}

        try:
            models = db_manager.get_all_models()
            total = len(models)

            for idx, model in enumerate(models):
                if self._stop_requested:
                    break

                model_id = model.get('id')
                file_path = model.get('file_path')
                current_hash = model.get('file_hash')

                self.progress.emit(idx + 1, total, f"Matching model {model_id}")

                try:
                    if not Path(file_path).exists():
                        self.logger.warning(f"File not found: {file_path}")
                        result["errors"] += 1
                        continue

                    file_hash = calculate_file_hash(file_path)
                    if file_hash and file_hash != current_hash:
                        db_manager.update_file_hash(model_id, file_hash)
                        result["updated"] += 1

                except Exception as e:
                    self.logger.error(f"Error matching model {model_id}: {e}")
                    result["errors"] += 1

                result["processed"] += 1

        except Exception as e:
            self.logger.error(f"Match files failed: {e}")
            raise

        return result

    def _regenerate_thumbnails(self, db_manager) -> dict:
        """Regenerate thumbnails for all models."""
        result = {"processed": 0, "updated": 0, "errors": 0}

        try:
            from src.gui.screenshot_generator import ScreenshotGenerator
            from src.gui.material_manager import MaterialManager
            from src.core.application_config import ApplicationConfig

            models = db_manager.get_all_models()
            total = len(models)

            # Load thumbnail settings
            config = ApplicationConfig.get_default()
            bg_image = config.thumbnail_bg_image
            material = config.thumbnail_material

            screenshot_gen = ScreenshotGenerator(
                width=128,
                height=128,
                background_image=bg_image,
                material_name=material
            )
            material_manager = MaterialManager()

            for idx, model in enumerate(models):
                if self._stop_requested:
                    break

                model_id = model.get('id')
                file_path = model.get('file_path')
                file_hash = model.get('file_hash')

                self.progress.emit(idx + 1, total, f"Generating thumbnail {model_id}")

                try:
                    if not Path(file_path).exists():
                        self.logger.warning(f"File not found: {file_path}")
                        result["errors"] += 1
                        continue

                    # Generate thumbnail
                    cache_dir = Path.home() / ".3dmm" / "thumbnails"
                    cache_dir.mkdir(parents=True, exist_ok=True)

                    if file_hash:
                        output_path = str(cache_dir / f"{file_hash}_128x128.png")
                    else:
                        output_path = str(cache_dir / f"model_{model_id}.png")

                    screenshot_path = screenshot_gen.capture_model_screenshot(
                        model_path=file_path,
                        output_path=output_path,
                        material_manager=material_manager,
                        material_name=None
                    )

                    if screenshot_path:
                        db_manager.update_model_thumbnail(model_id, screenshot_path)
                        result["updated"] += 1
                    else:
                        result["errors"] += 1

                except Exception as e:
                    self.logger.error(f"Error generating thumbnail {model_id}: {e}")
                    result["errors"] += 1

                result["processed"] += 1

        except Exception as e:
            self.logger.error(f"Regenerate thumbnails failed: {e}")
            raise

        return result

    def stop(self) -> None:
        """Request the worker to stop."""
        self._stop_requested = True
