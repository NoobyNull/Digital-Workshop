# Thumbnail Generation & Skinning - Implementation Plan

**Branch:** `thumbnailing-skinning`  
**Status:** Core Architecture Complete, Integration Pending

## Overview

This document outlines the complete implementation plan for the thumbnail generation and material skinning system. The core architecture is complete; integration into the model library workflow remains.

## Completed Components ✅

### 1. Core Modules

- **`src/core/view_optimizer.py`** - Orthogonal view selection (0/90/180/270° with Z-up)
- **`src/core/thumbnail_generator.py`** - VTK offscreen rendering at 1080x1080
- **`src/core/material_provider.py`** - Dynamic texture discovery from materials folder
- **`src/core/background_provider.py`** - Dynamic background discovery
- **`src/core/application_config.py`** - Settings for bg color/image and material
- **`src/core/database_manager.py`** - Thumbs directory and thumbnail_path schema

### 2. Resource Structure

```
src/resources/
├── backgrounds/           # Dynamically discovered background images
│   ├── *.png
│   └── *.jpg
└── materials/            # Dynamically discovered material textures
    ├── oak_wood.png      # Texture image
    ├── oak_wood.mtl      # Material properties (optional)
    └── *.{png,jpg}       # Any textures installer/users add
```

### 3. Database Schema

```sql
-- Added to models table
ALTER TABLE models ADD COLUMN thumbnail_path TEXT;
CREATE INDEX idx_models_thumbnail_path ON models(thumbnail_path);

-- Thumbs directory: database_location/thumbs/
-- Filename format: <blake2_hash>.png (1080x1080)
```

## Integration Tasks (Remaining)

### Phase 1: Model Library Integration

**File:** `src/gui/model_library.py`

**Task 1.1: Add ThumbnailGenerator Initialization**
```python
from core.thumbnail_generator import ThumbnailGenerator
from core.background_provider import BackgroundProvider
from core.material_provider import MaterialProvider

class ModelLibraryWidget:
    def __init__(self, ...):
        # ... existing code ...
        self.thumbnail_generator = ThumbnailGenerator(settings_manager=self.settings)
        self.background_provider = BackgroundProvider(settings_manager=self.settings)
        self.material_provider = MaterialProvider()
```

**Task 1.2: Implement On-Demand Thumbnail Generation**
```python
def _get_thumbnail_for_model(self, model_data: Dict) -> QPixmap:
    """
    Get thumbnail for a model, generating if necessary.
    Returns scaled pixmap for grid view display.
    """
    # 1. Check database for existing thumbnail path
    thumbnail_path = self.db.get_thumbnail_path(model_data['id'])
    
    # 2. Validate thumbnail exists and is not corrupt
    if thumbnail_path and Path(thumbnail_path).exists():
        try:
            pixmap = QPixmap(thumbnail_path)
            if not pixmap.isNull():
                return self._scale_thumbnail(pixmap)
        except Exception:
            # Corrupt thumbnail, regenerate
            pass
    
    # 3. Generate new thumbnail
    thumbnail_path = self._generate_thumbnail(model_data)
    
    # 4. Load and scale
    if thumbnail_path:
        pixmap = QPixmap(str(thumbnail_path))
        return self._scale_thumbnail(pixmap)
    
    # 5. Fallback to placeholder icon
    return self._get_placeholder_icon()
```

**Task 1.3: Add Thumbnail Generation Method**
```python
def _generate_thumbnail(self, model_data: Dict) -> Optional[Path]:
    """Generate thumbnail for a model."""
    try:
        thumbs_dir = self.db.get_thumbs_directory()
        
        # Get preferences
        background = self.background_provider.get_background()
        material = self.settings.thumbnail_material if hasattr(self.settings, 'thumbnail_material') else None
        
        # Generate
        thumbnail_path = self.thumbnail_generator.generate_thumbnail(
            model_path=model_data['file_path'],
            file_hash=model_data['file_hash'],
            output_dir=thumbs_dir,
            background=background,
            material=material
        )
        
        # Update database
        if thumbnail_path:
            self.db.update_thumbnail_path(model_data['id'], str(thumbnail_path))
            
        return thumbnail_path
        
    except Exception as e:
        self.logger.error(f"Thumbnail generation failed: {e}")
        return None
```

**Task 1.4: Add Dynamic Scaling for Grid View**
```python
def _scale_thumbnail(self, pixmap: QPixmap, target_size: int = 256) -> QPixmap:
    """
    Scale full 1080x1080 thumbnail to display size.
    Uses smooth transformation for high quality.
    """
    return pixmap.scaled(
        target_size,
        target_size,
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation
    )

# Grid size options for user selection
GRID_SIZES = {
    'small': 128,
    'medium': 256,
    'large': 512
}
```

