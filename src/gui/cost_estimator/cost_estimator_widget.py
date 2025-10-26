"""Cost Estimator Widget for project cost estimation."""

from typing import Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QDoubleSpinBox,
    QComboBox,
    QPushButton,
    QFormLayout,
    QMessageBox,
    QTabWidget,
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont

from src.core.logging_config import get_logger
from .cost_calculator import CostCalculator, CostEstimate
from .material_cost_manager import MaterialCostManager


logger = get_logger(__name__)


class CostEstimatorWidget(QWidget):
    """Main Cost Estimator Widget for project cost estimation."""

    # Signals
    cost_calculated = Signal(dict)  # Emitted when cost is calculated

    def __init__(self, parent=None):
        """Initialize the cost estimator widget."""
        super().__init__(parent)
        self.logger = logger

        # Initialize managers
        self.cost_calculator = CostCalculator()
        self.material_manager = MaterialCostManager()

        # Current estimate
        self.current_estimate: Optional[CostEstimate] = None

        # Setup UI
        self._setup_ui()
        self.logger.info("Cost Estimator Widget initialized")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # Title
        title = QLabel("Project Cost Estimator")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)

        # Create tab widget
        tabs = QTabWidget()

        # Material Cost Tab
        material_tab = self._create_material_tab()
        tabs.addTab(material_tab, "Material Cost")

        # Machine Time Tab
        machine_tab = self._create_machine_tab()
        tabs.addTab(machine_tab, "Machine Time")

        # Labor Cost Tab
        labor_tab = self._create_labor_tab()
        tabs.addTab(labor_tab, "Labor Cost")

        # Summary Tab
        summary_tab = self._create_summary_tab()
        tabs.addTab(summary_tab, "Summary")

        main_layout.addWidget(tabs)

        # Calculate button
        calc_button = QPushButton("Calculate Total Cost")
        calc_button.clicked.connect(self._calculate_cost)
        main_layout.addWidget(calc_button)

        # Results display
        self.results_label = QLabel("Results will appear here")
        self.results_label.setWordWrap(True)
        main_layout.addWidget(self.results_label)

        main_layout.addStretch()

    def _create_material_tab(self) -> QWidget:
        """Create the material cost tab."""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Material selection
        self.material_combo = QComboBox()
        self.material_combo.addItems(self.material_manager.get_material_names())
        layout.addRow("Material:", self.material_combo)

        # Quantity
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setMinimum(0.0)
        self.quantity_spin.setMaximum(10000.0)
        self.quantity_spin.setValue(1.0)
        layout.addRow("Quantity:", self.quantity_spin)

        # Unit
        self.unit_label = QLabel("kg")
        layout.addRow("Unit:", self.unit_label)

        # Cost per unit
        self.material_cost_spin = QDoubleSpinBox()
        self.material_cost_spin.setMinimum(0.0)
        self.material_cost_spin.setMaximum(10000.0)
        self.material_cost_spin.setValue(10.0)
        layout.addRow("Cost per Unit:", self.material_cost_spin)

        # Update unit when material changes
        self.material_combo.currentTextChanged.connect(self._on_material_changed)

        layout.addStretch()
        return widget

    def _create_machine_tab(self) -> QWidget:
        """Create the machine time tab."""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Machine time
        self.machine_hours_spin = QDoubleSpinBox()
        self.machine_hours_spin.setMinimum(0.0)
        self.machine_hours_spin.setMaximum(10000.0)
        self.machine_hours_spin.setValue(1.0)
        layout.addRow("Machine Time (hours):", self.machine_hours_spin)

        # Hourly rate
        self.machine_rate_spin = QDoubleSpinBox()
        self.machine_rate_spin.setMinimum(0.0)
        self.machine_rate_spin.setMaximum(10000.0)
        self.machine_rate_spin.setValue(50.0)
        layout.addRow("Hourly Rate ($):", self.machine_rate_spin)

        layout.addStretch()
        return widget

    def _create_labor_tab(self) -> QWidget:
        """Create the labor cost tab."""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Labor hours
        self.labor_hours_spin = QDoubleSpinBox()
        self.labor_hours_spin.setMinimum(0.0)
        self.labor_hours_spin.setMaximum(10000.0)
        self.labor_hours_spin.setValue(1.0)
        layout.addRow("Labor Hours:", self.labor_hours_spin)

        # Labor rate
        self.labor_rate_spin = QDoubleSpinBox()
        self.labor_rate_spin.setMinimum(0.0)
        self.labor_rate_spin.setMaximum(10000.0)
        self.labor_rate_spin.setValue(25.0)
        layout.addRow("Hourly Rate ($):", self.labor_rate_spin)

        # Overhead percentage
        self.overhead_spin = QDoubleSpinBox()
        self.overhead_spin.setMinimum(0.0)
        self.overhead_spin.setMaximum(100.0)
        self.overhead_spin.setValue(10.0)
        layout.addRow("Overhead (%):", self.overhead_spin)

        layout.addStretch()
        return widget

    def _create_summary_tab(self) -> QWidget:
        """Create the summary tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.summary_label = QLabel("No estimate calculated yet")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)
        layout.addStretch()

        return widget

    def _on_material_changed(self, material_name: str) -> None:
        """Handle material selection change."""
        material = self.material_manager.get_material(material_name)
        if material:
            self.unit_label.setText(material.unit)
            self.material_cost_spin.setValue(material.cost_per_unit)

    def _calculate_cost(self) -> None:
        """Calculate the total project cost."""
        try:
            # Get values from UI
            material_quantity = self.quantity_spin.value()
            material_cost_per_unit = self.material_cost_spin.value()
            machine_hours = self.machine_hours_spin.value()
            machine_rate = self.machine_rate_spin.value()
            labor_hours = self.labor_hours_spin.value()
            labor_rate = self.labor_rate_spin.value()
            overhead_percent = self.overhead_spin.value()

            # Calculate costs
            material_cost = self.cost_calculator.calculate_material_cost(
                material_quantity, material_cost_per_unit
            )
            machine_cost = self.cost_calculator.calculate_machine_time_cost(
                machine_hours, machine_rate
            )
            labor_cost = self.cost_calculator.calculate_labor_cost(
                labor_hours, labor_rate
            )

            # Get total estimate
            self.current_estimate = self.cost_calculator.estimate_total_cost(
                material_cost, machine_cost, labor_cost, overhead_percent
            )

            # Display results
            self._display_results()

            # Emit signal
            self.cost_calculated.emit(self.current_estimate.to_dict())

        except Exception as e:
            self.logger.error(f"Error calculating cost: {e}")
            QMessageBox.critical(
                self, "Calculation Error", f"Failed to calculate cost: {str(e)}"
            )

    def _display_results(self) -> None:
        """Display the cost calculation results."""
        if not self.current_estimate:
            return

        machine_rate = self.machine_rate_spin.value()
        labor_rate = self.labor_rate_spin.value()
        results_text = (
            "<b>Cost Estimate Summary</b><br><br>"
            f"Material Cost: ${self.current_estimate.material_cost:.2f}<br>"
            f"Machine Time: {self.current_estimate.machine_time_hours:.2f} "
            f"hours @ ${machine_rate:.2f}/hr = "
            f"${self.current_estimate.machine_time_cost:.2f}<br>"
            f"Labor Cost: {self.current_estimate.labor_hours:.2f} "
            f"hours @ ${labor_rate:.2f}/hr = "
            f"${self.current_estimate.labor_cost:.2f}<br>"
            f"Overhead: ${self.current_estimate.overhead_cost:.2f}<br>"
            "<br>"
            f"<b>Total Project Cost: ${self.current_estimate.total_cost:.2f}</b>"
        )

        self.results_label.setText(results_text)
        self.summary_label.setText(results_text)
