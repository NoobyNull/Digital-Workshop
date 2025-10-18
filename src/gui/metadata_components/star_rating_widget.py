"""
Star rating widget for metadata editing.

Provides an interactive 5-star rating system with visual feedback and hover effects.
"""

from typing import Optional

from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPolygonF
from PySide6.QtWidgets import QWidget

from src.core.logging_config import get_logger
from src.gui.theme_core import get_theme_color


class StarRatingWidget(QWidget):
    """
    Interactive star rating widget with visual feedback.

    Provides a 1-5 star rating system with hover effects and click interaction.
    """

    # Signal emitted when rating changes
    rating_changed = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the star rating widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize logger
        self.logger = get_logger(__name__)

        # Rating state
        self.current_rating = 0
        self.hover_rating = 0

        # Star properties
        self.star_size = 24
        self.star_spacing = 5
        self.star_count = 5

        # Star colors (from theme)
        self.filled_color = get_theme_color('star_filled')
        self.empty_color = get_theme_color('star_empty')
        self.hover_color = get_theme_color('star_hover')

        # Set widget size
        self.setFixedSize(
            self.star_count * (self.star_size + self.star_spacing) - self.star_spacing,
            self.star_size
        )

        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)

        self.logger.debug("Star rating widget initialized")

    def set_rating(self, rating: int) -> None:
        """
        Set the current rating.

        Args:
            rating: Rating value (1-5)
        """
        if 1 <= rating <= self.star_count:
            self.current_rating = rating
            self.update()
            self.rating_changed.emit(rating)
            self.logger.debug(f"Rating set to: {rating}")

    def get_rating(self) -> int:
        """
        Get the current rating.

        Returns:
            Current rating value (1-5)
        """
        return self.current_rating

    def reset_rating(self) -> None:
        """Reset the rating to 0."""
        self.current_rating = 0
        self.update()
        self.rating_changed.emit(0)
        self.logger.debug("Rating reset")

    def paintEvent(self, event) -> None:
        """Paint the star rating widget."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        for i in range(self.star_count):
            # Calculate star position
            x = i * (self.star_size + self.star_spacing)
            y = 0

            # Determine star color
            if i < self.current_rating:
                color = self.filled_color
            elif i < self.hover_rating:
                color = self.hover_color
            else:
                color = self.empty_color

            # Draw star
            self._draw_star(painter, x, y, self.star_size, color)

        painter.end()

    def _draw_star(self, painter: QPainter, x: int, y: int, size: int, color: QColor) -> None:
        """
        Draw a star shape.

        Args:
            painter: QPainter object
            x: X coordinate
            y: Y coordinate
            size: Star size
            color: Star color
        """
        painter.setPen(QPen(color.darker(120), 1))
        painter.setBrush(QBrush(color))

        # Create star path
        center_x = x + size / 2
        center_y = y + size / 2
        outer_radius = size / 2
        inner_radius = outer_radius * 0.4

        points = []
        for i in range(10):
            angle = 3.14159 * i / 5 - 3.14159 / 2
            if i % 2 == 0:
                radius = outer_radius
            else:
                radius = inner_radius

            px = center_x + radius * (angle if i % 4 < 2 else -angle)
            py = center_y + radius * (1 if i % 4 < 2 else -1)
            points.append(QPointF(px, py))

        painter.drawPolygon(QPolygonF(points))

    def mousePressEvent(self, event) -> None:
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton:
            rating = self._get_rating_from_position(event.pos().x())
            self.set_rating(rating)

    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move events for hover effects."""
        rating = self._get_rating_from_position(event.pos().x())
        if rating != self.hover_rating:
            self.hover_rating = rating
            self.update()

    def leaveEvent(self, event) -> None:
        """Handle mouse leave events."""
        self.hover_rating = 0
        self.update()

    def _get_rating_from_position(self, x: int) -> int:
        """
        Get rating value from mouse position.

        Args:
            x: Mouse X coordinate

        Returns:
            Rating value (1-5)
        """
        rating = (x // (self.star_size + self.star_spacing)) + 1
        return max(0, min(rating, self.star_count))

