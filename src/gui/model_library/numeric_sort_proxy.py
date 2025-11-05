"""
Numeric sort proxy model for Model Library.

This module provides a custom QSortFilterProxyModel that properly sorts
numeric columns (Size, Triangles) using their stored numeric values
instead of their display strings.
"""

from PySide6.QtCore import QSortFilterProxyModel, Qt


class NumericSortProxyModel(QSortFilterProxyModel):
    """
    Custom proxy model that sorts numeric columns properly.

    For columns that store numeric data in Qt.UserRole (Size, Triangles),
    this model uses the numeric value for sorting instead of the display string.
    This ensures that "100.8 MB" sorts after "3.9 MB" instead of before it.

    Also filters out models without thumbnails in grid view.
    """

    def __init__(self, parent=None):
        """Initialize the numeric sort proxy model."""
        super().__init__(parent)
        # Columns that should use numeric sorting (0-indexed)
        # 2 = Size, 3 = Triangles
        self.numeric_columns = {2, 3}
        # Flag to enable/disable thumbnail filtering (enabled for grid view)
        self.filter_no_thumbnails = False

    def lessThan(self, left, right):
        """
        Compare two items for sorting.
        
        For numeric columns, uses the UserRole data (numeric value).
        For other columns, uses default string comparison.
        
        Args:
            left: Left index to compare
            right: Right index to compare
            
        Returns:
            True if left < right, False otherwise
        """
        column = left.column()
        
        if column in self.numeric_columns:
            # Get numeric values from UserRole
            left_data = left.data(Qt.UserRole)
            right_data = right.data(Qt.UserRole)
            
            # Handle None/missing values
            if left_data is None:
                left_data = 0
            if right_data is None:
                right_data = 0
                
            return left_data < right_data
        
        # Default string comparison for other columns
        return super().lessThan(left, right)

    def filterAcceptsRow(self, source_row, source_parent):
        """
        Filter rows based on search text and thumbnail availability.

        When filter_no_thumbnails is True (grid view), only show models
        that have thumbnails generated.

        Args:
            source_row: Row index in source model
            source_parent: Parent index in source model

        Returns:
            True if row should be shown, False otherwise
        """
        # First check the default filter (search text)
        if not super().filterAcceptsRow(source_row, source_parent):
            return False

        # If thumbnail filtering is enabled, check for thumbnail
        if self.filter_no_thumbnails:
            source_model = self.sourceModel()
            if source_model:
                # Get the thumbnail item (column 0)
                thumbnail_index = source_model.index(source_row, 0, source_parent)
                if thumbnail_index.isValid():
                    # Check if the item has an icon (thumbnail)
                    icon = thumbnail_index.data(Qt.DecorationRole)
                    if not icon or icon.isNull():
                        return False

        return True

