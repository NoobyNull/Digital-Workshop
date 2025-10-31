
# Candy-Cadence User Manual

## Overview

Welcome to Candy-Cadence, your comprehensive 3D model management and viewing solution. This user manual provides detailed instructions for using all features of Candy-Cadence to organize, view, and manage your 3D model collections efficiently.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Interface Overview](#interface-overview)
3. [Importing Models](#importing-models)
4. [Viewing Models](#viewing-models)
5. [Organizing Collections](#organizing-collections)
6. [Metadata Management](#metadata-management)
7. [Search and Filter](#search-and-filter)
8. [Batch Operations](#batch-operations)
9. [Performance Optimization](#performance-optimization)
10. [File Format Support](#file-format-support)
11. [Settings and Preferences](#settings-and-preferences)
12. [Troubleshooting](#troubleshooting)
13. [FAQ](#faq)

## Getting Started

### First Launch

When you launch Candy-Cadence for the first time:

1. **Welcome Screen**: You'll see a welcome screen with quick start options
2. **Initial Setup**: The application will create necessary directories and database
3. **System Check**: Automatic verification of graphics capabilities
4. **Sample Models**: Option to download sample models for testing

### Quick Start Guide

#### Step 1: Import Your First Model
1. Click **"Import Models"** button or use **File → Import Models**
2. Browse and select your 3D model files
3. Choose import options (copy files, create thumbnails, etc.)
4. Click **"Import"** to begin

#### Step 2: View Your Model
1. Double-click on any model in the library
2. The 3D viewer will open with your model loaded
3. Use mouse controls to rotate, zoom, and pan
4. Use the toolbar for viewing options

#### Step 3: Organize Your Collection
1. Create folders to organize models by project, type, or category
2. Add tags and metadata for better searchability
3. Use the search function to quickly find specific models

### System Requirements

**Minimum Requirements:**
- Windows 7 SP1 (64-bit)
- Intel Core i3-3220 or equivalent
- Intel HD Graphics 4000 or equivalent
- 4GB RAM
- 100MB free disk space

**Recommended Requirements:**
- Windows 10/11 (64-bit)
- Intel Core i5-3470 or equivalent
- NVIDIA GeForce GTX 1050 or equivalent
- 8GB RAM
- 500MB free disk space (SSD preferred)

## Interface Overview

### Main Window Layout

The Candy-Cadence interface consists of several key areas:

```
┌─────────────────────────────────────────────────────────────┐
│ Menu Bar: File  Edit  View  Tools  Help                      │
├─────────────────────────────────────────────────────────────┤
│ Toolbar: [Import] [Export] [Search] [Settings] [?]          │
├─────────────┬───────────────────────────────────────────────┤
│ Model       │ Main 3D Viewer Area                            │
│ Library     │                                               │
│ Panel       │                                               │
│             │                                               │
│ - Folders   │                                               │
│ - Models    │                                               │
│ - Tags      │                                               │
│             │                                               │
├─────────────┴───────────────────────────────────────────────┤
│ Status Bar: [Ready] [Memory: 245MB] [Models: 156]           │
└─────────────────────────────────────────────────────────────┘
```

### Menu Bar

#### File Menu
- **Import Models**: Add new 3D models to your library
- **Export Models**: Export selected models to different formats
- **Create Folder**: Organize models into folders
- **Delete**: Remove selected items
- **Properties**: View detailed information about selected items
- **Exit**: Close the application

#### Edit Menu
- **Cut/Copy/Paste**: Standard editing operations
- **Select All**: Select all items in current view
- **Find**: Search for specific models
- **Preferences**: Application settings

#### View Menu
- **Refresh**: Update the current view
- **Sort By**: Change sorting criteria (name, date, size, etc.)
- **View Mode**: Switch between list, grid, and thumbnail views
- **Show/Hide Panels**: Toggle visibility of different interface panels
- **Fullscreen**: Enter fullscreen viewing mode

#### Tools Menu
- **Batch Operations**: Perform operations on multiple models
- **Generate Thumbnails**: Create or regenerate model thumbnails
- **Optimize Database**: Clean up and optimize the model database
- **Import/Export Settings**: Backup and restore application settings

#### Help Menu
- **User Manual**: Open this user manual
- **Keyboard Shortcuts**: View available keyboard shortcuts
- **System Information**: View system and application information
- **Check for Updates**: Check for application updates
- **About**: Application version and credits

### Toolbar

The toolbar provides quick access to frequently used functions:

| Button | Function | Description |
|--------|----------|-------------|
| ![Import](icons/import.png) | Import | Import new 3D model files |
| ![Export](icons/export.png) | Export | Export selected models |
| ![Search](icons/search.png) | Search | Open search panel |
| ![Settings](icons/settings.png) | Settings | Open application settings |
| ![Help](icons/help.png) | Help | Open help documentation |

### Model Library Panel

The Model Library Panel displays your organized collection of 3D models:

#### Tree View
- **Root Folder**: Main collection folder
- **Custom Folders**: User-created organization folders
- **Recent**: Recently accessed models
- **Favorites**: Marked favorite models

#### List View
- **Model Thumbnails**: Visual preview of each model
- **Model Names**: Descriptive names for easy identification
- **File Information**: Size, format, and modification date
- **Status Indicators**: Loading status, processing state

### 3D Viewer Area

The main viewing area provides interactive 3D model visualization:

#### Viewer Controls
- **Mouse Controls**: 
  - Left click + drag: Rotate model
  - Right click + drag: Pan view
  - Mouse wheel: Zoom in/out
  - Double-click: Reset view to default

#### View Options
- **Wireframe Mode**: Display model as wireframe
- **Solid Mode**: Display model as solid geometry
- **Textured Mode**: Display model with applied textures
- **Lighting**: Adjust lighting conditions
- **Background**: Change viewer background color

#### Information Display
- **Model Statistics**: Vertex count, triangle count, file size
- **Camera Position**: Current viewing angle and distance
- **Performance Info**: Frame rate and rendering statistics

## Importing Models

### Supported File Formats

Candy-Cadence supports a wide range of 3D model formats:

| Format | Extension | Description | Features |
|--------|-----------|-------------|----------|
| STL | .stl | Stereolithography | Geometry only, widely supported |
| OBJ | .obj | Wavefront OBJ | Geometry + materials + textures |
| 3MF | .3mf | 3D Manufacturing Format | Modern format with full metadata |
| STEP | .step, .stp | STEP | CAD format with precise geometry |
| PLY | .ply | Stanford PLY | Polygon file format with properties |

### Import Methods

#### Method 1: Drag and Drop
1. Open Windows Explorer and navigate to your model files
2. Select one or more 3D model files
3. Drag the files into the Candy-Cadence window
4. The import dialog will appear with options
5. Configure import settings and click **"Import"**

#### Method 2: Import Dialog
1. Click **"Import"** button or use **File → Import Models**
2. Browse to select your 3D model files
3. Choose import options:
   - **Copy files to library**: Keep original files in place
   - **Move files to library**: Move files into application directory
   - **Create thumbnails**: Generate preview images
   - **Extract metadata**: Read and store model information
4. Click **"Import"** to begin

#### Method 3: Batch Import
1. Use **Tools → Batch Operations → Import Models**
2. Select a folder containing multiple model files
3. Configure batch import settings:
   - Include subdirectories
   - File format filters
   - Naming conventions
4. Click **"Start Import"**

### Import Options

#### File Handling
- **Copy to Library**: Creates a copy of files in the application directory
- **Move to Library**: Moves files from original location
- **Reference Only**: Keeps files in original location (saves disk space)

#### Processing Options
- **Generate Thumbnails**: Creates preview images for quick identification
- **Extract Metadata**: Reads and stores model properties (dimensions, materials, etc.)
- **Validate Geometry**: Checks for common geometry issues
- **Optimize Mesh**: Simplifies geometry for better performance

#### Organization Options
- **Auto-categorize**: Automatically organize by file type or content
- **Create Date Folders**: Organize by import date
- **Custom Naming**: Apply naming patterns to imported files

### Import Progress

During import, you'll see a progress dialog showing:

- **Files Processed**: Number of files completed
- **Current File**: Name of file being processed
- **Progress Bar**: Overall import progress
- **Estimated Time**: Time remaining for completion
- **Errors/Warnings**: Any issues encountered during import

## Viewing Models

### Basic Viewing

#### Opening Models
1. **Double-click**: Double-click any model in the library to open it
2. **Right-click Menu**: Right-click model and select **"View"**
3. **Keyboard Shortcut**: Press **Enter** when model is selected

#### Navigation Controls
- **Rotate**: Left-click and drag to rotate the model
- **Pan**: Right-click and drag to move the view
- **Zoom**: Mouse wheel to zoom in and out
- **Reset View**: Double-click in the viewer to reset to default position

#### View Modes
- **Perspective**: Standard 3D perspective view
- **Orthographic**: Technical drawing style view
- **Fit to View**: Automatically adjust zoom to fit entire model
- **Zoom to Selection**: Focus on selected parts of the model

### Advanced Viewing Features

#### Lighting Controls
1.