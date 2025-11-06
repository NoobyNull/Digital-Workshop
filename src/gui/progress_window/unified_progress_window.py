"""
Unified Progress Window for Digital Workshop.

This module provides a unified progress window that adapts its UI based on
the operation mode (import, thumbnail generation, analysis, etc.).

Architecture:
    ┌─────────────────────────────────────────┐
    │    UnifiedProgressWindow (QDialog)      │
    ├─────────────────────────────────────────┤
    │  - Mode-based configuration             │
    │  - Overall progress tracking            │
    │  - Stage sections (collapsible)         │
    │  - VTK preview (adaptive sizing)        │
    │  - Dual progress (individual + batch)   │
    │  - Time estimation                      │
    │  - Pause/Resume/Cancel controls         │
    │  - Close warning system                 │
    │  - Background mode support              │
    └─────────────────────────────────────────┘

Usage:
    # For import operations
    window = UnifiedProgressWindow(
        mode=ProgressWindowMode.IMPORT,
        total_items=15,
        parent=self
    )
    window.connect_worker_signals(import_worker)
    window.show()

    # For thumbnail generation only
    window = UnifiedProgressWindow(
        mode=ProgressWindowMode.THUMBNAIL_ONLY,
        total_items=15,
        parent=self
    )
    window.connect_worker_signals(thumbnail_worker)
    window.show()
"""

import time
from typing import Optional, Dict

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QGroupBox,
    QMessageBox,
    QWidget,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal, QTimer, QSettings
from PySide6.QtGui import QCloseEvent, QFont

from src.core.logging_config import get_logger

from src.gui.progress_window.progress_window_mode import (
    ProgressWindowMode,
    StageStatus,
    StageProgress,
    ThumbnailProgress,
    OverallProgress,
    StageConfiguration,
    ProgressWeights,
)


