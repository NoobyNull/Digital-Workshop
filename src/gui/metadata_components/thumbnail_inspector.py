"""
Thumbnail inspector widget for viewing full-resolution thumbnails.

Provides a double-click popup dialog to inspect thumbnails at full resolution.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import (
    QLabel,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
)

from src.core.logging_config import get_logger


class ThumbnailInspectorLabel(QLabel):
    """
    Custom QLabel that displays thumbnails and opens a full-resolution
    inspector dialog on double-click.
    """

    def __init__(self, parent=None) -> None:
        """
        Initialize the thumbnail inspector label.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.full_resolution_pixmap = None
        self.thumbnail_path = None
        self.setCursor(Qt.PointingHandCursor)

    def set_thumbnail(
        self, pixmap: QPixmap, thumbnail_path: Optional[str] = None
    ) -> None:
        """
        Set the thumbnail image.

        Args:
            pixmap: The pixmap to display
            thumbnail_path: Path to the full-resolution thumbnail file
        """
        self.full_resolution_pixmap = pixmap
        self.thumbnail_path = thumbnail_path
        self.setPixmap(pixmap)

    def mouseDoubleClickEvent(self, event) -> None:
        """
        Handle double-click to open full-resolution inspector.

        Args:
            event: Mouse event
        """
        if self.full_resolution_pixmap and not self.full_resolution_pixmap.isNull():
            self._show_inspector()
        else:
            self.logger.debug("No thumbnail available to inspect")

    def _show_inspector(self) -> None:
        """Show the full-resolution thumbnail inspector dialog."""
        try:
            # Load full-resolution pixmap from file if path is available
            full_res_pixmap = self.full_resolution_pixmap
            if self.thumbnail_path:
                full_res_pixmap = QPixmap(self.thumbnail_path)
                if full_res_pixmap.isNull():
                    self.logger.warning(
                        f"Failed to load full-resolution thumbnail from {self.thumbnail_path}"
                    )
                    full_res_pixmap = self.full_resolution_pixmap

            dialog = ThumbnailInspectorDialog(
                full_res_pixmap, self.thumbnail_path, parent=self
            )
            dialog.exec()
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to show thumbnail inspector: %s", e)


class ThumbnailInspectorDialog(QDialog):
    """
    Dialog for viewing full-resolution thumbnails with zoom and pan controls.
    """

    def __init__(
        self, pixmap: QPixmap, thumbnail_path: Optional[str] = None, parent=None
    ) -> None:
        """
        Initialize the thumbnail inspector dialog.

        Args:
            pixmap: The full-resolution pixmap to display
            thumbnail_path: Path to the thumbnail file
            parent: Parent widget
        """
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.pixmap = pixmap
        self.thumbnail_path = thumbnail_path
        self.zoom_level = 1.0

        self._init_ui()
        self._setup_connections()

    def _init_ui(self) -> None:
        """Initialize the dialog UI."""
        self.setWindowTitle("Thumbnail Inspector")
        self.setGeometry(100, 100, 1000, 800)
        self.setWindowIcon(QIcon())

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Scroll area for image
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(
            """
            QScrollArea {
                background-color: #1E1E1E;
                border: 1px solid #444;
            }
        """
        )

        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setPixmap(self.pixmap)
        self.image_label.setStyleSheet(
            """
            QLabel {
                background-color: #1E1E1E;
                padding: 10px;
            }
        """
        )

        scroll_area.setWidget(self.image_label)
        main_layout.addWidget(scroll_area)

        # Control buttons layout
        button_layout = QHBoxLayout()

        # Zoom in button
        zoom_in_button = QPushButton("Zoom In (+)")
        zoom_in_button.clicked.connect(self._zoom_in)
        button_layout.addWidget(zoom_in_button)

        # Zoom out button
        zoom_out_button = QPushButton("Zoom Out (-)")
        zoom_out_button.clicked.connect(self._zoom_out)
        button_layout.addWidget(zoom_out_button)

        # Reset zoom button
        reset_zoom_button = QPushButton("Reset Zoom")
        reset_zoom_button.clicked.connect(self._reset_zoom)
        button_layout.addWidget(reset_zoom_button)

        # Fit to window button
        fit_button = QPushButton("Fit to Window")
        fit_button.clicked.connect(self._fit_to_window)
        button_layout.addWidget(fit_button)

        button_layout.addStretch()

        # Info label
        self.info_label = QLabel()
        self._update_info_label()
        button_layout.addWidget(self.info_label)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        main_layout.addLayout(button_layout)

    def _setup_connections(self) -> None:
        """Setup signal connections."""

    def _zoom_in(self) -> None:
        """Zoom in on the image."""
        self.zoom_level *= 1.2
        self._update_display()

    def _zoom_out(self) -> None:
        """Zoom out on the image."""
        self.zoom_level /= 1.2
        self._update_display()

    def _reset_zoom(self) -> None:
        """Reset zoom to 100%."""
        self.zoom_level = 1.0
        self._update_display()

    def _fit_to_window(self) -> None:
        """Fit image to window."""
        scroll_area = self.image_label.parent()
        if scroll_area:
            available_width = scroll_area.width() - 20
            available_height = scroll_area.height() - 20

            img_width = self.pixmap.width()
            img_height = self.pixmap.height()

            width_ratio = available_width / img_width if img_width > 0 else 1
            height_ratio = available_height / img_height if img_height > 0 else 1

            self.zoom_level = min(width_ratio, height_ratio, 1.0)
            self._update_display()

    def _update_display(self) -> None:
        """Update the displayed image based on zoom level."""
        new_width = int(self.pixmap.width() * self.zoom_level)
        new_height = int(self.pixmap.height() * self.zoom_level)

        scaled_pixmap = self.pixmap.scaledToWidth(new_width, Qt.SmoothTransformation)

        self.image_label.setPixmap(scaled_pixmap)
        self._update_info_label()

    def _update_info_label(self) -> None:
        """Update the info label with current zoom and image info."""
        zoom_percent = int(self.zoom_level * 100)
        size_info = f"{self.pixmap.width()}x{self.pixmap.height()}px"

        if self.thumbnail_path:
            file_size = Path(self.thumbnail_path).stat().st_size / 1024
            info_text = (
                f"Zoom: {zoom_percent}% | Size: {size_info} | File: {file_size:.1f}KB"
            )
        else:
            info_text = f"Zoom: {zoom_percent}% | Size: {size_info}"

        self.info_label.setText(info_text)

    def keyPressEvent(self, event) -> None:
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
            self._zoom_in()
        elif event.key() == Qt.Key_Minus:
            self._zoom_out()
        elif event.key() == Qt.Key_0:
            self._reset_zoom()
        elif event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
