# Background Color User-Settable Implementation

## Overview
Implemented user-settable background color for thumbnail generation. Users can now choose a custom background color through the Preferences dialog, which is persisted and used for all thumbnail generation operations.

## Changes Made

### 1. **ThumbnailSettingsTab** (`src/gui/preferences/tabs/thumbnail_settings_tab.py`)
- Added color picker button and preview label
- Added `_on_color_picker_clicked()` method to open color picker dialog
- Added `_update_color_preview()` method to display selected color
- Updated `_load_settings()` to load background color from QSettings
- Updated `get_settings()` to include background_color
- Updated `save_settings()` to persist background_color to QSettings
- Default color: `#404658` (professional dark teal-gray)

### 2. **ApplicationConfig** (`src/core/application_config.py`)
- Updated `thumbnail_bg_color` default from `"theme"` to `"#404658"`
- Now stores the professional dark teal-gray color as default

### 3. **Metadata Editor** (`src/gui/metadata_components/metadata_editor_main.py`)
- Updated thumbnail regeneration to load background color from settings
- Uses background image if set, otherwise uses background color
- Passes combined background preference to thumbnail service

### 4. **Library Event Handler** (`src/gui/model_library_components/library_event_handler.py`)
- Updated thumbnail regeneration to load background color from settings
- Uses background image if set, otherwise uses background color
- Passes combined background preference to thumbnail service

### 5. **Model Library** (`src/gui/model_library.py`)
- Updated thumbnail regeneration to load background color from settings
- Uses background image if set, otherwise uses background color
- Passes combined background preference to thumbnail service

### 6. **Import Dialog** (`src/gui/import_components/import_dialog.py`)
- Updated thumbnail generation during import to load background color from settings
- Uses background image if set, otherwise uses background color
- Passes combined background preference to thumbnail service

### 7. **Import Coordinator** (`src/core/import_coordinator.py`)
- Updated `_generate_thumbnails()` to load background color from settings
- Uses background image if set, otherwise uses background color
- Passes background and material to batch thumbnail generation

## How It Works

### User Flow
1. User opens Preferences dialog (Edit → Preferences)
2. Navigates to "Content" tab
3. Sees "Background Color" section with:
   - "Choose Color" button
   - Color preview box showing current color
   - "Background Image" section below (optional)
4. Clicks "Choose Color" to open color picker
5. Selects desired color
6. Color preview updates immediately
7. Clicks "Save" to persist settings

### Thumbnail Generation Flow
1. When generating thumbnails, code loads settings:
   ```python
   bg_image = settings.value("thumbnail/background_image", ...)
   bg_color = settings.value("thumbnail/background_color", ...)
   background = bg_image if bg_image else bg_color
   ```
2. If background image is set, it's used (takes priority)
3. Otherwise, background color is used
4. Color is passed to VTKRenderingEngine which handles hex color conversion

## Settings Storage

Settings are stored in QSettings with keys:
- `thumbnail/background_color` - Hex color string (e.g., "#404658")
- `thumbnail/background_image` - Path to background image (optional)
- `thumbnail/material` - Material name (optional)

## Default Behavior

- **Default Color**: `#404658` (professional dark teal-gray)
- **Priority**: Background image > Background color
- **Fallback**: If neither is set, uses default color

## Technical Details

### Color Picker Integration
- Uses Qt's `QColorDialog.getColor()` for native color picker
- Supports alpha channel (transparency)
- Returns hex color string (e.g., "#404658")

### Color Preview
- Shows selected color in a small preview box
- Updates immediately when color is changed
- Uses theme-aware styling for border

### Persistence
- Settings saved to QSettings on "Save" button click
- Settings loaded on preferences dialog open
- ApplicationConfig updated for runtime compatibility

## Testing

All modified files compile without errors:
- ✅ `thumbnail_settings_tab.py`
- ✅ `application_config.py`
- ✅ `metadata_editor_main.py`
- ✅ `library_event_handler.py`
- ✅ `model_library.py`

## User Experience

1. **Easy to Use**: Simple color picker button in preferences
2. **Visual Feedback**: Color preview shows selected color
3. **Persistent**: Settings saved and restored on app restart
4. **Flexible**: Can use color alone or combine with background image
5. **Professional**: Default color matches professional studio rendering style

## Future Enhancements

- Preset color options (Professional, Light, Dark, Custom)
- Color history/recent colors
- Per-project background color settings
- Background color preview in thumbnail list

