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
    QTabWidget,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from src.core.logging_config import get_logger
from .cost_calculator import (
    ProfessionalCostCalculator,
    CostEstimate,
    PricingStrategy,
)
from .material_cost_manager import MaterialCostManager

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

        # Current estimate
        self.current_estimate: Optional[CostEstimate] = None

        # Setup UI
        self._setup_ui()
        self.logger.info("Professional Cost Estimator Widget initialized")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("Professional Cost Estimator")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Create tab widget
        tabs = QTabWidget()

        # Material Tab
        tabs.addTab(self._create_material_tab(), "Materials")

        # Machine Time Tab
        tabs.addTab(self._create_machine_tab(), "Machine Time")

        # Labor Tab
        tabs.addTab(self._create_labor_tab(), "Labor & Design")

        # Shop Operations Tab
        tabs.addTab(self._create_shop_tab(), "Shop Operations")

        # Tools & Consumables Tab
        tabs.addTab(self._create_tools_tab(), "Tools & Consumables")

        # Settings Tab
        tabs.addTab(self._create_settings_tab(), "Settings")

        # Summary Tab
        tabs.addTab(self._create_summary_tab(), "Summary")

        layout.addWidget(tabs)

        # Calculate button
        calc_button = QPushButton("Calculate Estimate")
        calc_button.clicked.connect(self._calculate_estimate)
        layout.addWidget(calc_button)

        self.setLayout(layout)

    def _create_material_tab(self) -> QWidget:
        """Create material cost tab."""
        widget = QWidget()
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
        layout.addRow("Total Material Cost:", self.material_cost_display)

        widget.setLayout(layout)
        return widget

    def _create_machine_tab(self) -> QWidget:
        """Create machine time tab."""
        widget = QWidget()
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
        layout.addRow("Total Machine Cost:", self.machine_cost_display)

        widget.setLayout(layout)
        return widget

    def _create_labor_tab(self) -> QWidget:
        """Create labor and design tab."""
        widget = QWidget()
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
        layout.addRow("Total Labor Cost:", self.labor_cost_display)

        widget.setLayout(layout)
        return widget

    def _create_shop_tab(self) -> QWidget:
        """Create shop operations tab."""
        widget = QWidget()
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
        layout.addRow("Total Shop Cost:", self.shop_cost_display)

        widget.setLayout(layout)
        return widget

    def _create_tools_tab(self) -> QWidget:
        """Create tools and consumables tab."""
        widget = QWidget()
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
        layout.addRow("Total Tools Cost:", self.tools_cost_display)

        widget.setLayout(layout)
        return widget

    def _create_settings_tab(self) -> QWidget:
        """Create settings tab."""
        widget = QWidget()
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

        widget.setLayout(layout)
        return widget

    def _create_summary_tab(self) -> QWidget:
        """Create summary tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Summary table
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(2)
        self.summary_table.setHorizontalHeaderLabels(["Category", "Amount"])
        self.summary_table.setRowCount(10)

        layout.addWidget(self.summary_table)
        widget.setLayout(layout)
        return widget

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

        # Update summary table
        breakdown = self.current_estimate.get_cost_breakdown()
        for i, (category, amount) in enumerate(breakdown.items()):
            self.summary_table.setItem(i, 0, QTableWidgetItem(category))
            self.summary_table.setItem(i, 1, QTableWidgetItem(f"${amount:.2f}"))
