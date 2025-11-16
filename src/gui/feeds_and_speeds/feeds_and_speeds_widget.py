"""Feeds & Speeds Calculator Widget."""

from pathlib import Path
from typing import Optional, Dict, Any
import json
import os

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QPushButton,
    QLabel,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QSplitter,
    QMessageBox,
    QMenu,
    QDialog,
    QTreeWidget,
    QTreeWidgetItem,
    QComboBox,
    QCheckBox,
    QDialogButtonBox,
)
from PySide6.QtCore import Qt, QSettings

from src.core.logging_config import get_logger
from src.parsers.tool_database_manager import ToolDatabaseManager
from src.parsers.tool_parsers.vtdb_tool_parser import VTDBToolParser
from src.core.database.provider_repository import ProviderRepository
from src.gui.widgets.add_tool_dialog import AddToolDialog
from .tool_library_manager import ToolLibraryManager, Tool
from .personal_toolbox_manager import PersonalToolboxManager
from .unit_converter import UnitConverter
from src.core.services.tab_data_manager import TabDataManager
from src.core.database_manager import get_database_manager

logger = get_logger(__name__)

TREE_GROUPING_CHOICES = [
    ("none", "None"),
    ("tool_type", "Tool Type"),
    ("vendor", "Vendor"),
    ("unit", "Unit"),
    ("shank_diameter", "Shank Diameter"),
    ("number_of_flutes", "Number of Flutes"),
]

def _find_vectric_tool_databases() -> list[tuple[str, str, str]]:
    """Find Vectric tool databases under ProgramData.

    Only VTDB files that validate with :class:`VTDBToolParser` are returned.

    Returns:
        list of (product_name, version, db_path).
    """
    results: list[tuple[str, str, str]] = []
    seen: set[str] = set()

    try:
        program_data = Path(os.environ.get("PROGRAMDATA", r"C:\\ProgramData"))
    except Exception:
        return results

    parser = VTDBToolParser()

    base_dirs = [
        program_data / "Vectric",
        program_data / "Vetric",
    ]

    for base in base_dirs:
        if not base.is_dir():
            continue
        for product_dir in base.iterdir():
            if not product_dir.is_dir():
                continue
            product_name = product_dir.name
            for version_dir in product_dir.iterdir():
                if not version_dir.is_dir():
                    continue
                version_name = version_dir.name
                tool_db_dir = version_dir / "ToolDatabase"
                if not tool_db_dir.is_dir():
                    continue

                vtdb_files: list[Path] = []
                preferred = tool_db_dir / "tools.vtdb"
                if preferred.is_file():
                    vtdb_files.append(preferred)
                else:
                    vtdb_files.extend(tool_db_dir.glob("*.vtdb"))

                for vtdb in vtdb_files:
                    try:
                        key = str(vtdb.resolve())
                    except OSError:
                        key = str(vtdb)

                    if key in seen:
                        continue

                    # Only include VTDB files that have the expected 'tools' table
                    try:
                        valid, _ = parser.validate_file(key)
                    except Exception:
                        valid = False

                    if not valid:
                        continue

                    seen.add(key)
                    results.append((product_name, version_name, key))

    return results


