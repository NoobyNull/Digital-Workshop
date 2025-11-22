"""G-code Editor - Text editor with syntax highlighting for G-code."""

from __future__ import annotations

import re

from PySide6.QtWidgets import (
    QPlainTextEdit,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QCheckBox,
    QToolButton,
)
from PySide6.QtGui import (
    QSyntaxHighlighter,
    QTextDocument,
    QTextCharFormat,
    QFont,
    QColor,
    QTextCursor,
)
from PySide6.QtCore import Signal, Qt, QRegularExpression

SEARCH_FORWARD_ICON = "\u25bc"
SEARCH_BACK_ICON = "\u25b2"


class GcodeSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for G-code."""

    def __init__(self, document: QTextDocument) -> None:
        """Initialize the syntax highlighter."""
        super().__init__(document)

        # Define formats
        self.g_code_format = QTextCharFormat()
        self.g_code_format.setForeground(QColor(0, 128, 255))  # Blue
        self.g_code_format.setFontWeight(700)

        self.m_code_format = QTextCharFormat()
        self.m_code_format.setForeground(QColor(255, 128, 0))  # Orange
        self.m_code_format.setFontWeight(700)

        self.parameter_format = QTextCharFormat()
        self.parameter_format.setForeground(QColor(0, 200, 0))  # Green

        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor(128, 128, 128))  # Gray
        self.comment_format.setFontItalic(True)

        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor(255, 0, 0))  # Red

        self.dimmed_format = QTextCharFormat()
        self.dimmed_format.setForeground(QColor(120, 120, 120))

        self.show_rapids = True
        self.show_arcs = True
        self.show_canned = True

    def highlightBlock(self, text: str) -> None:
        """Highlight a block of text."""
        upper_text = text.upper()
        if self._should_dim_line(upper_text):
            self.setFormat(0, len(text), self.dimmed_format)
            return

        # Highlight comments
        comment_pattern = r";.*$"
        for match in re.finditer(comment_pattern, text):
            self.setFormat(
                match.start(), match.end() - match.start(), self.comment_format
            )

        # Remove comments from processing
        text_without_comments = re.sub(comment_pattern, "", text)

        # Highlight G-codes
        g_pattern = r"\bG\d+\b"
        for match in re.finditer(g_pattern, text_without_comments, re.IGNORECASE):
            self.setFormat(
                match.start(), match.end() - match.start(), self.g_code_format
            )

        # Highlight M-codes
        m_pattern = r"\bM\d+\b"
        for match in re.finditer(m_pattern, text_without_comments, re.IGNORECASE):
            self.setFormat(
                match.start(), match.end() - match.start(), self.m_code_format
            )

        # Highlight parameters (X, Y, Z, F, S, etc.)
        param_pattern = r"\b[XYZFSTIJ]\s*[-+]?\d*\.?\d+"
        for match in re.finditer(param_pattern, text_without_comments, re.IGNORECASE):
            self.setFormat(
                match.start(), match.end() - match.start(), self.parameter_format
            )

        # Highlight numbers
        number_pattern = r"[-+]?\d+\.?\d*"
        for match in re.finditer(number_pattern, text_without_comments):
            # Skip if already highlighted as parameter
            if not re.match(
                r"[XYZFSTIJ]", text_without_comments[max(0, match.start() - 1)]
            ):
                self.setFormat(
                    match.start(), match.end() - match.start(), self.number_format
                )

    def _should_dim_line(self, upper_text: str) -> bool:
        """Return True when the current line should be dimmed."""
        if not self.show_rapids and re.search(r"\bG0[0]?\b", upper_text):
            return True
        if not self.show_arcs and re.search(r"\bG0?[23]\b", upper_text):
            return True
        if not self.show_canned and re.search(r"\bG8[1-9]\b", upper_text):
            return True
        return False

    def set_filters(self, *, rapids: bool, arcs: bool, canned: bool) -> None:
        """Update filter settings and refresh highlighting."""
        self.show_rapids = rapids
        self.show_arcs = arcs
        self.show_canned = canned
        self.rehighlight()


class GcodeEditorWidget(QWidget):
    """Widget for editing G-code with syntax highlighting."""

    content_changed = Signal(str)  # Emits edited content
    reload_requested = Signal(str)  # Emits content when reload is requested
    save_requested = Signal(str)  # Emits content when save-to-project is requested
    line_selected = Signal(int)  # Emits 1-based line number when caret moves

    def __init__(self, parent=None) -> None:
        """Initialize the G-code editor."""
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Find/replace UI (stacked rows to save horizontal space)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Find...")
        self.search_input.textChanged.connect(self._on_search_text_changed)

        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replace...")

        self.case_checkbox = QCheckBox("Match case")
        self.regex_checkbox = QCheckBox("Regex")

        # Row 1: Find + options + navigation
        find_row = QHBoxLayout()
        find_row.addWidget(QLabel("Find:"))
        find_row.addWidget(self.search_input, 3)
        find_row.addWidget(self.case_checkbox)
        find_row.addWidget(self.regex_checkbox)

        self.find_prev_btn = QToolButton()
        self.find_prev_btn.setText(SEARCH_BACK_ICON)
        self.find_prev_btn.setToolTip("Find previous")
        self.find_prev_btn.clicked.connect(lambda: self._find_next(forward=False))
        find_row.addWidget(self.find_prev_btn)

        self.find_next_btn = QToolButton()
        self.find_next_btn.setText(SEARCH_FORWARD_ICON)
        self.find_next_btn.setToolTip("Find next")
        self.find_next_btn.clicked.connect(self._find_next)
        find_row.addWidget(self.find_next_btn)

        layout.addLayout(find_row)

        # Row 2: Replace entry + actions
        replace_row = QHBoxLayout()
        replace_row.addWidget(QLabel("Replace:"))
        replace_row.addWidget(self.replace_input, 3)

        self.replace_btn = QPushButton("Replace")
        self.replace_btn.clicked.connect(self._replace_one)
        replace_row.addWidget(self.replace_btn)

        self.replace_all_btn = QPushButton("Replace All")
        self.replace_all_btn.clicked.connect(self._replace_all)
        replace_row.addWidget(self.replace_all_btn)

        layout.addLayout(replace_row)

        # Text editor
        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont("Courier New", 10))
        self.editor.setLineWrapMode(QPlainTextEdit.NoWrap)

        # Apply syntax highlighting
        self.highlighter = GcodeSyntaxHighlighter(self.editor.document())

        # Connect signals
        self.editor.textChanged.connect(self._on_text_changed)
        self.editor.cursorPositionChanged.connect(self._emit_current_line)

        layout.addWidget(self.editor)

        # Button bar
        button_layout = QHBoxLayout()

        self.rapid_checkbox = QCheckBox("Rapids")
        self.rapid_checkbox.setChecked(True)
        self.rapid_checkbox.toggled.connect(self._on_filter_changed)
        button_layout.addWidget(self.rapid_checkbox)

        self.arc_checkbox = QCheckBox("Arcs")
        self.arc_checkbox.setChecked(True)
        self.arc_checkbox.toggled.connect(self._on_filter_changed)
        button_layout.addWidget(self.arc_checkbox)

        self.canned_checkbox = QCheckBox("Canned Cycles")
        self.canned_checkbox.setChecked(True)
        self.canned_checkbox.toggled.connect(self._on_filter_changed)
        button_layout.addWidget(self.canned_checkbox)

        button_layout.addStretch()

        self.save_btn = QPushButton("Save to Project…")
        self.save_btn.clicked.connect(self._on_save_clicked)
        button_layout.addWidget(self.save_btn)

        reload_btn = QPushButton("Reload & Render")
        reload_btn.clicked.connect(self._on_reload)
        button_layout.addWidget(reload_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

    def set_content(self, content: str) -> None:
        """Set the editor content."""
        self.editor.setPlainText(content)

    def get_content(self) -> str:
        """Get the editor content."""
        return self.editor.toPlainText()

    def _on_text_changed(self) -> None:
        """Handle text change."""
        self.content_changed.emit(self.get_content())

    def _emit_current_line(self) -> None:
        """Emit the currently selected line number."""
        block_number = self.editor.textCursor().blockNumber()
        self.line_selected.emit(block_number + 1)

    def _on_reload(self) -> None:
        """Handle reload button click."""
        self.reload_requested.emit(self.get_content())

    def _on_save_clicked(self) -> None:
        """Emit save requested with current content."""
        self.save_requested.emit(self.get_content())

    def _on_filter_changed(self) -> None:
        """Update move filters applied by the highlighter."""
        self.highlighter.set_filters(
            rapids=self.rapid_checkbox.isChecked(),
            arcs=self.arc_checkbox.isChecked(),
            canned=self.canned_checkbox.isChecked(),
        )

    def _on_search_text_changed(self, _: str) -> None:
        """Incremental search highlighting as text changes."""
        if self.search_input.text():
            self._find_next(from_start=True)

    def _move_cursor_to_start(self) -> None:
        """Move cursor to document start without emitting edits."""
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.Start)
        self.editor.setTextCursor(cursor)

    def _find_next(self, *, forward: bool = True, from_start: bool = False) -> bool:
        """Find the next/previous match, returning True on success."""
        pattern = self.search_input.text()
        if not pattern:
            return False

        if from_start:
            self._move_cursor_to_start()

        flags = QTextDocument.FindFlags()
        if not forward:
            flags |= QTextDocument.FindBackward

        if self.case_checkbox.isChecked():
            flags |= QTextDocument.FindCaseSensitively

        found = False
        if self.regex_checkbox.isChecked():
            expression = QRegularExpression(pattern)
            if not self.case_checkbox.isChecked():
                expression.setPatternOptions(QRegularExpression.CaseInsensitiveOption)
            found = self.editor.find(expression, flags)
        else:
            found = self.editor.find(pattern, flags)
        return found

    def _replace_one(self) -> None:
        """Replace current selection if it matches the search criteria."""
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            cursor.insertText(self.replace_input.text())
        self._find_next()

    def _replace_all(self) -> None:
        """Replace all matches in the document."""
        pattern = self.search_input.text()
        if not pattern:
            return

        self._move_cursor_to_start()
        replaced = 0
        while self._find_next():
            cursor = self.editor.textCursor()
            if not cursor.hasSelection():
                break
            cursor.insertText(self.replace_input.text())
            replaced += 1
        if replaced:
            self._find_next(from_start=True)

    def clear(self) -> None:
        """Clear the editor."""
        self.editor.clear()

    def set_read_only(self, read_only: bool) -> None:
        """Set read-only mode."""
        self.editor.setReadOnly(read_only)

    def highlight_line(self, line_number: int) -> None:
        """Center and highlight a specific line."""
        if line_number < 1:
            return
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, line_number - 1)
        self.editor.setTextCursor(cursor)
        self.editor.centerCursor()