class UnifiedProgressWindow(QDialog):
    """
    Unified progress window for all long-running operations.

    Adapts UI based on operation mode:
    - IMPORT: Shows all import stages with collapsible sections
    - THUMBNAIL_ONLY: Shows only thumbnail generation with prominent VTK preview
    - ANALYSIS_ONLY: Shows only analysis stage
    - REGENERATE: Shows regeneration progress

    Signals:
        operation_paused: Emitted when user pauses the operation
        operation_resumed: Emitted when user resumes the operation
        operation_cancelled: Emitted when user cancels the operation
        operation_completed: Emitted when operation completes successfully
    """

    # Signals
    operation_paused = Signal()
    operation_resumed = Signal()
    operation_cancelled = Signal()
    operation_completed = Signal()

    def __init__(
        self,
        mode: ProgressWindowMode,
        total_items: int,
        parent: Optional[QWidget] = None,
    ):
        """
        Initialize the unified progress window.

        Args:
            mode: Operation mode (IMPORT, THUMBNAIL_ONLY, etc.)
            total_items: Total number of items to process
            parent: Parent widget
        """
        super().__init__(parent)
        self.logger = get_logger(__name__)

        # Core state
        self.mode = mode
        self.total_items = total_items
        self.config = StageConfiguration.for_mode(mode, total_items)
        self.progress_weights = ProgressWeights()

        # Progress tracking
        self.overall_progress = OverallProgress(mode=mode, total_items=total_items)
        self.stage_progress: Dict[str, StageProgress] = {}
        self.thumbnail_progress = ThumbnailProgress(total_count=total_items)

        # State flags
        self.is_paused = False
        self.is_cancelled = False
        self.is_completed = False
        self.operation_start_time = time.time()

        # Timer for time updates
        self.time_update_timer = QTimer(self)
        self.time_update_timer.timeout.connect(self._update_time_display)
        self.time_update_timer.start(1000)  # Update every second

        # UI components (will be created in _setup_ui)
        self.overall_progress_bar: Optional[QProgressBar] = None
        self.overall_label: Optional[QLabel] = None
        self.time_label: Optional[QLabel] = None
        self.stage_sections: Dict[str, QGroupBox] = {}
        self.pause_button: Optional[QPushButton] = None
        self.cancel_button: Optional[QPushButton] = None
        self.minimize_button: Optional[QPushButton] = None

        # Setup UI
        self._setup_ui()
        self._configure_for_mode()
        self._restore_window_state()

        self.logger.info(
            "UnifiedProgressWindow initialized: mode=%s, total_items=%d",
            mode.value,
            total_items,
        )

    def _setup_ui(self) -> None:
        """Create all UI components."""
        self.setWindowTitle(self.config.window_title_prefix)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setModal(False)  # Non-modal so main window remains accessible

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Overall progress section
        overall_section = self._create_overall_progress_section()
        main_layout.addWidget(overall_section)

        # Scrollable area for stage sections
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setMinimumHeight(200)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(10)

        # Create all stage sections (visibility set in _configure_for_mode)
        self.stage_sections["validation"] = self._create_stage_section("Validation")
        self.stage_sections["hashing"] = self._create_stage_section("Hashing & Copying")
        self.stage_sections["thumbnails"] = self._create_thumbnail_section()
        self.stage_sections["analysis"] = self._create_stage_section("Analysis")

        for section in self.stage_sections.values():
            scroll_layout.addWidget(section)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

        # Time display
        self.time_label = QLabel("Elapsed: 0s | Remaining: Calculating...")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.time_label)

        # Control buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.pause_button = QPushButton("Pause")
        self.pause_button.setMinimumWidth(100)
        self.pause_button.clicked.connect(self._on_pause_resume_clicked)
        button_layout.addWidget(self.pause_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumWidth(100)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        button_layout.addWidget(self.cancel_button)

        button_layout.addStretch()

        self.minimize_button = QPushButton("Minimize to Background")
        self.minimize_button.setMinimumWidth(180)
        self.minimize_button.clicked.connect(self._on_minimize_clicked)
        button_layout.addWidget(self.minimize_button)

        main_layout.addLayout(button_layout)

        self.logger.debug("UI setup complete")

    def _create_overall_progress_section(self) -> QGroupBox:
        """Create the overall progress section."""
        section = QGroupBox("Overall Progress")
        layout = QVBoxLayout()

        self.overall_label = QLabel("Starting...")
        self.overall_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.overall_label.setFont(font)
        layout.addWidget(self.overall_label)

        self.overall_progress_bar = QProgressBar()
        self.overall_progress_bar.setRange(0, 100)
        self.overall_progress_bar.setValue(0)
        self.overall_progress_bar.setMinimumHeight(30)
        self.overall_progress_bar.setTextVisible(True)
        self.overall_progress_bar.setFormat("%p%")
        layout.addWidget(self.overall_progress_bar)

        section.setLayout(layout)
        return section

    def _create_stage_section(self, stage_name: str) -> QGroupBox:
        """Create a generic stage section."""
        section = QGroupBox(stage_name)
        layout = QVBoxLayout()

        status_label = QLabel("⏳ Waiting...")
        status_label.setObjectName(f"{stage_name.lower()}_status")
        layout.addWidget(status_label)

        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setObjectName(f"{stage_name.lower()}_progress")
        layout.addWidget(progress_bar)

        section.setLayout(layout)
        return section

    def _create_thumbnail_section(self) -> QGroupBox:
        """Create the thumbnail generation section with dual progress."""
        section = QGroupBox("Thumbnail Generation")
        layout = QVBoxLayout()

        # Current model label
        current_label = QLabel("Waiting to start...")
        current_label.setObjectName("thumbnail_current_label")
        layout.addWidget(current_label)

        # Individual progress
        individual_label = QLabel("Individual Progress:")
        layout.addWidget(individual_label)

        individual_progress = QProgressBar()
        individual_progress.setRange(0, 100)
        individual_progress.setValue(0)
        individual_progress.setObjectName("thumbnail_individual_progress")
        layout.addWidget(individual_progress)

        individual_stage = QLabel("Stage: Waiting...")
        individual_stage.setObjectName("thumbnail_individual_stage")
        layout.addWidget(individual_stage)

        # Batch progress (shown in THUMBNAIL_ONLY mode)
        batch_label = QLabel("Batch Progress:")
        batch_label.setObjectName("thumbnail_batch_label")
        layout.addWidget(batch_label)

        batch_progress = QProgressBar()
        batch_progress.setRange(0, 100)
        batch_progress.setValue(0)
        batch_progress.setObjectName("thumbnail_batch_progress")
        layout.addWidget(batch_progress)

        section.setLayout(layout)
        return section

    def _configure_for_mode(self) -> None:
        """Show/hide components based on operation mode."""
        # Configure stage visibility
        self.stage_sections["validation"].setVisible(self.config.show_validation)
        self.stage_sections["hashing"].setVisible(self.config.show_hashing)
        self.stage_sections["thumbnails"].setVisible(self.config.show_thumbnails)
        self.stage_sections["analysis"].setVisible(self.config.show_analysis)

        # Configure batch progress visibility (only in THUMBNAIL_ONLY mode)
        if self.mode == ProgressWindowMode.THUMBNAIL_ONLY:
            # Show batch progress
            batch_label = self.stage_sections["thumbnails"].findChild(
                QLabel, "thumbnail_batch_label"
            )
            batch_progress = self.stage_sections["thumbnails"].findChild(
                QProgressBar, "thumbnail_batch_progress"
            )
            if batch_label:
                batch_label.setVisible(True)
            if batch_progress:
                batch_progress.setVisible(True)
        else:
            # Hide batch progress in IMPORT mode
            batch_label = self.stage_sections["thumbnails"].findChild(
                QLabel, "thumbnail_batch_label"
            )
            batch_progress = self.stage_sections["thumbnails"].findChild(
                QProgressBar, "thumbnail_batch_progress"
            )
            if batch_label:
                batch_label.setVisible(False)
            if batch_progress:
                batch_progress.setVisible(False)

        self.logger.debug("Configured for mode: %s", self.mode.value)

    def _update_time_display(self) -> None:
        """Update elapsed and remaining time display."""
        if self.is_completed or self.is_cancelled:
            self.time_update_timer.stop()
            return

        # Calculate elapsed time
        elapsed = time.time() - self.operation_start_time
        self.overall_progress.elapsed_time = elapsed

        # Calculate remaining time
        self.overall_progress.calculate_remaining_time()

        # Update display
        elapsed_str = self.overall_progress.get_elapsed_time_formatted()
        remaining_str = self.overall_progress.get_remaining_time_formatted()

        if self.is_paused:
            self.time_label.setText(f"Elapsed: {elapsed_str} | Paused")
        else:
            self.time_label.setText(
                f"Elapsed: {elapsed_str} | Remaining: ~{remaining_str}"
            )

    def _on_pause_resume_clicked(self) -> None:
        """Handle pause/resume button click."""
        if self.is_paused:
            self.is_paused = False
            self.pause_button.setText("Pause")
            self.operation_resumed.emit()
            self.logger.info("Operation resumed by user")
        else:
            self.is_paused = True
            self.pause_button.setText("Resume")
            self.operation_paused.emit()
            self.logger.info("Operation paused by user")

    def _on_cancel_clicked(self) -> None:
        """Handle cancel button click."""
        reply = QMessageBox.question(
            self,
            "Cancel Operation?",
            f"Are you sure you want to cancel?\n\n"
            f"Completed: {self.overall_progress.items_completed} of {self.total_items}\n"
            f"Remaining: {self.total_items - self.overall_progress.items_completed}\n\n"
            f"This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.is_cancelled = True
            self.operation_cancelled.emit()
            self.logger.info("Operation cancelled by user")
            self.cancel_button.setEnabled(False)
            self.pause_button.setEnabled(False)

    def _on_minimize_clicked(self) -> None:
        """Handle minimize to background button click."""
        self.hide()
        self.logger.info("Window minimized to background")

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event with warning if operation in progress."""
        if self.is_completed or self.is_cancelled:
            self._save_window_state()
            event.accept()
            return

        # Show warning dialog
        reply = QMessageBox.question(
            self,
            "Stop Operation?",
            f"Operation is in progress.\n\n"
            f"Completed: {self.overall_progress.items_completed} of {self.total_items}\n"
            f"Remaining: {self.total_items - self.overall_progress.items_completed}\n\n"
            f"What would you like to do?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Stop generation
            self.is_cancelled = True
            self.operation_cancelled.emit()
            self._save_window_state()
            event.accept()
            self.logger.info("Operation stopped via close event")
        elif reply == QMessageBox.StandardButton.No:
            # Continue in background
            self.hide()
            event.ignore()
            self.logger.info("Window closed, continuing in background")
        else:
            # Cancel close
            event.ignore()

    def _save_window_state(self) -> None:
        """Save window position and size to settings."""
        settings = QSettings("DigitalWorkshop", "UnifiedProgressWindow")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("mode", self.mode.value)
        self.logger.debug("Window state saved")

    def _restore_window_state(self) -> None:
        """Restore window position and size from settings."""
        settings = QSettings("DigitalWorkshop", "UnifiedProgressWindow")
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
            self.logger.debug("Window state restored")

    def update_overall_progress(self, percent: int, message: str = "") -> None:
        """
        Update overall progress.

        Args:
            percent: Progress percentage (0-100)
            message: Optional status message
        """
        self.overall_progress.overall_percent = percent
        if self.overall_progress_bar:
            self.overall_progress_bar.setValue(percent)
        if self.overall_label and message:
            self.overall_label.setText(message)

    def update_stage_progress(
        self, stage_name: str, status: StageStatus, percent: int = 0, message: str = ""
    ) -> None:
        """
        Update progress for a specific stage.

        Args:
            stage_name: Name of the stage (validation, hashing, thumbnails, analysis)
            status: Current status of the stage
            percent: Progress percentage (0-100)
            message: Status message
        """
        # Update stage progress tracking
        if stage_name not in self.stage_progress:
            self.stage_progress[stage_name] = StageProgress(name=stage_name)

        stage = self.stage_progress[stage_name]
        stage.status = status
        stage.progress_percent = percent
        stage.message = message

        if status == StageStatus.IN_PROGRESS and stage.start_time is None:
            stage.start_time = time.time()
        elif status in (
            StageStatus.COMPLETED,
            StageStatus.FAILED,
            StageStatus.CANCELLED,
        ):
            stage.end_time = time.time()

        # Update UI
        section = self.stage_sections.get(stage_name.lower())
        if section and section.isVisible():
            status_label = section.findChild(QLabel, f"{stage_name.lower()}_status")
            progress_bar = section.findChild(
                QProgressBar, f"{stage_name.lower()}_progress"
            )

            if status_label:
                icon = stage.get_status_icon()
                status_label.setText(f"{icon} {message}")

            if progress_bar:
                progress_bar.setValue(percent)

    def update_thumbnail_progress(
        self,
        current_index: int,
        total_count: int,
        current_file: str,
        individual_percent: int,
        individual_stage: str,
    ) -> None:
        """
        Update thumbnail generation progress.

        Args:
            current_index: Current thumbnail index (1-based)
            total_count: Total number of thumbnails
            current_file: Name of current file being processed
            individual_percent: Progress of current thumbnail (0-100)
            individual_stage: Current stage (loading, material, rendering, etc.)
        """
        self.thumbnail_progress.current_index = current_index
        self.thumbnail_progress.total_count = total_count
        self.thumbnail_progress.current_file = current_file
        self.thumbnail_progress.individual_percent = individual_percent
        self.thumbnail_progress.individual_stage = individual_stage
        self.thumbnail_progress.batch_percent = int(
            (current_index / total_count) * 100 if total_count > 0 else 0
        )

        # Update completed count
        self.overall_progress.items_completed = current_index - 1

        # Update UI
        section = self.stage_sections.get("thumbnails")
        if section and section.isVisible():
            current_label = section.findChild(QLabel, "thumbnail_current_label")
            individual_progress = section.findChild(
                QProgressBar, "thumbnail_individual_progress"
            )
            individual_stage_label = section.findChild(
                QLabel, "thumbnail_individual_stage"
            )
            batch_progress = section.findChild(QProgressBar, "thumbnail_batch_progress")

            if current_label:
                current_label.setText(
                    f"Current: {current_file} ({current_index}/{total_count})"
                )

            if individual_progress:
                individual_progress.setValue(individual_percent)

            if individual_stage_label:
                individual_stage_label.setText(f"Stage: {individual_stage}")

            if batch_progress and batch_progress.isVisible():
                batch_progress.setValue(self.thumbnail_progress.batch_percent)

    def mark_item_completed(self, success: bool = True) -> None:
        """
        Mark an item as completed.

        Args:
            success: Whether the item completed successfully
        """
        if success:
            self.overall_progress.items_completed += 1
        else:
            self.overall_progress.items_failed += 1

    def mark_operation_completed(self) -> None:
        """Mark the entire operation as completed."""
        self.is_completed = True
        self.time_update_timer.stop()
        self.pause_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.operation_completed.emit()
        self.logger.info("Operation completed")

    def connect_worker_signals(self, worker) -> None:
        """
        Connect to worker signals based on operation mode.

        Args:
            worker: Worker thread object (ImportWorker or ThumbnailGenerationWorker)
        """
        # This will be implemented based on specific worker types
        # For now, it's a placeholder that subclasses or callers can override
        self.logger.info("Worker signals connected for mode: %s", self.mode.value)
