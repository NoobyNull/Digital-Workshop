# Rendering Backgrounds Issue

**Status**: ❌ NOT WORKING  
**Date Started**: 2025-11-05  
**Last Updated**: 2025-11-05 06:46

---

## Problem Description

Thumbnail background images are not rendering in generated thumbnails. When a background image (e.g., "Brick.png") is selected in preferences and a thumbnail is generated, the background appears as solid black instead of the expected texture.

### Expected Behavior
- User selects "Brick" background in Preferences → Thumbnail Settings
- Thumbnail is generated with brick texture as background
- Background image appears behind the 3D model

### Actual Behavior
- Thumbnail is generated with solid black background
- Background texture is not visible
- Logs show background image path is loaded correctly

---

## Investigation Timeline

### Initial Diagnosis (06:14 - 06:19)

**Findings:**
1. Settings ARE being loaded correctly from QSettings
2. Background path exists: `D:\Digital Workshop\src\resources\backgrounds\Brick.png`
3. Thumbnail generation logs show: "Background image exists, using: D:\...\Brick.png"
4. But thumbnail still has black background

**Test Results:**
```python
# Brick texture analysis
Image size: (1024, 1024)
Image mode: RGBA
Brick top-left corner: (120, 84, 69, 255)  # Reddish-brown
Brick center pixel: (123, 76, 67, 255)

# Generated thumbnail analysis
Image size: (1280, 1280)
Image mode: RGB
Unique colors: 37244
Top-left corner pixel: (0, 0, 0)  # BLACK - background not rendered!
```

---

## Troubleshooting Steps & Fixes Attempted

### Fix #1: VTK Texture Application Method (FAILED)

**Issue Identified:**
- Line 171 in `src/core/vtk_rendering_engine.py` used incorrect VTK API
- `actor.GetProperty().SetTexture("map_d", texture)` is for PBR materials only

**Fix Applied:**
```python
# Before (WRONG):
actor.GetProperty().SetTexture("map_d", texture)

# After (CORRECT):
actor.SetTexture(texture)
```

**File Modified:** `src/core/vtk_rendering_engine.py` (line 171)

**Result:** ❌ Still not working

---

### Fix #2: VTK Texture Coordinates (FAILED)

**Issue Identified:**
- Background plane had no UV texture coordinates
- VTK needs texture coordinates to map texture onto geometry

**Fix Applied:**
Added texture coordinate generation in `src/core/vtk_rendering_engine.py` (lines 157-197):

```python
# Generate texture coordinates for the plane
plane_output = plane.GetOutput()
num_points = plane_output.GetNumberOfPoints()

# Create texture coordinates array
tcoords = vtk.vtkFloatArray()
tcoords.SetNumberOfComponents(2)
tcoords.SetNumberOfTuples(num_points)
tcoords.SetName("TextureCoordinates")

# Set UV coordinates for each point (4 corners of the plane)
tcoords.SetTuple2(0, 0.0, 0.0)  # Bottom-left
tcoords.SetTuple2(1, 1.0, 0.0)  # Bottom-right
tcoords.SetTuple2(2, 0.0, 1.0)  # Top-left
tcoords.SetTuple2(3, 1.0, 1.0)  # Top-right

# Add texture coordinates to the plane
plane_output.GetPointData().SetTCoords(tcoords)

mapper = vtk.vtkPolyDataMapper()
mapper.SetInputData(plane_output)
```

**File Modified:** `src/core/vtk_rendering_engine.py` (lines 157-197)

**Result:** ❌ Still not working

---

### Fix #3: Library View Thumbnail Refresh (SUCCESS ✅)

**Issue Identified:**
- Qt's `QPixmapCache` was caching old thumbnail images
- Library view wasn't refreshing after thumbnail regeneration

**Fix Applied:**
Modified `src/gui/model_library/widget.py` (lines 173-208):

```python
def _refresh_model_display(self, model_id: Optional[int] = None) -> None:
    if model_id is not None:
        # Clear Qt's pixmap cache to force reload
        QPixmapCache.clear()
        
        # Get updated model from database
        updated_model = self.db_manager.get_model(model_id)
        if updated_model:
            thumbnail_path = updated_model.get("thumbnail_path")
            if thumbnail_path and Path(thumbnail_path).exists():
                # Find and update the specific item
                for row in range(self.list_model.rowCount()):
                    item = self.list_model.item(row, 0)
                    if item and item.data(Qt.UserRole) == model_id:
                        icon = QIcon(thumbnail_path)
                        item.setIcon(icon)
                        break
```

**Files Modified:**
- `src/gui/model_library/widget.py` (lines 173-208)

**Result:** ✅ Library view now refreshes correctly (but background still not rendering)

---

### Fix #4: Background Name Parsing (PARTIAL SUCCESS ⚠️)