class VectricToolImportDialog(QDialog):
    """Dialog for selecting Vectric tool databases to import."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Import Vectric Tool Databases")

        self._installations: list[tuple[str, str, str]] = _find_vectric_tool_databases()
        self._checkboxes: list[QCheckBox] = []

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        if not self._installations:
            layout.addWidget(
                QLabel("No Vectric tool databases were found under ProgramData.")
            )
        else:
            layout.addWidget(
                QLabel("Select which Vectric tool databases to import:")
            )
            for product, version, db_path in self._installations:
                checkbox = QCheckBox(f"Import {product} - {version} tools")
                checkbox.setToolTip(db_path)
                checkbox.setChecked(True)
                self._checkboxes.append(checkbox)
                layout.addWidget(checkbox)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

        # Disable OK if there is nothing to import
        if not self._installations:
            for button in button_box.buttons():
                if button_box.buttonRole(button) == QDialogButtonBox.AcceptRole:
                    button.setEnabled(False)
                    break

    def get_selected_databases(self) -> list[tuple[str, str, str]]:
        """Return list of (product, version, db_path) selected by the user."""
        selected: list[tuple[str, str, str]] = []
        for index, checkbox in enumerate(self._checkboxes):
            if checkbox.isChecked():
                selected.append(self._installations[index])
        return selected



class ToolTreeLayoutDialog(QDialog):
    """Dialog for configuring tool tree grouping and visible columns."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Tool Tree Layout")
        self.settings = QSettings()

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        layout.addWidget(QLabel("Grouping (inside each provider and My Tools):"))

        self.level1_combo = QComboBox()
        self.level2_combo = QComboBox()
        self.level3_combo = QComboBox()
        for combo in (self.level1_combo, self.level2_combo, self.level3_combo):
            for key, label in TREE_GROUPING_CHOICES:
                combo.addItem(label, key)

        level1_layout = QHBoxLayout()
        level1_layout.addWidget(QLabel("Level 1:"))
        level1_layout.addWidget(self.level1_combo)
        layout.addLayout(level1_layout)

        level2_layout = QHBoxLayout()
        level2_layout.addWidget(QLabel("Level 2:"))
        level2_layout.addWidget(self.level2_combo)
        layout.addLayout(level2_layout)

        level3_layout = QHBoxLayout()
        level3_layout.addWidget(QLabel("Level 3:"))
        level3_layout.addWidget(self.level3_combo)
        layout.addLayout(level3_layout)

        layout.addWidget(QLabel("Columns:"))

        self.type_checkbox = QCheckBox("Type")
        self.diameter_checkbox = QCheckBox("Diameter")
        self.vendor_checkbox = QCheckBox("Vendor")
        self.product_id_checkbox = QCheckBox("Product ID")
        self.custom_checkbox = QCheckBox("Custom")

        columns_layout = QHBoxLayout()
        columns_layout.addWidget(self.type_checkbox)
        columns_layout.addWidget(self.diameter_checkbox)
        columns_layout.addWidget(self.vendor_checkbox)
        columns_layout.addWidget(self.product_id_checkbox)
        columns_layout.addWidget(self.custom_checkbox)
        columns_layout.addStretch()
        layout.addLayout(columns_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)
        self._load_settings()

    def _set_combo_value(self, combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        if index < 0:
            index = combo.findData("none")
        if index >= 0:
            combo.setCurrentIndex(index)

    def _load_settings(self) -> None:
        """Load current grouping and column settings from QSettings."""
        try:
            # Grouping levels
            level1 = self.settings.value(
                "feeds_and_speeds/tree_group_level1", "tool_type", type=str
            )
            level2 = self.settings.value(
                "feeds_and_speeds/tree_group_level2", "none", type=str
            )
            level3 = self.settings.value(
                "feeds_and_speeds/tree_group_level3", "none", type=str
            )
            self._set_combo_value(self.level1_combo, level1 or "tool_type")
            self._set_combo_value(self.level2_combo, level2 or "none")
            self._set_combo_value(self.level3_combo, level3 or "none")

            # Column visibility
            raw_value = self.settings.value(
                "feeds_and_speeds/tool_tree_visible_columns", "", type=str
            )
            visible: dict[int, bool]
            if raw_value:
                parts = [p for p in raw_value.split(",") if ":" in p]
                visible = {}
                for part in parts:
                    idx_str, flag = part.split(":", 1)
                    try:
                        idx = int(idx_str)
                        visible[idx] = flag == "1"
                    except ValueError:
                        continue
            else:
                visible = {0: True, 1: True, 2: True, 3: False, 4: False, 5: False}

            self.type_checkbox.setChecked(visible.get(1, True))
            self.diameter_checkbox.setChecked(visible.get(2, True))
            self.vendor_checkbox.setChecked(visible.get(3, False))
            self.product_id_checkbox.setChecked(visible.get(4, False))
            self.custom_checkbox.setChecked(visible.get(5, False))
        except Exception:
            # On any failure, fall back to sensible defaults
            self._set_combo_value(self.level1_combo, "tool_type")
            self._set_combo_value(self.level2_combo, "none")
            self._set_combo_value(self.level3_combo, "none")
            self.type_checkbox.setChecked(True)
            self.diameter_checkbox.setChecked(True)
            self.vendor_checkbox.setChecked(False)
            self.product_id_checkbox.setChecked(False)
            self.custom_checkbox.setChecked(False)

    def accept(self) -> None:
        """Persist settings and close the dialog."""
        try:
            level1 = self.level1_combo.currentData()
            level2 = self.level2_combo.currentData()
            level3 = self.level3_combo.currentData()
            self.settings.setValue("feeds_and_speeds/tree_group_level1", level1)
            self.settings.setValue("feeds_and_speeds/tree_group_level2", level2)
            self.settings.setValue("feeds_and_speeds/tree_group_level3", level3)

            visible = {
                0: True,
                1: self.type_checkbox.isChecked(),
                2: self.diameter_checkbox.isChecked(),
                3: self.vendor_checkbox.isChecked(),
                4: self.product_id_checkbox.isChecked(),
                5: self.custom_checkbox.isChecked(),
            }
            parts: list[str] = []
            for col in range(6):
                parts.append(f"{col}:{1 if visible.get(col, True) else 0}")
            self.settings.setValue(
                "feeds_and_speeds/tool_tree_visible_columns", ",".join(parts)
            )
            self.settings.sync()
        except Exception:
            # If saving fails, do not block closing the dialog
            pass

        super().accept()



class FeedsAndSpeedsWidget(QWidget):
    """Main Feeds & Speeds Calculator Widget."""

    def __init__(self, parent=None) -> None:
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
        self.selected_tool_source: Optional[str] = None
        self.selected_provider_id: Optional[int] = None
        self.current_project_id: Optional[str] = None

        # Setup UI
        self._setup_ui()

    def _load_default_library(self) -> None:
        """Load bundled vendor tool libraries into the database on first run.

        This method keeps vendor databases separate so they can be updated or
        replaced later without touching the user's personal toolbox.
        """
        try:
            # Check if we have any providers in the database already
            providers = self.provider_repo.get_all_providers()
            if providers:
                self.logger.info("Found %s providers in database", len(providers))
                return

            # On first run, import all bundled libraries from resources/ToolLib
            resources_root = Path(__file__).parents[2] / "resources" / "ToolLib"
            if not resources_root.exists():
                self.logger.warning("Tool library resources directory not found: %s", resources_root)
                return

            imported_any = False

            for path in resources_root.iterdir():
                if not path.is_file():
                    continue

                if path.suffix.lower() not in {".json", ".csv", ".vtdb", ".tdb", ".tool"}:
                    continue

                provider_name = path.stem
                self.logger.info("Importing bundled tool library: %s", path.name)

                success, message = self.tool_database_manager.import_tools_from_file(
                    str(path), provider_name, mode="merge"
                )
                if success:
                    imported_any = True
                    self.logger.info("Bundled library imported: %s", message)
                else:
                    self.logger.warning(
                        "Failed to import bundled library %s: %s",
                        path,
                        message,
                    )

            if not imported_any:
                self.logger.warning(
                    "No bundled tool libraries were imported from %s",
                    resources_root,
                )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to load default libraries: %s", e)

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # Header with title and unit toggle
        header_layout = QHBoxLayout()
        title = QLabel("Feeds & Speeds Calculator")
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
        """Create the tool library panel with a hierarchical tree."""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title = QLabel("Tool Library")
        layout.addWidget(title)

        # Import / layout button row
        lib_layout = QHBoxLayout()
        self.import_tool_btn = QPushButton("Import Tools...")
        self.import_tool_btn.clicked.connect(self._on_import_tools)
        lib_layout.addWidget(self.import_tool_btn)

        self.import_vectric_btn = QPushButton("Import from Vectric...")
        self.import_vectric_btn.clicked.connect(self._on_import_from_vectric)
        lib_layout.addWidget(self.import_vectric_btn)

        self.tool_tree_layout_btn = QPushButton("Tree Layout...")
        self.tool_tree_layout_btn.clicked.connect(self._on_open_tool_tree_layout)
        lib_layout.addWidget(self.tool_tree_layout_btn)

        lib_layout.addStretch()
        layout.addLayout(lib_layout)

        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search tools...")
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Tool tree
        self.tool_tree = QTreeWidget()
        # Columns: 0=Tool, 1=Type, 2=Diameter, 3=Vendor, 4=Product ID, 5=Custom
        self.tool_tree.setColumnCount(6)
        self.tool_tree.setHeaderLabels([
            "Tool",
            "Type",
            "Diameter",
            "Vendor",
            "Product ID",
            "Custom",
        ])
        self.tool_tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.tool_tree.itemSelectionChanged.connect(self._on_tool_selected)
        self.tool_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        header = self.tool_tree.header()
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self._on_tool_header_context_menu)
        layout.addWidget(self.tool_tree)

        # Restore column visibility from settings
        self._restore_tool_tree_column_visibility()

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

        # Initial population
        self._rebuild_tool_tree()

        return panel


    def _restore_tool_tree_column_visibility(self) -> None:
        """Restore tool tree column visibility from QSettings.

        Column layout is fixed as:
        0=Tool, 1=Type, 2=Diameter, 3=Vendor, 4=Product ID, 5=Custom.
        """
        try:
            settings = QSettings()
            raw_value = settings.value(
                "feeds_and_speeds/tool_tree_visible_columns", "", type=str
            )
            visible: dict[int, bool]
            if raw_value:
                parts = [p for p in raw_value.split(",") if ":" in p]
                visible = {}
                for part in parts:
                    idx_str, flag = part.split(":", 1)
                    try:
                        idx = int(idx_str)
                        visible[idx] = flag == "1"
                    except ValueError:
                        continue
            else:
                # Default: show Tool/Type/Diameter, hide Vendor/Product ID and Custom
                visible = {0: True, 1: True, 2: True, 3: False, 4: False, 5: False}

            for col in range(self.tool_tree.columnCount()):
                is_visible = visible.get(col, True)
                self.tool_tree.setColumnHidden(col, not is_visible)
        except Exception as e:  # pragma: no cover - defensive
            self.logger.debug("Failed to restore tool tree column visibility: %s", e)

    def _save_tool_tree_column_visibility(self) -> None:
        """Persist current tool tree column visibility to QSettings."""
        try:
            settings = QSettings()
            parts: list[str] = []
            for col in range(self.tool_tree.columnCount()):
                visible = not self.tool_tree.isColumnHidden(col)
                parts.append(f"{col}:{1 if visible else 0}")
            settings.setValue(
                "feeds_and_speeds/tool_tree_visible_columns", ",".join(parts)
            )
        except Exception as e:  # pragma: no cover - defensive
            self.logger.debug("Failed to save tool tree column visibility: %s", e)


    def _on_open_tool_tree_layout(self) -> None:
        """Open the Tool Tree Layout dialog and refresh the tree if accepted."""
        dialog = ToolTreeLayoutDialog(self)
        if dialog.exec() == QDialog.Accepted:
            # Dialog persists settings into QSettings; just reapply them here.
            self._restore_tool_tree_column_visibility()
            self._load_providers()

    def _on_tool_header_context_menu(self, pos) -> None:
        """Show a header context menu to toggle visible columns."""
        header = self.tool_tree.header()
        global_pos = header.mapToGlobal(pos)

        menu = QMenu(self)
        labels = ["Tool", "Type", "Diameter", "Vendor", "Product ID", "Custom"]
        for col, label in enumerate(labels):
            action = menu.addAction(label)
            action.setCheckable(True)
            is_visible = not self.tool_tree.isColumnHidden(col)
            action.setChecked(is_visible)
            if col == 0:
                # Always keep the primary Tool column visible
                action.setEnabled(False)
                continue

            def toggle_column(checked: bool, column_index: int = col) -> None:
                self.tool_tree.setColumnHidden(column_index, not checked)
                self._save_tool_tree_column_visibility()

            action.toggled.connect(toggle_column)

        menu.exec(global_pos)

    def _get_tree_grouping_fields(self) -> list[str]:
        """Return configured grouping fields for the tool tree.

        Values are drawn from TREE_GROUPING_CHOICES and normalized so that any
        unexpected value becomes "none".
        """
        settings = QSettings()
        valid_keys = {key for key, _ in TREE_GROUPING_CHOICES}

        def _value(key: str, default: str) -> str:
            raw = settings.value(key, default, type=str) or default
            return raw if raw in valid_keys else "none"

        level1 = _value("feeds_and_speeds/tree_group_level1", "tool_type")
        level2 = _value("feeds_and_speeds/tree_group_level2", "none")
        level3 = _value("feeds_and_speeds/tree_group_level3", "none")
        return [level1, level2, level3]

    def _extract_geometry_property(self, tool_data: Dict[str, Any], prop_name: str) -> Optional[Any]:
        """Extract a geometry property from tool data.

        Supports both database-backed tools (with properties.geometry) and
        personal toolbox tools that may store geometry on the root or under a
        "geometry" key.
        """
        properties = tool_data.get("properties")
        if isinstance(properties, dict):
            geometry = properties.get("geometry") or {}
            if prop_name in geometry:
                return geometry.get(prop_name)

        geometry = tool_data.get("geometry") or {}
        if prop_name in geometry:
            return geometry.get(prop_name)

        alias_map = {
            "shank_diameter": ["SHK", "shank"],
            "number_of_flutes": ["NOF", "flutes"],
        }
        for alias in alias_map.get(prop_name, []):
            if alias in geometry:
                return geometry.get(alias)
    def _get_custom_column_text(self, tool_data: Dict[str, Any]) -> str:
        """Return text for the Custom column.

        For now this surfaces a placeholder value so that the column can be
        enabled/disabled and wired through the layout system. Once we start
        storing material or other custom properties for tools, this method is
        the single place to update to expose that information.
        """
        # Prefer an explicit custom label if one exists in the tool data
        custom_label = tool_data.get("custom_label")
        if isinstance(custom_label, str) and custom_label.strip():
            return custom_label.strip()

        # Fall back to any custom properties dictionary if present
        custom_props = tool_data.get("custom") or tool_data.get("custom_properties")
        if isinstance(custom_props, dict) and custom_props:
            # Join the first couple of key/value pairs into a short summary
            parts = []
            for idx, (key, value) in enumerate(custom_props.items()):
                parts.append(f"{key}={value}")
                if idx >= 1:
                    break
            return "; ".join(parts)

        return ""  # No custom data available yet

    def _get_group_label_for_tool(self, tool_data: Dict[str, Any], field: str) -> str:
        """Compute a human friendly group label for a tool and field."""
        if field == "tool_type":
            raw_type = (tool_data.get("tool_type") or "").strip()
            return raw_type or "Unspecified Type"

        if field == "vendor":
            vendor = (tool_data.get("vendor") or "").strip()
            return vendor or "Unspecified Vendor"

        if field == "unit":
            unit = (tool_data.get("unit") or "").strip()
            return unit or "Unspecified Unit"

        if field == "shank_diameter":
            value = self._extract_geometry_property(tool_data, "shank_diameter")
            if value in (None, ""):
                return "Unspecified Shank Diameter"
            try:
                numeric = float(value)
                return f"{numeric:g}"
            except (TypeError, ValueError):
                return str(value)

        if field == "number_of_flutes":
            value = self._extract_geometry_property(tool_data, "number_of_flutes")
            if value in (None, ""):
                return "Unspecified Flutes"
            try:
                numeric = int(float(value))
                return f"{numeric} flutes"
            except (TypeError, ValueError):
                return str(value)

        # "none" or unknown field
        return "Other"

    def _populate_branch_with_grouping(
        self,
        parent_item: QTreeWidgetItem,
        tools,
        group_fields: list[str],
        filter_text: str,
        source: str,
        provider_id: Optional[int] = None,
    ) -> None:
        """Populate a tree branch with tools grouped according to group_fields."""
        # Normalize grouping fields so we always have three positions.
        fields = [f if f and f != "none" else None for f in (group_fields or [])]
        while len(fields) < 3:
            fields.append(None)

        level1_nodes: dict[str, QTreeWidgetItem] = {}
        level2_nodes: dict[tuple[str, str], QTreeWidgetItem] = {}
        level3_nodes: dict[tuple[str, str, str], QTreeWidgetItem] = {}

        for tool in tools:
            tool_data = tool.to_dict() if hasattr(tool, "to_dict") else dict(tool)

            description = tool_data.get("description", "")
            if filter_text and filter_text not in description.lower():
                continue

            diameter_value = tool_data.get("diameter", 0.0) or 0.0
            try:
                diameter_value = float(diameter_value)
            except (TypeError, ValueError):
                diameter_value = 0.0

            if self.is_metric:
                diameter_value = self.unit_converter.inch_to_mm(diameter_value)
                unit = "mm"
            else:
                unit = "in"

            row_values = [
                description,
                tool_data.get("tool_type", ""),
                f"{diameter_value:.3f} {unit}",
                tool_data.get("vendor", ""),
                tool_data.get("product_id", ""),
                self._get_custom_column_text(tool_data),
            ]

            # Compute group labels for the configured fields
            labels: list[Optional[str]] = []
            for field in fields:
                if field is None:
                    labels.append(None)
                else:
                    labels.append(self._get_group_label_for_tool(tool_data, field))

            current_parent = parent_item

            # Level 1 grouping
            if fields[0]:
                label1 = labels[0] or "Unspecified"
                key1 = label1
                group1 = level1_nodes.get(key1)
                if group1 is None:
                    group1 = QTreeWidgetItem([label1, "", "", "", "", ""])
                    group1.setData(
                        0,
                        Qt.UserRole,
                        {"source": "group", "level": 1, "field": fields[0]},
                    )
                    parent_item.addChild(group1)
                    level1_nodes[key1] = group1
                current_parent = group1

            # Level 2 grouping
            if fields[1]:
                label2 = labels[1] or "Unspecified"
                key2 = ((labels[0] or ""), label2)
                group2 = level2_nodes.get(key2)
                if group2 is None:
                    group2 = QTreeWidgetItem([label2, "", "", "", "", ""])
                    group2.setData(
                        0,
                        Qt.UserRole,
                        {"source": "group", "level": 2, "field": fields[1]},
                    )
                    current_parent.addChild(group2)
                    level2_nodes[key2] = group2
                current_parent = group2

            # Level 3 grouping
            if fields[2]:
                label3 = labels[2] or "Unspecified"
                key3 = ((labels[0] or ""), (labels[1] or ""), label3)
                group3 = level3_nodes.get(key3)
                if group3 is None:
                    group3 = QTreeWidgetItem([label3, "", "", "", "", ""])
                    group3.setData(
                        0,
                        Qt.UserRole,
                        {"source": "group", "level": 3, "field": fields[2]},
                    )
                    current_parent.addChild(group3)
                    level3_nodes[key3] = group3
                current_parent = group3

            item = QTreeWidgetItem(row_values)
            user_data: Dict[str, Any] = {"source": source, "tool_data": tool_data}
            if provider_id is not None:
                user_data["provider_id"] = provider_id
            item.setData(0, Qt.UserRole, user_data)
            current_parent.addChild(item)

    def _rebuild_tool_tree(self, filter_text: str = "") -> None:
        """Rebuild the hierarchical tool tree using configured grouping settings."""
        try:
            if not hasattr(self, "tool_tree"):
                return

            self.tool_tree.clear()
            filter_text = (filter_text or "").strip().lower()

            group_fields = self._get_tree_grouping_fields()

            # My Tools branch (from QSettings-based personal toolbox)
            my_tools_root = QTreeWidgetItem(["My Tools", "", "", "", "", ""])
            my_tools_root.setData(
                0,
                Qt.UserRole,
                {"source": "root", "name": "my_tools"},
            )
            self.tool_tree.addTopLevelItem(my_tools_root)

            toolbox_tools = self.personal_toolbox_manager.get_toolbox()
            self._populate_branch_with_grouping(
                my_tools_root,
                toolbox_tools,
                group_fields,
                filter_text,
                source="my_tools",
            )

            # Provider branches (vendor libraries from tools.db)
            providers = self.provider_repo.get_all_providers()
            for provider in providers:
                provider_root = QTreeWidgetItem([provider["name"], "", "", "", "", ""])
                provider_root.setData(
                    0,
                    Qt.UserRole,
                    {"source": "provider_root", "provider_id": provider["id"]},
                )
                self.tool_tree.addTopLevelItem(provider_root)

                tools = self.tool_database_manager.get_tools_by_provider(provider["id"])
                # Stable ordering inside each group: group_fields may change, but
                # sorting by type + description keeps behaviour predictable.
                tools_sorted = sorted(
                    tools,
                    key=lambda t: (
                        (t.get("tool_type") or "").strip().lower(),
                        (t.get("description") or "").strip().lower(),
                    ),
                )

                self._populate_branch_with_grouping(
                    provider_root,
                    tools_sorted,
                    group_fields,
                    filter_text,
                    source="db",
                    provider_id=provider["id"],
                )

            self.tool_tree.expandAll()
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to rebuild tool tree: %s", e)

    def _create_calculator_panel(self) -> QWidget:
        """Create the calculator panel.

        This panel mirrors a typical CAM tool editor: geometry, cutting
        parameters, and feeds & speeds, plus derived metrics such as chip
        load and surface speed.
        """
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title = QLabel("Calculator")
        layout.addWidget(title)

        # Selected tool display
        self.selected_tool_label = QLabel("No tool selected")
        layout.addWidget(self.selected_tool_label)

        # Geometry group
        geometry_group = QGroupBox("Tool Geometry")
        geometry_layout = QFormLayout()

        self.diameter_input = QDoubleSpinBox()
        self.diameter_input.setRange(0.01, 1000.0)
        self.diameter_input.setDecimals(3)
        self.diameter_input.setValue(0.25)
        geometry_layout.addRow("Diameter:", self.diameter_input)

        self.flutes_input = QSpinBox()
        self.flutes_input.setRange(1, 20)
        self.flutes_input.setValue(2)
        geometry_layout.addRow("Flutes:", self.flutes_input)

        geometry_group.setLayout(geometry_layout)
        layout.addWidget(geometry_group)

        # Cutting parameters group
        cutting_group = QGroupBox("Cutting Parameters")
        cutting_layout = QFormLayout()

        self.stepdown_input = QDoubleSpinBox()
        self.stepdown_input.setRange(0.001, 100.0)
        self.stepdown_input.setDecimals(3)
        self.stepdown_input.setValue(0.25)
        cutting_layout.addRow("Pass depth (stepdown):", self.stepdown_input)

        self.stepover_input = QDoubleSpinBox()
        self.stepover_input.setRange(0.001, 100.0)
        self.stepover_input.setDecimals(3)
        self.stepover_input.setValue(0.125)
        cutting_layout.addRow("Stepover:", self.stepover_input)

        cutting_group.setLayout(cutting_layout)
        layout.addWidget(cutting_group)

        # Feeds & speeds group
        feeds_group = QGroupBox("Feeds && Speeds")
        feeds_layout = QFormLayout()

        self.rpm_input = QSpinBox()
        self.rpm_input.setRange(100, 100000)
        self.rpm_input.setSingleStep(100)
        self.rpm_input.setValue(18000)
        feeds_layout.addRow("Spindle speed (RPM):", self.rpm_input)

        self.feed_input = QDoubleSpinBox()
        self.feed_input.setRange(0.01, 50000.0)
        self.feed_input.setDecimals(2)
        self.feed_input.setValue(100.0)
        feeds_layout.addRow("Feed rate:", self.feed_input)

        self.plunge_input = QDoubleSpinBox()
        self.plunge_input.setRange(0.01, 50000.0)
        self.plunge_input.setDecimals(2)
        self.plunge_input.setValue(50.0)
        feeds_layout.addRow("Plunge rate:", self.plunge_input)

        feeds_group.setLayout(feeds_layout)
        layout.addWidget(feeds_group)

        # Wire change handlers so all fields recompute derived metrics
        for spin in (
            self.diameter_input,
            self.flutes_input,
            self.stepdown_input,
            self.stepover_input,
            self.rpm_input,
            self.feed_input,
            self.plunge_input,
        ):
            spin.valueChanged.connect(self._on_parameters_changed)

        # Derived metrics display
        results_group = QGroupBox("Derived Metrics")
        results_layout = QVBoxLayout()
        self.results_display = QLabel(
            "Select a tool and adjust parameters to see chip load, surface speed,\n"
            "and material removal rate."
        )
        self.results_display.setWordWrap(True)
        results_layout.addWidget(self.results_display)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        layout.addStretch()

        panel.setLayout(layout)

        # Apply initial unit suffixes
        self._update_calculator_unit_suffixes()

        return panel

    def _update_calculator_unit_suffixes(self) -> None:
        """Update suffixes for calculator fields based on current unit system."""
        if not hasattr(self, "unit_converter"):
            return

        length_label = self.unit_converter.get_unit_label(self.is_metric, "length")
        feed_label = self.unit_converter.get_unit_label(self.is_metric, "feed_rate")

        if hasattr(self, "diameter_input"):
            self.diameter_input.setSuffix(f" {length_label}")
        if hasattr(self, "stepdown_input"):
            self.stepdown_input.setSuffix(f" {length_label}")
        if hasattr(self, "stepover_input"):
            self.stepover_input.setSuffix(f" {length_label}")
        if hasattr(self, "feed_input"):
            self.feed_input.setSuffix(f" {feed_label}")
        if hasattr(self, "plunge_input"):
            self.plunge_input.setSuffix(f" {feed_label}")

    def _convert_current_calculator_units(self, to_metric: bool) -> None:
        """Convert calculator field values between SAE and metric.

        This is used when the unit toggle is changed so that all displayed
        values stay consistent with the selected unit system.
        """
        if not hasattr(self, "unit_converter") or not hasattr(self, "diameter_input"):
            return

        if to_metric:
            length_convert = self.unit_converter.inch_to_mm
            feed_convert = self.unit_converter.ipm_to_mmpm
        else:
            length_convert = self.unit_converter.mm_to_inch
            feed_convert = self.unit_converter.mmpm_to_ipm

        for spin in (
            self.diameter_input,
            self.stepdown_input,
            self.stepover_input,
        ):
            value = spin.value()
            spin.blockSignals(True)
            spin.setValue(length_convert(value))
            spin.blockSignals(False)

        for spin in (
            self.feed_input,
            self.plunge_input,
        ):
            value = spin.value()
            spin.blockSignals(True)
            spin.setValue(feed_convert(value))
            spin.blockSignals(False)

    def _on_parameters_changed(self, _value: float = 0.0) -> None:
        """Recompute derived metrics when any calculator input changes."""
        self._recalculate_metrics()

    def _load_selected_tool_defaults(self) -> None:
        """Populate calculator inputs from the selected tool's stored values."""
        if not self.selected_tool:
            # Nothing selected yet; keep defaults but clear results.
            self.results_display.setText("Select a tool to see calculations")
            return

        tool_data = self.selected_tool

        # Extract geometry and start values from either properties or root keys.
        properties = tool_data.get("properties")
        geometry = {}
        start_values = {}
        if isinstance(properties, dict):
            geometry = properties.get("geometry") or {}
            start_values = properties.get("start_values") or {}

        if not geometry:
            geometry = tool_data.get("geometry") or {}
        if not start_values:
            raw_start_values = tool_data.get("start_values", {})
            if isinstance(raw_start_values, dict):
                start_values = raw_start_values

        diameter = tool_data.get("diameter")
        if diameter in (None, ""):
            diameter = geometry.get("diameter") or geometry.get("DC")

        try:
            diameter_value = float(diameter) if diameter is not None else 0.0
        except (TypeError, ValueError):
            diameter_value = 0.0

        flutes = (
            geometry.get("number_of_flutes")
            or geometry.get("NOF")
            or geometry.get("flutes")
            or 2
        )
        try:
            flutes_value = int(float(flutes))
        except (TypeError, ValueError):
            flutes_value = 2

        stepdown = start_values.get("stepdown", 0.25)
        stepover = start_values.get("stepover", 0.125)
        rpm = start_values.get("n", start_values.get("rpm", 18000))
        feed = start_values.get("v_f", start_values.get("feed_rate", 100.0))
        plunge = start_values.get("v_plunge", start_values.get("plunge_rate", 50.0))

        # Convert from tool's native units into the current UI units so that
        # we never show mixed units.
        tool_unit = (tool_data.get("unit") or "inches").lower()
        tool_is_metric = tool_unit in ("mm", "metric", "millimeters")

        if tool_is_metric != self.is_metric:
            if self.is_metric:
                diameter_value = self.unit_converter.inch_to_mm(diameter_value)
                stepdown = self.unit_converter.inch_to_mm(stepdown)
                stepover = self.unit_converter.inch_to_mm(stepover)
                feed = self.unit_converter.ipm_to_mmpm(feed)
                plunge = self.unit_converter.ipm_to_mmpm(plunge)
            else:
                diameter_value = self.unit_converter.mm_to_inch(diameter_value)
                stepdown = self.unit_converter.mm_to_inch(stepdown)
                stepover = self.unit_converter.mm_to_inch(stepover)
                feed = self.unit_converter.mmpm_to_ipm(feed)
                plunge = self.unit_converter.mmpm_to_ipm(plunge)

        # Apply values without triggering recursive updates.
        for widget, value in (
            (self.diameter_input, diameter_value),
            (self.flutes_input, flutes_value),
            (self.stepdown_input, stepdown),
            (self.stepover_input, stepover),
            (self.rpm_input, rpm),
            (self.feed_input, feed),
            (self.plunge_input, plunge),
        ):
            widget.blockSignals(True)
            widget.setValue(value)
            widget.blockSignals(False)

        self._update_calculator_unit_suffixes()
        self._recalculate_metrics()


    def _recalculate_metrics(self) -> None:
        """Recompute chip load, surface speed, and material removal rate."""
        if not hasattr(self, "results_display"):
            return

        if not self.selected_tool:
            self.results_display.setText("Select a tool to see calculations")
            return

        try:
            rpm = max(1, int(self.rpm_input.value()))
            feed = max(0.0, float(self.feed_input.value()))
            stepdown = max(0.0, float(self.stepdown_input.value()))
            stepover = max(0.0, float(self.stepover_input.value()))
            flutes = max(1, int(self.flutes_input.value()))
            diameter = max(0.0, float(self.diameter_input.value()))
            plunge = max(0.0, float(self.plunge_input.value()))
        except (TypeError, ValueError):
            self.results_display.setText("Invalid numeric input")
            return

        chip_load = feed / (rpm * flutes) if rpm > 0 and flutes > 0 else 0.0

        # Surface speed uses the same base length unit as diameter.
        if self.is_metric:
            surface_speed = 3.14159 * diameter * rpm / 1000.0  # m/min
            surface_speed_label = f"{surface_speed:.1f} m/min"
            mrr_label = f"{(stepdown * stepover * feed):.2f} mm^3/min"
        else:
            surface_speed = 3.14159 * diameter * rpm / 12.0  # ft/min
            surface_speed_label = f"{surface_speed:.1f} ft/min"
            mrr_label = f"{(stepdown * stepover * feed):.2f} in^3/min"

        diameter_label = self.unit_converter.format_value(
            diameter, self.is_metric, "length"
        )
        stepdown_label = self.unit_converter.format_value(
            stepdown, self.is_metric, "length"
        )
        stepover_label = self.unit_converter.format_value(
            stepover, self.is_metric, "length"
        )
        feed_label = self.unit_converter.format_value(
            feed, self.is_metric, "feed_rate", decimals=2
        )
        plunge_label = self.unit_converter.format_value(
            plunge, self.is_metric, "feed_rate", decimals=2
        )
        chip_load_label = self.unit_converter.format_value(
            chip_load, self.is_metric, "length", decimals=4
        )

        description = self.selected_tool.get("description", "")

        text = (
            f"Tool: {description}\n"
            f"Diameter: {diameter_label}\n\n"
            f"Parameters:\n"
            f"  RPM: {rpm}\n"
            f"  Feed rate: {feed_label}\n"
            f"  Plunge rate: {plunge_label}\n"
            f"  Pass depth (stepdown): {stepdown_label}\n"
            f"  Stepover: {stepover_label}\n\n"
            f"Derived:\n"
            f"  Chip load per tooth: {chip_load_label}\n"
            f"  Surface speed: {surface_speed_label}\n"
            f"  Material removal rate: {mrr_label}\n"
        )

        self.results_display.setText(text)



    def _load_providers(self) -> None:
        """Refresh the tool tree from providers and personal toolbox."""
        try:
            filter_text = self.search_input.text() if hasattr(self, "search_input") else ""
            self._rebuild_tool_tree(filter_text)
            self.logger.info("Tool tree refreshed from providers")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to load providers into tool tree: %s", e)

    def _on_import_tools(self) -> None:
        """Handle import tools button click with smart update/merge behavior."""
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Tool Database",
            str(Path.home()),
            "Tool Files (*.json *.csv *.vtdb *.tdb *.tool);;All Files (*.*)",
        )

        if not file_path:
            return

        try:
            path = Path(file_path)
            provider_name = path.stem

            # Determine how to handle existing provider databases
            existing_provider = self.provider_repo.get_provider_by_name(provider_name)
            mode = "auto"

            if existing_provider:
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Question)
                msg_box.setWindowTitle("Import Tool Database")
                msg_box.setText(
                    f"A provider named '{provider_name}' already exists.\n\n"
                    "How would you like to handle this import?"
                )

                overwrite_button = msg_box.addButton(
                    "Overwrite existing (vendor update)", QMessageBox.AcceptRole
                )
                merge_button = msg_box.addButton(
                    "Merge (add only new tools)", QMessageBox.AcceptRole
                )
                cancel_button = msg_box.addButton(QMessageBox.Cancel)

                msg_box.setDefaultButton(merge_button)
                msg_box.exec()

                clicked = msg_box.clickedButton()
                if clicked is cancel_button:
                    return
                if clicked is overwrite_button:
                    mode = "overwrite"
                else:
                    mode = "merge"

            success, message = self.tool_database_manager.import_tools_from_file(
                file_path, provider_name, mode=mode
            )
            if success:
                QMessageBox.information(self, "Success", message)
                self._load_providers()
                self._populate_tools_table()
            else:
                QMessageBox.warning(self, "Import Failed", message)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            QMessageBox.critical(self, "Error", f"Failed to import: {str(e)}")
            self.logger.error("Import error: %s", e)


    def _on_import_from_vectric(self) -> None:
        """Import tool databases discovered under Vectric's ProgramData folder."""
        dialog = VectricToolImportDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return

        selections = dialog.get_selected_databases()
        if not selections:
            return

        any_success = False

        for product, version, db_path in selections:
            provider_name = f"Vectric {product} {version}"

            # Determine how to handle existing provider databases
            existing_provider = self.provider_repo.get_provider_by_name(provider_name)
            mode = "auto"

            if existing_provider:
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Question)
                msg_box.setWindowTitle("Import Vectric Tool Database")
                msg_box.setText(
                    f"A provider named '{provider_name}' already exists.\n\n"
                    "How would you like to handle this import?"
                )

                overwrite_button = msg_box.addButton(
                    "Overwrite existing (vendor update)", QMessageBox.AcceptRole
                )
                merge_button = msg_box.addButton(
                    "Merge (add only new tools)", QMessageBox.AcceptRole
                )
                cancel_button = msg_box.addButton(QMessageBox.Cancel)

                msg_box.setDefaultButton(merge_button)
                msg_box.exec()

                clicked = msg_box.clickedButton()
                if clicked is cancel_button:
                    continue
                if clicked is overwrite_button:
                    mode = "overwrite"
                else:
                    mode = "merge"

            success, message = self.tool_database_manager.import_tools_from_file(
                db_path, provider_name, mode=mode
            )
            if success:
                any_success = True
                self.logger.info("Imported Vectric tools from %s: %s", db_path, message)
            else:
                QMessageBox.warning(
                    self,
                    "Import Failed",
                    f"Failed to import '{provider_name}': {message}",
                )

        if any_success:
            QMessageBox.information(
                self,
                "Vectric Import Complete",
                "Imported one or more Vectric tool databases successfully.",
            )
            self._load_providers()
            self._populate_tools_table()

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
                    # Refresh tree so My Tools branch reflects the new tool
                    self._rebuild_tool_tree(self.search_input.text())
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
            geometry = db_tool["geometry"] if isinstance(db_tool["geometry"], dict) else {}
        if not start_values and "start_values" in db_tool:
            start_values = (
                db_tool["start_values"] if isinstance(db_tool["start_values"], dict) else {}
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
        """Backwards-compatible wrapper to refresh the tool tree."""
        self._load_providers()

    def _on_library_changed(self) -> None:
        """Backwards-compatible stub (no-op with tree-based UI)."""
        self.search_input.clear()
        self._load_providers()

    def _on_search_changed(self) -> None:
        """Handle search input change."""
        query = self.search_input.text()
        self._rebuild_tool_tree(query)

    def _on_tool_selected(self) -> None:
        """Handle tool selection from the tree."""
        if not hasattr(self, "tool_tree"):
            return

        item = self.tool_tree.currentItem()
        if item is None:
            return

        meta = item.data(0, Qt.UserRole)
        if not isinstance(meta, dict):
            return

        source = meta.get("source")
        if source not in {"db", "my_tools"}:
            # Ignore root nodes
            return

        tool_data = meta.get("tool_data") or {}
        self.selected_tool = tool_data
        self.selected_tool_source = source

        if source == "db":
            self.selected_provider_id = meta.get("provider_id")
        else:
            self.selected_provider_id = None

        self.selected_tool_label.setText(
            f"Selected: {tool_data.get('description', '')}"
        )
        self._update_calculator()

    def _on_tool_context_menu(self, pos) -> None:
        """Handle right-click context menu on the tool tree."""
        if not hasattr(self, "tool_tree"):
            return

        item = self.tool_tree.itemAt(pos)
        if item is None:
            return

        meta = item.data(0, Qt.UserRole)
        if not isinstance(meta, dict) or meta.get("source") != "db":
            # Only vendor DB tools can be added to My Toolbox from this menu.
            return

        # Ensure selection matches the context menu item
        self.tool_tree.setCurrentItem(item)
        self.selected_tool = meta.get("tool_data") or {}
        self.selected_tool_source = "db"
        self.selected_provider_id = meta.get("provider_id")

        menu = QMenu()
        add_action = menu.addAction("Add to My Toolbox")
        action = menu.exec(self.tool_tree.mapToGlobal(pos))

        if action == add_action:
            self._on_add_tool()

    def _on_add_tool(self) -> None:
        """Add selected vendor tool to personal toolbox."""
        if not self.selected_tool:
            QMessageBox.warning(self, "No Tool Selected", "Please select a tool first.")
            return

        if getattr(self, "selected_tool_source", None) != "db":
            QMessageBox.warning(
                self,
                "Not a Vendor Tool",
                "Please select a tool from a vendor library to add to My Toolbox.",
            )
            return

        # Convert to UI Tool format
        ui_tool = self._convert_db_tool_to_ui(self.selected_tool)

        if self.personal_toolbox_manager.add_tool(ui_tool):
            QMessageBox.information(
                self,
                "Success",
                f"Added '{self.selected_tool.get('description', '')}' to your toolbox.",
            )
            # Refresh tree so My Tools branch reflects the new tool
            self._rebuild_tool_tree(self.search_input.text())
        else:
            QMessageBox.warning(self, "Already Added", "This tool is already in your toolbox.")

    def _on_unit_toggle(self) -> None:
        """Handle unit toggle button."""
        was_metric = self.is_metric
        self.is_metric = self.unit_toggle_btn.isChecked()
        self.personal_toolbox_manager.set_auto_convert_to_metric(self.is_metric)
        self._update_unit_button_style()

        if was_metric != self.is_metric:
            self._convert_current_calculator_units(to_metric=self.is_metric)
            self._update_calculator_unit_suffixes()

        self._rebuild_tool_tree(self.search_input.text())
        self._recalculate_metrics()

    def _update_unit_button_style(self) -> None:
        """Update unit toggle button text."""
        if self.is_metric:
            self.unit_toggle_btn.setText("MET ✓")
        else:
            self.unit_toggle_btn.setText("SAE")

    def _update_calculator(self) -> None:
        """Populate calculator inputs from the selected tool and recalc metrics."""
        self._load_selected_tool_defaults()

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
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            QMessageBox.critical(self, "Error", f"Failed to restore data: {str(e)}")
