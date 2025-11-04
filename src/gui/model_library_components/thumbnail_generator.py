"""
Thumbnail generator for model library.

Generates visual thumbnails for models based on their properties.
"""

from typing import Any, Dict

from PySide6.QtCore import Qt, QPointF, QRectF, QSize
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPixmap

from src.core.logging_config import get_logger
from src.gui.theme_core import get_theme_color


logger = get_logger(__name__)


class ThumbnailGenerator:
    """Generates visual thumbnails for models."""

    def __init__(self, size: QSize = QSize(128, 128)):
        """
        Initialize the thumbnail generator.

        Args:
            size: Size of generated thumbnails (default 128x128)
        """
        self.size = size
        self.logger = get_logger(__name__)

    def generate_thumbnail(self, model_info: Dict[str, Any]) -> QPixmap:
        """
        Generate a thumbnail for a model.

        Args:
            model_info: Dictionary with model information

        Returns:
            QPixmap: Generated thumbnail image
        """
        try:
            pixmap = QPixmap(self.size)
            pixmap.fill(QColor(0, 0, 0, 0))

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            dimensions = model_info.get("dimensions", (1.0, 1.0, 1.0))
            width, height, depth = dimensions
            max_dim = max(width, height, depth) or 1.0
            norm_w = (width / max_dim) * (self.size.width() * 0.8)
            norm_h = (height / max_dim) * (self.size.height() * 0.8)
            cx = self.size.width() / 2
            cy = self.size.height() / 2

            tri_count = model_info.get("triangle_count", 0)
            if tri_count < 1000:
                painter.setPen(QPen(get_theme_color("text_muted"), 1))
                rect = QRectF(cx - norm_w / 2, cy - norm_h / 2, norm_w, norm_h)
                painter.drawRect(rect)
                painter.drawLine(rect.topLeft(), rect.bottomRight())
                painter.drawLine(rect.topRight(), rect.bottomLeft())
            elif tri_count < 10000:
                painter.setPen(QPen(get_theme_color("edge_color"), 1))
                c = get_theme_color("model_surface")
                c.setAlpha(180)
                painter.setBrush(QBrush(c))
                rect = QRectF(cx - norm_w / 2, cy - norm_h / 2, norm_w, norm_h)
                painter.drawRect(rect)
                c2 = get_theme_color("text_inverse")
                c2.setAlpha(100)
                painter.setBrush(QBrush(c2))
                painter.drawRect(QRectF(cx - norm_w / 2, cy - norm_h / 2, norm_w / 3, norm_h / 3))
            else:
                painter.setPen(QPen(get_theme_color("edge_color"), 1))
                c3 = get_theme_color("primary")
                c3.setAlpha(180)
                painter.setBrush(QBrush(c3))
                radius = min(norm_w, norm_h) / 2
                painter.drawEllipse(QPointF(cx, cy), radius, radius)
                painter.setPen(QPen(get_theme_color("primary_text"), 1))
                painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
                painter.drawEllipse(QPointF(cx, cy), radius * 0.7, radius * 0.7)
                painter.drawEllipse(QPointF(cx, cy), radius * 0.4, radius * 0.4)

            painter.setPen(QPen(get_theme_color("primary_text"), 1))
            c4 = get_theme_color("model_ambient")
            c4.setAlpha(200)
            painter.setBrush(QBrush(c4))
            indicator_rect = QRectF(self.size.width() - 25, self.size.height() - 15, 20, 12)
            painter.drawRect(indicator_rect)
            font = painter.font()
            font.setPointSize(6)
            painter.setFont(font)
            fmt = (model_info.get("format") or "UNK")[:3].upper()
            painter.drawText(indicator_rect, Qt.AlignCenter, fmt)

            painter.end()
            return pixmap
        except Exception as e:
            self.logger.error("Failed to generate thumbnail: %s", e)
            px = QPixmap(self.size)
            px.fill(Qt.lightGray)
            p = QPainter(px)
            p.setPen(QPen(Qt.red, 2))
            p.drawLine(10, 10, self.size.width() - 10, self.size.height() - 10)
            p.drawLine(self.size.width() - 10, 10, 10, self.size.height() - 10)
            p.end()
            return px
