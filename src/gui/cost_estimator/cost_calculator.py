"""Professional cost calculator for CNC woodworking projects."""

from typing import Dict
from dataclasses import dataclass, asdict
from enum import Enum


class PricingStrategy(Enum):
    """Pricing strategies for quotes."""

    TIME_AND_MATERIAL = "time_and_material"
    FIXED_BID = "fixed_bid"
    PERCENTAGE_MARKUP = "percentage_markup"


@dataclass
class CostEstimate:
    """Comprehensive cost estimate for a project."""

    # Material costs
    material_cost: float = 0.0
    material_waste_cost: float = 0.0
    total_material_cost: float = 0.0

    # Machine time costs
    machine_setup_hours: float = 0.0
    machine_setup_cost: float = 0.0
    machine_runtime_hours: float = 0.0
    machine_runtime_cost: float = 0.0
    total_machine_cost: float = 0.0

    # Labor costs
    design_hours: float = 0.0
    design_cost: float = 0.0
    labor_hours: float = 0.0
    labor_cost: float = 0.0
    total_labor_cost: float = 0.0

    # Shop operations
    finishing_hours: float = 0.0
    finishing_cost: float = 0.0
    assembly_hours: float = 0.0
    assembly_cost: float = 0.0
    other_shop_hours: float = 0.0
    other_shop_cost: float = 0.0
    total_shop_operations_cost: float = 0.0

    # Tool and consumables
    tool_wear_cost: float = 0.0
    consumables_cost: float = 0.0
    total_tool_cost: float = 0.0

    # Overhead
    overhead_cost: float = 0.0
    overhead_percentage: float = 0.0

    # Subtotals
    subtotal_cost: float = 0.0
    profit_margin_amount: float = 0.0
    profit_margin_percentage: float = 0.0

    # Final pricing
    total_cost_before_tax: float = 0.0
    tax_amount: float = 0.0
    tax_percentage: float = 0.0
    final_quote_price: float = 0.0

    # Metadata
    quantity: int = 1
    cost_per_unit: float = 0.0
    pricing_strategy: str = "percentage_markup"

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    def get_cost_breakdown(self) -> Dict[str, float]:
        """Get a breakdown of all cost categories."""
        return {
            "Material": self.total_material_cost,
            "Machine Time": self.total_machine_cost,
            "Labor": self.total_labor_cost,
            "Shop Operations": self.total_shop_operations_cost,
            "Tools & Consumables": self.total_tool_cost,
            "Overhead": self.overhead_cost,
            "Subtotal": self.subtotal_cost,
            "Profit Margin": self.profit_margin_amount,
            "Tax": self.tax_amount,
            "Final Quote": self.final_quote_price,
        }


class CostCalculator:
    """Main cost calculator for projects."""

    def __init__(self) -> None:
        """Initialize the cost calculator."""
        self.material_cost_per_unit = 0.0
        self.machine_hourly_rate = 0.0
        self.labor_hourly_rate = 0.0
        self.overhead_percentage = 0.0

    def calculate_material_cost(self, quantity: float, cost_per_unit: float) -> float:
        """
        Calculate material cost.

        Args:
            quantity: Amount of material
            cost_per_unit: Cost per unit of material

        Returns:
            Total material cost
        """
        return quantity * cost_per_unit

    def calculate_machine_time_cost(self, hours: float, hourly_rate: float) -> float:
        """
        Calculate machine time cost.

        Args:
            hours: Machine time in hours
            hourly_rate: Hourly rate for machine

        Returns:
            Total machine time cost
        """
        return hours * hourly_rate

    def calculate_labor_cost(self, hours: float, hourly_rate: float) -> float:
        """
        Calculate labor cost.

        Args:
            hours: Labor hours
            hourly_rate: Hourly labor rate

        Returns:
            Total labor cost
        """
        return hours * hourly_rate

    def calculate_overhead(self, subtotal: float, percentage: float) -> float:
        """
        Calculate overhead cost.

        Args:
            subtotal: Subtotal before overhead
            percentage: Overhead percentage (0-100)

        Returns:
            Overhead cost
        """
        return subtotal * (percentage / 100.0)

    def estimate_total_cost(
        self,
        material_cost: float,
        machine_time_cost: float,
        labor_cost: float,
        overhead_percentage: float = 0.0,
    ) -> CostEstimate:
        """
        Calculate total project cost.

        Args:
            material_cost: Material cost
            machine_time_cost: Machine time cost
            labor_cost: Labor cost
            overhead_percentage: Overhead percentage

        Returns:
            CostEstimate object with all costs
        """
        subtotal = material_cost + machine_time_cost + labor_cost
        overhead_cost = self.calculate_overhead(subtotal, overhead_percentage)
        total_cost = subtotal + overhead_cost

        return CostEstimate(
            material_cost=material_cost,
            total_material_cost=material_cost,
            machine_runtime_cost=machine_time_cost,
            total_machine_cost=machine_time_cost,
            labor_cost=labor_cost,
            total_labor_cost=labor_cost,
            overhead_cost=overhead_cost,
            overhead_percentage=overhead_percentage,
            subtotal_cost=total_cost,
            final_quote_price=total_cost,
        )