**Issue Identified:**
- Materials use `MaterialProvider` to resolve names → paths
- Backgrounds stored ABSOLUTE PATHS in preferences
- No `BackgroundProvider` to resolve background names

**User's Key Insight:**
> "I seen there is a lot of parsing for materials, why is there no parsing for backgrounds? Shouldn't only the item in preferences be parsed?"

**Fix Applied:**

#### 4.1 Enhanced BackgroundProvider
Added name-based lookup methods to `src/core/background_provider.py` (lines 71-192):

```python
def get_background_by_name(self, name: str) -> Path:
    """Get background path by name (without extension)."""
    # Try PNG first
    png_path = self.DEFAULT_BACKGROUNDS_DIR / f"{name}.png"
    if png_path.exists():
        return png_path
    
    # Try JPG
    jpg_path = self.DEFAULT_BACKGROUNDS_DIR / f"{name}.jpg"
    if jpg_path.exists():
        return jpg_path
    
    # Try JPEG
    jpeg_path = self.DEFAULT_BACKGROUNDS_DIR / f"{name}.jpeg"
    if jpeg_path.exists():
        return jpeg_path
    
    raise FileNotFoundError(f"Background '{name}' not found")
```

**Test Results:**
```
Brick -> D:\Digital Workshop\src\resources\backgrounds\Brick.png
Blue -> D:\Digital Workshop\src\resources\backgrounds\Blue.png
Gray -> D:\Digital Workshop\src\resources\backgrounds\Gray.png
```
✅ Name resolution works correctly

#### 4.2 Updated Preferences to Store Names
Modified `src/gui/preferences/tabs/thumbnail_settings_tab.py` (line 212):

```python
# Before: Store full path
item.setData(Qt.UserRole, str(bg_file))

# After: Store only name
item.setData(Qt.UserRole, bg_file.stem)
```

#### 4.3 Added Backward Compatibility
Modified `src/gui/preferences/tabs/thumbnail_settings_tab.py` (lines 266-285):

```python
# Handle both old format (full path) and new format (name only)
if "/" in bg_image or "\\" in bg_image:
    # Old format: full path like "D:\...\Brick.png"
    bg_name = Path(bg_image).stem
else:
    # New format: just the name like "Brick"
    bg_name = bg_image
```

#### 4.4 Updated Thumbnail Generator
Modified `src/core/thumbnail_components/thumbnail_generator_main.py` (lines 302-340):

```python
# Resolve background name to path using BackgroundProvider
from src.core.background_provider import BackgroundProvider
bg_provider = BackgroundProvider()

try:
    # Try to resolve as a background name
    resolved_path = bg_provider.get_background_by_name(background)
    self.logger.info("Resolved background '%s' to: %s", background, resolved_path)
    engine.set_background_image(str(resolved_path))
except FileNotFoundError:
    # Not a valid background name, check if it's a path
    if Path(background).exists():
        engine.set_background_image(background)
```

**Files Modified:**
- `src/core/background_provider.py` (lines 71-192)
- `src/gui/preferences/tabs/thumbnail_settings_tab.py` (lines 212, 266-285)
- `src/core/thumbnail_components/thumbnail_generator_main.py` (lines 302-340)

**Result:** ⚠️ Name resolution works, but background still not rendering

---

### Fix #5: Trimesh Loader Bug (SUCCESS ✅)

**Issue Identified:**
- Trimesh loader referenced non-existent `ModelFormat.PLY`, `OFF`, `GLB`, `GLTF`
- Caused crash: `AttributeError: type object 'ModelFormat' has no attribute 'PLY'`

**Fix Applied:**
Modified `src/parsers/trimesh_loader.py` (lines 195-201):

```python
# Before:
format_map = {
    '.stl': ModelFormat.STL,
    '.obj': ModelFormat.OBJ,
    '.3mf': ModelFormat.THREE_MF,
    '.ply': ModelFormat.PLY,  # ❌ Doesn't exist
    '.off': ModelFormat.OFF,  # ❌ Doesn't exist
    '.glb': ModelFormat.GLB,  # ❌ Doesn't exist
    '.gltf': ModelFormat.GLTF,  # ❌ Doesn't exist
}

# After:
format_map = {
    '.stl': ModelFormat.STL,
    '.obj': ModelFormat.OBJ,
    '.3mf': ModelFormat.THREE_MF,
    # Note: PLY, OFF, GLB, GLTF not in ModelFormat enum yet
    # These will use ModelFormat.UNKNOWN
}
```

**File Modified:** `src/parsers/trimesh_loader.py` (lines 195-201)

**Result:** ✅ Trimesh no longer crashes

---

## Current Status

### What's Working ✅
1. Background name resolution (`BackgroundProvider.get_background_by_name()`)
2. Library view thumbnail refresh (Qt pixmap cache clearing)
3. Trimesh loader (no more PLY crash)
4. Settings save/load with backward compatibility
5. Background path validation

