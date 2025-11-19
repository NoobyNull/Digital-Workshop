"""
Startup tips and welcome system for first-time users.

Displays helpful tips and hints when the application starts.
"""

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QFrame,
)
from PySide6.QtGui import QFont
from src.gui.walkthrough import WalkthroughManager


class StartupTipsDialog(QDialog):
    """Dialog that shows helpful tips on application startup."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Digital Workshop - Getting Started")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setModal(True)
        self.setStyleSheet(
            """
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333;
            }
        """
        )

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the startup tips UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Welcome header
        welcome_label = QLabel("Welcome to Digital Workshop!")
        welcome_font = QFont()
        welcome_font.setPointSize(18)
        welcome_font.setBold(True)
        welcome_label.setFont(welcome_font)
        layout.addWidget(welcome_label)

        # Subtitle
        subtitle = QLabel("Your Personal Digital Workshop")
        subtitle_font = QFont()
        subtitle_font.setPointSize(11)
        subtitle_font.setItalic(True)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(subtitle)

        # Quick start section
        quick_start_label = QLabel("Quick Start Guide:")
        quick_start_font = QFont()
        quick_start_font.setPointSize(12)
        quick_start_font.setBold(True)
        quick_start_label.setFont(quick_start_font)
        layout.addWidget(quick_start_label)

        # Steps
        steps = [
            "1. Add a folder with your 3D models (Files tab)",
            "2. Browse and select models in the Library",
            "3. View in 3D and edit metadata",
            "4. Organize with categories and tags",
        ]

        for step in steps:
            step_label = QLabel(f"  {step}")
            step_label.setFont(QFont("Arial", 10))
            layout.addWidget(step_label)

        layout.addSpacing(10)

        # Tips section
        tips_label = QLabel("💡 Pro Tips:")
        tips_font = QFont()
        tips_font.setPointSize(12)
        tips_font.setBold(True)
        tips_label.setFont(tips_font)
        layout.addWidget(tips_label)

        # Show 3 random tips
        tips = [WalkthroughManager.get_random_tip() for _ in range(3)]
        for i, tip in enumerate(tips, 1):
            tip_text = f"  • {tip.title}: {tip.content[:60]}..."
            tip_label = QLabel(tip_text)
            tip_label.setWordWrap(True)
            tip_label.setFont(QFont("Arial", 9))
            tip_label.setStyleSheet("color: #555; margin-left: 10px;")
            layout.addWidget(tip_label)

        layout.addStretch()

        # Checkbox
        self.dont_show_checkbox = QCheckBox("Don't show this on startup")
        self.dont_show_checkbox.setFont(QFont("Arial", 10))
        layout.addWidget(self.dont_show_checkbox)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        tips_btn = QPushButton("View All Tips")
        tips_btn.setMinimumWidth(120)
        tips_btn.clicked.connect(self._show_all_tips)
        button_layout.addWidget(tips_btn)

        close_btn = QPushButton("Get Started")
        close_btn.setMinimumWidth(120)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def _show_all_tips(self) -> None:
        """Show the full tips dialog."""
        from src.gui.walkthrough import WalkthroughDialog

        dialog = WalkthroughDialog(self)
        dialog.exec()

    def should_show_again(self) -> bool:
        """Check if startup tips should be shown next time."""
        return not self.dont_show_checkbox.isChecked()

    @staticmethod
    def should_show_on_startup() -> bool:
        """Check if startup tips should be shown based on settings."""
        settings = QSettings()
        # Show on first run, or if user hasn't disabled it
        return settings.value("show_startup_tips", True, type=bool)

    @staticmethod
    def save_preference(show: bool) -> None:
        """Save the user's preference for showing startup tips."""
        settings = QSettings()
        settings.setValue("show_startup_tips", show)


class ContextualHelpWidget(QFrame):
    """Small widget that shows contextual help in the UI."""

    def __init__(self, title: str, content: str, parent=None) -> None:
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet(
            """
            QFrame {
                background-color: #e3f2fd;
                border: 1px solid #90caf9;
                border-radius: 4px;
                padding: 10px;
            }
        """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Title
        title_label = QLabel(f"💡 {title}")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Content
        content_label = QLabel(content)
        content_label.setWordWrap(True)
        content_label.setFont(QFont("Arial", 9))
        layout.addWidget(content_label)

        # Close button
        close_btn = QPushButton("×")
        close_btn.setMaximumWidth(30)
        close_btn.clicked.connect(self.hide)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
