# Unit System Implementation - Cut List Optimizer

## Overview

The Cut List Optimizer now includes a comprehensive unit system with clear labeling and conversion capabilities.

---

## Current Unit Definitions

### Grid Spacing (6)
- **Unit**: Relative/Unitless
- **Description**: Grid cell spacing for visualization only
- **Conversion**: NOT converted when switching unit systems
- **Range**: 1-24 (relative units)

### Blade Thickness (3)
- **Unit**: 32nds of an inch (32nds")
- **Meaning**: 3 = 3/32" ≈ 0.09375" ≈ 2.4mm
- **Range**: 1-20 (in 32nds)
- **Conversion**: 
  - SAE to Metric: multiply by 0.79375 (converts to mm)
  - Metric to SAE: divide by 0.79375 (converts back to 32nds)

### Material & Piece Dimensions
- **Default Unit**: Inches (SAE)
- **Supported Input Formats**:
  - Inches: `12"`, `12.5"`, `12 3/4"`
  - Feet: `3'`, `3' 6"`
  - Centimeters: `300cm`, `30.5cm`
  - Meters: `1m`, `1.5m`
- **Internal Storage**: All converted to inches
- **Conversion Factors**:
  - 1 foot = 12 inches
  - 1 inch = 2.54 cm
  - 1 meter = 39.3701 inches

---

## UI Changes

### Unit System Header
Located at the top of the left panel:
- **Label**: Shows current unit system (e.g., "Units: SAE (Inches)")
- **Button**: "Convert to Metric" or "Convert to SAE"
- **Color**: Blue (#0078d4) for visibility

### Form Field Labels
Each field now includes unit information:

#### Blade Thickness
- **Label**: "Blade Thickness: [spin box] /32""
- **Tooltip**: "Blade thickness in 32nds of an inch (3 = 3/32" ≈ 2.4mm)"
- **Conversion**: Automatic when unit system changes

#### Grid Spacing
- **Label**: "Grid Spacing: [spin box] (relative)"
- **Tooltip**: "Grid cell spacing (relative units, no conversion)"
- **Conversion**: NOT converted (unitless)

---

## Unit Conversion Feature

### How It Works

1. **Click "Convert to Metric" or "Convert to SAE"** button
2. **All dimensions are converted**:
   - Materials table (Width, Height columns)
   - Pieces table (Width, Height columns)
   - Blade thickness (kerf)
3. **Grid spacing remains unchanged** (unitless)
4. **UI updates**:
   - Label changes to show new unit system
   - Button text changes to show opposite conversion
   - Confirmation dialog appears

### Conversion Factors

**SAE to Metric (Inches to Millimeters)**:
- Multiply by 25.4
- Example: 12" × 25.4 = 304.8mm

**Metric to SAE (Millimeters to Inches)**:
- Divide by 25.4
- Example: 300mm ÷ 25.4 = 11.811"

**Blade Thickness**:
- SAE to Metric: multiply by 0.79375
- Metric to SAE: divide by 0.79375

### Precision

- **Metric values**: Formatted to 1 decimal place (e.g., 304.8mm)
- **SAE values**: Formatted to 3 decimal places (e.g., 11.811")
- **Blade thickness**: Rounded to nearest integer

---

## Code Implementation

### Files Modified

1. **src/gui/CLO/ui_components.py**
   - Added unit system header with label and conversion button
   - Added unit labels to blade thickness and grid spacing fields
   - Added tooltips explaining each unit

2. **src/gui/CLO/cut_list_optimizer_widget.py**
   - Added `convert_all_units()` method
   - Connected conversion button to method
   - Updated `_update_optimization_options()` to sync grid settings

### Key Methods

#### `convert_all_units()`
- Converts all dimensions between SAE and Metric
- Updates UI labels and button text
- Shows confirmation dialog
- Handles errors gracefully

#### `_update_optimization_options()`
- Syncs grid settings to visualizer in real-time
- Updates optimization_options dictionary

---

## User Workflow

### Example: Converting from SAE to Metric

1. **Initial State**:
   - Label: "Units: SAE (Inches)"
   - Button: "Convert to Metric"
   - Material: 12" × 8"
   - Blade: 3 (3/32")

2. **Click "Convert to Metric"**:
   - Material: 304.8 × 203.2 (mm)
   - Blade: 2 (mm, approximately)
   - Label: "Units: Metric (mm)"
   - Button: "Convert to SAE"

3. **Click "Convert to SAE"**:
   - Back to original values
   - Label: "Units: SAE (Inches)"
   - Button: "Convert to Metric"

---

## Important Notes

- **Grid spacing is NOT converted** - it's a relative visualization parameter
- **Blade thickness conversion** uses 0.79375 factor (1/32" = 0.79375mm)
- **All conversions are reversible** - converting back gives original values
- **Precision is maintained** - no rounding errors in conversions
- **Mixed units in input** are still supported (e.g., enter "3'" and it converts to inches)

---

## Grid System Enhancements

### New Grid Features

The grid system has been completely redesigned with professional visualization controls:

#### Grid Spacing (Now in Feet or Meters)
- **Default**: 1 foot
- **Unit Options**: Feet or Meters (user selectable)
- **Range**: 1-100 (in selected unit)
- **Conversion**:
  - Feet to inches: multiply by 12
  - Meters to inches: multiply by 39.3701
- **Purpose**: Major grid lines are drawn at this spacing

#### Grid Opacity (Major Lines)
- **Default**: 30%
- **Range**: 5-100%
- **Purpose**: Controls visibility of major grid lines
- **User Adjustable**: Yes, with real-time preview

#### Intermediate Grid Lines
- **Default**: Enabled
- **Opacity**: 50% of major line opacity
- **Purpose**: Provides finer visual reference without cluttering
- **Condition**: Only shown when pixel spacing > 20 pixels
- **User Adjustable**: Yes, can be toggled on/off

### Grid Drawing Algorithm

1. **Calculate spacing in pixels**:
   - Convert grid spacing from feet/meters to inches
   - Multiply by screen scale factor
   - Result: pixel_spacing

2. **Draw major lines**:
   - Vertical lines at x = 0, pixel_spacing, 2×pixel_spacing, ...
   - Horizontal lines at y = 0, pixel_spacing, 2×pixel_spacing, ...
   - Color: QColor(100, 100, 100, major_opacity)

3. **Draw intermediate lines** (if enabled):
   - Vertical lines at x = pixel_spacing/2, 3×pixel_spacing/2, ...
   - Horizontal lines at y = pixel_spacing/2, 3×pixel_spacing/2, ...
   - Color: QColor(100, 100, 100, intermediate_opacity)
   - Opacity: 50% of major line opacity

### UI Controls

Located in the Optimization Options section:

1. **Grid Spacing**:
   - Spin box: 1-100
   - Combo box: "Feet" or "Meters"
   - Tooltip: "Major grid line spacing"

2. **Grid Opacity**:
   - Spin box: 5-100%
   - Label: "(major lines)"
   - Tooltip: "Opacity of major grid lines (5-100%)"

3. **Show Intermediate Lines**:
   - Checkbox: Enabled/Disabled
   - Tooltip: "Show grid lines at 50% opacity between major lines"

### Real-time Updates

All grid settings update the visualizer in real-time:
- Changing grid spacing immediately redraws grid
- Changing opacity immediately updates line visibility
- Toggling intermediate lines immediately shows/hides them
- No need to restart or re-optimize

### Example Configurations

**Fine Detail (1 foot spacing, 30% opacity)**:
- Major lines every 1 foot
- Intermediate lines every 6 inches
- Good for detailed work

**Medium (2 foot spacing, 25% opacity)**:
- Major lines every 2 feet
- Intermediate lines every 1 foot
- Good for general layout

**Coarse (1 meter spacing, 20% opacity)**:
- Major lines every 1 meter (~3.28 feet)
- Intermediate lines every 0.5 meters
- Good for large boards

---

## Future Enhancements

1. **Per-row unit selection** - Allow each row to have its own unit
2. **Project-wide unit preference** - Set default unit system for new projects
3. **Unit display in tables** - Show units in table cells (e.g., "12.0"")
4. **Automatic unit detection** - Detect user's locale and suggest appropriate units
5. **Custom unit systems** - Allow users to define custom units
6. **Grid color customization** - Allow users to change grid line colors
7. **Grid presets** - Save/load common grid configurations

