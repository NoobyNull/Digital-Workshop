"""
Database schema definitions for the 3D Model Import System.

Provides SQL schema for:
- import_sessions table: Tracks import operations
- import_files table: Tracks individual file imports
- model_analysis table: Stores detailed geometry analysis
- Extensions to models table for import tracking
"""

# Import sessions table
CREATE_IMPORT_SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS import_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME,
    status TEXT CHECK(status IN ('pending', 'running', 'completed', 'cancelled', 'error')) NOT NULL DEFAULT 'pending',
    total_files INTEGER DEFAULT 0,
    processed_files INTEGER DEFAULT 0,
    failed_files INTEGER DEFAULT 0,
    skipped_files INTEGER DEFAULT 0,
    duplicate_files INTEGER DEFAULT 0,
    file_management_mode TEXT CHECK(file_management_mode IN ('keep_organized', 'leave_in_place')) NOT NULL,
    source_directory TEXT,
    root_directory TEXT,
    options_json TEXT,
    duration_seconds REAL,
    total_size_bytes INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

# Import files table
CREATE_IMPORT_FILES_TABLE = """
CREATE TABLE IF NOT EXISTS import_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    original_path TEXT NOT NULL,
    managed_path TEXT,
    file_hash TEXT,
    file_size INTEGER,
    file_format TEXT,
    import_status TEXT CHECK(import_status IN (
        'pending', 'copying', 'hashing', 'thumbnail', 
        'analysis', 'completed', 'failed', 'skipped'
    )) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    progress_percent INTEGER DEFAULT 0,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME,
    processing_time_seconds REAL,
    FOREIGN KEY (session_id) REFERENCES import_sessions(id) ON DELETE CASCADE
);
"""

# Model analysis table
CREATE_MODEL_ANALYSIS_TABLE = """
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
);
"""

# Indexes for performance
CREATE_IMPORT_SESSIONS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_import_sessions_session_id ON import_sessions(session_id);",
    "CREATE INDEX IF NOT EXISTS idx_import_sessions_status ON import_sessions(status);",
    "CREATE INDEX IF NOT EXISTS idx_import_sessions_start_time ON import_sessions(start_time);",
]

CREATE_IMPORT_FILES_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_import_files_session_id ON import_files(session_id);",
    "CREATE INDEX IF NOT EXISTS idx_import_files_file_hash ON import_files(file_hash);",
    "CREATE INDEX IF NOT EXISTS idx_import_files_import_status ON import_files(import_status);",
    "CREATE INDEX IF NOT EXISTS idx_import_files_original_path ON import_files(original_path);",
]

CREATE_MODEL_ANALYSIS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_model_analysis_model_id ON model_analysis(model_id);",
    "CREATE INDEX IF NOT EXISTS idx_model_analysis_date ON model_analysis(analysis_date);",
]

# Model table extensions (ALTER TABLE statements)
MODELS_TABLE_EXTENSIONS = [
    """
    ALTER TABLE models
    ADD COLUMN file_management_mode TEXT
    CHECK(file_management_mode IN ('keep_organized', 'leave_in_place'));
    """,
    """
    ALTER TABLE models
    ADD COLUMN import_session_id INTEGER
    REFERENCES import_sessions(id) ON DELETE SET NULL;
    """,
    """
    ALTER TABLE models
    ADD COLUMN analysis_completed BOOLEAN DEFAULT 0;
    """,
    """
    ALTER TABLE models
    ADD COLUMN thumbnail_generated BOOLEAN DEFAULT 0;
    """,
    """
    ALTER TABLE models
    ADD COLUMN original_path TEXT;
    """,
    """
    ALTER TABLE models
    ADD COLUMN managed_path TEXT;
    """,
    """
    ALTER TABLE models
    ADD COLUMN thumbnail_source TEXT
    CHECK(thumbnail_source IN ('generated', 'paired', 'manual', NULL))
    DEFAULT NULL;
    """,
    """
    ALTER TABLE models
    ADD COLUMN paired_image_path TEXT;
    """,
]

# Views for convenience
CREATE_IMPORT_SUMMARY_VIEW = """
CREATE VIEW IF NOT EXISTS import_summary AS
SELECT 
    s.id,
    s.session_id,
    s.start_time,
    s.end_time,
    s.status,
    s.total_files,
    s.processed_files,
    s.failed_files,
    s.skipped_files,
    s.duplicate_files,
    s.file_management_mode,
    s.duration_seconds,
    s.total_size_bytes,
    COUNT(DISTINCT f.file_hash) as unique_files,
    SUM(CASE WHEN f.import_status = 'completed' THEN 1 ELSE 0 END) as completed_files
FROM import_sessions s
LEFT JOIN import_files f ON s.id = f.session_id
GROUP BY s.id;
"""


def get_all_schema_statements() -> None:
    """
    Get all schema creation statements in order.

    Returns:
        List of SQL statements to create the complete schema
    """
    statements = []

    # Tables
    statements.append(CREATE_IMPORT_SESSIONS_TABLE)
    statements.append(CREATE_IMPORT_FILES_TABLE)
    statements.append(CREATE_MODEL_ANALYSIS_TABLE)

    # Indexes
    statements.extend(CREATE_IMPORT_SESSIONS_INDEXES)
    statements.extend(CREATE_IMPORT_FILES_INDEXES)
    statements.extend(CREATE_MODEL_ANALYSIS_INDEXES)

    # Views
    statements.append(CREATE_IMPORT_SUMMARY_VIEW)

    return statements


def get_models_table_extensions() -> None:
    """
    Get ALTER TABLE statements for extending models table.

    Returns:
        List of ALTER TABLE SQL statements

    Note:
        These should be executed with error handling as columns may already exist
    """
    return MODELS_TABLE_EXTENSIONS


__all__ = [
    "CREATE_IMPORT_SESSIONS_TABLE",
    "CREATE_IMPORT_FILES_TABLE",
    "CREATE_MODEL_ANALYSIS_TABLE",
    "get_all_schema_statements",
    "get_models_table_extensions",
]
