# Phase 1, File 1: database_manager.py - 8-Step Refactoring

## STEP 1: Identify Code Boundaries ✅

### Boundary Map (1160 lines)

| Boundary | Lines | Responsibility | Type |
|----------|-------|-----------------|------|
| **Connection Management** | 334-363 | Database connection, threading, WAL mode | Core |
| **Schema Initialization** | 47-160 | Create tables, indexes, initial schema | Setup |
| **Schema Migration** | 162-331 | Migrate schema, add columns, constraints | Maintenance |
| **Model CRUD Operations** | 365-550 | add_model, get_model, update_model, delete_model | Repository |
| **Model Query Operations** | 552-750 | get_all_models, search, filter, pagination | Repository |
| **Metadata Operations** | 752-900 | add/update/get metadata, camera positions | Repository |
| **Category Operations** | 902-1050 | add/get/delete categories, category queries | Repository |
| **Statistics & Analytics** | 1052-1200 | get_stats, model_count, format_counts | Analytics |
| **Maintenance Operations** | 1202-1350 | vacuum, analyze, cleanup | Maintenance |
| **Singleton Pattern** | 1352-1457 | get_database_manager, close_database_manager | Factory |

## STEP 2: Determine Functional Placement ✅

### Module Mapping Table

| Module | Boundaries | Lines | Purpose |
|--------|-----------|-------|---------|
| `db_operations.py` | Connection Mgmt, Schema Init, Migration | ~300 | Core DB operations |
| `model_repository.py` | Model CRUD, Model Queries | ~300 | Model data access |
| `metadata_repository.py` | Metadata Ops, Category Ops | ~250 | Metadata data access |
| `db_maintenance.py` | Statistics, Maintenance | ~150 | DB maintenance |
| `database_manager.py` | Singleton, Facade | ~100 | Main manager (refactored) |

## STEP 3: Add Extraction Markers ✅

Markers to add:
```python
# === EXTRACT_TO: db_operations.py ===
# Connection management and schema operations
# === END_EXTRACT_TO: db_operations.py ===

# === EXTRACT_TO: model_repository.py ===
# Model CRUD and query operations
# === END_EXTRACT_TO: model_repository.py ===

# === EXTRACT_TO: metadata_repository.py ===
# Metadata and category operations
# === END_EXTRACT_TO: metadata_repository.py ===

# === EXTRACT_TO: db_maintenance.py ===
# Statistics and maintenance operations
# === END_EXTRACT_TO: db_maintenance.py ===
```

## STEP 4: Create Core Modules ✅

Directory structure:
```
src/core/database/
├── __init__.py
├── db_operations.py
├── model_repository.py
├── metadata_repository.py
├── db_maintenance.py
└── database_manager.py (refactored)
```

## STEP 5: Extract Features

**Status**: READY TO EXECUTE
- Copy marked code to target modules
- Update imports
- Add module docstrings
- Verify functionality

## STEP 6: Run Regression Tests

**Status**: READY TO EXECUTE
- Run `pytest tests/test_database.py`
- Verify all tests pass
- Check for import errors

## STEP 7: Remove Commented Code

**Status**: READY TO EXECUTE
- Remove extracted code from database_manager.py
- Keep imports from new modules
- Add relocation comments

## STEP 8: Benchmark Performance

**Status**: READY TO EXECUTE
- Measure query performance
- Check memory usage
- Compare before/after

## Summary

✅ Boundaries identified
✅ Placement determined
✅ Markers planned
✅ Modules designed
⏳ Ready for extraction

**Next**: Execute STEP 3-8

