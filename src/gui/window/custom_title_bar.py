"""
Custom title bar widget for themed window decorations.

Single Responsibility: Provide a custom, themeable title bar for the main window.
"""

from PySide6.QtCore import Qt, QSize, QRect, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QIcon
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QApplication
)


class CustomTitleBar(QWidget):
    """
    Custom title bar that can be themed with the application theme.

    Replaces the native OS title bar to allow full theming control.
    """

    # Signals for window control
    close_requested = Signal()
    minimize_requested = Signal()
    maximize_requested = Signal()

    def __init__(self, title: str = "", parent=None):
        """
        Initialize the custom title bar.

        Args:
            title: Window title text
            parent: Parent widget
        """
        super().__init__(parent)
        self.title_text = title
        self.is_maximized = False
        self.drag_start_pos = None

        self._init_ui()
        self._apply_theme()

    def _init_ui(self) -> None:
        """Initialize the title bar UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Title label
        self.title_label = QLabel(self.title_text)
        self.title_label.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(self.title_label, 1)

        # Window control buttons
        self.minimize_btn = self._create_button("−")
        self.maximize_btn = self._create_button("□")
        self.close_btn = self._create_button("✕")

        self.minimize_btn.clicked.connect(self.minimize_requested.emit)
        self.maximize_btn.clicked.connect(self.maximize_requested.emit)
        self.close_btn.clicked.connect(self.close_requested.emit)

        layout.addWidget(self.minimize_btn)
        layout.addWidget(self.maximize_btn)
        layout.addWidget(self.close_btn)

        self.setLayout(layout)
        self.setFixedHeight(32)

    def _create_button(self, text: str) -> QPushButton:
        """Create a window control button."""
        btn = QPushButton(text)
        btn.setFixedSize(32, 24)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 14px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        return btn

    def _apply_theme(self) -> None:
        """Apply the current theme to the title bar."""
        try:
            from src.gui.theme.simple_service import ThemeService
            service = ThemeService.instance()
            theme, _ = service.get_current_theme()

            # Set background color based on theme
            if theme == "dark":
                bg_color = "#1e1e1e"
            else:
                bg_color = "#f5f5f5"

            self.setStyleSheet(f"""
                CustomTitleBar {{
                    background-color: {bg_color};
                    border-bottom: 1px solid #cccccc;
                }}
            """)
        except Exception:
            # Fallback to dark theme
            self.setStyleSheet("""
                CustomTitleBar {
                    background-color: #1e1e1e;
                    border-bottom: 1px solid #cccccc;
                }
            """)

    def set_title(self, title: str) -> None:
        """Update the window title."""
        self.title_text = title
        self.title_label.setText(title)

    def update_theme(self) -> None:
        """Update the title bar theme."""
        self._apply_theme()

    def mousePressEvent(self, event):
        """Handle mouse press for window dragging."""
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Handle mouse move for window dragging."""
        if self.drag_start_pos is not None and event.buttons() == Qt.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self.drag_start_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        self.drag_start_pos = None
        event.accept()

    def mouseDoubleClickEvent(self, event):
        """Handle double-click for maximize/restore."""
        if event.button() == Qt.LeftButton:
            self.maximize_requested.emit()
            event.accept()

