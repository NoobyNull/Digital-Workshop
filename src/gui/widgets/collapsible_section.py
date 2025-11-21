"""
Collapsible Section Widget - A reusable widget for organizing settings into collapsible groups.

This widget provides a clickable header that toggles the visibility of its content,
helping to reduce visual clutter and improve the organization of dense UI sections.
"""

from PySide6.QtCore import Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFrame, QSizePolicy


class CollapsibleSection(QWidget):
    """
    A collapsible section widget with a clickable header and toggleable content.

    This widget provides progressive disclosure of settings, allowing users to
    expand only the sections they need, reducing visual clutter.

    Attributes:
        toggled: Signal emitted when the section is expanded/collapsed

    Example:
        >>> section = CollapsibleSection("Camera Settings", collapsed=False)
        >>> section.add_widget(QLabel("Mouse sensitivity:"))
        >>> section.add_widget(slider_widget)
        >>> section.toggled.connect(lambda expanded: print(f"Section {'expanded' if expanded else 'collapsed'}"))
    """

    toggled = Signal(bool)  # Emits True when expanded, False when collapsed

    def __init__(self, title: str, parent=None, collapsed: bool = False) -> None:
        """
        Initialize the collapsible section.

        Args:
            title: The title text to display in the header
            parent: The parent widget
            collapsed: Whether the section starts collapsed (default: False)
        """
        super().__init__(parent)
        self._collapsed = collapsed
        self._animation_duration = 150  # milliseconds

        self._setup_ui(title)

        # Set initial state
        if self._collapsed:
            self.content_frame.setMaximumHeight(0)
            self.content_frame.setVisible(False)

    def _setup_ui(self, title: str) -> None:
        """Setup the user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header button
        self.header_button = QPushButton()
        self.header_button.setCheckable(True)
        self.header_button.setChecked(not self._collapsed)
        self.header_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._update_header_text(title)

        # Header styling
        self.header_button.setStyleSheet(
            """
            QPushButton {
                text-align: left;
                padding: 8px 12px;
                border: none;
                background: transparent;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background: rgba(0, 0, 0, 0.05);
            }
            QPushButton:pressed {
                background: rgba(0, 0, 0, 0.1);
            }
        """
        )

        self.header_button.clicked.connect(self.toggle)
        layout.addWidget(self.header_button)

        # Content frame
        self.content_frame = QFrame()
        self.content_frame.setFrameShape(QFrame.NoFrame)
        self.content_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Content layout with left indentation
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(20, 4, 0, 8)
        self.content_layout.setSpacing(8)

        layout.addWidget(self.content_frame)

        # Setup animation
        self.animation = QPropertyAnimation(self.content_frame, b"maximumHeight")
        self.animation.setDuration(self._animation_duration)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)

    def _update_header_text(self, title: str) -> None:
        """Update the header button text with the appropriate arrow."""
        arrow = "▼" if not self._collapsed else "▶"
        self.header_button.setText(f"{arrow}  {title}")

    def toggle(self) -> None:
        """Toggle the visibility of the content section with animation."""
        self._collapsed = not self._collapsed

        # Update header
        title = self.header_button.text()[3:]  # Remove arrow and spaces
        self._update_header_text(title)

        # Animate content
        if self._collapsed:
            # Collapse
            start_height = self.content_frame.height()
            self.animation.setStartValue(start_height)
            self.animation.setEndValue(0)
            self.animation.finished.connect(
                lambda: self.content_frame.setVisible(False)
            )
        else:
            # Expand
            self.content_frame.setVisible(True)
            self.content_frame.setMaximumHeight(16777215)  # Reset max height
            content_height = self.content_layout.sizeHint().height()
            self.animation.setStartValue(0)
            self.animation.setEndValue(content_height)

        self.animation.start()
        self.header_button.setChecked(not self._collapsed)
        self.toggled.emit(not self._collapsed)

    def add_widget(self, widget: QWidget) -> None:
        """
        Add a widget to the content section.

        Args:
            widget: The widget to add to the content area
        """
        self.content_layout.addWidget(widget)

    def add_layout(self, layout) -> None:
        """
        Add a layout to the content section.

        Args:
            layout: The layout to add to the content area
        """
        self.content_layout.addLayout(layout)

    def add_stretch(self, stretch: int = 0) -> None:
        """
        Add a stretch to the content layout.

        Args:
            stretch: The stretch factor
        """
        self.content_layout.addStretch(stretch)

    def is_collapsed(self) -> bool:
        """
        Check if the section is currently collapsed.

        Returns:
            bool: True if collapsed, False if expanded
        """
        return self._collapsed

    def set_collapsed(self, collapsed: bool, animate: bool = True) -> None:
        """
        Set the collapsed state of the section.

        Args:
            collapsed: Whether the section should be collapsed
            animate: Whether to animate the transition (default: True)
        """
        if self._collapsed == collapsed:
            return

        if not animate:
            # Store animation duration and set to 0
            original_duration = self._animation_duration
            self.animation.setDuration(0)

        self.toggle()

        if not animate:
            # Restore animation duration
            self.animation.setDuration(original_duration)

    def set_title(self, title: str) -> None:
        """
        Update the section title.

        Args:
            title: The new title text
        """
        self._update_header_text(title)

    def clear(self) -> None:
        """Remove all widgets from the content section."""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Recursively clear nested layouts
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
