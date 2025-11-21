"""
Add Tool dialog for selecting and adding tools to feeds and speeds.

Provides UI for browsing providers, tools, and properties from the tool database.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
)
from PySide6.QtCore import Qt

from src.core.logging_config import get_logger
from src.core.database.tool_database_repository import ToolDatabaseRepository
from src.core.database.provider_repository import ProviderRepository

logger = get_logger(__name__)


class AddToolDialog(QDialog):
    """Dialog for adding tools from the tool database."""

    def __init__(self, db_path: str, parent=None) -> None:
        """Initialize Add Tool dialog.

        Args:
            db_path: Path to the tool database
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_path = db_path
        self.logger = logger

        # Initialize repositories
        self.tool_repo = ToolDatabaseRepository(db_path)
        self.provider_repo = ProviderRepository(db_path)

        # Selected tool data
        self.selected_provider = None
        self.selected_tool = None

        self._setup_ui()
        self._load_providers()

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        self.setWindowTitle("Add Tool")
        self.setGeometry(100, 100, 600, 500)

        layout = QVBoxLayout()

        # Provider section
        provider_label = QLabel("Select Provider:")
        layout.addWidget(provider_label)

        self.provider_list = QListWidget()
        self.provider_list.itemSelectionChanged.connect(self._on_provider_selected)
        layout.addWidget(self.provider_list)

        # Tools section
        tools_label = QLabel("Select Tool:")
        layout.addWidget(tools_label)

        self.tool_list = QListWidget()
        self.tool_list.itemSelectionChanged.connect(self._on_tool_selected)
        layout.addWidget(self.tool_list)

        # Buttons
        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Tool")
        self.add_button.clicked.connect(self.accept)
        self.add_button.setEnabled(False)
        button_layout.addWidget(self.add_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _load_providers(self) -> None:
        """Load providers from database."""
        try:
            providers = self.provider_repo.get_all_providers()
            self.provider_list.clear()

            for provider in providers:
                item = QListWidgetItem(provider["name"])
                item.setData(Qt.UserRole, provider["id"])
                self.provider_list.addItem(item)

            self.logger.info("Loaded %s providers", len(providers))

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to load providers: %s", e)

    def _on_provider_selected(self) -> None:
        """Handle provider selection change."""
        items = self.provider_list.selectedItems()
        if items:
            item = items[0]
            self.selected_provider = item.data(Qt.UserRole)
            self._load_tools_for_provider(self.selected_provider)
        else:
            self.tool_list.clear()

    def _load_tools_for_provider(self, provider_id: int) -> None:
        """Load tools for selected provider.

        Args:
            provider_id: ID of the selected provider
        """
        try:
            tools = self.tool_repo.search_tools(provider_id=provider_id)
            self.tool_list.clear()

            for tool in tools:
                item = QListWidgetItem(tool["description"])
                item.setData(Qt.UserRole, tool["id"])
                self.tool_list.addItem(item)

            self.logger.info("Loaded %s tools for provider {provider_id}", len(tools))

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to load tools: %s", e)

    def _on_tool_selected(self) -> None:
        """Handle tool selection change."""
        items = self.tool_list.selectedItems()
        if items:
            item = items[0]
            self.selected_tool = item.data(Qt.UserRole)
            self.add_button.setEnabled(True)
        else:
            self.selected_tool = None
            self.add_button.setEnabled(False)

    def get_selected_tool(self) -> Optional[dict]:
        """Get the selected tool data.

        Returns:
            Dictionary containing tool information or None
        """
        if self.selected_tool:
            try:
                tool_data = self.tool_repo.get_tool_by_id(self.selected_tool)
                return tool_data
            except (
                OSError,
                IOError,
                ValueError,
                TypeError,
                KeyError,
                AttributeError,
            ) as e:
                self.logger.error("Failed to get selected tool: %s", e)

        return None
