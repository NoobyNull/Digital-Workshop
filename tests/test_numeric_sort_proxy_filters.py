"""Tests for NumericSortProxyModel category and dirty filters.

These tests focus on the proxy's filtering behaviour only. They use a small
in-memory QStandardItemModel and do not touch any real database or widgets.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel

from src.gui.model_library.numeric_sort_proxy import NumericSortProxyModel


def _build_test_model() -> QStandardItemModel:
    """Create a small model with category and dirty state columns.

    Column layout matches the library list model:
    0: Thumbnail (unused here)
    1: Name
    2: Format
    3: Size
    4: Triangles
    5: Category
    6: Added Date
    7: Dirty (text + Qt.UserRole bool)
    """

    model = QStandardItemModel()
    model.setColumnCount(8)

    def add_row(name: str, category: str, is_dirty: bool) -> None:
        thumb = QStandardItem()
        name_item = QStandardItem(name)
        fmt = QStandardItem("STL")
        size_item = QStandardItem("1.0 MB")
        size_item.setData(1024 * 1024, Qt.UserRole)
        tri_item = QStandardItem("10,000")
        tri_item.setData(10_000, Qt.UserRole)
        category_item = QStandardItem(category)
        date_item = QStandardItem("2024-01-01")

        dirty_item = QStandardItem("Dirty" if is_dirty else "")
        dirty_item.setData(is_dirty, Qt.UserRole)

        model.appendRow(
            [
                thumb,
                name_item,
                fmt,
                size_item,
                tri_item,
                category_item,
                date_item,
                dirty_item,
            ]
        )

    add_row("Model A", "Animals", True)
    add_row("Model B", "Vehicles", False)
    add_row("Model C", "People", True)

    return model


def test_category_filter_limits_rows_by_category(qt_app):  # noqa: ARG001
    model = _build_test_model()
    proxy = NumericSortProxyModel()
    proxy.setSourceModel(model)

    # No category filter: all rows visible
    proxy.invalidateFilter()
    assert proxy.rowCount() == 3

    # Filter to Animals only
    proxy.set_category_filter("Animals")
    proxy.invalidateFilter()
    assert proxy.rowCount() == 1
    index = proxy.index(0, NumericSortProxyModel.CATEGORY_COLUMN)
    assert index.data() == "Animals"

    # Clear category filter
    proxy.set_category_filter(None)
    proxy.invalidateFilter()
    assert proxy.rowCount() == 3


def test_dirty_filter_limits_rows_by_dirty_state(qt_app):  # noqa: ARG001
    model = _build_test_model()
    proxy = NumericSortProxyModel()
    proxy.setSourceModel(model)

    # No dirty filter: all rows visible
    proxy.invalidateFilter()
    assert proxy.rowCount() == 3

    # Only dirty models
    proxy.set_dirty_filter("dirty")
    proxy.invalidateFilter()
    assert proxy.rowCount() == 2
    for row in range(proxy.rowCount()):
        dirty_index = proxy.index(row, NumericSortProxyModel.DIRTY_COLUMN)
        assert bool(dirty_index.data(Qt.UserRole)) is True

    # Only clean models
    proxy.set_dirty_filter("clean")
    proxy.invalidateFilter()
    assert proxy.rowCount() == 1
    dirty_index = proxy.index(0, NumericSortProxyModel.DIRTY_COLUMN)
    assert bool(dirty_index.data(Qt.UserRole)) is False

    # Unsupported value should behave like no filter
    proxy.set_dirty_filter("invalid")
    proxy.invalidateFilter()
    assert proxy.rowCount() == 3