### Phase 2: Preferences UI Integration

**File:** `src/gui/preferences.py`

**Task 2.1: Add Thumbnail Settings Section**
```python
# Add to preferences dialog:
- Background Color Picker (with hex input)
- Background Image Browse Button
- Material Selection Dropdown (populated from MaterialProvider)
- Preview Panel showing current settings
```

**Task 2.2: Implement Material Selection UI**
```python
def _create_material_selector(self):
    """Create combo box with dynamically discovered materials."""
    material_combo = QComboBox()
    
    # Add "None" option
    material_combo.addItem("No Material", None)
    
    # Populate from MaterialProvider
    materials = self.material_provider.get_available_materials()
    for material in materials:
        display_name = material['name'].replace('_', ' ').title()
        material_combo.addItem(display_name, material['name'])
    
    return material_combo
```

**Task 2.3: Add Background Image Browser**
```python
def _browse_background_image(self):
    """Browse for custom background image."""
    # Show file dialog
    file_path, _ = QFileDialog.getOpenFileName(
        self,
        "Select Background Image",
        str(Path.home()),
        "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*.*)"
    )
    
    if file_path:
        self.settings.thumbnail_bg_image = file_path
        self._update_background_preview()
```

**Task 2.4: Add Default Background Gallery**
```python
def _create_default_backgrounds_gallery(self):
    """Show gallery of default backgrounds from resources."""
    gallery = QListWidget()
    
    # Populate from BackgroundProvider
    backgrounds = self.background_provider.get_default_backgrounds()
    for bg_path in backgrounds:
        item = QListWidgetItem(bg_path.stem)
        item.setData(Qt.UserRole, str(bg_path))
        
        # Add thumbnail preview
        icon = QIcon(str(bg_path))
        item.setIcon(icon)
        
        gallery.addItem(item)
    
    return gallery
```

### Phase 3: Batch Operations (Optional Enhancement)

**Task 3.1: Add Batch Thumbnail Generation**
```python
def regenerate_all_thumbnails(self, progress_callback=None):
    """
    Regenerate thumbnails for all models in library.
    Runs in background thread to avoid UI blocking.
    """
    models = self.db.get_all_models()
    total = len(models)
    
    for i, model in enumerate(models):
        try:
            # Delete existing thumbnail
            if model.get('thumbnail_path'):
                Path(model['thumbnail_path']).unlink(missing_ok=True)
            
            # Generate new thumbnail
            self._generate_thumbnail(model)
            
            # Progress callback
            if progress_callback:
                progress_callback(i + 1, total)
                
        except Exception as e:
            self.logger.error(f"Failed to regenerate thumbnail for {model['filename']}: {e}")
```

**Task 3.2: Add UI Button**
```python
# In model library toolbar:
regenerate_btn = QPushButton("Regenerate Thumbnails")
regenerate_btn.clicked.connect(self._on_regenerate_all_clicked)

def _on_regenerate_all_clicked(self):
    """Show confirmation and start batch regeneration."""
    reply = QMessageBox.question(
        self,
        "Regenerate Thumbnails",
        f"Regenerate thumbnails for all {len(models)} models?\n"
        "This may take several minutes.",
        QMessageBox.Yes | QMessageBox.No
    )
    
    if reply == QMessageBox.Yes:
        # Start background worker
        self._start_batch_regeneration()
```

### Phase 4: Error Handling & Recovery

**Task 4.1: Corrupt Thumbnail Detection**
```python
def _is_thumbnail_valid(self, thumbnail_path: Path) -> bool:
    """Check if thumbnail is valid and not corrupt."""
    try:
        if not thumbnail_path.exists():
            return False
            
        # Try to load as QPixmap
        pixmap = QPixmap(str(thumbnail_path))
        if pixmap.isNull():
            self.logger.warning(f"Corrupt thumbnail detected: {thumbnail_path}")
            return False
            
        # Check dimensions (should be 1080x1080)
        if pixmap.width() != 1080 or pixmap.height() != 1080:
            self.logger.warning(f"Invalid thumbnail dimensions: {pixmap.width()}x{pixmap.height()}")
            return False
            
        return True
        
    except Exception as e:
        self.logger.error(f"Error validating thumbnail: {e}")
        return False
```