### What's NOT Working ❌
1. **Background texture rendering in VTK** - This is the core issue
2. Thumbnails still show solid black background instead of texture

---

## Technical Details

### VTK Rendering Pipeline

Current implementation in `src/core/vtk_rendering_engine.py`:

```python
def set_background_image(self, image_path: str) -> None:
    # 1. Load texture
    reader = vtk.vtkPNGReader()
    reader.SetFileName(image_path)
    reader.Update()
    
    # 2. Create texture
    texture = vtk.vtkTexture()
    texture.SetInputConnection(reader.GetOutputPort())
    texture.InterpolateOn()
    texture.EdgeClampOn()
    texture.RepeatOn()
    
    # 3. Create background plane
    plane = vtk.vtkPlaneSource()
    plane.SetOrigin(-scale, -scale, cam_focal[2] - distance * 1.5)
    plane.SetPoint1(scale, -scale, cam_focal[2] - distance * 1.5)
    plane.SetPoint2(-scale, scale, cam_focal[2] - distance * 1.5)
    plane.SetResolution(1, 1)
    plane.Update()
    
    # 4. Generate texture coordinates
    plane_output = plane.GetOutput()
    tcoords = vtk.vtkFloatArray()
    tcoords.SetNumberOfComponents(2)
    tcoords.SetNumberOfTuples(4)
    tcoords.SetName("TextureCoordinates")
    tcoords.SetTuple2(0, 0.0, 0.0)
    tcoords.SetTuple2(1, 1.0, 0.0)
    tcoords.SetTuple2(2, 0.0, 1.0)
    tcoords.SetTuple2(3, 1.0, 1.0)
    plane_output.GetPointData().SetTCoords(tcoords)
    
    # 5. Create mapper and actor
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(plane_output)
    
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.SetTexture(texture)
    actor.GetProperty().LightingOff()
    actor.GetProperty().SetOpacity(1.0)
    
    # 6. Add to renderer
    self.renderer.AddActor(actor)
```

### Logs Show Correct Path Resolution

```
[2025-11-05 06:19:40] DEBUG | thumbnail_generator_main | Background is string: D:\Digital Workshop\src\resources\backgrounds\Brick.png
[2025-11-05 06:19:40] INFO  | thumbnail_generator_main | Background image exists, using: D:\Digital Workshop\src\resources\backgrounds\Brick.png
[2025-11-05 06:19:40] DEBUG | vtk_rendering_engine | Background image set: D:\Digital Workshop\src\resources\backgrounds\Brick.png
```

But thumbnail still has black background.

---

## Possible Root Causes (To Investigate)

1. **VTK Plane Positioning**
   - Plane might be positioned behind camera's far clipping plane
   - Z-depth ordering might be incorrect
   - Plane might be too far behind the model

2. **VTK Texture Coordinate Ordering**
   - UV coordinates might not match plane vertex order
   - VTK might expect different coordinate system

3. **VTK Renderer Settings**
   - Depth testing might be culling the background plane
   - Renderer layers might be incorrect
   - Background plane might need different render order

4. **Offscreen Rendering Issues**
   - VTK offscreen rendering might not support textured backgrounds
   - Render window settings might be missing

5. **Texture Format Issues**
   - RGBA vs RGB mismatch
   - Texture might need different VTK reader settings

---

## Next Steps (Recommendations)

1. **Test with Simple VTK Example**
   - Create minimal VTK script to render textured plane
   - Verify VTK texture mapping works in isolation

2. **Check VTK Plane Vertex Order**
   - Log plane vertices and texture coordinates
   - Verify they match expected order

3. **Test Background Plane Visibility**
   - Render ONLY the background plane (no model)
   - Check if plane is visible at all

4. **Compare with Working Material Textures**
   - Materials ARE rendering correctly
   - Compare material texture code vs background texture code
   - Identify differences in approach

5. **Check VTK Documentation**
   - Review VTK texture mapping examples
   - Check if offscreen rendering needs special handling

---

## Files Modified

### Core Files
- `src/core/vtk_rendering_engine.py` (lines 157-197, 171)
- `src/core/background_provider.py` (lines 71-192)
- `src/core/thumbnail_components/thumbnail_generator_main.py` (lines 302-340)

### GUI Files
- `src/gui/model_library/widget.py` (lines 173-208)
- `src/gui/preferences/tabs/thumbnail_settings_tab.py` (lines 212, 266-285)

### Parser Files
- `src/parsers/trimesh_loader.py` (lines 195-201)

---

## Related Issues

- Materials render correctly with textures
- Background colors (solid colors) work fine
- Only background images fail to render

---

## References

- VTK Documentation: https://vtk.org/doc/nightly/html/classvtkTexture.html
- VTK Texture Mapping: https://vtk.org/Wiki/VTK/Examples/Cxx/Texture/TexturePlane

