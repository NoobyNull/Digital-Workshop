# Cut List Optimizer - Unit System Behavior

## Current Behavior with Mixed Units

### What Happens When You Mix Units

If you enter measurements using mixed unit systems (e.g., inches and meters, or mm and yards), the system will:

1. **Detect the mixed units** during validation
2. **Show a warning dialog** to the user
3. **Block the optimization** from running

### Example Scenarios

#### Scenario 1: Inches + Meters
```
Material 1: 12" x 8"        (imperial)
Material 2: 1m x 0.5m       (metric)
```
**Result:** ⚠️ Warning dialog appears, optimization blocked

#### Scenario 2: Feet + Centimeters
```
Piece 1: 3' x 2'            (imperial)
Piece 2: 50cm x 30cm        (metric)
```
**Result:** ⚠️ Warning dialog appears, optimization blocked

#### Scenario 3: Millimeters + Yards
```
Material: 500mm x 300mm     (metric)
Piece: 2yd x 1yd            (imperial)
```
**Result:** ⚠️ Warning dialog appears, optimization blocked

---

## Unit System Classification

### Imperial System (Blocked Together)
- Inches (`"`)
- Feet (`'`)
- Yards (if supported)

### Metric System (Blocked Together)
- Millimeters (mm)
- Centimeters (cm)
- Meters (m)

---

## What IS Allowed

### Within Imperial System ✅
```
Material: 12" x 8"
Piece 1: 3' x 2'
Piece 2: 6" x 4"
```
**Result:** ✅ All converted to inches internally, optimization proceeds

### Within Metric System ✅
```
Material: 500mm x 300mm
Piece 1: 1m x 0.5m
Piece 2: 250mm x 150mm
```
**Result:** ✅ All converted to millimeters internally, optimization proceeds

---

## How Unit Conversion Works

### Parsing Logic
The system uses `parse_fractional_input()` method which:

1. **Detects the unit** from the text suffix
2. **Extracts the numeric value** (supports fractions like "12 3/4")
3. **Converts to base unit:**
   - Imperial → inches (base)
   - Metric → millimeters (base)

### Conversion Factors
```python
# Imperial conversions (to inches)
feet → inches:      multiply by 12
cm → inches:        divide by 2.54
meters → inches:    multiply by 39.3701

# Metric conversions (to mm)
cm → mm:            multiply by 10
meters → mm:        multiply by 1000
inches → mm:        multiply by 25.4
```

---

## Validation Process

### Step 1: Check Unit Systems
```python
for each material and piece:
    detect unit system (imperial or metric)
    add to set of detected systems
```

### Step 2: Validate Consistency
```python
if len(unit_systems) > 1:
    show warning dialog
    return False (block optimization)
else:
    return True (allow optimization)
```

### Step 3: Warning Message
```
"Mixed Unit Systems Detected"

Your measurements mix imperial (inches/feet) 
with metric (cm/m).

Please use consistent systems:
- All imperial: inches (") and/or feet (')
- All metric: centimeters (cm) and/or meters (m)
```

---

## Supported Unit Formats

### Imperial
- `12"` - inches
- `12 3/4"` - fractional inches
- `3'` - feet
- `3' 6"` - feet and inches (if supported)

### Metric
- `300mm` - millimeters
- `30cm` - centimeters
- `1m` - meters
- `1.5m` - decimal meters

### No Unit
- `12` - assumes base unit (inches or mm depending on context)

---

## Recommendations for Users

### Best Practice
1. **Choose ONE unit system** for your entire project
2. **Use consistent units** throughout all materials and pieces
3. **Convert before entering** if you have mixed sources

### Example Workflow
```
If you have:
- Material in inches: 12" x 8"
- Piece in feet: 3' x 2'

Convert first:
- Material: 12" x 8" ✓
- Piece: 36" x 24" ✓ (3' = 36")

Then enter both in inches
```

---

## Future Enhancement Opportunities

### Option 1: Auto-Convert
Automatically convert all inputs to a selected base unit:
- User selects: "Use Inches" or "Use Millimeters"
- System converts all inputs to that unit
- Display converted values in table

### Option 2: Per-Row Unit Selection
Allow each row to have its own unit selector:
```
Material 1: [12] [inches]
Material 2: [300] [millimeters]
```
System auto-converts to common base unit

### Option 3: Global Unit Preference
Set project-wide unit system:
- Project settings: "Imperial" or "Metric"
- All inputs auto-convert to that system
- Display in consistent units

---

## Current Code Location

**File:** `src/gui/CLO/cut_list_optimizer_widget.py`

**Key Methods:**
- `validate_unit_consistency()` - Lines 595-622
- `_get_unit_system()` - Lines 624-631
- `parse_fractional_input()` - Lines 173-242

**Validation Trigger:**
- Called before optimization in `optimize_cuts()` method
- Blocks optimization if mixed units detected

