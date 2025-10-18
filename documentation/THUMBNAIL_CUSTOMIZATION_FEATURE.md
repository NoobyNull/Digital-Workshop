# Thumbnail Customization Feature

## Overview

A new **Thumbnails** tab has been added to the Preferences dialog, allowing users to customize how all generated thumbnails look. Users can select a background image and material that will be applied to all thumbnail generation operations.

## Location

**Menu:** Edit → Preferences → Thumbnails tab

## Features

### 1. **Background Image Selection**
- Browse and select from pre-configured background images
- Located in `src/resources/backgrounds/`
- Available backgrounds:
  - Blue.png
  - Brick.png
  - Gray.png
  - Green.png
- Live preview of selected background
- Thumbnails will render with the selected background

### 2. **Material Selection**
- Choose a material to apply to all models in thumbnails
- Located in `src/resources/materials/`
- Available materials:
  - None (Default) - No material applied
  - Bambu Board
  - Cherry
  - Maple
  - Paduc
  - Pine
  - Purpleheart
  - Red Oak
  - Sapele
- Material is applied to all models during thumbnail generation

### 3. **Live Preview**
- Shows selected background image
- Updates when background selection changes
- Helps visualize how thumbnails will look

## User Interface

### Background Section
```
Background Image
Select a background image for thumbnails:
[List of available backgrounds]
  - Blue
  - Brick
  - Gray
  - Green
```

### Material Section
```
Material
Select a material to apply to all thumbnails:
[Dropdown Menu]
  - None (Default)
  - Bambu Board
  - Cherry
  - Maple
  - Paduc
  - Pine
  - Purpleheart
  - Red Oak
  - Sapele
```

### Preview Section
```
Preview
[Live preview of selected background image]
```

## Implementation Details

### New Class: `ThumbnailSettingsTab`
- **Location:** `src/gui/preferences.py`
- **Purpose:** UI for thumbnail customization
- **Features:**
  - Populates backgrounds from `src/resources/backgrounds/`
  - Populates materials from `src/resources/materials/`
  - Loads current settings on initialization
  - Provides live preview
  - Exposes `get_settings()` method

### Updated Class: `ScreenshotGenerator`
- **Location:** `src/gui/screenshot_generator.py`
- **New Parameters:**
  - `background_image` - Path to background image file
  - `material_name` - Name of material to apply
- **New Method:** `_set_background()` - Applies background image or default color
- **Features:**
  - Loads background image from file
  - Converts to VTK texture
  - Falls back to default gray if image not found
  - Applies material to all models

### Updated Class: `BatchScreenshotWorker`
- **Location:** `src/gui/batch_screenshot_worker.py`
- **New Parameters:**
  - `background_image` - Passed to ScreenshotGenerator
  - `material_name` - Passed to ScreenshotGenerator
- **Features:**
  - Accepts thumbnail settings from preferences
  - Passes settings to ScreenshotGenerator
  - All generated thumbnails use same settings

## VTK Configuration

### Background Handling
```python
# If background image provided:
renderer.SetBackgroundTexture(texture)
renderer.TexturedBackgroundOn()

# Otherwise:
renderer.SetBackground(0.95, 0.95, 0.95)  # Light gray
```

### Material Application
```python
# Material applied via MaterialManager
material_manager.apply_material_to_actor(actor, material_name)
```

### Grid Visibility
- Grid is **disabled** in thumbnail generation
- Only model and background are rendered
- Clean, professional appearance

## Settings Persistence

Settings are stored in `ApplicationConfig`:
- `thumbnail_bg_image` - Path to selected background image
- `thumbnail_material` - Name of selected material

Settings persist across application restarts.

## Usage Workflow

### Step 1: Open Preferences
1. Click Edit → Preferences
2. Select "Thumbnails" tab

### Step 2: Select Background
1. Browse the background list
2. Click to select desired background
3. Preview updates automatically

### Step 3: Select Material
1. Open Material dropdown
2. Select desired material
3. "None (Default)" for no material

### Step 4: Generate Thumbnails
1. Go to Edit → Tools → Generate Library Screenshots
2. Or use File & Model Maintenance → Regenerate Thumbnails
3. All thumbnails will use selected settings

## Technical Notes

### Background Image Processing
- Images loaded from file using PIL
- Converted to VTK texture format
- Supports PNG, JPG, and other PIL-supported formats
- Automatically scaled to fit renderer

### Material Application
- Uses existing MaterialManager
- Applies wood textures and properties
- Supports PBR (Physically Based Rendering) if available
- Falls back to classic shading if needed

### Performance
- Settings loaded once at startup
- Applied to all models in batch
- No per-model overhead
- Efficient texture caching

## File Structure

```
src/resources/
├── backgrounds/
│   ├── Blue.png
│   ├── Brick.png
│   ├── Gray.png
│   └── Green.png
└── materials/
    ├── bambu_board.mtl
    ├── bambu_board.png
    ├── cherry.mtl
    ├── cherry.png
    ├── maple.mtl
    ├── maple.png
    ├── paduc.mtl
    ├── paduc.png
    ├── pine.mtl
    ├── pine.png
    ├── purpleheart.mtl
    ├── purpleheart.png
    ├── red_oak.mtl
    ├── red_oak.png
    ├── sapele.mtl
    └── sapele.png
```

## Adding New Backgrounds

1. Add PNG image to `src/resources/backgrounds/`
2. Image will automatically appear in preferences
3. Restart application or refresh preferences

## Adding New Materials

1. Add MTL file to `src/resources/materials/`
2. Add corresponding PNG texture file
3. Material will automatically appear in dropdown
4. Restart application or refresh preferences

## Future Enhancements

- Custom background image upload
- Background color picker
- Material preview in dropdown
- Per-model material override
- Batch material application
- Background blur/opacity settings

