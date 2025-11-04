"""
Deduplication status widget for status bar.

Shows hashing progress and duplicate count with clickable indicator.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton

# Import theme system for proper theming
try:
    from src.gui.theme import COLORS
    from src.gui.theme.simple_service import ThemeService
except ImportError:
    # Fallback if theme system is not available
    COLORS = None
    ThemeService = None

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class DeduplicationStatusWidget(QWidget):
    """Widget for displaying deduplication status in status bar."""

    duplicate_clicked = Signal()  # Emitted when duplicate indicator is clicked

    def __init__(self, parent=None) -> None:
        """
        Initialize deduplication status widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.duplicate_count = 0
        self.is_hashing = False

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup widget UI."""
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(5)

        # Hashing status label
        self.hash_label = QLabel("Hashing: 0%")
        self.hash_label.setVisible(False)
        self.hash_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.hash_label)

        # Duplicate indicator button
        self.duplicate_btn = QPushButton()
        self.duplicate_btn.setMaximumWidth(150)
        self.duplicate_btn.setVisible(False)
        self.duplicate_btn.clicked.connect(self.duplicate_clicked.emit)
        self.duplicate_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.duplicate_btn)

        # No stretch - this widget should stay on the right
        self.setLayout(layout)

    def set_hashing_progress(self, filename: str, progress: float) -> None:
        """
        Update hashing progress.

        Args:
            filename: Current file being hashed
            progress: Progress percentage (0-100)
        """
        self.is_hashing = True
        self.hash_label.setVisible(True)
        self.hash_label.setText(f"Hashing: {int(progress)}% ({filename})")

    def set_hashing_complete(self) -> None:
        """Mark hashing as complete."""
        self.is_hashing = False
        self.hash_label.setVisible(False)

    def set_duplicate_count(self, count: int) -> None:
        """
        Update duplicate count indicator.

        Args:
            count: Number of duplicate models
        """
        self.duplicate_count = count

        if count > 0:
            self.duplicate_btn.setVisible(True)
            self.duplicate_btn.setText(f"⚠️ {count} Duplicates")

            # Apply theme-aware styling
            try:
                if COLORS:
                    warning_color = getattr(COLORS, "warning", "#FF6B6B")
                    text_color = getattr(COLORS, "text", "#ffffff")
                else:
                    # Fallback colors
                    warning_color = "#FF6B6B"
                    text_color = "#ffffff"

                self.duplicate_btn.setStyleSheet(
                    f"background-color: {warning_color}; color: {text_color}; font-weight: bold; "
                    "border-radius: 3px; padding: 2px 8px;"
                )
            except (AttributeError, TypeError):
                # Fallback if theme system fails
                self.duplicate_btn.setStyleSheet(
                    "background-color: #FF6B6B; color: white; font-weight: bold; "
                    "border-radius: 3px; padding: 2px 8px;"
                )
        else:
            self.duplicate_btn.setVisible(False)

    def get_duplicate_count(self) -> int:
        """Get current duplicate count."""
        return self.duplicate_count

    def is_currently_hashing(self) -> bool:
        """Check if currently hashing."""
        return self.is_hashing
