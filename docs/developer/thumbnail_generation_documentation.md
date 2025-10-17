# Thumbnail Generation System Documentation

## Overview

The thumbnail generation system creates high-quality 1080x1080 PNG thumbnails for 3D models using VTK offscreen rendering with automatic best view detection and customizable backgrounds and materials.

## Architecture Components

### 1. ViewOptimizer (`src/core/view_optimizer.py`)

**Purpose:** Find the optimal orthogonal viewing angle for 3D model thumbnails.

**Key Features:**
- Tests orthogonal views only: 0°, 90°, 180°, 270° (front, right, back, left) and top view
- Z-up orientation for professional appearance
- Scores views based on visible surface area and balance
- No isometric or angled views - only face-on orthogonal angles

**API:**

```python
from core.view_optimizer import ViewOptimizer

optimizer = ViewOptimizer()

# Find best view for model bounds
camera_params = optimizer.find_best_orthogonal_view(
    bounds=(xmin, xmax, ymin, ymax, zmin, zmax),
    prefer_front=True  # Prefer front view when scores are equal
)

# Returns CameraParameters with:
# - position: (x, y, z)
# - focal_point: (x, y, z)
# - view_up: (x, y, z)
# - distance: float
# - view_name: 'front', 'right', 'back', 'left', or 'top'
```

**View Scoring:**
- **40%** Visible surface area
- **30%** Aspect ratio balance (prefer square-ish views)
- **20%** Consistency (slight preference for front/right views)
- **10%** Feature prominence

### 2. ThumbnailGenerator (`src/core/thumbnail_generator.py`)

**Purpose:** Generate 1080x1080 PNG thumbnails using VTK offscreen rendering.

**Key Features:**
- Offscreen rendering (no UI window)
- 1080x1080 resolution (1:1 ratio)
- BLAKE2 hash-based file naming
- Automatic best view detection
- Support for custom backgrounds (solid colors or images)
- Optional material/texture application
- Duplicate detection (skips if thumbnail exists)
- Memory-efficient cleanup

**API:**

```python
from core.thumbnail_generator import ThumbnailGenerator
from pathlib import Path

# Initialize with optional managers
generator = ThumbnailGenerator(
    settings_manager=app_config,
    database_manager=db_manager
)

# Generate thumbnail
thumbnail_path = generator.generate_thumbnail(
    model_path="path/to/model.stl",
    file_hash="abc123...",  # BLAKE2 hash
    output_dir=Path("database/thumbs"),
    background="#FFFFFF",  # Or RGB tuple (1.0, 1.0, 1.0), or image path
    size=(1080, 1080),  # Optional, defaults to 1080x1080
    material="Oak"  # Optional wood species name
)

# Returns Path to PNG or None on failure
```

**Background Options:**
- Hex color string: `"#F5F5F5"`
- RGB tuple (0-1): `(0.96, 0.96, 0.96)`
- Image path: `"path/to/background.png"`
- `None`: Uses settings preference

**Material Options:**
- Material name: Any texture filename from `src/resources/materials/` (without extension)
- Examples: `"oak_wood"`, `"seamless_oak_wood_texture_with_fine_grain"`
- System dynamically discovers all available materials
- `None`: Uses default gray appearance

### 3. BackgroundProvider (`src/core/background_provider.py`)

**Purpose:** Manage thumbnail background preferences with dynamic resource discovery.

**Key Features:**
- Dynamically scans `src/resources/backgrounds/` directory
- No hardcoded filenames - works with any images added
- Supports hex colors, RGB tuples, and image files
- Validates image paths and formats

**API:**

```python
from core.background_provider import BackgroundProvider

provider = BackgroundProvider(settings_manager=app_config)

# Get current background preference
background = provider.get_background()
# Returns: hex string, RGB tuple, or image path

# List all default background images (dynamic discovery)
backgrounds = provider.get_default_backgrounds()
# Returns: List[Path] - all PNG/JPG files in backgrounds folder

# Set preferences
provider.set_background_color("#FFFFFF")  # Or RGB tuple
provider.set_background_image("path/to/image.png")
provider.clear_background_image()  # Revert to color
```

