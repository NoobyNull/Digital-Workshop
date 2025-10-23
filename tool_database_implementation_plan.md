# Tool Database Management System Implementation Plan

## Overview
This document provides a detailed implementation plan for the tool database management system for the Digital Workshop application. The system will replace the existing JSON-based tool library with a unified SQLite database that can handle multiple tool formats (CSV, JSON, VTDB, and TDB).

## System Architecture

### Database Schema Design
The SQLite database will include the following tables:

1. **Providers Table**
   - id (INTEGER PRIMARY KEY)
   - name (TEXT UNIQUE NOT NULL)
   - description (TEXT)
   - file_path (TEXT)
   - format_type (TEXT) - 'CSV', 'JSON', 'VTDB', 'TDB'
   - created_at (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
   - updated_at (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

2. **Tools Table**
   - id (INTEGER PRIMARY KEY)
   - provider_id (INTEGER FOREIGN KEY REFERENCES Providers(id))
   - guid (TEXT)
   - description (TEXT NOT NULL)
   - tool_type (TEXT)
   - diameter (REAL)
   - vendor (TEXT)
   - product_id (TEXT)
   - unit (TEXT DEFAULT 'inches')
   - created_at (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
   - updated_at (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

3. **ToolProperties Table**
   - id (INTEGER PRIMARY KEY)
   - tool_id (INTEGER FOREIGN KEY REFERENCES Tools(id))
   - property_name (TEXT NOT NULL)
   - property_value (TEXT)
   - property_type (TEXT) - 'geometry', 'start_values', 'custom'
   - created_at (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

4. **Preferences Table**
   - id (INTEGER PRIMARY KEY)
   - key (TEXT UNIQUE NOT NULL)
   - value (TEXT)
   - created_at (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
   - updated_at (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

### File Structure
```
src/
├── core/
│   └── database/
│       ├── tool_database_repository.py    # Tool-specific database operations
│       ├── provider_repository.py         # Provider management
│       └── tool_preferences_repository.py # Preferences management
├── parsers/
│   ├── tool_parsers/
│   │   ├── __init__.py
│   │   ├── base_tool_parser.py           # Base class for tool parsers
│   │   ├── csv_tool_parser.py            # CSV format parser
│   │   ├── json_tool_parser.py           # JSON format parser
│   │   ├── vtdb_tool_parser.py           # VTDB (SQLite) format parser
│   │   └── tdb_tool_parser.py            # TDB (binary) format parser
│   └── tool_database_manager.py          # Unified tool database manager
├── gui/
│   └── feeds_and_speeds/
│       ├── add_tool_dialog.py            # "Add Tool" dialog
│       ├── external_db_dialog.py         # External database viewer/editor
│       ├── tool_preferences_dialog.py    # Database preferences dialog
│       ├── feeds_and_speeds_widget.py    # Updated main widget
│       └── tool_library_manager.py       # Updated to use database
└── tools/
    └── migration/
        └── json_to_sqlite_migrator.py    # Migration utility
```

## Implementation Steps

### Phase 1: Database Foundation

#### Step 1: Create SQLite database schema
- File: `src/core/database/tool_database_schema.py`
- Create database initialization script
- Define all tables with proper constraints and indexes
- Include migration system for schema updates

#### Step 2: Implement database repository classes
- File: `src/core/database/tool_database_repository.py`
- Implement CRUD operations for tools
- Include search and filtering capabilities
- Add transaction support for batch operations

- File: `src/core/database/provider_repository.py`
- Implement provider management
- Add provider import/export functionality

- File: `src/core/database/tool_preferences_repository.py`
- Implement preferences management
- Add validation for preference values

### Phase 2: Parser Implementation

#### Step 3: Create base tool parser
- File: `src/parsers/tool_parsers/base_tool_parser.py`
- Define common interface for all tool parsers
- Include progress reporting and error handling
- Add validation methods

#### Step 4: Implement CSV parser
- File: `src/parsers/tool_parsers/csv_tool_parser.py`
- Parse IDC-Woodcraft-Carbide-Create-Database-5-2-2025.csv format
- Handle CSV-specific edge cases
- Include data validation and cleaning

#### Step 5: Implement JSON parser
- File: `src/parsers/tool_parsers/json_tool_parser.py`
- Parse IDCWoodcraftFusion360Library.json format
- Maintain compatibility with existing JSON structure
- Add support for nested properties

#### Step 6: Implement VTDB parser
- File: `src/parsers/tool_parsers/vtdb_tool_parser.py`
- Parse IDC Woodcraft Vectric Tool Database Library Update rev 25-5.vtdb
- Handle SQLite-based VTDB format
- Include direct database-to-database migration

#### Step 7: Implement TDB parser
- File: `src/parsers/tool_parsers/tdb_tool_parser.py`
- Parse IDC-Woodcraft-Carveco-Tool-Database.tdb format
- Handle binary format with UTF-16 encoding
- Include format detection and validation

### Phase 3: Integration and Management

#### Step 8: Implement unified tool database manager
- File: `src/parsers/tool_database_manager.py`
- Integrate all parsers
- Provide unified interface for tool operations
- Include caching and performance optimization

#### Step 9: Create migration utility
- File: `src/tools/migration/json_to_sqlite_migrator.py`
- Migrate existing JSON tool library to SQLite
- Preserve user preferences and personal toolbox
- Include rollback capability

### Phase 4: User Interface Updates

#### Step 10: Update FeedsAndSpeedsWidget
- File: `src/gui/feeds_and_speeds/feeds_and_speeds_widget.py`
- Replace JSON-based operations with database operations
- Maintain existing UI functionality
- Add provider selection dropdown

#### Step 11: Create "Add Tool" dialog
- File: `src/gui/feeds_and_speeds/add_tool_dialog.py`
- Show available providers and their tools
- Include search and filtering
- Add preview of tool properties

#### Step 12: Implement export functionality
- File: `src/gui/feeds_and_speeds/export_dialog.py`
- Export to external databases
- Support multiple export formats
- Include progress reporting

#### Step 13: Create external database viewer/editor
- File: `src/gui/feeds_and_speeds/external_db_dialog.py`
- View and edit external database content
- Include calculation capabilities
- Add import/export functionality

#### Step 14: Implement preferences system
- File: `src/gui/feeds_and_speeds/tool_preferences_dialog.py`
- Manage external database paths
- Include database connection settings
- Add validation and testing

### Phase 5: Quality Assurance

#### Step 15: Add comprehensive logging
- Add JSON-formatted logs to all modules
- Include performance metrics
- Add error tracking and reporting

#### Step 16: Create unit tests
- File: `tests/test_tool_parsers.py`
- Test all parser functions
- Include edge cases and error conditions
- Test with sample files

#### Step 17: Create integration tests
- File: `tests/test_tool_database_integration.py`
- Test complete workflows
- Include database operations
- Test UI interactions

#### Step 18: Perform memory leak testing
- Test repeated operations
- Monitor memory usage
- Verify proper cleanup

#### Step 19: Create performance benchmarks
- File: `tests/test_tool_database_performance.py`
- Benchmark database operations
- Test with large datasets
- Verify performance requirements

#### Step 20: Write documentation
- File: `documentation/tool_database_system.md`
- Include user guide
- Add developer documentation
- Create troubleshooting guide

## Testing Requirements

### Unit Tests
- Each parser must have comprehensive unit tests
- Test with actual sample files provided by user
- Include edge cases and malformed data handling
- Verify error handling and logging

### Integration Tests
- Test complete import workflows
- Verify database operations
- Test UI interactions
- Include performance testing

### Memory Leak Testing
- Run each operation 10-20 times
- Monitor memory usage patterns
- Verify proper resource cleanup
- Test with large datasets

### Performance Benchmarks
- Database operations should complete within specified time limits
- Memory usage should remain stable during stress testing
- UI should remain responsive during operations
- Verify performance targets are met

## Expected Outcomes

When complete, the system will:

1. Replace the existing JSON-based tool library with a unified SQLite database
2. Support importing tools from four different formats (CSV, JSON, VTDB, TDB)
3. Provide an enhanced "Add Tool" dialog with provider selection
4. Include export functionality to external databases
5. Offer an external database viewer/editor for calculations
6. Maintain all existing functionality while adding new capabilities
7. Include comprehensive logging and error handling
8. Meet all performance and quality requirements

## Completion Criteria

The project is complete when:

1. All implementation steps are finished
2. All unit tests pass
3. All integration tests pass
4. Memory leak testing shows no leaks
5. Performance benchmarks meet requirements
6. Documentation is complete
7. User acceptance testing is successful
8. Existing functionality is preserved
9. New functionality works as specified
10. The system is ready for production use

## Mermaid Architecture Diagram

```mermaid
graph TB
    A[Feeds & Speeds Widget] --> B[Tool Database Manager]
    B --> C[Tool Database Repository]
    B --> D[Provider Repository]
    B --> E[Preferences Repository]
    
    F[CSV Parser] --> B
    G[JSON Parser] --> B
    H[VTDB Parser] --> B
    I[TDB Parser] --> B
    
    J[Add Tool Dialog] --> A
    K[External DB Dialog] --> A
    L[Preferences Dialog] --> A
    
    M[Migration Utility] --> C
    
    N[SQLite Database] --> C
    N --> D
    N --> E
    
    subgraph "Parsers"
        F
        G
        H
        I
    end
    
    subgraph "UI Components"
        A
        J
        K
        L
    end
    
    subgraph "Database Layer"
        C
        D
        E
        N
    end