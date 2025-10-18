# Screenshot Generation Feature - User Guide

## Quick Start

### Generating Screenshots
1. **Open the Application**
   - Launch 3D-MM (3D Model Manager)

2. **Add Models to Library** (if needed)
   - Use Model Library → Import to add models
   - Or drag and drop models into the library

3. **Generate Screenshots**
   - Click **Tools** menu
   - Select **Generate Screenshots for Library**
   - A progress dialog will appear

4. **View Thumbnails**
   - Wait for generation to complete
   - Switch to **Grid** view in Model Library
   - Thumbnails will display as icons

## What Happens During Generation

- Each model is loaded into the 3D viewer
- Materials are applied (if available)
- A screenshot is captured from the 3D view
- Screenshot is saved as a PNG file
- Database is updated with the thumbnail path
- Progress is shown in the status bar

## Where Screenshots Are Stored

- **Location**: `~/.3dmm/thumbnails/`
- **Filename**: `model_{id}.png`
- **Size**: 256x256 pixels (default)
- **Format**: PNG with RGB color

## Features

### Progress Tracking
- Real-time progress bar shows current/total models
- Status bar displays current model being processed
- Can be cancelled at any time

### Automatic Updates
- Model library automatically refreshes after completion
- Grid view displays new thumbnails immediately
- Database is updated with thumbnail paths

### Error Handling
- Failed models are skipped with warning
- Errors are logged for debugging
- Generation continues even if individual models fail

## Viewing Screenshots

### Grid View
1. Open Model Library
2. Click **Grid** tab
3. Thumbnails display as icons
4. Hover over icon to see model name
5. Click to select model
6. Double-click to load in viewer

### List View
- Thumbnails not displayed in list view
- Use grid view for visual browsing

## Troubleshooting

### Screenshots Not Appearing
- Ensure generation completed successfully
- Check status bar for errors
- Try refreshing the model library (View → Show Model Library)
- Verify models are in the database

### Generation Takes Too Long
- Large models take longer to render
- Generation runs in background (UI remains responsive)
- Can cancel and try again later

### Missing Thumbnails
- Some models may fail to generate screenshots
- Check application logs for errors
- Verify model files are valid and accessible

## Performance Notes

- Generation runs in background thread
- UI remains responsive during generation
- Each model takes 1-5 seconds depending on complexity
- 100 models typically takes 2-10 minutes

## Advanced Options

### Regenerate Screenshots
- Simply run "Generate Screenshots for Library" again
- Existing thumbnails will be overwritten
- Database will be updated with new paths

### Manual Thumbnail Management
- Thumbnails stored in `~/.3dmm/thumbnails/`
- Can be manually deleted to free space
- Will be regenerated on next batch run

## Tips

1. **First Time Setup**
   - Generate screenshots after adding models
   - Provides visual preview of library

2. **Regular Updates**
   - Regenerate after adding new models
   - Keeps library thumbnails current

3. **Performance**
   - Generation runs in background
   - Can continue working while generating
   - Close other applications for faster generation

4. **Storage**
   - Thumbnails use minimal disk space
   - ~50KB per screenshot (256x256)
   - 1000 models ≈ 50MB

## Keyboard Shortcuts

- **Tools Menu**: Alt+T
- **Generate Screenshots**: No default shortcut (use menu)

## Related Features

- **Material Manager**: Apply materials to models
- **Model Library**: Browse and manage models
- **Grid View**: Visual model browsing
- **Lighting Control**: Adjust lighting for screenshots

