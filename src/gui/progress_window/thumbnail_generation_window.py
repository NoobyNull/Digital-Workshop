"""
Specialized window for non-blocking thumbnail generation with live preview.

This module provides a dedicated QMainWindow for thumbnail generation that:
- Runs in a separate thread (non-blocking)
- Shows dual progress indicators (batch + individual)
- Displays live VTK preview of current model
- Provides clear warning on close
- Allows minimize to background
"""

import time
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QGroupBox,
    QMessageBox,
    QWidget,
)
from PySide6.QtCore import Qt, Signal, QTimer, QSettings
from PySide6.QtGui import QCloseEvent, QFont

from src.core.logging_config import get_logger
from src.gui.layout.flow_layout import FlowLayout
from src.gui.theme import (
    MIN_WIDGET_SIZE,
    SPACING_12,
    SPACING_16,
)


class ThumbnailGenerationWindow(QMainWindow):
    """Dedicated window for non-blocking thumbnail generation.

    Features:
    - Separate QMainWindow (not modal)
    - Dual progress indicators (batch + individual)
    - Clear close warning
    - Minimize to background
    - Window state persistence

    Signals:
        operation_paused: Emitted when user pauses
        operation_resumed: Emitted when user resumes
        operation_cancelled: Emitted when user cancels
        operation_completed: Emitted when operation completes
    """

    # Signals
    operation_paused = Signal()
    operation_resumed = Signal()
    operation_cancelled = Signal()
    operation_completed = Signal()

    def __init__(self, total_items: int, parent: Optional[QWidget] = None):
        """
        Initialize the thumbnail generation window.

        Args:
            total_items: Total number of thumbnails to generate
            parent: Parent widget
        """
        super().__init__(parent)
        self.logger = get_logger(__name__)

        # State
        self.total_items = total_items
        self.current_index = 0
        self.is_paused = False
        self.is_cancelled = False
        self.is_completed = False
        self.operation_start_time = time.time()

        # Timer for time updates (started lazily on first progress update)
        self.time_update_timer = QTimer(self)
        self.time_update_timer.setInterval(1000)
        self.time_update_timer.timeout.connect(self._update_time_display)

        # UI components
        self.batch_progress_bar: Optional[QProgressBar] = None
        self.individual_progress_bar: Optional[QProgressBar] = None
        self.batch_label: Optional[QLabel] = None
        self.individual_label: Optional[QLabel] = None
        self.stage_label: Optional[QLabel] = None
        self.time_label: Optional[QLabel] = None
        self.pause_button: Optional[QPushButton] = None
        self.cancel_button: Optional[QPushButton] = None

        # Setup UI
        self._setup_ui()
        self._restore_window_state()

        self.logger.info(
            "ThumbnailGenerationWindow initialized: total_items=%d", total_items
        )

    def _setup_ui(self) -> None:
        """Create all UI components."""
        self.setWindowTitle("Thumbnail Generation")
        self.setMinimumSize(900, 600)
        self.setWindowModality(Qt.WindowModality.NonModal)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(SPACING_12)
        main_layout.setContentsMargins(SPACING_16, SPACING_16, SPACING_16, SPACING_16)

        # Left side: Progress information
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(SPACING_12)

        # Batch progress section (or single-item progress)
        batch_section = self._create_batch_progress_section()
        if self.total_items == 1:
            batch_section.setTitle("Preview Progress")
            self.batch_label.setText("Generating preview image...")
        left_layout.addWidget(batch_section)

        # Individual progress section
        individual_section = self._create_individual_progress_section()
        left_layout.addWidget(individual_section)

        # Time display
        self.time_label = QLabel("Elapsed: 0s | Remaining: Calculating...")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(9)
        self.time_label.setFont(font)
        left_layout.addWidget(self.time_label)

        # Warning message
        warning_label = QLabel("⚠️  Closing this window will STOP thumbnail generation!")
        warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        warning_font = QFont()
        warning_font.setPointSize(9)
        warning_font.setBold(True)
        warning_label.setFont(warning_font)
        left_layout.addWidget(warning_label)

        # Control buttons
        button_layout = self._create_button_layout()
        left_layout.addLayout(button_layout)

        left_layout.addStretch()

        # Add left panel to main layout (full width; preview panel removed)
        main_layout.addWidget(left_panel, stretch=1)

        self.logger.debug("UI setup complete")

    def _create_batch_progress_section(self) -> QGroupBox:
        """Create batch progress section."""
        section = QGroupBox("Batch Progress")
        layout = QVBoxLayout()

        self.batch_label = QLabel("Starting...")
        self.batch_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.batch_label.setFont(font)
        layout.addWidget(self.batch_label)

        self.batch_progress_bar = QProgressBar()
        self.batch_progress_bar.setRange(0, 100)
        self.batch_progress_bar.setValue(0)
        self.batch_progress_bar.setMinimumHeight(30)
        self.batch_progress_bar.setTextVisible(True)
        self.batch_progress_bar.setFormat("%p%")
        layout.addWidget(self.batch_progress_bar)

        section.setLayout(layout)
        return section

    def _create_individual_progress_section(self) -> QGroupBox:
        """Create individual progress section."""
        section = QGroupBox("Current Image Progress")
        layout = QVBoxLayout()

        self.individual_label = QLabel("Waiting to start...")
        self.individual_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.individual_label)

        self.individual_progress_bar = QProgressBar()
        self.individual_progress_bar.setRange(0, 100)
        self.individual_progress_bar.setValue(0)
        self.individual_progress_bar.setMinimumHeight(25)
        self.individual_progress_bar.setTextVisible(True)
        self.individual_progress_bar.setFormat("%p%")
        layout.addWidget(self.individual_progress_bar)

        self.stage_label = QLabel("Stage: Waiting...")
        self.stage_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        font = QFont()
        font.setPointSize(8)
        self.stage_label.setFont(font)
        layout.addWidget(self.stage_label)

        section.setLayout(layout)
        return section

    def _create_button_layout(self) -> FlowLayout:
        """Create control button layout.

        Important: the FlowLayout must not be parented directly to a QWidget
        that already has its own layout (such as the main window or left
        panel), otherwise Qt will attempt to call setLayout() on that
        widget and emit warnings. We create it without a parent and let
        the containing layout take ownership via addLayout().
        """
        layout = FlowLayout()
        layout.setSpacing(SPACING_12)

        self.pause_button = QPushButton("Pause")
        self.pause_button.setMinimumWidth(100)
        self.pause_button.setMinimumHeight(MIN_WIDGET_SIZE)
        self.pause_button.clicked.connect(self._on_pause_resume_clicked)
        layout.addWidget(self.pause_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumWidth(100)
        self.cancel_button.setMinimumHeight(MIN_WIDGET_SIZE)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        layout.addWidget(self.cancel_button)

        minimize_button = QPushButton("Minimize to Background")
        minimize_button.setMinimumWidth(180)
        minimize_button.setMinimumHeight(MIN_WIDGET_SIZE)
        minimize_button.clicked.connect(self._on_minimize_clicked)
        layout.addWidget(minimize_button)

        return layout

    def _update_time_display(self) -> None:
        """Update elapsed and remaining time display."""
        if self.is_completed or self.is_cancelled:
            self.time_update_timer.stop()
            return

        elapsed = time.time() - self.operation_start_time
        elapsed_str = self._format_time(elapsed)

        if self.is_paused:
            self.time_label.setText(f"Elapsed: {elapsed_str} | Paused")
        else:
            # Calculate remaining time
            if self.current_index > 0:
                avg_time_per_item = elapsed / self.current_index
                remaining_items = self.total_items - self.current_index
                remaining_time = avg_time_per_item * remaining_items
                remaining_str = self._format_time(remaining_time)
                self.time_label.setText(
                    f"Elapsed: {elapsed_str} | Remaining: ~{remaining_str}"
                )
            else:
                self.time_label.setText(
                    f"Elapsed: {elapsed_str} | Remaining: Calculating..."
                )

    def _format_time(self, seconds: float) -> str:
        """Format seconds to human-readable time."""
        if seconds < 60:
            return f"{int(seconds)}s"
        if seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

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
            "Cancel Thumbnail Generation?",
            f"Are you sure you want to cancel?\n\n"
            f"Completed: {self.current_index} of {self.total_items}\n"
            f"Remaining: {self.total_items - self.current_index}\n\n"
            f"This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.is_cancelled = True
            self.operation_cancelled.emit()
            self.logger.info("Thumbnail generation cancelled by user")
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
            "Stop Thumbnail Generation?",
            f"Operation is in progress.\n\n"
            f"Completed: {self.current_index} of {self.total_items}\n"
            f"Remaining: {self.total_items - self.current_index}\n\n"
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
            self.logger.info("Thumbnail generation stopped via close event")
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
        settings = QSettings("DigitalWorkshop", "ThumbnailGenerationWindow")
        settings.setValue("geometry", self.saveGeometry())
        self.logger.debug("Window state saved")

    def _restore_window_state(self) -> None:
        """Restore window position and size from settings."""
        settings = QSettings("DigitalWorkshop", "ThumbnailGenerationWindow")
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
            self.logger.debug("Window state restored")

    def update_batch_progress(self, current: int, total: int) -> None:
        """Update batch progress and ensure the time display is active."""
        self.current_index = current
        percent = int((current / total) * 100) if total > 0 else 0

        if self.batch_progress_bar:
            self.batch_progress_bar.setValue(percent)

        if self.batch_label:
            self.batch_label.setText(f"Batch: {current} of {total} images")

        # Start timer lazily on first real progress update
        if not self.time_update_timer.isActive():
            self.time_update_timer.start()

    def update_individual_progress(
        self, current_file: str, percent: int, stage: str
    ) -> None:
        """Update individual image progress labels and progress bar."""
        if self.individual_label:
            self.individual_label.setText(f"Current: {current_file}")

        if self.individual_progress_bar:
            self.individual_progress_bar.setValue(percent)

        if self.stage_label:
            self.stage_label.setText(f"Stage: {stage}")

    def mark_operation_completed(self) -> None:
        """Mark the entire operation as completed."""
        self.is_completed = True
        self.time_update_timer.stop()
        self.pause_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.operation_completed.emit()
        self.logger.info("Thumbnail generation completed")

    def show_and_raise(self) -> None:
        """Show window and bring it to front and start timing."""
        self.show()
        self.raise_()
        self.activateWindow()

        # Start elapsed time tracking when the window becomes visible
        self.operation_start_time = time.time()
        if not self.time_update_timer.isActive():
            self.time_update_timer.start()
