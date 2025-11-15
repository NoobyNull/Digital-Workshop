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
from src.gui.theme import (
    MIN_WIDGET_SIZE,
    SPACING_8,
    SPACING_12,
    SPACING_16,
    COLORS,
)

# Import QSS helpers from the facade module
try:
    from src.gui.theme import qss_button_base, qss_progress_bar
except ImportError:
    # Fallback: create simple QSS functions
    def qss_button_base() -> str:
        """Fallback button styling."""
        return (
            f"QPushButton {{ background-color: {COLORS.surface}; "
            f"color: {COLORS.text}; border: 1px solid {COLORS.border}; "
            f"padding: 6px 12px; border-radius: 2px; }}"
        )

    def qss_progress_bar() -> str:
        """Fallback progress bar styling."""
        return (
            f"QProgressBar {{ border: 1px solid {COLORS.border}; "
            f"border-radius: 2px; background-color: {COLORS.window_bg}; "
            f"color: {COLORS.text}; }} "
            f"QProgressBar::chunk {{ background-color: {COLORS.progress_chunk}; }}"
        )


class ThumbnailGenerationWindow(QMainWindow):
    """
    Dedicated window for non-blocking thumbnail generation.

    Features:
    - Separate QMainWindow (not modal)
    - Dual progress indicators (batch + individual)
    - Live VTK preview panel
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

        # Timer for time updates
        self.time_update_timer = QTimer(self)
        self.time_update_timer.timeout.connect(self._update_time_display)
        self.time_update_timer.start(1000)

        # UI components
        self.batch_progress_bar: Optional[QProgressBar] = None
        self.individual_progress_bar: Optional[QProgressBar] = None
        self.batch_label: Optional[QLabel] = None
        self.individual_label: Optional[QLabel] = None
        self.stage_label: Optional[QLabel] = None
        self.time_label: Optional[QLabel] = None
        self.pause_button: Optional[QPushButton] = None
        self.cancel_button: Optional[QPushButton] = None
        self.preview_label: Optional[QLabel] = None
        self.preview_widget: Optional[QWidget] = None

        # Setup UI
        self._setup_ui()
        self._restore_window_state()

        self.logger.info("ThumbnailGenerationWindow initialized: total_items=%d", total_items)

    def _setup_ui(self) -> None:
        """Create all UI components."""
        self.setWindowTitle("Thumbnail Generation")
        self.setMinimumSize(900, 600)
        self.setWindowModality(Qt.WindowModality.NonModal)

        # Apply comprehensive theme styling
        self.setStyleSheet(
            f"""
            QMainWindow {{
                background-color: {COLORS.window_bg};
                color: {COLORS.text};
            }}
            QWidget {{
                background-color: {COLORS.window_bg};
                color: {COLORS.text};
            }}
            QGroupBox {{
                background-color: {COLORS.surface};
                border: 1px solid {COLORS.border};
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 4px 8px;
                color: {COLORS.text};
            }}
            QLabel {{
                color: {COLORS.text};
                background-color: transparent;
            }}
            """
        )

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

        # Batch progress section
        batch_section = self._create_batch_progress_section()
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
        warning_label.setStyleSheet(
            f"color: {COLORS.warning}; padding: {SPACING_8}px; "
            f"background-color: {COLORS.surface}; border-radius: 2px;"
        )
        left_layout.addWidget(warning_label)

        # Control buttons
        button_layout = self._create_button_layout()
        left_layout.addLayout(button_layout)

        left_layout.addStretch()

        # Add left panel to main layout
        main_layout.addWidget(left_panel, stretch=1)

        # Right side: VTK Preview
        preview_panel = self._create_preview_panel()
        main_layout.addWidget(preview_panel, stretch=2)

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
        self.batch_progress_bar.setStyleSheet(qss_progress_bar())
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
        self.individual_progress_bar.setStyleSheet(qss_progress_bar())
        layout.addWidget(self.individual_progress_bar)

        self.stage_label = QLabel("Stage: Waiting...")
        self.stage_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        font = QFont()
        font.setPointSize(8)
        self.stage_label.setFont(font)
        layout.addWidget(self.stage_label)

        section.setLayout(layout)
        return section

    def _create_preview_panel(self) -> QGroupBox:
        """Create VTK preview panel."""
        section = QGroupBox("Model Preview")
        layout = QVBoxLayout()

        # Preview label showing current file
        self.preview_label = QLabel("Waiting for model...")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setWordWrap(True)
        preview_font = QFont()
        preview_font.setPointSize(9)
        self.preview_label.setFont(preview_font)
        layout.addWidget(self.preview_label)

        # Placeholder for VTK preview (will be populated when rendering)
        self.preview_widget = QLabel("Preview will appear here during rendering")
        self.preview_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_widget.setMinimumSize(400, 400)
        self.preview_widget.setStyleSheet(
            f"QLabel {{ "
            f"background-color: {COLORS.surface_alt}; "
            f"border: 2px solid {COLORS.border}; "
            f"border-radius: 4px; "
            f"color: {COLORS.text_muted}; "
            f"}}"
        )
        layout.addWidget(self.preview_widget)

        section.setLayout(layout)
        return section

    def _create_button_layout(self) -> QHBoxLayout:
        """Create control button layout."""
        layout = QHBoxLayout()
        layout.setSpacing(SPACING_12)

        # Apply button styling
        button_style = qss_button_base()

        self.pause_button = QPushButton("Pause")
        self.pause_button.setMinimumWidth(100)
        self.pause_button.setMinimumHeight(MIN_WIDGET_SIZE)
        self.pause_button.setStyleSheet(button_style)
        self.pause_button.clicked.connect(self._on_pause_resume_clicked)
        layout.addWidget(self.pause_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumWidth(100)
        self.cancel_button.setMinimumHeight(MIN_WIDGET_SIZE)
        self.cancel_button.setStyleSheet(button_style)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        layout.addWidget(self.cancel_button)

        layout.addStretch()

        minimize_button = QPushButton("Minimize to Background")
        minimize_button.setMinimumWidth(180)
        minimize_button.setMinimumHeight(MIN_WIDGET_SIZE)
        minimize_button.setStyleSheet(button_style)
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
                self.time_label.setText(f"Elapsed: {elapsed_str} | Remaining: ~{remaining_str}")
            else:
                self.time_label.setText(f"Elapsed: {elapsed_str} | Remaining: Calculating...")

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
        """
        Update batch progress.

        Args:
            current: Current item index (1-based)
            total: Total items
        """
        self.current_index = current
        percent = int((current / total) * 100) if total > 0 else 0

        if self.batch_progress_bar:
            self.batch_progress_bar.setValue(percent)

        if self.batch_label:
            self.batch_label.setText(f"Batch: {current} of {total} images")

    def update_individual_progress(self, current_file: str, percent: int, stage: str) -> None:
        """
        Update individual image progress.

        Args:
            current_file: Name of current file
            percent: Progress percentage (0-100)
            stage: Current stage (loading, material, rendering, saving)
        """
        if self.individual_label:
            self.individual_label.setText(f"Current: {current_file}")

        if self.individual_progress_bar:
            self.individual_progress_bar.setValue(percent)

        if self.stage_label:
            self.stage_label.setText(f"Stage: {stage}")

        # Update preview label
        if self.preview_label:
            self.preview_label.setText(f"Rendering: {current_file}\n{stage}")

    def mark_operation_completed(self) -> None:
        """Mark the entire operation as completed."""
        self.is_completed = True
        self.time_update_timer.stop()
        self.pause_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.operation_completed.emit()
        self.logger.info("Thumbnail generation completed")

    def show_and_raise(self) -> None:
        """Show window and bring it to front."""
        self.show()
        self.raise_()
        self.activateWindow()
