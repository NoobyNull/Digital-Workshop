"""Cost Calculator for estimating project costs."""

from typing import Dict
from dataclasses import dataclass
from enum import Enum


class CostType(Enum):
    """Types of costs that can be estimated."""

    MATERIAL = "material"
    MACHINE_TIME = "machine_time"
    LABOR = "labor"
    OVERHEAD = "overhead"
    TOTAL = "total"


@dataclass
class CostEstimate:
    """Data class for cost estimates."""

    material_cost: float = 0.0
    machine_time_hours: float = 0.0
    machine_time_cost: float = 0.0
    labor_hours: float = 0.0
    labor_cost: float = 0.0
    overhead_cost: float = 0.0
    total_cost: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "material_cost": self.material_cost,
            "machine_time_hours": self.machine_time_hours,
            "machine_time_cost": self.machine_time_cost,
            "labor_hours": self.labor_hours,
            "labor_cost": self.labor_cost,
            "overhead_cost": self.overhead_cost,
            "total_cost": self.total_cost,
        }


class CostCalculator:
    """Main cost calculator for projects."""

    def __init__(self):
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
            machine_time_cost=machine_time_cost,
            labor_cost=labor_cost,
            overhead_cost=overhead_cost,
            total_cost=total_cost,
        )
