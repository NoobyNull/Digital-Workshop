# Thumbnail Customization User Guide

## Quick Start

### Step 1: Open Preferences
1. Click **Edit** in the menu bar
2. Select **Preferences**
3. Click the **Thumbnails** tab

### Step 2: Select Background
1. In the "Background Image" section, browse the list
2. Click on a background to select it:
   - **Blue** - Blue gradient background
   - **Brick** - Brick texture background
   - **Gray** - Gray solid background
   - **Green** - Green gradient background
3. The preview updates automatically

### Step 3: Select Material
1. In the "Material" section, click the dropdown
2. Choose a material:
   - **None (Default)** - No material applied
   - **Bambu Board** - Bamboo wood texture
   - **Cherry** - Cherry wood texture
   - **Maple** - Maple wood texture
   - **Paduc** - Paduc wood texture
   - **Pine** - Pine wood texture
   - **Purpleheart** - Purpleheart wood texture
   - **Red Oak** - Red oak wood texture
   - **Sapele** - Sapele wood texture

### Step 4: Save Settings
1. Click the **Save** button at the bottom
2. A confirmation message appears
3. Settings are saved and will be used for all future thumbnails

## Generating Thumbnails

### Method 1: Generate All Library Screenshots
1. Click **Edit** in the menu bar
2. Select **Tools** → **Generate Library Screenshots**
3. Progress bar shows generation status
4. All thumbnails use your selected background and material

### Method 2: File Maintenance
1. Click **Edit** → **Preferences**
2. Go to **Files** tab
3. In "File & Model Maintenance" section:
   - Select **Regenerate Thumbnails** from dropdown
   - Click **Start**
4. All thumbnails regenerated with your settings

## Preview

The **Preview** section shows what your selected background looks like. This helps you visualize how thumbnails will appear.

## Tips & Tricks

### Best Combinations
- **Blue background + Cherry wood** - Professional look
- **Brick background + Red Oak** - Warm, natural appearance
- **Gray background + Maple** - Clean, modern look
- **Green background + Bamboo** - Eco-friendly appearance

### Changing Settings
- You can change background and material anytime
- New settings apply to all future thumbnail generations
- Existing thumbnails are not affected until regenerated
- Use "Regenerate Thumbnails" to update all existing thumbnails

### Performance
- Background images are loaded efficiently
- Material application is optimized
- Thumbnail generation runs in background
- UI remains responsive during generation

## Troubleshooting

### Background Not Showing
- Ensure background image file exists in `src/resources/backgrounds/`
- Try selecting a different background
- Check file permissions

### Material Not Applied
- Ensure material files exist in `src/resources/materials/`
- Try selecting "None (Default)" then reselect material
- Check that material MTL and PNG files are present

### Settings Not Saving
- Click **Save** button (not just Close)
- Check that you have write permissions
- Try restarting the application

### Thumbnails Look Wrong
- Regenerate thumbnails using File Maintenance
- Check that background and material are correctly selected
- Verify background image file is valid

## Default Settings

If you haven't configured thumbnails:
- **Background:** Light gray (default)
- **Material:** None (default)

These defaults provide clean, professional-looking thumbnails.

## Resetting to Defaults

1. Open Preferences → Thumbnails
2. Select "None (Default)" for material
3. Select any background (or leave unselected)
4. Click Save

## Advanced: Adding Custom Backgrounds

To add custom backgrounds:
1. Place PNG image in `src/resources/backgrounds/`
2. Restart application
3. New background appears in list automatically

To add custom materials:
1. Place MTL file in `src/resources/materials/`
2. Place corresponding PNG texture file
3. Restart application
4. New material appears in dropdown automatically

## Keyboard Shortcuts

- **Alt+E** - Open Edit menu
- **Alt+P** - Open Preferences (after Edit menu)
- **Tab** - Navigate between sections

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify background and material files exist
3. Try regenerating thumbnails
4. Check application logs for errors

## See Also

- File & Model Maintenance - `FILE_MAINTENANCE_FEATURE.md`
- Thumbnail Implementation - `THUMBNAIL_CUSTOMIZATION_IMPLEMENTATION.md`
- Screenshot Generation - `SCREENSHOT_FEATURE_IMPLEMENTATION.md`

