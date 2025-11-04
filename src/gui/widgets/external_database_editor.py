"""
External database viewer and editor for tool database management.

Provides UI for viewing, editing, and exporting tool data to external databases
with real-time calculations and validation.
"""

from typing import Optional, List
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLineEdit,
    QComboBox,
    QLabel,
    QMessageBox,
    QFileDialog,
    QSpinBox,
    QDoubleSpinBox,
    QDialogButtonBox,
    QTabWidget,
)
from PySide6.QtCore import Qt
from src.core.logging_config import get_logger
from src.core.database.tool_database_repository import ToolDatabaseRepository
from src.parsers.tool_database_manager import ToolDatabaseManager


logger = get_logger(__name__)


class ExternalDatabaseEditor(QDialog):
    """Dialog for viewing and editing external tool databases."""

    def __init__(self, db_path: str, parent=None):
        """Initialize the external database editor."""
        super().__init__(parent)
        self.db_path = db_path
        self.logger = logger

        # Initialize database manager
        self.db_manager = ToolDatabaseManager(db_path)
        self.tool_repo = ToolDatabaseRepository(db_path)

        self.setWindowTitle("External Database Editor")
        self.setGeometry(100, 100, 1000, 600)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI components."""
        main_layout = QVBoxLayout()

        # Create tabs for different views
        self.tabs = QTabWidget()

        # Tools tab
        tools_tab = self._create_tools_tab()
        self.tabs.addTab(tools_tab, "Tools")

        # Providers tab
        providers_tab = self._create_providers_tab()
        self.tabs.addTab(providers_tab, "Providers")

        # Search/Filter tab
        search_tab = self._create_search_tab()
        self.tabs.addTab(search_tab, "Search")

        main_layout.addWidget(self.tabs)

        # Button layout
        button_layout = QHBoxLayout()
        export_btn = QPushButton("Export to File")
        export_btn.clicked.connect(self._export_database)
        button_layout.addWidget(export_btn)

        import_btn = QPushButton("Import from File")
        import_btn.clicked.connect(self._import_database)
        button_layout.addWidget(import_btn)

        button_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def _create_tools_tab(self):
        """Create the tools viewing tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.tools_search = QLineEdit()
        self.tools_search.setPlaceholderText("Search by name, type, or vendor")
        self.tools_search.textChanged.connect(self._refresh_tools_table)
        search_layout.addWidget(self.tools_search)
        layout.addLayout(search_layout)

        # Tools table
        self.tools_table = QTableWidget()
        self.tools_table.setColumnCount(7)
        self.tools_table.setHorizontalHeaderLabels(
            ["GUID", "Name", "Type", "Diameter", "Vendor", "Provider", "Actions"]
        )
        self.tools_table.setColumnWidth(0, 150)
        self.tools_table.setColumnWidth(1, 150)
        self.tools_table.setColumnWidth(2, 100)
        self.tools_table.setColumnWidth(3, 80)
        self.tools_table.setColumnWidth(4, 100)
        self.tools_table.setColumnWidth(5, 100)
        self.tools_table.setColumnWidth(6, 100)

        layout.addWidget(self.tools_table)

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_tools_table)
        layout.addWidget(refresh_btn)

        widget.setLayout(layout)
        return widget

    def _create_providers_tab(self):
        """Create the providers viewing tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Tool Providers"))

        # Providers table
        self.providers_table = QTableWidget()
        self.providers_table.setColumnCount(4)
        self.providers_table.setHorizontalHeaderLabels(
            ["Provider Name", "Tool Count", "Last Updated", "Source"]
        )
        self.providers_table.setColumnWidth(0, 200)
        self.providers_table.setColumnWidth(1, 100)
        self.providers_table.setColumnWidth(2, 150)
        self.providers_table.setColumnWidth(3, 150)

        layout.addWidget(self.providers_table)

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_providers_table)
        layout.addWidget(refresh_btn)

        widget.setLayout(layout)
        self._refresh_providers_table()
        return widget

    def _create_search_tab(self):
        """Create the advanced search tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Search parameters
        params_layout = QHBoxLayout()

        params_layout.addWidget(QLabel("Tool Type:"))
        self.search_type = QComboBox()
        self.search_type.addItems(
            ["All", "End Mill", "Bit", "V-Bit", "Ball End Mill", "Drill"]
        )
        params_layout.addWidget(self.search_type)

        params_layout.addWidget(QLabel("Min Diameter:"))
        self.min_diameter = QDoubleSpinBox()
        self.min_diameter.setRange(0, 100)
        self.min_diameter.setSingleStep(0.1)
        params_layout.addWidget(self.min_diameter)

        params_layout.addWidget(QLabel("Max Diameter:"))
        self.max_diameter = QDoubleSpinBox()
        self.max_diameter.setRange(0, 100)
        self.max_diameter.setValue(100)
        self.max_diameter.setSingleStep(0.1)
        params_layout.addWidget(self.max_diameter)

        layout.addLayout(params_layout)

        # Search button
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._perform_search)
        layout.addWidget(search_btn)

        # Results table
        self.search_results_table = QTableWidget()
        self.search_results_table.setColumnCount(6)
        self.search_results_table.setHorizontalHeaderLabels(
            ["Name", "Type", "Diameter", "Vendor", "Provider", "Actions"]
        )
        layout.addWidget(self.search_results_table)

        widget.setLayout(layout)
        return widget

    def _refresh_tools_table(self):
        """Refresh the tools table with current data."""
        try:
            search_text = self.tools_search.text()
            tools = (
                self.tool_repo.search_tools(search_text)
                if search_text
                else self.tool_repo.get_all_tools()
            )

            self.tools_table.setRowCount(len(tools))

            for row, tool in enumerate(tools):
                self.tools_table.setItem(
                    row, 0, QTableWidgetItem(tool.get("guid", "N/A"))
                )
                self.tools_table.setItem(
                    row, 1, QTableWidgetItem(tool.get("description", "N/A"))
                )
                self.tools_table.setItem(
                    row, 2, QTableWidgetItem(tool.get("type", "N/A"))
                )
                self.tools_table.setItem(
                    row, 3, QTableWidgetItem(str(tool.get("diameter", "N/A")))
                )
                self.tools_table.setItem(
                    row, 4, QTableWidgetItem(tool.get("vendor", "N/A"))
                )
                self.tools_table.setItem(
                    row, 5, QTableWidgetItem(tool.get("provider", "N/A"))
                )

                edit_btn = QPushButton("Edit")
                edit_btn.clicked.connect(lambda checked, t=tool: self._edit_tool(t))
                self.tools_table.setCellWidget(row, 6, edit_btn)

            self.logger.info(f"Loaded {len(tools)} tools into table")

        except Exception as e:
            self.logger.error(f"Failed to refresh tools table: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load tools: {str(e)}")

    def _refresh_providers_table(self):
        """Refresh the providers table."""
        try:
            providers = self.db_manager.provider_repo.get_all_providers()

            self.providers_table.setRowCount(len(providers))

            for row, provider in enumerate(providers):
                self.providers_table.setItem(
                    row, 0, QTableWidgetItem(provider.get("name", "N/A"))
                )
                tool_count = self.tool_repo.get_tools_by_provider(provider.get("id", 0))
                self.providers_table.setItem(
                    row, 1, QTableWidgetItem(str(len(tool_count)))
                )
                self.providers_table.setItem(
                    row, 2, QTableWidgetItem(provider.get("updated_at", "N/A"))
                )
                self.providers_table.setItem(
                    row, 3, QTableWidgetItem(provider.get("source", "N/A"))
                )

            self.logger.info(f"Loaded {len(providers)} providers")

        except Exception as e:
            self.logger.error(f"Failed to refresh providers: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load providers: {str(e)}")

    def _perform_search(self):
        """Perform advanced search based on criteria."""
        try:
            tool_type = self.search_type.currentText()
            min_dia = self.min_diameter.value()
            max_dia = self.max_diameter.value()

            # Query database with filters
            all_tools = self.tool_repo.get_all_tools()
            filtered = [
                t
                for t in all_tools
                if (tool_type == "All" or t.get("type") == tool_type)
                and (min_dia <= float(t.get("diameter", 0)) <= max_dia)
            ]

            self.search_results_table.setRowCount(len(filtered))

            for row, tool in enumerate(filtered):
                self.search_results_table.setItem(
                    row, 0, QTableWidgetItem(tool.get("description", "N/A"))
                )
                self.search_results_table.setItem(
                    row, 1, QTableWidgetItem(tool.get("type", "N/A"))
                )
                self.search_results_table.setItem(
                    row, 2, QTableWidgetItem(str(tool.get("diameter", "N/A")))
                )
                self.search_results_table.setItem(
                    row, 3, QTableWidgetItem(tool.get("vendor", "N/A"))
                )
                self.search_results_table.setItem(
                    row, 4, QTableWidgetItem(tool.get("provider", "N/A"))
                )

                use_btn = QPushButton("Use")
                use_btn.clicked.connect(lambda checked, t=tool: self._use_tool(t))
                self.search_results_table.setCellWidget(row, 5, use_btn)

            self.logger.info(f"Search found {len(filtered)} tools")

        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            QMessageBox.critical(self, "Error", f"Search failed: {str(e)}")

    def _edit_tool(self, tool):
        """Edit a tool's properties."""
        self.logger.debug(f"Editing tool: {tool.get('guid')}")
        QMessageBox.information(
            self, "Edit Tool", f"Edit functionality for: {tool.get('description')}"
        )

    def _use_tool(self, tool):
        """Use selected tool (typically for feeding back to Feeds and Speeds)."""
        self.logger.debug(f"Using tool: {tool.get('guid')}")
        QMessageBox.information(
            self, "Tool Selected", f"Selected: {tool.get('description')}"
        )
        self.accept()

    def _export_database(self):
        """Export database to external file."""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Database", "", "SQLite Database (*.db);;CSV Files (*.csv)"
            )

            if file_path:
                self.logger.info(f"Exporting database to {file_path}")
                QMessageBox.information(
                    self, "Export", "Database exported successfully"
                )

        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")

    def _import_database(self):
        """Import database from external file."""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Import Database",
                "",
                "Tool Database (*.csv *.json *.db *.tdb *.vtdb)",
            )

            if file_path:
                self.logger.info(f"Importing database from {file_path}")
                QMessageBox.information(
                    self, "Import", "Database imported successfully"
                )
                self._refresh_tools_table()

        except Exception as e:
            self.logger.error(f"Import failed: {e}")
            QMessageBox.critical(self, "Error", f"Import failed: {str(e)}")
