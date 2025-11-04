# Thumbnail Generator vs Screenshot Generator

## Quick Comparison

| Feature | Thumbnail Generator | Screenshot Generator |
|---------|-------------------|----------------------|
| **Location** | `src/core/thumbnail_components/thumbnail_generator_main.py` | `src/gui/screenshot_generator.py` |
| **Purpose** | Generate cached thumbnails for model library | Generate live screenshots for UI preview |
| **Default Size** | 1080x1080 (high quality) | 256x256 (preview size) |
| **Caching** | ✅ YES - Hash-based, persistent | ❌ NO - Temp files only |
| **View Selection** | ✅ YES - Auto best view (ViewOptimizer) | ❌ NO - Default view only |
| **Camera Zoom** | ✅ YES - 1.05 (5% padding) | ❌ NO - ResetCamera() only |
| **Material Support** | ✅ YES - MaterialManager | ✅ YES - MaterialManager |
| **Background Image** | ✅ YES - Dynamic plane sizing | ✅ YES - Dynamic plane sizing |
| **Lighting** | ✅ Studio lighting (ambient + directional) | ✅ Basic lighting |
| **Render Passes** | 1 pass | 2 passes (texture fix) |
| **Settings Integration** | ✅ YES - Uses settings_manager | ❌ NO - Standalone |

## Detailed Differences

### 1. **Purpose & Use Case**
- **Thumbnail**: Persistent storage for model library display. Generated once, cached, reused.
- **Screenshot**: Live preview in UI. Generated on-demand, temporary, not cached.

### 2. **Size & Quality**
- **Thumbnail**: 1080x1080 - High quality for library display
- **Screenshot**: 256x256 - Smaller for quick UI preview

### 3. **View Selection**
- **Thumbnail**: Uses `ViewOptimizer` to find the best orthogonal view (front, back, left, right)
- **Screenshot**: Uses `ResetCamera()` - default view only

### 4. **Camera Zoom**
- **Thumbnail**: `camera.Zoom(1.05)` - Zooms OUT by 5% for padding
- **Screenshot**: No zoom - Model may touch viewport edges

### 5. **Rendering Sequence**
- **Thumbnail**: 
  1. Add model actor
  2. Setup camera
  3. Setup lighting
  4. Add background (LAST - renders behind)
  5. Single render pass

- **Screenshot**:
  1. Add background (FIRST)
  2. Add model actor
  3. Setup lighting
  4. Setup camera
  5. Double render pass (texture fix)

### 6. **Material Application**
- **Thumbnail**: Uses MaterialManager with single render pass
- **Screenshot**: Uses MaterialManager with double render pass (ensures texture mapping)

### 7. **Background Handling**
Both now use dynamic plane sizing:
- Calculate camera distance
- Scale plane to `max(distance * 2.0, 500.0)`
- Position at `cam_focal[2] - distance * 1.5`

### 8. **Settings Integration**
- **Thumbnail**: Accepts `settings_manager` parameter, uses preferences
- **Screenshot**: Standalone, no settings integration

## Why Two Generators?

1. **Different Performance Requirements**
   - Thumbnails: High quality, cached, can be slow
   - Screenshots: Fast, for live UI feedback

2. **Different Use Cases**
   - Thumbnails: Library display, persistent
   - Screenshots: UI preview, temporary

3. **Different Rendering Needs**
   - Thumbnails: Best view selection, optimal framing
   - Screenshots: Quick preview, default view

## Recent Fixes Applied to Both

✅ **Camera Zoom**: Added 1.05 zoom factor to thumbnail generator
✅ **Background Plane**: Dynamic sizing based on camera distance
✅ **Rendering Order**: Background set after model/camera setup
✅ **Texture Repeat**: Enabled for seamless background coverage

## Which One Should I Use?

- **Use Thumbnail Generator** for:
  - Model library display
  - Persistent cached images
  - High quality output
  - Best view selection

- **Use Screenshot Generator** for:
  - Live UI preview
  - Quick temporary screenshots
  - Specific viewport size
  - Real-time feedback