## Configuration Settings

Settings are stored in `src/core/application_config.py`:

```python
@dataclass
class ApplicationConfig:
    # Thumbnail Generation Configuration
    thumbnail_bg_color: str = "#F5F5F5"  # Light gray default
    thumbnail_bg_image: Optional[str] = None  # Custom image path
    thumbnail_material: Optional[str] = None  # Wood species name
```

## Database Schema

The thumbnail system adds the following to the `models` table:

```sql
CREATE TABLE models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    format TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    file_hash TEXT,
    thumbnail_path TEXT,  -- NEW: Path to generated thumbnail
    date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_modified DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_models_thumbnail_path ON models(thumbnail_path);
```

**Database Methods:**

```python
# Get thumbs directory (creates if doesn't exist)
thumbs_dir = db.get_thumbs_directory()
# Returns: database_location/thumbs/

# Update thumbnail path for a model
success = db.update_thumbnail_path(model_id, "thumbs/abc123.png")

# Get thumbnail path
thumbnail_path = db.get_thumbnail_path(model_id)
```

## Directory Structure

```
database_location/
├── 3dmm.db
└── thumbs/
    ├── <blake2_hash_1>.png  (1080x1080)
    ├── <blake2_hash_2>.png
    └── <blake2_hash_3>.png
```

## Workflow Example

```python
from core.thumbnail_generator import ThumbnailGenerator
from core.background_provider import BackgroundProvider
from core.database_manager import get_database_manager

# Initialize components
db = get_database_manager()
bg_provider = BackgroundProvider(settings_manager=config)
generator = ThumbnailGenerator(
    settings_manager=config,
    database_manager=db
)

# Generate thumbnail
thumbs_dir = db.get_thumbs_directory()
background = bg_provider.get_background()
material = config.thumbnail_material

thumbnail_path = generator.generate_thumbnail(
    model_path=model.file_path,
    file_hash=model.file_hash,
    output_dir=thumbs_dir,
    background=background,
    material=material
)

if thumbnail_path:
    # Update database
    db.update_thumbnail_path(model.id, str(thumbnail_path))
    print(f"Thumbnail generated: {thumbnail_path}")
```

## Performance Characteristics

**Target Performance:**
- Generation time: < 2 seconds per thumbnail
- Resolution: Fixed 1080x1080 for quality
- Memory usage: Efficient VTK resource cleanup
- Duplicate detection: Skips generation if file exists

**Optimization Features:**
- Offscreen rendering (no display overhead)
- Automatic VTK resource cleanup with `gc.collect()`
- Texture caching in MaterialManager
- Fast array-based polydata construction

## Material System Integration

The thumbnail generator integrates with the existing `MaterialManager` to apply procedural wood textures.

**Available Wood Species (Dynamic from Database):**
- Oak (default)
- Walnut
- Cherry
- Maple
- Pine
- Custom species added by users

**Material Features:**
- Procedural grain generation (ring or straight patterns)
- Realistic wood appearance with grain variation
- PBR shading when supported
- Texture caching for performance

## Background System

**Dynamic Resource Discovery:**
- System automatically finds all PNG/JPG files in `src/resources/backgrounds/`
- No code changes needed when adding new backgrounds
- Installer can include default backgrounds
- Users can add custom backgrounds to resources folder

**Supported Background Types:**
1. **Solid Colors**
   - Hex strings: `"#F5F5F5"`, `"#FFFFFF"`
   - RGB tuples (0-1): `(0.96, 0.96, 0.96)`
   - RGB tuples (0-255): `(245, 245, 245)`

2. **Images**
   - PNG, JPG, JPEG, BMP formats
   - Any resolution (will be fitted to viewport)
   - Default images in `src/resources/backgrounds/`
   - Custom user images anywhere

