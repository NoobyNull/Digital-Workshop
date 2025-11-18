"""
Material repository for handling default materials in the database.

This module provides CRUD operations for materials that can be associated with models.
"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


class MaterialRepository:
    """Repository for managing materials in the database."""

    def __init__(self, get_connection_func):
        """
        Initialize the material repository.

        Args:
            get_connection_func: Function to get database connection
        """
        self._get_connection = get_connection_func
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info("MaterialRepository initialized")

    @log_function_call(logger)
    def add_material(
        self,
        name: str,
        file_path: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        texture_path: Optional[str] = None,
        mtl_path: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        is_default: bool = True,
        is_deletable: bool = False,
    ) -> int:
        """
        Add a new material to the database.

        Args:
            name: Material name (unique identifier)
            file_path: Path to material file
            display_name: Human-readable display name
            description: Material description
            texture_path: Path to texture image
            mtl_path: Path to MTL file
            properties: Additional material properties as JSON
            is_default: Whether this is a default material (cannot be deleted)
            is_deletable: Whether this material can be deleted

        Returns:
            ID of the newly created material
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Calculate file hash if file exists
                file_hash = None
                if Path(file_path).exists():
                    from src.utils.file_hash import calculate_file_hash

                    file_hash = calculate_file_hash(file_path)

                cursor.execute(
                    """
                    INSERT INTO materials (
                        name, display_name, description, file_path, file_hash,
                        texture_path, mtl_path, properties_json, is_default, is_deletable
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        name,
                        display_name or name,
                        description,
                        file_path,
                        file_hash,
                        texture_path,
                        mtl_path,
                        str(properties) if properties else None,
                        is_default,
                        is_deletable,
                    ),
                )

                material_id = cursor.lastrowid
                conn.commit()
                self.logger.info("Added material '%s' with ID %s", name, material_id)
                return material_id

        except sqlite3.IntegrityError:
            self.logger.error("Material with name '%s' already exists", name)
            raise
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to add material '%s': %s", name, e)
            raise

    @log_function_call(logger)
    def get_material(self, material_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a material by ID.

        Args:
            material_id: Material ID

        Returns:
            Material dictionary or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM materials WHERE id = ?",
                    (material_id,),
                )
                row = cursor.fetchone()

                if row:
                    material = dict(row)
                    if material.get("properties_json"):
                        try:
                            # Convert string back to dict if it's JSON
                            import json

                            material["properties"] = json.loads(material["properties_json"])
                        except (json.JSONDecodeError, TypeError):
                            material["properties"] = {}
                    return material

                return None

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to get material %s: %s", material_id, e)
            return None

    @log_function_call(logger)
    def get_material_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a material by name.

        Args:
            name: Material name

        Returns:
            Material dictionary or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM materials WHERE name = ?",
                    (name,),
                )
                row = cursor.fetchone()

                if row:
                    material = dict(row)
                    if material.get("properties_json"):
                        try:
                            import json

                            material["properties"] = json.loads(material["properties_json"])
                        except (json.JSONDecodeError, TypeError):
                            material["properties"] = {}
                    return material

                return None

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to get material by name '%s': %s", name, e)
            return None

    @log_function_call(logger)
    def get_all_materials(self, include_deletable: bool = True) -> List[Dict[str, Any]]:
        """
        Get all materials from the database.

        Args:
            include_deletable: Whether to include deletable materials

        Returns:
            List of material dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if include_deletable:
                    cursor.execute("SELECT * FROM materials ORDER BY is_default DESC, name ASC")
                else:
                    cursor.execute("SELECT * FROM materials WHERE is_default = 1 ORDER BY name ASC")

                rows = cursor.fetchall()
                materials = []

                for row in rows:
                    material = dict(row)
                    if material.get("properties_json"):
                        try:
                            import json

                            material["properties"] = json.loads(material["properties_json"])
                        except (json.JSONDecodeError, TypeError):
                            material["properties"] = {}
                    materials.append(material)

                return materials

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to get all materials: %s", e)
            return []

    @log_function_call(logger)
    def get_default_materials(self) -> List[Dict[str, Any]]:
        """
        Get all default materials (cannot be deleted).

        Returns:
            List of default material dictionaries
        """
        return self.get_all_materials(include_deletable=False)

    @log_function_call(logger)
    def update_material(
        self,
        material_id: int,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        texture_path: Optional[str] = None,
        mtl_path: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update material information.

        Args:
            material_id: Material ID
            display_name: New display name
            description: New description
            texture_path: New texture path
            mtl_path: New MTL path
            properties: New properties

        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Build update query dynamically
                updates = []
                params = []

                if display_name is not None:
                    updates.append("display_name = ?")
                    params.append(display_name)

                if description is not None:
                    updates.append("description = ?")
                    params.append(description)

                if texture_path is not None:
                    updates.append("texture_path = ?")
                    params.append(texture_path)

                if mtl_path is not None:
                    updates.append("mtl_path = ?")
                    params.append(mtl_path)

                if properties is not None:
                    import json

                    updates.append("properties_json = ?")
                    params.append(json.dumps(properties))

                if not updates:
                    return False

                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(material_id)

                query = f"UPDATE materials SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, params)

                success = cursor.rowcount > 0
                conn.commit()

                if success:
                    self.logger.info("Updated material %s", material_id)
                else:
                    self.logger.warning("Material %s not found for update", material_id)

                return success

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to update material %s: %s", material_id, e)
            return False

    @log_function_call(logger)
    def delete_material(self, material_id: int) -> bool:
        """
        Delete a material from the database.

        Args:
            material_id: Material ID

        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Check if material is deletable
                cursor.execute("SELECT is_default FROM materials WHERE id = ?", (material_id,))
                row = cursor.fetchone()

                if not row:
                    self.logger.warning("Material %s not found for deletion", material_id)
                    return False

                if row[0]:  # is_default is True
                    self.logger.error("Cannot delete default material %s", material_id)
                    return False

                # Delete the material
                cursor.execute("DELETE FROM materials WHERE id = ?", (material_id,))

                success = cursor.rowcount > 0
                conn.commit()

                if success:
                    self.logger.info("Deleted material %s", material_id)
                else:
                    self.logger.warning("Material %s not found for deletion", material_id)

                return success

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to delete material %s: %s", material_id, e)
            return False

    @log_function_call(logger)
    def get_materials_by_type(self, material_type: str = "wood") -> List[Dict[str, Any]]:
        """
        Get materials by type.

        Args:
            material_type: Type of materials to get

        Returns:
            List of material dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM materials WHERE type = ? ORDER BY name ASC",
                    (material_type,),
                )

                rows = cursor.fetchall()
                materials = []

                for row in rows:
                    material = dict(row)
                    if material.get("properties_json"):
                        try:
                            import json

                            material["properties"] = json.loads(material["properties_json"])
                        except (json.JSONDecodeError, TypeError):
                            material["properties"] = {}
                    materials.append(material)

                return materials

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to get materials by type '%s': %s", material_type, e)
            return []

    @log_function_call(logger)
    def initialize_default_materials(self) -> None:
        """
        Initialize the database with default materials from the filesystem.

        This method scans the materials directory and adds all found materials to the database
        as default, non-deletable resources.
        """
        try:
            materials_dir = Path(__file__).parent.parent.parent / "resources" / "materials"

            if not materials_dir.exists():
                self.logger.warning("Materials directory not found: %s", materials_dir)
                return

            # Find all texture files
            image_extensions = {".png", ".jpg", ".jpeg"}
            texture_files = [
                f
                for f in materials_dir.iterdir()
                if f.is_file() and f.suffix.lower() in image_extensions
            ]

            added_count = 0

            for texture_file in texture_files:
                material_name = texture_file.stem

                # Check if material already exists
                if self.get_material_by_name(material_name):
                    continue

                # Check for MTL file
                mtl_file = texture_file.with_suffix(".mtl")
                mtl_path = str(mtl_file) if mtl_file.exists() else None

                # Parse MTL properties if available
                properties = None
                if mtl_path and mtl_file.exists():
                    # Simple MTL parsing - just check for basic properties
                    properties = {}
                    try:
                        with open(mtl_file, "r") as f:
                            for line in f:
                                line = line.strip()
                                if line.startswith("newmtl"):
                                    parts = line.split(maxsplit=1)
                                    if len(parts) > 1:
                                        properties["material_name"] = parts[1]
                                elif line.startswith("Ns"):
                                    try:
                                        properties["shininess"] = float(line.split()[1])
                                    except (IndexError, ValueError):
                                        pass
                                elif line.startswith("Ka"):
                                    try:
                                        parts = line.split()
                                        properties["ambient"] = (
                                            float(parts[1]),
                                            float(parts[2]),
                                            float(parts[3]),
                                        )
                                    except (IndexError, ValueError):
                                        pass
                                elif line.startswith("Kd"):
                                    try:
                                        parts = line.split()
                                        properties["diffuse"] = (
                                            float(parts[1]),
                                            float(parts[2]),
                                            float(parts[3]),
                                        )
                                    except (IndexError, ValueError):
                                        pass
                                elif line.startswith("Ks"):
                                    try:
                                        parts = line.split()
                                        properties["specular"] = (
                                            float(parts[1]),
                                            float(parts[2]),
                                            float(parts[3]),
                                        )
                                    except (IndexError, ValueError):
                                        pass
                    except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError):
                        pass

                # Add material to database
                self.add_material(
                    name=material_name,
                    file_path=str(texture_file),
                    display_name=material_name.replace("_", " ").title(),
                    description=f"Default {material_name} material",
                    texture_path=str(texture_file),
                    mtl_path=mtl_path,
                    properties=properties,
                    is_default=True,
                    is_deletable=False,
                )
                added_count += 1

            self.logger.info("Initialized %s default materials from filesystem", added_count)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to initialize default materials: %s", e)
            raise
