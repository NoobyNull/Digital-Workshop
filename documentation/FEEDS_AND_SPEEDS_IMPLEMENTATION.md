# Feeds & Speeds Calculator Implementation

## Overview

A comprehensive Feeds & Speeds (F&S) calculator has been implemented in the hero window's F&S tab. This tool helps CNC operators calculate optimal cutting parameters for various tools and materials.

## Features

### 1. Tool Library Management

#### Multiple Libraries
- **IDC Woodcraft Library**: Pre-loaded professional tool database with 100+ tools
- **My Toolbox**: Personal library for frequently used tools
- Easy switching between libraries via dropdown

#### Tool Database Structure
Each tool includes:
- Description (e.g., "1/8\" Acrylic O Flute")
- Tool type (flat end mill, ball end mill, etc.)
- Geometry (diameter, length, flute count, etc.)
- Vendor information
- Product ID and link
- Pre-configured cutting parameters

### 2. Tool Selection & Management

#### Browsing Tools
- Search functionality to find tools by description
- Table view showing tool name, type, and diameter
- Real-time filtering as you type

#### Adding to Personal Toolbox
Two methods:
1. **Button Method**: Select tool → Click ">> Add to My Toolbox"
2. **Context Menu**: Right-click on tool → "Add to My Toolbox"

#### Personal Toolbox
- Stored in QSettings (persists across application restarts)
- Quick access to frequently used tools
- Remove tools by switching to "My Toolbox" and deleting

### 3. Unit Conversion (SAE ⇄ MET)

#### Persistent Toggle Button
- Located in header: "SAE ⇄ MET"
- Automatically converts all values
- Setting persists across application restarts

#### Automatic Conversions
- **Dimensions**: Inches ↔ Millimeters (×25.4)
- **Feed Rates**: IPM ↔ MM/min (×25.4)
- **RPM**: Stays the same (universal)

#### Converted Values
- Tool diameter
- Stepdown and stepover
- Feed rates
- All display labels update automatically

### 4. Feeds & Speeds Calculator

#### Input Parameters
- **RPM**: Spindle speed (100-50,000)
- **Feed Rate**: Tool advance rate (0.1-1000 in/min or mm/min)
- **Stepdown**: Depth of cut per pass
- **Stepover**: Horizontal tool advance per pass

#### Calculated Results
- **Surface Speed**: Cutting speed at tool edge
- **Material Removal Rate**: Volume of material removed per minute
- All values automatically convert based on unit selection

#### Preset Values
- Automatically loads recommended values from tool database
- Based on material type and tool geometry
- Can be manually adjusted

## Architecture

### Components

#### 1. `FeedsAndSpeedsWidget` (Main Widget)
- Central hub for all F&S functionality
- Manages UI layout and user interactions
- Coordinates between tool library and calculator

#### 2. `ToolLibraryManager`
- Loads tool databases from JSON files
- Searches and retrieves tools
- Manages multiple libraries

#### 3. `PersonalToolboxManager`
- Stores personal tools in QSettings
- Handles add/remove operations
- Manages unit conversion preference

#### 4. `UnitConverter`
- Converts between SAE and metric units
- Formats values with appropriate labels
- Handles all unit-specific calculations

### File Structure

```
src/gui/feeds_and_speeds/
├── __init__.py                      # Package exports
├── feeds_and_speeds_widget.py       # Main widget (300 lines)
├── tool_library_manager.py          # Tool database management
├── personal_toolbox_manager.py      # Personal library storage
└── unit_converter.py                # Unit conversion utilities
```

### Data Storage

#### Tool Database
- Location: `src/gui/IDCWoodcraftFusion360Library.json`
- Format: JSON with tool array
- Contains 100+ professional tools from IDC Woodcraft

#### Personal Toolbox
- Storage: QSettings (Windows Registry/AppData)
- Key: `feeds_and_speeds/personal_toolbox`
- Format: JSON array of tool objects
- Persists across application restarts

#### Unit Preference
- Storage: QSettings
- Key: `feeds_and_speeds/auto_convert_to_metric`
- Type: Boolean
- Persists across application restarts

