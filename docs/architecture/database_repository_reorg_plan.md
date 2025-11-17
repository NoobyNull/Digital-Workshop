# Database Repository Reorganization Plan

## Context
- The current `src/core/database` directory contains 30+ modules with mixed responsibilities (repositories, infrastructure, observability, tooling).
- CNC workflow expansion added additional repositories into the same folder, making navigation and ownership unclear.
- Most modules only depend on `logging_config` and SQLite helpers, so reorganizing into subpackages will not introduce circular import risk.

## Goals
1. Separate infrastructure/operations code from domain-specific repositories.
2. Group repositories by responsibility (core metadata, resources, CNC workflow, tool databases).
3. Provide stable public imports through curated `__init__.py` exports to minimize downstream changes.
4. Lay groundwork for future connectors (e.g., remote DB engines) by isolating connection factories and transaction helpers.

## Target Package Layout

```text
src/core/database/
├── __init__.py
├── infrastructure/
│   ├── __init__.py
│   ├── connections/
│   │   ├── __init__.py
│   │   ├── db_operations.py
│   │   ├── transaction_manager.py
│   │   └── database_manager.py
│   ├── maintenance/
│   │   ├── __init__.py
│   │   ├── db_maintenance.py
│   │   └── migration_manager.py
│   ├── observability/
│   │   ├── __init__.py
│   │   ├── error_handler.py
│   │   └── health_monitor.py
│   └── caching/
│       ├── __init__.py
│       └── cache_manager.py
├── repositories/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── model_repository.py
│   │   ├── metadata_repository.py
│   │   ├── file_repository.py
│   │   ├── project_repository.py
│   │   ├── search_repository.py
│   │   └── query_optimizer.py
│   ├── resources/
│   │   ├── __init__.py
│   │   ├── material_repository.py
│   │   ├── background_repository.py
│   │   └── model_resources_repository.py
│   ├── cnc_workflow/
│   │   ├── __init__.py
│   │   ├── project_model_repository.py
│   │   ├── gcode_repository.py
│   │   ├── cutlist_repository.py
│   │   └── cost_repository.py
│   └── tooling/
│       ├── __init__.py
│       ├── tool_import_repository.py
│       ├── tool_database_repository.py
│       ├── provider_repository.py
│       └── tool_preferences_repository.py
└── migrations/
    └── migration_*.sql
```

## Repository Entry Points
- `src/core/database/__init__.py` re-exports `DatabaseManager` plus commonly used repositories (backward compatibility).
- Each subpackage `__init__.py` exports its public classes so imports look like `from src.core.database.repositories.core import ModelRepository`.
- Non-public helpers (e.g., serialization utilities inside repositories) remain module-private to discourage leakage.

## Implementation Phases
1. **Bootstrap subpackages**: create directories + __init__ files, move modules physically, fix relative imports, keep existing tests green.
2. **Update facade wiring**: point `DatabaseManager` to new module paths (e.g., `from .repositories.resources import MaterialRepository`).
3. **Migration manager alignment**: relocate migration utilities under `infrastructure/maintenance` and hook future SQL migrations via discovery.
4. **Tooling updates**: adjust scripts in `tools/` and parsers that import provider/tool repositories.
5. **Documentation + diagrams**: refresh architecture docs to show new boundaries.

## Import Strategy
- Prefer absolute package imports (e.g., `from src.core.database.repositories.core import ModelRepository`) to avoid fragile relative chains.
- Maintain thin re-export surfaces to avoid touching dozens of GUI/modules; e.g., `src/core/database/repositories/__init__.py` can expose shorthand names.
- For helper modules used outside the database package (e.g., `query_optimizer`), consider dedicated service modules or explicit exports.

## Testing and Validation
- Run targeted unit suites: `tests/test_phase1_database_schema.py`, `tests/test_migration_manager.py`, CNC workflow tests touching repositories.
- Exercise integration suites that touch `DatabaseManager` to ensure import paths remain valid.
- Use lint + mypy (if configured) to catch stale imports.

## Open Questions / Follow-ups
- Should enhanced repositories (`enhanced_model_repository.py`) move under the same `repositories/core` namespace or a separate `experiments` folder?
- Do we want to keep `DatabaseManager` under infrastructure/connections or elevate it to package root for discoverability?
- Is it time to formalize repository interfaces in `src/core/interfaces` to decouple further?
- After reorg, consider enforcing package boundaries via import linter (e.g., `flake8-import-order` or custom script).