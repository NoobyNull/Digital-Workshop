"""Professional Cost Estimator Widget for CNC woodworking projects."""

from typing import Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDoubleSpinBox,
    QSpinBox,
    QComboBox,
    QPushButton,
    QFormLayout,
    QMessageBox,
    QScrollArea,
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont

from src.core.logging_config import get_logger
from .cost_calculator import (
    ProfessionalCostCalculator,
    CostEstimate,
    PricingStrategy,
)
from .material_cost_manager import MaterialCostManager
from src.core.services.tab_data_manager import TabDataManager
from src.core.database_manager import get_database_manager

logger = get_logger(__name__)


class CostEstimatorWidget(QWidget):
    """Professional Cost Estimator Widget for CNC woodworking projects."""

    # Signals
    cost_calculated = Signal(dict)

    def __init__(self, parent=None):
        """Initialize the cost estimator widget."""
        super().__init__(parent)
        self.logger = logger

        # Initialize managers
        self.calculator = ProfessionalCostCalculator()
        self.material_manager = MaterialCostManager()
        self.tab_data_manager = TabDataManager(get_database_manager())

        # Current estimate
        self.current_estimate: Optional[CostEstimate] = None
        self.current_project_id: Optional[str] = None

        # Setup UI
        self._setup_ui()
        self.logger.info("Professional Cost Estimator Widget initialized")

    def _setup_ui(self) -> None:
        """Set up the user interface as a worksheet."""
        main_layout = QVBoxLayout()

        # Title
        title = QLabel("Professional Cost Estimator Worksheet")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)

        # Create scrollable area for worksheet
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()

        # MATERIALS SECTION
        scroll_layout.addWidget(self._create_section_header("MATERIALS"))
        scroll_layout.addLayout(self._create_material_section())

        # MACHINE TIME SECTION
        scroll_layout.addWidget(self._create_section_header("MACHINE TIME"))
        scroll_layout.addLayout(self._create_machine_section())

        # LABOR & DESIGN SECTION
        scroll_layout.addWidget(self._create_section_header("LABOR & DESIGN"))
        scroll_layout.addLayout(self._create_labor_section())

        # SHOP OPERATIONS SECTION
        scroll_layout.addWidget(self._create_section_header("SHOP OPERATIONS"))
        scroll_layout.addLayout(self._create_shop_section())

        # TOOLS & CONSUMABLES SECTION
        scroll_layout.addWidget(self._create_section_header("TOOLS & CONSUMABLES"))
        scroll_layout.addLayout(self._create_tools_section())

        # SETTINGS SECTION
        scroll_layout.addWidget(self._create_section_header("SETTINGS"))
        scroll_layout.addLayout(self._create_settings_section())

        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        # Bottom section with calculate button and summary
        bottom_layout = QHBoxLayout()

        # Calculate button
        calc_button = QPushButton("Calculate Estimate")
        calc_button.setMinimumHeight(40)
        calc_button.clicked.connect(self._calculate_estimate)
        bottom_layout.addWidget(calc_button)

        # Summary display
        self.summary_display = QLabel("Ready to calculate...")
        self.summary_display.setWordWrap(True)
        bottom_layout.addWidget(self.summary_display)

        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

    def _create_section_header(self, title: str) -> QLabel:
        """Create a section header label."""
        header = QLabel(title)
        header_font = QFont()
        header_font.setPointSize(11)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setStyleSheet("color: #1a5490; margin-top: 12px; margin-bottom: 6px;")
        return header

    def _create_material_section(self) -> QFormLayout:
        """Create material cost section."""
        layout = QFormLayout()

        # Material selection
        self.material_combo = QComboBox()
        self.material_combo.addItems(self.material_manager.get_material_names())
        layout.addRow("Material:", self.material_combo)

        # Quantity
        self.material_quantity = QDoubleSpinBox()
        self.material_quantity.setMinimum(0.0)
        self.material_quantity.setMaximum(10000.0)
        self.material_quantity.setValue(1.0)
        layout.addRow("Quantity:", self.material_quantity)

        # Waste percentage
        self.waste_percentage = QDoubleSpinBox()
        self.waste_percentage.setMinimum(0.0)
        self.waste_percentage.setMaximum(100.0)
        self.waste_percentage.setValue(10.0)
        self.waste_percentage.setSuffix("%")
        layout.addRow("Waste %:", self.waste_percentage)

        # Material cost display
        self.material_cost_display = QLabel("$0.00")
        mat_cost_font = QFont()
        mat_cost_font.setBold(True)
        self.material_cost_display.setFont(mat_cost_font)
        layout.addRow("Total Material Cost:", self.material_cost_display)

        return layout

    def _create_machine_section(self) -> QFormLayout:
        """Create machine time section."""
        layout = QFormLayout()

        # Setup hours
        self.machine_setup_hours = QDoubleSpinBox()
        self.machine_setup_hours.setMinimum(0.0)
        self.machine_setup_hours.setMaximum(1000.0)
        layout.addRow("Setup Hours:", self.machine_setup_hours)

        # Runtime hours
        self.machine_runtime_hours = QDoubleSpinBox()
        self.machine_runtime_hours.setMinimum(0.0)
        self.machine_runtime_hours.setMaximum(1000.0)
        layout.addRow("Runtime Hours:", self.machine_runtime_hours)

        # Machine cost display
        self.machine_cost_display = QLabel("$0.00")
        mach_cost_font = QFont()
        mach_cost_font.setBold(True)
        self.machine_cost_display.setFont(mach_cost_font)
        layout.addRow("Total Machine Cost:", self.machine_cost_display)

        return layout

    def _create_labor_section(self) -> QFormLayout:
        """Create labor and design section."""
        layout = QFormLayout()

        # Design hours
        self.design_hours = QDoubleSpinBox()
        self.design_hours.setMinimum(0.0)
        self.design_hours.setMaximum(1000.0)
        layout.addRow("Design/CAM Hours:", self.design_hours)

        # Labor hours
        self.labor_hours = QDoubleSpinBox()
        self.labor_hours.setMinimum(0.0)
        self.labor_hours.setMaximum(1000.0)
        layout.addRow("Production Labor Hours:", self.labor_hours)

        # Labor cost display
        self.labor_cost_display = QLabel("$0.00")
        labor_cost_font = QFont()
        labor_cost_font.setBold(True)
        self.labor_cost_display.setFont(labor_cost_font)
        layout.addRow("Total Labor Cost:", self.labor_cost_display)

        return layout

    def _create_shop_section(self) -> QFormLayout:
        """Create shop operations section."""
        layout = QFormLayout()

        # Finishing hours
        self.finishing_hours = QDoubleSpinBox()
        self.finishing_hours.setMinimum(0.0)
        self.finishing_hours.setMaximum(1000.0)
        layout.addRow("Finishing Hours:", self.finishing_hours)

        # Assembly hours
        self.assembly_hours = QDoubleSpinBox()
        self.assembly_hours.setMinimum(0.0)
        self.assembly_hours.setMaximum(1000.0)
        layout.addRow("Assembly Hours:", self.assembly_hours)

        # Other shop hours
        self.other_shop_hours = QDoubleSpinBox()
        self.other_shop_hours.setMinimum(0.0)
        self.other_shop_hours.setMaximum(1000.0)
        layout.addRow("Other Shop Hours:", self.other_shop_hours)

        # Shop cost display
        self.shop_cost_display = QLabel("$0.00")
        shop_cost_font = QFont()
        shop_cost_font.setBold(True)
        self.shop_cost_display.setFont(shop_cost_font)
        layout.addRow("Total Shop Cost:", self.shop_cost_display)

        return layout

    def _create_tools_section(self) -> QFormLayout:
        """Create tools and consumables section."""
        layout = QFormLayout()

        # Tool wear cost
        self.tool_wear_cost = QDoubleSpinBox()
        self.tool_wear_cost.setMinimum(0.0)
        self.tool_wear_cost.setMaximum(10000.0)
        self.tool_wear_cost.setPrefix("$")
        layout.addRow("Tool Wear Cost:", self.tool_wear_cost)

        # Consumables cost
        self.consumables_cost = QDoubleSpinBox()
        self.consumables_cost.setMinimum(0.0)
        self.consumables_cost.setMaximum(10000.0)
        self.consumables_cost.setPrefix("$")
        layout.addRow("Consumables Cost:", self.consumables_cost)

        # Tools cost display
        self.tools_cost_display = QLabel("$0.00")
        tools_cost_font = QFont()
        tools_cost_font.setBold(True)
        self.tools_cost_display.setFont(tools_cost_font)
        layout.addRow("Total Tools Cost:", self.tools_cost_display)

        return layout

    def _create_settings_section(self) -> QFormLayout:
        """Create settings section."""
        layout = QFormLayout()

        # Overhead percentage
        self.overhead_pct = QDoubleSpinBox()
        self.overhead_pct.setMinimum(0.0)
        self.overhead_pct.setMaximum(100.0)
        self.overhead_pct.setValue(15.0)
        self.overhead_pct.setSuffix("%")
        layout.addRow("Overhead %:", self.overhead_pct)

        # Profit margin percentage
        self.profit_margin_pct = QDoubleSpinBox()
        self.profit_margin_pct.setMinimum(0.0)
        self.profit_margin_pct.setMaximum(100.0)
        self.profit_margin_pct.setValue(30.0)
        self.profit_margin_pct.setSuffix("%")
        layout.addRow("Profit Margin %:", self.profit_margin_pct)

        # Tax percentage
        self.tax_pct = QDoubleSpinBox()
        self.tax_pct.setMinimum(0.0)
        self.tax_pct.setMaximum(100.0)
        self.tax_pct.setSuffix("%")
        layout.addRow("Tax %:", self.tax_pct)

        # Quantity
        self.quantity = QSpinBox()
        self.quantity.setMinimum(1)
        self.quantity.setMaximum(10000)
        self.quantity.setValue(1)
        layout.addRow("Quantity:", self.quantity)

        return layout

    def _calculate_estimate(self) -> None:
        """Calculate the cost estimate."""
        try:
            # Update calculator settings
            self.calculator.set_overhead_and_margins(
                overhead_pct=self.overhead_pct.value(),
                profit_margin_pct=self.profit_margin_pct.value(),
                tax_pct=self.tax_pct.value(),
            )

            # Get material cost
            material = self.material_manager.get_material(
                self.material_combo.currentText()
            )
            material_cost = (
                self.material_quantity.value() * material.cost_per_unit
                if material
                else 0.0
            )

            # Generate estimate
            self.current_estimate = self.calculator.generate_estimate(
                material_cost=material_cost,
                waste_percentage=self.waste_percentage.value(),
                machine_setup_hours=self.machine_setup_hours.value(),
                machine_runtime_hours=self.machine_runtime_hours.value(),
                design_hours=self.design_hours.value(),
                labor_hours=self.labor_hours.value(),
                finishing_hours=self.finishing_hours.value(),
                assembly_hours=self.assembly_hours.value(),
                other_shop_hours=self.other_shop_hours.value(),
                tool_wear_cost=self.tool_wear_cost.value(),
                consumables_cost=self.consumables_cost.value(),
                quantity=self.quantity.value(),
            )

            # Update displays
            self._update_displays()

            # Emit signal
            self.cost_calculated.emit(self.current_estimate.to_dict())

            self.logger.info("Cost estimate calculated successfully")

        except Exception as e:
            self.logger.error(f"Error calculating estimate: {e}")
            QMessageBox.critical(self, "Error", f"Failed to calculate estimate: {e}")

    def _update_displays(self) -> None:
        """Update cost displays."""
        if not self.current_estimate:
            return

        # Update section displays
        self.material_cost_display.setText(
            f"${self.current_estimate.total_material_cost:.2f}"
        )
        self.machine_cost_display.setText(
            f"${self.current_estimate.total_machine_cost:.2f}"
        )
        self.labor_cost_display.setText(
            f"${self.current_estimate.total_labor_cost:.2f}"
        )
        self.shop_cost_display.setText(
            f"${self.current_estimate.total_shop_operations_cost:.2f}"
        )
        self.tools_cost_display.setText(
            f"${self.current_estimate.total_tool_cost:.2f}"
        )

        # Update summary display
        breakdown = self.current_estimate.get_cost_breakdown()
        summary_html = "<b>COST SUMMARY</b><br><br>"
        for category, amount in breakdown.items():
            summary_html += f"{category}: <b>${amount:.2f}</b><br>"

        summary_html += f"<br><b>FINAL QUOTE: ${self.current_estimate.final_quote_price:.2f}</b>"
        if self.current_estimate.quantity > 1:
            summary_html += (
                f"<br>Cost per unit: ${self.current_estimate.cost_per_unit:.2f}"
            )

        self.summary_display.setText(summary_html)

    def set_current_project(self, project_id: str) -> None:
        """Set the current project for saving/loading data."""
        self.current_project_id = project_id

    def save_to_project(self) -> None:
        """Save cost estimate data to current project."""
        if not self.current_project_id:
            QMessageBox.warning(self, "No Project", "Please select a project first")
            return

        # Gather data from UI
        materials_data = self.material_manager.get_all_materials()

        # Create data structure
        cost_estimate_data = {
            'materials': materials_data,
            'machine_setup_hours': self.machine_setup_hours.value(),
            'machine_run_hours': self.machine_run_hours.value(),
            'machine_hourly_rate': self.machine_hourly_rate.value(),
            'labor_design_hours': self.labor_design_hours.value(),
            'labor_setup_hours': self.labor_setup_hours.value(),
            'labor_run_hours': self.labor_run_hours.value(),
            'labor_hourly_rate': self.labor_hourly_rate.value(),
            'quantity': self.quantity_spinbox.value(),
            'pricing_strategy': self.pricing_strategy_combo.currentText(),
            'profit_margin': self.profit_margin_spinbox.value()
        }

        # Save to project
        success, message = self.tab_data_manager.save_tab_data_to_project(
            project_id=self.current_project_id,
            tab_name="Project Cost Estimator",
            data=cost_estimate_data,
            filename="cost_estimate.json",
            category="Cost Sheets"
        )

        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)

    def load_from_project(self) -> None:
        """Load cost estimate data from current project."""
        if not self.current_project_id:
            QMessageBox.warning(self, "No Project", "Please select a project first")
            return

        # Load from project
        success, data, message = self.tab_data_manager.load_tab_data_from_project(
            project_id=self.current_project_id,
            filename="cost_estimate.json"
        )

        if not success:
            QMessageBox.warning(self, "Load Failed", message)
            return

        # Restore data to UI
        try:
            # Restore machine time
            self.machine_setup_hours.setValue(data.get('machine_setup_hours', 0.0))
            self.machine_run_hours.setValue(data.get('machine_run_hours', 0.0))
            self.machine_hourly_rate.setValue(data.get('machine_hourly_rate', 50.0))

            # Restore labor
            self.labor_design_hours.setValue(data.get('labor_design_hours', 0.0))
            self.labor_setup_hours.setValue(data.get('labor_setup_hours', 0.0))
            self.labor_run_hours.setValue(data.get('labor_run_hours', 0.0))
            self.labor_hourly_rate.setValue(data.get('labor_hourly_rate', 50.0))

            # Restore quantity and pricing
            self.quantity_spinbox.setValue(data.get('quantity', 1))
            self.profit_margin_spinbox.setValue(data.get('profit_margin', 30.0))

            # Restore pricing strategy
            strategy = data.get('pricing_strategy', 'Markup')
            index = self.pricing_strategy_combo.findText(strategy)
            if index >= 0:
                self.pricing_strategy_combo.setCurrentIndex(index)

            # Trigger recalculation
            self._on_calculate()

            QMessageBox.information(self, "Success", message)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to restore data: {str(e)}")
