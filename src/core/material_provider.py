"""
Material Provider for Texture Discovery

This module dynamically discovers material texture images from the resources/materials folder.
Replaces procedural grain generation with actual texture files.
"""

from pathlib import Path
from typing import List, Optional, Dict
import re

from src.core.logging_config import get_logger


class MaterialProvider:
    """
    Manage material textures by discovering them from the resources/materials directory.

    Features:
    - Dynamic discovery of material texture images
    - No hardcoded filenames
    - Supports PNG, JPG texture files
    - MTL file parsing for material properties
    """

    # Default materials directory
    DEFAULT_MATERIALS_DIR = Path(__file__).parent.parent / "resources" / "materials"

    def __init__(self):
        """Initialize the material provider."""
        self.logger = get_logger(__name__)
        self.logger.info("MaterialProvider initialized")

    def get_available_materials(self) -> List[Dict[str, any]]:
        """
        Dynamically discover all available material textures.

        Scans the materials directory for PNG/JPG files and MTL files.

        Returns:
            List of material dictionaries with name, texture_path, and properties
        """
        try:
            if not self.DEFAULT_MATERIALS_DIR.exists():
                self.logger.warning(f"Materials directory not found: {self.DEFAULT_MATERIALS_DIR}")
                return []

            materials = []

            # Find all texture images
            image_extensions = {'.png', '.jpg', '.jpeg'}
            texture_files = [
                f for f in self.DEFAULT_MATERIALS_DIR.iterdir()
                if f.is_file() and f.suffix.lower() in image_extensions
            ]

            # For each texture, check if there's a matching MTL file
            for texture_file in texture_files:
                material_name = texture_file.stem
                mtl_file = texture_file.with_suffix('.mtl')

                material_info = {
                    'name': material_name,
                    'texture_path': texture_file,
                    'mtl_path': mtl_file if mtl_file.exists() else None
                }

                # Parse MTL file if it exists
                if mtl_file.exists():
                    properties = self._parse_mtl_file(mtl_file)
                    material_info['properties'] = properties

                materials.append(material_info)

            self.logger.debug(f"Found {len(materials)} material textures")
            return sorted(materials, key=lambda m: m['name'])

        except Exception as e:
            self.logger.error(f"Error discovering materials: {e}", exc_info=True)
            return []

    def get_material_by_name(self, name: str) -> Optional[Dict[str, any]]:
        """
        Get a specific material by name.

        Args:
            name: Material name (filename without extension)

        Returns:
            Material info dictionary or None if not found
        """
        try:
            self.logger.debug(f"[STL_TEXTURE_DEBUG] Looking for material with name: '{name}'")
            materials = self.get_available_materials()
            self.logger.debug(f"[STL_TEXTURE_DEBUG] Found {len(materials)} available materials")

            for material in materials:
                self.logger.debug(f"[STL_TEXTURE_DEBUG] Checking material: '{material['name']}'")
                if material['name'].lower() == name.lower():
                    self.logger.info(f"[STL_TEXTURE_DEBUG] Found material '{name}' with texture_path: {material.get('texture_path')}")
                    return material

            self.logger.warning(f"[STL_TEXTURE_DEBUG] Material '{name}' not found in {len(materials)} materials")
            return None

        except Exception as e:
            self.logger.error(f"[STL_TEXTURE_DEBUG] Error getting material '{name}': {e}", exc_info=True)
            return None

    def get_material_texture_path(self, name: str) -> Optional[Path]:
        """
        Get the texture image path for a material.

        Args:
            name: Material name

        Returns:
            Path to texture image or None if not found
        """
        material = self.get_material_by_name(name)
        if material:
            return material.get('texture_path')
        return None

    def _parse_mtl_file(self, mtl_path: Path) -> Dict[str, any]:
        """
        Parse an MTL file to extract material properties.

        Args:
            mtl_path: Path to MTL file

        Returns:
            Dictionary of material properties
        """
        properties = {}

        try:
            self.logger.debug(f"Starting to parse MTL file: {mtl_path}")
            with open(mtl_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue

                    self.logger.debug(f"Parsing line {line_num}: {line}")

                    # Parse material properties
                    if line.startswith('newmtl'):
                        # Material name
                        parts = line.split(maxsplit=1)
                        if len(parts) > 1:
                            properties['material_name'] = parts[1]
                            self.logger.debug(f"Found material name: {parts[1]}")

                    elif line.startswith('Ns'):
                        # Specular exponent (shininess)
                        try:
                            properties['shininess'] = float(line.split()[1])
                            self.logger.debug(f"Found shininess: {properties['shininess']}")
                        except (IndexError, ValueError) as e:
                            self.logger.warning(f"Failed to parse Ns value: {e}")

                    elif line.startswith('Ka'):
                        # Ambient color
                        try:
                            parts = line.split()
                            properties['ambient'] = (float(parts[1]), float(parts[2]), float(parts[3]))
                            self.logger.debug(f"Found ambient color: {properties['ambient']}")
                        except (IndexError, ValueError) as e:
                            self.logger.warning(f"Failed to parse Ka values: {e}")

                    elif line.startswith('Kd'):
                        # Diffuse color
                        try:
                            parts = line.split()
                            properties['diffuse'] = (float(parts[1]), float(parts[2]), float(parts[3]))
                            self.logger.debug(f"Found diffuse color: {properties['diffuse']}")
                        except (IndexError, ValueError) as e:
                            self.logger.warning(f"Failed to parse Kd values: {e}")

                    elif line.startswith('Ks'):
                        # Specular color
                        try:
                            parts = line.split()
                            properties['specular'] = (float(parts[1]), float(parts[2]), float(parts[3]))
                            self.logger.debug(f"Found specular color: {properties['specular']}")
                        except (IndexError, ValueError) as e:
                            self.logger.warning(f"Failed to parse Ks values: {e}")

                    elif line.startswith('map_Kd'):
                        # Diffuse texture map
                        parts = line.split(maxsplit=1)
                        if len(parts) > 1:
                            texture_path = parts[1]
                            properties['diffuse_map'] = texture_path
                            self.logger.debug(f"Found diffuse texture map: {texture_path}")

                            # Resolve relative path
                            if not Path(texture_path).is_absolute():
                                resolved_path = mtl_path.parent / texture_path
                                properties['diffuse_map_resolved'] = str(resolved_path)
                                self.logger.debug(f"Resolved relative texture path: {texture_path} -> {resolved_path}")
                                if resolved_path.exists():
                                    self.logger.debug(f"Resolved texture path exists: {resolved_path}")
                                else:
                                    self.logger.warning(f"Resolved texture path does not exist: {resolved_path}")
                            else:
                                properties['diffuse_map_resolved'] = texture_path
                                self.logger.debug(f"Absolute texture path: {texture_path}")

            self.logger.info(f"Parsed MTL file: {mtl_path.name} with {len(properties)} properties")
            self.logger.debug(f"Final properties: {properties}")

        except Exception as e:
            self.logger.error(f"Error parsing MTL file {mtl_path}: {e}", exc_info=True)

        return properties

    def validate_texture(self, texture_path: Path) -> bool:
        """
        Validate that a texture file exists and is readable.

        Args:
            texture_path: Path to texture file

        Returns:
            True if valid, False otherwise
        """
        try:
            if not texture_path.exists():
                self.logger.warning(f"Texture file not found: {texture_path}")
                return False

            if not texture_path.is_file():
                self.logger.warning(f"Texture path is not a file: {texture_path}")
                return False

            # Check extension
            supported_extensions = {'.png', '.jpg', '.jpeg', '.bmp'}
            if texture_path.suffix.lower() not in supported_extensions:
                self.logger.warning(f"Unsupported texture format: {texture_path.suffix}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating texture: {e}", exc_info=True)
            return False