class ProfessionalCostCalculator:
    """Professional cost calculator for CNC woodworking projects."""

    def __init__(self) -> None:
        """Initialize the calculator with default rates."""
        # Hourly rates
        self.labor_hourly_rate = 25.0
        self.design_hourly_rate = 50.0
        self.machine_setup_rate = 35.0
        self.machine_runtime_rate = 30.0
        self.finishing_hourly_rate = 20.0
        self.assembly_hourly_rate = 20.0

        # Overhead settings
        self.overhead_percentage = 15.0

        # Profit margin
        self.profit_margin_percentage = 30.0
        self.pricing_strategy = PricingStrategy.PERCENTAGE_MARKUP

        # Tax
        self.tax_percentage = 0.0

    def generate_estimate(
        self,
        material_cost: float,
        waste_percentage: float = 0.0,
        machine_setup_hours: float = 0.0,
        machine_runtime_hours: float = 0.0,
        design_hours: float = 0.0,
        labor_hours: float = 0.0,
        finishing_hours: float = 0.0,
        assembly_hours: float = 0.0,
        other_shop_hours: float = 0.0,
        tool_wear_cost: float = 0.0,
        consumables_cost: float = 0.0,
        quantity: int = 1,
    ) -> CostEstimate:
        """Generate a complete cost estimate."""
        # Calculate material costs
        mat_base = material_cost
        mat_waste = material_cost * (waste_percentage / 100.0)
        mat_total = mat_base + mat_waste

        # Calculate machine costs
        mach_setup = machine_setup_hours * self.machine_setup_rate
        mach_runtime = machine_runtime_hours * self.machine_runtime_rate
        mach_total = mach_setup + mach_runtime

        # Calculate labor costs
        design_cost = design_hours * self.design_hourly_rate
        labor_cost = labor_hours * self.labor_hourly_rate
        labor_total = design_cost + labor_cost

        # Calculate shop operations
        fin_cost = finishing_hours * self.finishing_hourly_rate
        asm_cost = assembly_hours * self.assembly_hourly_rate
        other_cost = other_shop_hours * self.labor_hourly_rate
        shop_total = fin_cost + asm_cost + other_cost

        # Tool costs
        tool_total = tool_wear_cost + consumables_cost

        # Subtotal before overhead
        subtotal_before_overhead = (
            mat_total + mach_total + labor_total + shop_total + tool_total
        )

        # Calculate overhead
        overhead = subtotal_before_overhead * (self.overhead_percentage / 100.0)

        # Subtotal with overhead
        subtotal = subtotal_before_overhead + overhead

        # Calculate profit margin
        profit_amount = subtotal * (self.profit_margin_percentage / 100.0)

        # Total before tax
        total_before_tax = subtotal + profit_amount

        # Calculate tax
        tax = total_before_tax * (self.tax_percentage / 100.0)

        # Final quote price
        final_price = total_before_tax + tax

        # Cost per unit
        cost_per_unit = final_price / quantity if quantity > 0 else 0.0

        return CostEstimate(
            material_cost=mat_base,
            material_waste_cost=mat_waste,
            total_material_cost=mat_total,
            machine_setup_hours=machine_setup_hours,
            machine_setup_cost=mach_setup,
            machine_runtime_hours=machine_runtime_hours,
            machine_runtime_cost=mach_runtime,
            total_machine_cost=mach_total,
            design_hours=design_hours,
            design_cost=design_cost,
            labor_hours=labor_hours,
            labor_cost=labor_cost,
            total_labor_cost=labor_total,
            finishing_hours=finishing_hours,
            finishing_cost=fin_cost,
            assembly_hours=assembly_hours,
            assembly_cost=asm_cost,
            other_shop_hours=other_shop_hours,
            other_shop_cost=other_cost,
            total_shop_operations_cost=shop_total,
            tool_wear_cost=tool_wear_cost,
            consumables_cost=consumables_cost,
            total_tool_cost=tool_total,
            overhead_cost=overhead,
            overhead_percentage=self.overhead_percentage,
            subtotal_cost=subtotal,
            profit_margin_amount=profit_amount,
            profit_margin_percentage=self.profit_margin_percentage,
            total_cost_before_tax=total_before_tax,
            tax_amount=tax,
            tax_percentage=self.tax_percentage,
            final_quote_price=final_price,
            quantity=quantity,
            cost_per_unit=cost_per_unit,
            pricing_strategy=self.pricing_strategy.value,
        )

    def set_hourly_rates(
        self,
        labor_rate: float = None,
        design_rate: float = None,
        setup_rate: float = None,
        runtime_rate: float = None,
        finishing_rate: float = None,
        assembly_rate: float = None,
    ) -> None:
        """Set custom hourly rates."""
        if labor_rate is not None:
            self.labor_hourly_rate = labor_rate
        if design_rate is not None:
            self.design_hourly_rate = design_rate
        if setup_rate is not None:
            self.machine_setup_rate = setup_rate
        if runtime_rate is not None:
            self.machine_runtime_rate = runtime_rate
        if finishing_rate is not None:
            self.finishing_hourly_rate = finishing_rate
        if assembly_rate is not None:
            self.assembly_hourly_rate = assembly_rate

    def set_overhead_and_margins(
        self,
        overhead_pct: float = None,
        profit_margin_pct: float = None,
        tax_pct: float = None,
    ) -> None:
        """Set overhead, profit margin, and tax percentages."""
        if overhead_pct is not None:
            self.overhead_percentage = max(0.0, min(100.0, overhead_pct))
        if profit_margin_pct is not None:
            self.profit_margin_percentage = max(0.0, min(100.0, profit_margin_pct))
        if tax_pct is not None:
            self.tax_percentage = max(0.0, min(100.0, tax_pct))
