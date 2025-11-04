"""
UI service implementation for managing user interface state, progress, and notifications.
"""

import time
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
    QProgressBar,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QGraphicsDropShadowEffect,
)

from src.core.logging_config import get_logger
from .gui_service_interfaces import (
    IViewerUIService,
    ProgressInfo,
    UIState,
    INotificationService,
)


@dataclass
class Notification:
    """Notification data structure."""

    id: str
    title: str
    message: str
    type: str
    timestamp: float
    duration_ms: int
    auto_hide: bool = True


class NotificationType(Enum):
    """Notification types."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class NotificationWidget(QWidget):
    """Widget for displaying notifications."""

    def __init__(self, notification: Notification, parent=None):
        """
        Initialize notification widget.

        Args:
            notification: Notification data
            parent: Parent widget
        """
        super().__init__(parent)
        self.notification = notification
        self.logger = get_logger(__name__)

        self.setFixedWidth(350)
        self.setFixedHeight(80)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._setup_ui()
        self._apply_styling()

        # Auto-hide timer
        if notification.auto_hide:
            self.hide_timer = QTimer()
            self.hide_timer.timeout.connect(self.hide)
            self.hide_timer.start(notification.duration_ms)

    def _setup_ui(self) -> None:
        """Setup the notification UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)

        # Title
        self.title_label = QLabel(self.notification.title)
        self.title_label.setObjectName("notificationTitle")

        # Message
        self.message_label = QLabel(self.notification.message)
        self.message_label.setObjectName("notificationMessage")
        self.message_label.setWordWrap(True)
        self.message_label.setMaximumHeight(40)

        layout.addWidget(self.title_label)
        layout.addWidget(self.message_label)

    def _apply_styling(self) -> None:
        """Apply styling based on notification type."""
        # Try to get theme colors, fallback to defaults if theme system unavailable
        try:
            from src.gui.theme import COLORS

            type_colors = {
                NotificationType.INFO: COLORS.info,
                NotificationType.WARNING: COLORS.warning,
                NotificationType.ERROR: COLORS.error,
                NotificationType.SUCCESS: COLORS.success,
            }
            shadow_color = COLORS.shadow
            text_color = COLORS.notification_text
        except (ImportError, AttributeError):
            # Fallback to hardcoded colors if theme system unavailable
            type_colors = {
                NotificationType.INFO: "#2196F3",
                NotificationType.WARNING: "#FF9800",
                NotificationType.ERROR: "#F44336",
                NotificationType.SUCCESS: "#4CAF50",
            }
            shadow_color = "#000000"
            text_color = "white"

        color = type_colors.get(
            NotificationType(self.notification.type), type_colors[NotificationType.INFO]
        )

        self.setStyleSheet(
            f"""
            NotificationWidget {{
                background-color: {color};
                border-radius: 8px;
                border: 1px solid {color};
            }}
            #notificationTitle {{
                color: {text_color};
                font-weight: bold;
                font-size: 14px;
            }}
            #notificationMessage {{
                color: {text_color};
                font-size: 12px;
            }}
        """
        )

        # Add drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(shadow_color)
        shadow.setOffset(2, 2)
        self.setGraphicsEffect(shadow)