## Usage Guide

### Adding a Tool to Your Toolbox

1. Open the F&S tab in the hero window
2. Select "IDC Woodcraft" from the library dropdown
3. Search for your tool (e.g., "1/8 acrylic")
4. Click on the tool in the table
5. Click ">> Add to My Toolbox" button
6. Confirm the success message

### Calculating Feeds & Speeds

1. Select a tool from any library
2. Tool details appear in the calculator panel
3. Adjust RPM, feed rate, stepdown, and stepover as needed
4. Results update automatically
5. Toggle SAE ⇄ MET to see values in different units

### Managing Your Toolbox

1. Switch to "My Toolbox" library
2. View all your saved tools
3. Search within your toolbox
4. Select a tool to use it in calculations

### Converting Units

1. Click the "SAE ⇄ MET" button in the header
2. All values convert automatically
3. Button shows current unit system
4. Setting persists on next launch

## Technical Details

### Tool Database Format

```json
{
  "data": [
    {
      "guid": "unique-id",
      "description": "Tool name",
      "type": "flat end mill",
      "vendor": "IDC Woodcraft",
      "product-id": "OF-18",
      "geometry": {
        "DC": 0.125,      // Diameter
        "LB": 0.8,        // Length
        "NOF": 1          // Number of flutes
      },
      "start-values": {
        "presets": [
          {
            "n": 17000,           // RPM
            "v_f": 60.0,          // Feed rate
            "stepdown": 0.125,
            "stepover": 0.0813
          }
        ]
      },
      "unit": "inches"
    }
  ]
}
```

### Unit Conversion Factors

- 1 inch = 25.4 mm
- 1 IPM = 25.4 MM/min
- RPM is universal (no conversion needed)

### QSettings Keys

```python
"feeds_and_speeds/personal_toolbox"        # JSON array of tools
"feeds_and_speeds/auto_convert_to_metric"  # Boolean
```

## Future Enhancements

1. **Material Database**: Add material-specific recommendations
2. **Tool Presets**: Save custom tool configurations
3. **Calculation History**: Track previous calculations
4. **Export**: Export calculations to G-code or CSV
5. **Import**: Import custom tool libraries
6. **Optimization**: Suggest optimal parameters based on material
7. **Tooltips**: Add detailed help for each parameter
8. **Validation**: Warn about unsafe parameter combinations

## Integration Points

### Central Widget Manager
- Integrated into hero tabs as "F&S" tab
- Loads automatically on application startup
- Falls back to placeholder if import fails

### Main Window
- Accessible via `main_window.feeds_and_speeds_widget`
- Persists across application restarts
- Integrated with theme system

## Error Handling

- Missing tool database: Falls back to empty library
- Invalid JSON: Logs error and skips malformed tools
- QSettings errors: Logs warning, continues with defaults
- Import errors: Falls back to placeholder widget

## Performance

- Tool database loads on first access (~100ms)
- Search is instant (client-side filtering)
- Unit conversion is real-time
- No network calls required
- Minimal memory footprint

## Testing

To test the Feeds & Speeds calculator:

```python
from src.gui.feeds_and_speeds import FeedsAndSpeedsWidget
from PySide6.QtWidgets import QApplication

app = QApplication([])
widget = FeedsAndSpeedsWidget()
widget.show()
app.exec()
```

## Troubleshooting

### Tools not appearing
- Check that `IDCWoodcraftFusion360Library.json` exists in `src/gui/`
- Verify JSON file is valid
- Check application logs for parsing errors

### Personal toolbox not saving
- Verify QSettings is working (check Windows Registry)
- Check file permissions
- Restart application to verify persistence

### Unit conversion not working
- Click the SAE ⇄ MET button to toggle
- Check that button shows correct state
- Verify QSettings is saving the preference

## References

- IDC Woodcraft: https://idcwoodcraft.com
- Fusion 360 Tool Library: https://fusion360.autodesk.com
- CNC Feeds & Speeds: https://www.cnccookbook.com/feeds-speeds/