**Task 4.2: Auto-Recovery**
```python
def _get_thumbnail_with_recovery(self, model_data: Dict) -> QPixmap:
    """Get thumbnail with automatic corruption recovery."""
    thumbnail_path_str = self.db.get_thumbnail_path(model_data['id'])
    
    if thumbnail_path_str:
        thumbnail_path = Path(thumbnail_path_str)
        
        # Check if valid
        if self._is_thumbnail_valid(thumbnail_path):
            pixmap = QPixmap(str(thumbnail_path))
            return self._scale_thumbnail(pixmap)
        else:
            # Corrupt or invalid - delete and regenerate
            self.logger.info(f"Regenerating corrupt thumbnail: {thumbnail_path}")
            thumbnail_path.unlink(missing_ok=True)
            self.db.update_thumbnail_path(model_data['id'], None)
    
    # Generate new thumbnail
    return self._get_thumbnail_for_model(model_data)
```

### Phase 5: Performance Optimization

**Task 5.1: Thumbnail Caching**
```python
class ThumbnailCache:
    """In-memory cache for scaled thumbnails."""
    
    def __init__(self, max_cache_mb: int = 100):
        self.cache: Dict[str, QPixmap] = {}
        self.max_size_bytes = max_cache_mb * 1024 * 1024
        self.current_size_bytes = 0
        
    def get(self, key: str, size: int) -> Optional[QPixmap]:
        """Get cached thumbnail at specific size."""
        cache_key = f"{key}_{size}"
        return self.cache.get(cache_key)
        
    def put(self, key: str, size: int, pixmap: QPixmap):
        """Cache scaled thumbnail."""
        cache_key = f"{key}_{size}"
        
        # Estimate pixmap size
        pixmap_bytes = pixmap.width() * pixmap.height() * 4  # RGBA
        
        # Evict if needed
        while self.current_size_bytes + pixmap_bytes > self.max_size_bytes and self.cache:
            # Remove oldest entry (FIFO)
            old_key = next(iter(self.cache))
            old_pixmap = self.cache.pop(old_key)
            self.current_size_bytes -= old_pixmap.width() * old_pixmap.height() * 4
        
        # Add to cache
        self.cache[cache_key] = pixmap
        self.current_size_bytes += pixmap_bytes
```

**Task 5.2: Lazy Loading**
```python
def _populate_grid_view(self):
    """Populate grid view with lazy thumbnail loading."""
    # Only generate thumbnails for visible items
    # Generate in background as user scrolls
    
    visible_range = self._get_visible_item_range()
    
    for i in visible_range:
        model = self.models[i]
        # Generate thumbnail in background thread
        self._queue_thumbnail_generation(model)
```

### Phase 6: User Workflow Features

**Task 6.1: Right-Click Context Menu**
```python
# Add to model library context menu:
- "Regenerate Thumbnail" - regenerate for selected model
- "Export Thumbnail..." - save thumbnail to user location
- "Change Thumbnail Material..." - apply different material
```

**Task 6.2: Material Preview**
```python
# In preferences or material picker:
def _show_material_preview(self, material_name: str):
    """Show preview of material on sample cube."""
    # Generate small preview using thumbnail system
    # Display in preferences dialog
```

## Implementation Checklist

### Core Integration (Essential)

- [ ] Initialize ThumbnailGenerator in ModelLibraryWidget.__init__
- [ ] Add _get_thumbnail_for_model() method with on-demand generation
- [ ] Implement _scale_thumbnail() for grid view display
- [ ] Add thumbnail validation and corruption detection
- [ ] Integrate into grid view item display
- [ ] Test with existing models in library

### Preferences UI (Essential)

- [ ] Add Thumbnail Settings tab to preferences
- [ ] Create background color picker widget
- [ ] Add background image browser button
- [ ] Create material selection dropdown (populated dynamically)
- [ ] Add preview panel for current settings
- [ ] Wire up save/apply functionality

### Performance (Recommended)

- [ ] Implement ThumbnailCache for scaled pixmaps
- [ ] Add lazy loading for grid view
- [ ] Queue thumbnail generation in background
- [ ] Add progress indicator for batch operations
- [ ] Monitor memory usage during generation

### User Features (Optional)

- [ ] Add "Regenerate Thumbnail" context menu item
- [ ] Add "Export Thumbnail" option
- [ ] Create material preview in preferences
- [ ] Add batch regeneration UI
- [ ] Implement thumbnail quality settings

## Testing Plan (Future)

### Unit Tests

- [ ] Test ViewOptimizer with various model geometries
- [ ] Test ThumbnailGenerator with different backgrounds
- [ ] Test MaterialProvider texture discovery
- [ ] Test database thumbnail_path CRUD operations
- [ ] Test corruption detection and recovery

### Integration Tests

- [ ] Test end-to-end thumbnail generation workflow
- [ ] Test grid view display with scaled thumbnails
- [ ] Test preferences UI changes apply correctly
- [ ] Test batch regeneration
- [ ] Test memory cleanup after generation

### Performance Tests

