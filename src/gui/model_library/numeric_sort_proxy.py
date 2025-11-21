"""
Numeric sort proxy model for Model Library.

This module provides a custom QSortFilterProxyModel that properly sorts
numeric columns (Size, Triangles) using their stored numeric values
instead of their display strings.
"""

from typing import Optional

from PySide6.QtCore import QSortFilterProxyModel, Qt


class NumericSortProxyModel(QSortFilterProxyModel):
    """Custom proxy model that sorts and filters library rows.

    For columns that store numeric data in Qt.UserRole (Size, Triangles),
    this model uses the numeric value for sorting instead of the display
    string so that "100.8 MB" sorts after "3.9 MB" instead of before it.

    It also supports:
    - Optional filtering by category
    - Optional filtering by dirty/clean status
    - Filtering out models without thumbnails in grid view.
    """

    # Logical column indices for additional filtering
    CATEGORY_COLUMN = 5
    DIRTY_COLUMN = 7

    def __init__(self, parent=None):
        """Initialize the numeric sort proxy model."""
        super().__init__(parent)
        # Columns that should use numeric sorting (0-indexed)
        # 3 = Size, 4 = Triangles
        self.numeric_columns = {3, 4}
        # Flag to enable/disable thumbnail filtering (enabled for grid view)
        self.filter_no_thumbnails = False
        # Optional additional filters
        self._category_filter: Optional[str] = None
        self._dirty_filter: Optional[str] = None
        self._advanced_query: str = ""
        self._parsed_advanced = []

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

    def set_category_filter(self, category: Optional[str]) -> None:
        """Set the active category filter.

        Args:
            category: Category name to filter by, or None for no filter.
        """
        self._category_filter = category or None

    def set_dirty_filter(self, dirty_filter: Optional[str]) -> None:
        """Set the active dirty/clean filter.

        Args:
            dirty_filter: One of "dirty", "clean", or None for no filter.
        """
        if dirty_filter not in {"dirty", "clean", None}:
            dirty_filter = None
        self._dirty_filter = dirty_filter

    # ------------------------------------------------------------------
    # Advanced boolean search
    # ------------------------------------------------------------------
    def set_advanced_query(self, query: str) -> None:
        """Set a boolean search query (supports AND / OR / !term)."""
        self._advanced_query = (query or "").strip()
        self._parsed_advanced = self._parse_advanced_query(self._advanced_query)
        self.invalidateFilter()

    def _parse_advanced_query(self, query: str):
        """Parse a simple boolean query into clauses.

        Supports OR-separated clauses; within a clause, terms are ANDed.
        Negation via leading '!'. No parentheses; quoted phrases are
        preserved, and '+' is treated like AND.
        """
        clauses = []
        if not query:
            return clauses

        normalized = query.replace("||", " OR ").replace("&&", " AND ")
        for raw_clause in normalized.split(" OR "):
            clause = []
            for token in self._tokenize_clause(raw_clause):
                if token.upper() == "AND":
                    continue
                neg = token.startswith("!")
                term = token[1:] if neg else token
                term = term.strip(" ,;'\"")
                if not term:
                    continue
                clause.append((neg, term.lower()))
            if clause:
                clauses.append(clause)
        return clauses

    def _tokenize_clause(self, clause: str):
        """Tokenize a clause respecting quotes and '+' as AND separators."""
        tokens = []
        current = []
        in_quote = False
        i = 0
        while i < len(clause):
            ch = clause[i]
            if ch == '"':
                in_quote = not in_quote
                i += 1
                continue
            if not in_quote and ch in {"+", " "}:
                if current:
                    tokens.append("".join(current))
                    current = []
                i += 1
                continue
            current.append(ch)
            i += 1
        if current:
            tokens.append("".join(current))
        return tokens

    def filterAcceptsRow(self, source_row, source_parent):
        """Filter rows based on search text, category, dirty status, and thumbnails.

        When ``filter_no_thumbnails`` is True (grid view), only show models that
        have thumbnails generated.

        Args:
            source_row: Row index in source model
            source_parent: Parent index in source model

        Returns:
            True if row should be shown, False otherwise.
        """
        # First check the default filter (search text)
        if not super().filterAcceptsRow(source_row, source_parent):
            return False

        source_model = self.sourceModel()
        if not source_model:
            return True

        # Apply category filter if set
        if self._category_filter:
            category_index = source_model.index(
                source_row, self.CATEGORY_COLUMN, source_parent
            )
            if category_index.isValid():
                category_value = category_index.data()
                if not category_value or str(category_value) != self._category_filter:
                    return False

        # Apply dirty/clean filter if set
        if self._dirty_filter:
            dirty_index = source_model.index(
                source_row, self.DIRTY_COLUMN, source_parent
            )
            is_dirty = False
            if dirty_index.isValid():
                dirty_data = dirty_index.data(Qt.UserRole)
                is_dirty = bool(dirty_data)

            if self._dirty_filter == "dirty" and not is_dirty:
                return False
            if self._dirty_filter == "clean" and is_dirty:
                return False

        # If thumbnail filtering is enabled, check for thumbnail
        if self.filter_no_thumbnails:
            # Get the thumbnail item (column 0)
            thumbnail_index = source_model.index(source_row, 0, source_parent)
            if thumbnail_index.isValid():
                # Check if the item has an icon (thumbnail)
                icon = thumbnail_index.data(Qt.DecorationRole)
                if not icon or icon.isNull():
                    return False

        # Apply advanced boolean query if present
        if self._parsed_advanced:
            haystack_parts = []
            column_count = source_model.columnCount()
            for col in range(column_count):
                idx = source_model.index(source_row, col, source_parent)
                if idx.isValid():
                    val = idx.data()
                    if val:
                        haystack_parts.append(str(val).lower())
            haystack = " ".join(haystack_parts)

            def clause_matches(clause):
                for neg, term in clause:
                    present = term in haystack
                    if neg and present:
                        return False
                    if not neg and not present:
                        return False
                return True

            if not any(clause_matches(c) for c in self._parsed_advanced):
                return False

        return True
