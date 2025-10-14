# Model Library Documentation

## Overview

The Model Library is a comprehensive interface component for the 3D-MM application that provides users with tools to manage, organize, and view 3D model collections. It features a file browser, model list/grid views, drag-and-drop support, thumbnail generation, and database integration.

## Architecture

### Components

The Model Library consists of several key components:

1. **ModelLibraryWidget**: The main widget that orchestrates all functionality
2. **ModelLoadWorker**: Background thread for loading models without blocking the UI
3. **ThumbnailGenerator**: Utility class for creating model previews
4. **File Browser**: Tree view for navigating file system
5. **Model Views**: List and grid views for displaying models
6. **Database Integration**: Connection to SQLite database for model metadata

### Class Hierarchy

```
ModelLibraryWidget (QWidget)
├── ModelLoadWorker (QThread)
├── ThumbnailGenerator
├── File Browser (QTreeView)
├── Model Views (QTableView, QListView)
└── Database Integration
```

## Features

### File Browser

The file browser provides a tree view of the file system for easy navigation:

- **Path Display**: Shows the current directory path
- **Tree Navigation**: Navigate through directories with expand/collapse functionality
- **File Type Recognition**: Identifies supported 3D model files (STL, OBJ, STEP, MF3)
- **Directory Scanning**: Scans directories for model files

### Model Views

Two different view modes are available for displaying models:

#### List View

- Displays models in a table with columns for name, format, size, triangle count, category, and added date
- Supports sorting by any column
- Alternating row colors for better readability
- Row selection with multiple selection support

#### Grid View

- Displays models as icons with thumbnails
- Supports larger visual previews
- Adjustable icon sizes
- Grid layout with spacing

### Model Loading

Models are loaded in a background thread to maintain UI responsiveness:

- **Progress Feedback**: Shows loading progress with percentage and status messages
- **Cancellation Support**: Users can cancel long-running operations
- **Error Handling**: Graceful error handling with user-friendly messages
- **Memory Management**: Efficient cleanup of resources

### Thumbnail Generation

The system generates simple geometry-based thumbnails for models:

- **Complexity-Based Rendering**: Different rendering styles based on triangle count
  - Simple models (< 1000 triangles): Wireframe box
  - Medium models (1000-10000 triangles): Solid box with highlight
  - Complex models (> 10000 triangles): Sphere with detail indicators
- **Format Indicators**: Shows file format in the corner of thumbnails
- **Error Thumbnails**: Provides visual feedback for failed thumbnail generation

### Search and Filter

Users can search and filter models:

- **Text Search**: Search by model name or filename
- **Category Filter**: Filter by model category
- **Format Filter**: Filter by file format
- **Real-time Updates**: Filters apply immediately as criteria change

### Drag and Drop

The interface supports drag-and-drop for adding models:

- **File Dragging**: Drag model files from file explorer
- **Directory Support**: Drag entire directories (planned feature)
- **Format Validation**: Only accepts supported file formats
- **Visual Feedback**: Shows drag enter/leave states

### Context Menu

Right-click context menu provides quick access to common operations:

- **Open**: Load the selected model in the 3D viewer
- **Edit Properties**: Open the property editor (planned feature)
- **Delete**: Remove the model from the library

### Database Integration

All model information is stored in a SQLite database:

- **Model Metadata**: Store filename, format, file path, file size, and dates
- **Custom Properties**: Title, description, keywords, category, source, rating
- **View Tracking**: Track view counts and last viewed dates
- **Categories**: Predefined and custom categories for organization

## Usage

### Basic Usage

```python
# Create the model library widget
model_library = ModelLibraryWidget()

# Connect signals to handle model selection
model_library.model_selected.connect(on_model_selected)
model_library.model_double_clicked.connect(on_model_double_clicked)

# Add to layout
layout.addWidget(model_library)
```

### Adding Models

```python
# Method 1: Import dialog
model_library._import_models()

# Method 2: Load specific files
file_paths = ["model1.stl", "model2.obj"]
model_library._load_models(file_paths)

# Method 3: Drag and drop (user interaction)
```

### Getting Selected Models

```python
# Get single selected model ID
model_id = model_library.get_selected_model_id()

# Get all selected model IDs
model_ids = model_library.get_selected_models()
```

### Switching View Modes

```python
# Switch to list view
model_library._set_view_mode(ViewMode.LIST)

# Switch to grid view
model_library._set_view_mode(ViewMode.GRID)
```

## Performance Considerations

### Memory Management

- **Background Loading**: Models are loaded in background threads to prevent UI blocking
- **Resource Cleanup**: Proper cleanup of resources when models are no longer needed
- **Garbage Collection**: Periodic garbage collection during large operations
- **Lazy Loading**: Thumbnails are generated on-demand

### UI Responsiveness

- **Progress Feedback**: All long operations provide progress feedback
- **Cancellation Support**: Users can cancel long-running operations
- **Thread Safety**: All UI updates are performed in the main thread
- **Efficient Rendering**: Minimal updates to the UI during operations

## Testing

The Model Library includes comprehensive tests:

- **Unit Tests**: Individual component testing
- **Integration Tests**: Complete workflow testing
- **Memory Leak Tests**: Repeated operation testing
- **Performance Tests**: Load time and responsiveness testing

### Running Tests

```bash
# Run all model library tests
python -m pytest tests/test_model_library.py -v

# Run specific test
python -m pytest tests/test_model_library.py::TestModelLibraryWidget::test_widget_initialization -v
```

## Troubleshooting

### Common Issues

1. **Models Not Loading**
   - Check file permissions
   - Verify file format is supported
   - Check database connection

2. **Thumbnails Not Displaying**
   - Verify model has valid geometry
   - Check thumbnail generation settings
   - Ensure adequate memory is available

3. **Search Not Working**
   - Verify database is properly initialized
   - Check search criteria
   - Ensure models are loaded in the view

4. **Performance Issues**
   - Check for memory leaks
   - Verify background thread is working
   - Consider reducing model complexity

### Debug Logging

Enable debug logging to troubleshoot issues:

```python
# Set logging level to DEBUG
import logging
logging.getLogger("3D-MM").setLevel(logging.DEBUG)
```

## Future Enhancements

### Planned Features

1. **Directory Scanning**: Full directory scanning for model files
2. **Property Editor**: Complete model property editing interface
3. **Batch Operations**: Batch import and processing
4. **Advanced Search**: More sophisticated search capabilities
5. **Custom Categories**: User-defined categories
6. **Model Previews**: 3D model previews in the grid view
7. **Export Functionality**: Export model lists and metadata

### Performance Improvements

1. **Caching**: Implement thumbnail caching
2. **Lazy Loading**: Load model details on-demand
3. **Background Processing**: More background processing for UI operations
4. **Memory Optimization**: Further memory usage optimization

## Dependencies

The Model Library depends on the following components:

- **PySide6**: Qt framework for GUI
- **SQLite**: Database for model metadata
- **STL Parser**: Custom parser for STL files
- **Logging System**: JSON-based logging system
- **Database Manager**: Database abstraction layer

## License

This component is part of the 3D-MM project and is subject to the project's license terms.