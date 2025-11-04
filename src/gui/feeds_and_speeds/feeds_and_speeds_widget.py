"""Feeds & Speeds Calculator Widget."""

from pathlib import Path
from typing import Optional, Dict, Any
import json

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSplitter,
    QMessageBox,
    QMenu,
    QDialog,
)
from PySide6.QtCore import Qt

from src.core.logging_config import get_logger
from src.parsers.tool_database_manager import ToolDatabaseManager
from src.core.database.provider_repository import ProviderRepository
from src.gui.widgets.add_tool_dialog import AddToolDialog
from .tool_library_manager import ToolLibraryManager, Tool
from .personal_toolbox_manager import PersonalToolboxManager
from .unit_converter import UnitConverter
from src.core.services.tab_data_manager import TabDataManager
from src.core.database_manager import get_database_manager

logger = get_logger(__name__)


class FeedsAndSpeedsWidget(QWidget):
    """Main Feeds & Speeds Calculator Widget."""

    def __init__(self, parent=None):
        """Initialize the widget."""
        super().__init__(parent)
        self.logger = logger

        # Initialize database path
        self.db_path = str(Path.home() / ".digital_workshop" / "tools.db")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize managers
        self.tool_database_manager = ToolDatabaseManager(self.db_path)
        self.provider_repo = ProviderRepository(self.db_path)
        self.personal_toolbox_manager = PersonalToolboxManager()
        self.unit_converter = UnitConverter()
        self.tab_data_manager = TabDataManager(get_database_manager())

        # Keep old manager for backward compatibility during migration
        self.tool_library_manager = ToolLibraryManager()

        # Load default library (import if needed)
        self._load_default_library()

        # UI state
        self.is_metric = self.personal_toolbox_manager.get_auto_convert_to_metric()
        self.selected_tool: Optional[Dict[str, Any]] = None
        self.selected_provider_id: Optional[int] = None
        self.current_project_id: Optional[str] = None

        # Setup UI
        self._setup_ui()

    def _load_default_library(self) -> None:
        """Load the default IDC Woodcraft library and import to database if needed."""
        try:
            # Check if we have any providers in the database
            providers = self.provider_repo.get_all_providers()

            if not providers:
                # Import default library to database
                library_path = (
                    Path(__file__).parent.parent / "IDCWoodcraftFusion360Library.json"
                )
                if library_path.exists():
                    self.logger.info("Importing default library to database...")
                    success, message = (
                        self.tool_database_manager.import_tools_from_file(
                            str(library_path), "IDC Woodcraft"
                        )
                    )
                    if success:
                        self.logger.info(f"Default library imported: {message}")
                    else:
                        self.logger.warning(
                            f"Failed to import default library: {message}"
                        )
                        # Fall back to old manager
                        self.tool_library_manager.load_library(
                            "IDC Woodcraft", str(library_path)
                        )
                else:
                    self.logger.warning(f"Library not found: {library_path}")
            else:
                self.logger.info(f"Found {len(providers)} providers in database")

        except Exception as e:
            self.logger.error(f"Failed to load default library: {e}")

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # Header with title and unit toggle
        header_layout = QHBoxLayout()
        title = QLabel("Feeds & Speeds Calculator")
        title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Unit toggle button
        self.unit_toggle_btn = QPushButton("SAE ⇄ MET")
        self.unit_toggle_btn.setMaximumWidth(100)
        self.unit_toggle_btn.setCheckable(True)
        self.unit_toggle_btn.setChecked(self.is_metric)
        self.unit_toggle_btn.clicked.connect(self._on_unit_toggle)
        self._update_unit_button_style()
        header_layout.addWidget(self.unit_toggle_btn)

        main_layout.addLayout(header_layout)

        # Main content splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left panel: Tool Library
        left_panel = self._create_tool_library_panel()
        splitter.addWidget(left_panel)

        # Right panel: Calculator
        right_panel = self._create_calculator_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter, 1)

        self.setLayout(main_layout)

    def _create_tool_library_panel(self) -> QWidget:
        """Create the tool library panel."""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title = QLabel("Tool Library")
        title.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(title)

        # Library selector (provider selector)
        lib_layout = QHBoxLayout()
        lib_layout.addWidget(QLabel("Provider:"))
        self.library_combo = QComboBox()
        lib_layout.addWidget(self.library_combo)

        # Add Tool button
        self.import_tool_btn = QPushButton("Import Tools...")
        self.import_tool_btn.clicked.connect(self._on_import_tools)
        lib_layout.addWidget(self.import_tool_btn)

        layout.addLayout(lib_layout)

        # Load providers into combo box
        self._load_providers()

        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search tools...")
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Tools table
        self.tools_table = QTableWidget()
        self.tools_table.setColumnCount(3)
        self.tools_table.setHorizontalHeaderLabels(["Tool", "Type", "Diameter"])
        self.tools_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tools_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )
        self.tools_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents
        )
        self.tools_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.tools_table.setSelectionMode(QTableWidget.SingleSelection)
        self.tools_table.itemSelectionChanged.connect(self._on_tool_selected)
        self.tools_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tools_table.customContextMenuRequested.connect(self._on_tool_context_menu)
        layout.addWidget(self.tools_table)

        # Action buttons
        button_layout = QHBoxLayout()

        self.add_tool_btn = QPushButton(">> Add to My Toolbox")
        self.add_tool_btn.clicked.connect(self._on_add_tool)
        button_layout.addWidget(self.add_tool_btn)

        self.add_from_db_btn = QPushButton("Add from Database...")
        self.add_from_db_btn.clicked.connect(self._on_add_from_database)
        button_layout.addWidget(self.add_from_db_btn)

        layout.addLayout(button_layout)

        panel.setLayout(layout)
        self._populate_tools_table()
        # Connect signal after initial setup to prevent premature triggers
        self.library_combo.currentTextChanged.connect(self._on_library_changed)
        return panel

    def _create_calculator_panel(self) -> QWidget:
        """Create the calculator panel."""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title = QLabel("Calculator")
        title.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(title)

        # Selected tool display
        self.selected_tool_label = QLabel("No tool selected")
        self.selected_tool_label.setStyleSheet(
            "background-color: #f0f0f0; padding: 8px; border-radius: 4px;"
        )
        layout.addWidget(self.selected_tool_label)

        # Input fields
        form_layout = QVBoxLayout()

        # RPM
        rpm_layout = QHBoxLayout()
        rpm_layout.addWidget(QLabel("RPM:"))
        self.rpm_input = QSpinBox()
        self.rpm_input.setRange(100, 50000)
        self.rpm_input.setValue(10000)
        rpm_layout.addWidget(self.rpm_input)
        rpm_layout.addStretch()
        form_layout.addLayout(rpm_layout)

        # Feed Rate
        feed_layout = QHBoxLayout()
        feed_layout.addWidget(QLabel("Feed Rate:"))
        self.feed_input = QDoubleSpinBox()
        self.feed_input.setRange(0.1, 1000.0)
        self.feed_input.setValue(50.0)
        self.feed_input.setSuffix(" in/min")
        feed_layout.addWidget(self.feed_input)
        feed_layout.addStretch()
        form_layout.addLayout(feed_layout)

        # Stepdown
        stepdown_layout = QHBoxLayout()
        stepdown_layout.addWidget(QLabel("Stepdown:"))
        self.stepdown_input = QDoubleSpinBox()
        self.stepdown_input.setRange(0.01, 10.0)
        self.stepdown_input.setValue(0.25)
        self.stepdown_input.setSuffix(" in")
        stepdown_layout.addWidget(self.stepdown_input)
        stepdown_layout.addStretch()
        form_layout.addLayout(stepdown_layout)

        # Stepover
        stepover_layout = QHBoxLayout()
        stepover_layout.addWidget(QLabel("Stepover:"))
        self.stepover_input = QDoubleSpinBox()
        self.stepover_input.setRange(0.01, 10.0)
        self.stepover_input.setValue(0.125)
        self.stepover_input.setSuffix(" in")
        stepover_layout.addWidget(self.stepover_input)
        stepover_layout.addStretch()
        form_layout.addLayout(stepover_layout)

        layout.addLayout(form_layout)
        layout.addStretch()

        # Results display
        results_label = QLabel("Results")
        results_label.setStyleSheet("font-weight: bold; margin-top: 12px;")
        layout.addWidget(results_label)

        self.results_display = QLabel(
            "Select a tool and adjust parameters to see results"
        )
        self.results_display.setStyleSheet(
            "background-color: #f9f9f9; padding: 8px; border-radius: 4px; font-family: monospace;"
        )
        self.results_display.setWordWrap(True)
        layout.addWidget(self.results_display)

        panel.setLayout(layout)
        return panel

    def _load_providers(self) -> None:
        """Load providers from database into combo box."""
        try:
            self.library_combo.clear()
            self.library_combo.addItem("My Toolbox")

            providers = self.provider_repo.get_all_providers()
            for provider in providers:
                self.library_combo.addItem(provider["name"])

            self.logger.info(f"Loaded {len(providers)} providers")
        except Exception as e:
            self.logger.error(f"Failed to load providers: {e}")

    def _on_import_tools(self) -> None:
        """Handle import tools button click."""
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Tool Database",
            str(Path.home()),
            "Tool Files (*.json *.csv *.vtdb *.tdb);;All Files (*.*)",
        )

        if file_path:
            try:
                success, message = self.tool_database_manager.import_tools_from_file(
                    file_path
                )
                if success:
                    QMessageBox.information(self, "Success", message)
                    self._load_providers()
                    self._populate_tools_table()
                else:
                    QMessageBox.warning(self, "Import Failed", message)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import: {str(e)}")
                self.logger.error(f"Import error: {e}")

    def _on_add_from_database(self) -> None:
        """Open Add Tool dialog to select tools from database."""
        dialog = AddToolDialog(self.db_path, self)
        if dialog.exec() == QDialog.Accepted:
            tool_data = dialog.get_selected_tool()
            if tool_data:
                # Convert to UI Tool format and add to personal toolbox
                ui_tool = self._convert_db_tool_to_ui(tool_data)
                if self.personal_toolbox_manager.add_tool(ui_tool):
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Added '{tool_data['description']}' to your toolbox.",
                    )
                else:
                    QMessageBox.warning(
                        self, "Already Added", "This tool is already in your toolbox."
                    )

    def _convert_db_tool_to_ui(self, db_tool: Dict[str, Any]) -> "Tool":
        """Convert database tool format to UI Tool format.

        Args:
            db_tool: Tool data from database

        Returns:
            Tool object for UI
        """
        from .tool_library_manager import Tool

        # Parse geometry and start_values if stored as properties
        geometry = {}
        start_values = {}

        # Try to load from properties
        properties = db_tool.get("properties", {})
        if isinstance(properties, dict):
            geometry = properties.get("geometry", {})
            start_values = properties.get("start_values", {})

        # If not in properties, try direct fields (for legacy data)
        if not geometry and "geometry" in db_tool:
            geometry = (
                db_tool["geometry"] if isinstance(db_tool["geometry"], dict) else {}
            )
        if not start_values and "start_values" in db_tool:
            start_values = (
                db_tool["start_values"]
                if isinstance(db_tool["start_values"], dict)
                else {}
            )

        return Tool(
            guid=db_tool.get("guid", ""),
            description=db_tool.get("description", ""),
            tool_type=db_tool.get("tool_type", ""),
            diameter=db_tool.get("diameter", 0.0),
            vendor=db_tool.get("vendor", ""),
            product_id=db_tool.get("product_id", ""),
            geometry=geometry,
            start_values=start_values,
            unit=db_tool.get("unit", "inches"),
        )

    def _populate_tools_table(self) -> None:
        """Populate the tools table."""
        provider_name = self.library_combo.currentText()

        if provider_name == "My Toolbox":
            tools = self.personal_toolbox_manager.get_toolbox()
            # Convert to dict format for consistency
            tools = [tool.to_dict() for tool in tools]
        else:
            # Load from database
            try:
                provider = self.provider_repo.get_provider_by_name(provider_name)
                if provider:
                    self.selected_provider_id = provider["id"]
                    tools = self.tool_database_manager.get_tools_by_provider(
                        provider["id"]
                    )
                else:
                    tools = []
            except Exception as e:
                self.logger.error(f"Failed to load tools: {e}")
                tools = []

        self.tools_table.setRowCount(len(tools))

        for row, tool in enumerate(tools):
            # Description
            desc_item = QTableWidgetItem(tool.get("description", ""))
            self.tools_table.setItem(row, 0, desc_item)

            # Type
            type_item = QTableWidgetItem(tool.get("tool_type", ""))
            self.tools_table.setItem(row, 1, type_item)

            # Diameter
            diameter = tool.get("diameter", 0.0)
            if self.is_metric:
                diameter = self.unit_converter.inch_to_mm(diameter)
                unit = "mm"
            else:
                unit = "in"
            diam_item = QTableWidgetItem(f"{diameter:.3f} {unit}")
            self.tools_table.setItem(row, 2, diam_item)

    def _on_library_changed(self) -> None:
        """Handle library selection change."""
        self._populate_tools_table()
        self.search_input.clear()

    def _on_search_changed(self) -> None:
        """Handle search input change."""
        query = self.search_input.text()
        provider_name = self.library_combo.currentText()

        if provider_name == "My Toolbox":
            tools = self.personal_toolbox_manager.get_toolbox()
            if query:
                tools = [t for t in tools if query.lower() in t.description.lower()]
            # Convert to dict format
            tools = [tool.to_dict() for tool in tools]
        else:
            # Search in database
            try:
                if query:
                    tools = self.tool_database_manager.search_tools(
                        query, self.selected_provider_id
                    )
                else:
                    # Show all tools for provider
                    if self.selected_provider_id:
                        tools = self.tool_database_manager.get_tools_by_provider(
                            self.selected_provider_id
                        )
                    else:
                        tools = []
            except Exception as e:
                self.logger.error(f"Search failed: {e}")
                tools = []

        self.tools_table.setRowCount(len(tools))

        for row, tool in enumerate(tools):
            desc_item = QTableWidgetItem(tool.get("description", ""))
            self.tools_table.setItem(row, 0, desc_item)

            type_item = QTableWidgetItem(tool.get("tool_type", ""))
            self.tools_table.setItem(row, 1, type_item)

            diameter = tool.get("diameter", 0.0)
            if self.is_metric:
                diameter = self.unit_converter.inch_to_mm(diameter)
                unit = "mm"
            else:
                unit = "in"
            diam_item = QTableWidgetItem(f"{diameter:.3f} {unit}")
            self.tools_table.setItem(row, 2, diam_item)

    def _on_tool_selected(self) -> None:
        """Handle tool selection."""
        current_row = self.tools_table.currentRow()
        if current_row < 0:
            return

        # Get tool from current provider
        provider_name = self.library_combo.currentText()
        if provider_name == "My Toolbox":
            tools = self.personal_toolbox_manager.get_toolbox()
            tools = [tool.to_dict() for tool in tools]
        else:
            # Get from database
            try:
                if self.selected_provider_id:
                    tools = self.tool_database_manager.get_tools_by_provider(
                        self.selected_provider_id
                    )
                else:
                    tools = []
            except Exception as e:
                self.logger.error(f"Failed to load tools: {e}")
                tools = []

        if current_row < len(tools):
            self.selected_tool = tools[current_row]
            self.selected_tool_label.setText(
                f"Selected: {self.selected_tool.get('description', '')}"
            )
            self._update_calculator()

    def _on_tool_context_menu(self, pos) -> None:
        """Handle right-click context menu."""
        if self.library_combo.currentText() == "My Toolbox":
            return

        menu = QMenu()
        add_action = menu.addAction("Add to My Toolbox")
        action = menu.exec(self.tools_table.mapToGlobal(pos))

        if action == add_action:
            self._on_add_tool()

    def _on_add_tool(self) -> None:
        """Add selected tool to personal toolbox."""
        if not self.selected_tool:
            QMessageBox.warning(self, "No Tool Selected", "Please select a tool first.")
            return

        # Convert to UI Tool format
        ui_tool = self._convert_db_tool_to_ui(self.selected_tool)

        if self.personal_toolbox_manager.add_tool(ui_tool):
            QMessageBox.information(
                self,
                "Success",
                f"Added '{self.selected_tool.get('description', '')}' to your toolbox.",
            )
        else:
            QMessageBox.warning(
                self, "Already Added", "This tool is already in your toolbox."
            )

    def _on_unit_toggle(self) -> None:
        """Handle unit toggle button."""
        self.is_metric = self.unit_toggle_btn.isChecked()
        self.personal_toolbox_manager.set_auto_convert_to_metric(self.is_metric)
        self._update_unit_button_style()
        self._populate_tools_table()
        self._update_calculator()

    def _update_unit_button_style(self) -> None:
        """Update unit toggle button style."""
        if self.is_metric:
            self.unit_toggle_btn.setText("MET ✓")
            self.unit_toggle_btn.setStyleSheet(
                "background-color: #4CAF50; color: white;"
            )
        else:
            self.unit_toggle_btn.setText("SAE")
            self.unit_toggle_btn.setStyleSheet("")

    def _update_calculator(self) -> None:
        """Update calculator display."""
        if not self.selected_tool:
            self.results_display.setText("Select a tool to see calculations")
            return

        # Get preset values from start_values
        start_values = self.selected_tool.get("start_values", {})
        if isinstance(start_values, str):
            try:
                start_values = json.loads(start_values)
            except (json.JSONDecodeError, TypeError, ValueError):
                start_values = {}

        # Check for presets array
        presets = start_values.get("presets", [])
        if presets and isinstance(presets, list) and len(presets) > 0:
            preset = presets[0]
            rpm = preset.get("n", 10000)
            feed = preset.get("v_f", 50.0)
            stepdown = preset.get("stepdown", 0.25)
            stepover = preset.get("stepover", 0.125)

            # Update inputs
            self.rpm_input.setValue(int(rpm))
            self.feed_input.setValue(feed)
            self.stepdown_input.setValue(stepdown)
            self.stepover_input.setValue(stepover)

        # Display results
        results = self._calculate_results()
        self.results_display.setText(results)

    def _calculate_results(self) -> str:
        """Calculate and format results."""
        if not self.selected_tool:
            return "No tool selected"

        rpm = self.rpm_input.value()
        feed = self.feed_input.value()
        stepdown = self.stepdown_input.value()
        stepover = self.stepover_input.value()
        diameter = self.selected_tool.get("diameter", 0.0)

        # Calculate surface speed
        surface_speed = (rpm * 3.14159 * diameter) / 12.0

        # Format results
        results = f"""
Tool: {self.selected_tool.get('description', '')}
Diameter: {self.unit_converter.format_value(diameter, self.is_metric, 'length')}

Parameters:
  RPM: {rpm}
  Feed Rate: {self.unit_converter.format_value(feed, self.is_metric, 'feed_rate')}
  Stepdown: {self.unit_converter.format_value(stepdown, self.is_metric, 'length')}
  Stepover: {self.unit_converter.format_value(stepover, self.is_metric, 'length')}

Calculated:
  Surface Speed: {self.unit_converter.format_value(surface_speed, self.is_metric, 'feed_rate')}
  Material Removal Rate: {(stepdown * stepover * feed):.2f} cu.in/min
        """

        return results.strip()

    def set_current_project(self, project_id: str) -> None:
        """Set the current project for saving/loading data."""
        self.current_project_id = project_id

    def save_to_project(self) -> None:
        """Save feeds and speeds data to current project."""
        if not self.current_project_id:
            QMessageBox.warning(self, "No Project", "Please select a project first")
            return

        # Gather data from personal toolbox
        tools_data = self.personal_toolbox_manager.get_all_tools()
        presets_data = self.personal_toolbox_manager.get_all_presets()

        # Create data structure
        feeds_speeds_data = {
            "tools": tools_data,
            "presets": presets_data,
            "is_metric": self.is_metric,
        }

        # Save to project
        success, message = self.tab_data_manager.save_tab_data_to_project(
            project_id=self.current_project_id,
            tab_name="Feed and Speed",
            data=feeds_speeds_data,
            filename="feeds_and_speeds.json",
            category="Feed and Speed",
        )

        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)

    def load_from_project(self) -> None:
        """Load feeds and speeds data from current project."""
        if not self.current_project_id:
            QMessageBox.warning(self, "No Project", "Please select a project first")
            return

        # Load from project
        success, data, message = self.tab_data_manager.load_tab_data_from_project(
            project_id=self.current_project_id, filename="feeds_and_speeds.json"
        )

        if not success:
            QMessageBox.warning(self, "Load Failed", message)
            return

        # Restore data to personal toolbox
        try:
            tools_data = data.get("tools", [])
            presets_data = data.get("presets", [])

            # Clear existing tools and presets
            self.personal_toolbox_manager.clear_all()

            # Restore tools
            for tool in tools_data:
                self.personal_toolbox_manager.add_tool(tool)

            # Restore presets
            for preset in presets_data:
                self.personal_toolbox_manager.add_preset(preset)

            # Refresh UI
            self._refresh_tool_list()

            QMessageBox.information(self, "Success", message)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to restore data: {str(e)}")