- [ ] Measure thumbnail generation time (target < 2s)
- [ ] Test memory usage during batch operations
- [ ] Verify no memory leaks after 20+ generations
- [ ] Test grid view scrolling performance

## Configuration Examples

### Basic Usage

```python
# Generate thumbnail with current settings
thumbs_dir = db.get_thumbs_directory()
background = bg_provider.get_background()
material = config.thumbnail_material

thumbnail_path = generator.generate_thumbnail(
    model_path="path/to/model.stl",
    file_hash="abc123...",
    output_dir=thumbs_dir,
    background=background,
    material=material
)
```

### Custom Background

```python
# Using solid color
generator.generate_thumbnail(..., background="#F0F0F0")

# Using image
generator.generate_thumbnail(..., background="path/to/bg.png")

# Using RGB tuple
generator.generate_thumbnail(..., background=(0.95, 0.95, 0.95))
```

### Material Selection

```python
# List available materials (dynamic)
materials = material_provider.get_available_materials()
for mat in materials:
    print(f"Material: {mat['name']}, Texture: {mat['texture_path']}")

# Apply material
generator.generate_thumbnail(..., material="oak_wood")
```

## Directory Structure After Implementation

```
database_location/
├── 3dmm.db
└── thumbs/
    ├── <hash1>.png (1080x1080)
    ├── <hash2>.png (1080x1080)
    └── ...

src/resources/
├── backgrounds/
│   ├── gradient_gray.png
│   ├── studio_white.jpg
│   └── ... (installer can add more)
└── materials/
    ├── oak_wood.png
    ├── oak_wood.mtl
    ├── walnut.png
    ├── walnut.mtl
    └── ... (installer can add more)
```

## Key Design Principles

### 1. Dynamic Discovery Everywhere
- **No hardcoded filenames**
- Background images: Scan backgrounds folder
- Material textures: Scan materials folder
- Installer adds files → System finds them automatically

### 2. Orthogonal Views Only
- Test angles: 0°, 90°, 180°, 270°
- Plus top view
- No isometric or diagonal views
- Z-up orientation (CAD standard)

### 3. Hash-Based Storage
- Filenames: `<blake2_hash>.png`
- Prevents duplicates automatically
- Same hash = same thumbnail
- Efficient storage

### 4. On-Demand Generation
- Generate when first accessed
- Skip if already exists
- Queue background generation
- No blocking UI

### 5. Graceful Degradation
- Missing texture → Default gray
- Missing background → Light gray
- Corrupt thumbnail → Auto-regenerate
- Generation failure → Placeholder icon

## Migration Notes

### Existing thumbnail system
If there's an existing thumbnail system in model_library.py:
1. Backup current implementation
2. Replace with new ThumbnailGenerator integration
3. Migrate existing thumbnails (optional):
   - Parse old thumbnail names
   - Re-key to hash-based naming
   - Or regenerate all

### Settings migration
Add to settings migration system:
```python
# In settings_migration.py
def migrate_v1_to_v2(old_settings):
    new_settings = old_settings.copy()
    
    # Add thumbnail defaults if missing
    if 'thumbnail_bg_color' not in new_settings:
        new_settings['thumbnail_bg_color'] = '#F5F5F5'
    if 'thumbnail_bg_image' not in new_settings:
        new_settings['thumbnail_bg_image'] = None
    if 'thumbnail_material' not in new_settings:
        new_settings['thumbnail_material'] = None
        
    return new_settings
```

## Performance Targets

- **Generation Time:** < 2 seconds per thumbnail
- **Grid View FPS:** > 30 FPS while scrolling
- **Memory Usage:** < 100 MB for 1000 cached scaled thumbnails
- **Batch Generation:** Progress feedback every 10 thumbnails

## Success Criteria

✅ Thumbnails generate at 1080x1080 resolution  
✅ Orthogonal views (0/90/180/270° + top) automatically selected  
✅ Backgrounds dynamically discovered from resources folder  
✅ Materials dynamically discovered from materials folder  
✅ Thumbnails stored in `database_location/thumbs/` as `<hash>.png`  
✅ Grid view scales thumbnails smoothly  
✅ No hardcoded resource names anywhere  
✅ Installer can add backgrounds/materials freely  
✅ Corruption auto-recovery works  
✅ Memory usage remains stable  

## Next Steps

1. **Review this implementation plan**
2. **Implement Phase 1** (Model Library Integration)
3. **Test with sample models**
4. **Implement Phase 2** (Preferences UI)
5. **Performance tuning** if needed
6. **Documentation for end users**

---

**Branch:** `thumbnailing-skinning`  
**Core:** Complete ✅  
**Integration:** Ready to implement  
**Testing:** Pending