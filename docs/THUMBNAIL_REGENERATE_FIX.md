# Thumbnail Force Regenerate Fix

## Problem

When using the "Regenerate Thumbnail" context menu action in the model library, the system was not actually regenerating the thumbnail if one already existed. Instead, it would return the cached thumbnail without replacing it.

### Observed Behavior
```
INFO:DigitalWorkshop-Raw.src.core.thumbnail_components.thumbnail_generator_main:Thumbnail already exists: C:\Users\Matthew\AppData\Roaming\3DModelManager\thumbnails\220f5e7474bb7c35df8390ffae72164d.png
```

The thumbnail was not being regenerated even though `force_regenerate=True` was being passed.

## Root Cause

The issue was a **missing parameter** in the `ThumbnailGenerator.generate_thumbnail()` method:

1. **ImportThumbnailService** had the `force_regenerate` parameter and respected it
2. **ThumbnailGenerator** did NOT have the `force_regenerate` parameter
3. When ImportThumbnailService called ThumbnailGenerator, it couldn't pass the parameter
4. ThumbnailGenerator always checked if the file existed and returned early

### Code Flow (Before Fix)
```
model_library._regenerate_thumbnail()
  ↓
ImportThumbnailService.generate_thumbnail(force_regenerate=True)
  ↓ (skips cache check because force_regenerate=True)
  ↓
ThumbnailGenerator.generate_thumbnail() ← NO force_regenerate parameter!
  ↓
  if thumbnail_path.exists():  ← Always returns here
      return thumbnail_path
```

## Solution

Added the `force_regenerate` parameter to `ThumbnailGenerator.generate_thumbnail()` and implemented proper handling:

### Changes Made

**1. src/core/thumbnail_components/thumbnail_generator_main.py**
- Added `force_regenerate: bool = False` parameter to `generate_thumbnail()` method
- Modified the existence check to respect the parameter:
  ```python
  if thumbnail_path.exists() and not force_regenerate:
      return thumbnail_path
  ```
- Added code to remove existing thumbnail before regeneration:
  ```python
  if force_regenerate and thumbnail_path.exists():
      thumbnail_path.unlink()
  ```

**2. src/core/import_thumbnail_service.py**
- Updated the call to `ThumbnailGenerator.generate_thumbnail()` to pass the parameter:
  ```python
  thumbnail_path = self.thumbnail_generator.generate_thumbnail(
      ...
      force_regenerate=force_regenerate
  )
  ```

### Code Flow (After Fix)
```
model_library._regenerate_thumbnail()
  ↓
ImportThumbnailService.generate_thumbnail(force_regenerate=True)
  ↓ (skips cache check because force_regenerate=True)
  ↓
ThumbnailGenerator.generate_thumbnail(force_regenerate=True)
  ↓
  if thumbnail_path.exists() and not force_regenerate:  ← Condition is False
      return thumbnail_path
  ↓
  if force_regenerate and thumbnail_path.exists():
      thumbnail_path.unlink()  ← Remove old thumbnail
  ↓
  Generate new thumbnail  ← Regeneration happens!
```

## Testing

Created comprehensive tests to verify:
1. ✓ `force_regenerate=True` parameter is properly passed through the call chain
2. ✓ `force_regenerate=False` parameter is properly passed through the call chain
3. ✓ Existing thumbnails are NOT regenerated when `force_regenerate=False`
4. ✓ Existing thumbnails ARE removed and regenerated when `force_regenerate=True`

All tests passed successfully.

## Expected Behavior After Fix

When user clicks "Regenerate Thumbnail" in the context menu:
1. The old thumbnail file is removed
2. A new thumbnail is generated with **current preferences** (material and background)
3. The database is updated with the new thumbnail path
4. The UI refreshes to show the updated thumbnail

### New Log Output
```
INFO:DigitalWorkshop-Raw.src.gui.model_library:Regenerating thumbnail with preferences: material=Oak, bg_image=None
INFO:DigitalWorkshop-Raw.src.core.thumbnail_components.thumbnail_generator_main:Removed existing thumbnail for regeneration: C:\Users\Matthew\AppData\Roaming\3DModelManager\thumbnails\220f5e7474bb7c35df8390ffae72164d.png
INFO:DigitalWorkshop-Raw.src.core.thumbnail_components.thumbnail_generator_main:Generating thumbnail for: C:\path\to\model.stl
INFO:DigitalWorkshop-Raw.src.core.thumbnail_components.thumbnail_generator_main:Thumbnail generated successfully in 2.34s: C:\Users\Matthew\AppData\Roaming\3DModelManager\thumbnails\220f5e7474bb7c35df8390ffae72164d.png
```

## Additional Changes: Using Preferences

After the initial fix, I also updated the regenerate functions to **use the current thumbnail preferences** (material and background settings) when regenerating:

**Files Updated:**
1. **src/gui/model_library.py** - `_regenerate_thumbnail()` method
2. **src/gui/metadata_components/metadata_editor_main.py** - Preview generation
3. **src/gui/model_library_components/library_event_handler.py** - Context menu preview generation

**What Changed:**
- All regenerate operations now load thumbnail preferences from `QSettings`
- Preferences are passed to `generate_thumbnail()` as `material` and `background` parameters
- Thumbnails are regenerated with the **current user preferences**, not the original settings

**Code Pattern Used:**
```python
# Load thumbnail settings from preferences
from src.core.application_config import ApplicationConfig
from PySide6.QtCore import QSettings

config = ApplicationConfig.get_default()
settings = QSettings()

# Get current thumbnail preferences
bg_image = settings.value("thumbnail/background_image", config.thumbnail_bg_image, type=str)
material = settings.value("thumbnail/material", config.thumbnail_material, type=str)

# Generate with preferences
result = thumbnail_service.generate_thumbnail(
    model_path=model_path,
    file_hash=file_hash,
    material=material,
    background=bg_image,
    force_regenerate=True
)
```

## Impact

- **Backward Compatible**: Default behavior unchanged (`force_regenerate=False`)
- **Fixes User Issue**: Regenerate action now actually regenerates
- **Uses Preferences**: Thumbnails regenerate with current user settings
- **Consistent**: Same parameter handling across all regenerate operations
- **Unified**: All 3 regenerate locations now use the same preference loading pattern

