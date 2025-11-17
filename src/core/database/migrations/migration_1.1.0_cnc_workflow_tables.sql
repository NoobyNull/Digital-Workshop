-- Migration: CNC Workflow Tables
-- Version: 1.1.0
-- Description: Adds project-model links, G-code lifecycle, cut list storage, cost estimation, and tool import tracking tables with supporting indexes.
-- Created: 2025-11-15T02:03:50.000Z

---METADATA---
{
    "version": "1.1.0",
    "name": "CNC Workflow Tables",
    "description": "Adds project-model links, G-code lifecycle, cut list storage, cost estimation, and tool import tracking tables with supporting indexes.",
    "dependencies": [],
    "created_at": "2025-11-15T02:03:50.000Z",
    "estimated_duration": 0.5,
    "checksum": ""
}
---END_METADATA---

---UP---
BEGIN;

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
);

CREATE INDEX IF NOT EXISTS idx_project_models_project ON project_models(project_id);
CREATE INDEX IF NOT EXISTS idx_project_models_model ON project_models(model_id);

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
);

CREATE INDEX IF NOT EXISTS idx_gcode_operations_project ON gcode_operations(project_id);
CREATE INDEX IF NOT EXISTS idx_gcode_operations_status ON gcode_operations(status);

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
);

CREATE INDEX IF NOT EXISTS idx_gcode_versions_operation ON gcode_versions(operation_id);
CREATE INDEX IF NOT EXISTS idx_gcode_versions_status ON gcode_versions(status);

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
    FOREIGN KEY (version_id) REFERENCES gcode_versions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_gcode_metrics_version ON gcode_metrics(version_id);

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
);

CREATE INDEX IF NOT EXISTS idx_gcode_tool_snapshots_version ON gcode_tool_snapshots(version_id);

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
);

CREATE INDEX IF NOT EXISTS idx_cutlist_scenarios_project ON cutlist_scenarios(project_id);
CREATE INDEX IF NOT EXISTS idx_cutlist_scenarios_status ON cutlist_scenarios(status);

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
);

CREATE INDEX IF NOT EXISTS idx_cutlist_materials_scenario ON cutlist_materials(scenario_id);

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
);

CREATE INDEX IF NOT EXISTS idx_cutlist_pieces_scenario ON cutlist_pieces(scenario_id);

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
);

CREATE INDEX IF NOT EXISTS idx_cutlist_sequences_scenario ON cutlist_sequences(scenario_id);

CREATE TABLE IF NOT EXISTS cost_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    data_json TEXT,
    created_by TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

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
);

CREATE INDEX IF NOT EXISTS idx_cost_snapshots_project ON cost_snapshots(project_id);

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
);

CREATE INDEX IF NOT EXISTS idx_cost_entries_snapshot ON cost_entries(snapshot_id);

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
);

CREATE INDEX IF NOT EXISTS idx_tool_provider_sources_name ON tool_provider_sources(provider_name);

CREATE TABLE IF NOT EXISTS tool_import_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_source_id INTEGER,
    imported_count INTEGER DEFAULT 0,
    duration_seconds REAL,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (provider_source_id) REFERENCES tool_provider_sources(id) ON DELETE SET NULL
);

COMMIT;
---END_UP---

---DOWN---
BEGIN;

DROP TABLE IF EXISTS tool_import_batches;
DROP TABLE IF EXISTS tool_provider_sources;

DROP INDEX IF EXISTS idx_cost_entries_snapshot;
DROP TABLE IF EXISTS cost_entries;

DROP INDEX IF EXISTS idx_cost_snapshots_project;
DROP TABLE IF EXISTS cost_snapshots;

DROP TABLE IF EXISTS cost_templates;

DROP INDEX IF EXISTS idx_cutlist_sequences_scenario;
DROP TABLE IF EXISTS cutlist_sequences;

DROP INDEX IF EXISTS idx_cutlist_pieces_scenario;
DROP TABLE IF EXISTS cutlist_pieces;

DROP INDEX IF EXISTS idx_cutlist_materials_scenario;
DROP TABLE IF EXISTS cutlist_materials;

DROP INDEX IF EXISTS idx_cutlist_scenarios_status;
DROP INDEX IF EXISTS idx_cutlist_scenarios_project;
DROP TABLE IF EXISTS cutlist_scenarios;

DROP INDEX IF EXISTS idx_gcode_tool_snapshots_version;
DROP TABLE IF EXISTS gcode_tool_snapshots;

DROP INDEX IF EXISTS idx_gcode_metrics_version;
DROP TABLE IF EXISTS gcode_metrics;

DROP INDEX IF EXISTS idx_gcode_versions_status;
DROP INDEX IF EXISTS idx_gcode_versions_operation;
DROP TABLE IF EXISTS gcode_versions;

DROP INDEX IF EXISTS idx_gcode_operations_status;
DROP INDEX IF EXISTS idx_gcode_operations_project;
DROP TABLE IF EXISTS gcode_operations;

DROP INDEX IF EXISTS idx_project_models_model;
DROP INDEX IF EXISTS idx_project_models_project;
DROP TABLE IF EXISTS project_models;

COMMIT;
---END_DOWN---