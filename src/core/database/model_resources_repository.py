"""
Model resources repository for handling associations between models and resources.

This module manages the many-to-many relationship between models and their associated
materials and backgrounds.
"""

import sqlite3
from typing import Any, Dict, List, Optional

from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


class ModelResourcesRepository:
    """Repository for managing model-resource associations."""

    def __init__(self, get_connection_func):
        """
        Initialize the model resources repository.

        Args:
            get_connection_func: Function to get database connection
        """
        self._get_connection = get_connection_func
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info("ModelResourcesRepository initialized")

    @log_function_call(logger)
    def associate_resource_with_model(
        self,
        model_id: int,
        resource_type: str,  # 'material' or 'background'
        resource_id: int,
        is_primary: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Associate a resource with a model.

        Args:
            model_id: ID of the model
            resource_type: Type of resource ('material' or 'background')
            resource_id: ID of the resource
            is_primary: Whether this is the primary resource of this type
            metadata: Additional metadata as JSON

        Returns:
            ID of the newly created association
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # If this is a primary resource, ensure no other primary resource of same type exists
                if is_primary:
                    cursor.execute(
                        "UPDATE model_resources SET is_primary = 0 WHERE model_id = ? AND resource_type = ?",
                        (model_id, resource_type),
                    )

                cursor.execute(
                    """
                    INSERT INTO model_resources (
                        model_id, resource_type, resource_id, is_primary, metadata_json
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        model_id,
                        resource_type,
                        resource_id,
                        is_primary,
                        str(metadata) if metadata else None,
                    ),
                )

                association_id = cursor.lastrowid
                conn.commit()
                self.logger.info(
                    "Associated %s %s with model %s (association ID: %s)",
                    resource_type,
                    resource_id,
                    model_id,
                    association_id,
                )
                return association_id

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error(
                "Failed to associate %s %s with model %s: %s",
                resource_type,
                resource_id,
                model_id,
                e,
            )
            raise

    @log_function_call(logger)
    def get_model_resources(self, model_id: int) -> List[Dict[str, Any]]:
        """
        Get all resources associated with a model.

        Args:
            model_id: ID of the model

        Returns:
            List of resource associations with resource details
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Get material associations
                cursor.execute(
                    """
                    SELECT 
                        mr.*,
                        m.id as resource_db_id,
                        m.name as resource_name,
                        m.display_name as resource_display_name,
                        m.file_path as resource_file_path,
                        m.type as resource_type_specific,
                        m.properties_json
                    FROM model_resources mr
                    JOIN materials m ON mr.resource_id = m.id
                    WHERE mr.model_id = ? AND mr.resource_type = 'material'
                    """,
                    (model_id,),
                )
                material_rows = cursor.fetchall()

                # Get background associations
                cursor.execute(
                    """
                    SELECT 
                        mr.*,
                        b.id as resource_db_id,
                        b.name as resource_name,
                        b.display_name as resource_display_name,
                        b.file_path as resource_file_path,
                        b.type as resource_type_specific,
                        NULL as properties_json
                    FROM model_resources mr
                    JOIN backgrounds b ON mr.resource_id = b.id
                    WHERE mr.model_id = ? AND mr.resource_type = 'background'
                    """,
                    (model_id,),
                )
                background_rows = cursor.fetchall()

                # Combine and process results
                associations = []

                for row in material_rows + background_rows:
                    association = dict(row)

                    # Parse metadata if it exists
                    if association.get("metadata_json"):
                        try:
                            import json

                            association["metadata"] = json.loads(
                                association["metadata_json"]
                            )
                        except (json.JSONDecodeError, TypeError):
                            association["metadata"] = {}

                    # Parse properties if they exist
                    if association.get("properties_json"):
                        try:
                            import json

                            association["resource_properties"] = json.loads(
                                association["properties_json"]
                            )
                        except (json.JSONDecodeError, TypeError):
                            association["resource_properties"] = {}

                    # Clean up JSON fields
                    association.pop("metadata_json", None)
                    association.pop("properties_json", None)

                    associations.append(association)

                return associations

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to get resources for model %s: %s", model_id, e)
            return []

    @log_function_call(logger)
    def get_model_materials(self, model_id: int) -> List[Dict[str, Any]]:
        """
        Get all materials associated with a model.

        Args:
            model_id: ID of the model

        Returns:
            List of material associations
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT 
                        mr.*,
                        m.id as material_id,
                        m.name as material_name,
                        m.display_name as material_display_name,
                        m.file_path as material_file_path,
                        m.texture_path as material_texture_path,
                        m.mtl_path as material_mtl_path,
                        m.properties_json
                    FROM model_resources mr
                    JOIN materials m ON mr.resource_id = m.id
                    WHERE mr.model_id = ? AND mr.resource_type = 'material'
                    ORDER BY mr.is_primary DESC, mr.created_at ASC
                    """,
                    (model_id,),
                )
                rows = cursor.fetchall()

                materials = []
                for row in rows:
                    material = dict(row)

                    # Parse properties if they exist
                    if material.get("properties_json"):
                        try:
                            import json

                            material["properties"] = json.loads(
                                material["properties_json"]
                            )
                        except (json.JSONDecodeError, TypeError):
                            material["properties"] = {}

                    # Clean up JSON field
                    material.pop("properties_json", None)
                    materials.append(material)

                return materials

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to get materials for model %s: %s", model_id, e)
            return []

    @log_function_call(logger)
    def get_model_backgrounds(self, model_id: int) -> List[Dict[str, Any]]:
        """
        Get all backgrounds associated with a model.

        Args:
            model_id: ID of the model

        Returns:
            List of background associations
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT 
                        mr.*,
                        b.id as background_id,
                        b.name as background_name,
                        b.display_name as background_display_name,
                        b.file_path as background_file_path,
                        b.thumbnail_path as background_thumbnail_path
                    FROM model_resources mr
                    JOIN backgrounds b ON mr.resource_id = b.id
                    WHERE mr.model_id = ? AND mr.resource_type = 'background'
                    ORDER BY mr.is_primary DESC, mr.created_at ASC
                    """,
                    (model_id,),
                )
                rows = cursor.fetchall()

                return [dict(row) for row in rows]

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to get backgrounds for model %s: %s", model_id, e)
            return []

    @log_function_call(logger)
    def get_primary_material(self, model_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the primary material for a model.

        Args:
            model_id: ID of the model

        Returns:
            Primary material association or None if not found
        """
        try:
            materials = self.get_model_materials(model_id)
            for material in materials:
                if material.get("is_primary"):
                    return material

            # If no primary material found, return the first one
            return materials[0] if materials else None

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error(
                "Failed to get primary material for model %s: %s", model_id, e
            )
            return None

    @log_function_call(logger)
    def get_primary_background(self, model_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the primary background for a model.

        Args:
            model_id: ID of the model

        Returns:
            Primary background association or None if not found
        """
        try:
            backgrounds = self.get_model_backgrounds(model_id)
            for background in backgrounds:
                if background.get("is_primary"):
                    return background

            # If no primary background found, return the first one
            return backgrounds[0] if backgrounds else None

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error(
                "Failed to get primary background for model %s: %s", model_id, e
            )
            return None

    @log_function_call(logger)
    def update_resource_association(
        self,
        association_id: int,
        is_primary: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update a model-resource association.

        Args:
            association_id: ID of the association
            is_primary: Whether this should be the primary resource
            metadata: Updated metadata

        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Get current association to determine type
                cursor.execute(
                    "SELECT model_id, resource_type FROM model_resources WHERE id = ?",
                    (association_id,),
                )
                row = cursor.fetchone()

                if not row:
                    self.logger.warning(
                        "Association %s not found for update", association_id
                    )
                    return False

                model_id, resource_type = row

                # Build update query dynamically
                updates = []
                params = []

                if is_primary is not None:
                    # If setting as primary, clear other primary resources of same type
                    if is_primary:
                        cursor.execute(
                            "UPDATE model_resources SET is_primary = 0 WHERE model_id = ? AND resource_type = ?",
                            (model_id, resource_type),
                        )
                    updates.append("is_primary = ?")
                    params.append(is_primary)

                if metadata is not None:
                    import json

                    updates.append("metadata_json = ?")
                    params.append(json.dumps(metadata))

                if not updates:
                    return False

                updates.append("created_at = CURRENT_TIMESTAMP")  # Update timestamp
                params.append(association_id)

                query = f"UPDATE model_resources SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, params)

                success = cursor.rowcount > 0
                conn.commit()

                if success:
                    self.logger.info("Updated association %s", association_id)
                else:
                    self.logger.warning(
                        "Association %s not found for update", association_id
                    )

                return success

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to update association %s: %s", association_id, e)
            return False

    @log_function_call(logger)
    def remove_resource_association(
        self, model_id: int, resource_type: str, resource_id: int
    ) -> bool:
        """
        Remove a resource association from a model.

        Args:
            model_id: ID of the model
            resource_type: Type of resource ('material' or 'background')
            resource_id: ID of the resource

        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    "DELETE FROM model_resources WHERE model_id = ? AND resource_type = ? AND resource_id = ?",
                    (model_id, resource_type, resource_id),
                )

                success = cursor.rowcount > 0
                conn.commit()

                if success:
                    self.logger.info(
                        "Removed %s %s from model %s",
                        resource_type,
                        resource_id,
                        model_id,
                    )
                else:
                    self.logger.warning(
                        "Association not found for model %s, %s %s",
                        model_id,
                        resource_type,
                        resource_id,
                    )

                return success

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error(
                "Failed to remove %s %s from model %s: %s",
                resource_type,
                resource_id,
                model_id,
                e,
            )
            return False

    @log_function_call(logger)
    def remove_all_model_resources(self, model_id: int) -> int:
        """
        Remove all resource associations from a model.

        Args:
            model_id: ID of the model

        Returns:
            Number of associations removed
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    "DELETE FROM model_resources WHERE model_id = ?",
                    (model_id,),
                )

                removed_count = cursor.rowcount
                conn.commit()

                self.logger.info(
                    "Removed %s resource associations from model %s",
                    removed_count,
                    model_id,
                )

                return removed_count

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error(
                "Failed to remove resources from model %s: %s", model_id, e
            )
            return 0

    @log_function_call(logger)
    def get_models_using_material(self, material_id: int) -> List[Dict[str, Any]]:
        """
        Get all models that are using a specific material.

        Args:
            material_id: ID of the material

        Returns:
            List of model associations
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT 
                        mr.*,
                        m.filename as model_filename,
                        m.format as model_format,
                        mm.title as model_title
                    FROM model_resources mr
                    JOIN models m ON mr.model_id = m.id
                    LEFT JOIN model_metadata mm ON m.id = mm.model_id
                    WHERE mr.resource_type = 'material' AND mr.resource_id = ?
                    ORDER BY m.filename ASC
                    """,
                    (material_id,),
                )
                rows = cursor.fetchall()

                return [dict(row) for row in rows]

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error(
                "Failed to get models using material %s: %s", material_id, e
            )
            return []

    @log_function_call(logger)
    def get_models_using_background(self, background_id: int) -> List[Dict[str, Any]]:
        """
        Get all models that are using a specific background.

        Args:
            background_id: ID of the background

        Returns:
            List of model associations
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT 
                        mr.*,
                        m.filename as model_filename,
                        m.format as model_format,
                        mm.title as model_title
                    FROM model_resources mr
                    JOIN models m ON mr.model_id = m.id
                    LEFT JOIN model_metadata mm ON m.id = mm.model_id
                    WHERE mr.resource_type = 'background' AND mr.resource_id = ?
                    ORDER BY m.filename ASC
                    """,
                    (background_id,),
                )
                rows = cursor.fetchall()

                return [dict(row) for row in rows]

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error(
                "Failed to get models using background %s: %s", background_id, e
            )
            return []
