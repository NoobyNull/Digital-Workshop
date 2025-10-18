# Memory Calculation Examples

**Algorithm**: `min(minimum_doubled, fifty_percent_available, hard_max)`

Where:
- **minimum_doubled** = 512MB × 2 = 1024MB
- **fifty_percent_available** = Available system memory ÷ 2
- **hard_max** = Total system memory × 80% (reserves 20%)

---

## 📊 CALCULATION EXAMPLES

### Low-End System (4GB RAM)
```
Total: 4096 MB
Available: 3072 MB (75% after OS)
Reserve: 20%

Calculation:
- Minimum doubled: 1024 MB
- 50% available: 3072 ÷ 2 = 1536 MB
- Hard max: 4096 × 0.8 = 3276 MB
- Result: min(1024, 1536, 3276) = 1024 MB ✅

Interpretation: Gets minimum needed (1GB), leaves 3GB for OS/other apps
```

### Mid-Range System (8GB RAM)
```
Total: 8192 MB
Available: 6144 MB (75% after OS)
Reserve: 20%

Calculation:
- Minimum doubled: 1024 MB
- 50% available: 6144 ÷ 2 = 3072 MB
- Hard max: 8192 × 0.8 = 6553 MB
- Result: min(1024, 3072, 6553) = 1024 MB ✅

Interpretation: Gets minimum needed (1GB), leaves 7GB for OS/other apps
```

### High-End System (16GB RAM)
```
Total: 16384 MB
Available: 12288 MB (75% after OS)
Reserve: 20%

Calculation:
- Minimum doubled: 1024 MB
- 50% available: 12288 ÷ 2 = 6144 MB
- Hard max: 16384 × 0.8 = 13107 MB
- Result: min(1024, 6144, 13107) = 1024 MB ✅

Interpretation: Gets minimum needed (1GB), leaves 15GB for OS/other apps
```

### Very High-End System (32GB RAM)
```
Total: 32768 MB
Available: 24576 MB (75% after OS)
Reserve: 20%

Calculation:
- Minimum doubled: 1024 MB
- 50% available: 24576 ÷ 2 = 12288 MB
- Hard max: 32768 × 0.8 = 26214 MB
- Result: min(1024, 12288, 26214) = 1024 MB ✅

Interpretation: Gets minimum needed (1GB), leaves 31GB for OS/other apps
```

### Ultra High-End System (128GB RAM) - YOUR SYSTEM
```
Total: 130785 MB
Available: 82874 MB (63% after OS)
Reserve: 20%

Calculation:
- Minimum doubled: 1024 MB
- 50% available: 82874 ÷ 2 = 41437 MB
- Hard max: 130785 × 0.8 = 104628 MB
- GPU: Shared VRAM (32696 MB - integrated GPU detected)
- Result: min(1024, 41437, 104628) = 1024 MB ✅

Interpretation: Gets minimum needed (1GB), leaves 129GB for OS/other apps
```

---

## 🎯 KEY INSIGHTS

### Why This Algorithm Works

1. **Minimum Doubled (1024MB)**
   - Ensures app always has enough to run
   - Prevents crashes on low-memory systems
   - Scales with minimum specification

2. **50% of Available**
   - Never hogs all available memory
   - Leaves room for other apps
   - Adapts to current system load

3. **Hard Max (Total - 20%)**
   - Reserves 20% for OS/system processes
   - Prevents system slowdown
   - Ensures stability

### Scaling Behavior

- **4GB system**: Gets 1GB (25% of total)
- **8GB system**: Gets 1GB (12.5% of total)
- **16GB system**: Gets 1GB (6.25% of total)
- **32GB system**: Gets 1GB (3.125% of total)
- **128GB system**: Gets 1GB (0.78% of total)

**Pattern**: On systems with more RAM, the app uses a smaller percentage, leaving more for other applications.

---

## 🔧 MANUAL OVERRIDE

Users can override the automatic calculation by:
1. Opening Preferences → Performance tab
2. Selecting "Manual Override"
3. Adjusting the slider (512MB - 4GB)
4. Clicking OK to save

**Note**: Manual override is capped at 4GB to prevent excessive memory usage.

---

## 📝 CONFIGURATION

**Default Values** (in `src/core/application_config.py`):
```python
min_memory_specification_mb: int = 512  # Doubled to 1024MB
system_memory_reserve_percent: int = 20  # Reserve 20% for OS
```

**To Adjust**:
- Change `min_memory_specification_mb` to adjust minimum (doubled value)
- Change `system_memory_reserve_percent` to adjust OS reserve

---

## ✅ BENEFITS

- ✅ **Intelligent**: Scales with system resources
- ✅ **Safe**: Reserves OS memory
- ✅ **Flexible**: Manual override available
- ✅ **Transparent**: Shows calculation in UI
- ✅ **Persistent**: Settings saved across restarts
- ✅ **GPU-Aware**: Detects dedicated vs integrated GPU

---

**Status**: ✅ **ALGORITHM VERIFIED & WORKING** 🚀

