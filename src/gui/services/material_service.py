"""
Enhanced material management service with validation, preview, and search capabilities.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import Signal, QThread
from PySide6.QtGui import QImage

from src.core.logging_config import get_logger
from src.core.settings_manager import get_settings_manager
from .gui_service_interfaces import IMaterialService, IViewerUIService


class MaterialCategory(Enum):
    """Material categories."""

    WOOD = "wood"
    METAL = "metal"
    PLASTIC = "plastic"
    FABRIC = "fabric"
    STONE = "stone"
    GLASS = "glass"
    CERAMIC = "ceramic"
    LIQUID = "liquid"
    ORGANIC = "organic"
    SYNTHETIC = "synthetic"
    COMPOSITE = "composite"


@dataclass
class MaterialValidationResult:
    """Material validation result."""

    is_valid: bool
    error_message: str
    warnings: List[str]
    suggestions: List[str]


@dataclass
class MaterialInfo:
    """Material information structure."""

    name: str
    category: MaterialCategory
    description: str
    properties: Dict[str, Any]
    preview_image_path: Optional[str] = None
    created_date: Optional[str] = None
    modified_date: Optional[str] = None
    version: str = "1.0"


class MaterialValidationWorker(QThread):
    """Worker thread for validating materials asynchronously."""

    validation_completed = Signal(str, object)  # material_name, MaterialValidationResult
    validation_progress = Signal(str, float)  # material_name, progress_percentage

    def __init__(self, material_data: Dict[str, Any], material_name: str) -> None:
        """
        Initialize material validation worker.

        Args:
            material_data: Material data to validate
            material_name: Name of the material
        """
        super().__init__()
        self.material_data = material_data
        self.material_name = material_name
        self.logger = get_logger(__name__)

    def run(self) -> None:
        """Run material validation."""
        try:
            self.logger.info("Starting material validation: %s", self.material_name)

            # Simulate validation steps
            validation_steps = [
                ("Checking data structure", 20),
                ("Validating properties", 40),
                ("Checking preview image", 60),
                ("Validating references", 80),
                ("Final validation", 100),
            ]

            for step_name, progress in validation_steps:
                self.validation_progress.emit(self.material_name, progress)
                time.sleep(0.05)  # Simulate work

                # Check for cancellation
                if self.isInterruptionRequested():
                    self.logger.info("Material validation cancelled")
                    return

            # Perform actual validation
            result = self._validate_material_data()

            self.validation_completed.emit(self.material_name, result)

            if result.is_valid:
                self.logger.info("Material validation successful: %s", self.material_name)
            else:
                self.logger.warning(
                    f"Material validation failed: {self.material_name} - {result.error_message}"
                )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error during material validation: %s", e, exc_info=True)
            error_result = MaterialValidationResult(False, str(e), [], [])
            self.validation_completed.emit(self.material_name, error_result)

    def _validate_material_data(self) -> MaterialValidationResult:
        """Validate material data structure and content."""
        try:
            warnings = []
            suggestions = []

            # Check required fields
            required_fields = ["name", "category", "properties"]
            missing_fields = []
            for field in required_fields:
                if field not in self.material_data:
                    missing_fields.append(field)

            if missing_fields:
                return MaterialValidationResult(
                    False,
                    f"Missing required fields: {', '.join(missing_fields)}",
                    warnings,
                    suggestions,
                )

            # Validate name
            name = self.material_data.get("name", "").strip()
            if not name:
                return MaterialValidationResult(
                    False, "Material name cannot be empty", warnings, suggestions
                )

            if len(name) > 100:
                warnings.append("Material name is quite long and may be truncated in UI")

            # Validate category
            category_str = self.material_data.get("category", "").lower()
            try:
                category = MaterialCategory(category_str)
            except ValueError:
                valid_categories = [c.value for c in MaterialCategory]
                return MaterialValidationResult(
                    False,
                    f"Invalid category '{category_str}'. Valid categories: {', '.join(valid_categories)}",
                    warnings,
                    suggestions,
                )

            # Validate properties
            properties = self.material_data.get("properties", {})
            if not isinstance(properties, dict):
                return MaterialValidationResult(
                    False, "Properties must be a dictionary", warnings, suggestions
                )

            # Check property types
            numeric_properties = [
                "density",
                "hardness",
                "thermal_conductivity",
                "electrical_conductivity",
            ]
            for prop in numeric_properties:
                if prop in properties:
                    try:
                        float(properties[prop])
                    except (ValueError, TypeError):
                        warnings.append(f"Property '{prop}' should be numeric")

            # Check color properties
            color_properties = ["base_color", "specular_color", "emission_color"]
            for prop in color_properties:
                if prop in properties:
                    color_val = properties[prop]
                    if isinstance(color_val, str):
                        # Basic hex color validation
                        if not (color_val.startswith("#") and len(color_val) in [4, 7, 9]):
                            warnings.append(f"Color property '{prop}' should be in hex format")

            # Check preview image
            preview_path = self.material_data.get("preview_image_path")
            if preview_path:
                if not Path(preview_path).exists():
                    warnings.append(f"Preview image not found: {preview_path}")

            # Generate suggestions
            if not preview_path:
                suggestions.append(
                    "Consider adding a preview image for better material identification"
                )

            if "base_color" not in properties:
                suggestions.append("Consider adding a base_color property")

            if "roughness" not in properties:
                suggestions.append("Consider adding a roughness property for PBR materials")

            return MaterialValidationResult(True, "", warnings, suggestions)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return MaterialValidationResult(False, f"Validation error: {e}", [], [])


class MaterialService(IMaterialService):
    """Enhanced material service with validation, preview, and search capabilities."""

    def __init__(self, ui_service: IViewerUIService) -> None:
        """
        Initialize material service.

        Args:
            ui_service: UI service for progress and state management
        """
        super().__init__()
        self.ui_service = ui_service
        self.logger = get_logger(__name__)

        # Material storage
        self.materials: Dict[str, MaterialInfo] = {}
        self.material_categories: Dict[MaterialCategory, List[str]] = {}
        self.material_cache: Dict[str, Dict[str, Any]] = {}
        self.validation_workers: Dict[str, MaterialValidationWorker] = {}

        # Storage paths
        self.materials_directory = Path("materials")
        self.previews_directory = Path("materials/previews")
        self.templates_directory = Path("materials/templates")

        # Settings
        self.settings_manager = get_settings_manager()

        # Ensure directories exist
        self._setup_directories()

        # Load existing materials
        self._load_materials()

        self.logger.info("Material service initialized")

    def _setup_directories(self) -> None:
        """Create necessary directories."""
        try:
            self.materials_directory.mkdir(exist_ok=True)
            self.previews_directory.mkdir(exist_ok=True)
            self.templates_directory.mkdir(exist_ok=True)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error creating material directories: %s", e)

    def _load_materials(self) -> None:
        """Load existing materials from storage."""
        try:
            # Load from JSON files in materials directory
            if self.materials_directory.exists():
                for material_file in self.materials_directory.glob("*.json"):
                    material_data = self._load_material_file(material_file)
                    if material_data:
                        material_info = self._create_material_info(material_data)
                        if material_info:
                            self.materials[material_info.name] = material_info

            # Build category index
            self._build_category_index()

            self.logger.info("Loaded %s materials", len(self.materials))

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error loading materials: %s", e)

    def _build_category_index(self) -> None:
        """Build index of materials by category."""
        self.material_categories.clear()

        for material_name, material_info in self.materials.items():
            category = material_info.category
            if category not in self.material_categories:
                self.material_categories[category] = []
            self.material_categories[category].append(material_name)

    def validate_material(self, material_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate material data before application."""
        try:
            material_name = material_data.get("name", "Unknown")

            # Check if validation is already running
            if material_name in self.validation_workers:
                worker = self.validation_workers[material_name]
                if worker.isRunning():
                    return False, "Material validation is already in progress"

            # Start validation worker
            worker = MaterialValidationWorker(material_data, material_name)
            worker.validation_completed.connect(self._on_validation_completed)
            worker.validation_progress.connect(self._on_validation_progress)

            self.validation_workers[material_name] = worker
            worker.start()

            # Return immediate result for basic validation
            basic_valid, basic_error = self._validate_material_basic(material_data)
            return basic_valid, basic_error

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error validating material: %s", e)
            return False, f"Validation error: {e}"

    def _validate_material_basic(self, material_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Perform basic material validation."""
        try:
            # Check required fields
            required_fields = ["name", "category", "properties"]
            for field in required_fields:
                if field not in material_data:
                    return False, f"Missing required field: {field}"

            # Validate category
            try:
                category = MaterialCategory(material_data["category"].lower())
            except (ValueError, AttributeError):
                valid_categories = [c.value for c in MaterialCategory]
                return (
                    False,
                    f"Invalid category. Valid categories: {', '.join(valid_categories)}",
                )

            return True, ""

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return False, f"Basic validation error: {e}"

    def get_material_preview(self, material_name: str) -> Optional[bytes]:
        """Get preview image for a material."""
        try:
            material_info = self.materials.get(material_name)
            if not material_info or not material_info.preview_image_path:
                return None

            preview_path = Path(material_info.preview_image_path)
            if not preview_path.exists():
                # Try to generate preview from material properties
                return self._generate_material_preview(material_info)

            # Load existing preview
            with open(preview_path, "rb") as f:
                return f.read()

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error getting material preview: %s", e)
            return None

    def _generate_material_preview(self, material_info: MaterialInfo) -> Optional[bytes]:
        """Generate preview image for a material."""
        try:
            # Create a simple preview based on material properties
            from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont
            from PySide6.QtCore import QSize, Qt, QRect

            # Create image
            image_size = QSize(200, 200)
            image = QImage(image_size, QImage.Format.Format_ARGB32_Premultiplied)
            painter = QPainter(image)

            # Fill background
            painter.fillRect(image.rect(), QColor(240, 240, 240))

            # Get material color from properties
            base_color = material_info.properties.get("base_color")

            # Use theme color if no material color specified
            if not base_color:
                try:
                    from src.gui.theme import vtk_rgb

                    theme_color = vtk_rgb("material")
                    base_color = f"#{theme_color[0]:02x}{theme_color[1]:02x}{theme_color[2]:02x}"
                except (ImportError, AttributeError):
                    base_color = "#CCCCCC"  # Keep minimal fallback only

            if isinstance(base_color, str):
                color = QColor(base_color)
            else:
                color = QColor(200, 200, 200)

            # Draw material representation
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.PenStyle.NoPen))

            # Draw main material area
            main_rect = QRect(20, 20, 160, 100)
            painter.drawRect(main_rect)

            # Add some texture based on material type
            if material_info.category == MaterialCategory.WOOD:
                # Draw wood grain lines
                painter.setPen(QPen(QColor(139, 69, 19), 1))
                for i in range(25, 165, 10):
                    painter.drawLine(i, 25, i, 115)
            elif material_info.category == MaterialCategory.METAL:
                # Draw metallic shine
                painter.setPen(QPen(QColor(255, 255, 255), 2))
                painter.drawLine(25, 35, 175, 35)
                painter.drawLine(25, 55, 175, 55)

            # Draw material name
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            painter.drawText(20, 140, material_info.name)

            # Draw category
            painter.setFont(QFont("Arial", 10))
            painter.drawText(20, 160, material_info.category.value.title())

            painter.end()

            # Convert to bytes
            from PySide6.QtCore import QBuffer, QByteArray

            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QBuffer.OpenModeFlag.ReadWrite)
            image.save(buffer, b"PNG")
            buffer.close()

            return bytes(byte_array)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error generating material preview: %s", e)
            return None

    def create_material_from_template(
        self, template_name: str, custom_params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create a new material from a template."""
        try:
            template_path = self.templates_directory / f"{template_name}.json"
            if not template_path.exists():
                self.logger.error("Template not found: %s", template_path)
                return None

            # Load template
            with open(template_path, "r", encoding="utf-8") as f:
                template_data = json.load(f)

            # Apply custom parameters
            material_data = template_data.copy()
            material_data.update(custom_params)

            # Generate unique name if not provided
            if "name" not in custom_params:
                base_name = template_data.get("name", "Material")
                material_data["name"] = self._generate_unique_material_name(base_name)

            # Validate created material
            is_valid, error_message = self.validate_material(material_data)
            if not is_valid:
                self.logger.error("Template material validation failed: %s", error_message)
                return None

            return material_data

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error creating material from template: %s", e)
            return None

    def _generate_unique_material_name(self, base_name: str) -> str:
        """Generate a unique material name."""
        counter = 1
        original_name = base_name

        while base_name in self.materials:
            base_name = f"{original_name}_{counter}"
            counter += 1

        return base_name

    def get_material_categories(self) -> List[str]:
        """Get list of available material categories."""
        return [category.value for category in MaterialCategory]

    def search_materials(self, query: str, category: Optional[str] = None) -> List[str]:
        """Search for materials by name and optionally category."""
        try:
            query_lower = query.lower().strip()
            results = []

            for material_name, material_info in self.materials.items():
                # Check name match
                name_match = query_lower in material_name.lower()

                # Check description match
                desc_match = query_lower in material_info.description.lower()

                # Check category filter
                category_match = True
                if category:
                    category_match = material_info.category.value == category.lower()

                # Check properties match
                properties_match = False
                for prop_name, prop_value in material_info.properties.items():
                    if isinstance(prop_value, str) and query_lower in prop_value.lower():
                        properties_match = True
                        break

                if (name_match or desc_match or properties_match) and category_match:
                    results.append(material_name)

            return sorted(results)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error searching materials: %s", e)
            return []

    def get_material_templates(self) -> List[str]:
        """Get list of available material templates."""
        try:
            templates = []
            if self.templates_directory.exists():
                for template_file in self.templates_directory.glob("*.json"):
                    templates.append(template_file.stem)
            return sorted(templates)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error getting material templates: %s", e)
            return []

    def save_material(self, material_data: Dict[str, Any]) -> bool:
        """Save material data to storage."""
        try:
            material_name = material_data.get("name")
            if not material_name:
                self.logger.error("Cannot save material without name")
                return False

            # Validate before saving
            is_valid, error_message = self.validate_material(material_data)
            if not is_valid:
                self.logger.error("Cannot save invalid material: %s", error_message)
                return False

            # Save to file
            material_file = self.materials_directory / f"{material_name}.json"
            with open(material_file, "w", encoding="utf-8") as f:
                json.dump(material_data, f, indent=2, ensure_ascii=False)

            # Update in-memory cache
            material_info = self._create_material_info(material_data)
            if material_info:
                self.materials[material_name] = material_info
                self._build_category_index()

            self.logger.info("Material saved: %s", material_name)
            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error saving material: %s", e)
            return False

    def _create_material_info(self, material_data: Dict[str, Any]) -> Optional[MaterialInfo]:
        """Create MaterialInfo from material data."""
        try:
            return MaterialInfo(
                name=material_data.get("name", ""),
                category=MaterialCategory(material_data.get("category", "synthetic").lower()),
                description=material_data.get("description", ""),
                properties=material_data.get("properties", {}),
                preview_image_path=material_data.get("preview_image_path"),
                created_date=material_data.get("created_date"),
                modified_date=material_data.get("modified_date"),
                version=material_data.get("version", "1.0"),
            )
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error creating material info: %s", e)
            return None

    def _load_material_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load material data from file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error loading material file %s: {e}", file_path)
            return None

    def _on_validation_completed(
        self, material_name: str, result: MaterialValidationResult
    ) -> None:
        """Handle validation completion."""
        try:
            if material_name in self.validation_workers:
                del self.validation_workers[material_name]

            if not result.is_valid:
                self.logger.warning(
                    f"Material validation failed: {material_name} - {result.error_message}"
                )
            if result.warnings:
                self.logger.info(
                    f"Material validation warnings: {material_name} - {result.warnings}"
                )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error handling validation completion: %s", e)

    def _on_validation_progress(self, material_name: str, progress: float) -> None:
        """Handle validation progress updates."""
        try:
            self.logger.debug("Material validation progress: %s - {progress:.1f}%", material_name)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error handling validation progress: %s", e)
