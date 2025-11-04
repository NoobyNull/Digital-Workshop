"""
Searchable help dialog for the application.

Provides keyword search across all documentation with results display.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QTextEdit,
    QSplitter,
    QLabel,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont

from src.core.logging_config import get_logger
from src.gui.help_system.documentation_indexer import DocumentationIndexer

logger = get_logger(__name__)


class HelpDialog(QDialog):
    """Searchable help dialog."""

    def __init__(self, parent=None):
        """Initialize help dialog."""
        super().__init__(parent)
        self.setWindowTitle("Help - Search Documentation")
        self.setSize(1000, 700)
        self.indexer = DocumentationIndexer()
        self.current_results = []
        self._setup_ui()
        self._build_index()

    def setSize(self, width: int, height: int) -> None:
        """Set dialog size."""
        self.resize(width, height)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout()

        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search Documentation:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Enter keywords (e.g., 'settings', 'lighting', 'grid')"
        )
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Results and content splitter
        splitter = QSplitter(Qt.Horizontal)

        # Results list
        results_layout = QVBoxLayout()
        results_label = QLabel("Results:")
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self._on_result_selected)
        results_layout.addWidget(results_label)
        results_layout.addWidget(self.results_list)

        results_widget = QListWidget()
        results_widget.setLayout(results_layout)

        # Content display
        content_layout = QVBoxLayout()
        content_label = QLabel("Content:")
        self.content_display = QTextEdit()
        self.content_display.setReadOnly(True)
        content_layout.addWidget(content_label)
        content_layout.addWidget(self.content_display)

        # Create widgets for splitter
        from PySide6.QtWidgets import QWidget

        results_container = QWidget()
        results_container.setLayout(results_layout)

        content_container = QWidget()
        content_container.setLayout(content_layout)

        splitter.addWidget(results_container)
        splitter.addWidget(content_container)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def _build_index(self) -> None:
        """Build documentation index."""
        try:
            self.indexer.build_index()
            self.status_label.setText(
                f"Documentation indexed: {len(self.indexer.topics)} topics"
            )
            logger.info(f"Help system indexed {len(self.indexer.topics)} topics")
        except Exception as e:
            logger.error(f"Error building documentation index: {e}")
            self.status_label.setText(f"Error building index: {e}")

    def _on_search(self, query: str) -> None:
        """Handle search input."""
        if len(query) < 2:
            self.results_list.clear()
            self.content_display.clear()
            self.status_label.setText("Enter at least 2 characters to search")
            return

        try:
            self.current_results = self.indexer.search(query)
            self._display_results()
        except Exception as e:
            logger.error(f"Error searching documentation: {e}")
            self.status_label.setText(f"Search error: {e}")

    def _display_results(self) -> None:
        """Display search results."""
        self.results_list.clear()

        if not self.current_results:
            self.status_label.setText("No results found")
            self.content_display.clear()
            return

        for topic, score in self.current_results:
            item_text = f"{topic.title} ({topic.category})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, topic)
            self.results_list.addItem(item)

        self.status_label.setText(f"Found {len(self.current_results)} results")

        # Auto-select first result
        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)
            self._on_result_selected(self.results_list.item(0))

    def _on_result_selected(self, item: QListWidgetItem) -> None:
        """Handle result selection."""
        topic = item.data(Qt.UserRole)
        if topic:
            # Format content display
            content = f"""
<h2>{topic.title}</h2>
<p><b>Category:</b> {topic.category}</p>
<p><b>File:</b> {topic.file_path}</p>
<p><b>Section:</b> {topic.section}</p>
<hr>
<p>{topic.content}</p>
<p><b>Keywords:</b> {', '.join(topic.keywords)}</p>
"""
            self.content_display.setHtml(content)
