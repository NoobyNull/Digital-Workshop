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
from typing import Optional, List
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
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QSplitter,
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer, QSize
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont

from src.core.logging_config import get_logger
from src.core.cancellation_token import CancellationToken
from src.core.import_file_manager import (
    ImportFileManager,
    FileManagementMode,
    DuplicateAction,
    ImportResult,
)
from src.core.import_thumbnail_service import ImportThumbnailService
from src.core.import_analysis_service import ImportAnalysisService


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


class ImportWorker(QThread):
    """
    Background worker thread for import process.

    Handles all import operations without blocking the UI thread.
    """

    # Signals for progress communication
    stage_changed = Signal(str, str)  # stage, message
    file_progress = Signal(str, int, str)  # filename, percent, message
    overall_progress = Signal(int, int, int)  # current, total, percent
    thumbnail_progress = Signal(int, int, str)  # current, total, current_file
    import_completed = Signal(object)  # ImportResult
    import_failed = Signal(str)  # error_message

    def __init__(
        self,
        file_paths: List[str],
        mode: FileManagementMode,
        root_directory: Optional[str],
        generate_thumbnails: bool,
        run_analysis: bool,
    ):
        """
        Initialize import worker.

        Args:
            file_paths: List of file paths to import
            mode: File management mode
            root_directory: Root directory for organized mode
            generate_thumbnails: Whether to generate thumbnails
            run_analysis: Whether to run background analysis
        """
        super().__init__()
        self.file_paths = file_paths
        self.mode = mode
        self.root_directory = root_directory
        self.generate_thumbnails = generate_thumbnails
        self.run_analysis = run_analysis

        self.logger = get_logger(__name__)
        self.cancellation_token = CancellationToken()

        # Initialize services
        self.file_manager = ImportFileManager()
        self.thumbnail_service = (
            ImportThumbnailService() if generate_thumbnails else None
        )
        self.analysis_service = ImportAnalysisService() if run_analysis else None

    def run(self):
        """Execute the import process."""
        try:
            self.stage_changed.emit("validation", "Validating files and settings...")

            # Start import session
            success, error, session = self.file_manager.start_import_session(
                self.file_paths, self.mode, self.root_directory, DuplicateAction.SKIP
            )

            if not success:
                self.import_failed.emit(error)
                return

            total_files = len(session.files)
            files_to_process = []

            # Process each file
            for idx, file_info in enumerate(session.files):
                if self.cancellation_token.is_cancelled():
                    break

                file_name = Path(file_info.original_path).name

                # Report overall progress
                self.overall_progress.emit(
                    idx, total_files, int((idx / total_files) * 100)
                )

                # Process file (hashing + copying if needed)
                self.stage_changed.emit("hashing", f"Processing {file_name}...")

                def file_progress_callback(message, percent):
                    self.file_progress.emit(file_name, percent, message)

                success, error = self.file_manager.process_file(
                    file_info, session, file_progress_callback, self.cancellation_token
                )

                if not success:
                    self.logger.warning(f"Failed to process {file_name}: {error}")
                    continue

                # Collect files for thumbnail generation (don't generate here - it blocks!)
                if self.generate_thumbnails and file_info.file_hash:
                    files_to_process.append(
                        (
                            file_info.managed_path or file_info.original_path,
                            file_info.file_hash,
                        )
                    )

            # Generate thumbnails in separate worker (truly non-blocking)
            if files_to_process:
                self.stage_changed.emit(
                    "thumbnails",
                    f"Generating thumbnails for {len(files_to_process)} files...",
                )
                try:
                    from src.core.application_config import ApplicationConfig
                    from PySide6.QtCore import QSettings

                    config = ApplicationConfig.get_default()
                    settings = QSettings()

                    # Get current thumbnail preferences
                    bg_image = settings.value(
                        "thumbnail/background_image",
                        config.thumbnail_bg_image,
                        type=str,
                    )
                    material = settings.value(
                        "thumbnail/material", config.thumbnail_material, type=str
                    )
                    bg_color = settings.value(
                        "thumbnail/background_color",
                        config.thumbnail_bg_color,
                        type=str,
                    )

                    # Use background image if set, otherwise use background color
                    background = bg_image if bg_image else bg_color

                    self.logger.debug(
                        f"Thumbnail preferences: bg_image={bg_image}, bg_color={bg_color}, background={background}, material={material}"
                    )

                    # Create and start thumbnail generation worker
                    from src.gui.thumbnail_generation_worker import (
                        ThumbnailGenerationWorker,
                    )

                    thumbnail_worker = ThumbnailGenerationWorker(
                        files_to_process, background=background, material=material
                    )

                    # Connect signals
                    thumbnail_worker.progress_updated.connect(
                        lambda current, total, file: self.thumbnail_progress.emit(
                            current, total, file
                        )
                    )
                    thumbnail_worker.error_occurred.connect(
                        lambda file, error: self.logger.warning(
                            f"Thumbnail error for {file}: {error}"
                        )
                    )

                    # Run worker and wait for completion
                    thumbnail_worker.start()
                    thumbnail_worker.wait()  # Block until thumbnails are done

                    self.logger.info("Thumbnail generation completed")
                except Exception as e:
                    self.logger.warning(f"Failed to generate thumbnails: {e}")

            # Complete import session
            result = self.file_manager.complete_import_session(
                session, not self.cancellation_token.is_cancelled()
            )

            # Start background analysis if enabled
            if self.run_analysis and result.processed_files > 0:
                self.stage_changed.emit("analysis", "Queueing background analysis...")
                # Analysis runs in background, doesn't block completion
                file_model_pairs = [
                    (f.managed_path or f.original_path, idx + 1)
                    for idx, f in enumerate(session.files)
                    if f.import_status == "completed"
                ]
                if file_model_pairs:
                    self.analysis_service.start_batch_analysis(
                        file_model_pairs, cancellation_token=self.cancellation_token
                    )

            self.import_completed.emit(result)

        except Exception as e:
            self.logger.error(f"Import worker failed: {e}", exc_info=True)
            self.import_failed.emit(str(e))

    def cancel(self):
        """Cancel the import operation."""
        self.cancellation_token.cancel()


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

    def __init__(self, parent=None, root_folder_manager=None):
        """
        Initialize the import dialog.

        Args:
            parent: Parent widget
            root_folder_manager: Optional RootFolderManager instance
        """
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.root_folder_manager = root_folder_manager

        # State
        self.current_stage = ImportStage.IDLE
        self.import_result: Optional[ImportResult] = None
        self.import_worker: Optional[ImportWorker] = None
        self.selected_files: List[str] = []
        self.start_time: Optional[float] = None

        # Setup UI
        self._setup_ui()
        self._connect_signals()

        # Enable drag and drop
        self.setAcceptDrops(True)

        self.logger.info("ImportDialog initialized")

    def _setup_ui(self):
        """Setup the dialog user interface."""
        self.setWindowTitle("Import 3D Models")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)

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
        splitter = QSplitter(Qt.Vertical)

        # === File Selection Section ===
        file_section = self._create_file_selection_section()
        splitter.addWidget(file_section)

        # === Options Section ===
        options_section = self._create_options_section()
        splitter.addWidget(options_section)

        # === Progress Section ===
        progress_section = self._create_progress_section()
        splitter.addWidget(progress_section)

        # Set splitter sizes
        splitter.setSizes([300, 150, 150])
        main_layout.addWidget(splitter, 1)

        # === Status bar ===
        self.status_label = QLabel("Ready to import")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        main_layout.addWidget(self.status_label)

        # === Buttons ===
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.import_button = QPushButton("Start Import")
        self.import_button.setMinimumWidth(120)
        self.import_button.setEnabled(False)
        button_layout.addWidget(self.import_button)

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
        hint_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        layout.addWidget(hint_label)

        return group

    def _create_options_section(self) -> QGroupBox:
        """Create the import options section."""
        group = QGroupBox("Import Options")
        layout = QVBoxLayout(group)

        # File Management Mode
        mode_label = QLabel("File Management:")
        mode_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(mode_label)

        self.keep_organized_radio = QRadioButton("Keep Organized")
        self.keep_organized_radio.setToolTip(
            "Copy files to managed directory with organized folder structure"
        )
        self.keep_organized_radio.setChecked(True)
        layout.addWidget(self.keep_organized_radio)

        self.leave_in_place_radio = QRadioButton("Leave in Place")
        self.leave_in_place_radio.setToolTip(
            "Track files in their original locations without copying"
        )
        layout.addWidget(self.leave_in_place_radio)

        # Root directory selection (for keep organized mode)
        root_layout = QHBoxLayout()
        root_layout.addSpacing(20)
        self.root_dir_label = QLabel("Root Directory:")
        root_layout.addWidget(self.root_dir_label)

        self.root_dir_path = QLabel("Not selected")
        self.root_dir_path.setStyleSheet("color: #666; font-style: italic;")
        root_layout.addWidget(self.root_dir_path, 1)

        self.root_dir_button = QPushButton("Browse...")
        self.root_dir_button.setMaximumWidth(100)
        root_layout.addWidget(self.root_dir_button)
        layout.addLayout(root_layout)

        # Additional options
        layout.addSpacing(10)
        options_label = QLabel("Processing Options:")
        options_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(options_label)

        from PySide6.QtWidgets import QCheckBox

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

        # Current file progress
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Current:"))

        self.file_progress_bar = QProgressBar()
        self.file_progress_bar.setRange(0, 100)
        self.file_progress_bar.setValue(0)
        self.file_progress_bar.setTextVisible(True)
        file_layout.addWidget(self.file_progress_bar, 1)
        layout.addLayout(file_layout)

        # Thumbnail generation status
        thumbnail_layout = QHBoxLayout()
        thumbnail_layout.addWidget(QLabel("Thumbnails:"))

        self.thumbnail_status_label = QLabel("Waiting...")
        self.thumbnail_status_label.setStyleSheet("color: #666;")
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
        self.stage_label.setStyleSheet("font-weight: bold;")
        stage_layout.addWidget(self.stage_label, 1)

        self.time_label = QLabel("")
        self.time_label.setAlignment(Qt.AlignRight)
        stage_layout.addWidget(self.time_label)
        layout.addLayout(stage_layout)

        # Status/Error display
        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        self.progress_text.setMaximumHeight(100)
        self.progress_text.setPlaceholderText("Import progress will be shown here...")
        layout.addWidget(self.progress_text)

        # Initially hide progress section
        group.setVisible(False)
        self.progress_section = group

        return group

    def _connect_signals(self):
        """Connect widget signals."""
        self.add_files_button.clicked.connect(self._on_add_files)
        self.add_folder_button.clicked.connect(self._on_add_folder)
        self.remove_button.clicked.connect(self._on_remove_selected)
        self.clear_button.clicked.connect(self._on_clear_all)

        self.file_list.itemSelectionChanged.connect(self._on_file_selection_changed)

        self.keep_organized_radio.toggled.connect(self._on_mode_changed)
        self.root_dir_button.clicked.connect(self._on_select_root_directory)

        self.import_button.clicked.connect(self._on_start_import)
        self.cancel_button.clicked.connect(self._on_cancel)

        # Update time elapsed timer
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self._update_time_elapsed)

    def _on_add_files(self):
        """Handle add files button click."""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter(
            "3D Model Files (*.stl *.obj *.step *.stp *.3mf *.ply);;All Files (*.*)"
        )

        if file_dialog.exec():
            files = file_dialog.selectedFiles()
            self._add_files(files)

    def _on_add_folder(self):
        """Handle add folder button click."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder Containing Model Files"
        )

        if folder:
            # Find all model files in folder
            folder_path = Path(folder)
            model_extensions = {".stl", ".obj", ".step", ".stp", ".3mf", ".ply"}
            files = []

            for ext in model_extensions:
                files.extend(str(p) for p in folder_path.rglob(f"*{ext}"))
                files.extend(str(p) for p in folder_path.rglob(f"*{ext.upper()}"))

            if files:
                self._add_files(files)
                self._log_message(f"Found {len(files)} model files in folder")
            else:
                QMessageBox.warning(
                    self,
                    "No Files Found",
                    "No 3D model files found in the selected folder.",
                )

    def _add_files(self, files: List[str]):
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
                except Exception as e:
                    # Collect failed files instead of showing dialog
                    failed_files.append((Path(file_path).name, str(e)))
                    self.logger.warning(f"Failed to add file {file_path}: {e}")

        if added_count > 0:
            self._update_import_button_state()
            self._log_message(f"Added {added_count} file(s)")
            self.status_label.setText(f"{len(self.selected_files)} file(s) selected")

        # Show summary of failures if any
        if failed_files:
            self._show_import_failures_summary(failed_files, added_count)

    def _show_import_failures_summary(
        self, failed_files: List[tuple], added_count: int
    ):
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

    def _on_remove_selected(self):
        """Remove selected files from the list."""
        selected_items = self.file_list.selectedItems()

        for item in selected_items:
            file_path = item.data(Qt.UserRole)
            self.selected_files.remove(file_path)
            self.file_list.takeItem(self.file_list.row(item))

        self._update_import_button_state()
        self.status_label.setText(f"{len(self.selected_files)} file(s) selected")

    def _on_clear_all(self):
        """Clear all files from the list."""
        self.selected_files.clear()
        self.file_list.clear()
        self._update_import_button_state()
        self.status_label.setText("Ready to import")

    def _on_file_selection_changed(self):
        """Handle file selection change."""
        has_selection = len(self.file_list.selectedItems()) > 0
        self.remove_button.setEnabled(has_selection)

    def _on_mode_changed(self, checked: bool):
        """Handle file management mode change."""
        if checked:  # Keep organized mode selected
            self.root_dir_label.setEnabled(True)
            self.root_dir_path.setEnabled(True)
            self.root_dir_button.setEnabled(True)
        else:
            self.root_dir_label.setEnabled(False)
            self.root_dir_path.setEnabled(False)
            self.root_dir_button.setEnabled(False)

        self._update_import_button_state()

    def _on_select_root_directory(self):
        """Handle root directory selection."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Root Directory for Organized Storage"
        )

        if folder:
            self.root_dir_path.setText(folder)
            self.root_dir_path.setStyleSheet("color: #000;")
            self._update_import_button_state()

    def _update_import_button_state(self):
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

    def _on_start_import(self):
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

        msg = (
            f"Import {file_count} file(s) ({total_size:.2f} MB)?\n\n"
            f"Mode: {'Keep Organized' if self.keep_organized_radio.isChecked() else 'Leave in Place'}\n"
        )

        if self.keep_organized_radio.isChecked():
            msg += f"Root Directory: {self.root_dir_path.text()}\n"

        msg += f"Generate Thumbnails: {'Yes' if self.generate_thumbnails_check.isChecked() else 'No'}\n"
        msg += f"Run Analysis: {'Yes' if self.run_analysis_check.isChecked() else 'No'}"

        reply = QMessageBox.question(
            self, "Confirm Import", msg, QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # Start import
        self._start_import_worker()

    def _start_import_worker(self):
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

        # Show progress section
        self.progress_section.setVisible(True)

        # Update UI state
        self.current_stage = ImportStage.VALIDATION
        self.start_time = time.time()
        self.time_timer.start(1000)  # Update every second

        # Clear progress display
        self.progress_text.clear()
        self.overall_progress_bar.setValue(0)
        self.file_progress_bar.setValue(0)
        self.thumbnail_progress_bar.setValue(0)
        self.thumbnail_status_label.setText("Waiting...")

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

        self.import_worker = ImportWorker(
            self.selected_files,
            mode,
            root_dir,
            self.generate_thumbnails_check.isChecked(),
            self.run_analysis_check.isChecked(),
        )

        # Connect worker signals
        self.import_worker.stage_changed.connect(self._on_stage_changed)
        self.import_worker.file_progress.connect(self._on_file_progress)
        self.import_worker.overall_progress.connect(self._on_overall_progress)
        self.import_worker.thumbnail_progress.connect(self._on_thumbnail_progress)
        self.import_worker.import_completed.connect(self._on_import_completed)
        self.import_worker.import_failed.connect(self._on_import_failed)

        # Start worker
        self.import_worker.start()

        self._log_message("Import started...")
        self.status_label.setText("Importing...")

    def _on_stage_changed(self, stage: str, message: str):
        """Handle import stage change."""
        self.stage_label.setText(stage.replace("_", " ").title())
        self._log_message(message)

    def _on_file_progress(self, filename: str, percent: int, message: str):
        """Handle individual file progress update."""
        self.file_progress_bar.setValue(percent)
        self._log_message(f"{filename}: {message}")

    def _on_overall_progress(self, current: int, total: int, percent: int):
        """Handle overall progress update."""
        self.overall_progress_bar.setValue(percent)
        self.progress_label.setText(f"{current} / {total}")

    def _on_thumbnail_progress(self, current: int, total: int, current_file: str):
        """Handle thumbnail generation progress update."""
        percent = int((current / total) * 100) if total > 0 else 0
        self.thumbnail_progress_bar.setValue(percent)
        self.thumbnail_status_label.setText(f"{current}/{total}: {current_file}")
        self._log_message(f"✓ Thumbnail {current}/{total}: {current_file}")

    def _on_import_completed(self, result: ImportResult):
        """Handle successful import completion."""
        self.current_stage = ImportStage.COMPLETED
        self.import_result = result
        self.time_timer.stop()

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

        # Show completion message
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

    def _on_import_failed(self, error_message: str):
        """Handle import failure."""
        self.current_stage = ImportStage.FAILED
        self.time_timer.stop()

        self._log_message(f"\n❌ Import failed: {error_message}")
        self.stage_label.setText("Failed")
        self.status_label.setText("Import failed")

        QMessageBox.critical(
            self, "Import Failed", f"Import failed with error:\n\n{error_message}"
        )

        # Re-enable controls
        self._reset_controls()

    def _on_cancel(self):
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

                self.current_stage = ImportStage.CANCELLED
                self.time_timer.stop()
                self._log_message("Import cancelled by user")
                self.stage_label.setText("Cancelled")

                self._reset_controls()
        else:
            # Just close the dialog
            self.reject()

    def _reset_controls(self):
        """Reset controls after import completion or failure."""
        self.add_files_button.setEnabled(True)
        self.add_folder_button.setEnabled(True)
        self.remove_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.keep_organized_radio.setEnabled(True)
        self.leave_in_place_radio.setEnabled(True)
        self.root_dir_button.setEnabled(True)
        self.generate_thumbnails_check.setEnabled(True)
        self.run_analysis_check.setEnabled(True)
        self._update_import_button_state()

    def _update_time_elapsed(self):
        """Update elapsed time display."""
        if self.start_time:
            elapsed = time.time() - self.start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            self.time_label.setText(f"Time: {minutes}:{seconds:02d}")

    def _log_message(self, message: str):
        """
        Add a message to the progress log.

        Args:
            message: Message to log
        """
        timestamp = time.strftime("%H:%M:%S")
        self.progress_text.append(f"[{timestamp}] {message}")

        # Auto-scroll to bottom
        scrollbar = self.progress_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    # Drag and drop support
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """Handle drop event."""
        files = []

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
                # Directory - find all model files
                model_extensions = {".stl", ".obj", ".step", ".stp", ".3mf", ".ply"}
                for ext in model_extensions:
                    files.extend(str(p) for p in path.rglob(f"*{ext}"))
                    files.extend(str(p) for p in path.rglob(f"*{ext.upper()}"))

        if files:
            self._add_files(files)
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
