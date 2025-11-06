# Thumbnail Materials

This directory contains wood material definitions and textures used for thumbnail generation in Digital Workshop.

## Adding New Materials

Each material requires **TWO files** with the **same name**:

1. **Material Definition** (`.mtl` file) - Defines material properties
2. **Material Texture** (`.png` file) - Visual preview image

### Example:
```
resources/materials/
├── Oak.mtl           → Material definition
├── Oak.png           → Texture preview (shown in UI)
├── Walnut.mtl        → Material definition
├── Walnut.png        → Texture preview (shown in UI)
└── Cherry.mtl        → Material definition
    Cherry.png        → Texture preview (shown in UI)
```

## Material Definition File (.mtl)

The `.mtl` file uses Wavefront MTL format. Here's a basic template:

```mtl
# Material: Oak
newmtl Oak
Ka 0.8 0.6 0.4        # Ambient color (RGB 0-1)
Kd 0.8 0.6 0.4        # Diffuse color (RGB 0-1)
Ks 0.3 0.3 0.3        # Specular color (RGB 0-1)
Ns 50.0               # Specular exponent (shininess)
d 1.0                 # Transparency (1.0 = opaque)
illum 2               # Illumination model
map_Kd Oak_texture.jpg  # Optional: Path to texture image
```

### Material Properties Explained:

- **Ka** (Ambient): Base color in shadow
- **Kd** (Diffuse): Main surface color
- **Ks** (Specular): Highlight color (usually gray/white)
- **Ns** (Shininess): 0-1000, higher = shinier
- **d** (Transparency): 0.0 (transparent) to 1.0 (opaque)
- **illum**: Illumination model (2 = standard)
- **map_Kd**: Optional texture map file

## Material Texture File (.png)

The `.png` file is the visual preview shown in the UI:

- **Format**: PNG (recommended)
- **Size**: 256x256 pixels or larger
- **Content**: Representative sample of the wood grain/texture
- **Naming**: Must match the `.mtl` filename exactly

### Example:
- `Oak.mtl` → `Oak.png`
- `Walnut.mtl` → `Walnut.png`

## Common Wood Material Examples

### Light Woods:
```mtl
# Pine
newmtl Pine
Ka 0.9 0.8 0.6
Kd 0.9 0.8 0.6
Ks 0.2 0.2 0.2
Ns 30.0
```

### Medium Woods:
```mtl
# Oak
newmtl Oak
Ka 0.8 0.6 0.4
Kd 0.8 0.6 0.4
Ks 0.3 0.3 0.3
Ns 50.0
```

### Dark Woods:
```mtl
# Walnut
newmtl Walnut
Ka 0.4 0.3 0.2
Kd 0.4 0.3 0.2
Ks 0.4 0.4 0.4
Ns 70.0
```

## How It Works

1. All `.mtl` files in this directory are automatically detected
2. Matching `.png` files are used as preview images in the UI
3. Materials appear as clickable buttons in Preferences → Content
4. Selected material is applied to all thumbnail generation
5. The material properties affect how the 3D model is rendered

## Best Practices

- **Naming**: Use wood species names (Oak, Walnut, Cherry, etc.)
- **Colors**: Match RGB values to real wood colors
- **Shininess**: Wood is typically 30-70 (not too shiny)
- **Textures**: Use high-quality wood grain images for previews
- **Consistency**: Keep similar woods grouped (light, medium, dark)

## Finding Wood Textures

Free texture sources:
- **Texture Haven** (polyhaven.com) - CC0 textures
- **Texture.com** - Free wood textures
- **Pixabay** - Free stock photos of wood
- **Unsplash** - High-quality wood photos

## Troubleshooting

**Material not appearing?**
- Ensure both `.mtl` and `.png` files exist
- Check filenames match exactly (case-sensitive)
- Verify `.mtl` file has valid MTL format
- Restart Digital Workshop to refresh the list

**Material looks wrong in thumbnails?**
- Adjust Ka/Kd values for correct color
- Increase Ns for more shine, decrease for matte
- Check illum value (should be 2 for standard)

**No preview image?**
- Ensure `.png` file exists with same name as `.mtl`
- Check PNG file is valid and not corrupted
- Use square aspect ratio for best results

## Advanced: Custom Textures

To use actual texture maps in materials:

1. Add texture image to this directory (e.g., `Oak_texture.jpg`)
2. Reference it in the `.mtl` file:
   ```mtl
   map_Kd Oak_texture.jpg
   ```
3. Digital Workshop will apply the texture to the 3D model

## Material Library

Consider creating a library of common woods:

**Softwoods**: Pine, Cedar, Fir, Spruce
**Hardwoods**: Oak, Maple, Cherry, Walnut, Mahogany
**Exotic**: Teak, Ebony, Rosewood, Zebrawood
**Engineered**: Plywood, MDF, Particle Board

Each with appropriate color values and textures!

