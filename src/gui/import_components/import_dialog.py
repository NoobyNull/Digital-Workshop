"""
Import Dialog for 3D Model Import Process.
Provides a comprehensive user interface for importing 3D models with:
- File/directory selection with drag-and-drop support
- File management preference selection (keep organized vs leave in place)
- Multi-stage progress tracking (hashing, copying, thumbnails, analysis)
- Real-time progress updates with detailed stage information
- Cancellation support for long operations
- Import results summary with statistics
- Error display with recovery options
Example:
    >>> from src.gui.import_components import ImportDialog
    >>> dialog = ImportDialog()
    >>> if dialog.exec() == QDialog.Accepted:
    ...     print(f"Imported {dialog.get_import_result().processed_files} files")
"""

import time
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from enum import Enum
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QGroupBox,
    QRadioButton,
    QComboBox,
    QSpinBox,
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QSplitter,
    QCheckBox,
    QProgressDialog,
    QGridLayout,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QTimer, QSize, QSettings
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont
from src.core.logging_config import get_logger
from src.core.application_config import ApplicationConfig
from src.core.services.library_settings import LibraryMode, LibrarySettings
from src.core.services.import_settings import ImportSettings
from src.core.root_folder_manager import RootFolderManager
from src.core.import_file_manager import (
    ImportFileManager,
    FileManagementMode,
    DuplicateAction,
    ImportResult,
    ImportFileInfo,
    ImportSession,
)
from src.core.import_coordinator import ImportCoordinator
from src.gui.services.ai_description_service import AIDescriptionService
from src.gui.thumbnail_generation_coordinator import ThumbnailGenerationCoordinator
from src.gui.workers.folder_scan_worker import FolderScanWorker
from src.gui.background_tasks.import_background_monitor import ImportBackgroundMonitor
from src.gui.import_components.import_workers import (
    ImportJobConfig,
    ImportWorker,
    PipelineImportWorker,
)
from src.gui.import_components.import_dialog_controller import ImportDialogController
from src.gui.workers.base_worker import BaseWorker

# Import modular pipeline
from src.core.import_pipeline import (
    create_pipeline,
    ImportTask,
    PipelineProgress,
    PipelineResult,
)
from src.core.database_manager import get_database_manager
from src.core.thumbnail_generator import ThumbnailGenerator


