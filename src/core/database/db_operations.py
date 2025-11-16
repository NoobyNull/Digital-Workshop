"""
Database operations module for connection management and schema initialization.

Handles SQLite connection creation, configuration, and database schema setup.
"""

import sqlite3
from pathlib import Path

from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


class DatabaseOperations:
    """Handles database connection and schema operations."""

    def __init__(self, db_path: str) -> None:
        """
        Initialize database operations.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @log_function_call(logger)
    def get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection with proper settings.

        Returns:
            SQLite connection object
        """
        try:
            conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30.0,  # 30 second timeout
            )

            # Return rows as dictionary-like objects for convenient access
            conn.row_factory = sqlite3.Row

            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")

            # Set WAL mode for better performance
            conn.execute("PRAGMA journal_mode = WAL")

            # Optimize for performance
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA cache_size = 10000")
            conn.execute("PRAGMA temp_store = MEMORY")

            return conn

        except sqlite3.Error as e:
            logger.error("Failed to create database connection: %s", str(e))
            raise

    @log_function_call(logger)
    def initialize_schema(self) -> None:
        """
        Initialize the database with the required schema.

        Creates tables for models, model_metadata, and categories if they don't exist.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Create models table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS models (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT NOT NULL,
                        format TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        file_size INTEGER,
                        file_hash TEXT,
                        thumbnail_path TEXT,
                        date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_modified DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create model_metadata table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS model_metadata (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        model_id INTEGER REFERENCES models(id),
                        title TEXT,
                        description TEXT,
                        keywords TEXT,
                        category TEXT,
                        source TEXT,
                        rating INTEGER CHECK(rating >= 0 AND rating <= 5),
                        view_count INTEGER DEFAULT 0,
                        last_viewed DATETIME DEFAULT CURRENT_TIMESTAMP,
                        camera_position_x REAL,
                        camera_position_y REAL,
                        camera_position_z REAL,
                        camera_focal_x REAL,
                        camera_focal_y REAL,
                        camera_focal_z REAL,
                        camera_view_up_x REAL,
                        camera_view_up_y REAL,
                        camera_view_up_z REAL,
                        UNIQUE(model_id)
                    )
                """
                )

                # Create categories table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        description TEXT,
                        color TEXT,
                        icon TEXT,
                        sort_order INTEGER DEFAULT 0
                    )
                """
                )

                # Create projects table for project management
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS projects (
                        id TEXT PRIMARY KEY,
                        name TEXT UNIQUE NOT NULL,
                        base_path TEXT,
                        import_tag TEXT,
                        original_path TEXT,
                        structure_type TEXT,
                        import_date DATETIME,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create files table for file tracking
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS files (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        file_name TEXT NOT NULL,
                        file_size INTEGER,
                        file_hash TEXT,
                        status TEXT DEFAULT 'pending',
                        link_type TEXT,
                        original_path TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                    )
                """
                )

                # Create model_analysis table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS model_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        model_id INTEGER NOT NULL,
                        triangle_count INTEGER,
                        vertex_count INTEGER,
                        face_count INTEGER,
                        edge_count INTEGER,
                        unique_vertex_count INTEGER,
                        volume REAL,
                        surface_area REAL,
                        bounding_box_min_x REAL,
                        bounding_box_min_y REAL,
                        bounding_box_min_z REAL,
                        bounding_box_max_x REAL,
                        bounding_box_max_y REAL,
                        bounding_box_max_z REAL,
                        bounding_box_width REAL,
                        bounding_box_height REAL,
                        bounding_box_depth REAL,
                        non_manifold_edges INTEGER DEFAULT 0,
                        duplicate_vertices INTEGER DEFAULT 0,
                        degenerate_triangles INTEGER DEFAULT 0,
                        analysis_time_seconds REAL,
                        analysis_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        analysis_version TEXT DEFAULT '1.0',
                        FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
                    )
                """
                )

                # Create indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_models_filename ON models(filename)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_models_format ON models(format)")
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_models_file_hash ON models(file_hash)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_model_analysis_model_id ON model_analysis(model_id)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_models_thumbnail_path ON models(thumbnail_path)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_metadata_category ON model_metadata(category)"
                )

                # Create indexes for projects and files
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name)")
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_projects_import_tag ON projects(import_tag)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_files_project_id ON files(project_id)"
                )
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_status ON files(status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_file_hash ON files(file_hash)")

                # Create materials and backgrounds tables for default resources
                self._create_resources_tables(cursor)

                # Create extended workflow tables (G-code, cut lists, cost tracking, tool imports, etc.)
                self._create_extended_workflow_tables(cursor)

                # Run migrations
                self.migrate_schema(cursor)

                # Seed default categories
                default_categories = [
                    ("Characters", "Character models", "#FF6B6B", 0),
                    ("Buildings", "Architecture and structures", "#4ECDC4", 1),
                    ("Vehicles", "Cars, planes, ships", "#45B7D1", 2),
                    ("Nature", "Plants, animals, landscapes", "#96CEB4", 3),
                    ("Objects", "Miscellaneous objects", "#FFEAA7", 4),
                ]

                for name, desc, color, sort_order in default_categories:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO categories (name, description, color, sort_order)
                        VALUES (?, ?, ?, ?)
                    """,
                        (name, desc, color, sort_order),
                    )

                conn.commit()
                logger.info("Database schema initialized successfully")

        except sqlite3.Error as e:
            logger.error("Failed to initialize database schema: %s", str(e))
            raise

    @log_function_call(logger)
    def migrate_schema(self, cursor: sqlite3.Cursor) -> None:
        """
        Migrate database schema to newer versions if needed.

        Args:
            cursor: SQLite cursor object
        """
        try:
            # Migration 1: Add file_hash column if it doesn't exist
            cursor.execute("PRAGMA table_info(models)")
            model_columns = cursor.fetchall()
            has_file_hash = any(col[1] == "file_hash" for col in model_columns)

            if not has_file_hash:
                logger.info("Adding file_hash column to models table")
                cursor.execute("ALTER TABLE models ADD COLUMN file_hash TEXT")
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_models_file_hash ON models(file_hash)"
                )
                logger.info("file_hash column added successfully")

            # Migration 2: Add thumbnail_path column if it doesn't exist
            has_thumbnail_path = any(col[1] == "thumbnail_path" for col in model_columns)

            if not has_thumbnail_path:
                logger.info("Adding thumbnail_path column to models table")
                cursor.execute("ALTER TABLE models ADD COLUMN thumbnail_path TEXT")
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_models_thumbnail_path ON models(thumbnail_path)"
                )
                logger.info("thumbnail_path column added successfully")

            # Migration 3: Add missing columns to categories table
            cursor.execute("PRAGMA table_info(categories)")
            category_columns = cursor.fetchall()
            category_col_names = [col[1] for col in category_columns]

            if "description" not in category_col_names:
                logger.info("Adding description column to categories table")
                cursor.execute("ALTER TABLE categories ADD COLUMN description TEXT")
                logger.info("description column added successfully")

            if "sort_order" not in category_col_names:
                logger.info("Adding sort_order column to categories table")
                cursor.execute("ALTER TABLE categories ADD COLUMN sort_order INTEGER DEFAULT 0")
                logger.info("sort_order column added successfully")

            # Migration 4: Add linked_model_id for deduplication tracking
            has_linked_model_id = any(col[1] == "linked_model_id" for col in model_columns)

            if not has_linked_model_id:
                logger.info("Adding linked_model_id column to models table")
                cursor.execute(
                    "ALTER TABLE models ADD COLUMN linked_model_id INTEGER REFERENCES models(id)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_models_linked_model_id ON models(linked_model_id)"
                )
                logger.info("linked_model_id column added successfully")

            # Migration 5: Ensure projects table exists (for project management)
            cursor.execute("PRAGMA table_info(projects)")
            projects_columns = cursor.fetchall()

            if not projects_columns:
                logger.info("Creating projects table")
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS projects (
                        id TEXT PRIMARY KEY,
                        name TEXT UNIQUE NOT NULL,
                        base_path TEXT,
                        import_tag TEXT,
                        original_path TEXT,
                        structure_type TEXT,
                        import_date DATETIME,
                        active_machine_id INTEGER,
                        feed_override_pct REAL DEFAULT 100.0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name)")
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_projects_import_tag ON projects(import_tag)"
                )
                logger.info("projects table created successfully")

                # Refresh project columns after potential creation
                cursor.execute("PRAGMA table_info(projects)")
                projects_columns = cursor.fetchall()

            project_col_names = [col[1] for col in projects_columns]

            if "active_machine_id" not in project_col_names:
                logger.info("Adding active_machine_id column to projects table")
                cursor.execute("ALTER TABLE projects ADD COLUMN active_machine_id INTEGER")
                logger.info("active_machine_id column added successfully")

            if "feed_override_pct" not in project_col_names:
                logger.info("Adding feed_override_pct column to projects table")
                cursor.execute(
                    "ALTER TABLE projects ADD COLUMN feed_override_pct REAL DEFAULT 100.0"
                )
                logger.info("feed_override_pct column added successfully")

            # Migration 6: Ensure files table exists (for file tracking)
            cursor.execute("PRAGMA table_info(files)")
            files_columns = cursor.fetchall()

            if not files_columns:
                logger.info("Creating files table")
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS files (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        file_name TEXT NOT NULL,
                        file_size INTEGER,
                        file_hash TEXT,
                        status TEXT DEFAULT 'pending',
                        link_type TEXT,
                        original_path TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                    )
                """
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_files_project_id ON files(project_id)"
                )
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_status ON files(status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_file_hash ON files(file_hash)")
                logger.info("files table created successfully")

            # Migration 7: Ensure new timing columns exist on gcode_metrics
            cursor.execute("PRAGMA table_info(gcode_metrics)")
            metrics_columns = cursor.fetchall()
            metrics_col_names = [col[1] for col in metrics_columns]

            if metrics_columns:
                if "best_case_time_seconds" not in metrics_col_names:
                    logger.info("Adding best_case_time_seconds column to gcode_metrics table")
                    cursor.execute(
                        "ALTER TABLE gcode_metrics ADD COLUMN best_case_time_seconds REAL"
                    )
                if "time_correction_factor" not in metrics_col_names:
                    logger.info("Adding time_correction_factor column to gcode_metrics table")
                    cursor.execute(
                        "ALTER TABLE gcode_metrics ADD COLUMN time_correction_factor REAL"
                    )

        except sqlite3.Error as e:
            logger.error("Failed to migrate database schema: %s", str(e))
            raise

    def _create_resources_tables(self, cursor: sqlite3.Cursor) -> None:
        """
        Create tables for storing default materials and backgrounds as database resources.

        These tables store the default resources that cannot be deleted and can be associated with models.
        """
        # Materials table for default material resources
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                type TEXT NOT NULL DEFAULT 'wood',
                display_name TEXT,
                description TEXT,
                file_path TEXT NOT NULL,
                file_hash TEXT,
                texture_path TEXT,
                mtl_path TEXT,
                properties_json TEXT,
                is_default BOOLEAN DEFAULT 0,
                is_deletable BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_materials_name ON materials(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_materials_type ON materials(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_materials_default ON materials(is_default)")

        # Backgrounds table for default background resources
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS backgrounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                display_name TEXT,
                description TEXT,
                file_path TEXT NOT NULL,
                file_hash TEXT,
                file_size INTEGER,
                thumbnail_path TEXT,
                is_default BOOLEAN DEFAULT 0,
                is_deletable BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_backgrounds_name ON backgrounds(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_backgrounds_default ON backgrounds(is_default)")

        # Model resource associations table to link models with materials and backgrounds
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS model_resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER NOT NULL,
                resource_type TEXT NOT NULL CHECK(resource_type IN ('material', 'background')),
                resource_id INTEGER NOT NULL,
                is_primary BOOLEAN DEFAULT 0,
                metadata_json TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
                FOREIGN KEY (resource_id) REFERENCES materials(id) ON DELETE CASCADE,
                FOREIGN KEY (resource_id) REFERENCES backgrounds(id) ON DELETE CASCADE
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_model_resources_model ON model_resources(model_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_model_resources_type ON model_resources(resource_type)")

    def _create_extended_workflow_tables(self, cursor: sqlite3.Cursor) -> None:
        """
        Create tables that power the CNC workflow (project models, G-code, cut lists, costing, tool DB imports).
        """
        # Machine profiles (generic kinematics for timing)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS machines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                max_feed_mm_min REAL NOT NULL DEFAULT 600.0,
                accel_mm_s2 REAL NOT NULL DEFAULT 100.0,
                notes TEXT,
                is_default INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Project ↔ model association
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS project_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                model_id INTEGER,
                role TEXT,
                version TEXT,
                material_tag TEXT,
                orientation_hint TEXT,
                derived_from_model_id INTEGER,
                metadata_json TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE SET NULL,
                FOREIGN KEY (derived_from_model_id) REFERENCES models(id) ON DELETE SET NULL
            )
        """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_project_models_project ON project_models(project_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_project_models_model ON project_models(model_id)"
        )

        # G-code operations and versioning
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS gcode_operations (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                model_id INTEGER,
                name TEXT NOT NULL,
                status TEXT DEFAULT 'draft',
                strategy TEXT,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE SET NULL
            )
        """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_gcode_operations_project ON gcode_operations(project_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_gcode_operations_status ON gcode_operations(status)"
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS gcode_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_id TEXT NOT NULL,
                version_label TEXT,
                file_path TEXT NOT NULL,
                file_hash TEXT,
                revision INTEGER DEFAULT 1,
                status TEXT DEFAULT 'draft',
                feed_snapshot_json TEXT,
                tool_list_json TEXT,
                checksum TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (operation_id) REFERENCES gcode_operations(id) ON DELETE CASCADE
            )
        """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_gcode_versions_operation ON gcode_versions(operation_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_gcode_versions_status ON gcode_versions(status)"
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS gcode_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version_id INTEGER NOT NULL,
                total_time_seconds REAL,
                cutting_time_seconds REAL,
                rapid_time_seconds REAL,
                tool_changes INTEGER,
                distance_cut REAL,
                distance_rapid REAL,
                material_removed REAL,
                warnings TEXT,
                best_case_time_seconds REAL,
                time_correction_factor REAL,
                FOREIGN KEY (version_id) REFERENCES gcode_versions(id) ON DELETE CASCADE
            )
        """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_gcode_metrics_version ON gcode_metrics(version_id)"
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS gcode_tool_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version_id INTEGER NOT NULL,
                tool_number TEXT,
                tool_id INTEGER,
                provider_name TEXT,
                tool_db_source TEXT,
                feed_rate REAL,
                plunge_rate REAL,
                spindle_speed REAL,
                stepdown REAL,
                stepover REAL,
                notes TEXT,
                metadata_json TEXT,
                FOREIGN KEY (version_id) REFERENCES gcode_versions(id) ON DELETE CASCADE
            )
        """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_gcode_tool_snapshots_version ON gcode_tool_snapshots(version_id)"
        )

        # Cut list optimizer data
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cutlist_scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                stock_strategy TEXT,
                status TEXT DEFAULT 'draft',
                metadata_json TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_cutlist_scenarios_project ON cutlist_scenarios(project_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_cutlist_scenarios_status ON cutlist_scenarios(status)"
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cutlist_materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_id INTEGER NOT NULL,
                description TEXT,
                width REAL,
                height REAL,
                thickness REAL,
                quantity INTEGER DEFAULT 1,
                grain TEXT,
                material_tag TEXT,
                waste_area REAL,
                metadata_json TEXT,
                FOREIGN KEY (scenario_id) REFERENCES cutlist_scenarios(id) ON DELETE CASCADE
            )
        """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_cutlist_materials_scenario ON cutlist_materials(scenario_id)"
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cutlist_pieces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_id INTEGER NOT NULL,
                project_model_id INTEGER,
                name TEXT,
                width REAL,
                height REAL,
                thickness REAL,
                quantity INTEGER DEFAULT 1,
                grain TEXT,
                orientation TEXT,
                placement_json TEXT,
                FOREIGN KEY (scenario_id) REFERENCES cutlist_scenarios(id) ON DELETE CASCADE,
                FOREIGN KEY (project_model_id) REFERENCES project_models(id) ON DELETE SET NULL
            )
        """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_cutlist_pieces_scenario ON cutlist_pieces(scenario_id)"
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cutlist_sequences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_id INTEGER NOT NULL,
                sequence_order INTEGER NOT NULL,
                piece_id INTEGER,
                board_reference TEXT,
                instruction TEXT,
                metadata_json TEXT,
                FOREIGN KEY (scenario_id) REFERENCES cutlist_scenarios(id) ON DELETE CASCADE,
                FOREIGN KEY (piece_id) REFERENCES cutlist_pieces(id) ON DELETE SET NULL
            )
        """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_cutlist_sequences_scenario ON cutlist_sequences(scenario_id)"
        )

        # Cost estimation data
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cost_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                data_json TEXT,
                created_by TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cost_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                name TEXT,
                template_id INTEGER,
                total_material_cost REAL,
                total_machine_cost REAL,
                total_labor_cost REAL,
                total_shop_cost REAL,
                total_tool_cost REAL,
                total_expense_cost REAL,
                overhead_pct REAL,
                    profit_margin_pct REAL,
                tax_pct REAL,
                final_quote REAL,
                quantity INTEGER DEFAULT 1,
                data_json TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (template_id) REFERENCES cost_templates(id) ON DELETE SET NULL
            )
        """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_cost_snapshots_project ON cost_snapshots(project_id)"
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cost_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER NOT NULL,
                category TEXT,
                source_type TEXT,
                source_reference TEXT,
                description TEXT,
                quantity REAL,
                unit TEXT,
                rate REAL,
                cost REAL,
                metadata_json TEXT,
                FOREIGN KEY (snapshot_id) REFERENCES cost_snapshots(id) ON DELETE CASCADE
            )
        """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_cost_entries_snapshot ON cost_entries(snapshot_id)"
        )

        # Tool database import tracking
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tool_provider_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider_name TEXT NOT NULL,
                source_path TEXT,
                checksum TEXT,
                format_type TEXT,
                status TEXT,
                imported_at DATETIME,
                last_sync_at DATETIME,
                metadata_json TEXT
            )
        """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tool_provider_sources_name ON tool_provider_sources(provider_name)"
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tool_import_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider_source_id INTEGER,
                imported_count INTEGER DEFAULT 0,
                duration_seconds REAL,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (provider_source_id) REFERENCES tool_provider_sources(id) ON DELETE SET NULL
            )
        """
        )
