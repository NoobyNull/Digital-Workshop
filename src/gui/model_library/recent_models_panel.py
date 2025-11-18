"""UI widget that displays the recent models MRU list."""

from __future__ import annotations

from datetime import datetime
from functools import partial
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class RecentModelsPanel(QGroupBox):
    """Displays the MRU list with star controls."""

    entry_activated = Signal(int)
    favorite_toggled = Signal(int, bool)

    def __init__(self, parent=None) -> None:
        super().__init__("Recent Models")
        self.setObjectName("RecentModelsPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        description = QLabel(
            "Double-click to reopen a model. Click the star to pin favorites "
            "so they are easy to find."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        self.empty_label = QLabel("No models opened yet.")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setObjectName("RecentEmptyLabel")

        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setUniformItemSizes(True)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)

        layout.addWidget(self.list_widget)
        layout.addWidget(self.empty_label)

        self.set_entries([])

    def set_entries(self, entries: List[Dict[str, object]]) -> None:
        """Replace the MRU rows with the supplied entries."""

        self.list_widget.clear()

        if not entries:
            self.list_widget.hide()
            self.empty_label.show()
            return

        self.list_widget.show()
        self.empty_label.hide()

        for entry in entries:
            model_id = int(entry["model_id"])
            item = QListWidgetItem()
            item.setData(Qt.UserRole, model_id)

            row_widget = _RecentModelRow(entry)
            row_widget.favorite_toggled.connect(
                partial(self.favorite_toggled.emit, model_id)
            )

            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, row_widget)

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        model_id = item.data(Qt.UserRole)
        if model_id is not None:
            self.entry_activated.emit(int(model_id))


class _RecentModelRow(QWidget):
    """Compact row with name, metadata, and a star toggle."""

    favorite_toggled = Signal(bool)

    def __init__(self, entry: Dict[str, object]) -> None:
        super().__init__()
        self._entry = entry

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.star_button = QToolButton()
        self.star_button.setCheckable(True)
        self.star_button.setAutoRaise(True)
        self.star_button.setChecked(bool(entry.get("is_favorite")))
        self.star_button.clicked.connect(self._emit_toggle)
        self._update_star_icon()
        layout.addWidget(self.star_button)

        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(0)

        primary_text = (
            entry.get("title")
            or entry.get("filename")
            or (entry.get("file_path") or "Unknown Model")
        )
        title_label = QLabel(str(primary_text))
        title_label.setObjectName("RecentModelTitle")
        info_layout.addWidget(title_label)

        subtitle_bits: List[str] = []
        category = entry.get("category")
        if category:
            subtitle_bits.append(str(category))
        fmt = entry.get("format")
        if fmt:
            subtitle_bits.append(str(fmt).upper())
        relative = _format_relative_time(entry.get("last_accessed"))
        if relative:
            subtitle_bits.append(relative)

        subtitle = " • ".join(subtitle_bits)
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("RecentModelMeta")
        info_layout.addWidget(subtitle_label)

        layout.addLayout(info_layout, 1)

    def _emit_toggle(self, checked: bool) -> None:
        self.favorite_toggled.emit(bool(checked))
        self._update_star_icon()

    def _update_star_icon(self) -> None:
        # Unicode stars provide a lightweight visual indicator without bundling icons.
        self.star_button.setText("★" if self.star_button.isChecked() else "☆")
        self.star_button.setToolTip(
            "Unstar model" if self.star_button.isChecked() else "Star model"
        )
        if self.star_button.isChecked():
            self.star_button.setStyleSheet("color: #f2b01e;")
        else:
            self.star_button.setStyleSheet("color: #808080;")


def _format_relative_time(raw: Optional[object]) -> str:
    """Return a friendly relative time string."""

    if raw is None:
        return ""

    try:
        text = str(raw)
        timestamp = datetime.fromisoformat(text)
    except Exception:
        logger.debug("Failed to parse MRU timestamp: %r", raw)
        return ""

    delta = datetime.utcnow() - timestamp
    seconds = max(0, int(delta.total_seconds()))

    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    if days < 30:
        return f"{days}d ago"
    months = days // 30
    return f"{months}mo ago"