class ImportStage(Enum):
    """Import process stages."""

    IDLE = "idle"
    FILE_SELECTION = "file_selection"
    VALIDATION = "validation"
    HASHING = "hashing"
    COPYING = "copying"
    THUMBNAILS = "thumbnails"
    ANALYSIS = "analysis"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ImportDialog(QDialog):
    """
    Main import dialog for 3D model import process.
    Provides a comprehensive interface for importing 3D models with:
    - File/directory selection with drag-and-drop
    - File management preference selection
    - Multi-stage progress tracking
    - Real-time progress updates
    - Cancellation support
    - Import results summary
    Example:
        >>> dialog = ImportDialog(parent=main_window)
        >>> if dialog.exec() == QDialog.Accepted:
        ...     result = dialog.get_import_result()
        ...     print(f"Successfully imported {result.processed_files} files")
    """

    def __init__(self, parent=None, root_folder_manager=None) -> None:
        """Initialize the import dialog.
        Args:
            parent: Parent widget
            root_folder_manager: Optional RootFolderManager instance
        """
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.controller = ImportDialogController()
        self.root_folder_manager = root_folder_manager
        # State
        self.current_stage = ImportStage.IDLE
        self.import_result: Optional[ImportResult] = None
        self.import_worker: Optional[PipelineImportWorker] = None
        self.selected_files: List[str] = []
        self.start_time: Optional[float] = None
        self.folder_scan_worker: Optional[FolderScanWorker] = None
        self.folder_scan_dialog = None
        self._managed_mode_confirmed = False
        self._background_monitor = None
        self._background_mode = False
        self.pending_label = QLabel("")
        self.pending_label.setVisible(False)
        self.pending_button = QPushButton("Import Pending")
        self.pending_button.setVisible(False)
        self._default_splitter_sizes = [320, 170, 320]
        self._settings = QSettings()
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self._update_time_elapsed)
        self._last_plain_log_message: Optional[str] = None
        self._file_start_times: dict[str, float] = {}
        self._worker_rows: List[Dict[str, Any]] = []
        self._worker_assignments: Dict[str, int] = {}
        self._worker_capacity: int = 0
        self.import_settings = ImportSettings()
        self._concurrency_mode: str = self.import_settings.get_mode()
        # Setup UI
        self._setup_ui()
        self._connect_signals()
        self._apply_concurrency_mode_ui(self._concurrency_mode)
        self._apply_library_preferences()
        self._update_pending_label()
        # Enable drag and drop
        self.setAcceptDrops(True)
        self.logger.info("ImportDialog initialized")

    def _apply_concurrency_mode_ui(self, mode: str) -> None:
        """Sync the concurrency combo to the given mode."""
        mode = mode if mode in ("serial", "concurrent") else "serial"
        self._concurrency_mode = mode
        if hasattr(self, "concurrency_combo"):
            idx = self.concurrency_combo.findData(mode)
            if idx >= 0:
                self.concurrency_combo.setCurrentIndex(idx)
        if hasattr(self, "prep_workers_spin"):
            self.prep_workers_spin.setEnabled(mode == "concurrent")

    def _on_concurrency_changed(self, mode: str) -> None:
        """Persist user-selected concurrency mode."""
        mode = mode if mode in ("serial", "concurrent") else "serial"
        self._concurrency_mode = mode
        try:
            self.import_settings.set_mode(mode)
        except Exception:
            self.logger.debug("Failed to persist concurrency mode")
        self._apply_concurrency_mode_ui(mode)

    def _on_prep_workers_changed(self, value: int) -> None:
        """Persist the desired prep worker count."""
        try:
            data = self.import_settings.get_concurrency()
            self.import_settings.set_concurrency(
                value, data.thumbnail_workers, data.queue_limit
            )
        except Exception:
            self.logger.debug("Failed to persist prep worker count")

    def _persist_prep_worker_setting(self) -> None:
        """Persist current prep worker value without altering other settings."""
        try:
            data = self.import_settings.get_concurrency()
            self.import_settings.set_concurrency(
                self.prep_workers_spin.value(),
                data.thumbnail_workers,
                data.queue_limit,
            )
        except Exception:
            self.logger.debug("Failed to persist prep worker value during start")

    def _apply_library_preferences(self) -> None:
        """Initialize mode/root directory from global library settings.
        This keeps the import dialog aligned with the first-launch
        library configuration (leave-in-place vs consolidated).
        """
        try:
            settings = LibrarySettings()
            mode = settings.get_mode()
            base_root = settings.get_base_root()
        except Exception as exc:  # pragma: no cover - defensive logging
            self.logger.warning("Failed to read library settings: %s", exc)
            return
        if mode == LibraryMode.CONSOLIDATED:
            # Consolidated mode: keep files organized under the configured root
            try:
                projects_root = base_root or settings.ensure_projects_root()
            except OSError as exc:
                self.logger.error("Failed to prepare Projects folder: %s", exc)
                projects_root = base_root
            self.keep_organized_radio.setChecked(True)
            self.leave_in_place_radio.setChecked(False)
            self.root_dir_path.setText(
                str(projects_root) if projects_root else "Not configured"
            )
            self.root_dir_button.setText("Change Folder...")
            self._managed_mode_confirmed = True
        else:
            # Leave-in-place mode (or missing root): no managed root required
            self.keep_organized_radio.setChecked(False)
            self.leave_in_place_radio.setChecked(True)
            self.root_dir_path.setText("Not selected")
            self.root_dir_button.setText("Browse...")
        self._update_import_button_state()

    # ----- Worker progress helpers -----
    def _init_worker_rows(self, count: int) -> None:
        """Create/reset worker progress rows."""
        count = max(1, int(count))
        self._worker_capacity = count
        self._worker_assignments.clear()
        # Clear existing widgets (grid)
        while self.workers_layout.count():
            item = self.workers_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self._worker_rows = []
        columns = 2 if count > 1 else 1
        for idx in range(count):
            row_widget = QGroupBox(f"Worker {idx + 1}")
            row_widget.setMinimumSize(180, 180)
            row_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            row_layout = QVBoxLayout(row_widget)
            row_layout.setSpacing(6)
            title = QLabel("Idle")
            title.setStyleSheet("font-weight: bold;")
            row_layout.addWidget(title)
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setTextVisible(True)
            bar.setFormat("Idle")
            bar.setMinimumHeight(24)
            row_layout.addWidget(bar)
            stage = QLabel("Waiting")
            stage.setStyleSheet("color: #666;")
            stage.setWordWrap(True)
            row_layout.addWidget(stage)
            row_layout.addStretch()
            r = idx // columns
            c = idx % columns
            self.workers_layout.addWidget(row_widget, r, c)
            self._worker_rows.append(
                {"title": title, "bar": bar, "stage": stage, "file": None}
            )
        self.workers_group.setVisible(True)

    def _describe_worker_stage(self, message: str) -> str:
        """Normalize a message into a compact stage label."""
        msg = (message or "").lower()
        if "hash" in msg:
            return "Hashing"
        if "copy" in msg or "move" in msg:
            return "Copy/Moving"
        if "thumbnail" in msg or "generate" in msg:
            return "Generating"
        if "tag" in msg or "ai" in msg:
            return "AI tagging"
        if "db" in msg or "database" in msg or "persist" in msg:
            return "Updating DB"
        if "load" in msg or "processing" in msg:
            return "Loading"
        return message or "Working"

    def _assign_worker_slot(self, filename: str) -> int:
        """Assign a file to an available worker slot, reusing when needed."""
        if filename in self._worker_assignments:
            return self._worker_assignments[filename]
        # Find an idle slot
        for idx, row in enumerate(self._worker_rows):
            if row["file"] is None:
                row["file"] = filename
                self._worker_assignments[filename] = idx
                return idx
        # Reuse oldest slot if none idle
        idx = len(self._worker_assignments) % self._worker_capacity
        for existing, slot in list(self._worker_assignments.items()):
            if slot == idx:
                self._worker_assignments.pop(existing, None)
                break
        self._worker_assignments[filename] = idx
        self._worker_rows[idx]["file"] = filename
        return idx

    def _release_worker_slot(self, filename: str) -> None:
        """Mark a worker slot as idle."""
        idx = self._worker_assignments.pop(filename, None)
        if idx is None or idx >= len(self._worker_rows):
            return
        row = self._worker_rows[idx]
        row["file"] = None
        row["title"].setText(f"Worker {idx + 1}: Idle")
        row["bar"].setValue(0)
        row["bar"].setFormat("Idle")
        row["stage"].setText("Waiting")

    def _update_worker_slot(self, filename: str, percent: int, message: str) -> None:
        """Update worker UI for a given file."""
        if not hasattr(self, "workers_group"):
            return
        slot = self._assign_worker_slot(filename)
        if slot >= len(self._worker_rows):
            return
        row = self._worker_rows[slot]
        stage_text = self._describe_worker_stage(message)
        row["title"].setText(f"Worker {slot + 1}: {filename}")
        row["bar"].setValue(max(0, min(100, percent)))
        row["bar"].setFormat(f"{filename} - {stage_text} (%p%)")
        row["stage"].setText(stage_text)
        if (
            percent >= 100
            or "completed" in message.lower()
            or "failed" in message.lower()
        ):
            self._release_worker_slot(filename)

    def _setup_ui(self) -> None:
        """Setup the dialog user interface."""
        self.setWindowTitle("Import 3D Models")
        # Default to the attached reference image height (820x768) so the progress area is visible.
        self.setMinimumSize(820, 768)
        self.resize(980, 768)
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        # Title and description
        title_label = QLabel("Import 3D Models")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        desc_label = QLabel(
            "Select 3D model files to import into your library. "
            "You can drag and drop files or folders, or use the browse button."
        )
        desc_label.setWordWrap(True)
        main_layout.addWidget(desc_label)
        # Create splitter for file list and options
        self.splitter = QSplitter(Qt.Vertical)
        # === File Selection Section ===
        self.file_section = self._create_file_selection_section()
        self.splitter.addWidget(self.file_section)
        # === Options Section ===
        self.options_section = self._create_options_section()
        self.splitter.addWidget(self.options_section)
        # === Progress Section ===
        progress_section = self._create_progress_section()
        self.splitter.addWidget(progress_section)
        # Set splitter sizes
        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setStretchFactor(2, 3)
        self.splitter.setSizes(self._default_splitter_sizes)
        main_layout.addWidget(self.splitter, 1)
        # Timer for elapsed time display (runs during imports)
        if not hasattr(self, "time_timer"):
            self.time_timer = QTimer(self)
            self.time_timer.timeout.connect(self._update_time_elapsed)
        # === Status bar ===
        self.status_label = QLabel("Ready to import")
        main_layout.addWidget(self.status_label)
        # === Buttons ===
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.import_button = QPushButton("Start Import")
        self.import_button.setMinimumWidth(120)
        self.import_button.setEnabled(False)
        button_layout.addWidget(self.import_button)
        self.background_button = QPushButton("Run in Background")
        self.background_button.setEnabled(False)
        self.background_button.setToolTip(
            "Start an import before sending it to the background."
        )
        button_layout.addWidget(self.background_button)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumWidth(120)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

    def _create_file_selection_section(self) -> QGroupBox:
        """Create the file selection section."""
        group = QGroupBox("Files to Import")
        layout = QVBoxLayout(group)
        # File list
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.file_list.setMinimumHeight(150)
        layout.addWidget(self.file_list)
        # Buttons
        button_layout = QHBoxLayout()
        self.add_files_button = QPushButton("Add Files...")
        self.add_files_button.setToolTip("Select individual model files to import")
        button_layout.addWidget(self.add_files_button)
        self.add_folder_button = QPushButton("Add Folder...")
        self.add_folder_button.setToolTip("Select a folder containing model files")
        button_layout.addWidget(self.add_folder_button)
        self.import_from_url_button = QPushButton("Import from URL...")
        self.import_from_url_button.setToolTip(
            "Download and import a model from the web"
        )
        button_layout.addWidget(self.import_from_url_button)
        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.setEnabled(False)
        button_layout.addWidget(self.remove_button)
        self.clear_button = QPushButton("Clear All")
        self.clear_button.setEnabled(False)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        # Drop zone hint
        hint_label = QLabel("💡 Tip: You can drag and drop files or folders here")
        layout.addWidget(hint_label)
        return group

    def _create_options_section(self) -> QGroupBox:
        """Create the import options section."""
        group = QGroupBox("Import Options")
        layout = QVBoxLayout(group)
        # File Management Mode
        mode_label = QLabel("File Management:")
        layout.addWidget(mode_label)
        self.keep_organized_radio = QRadioButton("Keep Organized")
        self.keep_organized_radio.setToolTip(
            "Copy files to managed directory with organized folder structure"
        )
        self.keep_organized_radio.setChecked(True)
        layout.addWidget(self.keep_organized_radio)
        # Root directory selection (for keep organized mode) - indented under Keep Organized
        root_layout = QHBoxLayout()
        root_layout.addSpacing(20)
        self.root_dir_label = QLabel("Root Directory:")
        root_layout.addWidget(self.root_dir_label)
        self.root_dir_path = QLabel("Not selected")
        root_layout.addWidget(self.root_dir_path, 1)
        self.root_dir_button = QPushButton("Browse...")
        self.root_dir_button.setMaximumWidth(100)
        root_layout.addWidget(self.root_dir_button)
        layout.addLayout(root_layout)
        self.leave_in_place_radio = QRadioButton("Leave in Place")
        self.leave_in_place_radio.setToolTip(
            "Track files in their original locations without copying"
        )
        layout.addWidget(self.leave_in_place_radio)
        # Additional options
        layout.addSpacing(10)
        options_label = QLabel("Processing Options:")
        layout.addWidget(options_label)
        self.generate_thumbnails_check = QCheckBox("Generate Thumbnails")
        self.generate_thumbnails_check.setChecked(True)
        self.generate_thumbnails_check.setToolTip(
            "Generate preview thumbnails during import"
        )
        layout.addWidget(self.generate_thumbnails_check)
        self.run_analysis_check = QCheckBox("Run Background Analysis")
        self.run_analysis_check.setChecked(True)
        self.run_analysis_check.setToolTip(
            "Analyze model geometry in the background after import"
        )
        layout.addWidget(self.run_analysis_check)
        layout.addSpacing(8)
        concurrency_label = QLabel("Execution Mode:")
        layout.addWidget(concurrency_label)
        self.concurrency_combo = QComboBox()
        self.concurrency_combo.addItem("Serial (safer for drag/drop)", "serial")
        self.concurrency_combo.addItem("Concurrent (faster for folders)", "concurrent")
        layout.addWidget(self.concurrency_combo)
        # User-adjustable parallel workers (applies when mode = concurrent)
        concurrency = self.import_settings.get_concurrency()
        self.prep_workers_spin = QSpinBox()
        self.prep_workers_spin.setRange(1, 16)
        self.prep_workers_spin.setValue(concurrency.prep_workers)
        self.prep_workers_spin.setSuffix(" workers")
        self.prep_workers_spin.setToolTip(
            "How many files to process in parallel (only used in Concurrent mode)."
        )
        layout.addWidget(self.prep_workers_spin)
        # User-adjustable batch size to control queue/backlog visibility
        default_cap = int(
            self._settings.value(
                "import/batch_size",
                getattr(ImportFileManager, "MAX_IMPORT_FILES", 500),
                type=int,
            )
            or 500
        )
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(10, 2000)
        self.batch_size_spin.setValue(max(10, min(2000, default_cap)))
        self.batch_size_spin.setSuffix(" files per batch")
        self.batch_size_spin.setToolTip(
            "How many files to process before queuing the remainder as pending batches."
        )
        layout.addWidget(self.batch_size_spin)
        self.enable_ai_tagging_check = QCheckBox(
            "Enable AI auto-tagging after thumbnails"
        )
        self.enable_ai_tagging_check.setToolTip(
            "Submit generated thumbnails to the AI description service to suggest tags/keywords."
        )
        settings = QSettings()
        self.enable_ai_tagging_check.setChecked(
            settings.value("ai/auto_tag_import", False, type=bool)
        )
        # Keep UI changes reflected in preferences
        self.enable_ai_tagging_check.toggled.connect(
            lambda checked: settings.setValue("ai/auto_tag_import", bool(checked))
        )
        self.batch_size_spin.valueChanged.connect(
            lambda value: settings.setValue("import/batch_size", int(value))
        )
        layout.addWidget(self.enable_ai_tagging_check)
        warning = QLabel(
            '<span style="color:#c00; font-weight:bold;">Note:</span> AI calls may incur charges from your '
            "provider. For cost control, prefer a self-hosted model such as Ollama."
        )
        warning.setWordWrap(True)
        layout.addWidget(warning)
        return group

    def _create_progress_section(self) -> QGroupBox:
        """Create the progress tracking section."""
        group = QGroupBox("Import Progress")
        layout = QVBoxLayout(group)
        # Overall progress
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("Overall:"))
        self.overall_progress_bar = QProgressBar()
        self.overall_progress_bar.setRange(0, 100)
        self.overall_progress_bar.setValue(0)
        self.overall_progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.overall_progress_bar, 1)
        self.progress_label = QLabel("0 / 0")
        progress_layout.addWidget(self.progress_label)
        layout.addLayout(progress_layout)
        # Worker detail (one row per concurrent worker)
        self.workers_group = QGroupBox("Concurrent Workers")
        self.workers_layout = QGridLayout(self.workers_group)
        self.workers_layout.setSpacing(12)
        self.workers_group.setVisible(False)
        layout.addWidget(self.workers_group)
        # Current file progress
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Current:"))
        self.file_progress_bar = QProgressBar()
        self.file_progress_bar.setRange(0, 100)
        self.file_progress_bar.setValue(0)
        self.file_progress_bar.setTextVisible(True)
        file_layout.addWidget(self.file_progress_bar, 1)
        layout.addLayout(file_layout)
        # Pending batch status
        pending_layout = QHBoxLayout()
        pending_layout.addWidget(self.pending_label, 1)
        self.pending_button.setMaximumWidth(150)
        pending_layout.addWidget(self.pending_button)
        layout.addLayout(pending_layout)
        # Thumbnail generation status
        thumbnail_layout = QHBoxLayout()
        thumbnail_layout.addWidget(QLabel("Thumbnails:"))
        self.thumbnail_status_label = QLabel("Waiting...")
        thumbnail_layout.addWidget(self.thumbnail_status_label, 1)
        self.thumbnail_progress_bar = QProgressBar()
        self.thumbnail_progress_bar.setRange(0, 100)
        self.thumbnail_progress_bar.setValue(0)
        self.thumbnail_progress_bar.setTextVisible(True)
        self.thumbnail_progress_bar.setMaximumWidth(150)
        thumbnail_layout.addWidget(self.thumbnail_progress_bar)
        layout.addLayout(thumbnail_layout)
        # Stage indicator
        stage_layout = QHBoxLayout()
        stage_layout.addWidget(QLabel("Stage:"))
        self.stage_label = QLabel("Idle")
        stage_layout.addWidget(self.stage_label, 1)
        self.time_label = QLabel("")
        self.time_label.setAlignment(Qt.AlignRight)
        stage_layout.addWidget(self.time_label)
        layout.addLayout(stage_layout)
        # Status/Error display
        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        self.progress_text.setMinimumHeight(200)
        self.progress_text.setPlaceholderText("Import progress will be shown here...")
        layout.addWidget(self.progress_text)
        # Initially hide progress section
        group.setVisible(False)
        self.progress_section = group
        return group

    def _expand_progress_section(self) -> None:
        """Ensure the progress pane is visible with a reasonable size."""
        if not hasattr(self, "splitter"):
            return
        sizes = self.splitter.sizes()
        if len(sizes) < 3:
            self.splitter.setSizes([320, 180, 240])
            return
        # If the progress panel was hidden, its size can collapse to 0.
        # Guarantee it gets a sensible share of space when shown.
        progress_min = 260
        if sizes[2] < progress_min:
            new_sizes = [
                max(220, sizes[0]),
                max(170, sizes[1]),
                progress_min,
            ]
            self.splitter.setSizes(new_sizes)

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        self.add_files_button.clicked.connect(self._on_add_files)
        self.add_folder_button.clicked.connect(self._on_add_folder)
        self.import_from_url_button.clicked.connect(self._on_import_from_url)
        self.remove_button.clicked.connect(self._on_remove_selected)
        self.clear_button.clicked.connect(self._on_clear_all)
        self.file_list.itemSelectionChanged.connect(self._on_file_selection_changed)
        self.keep_organized_radio.toggled.connect(self._on_mode_changed)
        self.root_dir_button.clicked.connect(self._on_select_root_directory)
        self.import_button.clicked.connect(self._on_start_import)
        self.pending_button.clicked.connect(self._start_pending_import)
        self.background_button.clicked.connect(self._send_to_background)
        self.cancel_button.clicked.connect(self._on_cancel)
        self.concurrency_combo.currentIndexChanged.connect(
            lambda _: self._on_concurrency_changed(self.concurrency_combo.currentData())
        )
        if hasattr(self, "batch_size_spin"):
            self.batch_size_spin.valueChanged.connect(self._on_batch_size_changed)
            self._on_batch_size_changed(self.batch_size_spin.value())

    def _collapse_to_progress_only(self) -> None:
        """Hide selection/options panes and give space to progress during import."""
        if hasattr(self, "file_section"):
            self.file_section.setVisible(False)
        if hasattr(self, "options_section"):
            self.options_section.setVisible(False)
        self.progress_section.setVisible(True)
        # Bias splitter toward progress area
        try:
            total_height = max(1, sum(self.splitter.sizes()))
            self.splitter.setSizes([1, 1, max(240, total_height - 2)])
        except Exception:
            self.splitter.setSizes([0, 0, 1])

    def _restore_full_layout(self) -> None:
        """Restore default splitter layout after an import ends."""
        if hasattr(self, "file_section"):
            self.file_section.setVisible(True)
        if hasattr(self, "options_section"):
            self.options_section.setVisible(True)
        self.progress_section.setVisible(False)
        try:
            self.splitter.setSizes(self._default_splitter_sizes)
        except Exception:
            pass
        if hasattr(self, "prep_workers_spin"):
            self.prep_workers_spin.valueChanged.connect(self._on_prep_workers_changed)

    def _on_add_files(self) -> None:
        """Handle add files button click."""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter(
            "3D Model Files (*.stl *.obj *.step *.stp *.3mf *.ply);;All Files (*.*)"
        )
        if file_dialog.exec():
            files = file_dialog.selectedFiles()
            self._add_files(files)
            self._apply_concurrency_mode_ui("serial")

    def _on_add_folder(self) -> None:
        """Handle add folder button click."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder Containing Model Files"
        )
        if folder:
            self._start_folder_scan(folder)

    def _on_import_from_url(self) -> None:
        """Open the URL import dialog and close when it finishes."""
        from src.gui.import_components.url_import_dialog import UrlImportDialog

        dialog = UrlImportDialog(self)
        if dialog.exec():
            result = dialog.get_import_result()
            if result and result.import_result:
                self.import_result = result.import_result
                self.accept()

    def _start_folder_scan(self, folder: str) -> None:
        """Start background scan for model files in the selected folder."""
        if self.folder_scan_worker is not None and self.folder_scan_worker.isRunning():
            self.logger.info("Folder scan already in progress")
            return
        model_extensions = [".stl", ".obj", ".step", ".stp", ".3mf", ".ply"]
        self.folder_scan_worker = FolderScanWorker(folder, model_extensions)
        self.folder_scan_worker.progress_updated.connect(self._on_folder_scan_progress)
        self.folder_scan_worker.scan_completed.connect(self._on_folder_scan_completed)
        self.folder_scan_worker.error_occurred.connect(self._on_folder_scan_error)
        self.folder_scan_worker.cancelled.connect(self._on_folder_scan_cancelled)
        self.folder_scan_dialog = QProgressDialog(
            "Scanning folder for 3D model files...",
            "Cancel",
            0,
            0,
            self,
        )
        self.folder_scan_dialog.setWindowModality(Qt.WindowModal)
        self.folder_scan_dialog.setMinimumDuration(0)
        self.folder_scan_dialog.setAutoClose(False)
        self.folder_scan_dialog.setAutoReset(False)
        self.folder_scan_dialog.canceled.connect(self._on_folder_scan_dialog_canceled)
        self.folder_scan_dialog.show()
        self.folder_scan_worker.start()

    def _on_folder_scan_progress(self, count: int, current_path: str) -> None:
        """Update progress dialog during folder scan."""
        if self.folder_scan_dialog is None:
            return
        if current_path:
            self.folder_scan_dialog.setLabelText(
                f"Scanning folder for 3D model files...\n"
                f"Found {count} files so far in:\n{current_path}"
            )
        else:
            self.folder_scan_dialog.setLabelText(
                f"Scanning folder for 3D model files...\nFound {count} files so far..."
            )

    def _on_folder_scan_completed(self, files: List[str]) -> None:
        """Handle completion of folder scan."""
        if self.folder_scan_dialog is not None:
            try:
                self.folder_scan_dialog.canceled.disconnect(
                    self._on_folder_scan_dialog_canceled
                )
            except Exception:
                pass
            self.folder_scan_dialog.close()
            self.folder_scan_dialog = None
        self.folder_scan_worker = None
        if files:
            self._add_files(files)
            self._apply_concurrency_mode_ui("concurrent")
            self._log_message(f"Found {len(files)} model files in folder")
        else:
            QMessageBox.warning(
                self,
                "No Files Found",
                "No 3D model files found in the selected folder.",
            )

    def _on_folder_scan_error(self, error: str) -> None:
        """Handle errors during folder scan."""
        if self.folder_scan_dialog is not None:
            self.folder_scan_dialog.close()
            self.folder_scan_dialog = None
        self.folder_scan_worker = None
        QMessageBox.critical(
            self,
            "Folder Scan Error",
            f"Failed to scan folder for model files:\n{error}",
        )

    def _on_folder_scan_cancelled(self) -> None:
        """Handle cancellation of folder scan."""
        if self.folder_scan_dialog is not None:
            self.folder_scan_dialog.close()
            self.folder_scan_dialog = None
        self.folder_scan_worker = None
        self._log_message("Folder scan cancelled by user")

    def _on_folder_scan_dialog_canceled(self) -> None:
        """Handle cancel request from the progress dialog."""
        if self.folder_scan_worker is not None:
            self.folder_scan_worker.cancel()

    def _add_files(self, files: List[str]) -> None:
        """
        Add files to the import list.
        Collects all failures and shows a summary at the end instead of
        showing a dialog for each failed file.
        Args:
            files: List of file paths to add
        """
        added_count = 0
        failed_files = []
        for file_path in files:
            # Check if file already in list
            if file_path not in self.selected_files:
                try:
                    # Add to list widget
                    file_name = Path(file_path).name
                    file_size = Path(file_path).stat().st_size / (1024 * 1024)  # MB
                    self.selected_files.append(file_path)
                    item = QListWidgetItem(f"{file_name} ({file_size:.2f} MB)")
                    item.setData(Qt.UserRole, file_path)
                    item.setToolTip(file_path)
                    self.file_list.addItem(item)
                    added_count += 1
                except (
                    OSError,
                    IOError,
                    ValueError,
                    TypeError,
                    KeyError,
                    AttributeError,
                ) as exc:
                    # Collect failed files instead of showing dialog
                    failed_files.append((Path(file_path).name, str(exc)))
                    self.logger.warning("Failed to add file %s: %s", file_path, exc)
        if added_count > 0:
            self._update_import_button_state()
            self._log_message(f"Added {added_count} file(s)")
            self.status_label.setText(f"{len(self.selected_files)} file(s) selected")
        # Show summary of failures if any
        if failed_files:
            self._show_import_failures_summary(failed_files, added_count)

    def _show_import_failures_summary(
        self, failed_files: List[tuple], added_count: int
    ) -> None:
        """
        Show a summary dialog of all failed files instead of individual dialogs.
        Args:
            failed_files: List of (filename, error_reason) tuples
            added_count: Number of files successfully added
        """
        failure_count = len(failed_files)
        # Build failure list
        failure_list = "\n".join(
            f"  • {name}: {reason}"
            for name, reason in failed_files[:20]  # Show first 20
        )
        if failure_count > 20:
            failure_list += f"\n  ... and {failure_count - 20} more"
        # Build message
        message = (
            f"Import Summary:\n\n"
            f"✓ Successfully added: {added_count} file(s)\n"
            f"✗ Failed to add: {failure_count} file(s)\n\n"
            f"Failed files:\n{failure_list}"
        )
        # Log failures
        self._log_message(f"\n⚠️  {failure_count} file(s) failed to add:")
        for name, reason in failed_files:
            self._log_message(f"  • {name}: {reason}")
        # Show summary dialog
        QMessageBox.warning(self, "Import Summary - Some Files Failed", message)

    def _on_remove_selected(self) -> None:
        """Remove selected files from the list."""
        selected_items = self.file_list.selectedItems()
        for item in selected_items:
            file_path = item.data(Qt.UserRole)
            self.selected_files.remove(file_path)
            self.file_list.takeItem(self.file_list.row(item))
        self._update_import_button_state()
        self.status_label.setText(f"{len(self.selected_files)} file(s) selected")

    def _on_clear_all(self) -> None:
        """Clear all files from the list."""
        self.selected_files.clear()
        self.file_list.clear()
        self._update_import_button_state()
        self.status_label.setText("Ready to import")

    def _on_file_selection_changed(self) -> None:
        """Handle file selection change."""
        has_selection = len(self.file_list.selectedItems()) > 0
        self.remove_button.setEnabled(has_selection)

    def _on_mode_changed(self, checked: bool) -> None:
        """Handle file management mode change."""
        if not checked:
            return
        managed = self.keep_organized_radio.isChecked()
        self.root_dir_label.setEnabled(managed)
        self.root_dir_path.setEnabled(managed)
        self.root_dir_button.setEnabled(managed)
        settings = LibrarySettings()
        if managed:
            settings.set_mode(LibraryMode.CONSOLIDATED)
            try:
                projects_root = settings.ensure_projects_root()
            except OSError as exc:
                self.logger.error("Unable to use Projects folder: %s", exc)
                QMessageBox.critical(
                    self,
                    "Projects Folder Error",
                    f"Unable to use the managed Projects folder:\n\n{exc}",
                )
                self.keep_organized_radio.setChecked(False)
                self.leave_in_place_radio.setChecked(True)
                self.root_dir_label.setEnabled(False)
                self.root_dir_path.setEnabled(False)
                self.root_dir_button.setEnabled(False)
                self.root_dir_button.setText("Browse...")
                self.root_dir_path.setText("Not selected")
                self._update_import_button_state()
                return
            self.root_dir_path.setText(str(projects_root))
            self.root_dir_button.setText("Change Folder...")
            if not self._managed_mode_confirmed:
                if not self._confirm_managed_mode(str(projects_root)):
                    self._managed_mode_confirmed = False
                    self.keep_organized_radio.setChecked(False)
                    self.leave_in_place_radio.setChecked(True)
                    self.root_dir_button.setText("Browse...")
                    self.root_dir_path.setText("Not selected")
                    self.root_dir_label.setEnabled(False)
                    self.root_dir_path.setEnabled(False)
                    self.root_dir_button.setEnabled(False)
                    self._update_import_button_state()
                    return
                self._managed_mode_confirmed = True
        else:
            settings.set_mode(LibraryMode.LEAVE_IN_PLACE)
            self.root_dir_button.setText("Browse...")
            self.root_dir_path.setText("Not selected")
            self._managed_mode_confirmed = False
        manager = self.root_folder_manager or RootFolderManager.get_instance()
        if manager is not None:
            manager.reload_from_settings()
        self._update_import_button_state()

    def _on_select_root_directory(self) -> None:
        """Handle root directory selection."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Projects Folder",
            (
                self.root_dir_path.text()
                if self.root_dir_path.text() not in {"", "Not selected"}
                else str(LibrarySettings().get_default_projects_root())
            ),
        )
        if not folder:
            return
        selected = Path(folder)
        try:
            selected.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            QMessageBox.critical(
                self, "Projects Folder Error", f"Unable to use that folder:\n\n{exc}"
            )
            return
        settings = LibrarySettings()
        settings.set_mode(LibraryMode.CONSOLIDATED)
        settings.set_base_root(selected)
        self.root_dir_path.setText(str(selected))
        self.root_dir_button.setText("Change Folder...")
        self._managed_mode_confirmed = False
        if not self._confirm_managed_mode(str(selected)):
            self.keep_organized_radio.setChecked(False)
            self.leave_in_place_radio.setChecked(True)
            self.root_dir_button.setText("Browse...")
            self.root_dir_path.setText("Not selected")
            self._update_import_button_state()
            return
        manager = self.root_folder_manager or RootFolderManager.get_instance()
        if manager is not None:
            manager.reload_from_settings()
        self._update_import_button_state()

    def _confirm_managed_mode(self, target_path: str) -> bool:
        """Prompt user before enabling managed storage."""
        message = (
            "Digital Workshop will take ownership of organizing your imports.\n\n"
            f"All files brought in through this import dialog will be moved into:\n"
            f"{target_path}\n\n"
            "Any future imports will also be copied to this location. Continue?"
        )
        reply = QMessageBox.question(
            self,
            "Enable Managed Storage?",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return reply == QMessageBox.Yes

    def _update_import_button_state(self) -> None:
        """Update import button enabled state."""
        has_files = len(self.selected_files) > 0
        if self.keep_organized_radio.isChecked():
            has_root_dir = self.root_dir_path.text() != "Not selected"
            can_import = has_files and has_root_dir
        else:
            can_import = has_files
        self.import_button.setEnabled(
            can_import and self.current_stage == ImportStage.IDLE
        )
        self.clear_button.setEnabled(len(self.selected_files) > 0)

    def _update_pending_label(self) -> None:
        """Update the pending import batches label/button visibility."""
        try:
            batch_count = ImportCoordinator.pending_batch_count()
        except Exception as exc:
            self.logger.warning("Unable to read pending batches: %s", exc)
            batch_count = 0
        has_pending = batch_count > 0
        if has_pending:
            self.pending_label.setText(
                f"Pending imports: {batch_count} batch(es) queued"
            )
        else:
            self.pending_label.setText("")
        self.pending_label.setVisible(has_pending)
        self.pending_button.setVisible(has_pending)
        self.pending_button.setEnabled(has_pending)

    def _start_pending_import(self) -> None:
        """Start the next set of pending imports, if any."""
        if self.import_worker and self.import_worker.isRunning():
            QMessageBox.information(
                self,
                "Import Running",
                "Please wait for the current import to finish before starting pending batches.",
            )
            return
        try:
            batches = ImportCoordinator._load_pending_batches()
        except Exception as exc:
            self.logger.warning("Failed to load pending batches: %s", exc)
            batches = []
        if not batches:
            QMessageBox.information(
                self, "No Pending Imports", "There are no pending batches to import."
            )
            self._update_pending_label()
            return
        # Flatten so the standard start flow can re-slice and re-persist.
        files = [path for batch in batches for path in batch]
        remaining = batches[1:] if len(batches) > 1 else []
        ImportCoordinator._save_pending_batches(remaining)
        self._update_pending_label()
        # Replace the current selection with the pending batch contents.
        self.selected_files.clear()
        self.file_list.clear()
        self._add_files(files)
        self._on_start_import()

    def _on_start_import(self) -> None:
        """Start the import process."""
        # Validate settings
        if self.keep_organized_radio.isChecked():
            root_dir = self.root_dir_path.text()
            if root_dir == "Not selected":
                QMessageBox.warning(
                    self,
                    "Root Directory Required",
                    "Please select a root directory for organized storage mode.",
                )
                return
        # Confirm import
        file_count = len(self.selected_files)
        total_size = sum(Path(f).stat().st_size for f in self.selected_files) / (
            1024 * 1024
        )
        try:
            cap = self._get_batch_size()
        except Exception:
            cap = getattr(ImportFileManager, "MAX_IMPORT_FILES", 500)
        msg = (
            f"Import {file_count} file(s) ({total_size:.2f} MB)?\n\n"
            f"Mode: {'Keep Organized' if self.keep_organized_radio.isChecked() else 'Leave in Place'}\n"
        )
        if self.keep_organized_radio.isChecked():
            msg += f"Root Directory: {self.root_dir_path.text()}\n"
        msg += f"Generate Thumbnails: {'Yes' if self.generate_thumbnails_check.isChecked() else 'No'}\n"
        msg += f"Run Analysis: {'Yes' if self.run_analysis_check.isChecked() else 'No'}"
        if file_count > cap:
            msg += (
                f"\n\nNote: Imports run in batches of {cap}. The first batch will start now and the "
                f"remaining {file_count - cap} file(s) will stay queued as pending batches."
            )
        reply = QMessageBox.question(
            self, "Confirm Import", msg, QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        # Start import
        self._start_import_worker()

    def _start_import_worker(self) -> None:
        """Start the import worker thread."""
        # Disable controls
        self.add_files_button.setEnabled(False)
        self.add_folder_button.setEnabled(False)
        self.remove_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.import_button.setEnabled(False)
        self.keep_organized_radio.setEnabled(False)
        self.leave_in_place_radio.setEnabled(False)
        self.root_dir_button.setEnabled(False)
        self.generate_thumbnails_check.setEnabled(False)
        self.run_analysis_check.setEnabled(False)
        self.background_button.setEnabled(False)
        # Show progress section
        self.progress_section.setVisible(True)
        self._collapse_to_progress_only()
        self._expand_progress_section()
        self._background_mode = False
        self._background_monitor = None
        # Update UI state
        self.current_stage = ImportStage.VALIDATION
        self.start_time = time.time()
        self.time_timer.start(1000)  # Update every second
        # Clear progress display
        self.progress_text.clear()
        self._last_plain_log_message = None
        self._file_start_times.clear()
        self.overall_progress_bar.setValue(0)
        self.file_progress_bar.setValue(0)
        self.thumbnail_progress_bar.setValue(0)
        if self.generate_thumbnails_check.isChecked():
            self.thumbnail_status_label.setText("Waiting...")
        else:
            self.thumbnail_status_label.setText("Disabled")
        # Move archive files (.zip) to the end of the queue and confirm handling with the user.
        self.selected_files = self._handle_archives(self.selected_files)
        cap = self._get_batch_size()
        # Slice into batches and persist any remainder as pending.
        paths = list(self.selected_files)
        batches = (
            [paths[i : i + cap] for i in range(0, len(paths), cap)] if paths else []
        )
        pending_batches = batches[1:] if len(batches) > 1 else []
        ImportCoordinator._save_pending_batches(pending_batches)
        self._update_pending_label()
        if not batches:
            QMessageBox.warning(self, "No Files", "No files available to import.")
            self._reset_controls()
            return
        self.selected_files = batches[0]
        # Create and start worker
        mode = (
            FileManagementMode.KEEP_ORGANIZED
            if self.keep_organized_radio.isChecked()
            else FileManagementMode.LEAVE_IN_PLACE
        )
        root_dir = (
            self.root_dir_path.text()
            if mode == FileManagementMode.KEEP_ORGANIZED
            else None
        )
        # Capture current concurrency mode (UI could have been changed manually).
        current_mode = self.concurrency_combo.currentData() or "serial"
        self._concurrency_mode = (
            current_mode if current_mode in ("serial", "concurrent") else "serial"
        )
        if self._concurrency_mode == "concurrent" and hasattr(
            self, "prep_workers_spin"
        ):
            self._persist_prep_worker_setting()
        # Compute worker capacities for UI and worker overrides.
        try:
            concurrency_settings = self.import_settings.get_concurrency()
        except Exception:
            concurrency_settings = None
        prep_workers_used = (
            1
            if self._concurrency_mode == "serial"
            else (
                self.prep_workers_spin.value()
                if hasattr(self, "prep_workers_spin")
                else (concurrency_settings.prep_workers if concurrency_settings else 1)
            )
        )
        pipeline_workers_used = 1
        if self._concurrency_mode == "concurrent" and concurrency_settings:
            pipeline_workers_used = max(
                1,
                min(
                    concurrency_settings.queue_limit,
                    concurrency_settings.thumbnail_workers,
                ),
            )
        worker_slots = max(prep_workers_used, pipeline_workers_used, 1)
        self._init_worker_rows(worker_slots)
        config = ImportJobConfig(
            generate_thumbnails=self.generate_thumbnails_check.isChecked(),
            run_analysis=self.run_analysis_check.isChecked(),
            concurrency_mode=self._concurrency_mode,
            prep_workers=prep_workers_used,
            pipeline_workers=pipeline_workers_used,
        )
        # Use the new pipeline-based worker for complete import functionality
        self.import_worker = PipelineImportWorker(
            self.selected_files,
            mode,
            root_dir,
            config=config,
        )
        # Connect worker signals
        self.import_worker.stage_changed.connect(self._on_stage_changed)
        self.import_worker.file_progress.connect(self._on_file_progress)
        self.import_worker.overall_progress.connect(self._on_overall_progress)
        self.import_worker.thumbnail_progress.connect(self._on_thumbnail_progress)
        self.import_worker.model_imported.connect(self._on_model_imported)
        self.import_worker.import_completed.connect(self._on_import_completed)
        self.import_worker.import_cancelled.connect(self._on_import_cancelled)
        self.import_worker.import_failed.connect(self._on_import_failed)
        # Allow parent window to connect to model_imported signal for real-time updates
        parent = self.parent()
        if parent and hasattr(parent, "_on_model_imported_during_import"):
            handler = getattr(parent, "_on_model_imported_during_import")
            self.import_worker.model_imported.connect(handler)
        # Start worker
        self.import_worker.start()
        self._log_message("Import started...")
        self.status_label.setText("Importing...")
        self.background_button.setEnabled(True)
        self.background_button.setToolTip(
            "Hide this window and continue the import in the background."
        )

    def _on_stage_changed(self, stage: str, message: str) -> None:
        """Handle import stage change."""
        self.stage_label.setText(stage.replace("_", " ").title())
        self._log_message(message)

    def _on_file_progress(self, filename: str, percent: int, message: str) -> None:
        """Handle individual file progress update."""
        import time

        now = time.time()
        started = self._file_start_times.get(filename)
        # First sighting of this file: log start and record timestamp
        if started is None:
            self._file_start_times[filename] = now
            self._log_message(f"{filename}: started")
        # Only log on completion/failure to avoid spam
        if percent >= 100 or "Completed" in message or "Failed" in message:
            start_time = self._file_start_times.pop(filename, now)
            elapsed = now - start_time
            status = (
                "completed" if percent >= 100 or "Completed" in message else "failed"
            )
            self._log_message(f"{filename}: {status} in {elapsed:.1f}s")
        # Update per-worker UI
        self._update_worker_slot(filename, percent, message)
        self.file_progress_bar.setValue(percent)

    def _on_overall_progress(self, current: int, total: int, percent: int) -> None:
        """Handle overall progress update."""
        # Reset per-file tracking when a new overall run starts indexing
        if current == 0:
            self._file_start_times.clear()
        self.overall_progress_bar.setValue(percent)
        self.progress_label.setText(f"{current} / {total}")

    def _on_thumbnail_progress(
        self, current: int, total: int, current_file: str
    ) -> None:
        """Handle thumbnail generation progress update."""
        percent = int((current / total) * 100) if total > 0 else 0
        self.thumbnail_progress_bar.setValue(percent)
        self.thumbnail_status_label.setText(f"{current}/{total}: {current_file}")

    def _send_to_background(self) -> None:
        """Detach the running import and let it continue in the background."""
        if (
            self._background_mode
            or not self.import_worker
            or not self.import_worker.isRunning()
        ):
            return
        parent = self.parent()
        if parent is None:
            QMessageBox.warning(
                self,
                "Background Import Unavailable",
                "A parent window is required to show background status updates.",
            )
            return
        self._background_mode = True
        self.background_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.time_timer.stop()
        self.status_label.setText("Import running in background…")
        self._log_message("Sending import to background...")
        # Route progress updates to the main window status bar.
        self._background_monitor = ImportBackgroundMonitor(parent, self.import_worker)
        # Disconnect dialog slots so Qt does not emit to a closed dialog.
        self._disconnect_worker_signals()
        # Close the dialog without cancelling the worker.
        self.done(QDialog.Rejected)

    def _disconnect_worker_signals(self) -> None:
        """Disconnect worker signals from dialog slots."""
        if not self.import_worker:
            return
        signal_handlers = [
            (self.import_worker.stage_changed, self._on_stage_changed),
            (self.import_worker.file_progress, self._on_file_progress),
            (self.import_worker.overall_progress, self._on_overall_progress),
            (self.import_worker.thumbnail_progress, self._on_thumbnail_progress),
            (self.import_worker.import_completed, self._on_import_completed),
            (self.import_worker.import_cancelled, self._on_import_cancelled),
            (self.import_worker.import_failed, self._on_import_failed),
        ]
        for signal, handler in signal_handlers:
            try:
                signal.disconnect(handler)
            except TypeError:
                pass

    def was_backgrounded(self) -> bool:
        """Return True if the dialog handed the import off to the background."""
        return self._background_mode

    def _on_model_imported(self, model_id: int) -> None:
        """
        Handle individual model import completion.
        This is called after each model is successfully imported, allowing
        the UI to refresh incrementally instead of waiting for all imports.
        Args:
            model_id: Database ID of the imported model
        """
        # Notify parent window to refresh model library
        parent = self.parent()
        if parent and hasattr(parent, "_on_model_imported_during_import"):
            try:
                handler = getattr(parent, "_on_model_imported_during_import")
                handler(model_id)
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.warning("Failed to notify parent of model import: %s", exc)

    def _handle_archives(self, files: List[str]) -> List[str]:
        """Move archives to the end of the queue and ask user how to handle them."""
        zips = [f for f in files if Path(f).suffix.lower() == ".zip"]
        if not zips:
            return files
        base_list = [f for f in files if f not in zips]
        message_lines = [
            "Archive files were detected in the import list.",
            "",
            "How would you like to handle them?",
            " - Continue: unzip archives with the built-in importer.",
            " - Ignore: skip these archives and import the other files.",
            "",
            "Archives:",
            *[f" • {Path(z).name}" for z in zips],
        ]
        message = "\n".join(message_lines)
        reply = QMessageBox.question(
            self,
            "Archive Detected",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply == QMessageBox.No:
            # Skip archives entirely
            self._log_message("User chose to ignore archive files; skipping them.")
            return base_list
        # Keep archives, but push them to the end so regular files finish first.
        self._log_message(
            "Archives moved to end of queue; will be unpacked when reached."
        )
        return base_list + zips

    def _on_import_completed(self, result: ImportResult) -> None:
        """Handle successful import completion."""
        self.current_stage = ImportStage.COMPLETED
        self.import_result = result
        self.time_timer.stop()
        self.background_button.setEnabled(False)
        if self._background_mode:
            return
        # Show results
        duration = result.duration_seconds
        self._log_message(
            f"\nImport completed in {duration:.1f} seconds:\n"
            f"  • Total files: {result.total_files}\n"
            f"  • Processed: {result.processed_files}\n"
            f"  • Failed: {result.failed_files}\n"
            f"  • Skipped: {result.skipped_files}\n"
            f"  • Duplicates: {result.duplicate_count}\n"
            f"  • Total size: {result.total_size_bytes / (1024 * 1024):.2f} MB"
        )
        self.overall_progress_bar.setValue(100)
        self.file_progress_bar.setValue(100)
        self.thumbnail_progress_bar.setValue(100)
        self.thumbnail_status_label.setText("Complete")
        self.stage_label.setText("Completed")
        self.status_label.setText(
            f"Import completed: {result.processed_files} file(s) imported"
        )
        self._update_pending_label()
        # Show completion message
        if self.enable_ai_tagging_check.isChecked():
            self._run_ai_tagging(result)
        QMessageBox.information(
            self,
            "Import Complete",
            f"Successfully imported {result.processed_files} of {result.total_files} file(s).\n\n"
            f"Duration: {duration:.1f} seconds\n"
            f"Failed: {result.failed_files}\n"
            f"Skipped: {result.skipped_files}",
        )
        # Close dialog
        self.accept()

    def _on_import_cancelled(self, result: Optional[ImportResult], reason: str) -> None:
        """Handle cancellation signal from the worker."""
        self.current_stage = ImportStage.CANCELLED
        self.time_timer.stop()
        self.background_button.setEnabled(False)
        if result:
            self.import_result = result
        summary = ""
        if result:
            summary = (
                f"\nProcessed: {result.processed_files}\n"
                f"Failed: {result.failed_files}\n"
                f"Skipped: {result.skipped_files}"
            )
        self._log_message(f"Import cancelled: {reason}{summary}")
        self.stage_label.setText("Cancelled")
        self.status_label.setText("Import cancelled")
        self._update_pending_label()
        self._file_start_times.clear()
        if self._background_mode:
            return
        QMessageBox.information(
            self,
            "Import Cancelled",
            f"The import was cancelled:\n\n{reason}{summary}",
        )
        self._reset_controls()

    def _on_import_failed(self, error_message: str) -> None:
        """Handle import failure."""
        self.current_stage = ImportStage.FAILED
        self.time_timer.stop()
        self.background_button.setEnabled(False)
        if self._background_mode:
            return
        self._log_message(f"\n❌ Import failed: {error_message}")
        self.stage_label.setText("Failed")
        self.status_label.setText("Import failed")
        self._update_pending_label()
        self._file_start_times.clear()
        QMessageBox.critical(
            self, "Import Failed", f"Import failed with error:\n\n{error_message}"
        )
        # Re-enable controls
        self._reset_controls()

    def _run_ai_tagging(self, result: ImportResult) -> None:
        """Best-effort AI tagging using generated thumbnails."""
        try:
            ai_enabled = bool(QSettings().value("ai/auto_tag_import", False, type=bool))
            if not ai_enabled:
                return
            db_manager = get_database_manager()
            ai_service = AIDescriptionService()
        except Exception as exc:
            self._log_message(f"AI tagging unavailable: {exc}")
            return
        thumb_map = {}
        if self.import_worker and hasattr(self.import_worker, "generated_thumbnails"):
            try:
                from pathlib import Path

                thumb_map = {
                    Path(f).resolve(): thumb
                    for f, thumb in getattr(
                        self.import_worker, "generated_thumbnails", []
                    )
                }
            except Exception:
                thumb_map = {}
        processed = 0
        tagged = 0
        for file_info in getattr(
            result, "session", ImportSession("", FileManagementMode.LEAVE_IN_PLACE)
        ).files:
            if getattr(file_info, "import_status", "") not in ("completed", "success"):
                continue
            path = file_info.managed_path or file_info.original_path
            if not path:
                continue
            processed += 1
            try:
                model = db_manager.get_model_by_path(path)
                if not model:
                    continue
                # Prefer thumbnail path if available; skip when missing to avoid passing 3D file to AI.
                from pathlib import Path

                thumb = thumb_map.get(Path(path).resolve())
                if not thumb:
                    continue
                ai_result = ai_service.analyze_image(thumb)
                keywords = ai_result.get("metadata_keywords") or []
                if keywords:
                    db_manager.update_model_keywords_tags(
                        model["id"], add_tags=keywords
                    )
                    tagged += 1
            except Exception as exc:
                self._log_message(f"AI tagging skipped for {path}: {exc}")
        if tagged:
            self._log_message(
                f"AI tagging applied to {tagged} of {processed} imported file(s)."
            )

    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        if self.import_worker and self.import_worker.isRunning():
            # Confirm cancellation
            reply = QMessageBox.question(
                self,
                "Cancel Import",
                "Are you sure you want to cancel the import?\n\n"
                "Any files already processed will remain imported.",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self._log_message("Cancelling import...")
                self.status_label.setText("Cancelling...")
                self.import_worker.cancel()
                self.import_worker.wait()
        else:
            # Just close the dialog
            self.reject()

    def _reset_controls(self) -> None:
        """Reset controls after import completion or failure."""
        # Return to idle state so the user can restart the import
        self.current_stage = ImportStage.IDLE
        self.import_worker = None
        self.add_files_button.setEnabled(True)
        self.add_folder_button.setEnabled(True)
        self.remove_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.keep_organized_radio.setEnabled(True)
        self.leave_in_place_radio.setEnabled(True)
        self.root_dir_button.setEnabled(True)
        self.generate_thumbnails_check.setEnabled(True)
        self.run_analysis_check.setEnabled(True)
        self.background_button.setEnabled(False)
        self._background_mode = False
        self._update_import_button_state()
        self._update_pending_label()
        self._file_start_times.clear()
        # Restore full layout if it was collapsed for progress-only view.
        self._restore_full_layout()

    def _get_batch_size(self) -> int:
        """Return the configured batch size, clamped to sane bounds."""
        try:
            if hasattr(self, "batch_size_spin"):
                value = int(self.batch_size_spin.value())
            else:
                value = int(
                    self._settings.value(
                        "import/batch_size",
                        getattr(ImportFileManager, "MAX_IMPORT_FILES", 500),
                        type=int,
                    )
                    or 500
                )
        except Exception:
            value = getattr(ImportFileManager, "MAX_IMPORT_FILES", 500)
        return max(10, min(2000, value or 500))

    def _on_batch_size_changed(self, value: int) -> None:
        """Persist batch size changes."""
        try:
            self._settings.setValue("import/batch_size", int(value))
        except Exception:
            self.logger.debug("Failed to persist batch size")

    def reject(self) -> None:
        """
        Ensure the importer stops when the window is closed (title bar X or Esc).
        This cancels any running worker to avoid background processing after
        the dialog is dismissed.
        """
        if self.import_worker and self.import_worker.isRunning():
            self._log_message("Closing import window: cancelling active import...")
            self.status_label.setText("Cancelling...")
            try:
                self.import_worker.cancel()
                self.import_worker.wait()
            except Exception as exc:
                self.logger.warning("Failed to cancel import on close: %s", exc)
        super().reject()

    def _update_time_elapsed(self) -> None:
        """Update elapsed time display."""
        if self.start_time:
            elapsed = time.time() - self.start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            self.time_label.setText(f"Time: {minutes}:{seconds:02d}")

    def _log_message(self, message: str) -> None:
        """
        Add a message to the progress log.
        Args:
            message: Message to log
        """
        # Avoid spamming the log with per-millisecond updates; only log when the content changes.
        if message == self._last_plain_log_message:
            return
        self._last_plain_log_message = message
        timestamp = time.strftime("%H:%M:%S")
        self.progress_text.append(f"[{timestamp}] {message}")
        # Auto-scroll to bottom
        scrollbar = self.progress_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    # Drag and drop support
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop event."""
        files = []
        has_directory = False
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            path = Path(file_path)
            if path.is_file():
                # Single file
                if path.suffix.lower() in {
                    ".stl",
                    ".obj",
                    ".step",
                    ".stp",
                    ".3mf",
                    ".ply",
                }:
                    files.append(str(path))
            elif path.is_dir():
                has_directory = True
                # Directory - find all model files
                model_extensions = {".stl", ".obj", ".step", ".stp", ".3mf", ".ply"}
                for ext in model_extensions:
                    files.extend(str(p) for p in path.rglob(f"*{ext}"))
                    files.extend(str(p) for p in path.rglob(f"*{ext.upper()}"))
        if files:
            self._add_files(files)
            # Default concurrency per source: serial for files, concurrent for directories.
            self._apply_concurrency_mode_ui("concurrent" if has_directory else "serial")
            event.acceptProposedAction()

    def get_import_result(self) -> Optional[ImportResult]:
        """
        Get the import result after completion.
        Returns:
            ImportResult object if import completed, None otherwise
        """
        return self.import_result

    def sizeHint(self) -> QSize:
        """Return preferred size for the dialog."""
        return QSize(900, 700)
