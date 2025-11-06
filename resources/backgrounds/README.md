# Thumbnail Backgrounds

This directory contains background images used for thumbnail generation in Digital Workshop.

## Adding New Backgrounds

1. **File Format**: PNG (recommended for transparency support)
2. **Recommended Size**: 1280x1280 pixels or larger
3. **Naming**: The filename (without extension) becomes the display name
4. **Location**: Place files directly in this directory

### Example:
```
resources/backgrounds/
├── Brick.png          → Appears as "Brick"
├── Wood_Grain.png     → Appears as "Wood Grain"
├── Marble.png         → Appears as "Marble"
└── Studio_White.png   → Appears as "Studio White"
```

## Best Practices

- **Resolution**: Use high-resolution images (1280x1280 or higher) for best quality
- **Aspect Ratio**: Square images (1:1) work best
- **File Size**: Keep under 5MB for performance
- **Naming**: Use descriptive names with underscores for spaces
- **Colors**: Consider both light and dark backgrounds for versatility

## Supported Formats

- **PNG** (recommended) - Supports transparency
- **JPG/JPEG** - Good for photographic backgrounds
- **BMP** - Basic support

## How It Works

1. All PNG files in this directory are automatically detected
2. They appear as clickable image buttons in Preferences → Content
3. Selected background is applied to all thumbnail generation
4. Background images are scaled to fit the 1280x1280 thumbnail size

## Tips

- **Studio Backgrounds**: Plain colors or subtle gradients work well
- **Textured Backgrounds**: Wood, concrete, fabric textures add visual interest
- **Branded Backgrounds**: Add your logo or watermark for professional look
- **Seasonal Themes**: Create holiday or seasonal backgrounds

## Troubleshooting

**Background not appearing?**
- Ensure file is PNG format
- Check filename has no special characters
- Restart Digital Workshop to refresh the list

**Background looks distorted?**
- Use square aspect ratio (1:1)
- Increase resolution to 1280x1280 or higher

