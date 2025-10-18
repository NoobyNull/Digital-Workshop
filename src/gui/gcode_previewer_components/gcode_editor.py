"""G-code Editor - Text editor with syntax highlighting for G-code."""

from PySide6.QtWidgets import QPlainTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtGui import QSyntaxHighlighter, QTextDocument, QTextCharFormat, QFont, QColor
from PySide6.QtCore import Qt, Signal
import re


class GcodeSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for G-code."""
    
    def __init__(self, document: QTextDocument):
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
    
    def highlightBlock(self, text: str) -> None:
        """Highlight a block of text."""
        # Highlight comments
        comment_pattern = r';.*$'
        for match in re.finditer(comment_pattern, text):
            self.setFormat(match.start(), match.end() - match.start(), self.comment_format)
        
        # Remove comments from processing
        text_without_comments = re.sub(comment_pattern, '', text)
        
        # Highlight G-codes
        g_pattern = r'\bG\d+\b'
        for match in re.finditer(g_pattern, text_without_comments, re.IGNORECASE):
            self.setFormat(match.start(), match.end() - match.start(), self.g_code_format)
        
        # Highlight M-codes
        m_pattern = r'\bM\d+\b'
        for match in re.finditer(m_pattern, text_without_comments, re.IGNORECASE):
            self.setFormat(match.start(), match.end() - match.start(), self.m_code_format)
        
        # Highlight parameters (X, Y, Z, F, S, etc.)
        param_pattern = r'\b[XYZFSTIJ]\s*[-+]?\d*\.?\d+'
        for match in re.finditer(param_pattern, text_without_comments, re.IGNORECASE):
            self.setFormat(match.start(), match.end() - match.start(), self.parameter_format)
        
        # Highlight numbers
        number_pattern = r'[-+]?\d+\.?\d*'
        for match in re.finditer(number_pattern, text_without_comments):
            # Skip if already highlighted as parameter
            if not re.match(r'[XYZFSTIJ]', text_without_comments[max(0, match.start() - 1)]):
                self.setFormat(match.start(), match.end() - match.start(), self.number_format)


class GcodeEditorWidget(QWidget):
    """Widget for editing G-code with syntax highlighting."""
    
    content_changed = Signal(str)  # Emits edited content
    reload_requested = Signal(str)  # Emits content when reload is requested
    
    def __init__(self, parent=None):
        """Initialize the G-code editor."""
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Text editor
        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont("Courier New", 10))
        self.editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        
        # Apply syntax highlighting
        self.highlighter = GcodeSyntaxHighlighter(self.editor.document())
        
        # Connect signals
        self.editor.textChanged.connect(self._on_text_changed)
        
        layout.addWidget(self.editor)
        
        # Button bar
        button_layout = QHBoxLayout()
        
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
    
    def _on_reload(self) -> None:
        """Handle reload button click."""
        self.reload_requested.emit(self.get_content())
    
    def clear(self) -> None:
        """Clear the editor."""
        self.editor.clear()
    
    def set_read_only(self, read_only: bool) -> None:
        """Set read-only mode."""
        self.editor.setReadOnly(read_only)

