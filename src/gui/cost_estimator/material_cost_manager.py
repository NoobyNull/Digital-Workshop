"""Material cost management for the cost estimator."""

from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import json
from pathlib import Path


@dataclass
class Material:
    """Data class for material information."""

    name: str
    cost_per_unit: float
    unit: str = "kg"
    description: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


class MaterialCostManager:
    """Manages material costs and library."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the material cost manager.

        Args:
            db_path: Path to store material library (optional)
        """
        self.db_path = db_path or str(
            Path.home() / ".digital_workshop" / "materials.json"
        )
        self.materials: Dict[str, Material] = {}
        self._load_materials()

    def _load_materials(self) -> None:
        """Load materials from file."""
        try:
            if Path(self.db_path).exists():
                with open(self.db_path, "r") as f:
                    data = json.load(f)
                    for name, material_data in data.items():
                        self.materials[name] = Material(**material_data)
            else:
                # Create default materials
                self._create_default_materials()
                self._save_materials()
        except Exception as e:
            print(f"Error loading materials: {e}")
            self._create_default_materials()

    def _create_default_materials(self) -> None:
        """Create default material library."""
        default_materials = {
            "Aluminum": Material("Aluminum", 15.0, "kg", "Aluminum stock"),
            "Steel": Material("Steel", 8.0, "kg", "Steel stock"),
            "Brass": Material("Brass", 12.0, "kg", "Brass stock"),
            "Wood (Oak)": Material("Wood (Oak)", 5.0, "board_ft", "Oak lumber"),
            "Wood (Maple)": Material("Wood (Maple)", 6.0, "board_ft", "Maple lumber"),
            "Plastic (ABS)": Material("Plastic (ABS)", 3.0, "kg", "ABS plastic"),
            "Plastic (PLA)": Material("Plastic (PLA)", 2.5, "kg", "PLA plastic"),
        }
        self.materials = default_materials

    def _save_materials(self) -> None:
        """Save materials to file."""
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.db_path, "w") as f:
                data = {
                    name: material.to_dict()
                    for name, material in self.materials.items()
                }
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving materials: {e}")

    def add_material(self, material: Material) -> bool:
        """
        Add a material to the library.

        Args:
            material: Material object to add

        Returns:
            True if successful, False otherwise
        """
        try:
            self.materials[material.name] = material
            self._save_materials()
            return True
        except Exception as e:
            print(f"Error adding material: {e}")
            return False

    def remove_material(self, name: str) -> bool:
        """
        Remove a material from the library.

        Args:
            name: Name of material to remove

        Returns:
            True if successful, False otherwise
        """
        try:
            if name in self.materials:
                del self.materials[name]
                self._save_materials()
                return True
            return False
        except Exception as e:
            print(f"Error removing material: {e}")
            return False

    def get_material(self, name: str) -> Optional[Material]:
        """
        Get a material by name.

        Args:
            name: Name of material

        Returns:
            Material object or None if not found
        """
        return self.materials.get(name)

    def get_all_materials(self) -> List[Material]:
        """
        Get all materials.

        Returns:
            List of all materials
        """
        return list(self.materials.values())

    def get_material_names(self) -> List[str]:
        """
        Get all material names.

        Returns:
            List of material names
        """
        return list(self.materials.keys())

    def update_material_cost(self, name: str, cost_per_unit: float) -> bool:
        """
        Update the cost of a material.

        Args:
            name: Name of material
            cost_per_unit: New cost per unit

        Returns:
            True if successful, False otherwise
        """
        try:
            if name in self.materials:
                self.materials[name].cost_per_unit = cost_per_unit
                self._save_materials()
                return True
            return False
        except Exception as e:
            print(f"Error updating material cost: {e}")
            return False
