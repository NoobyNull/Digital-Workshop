"""
Grid view delegate that displays only icons without text labels.

This delegate is used for the grid view in the model library to show
only thumbnail images without filenames below them.
"""

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QStyledItemDelegate, QStyle


class GridIconDelegate(QStyledItemDelegate):
    """
    Custom delegate for grid view that displays only icons without text.

    This removes the filename text that normally appears below icons in
    QListView IconMode, creating a clean grid of thumbnails.
    """

    def __init__(self, parent=None) -> None:
        """
        Initialize the grid icon delegate.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.icon_size = QSize(128, 128)

    def set_icon_size(self, size: QSize) -> None:
        """Set the size of icons to display."""
        self.icon_size = size

    def paint(self, painter: QPainter, option, index) -> None:
        """
        Paint only the icon, not the text.

        Args:
            painter: QPainter for drawing
            option: Style option containing geometry and state
            index: Model index
        """
        # Get the icon from the model
        icon = index.data(Qt.DecorationRole)

        if not icon or icon.isNull():
            # If no icon, just draw the selection background
            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())
            return

        # Draw selection background if selected
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        # Draw the icon centered in the item rect
        pixmap = icon.pixmap(self.icon_size)

        # Calculate position to center the icon
        x = option.rect.x() + (option.rect.width() - pixmap.width()) // 2
        y = option.rect.y() + (option.rect.height() - pixmap.height()) // 2

        painter.drawPixmap(x, y, pixmap)

    def sizeHint(self, option, index) -> QSize:  # pylint: disable=unused-argument
        """
        Return the size hint for an item.

        Args:
            option: Style option
            index: Model index

        Returns:
            Size hint for the item
        """
        # Add some padding around the icon
        padding = 10
        return QSize(
            self.icon_size.width() + padding, self.icon_size.height() + padding
        )
