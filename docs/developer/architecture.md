# 3D-MM Architecture

## Project Structure

```
3D-MM/
├── src/                    # Source code
│   ├── core/              # Core business logic
│   ├── gui/               # User interface components
│   ├── parsers/           # 3D format parsers
│   └── utils/             # Utility functions
├── resources/             # Application resources
│   ├── icons/             # Icon files
│   └── styles/            # CSS stylesheets
├── tests/                 # Test suite
├── docs/                  # Documentation
├── installer/             # Installation scripts
└── requirements.txt       # Python dependencies
```

## Core Components

### Core Module (`src/core/`)

The core module contains the main business logic of the application:

- **Database Manager**: Handles all SQLite database operations
- **Model Manager**: Manages 3D model objects and operations
- **Search Engine**: Provides search and filtering capabilities
- **Logging Configuration**: Sets up JSON-based logging

### GUI Module (`src/gui/`)

The GUI module contains all user interface components:

- **Model Viewer**: 3D visualization widget using PySide2-3D
- **Model Library**: Main interface for browsing and managing models
- **Metadata Editor**: Widget for editing model properties and tags

### Parsers Module (`src/parsers/`)

The parsers module handles various 3D file formats:

- **STL Parser**: For STL stereolithography files
- **OBJ Parser**: For Wavefront OBJ files
- **3MF Parser**: For 3D Manufacturing Format files
- **STEP Parser**: For STEP/ISO 10303 files

### Utils Module (`src/utils/`)

The utils module contains utility functions:

- **File Utils**: File operations and validation
- **Geometry Utils**: Calculations for 3D geometry

## Data Flow

1. User imports 3D models through the GUI
2. Parser validates and extracts model data
3. Model Manager processes and stores in database
4. Model Viewer renders the 3D model
5. User can search, filter, and organize models

## Technology Stack

- **Python 3.8-3.12**: Core programming language
- **PySide6**: GUI framework
- **PySide2-3D**: 3D visualization
- **SQLite**: Database for model metadata
- **VTK**: Optional advanced 3D visualization
- **NumPy**: Numerical operations for geometry

## Performance Considerations

- Adaptive loading based on hardware capabilities
- Progressive rendering for large files
- Memory-efficient processing
- Background loading with progress feedback