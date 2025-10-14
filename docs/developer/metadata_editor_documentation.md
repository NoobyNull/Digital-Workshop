# Metadata Editor Documentation

## Overview

The Metadata Editor is a comprehensive widget for editing 3D model metadata in the 3D-MM application. It provides a user-friendly interface for managing model properties including title, description, keywords, category, source, and rating.

## Features

### Form Fields
- **Title**: Custom name for the model
- **Description**: Detailed description of the model
- **Keywords**: Comma-separated keywords for search and categorization
- **Category**: Selection from predefined categories or custom categories
- **Source**: URL or reference to where the model came from

### Star Rating System
- Interactive 1-5 star rating widget
- Visual feedback with hover effects
- Click to set rating
- Gold filled stars for selected rating
- Light gold hover preview
- Gray empty stars for unselected rating

### Action Buttons
- **Save**: Save metadata to database
- **Cancel**: Discard changes and revert to original values
- **Reset**: Reset form to original metadata values

### Model Information Display
- Filename, format, file size, and triangle count
- Automatically populated when a model is selected
- Read-only display of model properties

## Architecture

### Components

#### StarRatingWidget
A custom widget for displaying and interacting with star ratings:
- Inherits from QWidget
- Custom painting for star shapes
- Mouse event handling for interaction
- Signal emission for rating changes

#### MetadataEditorWidget
The main widget that provides the metadata editing interface:
- Inherits from QWidget
- Integrates with database manager
- Handles form validation and error handling
- Manages state and change detection

### Database Integration

The metadata editor integrates with the database manager to:
- Load existing metadata for models
- Save new or updated metadata
- Handle database errors gracefully
- Validate category references

### Signal System

The metadata editor uses Qt's signal system for:
- `metadata_saved(model_id)`: Emitted when metadata is successfully saved
- `metadata_changed(model_id)`: Emitted when any field is modified
- `rating_changed(rating)`: Emitted when the star rating changes

## Usage

### Basic Usage

```python
from gui.metadata_editor import MetadataEditorWidget

# Create the widget
editor = MetadataEditorWidget()

# Load metadata for a model
editor.load_model_metadata(model_id)

# Connect to signals
editor.metadata_saved.connect(on_metadata_saved)
editor.metadata_changed.connect(on_metadata_changed)
```

### Integration with Main Window

The metadata editor is integrated into the main window as a dock widget:
- Placed in the bottom dock area
- Automatically loads metadata when a model is selected
- Updates the model library when metadata is saved

## Validation

### Input Validation

The metadata editor performs the following validation:
- **Title**: Recommended but not required (shows confirmation dialog if empty)
- **Keywords**: Limited to 20 keywords maximum
- **Rating**: Must be between 0 and 5

### Error Handling

- Database errors are caught and displayed to the user
- Invalid input shows appropriate warning messages
- Unsaved changes are detected on close

## Performance Considerations

### Memory Management
- Efficient cleanup of resources
- Garbage collection on widget destruction
- No memory leaks during repeated operations

### UI Responsiveness
- Non-blocking database operations
- Progress feedback for long operations
- Smooth interaction during metadata editing

## Testing

### Unit Tests

The metadata editor includes comprehensive unit tests:
- Star rating widget functionality
- Form field validation
- Database integration
- Signal emission
- Error handling

### Test Coverage

Tests cover:
- Widget initialization
- Metadata loading and saving
- Form validation
- User interaction
- Error scenarios

## Styling

The metadata editor uses CSS styling for:
- Consistent appearance with the application
- Hover effects on interactive elements
- Focus indicators for form fields
- Professional look and feel

## Future Enhancements

### Potential Improvements
- Batch metadata editing for multiple models
- Custom metadata fields
- Metadata templates
- Import/export of metadata
- Metadata history and versioning

### Integration Opportunities
- Tag management system
- Advanced search filters
- Metadata-based model recommendations
- Statistical analysis of metadata usage

## Troubleshooting

### Common Issues

1. **Metadata not saving**
   - Check database connection
   - Verify model ID is valid
   - Check for validation errors

2. **Categories not loading**
   - Verify database contains categories
   - Check database manager connection
   - Restart application

3. **Star rating not responding**
   - Check mouse events are being captured
   - Verify widget is enabled
   - Check for overlapping widgets

### Debug Information

The metadata editor logs detailed information:
- Initialization and cleanup
- Database operations
- Validation errors
- User interactions

Check the log files for detailed error information.

## API Reference

### MetadataEditorWidget

#### Methods

- `load_model_metadata(model_id)`: Load metadata for a model
- `has_unsaved_changes()`: Check if there are unsaved changes
- `cleanup()`: Clean up resources

#### Signals

- `metadata_saved(model_id)`: Emitted when metadata is saved
- `metadata_changed(model_id)`: Emitted when metadata changes

### StarRatingWidget

#### Methods

- `set_rating(rating)`: Set the rating value
- `get_rating()`: Get the current rating
- `reset_rating()`: Reset the rating to 0

#### Signals

- `rating_changed(rating)`: Emitted when rating changes