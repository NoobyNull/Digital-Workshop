# Digital Workshop Resources

This directory contains resources used by Digital Workshop for thumbnail generation and UI customization.

## Directory Structure

```
resources/
├── backgrounds/       # Background images for thumbnails
├── materials/         # Wood material definitions and textures
├── icons/            # Application icons
├── README.md         # This file
├── license.txt       # License information
└── readme.txt        # Original readme
```

## Quick Start

### Adding Backgrounds

1. Place PNG images in `backgrounds/` directory
2. Filename becomes the display name (e.g., `Brick.png` → "Brick")
3. Recommended size: 1280x1280 pixels
4. See `backgrounds/README.md` for details

### Adding Materials

1. Create two files with the same name:
   - `MaterialName.mtl` - Material definition (Wavefront MTL format)
   - `MaterialName.png` - Preview texture image
2. Place both in `materials/` directory
3. See `materials/README.md` for details and examples

## Usage in Digital Workshop

### Thumbnail Settings

Access via: **Preferences → Content**

- **Background**: Click on background image to select
- **Material**: Click on material texture to select
- **Color**: Use color picker for solid background color

Selected background and material apply to all thumbnail generation operations.

## File Formats

### Backgrounds
- **PNG** (recommended) - Supports transparency
- **JPG/JPEG** - Good for photos
- **BMP** - Basic support

### Materials
- **MTL** (required) - Wavefront material definition
- **PNG** (required) - Preview texture image

## Examples

### Example Background
```
resources/backgrounds/Studio_White.png
```
- 1280x1280 pixels
- Plain white background
- Appears as "Studio White" in UI

### Example Material
```
resources/materials/Oak.mtl      # Material definition
resources/materials/Oak.png      # Preview texture
```
- MTL file defines color and properties
- PNG file shows in UI as preview
- Appears as "Oak" in material selector

## Best Practices

1. **Naming**: Use descriptive names with underscores for spaces
2. **Organization**: Keep similar items grouped
3. **Quality**: Use high-resolution images (1280x1280+)
4. **Size**: Keep files under 5MB for performance
5. **Consistency**: Match material colors to real-world references

## Troubleshooting

**Items not appearing?**
- Check file format (PNG for backgrounds, MTL+PNG for materials)
- Verify filenames have no special characters
- Ensure files are in correct directory
- Restart Digital Workshop to refresh

**Preview not showing?**
- For materials: Ensure `.png` file exists with same name as `.mtl`
- Check file is not corrupted
- Verify file permissions

## Resources

### Free Texture Sources
- **Poly Haven** (polyhaven.com) - CC0 textures and HDRIs
- **Texture.com** - Free texture library
- **Pixabay** - Free stock photos
- **Unsplash** - High-quality photography

### Material References
- **Wood Database** (wood-database.com) - Wood species info
- **Material Library** - Common MTL format examples

## Support

For more information:
- See individual README files in subdirectories
- Check Digital Workshop documentation
- Visit project repository for updates

## License

See `license.txt` for licensing information.

