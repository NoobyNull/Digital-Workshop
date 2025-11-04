"""Auto-closing message box with countdown timer."""

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QMessageBox


class AutoCloseMessageBox(QMessageBox):
    """Message box that automatically closes after a specified duration with countdown."""

    def __init__(self, title: str, message: str, parent=None, timeout_ms: int = 5000):
        """
        Initialize auto-closing message box.

        Args:
            title: Dialog title
            message: Dialog message
            parent: Parent widget
            timeout_ms: Time in milliseconds before auto-close (default: 5000ms = 5 seconds)
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.timeout_ms = timeout_ms
        self.remaining_ms = timeout_ms

        # Set message with countdown placeholder
        self.base_message = message
        self._update_message()

        # Set icon and buttons
        self.setIcon(QMessageBox.Information)
        self.setStandardButtons(QMessageBox.Ok)

        # Create timer for countdown
        self.timer = QTimer()
        self.timer.timeout.connect(self._on_timer_tick)
        self.timer.start(100)  # Update every 100ms for smooth countdown

    def _update_message(self) -> None:
        """Update message with current countdown."""
        seconds_remaining = max(0, self.remaining_ms // 1000)
        self.setText(
            f"{self.base_message}\n\nThis window will close in {seconds_remaining}s"
        )

    def _on_timer_tick(self) -> None:
        """Handle timer tick for countdown."""
        self.remaining_ms -= 100

        if self.remaining_ms <= 0:
            self.timer.stop()
            self.accept()
        else:
            self._update_message()

    def closeEvent(self, event) -> None:
        """Handle close event to stop timer."""
        self.timer.stop()
        super().closeEvent(event)


def show_auto_close_message(
    parent, title: str, message: str, timeout_ms: int = 5000
) -> None:
    """
    Show an auto-closing information message box.

    Args:
        parent: Parent widget
        title: Dialog title
        message: Dialog message
        timeout_ms: Time in milliseconds before auto-close (default: 5000ms = 5 seconds)

    Example:
        show_auto_close_message(self, "Success", "Folder added successfully!", 5000)
    """
    dialog = AutoCloseMessageBox(title, message, parent, timeout_ms)
    dialog.exec()