class ProgressWidget(QWidget):
    """Widget for displaying progress information."""

    def __init__(self, parent=None):
        """
        Initialize progress widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.logger = get_logger(__name__)

        self.setFixedHeight(60)
        self.setVisible(False)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the progress UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        # Message label
        self.message_label = QLabel()
        self.message_label.setVisible(False)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)

        layout.addWidget(self.progress_bar, 1)
        layout.addWidget(self.message_label, 2)
        layout.addWidget(self.cancel_button)

    def show_progress(self, progress: ProgressInfo) -> None:
        """Show progress information."""
        try:
            self.progress_bar.setVisible(True)
            self.message_label.setVisible(True)

            self.progress_bar.setRange(0, int(progress.total))
            self.progress_bar.setValue(int(progress.current))
            self.message_label.setText(progress.message)

            self.setVisible(True)

        except Exception as e:
            self.logger.error(f"Error showing progress: {e}")

    def hide_progress(self) -> None:
        """Hide progress information."""
        self.setVisible(False)
        self.progress_bar.setVisible(False)
        self.message_label.setVisible(False)

    def enable_cancellation(self, enabled: bool) -> None:
        """Enable or disable cancellation."""
        self.cancel_button.setVisible(enabled)

    def _on_cancel_clicked(self) -> None:
        """Handle cancel button click."""
        # Emit signal that would be connected to cancellation handler
        self.logger.info("Cancellation requested by user")

    def set_message(self, message: str) -> None:
        """Set progress message."""
        self.message_label.setText(message)


class ViewerUIService(IViewerUIService):
    """Implementation of viewer UI service."""

    def __init__(self, parent_widget: QWidget):
        """
        Initialize viewer UI service.

        Args:
            parent_widget: Parent widget for UI components
        """
        super().__init__()
        self.parent_widget = parent_widget
        self.logger = get_logger(__name__)

        # State management
        self.current_state = UIState.READY
        self.cancellation_enabled = False
        self.cancellation_requested = False

        # UI components
        self.progress_widget: Optional[ProgressWidget] = None
        self.notification_widgets: Dict[str, NotificationWidget] = {}

        # Setup UI components
        self._setup_ui_components()

        self.logger.info("Viewer UI service initialized")

    def _setup_ui_components(self) -> None:
        """Setup UI components."""
        try:
            # Create progress widget
            self.progress_widget = ProgressWidget(self.parent_widget)

            # Position progress widget at bottom of parent
            if hasattr(self.parent_widget, "layout"):
                self.parent_widget.layout().addWidget(self.progress_widget)

        except Exception as e:
            self.logger.error(f"Error setting up UI components: {e}")

    def set_ui_state(self, state: UIState, message: str = "") -> None:
        """Set the current UI state."""
        try:
            old_state = self.current_state
            self.current_state = state

            # Update UI based on state
            self._update_ui_for_state(state, message)

            self.logger.debug(f"UI state changed: {old_state.value} -> {state.value}")

        except Exception as e:
            self.logger.error(f"Error setting UI state: {e}")

    def _update_ui_for_state(self, state: UIState, message: str) -> None:
        """Update UI based on current state."""
        try:
            # Update cursor
            if state == UIState.LOADING or state == UIState.PROCESSING:
                QApplication.setOverrideCursor(Qt.WaitCursor)
            else:
                QApplication.restoreOverrideCursor()

            # Update status message if available
            if hasattr(self.parent_widget, "statusBar") and message:
                self.parent_widget.statusBar().showMessage(message)

            # Update progress visibility
            if state == UIState.LOADING:
                if self.progress_widget:
                    self.progress_widget.setVisible(True)
            else:
                if self.progress_widget:
                    self.progress_widget.hide_progress()

        except Exception as e:
            self.logger.error(f"Error updating UI for state: {e}")

    def get_ui_state(self) -> UIState:
        """Get current UI state."""
        return self.current_state

    def show_progress(self, progress: ProgressInfo) -> None:
        """Show progress information to user."""
        try:
            if self.progress_widget:
                self.progress_widget.show_progress(progress)
        except Exception as e:
            self.logger.error(f"Error showing progress: {e}")

    def hide_progress(self) -> None:
        """Hide progress indicator."""
        try:
            if self.progress_widget:
                self.progress_widget.hide_progress()
        except Exception as e:
            self.logger.error(f"Error hiding progress: {e}")

    def enable_cancellation(self, cancellable: bool) -> None:
        """Enable or disable operation cancellation."""
        self.cancellation_enabled = cancellable
        try:
            if self.progress_widget:
                self.progress_widget.enable_cancellation(cancellable)
        except Exception as e:
            self.logger.error(f"Error enabling cancellation: {e}")

    def is_cancellation_requested(self) -> bool:
        """Check if user requested cancellation."""
        return self.cancellation_requested

    def reset_cancellation(self) -> None:
        """Reset cancellation request flag."""
        self.cancellation_requested = False

    def show_error(self, title: str, message: str, details: str = "") -> None:
        """Show error dialog to user."""
        try:
            # Show dialog
            msg_box = QMessageBox(self.parent_widget)
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            if details:
                msg_box.setDetailedText(details)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()

            # Also show as notification
            self._show_notification(title, message, NotificationType.ERROR)

            self.logger.error(f"Error shown to user: {title} - {message}")

        except Exception as e:
            self.logger.error(f"Error showing error dialog: {e}")

    def show_warning(self, title: str, message: str) -> None:
        """Show warning dialog to user."""
        try:
            msg_box = QMessageBox(self.parent_widget)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()

            # Also show as notification
            self._show_notification(title, message, NotificationType.WARNING)

            self.logger.warning(f"Warning shown to user: {title} - {message}")

        except Exception as e:
            self.logger.error(f"Error showing warning dialog: {e}")

    def show_info(self, title: str, message: str) -> None:
        """Show information dialog to user."""
        try:
            msg_box = QMessageBox(self.parent_widget)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()

            # Also show as notification
            self._show_notification(title, message, NotificationType.INFO)

            self.logger.info(f"Info shown to user: {title} - {message}")

        except Exception as e:
            self.logger.error(f"Error showing info dialog: {e}")

    def _show_notification(
        self, title: str, message: str, notification_type: NotificationType
    ) -> None:
        """Show a notification widget."""
        try:
            notification = Notification(
                id=f"notification_{int(time.time() * 1000)}",
                title=title,
                message=message,
                type=notification_type.value,
                timestamp=time.time(),
                duration_ms=5000,
                auto_hide=True,
            )

            widget = NotificationWidget(notification, self.parent_widget)

            # Position widget (top-right corner)
            if hasattr(self.parent_widget, "geometry"):
                parent_rect = self.parent_widget.geometry()
                x = parent_rect.right() - widget.width() - 20
                y = parent_rect.top() + 20
                widget.move(x, y)

            widget.show()

            # Store reference and auto-remove
            self.notification_widgets[notification.id] = widget

            # Auto-remove after duration
            if notification.auto_hide:
                QTimer.singleShot(
                    notification.duration_ms,
                    lambda: self._remove_notification(notification.id),
                )

        except Exception as e:
            self.logger.error(f"Error showing notification: {e}")

    def _remove_notification(self, notification_id: str) -> None:
        """Remove a notification widget."""
        try:
            if notification_id in self.notification_widgets:
                widget = self.notification_widgets[notification_id]
                widget.hide()
                widget.deleteLater()
                del self.notification_widgets[notification_id]
        except Exception as e:
            self.logger.error(f"Error removing notification: {e}")


class NotificationService(INotificationService):
    """Implementation of notification service."""

    def __init__(self, parent_widget: QWidget):
        """
        Initialize notification service.

        Args:
            parent_widget: Parent widget for notifications
        """
        super().__init__()
        self.parent_widget = parent_widget
        self.logger = get_logger(__name__)
        self.notifications_enabled = True
        self.active_notifications: Dict[str, NotificationWidget] = {}

        self.logger.info("Notification service initialized")

    def show_notification(
        self,
        title: str,
        message: str,
        notification_type: str = "info",
        duration_ms: int = 5000,
    ) -> str:
        """Show a notification to the user."""
        if not self.notifications_enabled:
            return ""

        try:
            notification = Notification(
                id=f"notification_{int(time.time() * 1000)}",
                title=title,
                message=message,
                type=notification_type,
                timestamp=time.time(),
                duration_ms=duration_ms,
                auto_hide=True,
            )

            widget = NotificationWidget(notification, self.parent_widget)

            # Position widget (stack from top-right)
            self._position_notification(widget)

            widget.show()
            self.active_notifications[notification.id] = widget

            # Auto-remove after duration
            if duration_ms > 0:
                QTimer.singleShot(duration_ms, lambda: self.hide_notification(notification.id))

            self.logger.debug(f"Notification shown: {title}")
            return notification.id

        except Exception as e:
            self.logger.error(f"Error showing notification: {e}")
            return ""

    def _position_notification(self, widget: NotificationWidget) -> None:
        """Position notification widget."""
        try:
            if hasattr(self.parent_widget, "geometry"):
                parent_rect = self.parent_widget.geometry()
                x = parent_rect.right() - widget.width() - 20

                # Stack notifications vertically
                y_offset = 20
                for existing_widget in self.active_notifications.values():
                    if existing_widget.isVisible():
                        y_offset += existing_widget.height() + 10

                y = parent_rect.top() + y_offset
                widget.move(x, y)
        except Exception as e:
            self.logger.error(f"Error positioning notification: {e}")

    def hide_notification(self, notification_id: str) -> bool:
        """Hide a specific notification."""
        try:
            if notification_id in self.active_notifications:
                widget = self.active_notifications[notification_id]
                widget.hide()
                widget.deleteLater()
                del self.active_notifications[notification_id]
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error hiding notification: {e}")
            return False

    def clear_all_notifications(self) -> None:
        """Clear all active notifications."""
        try:
            for notification_id in list(self.active_notifications.keys()):
                self.hide_notification(notification_id)
            self.logger.info("All notifications cleared")
        except Exception as e:
            self.logger.error(f"Error clearing notifications: {e}")

    def set_notification_enabled(self, enabled: bool) -> None:
        """Enable or disable notifications globally."""
        self.notifications_enabled = enabled
        if not enabled:
            self.clear_all_notifications()
        self.logger.info(f"Notifications {'enabled' if enabled else 'disabled'}")
