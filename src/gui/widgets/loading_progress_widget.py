"""
Loading Progress Widget for background loading operations.

This module provides a custom progress bar widget with integrated cancellation
support for background loading operations in the 3D Model Manager.
"""

import logging
from typing import Optional
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QTimer, QSize
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
)

from src.core.logging_config import get_logger


class LoadingProgressWidget(QWidget):
    """
    Custom progress bar widget with integrated cancel button for background loading.

    This widget displays loading progress, status messages, file names, and provides
    cancellation support for background loading operations.
    """

    # Signals
    cancel_requested = Signal()  # Emitted when user clicks cancel button

    def __init__(self, parent: Optional[QWidget] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize the loading progress widget.

        Args:
            parent: Parent widget
            logger: Optional logger instance
        """
        super().__init__(parent)
        self.logger = logger or get_logger(__name__)

        # State variables
        self.current_job_id = None
        self.is_loading = False
        self.start_time = 0
        self.estimated_total_time = 0
        self.last_progress_update = 0

        # UI components
        self._setup_ui()
        self._connect_signals()

        self.logger.debug("LoadingProgressWidget initialized")

    def _setup_ui(self) -> None:
        """Set up the widget's user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(2)

        # Top row: Progress bar and cancel button
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(5)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumWidth(200)
        self.progress_bar.setMaximumHeight(20)
        progress_layout.addWidget(self.progress_bar)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedSize(60, 20)
        self.cancel_button.setToolTip("Cancel loading operation")
        progress_layout.addWidget(self.cancel_button)

        layout.addLayout(progress_layout)

        # Bottom row: Status information
        info_layout = QHBoxLayout()
        info_layout.setSpacing(10)

        # Status label (shows current operation)
        self.status_label = QLabel("Ready")
        self.status_label.setMinimumWidth(150)
        info_layout.addWidget(self.status_label)

        # File name label
        self.file_label = QLabel("")
        self.file_label.setMinimumWidth(100)
        font = self.file_label.font()
        font.setItalic(True)
        self.file_label.setFont(font)
        info_layout.addWidget(self.file_label)

        # Time remaining label
        self.time_label = QLabel("")
        self.time_label.setMinimumWidth(80)
        self.time_label.setAlignment(Qt.AlignRight)
        info_layout.addWidget(self.time_label)

        # Add stretch to push items to the left
        info_layout.addStretch()

        layout.addLayout(info_layout)

        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMaximumHeight(50)

        # Initially hide the widget
        self.setVisible(False)

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        self.cancel_button.clicked.connect(self._on_cancel_clicked)

    def start_loading(
        self, job_id: str, file_path: str, initial_message: str = "Initializing..."
    ) -> None:
        """
        Start displaying loading progress for a job.

        Args:
            job_id: Unique identifier for the loading job
            file_path: Path to the file being loaded
            initial_message: Initial status message
        """
        try:
            self.current_job_id = job_id
            self.is_loading = True
            self.start_time = self._get_current_time()
            self.last_progress_update = self.start_time
            self.estimated_total_time = 0

            # Update UI
            self.progress_bar.setValue(0)
            self.progress_bar.setRange(0, 100)

            # Set file name (just filename, not full path)
            file_name = Path(file_path).name if file_path else "Unknown"
            self.file_label.setText(file_name)

            self.status_label.setText(initial_message)
            self.time_label.setText("")

            # Enable cancel button
            self.cancel_button.setEnabled(True)
            self.cancel_button.setText("Cancel")

            # Show the widget
            self.setVisible(True)

            self.logger.debug("Started loading display for job %s: {file_path}", job_id)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to start loading display: %s", e)

    def update_progress(self, progress: float, message: str) -> None:
        """
        Update loading progress with smooth animation.

        Args:
            progress: Progress percentage (0-100)
            message: Status message
        """
        try:
            if not self.is_loading:
                return

            current_time = self._get_current_time()

            # Smooth progress bar updates to prevent jerky movement
            current_value = self.progress_bar.value()
            target_value = int(progress)

            # Only update if there's a meaningful change (>0.5%) or significant time has passed
            time_since_last_update = current_time - self.last_progress_update
            progress_diff = abs(target_value - current_value)

            if progress_diff >= 0.5 or time_since_last_update >= 0.1:  # Update every 100ms minimum
                # Smooth transition for small changes
                if progress_diff <= 5.0 and time_since_last_update < 0.5:
                    # Animate small changes smoothly
                    self._animate_progress(current_value, target_value)
                else:
                    # Direct update for larger changes
                    self.progress_bar.setValue(target_value)

            # Update status message
            self.status_label.setText(message)

            # Estimate time remaining
            self._update_time_estimate(current_time, progress)

            self.last_progress_update = current_time

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to update progress: %s", e)

    def _animate_progress(self, from_value: int, to_value: int) -> None:
        """
        Animate progress bar changes for smooth visual feedback.

        Args:
            from_value: Starting progress value
            to_value: Target progress value
        """
        try:
            # Use QTimer for smooth animation
            steps = max(1, abs(to_value - from_value) // 2)  # 2-3 steps for small changes
            step_size = (to_value - from_value) / steps

            def animate_step(current_step: int = 0):
                if current_step >= steps:
                    self.progress_bar.setValue(to_value)
                    return

                intermediate_value = int(from_value + step_size * (current_step + 1))
                self.progress_bar.setValue(intermediate_value)

                # Schedule next step
                QTimer.singleShot(20, lambda: animate_step(current_step + 1))  # 20ms intervals

            animate_step()

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            # Fallback to direct update if animation fails
            self.logger.debug("Progress animation failed, using direct update: %s", e)
            self.progress_bar.setValue(to_value)

    def finish_loading(self, success: bool = True, final_message: str = "Completed") -> None:
        """
        Finish loading operation.

        Args:
            success: Whether loading completed successfully
            final_message: Final status message
        """
        try:
            self.is_loading = False

            if success:
                self.progress_bar.setValue(100)
                self.status_label.setText(final_message)
                self.time_label.setText("Done")
                self.cancel_button.setEnabled(False)
                self.cancel_button.setText("Done")
            else:
                self.status_label.setText(final_message)
                self.time_label.setText("Failed")
                self.cancel_button.setEnabled(False)
                self.cancel_button.setText("Failed")

            # Keep widget visible briefly, then hide
            QTimer.singleShot(3000, self._hide_widget)

            self.logger.debug("Finished loading display for job %s", self.current_job_id)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to finish loading display: %s", e)

    def cancel_loading(self) -> None:
        """Cancel the current loading operation."""
        try:
            if not self.is_loading:
                return

            self.is_loading = False
            self.status_label.setText("Cancelling...")
            self.time_label.setText("")
            self.cancel_button.setEnabled(False)
            self.cancel_button.setText("Cancelling...")

            # Emit cancel signal
            self.cancel_requested.emit()

            self.logger.debug("Cancelled loading for job %s", self.current_job_id)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to cancel loading: %s", e)

    def _update_time_estimate(self, current_time: float, progress: float) -> None:
        """
        Update time remaining estimate.

        Args:
            current_time: Current timestamp
            progress: Current progress percentage
        """
        try:
            if progress <= 0:
                self.time_label.setText("")
                return

            elapsed = current_time - self.start_time

            if elapsed > 0 and progress > 0:
                # Estimate total time based on current progress
                estimated_total = elapsed / (progress / 100.0)
                remaining = estimated_total - elapsed

                if remaining > 0:
                    if remaining < 60:
                        self.time_label.setText(f"{remaining:.1f}s left")
                    elif remaining < 3600:
                        minutes = int(remaining // 60)
                        seconds = int(remaining % 60)
                        self.time_label.setText(f"{minutes}:{seconds:02d} left")
                    else:
                        hours = int(remaining // 3600)
                        minutes = int((remaining % 3600) // 60)
                        self.time_label.setText(f"{hours}:{minutes:02d} left")
                else:
                    self.time_label.setText("Finishing...")
            else:
                self.time_label.setText("")

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.debug("Failed to update time estimate: %s", e)
            self.time_label.setText("")

    def _on_cancel_clicked(self) -> None:
        """Handle cancel button click."""
        if self.is_loading:
            self.cancel_loading()

    def _hide_widget(self) -> None:
        """Hide the widget after completion."""
        try:
            self.setVisible(False)
            self.current_job_id = None
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to hide widget: %s", e)

    def _get_current_time(self) -> float:
        """Get current time in seconds."""
        import time

        return time.time()

    def sizeHint(self) -> QSize:
        """Return preferred size for the widget."""
        return QSize(400, 50)

    def minimumSizeHint(self) -> QSize:
        """Return minimum size for the widget."""
        return QSize(300, 40)