## Usage in Model Library

The thumbnail generation is designed for on-demand usage:

```python
# Check if thumbnail exists
thumbnail_path = db.get_thumbnail_path(model.id)

if thumbnail_path and Path(thumbnail_path).exists():
    # Load existing thumbnail
    pixmap = QPixmap(thumbnail_path)
else:
    # Generate new thumbnail
    thumbs_dir = db.get_thumbs_directory()
    thumbnail_path = generator.generate_thumbnail(
        model_path=model.file_path,
        file_hash=model.file_hash,
        output_dir=thumbs_dir
    )
    if thumbnail_path:
        db.update_thumbnail_path(model.id, str(thumbnail_path))
        pixmap = QPixmap(str(thumbnail_path))

# Scale for grid view display
scaled_pixmap = pixmap.scaled(
    256, 256,  # Display size
    Qt.KeepAspectRatio,
    Qt.SmoothTransformation
)
```

## Error Handling

The system includes comprehensive error handling:

**Graceful Degradation:**
- Missing model → Log error, return None
- Corrupt thumbnail → Auto-delete and regenerate
- Invalid background → Fall back to default gray
- Material not found → Use default appearance
- VTK rendering failure → Return None with logging

**Logging:**
- Generation time tracking
- Success/failure status
- View selection decisions
- Material application results
- Error details with stack traces

## Best Practices

1. **Check for Existing Thumbnails First**
   ```python
   if not Path(thumbnail_path).exists():
       generate_thumbnail(...)
   ```

2. **Use Hash-Based Naming**
   ```python
   # Thumbnails named by BLAKE2 hash prevent duplicates
   filename = f"{model.file_hash}.png"
   ```

3. **Scale Thumbnails for Display**
   ```python
   # Always scale from full 1080x1080 for display
   # Never scale before saving
   display_pixmap = full_pixmap.scaled(size, Qt.SmoothTransformation)
   ```

4. **Handle Missing Resources**
   ```python
   # System falls back gracefully
   # Always check return values
   if thumbnail_path is None:
       use_placeholder_icon()
   ```

## Future Enhancements

Potential improvements for future versions:

- **Multi-Format Support:** Extend beyond STL to OBJ, STEP, 3MF
- **Batch Generation:** UI for regenerating all thumbnails
- **Custom Views:** Save user-preferred camera angles per model
- **Resolution Options:** Allow 512x512 or 2048x2048 in settings
- **Render Quality:** Progressive quality options
- **Material Presets:** Save favorite material combinations

## Troubleshooting

### Thumbnail Not Generated

**Symptoms:** `generate_thumbnail()` returns None

**Causes:**
1. Model file not found or corrupt
2. Insufficient permissions for thumbs directory
3. VTK rendering failure
4. Out of memory

**Solutions:**
- Check logs for detailed error messages
- Verify file paths and permissions
- Ensure VTK is properly installed
- Monitor memory usage

### Incorrect View Angle

**Symptoms:** Thumbnail shows wrong side of model

**Causes:**
1. Model has unusual dimensions
2. View scoring prefers different angle

**Solutions:**
- Check model bounds in logs
- Review view scores for each angle
- Adjust `prefer_front` parameter if needed

### Material Not Applied

**Symptoms:** Thumbnail shows gray model instead of wood texture

**Causes:**
1. MaterialManager not initialized
2. Species name not in database
3. Database connection issue

**Solutions:**
- Pass database_manager to ThumbnailGenerator
- Verify species name exists: `db.get_wood_materials()`
- Check material application logs

### Background Not Applied

**Symptoms:** Thumbnail has wrong background

**Causes:**
1. Invalid color format
2. Image file not found
3. Settings not loaded

**Solutions:**
- Use hex format: `"#F5F5F5"`
- Verify image path exists
- Check settings_manager initialization