"""
Refactored database manager - facade pattern for modular database operations.

Delegates to specialized repository and maintenance modules for clean separation of concerns.
"""

import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..logging_config import get_logger, log_function_call
from .db_operations import DatabaseOperations
from .model_repository import ModelRepository
from .metadata_repository import MetadataRepository
from .db_maintenance import DatabaseMaintenance
from .project_repository import ProjectRepository
from .file_repository import FileRepository
from .project_model_repository import ProjectModelRepository
from .gcode_repository import GcodeRepository
from .cutlist_repository import CutListRepository
from .cost_repository import CostRepository
from .tool_import_repository import ToolImportRepository
from .material_repository import MaterialRepository
from .machine_repository import MachineRepository
from .background_repository import BackgroundRepository
from .model_resources_repository import ModelResourcesRepository

logger = get_logger(__name__)


class DatabaseManager:
    """
    Facade for database operations.

    Delegates to specialized modules for models, metadata, maintenance, and operations.
    """

    def __init__(self, db_path: str = "data/3dmm.db") -> None:
        """
        Initialize the database manager.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self._lock = threading.Lock()

        logger.info("Initializing database manager with path: %s", self.db_path)

        # Initialize specialized modules
        self._db_ops = DatabaseOperations(str(self.db_path))
        get_conn = self._db_ops.get_connection
        self._model_repo = ModelRepository(get_conn)
        self._metadata_repo = MetadataRepository(get_conn)
        self._maintenance = DatabaseMaintenance(get_conn)
        self._project_repo = ProjectRepository(get_conn)
        self._file_repo = FileRepository(get_conn)
        self._project_model_repo = ProjectModelRepository(get_conn)
        self._gcode_repo = GcodeRepository(get_conn)
        self._cutlist_repo = CutListRepository(get_conn)
        self._cost_repo = CostRepository(get_conn)
        self._tool_import_repo = ToolImportRepository(get_conn)
        self._machine_repo = MachineRepository(get_conn)
        self._material_repo = MaterialRepository(get_conn)
        self._background_repo = BackgroundRepository(get_conn)
        self._model_resources_repo = ModelResourcesRepository(get_conn)

        # Initialize database schema and default resources
        self._db_ops.initialize_schema()
        self._machine_repo.initialize_default_machine()
        self._material_repo.initialize_default_materials()
        self._background_repo.initialize_default_backgrounds()

    # ===== Model Operations (delegated to ModelRepository) =====

    def add_model(
        self,
        filename: str,
        model_format: str,
        file_path: str,
        file_size: Optional[int] = None,
        file_hash: Optional[str] = None,
    ) -> int:
        """Add a new model to the database."""
        return self._model_repo.add_model(filename, model_format, file_path, file_size, file_hash)

    def find_model_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Find a model by its file hash."""
        return self._model_repo.find_model_by_hash(file_hash)

    def update_file_hash(self, model_id: int, file_hash: str) -> bool:
        """Update file hash for a model."""
        return self._model_repo.update_file_hash(model_id, file_hash)

    def link_duplicate_model(self, duplicate_id: int, keep_id: int) -> bool:
        """Link a duplicate model to the model being kept."""
        return self._model_repo.link_duplicate_model(duplicate_id, keep_id)

    def get_model(self, model_id: int) -> Optional[Dict[str, Any]]:
        """Get model information by ID."""
        return self._model_repo.get_model(model_id)

    def get_model_by_id(self, model_id: int) -> Optional[Dict[str, Any]]:
        """Get model information by ID (alias for get_model)."""
        return self._model_repo.get_model(model_id)

    def get_model_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get model information by file path."""
        return self._model_repo.get_model_by_path(file_path)

    def update_model_hash(self, model_id: int, file_hash: str) -> bool:
        """Update file hash for a model."""
        return self._model_repo.update_model_hash(model_id, file_hash)

    def get_all_models(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all models from the database."""
        return self._model_repo.get_all_models(limit, offset)

    def update_model_thumbnail(self, model_id: int, thumbnail_path: str) -> bool:
        """Update thumbnail path for a model."""
        return self._model_repo.update_model_thumbnail(model_id, thumbnail_path)

    def update_model_camera_view(
        self,
        model_id: int,
        camera_position: tuple,
        camera_focal_point: tuple,
        camera_view_up: tuple,
        camera_view_name: str,
    ) -> bool:
        """Update optimal camera view parameters for a model."""
        return self._model_repo.update_model_camera_view(
            model_id, camera_position, camera_focal_point, camera_view_up, camera_view_name
        )

    def delete_model(self, model_id: int) -> bool:
        """Delete a model from the database."""
        return self._model_repo.delete_model(model_id)

    def add_model_analysis(
        self,
        model_id: int,
        triangle_count: Optional[int] = None,
        vertex_count: Optional[int] = None,
        min_bounds: Optional[tuple] = None,
        max_bounds: Optional[tuple] = None,
        **kwargs,
    ) -> int:
        """Add analysis data for a model."""
        return self._model_repo.add_model_analysis(
            model_id, triangle_count, vertex_count, min_bounds, max_bounds, **kwargs
        )

    # ===== Metadata Operations (delegated to MetadataRepository) =====

    def add_metadata(self, model_id: int, **kwargs) -> int:
        """Add metadata for a model."""
        return self._metadata_repo.add_metadata(model_id, **kwargs)

    # Compatibility alias for tests
    def add_model_metadata(self, model_id: int, **kwargs) -> int:
        """Add metadata for a model (compatibility alias)."""
        return self.add_metadata(model_id, **kwargs)

    def get_model_metadata(self, model_id: int) -> Optional[Dict[str, Any]]:
        """Get model metadata."""
        return self._metadata_repo.get_model_metadata(model_id)

    def update_model_metadata(self, model_id: int, **kwargs) -> bool:
        """Update model metadata."""
        return self._metadata_repo.update_model_metadata(model_id, **kwargs)

    def save_camera_orientation(self, model_id: int, camera_data: Dict[str, float]) -> bool:
        """Save camera orientation for a model."""
        return self._metadata_repo.save_camera_orientation(model_id, camera_data)

    def get_camera_orientation(self, model_id: int) -> Optional[Dict[str, float]]:
        """Get saved camera orientation for a model."""
        return self._metadata_repo.get_camera_orientation(model_id)

    def increment_view_count(self, model_id: int) -> bool:
        """Increment the view count for a model."""
        return self._metadata_repo.increment_view_count(model_id)

    def get_categories(self) -> List[Dict[str, Any]]:
        """Get all categories from the database."""
        return self._metadata_repo.get_categories()

    def add_category(self, name: str, color: str = "#CCCCCC", sort_order: int = 0) -> int:
        """Add a new category."""
        return self._metadata_repo.add_category(name, color, sort_order)

    def delete_category(self, category_id: int) -> bool:
        """Delete a category."""
        return self._metadata_repo.delete_category(category_id)

    # ===== Maintenance Operations (delegated to DatabaseMaintenance) =====

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        return self._maintenance.get_database_stats()

    def vacuum_database(self) -> None:
        """Vacuum the database to reclaim unused space."""
        return self._maintenance.vacuum_database()

    def analyze_database(self) -> None:
        """Analyze the database to update query planner statistics."""
        return self._maintenance.analyze_database()

    # ===== Additional Methods for Compatibility =====

    def update_model(self, model_id: int, **kwargs) -> bool:
        """
        Update model information.

        Args:
            model_id: Model ID
            **kwargs: Fields to update (filename, format, file_path, file_size)

        Returns:
            True if successful
        """
        try:
            with self._db_ops.get_connection() as conn:
                cursor = conn.cursor()

                # Filter valid fields
                valid_fields = {"filename", "format", "file_path", "file_size"}
                updates = {k: v for k, v in kwargs.items() if k in valid_fields}

                if not updates:
                    return False

                # Build update query
                set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
                values = list(updates.values())
                values.append(model_id)

                cursor.execute(
                    f"""
                    UPDATE models
                    SET {set_clause}, last_modified = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    values,
                )

                success = cursor.rowcount > 0
                conn.commit()

                if success:
                    logger.info("Updated model %s", model_id)

                return success

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as err:
            logger.exception("Failed to update model %s", model_id, exc_info=err)
            return False

    def search_models(
        self,
        query: str = "",
        category: Optional[str] = None,
        model_format: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for models by query and filters.

        Args:
            query: Search query string
            category: Filter by category
            format: Filter by format

        Returns:
            List of matching models
        """
        try:
            with self._db_ops.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                sql = """
                    SELECT m.*, mm.title, mm.description, mm.keywords, mm.category,
                           mm.source, mm.rating, mm.view_count, mm.last_viewed
                    FROM models m
                    LEFT JOIN model_metadata mm ON m.id = mm.model_id
                    WHERE 1=1
                """
                params = []

                if query:
                    sql += """ AND (
                        m.filename LIKE ? OR
                        mm.title LIKE ? OR
                        mm.description LIKE ? OR
                        mm.keywords LIKE ?
                    )"""
                    query_param = f"%{query}%"
                    params.extend([query_param] * 4)

                if category:
                    sql += " AND mm.category = ?"
                    params.append(category)

                if model_format:
                    sql += " AND m.format = ?"
                    params.append(model_format)

                cursor.execute(sql, params)
                rows = cursor.fetchall()

                return [dict(row) for row in rows]

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to search models: %s", e)
            return []

    def update_category(self, category_id: int, **kwargs) -> bool:
        """
        Update a category.

        Args:
            category_id: Category ID
            **kwargs: Fields to update (name, color)

        Returns:
            True if successful
        """
        try:
            with self._db_ops.get_connection() as conn:
                cursor = conn.cursor()

                # Filter valid fields
                valid_fields = {"name", "color"}
                updates = {k: v for k, v in kwargs.items() if k in valid_fields}

                if not updates:
                    return False

                # Build update query
                set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
                values = list(updates.values())
                values.append(category_id)

                cursor.execute(
                    f"""
                    UPDATE categories
                    SET {set_clause}
                    WHERE id = ?
                """,
                    values,
                )

                success = cursor.rowcount > 0
                conn.commit()

                if success:
                    logger.info("Updated category %s", category_id)

                return success

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as err:
            logger.exception("Failed to update category %s", category_id, exc_info=err)
            return False

    # ===== Project Operations (delegated to ProjectRepository) =====

    def create_project(
        self,
        name: str,
        base_path: Optional[str] = None,
        import_tag: Optional[str] = None,
        original_path: Optional[str] = None,
        structure_type: Optional[str] = None,
    ) -> str:
        """Create a new project."""
        return self._project_repo.create_project(
            name, base_path, import_tag, original_path, structure_type
        )

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID."""
        return self._project_repo.get_project(project_id)

    def get_project_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get project by name (case-insensitive)."""
        return self._project_repo.get_project_by_name(name)

    def list_projects(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """List all projects."""
        return self._project_repo.list_projects(limit, offset)

    def list_imported_projects(self) -> List[Dict[str, Any]]:
        """List all imported projects."""
        return self._project_repo.list_imported_projects()

    def update_project(self, project_id: str, **kwargs) -> bool:
        """Update project fields."""
        return self._project_repo.update_project(project_id, **kwargs)

    def delete_project(self, project_id: str) -> bool:
        """Delete project and associated files."""
        return self._project_repo.delete_project(project_id)

    def get_project_count(self) -> int:
        """Get total number of projects."""
        return self._project_repo.get_project_count()

    def get_project_active_machine(self, project_id: str) -> Optional[int]:
        """Get active machine ID for a project."""
        return self._project_repo.get_active_machine(project_id)

    def set_project_active_machine(self, project_id: str, machine_id: Optional[int]) -> bool:
        """Set active machine for a project."""
        return self._project_repo.set_active_machine(project_id, machine_id)

    def get_project_feed_override(self, project_id: str) -> float:
        """Get the feed override percentage for a project."""
        return self._project_repo.get_feed_override(project_id)

    def set_project_feed_override(self, project_id: str, override_pct: float) -> bool:
        """Set the feed override percentage for a project."""
        return self._project_repo.set_feed_override(project_id, override_pct)

    # ===== File Operations (delegated to FileRepository) =====

    def add_file(
        self,
        project_id: str,
        file_path: str,
        file_name: str,
        file_size: Optional[int] = None,
        file_hash: Optional[str] = None,
        status: str = "pending",
        link_type: Optional[str] = None,
        original_path: Optional[str] = None,
    ) -> int:
        """Add a file to a project."""
        return self._file_repo.add_file(
            project_id,
            file_path,
            file_name,
            file_size,
            file_hash,
            status,
            link_type,
            original_path,
        )

    def get_file(self, file_id: int) -> Optional[Dict[str, Any]]:
        """Get file by ID."""
        return self._file_repo.get_file(file_id)

    def get_files_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all files in a project."""
        return self._file_repo.get_files_by_project(project_id)

    def get_files_by_status(self, project_id: str, status: str) -> List[Dict[str, Any]]:
        """Get files by status in a project."""
        return self._file_repo.get_files_by_status(project_id, status)

    def update_file_status(self, file_id: int, status: str) -> bool:
        """Update file status."""
        return self._file_repo.update_file_status(file_id, status)

    def update_file(self, file_id: int, **kwargs) -> bool:
        """Update file fields."""
        return self._file_repo.update_file(file_id, **kwargs)

    def delete_file(self, file_id: int) -> bool:
        """Delete a file record."""
        return self._file_repo.delete_file(file_id)

    def get_file_count_by_project(self, project_id: str) -> int:
        """Get total number of files in a project."""
        return self._file_repo.get_file_count_by_project(project_id)

    def find_duplicate_by_hash(self, project_id: str, file_hash: str) -> Optional[Dict[str, Any]]:
        """Find duplicate file by hash in a project."""
        return self._file_repo.find_duplicate_by_hash(project_id, file_hash)

    # ===== Project ↔ Model Associations (delegated to ProjectModelRepository) =====

    def link_model_to_project(
        self,
        project_id: str,
        model_id: Optional[int] = None,
        **kwargs: Any,
    ) -> int:
        """
        Create an association between a project and a model/derived asset.

        kwargs may include: role, version, material_tag, orientation_hint, derived_from_model_id, metadata.
        """
        return self._project_model_repo.create_project_model(project_id, model_id, **kwargs)

    def get_project_model_link(self, record_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a single project-model association."""
        return self._project_model_repo.get_project_model(record_id)

    def list_project_models(self, project_id: str) -> List[Dict[str, Any]]:
        """List all models (and derived assets) linked to a project."""
        return self._project_model_repo.list_by_project(project_id)

    def list_project_models_by_role(self, project_id: str, role: str) -> List[Dict[str, Any]]:
        """List project associations filtered by workflow role (e.g., stock, reference, output)."""
        return self._project_model_repo.list_by_role(project_id, role)

    def list_project_links_for_model(self, model_id: int) -> List[Dict[str, Any]]:
        """List every project association referencing a given model."""
        return self._project_model_repo.list_by_model(model_id)

    def update_project_model_link(self, record_id: int, **kwargs: Any) -> bool:
        """Update metadata for a project-model association."""
        return self._project_model_repo.update_project_model(record_id, **kwargs)

    def delete_project_model_link(self, record_id: int) -> bool:
        """Remove the association between a project and a model/derived asset."""
        return self._project_model_repo.delete_project_model(record_id)

    # ===== G-code Operations / Metrics / Tool Snapshots =====

    def create_gcode_operation(self, **kwargs: Any) -> str:
        """Create a G-code operation row."""
        return self._gcode_repo.create_operation(**kwargs)

    def get_gcode_operation(self, operation_id: str) -> Optional[Dict[str, Any]]:
        return self._gcode_repo.get_operation(operation_id)

    def list_gcode_operations(
        self, project_id: Optional[str] = None, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        return self._gcode_repo.list_operations(project_id=project_id, status=status)

    def update_gcode_operation(self, operation_id: str, **kwargs: Any) -> bool:
        return self._gcode_repo.update_operation(operation_id, **kwargs)

    def delete_gcode_operation(self, operation_id: str) -> bool:
        return self._gcode_repo.delete_operation(operation_id)

    def create_gcode_version(self, **kwargs: Any) -> int:
        return self._gcode_repo.create_version(**kwargs)

    def get_gcode_version(self, version_id: int) -> Optional[Dict[str, Any]]:
        return self._gcode_repo.get_version(version_id)

    def list_gcode_versions(self, operation_id: str) -> List[Dict[str, Any]]:
        return self._gcode_repo.list_versions(operation_id)

    def update_gcode_version(self, version_id: int, **kwargs: Any) -> bool:
        return self._gcode_repo.update_version(version_id, **kwargs)

    def delete_gcode_version(self, version_id: int) -> bool:
        return self._gcode_repo.delete_version(version_id)

    def upsert_gcode_metrics(self, version_id: int, **metrics: Any) -> bool:
        return self._gcode_repo.upsert_metrics(version_id, **metrics)

    def get_gcode_metrics(self, version_id: int) -> Optional[Dict[str, Any]]:
        return self._gcode_repo.get_metrics(version_id)

    def add_gcode_tool_snapshot(self, **kwargs: Any) -> int:
        return self._gcode_repo.add_tool_snapshot(**kwargs)

    def list_gcode_tool_snapshots(self, version_id: int) -> List[Dict[str, Any]]:
        return self._gcode_repo.list_tool_snapshots(version_id)

    def delete_gcode_tool_snapshots(self, version_id: int) -> int:
        return self._gcode_repo.delete_tool_snapshots(version_id)

    # ===== Cut List Optimizer (Scenarios / Materials / Pieces / Sequences) =====

    def create_cutlist_scenario(self, **kwargs: Any) -> int:
        return self._cutlist_repo.create_scenario(**kwargs)

    def get_cutlist_scenario(self, scenario_id: int) -> Optional[Dict[str, Any]]:
        return self._cutlist_repo.get_scenario(scenario_id)

    def list_cutlist_scenarios(
        self, project_id: str, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        return self._cutlist_repo.list_scenarios(project_id, status)

    def update_cutlist_scenario(self, scenario_id: int, **kwargs: Any) -> bool:
        return self._cutlist_repo.update_scenario(scenario_id, **kwargs)

    def delete_cutlist_scenario(self, scenario_id: int) -> bool:
        return self._cutlist_repo.delete_scenario(scenario_id)

    def add_cutlist_material(self, **kwargs: Any) -> int:
        return self._cutlist_repo.add_material(**kwargs)

    def list_cutlist_materials(self, scenario_id: int) -> List[Dict[str, Any]]:
        return self._cutlist_repo.list_materials(scenario_id)

    def delete_cutlist_material(self, material_id: int) -> bool:
        return self._cutlist_repo.delete_material(material_id)

    def add_cutlist_piece(self, **kwargs: Any) -> int:
        return self._cutlist_repo.add_piece(**kwargs)

    def list_cutlist_pieces(self, scenario_id: int) -> List[Dict[str, Any]]:
        return self._cutlist_repo.list_pieces(scenario_id)

    def delete_cutlist_piece(self, piece_id: int) -> bool:
        return self._cutlist_repo.delete_piece(piece_id)

    def add_cutlist_sequence_step(self, **kwargs: Any) -> int:
        return self._cutlist_repo.add_sequence_step(**kwargs)

    def list_cutlist_sequence(self, scenario_id: int) -> List[Dict[str, Any]]:
        return self._cutlist_repo.list_sequence(scenario_id)

    # ===== Machine Profiles / Kinematics =====

    def add_machine(self, **kwargs: Any) -> int:
        """Create a new machine profile."""
        return self._machine_repo.add_machine(**kwargs)

    def get_machine(self, machine_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a single machine by ID."""
        return self._machine_repo.get_machine(machine_id)

    def get_machine_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Fetch a machine by its unique name."""
        return self._machine_repo.get_machine_by_name(name)

    def list_machines(self) -> List[Dict[str, Any]]:
        """Return all machine profiles, default first."""
        return self._machine_repo.get_all_machines()

    def get_default_machine(self) -> Optional[Dict[str, Any]]:
        """Return the default machine profile, if configured."""
        return self._machine_repo.get_default_machine()

    def update_machine(self, machine_id: int, **kwargs: Any) -> bool:
        """Update a machine profile."""
        return self._machine_repo.update_machine(machine_id, **kwargs)

    def delete_machine(self, machine_id: int) -> bool:
        """Delete a machine profile if it is not marked as default."""
        return self._machine_repo.delete_machine(machine_id)

    def delete_cutlist_sequence(self, scenario_id: int) -> int:
        return self._cutlist_repo.delete_sequence(scenario_id)

    # ===== Cost Estimation =====

    def create_cost_template(self, **kwargs: Any) -> int:
        return self._cost_repo.create_template(**kwargs)

    def list_cost_templates(self) -> List[Dict[str, Any]]:
        return self._cost_repo.list_templates()

    def get_cost_template(self, template_id: int) -> Optional[Dict[str, Any]]:
        return self._cost_repo.get_template(template_id)

    def update_cost_template(self, template_id: int, **kwargs: Any) -> bool:
        return self._cost_repo.update_template(template_id, **kwargs)

    def delete_cost_template(self, template_id: int) -> bool:
        return self._cost_repo.delete_template(template_id)

    def create_cost_snapshot(self, **kwargs: Any) -> int:
        return self._cost_repo.create_snapshot(**kwargs)

    def list_cost_snapshots(self, project_id: str) -> List[Dict[str, Any]]:
        return self._cost_repo.list_snapshots(project_id)

    def get_cost_snapshot(self, snapshot_id: int) -> Optional[Dict[str, Any]]:
        return self._cost_repo.get_snapshot(snapshot_id)

    def update_cost_snapshot(self, snapshot_id: int, **kwargs: Any) -> bool:
        return self._cost_repo.update_snapshot(snapshot_id, **kwargs)

    def delete_cost_snapshot(self, snapshot_id: int) -> bool:
        return self._cost_repo.delete_snapshot(snapshot_id)

    def add_cost_entry(self, **kwargs: Any) -> int:
        return self._cost_repo.add_entry(**kwargs)

    def list_cost_entries(self, snapshot_id: int) -> List[Dict[str, Any]]:
        return self._cost_repo.list_entries(snapshot_id)

    def delete_cost_entries(self, snapshot_id: int) -> int:
        return self._cost_repo.delete_entries(snapshot_id)

    # ===== Tool Import Tracking =====

    def create_tool_provider_source(self, **kwargs: Any) -> int:
        return self._tool_import_repo.create_provider_source(**kwargs)

    def update_tool_provider_source(self, source_id: int, **kwargs: Any) -> bool:
        return self._tool_import_repo.update_provider_source(source_id, **kwargs)

    def list_tool_provider_sources(self) -> List[Dict[str, Any]]:
        return self._tool_import_repo.list_provider_sources()

    def get_tool_provider_source(self, source_id: int) -> Optional[Dict[str, Any]]:
        return self._tool_import_repo.get_provider_source(source_id)

    def delete_tool_provider_source(self, source_id: int) -> bool:
        return self._tool_import_repo.delete_provider_source(source_id)

    def create_tool_import_batch(self, **kwargs: Any) -> int:
        return self._tool_import_repo.create_import_batch(**kwargs)

    def list_tool_import_batches(
        self, provider_source_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        return self._tool_import_repo.list_import_batches(provider_source_id)

    def get_tool_import_batch(self, batch_id: int) -> Optional[Dict[str, Any]]:
        return self._tool_import_repo.get_import_batch(batch_id)

    def delete_tool_import_batch(self, batch_id: int) -> bool:
        return self._tool_import_repo.delete_import_batch(batch_id)

    # ===== Resource Operations (Materials, Backgrounds, and Model Resources) =====

    # --- Materials ---

    def add_material(self, **kwargs: Any) -> int:
        return self._material_repo.add_material(**kwargs)

    def get_material(self, material_id: int) -> Optional[Dict[str, Any]]:
        return self._material_repo.get_material(material_id)

    def get_material_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        return self._material_repo.get_material_by_name(name)

    def get_all_materials(self, include_deletable: bool = True) -> List[Dict[str, Any]]:
        return self._material_repo.get_all_materials(include_deletable=include_deletable)

    def get_default_materials(self) -> List[Dict[str, Any]]:
        return self._material_repo.get_default_materials()

    def delete_material(self, material_id: int) -> bool:
        return self._material_repo.delete_material(material_id)

    # --- Backgrounds ---

    def add_background(self, **kwargs: Any) -> int:
        return self._background_repo.add_background(**kwargs)

    def get_background(self, background_id: int) -> Optional[Dict[str, Any]]:
        return self._background_repo.get_background(background_id)

    def get_background_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        return self._background_repo.get_background_by_name(name)

    def get_all_backgrounds(self, include_deletable: bool = True) -> List[Dict[str, Any]]:
        return self._background_repo.get_all_backgrounds(include_deletable=include_deletable)

    def get_default_backgrounds(self) -> List[Dict[str, Any]]:
        return self._background_repo.get_default_backgrounds()

    def delete_background(self, background_id: int) -> bool:
        return self._background_repo.delete_background(background_id)

    # --- Model resources associations ---

    def associate_resource_with_model(self, **kwargs: Any) -> int:
        return self._model_resources_repo.associate_resource_with_model(**kwargs)

    def get_model_materials(self, model_id: int) -> List[Dict[str, Any]]:
        return self._model_resources_repo.get_model_materials(model_id)

    def get_model_backgrounds(self, model_id: int) -> List[Dict[str, Any]]:
        return self._model_resources_repo.get_model_backgrounds(model_id)

    def get_primary_material(self, model_id: int) -> Optional[Dict[str, Any]]:
        return self._model_resources_repo.get_primary_material(model_id)

    def get_primary_background(self, model_id: int) -> Optional[Dict[str, Any]]:
        return self._model_resources_repo.get_primary_background(model_id)

    def remove_resource_association(
        self,
        model_id: int,
        resource_type: str,
        resource_id: int,
    ) -> bool:
        return self._model_resources_repo.remove_resource_association(
            model_id=model_id,
            resource_type=resource_type,
            resource_id=resource_id,
        )

    def remove_all_model_resources(self, model_id: int) -> int:
        return self._model_resources_repo.remove_all_model_resources(model_id)

    def get_models_using_material(self, material_id: int) -> List[Dict[str, Any]]:
        return self._model_resources_repo.get_models_using_material(material_id)

    def get_models_using_background(self, background_id: int) -> List[Dict[str, Any]]:
        return self._model_resources_repo.get_models_using_background(background_id)

    # ===== Connection Management =====

    def get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection.

        Returns:
            SQLite connection object
        """
        return self._db_ops.get_connection()

    @log_function_call(logger)
    def close(self) -> None:
        """Close the database connection."""
        logger.info("Database manager closed")
