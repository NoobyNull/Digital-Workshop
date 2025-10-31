# Module Dependency Diagrams

## Current Architecture Dependencies

### Core Module Dependencies

```mermaid
graph TD
    A[application.py] --> B[application_config.py]
    A --> C[application_bootstrap.py]
    A --> D[exception_handler.py]
    A --> E[system_initializer.py]
    A --> F[gui.main_window]
    
    C --> G[logging_config.py]
    C --> H[material_provider.py]
    C --> I[background_provider.py]
    
    F --> J[model_library.py]
    F --> K[viewer_widget_vtk.py]
    F --> L[theme_manager_widget.py]
    F --> M[metadata_editor.py]
    
    J --> N[model_library_components]
    K --> O[viewer_3d_components]
    L --> P[theme_components]
```

### Database Architecture

```mermaid
graph TD
    A[database_manager.py] --> B[database.database_manager]
    B --> C[model_repository.py]
    B --> D[metadata_repository.py]
    B --> E[search_repository.py]
    B --> F[db_operations.py]
    B --> G[db_maintenance.py]
    
    C --> H[SQLite Database]
    D --> H
    E --> H
    F --> H
    G --> H
```

### Parser System Architecture

```mermaid
graph TD
    A[base_parser.py] --> B[stl_parser.py]
    A --> C[obj_parser.py]
    A --> D[threemf_parser.py]
    A --> E[step_parser.py]
    A --> F[format_detector.py]
    
    B --> G[stl_components]
    G --> H[stl_format_detector.py]
    G --> I[stl_models.py]
    G --> J[stl_parser_main.py]
    
    F --> K[ModelFormat Enum]
    A --> L[Model Class]
    A --> M[LoadingState Enum]
```

### Theme System Architecture

```mermaid
graph TD
    A[theme_core.py] --> B[manager.py]
    A --> C[presets.py]
    A --> D[persistence.py]
    A --> E[theme_constants.py]
    A --> F[theme_defaults.py]
    
    B --> G[ThemeManager Singleton]
    G --> H[qt_material_service.py]
    G --> I[simple_service.py]
    G --> J[qt_material_core.py]
    
    H --> K[qt_material library]
    I --> L[qt-material integration]
```

### GUI Component Dependencies

```mermaid
graph TD
    A[main_window.py] --> B[dock_manager.py]
    A --> C[event_handler.py]
    A --> D[menu_manager.py]
    
    B --> E[model_library.py]
    B --> F[viewer_widget_vtk.py]
    B --> G[metadata_editor.py]
    
    E --> H[model_library_facade.py]
    H --> I[library_ui_manager.py]
    H --> J[library_model_manager.py]
    H --> K[library_file_browser.py]
    
    F --> L[viewer_widget_facade.py]
    L --> M[vtk_scene_manager.py]
    L --> N[model_renderer.py]
    L --> O[camera_controller.py]
```

## Problematic Dependencies

### Circular Dependencies (Current Issues)

```mermaid
graph LR
    A[parsers.base_parser] -.->|lazy import| B[core.model_cache]
    B -.->|lazy import| A
    
    C[gui.theme.service] -.->|lazy import| D[gui.theme.manager]
    D -.->|lazy import| C
    
    E[gui.CLO.ui_components] -.->|delayed connection| F[main_window]
    F -.->|delayed connection| E
```

### High Coupling Areas

```mermaid
graph TD
    A[ThemeManager] --> B[GUI Components]
    A --> C[Core Services]
    A --> D[Database]
    
    E[DatabaseManager] --> F[GUI Components]
    E --> G[Core Services]
    E --> H[Parsers]
    
    I[MainWindow] --> J[All GUI Components]
    I --> K[Core Services]
    I --> L[Database]
```

## Improved Architecture (Target State)

### Reduced Coupling Design

```mermaid
graph TD
    A[Application Layer] --> B[Service Layer]
    B --> C[Data Access Layer]
    B --> D[UI Layer]
    
    C --> E[Database Repositories]
    C --> F[Cache Services]
    
    D --> G[GUI Components]
    D --> H[View Models]
    
    B --> I[Theme Service Interface]
    B --> J[Model Service Interface]
    B --> K[Database Service Interface]
    
    I --> L[Theme Implementation]
    J --> M[Model Implementation]
    K --> N[Database Implementation]
```

### Interface-Based Architecture

```mermaid
graph TD
    A[GUI Components] --> B[IThemeService]
    A --> C[IModelService]
    A --> D[IDatabaseService]
    
    B --> E[QtMaterialThemeService]
    C --> F[ModelManagementService]
    D --> G[DatabaseService]
    
    F --> H[ModelRepository]
    G --> I[Database Operations]
    
    H --> J[SQLite Database]
    I --> J
```

## Dependency Rules

### Allowed Dependencies
- Core → Core (same level)
- Core → Database (data access)
- GUI → Core Services (through interfaces)
- Parsers → Core (data structures)
- GUI → GUI (sibling components)

### Forbidden Dependencies
- GUI → Core (direct implementation)
- Database → GUI
- Parsers → GUI
- Circular imports (any direction)
- Implementation → Interface (reverse dependency)

### Dependency Injection Points
- Service interfaces in constructors
- Repository interfaces in services
- Factory pattern for complex object creation
- Plugin system for extensibility

## Migration Strategy

### Phase 1: Interface Extraction
1. Extract service interfaces
2. Create abstract base classes
3. Implement dependency injection containers

### Phase 2: Refactoring
1. Remove direct dependencies
2. Implement proper abstractions
3. Update import statements

### Phase 3: Testing
1. Add unit tests for interfaces
2. Integration tests for services
3. End-to-end testing

### Phase 4: Cleanup
1. Remove legacy code
2. Update documentation
3. Performance optimization