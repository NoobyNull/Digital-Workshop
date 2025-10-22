# Feeds & Speeds Calculator - Quick Start Guide

## What's New

A professional Feeds & Speeds calculator has been added to the hero window's **F&S** tab. This tool helps CNC operators calculate optimal cutting parameters for various tools and materials.

## Layout Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Feeds & Speeds Calculator                        SAE ⇄ MET ✓   │
├──────────────────────────┬──────────────────────────────────────┤
│                          │                                      │
│  TOOL LIBRARY            │  CALCULATOR                          │
│  ─────────────────────   │  ──────────────────────────────────  │
│                          │                                      │
│  Library: [IDC Woodcraft]│  Selected: 1/8" Acrylic O Flute     │
│  Search: [_____________] │                                      │
│                          │  RPM:        [10000]                │
│  ┌────────────────────┐  │  Feed Rate:  [60.0] in/min          │
│  │ Tool    │ Type │ Ø  │  │  Stepdown:   [0.125] in            │
│  ├────────────────────┤  │  Stepover:   [0.0813] in           │
│  │ 1/8" Acrylic O Fl  │  │                                      │
│  │ 1/16" Acrylic O Fl │  │  RESULTS                             │
│  │ 1/4" Acrylic O Fl  │  │  ──────────────────────────────────  │
│  │ 3/8" Acrylic O Fl  │  │                                      │
│  │ 1/2" Acrylic O Fl  │  │  Surface Speed: 556.32 in/min       │
│  │ ...                │  │  Material Removal: 6.12 cu.in/min   │
│  └────────────────────┘  │                                      │
│                          │                                      │
│  >> Add to My Toolbox    │                                      │
│                          │                                      │
└──────────────────────────┴──────────────────────────────────────┘
```

## Key Features

### 1. Tool Library (Left Panel)

**Library Selection**
- Switch between "IDC Woodcraft" (100+ professional tools) and "My Toolbox" (your personal tools)

**Search**
- Type to search tools by name
- Results update in real-time

**Tool Table**
- Shows tool name, type, and diameter
- Click to select a tool
- Right-click for context menu

**Add to Toolbox**
- Click ">> Add to My Toolbox" to save frequently used tools
- Tools persist across application restarts

### 2. Calculator (Right Panel)

**Tool Display**
- Shows selected tool name and specifications

**Input Parameters**
- **RPM**: Spindle speed (100-50,000)
- **Feed Rate**: Tool advance rate
- **Stepdown**: Depth of cut per pass
- **Stepover**: Horizontal tool advance

**Results**
- **Surface Speed**: Cutting speed at tool edge
- **Material Removal Rate**: Volume removed per minute
- Updates automatically as you adjust parameters

### 3. Unit Conversion

**SAE ⇄ MET Button**
- Located in top-right corner
- Click to toggle between inches and millimeters
- Shows current unit system (SAE or MET ✓)
- **Persists across application restarts**

**Automatic Conversions**
- Tool diameter: in ↔ mm
- Feed rates: in/min ↔ mm/min
- Stepdown/stepover: in ↔ mm
- RPM stays the same (universal)

## How to Use

### Adding a Tool to Your Toolbox

1. Open the **F&S** tab in the hero window
2. Select **"IDC Woodcraft"** from the library dropdown
3. Search for your tool (e.g., "1/8 acrylic")
4. Click on the tool in the table to select it
5. Click **">> Add to My Toolbox"** button
6. Confirm the success message

**Next time you launch the app, your tool will be in "My Toolbox"**

### Calculating Feeds & Speeds

1. Select a tool from any library
2. Tool details appear in the calculator panel
3. Adjust RPM, feed rate, stepdown, and stepover as needed
4. Results update automatically
5. Use the calculated values in your CNC software

### Converting Units

1. Click the **"SAE ⇄ MET"** button in the top-right
2. All values convert automatically:
   - Diameters: inches → millimeters
   - Feed rates: in/min → mm/min
   - Stepdown/stepover: inches → millimeters
3. Button shows current unit system
4. **Setting persists on next launch**

### Managing Your Toolbox

1. Switch to **"My Toolbox"** library
2. View all your saved tools
3. Search within your toolbox
4. Select a tool to use it in calculations
5. Right-click to remove tools (future enhancement)

## Tool Database

### IDC Woodcraft Library

The pre-loaded library includes 100+ professional tools:
- **Acrylic bits** (O-flute, various sizes)
- **Wood bits** (upcut, downcut, compression)
- **Metal bits** (carbide, various geometries)
- **Specialty bits** (V-carve, engraving, etc.)

Each tool includes:
- Recommended RPM
- Feed rates for different materials
- Stepdown and stepover recommendations
- Vendor information and product links

### Personal Toolbox

Your personal toolbox is stored locally and includes:
- All tools you've added
- Your custom configurations
- Unit preference (SAE or MET)

**Storage**: Windows Registry (QSettings)
**Persistence**: Across application restarts
**Backup**: Stored in your Windows user profile

## Tips & Tricks

### Optimize Your Workflow

1. **Add frequently used tools** to your toolbox
2. **Save tool configurations** by noting the parameters
3. **Use the search** to quickly find tools
4. **Toggle units** to match your CNC software

### Best Practices

- Start with recommended values from the tool database
- Adjust stepdown/stepover based on your machine's rigidity
- Monitor tool temperature and adjust feed rate if needed
- Use the material removal rate to estimate cycle time

### Common Scenarios

**Acrylic Cutting**
- Search: "acrylic"
- Select: "1/8\" Acrylic O Flute"
- RPM: 17,000
- Feed: 60 in/min
- Stepdown: 0.125"

**Wood Routing**
- Search: "wood"
- Select appropriate bit size
- RPM: 12,000-18,000
- Feed: 80-120 in/min
- Stepdown: 0.25-0.5"

**Metal Milling**
- Search: "metal"
- Select carbide bit
- RPM: 5,000-10,000
- Feed: 20-40 in/min
- Stepdown: 0.1-0.2"

## Troubleshooting

### Tools not appearing
- Ensure you're in the F&S tab
- Check that "IDC Woodcraft" is selected in the library dropdown
- Try searching for a common tool like "acrylic"

### Personal toolbox not saving
- Restart the application to verify persistence
- Check that you have write permissions to your user profile
- Try adding a tool again

### Unit conversion not working
- Click the "SAE ⇄ MET" button to toggle
- Verify the button shows the correct unit system
- Restart the application if needed

### Calculations seem wrong
- Verify the tool diameter is correct
- Check that RPM is in the valid range
- Ensure feed rate units match your CNC software

## Next Steps

1. **Explore the tool library** - Browse available tools
2. **Add your favorite tools** - Build your personal toolbox
3. **Calculate parameters** - Use the calculator for your projects
4. **Toggle units** - Switch between SAE and metric as needed

## Support

For issues or feature requests:
1. Check the troubleshooting section above
2. Review the detailed documentation: `FEEDS_AND_SPEEDS_IMPLEMENTATION.md`
3. Check application logs for error messages

## References

- **IDC Woodcraft**: https://idcwoodcraft.com
- **Fusion 360 Tool Library**: https://fusion360.autodesk.com
- **CNC Feeds & Speeds Guide**: https://www.cnccookbook.com/feeds-speeds/
- **Carbide 3D**: https://carbide3d.com/feeds-speeds/

